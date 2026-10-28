"""General chat motion tools using isolated HTTP, SQLite, and local rendering."""
import hashlib
import json
import shutil
import subprocess
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import chat_general
import production_context
from app import Store
from tests import test_chat_general_http as base
from tests.test_chat_runtime import response, use
from tests.test_motion import scene


class GeneralChatMotionTest(unittest.TestCase):
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.post('shot', song='A', shot='s', description='synthetic motion')

    def post(self, action, **data):
        status, result = self.f.action(action, **data)
        self.assertEqual(status, 200, result)
        return result

    def project(self):
        return self.f.state()['projects']['A']

    def shot_id(self):
        return production_context.shot_id(self.project(), 's')

    def motion_scene(self):
        value = scene()
        value['frame_count'] = 72
        for layer in value['layers']:
            layer['out_frame'] = 72
        value['layers'][0]['text'] = '새로운 리듬 BEAT'
        value['layers'][2]['keyframes'].append(dict(frame=71,x=700,y=680,opacity=1,easing='linear'))
        return value

    def send_tool(self, name, args):
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('motion-call', name, args)], 'tool_use'), response()]
        preview = self.f.preview()
        status, result = self.f.approve(preview)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        project = self.project()
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
        return preview, project['general_chat_previews'][-1]

    def complete_follow(self, follow):
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'], 'completed')

    def test_tool_scope_is_exact_and_old_preview_cannot_execute_new_tool(self):
        transport = self.f.http.store.general_chat_runtime.transport
        args = dict(shot_id=self.shot_id(), base_motion_revision=0, scene=self.motion_scene())
        old_scope = tuple(x for x in chat_general.ALLOWED_TOOLS if x not in {'propose_motion_scene', 'request_motion_render'})
        with patch.object(chat_general, 'ALLOWED_TOOLS', old_scope):
            old = self.f.preview()
        self.assertNotIn('propose_motion_scene', old['tool_scope'])
        transport.responses = [response([use('motion-call', 'propose_motion_scene', args)], 'tool_use')]
        status, result = self.f.approve(old)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertFalse(self.project().get('motion_proposals'))
        self.assertEqual(self.f.state()['jobs'], [])
        self.assertEqual(len(transport.messages), 1)
        turn = self.project()['general_chat_turns'][-1]
        self.assertEqual(turn['status'], 'outcome_unknown')

    def test_new_preview_names_both_tools_and_binds_manifest(self):
        fresh = self.f.preview()
        self.assertTrue({'propose_motion_scene','request_motion_render'}.issubset(fresh['tool_scope']))
        self.assertEqual({x['name'] for x in fresh['message_body']['tools']}, set(fresh['tool_scope']))
        with self.f.http.store.connect() as c:changed = chat_general.get_row(c, 'general_chat_previews', fresh['id'])
        changed['tool_scope'].remove('request_motion_render')
        self.assertNotEqual(chat_general.manifest_digest(changed), fresh['manifest_sha256'])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'media tools required')
    def test_proposal_review_render_and_edit_are_separate(self):
        value = self.motion_scene()
        args = dict(shot_id=self.shot_id(), base_motion_revision=0, scene=value)
        first, follow = self.send_tool('propose_motion_scene', args)
        transport = self.f.http.store.general_chat_runtime.transport
        project = self.project(); proposal = project['motion_proposals'][0]
        self.assertEqual(proposal['status'], 'proposed')
        self.assertEqual(proposal['scene'], value)
        self.assertNotIn('motion_head', project['shots']['s'])
        self.assertEqual(self.f.state()['jobs'], [])
        self.assertEqual(len(transport.messages), 1)
        self.assertIn('motion-call', json.dumps(follow['message_body']))
        status, _ = self.f.approve(follow, rights=False)
        self.assertEqual(status, 400)
        self.assertEqual(len(transport.messages), 1)
        self.complete_follow(follow)

        self.post('motion_review', song='A', proposal_id=proposal['id'], decision='approved')
        version = deepcopy(self.project()['shots']['s']['motion_versions'][-1])
        bad = dict(shot_id=self.shot_id(), motion_revision=1, grant_id='invalid-grant')
        _, follow = self.send_tool('request_motion_render', bad)
        self.assertEqual(self.f.state()['jobs'], [])
        self.assertIn('blocked', json.dumps(follow['message_body']))
        self.complete_follow(follow)
        valid = dict(shot_id=self.shot_id(), motion_revision=1, grant_id=version['approval']['id'])
        _, follow = self.send_tool('request_motion_render', valid)
        queued = self.f.state()['jobs'][-1]
        self.assertEqual((queued['kind'], queued['status']), ('local-motion','queued'))
        self.complete_follow(follow)
        self.assertTrue(self.f.http.store.process_next())
        job = self.f.state()['jobs'][-1]
        self.assertEqual(job['status'], 'completed', job.get('error'))
        self.assertEqual(job['verified']['frames'], 72)
        take = self.project()['shots']['s']['takes'][-1]
        self.assertIsNone(self.project()['shots']['s']['selected'])
        self.assertEqual(take['rights'], '사용권 미확인')
        output = Path(take['asset'])
        self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), job['sha256'])
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames','-of','json',str(output)]))
        stream = probe['streams'][0]
        self.assertEqual((stream['width'],stream['height'],int(stream['nb_read_frames'])), (1920,1080,72))
        def frame(number):
            return subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-vf',f'select=eq(n\\,{number})','-frames:v','1','-f','image2pipe','-vcodec','png','-'])
        self.assertNotEqual(frame(0),frame(36),'the animated circle must change the rendered frame')
        self.assertEqual(Store(self.f.tmp.name).state()['jobs'][-1]['sha256'], job['sha256'])
        changed = deepcopy(value)
        changed['layers'][2]['in_frame'] = 12
        changed['layers'][2]['keyframes'][0]['frame'] = 12
        _, follow = self.send_tool('propose_motion_scene', dict(shot_id=self.shot_id(), base_motion_revision=1, scene=changed))
        latest = self.project()['motion_proposals'][-1]
        self.assertEqual(latest['scene']['layers'][:2], value['layers'][:2])
        self.assertEqual(self.project()['shots']['s']['motion_versions'][0], version)
        self.assertEqual(latest['status'], 'proposed')
        self.assertEqual(len(self.f.state()['jobs']), 1)

    def test_cancelled_turn_never_executes_motion_tool(self):
        args = dict(shot_id=self.shot_id(), base_motion_revision=0, scene=self.motion_scene())
        self.f.http.store.general_chat_runtime.transport.responses = [response([use('motion-call','propose_motion_scene',args)],'tool_use')]
        first = self.f.preview(); status, result = self.f.approve(first)
        self.assertEqual(status, 200, result)
        identifier = result['turn']['id']; ready = threading.Event(); resume = threading.Event()
        original = self.f.http.store.mutate
        def pause_tool(request):
            if request['action'] == 'production_tool':
                ready.set()
                if not resume.wait(10): raise TimeoutError('fixture synchronization')
                state=self.f.state();session=state['projects']['A']['active_conversation']
                request['revision']=state['revision'];request['conversation_revision']=session['revision'];request['shared_version']=session['shared_version']
            return original(request)
        with patch.object(self.f.http.store, 'mutate', side_effect=pause_tool):
            worker = threading.Thread(target=self.f.http.store.general_chat_runtime.process_next); worker.start()
            try:
                self.assertTrue(ready.wait(10))
                self.post('general_chat_cancel', song='A', turn=identifier)
            finally:
                resume.set(); worker.join(10)
            self.assertFalse(worker.is_alive())
        self.assertFalse(self.project().get('motion_proposals'))
        self.assertEqual(self.f.state()['jobs'], [])

    def test_changed_font_blocks_general_chat_motion_render(self):
        args=dict(shot_id=self.shot_id(),base_motion_revision=0,scene=self.motion_scene())
        proposed=self.post('motion_propose',song='A',**args)['motion']['proposal_id']
        with patch('motion_renderer.validate_text',return_value={}):
            self.post('motion_review',song='A',proposal_id=proposed,decision='approved')
        grant=self.project()['shots']['s']['motion_versions'][0]['approval']['id']
        with patch('motion_renderer.font_manifest',return_value={'changed':True}):
            _,follow=self.send_tool('request_motion_render',dict(shot_id=self.shot_id(),motion_revision=1,grant_id=grant))
        self.assertIn('blocked',json.dumps(follow['message_body']))
        self.assertEqual(self.f.state()['jobs'],[])

    def test_nondefault_grant_ownership_legacy_repair_and_cross_conversation(self):
        status, created = self.f.action('conversation_create', song='A', title='first')
        self.assertEqual(status, 200, created); cid = created['conversation']['id']
        status, created = self.f.session_action(cid, 'motion_propose', song='A', shot_id=self.shot_id(), base_motion_revision=0, scene=self.motion_scene())
        self.assertEqual(status, 200, created); proposal = created['motion']['proposal_id']
        with patch('motion_renderer.validate_text', return_value={}):
            status, result = self.f.session_action(cid, 'motion_review', song='A', proposal_id=proposal, decision='approved')
        self.assertEqual(status, 200, result)
        project = self.f.session_state(cid)['projects']['A']; version = project['shots']['s']['motion_versions'][0]
        grant = version['approval']['id']
        with self.f.http.store.connect() as c:
            revision, raw = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(raw); owners = state['projects']['A']['conversation_owners']
            self.assertEqual(owners[grant]['conversation_id'], cid)
            # Simulate an existing approved record created before owner registration.
            del owners[grant]
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
        status,handoff=self.f.action('model_handoff',song='A')
        self.assertEqual(status,200,handoff);self.assertNotIn(grant,json.dumps(handoff))
        default_shot=self.f.state()['projects']['A']['shots']['s']
        self.assertFalse(default_shot['motion_grant_available']);self.assertIsNone(default_shot['motion_versions'][0]['approval']['id'])
        status,_=self.f.action('motion_render',song='A',shot_id=self.shot_id(),motion_revision=1,grant_id=grant)
        self.assertEqual(status,400)
        status, result = self.f.session_action(cid, 'motion_review', song='A', proposal_id=proposal, decision='approved')
        self.assertEqual(status, 200, result)
        with self.f.http.store.connect() as c:
            state = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]); owners = state['projects']['A']['conversation_owners']
            self.assertEqual(owners[grant]['conversation_id'], cid)
        status, result = self.f.session_action(cid, 'motion_render', song='A', shot_id=self.shot_id(), motion_revision=1, grant_id=grant)
        self.assertEqual(status, 200, result)
        self.assertEqual(result['motion']['state'], 'queued')
        status, result = self.f.session_action(cid, 'motion_render', song='A', shot_id=self.shot_id(), motion_revision=1, grant_id=grant)
        self.assertEqual(status, 200, result)
        self.assertEqual(len(self.f.session_state(cid)['jobs']), 1)
        status, created = self.f.action('conversation_create', song='A', title='other')
        self.assertEqual(status, 200, created); other = created['conversation']['id']
        status, _ = self.f.session_action(other, 'motion_render', song='A', shot_id=self.shot_id(), motion_revision=1, grant_id=grant)
        self.assertEqual(status, 400)
        other_shot=self.f.session_state(other)['projects']['A']['shots']['s']
        self.assertFalse(other_shot['motion_grant_available']);self.assertIsNone(other_shot['motion_versions'][0]['approval']['id'])
        self.assertTrue(self.f.session_state(cid)['projects']['A']['shots']['s']['motion_grant_available'])
        status, _ = self.f.session_action(cid, 'motion_render', song='A', shot_id=self.shot_id(), motion_revision=2, grant_id=grant)
        self.assertEqual(status, 409)

    def test_nondefault_general_chat_uses_only_its_approved_motion_grant(self):
        status, created=self.f.action('conversation_create',song='A',title='motion chat')
        self.assertEqual(status,200,created);cid=created['conversation']['id']
        transport=self.f.http.store.general_chat_runtime.transport
        args=dict(shot_id=self.shot_id(),base_motion_revision=0,scene=self.motion_scene())
        def request_tool(conversation,name,arguments):
            transport.responses=[response([use('call',name,arguments)],'tool_use'),response()]
            status, result=self.f.session_action(conversation,'general_chat_preview',song='A',prompt='합성 모션',maximum_micro=10000)
            self.assertEqual(status,200,result);preview=result['general_chat_preview']
            status,result=self.f.session_action(conversation,'general_chat_decide',song='A',preview_id=preview['id'],manifest_sha256=preview['manifest_sha256'],decision='approve',rights_confirmed=True)
            self.assertEqual(status,200,result);self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
            return self.f.session_state(conversation)['projects']['A']
        project=request_tool(cid,'propose_motion_scene',args)
        self.assertEqual(project['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        self.assertEqual(len(project['motion_proposals']),1)
        follow=project['general_chat_previews'][-1]
        status,result=self.f.session_action(cid,'general_chat_decide',song='A',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='reject',rights_confirmed=True)
        self.assertEqual(status,200,result)
        with patch('motion_renderer.validate_text',return_value={}):
            status,result=self.f.session_action(cid,'motion_review',song='A',proposal_id=project['motion_proposals'][0]['id'],decision='approved')
        self.assertEqual(status,200,result)
        project=self.f.session_state(cid)['projects']['A'];grant=project['shots']['s']['motion_versions'][0]['approval']['id']
        project=request_tool(cid,'search_project_context',{'query':'current motion'})
        follow=project['general_chat_previews'][-1];self.assertIn(grant,json.dumps(follow['message_body']))
        status,result=self.f.session_action(cid,'general_chat_decide',song='A',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='reject',rights_confirmed=True)
        self.assertEqual(status,200,result)
        project=request_tool(cid,'request_motion_render',dict(shot_id=self.shot_id(),motion_revision=1,grant_id=grant))
        self.assertEqual(project['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        self.assertEqual(len(self.f.session_state(cid)['jobs']),1)
        status,created=self.f.action('conversation_create',song='A',title='other')
        self.assertEqual(status,200,created);other=created['conversation']['id']
        status,handoff=self.f.session_action(other,'model_handoff',song='A')
        self.assertEqual(status,200,handoff);self.assertNotIn(grant,json.dumps(handoff))
        project=request_tool(other,'search_project_context',{'query':'current motion'})
        follow=project['general_chat_previews'][-1];self.assertNotIn(grant,json.dumps(follow['message_body']))
        status,result=self.f.session_action(other,'general_chat_decide',song='A',preview_id=follow['id'],manifest_sha256=follow['manifest_sha256'],decision='reject',rights_confirmed=True)
        self.assertEqual(status,200,result)
        project=request_tool(other,'request_motion_render',dict(shot_id=self.shot_id(),motion_revision=1,grant_id=grant))
        turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['usage'],{'input_tokens':100,'output_tokens':100})
        self.assertFalse(turn['billing_confirmed'])
        self.assertEqual(self.f.session_state(other)['jobs'],[])
        with self.f.http.store.connect() as c:
            stored=chat_general.get_row(c,'general_chat_turns',turn['id'])
            reservation=c.execute('SELECT state,actual FROM reservations WHERE id=?',(stored['reservation'],)).fetchone()
            self.assertEqual(reservation[0],'settled');self.assertGreater(reservation[1],0)
            self.assertEqual(c.execute("SELECT state FROM provider_attempts WHERE job=? AND operation='chat-message'",(turn['id'],)).fetchone()[0],'observed')

    def test_legacy_repair_rejects_ambiguous_or_foreign_ownership(self):
        status, created = self.f.action('conversation_create', song='A', title='first')
        self.assertEqual(status, 200, created); cid = created['conversation']['id']
        status, created = self.f.session_action(cid, 'motion_propose', song='A', shot_id=self.shot_id(), base_motion_revision=0, scene=self.motion_scene())
        self.assertEqual(status, 200, created); proposal = created['motion']['proposal_id']
        with patch('motion_renderer.validate_text', return_value={}):
            status, result = self.f.session_action(cid, 'motion_review', song='A', proposal_id=proposal, decision='approved')
        self.assertEqual(status, 200, result)
        grant = self.f.session_state(cid)['projects']['A']['shots']['s']['motion_versions'][0]['approval']['id']
        with self.f.http.store.connect() as c:
            revision, raw = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(raw); project = state['projects']['A']; del project['conversation_owners'][grant]
            item = next(x for x in project['motion_proposals'] if x['id']==proposal)
            item['scene']['layers'][0]['text']='다른 증거'
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
        status, _ = self.f.session_action(cid, 'motion_review', song='A', proposal_id=proposal, decision='approved')
        self.assertEqual(status, 400)
        with self.f.http.store.connect() as c:
            revision, raw = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state=json.loads(raw); project=state['projects']['A']
            self.assertNotIn(grant,project['conversation_owners'])
            item=next(x for x in project['motion_proposals'] if x['id']==proposal)
            item['scene']=deepcopy(project['shots']['s']['motion_versions'][0]['scene'])
            project['conversation_owners'][grant]={'conversation_id':'foreign','kind':'motion_grants'}
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
        status, _ = self.f.session_action(cid, 'motion_review', song='A', proposal_id=proposal, decision='approved')
        self.assertEqual(status,400)
        with self.f.http.store.connect() as c:
            state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            self.assertEqual(state['projects']['A']['conversation_owners'][grant]['conversation_id'],'foreign')

    def test_existing_restore_workflow_creates_new_owned_grant_without_reassigning_old(self):
        status, created=self.f.action('conversation_create',song='A',title='motion owner')
        self.assertEqual(status,200,created);cid=created['conversation']['id']
        status, created=self.f.session_action(cid,'motion_propose',song='A',shot_id=self.shot_id(),base_motion_revision=0,scene=self.motion_scene())
        self.assertEqual(status,200,created)
        with patch('motion_renderer.validate_text',return_value={}):
            status,result=self.f.session_action(cid,'motion_review',song='A',proposal_id=created['motion']['proposal_id'],decision='approved')
        self.assertEqual(status,200,result)
        project=self.f.session_state(cid)['projects']['A'];old=project['shots']['s']['motion_versions'][0]['approval']['id']
        with self.f.http.store.connect() as c:
            revision,raw=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();state=json.loads(raw)
            del state['projects']['A']['conversation_owners'][old]
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
        status,result=self.f.session_action(cid,'motion_restore',song='A',shot_id=self.shot_id(),base_motion_revision=1,version=1)
        self.assertEqual(status,200,result);self.assertFalse(result['motion']['applied'])
        with patch('motion_renderer.validate_text',return_value={}):
            status,result=self.f.session_action(cid,'motion_review',song='A',proposal_id=result['motion']['proposal_id'],decision='approved')
        self.assertEqual(status,200,result)
        project=self.f.session_state(cid)['projects']['A'];new=project['shots']['s']['motion_versions'][1]['approval']['id']
        self.assertNotEqual(new,old);self.assertEqual(project['shots']['s']['motion_head'],2)
        status,result=self.f.session_action(cid,'motion_render',song='A',shot_id=self.shot_id(),motion_revision=2,grant_id=new)
        self.assertEqual(status,200,result);self.assertEqual(result['motion']['state'],'queued')
        with self.f.http.store.connect() as c:
            state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);owners=state['projects']['A']['conversation_owners']
            self.assertNotIn(old,owners);self.assertEqual(owners[new]['conversation_id'],cid)

    def test_unambiguous_default_legacy_motion_grant_remains_usable(self):
        status,created=self.f.action('motion_propose',song='A',shot_id=self.shot_id(),base_motion_revision=0,scene=self.motion_scene())
        self.assertEqual(status,200,created);proposal=created['motion']['proposal_id']
        with patch('motion_renderer.validate_text',return_value={}):
            status,result=self.f.action('motion_review',song='A',proposal_id=proposal,decision='approved')
        self.assertEqual(status,200,result)
        grant=self.project()['shots']['s']['motion_versions'][0]['approval']['id']
        with self.f.http.store.connect() as c:
            revision,raw=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();state=json.loads(raw);project=state['projects']['A']
            project['conversation_owners'].pop(grant);project['conversation_owners'].pop(proposal)
            next(x for x in project['motion_proposals'] if x['id']==proposal).pop('conversation_id')
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
        self.assertTrue(self.project()['shots']['s']['motion_grant_available'])
        status,result=self.f.action('motion_render',song='A',shot_id=self.shot_id(),motion_revision=1,grant_id=grant)
        self.assertEqual(status,200,result);self.assertEqual(result['motion']['state'],'queued')


if __name__ == '__main__':
    unittest.main()
