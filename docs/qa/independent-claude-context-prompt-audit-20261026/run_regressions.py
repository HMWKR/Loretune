"""Run explicit related offline tests; never discover the HTTP suite."""
import datetime,json,os,socket,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'snapshot'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'));os.chdir(ROOT)
def denied(*a,**k):raise RuntimeError('AUDIT_OFFLINE_NETWORK_FORBIDDEN')
socket.socket.connect=socket.socket.connect_ex=socket.socket.bind=denied
socket.create_connection=denied
modules=['tests.test_chat_runtime','tests.test_chat_protocols','tests.test_production_tools','tests.test_ontology','tests.test_project_ontology','tests.test_fal_multimodel','tests.test_action_execution','tests.test_chat_live_scope']
loader=unittest.TestLoader();loaded=loader.loadTestsFromNames(modules)
def flat(s):
 for x in s:
  if isinstance(x,unittest.TestSuite):yield from flat(x)
  else:yield x
excluded=['tests.test_project_ontology.ProjectOntologyTest.test_http_stale_ontology_is_conflict_and_request_retry_is_idempotent']
tests=[t for t in flat(loaded) if t.id() not in excluded]
# Only memory proposal cases from a renderer fixture; no render execution added.
for name in ['test_memory_exact_provenance_human_application_and_global_canon_unchanged','test_memory_duplicate_identity_preservation_and_foreign_render_job_isolation']:
 tests.extend(flat(loader.loadTestsFromName('tests.test_local_creation_tools.LocalToolsTest.'+name)))
passed=[]
class Result(unittest.TextTestResult):
 def addSuccess(self,test):passed.append(test.id());super().addSuccess(test)
result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.TestSuite(tests))
data=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),testsRun=result.testsRun,passed=passed,errors=[(t.id(),s) for t,s in result.errors],failures=[(t.id(),s) for t,s in result.failures],excludedNotRun=excluded,network='connect/bind denied; injected fake transports only',sharedDB='not read or written')
(HERE/'regression-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));sys.exit(0 if result.wasSuccessful() else 1)
