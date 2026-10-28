"""Isolated consent/queue contracts; no credentials or network provider."""
import json
import hashlib
import base64
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

import chat_general
import chat_runtime
import anthropic_ontology
import contracts
import ledger
import model_selection
from app import server
from tests.test_chat_runtime import ARGS, PROMPT, Fake, response, use


class GeneralChatHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        fixtures=[response([use('plan','propose_media_plan',ARGS)],'tool_use'),response()]
        self.http=server(self.tmp.name,0,general_chat_fixture=fixtures)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base='http://127.0.0.1:'+str(self.http.server_port)
        self.action('project',name='A',era='default',story=0)
        self.action('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
        self.pid=contracts.project_id(self.http.store.workspace_id,'A')
        with self.http.store.connect() as c:
            ledger.patch_budget(c,self.http.store.workspace_id,'rehearsal:project:'+self.pid,
                                dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
    def shutdown(self):
        self.http.shutdown();self.http.server_close();self.thread.join()
    def state(self):
        with urlopen(self.base+'/api/state') as r:return json.load(r)
    def send(self,payload):
        request=Request(self.base+'/api/action',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':self.state()['token']})
        try:
            with urlopen(request) as r:return r.status,json.load(r)
        except HTTPError as e:
            with e:return e.code,json.load(e)
    def session_state(self,cid):
        with urlopen(self.base+'/api/state?'+urlencode({'song':'A','conversation':cid})) as r:return json.load(r)
    def session_action(self,cid,action,**data):
        state=self.session_state(cid);active=state['projects']['A']['active_conversation']
        return self.send(dict(action=action,data=data,revision=state['revision'],request_id=uuid.uuid4().hex,
                              conversation_id=cid,conversation_revision=active['revision'],shared_version=active['shared_version']))
    def action(self,action,**data):
        return self.send(dict(action=action,data=data,revision=self.state()['revision'],request_id=uuid.uuid4().hex))
    def preview(self):
        status,result=self.action('general_chat_preview',song='A',prompt='음원에 맞는 장면을 제안해 줘',maximum_micro=10000)
        self.assertEqual(status,200,result);return result['general_chat_preview']
    def approve(self,preview,decision='approve',rights=True):
        return self.action('general_chat_decide',song='A',preview_id=preview['id'],manifest_sha256=preview['manifest_sha256'],decision=decision,rights_confirmed=rights)
    def test_preview_approval_tool_and_continuation_require_distinct_consent(self):
        first=self.preview();transport=self.http.store.general_chat_runtime.transport
        self.assertEqual((len(transport.counted),len(transport.messages)),(0,0))
        self.assertEqual(first['mode'],'contract-fake')
        self.assertEqual(first['message_sha256'],chat_general.digest(first['message_body']))
        status,result=self.approve(first);self.assertEqual(status,200,result)
        self.assertEqual(result['turn']['status'],'queued')
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'awaiting_continuation_approval',turn)
        self.assertEqual(len(project['guided_plans']),1)
        self.assertEqual(project['guided_plans'][0]['status'],'proposed')
        self.assertEqual(transport.counted,[first['count_body']]);self.assertEqual(transport.messages,[first['message_body']])
        second=project['general_chat_previews'][-1]
        self.assertIn('tool_result',json.dumps(second['message_body']))
        self.assertEqual(len(transport.messages),1)
        status,result=self.approve(second);self.assertEqual(status,200,result)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        turn=self.state()['projects']['A']['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'completed',turn);self.assertFalse(turn['billing_confirmed'])
        self.assertEqual(transport.messages[-1],second['message_body']);self.assertEqual(len(transport.messages),2)
    def test_reject_missing_rights_and_stale_context_do_not_send(self):
        first=self.preview();status,_=self.approve(first,rights=False);self.assertEqual(status,400)
        status,_=self.approve(first,'reject');self.assertEqual(status,200)
        self.assertFalse(self.http.store.general_chat_runtime.transport.counted)
        second=self.preview();self.action('shot',song='A',shot='changed',description='changed')
        status,_=self.approve(second);self.assertEqual(status,400)
        self.assertFalse(self.http.store.general_chat_runtime.transport.counted)
    def test_same_request_id_replay_is_idempotent_and_other_request_cannot_consume(self):
        first=self.preview();payload=dict(action='general_chat_decide',data=dict(song='A',preview_id=first['id'],manifest_sha256=first['manifest_sha256'],decision='approve',rights_confirmed=True),revision=self.state()['revision'],request_id=uuid.uuid4().hex)
        status,result=self.send(payload);self.assertEqual(status,200,result)
        status,again=self.send(payload);self.assertEqual(status,200);self.assertEqual(again,result)
        status,_=self.approve(first);self.assertEqual(status,400)
        self.assertEqual(len(self.state()['projects']['A']['general_chat_turns']),1)
    def test_competing_approvals_consume_once_and_reserve_once(self):
        first=self.preview();revision=self.state()['revision']
        def submit(_):
            return self.send(dict(action='general_chat_decide',data=dict(song='A',preview_id=first['id'],manifest_sha256=first['manifest_sha256'],decision='approve',rights_confirmed=True),revision=revision,request_id=uuid.uuid4().hex))[0]
        with ThreadPoolExecutor(2) as pool:statuses=list(pool.map(submit,range(2)))
        self.assertEqual(statuses.count(200),1);self.assertTrue(all(x in {200,400,409} for x in statuses))
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM general_chat_turns').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
    def test_changed_rights_and_tampered_manifest_do_not_send(self):
        first=self.preview()
        with self.http.store.connect() as c:
            c.execute('INSERT INTO asset_rights VALUES (?,?,?,?)',('a'*64,1,'changed',1))
        status,_=self.approve(first);self.assertEqual(status,400)
        second=self.preview();second['manifest_sha256']='0'*64
        status,_=self.approve(second);self.assertEqual(status,400)
        self.assertEqual(self.http.store.general_chat_runtime.transport.counted,[])
    def test_budget_change_and_reservation_error_roll_back_grant_and_turn(self):
        first=self.preview()
        with self.http.store.connect() as c:
            ledger.patch_budget(c,self.http.store.workspace_id,'rehearsal:project:'+self.pid,
                                dict(limit={'amount':'2','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),1)
        status,_=self.approve(first);self.assertEqual(status,400)
        second=self.preview()
        req=dict(action='general_chat_decide',data=dict(song='A',preview_id=second['id'],manifest_sha256=second['manifest_sha256'],decision='approve',rights_confirmed=True),revision=self.state()['revision'],request_id=uuid.uuid4().hex)
        with patch.object(chat_general.ledger,'command',side_effect=sqlite3.OperationalError('fixture reservation failure')):
            with self.assertRaises(sqlite3.OperationalError):self.http.store.mutate(req)
        with self.http.store.connect() as c:
            self.assertEqual(chat_general.get_row(c,'general_chat_previews',second['id'])['state'],'pending')
            self.assertEqual(c.execute('SELECT count(*) FROM general_chat_turns').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
        self.assertEqual(self.http.store.general_chat_runtime.transport.counted,[])
    def test_unknown_and_restart_keep_reservation_and_block_repeat(self):
        self.http.store.general_chat_runtime.transport.responses=['__unknown__']
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        turn=self.state()['projects']['A']['general_chat_turns'][-1];self.assertEqual(turn['status'],'outcome_unknown')
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
            chat_general.recover(c)
        status,_=self.action('general_chat_preview',song='A',prompt='다시 요청',maximum_micro=10000)
        self.assertEqual(status,400);self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.http.store.general_chat_runtime.transport.messages),1)
    def test_over_limit_usage_keeps_actual_and_no_tool_call(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use');upstream['usage']={'input_tokens':100,'output_tokens':100000}
        self.http.store.general_chat_runtime.transport.responses=[upstream]
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        self.http.store.general_chat_runtime.process_next()
        project=self.state()['projects']['A'];self.assertEqual(project['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertEqual(project['general_chat_turns'][-1]['usage']['output_tokens'],100000)
        self.assertFalse(project.get('guided_plans'))
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state,actual FROM reservations').fetchone(),('disputed',50010))
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
    def test_other_conversation_cannot_view_or_consume_preview(self):
        first=self.preview();status,result=self.action('conversation_create',song='A',title='다른 대화')
        self.assertEqual(status,200,result);cid=result['conversation']['id']
        self.assertEqual(self.session_state(cid)['projects']['A']['general_chat_previews'],[])
        status,_=self.session_action(cid,'general_chat_decide',song='A',preview_id=first['id'],manifest_sha256=first['manifest_sha256'],decision='approve',rights_confirmed=True)
        self.assertEqual(status,400);self.assertEqual(self.http.store.general_chat_runtime.transport.counted,[])
    def test_restart_running_request_marks_uncertain_without_resubmission(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result);identifier=result['turn']['id']
        with self.http.store.connect() as c:
            turn=chat_general.get_row(c,'general_chat_turns',identifier);turn['status']='running';chat_general.put(c,'general_chat_turns',turn)
            chat_general.recover(c)
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertFalse(self.http.store.general_chat_runtime.process_next());self.assertEqual(self.http.store.general_chat_runtime.transport.messages,[])
    def test_cancel_queued_releases_reservation_without_call(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        status,result=self.action('general_chat_cancel',song='A',turn=result['turn']['id']);self.assertEqual(status,200,result)
        self.assertEqual(result['general_chat_turn']['status'],'cancelled')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
        self.assertFalse(self.http.store.general_chat_runtime.process_next());self.assertEqual(self.http.store.general_chat_runtime.transport.messages,[])
        run=next(r for r in self.state()['projects']['A']['production_runs'] if r['id']==result['general_chat_turn'].get('run')) if result['general_chat_turn'].get('run') else self.state()['projects']['A']['production_runs'][-1]
        self.assertEqual(run['state'],'cancelled')

    def test_model_change_reserves_until_completion_and_cancel_requires_reselection(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        with self.http.store.connect() as c:
            original_preview=chat_general.get_row(c,'general_chat_previews',first['id'])
            original_turn=chat_general.get_row(c,'general_chat_turns',result['turn']['id'])
        project=self.state()['projects']['A'];model_revision=project['active_conversation']['model_revision']
        status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision)
        self.assertEqual(status,200)
        self.assertEqual(self.state()['projects']['A']['effective_chat_selection'],'anthropic-haiku-5-5')
        status,_=self.action('model_settings',song='A',selections={'chat':'xai-grok-4-7'},model_revision=project['model_settings']['revision'])
        self.assertEqual(status,400)
        project=self.state()['projects']['A']
        self.assertEqual(project['general_chat_turns'][-1]['status'],'queued')
        with self.http.store.connect() as c:
            self.assertEqual(chat_general.get_row(c,'general_chat_previews',first['id']),original_preview)
            self.assertEqual(chat_general.get_row(c,'general_chat_turns',result['turn']['id']),original_turn)
        self.assertEqual(project['active_conversation']['model_revision'],model_revision+1)
        self.assertEqual(project['active_conversation']['pending_chat_selection']['after_turn'],result['turn']['id'])
        status,_=self.action('general_chat_cancel',song='A',turn=result['turn']['id']);self.assertEqual(status,200)
        status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision)
        self.assertEqual(status,409)
        project=self.state()['projects']['A']
        self.assertEqual(project['effective_chat_selection'],'anthropic-haiku-5-5')
        self.assertIn('pending_chat_selection',project['active_conversation'])
        status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision+1)
        self.assertEqual(status,200)
        self.assertNotIn('pending_chat_selection',self.state()['projects']['A']['active_conversation'])

    def test_running_model_change_does_not_invalidate_approved_reply(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        with self.http.store.connect() as c:
            original_preview=chat_general.get_row(c,'general_chat_previews',first['id'])
            original_turn=chat_general.get_row(c,'general_chat_turns',result['turn']['id'])
        transport=self.http.store.general_chat_runtime.transport
        transport.responses=[response()];original=transport.complete
        ready=threading.Event();resume=threading.Event()
        def pause(body):
            ready.set()
            if not resume.wait(10):raise TimeoutError('test synchronization failed')
            return original(body)
        with patch.object(transport,'complete',side_effect=pause):
            worker=threading.Thread(target=self.http.store.general_chat_runtime.process_next);worker.start()
            try:
                self.assertTrue(ready.wait(10))
                project=self.state()['projects']['A'];model_revision=project['active_conversation']['model_revision']
                status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision)
                self.assertEqual(status,200)
                self.assertEqual(self.state()['projects']['A']['effective_chat_selection'],'anthropic-haiku-5-5')
                status,_=self.action('model_settings',song='A',selections={'chat':'xai-grok-4-7'},model_revision=project['model_settings']['revision'])
                self.assertEqual(status,400)
            finally:
                resume.set();worker.join(10)
            self.assertFalse(worker.is_alive())
        project=self.state()['projects']['A'];self.assertEqual(project['general_chat_turns'][-1]['status'],'completed')
        self.assertEqual(project['production_runs'][-1]['state'],'completed')
        with self.http.store.connect() as c:
            self.assertEqual(chat_general.get_row(c,'general_chat_previews',first['id']),original_preview)
            completed=chat_general.get_row(c,'general_chat_turns',result['turn']['id'])
            self.assertEqual(completed['binding'],original_turn['binding'])
            self.assertEqual(completed['model'],original_turn['model'])
        self.assertEqual(len(transport.messages),1)
        self.assertEqual(project['effective_chat_selection'],'xai-grok-4-7')
        self.assertNotIn('pending_chat_selection',project['active_conversation'])
        status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision)
        self.assertEqual(status,409)
        status,_=self.action('conversation_model',song='A',selection='xai-grok-4-7',model_revision=model_revision+1)
        self.assertEqual(status,200)
    def connect_synthetic(self):
        project=self.state()['projects']['A']
        approval=dict(model=anthropic_ontology.MODEL,workspace_id=self.http.store.workspace_id,project_id=self.pid,synthetic_only=True,expires=time.time()+300,
                      context_hash=model_selection.snapshot(project)['sha256'],prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],price_revision='haiku-5-5-20261027-tiered',max_rounds=2)
        self.http.store.chat_runtime=chat_runtime.ChatRuntime(self.http.store,Fake([response()]),approval,self.tmp.name+'/synthetic.sqlite3')
    def test_synthetic_and_general_queues_block_each_other(self):
        self.connect_synthetic();status,result=self.action('chat_turn',song='A',prompt=PROMPT);self.assertEqual(status,200,result)
        status,_=self.action('general_chat_preview',song='A',prompt='새 요청',maximum_micro=10000);self.assertEqual(status,400)
        status,result=self.action('chat_cancel',song='A',turn=result['chat_turn']['id']);self.assertEqual(status,200,result)
        preview=self.preview();status,result=self.approve(preview);self.assertEqual(status,200,result)
        status,_=self.action('chat_turn',song='A',prompt=PROMPT);self.assertEqual(status,400)
    def test_settlement_failure_keeps_unknown_and_no_new_tool_or_message(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        original=ledger.command
        def fail_settle(c,workspace,scope,kind,data,key):
            if kind=='settle':raise sqlite3.OperationalError('fixture journal failure')
            return original(c,workspace,scope,kind,data,key)
        with patch.object(chat_general.ledger,'command',side_effect=fail_settle):self.http.store.general_chat_runtime.process_next()
        project=self.state()['projects']['A'];self.assertEqual(project['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertEqual(project['general_chat_turns'][-1]['usage'],{'input_tokens':100,'output_tokens':100})
        self.assertFalse(project.get('guided_plans'))
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
    def test_persistent_ledger_failure_records_unknown_and_preserves_reservation(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        with patch.object(chat_general.ledger,'command',side_effect=sqlite3.OperationalError('ledger unavailable')):
            self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['journal_failure'],'update_failed')
        self.assertEqual(turn['usage'],{'input_tokens':100,'output_tokens':100})
        self.assertFalse(project.get('guided_plans'))
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
            chat_general.recover(c)
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.http.store.general_chat_runtime.transport.messages),1)

    def test_cancel_after_settlement_before_tool_does_not_create_proposal(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        identifier=result['turn']['id'];ready=threading.Event();resume=threading.Event()
        original=chat_general.chat_protocols.normalize
        def pause_after_response(*args,**kwargs):
            value=original(*args,**kwargs);ready.set()
            if not resume.wait(10):raise TimeoutError('test synchronization failed')
            return value
        with patch.object(chat_general.chat_protocols,'normalize',side_effect=pause_after_response):
            worker=threading.Thread(target=self.http.store.general_chat_runtime.process_next)
            worker.start()
            try:
                self.assertTrue(ready.wait(10))
                status,result=self.action('general_chat_cancel',song='A',turn=identifier)
                self.assertEqual(status,200,result)
                self.assertEqual(result['general_chat_turn']['status'],'cancel_requested')
            finally:
                resume.set();worker.join(10)
            self.assertFalse(worker.is_alive())
        project=self.state()['projects']['A']
        self.assertFalse(project.get('guided_plans'))
        self.assertEqual(project['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.http.store.general_chat_runtime.transport.messages),1)

    def test_cancel_after_tool_preparation_is_checked_in_tool_transaction(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        identifier=result['turn']['id'];ready=threading.Event();resume=threading.Event()
        original=self.http.store.mutate
        def pause_tool(request):
            if request['action']=='production_tool':
                ready.set()
                if not resume.wait(10):raise TimeoutError('test synchronization failed')
                # Model the worker obtaining fresh metadata after cancellation;
                # revision freshness alone must not permit the cancelled call.
                current=self.state();project=current['projects']['A'];session=project['active_conversation']
                request['revision']=current['revision'];request['conversation_revision']=session['revision'];request['shared_version']=session['shared_version']
            return original(request)
        with patch.object(self.http.store,'mutate',side_effect=pause_tool):
            worker=threading.Thread(target=self.http.store.general_chat_runtime.process_next);worker.start()
            try:
                self.assertTrue(ready.wait(10))
                status,result=self.action('general_chat_cancel',song='A',turn=identifier)
                self.assertEqual(status,200,result)
            finally:
                resume.set();worker.join(10)
            self.assertFalse(worker.is_alive())
        project=self.state()['projects']['A']
        self.assertFalse(project.get('guided_plans'))
        self.assertEqual(project['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertEqual(project['production_runs'][-1]['state'],'outcome_unknown')

    def test_restart_with_ledger_failure_preserves_unknown_and_held_amount(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        identifier=result['turn']['id']
        with self.http.store.connect() as c:
            turn=chat_general.get_row(c,'general_chat_turns',identifier);turn['status']='running';chat_general.put(c,'general_chat_turns',turn)
            with patch.object(chat_general.ledger,'command',side_effect=sqlite3.OperationalError('ledger unavailable')):
                chat_general.recover(c)
            turn=chat_general.get_row(c,'general_chat_turns',identifier)
            self.assertEqual((turn['status'],turn['journal_failure']),('outcome_unknown','update_failed'))
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.http.store.general_chat_runtime.transport.messages,[])

    def test_turn_storage_failure_propagates_and_restart_recovers(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        identifier=result['turn']['id'];original_put=chat_general.put
        def fail_unknown(c,table,item):
            if table=='general_chat_turns' and item['status']=='outcome_unknown':raise sqlite3.OperationalError('turn storage unavailable')
            return original_put(c,table,item)
        with patch.object(chat_general.ledger,'command',side_effect=sqlite3.OperationalError('ledger unavailable')),patch.object(chat_general,'put',side_effect=fail_unknown):
            with self.assertRaises(sqlite3.OperationalError):self.http.store.general_chat_runtime.process_next()
        with self.http.store.connect() as c:
            self.assertEqual(chat_general.get_row(c,'general_chat_turns',identifier)['status'],'running')
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
            chat_general.recover(c)
            self.assertEqual(chat_general.get_row(c,'general_chat_turns',identifier)['status'],'outcome_unknown')
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.http.store.general_chat_runtime.transport.messages),1)
    def test_rights_changed_after_queue_blocks_count_and_releases_reservation(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        with self.http.store.connect() as c:c.execute('INSERT INTO asset_rights VALUES (?,?,?,?)',('b'*64,1,'changed',2))
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        turn=self.state()['projects']['A']['general_chat_turns'][-1];self.assertEqual(turn['status'],'blocked_before_message')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
        self.assertEqual(self.http.store.general_chat_runtime.transport.counted,[])
    def test_private_reasoning_is_not_saved_or_sent_in_a_continuation(self):
        secret='fixture-private-reasoning-canary'
        upstream=response([dict(type='thinking',thinking=secret),use('plan','propose_media_plan',ARGS)],'tool_use')
        self.http.store.general_chat_runtime.transport.responses=[upstream]
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        self.http.store.general_chat_runtime.process_next()
        project=self.state()['projects']['A'];self.assertEqual(project['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertFalse(project.get('guided_plans'));self.assertNotIn(secret,json.dumps(project))
        self.assertNotIn(secret,(self.http.store.db).read_bytes().decode('latin1'))
        self.assertEqual(len(self.http.store.general_chat_runtime.transport.messages),1)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'media tools required')
    def test_fake_chat_proposes_edit_and_requires_human_render_approval(self):
        def post(action,**data):
            status,result=self.action(action,**data);self.assertEqual(status,200,result);return result
        image=Path(self.tmp.name)/'red.png';audio=Path(self.tmp.name)/'tone.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x64','-frames:v','1',str(image)],check=True)
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-c:a','pcm_s16le',str(audio)],check=True)
        post('audio',song='A',filename='tone.wav',content=base64.b64encode(audio.read_bytes()).decode(),rights='synthetic generated audio')
        post('shot',song='A',shot='scene',description='synthetic scene')
        post('take',song='A',shot='scene',shot_revision=0,filename='red.png',content=base64.b64encode(image.read_bytes()).decode(),reason='synthetic',rights='synthetic generated image')
        post('select',song='A',shot='scene',take=1,shot_revision=1)
        post('review_take',song='A',shot='scene',take=1,decision='approved',reason='synthetic review')
        timeline=dict(clips=[dict(shot='scene',take=1,trim=0,duration=2)],audio=1,audio_offset=0,subtitles=[],profile='preview')
        post('timeline',song='A',timeline=timeline)
        changes=dict(description='합성 자막 추가',timeline_version=1,commands=[dict(op='set_captions',cues=[dict(start=0,end=1,text='합성 자막')])])
        transport=self.http.store.general_chat_runtime.transport
        transport.responses=[response([use('edit','propose_timeline_changes',changes)],'tool_use'),response()]
        first=self.preview();self.assertIn('propose_timeline_changes',first['tool_scope']);self.assertEqual(transport.messages,[])
        status,_=self.approve(first);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];self.assertEqual(project['timeline_head'],1)
        self.assertEqual(len(project['timeline_edit_proposals']),1)
        proposal=project['timeline_edit_proposals'][0];self.assertEqual(proposal['status'],'proposed')
        next_preview=project['general_chat_previews'][-1];self.assertEqual(len(transport.messages),1)
        status,_=self.approve(next_preview);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'completed')
        post('review_timeline_proposal',song='A',proposal_id=proposal['id'],timeline_version=1,decision='approved')
        project=self.state()['projects']['A'];self.assertEqual(project['timeline_head'],2)
        self.assertEqual(project['timeline_versions'][-1]['subtitles'][0]['text'],'합성 자막')
        transport.responses=[response([use('render-bad','request_render',dict(timeline_version=2,grant_id='not-approved'))],'tool_use'),response()]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.state()['jobs'],[])
        follow=self.state()['projects']['A']['general_chat_previews'][-1]
        status,_=self.approve(follow);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        post('approve_timeline',song='A')
        grant=self.state()['projects']['A']['timeline_versions'][-1]['approval']['id']
        transport.responses=[response([use('render-ok','request_render',dict(timeline_version=2,grant_id=grant))],'tool_use'),response()]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];follow=project['general_chat_previews'][-1]
        self.assertEqual(project['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        job=self.state()['jobs'][-1];self.assertEqual(job['status'],'queued')
        self.assertTrue(self.http.store.process_next())
        job=self.state()['jobs'][-1];self.assertEqual(job['status'],'completed',job.get('error'))
        with urlopen(self.base+job['download']) as r:video=r.read()
        output=Path(self.tmp.name)/'download.mp4';output.write_bytes(video)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
        self.assertEqual({s['codec_type'] for s in probe['streams']},{'video','audio','subtitle'})
        captions=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-map','0:s:0','-f','srt','-']).decode()
        self.assertIn('합성 자막',captions)
        status,_=self.approve(follow);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'completed')

    def test_project_context_is_disclosed_only_in_next_approval(self):
        status,_=self.action('shot',song='A',shot='private-fixture-shot-name',description='synthetic');self.assertEqual(status,200)
        transport=self.http.store.general_chat_runtime.transport
        transport.responses=[response([use('lookup','search_project_context',{'query':'current edit'})],'tool_use'),response()]
        first=self.preview();self.assertNotIn('private-fixture-shot-name',json.dumps(first['message_body']))
        status,_=self.approve(first);self.assertEqual(status,200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        p=self.state()['projects']['A'];follow=p['general_chat_previews'][-1]
        self.assertIn('private-fixture-shot-name',json.dumps(follow['message_body']))
        self.assertEqual(len(transport.messages),1)
        self.assertNotIn('private-fixture-shot-name',json.dumps(transport.messages[0]))
        status,_=self.approve(follow,rights=False);self.assertEqual(status,400)
        status,_=self.approve(follow,decision='reject');self.assertEqual(status,200)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),1)

    def _assert_unpriced_observation(self, upstream, reason, expected):
        upstream['_request_id']='req_safe_456'
        upstream['opaque_sensitive_fixture']='do-not-store-fixture-secret'
        transport=self.http.store.general_chat_runtime.transport;transport.responses=[upstream]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        p=self.state()['projects']['A'];turn=p['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['pricing_status'],reason)
        self.assertEqual(turn['observed_usage'],expected)
        self.assertEqual(turn['steps'][-1]['request_id'],'req_safe_456')
        self.assertNotIn('do-not-store-fixture-secret',json.dumps(turn))
        self.assertFalse(p.get('guided_plans'))
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
            chat_general.recover(c)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),1)

    def test_huge_observed_usage_is_preserved_as_exact_json_safe_string(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
        upstream['usage']={'input_tokens':10**20,'output_tokens':100}
        self._assert_unpriced_observation(upstream,'amount_out_of_range',{
            'input_tokens':{'status':'valid','value':str(10**20)},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'absent'},'cache_read_input_tokens':{'status':'absent'},
            'service_tier':{'status':'absent'}})

    def test_unpriced_service_tier_is_distinguished_from_missing_usage(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use');upstream['service_tier']='priority'
        self._assert_unpriced_observation(upstream,'unsupported_service_tier',{
            'input_tokens':{'status':'valid','value':'100'},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'absent'},'cache_read_input_tokens':{'status':'absent'},
            'service_tier':{'status':'valid','value':'priority'}})

    def test_nested_billing_dimensions_do_not_settle_or_execute_tools(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
        upstream['usage'].update(service_tier='priority',speed='fast',inference_geo='us',server_tool_use={'web_fetch_requests':0,'web_search_requests':1})
        self._assert_unpriced_observation(upstream,'unsupported_service_tier',{
            'input_tokens':{'status':'valid','value':'100'},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'absent'},'cache_read_input_tokens':{'status':'absent'},
            'service_tier':{'status':'valid','value':'priority'},'speed':{'status':'valid','value':'fast'},
            'inference_geo':{'status':'valid','value':'us'},'server_tool_use':{'status':'unsupported'}})

    def test_mismatched_response_model_cannot_use_selected_model_price(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use');upstream['model']='different-model'
        self._assert_unpriced_observation(upstream,'pricing_contract_changed',{
            'input_tokens':{'status':'valid','value':'100'},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'absent'},'cache_read_input_tokens':{'status':'absent'},
            'service_tier':{'status':'absent'}})

    def test_official_standard_usage_shape_completes(self):
        upstream=response();upstream['usage'].update(service_tier='standard',speed='standard',inference_geo='global',
            server_tool_use={'web_fetch_requests':0,'web_search_requests':0},
            cache_creation={'ephemeral_1h_input_tokens':0,'ephemeral_5m_input_tokens':0},
            cache_creation_input_tokens=0,cache_read_input_tokens=0,output_tokens_details={'thinking_tokens':5})
        self.http.store.general_chat_runtime.transport.responses=[upstream]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        turn=self.state()['projects']['A']['general_chat_turns'][-1]
        self.assertEqual((turn['status'],turn['pricing_status']),('completed','priced'))
        self.assertFalse(turn['billing_confirmed'])

    def test_unpriced_cache_usage_is_observed_without_settlement(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
        upstream['usage']['cache_creation_input_tokens']=17;upstream['usage']['cache_read_input_tokens']=9
        self._assert_unpriced_observation(upstream,'unsupported_cache_usage',{
            'input_tokens':{'status':'valid','value':'100'},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'valid','value':'17'},'cache_read_input_tokens':{'status':'valid','value':'9'},
            'service_tier':{'status':'absent'}})

    def test_response_usage_survives_cancellation_or_rights_change(self):
        for change in ('cancel', 'rights'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                self._observed_usage_race(folder, change)

    def test_observation_limit_explicitly_rejects_extreme_integer_without_truncation(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
        upstream['usage']={'input_tokens':10**300,'output_tokens':100}
        self._assert_unpriced_observation(upstream,'invalid_or_unrepresentable_usage',{
            'input_tokens':{'status':'too_large'},'output_tokens':{'status':'valid','value':'100'},
            'cache_creation_input_tokens':{'status':'absent'},'cache_read_input_tokens':{'status':'absent'},
            'service_tier':{'status':'absent'}})

    def test_priced_but_browser_unsafe_integer_is_exact_string_and_blocks_tool(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
        upstream['usage']={'input_tokens':10**16,'output_tokens':100}
        self.http.store.general_chat_runtime.transport.responses=[upstream]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        p=self.state()['projects']['A'];turn=p['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['usage']['input_tokens'],str(10**16))
        self.assertEqual(turn['observed_usage']['input_tokens']['value'],str(10**16))
        self.assertEqual(turn['steps'][-1]['usage']['input_tokens'],str(10**16))
        self.assertFalse(p.get('guided_plans'))
        with self.http.store.connect() as c:
            state,actual=c.execute('SELECT state,actual FROM reservations').fetchone()
            self.assertEqual(state,'disputed');self.assertGreater(actual,10**15)

    def test_unsupported_usage_survives_cancellation_and_rights_change(self):
        for change in ('cancel','rights'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
                upstream['usage']['cache_read_input_tokens']=7
                self._observed_usage_race(folder,change,upstream,'unsupported_cache_usage')

    def test_nested_unpriced_usage_survives_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use')
            upstream['usage'].update(speed='fast',inference_geo='us')
            self._observed_usage_race(folder,'cancel',upstream,'unsupported_speed')

    def test_unpriced_observation_survives_persistent_journal_failure_and_restart(self):
        upstream=response([use('plan','propose_media_plan',ARGS)],'tool_use');upstream['service_tier']='priority'
        upstream['_request_id']='req_safe_456'
        self.http.store.general_chat_runtime.transport.responses=[upstream]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200)
        with patch.object(chat_general.ledger,'command',side_effect=sqlite3.OperationalError('synthetic failure')):
            self.assertTrue(self.http.store.general_chat_runtime.process_next())
        turn=self.state()['projects']['A']['general_chat_turns'][-1]
        self.assertEqual((turn['status'],turn['pricing_status'],turn['journal_failure']),('outcome_unknown','unsupported_service_tier','update_failed'))
        self.assertEqual(turn['observed_usage']['input_tokens'],{'status':'valid','value':'100'})
        self.assertEqual(turn['steps'][-1]['request_id'],'req_safe_456')
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
            chat_general.recover(c)
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'reserved')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())

    def _assert_second_round_usage(self, usage, reason, expected_usage, service_tier=None):
        first_response=response([use('first-plan','propose_media_plan',ARGS)],'tool_use')
        first_response['usage']={'input_tokens':17,'output_tokens':9}
        second_response=response([use('second-plan','propose_media_plan',ARGS)],'tool_use')
        second_response['usage']=usage
        second_response['_request_id']='req_second_round'
        second_response['sensitive_fixture']='do-not-store-round-secret'
        if service_tier is not None:second_response['service_tier']=service_tier
        transport=self.http.store.general_chat_runtime.transport
        transport.responses=[first_response,second_response]
        first=self.preview();status,_=self.approve(first);self.assertEqual(status,200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'awaiting_continuation_approval')
        self.assertEqual(turn['usage'],{'input_tokens':17,'output_tokens':9})
        following=project['general_chat_previews'][-1]
        status,_=self.approve(following);self.assertEqual(status,200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['pricing_status'],reason)
        self.assertEqual(turn['usage'],expected_usage)
        self.assertEqual(turn['steps'][0]['usage'],{'input_tokens':17,'output_tokens':9})
        self.assertEqual(turn['steps'][-1]['request_id'],'req_second_round')
        self.assertNotIn('do-not-store-round-secret',json.dumps(turn))
        self.assertEqual(len(project['guided_plans']),1)
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations ORDER BY rowid DESC LIMIT 1').fetchone()[0],'uncertain')
            chat_general.recover(c)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),2)

    def test_second_round_large_usage_does_not_show_first_round(self):
        self._assert_second_round_usage({'input_tokens':10**20,'output_tokens':5},'amount_out_of_range',None)

    def test_second_round_missing_usage_does_not_show_first_round(self):
        self._assert_second_round_usage({'input_tokens':19},'invalid_or_unrepresentable_usage',None)

    def test_second_round_invalid_usage_does_not_show_first_round(self):
        self._assert_second_round_usage({'input_tokens':True,'output_tokens':5},'invalid_or_unrepresentable_usage',None)

    def test_second_round_unrepresentable_usage_does_not_show_first_round(self):
        self._assert_second_round_usage({'input_tokens':10**300,'output_tokens':5},'invalid_or_unrepresentable_usage',None)

    def test_second_round_unpriced_tier_displays_current_usage(self):
        self._assert_second_round_usage({'input_tokens':19,'output_tokens':5},'unsupported_service_tier',{'input_tokens':19,'output_tokens':5},'priority')

    def test_second_round_unpriced_cache_displays_current_usage(self):
        self._assert_second_round_usage({'input_tokens':19,'output_tokens':5,'cache_read_input_tokens':3},'unsupported_cache_usage',{'input_tokens':19,'output_tokens':5})

    def _observed_usage_race(self, folder, change, upstream=None, expected_reason=None):
        upstream=upstream or response([use('plan','propose_media_plan',ARGS)],'tool_use')
        http=server(folder,0,general_chat_fixture=[upstream])
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        self.addCleanup(lambda:(http.shutdown(),http.server_close(),thread.join()))
        base='http://127.0.0.1:'+str(http.server_port)
        def state():
            with urlopen(base+'/api/state') as r:return json.load(r)
        def action(kind,**data):
            s=state();req=Request(base+'/api/action',data=json.dumps(dict(action=kind,data=data,revision=s['revision'],request_id=uuid.uuid4().hex)).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':s['token']})
            with urlopen(req) as r:return json.load(r)
        action('project',name='race',era='default',story=0)
        action('model_settings',song='race',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
        pid=contracts.project_id(http.store.workspace_id,'race')
        with http.store.connect() as c:
            ledger.patch_budget(c,http.store.workspace_id,'rehearsal:project:'+pid,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
        p=action('general_chat_preview',song='race',prompt='권리 경계 합성 시험',maximum_micro=10000)['general_chat_preview']
        identifier=action('general_chat_decide',song='race',preview_id=p['id'],manifest_sha256=p['manifest_sha256'],decision='approve',rights_confirmed=True)['turn']['id']
        entered=threading.Event();resume=threading.Event();transport=http.store.general_chat_runtime.transport;original=transport.complete
        def delayed(body):
            entered.set();self.assertTrue(resume.wait(5));result=original(body);result['_request_id']='req_fixture_123';return result
        with patch.object(transport,'complete',side_effect=delayed):
            worker=threading.Thread(target=http.store.general_chat_runtime.process_next);worker.start()
            try:
                self.assertTrue(entered.wait(5))
                if change=='cancel':action('general_chat_cancel',song='race',turn=identifier)
                else:
                    with http.store.connect() as c:c.execute('INSERT INTO asset_rights VALUES (?,?,?,?)',('c'*64,1,'synthetic revoke',3))
            finally:resume.set();worker.join(10)
            self.assertFalse(worker.is_alive())
        p=state()['projects']['race'];turn=p['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown')
        self.assertEqual(turn['usage'],{'input_tokens':100,'output_tokens':100})
        self.assertEqual(turn['steps'][-1]['request_id'],'req_fixture_123')
        if expected_reason:self.assertEqual(turn['pricing_status'],expected_reason)
        self.assertFalse(p.get('guided_plans'))
        with http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual FROM reservations').fetchone(),('uncertain',None) if expected_reason else ('settled',60))
        self.assertFalse(http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages),1)
