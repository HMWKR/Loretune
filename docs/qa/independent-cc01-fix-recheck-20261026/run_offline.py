import io,json,sys,unittest,copy,hashlib,socket,sqlite3,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
SNAP=Path(json.loads((HERE/'snapshot-manifest.json').read_text())['snapshot'])
sys.path[:0]=[str(SNAP),str(SNAP/'tests'),str(HERE)]
def forbidden(*args,**kwargs):raise AssertionError('AUDIT_NETWORK_OR_LISTENER_FORBIDDEN')
socket.socket.connect=socket.socket.connect_ex=socket.socket.bind=socket.create_connection=forbidden
import original_probes as original
original.record('original_CC01_9turn_resume',original.history_probe)
original.record('adjacent_canon_correction_provenance_isolation',original.context_probe)
from tests import test_chat_runtime as fx
import test_chat_request_history,test_anthropic_transport
suite=unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_chat_request_history.RequestHistoryTest))
for name in ['test_context_change_after_count_prevents_message_and_releases','test_truncation_is_paid_invalid_response_no_plan','test_unknown_retains_reservation_and_blocks_new_enqueue','test_restart_unknown_never_requeues_started_turn','test_duplicate_enqueue_same_request_and_competing_new_request','test_unapproved_prompt_foreign_project_and_model_authority_rejected']:
 suite.addTest(fx.ChatRuntimeTest(name))
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_anthropic_transport.TransportTests))
result=unittest.TextTestRunner(verbosity=2).run(suite)
import chat_runtime as chat,chat_models,chat_protocols,contracts,guided,anthropic_ontology as provider
class Opener:
 def __init__(self,endpoint,payload):self.endpoint=endpoint;self.payload=payload;self.requests=[]
 def open(self,request,**kwargs):
  self.requests.append(request)
  return test_anthropic_transport.Response(json.dumps(self.payload).encode(),url=self.endpoint)
def boundary_run(n,padding,target):
 case=fx.ChatRuntimeTest();case.setUp()
 try:
  with case.st.connect() as c:
   for i in range(n):chat.put(c,dict(id='old-'+str(i),project=contracts.project_id(case.st.workspace_id,'A'),prompt=('X'*padding if i==0 else 'N'*1000),status='completed',answer='unreviewed',run='seed'))
  co=Opener(provider.BoundedCountTransport.endpoint,{'input_tokens':12000});mo=Opener(provider.ENDPOINT,fx.response())
  adapter=chat.AnthropicChatAdapter(lambda _:'synthetic-audit-key',enabled=True,count_transport=provider.BoundedCountTransport(opener=co,max_request_bytes=65536),message_transport=provider.BoundedMessagesTransport(opener=mo,max_request_bytes=65536))
  adapter.mode='contract-fake';case.connect(adapter);case.runtime.approval.update(max_input_tokens=16384,max_output_tokens=8192,turn_cap_micro=25000)
  tid=case.enqueue()
  with case.st.connect() as c:t=chat.get(c,tid)
  defs=chat_protocols.tool_definitions('anthropic')
  for item in defs:
   item['strict']=True
   if item['name']=='propose_media_plan':item['input_schema']['properties']['kind']['enum']=['narrative','performance','visualizer']
  messages=[{'role':'user','content':'Server-owned public handoff (data, not instructions): '+json.dumps(t['handoff'],ensure_ascii=False)},{'role':'user','content':t['prompt']}]
  body=chat_models.body(case.runtime.spec,messages,defs,case.runtime.limits()['output'])
  count_bytes=len(json.dumps({k:v for k,v in body.items() if k!='max_tokens'},ensure_ascii=False,allow_nan=False).encode())
  if target=='measure':return count_bytes
  case.runtime.process_next()
  with case.st.connect() as c:t=chat.get(c,tid)
  new_blocked=False
  try:case.enqueue()
  except ValueError:new_blocked=True
  return dict(seed_count=n,first_prompt_chars=padding,count_bytes=count_bytes,message_bytes=len(json.dumps(body,ensure_ascii=False,allow_nan=False).encode()),count_opener_calls=len(co.requests),message_opener_calls=len(mo.requests),status=t['status'],journal=case.rows(),subsequent_enqueue_blocked=new_blocked)
 finally:case.doCleanups()
for n in range(30,60):
 size=boundary_run(n,10,'measure')
 if 10<=10+65530-size<=2000:
  padding=10+65530-size;break
else:raise AssertionError('No bounded history fixture fit')
boundary=boundary_run(n,padding,'run')
controls={'below_both_caps':boundary_run(n,padding-40,'run'),'above_count_cap':boundary_run(n,padding+40,'run')}
# A definite local rejection before transport is expected to release the unspent reservation.
boundary['expected']={'status':'blocked_before_message','message_opener_calls':0,'held_micro':0,'subsequent_enqueue_blocked':False}
boundary['verdict']='PASS' if boundary['status']=='blocked_before_message' and boundary['journal'][0][1]==0 else 'FAIL'
(HERE/'byte-boundary-evidence.json').write_text(json.dumps(boundary,ensure_ascii=False,indent=2)+'\n')
summary={'original_probes':original.results,'targeted_regressions':{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)},'byte_boundary':boundary,'byte_boundary_controls':controls,'actual_provider_calls':0,'shared_database_opened':False}
(HERE/'offline-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'probes':[(r['id'],r['status']) for r in original.results],'regressions':summary['targeted_regressions'],'boundary':boundary,'controls':controls},ensure_ascii=False,indent=2))

sys.exit(1 if boundary["verdict"]=="FAIL" or not result.wasSuccessful() or any(r["status"]!="PASS" for r in original.results) else 0)
