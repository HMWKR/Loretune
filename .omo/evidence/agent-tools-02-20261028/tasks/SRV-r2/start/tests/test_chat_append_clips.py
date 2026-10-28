"""Append existing, visible Takes to a proposed timeline without granting approval."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import chat_models
import chat_protocols
import editing
import production_context
import production_tools
from tests import test_local_creation_tools as fixtures
from tests import test_timeline_repeated_http as repeated_fixture
from tests import test_chat_sessions as conversation_fixture
from tests import test_chat_general_http as general_fixture
from tests.test_chat_runtime import response,use


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class AppendClipsTest(unittest.TestCase):
    setUp=fixtures.LocalToolsTest.setUp
    call=fixtures.LocalToolsTest.call
    project=fixtures.LocalToolsTest.project
    tool=fixtures.LocalToolsTest.tool

    def add_source(self):
        path=Path(self.fixture.temp.name)/'separate-blue.png'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64','-frames:v','1',str(path)],check=True)
        self.call('shot',shot='extra',description='별도 장면')
        self.call('take',shot='extra',shot_revision=0,filename='blue.png',content=base64.b64encode(path.read_bytes()).decode(),reason='합성',rights='직접 제작')
        return dict(source_shot_id=production_context.shot_id(self.project(),'extra'),source_take_id=1,trim=0,duration=1)

    def propose(self,clip,commands=None):
        return self.tool('propose_timeline_changes',dict(description='별도 컷 추가',timeline_version=self.project()['timeline_head'],commands=commands or [dict(op='append_clips',clips=[clip])]))[0]

    def test_provider_schemas_snapshot_diff_and_human_approval(self):
        clip=self.add_source();before=deepcopy(self.project())
        for provider in ('anthropic','openai','xai'):
            definition=next(x for x in chat_protocols.tool_definitions(provider) if x['name']=='propose_timeline_changes')
            schema=definition['input_schema'] if provider=='anthropic' else definition['parameters']
            self.assertEqual(sum(x['properties']['op']['enum']==['append_clips'] for x in schema['properties']['commands']['items']['anyOf']),1)
            args=dict(description='기존 영상 추가',timeline_version=before['timeline_head'],commands=[dict(op='append_clips',clips=[clip,clip])])
            result,_=self.tool('propose_timeline_changes',args,provider)
            self.assertEqual(result['status'],'proposed');self.assertFalse(result['applied'])
        self.assertIn('append_clips',chat_models.SYSTEM)
        diff=result['timeline_diff'];self.assertEqual([x['proposed_clip_index'] for x in diff['added_clips']],[2,3]);self.assertEqual([x['after']['shot'] for x in diff['added_clips']],['extra','extra'])
        after=self.project();self.assertEqual(after['timeline_versions'],before['timeline_versions']);self.assertEqual(after['shots'],before['shots']);self.assertEqual(after['audio_versions'],before['audio_versions'])
        proposal=after['timeline_edit_proposals'][-1]
        self.assertEqual(proposal['added_sources'][0]['sha256'],after['shots']['extra']['takes'][0]['sha256'])
        self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=before['timeline_head'],decision='approved')
        self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=before['timeline_head'],decision='approved')
        new=self.project()['timeline_versions'][-1];self.assertEqual([x['shot'] for x in new['clips']],['a','b','extra','extra']);self.assertNotIn('approval',new)
        self.assertEqual(len(self.project()['timeline_versions']),len(before['timeline_versions'])+1);self.assertEqual(self.project()['shots'],before['shots'])

    def test_bad_fields_combinations_and_thirty_cut_limit(self):
        clip=self.add_source()
        for bad in ([],[{}],[dict(clip,source_take_id=True)],[dict(clip,trim=-1)],[dict(clip,duration=0)],[dict(clip,source_shot_id=[])],[dict(clip,url='http://invalid')]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                production_tools.validate('propose_timeline_changes',dict(description='invalid',timeline_version=1,commands=[dict(op='append_clips',clips=bad)]))
        for commands in ([dict(op='append_clips',clips=[clip]),dict(op='remove_clips',clip_indices=[0])],
                         [dict(op='append_clips',clips=[clip]),dict(op='reorder_clips',order=[1,0])],
                         [dict(op='append_clips',clips=[clip]*29)]):
            result=self.propose(clip,commands);self.assertEqual(result['status'],'blocked')
        for bad in (dict(clip,source_take_id=999),dict(clip,source_shot_id='foreign-project-shot')):
            try:result=self.propose(bad);self.assertEqual(result['status'],'blocked')
            except ValueError:pass

    def test_source_change_rights_and_bytes_block_after_proposal(self):
        clip=self.add_source();result=self.propose(clip);p=self.project();take=p['shots']['extra']['takes'][0]
        self.call('asset_rights',sha256=take['sha256'],blocked=True,reason='사용 중지')
        with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=p['timeline_head'],decision='approved')
        self.assertEqual(self.project()['timeline_head'],p['timeline_head'])
        self.call('asset_rights',sha256=take['sha256'],blocked=False,reason='사용 재개')
        Path(take['asset']).write_bytes(b'changed fixture')
        with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=p['timeline_head'],decision='approved')
        self.assertEqual(self.project()['timeline_head'],p['timeline_head'])

    def test_twenty_nine_to_thirty_clips_succeeds_but_thirty_one_fails(self):
        clip=self.add_source();timeline=editing.current(self.project())
        timeline['clips']=[deepcopy(timeline['clips'][0]) for _ in range(29)]
        self.call('timeline',timeline=timeline)
        one=self.propose(clip);self.assertEqual(one['status'],'proposed');self.assertEqual(one['timeline_diff']['added_clips'][0]['proposed_clip_index'],29)
        two=self.propose(clip,[dict(op='append_clips',clips=[clip,clip])]);self.assertEqual(two['status'],'blocked')
        self.assertEqual(len(editing.current(self.project())['clips']),29)

    def test_symlinked_source_is_not_accepted_on_review(self):
        clip=self.add_source();result=self.propose(clip);p=self.project()
        asset=Path(p['shots']['extra']['takes'][0]['asset']);asset.unlink();asset.symlink_to(self.fixture.img)
        with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=p['timeline_head'],decision='approved')
        self.assertEqual(self.project()['timeline_head'],p['timeline_head'])

    def test_new_source_revision_stales_but_unrelated_shot_does_not(self):
        clip=self.add_source();result=self.propose(clip);p=self.project()
        self.call('shot',shot='unrelated',description='관련 없는 장면')
        self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=p['timeline_head'],decision='approved')
        self.assertEqual(self.project()['timeline_head'],p['timeline_head']+1)
        result=self.propose(clip);p=self.project();take=p['shots']['extra']['takes'][0]
        self.call('take',shot='extra',shot_revision=p['shots']['extra']['revision'],filename='again.png',content=base64.b64encode(Path(take['asset']).read_bytes()).decode(),reason='new candidate',rights='직접 제작')
        with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=p['timeline_head'],decision='approved')
        self.assertEqual(self.project()['timeline_head'],p['timeline_head'])


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class AppendClipsHTTPTest(unittest.TestCase):
    setUp=repeated_fixture.RepeatedTimelineHTTPTest.setUp
    close_server=repeated_fixture.RepeatedTimelineHTTPTest.close_server
    get_state=repeated_fixture.RepeatedTimelineHTTPTest.get_state
    project=repeated_fixture.RepeatedTimelineHTTPTest.project
    request=repeated_fixture.RepeatedTimelineHTTPTest.request
    post=repeated_fixture.RepeatedTimelineHTTPTest.post
    select=repeated_fixture.RepeatedTimelineHTTPTest.select
    timeline=repeated_fixture.RepeatedTimelineHTTPTest.timeline

    def test_http_model_receipts_for_invisible_and_malformed_sources(self):
        def session_state(cid):
            with urlopen(self.base+'/api/state?'+urlencode({'song':'A','conversation':cid})) as response:return json.load(response)
        def session_request(cid,action,data):
            state=session_state(cid);active=state['projects']['A']['active_conversation']
            body=dict(action=action,data=dict(song='A',**data),revision=state['revision'],request_id=uuid.uuid4().hex,conversation_id=cid,conversation_revision=active['revision'],shared_version=active['shared_version'])
            req=Request(self.base+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':state['token']})
            try:
                with urlopen(req) as response:return response.status,json.load(response)
            except HTTPError as exc:
                with exc:return exc.code,json.load(exc)
        default=self.project()['active_conversation']['id']
        other=self.post('conversation_create',song='A',title='다른 대화')['conversation']['id']
        shot=session_state(other)['projects']['A']['shots']['s']
        status,_=session_request(other,'take',dict(shot='s',shot_revision=shot['revision'],filename='other.png',content=self.images[0],reason='다른 대화',rights='직접 제작'))
        self.assertEqual(status,200)
        self.post('timeline',song='A',timeline=self.timeline())
        project=self.project();shot_id=production_context.shot_id(project,'s')
        run=self.post('production_run',song='A')['run']['id']
        def call(identifier,clip):
            return dict(id=identifier,name='propose_timeline_changes',arguments=dict(description='추가',timeline_version=1,commands=[dict(op='append_clips',clips=[clip])]),complete=True)
        hidden=dict(source_shot_id=shot_id,source_take_id=3,trim=0,duration=1)
        for identifier,clip in (('hidden',hidden),('missing',dict(hidden,source_shot_id='missing-shot'))):
            status,value=session_request(default,'production_tool',dict(run=run,call=call(identifier,clip)))
            self.assertEqual(status,200);self.assertEqual(value['tool']['status'],'blocked')
        status,value=session_request(default,'production_tool',dict(run=run,call=call('bad-type',dict(hidden,source_shot_id=[]))))
        self.assertEqual(status,200);self.assertEqual(value['tool']['status'],'invalid_arguments')
        status,_=session_request(default,'production_tool',dict(run=run,call=call('nested-hidden',dict(hidden,source_shot_id=[dict(shot='s',take=3)]))))
        self.assertEqual(status,400)
        # Extra hidden references and other tools retain the preflight guard.
        status,_=session_request(default,'production_tool',dict(run=run,call=call('extra',dict(hidden,shot='s',take=3))))
        self.assertEqual(status,400)
        unrelated=dict(id='other-tool',name='prepare_image_action',arguments=dict(wrapper=dict(op='append_clips',clips=[hidden])),complete=True)
        status,_=session_request(default,'production_tool',dict(run=run,call=unrelated));self.assertEqual(status,400)
        self.assertEqual(self.project()['timeline_head'],1)

    def test_http_approval_render_audio_caption_restart_and_restore(self):
        audio=Path(self.tmp.name)/'audio.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=6',str(audio)],check=True)
        self.post('audio',song='A',filename='audio.wav',content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 제작')
        self.post('shot',song='A',shot='extra',description='파란 장면')
        self.post('take',song='A',shot='extra',shot_revision=0,filename='blue.png',content=self.images[1],reason='합성',rights='직접 제작')
        self.post('review_take',song='A',shot='extra',take=1,decision='approved',reason='합성 검토')
        base=self.timeline();base['audio']=1;base['subtitles']=[dict(start=0,end=1,text='테스트 자막')]
        self.post('timeline',song='A',timeline=base)
        before=deepcopy(self.project());shot_id=production_context.shot_id(before,'extra')
        clips=[dict(source_shot_id=shot_id,source_take_id=1,trim=0,duration=1),dict(source_shot_id=production_context.shot_id(before,'s'),source_take_id=1,trim=0,duration=1)]
        run=self.post('production_run',song='A')['run']['id']
        call=dict(id='append-clip',name='propose_timeline_changes',arguments=dict(description='기존 컷 둘 추가',timeline_version=1,commands=[dict(op='append_clips',clips=clips)]),complete=True)
        result=self.post('production_tool',song='A',run=run,call=call)['tool'];self.assertEqual(result['status'],'proposed')
        self.assertEqual([x['proposed_clip_index'] for x in result['timeline_diff']['added_clips']],[2,3]);self.assertEqual(self.project()['timeline_versions'],before['timeline_versions'])
        unauthorized=dict(action='review_timeline_proposal',data=dict(song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved'),revision=self.get_state()['revision'],request_id=uuid.uuid4().hex)
        req=Request(self.base+'/api/action',data=json.dumps(unauthorized).encode(),headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as denied:urlopen(req)
        self.assertEqual(denied.exception.code,403);denied.exception.close()
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
        self.post('review_timeline_proposal',song='A',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
        after=self.project();new=after['timeline_versions'][-1];self.assertEqual(after['timeline_head'],2);self.assertEqual(len(after['timeline_versions']),2)
        self.assertEqual([(x['shot'],x['take']) for x in new['clips']],[('s',1),('s',2),('extra',1),('s',1)]);self.assertNotIn('approval',new)
        self.assertEqual(after['shots'],before['shots']);self.assertEqual(after['timeline_versions'][0],before['timeline_versions'][0])
        from app import Store
        self.assertEqual(Store(self.tmp.name).state()['projects']['A']['timeline_head'],2)
        self.post('approve_timeline',song='A');job=self.post('render_job',song='A')['job'];self.assertTrue(self.http.store.process_next())
        record=next(j for j in self.get_state()['jobs'] if j['id']==job);self.assertEqual(record['status'],'completed',record.get('error'))
        path=Path(self.tmp.name)/'exports'/(job+'.mp4');probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
        self.assertEqual({s['codec_type'] for s in probe['streams']},{'audio','video','subtitle'});self.assertAlmostEqual(float(probe['format']['duration']),4,places=2)
        def pixel(at):return subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1','-vf','crop=2:2:320:180,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-'])
        colors=[pixel(x) for x in (.5,1.5,2.5,3.5)];self.assertGreater(colors[0][0],180);self.assertGreater(colors[1][2],180);self.assertGreater(colors[2][2],180);self.assertGreater(colors[3][0],180)
        self.post('restore_timeline',song='A',version=1);restored=self.project()['timeline_versions'][-1]
        self.assertEqual(restored['clips'],before['timeline_versions'][0]['clips']);self.assertNotIn('approval',restored)


class AppendConversationScopeTest(unittest.TestCase):
    setUp=conversation_fixture.ConversationScopeTest.setUp
    request=conversation_fixture.ConversationScopeTest.request
    create_session=conversation_fixture.ConversationScopeTest.create_session

    def test_other_conversation_unapproved_and_revoked_take_never_applies(self):
        from image_adapter import SyntheticImageAdapter
        def mutate(action,data,conversation):return self.store.mutate(self.request(action,data,conversation))
        def p(conversation):return self.store.state({'A':conversation})['projects']['A']
        other=self.create_session()
        for name,cid,width in (('base',self.default,32),('other',other,33)):
            mutate('shot',{'shot':name,'description':'합성 장면'},cid)
            image=SyntheticImageAdapter().generate({'prompt':'synthetic','width':width,'height':32})['bytes']
            mutate('take',{'shot':name,'shot_revision':0,'filename':name+'.png','content':base64.b64encode(image).decode(),'reason':'합성','rights':'직접 제작'},cid)
        mutate('select',{'shot':'base','take':1,'shot_revision':1},self.default)
        base=editing.current(p(self.default));base['clips']=[base['clips'][0]]
        mutate('timeline',{'timeline':base},self.default)
        source=production_context.shot_id(p(self.default),'other')
        command=dict(op='append_clips',clips=[dict(source_shot_id=source,source_take_id=1,trim=0,duration=1)])
        run=mutate('production_run',{},self.default)['run']['id']
        call=dict(id='not-visible',name='propose_timeline_changes',arguments=dict(description='다른 대화의 후보',timeline_version=1,commands=[command]),complete=True)
        blocked=mutate('production_tool',{'run':run,'call':call},self.default)['tool'];self.assertEqual(blocked['status'],'blocked')
        missing=deepcopy(call);missing['id']='missing';missing['arguments']['commands'][0]['clips'][0]['source_shot_id']='missing-shot'
        self.assertEqual(mutate('production_tool',{'run':run,'call':missing},self.default)['tool']['status'],'blocked')
        mutate('review_take',{'shot':'other','take':1,'decision':'approved','reason':'검토'},other)
        run=mutate('production_run',{},self.default)['run']['id'];call['id']='shared'
        result=mutate('production_tool',{'run':run,'call':call},self.default)['tool'];self.assertEqual(result['status'],'proposed')
        mutate('review_take',{'shot':'other','take':1,'decision':'rejected','reason':'승인 철회'},other)
        with self.assertRaises(ValueError):mutate('review_timeline_proposal',{'proposal_id':result['proposal_id'],'timeline_version':1,'decision':'approved'},self.default)
        self.assertEqual(p(self.default)['timeline_head'],1)

    def test_legacy_and_typed_clip_changes_recheck_conversation_visibility(self):
        from image_adapter import SyntheticImageAdapter
        def mutate(action,data,conversation):return self.store.mutate(self.request(action,data,conversation))
        def p(conversation):return self.store.state({'A':conversation})['projects']['A']
        other=self.create_session();mutate('shot',{'shot':'base','description':'합성 장면'},self.default)
        for cid,width in ((self.default,32),(other,33)):
            image=SyntheticImageAdapter().generate({'prompt':'synthetic','width':width,'height':32})['bytes']
            shot=p(cid)['shots']['base'];mutate('take',{'shot':'base','shot_revision':shot['revision'],'filename':'clip.png','content':base64.b64encode(image).decode(),'reason':'합성','rights':'직접 제작'},cid)
        mutate('select',{'shot':'base','take':1,'shot_revision':p(self.default)['shots']['base']['revision']},self.default)
        mutate('timeline',{'timeline':editing.current(p(self.default))},self.default)
        change=dict(clip_index=0,take=2,trim=0,duration=1)
        def propose(cid,name,identifier):
            run=mutate('production_run',{},cid)['run']['id']
            args=dict(description='Take 변경',timeline_version=1)
            if name=='propose_timeline_edit':args['changes']=[change]
            else:args['commands']=[dict(op='set_clip',**change)]
            return mutate('production_tool',{'run':run,'call':dict(id=identifier,name=name,arguments=args,complete=True)},cid)['tool']
        for name in ('propose_timeline_edit','propose_timeline_changes'):
            self.assertEqual(propose(self.default,name,'hidden-'+name)['status'],'blocked')
            self.assertEqual(propose(other,name,'own-'+name)['status'],'proposed')
        mutate('review_take',{'shot':'base','take':2,'decision':'approved','reason':'공유 검토'},other)
        proposals=[propose(self.default,name,'shared-'+name) for name in ('propose_timeline_edit','propose_timeline_changes')]
        self.assertTrue(all(x['status']=='proposed' for x in proposals))
        mutate('review_take',{'shot':'base','take':2,'decision':'rejected','reason':'승인 철회'},other)
        for result in proposals:
            with self.assertRaises(ValueError):mutate('review_timeline_proposal',{'proposal_id':result['proposal_id'],'timeline_version':1,'decision':'approved'},self.default)
        self.assertEqual(p(self.default)['timeline_head'],1)


class AppendGeneralChatReceiptTest(unittest.TestCase):
    setUp=general_fixture.GeneralChatHTTPTest.setUp
    shutdown=general_fixture.GeneralChatHTTPTest.shutdown
    state=general_fixture.GeneralChatHTTPTest.state
    send=general_fixture.GeneralChatHTTPTest.send
    action=general_fixture.GeneralChatHTTPTest.action
    preview=general_fixture.GeneralChatHTTPTest.preview
    approve=general_fixture.GeneralChatHTTPTest.approve

    def check_result(self,source,expected):
        request=dict(description='존재 여부 확인',timeline_version=0,commands=[dict(op='append_clips',clips=[dict(source_shot_id=source,source_take_id=1,trim=0,duration=1)])])
        transport=self.http.store.general_chat_runtime.transport
        transport.responses=[response([use('append','propose_timeline_changes',request)],'tool_use'),response()]
        preview=self.preview();self.assertEqual(self.approve(preview)[0],200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(project.get('timeline_edit_proposals',[]),[])
        self.assertEqual(len(transport.messages),1)
        if expected=='invalid_arguments':
            # The existing protocol normalizer rejects malformed provider output
            # before it reaches the tool executor; no continuation is sent.
            self.assertEqual(turn['status'],'outcome_unknown');self.assertEqual(project['general_chat_previews'],[])
            self.assertFalse(turn['billing_confirmed']);self.assertFalse(self.http.store.general_chat_runtime.process_next())
        else:
            self.assertEqual(turn['status'],'awaiting_continuation_approval')
            follow=project['general_chat_previews'][-1]
            results=[json.loads(block['content']) for message in follow['message_body']['messages'] for block in message.get('content',[]) if isinstance(block,dict) and block.get('type')=='tool_result']
            self.assertEqual(results[-1]['status'],expected)

    def test_missing_source_returns_blocked_tool_receipt(self):self.check_result('missing-shot','blocked')
    def test_malformed_source_stops_at_provider_protocol_boundary(self):self.check_result([], 'invalid_arguments')


if __name__=='__main__':unittest.main()
