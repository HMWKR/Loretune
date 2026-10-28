"""Allowlisted official fal contracts, not account availability or live enablement.
Output collection retains the approved private fal CDN policy; no public fallback.
Prices are injected verified quotes, never inferred across endpoints or credits.
"""
import base64,hashlib,json,time
from copy import deepcopy
import ledger

CONNECTION='fal-model-queue-v1'
MODELS={
 'fal-flux-schnell':dict(endpoint='fal-ai/flux/schnell',role='image',task='text-to-image'),
 'fal-flux-pro-1-1':dict(endpoint='fal-ai/flux-pro/v1.1',role='image',task='text-to-image'),
 'fal-kling-2-6-pro':dict(endpoint='fal-ai/kling-video/v2.6/pro/image-to-video',role='video',task='image-to-video'),
 'fal-kling-2-5-turbo':dict(endpoint='fal-ai/kling-video/v2.5-turbo/pro/image-to-video',role='video',task='image-to-video'),
}
SIZES={'16:9':{'width':1024,'height':576},'9:16':{'width':576,'height':1024},'1:1':{'width':1024,'height':1024}}

def spec(identifier):
 if identifier not in MODELS:raise ValueError('unsupported fal selection; no fallback')
 item=deepcopy(MODELS[identifier]);item.update(id=identifier,source='https://fal.ai/models/'+item['endpoint']+'/api');return item

class Contract:
 PROVIDER='fal.ai';CONNECTION=CONNECTION
 def __init__(self,identifier,quote=None):
  self.spec=spec(identifier);self.MODEL=self.spec['endpoint'];self.role=self.spec['role'];self.quote=deepcopy(quote)
 def payload(self,prompt,options,frames=()):
  if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=1000:raise ValueError('prompt required, maximum 1000 characters')
  if self.role=='image':
   if set(options)!={'ratio'} or options['ratio'] not in SIZES or frames:raise ValueError('selected text-to-image model does not support reference roles')
   value=dict(prompt=prompt,image_size=deepcopy(SIZES[options['ratio']]),num_images=1,output_format='png')
   if self.spec['id']=='fal-flux-schnell':value.update(num_inference_steps=4,enable_safety_checker=True)
   else:value.update(safety_tolerance='2',enhance_prompt=False)
   return value
  if set(options)!={'duration','generate_audio'} or type(options['duration']) is not int or options['duration'] not in (5,10) or options['generate_audio'] is not False:raise ValueError('unsupported duration/audio options')
  if len(frames)!=1 or not isinstance(frames[0],bytes) or not frames[0].startswith(b'\x89PNG\r\n\x1a\n') or not 0<len(frames[0])<=4*1024*1024:raise ValueError('one validated local PNG start frame required')
  value=dict(prompt=prompt,duration=str(options['duration']),enable_safety_checker=True)
  field='start_image_url' if self.spec['id']=='fal-kling-2-6-pro' else 'image_url'
  value[field]='data:image/png;base64,'+base64.b64encode(frames[0]).decode()
  if self.spec['id']=='fal-kling-2-6-pro':value['generate_audio']=False
  return value
 def validate_payload(self,data):
  try:
   if self.role=='image':
    ratio=next(k for k,v in SIZES.items() if v==data['image_size']);expected=self.payload(data['prompt'],{'ratio':ratio})
   else:
    field='start_image_url' if self.spec['id']=='fal-kling-2-6-pro' else 'image_url';uri=data[field]
    if not uri.startswith('data:image/png;base64,'):raise ValueError()
    raw=base64.b64decode(uri.split(',',1)[1],validate=True);expected=self.payload(data['prompt'],{'duration':int(data['duration']),'generate_audio':False},[raw])
   if expected!=data:raise ValueError()
  except (KeyError,TypeError,ValueError,StopIteration):raise ValueError('fal model input contract mismatch') from None
 def estimate(self,data):
  self.validate_payload(data);q=deepcopy(self.quote)
  if not q or q.get('model')!=self.MODEL or q.get('provider')!=self.PROVIDER or q.get('input_sha256')!=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest():raise ValueError('current model/input price quote required')
  if q.get('kind') not in {'fixture','documented-estimate'} or q.get('expires',0)<=time.time() or q.get('expires',0)>time.time()+86400:raise ValueError('price validity required')
  if q.get('source')!=self.spec['source'] or not q.get('price_revision') or q.get('money',{}).get('currency')!='USD' or ledger.units(q['money'])<=0:raise ValueError('verified price source required')
  return q
