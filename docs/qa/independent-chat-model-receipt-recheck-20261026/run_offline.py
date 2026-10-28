import json,sys,os,unittest,subprocess,tempfile,uuid,shutil
from pathlib import Path
out=Path(__file__).resolve().parent;root=out.parents[2];m=json.loads((out/'base-manifest.json').read_text());work=Path(m['work']);shutil.copy2(out/'probe.cjs',work/'tests/independent_cq_probe.cjs')
os.chdir(work);sys.dont_write_bytecode=True;sys.path[:0]=[str(work),str(work/'tests')];blocked=[]
def audit(event,args):
 if event in {'socket.connect','socket.bind'}:blocked.append(event);raise AssertionError('No network/listener')
 if event=='subprocess.Popen' and (Path(os.fsdecode(args[0])).name!='node' or args[1][1] not in ['-e','tests/independent_cq_probe.cjs']):blocked.append(event);raise AssertionError('Only local Node fixtures')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if p.name.startswith('.env') or p.name in {'auth.json','credentials','credentials.json'} or (p.is_relative_to(root) and not p.is_relative_to(out)):blocked.append('file');raise AssertionError('No canonical/secret access')
sys.addaudithook(audit)
from app import Store
from tests.test_chat_display import ChatDisplayTest
with (out/'existing-tests.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ChatDisplayTest))
with tempfile.TemporaryDirectory(prefix='aethon-cq-synthetic-') as d:
 st=Store(d)
 def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 call('project',name='A',era='default',story=0);call('shot',song='A',shot='s',description='synthetic no-motion scene')
 catalog=st.state()['model_catalog']['models'];gpt=next(x['id'] for x in catalog if x['model']=='gpt-6-luna');grok=next(x['id'] for x in catalog if x['model']=='grok-4.7');video=next(x['id'] for x in catalog if x['role']=='video')
 def select(value):
  call('model_settings',song='A',selections={'chat':value},model_revision=st.state()['projects']['A']['model_settings']['revision']);return st.state()
 before=select(gpt);changed=select(grok);cleared=select(None)
 assert before['projects']['A']['chat_receipts']==changed['projects']['A']['chat_receipts']==cleared['projects']['A']['chat_receipts']==[]
 assert before['projects']['A']['chat_connection']==changed['projects']['A']['chat_connection']==cleared['projects']['A']['chat_connection']
 payload=dict(before=before,grok=changed,cleared=cleared,gptId=gpt,videoId=video)
 (out/'synthetic-probe-input.json').write_text(json.dumps(payload,indent=2)+'\n')
 probe=subprocess.run(['node','tests/independent_cq_probe.cjs'],input=json.dumps(payload),text=True,capture_output=True,cwd=work)
 if probe.returncode:raise AssertionError(probe.stdout+probe.stderr)
 observed=json.loads(probe.stdout);(out/'independent-probe.json').write_text(json.dumps(observed,indent=2)+'\n')
 record=dict(existing_tests=result.testsRun,existing_failures=len(result.failures),existing_errors=len(result.errors),independent_pass=observed['passed'],independent_fail=observed['failed'],blocked_operations=blocked,provider_calls=0,http_requests=0,synthetic_database_only=True)
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));print(probe.stdout)
