"""Selected-model synthetic protocol and actual local overlay edit contracts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import uuid

import chat_general
import editing
import local_creation_tools as local
import motion_renderer
import production_context
import production_tools
from tests import test_chat_general_http as general_base
from tests.test_chat_runtime import response,use
from tests.test_motion import scene


class AIMotionOverlayTest(unittest.TestCase):
    def setUp(self):
        self.f=general_base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.post('shot',song='A',shot='s',description='synthetic overlay source')
        self.post('take',song='A',shot='s',shot_revision=0,filename='base.png',
                  content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
                  reason='synthetic',rights='directly authored')
        self.post('select',song='A',shot='s',take=1,shot_revision=1)
        self.post('review_take',song='A',shot='s',take=1,decision='approved',reason='synthetic checked')
        value=scene();value['layers']=value['layers'][:1];value['layers'][0].update(text='모델 편집 한글',color='#000000')
        self.add_motion(value)
        timeline=editing.current(self.project());timeline['clips'][0]['duration']=3;timeline['profile']='preview'
        self.post('timeline',song='A',timeline=timeline);self.post('approve_timeline',song='A')

    def post(self,action,**data):
        code,result=self.f.action(action,**data);self.assertEqual(code,200,result);return result

    def project(self):return self.f.state()['projects']['A']

    def source_id(self):return production_context.shot_id(self.project(),'s')

    def add_motion(self,value):
        proposal=self.post('motion_propose',song='A',shot_id=self.source_id(),
                           base_motion_revision=self.project()['shots']['s'].get('motion_head',0),scene=value)['motion']['proposal_id']
        with patch.object(motion_renderer,'validate_text',return_value={}):
            self.post('motion_review',song='A',proposal_id=proposal,decision='approved')

    def command(self,**changes):
        value=dict(op='set_motion_overlay',clip_index=0,source_shot_id=self.source_id(),motion_revision=1,start=.5,end=2.5,offset_x=0,offset_y=0)
        value.update(changes);return value

    def args(self,commands=None):
        return dict(description='합성 모션 겹치기 제안',timeline_version=self.project()['timeline_head'],commands=commands or [self.command()])

    def tool(self,args,run=None):
        run=run or self.post('production_run',song='A')['run']['id']
        result=self.post('production_tool',song='A',run=run,
                         call=dict(id=uuid.uuid4().hex,name='propose_timeline_changes',arguments=args,complete=True))['tool']
        return result,run

    def chat_tool(self,name,args,*,legacy_schema=False):
        transport=self.f.http.store.general_chat_runtime.transport
        transport.responses=[response([use('synthetic-overlay',name,args)],'tool_use')]
        if legacy_schema:
            schema=deepcopy(local.COMMAND_SCHEMA)
            schema['items']['anyOf']=[x for x in schema['items']['anyOf'] if x['properties']['op']['enum'][0] not in local.OVERLAY_OPERATIONS]
            with patch.object(local,'COMMAND_SCHEMA',schema):preview=self.f.preview()
        else:preview=self.f.preview()
        code,result=self.f.approve(preview);self.assertEqual(code,200,result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        p=self.project();turn=p['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'awaiting_continuation_approval',turn)
        follow=p['general_chat_previews'][-1]
        blocks=[b for message in follow['message_body']['messages'] if isinstance(message.get('content'),list)
                for b in message['content'] if b.get('type')=='tool_result']
        tool_result=json.loads(blocks[-1]['content'])
        code,result=self.f.approve(follow,decision='reject');self.assertEqual(code,200,result)
        return tool_result,preview,follow

    def test_context_has_stored_overlay_and_bounded_approved_history_without_grants(self):
        self.post('timeline',song='A',timeline=dict(editing.current(self.project()),clips=[dict(
            shot='s',take=1,duration=3,trim=0,motion_overlay=dict(shot='s',motion_revision=1,start=.5,end=2.5,offset_x=120,offset_y=20))]))
        result,_,_=self.chat_tool('search_project_context',dict(query='current overlay'))
        targets=result['execution_targets'];overlay=targets['timeline']['clips'][0]['motion_overlay']
        self.assertEqual(overlay['source_shot_id'],self.source_id());self.assertEqual(overlay['offset_x'],120)
        self.assertEqual(overlay['motion_revision'],1)
        catalog=targets['motion_overlay_sources'];self.assertEqual(len(catalog['items']),1)
        self.assertNotIn('scene',catalog['items'][0]);self.assertNotIn('grant_id',catalog['items'][0])
        self.assertEqual(catalog['items'][0]['approval_status'],'recorded_immutable_source')
        p=self.project();version=p['shots']['s']['motion_versions'][0]
        p['shots']['s']['motion_versions']=[dict(deepcopy(version),id=n) for n in range(1,41)]
        first=production_context.motion_overlay_sources(p);self.assertEqual(len(first['items']),32)
        self.assertEqual(first['next_query'],'motion-overlay-sources offset=32')
        second=production_context.motion_overlay_sources(p,first['next_query'])
        self.assertEqual([x['motion_revision'] for x in second['items']],list(range(33,41)))
        self.assertIsNone(second['next_query'])
        self.assertLess(len(json.dumps(first,ensure_ascii=False).encode()),16*1024)
        self.assertFalse(any('scene' in item or 'grant_id' in item for item in first['items']))
        self.assertEqual(production_context.motion_overlay_sources(p,'motion-overlay-sources offset=9999999')['items'],[])
        for query in ['motion-overlay-sources offset=-1','motion-overlay-sources offset=nan','motion-overlay-sources offset=1.5','motion-overlay-sources offset=99999999']:
            with self.assertRaises(ValueError):production_tools.validate('search_project_context',dict(query=query))

    def test_old_general_manifest_cannot_gain_new_operations_with_current_run_marker(self):
        before=deepcopy(self.project()['timeline_versions'])
        result,old,_=self.chat_tool('propose_timeline_changes',self.args(),legacy_schema=True)
        self.assertEqual(result['status'],'blocked');self.assertEqual(result['code'],'TOOL_SCHEMA_REVIEW_REQUIRED')
        self.assertEqual(self.project()['timeline_versions'],before)
        self.assertNotIn('set_motion_overlay',json.dumps(old['message_body']['tools']))

    def test_legacy_missing_malformed_or_future_run_markers_are_blocked(self):
        for marker in [None,1,3,'2',True]:
            run=self.post('production_run',song='A')['run']['id']
            with self.f.http.store.connect() as db:
                revision,body=db.execute('SELECT revision,body FROM state').fetchone();saved=json.loads(body)
                item=next(x for x in saved['projects']['A']['production_runs'] if x['id']==run)
                if marker is None:item.pop('timeline_command_revision')
                else:item['timeline_command_revision']=marker
                db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(saved),))
            result,_=self.tool(self.args(),run)
            self.assertEqual(result['code'],'TOOL_SCHEMA_REVIEW_REQUIRED',marker)

    def test_new_command_proposes_diff_then_human_applies_without_output_approval(self):
        before=deepcopy(self.project());result,_=self.tool(self.args())
        self.assertEqual(result['status'],'proposed');self.assertFalse(result['applied'])
        self.assertEqual(self.project()['timeline_versions'],before['timeline_versions'])
        diff=result['timeline_diff']['motion_overlays'][0]
        self.assertIsNone(diff['before']);self.assertEqual(diff['after']['motion_revision'],1)
        self.assertEqual(diff['after']['shot'],'s')
        applied=self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=before['timeline_head'],decision='approved')['timeline_proposal']
        self.assertTrue(applied['applied']);self.assertFalse(applied['output_approved'])
        current=editing.current(self.project());self.assertNotIn('approval',current)
        self.assertEqual(current['clips'][0]['motion_overlay'],diff['after'])
        self.assertEqual(self.project()['timeline_versions'][0],before['timeline_versions'][0])
        self.assertEqual(self.f.action('render_job',song='A')[0],400)

    def test_clear_preserves_source_and_reordering_binds_base_occurrence(self):
        initial,_=self.tool(self.args())
        self.post('review_timeline_proposal',song='A',proposal_id=initial['proposal_id'],timeline_version=1,decision='approved')
        version=deepcopy(self.project()['shots']['s']['motion_versions'])
        result,_=self.tool(self.args([dict(op='clear_motion_overlay',clip_index=0)]))
        self.assertIsNone(result['timeline_diff']['motion_overlays'][0]['after'])
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=2,decision='approved')
        self.assertNotIn('motion_overlay',editing.current(self.project())['clips'][0]);self.assertEqual(version,self.project()['shots']['s']['motion_versions'])
        timeline=editing.current(self.project());timeline['clips']*=2
        self.post('timeline',song='A',timeline=timeline)
        result,_=self.tool(self.args([self.command(clip_index=0),dict(op='reorder_clips',order=[1,0])]))
        self.assertEqual(result['timeline_diff']['motion_overlays'][0]['proposed_clip_index'],1)

    def test_wrong_source_project_bounds_unknown_fields_and_duplicate_target_reject(self):
        for change in [dict(source_shot_id='foreign-project'),dict(motion_revision=999),dict(end=3.1),dict(offset_x=1921),dict(offset_y=float('nan')),dict(clip_index=True)]:
            run=self.post('production_run',song='A')['run']['id']
            code,result=self.f.action('production_tool',song='A',run=run,call=dict(id=uuid.uuid4().hex,name='propose_timeline_changes',arguments=self.args([self.command(**change)]),complete=True))
            if code==200:self.assertIn(result['tool']['status'],{'blocked','invalid_arguments'},change)
            else:self.assertEqual(code,400,result)
        self.post('project',name='B',era='default',story=0);self.post('shot',song='B',shot='foreign',description='another project')
        source=production_context.shot_id(self.f.state()['projects']['B'],'foreign')
        run=self.post('production_run',song='A')['run']['id']
        code,_=self.f.action('production_tool',song='A',run=run,call=dict(id=uuid.uuid4().hex,name='propose_timeline_changes',arguments=self.args([self.command(source_shot_id=source)]),complete=True))
        self.assertEqual(code,400)
        result,_=self.tool(self.args([self.command(),dict(op='clear_motion_overlay',clip_index=0)]));self.assertEqual(result['status'],'invalid_arguments')
        bad=self.command();bad['path']='/tmp/no'
        result,_=self.tool(self.args([bad]));self.assertEqual(result['status'],'invalid_arguments')
        result,_=self.tool(self.args([self.command(),dict(op='remove_clips',clip_indices=[0])]))
        self.assertEqual(result['status'],'blocked')

    def test_stale_rights_and_source_bytes_revalidated_before_human_apply(self):
        result,_=self.tool(self.args())
        self.post('timeline',song='A',timeline=editing.current(self.project()))
        self.assertEqual(self.f.action('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')[0],409)
        result,_=self.tool(self.args());take=self.project()['shots']['s']['takes'][0]
        self.post('asset_rights',sha256=take['sha256'],blocked=True,reason='synthetic hold')
        self.assertEqual(self.f.action('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=self.project()['timeline_head'],decision='approved')[0],400)
        self.post('asset_rights',sha256=take['sha256'],blocked=False,reason='synthetic restore')
        result,_=self.tool(self.args())
        Path(take['asset']).write_bytes(b'controlled corrupted fixture')
        self.assertEqual(self.f.action('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=self.project()['timeline_head'],decision='approved')[0],400)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'media tools required')
    def test_selected_anthropic_synthetic_protocol_to_preview_actual_render_and_reopen(self):
        lookup,preview,_=self.chat_tool('search_project_context',dict(query='current approved motion sources'))
        self.assertEqual(preview['message_body']['model'],'claude-haiku-5-5')
        source=lookup['execution_targets']['motion_overlay_sources']['items'][0]
        command=self.command(source_shot_id=source['source_shot_id'],motion_revision=source['motion_revision'])
        result,manifest,_=self.chat_tool('propose_timeline_changes',self.args([command]))
        self.assertEqual(result['status'],'proposed')
        self.assertIn('set_motion_overlay',json.dumps(manifest['message_body']['tools']))
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
        raw=self.f.http.store.timeline_preview('A',2,0,24);self.assertTrue(raw.startswith(b'\x89PNG'))
        self.post('approve_timeline',song='A');job=self.post('render_job',song='A')['job']
        self.assertTrue(self.f.http.store.process_next())
        final=next(x for x in self.f.state()['jobs'] if x['id']==job)
        self.assertEqual(final['status'],'completed',final.get('error'))
        self.assertEqual(final['snapshot']['shots']['0']['motion_overlay']['motion_revision'],1)
        from app import Store
        reopened=Store(self.f.tmp.name).state()
        self.assertEqual(reopened['jobs'][0]['sha256'],hashlib.sha256((self.f.http.store.root/'exports'/(job+'.mp4')).read_bytes()).hexdigest())
        self.assertFalse(self.project()['general_chat_turns'][-1]['billing_confirmed'])


if __name__=='__main__':unittest.main()
