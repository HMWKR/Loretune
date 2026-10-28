import json,sys,os,unittest,subprocess
from pathlib import Path
out=Path(__file__).resolve().parent;root=out.parents[2];m=json.loads((out/'base-manifest.json').read_text());work=Path(m['work']);os.chdir(work);sys.dont_write_bytecode=True;sys.path[:0]=[str(work),str(work/'tests')];blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind'}:blocked.append(event);raise AssertionError('Network/listener forbidden')
 if event=='subprocess.Popen' and (Path(os.fsdecode(args[0])).name!='node' or args[1][1] not in ['-e','tests/independent_cq_probe.cjs','tests/chat_model_polling.cjs']):blocked.append(event);raise AssertionError('Only declared offline Node fixtures allowed')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'} or (p.is_relative_to(root) and not p.is_relative_to(out)):blocked.append('file');raise AssertionError('Canonical/secret access forbidden')
sys.addaudithook(audit)
payload=(out/'synthetic-probe-input.json').read_text()
original=subprocess.run(['node','tests/independent_cq_probe.cjs'],input=payload,text=True,capture_output=True,cwd=work)
if original.returncode:raise AssertionError(original.stdout+original.stderr)
observed=json.loads(original.stdout);(out/'original-counterexamples-after.json').write_text(json.dumps(observed,indent=2)+'\n')
from tests.test_chat_model_polling import ChatModelPollingTest
with (out/'targeted-tests.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ChatModelPollingTest))
guards=subprocess.run(['node','tests/chat_model_polling.cjs'],input=payload,text=True,capture_output=True,cwd=work)
if guards.returncode:raise AssertionError(guards.stdout+guards.stderr)
g=json.loads(guards.stdout);(out/'guard-observations.json').write_text(json.dumps(g,indent=2)+'\n')
record=dict(original_cases=dict(passed=observed['passed'],failed=observed['failed']),targeted_unittests=dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors)),nested_guard_conditions=g['count'],guard_capture_is_overlapping_not_additional=True,blocked_operations=blocked,provider_calls=0,http_requests=0,browser_actions=0)
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));print(original.stdout)
raise SystemExit(bool(observed['failed']) or not result.wasSuccessful())
