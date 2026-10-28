"""Actual local HTTP permission/effort settings; no real provider or keys."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from threading import Event,Thread
import unittest
from unittest.mock import patch
import uuid

import agent_preferences as preferences
import app
import chat_general
import chat_models
import editing
from tests import test_chat_general_http as base
from tests.test_chat_runtime import response,use


class AgentPreferencesTest(unittest.TestCase):
    def setUp(self):
        self.f=base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)

    def project(self):return self.f.state()['projects']['A']

    def post(self,action,**data):
        code,result=self.f.action(action,**data);self.assertEqual(code,200,result);return result

    def settings(self,mode='review',effort='low',selection='anthropic-haiku-5-5',cid=None):
        project=self.f.session_state(cid)['projects']['A'] if cid else self.project()
        current=project['agent_preferences']['by_model'][selection]
        data=dict(song='A',selection=selection,settings_revision=current['revision'],mode=mode,effort=effort)
        code,result=self.f.session_action(cid,'conversation_agent_settings',**data) if cid else self.f.action('conversation_agent_settings',**data)
        self.assertEqual(code,200,result);return result['agent_settings']

    def seed_timeline(self,repeat=False):
        self.post('shot',song='A',shot='s',description='synthetic media')
        self.post('take',song='A',shot='s',shot_revision=0,filename='base.png',
                  content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
                  reason='own fixture',rights='directly authored fixture')
        self.post('select',song='A',shot='s',take=1,shot_revision=1)
        self.post('review_take',song='A',shot='s',take=1,decision='approved',reason='checked')
        value=editing.current(self.project());value['profile']='preview';value['clips'][0]['duration']=1.5 if repeat else 3
        if repeat:value['clips']*=2
        self.post('timeline',song='A',timeline=value);self.post('approve_timeline',song='A')

    def args(self,commands=None):
        return dict(description='synthetic bounded edit',timeline_version=self.project()['timeline_head'],
                    commands=commands or [dict(op='set_clip',clip_index=0,take=1,trim=0,duration=2.5)])

    def direct_tool(self,name,args,run=None):
        run=run or self.post('production_run',song='A')['run']['id']
        result=self.post('production_tool',song='A',run=run,
                         call=dict(id=uuid.uuid4().hex,name=name,arguments=args,complete=True))['tool']
        return result,run

    def send_tool(self,name,args):
        transport=self.f.http.store.general_chat_runtime.transport
        transport.responses=[response([use('agent-tool',name,args)],'tool_use')]
        preview=self.f.preview();code,result=self.f.approve(preview);self.assertEqual(code,200,result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        p=self.project();turn=p['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'awaiting_continuation_approval',turn)
        follow=p['general_chat_previews'][-1]
        blocks=[b for message in follow['message_body']['messages'] if isinstance(message.get('content'),list)
                for b in message['content'] if b.get('type')=='tool_result']
        return json.loads(blocks[-1]['content']),preview,follow

    def reject_follow(self,follow):
        code,result=self.f.approve(follow,decision='reject');self.assertEqual(code,200,result)

    def test_actual_http_save_reload_per_model_and_stale_revision(self):
        value=self.settings('full_access','high');self.assertEqual(value['revision'],1)
        self.settings('read_only','xhigh','xai-grok-4-7')
        prefs=self.project()['agent_preferences'];self.assertEqual(prefs['current']['effort'],'high')
        self.assertEqual(prefs['by_model']['xai-grok-4-7']['mode'],'read_only')
        reopened=app.Store(self.f.tmp.name).state()['projects']['A']['agent_preferences']
        self.assertEqual(reopened['by_model'],prefs['by_model'])
        code,_=self.f.action('conversation_agent_settings',song='A',selection='anthropic-haiku-5-5',settings_revision=0,mode='review',effort='low')
        self.assertEqual(code,409)

    def test_conversation_isolation_shared_media_fingerprint_and_cas(self):
        cid=self.post('conversation_create',song='A',title='B')['conversation']['id']
        before=self.f.session_state(cid)['projects']['A']['active_conversation']['shared_version']
        self.settings('full_access','high')
        p=self.f.session_state(cid)['projects']['A'];self.assertEqual(p['agent_preferences']['current']['mode'],'review')
        self.assertEqual(p['active_conversation']['shared_version'],before)
        self.settings('read_only','medium',cid=cid)
        self.assertEqual(self.project()['agent_preferences']['current']['mode'],'full_access')

    def test_invalid_modes_efforts_fields_and_nonchat_models_rejected(self):
        before=self.project()['agent_preferences']['current']
        for change in [dict(mode='root'),dict(mode=True),dict(effort='xhigh'),dict(effort='max'),dict(effort='none'),
                       dict(selection='fal-kling-2-6-pro'),dict(selection='unknown'),dict(extra=True)]:
            data=dict(song='A',selection='anthropic-haiku-5-5',settings_revision=0,mode='review',effort='low');data.update(change)
            self.assertEqual(self.f.action('conversation_agent_settings',**data)[0],400,change)
        self.assertEqual(self.project()['agent_preferences']['current'],before)

    def test_vendor_effort_body_and_route_projection_are_not_unified(self):
        for effort in ['low','medium','high']:
            self.settings(effort=effort);preview=self.f.preview()
            self.assertEqual(preview['message_body']['output_config']['effort'],effort)
            self.assertEqual(preview['count_body']['output_config']['effort'],effort)
            self.assertEqual(preview['message_body']['thinking'],{'type':'disabled'})
        for selection in ['openai-gpt-6-luna','xai-grok-4-7']:
            cap=self.project()['agent_preferences']['capabilities']['models'][selection]
            self.assertFalse(cap['general_route_supported']);self.assertFalse(cap['general_route_configured'])
            for effort in preferences.EFFORTS[selection]:
                body=chat_models.body(chat_models.contract(selection),[],[],100,effort=effort)
                self.assertEqual(body['reasoning']['effort'],effort)
        with self.assertRaises(ValueError):chat_models.body(chat_models.contract('xai-grok-4-7'),[],[],100,effort='none')
        with self.assertRaises(ValueError):chat_models.body(chat_models.contract('xai-grok-4-7'),[],[],100,effort='max')

    def test_idle_old_preview_stales_after_setting_change_without_message(self):
        preview=self.f.preview();raw=deepcopy(preview['message_body'])
        self.settings(effort='high')
        self.assertEqual(self.f.approve(preview)[0],400)
        self.assertEqual(self.f.http.store.general_chat_runtime.transport.messages,[])
        with self.f.http.store.connect() as db:stored=chat_general.get_row(db,'general_chat_previews',preview['id'])
        self.assertEqual(stored['message_body'],raw)

    def test_read_only_manifest_and_direct_write_denial(self):
        self.settings('read_only','low');preview=self.f.preview()
        self.assertEqual(preview['tool_scope'],['search_project_context','get_model_capabilities','get_generation_job','estimate_media_plan'])
        self.assertEqual([x['name'] for x in preview['message_body']['tools']],['search_project_context','get_model_capabilities','estimate_media_plan','get_generation_job'])
        result,_=self.direct_tool('propose_media_plan',dict(goal='a',scenes='b',style='',constraints='',kind='narrative'))
        self.assertEqual(result['code'],'AGENT_READ_ONLY');self.assertFalse(self.project().get('guided_plans'))

    def test_review_preserved_full_draft_diff_and_old_run_cannot_elevate(self):
        self.seed_timeline();before=deepcopy(editing.current(self.project()))
        result,old_run=self.direct_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'proposed');self.assertEqual(editing.current(self.project()),before)
        self.settings('full_access','low')
        result,_=self.direct_tool('propose_timeline_changes',self.args(),old_run)
        self.assertEqual(result['status'],'proposed');self.assertEqual(self.project()['timeline_head'],1)
        result,_=self.direct_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'applied_draft');self.assertTrue(result['agent_draft_created'])
        self.assertFalse(result['output_approved']);self.assertEqual(result['application_actor'],'agent-draft')
        current=editing.current(self.project());self.assertEqual(current['id'],2);self.assertNotIn('approval',current)
        self.assertEqual(current['agent_draft']['actor'],'agent-draft')
        proposal=next(x for x in self.project()['timeline_edit_proposals'] if x['id']==result['proposal_id'])
        self.assertNotIn('reviews',proposal)
        self.assertEqual(self.project()['timeline_versions'][0],before)
        self.assertEqual(self.f.action('render_job',song='A')[0],400)

    def test_full_removal_and_clear_remain_proposals_and_delete_tools_never_execute(self):
        self.seed_timeline(repeat=True);self.settings('full_access','low')
        before=deepcopy(editing.current(self.project()))
        for commands in [[dict(op='remove_clips',clip_indices=[0])],[dict(op='clear_motion_overlay',clip_index=0)]]:
            result,_=self.direct_tool('propose_timeline_changes',self.args(commands))
            self.assertEqual(result['status'],'proposed');self.assertEqual(editing.current(self.project()),before)
        for name in ['delete_account','account_delete','delete_file','delete_asset','execute_arbitrary_code']:
            result,_=self.direct_tool(name,{})
            self.assertEqual(result['status'],'invalid_arguments');self.assertEqual(editing.current(self.project()),before)

    def test_active_body_frozen_downgrade_immediate_and_reupgrade_cannot_rewiden(self):
        self.seed_timeline();self.settings('full_access','high');args=self.args()
        transport=self.f.http.store.general_chat_runtime.transport
        transport.responses=[response([use('held-write','propose_timeline_changes',args)],'tool_use')]
        entered=Event();release=Event();original=transport.complete;captured=[]
        def held(body):
            captured.append(deepcopy(body));entered.set()
            if not release.wait(8):raise TimeoutError('controlled hold')
            return original(body)
        transport.complete=held
        preview=self.f.preview();self.assertEqual(self.f.approve(preview)[0],200)
        worker=Thread(target=self.f.http.store.general_chat_runtime.process_next);worker.start()
        try:
            self.assertTrue(entered.wait(3));self.settings('read_only','medium');self.settings('full_access','low')
        finally:release.set();worker.join(10);transport.complete=original
        self.assertFalse(worker.is_alive());p=self.project();self.assertEqual(p['timeline_head'],1)
        turn=p['general_chat_turns'][-1];self.assertEqual(turn['status'],'awaiting_continuation_approval',turn)
        self.assertEqual(captured[0],preview['message_body'])
        follow=p['general_chat_previews'][-1]
        self.assertEqual(follow['message_body']['output_config']['effort'],'high')
        self.assertEqual(follow['tool_scope'],['search_project_context','get_model_capabilities','get_generation_job','estimate_media_plan'])
        active=p['agent_preferences']['active_response'];self.assertEqual(active['effective_mode'],'read_only')
        self.assertEqual(active['mode'],'full_access');self.assertEqual(active['effort'],'high')
        self.assertTrue(p['agent_preferences']['settings_pending'])
        self.reject_follow(follow)
        result,_,follow=self.send_tool('propose_timeline_changes',args)
        self.assertEqual(result['status'],'applied_draft');self.assertEqual(self.project()['timeline_head'],2)
        self.assertEqual(follow['message_body']['output_config']['effort'],'low')
        self.reject_follow(follow)

    def test_full_self_effect_settles_usage_and_requires_followup_consent(self):
        self.seed_timeline();self.settings('full_access','medium')
        result,preview,follow=self.send_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'applied_draft');self.assertEqual(result['timeline_version'],2)
        self.assertIn('applied_draft',json.dumps(follow['message_body']))
        turn=self.project()['general_chat_turns'][-1]
        self.assertIsNone(turn['error']);self.assertNotEqual(turn['status'],'outcome_unknown')
        transport=self.f.http.store.general_chat_runtime.transport;self.assertEqual(len(transport.messages),1)
        transport.responses=[response()]
        self.assertEqual(self.f.approve(follow)[0],200);self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),2)
        self.assertEqual(transport.messages[-1]['output_config']['effort'],'medium')
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'completed')
        self.assertEqual(self.project()['timeline_head'],2)

    def test_tampered_run_settings_and_legacy_marker_never_grant_full(self):
        self.seed_timeline();run=self.post('production_run',song='A')['run']['id']
        with self.f.http.store.connect() as db:
            body=json.loads(db.execute('SELECT body FROM state').fetchone()[0]);item=next(x for x in body['projects']['A']['production_runs'] if x['id']==run)
            item.pop('agent_settings');item.pop('agent_permission_ceiling');db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(body),))
        self.settings('full_access','low');result,_=self.direct_tool('propose_timeline_changes',self.args(),run)
        self.assertEqual(result['status'],'proposed');self.assertEqual(self.project()['timeline_head'],1)

    def test_cancel_and_unknown_keep_desired_settings_without_replay(self):
        self.settings('review','high');preview=self.f.preview();self.assertEqual(self.f.approve(preview)[0],200)
        turn=self.project()['general_chat_turns'][-1];self.settings('read_only','low')
        self.post('general_chat_cancel',song='A',turn=turn['id'])
        self.assertFalse(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.f.http.store.general_chat_runtime.transport.messages,[])
        self.settings('review','medium');transport=self.f.http.store.general_chat_runtime.transport;transport.responses=['__unknown__']
        preview=self.f.preview();self.assertEqual(self.f.approve(preview)[0],200);self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.settings('read_only','high');self.assertFalse(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),1)
        reopened=app.Store(self.f.tmp.name).state()['projects']['A']
        self.assertEqual(reopened['agent_preferences']['current']['mode'],'read_only')
        self.assertEqual(reopened['general_chat_turns'][-1]['status'],'outcome_unknown')

    def test_restart_preserves_queued_frozen_effort_and_immediate_permission_ceiling(self):
        self.seed_timeline();self.settings('full_access','high')
        preview=self.f.preview();self.assertEqual(self.f.approve(preview)[0],200)
        self.settings('read_only','medium')
        reopened=app.Store(self.f.tmp.name)
        transport=chat_general.FixtureTransport([response([use('after-restart','propose_timeline_changes',self.args())],'tool_use')])
        runtime=chat_general.Runtime(reopened,transport);reopened.general_chat_runtime=runtime
        self.assertTrue(runtime.process_next());p=reopened.state()['projects']['A']
        self.assertEqual(p['timeline_head'],1)
        self.assertEqual(transport.messages[0],preview['message_body'])
        self.assertEqual(transport.messages[0]['output_config']['effort'],'high')
        self.assertEqual(p['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        self.assertEqual(p['agent_preferences']['active_response']['effective_mode'],'read_only')
        self.assertIn('AGENT_READ_ONLY',json.dumps(p['general_chat_previews'][-1]['message_body']))
        self.assertFalse(runtime.process_next());self.assertEqual(len(transport.messages),1)

    def test_running_restart_keeps_settings_and_uncertain_without_replay(self):
        self.settings('full_access','high');preview=self.f.preview()
        self.assertEqual(self.f.approve(preview)[0],200)
        with self.f.http.store.connect() as db:
            turn=chat_general.get_row(db,'general_chat_turns',self.project()['general_chat_turns'][-1]['id'])
            turn['status']='running';chat_general.put(db,'general_chat_turns',turn)
        self.settings('read_only','medium');reopened=app.Store(self.f.tmp.name)
        with reopened.connect() as db:chat_general.recover(db)
        p=reopened.state()['projects']['A'];self.assertEqual(p['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertEqual(p['agent_preferences']['current']['effort'],'medium')
        self.assertEqual(p['agent_preferences']['active_response']['effort'],'high')
        transport=chat_general.FixtureTransport([response()]);runtime=chat_general.Runtime(reopened,transport)
        self.assertFalse(runtime.process_next());self.assertEqual(transport.messages,[])

    def test_queued_frozen_settings_tamper_blocks_before_count_or_message(self):
        self.settings('full_access','high');preview=self.f.preview()
        self.assertEqual(self.f.approve(preview)[0],200)
        with self.f.http.store.connect() as db:
            state=json.loads(db.execute('SELECT body FROM state').fetchone()[0])
            state['projects']['A']['production_runs'][-1]['agent_settings']['effort']='low'
            db.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(state),))
        runtime=self.f.http.store.general_chat_runtime;self.assertTrue(runtime.process_next())
        self.assertEqual(runtime.transport.counted,[]);self.assertEqual(runtime.transport.messages,[])
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'blocked_before_message')

    def test_full_draft_stale_version_revoked_rights_and_asset_change_never_apply(self):
        self.seed_timeline();self.settings('full_access','low')
        args=self.args();self.post('timeline',song='A',timeline=editing.current(self.project()))
        result,_=self.direct_tool('propose_timeline_changes',args)
        self.assertEqual(result['status'],'blocked');self.assertEqual(self.project()['timeline_head'],2)
        sha=self.project()['shots']['s']['takes'][0]['sha256']
        self.post('asset_rights',sha256=sha,blocked=True,reason='owned fixture revoked')
        result,_=self.direct_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'blocked');self.assertEqual(self.project()['timeline_head'],2)
        self.post('asset_rights',sha256=sha,blocked=False,reason='owned fixture restored')
        original=deepcopy(self.project()['timeline_versions'])
        take=self.project()['shots']['s']['takes'][0]
        path=Path(take['asset']);path.write_bytes(b'not the recorded media')
        result,_=self.direct_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'blocked');self.assertEqual(self.project()['timeline_versions'],original)

    def test_legacy_anthropic_effort_and_permission_downgrade_are_frozen(self):
        self.settings('full_access','high');self.f.connect_synthetic()
        runtime=self.f.http.store.chat_runtime;adapter=runtime.adapter
        adapter.responses=[response([use('read','search_project_context',{'query':'current'})],'tool_use'),response()]
        self.post('chat_turn',song='A',prompt=base.PROMPT)
        adapter.on_count=lambda:self.settings('read_only','medium')
        self.assertTrue(runtime.process_next())
        self.assertEqual(self.project()['chat_turns'][-1]['status'],'completed')
        self.assertEqual(len(adapter.messages),2)
        self.assertTrue(all(body['output_config']['effort']=='high' for body in adapter.messages))
        self.assertTrue(all(body['thinking']=={'type':'disabled'} for body in adapter.messages))
        self.assertEqual([x['name'] for x in adapter.messages[-1]['tools']],['search_project_context','get_model_capabilities','estimate_media_plan','get_generation_job'])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'media tools required')
    def test_actual_full_draft_preview_render_still_needs_final_approval(self):
        self.seed_timeline();self.settings('full_access','low')
        result,_,follow=self.send_tool('propose_timeline_changes',self.args())
        self.assertEqual(result['status'],'applied_draft');self.reject_follow(follow)
        raw=self.f.http.store.timeline_preview('A',2,0,24);self.assertTrue(raw.startswith(b'\x89PNG'))
        self.assertEqual(self.f.action('render_job',song='A')[0],400)
        self.post('approve_timeline',song='A');job=self.post('render_job',song='A')['job']
        self.assertTrue(self.f.http.store.process_next());final=next(x for x in self.f.state()['jobs'] if x['id']==job)
        self.assertEqual(final['status'],'completed',final.get('error'))
        self.assertEqual(final['snapshot']['timeline']['agent_draft']['actor'],'agent-draft')
        self.assertEqual(hashlib.sha256((self.f.http.store.root/'exports'/(job+'.mp4')).read_bytes()).hexdigest(),final['sha256'])


if __name__=='__main__':unittest.main()
