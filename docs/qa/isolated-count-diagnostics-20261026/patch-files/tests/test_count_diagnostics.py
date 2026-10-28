"""Offline provenance tests: never read an error body or persist upstream text."""
import io,json,sqlite3,unittest,urllib.error
from unittest.mock import Mock
import anthropic_ontology as provider
import chat_runtime as chat
from tests import test_chat_runtime as fixture
from test_anthropic_transport import Response

KEY='synthetic-key-DO-NOT-RETAIN'
PRIVATE='private-customer-DO-NOT-RETAIN'
RID='req_synthetic_count_01'
class NoRead(io.BytesIO):
 def read(self,*args,**kwargs):raise AssertionError('error body must never be read')
class DiagnosticsTest(unittest.TestCase):
 setUp=fixture.ChatRuntimeTest.setUp
 call=fixture.ChatRuntimeTest.call
 connect=fixture.ChatRuntimeTest.connect
 enqueue=fixture.ChatRuntimeTest.enqueue
 turn=fixture.ChatRuntimeTest.turn
 rows=fixture.ChatRuntimeTest.rows
 def setup_diagnostic(self,*,count_failure=None,count_raw=b'{"input_tokens":100}',rid=RID,message_failure=None,supplier_failure=None):
  self.co=Mock();self.mo=Mock();self.secret_calls=[]
  if count_failure is not None:self.co.open.side_effect=count_failure
  else:self.co.open.return_value=Response(count_raw,url=provider.BoundedCountTransport.endpoint,headers={'Content-Type':'application/json','request-id':rid})
  if message_failure is not None:self.mo.open.side_effect=message_failure
  else:self.mo.open.return_value=Response(json.dumps(fixture.response()).encode())
  def supplier(name):
   self.secret_calls.append(name)
   if supplier_failure:raise supplier_failure
   return KEY
  a=chat.AnthropicChatAdapter(supplier,enabled=True,count_transport=provider.BoundedCountTransport(opener=self.co,max_request_bytes=65536),message_transport=provider.BoundedMessagesTransport(opener=self.mo,max_request_bytes=65536));a.mode='contract-fake';self.connect(a)
 def execute(self):self.enqueue();self.runtime.process_next();return self.turn()
 def failure(self):
  t=self.turn()
  with sqlite3.connect(self.journal) as c:meta=json.loads(c.execute('SELECT metadata FROM trials ORDER BY rowid DESC LIMIT 1').fetchone()[0])
  self.assertEqual(t['steps'][-1]['failure'],meta['failure']);return meta['failure']
 def no_leaks(self):
  for p in self.root.rglob('*'):
   if p.is_file():
    data=p.read_bytes()
    for value in [KEY,PRIVATE,'authorization','x-api-key']:
     self.assertNotIn(value.encode(),data,str(p))
 def test_count_http_status_and_header_id_no_error_body_or_secret(self):
  failure=urllib.error.HTTPError(provider.BoundedCountTransport.endpoint,400,KEY+PRIVATE,{'request-id':RID,'authorization':KEY},NoRead((KEY+PRIVATE).encode()))
  self.setup_diagnostic(count_failure=failure);self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='http',http_status=400,request_id=RID))
  self.assertEqual(self.rows(),[('blocked_before_message',0,None)]);self.mo.open.assert_not_called();self.no_leaks()
 def test_invalid_http_status_and_request_id_are_omitted(self):
  failure=urllib.error.HTTPError(provider.BoundedCountTransport.endpoint,999,PRIVATE,{'request-id':'req_bad\r\n'+KEY},NoRead())
  self.setup_diagnostic(count_failure=failure);self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='http'));self.no_leaks()
 def test_count_transport_timeout_has_no_upstream_text_and_no_retry(self):
  self.setup_diagnostic(count_failure=TimeoutError(KEY+PRIVATE));self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='transport'))
  self.assertEqual(self.rows(),[('blocked_before_message',0,None)]);self.assertFalse(self.runtime.process_next());self.assertEqual(self.co.open.call_count,1);self.mo.open.assert_not_called();self.no_leaks()
 def test_malformed_json_preserves_only_valid_header_id(self):
  self.setup_diagnostic(count_raw=(KEY+PRIVATE).encode());self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='malformed_response',request_id=RID));self.no_leaks()
 def test_missing_count_field_is_malformed_not_silent_transport_error(self):
  self.setup_diagnostic(count_raw=json.dumps({'echo':KEY+PRIVATE}).encode());self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='malformed_response',request_id=RID));self.no_leaks()
 def test_response_body_cannot_supply_request_id(self):
  self.setup_diagnostic(count_raw=json.dumps({'_request_id':'req_forged_body','echo':PRIVATE}).encode(),rid='invalid header')
  self.execute();self.assertEqual(self.failure(),dict(stage='count',category='malformed_response'));self.no_leaks()
 def test_credential_failure_is_classified_without_reading_files(self):
  self.setup_diagnostic(supplier_failure=ValueError(KEY+PRIVATE));self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='credentials'));self.co.open.assert_not_called();self.mo.open.assert_not_called();self.no_leaks()
 def test_messages_timeout_stays_unknown_and_reserved(self):
  self.setup_diagnostic(message_failure=TimeoutError(KEY+PRIVATE));self.execute()
  self.assertEqual(self.failure(),dict(stage='messages',category='transport'))
  self.assertEqual(self.rows(),[('outcome_unknown',2458,None)])
  with self.assertRaises(ValueError):self.enqueue()
  self.assertEqual(self.mo.open.call_count,1);self.assertFalse(self.runtime.process_next());self.no_leaks()
 def test_request_id_echoing_credential_is_omitted(self):
  failure=urllib.error.HTTPError(provider.BoundedCountTransport.endpoint,400,PRIVATE,{'request-id':'req_'+KEY},NoRead())
  self.setup_diagnostic(count_failure=failure);self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='http',http_status=400));self.no_leaks()
 def test_over_limit_count_is_a_local_limit_failure(self):
  self.setup_diagnostic(count_raw=b'{"input_tokens":4097}');self.execute()
  self.assertEqual(self.failure(),dict(stage='count',category='input_limit'))
  self.assertEqual(self.rows(),[('blocked_before_message',0,None)]);self.mo.open.assert_not_called();self.no_leaks()

if __name__=='__main__':unittest.main()
