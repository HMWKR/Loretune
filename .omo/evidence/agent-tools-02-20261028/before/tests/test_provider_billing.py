"""Synthetic provider records only; no billing API/account access."""
import json,tempfile,time,unittest,uuid
from concurrent.futures import ThreadPoolExecutor
from app import Store
import fal_provider,ledger,provider_billing as billing
class BillingTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=Store(self.tmp.name)
  self.quote=fal_provider.estimate();self.quote['budget_revision']=1
  with self.s.connect() as c:ledger.patch_budget(c,self.s.workspace_id,'fixture',dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
  self.job=self.s.generation.admit('fixture',{'duration':'10','generate_audio':False},self.quote,{'song':'fixture','execution_mode':'contract-fake'},'fixture',approved=True)
  self.job.update(receipt={'request_id':'fixture-request'},state='import_blocked')
  with self.s.connect() as c:self.s.generation.save(c,self.job)
  self.record=dict(request_id='fixture-request',endpoint_id=fal_provider.MODEL,timestamp='2026-10-25T00:00:00Z',quantity=10,unit='second',cost_subtotal=.7,cost_discount=0,cost_total=.7,cost_estimate_nano_usd=700000000)
 def run_record(self,record=None,source='fal-billed'):
  return billing.reconcile(self.s,self.job['id'],source,record or self.record,evidence_class='fixture')
 def reservation(self):
  with self.s.connect() as c:return c.execute('SELECT state,actual FROM reservations').fetchone()
 def test_estimate_never_settles_then_exact_billed_record_settles_once(self):
  usage={'time_series':[{'bucket':'2026-10-25T00:00:00Z','results':[dict(self.record,currency='USD')]}]}
  out=billing.record_fal_usage(self.s,usage,evidence_class='fixture')[0];self.assertEqual(out['kind'],'aggregate_estimate');self.assertIsNone(out['job_attribution']);self.assertEqual(self.reservation(),('reserved',None))
  out=self.run_record();self.assertEqual(self.reservation(),('settled',700000));self.assertEqual(self.run_record(),out)
  j=self.s.generation.get(self.job['id']);self.assertEqual(j['state'],'import_blocked');self.assertFalse(j['cost_confirmed']);self.assertFalse(out['invoice_confirmed'])
 def test_concurrent_record_never_double_charges(self):
  with ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(lambda _:self.run_record(),range(2)))
  self.assertEqual(out[0],out[1]);self.assertEqual(self.reservation(),('settled',700000))
  with self.s.connect() as c:self.assertEqual(c.execute("SELECT count(*) FROM ledger_events WHERE kind='settled'").fetchone()[0],1)
 def test_identity_and_numeric_validation_fail_without_mutation(self):
  for patch in [dict(request_id='other'),dict(endpoint_id='other'),dict(cost_total=-1),dict(cost_estimate_nano_usd=700000001),dict(cost_discount=.1),dict(cost_total='NaN')]:
   with self.subTest(patch=patch):
    with self.assertRaises(ValueError):self.run_record(dict(self.record,**patch))
    self.assertEqual(self.reservation(),('reserved',None))
 def test_changed_record_is_conflict_not_invented_refund(self):
  self.run_record();r=dict(self.record,cost_total=.5,cost_discount=.2,cost_estimate_nano_usd=500000000)
  out=self.run_record(r);self.assertEqual(out['reconciliation'],'conflicting_record_requires_review');self.assertEqual(self.reservation(),('settled',700000))
 def test_nano_precision_retained_with_conservative_local_rounding(self):
  r=dict(self.record,cost_total=.000000001,cost_subtotal=.000000001,cost_estimate_nano_usd=1)
  out=self.run_record(r);self.assertEqual(out['exact_nano_usd'],1);self.assertEqual(out['rounding_nano_usd'],999);self.assertEqual(self.reservation(),('settled',1))
 def test_late_charge_after_verified_unsubmitted_marks_disputed(self):
  with self.s.connect() as c:ledger.command(c,self.s.workspace_id,'fixture','release',{'reservation':self.job['reservation']},'fixture-release')
  self.run_record();self.assertEqual(self.reservation(),('disputed',700000))
 def test_fixture_cannot_authenticate_real_billing_and_record_does_not_copy_secrets(self):
  with self.assertRaises(ValueError):billing.reconcile(self.s,self.job['id'],'fal-billed',self.record,evidence_class='authenticated-provider')
  self.run_record(dict(self.record,token='secret-canary',url='https://signed.invalid/?secret',auth_method='private-canary'))
  with self.s.connect() as c:raw=''.join(r[0] for r in c.execute('SELECT body FROM provider_cost_observations'))
  self.assertNotIn('canary',raw);self.assertNotIn('signed.invalid',raw)
 def test_unknown_or_missing_receipt_never_releases(self):
  with self.assertRaises(ValueError):self.run_record(source='unknown')
  self.job['receipt']=None
  with self.s.connect() as c:self.s.generation.save(c,self.job)
  with self.assertRaises(ValueError):self.run_record()
  self.assertEqual(self.reservation(),('reserved',None))
 def test_overspend_record_does_not_claim_provider_budget_enforcement(self):
  out=self.run_record(dict(self.record,cost_total=1.2,cost_subtotal=1.2,cost_estimate_nano_usd=1200000000))
  self.assertEqual(self.reservation(),('disputed',1200000))
  with self.s.connect() as c:self.assertEqual(ledger.budget(c,self.s.workspace_id,'fixture')['data']['overrun']['amount'],'0.2')
