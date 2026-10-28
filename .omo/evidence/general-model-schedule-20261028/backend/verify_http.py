import hashlib,json,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root))
from tests import test_general_model_schedule as schedule,test_general_model_capability as capability
out=Path(__file__).resolve().parent
records=[]
classes=(schedule.GeneralModelSchedulingHTTPTest,capability.GeneralModelCapabilityHTTPTest)
for cls in classes:
    original_request=cls.request
    original_setup=cls.setUp
    def request(self,method,path,body=None,headers=None,_request=original_request):
        status,result=_request(self,method,path,body,headers)
        if path.startswith('/api/state'):
            projects={name:{k:p.get(k) for k in ('effective_chat_selection','active_conversation','general_chat_connection','general_chat_turns','general_chat_previews')} for name,p in result.get('projects',{}).items()}
            observed={'revision':result.get('revision'),'projects':projects}
        else:observed=result
        records.append(dict(test=self.id(),method=method,path=path,action=(body or {}).get('action'),data=(body or {}).get('data'),status=status,result=observed))
        return status,result
    def setup(self,_setup=original_setup):
        _setup(self)
        def capture():
            records.append(dict(test=self.id(),synthetic_provider_requests=[dict(url=u,body=json.loads(b),sha256=hashlib.sha256(b).hexdigest()) for u,b,t in self.socket.requests],synthetic_credential_reads=len(self.keys)))
        self.addCleanup(capture)
    cls.request=request;cls.setUp=setup
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in classes)
result=unittest.TextTestRunner(verbosity=2).run(suite)
(out/'http-receipts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
(out/'http-result.json').write_text(json.dumps(dict(tests=result.testsRun,passed=result.wasSuccessful(),failures=len(result.failures),errors=len(result.errors),real_provider_calls=0)))
sys.exit(not result.wasSuccessful())
