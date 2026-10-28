"""One-use collection/status recovery for existing fal dispatcher jobs.
Shares GenerationQueue; never calls submit or changes an existing asset ACL.
Only trusted runtime evidence can authorize a denied retrieval retry.
"""
import json,time
from urllib.parse import urlsplit
import action_execution as actions,action_assets,contracts,guided
from fal_models import CONNECTION
from fal_provider import ProviderError
PERMISSION_ERRORS={p+str(n) for p in ('download_http_','provider_http_','provider_media_http_','cdn_token_http_') for n in (401,403)}
RECOVERABLE={'import_blocked','reconciliation_required','cancelled_result','image_recovery_pending'}

def permission_failure(job):
 return job.get('retrieval_permission_failure') or (job.get('failure_code') if job.get('failure_code') in PERMISSION_ERRORS else None)

def check(c,store,job,operation):
 if operation not in {'status','collect'}:raise ValueError('기존 상태 조회 또는 결과 수집만 가능합니다.')
 pipe=store.media_dispatch;b=job.get('context',{}).get('action_binding',{})
 if pipe is None or job['context'].get('dispatch')!=CONNECTION:raise ValueError('기존 작업의 모델 연결을 확인하세요.')
 p,pid=pipe.project(c,job['context']['song']);w=store.workspace_id
 if (b.get('workspace'),b.get('project'),b.get('connection_id'))!=(w,pid,CONNECTION):raise ValueError('작업 귀속이 다릅니다.')
 a=actions.get(c,'production_actions',w,pid,b['action_id']);g=actions.get(c,'execution_grants',w,pid,b['grant_id']);ad=pipe.adapter(a)
 row=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,a['id'])).fetchone()
 if not row or row[0]!=job['id'] or a['hash']!=b['action_hash'] or g['state']!='active' or g['hash']!=b['grant_hash']:raise ValueError('기존 작업 승인·연결이 변경되었습니다.')
 if job['mode']!=ad.mode:raise ValueError('시험/실제 연결을 혼용할 수 없습니다.')
 if job['context']['shot'] not in p['shots']:raise ValueError('대상 장면이 없습니다.')
 action_assets.validate(c,store,p,{'action':a})
 try:
  for field in ('status_url','response_url','cancel_url'):ad._url(job.get('receipt') or {},field)
 except ProviderError:raise ValueError('기존 접수번호가 없습니다. 새 생성 없이 접수 확인이 필요합니다.') from None
 gate=pipe.recovery_approvals.get(job['id'],{})
 required=dict(workspace=w,project=pid,connection_id=CONNECTION,model=a['release_id'],job=job['id'],request_id=job['receipt']['request_id'],operation=operation)
 if any(gate.get(k)!=v for k,v in required.items()) or not gate.get('id') or not gate.get('evidence') or gate.get('expires',0)<=time.time() or gate['id'] in job.get('retrieval_approvals_used',[]):raise ValueError('기존 요청의 일회 복구 확인이 필요합니다. 새 생성하지 않습니다.')
 if ad.mode!='contract-fake' and (gate.get('account_verified') is not True or gate.get('integration_verified') is not True or gate.get('retrieval_authorized') is not True or not ad.live_enabled):raise ValueError('기존 모델의 실제 인증·복구 권한 검증이 필요합니다.')
 denied=permission_failure(job)
 if denied and (gate.get('resolves_permission') is not True or gate.get('resolved_failure')!=denied):raise ValueError('접근 거절 해결 근거 확인 전 같은 요청을 반복하지 않습니다.')
 if operation=='collect':
  if not job.get('result') or job.get('failure_code') in {'download_http_404','download_http_410','provider_media_http_404','provider_media_http_410'}:raise ValueError('파일이 없거나 만료됐습니다. 기존 접수 상태 확인이 먼저 필요합니다.')
  url=urlsplit(job['result'].get('url',''))
  if url.scheme!='https' or url.hostname!='v3b.fal.media' or url.port not in (None,443) or url.username or url.password or url.fragment:raise ValueError('승인된 비공개 결과 주소가 아닙니다.')
  if gate.get('result_sha256')!=guided.fingerprint(job['result']):raise ValueError('확인한 기존 결과가 변경되었습니다.')
 if job['state'] not in RECOVERABLE:raise ValueError('지금은 수동 복구 대상이 아닙니다.')
 return gate,ad

def describe(c,store,job):
 result=dict(can_status=False,can_collect=False,reason='기존 요청만 확인하며 새로 생성하지 않습니다.')
 if job['state']=='imported':return dict(result,reason='파일과 Take 등록 완료 · 선택과 승인은 별도입니다.')
 if job['state'] in {'image_recovery_pending','image_recovery_running','downloading'}:return dict(result,reason='기존 결과를 처리 중입니다. 자동 재생성 없음.')
 for op in ('status','collect'):
  try:check(c,store,job,op);result['can_'+op]=True
  except (ValueError,KeyError,ProviderError):pass
 if result['can_status'] or result['can_collect']:result['reason']='확인된 기존 요청의 일회 복구를 진행할 수 있습니다.'
 elif permission_failure(job):result['reason']='접근 권한 해결 근거 확인 대기 · 재시도·재생성 없음.'
 elif not job.get('receipt'):result['reason']='접수번호 확인 전입니다. 중복 생성하지 않습니다.'
 elif job['state'] in RECOVERABLE:result['reason']='기존 모델 연결과 결과 회수 권한 확인이 필요합니다.'
 return result

def enqueue(c,store,job,operation):
 if job['state']=='image_recovery_pending':
  if job['recovery_pending']['operation']!=operation:raise ValueError('이미 다른 복구를 처리 중입니다.')
  return job
 gate,_=check(c,store,job,operation)
 job.update(state='image_recovery_pending',recovery_pending=dict(operation=operation,approval_id=gate['id'],gate_hash=guided.fingerprint(gate)),last_error=None)
 store.generation.save(c,job);return job

def execute(store,identifier):
 with store.connect() as c:
  c.execute('BEGIN IMMEDIATE');job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
  if job['state']!='image_recovery_pending':return False
  pending=job['recovery_pending'];gate,ad=check(c,store,job,pending['operation'])
  if guided.fingerprint(gate)!=pending['gate_hash']:raise ValueError('복구 확인이 변경되었습니다.')
  job.setdefault('retrieval_approvals_used',[]).append(gate['id']);job.update(state='image_recovery_running');store.generation.save(c,job)
 if pending['operation']=='collect':store.generation.import_result(identifier,ad.download,recovery=True)
 else:
  latest=store.generation.poll(identifier,ad,recovery=True)
  if latest['state']=='result_ready':
   with store.connect() as c:
    c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
    if latest['state']=='result_ready':latest.update(state='import_blocked',failure_code='collection_requires_approval',last_error='기존 결과 확인됨. 결과 수집 확인 후 연결하세요.');store.generation.save(c,latest)
 return True
