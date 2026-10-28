"""Offline isolated tests; never activates hooks or changes canonical inputs."""
import copy, hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys, tempfile, time

REPO = pathlib.Path('/Users/leesungmin/Desktop/Loretune')
SOURCE = REPO/'tools/document-gate/check.py'
OUT = pathlib.Path(__file__).parent
results = []

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

with tempfile.TemporaryDirectory(prefix='independent-document-gate-') as temp:
    stage = pathlib.Path(temp).resolve()
    engine = stage/'tools/document-gate/check.py'
    engine.parent.mkdir(parents=True)
    shutil.copy2(SOURCE, engine)
    tests = stage/'tests/document-gate'
    tests.mkdir(parents=True)
    shutil.copy2(REPO/'tests/document-gate/test_gate.py', tests/'test_gate.py')
    spec = importlib.util.spec_from_file_location('isolated_gate', engine)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    base = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(tests), '-v'], cwd=stage, capture_output=True, text=True, timeout=30)
    (OUT/'existing-fixtures.log').write_text(base.stdout+base.stderr)

    def fixture(name):
        root = stage/name
        root.mkdir()
        def write(path, value):
            p=root/path;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(value if isinstance(value,str) else json.dumps(value))
        write('docs/current.md','SYNTHETIC_CURRENT')
        write('kit/docs/current.md','SYNTHETIC_CURRENT')
        write('kit/context.md','SYNTHETIC_CONTEXT')
        registry={'project_id':'synthetic-registry','registry_revision':1,'objects':[{'id':'D','kind':'Document','canonical_key':'Document:current','file':'docs/current.md','sha256':sha(root/'docs/current.md')}],'heads':{'Document:current':'D'}}
        write('kit/registry.json',registry)
        receipt={'registry_revision':1,'registry_sha256':sha(root/'kit/registry.json'),'context_file':'context.md','context_sha256':sha(root/'kit/context.md'),'heads':registry['heads']}
        write('kit/receipt.json',receipt)
        policy={'schema_version':1,'project_id':'synthetic','scan':{'roots':['docs'],'extensions':['.md']},'registries':[{'name':'kit','base':'kit','path':'kit/registry.json','project_id':'synthetic-registry'}],'documents':[{'path':'docs/current.md','classification':'current','registration':'required','reason':'synthetic','registrations':[{'registry':'kit','file':'docs/current.md','require_head':True}]}],'contexts':[{'registry':'kit','receipt':'kit/receipt.json','usage':'current','reason':'synthetic'}]}
        write('.document-gate.json',policy)
        return root,policy,write

    root,p,write=fixture('fresh-pending-context')
    p['contexts'][0].update(usage='review-required',reason='Still undecided whether current or historical')
    write('.document-gate.json',p)
    result,code=gate.check(root)
    results.append({'id':'DG01a','expected':'nonzero/review-required until classification resolved','observed':{'exit':code,'status':result['status'],'findings':result['findings'],'warnings':result['warnings']},'pass':code!=0})

    root,p,write=fixture('pending-document-exempt-registration')
    p['documents'][0].update(classification='legacy-review-pending',registration='not-required',baseline_sha256=sha(root/'docs/current.md'))
    write('.document-gate.json',p)
    result,code=gate.check(root)
    results.append({'id':'DG01b','expected':'nonzero/review-required while document classification is unresolved','observed':{'exit':code,'status':result['status']},'pass':code!=0})

    root,p,write=fixture('fifo-document')
    (root/'docs/current.md').unlink()
    os.mkfifo(root/'docs/current.md',0o600)
    payload=json.dumps({'hook_event_name':'Stop','cwd':str(root),'stop_hook_active':False})
    started=time.monotonic()
    try:
        proc=subprocess.run([sys.executable,'-B',str(engine),'--hook'],input=payload,capture_output=True,text=True,timeout=1.5)
        observation={'exit':proc.returncode,'stdout':proc.stdout,'elapsed_seconds':time.monotonic()-started}
        passed=proc.returncode==0 and 'incomplete' in proc.stdout
    except subprocess.TimeoutExpired:
        observation={'timeout_seconds':1.5,'elapsed_seconds':time.monotonic()-started,'isolated_child_killed_and_waited':True,'native_hook_executed':False}
        passed=False
    results.append({'id':'DG02','expected':'reject nonregular file promptly with bounded incomplete result','observed':observation,'pass':passed})

    root,p,write=fixture('malformed-registry')
    write('kit/registry.json',{'project_id':'synthetic-registry','registry_revision':1,'objects':[None],'heads':{}})
    proc=subprocess.run([sys.executable,'-B',str(engine),'--hook'],input=json.dumps({'hook_event_name':'Stop','cwd':str(root),'stop_hook_active':False}),capture_output=True,text=True,timeout=3)
    results.append({'id':'DG03','expected':'structured incomplete JSON, no traceback','observed':{'exit':proc.returncode,'stdout':proc.stdout,'stderr_tail':proc.stderr.splitlines()[-2:]},'pass':proc.returncode==0 and 'incomplete' in proc.stdout})

    root,p,write=fixture('ordinary-guards')
    (root/'docs/new.md').write_text('SYNTHETIC_NEW')
    block=gate.hook({'hook_event_name':'Stop','cwd':str(root),'stop_hook_active':False})
    resumed=gate.hook({'hook_event_name':'Stop','cwd':str(root),'stop_hook_active':True})
    results.append({'id':'C01','expected':'one continuation then warning','observed':{'first':block,'second':resumed},'pass':block.get('decision')=='block' and 'decision' not in resumed})
    unrelated=stage/'no-policy';unrelated.mkdir()
    result,code=gate.check(unrelated)
    results.append({'id':'C02','expected':'not-configured=2; no policy creation','observed':{'exit':code,'status':result['status'],'files':list(unrelated.iterdir())},'pass':code==2 and not list(unrelated.iterdir())})
    root,p,write=fixture('command-injection-guard')
    p['command']='SHOULD_NEVER_EXECUTE';write('.document-gate.json',p)
    try:gate.check(root);blocked=False
    except gate.Invalid:blocked=True
    results.append({'id':'C03','expected':'unknown command policy rejected','observed':{'blocked':blocked},'pass':blocked})
    manifest={'source_sha256':sha(engine),'source_unchanged':sha(engine)==sha(SOURCE),'python':sys.version,'baseline_exit':base.returncode,'results':results,'scope':'isolated local fixtures only; no actual hooks, providers, shared registry or product data'}
    (OUT/'results.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
