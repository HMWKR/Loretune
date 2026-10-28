"""Provider-neutral in-memory contract fixture. No sockets, credentials or vendor URLs."""
import base64,time,uuid
from types import SimpleNamespace
from fal_provider import ProviderError
MODEL='synthetic-image-fixture'
PROVIDER='synthetic-local'
CONNECTION='fixture-image-v1'
OUTPUT_POLICY='local-fixture-only'
RETENTION_NOTICE='로컬 합성 fixture · 외부 전송·보관 없음'
MAX_BYTES=16*1024*1024

def payload(prompt,ratio,references=()):
 if not isinstance(prompt,str) or not 1<=len(prompt)<=1000:raise ValueError('fixture prompt')
 if ratio not in {'1920:1080','1080:1920','1080:1080'}:raise ValueError('fixture ratio')
 refs=[]
 for raw in references:
  if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('fixture PNG')
  refs.append(base64.b64encode(raw).decode())
 if len(refs)>3:raise ValueError('fixture refs')
 return dict(model=MODEL,prompt=prompt,ratio=ratio,references=refs)

def validate_payload(data):
 if payload(data['prompt'],data['ratio'],[base64.b64decode(x,validate=True) for x in data['references']])!=data:raise ValueError('fixture payload')

def estimate():
 return dict(provider=PROVIDER,model=MODEL,kind='synthetic estimate; no charge',money={'amount':'0.08','currency':'USD'},output_count=1,expires=time.time()+300,automatic_retries=False)

class ImageFixture:
 mode='contract-fake';live_enabled=False;connection_id=CONNECTION;billing_source=None
 def __init__(self,transport=None):
  self._transport=transport;self.contract=SimpleNamespace(MODEL=MODEL,PROVIDER=PROVIDER,CONNECTION=CONNECTION,OUTPUT_POLICY=OUTPUT_POLICY,RETENTION_NOTICE=RETENTION_NOTICE,payload=payload,validate_payload=validate_payload,estimate=estimate)
 @staticmethod
 def identifier(receipt):
  try:
   value=uuid.UUID(receipt['request_id'])
   if value.version!=4:raise ValueError()
   return str(value)
  except (KeyError,ValueError,TypeError):raise ProviderError('untrusted_provider_receipt') from None
 def submit(self,data):
  validate_payload(data);value=self._transport('POST','fixture:submit',{},data)
  return dict(request_id=self.identifier({'request_id':value['id']}))
 def status(self,receipt):
  value=self._transport('GET','fixture:status',{},None)
  if value['id']!=self.identifier(receipt):raise ProviderError('untrusted_provider_receipt')
  state=value['status'];ready=state=='SUCCEEDED'
  result=dict(url=value['output'][0]) if ready else None
  if result:self.validate_output_url(result['url'])
  return dict(state='COMPLETED' if ready else 'IN_PROGRESS',provider_state=state,result_ready=ready,result=result,terminal_state={'FAILED':'failed','CANCELLED':'provider_cancelled'}.get(state))
 @staticmethod
 def validate_output_url(url):
  if url!='fixture://approved-image':raise ProviderError('untrusted_output_url')
 def download(self,url):
  self.validate_output_url(url);raise AssertionError('fixture download bytes must be explicitly injected')
 def cancel(self,receipt):raise ProviderError('cancel_not_supported')
