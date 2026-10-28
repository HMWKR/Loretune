"""Local-only API compatibility subset. This does not implement organization identity."""
import re
import uuid
import datetime
import ledger
import json
import hashlib
import time
from urllib.parse import urlsplit, parse_qs


def project_id(workspace, name):
    return str(uuid.uuid5(uuid.UUID(workspace),name))


def version_id(workspace, name, version):
    return str(uuid.uuid5(uuid.UUID(project_id(workspace,name)),str(version)))


def error(status, code, message):
    return status,dict(code=code,message=message,requestId=str(uuid.uuid4()),retryable=False)


def read(store, path, authorized, permissions=None):
    if not authorized:return error(401,'unauthenticated','유효한 로컬 세션 Bearer 토큰이 필요합니다.')
    parsed=urlsplit(path)
    billing=re.fullmatch(r'/v1/workspaces/([^/]+)/billing/ledger',parsed.path)
    if billing:
        if permissions is not None and 'billing.read' not in permissions:return error(403,'forbidden','billing.read 권한이 필요합니다.')
        if billing[1]!=store.workspace_id:return error(404,'not_found','리소스를 찾을 수 없습니다.')
        query=parse_qs(parsed.query,keep_blank_values=True)
        try:
            if set(query)-{'limit','cursor'} or any(len(v)!=1 for v in query.values()):raise ValueError()
            limit=int(query.get('limit',['50'])[0]);offset=int(query.get('cursor',['0'])[0])
            if not 1<=limit<=200 or offset<0:raise ValueError()
        except ValueError:return error(400,'invalid_query','페이지 매개변수를 확인하세요.')
        with store.connect() as c:
            rows=c.execute('SELECT id,reservation,kind,amount,created,note,budget FROM ledger_events WHERE workspace=? ORDER BY rowid LIMIT ? OFFSET ?',(store.workspace_id,limit+1,offset)).fetchall()
            items=[]
            for r in rows[:limit]:
                currency=c.execute('SELECT currency FROM budgets WHERE id=?',(r[6],)).fetchone()[0]
                items.append(dict(id=r[0],revision=1,state=r[2],createdAt=datetime.datetime.fromtimestamp(r[4],datetime.timezone.utc).isoformat(),data=dict(reservationId=r[1],amount=ledger.money(r[3],currency),note=r[5],budgetId=r[6])))
        return 200,dict(items=items,nextCursor=str(offset+limit) if len(rows)>limit else None)
    match=re.fullmatch(r'/v1/workspaces/([^/]+)/(jobs|projects)/([^/]+)(/(?:versions|events))?',parsed.path)
    if not match:return error(404,'not_found','지원하지 않거나 접근할 수 없는 리소스입니다.')
    workspace,kind,identifier,suffix=match.groups()
    permission='jobs.read' if kind=='jobs' else 'projects.read'
    if permissions is not None and permission not in permissions:return error(403,'forbidden',permission+' 권한이 필요합니다.')
    try:workspace=str(uuid.UUID(workspace));identifier=str(uuid.UUID(identifier))
    except ValueError:return error(400,'invalid_id','경로 ID는 UUID여야 합니다.')
    if workspace!=store.workspace_id:return error(404,'not_found','리소스를 찾을 수 없습니다.')
    state=store.state()
    if kind=='jobs' and suffix in {None,'/events'}:
        if parsed.query:return error(400,'invalid_query','작업 조회는 쿼리 매개변수를 받지 않습니다.')
        job=next((j for j in state['jobs'] if str(uuid.UUID(j['id']))==identifier),None)
        if not job:return error(404,'not_found','리소스를 찾을 수 없습니다.')
        mapping={'completed':'succeeded','interrupted':'reconciliation_required'}
        value=dict(id=identifier,kind='local_render',state=mapping.get(job['status'],job['status']),
                   stage=job['status'],progress=job['progress']/100,costStatus='pending',
                   attempts=1 if job.get('started') else 0,revision=job.get('revision',1))
        if job.get('cancel_requested') and job['status']=='running':value['state']='cancel_requested'
        # Local compute is unmetered: do not claim confirmed total cost.
        if job.get('error'):
            value['failure']=error(422,'render_failed',job['error'])[1]
        else:value['failure']=None
        return 200,value
    if kind=='projects' and suffix=='/versions':
        name=next((n for n in state['projects'] if project_id(workspace,n)==identifier),None)
        if name is None:return error(404,'not_found','리소스를 찾을 수 없습니다.')
        query=parse_qs(parsed.query,keep_blank_values=True)
        if set(query)-{'limit','cursor'} or any(len(v)!=1 for v in query.values()):
            return error(400,'invalid_query','페이지 매개변수를 확인하세요.')
        try:
            limit=int(query.get('limit',['50'])[0]);offset=int(query.get('cursor',['0'])[0])
            if not 1<=limit<=200 or offset<0:raise ValueError()
        except ValueError:return error(400,'invalid_query','limit은 1~200, cursor는 반환된 페이지 커서여야 합니다.')
        versions=state['projects'][name]['timeline_versions']
        if offset>len(versions):return error(400,'invalid_cursor','페이지 커서가 범위를 벗어났습니다.')
        items=[dict(id=version_id(workspace,name,v['id']),revision=v['id'],
                    state='approved' if v.get('approval') else 'draft',data=v)
               for v in versions[offset:offset+limit]]
        return 200,dict(items=items,nextCursor=str(offset+limit) if offset+limit<len(versions) else None)
    return error(404,'not_found','지원하지 않거나 접근할 수 없는 리소스입니다.')


def patch_budget(store,path,body,if_match,authorized,permissions=None):
    if not authorized:return error(401,'unauthenticated','유효한 로컬 세션 Bearer 토큰이 필요합니다.')
    if permissions is not None and 'billing.manage' not in permissions:return error(403,'forbidden','billing.manage 권한이 필요합니다.')
    match=re.fullmatch(r'/v1/workspaces/([^/]+)/billing/budgets',path)
    if not match or match[1]!=store.workspace_id:return error(404,'not_found','리소스를 찾을 수 없습니다.')
    allowed={'period','projectId','limit','maxConcurrentJobs','allowAutomaticRetries'}
    if not isinstance(body,dict) or set(body)-allowed or not {'period','limit','maxConcurrentJobs','allowAutomaticRetries'}<=set(body):return error(400,'invalid_body','BudgetPatch 필드를 확인하세요.')
    if body['period']=='month' and 'projectId' not in body:scope='month:'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m')
    elif body['period']=='project':
        if not isinstance(body.get('projectId'),str):return error(400,'invalid_project','projectId는 UUID 문자열이어야 합니다.')
        ids={project_id(store.workspace_id,n) for n in store.state()['projects']}
        if body.get('projectId') not in ids:return error(404,'not_found','프로젝트를 찾을 수 없습니다.')
        scope='project:'+body['projectId']
    else:return error(422,'unsupported_scope','month 또는 project 예산 범위를 확인하세요.')
    if not if_match or not re.fullmatch(r'"\d+"',if_match):return error(400,'missing_precondition','If-Match에 읽은 예산 revision을 따옴표로 전달하세요. 신규는 "0"입니다.')
    try:
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            result=ledger.patch_budget(c,store.workspace_id,scope,body,int(if_match.strip('"')))
        return 200,result
    except ledger.LedgerError as exc:return error(exc.status,'budget_conflict' if exc.status in {409,412} else 'invalid_budget',str(exc))


def cancel_job(store,path,body,key,authorized,permissions=None):
    if not authorized:return error(401,'unauthenticated','유효한 로컬 세션 Bearer 토큰이 필요합니다.')
    if permissions is not None and 'jobs.cancel' not in permissions:return error(403,'forbidden','jobs.cancel 권한이 필요합니다.')
    match=re.fullmatch(r'/v1/workspaces/([^/]+)/jobs/([^/]+)/cancel',path)
    if not match or match[1]!=store.workspace_id:return error(404,'not_found','리소스를 찾을 수 없습니다.')
    try:identifier=uuid.UUID(match[2]).hex
    except ValueError:return error(400,'invalid_id','jobId는 UUID여야 합니다.')
    if not isinstance(body,dict) or set(body)!={'reason'} or not isinstance(body['reason'],str) or not 1<=len(body['reason'].strip())<=1000:
        return error(400,'invalid_body','CancelCreate.reason을1~1000자로 입력하세요.')
    if not key or not 16<=len(key)<=128:return error(400,'invalid_idempotency_key','Idempotency-Key는16~128자여야 합니다.')
    scoped='v1:'+store.workspace_id+':cancelJob:'+key
    digest=hashlib.sha256(json.dumps(dict(job=identifier,body=body),sort_keys=True).encode()).hexdigest()
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        old=c.execute('SELECT digest,result FROM requests WHERE id=?',(scoped,)).fetchone()
        if old:
            if old[0]!=digest:return error(409,'idempotency_conflict','같은 키에 다른 입력을 보낼 수 없습니다.')
            return 202,json.loads(old[1])
        row=c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()
        if not row:return error(404,'not_found','리소스를 찾을 수 없습니다.')
        job=json.loads(row[0])
        if job['status'] not in {'queued','running'}:return error(409,'terminal_job','종료된 작업입니다. 자동 재실행하거나 환불하지 않습니다.')
        job.update(cancel_requested=True,revision=job.get('revision',1)+1)
        job.setdefault('cancellation_requests',[]).append(dict(reason=body['reason'],at=time.time()))
        if job['status']=='queued':job['status']='cancelled'
        c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),identifier))
        canonical=str(uuid.UUID(identifier));base=f'/v1/workspaces/{store.workspace_id}/jobs/{canonical}'
        result=dict(jobId=canonical,state='cancelled' if job['status']=='cancelled' else 'cancel_requested',reservationId=None,statusUrl=base,eventsUrl=base+'/events')
        c.execute('INSERT INTO requests VALUES (?,?,?)',(scoped,digest,json.dumps(result)))
        return 202,result
