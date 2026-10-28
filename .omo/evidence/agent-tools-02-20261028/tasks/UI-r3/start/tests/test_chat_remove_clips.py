"""A model may propose removal of timeline occurrences, not delete source media."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import chat_models
import chat_protocols
import editing
import local_creation_tools
import production_tools
from tests import test_local_creation_tools as fixtures
from tests import test_timeline_repeated_http as repeated_fixture


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class RemoveClipsTest(unittest.TestCase):
    setUp=fixtures.LocalToolsTest.setUp
    call=fixtures.LocalToolsTest.call
    project=fixtures.LocalToolsTest.project
    tool=fixtures.LocalToolsTest.tool

    def args(self,commands):
        return dict(description='제외 제안',timeline_version=self.project()['timeline_head'],commands=commands)

    def test_all_provider_schemas_and_runtime_validation(self):
        command=dict(op='remove_clips',clip_indices=[0])
        for provider in ('anthropic','openai','xai'):
            defs=chat_protocols.tool_definitions(provider)
            item=next(x for x in defs if x['name']=='propose_timeline_changes')
            schema=item['input_schema'] if provider=='anthropic' else item['parameters']
            variants=schema['properties']['commands']['items']['anyOf']
            self.assertEqual(sum(x['properties']['op']['enum']==['remove_clips'] for x in variants),1)
            result,_=self.tool('propose_timeline_changes',self.args([command]),provider)
            self.assertEqual(result['status'],'proposed');self.assertFalse(result['applied'])
        self.assertIn('remove_clips',chat_models.SYSTEM)
        for value in ([],[0,0],[True],[-1],[0]*31,'0'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                production_tools.validate('propose_timeline_changes',self.args([dict(op='remove_clips',clip_indices=value)]))
        for bad in (dict(op=[],clip_indices=[0]),dict(op='set_clip',clip_index=[],take=1,trim=0,duration=1)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                production_tools.validate('propose_timeline_changes',self.args([command,bad]))

    def test_duplicate_occurrences_and_mixed_clip_edit(self):
        timeline=editing.current(self.project());timeline['clips']=[deepcopy(timeline['clips'][0]),deepcopy(timeline['clips'][0]),deepcopy(timeline['clips'][1])]
        self.call('timeline',timeline=timeline);before=deepcopy(self.project());base=editing.current(before)
        commands=[dict(op='set_clip',clip_index=2,take=1,trim=.25,duration=.5),dict(op='remove_clips',clip_indices=[0])]
        result,_=self.tool('propose_timeline_changes',self.args(commands))
        self.assertEqual(result['status'],'proposed');self.assertFalse(result['applied'])
        diff=result['timeline_diff']
        self.assertEqual(diff['clip_order'],{'changed':True,'before':[0,1,2],'after':[1,2]})
        self.assertEqual(diff['removed_clips'],[{'base_clip_index':0,'before':base['clips'][0]}])
        self.assertEqual(diff['clips'][0]['base_clip_index'],2);self.assertEqual(diff['clips'][0]['proposed_clip_index'],1)
        proposal=self.project()['timeline_edit_proposals'][-1]
        self.assertEqual(proposal['timeline']['clips'][0],base['clips'][1]);self.assertEqual(proposal['timeline']['clips'][1]['trim'],.25)
        self.assertEqual(self.project()['timeline_versions'],before['timeline_versions']);self.assertEqual(self.project()['shots'],before['shots']);self.assertEqual(self.project()['audio_versions'],before['audio_versions'])

    def test_invalid_targets_combinations_and_subtitle_boundaries(self):
        invalid=[[dict(op='remove_clips',clip_indices=[0,1])],[dict(op='remove_clips',clip_indices=[2])],
          [dict(op='remove_clips',clip_indices=[0]),dict(op='reorder_clips',order=[1,0])],
          [dict(op='remove_clips',clip_indices=[0]),dict(op='set_clip',clip_index=0,take=1,trim=0,duration=1)],
          [dict(op='remove_clips',clip_indices=[0]),dict(op='remove_clips',clip_indices=[1])]]
        for commands in invalid:
            before=deepcopy(self.project())
            try:
                result,_=self.tool('propose_timeline_changes',self.args(commands));self.assertIn(result['status'],('blocked','invalid_arguments'))
            except ValueError:pass
            self.assertEqual(self.project()['timeline_versions'],before['timeline_versions']);self.assertEqual(self.project()['shots'],before['shots'])
        timeline=editing.current(self.project());timeline['subtitles']=[dict(start=1,end=2,text='후반 자막')]
        self.call('timeline',timeline=timeline)
        result,_=self.tool('propose_timeline_changes',self.args([dict(op='remove_clips',clip_indices=[0])]))
        self.assertEqual(result['status'],'blocked')
        result,_=self.tool('propose_timeline_changes',self.args([dict(op='remove_clips',clip_indices=[0]),dict(op='set_captions',cues=[dict(start=0,end=1,text='직접 수정')])]))
        self.assertEqual(result['status'],'proposed');self.assertFalse(result['captions_preserved'])

    def test_stale_and_repeat_review(self):
        before=deepcopy(self.project());args=self.args([dict(op='remove_clips',clip_indices=[0])])
        out,run=self.tool('propose_timeline_changes',args,identifier='remove')
        again,_=self.tool('propose_timeline_changes',args,run=run,identifier='remove');self.assertEqual(out,again)
        self.assertEqual(self.project()['timeline_head'],before['timeline_head'])
        self.call('review_timeline_proposal',proposal_id=out['proposal_id'],timeline_version=args['timeline_version'],decision='approved')
        self.call('review_timeline_proposal',proposal_id=out['proposal_id'],timeline_version=args['timeline_version'],decision='approved')
        self.assertEqual(len(self.project()['timeline_versions']),len(before['timeline_versions'])+1)
        stale,_=self.tool('propose_timeline_changes',args);self.assertEqual(stale['status'],'blocked')

    def test_stale_proposal_never_applies_after_intervening_save(self):
        args=self.args([dict(op='remove_clips',clip_indices=[0])]);out,_=self.tool('propose_timeline_changes',args)
        self.call('timeline',timeline=editing.current(self.project()));before=deepcopy(self.project())
        with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=out['proposal_id'],timeline_version=args['timeline_version'],decision='approved')
        self.assertEqual(self.project(),before)

    def test_thirty_occurrences_can_reduce_to_one_but_never_zero(self):
        timeline=editing.current(self.project());timeline['clips']=[deepcopy(timeline['clips'][0]) for _ in range(30)]
        self.call('timeline',timeline=timeline)
        out,_=self.tool('propose_timeline_changes',self.args([dict(op='remove_clips',clip_indices=list(range(29)))]))
        self.assertEqual(out['status'],'proposed');self.assertEqual(len(out['timeline_diff']['removed_clips']),29)
        self.assertEqual(self.project()['timeline_edit_proposals'][-1]['timeline']['clips'],[timeline['clips'][29]])
        out,_=self.tool('propose_timeline_changes',self.args([dict(op='remove_clips',clip_indices=list(range(30)))]))
        self.assertEqual(out['status'],'blocked')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class RemoveClipsHTTPTest(unittest.TestCase):
    setUp=repeated_fixture.RepeatedTimelineHTTPTest.setUp
    close_server=repeated_fixture.RepeatedTimelineHTTPTest.close_server
    get_state=repeated_fixture.RepeatedTimelineHTTPTest.get_state
    project=repeated_fixture.RepeatedTimelineHTTPTest.project
    request=repeated_fixture.RepeatedTimelineHTTPTest.request
    post=repeated_fixture.RepeatedTimelineHTTPTest.post
    select=repeated_fixture.RepeatedTimelineHTTPTest.select
    timeline=repeated_fixture.RepeatedTimelineHTTPTest.timeline

    def test_http_proposal_human_approval_audio_render_and_restore(self):
        audio=Path(self.tmp.name)/'audio.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=5',str(audio)],check=True)
        self.post('audio',song='A',filename='audio.wav',content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 제작')
        base=self.timeline();base['clips'].append(deepcopy(base['clips'][0]));base['audio']=1;base['subtitles']=[dict(start=0,end=1,text='테스트 자막')]
        self.post('timeline',song='A',timeline=base)
        before=deepcopy(self.project());run=self.post('production_run',song='A')['run']['id']
        command=dict(op='remove_clips',clip_indices=[0])
        call=dict(id='occurrence-remove',name='propose_timeline_changes',arguments=dict(description='첫 반복 컷 제외',timeline_version=1,commands=[command]),complete=True)
        result=self.post('production_tool',song='A',run=run,call=call)['tool']
        self.assertEqual(result['status'],'proposed');self.assertEqual(result['timeline_diff']['clip_order']['after'],[1,2]);self.assertFalse(result['applied'])
        self.assertEqual(self.project()['timeline_versions'],before['timeline_versions']);self.assertEqual(self.project()['shots'],before['shots'])
        unauthorized=dict(action='review_timeline_proposal',data=dict(song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved'),revision=self.get_state()['revision'],request_id=uuid.uuid4().hex)
        req=Request(self.base+'/api/action',data=json.dumps(unauthorized).encode(),headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as denied:urlopen(req)
        self.assertEqual(denied.exception.code,403);denied.exception.close();self.assertEqual(self.project()['timeline_head'],1)
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
        after=self.project();self.assertEqual(after['timeline_head'],2);self.assertEqual(len(after['timeline_versions']),2)
        new=after['timeline_versions'][-1];self.assertEqual([c['take'] for c in new['clips']],[2,1]);self.assertNotIn('approval',new)
        self.assertEqual(after['shots'],before['shots']);self.assertEqual(after['audio_versions'],before['audio_versions']);self.assertEqual(after['timeline_versions'][0],before['timeline_versions'][0])
        self.post('approve_timeline',song='A');job=self.post('render_job',song='A')['job'];self.assertTrue(self.http.store.process_next())
        record=next(j for j in self.get_state()['jobs'] if j['id']==job);self.assertEqual(record['status'],'completed',record.get('error'))
        path=Path(self.tmp.name)/'exports'/(job+'.mp4')
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        self.assertEqual({s['codec_type'] for s in probe['streams']},{'audio','video','subtitle'});self.assertAlmostEqual(float(probe['format']['duration']),2,places=2)
        def pixel(at):
            return subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1','-vf','crop=2:2:320:180,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-'])
        blue,red=pixel(.5),pixel(1.5);self.assertGreater(blue[2],180);self.assertGreater(red[0],180)
        self.post('restore_timeline',song='A',version=1);restored=self.project()['timeline_versions'][-1]
        self.assertEqual(restored['clips'],before['timeline_versions'][0]['clips']);self.assertNotIn('approval',restored)


if __name__=='__main__':unittest.main()
