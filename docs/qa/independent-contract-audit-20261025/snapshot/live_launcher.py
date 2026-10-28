"""Explicit, ephemeral live launcher. Never sources shell code or writes secrets."""
import argparse
import json
import os
import re
import stat
import time
import hashlib
from pathlib import Path
from fal_provider import FalKling, MODEL, private_lifecycle_candidate


def validate_approval(gate):
    required={'model','workspace_id','song','shot','image_sha256','prompt_sha256','privacy','retention_seconds','duration','generate_audio','price_money','price_checked_at','maximum_calls','maximum_units','expires'}
    if isinstance(gate,dict) and 'private_reader' in gate:
        required |= {'private_reader','reader_evidence','lifecycle_sha256'}
        policy=private_lifecycle_candidate(gate['private_reader'])
        if not gate.get('reader_evidence') or gate.get('lifecycle_sha256')!=hashlib.sha256(json.dumps(policy,sort_keys=True,separators=(',',':')).encode()).hexdigest():raise ValueError('본인 reader 근거와 정책 해시를 확인하세요.')
    if not isinstance(gate,dict) or set(gate)!=required:raise ValueError('승인 문서 필드를 확인하세요.')
    if gate['model']!=MODEL or gate['privacy']!='private' or gate['retention_seconds']!=3600 or gate['duration']!=10 or gate['generate_audio'] is not False:raise ValueError('승인된 모델·비공개·출력 범위가 아닙니다.')
    if type(gate['maximum_calls']) is not int or gate['maximum_calls']!=1 or type(gate['maximum_units']) is not int or not 700000<=gate['maximum_units']<=1000000:raise ValueError('1회/$1 이하 승인 범위가 필요합니다.')
    if gate['price_money']!={'amount':'0.70','currency':'USD'}:raise ValueError('가격 재확인이 필요합니다.')
    now=time.time()
    if type(gate['expires']) not in (int,float) or not now<gate['expires']<=now+3600:raise ValueError('승인 유효시간은 현재부터 최대1시간입니다.')
    if type(gate['price_checked_at']) not in (int,float) or not 0<=now-gate['price_checked_at']<=86400:raise ValueError('24시간 이내 가격 확인이 필요합니다.')
    for name in ['image_sha256','prompt_sha256']:
        if not isinstance(gate[name],str) or not re.fullmatch('[0-9a-f]{64}',gate[name]):raise ValueError('승인 입력 해시가 필요합니다.')
    for name in ['workspace_id','song','shot']:
        if not isinstance(gate[name],str) or not gate[name].strip():raise ValueError('승인 작품·샷 범위가 필요합니다.')


def parse_key(contents,name):
    if not re.fullmatch('[A-Z][A-Z0-9_]{0,63}',name):raise ValueError('환경변수 이름 형식을 확인하세요.')
    values=[]
    for line in contents.splitlines():
        line=line.strip()
        if line.startswith('export '):line=line[7:].strip()
        if '=' not in line:continue
        left,value=line.split('=',1)
        if left.strip()!=name:continue
        value=value.strip()
        if len(value)>=2 and value[0]==value[-1] and value[0] in '\"\'':value=value[1:-1]
        if not re.fullmatch(r'[A-Za-z0-9_:.-]{8,512}',value):raise ValueError('키 항목은 보간·명령·이스케이프 없는 단일 리터럴이어야 합니다.')
        values.append(value)
    if len(values)!=1:raise ValueError('선택한 키 항목은 정확히 하나여야 합니다.')
    return values[0]


def load_runtime(env_path,gate,*,key_name='FAL_KEY',approved=False):
    if not approved:raise PermissionError('실제 파일 접근·키 주입·외부 호출 승인이 필요합니다.')
    validate_approval(gate)
    # Open once, forbid symlink traversal at the final component, and bound reads.
    fd=os.open(env_path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>65536:raise ValueError('비밀 파일 형식/크기를 확인하세요.')
        raw=stream.read(65537)
        if len(raw)>65536:raise ValueError('비밀 파일 크기를 확인하세요.')
    try:contents=raw.decode('utf-8')
    except UnicodeError:raise ValueError('비밀 파일 인코딩을 확인하세요.') from None
    key=parse_key(contents,key_name)
    return FalKling(live_enabled=True,key=key,private_reader=gate.get('private_reader'))


def main():
    parser=argparse.ArgumentParser(description='승인 완료 후에만 사용하는1회 Kling 검증 런처')
    parser.add_argument('--execute-approved-live',action='store_true')
    parser.add_argument('--approval-file',type=Path)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--key-name',default='FAL_KEY')
    parser.add_argument('--data',type=Path,default=Path(__file__).resolve().parent/'data')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    if not args.execute_approved_live:
        print('비활성: 비밀 파일을 읽거나 서버/외부 요청을 시작하지 않았습니다.');return
    if not args.approval_file or not args.env_file:parser.error('명시적인 승인 문서와 비밀 파일 경로가 필요합니다.')
    try:
        gate=json.loads(args.approval_file.read_text())
        adapter=load_runtime(args.env_file,gate,approved=True,key_name=args.key_name)
        from app import server
        from threading import Thread
        http=server(args.data,args.port,provider_adapter=adapter,generation_approval=gate)
        if http.store.workspace_id!=gate['workspace_id']:
            http.server_close();raise ValueError('승인 작업공간 불일치')
        def worker():
            while True:
                if not http.store.process_next() and not http.store.process_generation():time.sleep(.3)
        Thread(target=worker,daemon=True).start()
        print('승인된 로컬 테스트 서버 시작. 키는 표시/저장하지 않습니다.',flush=True)
        http.serve_forever()
    except Exception:
        # Do not include original exception, file contents, URL query or credential.
        raise SystemExit('실행을 중단했습니다. 승인 문서·파일 형식·포트 상태를 확인하세요.') from None

if __name__=='__main__':main()
