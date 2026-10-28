import json,sys,os,unittest,tempfile,socket
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch

out=Path(__file__).resolve().parent;manifest=json.loads((out/'base-manifest.json').read_text());work=Path(manifest['work']).resolve();root=out.parents[2]
os.chdir(work);sys.dont_write_bytecode=True;sys.path[:0]=[str(work),str(work/'tests')]
blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind','subprocess.Popen'}:
  blocked.append(event);raise AssertionError('No external, listener or renderer execution')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'} or (p.is_relative_to(root) and not p.is_relative_to(out)):
   blocked.append('forbidden file');raise AssertionError('Only isolated source/data and audit output permitted')
sys.addaudithook(audit)
import chat_models,chat_protocols,production_tools,production_context,motion_renderer
from tests.test_motion import MotionTest,scene

observations={}
class IndependentControls(unittest.TestCase):
 def test_wire_transform_does_not_relax_nine_local_bounds(self):
  original=chat_protocols.tool_definitions('anthropic')
  chat_models.body(chat_models.contract('anthropic-haiku-5-5'),[],original,8192)
  cases=[('frames',lambda s:s.update(frame_count=97)),('canvas',lambda s:s.update(width=4096)),('layers',lambda s:s.update(layers=[dict(deepcopy(s['layers'][0]),id='L'+str(i)) for i in range(9)])),('keyframes',lambda s:s['layers'][0].update(keyframes=[dict(s['layers'][0]['keyframes'][0],frame=i) for i in range(9)])),('text_length',lambda s:s['layers'][0].update(text='가'*81)),('font_size',lambda s:s['layers'][0].update(font_size=161)),('opacity',lambda s:s['layers'][0]['keyframes'][0].update(opacity=1.1)),('nonfinite',lambda s:s['layers'][0]['keyframes'][0].update(x=float('nan'))),('unknown_path',lambda s:s.update(path='/tmp/injected'))]
  for name,change in cases:
   value=scene();change(value)
   with self.subTest(name=name),self.assertRaises(ValueError):production_tools.validate('propose_motion_scene',dict(shot_id='synthetic',base_motion_revision=0,scene=value))
  observations['post_wire_invalid_motion_cases']=[x[0] for x in cases]
 def test_approved_motion_projection_omission_and_execution_guards(self):
  fx=MotionTest();fx.setUp();self.addCleanup(fx.doCleanups)
  with patch.object(motion_renderer,'validate_text',return_value={}),patch.object(motion_renderer,'font_manifest',return_value={'synthetic':'fixed'}):
   fx.approve(fx.proposal());approved=fx.p()['shots']['s']['motion_versions'][0]
   pending=fx.proposal()
   with fx.st.connect() as c:targets=production_context.read(c,fx.st,fx.p(),'A')
   projection=targets['shots'][0]['motion']
   self.assertEqual(projection['grant_id'],approved['approval']['id']);self.assertEqual(approved['approval']['actor'],'local-owner');self.assertEqual(approved['approval']['scope'],'local-motion-candidate')
   self.assertEqual(set(projection),{'revision','scene','grant_id'})
   self.assertEqual(projection['revision'],1)
   self.assertEqual(next(x for x in fx.p()['motion_proposals'] if x['id']==pending)['status'],'proposed')
   with self.assertRaises(ValueError):fx.call('motion_render',shot_id=fx.args()['shot_id'],motion_revision=1,grant_id='invented')
   accepted=fx.queue();self.assertFalse(accepted['output_approved']);self.assertFalse(accepted['finished_verified'])
   self.assertEqual(fx.queue()['job_id'],accepted['job_id'])
   fx.call('cancel_job',job=accepted['job_id']);self.assertEqual(fx.queue()['job_id'],accepted['job_id'])
   fx.approve(pending)
   with self.assertRaises(ValueError):fx.call('motion_render',shot_id=fx.args()['shot_id'],motion_revision=1,grant_id=approved['approval']['id'])
   with self.assertRaises(ValueError):fx.call('motion_render',shot_id=fx.args()['shot_id'],motion_revision=2,grant_id=approved['approval']['id'])
   fx.call('project',name='B',era='default',story=0)
   with self.assertRaises(ValueError):fx.call('motion_render',song='B',shot_id=fx.args()['shot_id'],motion_revision=2,grant_id=approved['approval']['id'])
   self.assertEqual(fx.p()['shots']['s']['takes'],[])
   observations['approval_projection']={'keys':list(projection),'current_revision':projection['revision'],'server_actor':approved['approval']['actor'],'server_scope':approved['approval']['scope'],'new_proposal_remained_pending_before_human_review':True,'fake_stale_foreign_grant_rejected':True,'cancelled_job_reused':True,'no_take_generated':True}

suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromName('tests.test_strict_wire_schema'),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls)])
with (out/'offline-tests.log').open('w') as log:r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
result={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'blocked_operations':blocked,'observations':observations,'status':'PASS' if r.wasSuccessful() else 'FAIL','provider_calls':0}
(out/'offline-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if not r.wasSuccessful():
 for t,e in r.failures+r.errors:print(t.id(),e)
raise SystemExit(not r.wasSuccessful())
