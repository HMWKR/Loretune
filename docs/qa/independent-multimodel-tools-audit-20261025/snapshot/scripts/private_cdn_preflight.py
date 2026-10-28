"""One approved synthetic private CDN control; no inference, retries or secret persistence."""
import hashlib,json,os,stat,time
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.error import HTTPError
from urllib.parse import urlsplit
from fal_provider import NoRedirect,LIFECYCLE
from live_launcher import parse_key
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/qa/production-scenarios/private-preflight-result.json'
SHA='345156ca8dfe5abcfc54a9382820164fc42de77a32cf67ce9eb49e4dcdfcbcb1'

def main():
    if os.environ.get('LORETUNE_APPROVED_PRIVATE_CONTROL')!='1':raise SystemExit('disabled')
    report={'started':time.time(),'model_calls':0,'maximum_files':1,'retention_seconds':3600,'acl':'private owner only','steps':[],'billing':'No inference requested; storage/read charge unconfirmed','status':'started'}
    with OUT.open('x') as f:json.dump(report,f)
    def save():OUT.write_text(json.dumps(report,indent=2))
    def call(stage,method,url,body=None,headers=None,limit=65536):
        report['steps'].append({'stage':stage,'state':'sending'});save()
        try:
            with build_opener(NoRedirect()).open(Request(url,data=body,headers=headers or {},method=method),timeout=30) as r:
                raw=r.read(limit+1);report['steps'][-1].update(http_status=r.status,state='received',bytes=len(raw));save()
                if len(raw)>limit:raise ValueError('response_limit')
                return raw
        except HTTPError as e:
            report['steps'][-1].update(http_status=e.code,state='denied' if e.code in (401,403) else 'http_error');e.close();save();raise RuntimeError('http_stop') from None
    try:
        raw=(ROOT/'docs/qa/fixtures/kling-live-v1/start-frame.png').read_bytes()
        if len(raw)!=4423 or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('fixture_mismatch')
        report['input_bytes']=len(raw);report['input_sha256']=SHA;save()
        fd=os.open(ROOT/'.env',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size>65536:raise ValueError('env_boundary')
            key=parse_key(f.read(65537).decode(),'FAL_KEY')
        auth={'Authorization':'Key '+key,'Content-Type':'application/json'}
        init=json.loads(call('initiate','POST','https://rest.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3',json.dumps({'file_name':'loretune-private-control.png','content_type':'image/png'}).encode(),dict(auth,**{'X-Fal-Object-Lifecycle-Preference':json.dumps(LIFECYCLE)})))
        for name in ('upload_url','file_url'):
            u=urlsplit(init[name])
            if u.scheme!='https' or u.hostname not in {'v3.fal.media','v3b.fal.media','fal.media'} or u.port not in (None,443) or u.username or u.password or u.fragment:raise ValueError('unexpected_storage_origin')
        if urlsplit(init['file_url']).hostname!='v3b.fal.media':raise ValueError('non_v3_output')
        call('upload','PUT',init['upload_url'],raw,{'Content-Type':'image/png'})
        token=json.loads(call('token','POST','https://rest.fal.ai/storage/auth/token?storage_type=fal-cdn-v3',b'{"expiration_seconds":600}',auth)).get('token')
        if not isinstance(token,str) or not token or any(c in token for c in '\r\n'):raise ValueError('invalid_token')
        got=call('authenticated_read','GET',init['file_url'],headers={'Authorization':'Bearer '+token},limit=4423)
        report['sha256_matches']=hashlib.sha256(got).hexdigest()==SHA
        report['status']='passed' if report['sha256_matches'] else 'hash_mismatch'
        report['anonymous_access']='not tested; limited to one authenticated read'
    except Exception as e:
        report['status']='stopped';report['error_class']=type(e).__name__
        report['failure_code']=str(e) if type(e) is ValueError and str(e) in {'fixture_mismatch','env_boundary','unexpected_storage_origin','non_v3_output','invalid_token','response_limit'} else 'operation_stopped_no_retry'
    report['finished']=time.time();save();print(json.dumps(report))
if __name__=='__main__':main()
