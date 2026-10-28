"""Narrow Kling queue adapter. Disabled by default; never loads .env or auto-retries."""
import io
from http.client import IncompleteRead
import hashlib
import base64
import json
import os
import re
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

MODEL='fal-ai/kling-video/v2.6/pro/image-to-video'
BASE='https://queue.fal.run/'
PRICE_SOURCE='https://fal.ai/models/'+MODEL
TOKEN_URL='https://rest.fal.ai/storage/auth/token?storage_type=fal-cdn-v3'
MAX_RESULT_BYTES=128*1024*1024
LIFECYCLE={'expiration_duration_seconds':3600,'initial_acl':{'default':'forbid','rules':[]}}

def private_lifecycle_candidate(nickname):
    """Pure proposal only; syntax checks do NOT establish identity or authorize sending.

    Live submit still uses LIFECYCLE until a verified nickname is bound to approval.
    This intentionally conservative alphabet is a local guard, not fal's full schema.
    """
    if not isinstance(nickname,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',nickname):
        raise ValueError('정확히 확인된 fal nickname이 필요합니다. 이메일·표시 이름·URL은 사용할 수 없습니다.')
    return {'expiration_duration_seconds':3600,'initial_acl':{'default':'forbid',
            'rules':[{'user':nickname,'decision':'allow'}]}}

class ProviderError(RuntimeError):
    def __init__(self,code,uncertain=False):
        super().__init__(code);self.code=code;self.uncertain=uncertain
        self.terminal=code in {'provider_http_400','provider_http_401','provider_http_403','provider_http_404','provider_http_410','provider_http_422','unknown_provider_state','invalid_provider_result'}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def payload(prompt,image):
    if not isinstance(prompt,str) or not 1<=len(prompt.strip())<=1000:raise ValueError('장면 지시를 1~1000자로 입력하세요.')
    if not isinstance(image,bytes) or not image.startswith(b'\x89PNG\r\n\x1a\n') or len(image)>4_000_000:raise ValueError('검증된 4MB 이하 PNG 시작 프레임이 필요합니다.')
    return dict(prompt=prompt,start_image_url='data:image/png;base64,'+base64.b64encode(image).decode(),duration='10',generate_audio=False,enable_safety_checker=True)


def estimate():
    return dict(provider='fal.ai',model=MODEL,duration=10,generate_audio=False,
                money={'amount':'0.70','currency':'USD'},source=PRICE_SOURCE,
                checked='2026-10-25',expires=time.time()+300,kind='documented-estimate; actual billing unconfirmed',
                automatic_retries=False)


def validate_gate(gate,prep,workspace):
    expected=dict(model=MODEL,workspace_id=workspace,song=prep['song'],shot=prep['shot'],
        image_sha256=prep['source']['sha256'],prompt_sha256=hashlib.sha256(prep['prompt'].encode()).hexdigest(),
        privacy='private',retention_seconds=3600,duration=10,generate_audio=False)
    if any(gate.get(k)!=v for k,v in expected.items()):raise ValueError('승인 대상 모델·작품·입력 해시·비공개 옵션이 일치하지 않습니다.')
    if gate.get('price_money')!=prep['estimate']['money'] or not isinstance(gate.get('price_checked_at'),(int,float)) or not 0<=time.time()-gate['price_checked_at']<=86400:
        raise ValueError('승인된 가격과 최근 확인 시각이 필요합니다.')


class FalKling:
    def __init__(self,*,live_enabled=False,key=None,transport=None,private_reader=None):
        self.live_enabled=live_enabled;self._key=key;self._transport=transport
        self.mode='contract-fake' if transport is not None else 'live-unverified' if live_enabled else 'disconnected'
        self._lifecycle=private_lifecycle_candidate(private_reader) if private_reader is not None else json.loads(json.dumps(LIFECYCLE))

    @classmethod
    def from_environment(cls,*,live_enabled=False):
        # Do not even read the environment until the explicitly approved runtime is enabled.
        if not live_enabled:return cls()
        return cls(live_enabled=True,key=os.environ.get('FAL_KEY'))

    def _request(self,method,url,body=None):
        parts=urlsplit(url)
        if not (url==TOKEN_URL and method=='POST') and (parts.scheme!='https' or parts.netloc!='queue.fal.run' or parts.fragment or parts.query):
            raise ProviderError('untrusted_provider_url')
        headers={'Content-Type':'application/json','X-Fal-No-Retry':'1'}
        if method=='POST' and url==BASE+MODEL:headers['X-Fal-Object-Lifecycle-Preference']=json.dumps(self._lifecycle,separators=(',',':'))
        if self._transport is not None:
            return self._transport(method,url,headers,body)
        if not self.live_enabled or not self._key:raise ProviderError('provider_not_connected')
        headers['Authorization']='Key '+self._key
        request=Request(url,data=json.dumps(body).encode() if body is not None else None,method=method,headers=headers)
        try:
            with build_opener(NoRedirect()).open(request,timeout=30) as response:
                raw=response.read(2_000_001)
                if len(raw)>2_000_000:raise ProviderError('provider_response_too_large',method=='POST')
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            # Never echo upstream body: it can contain input data or credentials.
            code=exc.code;exc.close()
            raise ProviderError('provider_http_'+str(code),method=='POST' and code>=500) from None
        except (URLError,TimeoutError,OSError,ValueError,IncompleteRead):
            raise ProviderError('provider_response_uncertain',method=='POST') from None

    def submit(self,data):
        if set(data)!={'prompt','start_image_url','duration','generate_audio','enable_safety_checker'} or data['duration']!='10' or data['generate_audio'] is not False or data['enable_safety_checker'] is not True:
            raise ValueError('승인된 10초·무음·안전 검사 입력만 지원합니다.')
        value=self._request('POST',BASE+MODEL,data)
        try:
            identifier=str(uuid.UUID(value['request_id']))
            prefix=BASE+'fal-ai/kling-video/requests/'+identifier
            urls={name:value[name] for name in ['status_url','response_url','cancel_url']}
            for name,suffix in [('status_url','/status'),('response_url',''),('cancel_url','/cancel')]:
                if urls[name]!=prefix+suffix:raise ValueError()
        except (KeyError,TypeError,ValueError):raise ProviderError('provider_receipt_uncertain',True) from None
        return dict(request_id=identifier,**urls)

    @staticmethod
    def _url(receipt,name):
        try:
            identifier=str(uuid.UUID(receipt['request_id']))
            suffix={'status_url':'/status','response_url':'','cancel_url':'/cancel'}[name]
            expected=BASE+'fal-ai/kling-video/requests/'+identifier+suffix
            if receipt[name]!=expected:raise ValueError()
            return expected
        except (KeyError,TypeError,ValueError):raise ProviderError('untrusted_provider_receipt') from None

    def status(self,receipt):
        result=self._request('GET',self._url(receipt,'status_url'))
        state=result.get('status')
        if state not in {'IN_QUEUE','IN_PROGRESS','COMPLETED'}:raise ProviderError('unknown_provider_state')
        # COMPLETED means retrieve the result, not generation success or user approval.
        return dict(state=state,result_ready=state=='COMPLETED',approved=False,cost_confirmed=False)

    def result(self,receipt):
        value=self._request('GET',self._url(receipt,'response_url'))
        try:
            video=value['video'];parts=urlsplit(video['url'])
            if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:raise ValueError()
            if parts.hostname!='v3b.fal.media' or parts.port not in {None,443} or parts.fragment:raise ValueError()
        except (KeyError,TypeError,ValueError):raise ProviderError('invalid_provider_result') from None
        return dict(url=video['url'],content_type=video.get('content_type'),approved=False,cost_confirmed=False)

    def cancel(self,receipt):
        self._request('PUT',self._url(receipt,'cancel_url'))
        return dict(cancel_requested=True,refund_confirmed=False)

    @staticmethod
    def read_video(response):
        content_type=response.headers.get('Content-Type','').split(';')[0].strip().lower()
        if content_type not in {'video/mp4','application/octet-stream'}:raise ProviderError('invalid_media_content_type')
        declared=response.headers.get('Content-Length')
        if declared is not None:
            try:length=int(declared)
            except ValueError:raise ProviderError('invalid_media_length') from None
            if length<1 or length>MAX_RESULT_BYTES:raise ProviderError('provider_media_too_large')
        output=io.BytesIO();total=0
        while True:
            chunk=response.read(min(1024*1024,MAX_RESULT_BYTES-total+1))
            if not chunk:break
            total+=len(chunk)
            if total>MAX_RESULT_BYTES:raise ProviderError('provider_media_too_large')
            output.write(chunk)
        if not total or (declared is not None and total!=length):raise ProviderError('truncated_media')
        raw=output.getvalue()
        if len(raw)<12 or raw[4:8]!=b'ftyp':raise ProviderError('invalid_mp4_signature')
        return raw

    def download(self,url):
        # ACL output is v3 only. The API key is never sent to the CDN.
        if not self.live_enabled:raise ProviderError('provider_not_connected')
        p=urlsplit(url)
        if p.scheme!='https' or p.hostname!='v3b.fal.media' or p.port not in {None,443} or p.username or p.password or p.fragment:
            raise ProviderError('untrusted_media_url')
        # One normal expiry refresh on401;403 never triggers refresh/fallback.
        for attempt in range(2):
            try:
                try:value=self._request('POST',TOKEN_URL,{'expiration_seconds':600})
                except ProviderError as exc:
                    if exc.code.startswith('provider_http_'):
                        raise ProviderError('cdn_token_http_'+exc.code.removeprefix('provider_http_')) from None
                    raise
                token=value.get('token')
                if not isinstance(token,str) or not token or any(c in token for c in '\r\n'):raise ProviderError('invalid_cdn_token')
                request=Request(url,headers={'Authorization':'Bearer '+token})
                with build_opener(NoRedirect()).open(request,timeout=30) as response:return self.read_video(response)
            except HTTPError as exc:
                code=exc.code;exc.close()
                if code==401 and attempt==0:continue
                raise ProviderError('provider_media_http_'+str(code)) from None
            except IncompleteRead:raise ProviderError('truncated_media') from None
            except (URLError,TimeoutError,OSError):raise ProviderError('provider_media_download_failed') from None
