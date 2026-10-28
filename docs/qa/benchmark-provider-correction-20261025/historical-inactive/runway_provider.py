"""Narrow, inactive Runway gen4_image adapter. No environment reads/retries.
Official OpenAPI 2026-10-25, version 2024-11-06. Signed output != fal private ACL.
"""
import base64,json,re,time,uuid
from urllib.parse import urlsplit
from urllib.request import Request,build_opener
from urllib.error import HTTPError,URLError
from http.client import IncompleteRead
from fal_provider import ProviderError,NoRedirect
MODEL='gen4_image'
BASE='https://api.dev.runwayml.com/v1/'
VERSION='2024-11-06'
CONNECTION='runway-gen4-image-v1'
PRICE_SOURCE='https://docs.dev.runwayml.com/guides/pricing/'
MAX_BYTES=16*1024*1024
RATIOS={'1920:1080','1080:1920','1080:1080'}  # explicitly bounded 1080p subset

def payload(prompt,ratio,references=()):
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt.encode('utf-16-le'))//2>1000:raise ValueError('Runway prompt must be 1–1000 UTF-16 units')
    if ratio not in RATIOS:raise ValueError('unsupported image ratio')
    if not isinstance(references,(list,tuple)) or len(references)>3:raise ValueError('at most three reference images')
    result=dict(model=MODEL,promptText=prompt,ratio=ratio)
    refs=[]
    for n,raw in enumerate(references):
        if not isinstance(raw,bytes) or not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('PNG references only in this integration')
        uri='data:image/png;base64,'+base64.b64encode(raw).decode()
        if len(uri)>5242880:raise ValueError('reference data URI exceeds 5MB')
        refs.append(dict(uri=uri,tag='ref'+str(n+1)))
    if refs:result['referenceImages']=refs
    return result

def validate_payload(data):
    if not isinstance(data,dict) or set(data)-{'model','promptText','ratio','referenceImages'} or data.get('model')!=MODEL:raise ValueError('unsupported image request')
    refs=[]
    for n,item in enumerate(data.get('referenceImages',[])):
        if set(item)!={'uri','tag'} or item['tag']!='ref'+str(n+1) or not item['uri'].startswith('data:image/png;base64,'):raise ValueError('unapproved reference role/input')
        refs.append(base64.b64decode(item['uri'].split(',',1)[1],validate=True))
    if payload(data.get('promptText'),data.get('ratio'),refs)!=data:raise ValueError('invalid image request')

def estimate():
    return dict(provider='runway',model=MODEL,kind='documented-estimate; invoice unverified',
        money={'amount':'0.08','currency':'USD'},credits=8,output_count=1,source=PRICE_SOURCE,
        checked='2026-10-25',expires=time.time()+300,automatic_retries=False)

class RunwayImage:
    def __init__(self,*,key=None,live_enabled=False,transport=None,output_hosts=()):
        self._key=key;self.live_enabled=live_enabled;self._transport=transport
        self.mode='contract-fake' if transport is not None else 'live-unverified' if live_enabled else 'disconnected'
        # No wildcard CloudFront trust. Runtime must approve exact documented/observed host.
        self.output_hosts=frozenset(output_hosts)
        for host in self.output_hosts:
            if not re.fullmatch(r'[a-z0-9-]+\.cloudfront\.net',host):raise ValueError('exact output host required')
    def _request(self,method,path,body=None):
        if not (method=='POST' and path=='text_to_image') and not (method in {'GET','DELETE'} and re.fullmatch(r'tasks/[0-9a-f-]{36}',path)):raise ProviderError('untrusted_provider_url')
        headers={'Content-Type':'application/json','X-Runway-Version':VERSION}
        if self._transport is not None:return self._transport(method,BASE+path,headers,body)
        if not self.live_enabled or not self._key:raise ProviderError('provider_not_connected')
        headers['Authorization']='Bearer '+self._key
        try:
            with build_opener(NoRedirect()).open(Request(BASE+path,method=method,headers=headers,data=json.dumps(body).encode() if body is not None else None),timeout=30) as response:
                raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ProviderError('provider_response_too_large',method=='POST')
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            code=exc.code;exc.close();raise ProviderError('provider_http_'+str(code),method=='POST' and code>=500) from None
        except (URLError,TimeoutError,OSError,ValueError,IncompleteRead):raise ProviderError('provider_response_uncertain',method=='POST') from None
    @staticmethod
    def identifier(receipt):
        try:
            value=uuid.UUID(receipt['request_id'])
            if value.version!=4:raise ValueError()
            return str(value)
        except (KeyError,ValueError,TypeError):raise ProviderError('untrusted_provider_receipt') from None
    def submit(self,data):
        validate_payload(data);value=self._request('POST','text_to_image',data)
        try:return {'request_id':self.identifier({'request_id':value['id']})}
        except (ProviderError,KeyError,TypeError):raise ProviderError('provider_receipt_uncertain',True) from None
    def status(self,receipt):
        identifier=self.identifier(receipt);value=self._request('GET','tasks/'+identifier)
        if value.get('id')!=identifier or value.get('status') not in {'PENDING','THROTTLED','RUNNING','SUCCEEDED','FAILED','CANCELLED'}:raise ProviderError('unknown_provider_state')
        state=value['status'];terminal=state in {'FAILED','CANCELLED'}
        # Returned task cost is provider-reported credits, never a USD payment invoice.
        billing={'source':'runway-task','request_id':identifier,'provider_state':state,
                 'credits':value.get('cost',{}).get('credits'),'estimated_credits':value.get('estimatedCost',{}).get('credits')}
        result=None
        if state=='SUCCEEDED':
            outputs=value.get('output')
            if not isinstance(outputs,list) or len(outputs)!=1:raise ProviderError('invalid_provider_result')
            self.validate_output_url(outputs[0]);result=dict(url=outputs[0],content_type=None,approved=False,cost_confirmed=False)
        return dict(state='IN_PROGRESS' if state=='RUNNING' else 'IN_QUEUE',provider_state=state,
            result_ready=state=='SUCCEEDED',result=result,terminal_state=('failed' if state=='FAILED' else 'provider_cancelled') if terminal else None,billing=billing)
    def validate_output_url(self,url):
        try:
            if not isinstance(url,str) or len(url)>16384:raise ValueError()
            p=urlsplit(url)
            if p.scheme!='https' or p.hostname not in self.output_hosts or p.username or p.password or p.port not in {None,443} or p.fragment or not p.path:raise ValueError()
        except (TypeError,ValueError):raise ProviderError('untrusted_provider_output') from None
    def cancel(self,receipt):
        # DELETE also deletes a completed task; do not turn a cancel race into data loss.
        raise ProviderError('cancel_unsupported_without_delete_authorization')
    def download(self,url):
        self.validate_output_url(url)
        if not self.live_enabled and self._transport is None:raise ProviderError('provider_not_connected')
        try:
            # Signed URL only: never forward the API key or authentication header.
            with build_opener(NoRedirect()).open(Request(url,headers={'Accept':'image/png,image/jpeg'}),timeout=30) as response:
                mime=response.headers.get('Content-Type','').split(';')[0].lower()
                if mime not in {'image/png','image/jpeg'}:raise ProviderError('result_mime_invalid')
                length=response.headers.get('Content-Length')
                if length is not None and (not length.isdigit() or not 0<int(length)<=MAX_BYTES):raise ProviderError('result_size_invalid')
                raw=response.read(MAX_BYTES+1)
                if not raw or len(raw)>MAX_BYTES or (length is not None and len(raw)!=int(length)):raise ProviderError('result_size_invalid')
                if (mime=='image/png' and not raw.startswith(b'\x89PNG\r\n\x1a\n')) or (mime=='image/jpeg' and not raw.startswith(b'\xff\xd8\xff')):raise ProviderError('result_mime_invalid')
                return raw
        except HTTPError as exc:
            code=exc.code;exc.close();raise ProviderError('download_http_'+str(code)) from None
        except (URLError,TimeoutError,OSError,IncompleteRead):raise ProviderError('download_interrupted') from None
