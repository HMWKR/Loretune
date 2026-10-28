import ast,json,socket,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
work=Path(json.loads((HERE/'base-manifest.json').read_text())['work'])
sys.path[:0]=[str(work),str(work/'tests')]
def denied(*args,**kwargs):raise AssertionError('ISOLATED_TEST_NO_NETWORK_OR_LISTENER')
socket.socket.connect=socket.socket.connect_ex=socket.socket.bind=socket.create_connection=denied
for p in ['chat_runtime.py','anthropic_ontology.py','tests/test_count_diagnostics.py']:ast.parse((work/p).read_text())
suite=unittest.defaultTestLoader.loadTestsFromNames(['test_count_diagnostics','test_chat_preflight','test_anthropic_transport'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
(HERE/'test-results.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),actual_network_calls=0,credential_file_reads=0,product_files_modified=False,work=str(work)),indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() else 1)
