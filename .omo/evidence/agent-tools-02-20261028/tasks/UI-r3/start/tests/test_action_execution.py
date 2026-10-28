import unittest,tempfile,time,json
from concurrent.futures import ThreadPoolExecutor
from app import Store
import action_execution as a
import ledger
from loretune import Conflict

class ActionExecutionTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name);self.w=self.st.workspace_id;self.p='fixture'
  with self.st.connect() as c:ledger.patch_budget(c,self.w,'rehearsal:project:'+self.p,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
 def tx(self,fn,*args,**kw):
  with self.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');return fn(c,self.w,self.p,*args,**kw)
 def action(self,dependencies=(),role='image'):
  return self.tx(a.propose,plan_id='plan',plan_revision=1,context_hash='context',role=role,release_id='fake-image-v1',inputs={'prompt':'synthetic'},options={'ratio':'1:1'},dependencies=dependencies)
 def grant(self,actions,amount='0.4'):
  return self.tx(a.grant,[x['id'] for x in actions],actor='local-owner',approved=True,expires=time.time()+300,price_revision='fixture-price1',money_by_action={x['id']:{'amount':amount,'currency':'USD'} for x in actions})
 def admit(self,x,g):return self.tx(a.admit,x['id'],g['id'],context_hash='context',price_revision='fixture-price1')
 def claim(self,j,**kw):return self.tx(a.claim,j['id'],context_hash='context',price_revision='fixture-price1',**kw)
 def test_same_action_parallel_admission_reserves_once_and_survives_reopen(self):
  x=self.action();g=self.grant([x])
  with ThreadPoolExecutor(max_workers=2) as pool:jobs=list(pool.map(lambda _:self.admit(x,g),range(2)))
  self.assertEqual(jobs[0]['id'],jobs[1]['id'])
  with Store(self.tmp.name).connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
   self.assertEqual(a.get(c,'action_jobs',self.w,self.p,jobs[0]['id'])['action']['inputs'],{'prompt':'synthetic'})
 def test_concurrent_different_actions_cannot_exceed_budget(self):
  xs=[self.action(),self.action()];g=self.grant(xs,'0.7')
  def admit(x):
   try:return self.admit(x,g)['id']
   except ledger.LedgerError:return 'blocked'
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(admit,xs))
  self.assertEqual(results.count('blocked'),1)
 def test_rollback_between_reservation_and_queue_insert_is_atomic(self):
  x=self.action();g=self.grant([x])
  with self.st.connect() as c:c.execute("CREATE TRIGGER reject_job BEFORE INSERT ON action_jobs BEGIN SELECT RAISE(ABORT,'fixture'); END")
  with self.assertRaises(Exception):self.admit(x,g)
  with self.st.connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
   self.assertEqual(c.execute('SELECT count(*) FROM action_admissions').fetchone()[0],0)
 def test_grant_mutation_revocation_context_and_price_block(self):
  x=self.action();g=self.grant([x])
  for changes in [{'context_hash':'changed','price_revision':'fixture-price1'},{'context_hash':'context','price_revision':'changed'}]:
   with self.assertRaises(ValueError):self.tx(a.admit,x['id'],g['id'],**changes)
  j=self.admit(x,g);self.tx(a.revoke,g['id'],1);self.assertEqual(self.claim(j)['state'],'blocked')
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
 def test_unknown_claim_recovery_never_reissues_or_releases(self):
  x=self.action();g=self.grant([x]);j=self.admit(x,g);self.claim(j);self.tx(a.recover)
  self.assertEqual(self.claim(j)['state'],'outcome_unknown')
  self.assertEqual(self.admit(x,g)['id'],j['id'])
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
 def test_dependencies_require_owned_collected_approved_output_and_keep_hash(self):
  x=self.action();child=self.action([x['id']],role='video');g=self.grant([x,child])
  with self.assertRaises(ValueError):self.admit(child,g)
  j=self.admit(x,g);self.claim(j)
  with self.assertRaises(ValueError):self.tx(a.record_result,j['id'],asset_hash='a'*64,output_slot='video')
  self.tx(a.record_result,j['id'],asset_hash='a'*64,output_slot='image')
  with self.assertRaises(ValueError):self.admit(child,g)
  self.tx(a.approve_result,j['id'],actor='local-owner');out=self.admit(child,g)
  self.assertEqual(out['dependencies'][0]['result']['sha256'],'a'*64)
  with self.st.connect() as c:
   with self.assertRaises(ValueError):a.get(c,'action_jobs',self.w,'other',j['id'])
   with self.assertRaises(ValueError):a.propose(c,self.w,'other',plan_id='p',plan_revision=1,context_hash='c',role='video',release_id='fake',inputs={},options={},dependencies=[x['id']])
 def test_model_cannot_grant_and_results_are_idempotent(self):
  x=self.action()
  with self.assertRaises(ValueError):self.tx(a.grant,[x['id']],actor='model',approved=True,expires=time.time()+300,price_revision='p',money_by_action={x['id']:{'amount':'0','currency':'USD'}})
  g=self.grant([x]);j=self.admit(x,g);self.claim(j)
  first=self.tx(a.record_result,j['id'],asset_hash='a'*64,output_slot='image')
  self.assertEqual(first,self.tx(a.record_result,j['id'],asset_hash='a'*64,output_slot='image'))
  with self.assertRaises(Conflict):self.tx(a.record_result,j['id'],asset_hash='b'*64,output_slot='image')
 def test_synthetic_image_bytes_to_validated_store_then_dependency_admission(self):
  from image_adapter import SyntheticImageAdapter
  x=self.action();g=self.grant([x]);j=self.admit(x,g);self.claim(j)
  output=SyntheticImageAdapter().generate(dict(prompt='synthetic',width=32,height=32))
  path,metadata=self.st.save_media(output['bytes'],'.png','video')
  result=self.tx(a.record_result,j['id'],asset_hash=path.stem,output_slot='image')
  self.assertFalse(result['result_approved']);self.tx(a.approve_result,j['id'],actor='local-owner')
  child=self.action([x['id']],role='video');child_grant=self.grant([child]);downstream=self.admit(child,child_grant)
  self.assertEqual(downstream['dependencies'][0]['result']['sha256'],path.stem)
  self.assertEqual(downstream['external_calls'],0)
