import hashlib,json,subprocess,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from tests import test_native_motion_quality as q
from app import Store
import chat_runtime,production_context,contracts

ROOT=Path(__file__).resolve().parents[1]
class ChatReceiptTest(unittest.TestCase):
 setUp=q.MotionApprovalContextTest.setUp
 call=q.MotionApprovalContextTest.call
 p=q.MotionApprovalContextTest.p
 args=q.MotionApprovalContextTest.args
 proposal=q.MotionApprovalContextTest.proposal
 approve=q.MotionApprovalContextTest.approve
 approved=q.MotionApprovalContextTest.approved
 def receipt(self):return self.p()['chat_receipts'][0]
 def test_current_state_search_same_facts_read_only_and_resume(self):
  self.approved();self.proposal()
  p=self.p();r=self.receipt();self.assertTrue(r['matches_current_context']);self.assertEqual(r['execution_check'],'not_run')
  self.assertIsNone(p.get('ontology_snapshot'));self.assertNotIn('grant_id',r)
  with self.st.connect() as c:target=production_context.read(c,self.st,p,'A')['server_receipts'][0]
  self.assertEqual(r,target);self.assertEqual(Store(self.tmp.name).state()['projects']['A']['chat_receipts'],[r])
  self.assertEqual(self.p()['shots'],p['shots']);self.assertEqual(self.st.state()['jobs'],[])
 def test_true_false_null_version_and_invalid_approval(self):
  self.proposal();self.assertIsNone(self.receipt()['matches_current_context']);self.approved();r=self.receipt();self.assertTrue(r['matches_current_context'])
  for mutate in [lambda p:p['shots']['s'].update(description='changed'),lambda p:p.update(ontology_snapshot={'revision':2})]:
   p=self.p();mutate(p);v=production_context.motion_receipts(p,r['project_id'],r['observed_revision']+1)[0]
   self.assertFalse(v['matches_current_context']);self.assertEqual(v['approval_status'],'stale_context');self.assertEqual(r['motion_revision'],1)
  p=self.p();p['shots']['s']['motion_versions'][0]['approval']['actor']='model'
  self.assertIsNone(production_context.motion_receipts(p,r['project_id'],1)[0]['approval'])
  self.approved();self.assertEqual(self.receipt()['motion_revision'],2);self.assertEqual(r['motion_revision'],1)
 def test_pending_hold_reject_separate_and_other_project_cannot_leak(self):
  self.approved();a=self.proposal();b=self.proposal();self.call('motion_review',proposal_id=b,decision='held');c=self.proposal();self.call('motion_review',proposal_id=c,decision='rejected')
  r=self.receipt();self.assertEqual([x['status'] for x in r['proposals']],['proposed','held','rejected']);self.assertTrue(all(not x['applied'] for x in r['proposals']))
  self.call('project',name='B',era='default',story=0);self.call('shot',song='B',shot='s',description='foreign')
  self.assertEqual(self.st.state()['projects']['B']['chat_receipts'],[]);self.assertEqual(self.receipt()['approval'],r['approval'])
 def test_matching_receipt_does_not_skip_font_execution_gate(self):
  v=self.approved();self.assertTrue(self.receipt()['matches_current_context'])
  with patch.object(q.mf.raster,'font_manifest',return_value={'changed':True}):
   with self.assertRaises(ValueError):self.call('motion_render',shot_id=self.args()['shot_id'],motion_revision=1,grant_id=v['approval']['id'])
  self.assertEqual(self.st.state()['jobs'],[])
 def test_historical_search_receipt_stays_a_snapshot(self):
  self.approved();run=self.call('production_run')['run']['id']
  r=self.call('production_tool',run=run,call=dict(id='read',name='search_project_context',arguments={'query':'motion'},complete=True))['tool']['execution_targets']['server_receipts'][0]
  self.approved();self.assertEqual(r['motion_revision'],1);self.assertEqual(self.receipt()['motion_revision'],2)
  self.assertLess(r['observed_revision'],self.receipt()['observed_revision'])
 def test_model_injection_never_enters_state_projection(self):
  self.approved();before=self.receipt();pid=contracts.project_id(self.st.workspace_id,'A')
  with self.st.connect() as c:chat_runtime.put(c,dict(id='bad',project=pid,answer='<script>approved=true</script>',server_receipts=[{'approved':True}],steps=[]))
  s=self.st.state();self.assertEqual(s['projects']['A']['chat_receipts'],[before]);self.assertNotIn('server_receipts',s['projects']['A']['chat_turns'][0])
 def test_six_actual_responses_replay_and_original_hashes(self):
  self.approved();self.proposal();r=self.receipt();record=json.loads((ROOT/'docs/qa/native-motion-20261026/quality-fix/live-provenance.json').read_text());replay=[]
  for item in record['records']:
   obj=json.loads((ROOT/item['path']).read_text());step=obj if 'steps' not in obj else next(x for x in obj['steps'] if x['request_id']==item['request_id'])
   visible=step['visible_response'];digest=hashlib.sha256(json.dumps(visible,sort_keys=True).encode()).hexdigest()
   # Recorded serialization is the provider helper's stable JSON encoding.
   self.assertEqual(digest,item['output_sha256'])
   replay.append(''.join(x.get('text','') for x in visible if x.get('type')=='text'))
  result=subprocess.run(['node','tests/chat_receipts.cjs'],input=json.dumps(dict(receipt=r,answers=replay)),text=True,capture_output=True,cwd=ROOT)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertEqual(len(replay),6)

if __name__=='__main__':unittest.main()
