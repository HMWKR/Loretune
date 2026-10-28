import sys,socket,json,time,uuid,unittest
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent/'snapshot'))
from tests.test_fal_multimodel import FalMultiTest
from tests.test_chat_runtime import ChatRuntimeTest,Fake,response
import action_execution as actions,chat_models,chat_protocols,contracts,guided,ledger,model_selection
from fal_model_adapter import FalModelAdapter
from fal_models import Contract
class Independent(unittest.TestCase):
 def fixture(self):
  f=FalMultiTest();f.setUp();self.addCleanup(f.doCleanups);f.setup_model('fal-flux-schnell');return f
 def new_action(self,f,model=None):
  return f.call('media_prepare',song='synthetic',shot='장면 1',shot_revision=f.shot()['revision'],prompt='blue geometry',options={'ratio':'16:9'},refs=[],**({'model':model} if model else {}))['media_action']
 def approve(self,f,prep):
  a=prep['action'];g=deepcopy(f.pipe.gates[f.action['id']]);g.update(action_hash=a['hash'],input_sha256=prep['input_sha256'],model=a['release_id'],output_policy=a['options']['output_policy']);f.pipe.gates[a['id']]=g
  return f.call('media_approve',song='synthetic',action_id=a['id'])['media_grant']
 def test_same_tool_id_mismatch_conflicts_and_new_id_creates_new_candidate(self):
  f=self.fixture();run=f.call('production_run',song='synthetic')['run']['id'];args=dict(shot_id='장면 1',model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9',shot_revision=f.shot()['revision'])
  def call(i,a):return f.call('production_tool',song='synthetic',run=run,call=dict(id=i,name='prepare_image_action',arguments=a,complete=True))['tool']
  one=call('same',args);self.assertEqual(call('same',args),one)
  with self.assertRaises(ValueError):call('same',dict(args,prompt='different input'))
  two=call('new-candidate',args);self.assertNotEqual(one['action_id'],two['action_id'])
  with f.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0);self.assertEqual(c.execute('SELECT count(*) FROM execution_grants').fetchone()[0],1)
 def test_explicit_second_model_routes_exactly_without_fallback(self):
  f=self.fixture();c=Contract('fal-flux-pro-1-1');payload=c.payload('blue geometry',{'ratio':'16:9'});q=deepcopy(f.ad.contract.quote);q.update(model=c.MODEL,input_sha256=guided.fingerprint(payload),source=c.spec['source'])
  second=FalModelAdapter('fal-flux-pro-1-1',quote=q,transport=lambda *a:self.fail('no approval to submit'))
  f.pipe.adapters['fal-flux-pro-1-1']=second
  prep=self.new_action(f,'fal-flux-pro-1-1');self.assertEqual(prep['action']['release_id'],c.MODEL);self.assertEqual(prep['action']['options']['selection_origin'],'explicit')
  self.assertEqual(self.new_action(f)['action']['release_id'],f.ad.contract.MODEL)
  del f.pipe.adapters['fal-flux-pro-1-1']
  with self.assertRaises(ValueError):self.new_action(f,'fal-flux-pro-1-1')
  self.assertEqual(f.calls,[])
 def test_grant_revocation_before_submit_releases_only_unsent(self):
  f=self.fixture();j=f.request()['job_id']
  with f.st.connect() as c:actions.revoke(c,f.w,f.pid,f.grant['id'],1)
  f.st.process_generation();job=f.st.generation.get(j);self.assertEqual(job['state'],'submission_blocked');self.assertTrue(job['verified_unsubmitted']);self.assertFalse(f.calls)
  with f.st.connect() as c:self.assertEqual(c.execute('SELECT state,actual FROM reservations WHERE id=?',(job['reservation'],)).fetchone(),('cancelled',None))
 def test_two_distinct_actions_compete_for_single_budget(self):
  f=self.fixture();prep=self.new_action(f);g=self.approve(f,prep)
  def request(pair):
   try:
    with f.st.connect() as c:
     c.execute('BEGIN IMMEDIATE');p,_=f.pipe.project(c,'synthetic');return f.pipe.request(c,f.w,f.pid,p,*pair)['status']
   except ValueError:return 'blocked'
  with ThreadPoolExecutor(2) as pool:result=list(pool.map(request,[(f.action,f.grant['id']),(prep['action'],g['id'])]))
  self.assertCountEqual(result,['accepted','blocked'])
  with f.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1);self.assertEqual(c.execute('SELECT count(*) FROM generation_jobs').fetchone()[0],1)
 def test_unknown_submission_retains_budget_and_blocks_new_candidate(self):
  f=self.fixture();j=f.request()['job_id']
  def lost(*a):f.calls.append(a);raise TimeoutError()
  f.ad._transport=lost;f.st.process_generation();f.st.generation.recover();f.st.process_generation();job=f.st.generation.get(j)
  self.assertEqual(job['state'],'reconciliation_required');self.assertEqual(len(f.calls),1)
  with f.st.connect() as c:
   b=ledger.budget(c,f.w,'project:'+f.pid);self.assertEqual(ledger.units(b['data']['available']),0);self.assertEqual(c.execute('SELECT actual FROM reservations WHERE id=?',(job['reservation'],)).fetchone(),(None,))
  self.assertEqual(f.request()['job_id'],j)
  prep=self.new_action(f);g=self.approve(f,prep)
  with f.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');p,_=f.pipe.project(c,'synthetic')
   with self.assertRaises(ValueError):f.pipe.request(c,f.w,f.pid,p,prep['action'],g['id'])
  self.assertEqual(len(f.calls),1)
 def test_mutated_asset_bytes_block_before_submit(self):
  f=FalMultiTest();f.setUp();self.addCleanup(f.doCleanups);f.setup_model('fal-kling-2-5-turbo');j=f.request()['job_id'];t=f.shot()['takes'][0]
  from pathlib import Path
  Path(t['asset']).write_bytes(b'synthetic mutated file')
  f.st.process_generation();self.assertEqual(f.st.generation.get(j)['state'],'submission_blocked');self.assertFalse(f.calls)
 def test_price_mutation_before_submit_blocks(self):
  f=self.fixture();j=f.request()['job_id'];f.ad.contract.quote['price_revision']='changed';f.st.process_generation();self.assertEqual(f.st.generation.get(j)['state'],'submission_blocked');self.assertFalse(f.calls)
 def test_completed_tool_job_handoff_keeps_local_receipt_without_provider_tokens(self):
  f=self.fixture();j=f.request()['job_id'];f.call('model_settings',song='synthetic',selections={'chat':'xai-grok-4-7'},model_revision=f.project()['model_settings']['revision'])
  with f.st.connect() as c:jobs=actions.project_jobs(c,f.w,f.pid,'synthetic')
  h=chat_protocols.handoff(f.project(),'synthetic',jobs);self.assertEqual(h['jobs'],[{'id':j,'state':'prepared','mode':'contract-fake'}]);self.assertNotIn('receipt',json.dumps(h));self.assertEqual(f.request('xai')['job_id'],j)
 def test_protocol_authority_injection_never_normalizes(self):
  for provider in chat_protocols.PROVIDERS:
   for name,args in [('ontology_apply',{'approved':True}),('request_render',{'timeline_version':1,'grant_id':'x','approved':True}),('get_model_capabilities',{'role':'image','endpoint':'https://forbidden.invalid'})]:
    r={'stop_reason':'tool_use','content':[{'type':'tool_use','id':'x','name':name,'input':args}]} if provider=='anthropic' else {'status':'completed','output':[{'type':'function_call','call_id':'x','name':name,'arguments':json.dumps(args)}]}
    with self.assertRaises(ValueError):chat_protocols.normalize(provider,r,'run')
 def test_provider_rates_output_reasoning_bounds_and_input_gate(self):
  self.assertEqual(str(chat_models.cost(chat_models.contract('xai-grok-4-7'),100,100)),'0.0008')
  for key in chat_models.MODELS:
   spec=chat_models.contract(key);body=chat_models.body(spec,[],[],256);self.assertEqual(body.get('max_tokens',body.get('max_output_tokens')),256)
   with self.assertRaises(ValueError):chat_models.usage(spec,{'usage':{'input_tokens':1,'output_tokens':True}})
   with self.assertRaises(ValueError):chat_models.usage(spec,{'usage':{'input_tokens':1,'output_tokens':1},'service_tier':'unpriced'})
   self.assertEqual(chat_models.usage(spec,{'usage':{'input_tokens':100,'output_tokens':200,'output_tokens_details':{'reasoning_tokens':150}}})['output_tokens'],200)
  f=ChatRuntimeTest();f.setUp();self.addCleanup(f.doCleanups);f.connect(Fake());f.adapter.tokens=4097;f.enqueue();f.runtime.process_next();self.assertEqual(f.adapter.messages,[]);self.assertEqual(f.rows()[0][1],0)
def forbidden(*a,**kw):raise AssertionError('AUDIT network/listener prohibited')
if __name__=='__main__':
 with patch.object(socket.socket,'connect',forbidden),patch.object(socket.socket,'bind',forbidden),patch('socket.create_connection',forbidden):
  suite=unittest.defaultTestLoader.loadTestsFromTestCase(Independent);result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
