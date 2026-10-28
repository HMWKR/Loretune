import tempfile,time,unittest,uuid
from app import Store
import action_execution as actions
import guided,ledger,model_selection,production_tools
from loretune import Conflict

class ActionToolBridgeTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.store=Store(self.tmp.name);self.w=self.store.workspace_id;self.p='fixture-project';self.project={}
  self.plan=guided.propose(self.project,dict(goal='fixture',scenes='geometry',style='',constraints='',kind='visualizer'))
  self.run=production_tools.begin(self.project)
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE')
   ledger.patch_budget(c,self.w,'rehearsal:project:'+self.p,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
   self.action=actions.propose(c,self.w,self.p,plan_id=self.plan['id'],plan_revision=self.plan['version'],context_hash=model_selection.snapshot(self.project)['sha256'],role='image',release_id='synthetic-fixture',inputs={'prompt':'geometry'},options={})
   self.grant=actions.grant(c,self.w,self.p,[self.action['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='rehearsal-v1',money_by_action={self.action['id']:{'amount':'0','currency':'USD'}})
  self.args=dict(plan_id=self.plan['id'],action_id=self.action['id'],grant_id=self.grant['id'])
 def call(self,identifier='call',args=None):
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE')
   return production_tools.execute(self.project,self.run['id'],dict(id=identifier,name='request_media_generation',arguments=args or self.args,complete=True),request_generation=lambda d:actions.request_from_plan(c,self.w,self.p,self.project,d))
 def test_tool_returns_same_persisted_receipt_without_external_execution(self):
  first=self.call();second=self.call('another')
  self.assertEqual(first['job_id'],second['job_id']);self.assertEqual(first['mode'],'rehearsal');self.assertEqual(first['external_calls'],0)
  with self.store.connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM action_jobs').fetchone()[0],1)
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
 def test_foreign_plan_and_stale_revision_never_reserve(self):
  with self.assertRaises(ValueError):self.call(args={**self.args,'plan_id':'foreign'})
  self.plan['version']+=1
  with self.assertRaises(Conflict):self.call()
  with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
 def test_revocation_and_scope_substitution_fail_closed(self):
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE');actions.revoke(c,self.w,self.p,self.grant['id'],1)
  with self.assertRaises(ValueError):self.call()
  with self.store.connect() as c:
   with self.assertRaises(ValueError):actions.request_from_plan(c,self.w,'foreign',self.project,self.args)
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
 def test_public_state_scopes_receipts_and_omits_inputs(self):
  for name in ['A','B']:
   self.store.mutate(dict(action='project',data=dict(name=name,era='default',story=0),revision=self.store.state()['revision'],request_id=uuid.uuid4().hex))
  identifier=self.store.state()['project_ids']['A']
  with self.store.connect() as c:
   actions.put(c,'action_jobs',self.w,identifier,dict(id='fixture-job',state='prepared',mode='rehearsal',external_calls=0,result_approved=False,action={'inputs':'private-fixture'}))
  state=self.store.state()
  self.assertEqual(state['projects']['B']['rehearsal_jobs'],[])
  exposed=state['projects']['A']['rehearsal_jobs'][0]
  self.assertEqual(exposed['id'],'fixture-job');self.assertNotIn('action',exposed)
