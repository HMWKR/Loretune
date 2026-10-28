"""Audit evidence runner only; never imported by the product test suite."""
import sys,json,os,socket,unittest,time,hashlib
from pathlib import Path
from copy import deepcopy

out=Path(__file__).resolve().parent
manifest=json.loads((out/'base-manifest.json').read_text())
work=Path(manifest['work']).resolve()
root=out.parents[2]
sys.dont_write_bytecode=True
os.chdir(work)
sys.path[:0]=[str(work),str(work/'tests')]
blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind'}:
  blocked.append(event);raise AssertionError('Network/listener forbidden in audit')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'}:
   blocked.append('secret_file');raise AssertionError('Secret files forbidden in audit')
  if p.is_relative_to(root) and not p.is_relative_to(out):
   blocked.append('canonical_file');raise AssertionError('Canonical files forbidden during isolated execution')
 if event=='subprocess.Popen':
  exe=Path(os.fsdecode(args[0])).name
  if exe not in {'ffmpeg','ffprobe'} or any('://' in str(a) for a in args[1]):
   blocked.append('subprocess');raise AssertionError('Only local synthetic ffmpeg/ffprobe fixtures allowed')
sys.addaudithook(audit)

import chat_protocols as codec, production_tools as tools
from tests.test_motion import scene
expected={
 'propose_motion_scene':{'shot_id':'string','base_motion_revision':'integer','scene':'object'},
 'request_motion_render':{'shot_id':'string','motion_revision':'integer','grant_id':'string'},
 'propose_timeline_changes':{'description':'string','timeline_version':'integer','commands':'array'},
}
inputs={
 'propose_motion_scene':dict(shot_id='synthetic-shot',base_motion_revision=0,scene=scene()),
 'request_motion_render':dict(shot_id='synthetic-shot',motion_revision=1,grant_id='synthetic-grant'),
 'propose_timeline_changes':dict(description='synthetic reorder proposal',timeline_version=1,commands=[dict(op='reorder_clips',order=[0])]),
}
probes=[]
def strict_objects(value):
 if isinstance(value,dict):
  if value.get('type')=='object':
   assert value['additionalProperties'] is False
   assert set(value['required'])==set(value['properties'])
  for v in value.values():strict_objects(v)
 elif isinstance(value,list):
  for v in value:strict_objects(v)
def envelope(provider,name,args):
 if provider=='anthropic':return dict(stop_reason='tool_use',content=[dict(type='tool_use',id='synthetic-call',name=name,input=args)])
 return dict(status='completed',output=[dict(type='function_call',call_id='synthetic-call',name=name,arguments=json.dumps(args))])
for provider in sorted(codec.PROVIDERS):
 definitions={d['name']:d.get('input_schema',d.get('parameters')) for d in codec.tool_definitions(provider)}
 for name,fields in expected.items():
  schema=definitions[name];strict_objects(schema)
  assert {k:v['type'] for k,v in schema['properties'].items()}==fields
  args=inputs[name];normalized=codec.normalize(provider,envelope(provider,name,args),'synthetic-run')
  assert normalized['calls'][0]['arguments']==args
  rejected=0
  invalid=[]
  for key in ['actor','approved','permission','path','endpoint']:
   invalid.append(dict(args,**{key:'injected'}))
  for key in args:
   candidate=deepcopy(args);del candidate[key];invalid.append(candidate)
  for key,kind in fields.items():
   if kind=='integer':invalid.append(dict(args,**{key:True}))
  for candidate in invalid:
   try:codec.normalize(provider,envelope(provider,name,candidate),'synthetic-run')
   except ValueError:rejected+=1
   else:raise AssertionError('Invalid tool arguments accepted')
  probes.append(dict(provider=provider,tool=name,status='PASS',fields=fields,rejected_cases=rejected))

names=[
 'tests.test_chat_protocols',
 'tests.test_motion.MotionTest.test_schema_bounds_and_no_code_or_paths',
 'tests.test_motion.MotionTest.test_frame_clock_easing_interval_and_delayed_only_circle',
 'tests.test_motion.MotionTest.test_three_protocols_propose_idempotently_without_apply',
 'tests.test_motion.MotionTest.test_human_versions_hold_reject_stale_foreign_restore_and_original_preserved',
 'tests.test_motion.MotionTest.test_render_grant_cancel_reuse_and_font_change',
 'tests.test_timeline_commands',
 'tests.test_local_creation_tools.LocalToolsTest.test_stale_edit_and_foreign_proposal_rejected_without_mutation',
 'tests.test_local_creation_tools.LocalToolsTest.test_three_protocols_propose_without_applying_and_human_apply_preserves_other_inputs',
]
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
start=time.monotonic()
with (out/'test-results.log').open('w') as log:
 result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
record=dict(snapshot=str(work),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),seconds=round(time.monotonic()-start,3),status='PASS' if result.wasSuccessful() else 'FAIL',targeted_probes=probes,blocked_operations=blocked,network_calls=0,provider_calls=0,coretext_render_executed=False,full_suite=False)
(out/'test-results.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='targeted_probes'}))
if not result.wasSuccessful():
 for name,text in result.failures+result.errors:print(name.id(),text)
raise SystemExit(0 if result.wasSuccessful() else 1)
