import hashlib,io,json,sqlite3,tempfile,threading,time,unittest,uuid
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock
from app import Store
import anthropic_ontology as provider
import chat_runtime as chat
import contracts,model_selection

PROMPT='Synthetic: look up Mira, save a proposed studio scene and report its receipt.'
ARGS=dict(goal='Mira synthetic clip',scenes='Mira in studio wearing scoped red coat',style='',constraints='Preserve global blue coat',kind='narrative')
def response(blocks=None,stop='end_turn'):
 return dict(_request_id='synthetic-request',stop_reason=stop,usage=dict(input_tokens=100,output_tokens=100),content=blocks or [dict(type='text',text='Saved proposal only; no approval or generated media.')])
def use(identifier,name,args):return dict(type='tool_use',id=identifier,name=name,input=args)
class SyntheticResponse(io.BytesIO):
 def __init__(self,raw=b'{}',*,status=200,url=provider.ENDPOINT,headers=None):
  super().__init__(raw);self.status=status;self.url=url;self.headers={'Content-Type':'application/json'} if headers is None else headers
 def geturl(self):return self.url
class SyntheticOpener:
 """No socket path; fixtures configure a memory response or an exception."""
 def __init__(self):self.open=Mock()
 @property
 def requests(self):return [call.args[0] for call in self.open.call_args_list]
class SyntheticTransportAdapter:
 """Test-only wrapper around the production adapter with pinned fake openers."""
 mode='contract-fake'
 def __init__(self,adapter,count_opener,message_opener):
  self.adapter=adapter;self.count_opener=count_opener;self.message_opener=message_opener
  self._validate()
 def _validate(self):
  if (type(self.adapter) is not chat.AnthropicChatAdapter or
      type(self.adapter.count_transport) is not provider.BoundedCountTransport or
      type(self.adapter.message_transport) is not provider.BoundedMessagesTransport or
      self.adapter.count_transport._opener is not self.count_opener or
      self.adapter.message_transport._opener is not self.message_opener or
      type(self.count_opener) is not SyntheticOpener or type(self.message_opener) is not SyntheticOpener):
   raise ValueError('test transport openers changed')
  for opener in (self.count_opener,self.message_opener):
   operation=opener.open
   if type(operation).__mro__[1:2] != (Mock,) or operation._mock_wraps is not None:raise ValueError('test opener must be synthetic')
   failure=operation.side_effect
   if failure is not None and not isinstance(failure,BaseException):raise ValueError('test opener must be synthetic')
   if failure is None and type(operation.return_value) is not SyntheticResponse:raise ValueError('test response must be synthetic')
 def preflight(self,body):self._validate();return self.adapter.preflight(body)
 def count(self,body):self._validate();return self.adapter.count(body)
 def complete(self,body):self._validate();return self.adapter.complete(body)
class Fake:
 mode='contract-fake'
 def __init__(self,responses=()):self.responses=list(responses);self.counts=[];self.messages=[];self.on_count=None;self.on_message=None;self.tokens=100
 def count(self,body):
  self.counts.append(deepcopy(body))
  if self.on_count:self.on_count()
  return self.tokens
 def complete(self,body):
  self.messages.append(deepcopy(body))
  if self.on_message:self.on_message()
  value=self.responses.pop(0)
  if isinstance(value,Exception):raise value
  return deepcopy(value)
class ChatRuntimeTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.st=Store(self.root)
  self.call('setting',text='Mira wears a blue coat globally.',era='default',valid_from=0,valid_to=9)
  self.call('project',name='A',era='default',story=0)
  self.call('project',name='B',era='default',story=0)
  self.call('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  self.journal=self.root/'synthetic-usage.sqlite3'
 def call(self,action,**data):return self.st.mutate(dict(action=action,data=data,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def connect(self,adapter):
  self.adapter=adapter
  approval=dict(model=provider.MODEL,workspace_id=self.st.workspace_id,project_id=contracts.project_id(self.st.workspace_id,'A'),synthetic_only=True,expires=time.time()+300,
                context_hash=model_selection.snapshot(self.st.state()['projects']['A'])['sha256'],prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],price_revision='haiku-5-5-20261027-tiered',max_rounds=4)
  self.runtime=chat.ChatRuntime(self.st,adapter,approval,self.journal);self.st.chat_runtime=self.runtime
 def enqueue(self):return self.call('chat_turn',song='A',prompt=PROMPT)['chat_turn']['id']
 def turn(self):return self.st.state()['projects']['A']['chat_turns'][-1]
 def rows(self):
  with closing(sqlite3.connect(self.journal)) as c:return c.execute('SELECT state,held_micro,actual_micro FROM trials ORDER BY rowid').fetchall()
 def test_canonical_tool_plan_final_reply_persist_and_truthful_provenance(self):
  self.connect(Fake([response([use('c1','search_project_context',{'query':'Mira'})],'tool_use'),response([use('c2','propose_media_plan',ARGS)],'tool_use'),response()]))
  self.enqueue();self.assertTrue(self.runtime.process_next());self.assertFalse(self.runtime.process_next())
  t=self.turn();self.assertEqual(t['status'],'completed');self.assertEqual(t['answer_review'],'unreviewed');self.assertFalse(t['billing_confirmed'])
  state=Store(self.root).state();p=state['projects']['A'];self.assertEqual(len(p['guided_plans']),1);plan=p['guided_plans'][0]
  self.assertEqual(plan['source']['mode'],'contract-fake');self.assertEqual(plan['status'],'proposed');self.assertEqual(plan['scenes'][0]['description'],ARGS['scenes'])
  self.assertEqual(len(self.adapter.messages),3);self.assertIn('Mira wears a blue coat',json.dumps(self.adapter.messages[1]))
  self.assertIn(plan['id'],json.dumps(self.adapter.messages[2]));self.assertEqual(state['generation_jobs'],[]);self.assertFalse(p['production_runs'][0]['live_model_called'])
  self.assertEqual([r[2] for r in self.rows()],[60,60,60])
 def test_parallel_tool_results_one_message_and_duplicate_tool_idempotence(self):
  blocks=[use('lookup','search_project_context',{'query':'Mira'}),use('plan','propose_media_plan',ARGS)]
  self.connect(Fake([response(blocks,'tool_use'),response([blocks[1]],'tool_use'),response()]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'completed');self.assertEqual(len(self.st.state()['projects']['A']['guided_plans']),1)
  self.assertEqual(len(self.adapter.messages[1]['messages'][-1]['content']),2)
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM action_jobs').fetchone()[0],0)
 def test_duplicate_enqueue_same_request_and_competing_new_request(self):
  self.connect(Fake([response()]));req=dict(action='chat_turn',data=dict(song='A',prompt=PROMPT),revision=self.st.state()['revision'],request_id='one')
  first=self.st.mutate(req);self.assertEqual(self.st.mutate(req),first)
  with self.assertRaises(ValueError):self.enqueue()
  self.assertEqual(len(self.st.state()['projects']['A']['chat_turns']),1)
 def test_unapproved_prompt_foreign_project_and_model_authority_rejected(self):
  self.connect(Fake())
  for data in [dict(song='A',prompt='actual user material'),dict(song='B',prompt=PROMPT),dict(song='A',prompt=PROMPT,approved=True)]:
   with self.assertRaises(ValueError):self.call('chat_turn',**data)
  self.assertFalse(self.journal.exists());self.assertEqual(self.adapter.counts,[])
 def test_cancel_queued_never_calls_provider(self):
  self.connect(Fake());identifier=self.enqueue();self.call('chat_cancel',song='A',turn=identifier)
  self.assertFalse(self.runtime.process_next());self.assertEqual(self.turn()['status'],'cancelled');self.assertEqual(self.adapter.counts,[])
 def test_cancel_after_message_preserves_cost_but_does_not_apply_tools(self):
  self.connect(Fake([response([use('plan','propose_media_plan',ARGS)],'tool_use')]))
  identifier=self.enqueue();self.adapter.on_message=lambda:self.call('chat_cancel',song='A',turn=identifier)
  self.runtime.process_next();self.assertEqual(self.turn()['status'],'cancelled');self.assertEqual(self.rows()[0][2],60)
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_context_change_after_count_prevents_message_and_releases(self):
  self.connect(Fake());self.enqueue();self.adapter.on_count=lambda:self.call('shot',song='A',shot='new',description='changed')
  self.runtime.process_next();self.assertEqual(self.turn()['status'],'blocked_before_message');self.assertEqual(self.adapter.messages,[]);self.assertEqual(self.rows()[0][1],0)
 def test_truncation_is_paid_invalid_response_no_plan(self):
  self.connect(Fake([response([use('plan','propose_media_plan',ARGS)],'max_tokens')]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'response_validation_failed');self.assertEqual(self.rows()[0][2],60);self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_unknown_retains_reservation_and_blocks_new_enqueue(self):
  self.connect(Fake([TimeoutError('sensitive upstream message')]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'outcome_unknown');self.assertEqual(self.rows()[0],('outcome_unknown',2458,None));self.assertNotIn('sensitive',json.dumps(self.turn()))
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_live_unknown_blocks_another_project_before_count_or_message(self):
  adapter=Fake([TimeoutError('synthetic timeout')]);adapter.mode='anthropic-live'
  self.connect(adapter);self.enqueue();self.runtime.process_next()
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  self.call('model_settings',song='B',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  self.runtime.approval['project_id']=contracts.project_id(self.st.workspace_id,'B')
  self.runtime.approval['context_hash']=model_selection.snapshot(self.st.state()['projects']['B'])['sha256']
  self.call('chat_turn',song='B',prompt=PROMPT);self.runtime.process_next()
  self.assertEqual(self.st.state()['projects']['B']['chat_turns'][-1]['status'],'blocked_before_message')
  self.assertEqual((len(adapter.counts),len(adapter.messages)),(1,1))
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
 def test_live_preserved_reservation_cannot_send_after_other_attempt_becomes_unknown(self):
  adapter=Fake([response()]);adapter.mode='anthropic-live';self.connect(adapter)
  self.runtime.journal.reserve('first','hash','first',100,10000)
  adapter.on_count=lambda:self.runtime.journal.update('first','outcome_unknown',{'messages_submitted':True})
  self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.turn()['status'],'blocked_before_message')
  self.assertEqual((len(adapter.counts),len(adapter.messages)),(1,0))
  self.assertEqual(self.rows(),[('outcome_unknown',100,None),('blocked_before_message',0,None)])
 def test_input_token_cap_no_message_and_no_fake_billing(self):
  self.connect(Fake());self.adapter.tokens=4097;self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'blocked_before_message');self.assertEqual(self.adapter.messages,[]);self.assertEqual(self.rows()[0][1],0)
 def test_reported_input_above_cap_is_recorded_and_stops_tool_execution(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use');result['usage']={'input_tokens':4097,'output_tokens':100}
  self.connect(Fake([result,response()]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'response_validation_failed');self.assertFalse(self.turn()['billing_confirmed'])
  self.assertEqual(self.turn()['steps'][0]['failure']['category'],'usage_limit_exceeded')
  self.assertEqual(self.rows()[0][2],460);self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
  self.assertEqual(len(self.adapter.messages),1);self.assertFalse(self.runtime.process_next())
 def test_missing_usage_keeps_reservation_unknown_and_blocks_another_turn(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use');result.pop('usage')
  self.connect(Fake([result]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'outcome_unknown');self.assertFalse(self.turn()['billing_confirmed'])
  self.assertEqual(self.turn()['steps'][0]['failure']['category'],'usage_unsettled')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None));self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_nested_unpriced_usage_preserves_legacy_journal_reservation(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use')
  result['usage'].update(service_tier='priority',speed='fast',inference_geo='us',server_tool_use={'web_search_requests':1})
  self.connect(Fake([result]));self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.turn()['steps'][0]['failure']['category'],'usage_unsettled')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_mismatched_response_model_preserves_legacy_reservation(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use');result['model']='different-model'
  self.connect(Fake([result]));self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_live_mode_requires_response_model_without_contacting_provider(self):
  adapter=Fake([response([use('plan','propose_media_plan',ARGS)],'tool_use')]);adapter.mode='anthropic-live'
  self.connect(adapter);self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_live_mode_requires_billing_evidence_without_contacting_provider(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use');result['model']=provider.MODEL
  adapter=Fake([result]);adapter.mode='anthropic-live'
  self.connect(adapter);self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_real_adapter_class_cannot_bypass_model_check_by_fake_mode(self):
  def no_credentials(_):raise AssertionError('credential lookup prohibited in test')
  live=chat.UsageJournal(self.journal,'anthropic-live');live.reserve('prior','h','prior',2458,10000)
  live.update('prior','outcome_unknown',{'messages_submitted':True})
  adapter=chat.AnthropicChatAdapter(no_credentials);adapter.mode='contract-fake'
  adapter.preflight=lambda body:None;adapter.count=lambda body:100
  adapter.complete=lambda body:response([use('plan','propose_media_plan',ARGS)],'tool_use')
  with self.assertRaises(ValueError):self.connect(adapter)
  self.assertEqual(self.rows(),[('outcome_unknown',2458,None)])
 def test_real_adapter_mode_change_after_connect_is_rejected_before_reservation(self):
  def no_credentials(_):raise AssertionError('credential lookup prohibited in test')
  adapter=chat.AnthropicChatAdapter(no_credentials);self.connect(adapter);adapter.mode='contract-fake'
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.journal.exists())
 def test_synthetic_wrapper_rejects_default_and_changed_transport(self):
  def no_credentials(_):raise AssertionError('credential lookup prohibited in test')
  count_opener=SyntheticOpener();message_opener=SyntheticOpener()
  count_opener.open.return_value=SyntheticResponse();message_opener.open.return_value=SyntheticResponse()
  actual=chat.AnthropicChatAdapter(no_credentials)
  with self.assertRaises(ValueError):SyntheticTransportAdapter(actual,count_opener,message_opener)
  adapter=chat.AnthropicChatAdapter(no_credentials,
   count_transport=provider.BoundedCountTransport(opener=count_opener),
   message_transport=provider.BoundedMessagesTransport(opener=message_opener))
  fixture_adapter=SyntheticTransportAdapter(adapter,count_opener,message_opener)
  adapter.message_transport._opener=None
  with self.assertRaises(ValueError):fixture_adapter.preflight({})
 def test_synthetic_wrapper_rejects_urllib_and_callable_side_effect(self):
  def no_credentials(_):raise AssertionError('credential lookup prohibited in test')
  real_opener=urllib.request.build_opener()
  fake=SyntheticOpener();fake.open.return_value=SyntheticResponse()
  actual=chat.AnthropicChatAdapter(no_credentials,
   count_transport=provider.BoundedCountTransport(opener=real_opener),
   message_transport=provider.BoundedMessagesTransport(opener=fake))
  with self.assertRaises(ValueError):SyntheticTransportAdapter(actual,real_opener,fake)
  actual.count_transport=provider.BoundedCountTransport(opener=fake)
  fake.open.side_effect=lambda *_:None
  with self.assertRaises(ValueError):SyntheticTransportAdapter(actual,fake,fake)
 def test_unrecordable_usage_does_not_release_reservation(self):
  result=response();result['usage']={'input_tokens':100,'output_tokens':10**25}
  self.connect(Fake([result]));self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.turn()['steps'][0]['failure']['category'],'usage_unsettled')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  with self.assertRaises(ValueError):self.enqueue()
 def test_persistent_journal_failure_after_response_saves_unknown_and_recovery(self):
  result=response([use('plan','propose_media_plan',ARGS)],'tool_use')
  self.connect(Fake([result]));self.enqueue();original=self.runtime.journal.update;failed=[]
  def broken(identifier,state,metadata,**kwargs):
   if state=='response_received' or failed:
    failed.append(state);raise sqlite3.OperationalError('sensitive journal path')
   return original(identifier,state,metadata,**kwargs)
  self.runtime.journal.update=broken
  self.assertTrue(self.runtime.process_next())
  turn=self.turn();self.assertEqual(turn['status'],'outcome_unknown')
  self.assertEqual(turn['steps'][0]['journal_failure']['category'],'update_failed')
  self.assertFalse(turn['billing_confirmed']);self.assertNotIn('sensitive journal path',json.dumps(turn))
  self.assertEqual(self.rows()[0],('message_started',2458,None))
  self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
  self.assertEqual(self.st.state()['projects']['A']['production_runs'][-1]['state'],'outcome_unknown')
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
  restarted=Store(self.root)
  with restarted.connect() as c:chat.recover(c)
  self.assertEqual(restarted.state()['projects']['A']['chat_turns'][-1]['status'],'outcome_unknown')
  self.assertEqual(self.rows()[0],('message_started',2458,None))
 def test_cancel_after_submission_cannot_hide_unknown_outcome(self):
  self.connect(Fake([TimeoutError('sensitive upstream message')]));identifier=self.enqueue()
  self.adapter.on_message=lambda:self.call('chat_cancel',song='A',turn=identifier)
  self.runtime.process_next();self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_cancel_and_journal_failure_remain_unknown(self):
  self.connect(Fake([response()]));identifier=self.enqueue();original=self.runtime.journal.update;failed=[]
  self.adapter.on_message=lambda:self.call('chat_cancel',song='A',turn=identifier)
  def broken(attempt,state,metadata,**kwargs):
   if state=='response_received' or failed:
    failed.append(state);raise sqlite3.OperationalError('journal unavailable')
   return original(attempt,state,metadata,**kwargs)
  self.runtime.journal.update=broken;self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'outcome_unknown')
  self.assertEqual(self.turn()['steps'][0]['journal_failure']['category'],'update_failed')
  self.assertEqual(self.rows()[0],('message_started',2458,None))
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_unknown_state_write_failure_propagates_and_restart_recovers(self):
  self.connect(Fake([response()]));identifier=self.enqueue();update=self.runtime.journal.update;save=self.runtime._save;failed=[]
  def broken_update(attempt,state,metadata,**kwargs):
   if state=='response_received' or failed:
    failed.append(state);raise sqlite3.OperationalError('journal unavailable')
   return update(attempt,state,metadata,**kwargs)
  def broken_save(turn):
   if turn['status']=='outcome_unknown':raise sqlite3.OperationalError('turn store unavailable')
   return save(turn)
  self.runtime.journal.update=broken_update;self.runtime._save=broken_save
  with self.assertRaisesRegex(sqlite3.OperationalError,'turn store unavailable'):self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'running');self.assertEqual(self.rows()[0],('message_started',2458,None))
  restarted=Store(self.root)
  with restarted.connect() as c:chat.recover(c)
  self.assertEqual(restarted.state()['projects']['A']['chat_turns'][-1]['status'],'outcome_unknown')
  with self.assertRaises(ValueError):self.enqueue()
  self.assertFalse(self.runtime.process_next());self.assertEqual(len(self.adapter.messages),1)
 def test_restart_unknown_never_requeues_started_turn(self):
  self.connect(Fake());identifier=self.enqueue()
  with self.st.connect() as c:
   t=chat.get(c,identifier);t['status']='running';chat.put(c,t)
  self.runtime.journal.reserve('chat:'+identifier+':0','hash',identifier,2458,10000)
  restarted=Store(self.root)
  with restarted.connect() as c:chat.recover(c)
  self.assertEqual(self.turn()['status'],'outcome_unknown');self.assertFalse(self.runtime.process_next());self.assertEqual(self.rows()[0][1],2458)
 def test_two_workers_claim_only_once(self):
  self.connect(Fake([response()]));self.enqueue();entered=threading.Event();release=threading.Event()
  def block():entered.set();self.assertTrue(release.wait(5))
  self.adapter.on_count=block
  with ThreadPoolExecutor(2) as pool:
   f=pool.submit(self.runtime.process_next);self.assertTrue(entered.wait(5));other=pool.submit(self.runtime.process_next);self.assertFalse(other.result(5));release.set();self.assertTrue(f.result(5))
  self.assertEqual(len(self.adapter.messages),1);self.assertEqual(self.turn()['status'],'completed')
 def test_existing_unknown_cost_counts_toward_atomic_budget(self):
  self.connect(Fake());self.runtime.journal.reserve('prior-unknown','h','old',49_999_000,50_000_000)
  self.enqueue();self.runtime.process_next();self.assertEqual(self.turn()['status'],'blocked_before_message');self.assertEqual(self.adapter.counts,[])
 def test_disabled_connection_without_secret_reads(self):
  self.assertFalse(self.st.state()['projects']['A']['chat_connection']['available'])
  with self.assertRaises(ValueError):self.call('chat_turn',song='A',prompt=PROMPT)
 def test_real_adapter_transport_fake_secret_canary_never_persisted(self):
  secret='synthetic-key-canary';seen=[]
  def count(url,headers,body):
   self.assertEqual(url,provider.BoundedCountTransport.endpoint);self.assertEqual(headers['x-api-key'],secret);seen.append('count');return {'input_tokens':100}
  def complete(url,headers,body):
   self.assertEqual(url,provider.ENDPOINT);self.assertEqual(headers['x-api-key'],secret);seen.append('message');return response([dict(type='text',text=secret)])
  names=[]
  def supplier(name):names.append(name);return secret
  adapter=chat.AnthropicChatAdapter(supplier,enabled=True,count_transport=count,message_transport=complete)
  self.connect(adapter);self.enqueue();self.runtime.process_next()
  self.assertEqual(seen,['count','message']);self.assertEqual(names,['Anthropic_KEY','Anthropic_KEY']);self.assertEqual(self.turn()['status'],'outcome_unknown')
  for p in self.root.rglob('*'):
   if p.is_file():self.assertNotIn(secret.encode(),p.read_bytes())
 def test_adapter_success_uses_same_store_bridge_with_transport_fixture(self):
  seq=[response([use('plan','propose_media_plan',ARGS)],'tool_use'),response()]
  for item in seq:
   item['model']=provider.MODEL
   item['usage'].update(service_tier='standard',speed='standard',inference_geo='global',cache_creation_input_tokens=0,cache_read_input_tokens=0,server_tool_use={'web_fetch_requests':0,'web_search_requests':0})
  adapter=chat.AnthropicChatAdapter(lambda name:'synthetic-key',enabled=True,count_transport=lambda *args:{'input_tokens':100},message_transport=lambda *args:seq.pop(0))
  self.connect(adapter);self.enqueue();self.runtime.process_next();self.assertEqual(self.turn()['status'],'completed')
  p=self.st.state()['projects']['A'];self.assertEqual(p['guided_plans'][0]['source']['mode'],'anthropic-live')
  self.assertTrue(p['production_runs'][0]['live_model_called']) # Transport fixture, not evidence of a real API call.
 def test_real_adapter_fixture_uses_live_journal_and_blocks_after_unpriced_response(self):
  calls=[]
  def count(*args):calls.append('count');return {'input_tokens':100}
  def message(*args):
   calls.append('message');result=response();result['model']=provider.MODEL;return result
  adapter=chat.AnthropicChatAdapter(lambda _:'synthetic-only-key',enabled=True,count_transport=count,message_transport=message)
  self.connect(adapter);self.enqueue();self.assertTrue(self.runtime.process_next())
  self.assertEqual(self.runtime.journal.mode,'anthropic-live')
  self.assertEqual(self.turn()['status'],'outcome_unknown');self.assertEqual(self.rows()[0],('outcome_unknown',2458,None))
  with self.assertRaisesRegex(ValueError,'unresolved message'):
   self.runtime.journal.reserve('other-turn','hash','other-turn',100,10000)
  self.assertEqual(calls,['count','message'])
 def test_fake_and_real_billing_evidence_cannot_share_journal(self):
  live=chat.UsageJournal(self.journal,'anthropic-live');live.reserve('live-synthetic','h','live',1000,10000)
  self.connect(Fake());self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'blocked_before_message');self.assertEqual(self.adapter.counts,[]);self.assertEqual(len(self.rows()),1)
 def test_concurrent_cumulative_reservations_never_exceed_cap(self):
  journal=chat.UsageJournal(self.journal);journal.reserve('prior','h','prior',49_999_000,50_000_000)
  def reserve(i):
   try:journal.reserve('chat:'+str(i)+':0','h',str(i),600,10000);return 'ok'
   except ValueError:return 'blocked'
  with ThreadPoolExecutor(2) as pool:self.assertCountEqual(list(pool.map(reserve,[1,2])),['ok','blocked'])
  self.assertEqual(sum(r[1] for r in self.rows()),49_999_600)
