import json,sys,unittest,socket
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SNAP=Path(json.loads((HERE/'snapshot-manifest.json').read_text())['snapshot'])
sys.path[:0]=[str(SNAP),str(SNAP/'tests')]
def forbidden(*args,**kwargs):raise AssertionError('AUDIT_NETWORK_OR_LISTENER_FORBIDDEN')
socket.socket.connect=socket.socket.connect_ex=socket.socket.bind=socket.create_connection=forbidden
from tests import test_chat_runtime as fx
import chat_runtime as chat,chat_models,chat_protocols,contracts,anthropic_ontology as provider,test_anthropic_transport,test_chat_preflight
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
  supplier_calls=[]
  def supplier(name):supplier_calls.append(name);return 'synthetic-audit-key'
  adapter=chat.AnthropicChatAdapter(supplier,enabled=True,count_transport=provider.BoundedCountTransport(opener=co,max_request_bytes=65536),message_transport=provider.BoundedMessagesTransport(opener=mo,max_request_bytes=65536))
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
  return dict(seed_count=n,first_prompt_chars=padding,count_bytes=count_bytes,message_bytes=len(json.dumps(body,ensure_ascii=False,allow_nan=False).encode()),supplier_calls=len(supplier_calls),count_opener_calls=len(co.requests),message_opener_calls=len(mo.requests),status=t['status'],journal=case.rows(),subsequent_enqueue_blocked=new_blocked)
 finally:case.doCleanups()

with patch('time.time',return_value=1793030000.0):
 for n in range(30,60):
  size=boundary_run(n,10,'measure')
  if 10<=10+65529-size<=2000:
   padding=10+65529-size;break
 else:raise AssertionError('fixture fit unavailable')
 observed=boundary_run(n,padding,'run')
expected=dict(count_bytes=65529,message_bytes=65549,count_opener_calls=0,message_opener_calls=0,supplier_calls=0,status='blocked_before_message',subsequent_enqueue_blocked=False)
assert all(observed[k]==v for k,v in expected.items()),observed
assert observed['journal']==[('blocked_before_message',0,None)],observed
original={'status':'PASS','observed':observed,'expected':expected}
suite=unittest.TestSuite()
for name in ['test_exact_messages_limit_sends_exact_validated_payload','test_one_byte_above_messages_limit_never_count_or_messages','test_count_network_failure_is_not_messages_submission_and_does_not_retry','test_messages_network_failure_keeps_unknown_reservation_and_duplicate_guard','test_preflight_releases_only_this_reservation','test_later_round_local_rejection_preserves_completed_usage_and_tool_result']:
 suite.addTest(test_chat_preflight.ChatPreflightTest(name))
result=unittest.TextTestRunner(verbosity=2).run(suite)
value=dict(original_counterexample=original,nearest_guards=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors)),actual_provider_calls=0,secret_file_reads=0,shared_database_opened=False,sockets='forbidden')
(HERE/'results.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
