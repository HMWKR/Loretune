"""Allowlisted official fal contracts, not account availability or live enablement.
Output collection retains the approved private fal CDN policy; no public fallback.
Prices are injected verified quotes, never inferred across endpoints or credits.
"""
import base64,hashlib,json,time
from copy import deepcopy
from decimal import Decimal
import ledger

CONNECTION='fal-model-queue-v1'
MODELS={
 'fal-flux-schnell':dict(endpoint='fal-ai/flux/schnell',role='image',task='text-to-image'),
 'fal-flux-pro-1-1':dict(endpoint='fal-ai/flux-pro/v1.1',role='image',task='text-to-image'),
 'fal-kling-2-6-pro':dict(endpoint='fal-ai/kling-video/v2.6/pro/image-to-video',role='video',task='image-to-video'),
 'fal-kling-2-5-turbo':dict(endpoint='fal-ai/kling-video/v2.5-turbo/pro/image-to-video',role='video',task='image-to-video'),
}
SIZES={'16:9':{'width':1024,'height':576},'9:16':{'width':576,'height':1024},'1:1':{'width':1024,'height':1024}}
# D19 (user decision 2026-10-28): published fal model-page unit prices, read once
# without an account. A documented estimate shown beside the quote; never a quote,
# a billing claim or an execution input. Verbatim page text:
#  flux/schnell "$0.003 per megapixel" / flux-pro/v1.1 "$0.04 per megapixel",
#   both "Images are billed by rounding up to the nearest megapixel."
#  kling v2.6 pro i2v "Videos generated without audio cost $0.07 per second."
#  kling v2.5-turbo pro i2v "For 5s video your request will cost $0.35. For every
#   additional second you will be charged $0.07." (= 0.07/s for the 5s and 10s allowed here)
PRICE_FETCHED_AT='2026-10-28T09:28:18Z'
PRICE_REVISION='fal-public-model-pages-20261028'
UNIT_PRICES={
 'fal-flux-schnell':dict(amount='0.003',currency='USD',unit='megapixel',source='https://fal.ai/models/fal-ai/flux/schnell'),
 'fal-flux-pro-1-1':dict(amount='0.04',currency='USD',unit='megapixel',source='https://fal.ai/models/fal-ai/flux-pro/v1.1'),
 'fal-kling-2-6-pro':dict(amount='0.07',currency='USD',unit='second',source='https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video'),
 'fal-kling-2-5-turbo':dict(amount='0.07',currency='USD',unit='second',source='https://fal.ai/models/fal-ai/kling-video/v2.5-turbo/pro/image-to-video'),
}

def unit_price(identifier):
 item=UNIT_PRICES.get(identifier)
 if item is None:return None
 return dict(deepcopy(item),fetched_at=PRICE_FETCHED_AT,revision=PRICE_REVISION,kind='documented-estimate')

def price_view(identifier,options,quote_money=None,unit=None):
 """Unit x quantity for the configured output beside the quote total; neither replaces the other."""
 unit=deepcopy(unit) if unit else unit_price(identifier)
 if unit is None:return dict(unit_price=None,reason='공식 단가를 찾지 못했습니다.')
 rate=Decimal(unit['amount'])
 if unit['unit']=='second':
  quantity=int(options['duration']);formula=f"{unit['amount']} USD/초 × {quantity}초"
 else:
  size=SIZES[options['ratio']];pixels=size['width']*size['height']
  # The pages do not define a megapixel; publish a per-image figure only where 10^6 and 2^20 agree.
  decimal,binary=-(-pixels//1_000_000),-(-pixels//1_048_576)
  formula=f"올림({size['width']}×{size['height']} px ÷ 1MP) × {unit['amount']} USD/MP"
  if decimal!=binary:
   return dict(unit_price=unit,quantity=None,expected_total=None,formula=formula,quote_total=deepcopy(quote_money),matches_quote=None,
               reason=f'메가픽셀 정의(10^6 또는 2^20 px)가 공개 문서에 없어 장당 금액 미확정: {rate*decimal} 또는 {rate*binary} USD')
  quantity=decimal
 expected=ledger.money(int(rate*quantity*1_000_000),unit['currency'])
 value=dict(unit_price=unit,quantity=quantity,expected_total=expected,formula=formula+f' = {expected["amount"]} USD',quote_total=deepcopy(quote_money))
 value['matches_quote']=None if quote_money is None else ledger.units(quote_money)==ledger.units(expected) and quote_money['currency']==expected['currency']
 if value['matches_quote'] is False:value['mismatch']='견적 총액과 단가×수량이 다릅니다. 둘 다 표시하며 어느 쪽도 자동 선택하지 않습니다.'
 return value

def identifier_for(endpoint):
 return next((k for k,v in MODELS.items() if v['endpoint']==endpoint),None)

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
