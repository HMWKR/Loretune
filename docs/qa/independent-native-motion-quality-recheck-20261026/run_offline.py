import json,sys,os,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
out=Path(__file__).resolve().parent;root=out.parents[2];m=json.loads((out/'base-manifest.json').read_text());work=Path(m['work']).resolve();os.chdir(work);sys.dont_write_bytecode=True;sys.path[:0]=[str(work),str(work/'tests')]
blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind'}:blocked.append(event);raise AssertionError('Network/listener forbidden')
 if event=='subprocess.Popen' and (Path(os.fsdecode(args[0])).name not in {'ffmpeg','ffprobe'} or any('://' in str(x) for x in args[1])):blocked.append(event);raise AssertionError('Only local synthetic media fixture subprocesses allowed')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'} or (p.is_relative_to(root) and not p.is_relative_to(out)):blocked.append('file');raise AssertionError('Canonical/secret file access forbidden')
sys.addaudithook(audit)
import production_context,motion_renderer
from tests.test_motion import MotionTest
observations={}
class IndependentMeaningControls(unittest.TestCase):
 def fixture(self):
  f=MotionTest();f.setUp();self.addCleanup(f.doCleanups)
  with patch.object(motion_renderer,'validate_text',return_value={}),patch.object(motion_renderer,'font_manifest',return_value={'synthetic':'original'}):f.approve(f.proposal())
  return f
 def test_empty_ontology_can_match_but_real_context_change_stales_record(self):
  f=self.fixture();before=deepcopy(f.p());self.assertIsNone(before.get('ontology_snapshot'))
  lookup=production_context.motion_context(before,'s')
  self.assertEqual(lookup['approval_status'],'recorded');self.assertTrue(lookup['approval']['matches_current_context']);self.assertTrue(lookup['requires_revalidation'])
  self.assertEqual(before,f.p());self.assertEqual(f.st.state()['jobs'],[])
  changed=deepcopy(before);changed['ontology_snapshot']={'revision':1,'graph':{'entities':[],'relations':[]}}
  stale=production_context.motion_context(changed,'s');self.assertEqual(stale['approval_status'],'stale_context');self.assertFalse(stale['approval']['matches_current_context']);self.assertIsNone(stale['grant_id'])
  self.assertEqual(f.p(),before)
  observations['ontology']={'empty_snapshot_match':True,'actual_context_change_stales':True,'read_only':True}
 def test_lookup_context_match_does_not_suppress_font_revalidation(self):
  f=self.fixture();before=deepcopy(f.p());f.proposal();v=before['shots']['s']['motion_versions'][0]
  with patch.object(motion_renderer,'font_manifest',return_value={'synthetic':'changed'}):
   lookup=production_context.motion_context(f.p(),'s');self.assertTrue(lookup['approval']['matches_current_context']);self.assertEqual(lookup['approval_status'],'recorded')
   with self.assertRaisesRegex(ValueError,'폰트'):f.call('motion_render',shot_id=f.args()['shot_id'],motion_revision=1,grant_id=v['approval']['id'])
  self.assertEqual(f.p()['shots'],before['shots']);self.assertEqual(f.st.state()['jobs'],[])
  self.assertEqual(lookup['proposals'][0]['status'],'proposed');self.assertFalse(lookup['proposals'][0]['applied'])
  observations['font']={'context_match_does_not_mean_executable':True,'changed_font_rejected':True,'pending_proposal_unapproved':True,'jobs_created':0}
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName('tests.test_native_motion_quality'),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentMeaningControls)])
with (out/'offline-tests.log').open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
record={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'status':'PASS' if r.wasSuccessful() else 'FAIL','blocked_operations':blocked,'observations':observations,'provider_calls':0,'full_suite':False}
(out/'offline-tests.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if not r.wasSuccessful():
 for t,e in r.failures+r.errors:print(t.id(),e)
raise SystemExit(not r.wasSuccessful())
