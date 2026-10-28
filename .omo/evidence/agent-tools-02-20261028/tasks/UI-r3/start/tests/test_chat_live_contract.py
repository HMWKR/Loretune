"""Explicit local HTTP transport exercises; no credentials or provider access."""
import hashlib
import json
import tempfile
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import chat_general
import chat_runtime
import contracts
import ledger
from app import server
from tests.test_chat_runtime import ARGS, response, use


class Provider:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.count_started=threading.Event();self.count_wait=None
        self.message_started=threading.Event();self.message_wait=None
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                body=self.rfile.read(int(self.headers['Content-Length']))
                owner.requests.append((self.path,body,dict(self.headers)))
                started,gate=(owner.count_started,owner.count_wait) if self.path.endswith('count_tokens') else (owner.message_started,owner.message_wait)
                started.set()
                if gate and not gate.wait(5):return
                value={'input_tokens':100} if self.path.endswith('count_tokens') else owner.replies.pop(0)
                if value=='drop':
                    self.connection.close(); return
                raw=json.dumps(value).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
        self.http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
    def close(self):self.http.shutdown();self.http.server_close();self.thread.join()
class LiveContractHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.provider=Provider([response()]);self.addCleanup(self.provider.close)
        self.keys=[]
        def key(name):self.keys.append(name);return 'synthetic-key-not-real'
        count=chat_general.LoopbackTransport(self.provider.http.server_port)
        message=chat_general.LoopbackTransport(self.provider.http.server_port)
        adapter=chat_runtime.AnthropicChatAdapter(key,enabled=True,count_transport=count,message_transport=message)
        transport=chat_general.LiveTransport(adapter,'local-test-account',1,test_only=True)
        self.http=server(self.tmp.name,0,general_chat_live=transport)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
        self.base='http://127.0.0.1:'+str(self.http.server_port)
        self.action('project',name='A',era='default',story=0)
        self.action('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
        self.pid=contracts.project_id(self.http.store.workspace_id,'A')
        with self.http.store.connect() as c:
            ledger.patch_budget(c,self.http.store.workspace_id,'rehearsal-live:project:'+self.pid,
                                dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
    def close(self):self.http.shutdown();self.http.server_close();self.thread.join()
    def state(self):
        with urlopen(self.base+'/api/state') as r:return json.load(r)
    def send(self,payload):
        request=Request(self.base+'/api/action',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':self.state()['token']})
        try:
            with urlopen(request) as r:return r.status,json.load(r)
        except HTTPError as e:
            with e:return e.code,json.load(e)
    def action(self,action,**data):
        return self.send(dict(action=action,data=data,revision=self.state()['revision'],request_id=uuid.uuid4().hex))
    def preview(self,*,total=10000):
        status,value=self.action('general_chat_preview',song='A',prompt='음악에 맞는 장면을 계획해 줘',maximum_micro=10000,total_maximum_micro=total)
        self.assertEqual(status,200,value);return value['general_chat_preview']
    def approve(self,p,*,decision='approve',rights=True):
        return self.action('general_chat_decide',song='A',preview_id=p['id'],manifest_sha256=p['manifest_sha256'],decision=decision,rights_confirmed=rights)
    def test_exact_approved_bytes_and_estimate_is_not_confirmed(self):
        p=self.preview();self.assertEqual((self.keys,self.provider.requests),([],[]))
        self.assertEqual(p['mode'],'contract-live-test');self.assertEqual(p['destination'],'http://127.0.0.1:'+str(self.provider.http.server_port))
        self.assertEqual(p['message_body']['thinking'],{'type':'disabled'})
        self.assertEqual(self.approve(p)[0],200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual([r[0] for r in self.provider.requests],['/count_tokens','/messages'])
        self.assertEqual(hashlib.sha256(self.provider.requests[0][1]).hexdigest(),p['count_wire_sha256'])
        self.assertEqual(hashlib.sha256(self.provider.requests[1][1]).hexdigest(),p['message_wire_sha256'])
        state=self.state()['projects']['A'];turn=state['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'completed');self.assertFalse(turn['billing_confirmed'])
        with self.http.store.connect() as c:
            b=ledger.budget(c,self.http.store.workspace_id,'rehearsal-live:project:'+self.pid)
            self.assertEqual(b['data']['netConfirmed']['amount'],'0');self.assertEqual(b['data']['netEstimated']['amount'],'0.00006')
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'estimated')
        self.assertEqual(self.keys,['Anthropic_KEY','Anthropic_KEY'])
    def test_test_mode_cannot_use_real_transport_or_real_key(self):
        real=chat_runtime.AnthropicChatAdapter(lambda _: 'never-read',enabled=True)
        with self.assertRaises(ValueError):chat_general.LiveTransport(real,'acct',1,test_only=True)
        with self.assertRaises(ValueError):chat_general.LiveTransport(self.http.store.general_chat_runtime.transport.adapter,'acct',1)
        local=chat_general.LoopbackTransport(self.provider.http.server_port)
        with self.assertRaises(ValueError):local(chat_runtime.anthropic.ENDPOINT,{'x-api-key':'not-synthetic'}, {})
        self.assertEqual((self.keys,self.provider.requests),([],[]))
    def test_config_change_invalidates_approved_preview(self):
        p=self.preview();transport=self.http.store.general_chat_runtime.transport
        transport.connection_revision+=1
        self.assertEqual(self.approve(p)[0],400);self.assertEqual((self.keys,self.provider.requests),([],[]))
    def test_real_configuration_fails_closed_without_reading_credentials_or_sending(self):
        called=[]
        adapter=chat_runtime.AnthropicChatAdapter(lambda name:called.append(name),enabled=True)
        transport=chat_general.LiveTransport(adapter,'unverified-account',1)
        with self.assertRaises(ValueError):server(self.tmp.name,0,general_chat_live=transport)
        with self.assertRaises(ValueError):chat_general.Runtime(self.http.store,transport)
        with self.assertRaises(ValueError):transport.count({})
        with self.assertRaises(ValueError):transport.complete({})
        self.assertEqual((called,self.provider.requests),([],[]))
    def test_loopback_endpoint_is_part_of_manifest(self):
        p=self.preview();transport=self.http.store.general_chat_runtime.transport
        self.assertIn(str(self.provider.http.server_port),p['endpoints']['count'])
        transport.adapter.message_transport.port=1
        self.assertEqual(self.approve(p)[0],400);self.assertEqual((self.keys,self.provider.requests),([],[]))
    def test_tool_result_requires_separate_exact_consent(self):
        self.provider.replies=[response([use('plan','propose_media_plan',ARGS)],'tool_use'),response()]
        p=self.preview();self.assertEqual(self.approve(p)[0],200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        state=self.state()['projects']['A'];turn=state['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'awaiting_continuation_approval');self.assertEqual(len(self.provider.requests),2)
        next_preview=state['general_chat_previews'][-1]
        self.assertIn('tool_result',json.dumps(next_preview['message_body']))
        self.assertEqual(self.approve(next_preview,rights=False)[0],400);self.assertEqual(len(self.provider.requests),2)
        self.assertEqual(self.approve(next_preview)[0],200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'completed')
        self.assertEqual(hashlib.sha256(self.provider.requests[-1][1]).hexdigest(),next_preview['message_wire_sha256'])
    def test_rejection_stale_and_competing_approval_do_not_send(self):
        p=self.preview();self.assertEqual(self.approve(p,rights=False)[0],400)
        self.assertEqual(self.approve(p,decision='reject')[0],200);self.assertEqual(self.provider.requests,[])
        p=self.preview();self.action('shot',song='A',shot='s',description='changed')
        self.assertEqual(self.approve(p)[0],400);self.assertEqual(self.provider.requests,[])
        p=self.preview();rev=self.state()['revision']
        def send(_):
            return self.send(dict(action='general_chat_decide',data=dict(song='A',preview_id=p['id'],manifest_sha256=p['manifest_sha256'],decision='approve',rights_confirmed=True),revision=rev,request_id=uuid.uuid4().hex))[0]
        with ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(send,range(2)))
        self.assertEqual(codes.count(200),1);self.assertEqual(self.provider.requests,[])
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
    def test_transport_loss_keeps_reservation_and_does_not_repeat(self):
        self.provider.replies=['drop'];p=self.preview();self.assertEqual(self.approve(p)[0],200)
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'outcome_unknown')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
        self.assertFalse(self.http.store.general_chat_runtime.process_next());self.assertEqual(len(self.provider.requests),2)
    def test_uncertain_budget_blocks_new_approval_and_already_queued_transmission(self):
        p=self.preview();self.assertEqual(self.approve(p)[0],200)
        scope='rehearsal-live:project:'+self.pid
        with self.http.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');b=ledger.budget(c,self.http.store.workspace_id,scope)
            r=ledger.command(c,self.http.store.workspace_id,scope,'reserve',dict(money={'amount':'0.01','currency':'USD'},budget_revision=b['revision'],expires=time.time()+60,job='other-job'),'other-reserve')
            ledger.command(c,self.http.store.workspace_id,scope,'uncertain',{'reservation':r['reservation']},'other-uncertain')
        self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.provider.requests,[])
        with self.http.store.connect() as c:
            self.assertEqual(c.execute("SELECT state FROM reservations WHERE job='other-job'").fetchone()[0],'uncertain')
            self.assertEqual(c.execute("SELECT state FROM reservations WHERE job!='other-job'").fetchone()[0],'cancelled')
        p=self.preview();self.assertEqual(self.approve(p)[0],400);self.assertEqual(self.provider.requests,[])
        with self.http.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            ledger.command(c,self.http.store.workspace_id,scope,'settle',{'reservation':r['reservation'],'money':{'amount':'0.001','currency':'USD'}},'other-reconciled')
        self.assertEqual(self.approve(p)[0],200)
    def test_cancel_after_count_transmission_blocks_message(self):
        self.provider.count_wait=threading.Event();p=self.preview();status,result=self.approve(p)
        self.assertEqual(status,200);worker=threading.Thread(target=self.http.store.general_chat_runtime.process_next);worker.start()
        self.assertTrue(self.provider.count_started.wait(5))
        self.assertEqual(self.action('general_chat_cancel',song='A',turn=result['turn']['id'])[0],200)
        self.provider.count_wait.set();worker.join(10);self.assertFalse(worker.is_alive())
        turn=self.state()['projects']['A']['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'cancelled');self.assertEqual(turn['count_status'],'response_received')
        self.assertEqual([r[0] for r in self.provider.requests],['/count_tokens'])
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
    def test_cancel_after_message_preserves_observed_estimate_and_blocks_tools(self):
        self.provider.replies=[response([use('plan','propose_media_plan',ARGS)],'tool_use')]
        self.provider.message_wait=threading.Event();p=self.preview();status,result=self.approve(p);self.assertEqual(status,200)
        worker=threading.Thread(target=self.http.store.general_chat_runtime.process_next);worker.start()
        self.assertTrue(self.provider.message_started.wait(5))
        self.assertEqual(self.action('general_chat_cancel',song='A',turn=result['turn']['id'])[0],200)
        self.provider.message_wait.set();worker.join(10);self.assertFalse(worker.is_alive())
        project=self.state()['projects']['A'];turn=project['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'cancelled');self.assertEqual(turn['usage'],{'input_tokens':100,'output_tokens':100})
        self.assertEqual(turn['pricing_status'],'priced');self.assertIsNone(turn['answer'])
        self.assertEqual(project.get('guided_plans',[]),[]);self.assertFalse(turn['billing_confirmed'])
        with self.http.store.connect() as c:
            stored=chat_general.get_row(c,'general_chat_turns',turn['id'])
            self.assertNotIn('pending_tool',stored)
            self.assertEqual(c.execute('SELECT state,actual FROM reservations WHERE id=?',(stored['reservation'],)).fetchone(),('estimated',60))
            self.assertEqual(c.execute('SELECT operation,state FROM provider_attempts WHERE reservation=? ORDER BY operation',(stored['reservation'],)).fetchall(),[('chat-count','observed'),('chat-message','observed')])
        self.assertFalse(self.http.store.general_chat_runtime.process_next());self.assertEqual(len(self.provider.requests),2)
    def test_restart_does_not_repeat_interrupted_approved_round(self):
        p=self.preview();status,result=self.approve(p);self.assertEqual(status,200)
        with self.http.store.connect() as c:
            turn=chat_general.get_row(c,'general_chat_turns',result['turn']['id']);turn['status']='running';chat_general.put(c,'general_chat_turns',turn)
        reopened=server(self.tmp.name,0,general_chat_live=self.http.store.general_chat_runtime.transport)
        try:
            with reopened.store.connect() as c:
                turn=chat_general.get_row(c,'general_chat_turns',turn['id']);self.assertEqual(turn['status'],'outcome_unknown')
                self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
            self.assertFalse(reopened.store.general_chat_runtime.process_next());self.assertEqual(self.provider.requests,[])
        finally:reopened.server_close()
    def test_turn_total_cap_stops_followup(self):
        self.provider.replies=[response([use('plan','propose_media_plan',ARGS)],'tool_use')]
        p=self.preview(total=3687);  # exactly one worst round (D20: MAX_INPUT 16384)
        self.assertEqual(self.approve(p)[0],200);self.assertTrue(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.provider.requests),2)
        self.assertEqual(self.state()['projects']['A']['general_chat_turns'][-1]['status'],'limit_reached')
        self.assertFalse(self.http.store.general_chat_runtime.process_next())


if __name__=='__main__':unittest.main()
