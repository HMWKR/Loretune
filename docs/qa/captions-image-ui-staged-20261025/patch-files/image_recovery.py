"""Readiness display + one-use recovery of an existing image job. No activation API.
Configuration/verification/retrieval evidence is supplied by trusted server code only.
Model args and browser flags cannot authorize a provider or mint new access.
"""
import json,time
import action_execution as actions,action_assets,contracts,guided
import runway_provider as runway

PERMISSION_ERRORS={'download_http_401','download_http_403','provider_http_401','provider_http_403'}
POLICY='runway-signed-url-24-48h; local-copy; not-fal-private-1h'

def capability(store,name):
    pipe=store.image_pipeline
    result=dict(state='unconfigured',available=False,mode='disconnected',model=runway.MODEL,
        reason='이미지 연결이 설정되지 않았습니다. 모델 선택만으로 외부 실행되지 않습니다.',
        checks=dict(account=False,configuration=False,integration=False,approval=False),
        policy='Runway 결과 URL: API 조회 후 24–48시간 내 만료 · 서버 파일 삭제 시각·본인 전용 접근 미확인')
    if pipe is None:return result
    adapter=pipe.adapter;v=pipe.verification or {};g=pipe.gate or {}
    result['mode']=adapter.mode
    binding=v.get('workspace')==store.workspace_id and v.get('connection_id')==runway.CONNECTION and v.get('model')==runway.MODEL and v.get('output_policy')==POLICY
    result['checks']=dict(account=binding and v.get('account_verified') is True,
        configuration=binding and v.get('configuration_verified') is True,
        integration=binding and v.get('integration_verified') is True and bool(v.get('evidence_id')) and v.get('expires',0)>time.time(),
        approval=g.get('project')==contracts.project_id(store.workspace_id,name) and g.get('workspace')==store.workspace_id and g.get('expires',0)>time.time() and g.get('live_approved') is True)
    configured=adapter.mode=='live-unverified' and adapter.live_enabled and bool(adapter._key) and bool(adapter.output_hosts)
    result['configured']=configured
    if v.get('blocked'):
        result.update(state='blocked',reason='서버 연결 검증이 차단되었습니다. 설정/권한 확인 전 실행할 수 없습니다.')
    elif configured and all(result['checks'].values()):
        result.update(state='available',available=True,reason='서버에서 확인한 계정·설정·검증 및 승인 범위만 사용 가능합니다. 작업별 입력·비용 승인은 별도입니다.')
    else:result.update(state='unverified',reason='계약 구현 후보입니다. 계정·설정·실제 통합·전송 승인을 확인하기 전 활성화할 수 없습니다.')
    return result

def check(c,store,job,operation):
    if operation not in {'status','collect'}:raise ValueError('기존 상태 조회 또는 결과 수집만 가능합니다.')
    context=job.get('context',{});pipe=store.image_pipeline
    if context.get('output_kind')!='image' or pipe is None:raise ValueError('이미지 복구 연결이 설정되지 않았습니다.')
    p,pid=pipe.project(c,context['song']);b=context.get('action_binding',{})
    if (b.get('workspace'),b.get('project'),b.get('connection_id'))!=(store.workspace_id,pid,runway.CONNECTION):raise ValueError('이미지 작업 귀속이 다릅니다.')
    mapped=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(store.workspace_id,pid,b['action_id'])).fetchone()
    if not mapped or mapped[0]!=job['id']:raise ValueError('기존 작업 연결을 확인하세요.')
    action=actions.get(c,'production_actions',store.workspace_id,pid,b['action_id']);grant=actions.get(c,'execution_grants',store.workspace_id,pid,b['grant_id'])
    if action['hash']!=b['action_hash'] or grant['state']!='active':raise ValueError('원래 작업 승인/입력이 변경되거나 철회되었습니다.')
    # Collection preserves old output even if the shot was edited; current rights still apply.
    action_assets.validate(c,store,p,{'action':action})
    if context['shot'] not in p['shots']:raise ValueError('연결할 샷이 없습니다.')
    receipt=job.get('receipt') or {}
    try:pipe.adapter.identifier(receipt)
    except runway.ProviderError:raise ValueError('확인된 기존 접수번호가 없습니다. 새 생성하지 않습니다.') from None
    if job['mode']!=pipe.adapter.mode:raise ValueError('모의/실제 복구 연결을 혼용할 수 없습니다.')
    v=pipe.verification or {}
    if job['mode']!='contract-fake':
        cap=capability(store,context['song'])
        if not cap.get('configured') or not all(cap['checks'][k] for k in ('account','configuration','integration')) or cap['state']=='blocked':raise ValueError('실제 복구 연결의 계정·설정·통합 검증이 필요합니다.')
    gate=pipe.recovery_approval or {}
    required=dict(job=job['id'],request_id=receipt['request_id'],workspace=store.workspace_id,
        project=pid,connection_id=runway.CONNECTION,operation=operation)
    if any(gate.get(k)!=v for k,v in required.items()) or gate.get('expires',0)<=time.time() or not gate.get('id') or not gate.get('evidence') or gate['id'] in job.get('retrieval_approvals_used',[]):raise ValueError('이 기존 요청에 대한 일회 복구 허가가 필요합니다. 새 생성은 하지 않습니다.')
    if job.get('failure_code') in PERMISSION_ERRORS and (gate.get('resolves_permission') is not True or gate.get('resolved_failure')!=job['failure_code']):raise ValueError('접근 거절 해결 근거 확인 전 같은 요청을 반복하지 않습니다.')
    if operation=='collect':
        if not job.get('result') or job.get('failure_code') in {'download_http_404','download_http_410'}:raise ValueError('결과 URL이 없거나 만료됐습니다. 기존 접수 상태 확인이 먼저 필요합니다.')
        try:pipe.adapter.validate_output_url(job['result']['url'])
        except runway.ProviderError:raise ValueError('승인된 결과 호스트 검증이 필요합니다.') from None
        if gate.get('result_sha256')!=guided.fingerprint(job['result']):raise ValueError('승인한 기존 결과와 다릅니다.')
    if job['state'] not in {'import_blocked','reconciliation_required','cancelled_result','image_recovery_pending'}:raise ValueError('이 상태는 수동 복구 대상이 아닙니다.')
    return gate

def describe(store,job):
    result=dict(can_status=False,can_collect=False,reason='새 생성 없이 기존 요청만 조회·수집합니다.')
    if job['state']=='imported':
        return dict(result,reason='로컬 저장과 Take 등록이 완료되었습니다. 선택과 검토는 별도이며 복구를 다시 실행하지 않습니다.')
    if job['state'] in {'image_recovery_pending','image_recovery_running','downloading'}:
        return dict(result,reason='기존 요청 복구를 처리 중입니다. 새로 제출하지 말고 완료 상태를 기다리세요.')
    for operation in ('status','collect'):
        try:
            with store.connect() as c:check(c,store,job,operation)
            result['can_'+operation]=True
        except (ValueError,KeyError,runway.ProviderError) as exc:
            # Only local, controlled errors; never include URL/key/provider body.
            result['reason']='복구 연결/기존 요청 검증이 필요합니다.' if isinstance(exc,(KeyError,runway.ProviderError)) else str(exc)
    if result['can_status'] or result['can_collect']:result['reason']='서버에서 확인한 이 기존 요청의 일회 복구만 가능합니다.'
    return result

def enqueue(c,store,job,operation):
    if job['state']=='image_recovery_pending':return job
    gate=check(c,store,job,operation)
    job.update(state='image_recovery_pending',recovery_pending=dict(operation=operation,approval_id=gate['id'],gate_hash=guided.fingerprint(gate)),last_error=None)
    store.generation.save(c,job);return job

def execute(pipe,identifier):
    store=pipe.store
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
        if job['state']!='image_recovery_pending':return False
        pending=job['recovery_pending'];gate=check(c,store,job,pending['operation'])
        if guided.fingerprint(gate)!=pending['gate_hash']:raise ValueError('복구 허가가 변경되었습니다.')
        job.setdefault('retrieval_approvals_used',[]).append(gate['id'])
        job.update(state='image_recovery_running');store.generation.save(c,job)
    if pending['operation']=='collect':store.generation.import_result(identifier,pipe.adapter.download,recovery=True)
    else:
        latest=store.generation.poll(identifier,pipe.adapter,recovery=True)
        if latest['state']=='result_ready':
            with store.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
                if latest['state']=='result_ready':
                    latest.update(state='import_blocked',failure_code='collection_requires_approval',last_error='기존 결과 조회 완료. 별도 수집 허가 후 연결하세요.');store.generation.save(c,latest)
    return True
