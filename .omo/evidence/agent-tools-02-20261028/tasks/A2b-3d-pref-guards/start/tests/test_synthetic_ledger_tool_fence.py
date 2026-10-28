"""Synthetic chat tool calls must not outlive cancellation or their approval."""
import unittest
import json
import threading
import uuid
from copy import deepcopy
from unittest.mock import patch
from urllib.request import Request, urlopen

from app import server
import chat_runtime
import chat_sessions
import test_chat_runtime as fixtures


class SyntheticToolFenceTest(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.ChatRuntimeTest('test_cancel_after_message_preserves_cost_but_does_not_apply_tools')
  self.fixture.setUp()
  self.addCleanup(self.fixture.doCleanups)
  self.fixture.connect(fixtures.Fake([fixtures.response([fixtures.use('plan','propose_media_plan',fixtures.ARGS)],'tool_use'),fixtures.response()]))
  self.identifier=self.fixture.enqueue()

 def assert_cancelled_without_plan(self):
  self.assertEqual(self.fixture.turn()['status'],'cancelled')
  self.assertFalse(self.fixture.st.state()['projects']['A'].get('guided_plans'))
  self.assertEqual(len(self.fixture.adapter.messages),1)

 def test_cancel_after_fresh_before_pending_tool(self):
  f=self.fixture;original=f.runtime._fresh;calls=[0]
  def race(turn):
   original(turn);calls[0]+=1
   if calls[0]==4:f.call('chat_cancel',song='A',turn=self.identifier)
  f.runtime._fresh=race
  with patch.object(chat_runtime,'claim_tool',wraps=chat_runtime.claim_tool) as guard:
   f.runtime.process_next()
  self.assertEqual(guard.call_count,1)
  self.assert_cancelled_without_plan()

 def test_cancel_after_count_fresh_before_message_claim(self):
  f=self.fixture;original=f.runtime._fresh;calls=[0]
  def race(turn):
   original(turn);calls[0]+=1
   if calls[0]==2:f.call('chat_cancel',song='A',turn=self.identifier)
  f.runtime._fresh=race
  f.runtime.process_next()
  self.assertEqual(f.turn()['status'],'cancelled')
  self.assertEqual(f.adapter.messages,[])
  self.assertEqual(f.rows()[0][1],0)

 def test_changed_approval_after_count_before_message_claim(self):
  f=self.fixture;original=f.runtime._fresh;calls=[0]
  def race(turn):
   original(turn);calls[0]+=1
   if calls[0]==2:f.runtime.approval['price_revision']='changed'
  f.runtime._fresh=race
  f.runtime.process_next()
  self.assertEqual(f.turn()['status'],'blocked_before_message')
  self.assertEqual(f.adapter.messages,[])
  self.assertEqual(f.rows()[0][1],0)

 def pause_journal_message_update(self,fail_release=False):
  f=self.fixture;original=f.runtime.journal.update;waiting=threading.Event();resume=threading.Event();errors=[]
  def update(identifier,state,metadata,**kwargs):
   if fail_release and kwargs.get('release'):raise OSError('injected journal release failure')
   result=original(identifier,state,metadata,**kwargs)
   if state=='message_started':
    waiting.set()
    if not resume.wait(5):raise RuntimeError('test synchronization timeout')
   return result
  f.runtime.journal.update=update
  def run():
   try:f.runtime.process_next()
   except Exception as exc:errors.append(exc)
  worker=threading.Thread(target=run);worker.start()
  self.addCleanup(lambda:(resume.set(),worker.join(5)))
  self.assertTrue(waiting.wait(5),'worker did not reach journal boundary')
  return resume,worker,errors

 def finish_paused_worker(self,resume,worker,errors):
  resume.set();worker.join(5)
  self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
  self.assertEqual(self.fixture.adapter.messages,[])

 def test_cancel_during_journal_update_before_adapter_releases_hold(self):
  f=self.fixture;resume,worker,errors=self.pause_journal_message_update()
  f.call('chat_cancel',song='A',turn=self.identifier)
  self.finish_paused_worker(resume,worker,errors)
  self.assertEqual(f.turn()['status'],'cancelled')
  self.assertEqual(f.rows()[0],('blocked_before_message',0,None))

 def test_approval_change_during_journal_update_before_adapter_releases_hold(self):
  f=self.fixture;resume,worker,errors=self.pause_journal_message_update()
  f.runtime.approval['price_revision']='changed'
  self.finish_paused_worker(resume,worker,errors)
  self.assertEqual(f.turn()['status'],'blocked_before_message')
  self.assertEqual(f.rows()[0],('blocked_before_message',0,None))

 def test_recovery_during_journal_update_before_adapter_preserves_unknown(self):
  f=self.fixture;resume,worker,errors=self.pause_journal_message_update()
  with f.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');chat_runtime.recover(c)
  self.finish_paused_worker(resume,worker,errors)
  self.assertEqual(f.turn()['status'],'outcome_unknown')
  self.assertEqual(f.rows()[0],('blocked_before_message',0,None))
  self.assertFalse(f.runtime.process_next())

 def test_journal_release_failure_after_cancel_retains_unknown_hold(self):
  f=self.fixture;resume,worker,errors=self.pause_journal_message_update(fail_release=True)
  f.call('chat_cancel',song='A',turn=self.identifier)
  self.finish_paused_worker(resume,worker,errors)
  self.assertEqual(f.turn()['status'],'outcome_unknown')
  self.assertEqual(f.rows()[0],('message_started',2458,None))
  self.assertEqual(f.turn()['steps'][0]['journal_failure']['category'],'update_failed')

 def test_cancel_after_pending_before_tool_transaction(self):
  f=self.fixture;original=f.st.mutate
  def race(request):
   if request['action']=='production_tool':
    f.call('chat_cancel',song='A',turn=self.identifier)
    # Model a request refreshed after cancellation: rejection must come from
    # the transaction's turn fence, not just optimistic revision checking.
    request=deepcopy(request)
    with f.st.connect() as c:
     revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
    p=json.loads(body)['projects']['A'];request['revision']=revision
    request['conversation_revision']=chat_sessions.resolve(p,request['conversation_id'])['revision']
    request['shared_version']=chat_sessions.shared_fingerprint(p)
   return original(request)
  f.st.mutate=race
  with patch.object(chat_runtime,'claim_tool',wraps=chat_runtime.claim_tool) as guard:
   f.runtime.process_next()
  self.assertEqual(guard.call_count,1)
  self.assert_cancelled_without_plan()

 def test_changed_approval_before_tool_transaction_blocks_side_effect(self):
  f=self.fixture;original=f.st.mutate
  def race(request):
   if request['action']=='production_tool':f.runtime.approval['price_revision']='changed'
   return original(request)
  f.st.mutate=race
  f.runtime.process_next()
  self.assertEqual(f.turn()['status'],'response_validation_failed')
  self.assertFalse(f.st.state()['projects']['A'].get('guided_plans'))
  self.assertEqual(len(f.adapter.messages),1)

 def test_restart_fences_late_worker_without_applying_tool(self):
  f=self.fixture
  def restart():
   with f.st.connect() as c:
    c.execute('BEGIN IMMEDIATE');chat_runtime.recover(c)
  f.adapter.on_message=restart
  f.runtime.process_next()
  self.assertEqual(f.turn()['status'],'outcome_unknown')
  self.assertFalse(f.st.state()['projects']['A'].get('guided_plans'))
  self.assertEqual(len(f.adapter.messages),1)

 def test_http_cancel_race_blocks_tool_and_persists_status(self):
  f=self.fixture
  http=server(f.root,0,chat_configuration=dict(adapter=f.adapter,approval=f.runtime.approval,journal_path=f.journal))
  thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
  def close():http.shutdown();http.server_close();thread.join()
  self.addCleanup(close)
  base='http://127.0.0.1:'+str(http.server_port);runtime=http.store.chat_runtime
  original=runtime._fresh;calls=[0];statuses=[]
  def race(turn):
   original(turn);calls[0]+=1
   if calls[0]==4:
    with urlopen(base+'/api/state') as r:state=json.load(r)
    request=dict(action='chat_cancel',data=dict(song='A',turn=self.identifier),revision=state['revision'],request_id=uuid.uuid4().hex)
    req=Request(base+'/api/action',data=json.dumps(request).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':http.token})
    with urlopen(req) as r:statuses.append((r.status,json.load(r)['chat_turn']['status']))
  runtime._fresh=race
  self.assertTrue(runtime.process_next())
  with urlopen(base+'/api/state') as r:state=json.load(r)
  self.assertEqual(statuses,[(200,'cancel_requested')])
  self.assertEqual(state['projects']['A']['chat_turns'][-1]['status'],'cancelled')
  self.assertFalse(state['projects']['A'].get('guided_plans'))


if __name__=='__main__':unittest.main()
