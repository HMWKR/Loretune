import json,sys,os,unittest,subprocess,shutil
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
out=Path(__file__).resolve().parent;root=out.parents[2]
manifest=json.loads((out/'base-manifest.json').read_text());work=Path(manifest['work'])
shutil.copy2(out/'independent_render.cjs',work/'tests/independent_render.cjs')
os.chdir(work);sys.dont_write_bytecode=True;sys.path[:0]=[str(work),str(work/'tests')]
blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind'}:blocked.append(event);raise AssertionError('No network or listener')
 if event=='subprocess.Popen' and (Path(os.fsdecode(args[0])).name!='node' or args[1][1] not in ['tests/chat_receipts.cjs','tests/independent_render.cjs']):blocked.append(event);raise AssertionError('Only specified offline Node fixtures allowed')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'} or (p.is_relative_to(root) and not p.is_relative_to(out)):blocked.append('file');raise AssertionError('Canonical/secret access forbidden')
sys.addaudithook(audit)
from tests.test_chat_receipts import ChatReceiptTest
from tests.test_native_motion_quality import MotionApprovalContextTest
import production_context,motion_renderer
observations={}
class IndependentReceiptControls(unittest.TestCase):
 def fixture(self):
  f=ChatReceiptTest();f.setUp();self.addCleanup(f.doCleanups);f.approved();f.proposal();return f
 def test_real_render_keeps_stale_current_and_true_history_separate(self):
  f=self.fixture();past=deepcopy(f.receipt());p=f.p();p['shots']['s']['description']='changed context'
  current=production_context.motion_receipts(p,past['project_id'],past['observed_revision']+1)[0]
  self.assertFalse(current['matches_current_context']);self.assertTrue(past['matches_current_context'])
  f.approved();new=f.receipt();self.assertEqual(new['motion_revision'],2)
  result=subprocess.run(['node','tests/independent_render.cjs'],input=json.dumps(dict(past=past,current=current,next=new)),text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr);observations['render']=json.loads(result.stdout)
 def test_receipt_projection_does_not_change_database_or_authorize_execution(self):
  f=self.fixture()
  with f.st.connect() as c:before='\n'.join(c.iterdump())
  for _ in range(3):
   p=f.p();r=p['chat_receipts'][0]
   with f.st.connect() as c:self.assertEqual(production_context.read(c,f.st,p,'A')['server_receipts'],p['chat_receipts'])
  with f.st.connect() as c:self.assertEqual('\n'.join(c.iterdump()),before)
  self.assertEqual(r['execution_check'],'not_run');self.assertTrue(r['matches_current_context'])
  v=f.p()['shots']['s']['motion_versions'][-1]
  with self.assertRaises(ValueError):f.call('motion_render',shot_id=f.args()['shot_id'],motion_revision=v['id'],grant_id='invented')
  with patch.object(motion_renderer,'font_manifest',return_value={'synthetic':'changed'}):
   with self.assertRaises(ValueError):f.call('motion_render',shot_id=f.args()['shot_id'],motion_revision=v['id'],grant_id=v['approval']['id'])
  self.assertEqual(f.st.state()['jobs'],[])
  observations['authority']={'complete_synthetic_database_unchanged_by_reads':True,'invented_grant_rejected':True,'changed_font_rejected':True,'jobs':0}
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(ChatReceiptTest),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentReceiptControls),MotionApprovalContextTest('test_model_cannot_inject_approval_and_old_grant_stays_rejected')])
with (out/'offline-tests.log').open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
record={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'status':'PASS' if r.wasSuccessful() else 'FAIL','blocked_operations':blocked,'observations':observations,'provider_calls':0,'full_suite':False}
(out/'offline-tests.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if not r.wasSuccessful():
 for t,e in r.failures+r.errors:print(t.id(),e)
raise SystemExit(not r.wasSuccessful())
