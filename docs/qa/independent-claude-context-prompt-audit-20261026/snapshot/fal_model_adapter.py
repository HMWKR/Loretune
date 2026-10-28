"""Real fal queue adapter using allowlisted per-model contracts; disabled by default.
Synthetic transports exercise the same submit/status/result/cancel code. Private
image-to-video chaining re-encodes validated local bytes; never forwards a CDN URL.
"""
import io,uuid
from urllib.parse import urlsplit
import fal_provider as fal
from fal_models import Contract,CONNECTION

class FalModelAdapter(fal.FalKling):
 connection_id=CONNECTION
 def __init__(self,identifier,*,quote=None,**kwargs):
  super().__init__(**kwargs);self.contract=Contract(identifier,quote);self.model_endpoint=self.contract.MODEL
  self.prefix=fal.BASE+'/'.join(self.model_endpoint.split('/')[:2])+'/requests/'
 def submit(self,data):
  self.contract.validate_payload(data);value=self._request('POST',fal.BASE+self.model_endpoint,data)
  try:
   identifier=str(uuid.UUID(value['request_id']));receipt={k:value[k] for k in ('status_url','response_url','cancel_url')};receipt['request_id']=identifier
   for key in ('status_url','response_url','cancel_url'):self._url(receipt,key)
  except (KeyError,TypeError,ValueError,fal.ProviderError):raise fal.ProviderError('provider_receipt_uncertain',True) from None
  return receipt
 def _url(self,receipt,name):
  try:
   identifier=str(uuid.UUID(receipt['request_id']));expected=self.prefix+identifier+{'status_url':'/status','response_url':'','cancel_url':'/cancel'}[name]
   if receipt[name]!=expected:raise ValueError()
   return expected
  except (KeyError,TypeError,ValueError):raise fal.ProviderError('untrusted_provider_receipt') from None
 def result(self,receipt):
  value=self._request('GET',self._url(receipt,'response_url'))
  try:
   if self.contract.role=='image':
    if len(value['images'])!=1 or any(value.get('has_nsfw_concepts',[])):raise ValueError()
    asset=value['images'][0]
   else:asset=value['video']
   p=urlsplit(asset['url'])
   if p.scheme!='https' or p.hostname!='v3b.fal.media' or p.port not in (None,443) or p.username or p.password or p.fragment:raise ValueError()
   return dict(url=asset['url'],content_type=asset.get('content_type'),approved=False,cost_confirmed=False)
  except (KeyError,TypeError,ValueError):raise fal.ProviderError('invalid_provider_result') from None
 def read_video(self,response):
  if self.contract.role=='video':return super().read_video(response)
  mime=response.headers.get('Content-Type','').split(';')[0].lower().strip()
  if mime!='image/png':raise fal.ProviderError('invalid_media_content_type')
  limit=16*1024*1024;declared=response.headers.get('Content-Length')
  try:length=int(declared) if declared is not None else None
  except ValueError:raise fal.ProviderError('invalid_media_length') from None
  if length is not None and not 0<length<=limit:raise fal.ProviderError('provider_media_too_large')
  data=response.read(limit+1)
  if len(data)>limit:raise fal.ProviderError('provider_media_too_large')
  if length is not None and len(data)!=length:raise fal.ProviderError('truncated_media')
  if not data.startswith(b'\x89PNG\r\n\x1a\n'):raise fal.ProviderError('invalid_png_signature')
  return data
