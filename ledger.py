"""Transactional provider-cost ledger. Integer micro-units; no payment/provider calls."""
import hashlib
import sqlite3
import json
import math
import re
import time
import uuid
from decimal import Decimal


class LedgerError(ValueError):
    def __init__(self, message, status=409):super().__init__(message);self.status=status

class AttemptExists(LedgerError):
    """An attempted transmission is never implicitly claimed again."""

class BudgetExposureBlocked(LedgerError):
    """A new transmission cannot be bounded against the current budget."""


def units(money):
    if not isinstance(money,dict) or set(money)!={'amount','currency'}:
        raise LedgerError('Money의 amount/currency를 확인하세요.',422)
    if not isinstance(money['amount'],str) or len(money['amount'])>40 or not re.fullmatch(r'\d+(\.\d{1,6})?',money['amount']):
        raise LedgerError('금액은 소수점6자리 이내의 양수 문자열이어야 합니다.',422)
    if not isinstance(money['currency'],str) or not re.fullmatch('[A-Z]{3}',money['currency']):
        raise LedgerError('통화는 대문자3자리여야 합니다.',422)
    value=int(Decimal(money['amount'])*1_000_000)
    if value>9_000_000_000_000_000:raise LedgerError('지원 금액 범위를 초과했습니다.',422)
    return value


def money(value,currency):
    return dict(amount=format(Decimal(value)/1_000_000,'f'),currency=currency)


def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS budgets (id TEXT PRIMARY KEY, workspace TEXT, scope TEXT, currency TEXT, ceiling INTEGER, max_jobs INTEGER, retry INTEGER, revision INTEGER, UNIQUE(workspace,scope))')
    c.execute('CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, budget TEXT, amount INTEGER, actual INTEGER, refunded INTEGER, state TEXT, job TEXT, created REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS ledger_events (id TEXT PRIMARY KEY, workspace TEXT, budget TEXT, reservation TEXT, kind TEXT, amount INTEGER, created REAL, note TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS ledger_requests (key TEXT PRIMARY KEY, digest TEXT, result TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS provider_attempts (id TEXT PRIMARY KEY, workspace TEXT NOT NULL, budget TEXT NOT NULL, reservation TEXT NOT NULL, job TEXT NOT NULL, operation TEXT NOT NULL, request_hash TEXT NOT NULL, binding_hash TEXT NOT NULL, owner TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS provider_late_observations (attempt TEXT PRIMARY KEY, request_hash TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL)')
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_observations_no_update BEFORE UPDATE ON provider_late_observations BEGIN SELECT RAISE(ABORT,'late observation is append-only'); END")
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_observations_no_delete BEFORE DELETE ON provider_late_observations BEGIN SELECT RAISE(ABORT,'late observation is append-only'); END")
    c.execute('CREATE TABLE IF NOT EXISTS provider_late_evidence_ids (id INTEGER PRIMARY KEY AUTOINCREMENT, attempt TEXT NOT NULL UNIQUE)')
    c.execute('INSERT INTO provider_late_evidence_ids(attempt) SELECT o.attempt FROM provider_late_observations o WHERE NOT EXISTS (SELECT 1 FROM provider_late_evidence_ids e WHERE e.attempt=o.attempt) ORDER BY o.rowid')
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_evidence_ids_no_update BEFORE UPDATE ON provider_late_evidence_ids BEGIN SELECT RAISE(ABORT,'late evidence id is append-only'); END")
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_evidence_ids_no_delete BEFORE DELETE ON provider_late_evidence_ids BEGIN SELECT RAISE(ABORT,'late evidence id is append-only'); END")
    c.execute('CREATE TABLE IF NOT EXISTS provider_late_reviews (id TEXT PRIMARY KEY, attempt TEXT NOT NULL, workspace TEXT NOT NULL, scope TEXT NOT NULL, idempotency_key TEXT NOT NULL, digest TEXT NOT NULL, prior_revision INTEGER NOT NULL, decision TEXT NOT NULL, created REAL NOT NULL, UNIQUE(workspace,scope,idempotency_key))')
    c.execute('CREATE INDEX IF NOT EXISTS provider_late_reviews_attempt ON provider_late_reviews(workspace,scope,attempt)')
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_reviews_no_update BEFORE UPDATE ON provider_late_reviews BEGIN SELECT RAISE(ABORT,'late review is append-only'); END")
    c.execute("CREATE TRIGGER IF NOT EXISTS provider_late_reviews_no_delete BEFORE DELETE ON provider_late_reviews BEGIN SELECT RAISE(ABORT,'late review is append-only'); END")


def late_observations(c, workspace, scope, after=0, limit=20, identifier=None, detailed=False):
    """Project-scoped evidence projections; never return stored raw payloads."""
    sql='''SELECT e.id,o.payload,o.created,a.operation,a.state,r.state,a.id
        FROM provider_late_observations o
        JOIN provider_late_evidence_ids e ON e.attempt=o.attempt
        JOIN provider_attempts a ON a.id=o.attempt
        JOIN budgets b ON b.id=a.budget AND b.workspace=a.workspace
        JOIN reservations r ON r.id=a.reservation AND r.budget=b.id
        WHERE a.workspace=? AND b.workspace=? AND b.scope=? AND e.id>?'''
    params=[workspace,workspace,scope,after]
    if identifier is not None:
        sql+=' AND e.id=?';params.append(identifier)
    sql+=' ORDER BY e.id LIMIT ?';params.append(limit)
    values=[]
    for number,payload,created,operation,attempt_state,reservation_state,attempt in c.execute(sql,params):
        revision=c.execute('SELECT COUNT(*) FROM provider_late_reviews WHERE attempt=? AND workspace=? AND scope=?',(attempt,workspace,scope)).fetchone()[0]
        latest=c.execute('SELECT decision FROM provider_late_reviews WHERE attempt=? AND workspace=? AND scope=? ORDER BY rowid DESC LIMIT 1',(attempt,workspace,scope)).fetchone()
        item=dict(id=number,kind='generation_receipt' if operation=='generation-submit' else 'chat_usage',
            observedAt=created,reviewState=latest[0] if latest else 'unreviewed',revision=revision,
            attemptState=attempt_state,reservationState=reservation_state)
        if detailed:
            observation=json.loads(payload)
            item['evidenceDigest']=hashlib.sha256(payload.encode()).hexdigest()
            item['evidence']=dict(receiptObserved=bool(observation.get('request_id')))
            if operation=='chat-message':
                item['evidence']['usageStatuses']={name:value['status'] for name,value in observation['usage'].items()}
                if 'model_status' in observation:item['evidence']['modelStatus']=observation['model_status']
                if 'billing_sources' in observation:
                    item['evidence']['usageSources']=observation['billing_sources']
                    for name,source in observation['billing_sources'].items():
                        if source in {'response','unknown'} and item['evidence']['usageStatuses'].get(name)=='valid':
                            item['evidence']['usageStatuses'][name]='unconfirmed'
        values.append(item)
    return values


def review_late_observation(c,workspace,scope,identifier,key,decision,digest,revision):
    if not c.in_transaction:raise LedgerError('검토 기록은 원장 트랜잭션이 필요합니다.')
    items=late_observations(c,workspace,scope,identifier=identifier,detailed=True)
    if not items:raise LedgerError('리소스를 찾을 수 없습니다.',404)
    attempt=c.execute('SELECT attempt FROM provider_late_evidence_ids WHERE id=?',(identifier,)).fetchone()[0]
    old=c.execute('SELECT attempt,digest,prior_revision,decision FROM provider_late_reviews WHERE workspace=? AND scope=? AND idempotency_key=?',(workspace,scope,key)).fetchone()
    if old:
        if old!=(attempt,digest,revision,decision):raise LedgerError('같은 요청 키가 다른 검토에 사용되었습니다.')
        return dict(id=identifier,reviewState=decision,revision=revision+1)
    item=items[0]
    if item['evidenceDigest']!=digest or item['revision']!=revision:raise LedgerError('증거 또는 검토 버전이 변경되었습니다. 다시 조회하세요.',412)
    c.execute('INSERT INTO provider_late_reviews VALUES (?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),attempt,workspace,scope,key,digest,revision,decision,time.time()))
    return dict(id=identifier,reviewState=decision,revision=revision+1)


def attempt_identifier(workspace, scope, reservation, job, operation):
    return hashlib.sha256(json.dumps([workspace,scope,reservation,job,operation],separators=(',',':')).encode()).hexdigest()


def claim_attempt(c, workspace, scope, reservation, job, operation, request_hash, binding_hash, *, enforce_bounded_exposure=True):
    """Claim one request inside the caller's existing BEGIN IMMEDIATE.

    The reservation is the sole money hold. Attempt records do not spend money
    or serialize unrelated work, and never contain request bodies or keys.
    """
    if not c.in_transaction:raise LedgerError('전송 claim은 원장 트랜잭션이 필요합니다.')
    if operation not in {'generation-submit','chat-count','chat-message'}:raise LedgerError('전송 작업을 확인하세요.',422)
    if not all(isinstance(x,str) and re.fullmatch(r'[0-9a-f]{64}',x) for x in (request_hash,binding_hash)):
        raise LedgerError('전송 입력·승인 해시를 확인하세요.',422)
    if not isinstance(job,str) or not job or len(job)>200:raise LedgerError('전송 작업 식별자를 확인하세요.',422)
    b=budget(c,workspace,scope)
    if not b:raise LedgerError('공급자 예산을 먼저 설정하세요.')
    row=c.execute('SELECT job,state FROM reservations WHERE id=? AND budget=?',(reservation,b['id'])).fetchone()
    if not row or row[0]!=job or row[1]!='reserved':raise LedgerError('전송 예약과 작업의 연결을 확인하세요.')
    identifier=attempt_identifier(workspace,scope,reservation,job,operation)
    # A prior claim is a possible transmission even if a separate budget guard
    # would now block a fresh request. Never classify it as unsubmitted.
    if c.execute('SELECT 1 FROM provider_attempts WHERE id=?',(identifier,)).fetchone():
        raise AttemptExists('기존 전송 시도를 확인하세요. 자동 재전송하지 않습니다.')
    if enforce_bounded_exposure:require_bounded_exposure(c,workspace,scope)
    owner=uuid.uuid4().hex;now=time.time()
    try:
        c.execute('INSERT INTO provider_attempts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(identifier,workspace,b['id'],reservation,job,operation,request_hash,binding_hash,owner,'sending',now,now))
    except sqlite3.IntegrityError as exc:raise AttemptExists('기존 전송 시도를 확인하세요. 자동 재전송하지 않습니다.') from exc
    return identifier,owner


def finish_attempt(c, identifier, owner, state):
    """Fence stale workers; not_sent requires trusted proof before transport."""
    if not c.in_transaction:raise LedgerError('전송 결과는 원장 트랜잭션이 필요합니다.')
    if state not in {'observed','unknown','not_sent'}:raise LedgerError('전송 결과 상태를 확인하세요.',422)
    changed=c.execute("UPDATE provider_attempts SET state=?,updated=? WHERE id=? AND owner=? AND state='sending'",(state,time.time(),identifier,owner)).rowcount
    if changed!=1:raise LedgerError('전송 시도 소유권 또는 상태가 변경됐습니다.')


def recover_attempt(c, identifier):
    """Record interruption without reopening the claim or repeating a send."""
    if not c.in_transaction:raise LedgerError('복구는 원장 트랜잭션이 필요합니다.')
    c.execute("UPDATE provider_attempts SET state='unknown',updated=? WHERE id=? AND state='sending'",(time.time(),identifier))


def record_late_observation(c, identifier, owner, request_hash, payload):
    """Append only bounded evidence for the original fenced sender; never settle."""
    if not c.in_transaction:raise LedgerError('늦은 관측은 원장 트랜잭션이 필요합니다.')
    row=c.execute('SELECT owner,request_hash,operation,state FROM provider_attempts WHERE id=?',(identifier,)).fetchone()
    if not row or row[0]!=owner or row[1]!=request_hash or row[3]!='unknown':raise LedgerError('늦은 관측의 전송 소유권을 확인하세요.')
    if not isinstance(payload,dict):raise LedgerError('늦은 관측 형식을 확인하세요.',422)
    if row[2]=='generation-submit':
        if set(payload)!={'request_id'} or not isinstance(payload['request_id'],str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',payload['request_id']):
            raise LedgerError('공급자 접수번호를 확인하세요.',422)
    elif row[2]=='chat-message':
        if set(payload)-{'request_id','usage','model_status','billing_sources'} or 'usage' not in payload:raise LedgerError('사용량 관측 형식을 확인하세요.',422)
        if 'model_status' in payload and (type(payload['model_status']) is not str or payload['model_status'] not in {'match','mismatch','missing','invalid','unknown'}):raise LedgerError('모델 관측 상태를 확인하세요.',422)
        if 'billing_sources' in payload:
            sources=payload['billing_sources']
            if not isinstance(sources,dict) or set(sources)!={'service_tier','speed','inference_geo','server_tool_use'} or any(type(v) is not str or v not in {'usage','response','both','absent','unknown'} for v in sources.values()):raise LedgerError('사용량 관측 출처를 확인하세요.',422)
        rid=payload.get('request_id')
        if rid is not None and (not isinstance(rid,str) or not re.fullmatch(r'req_[A-Za-z0-9_-]{1,195}',rid)):raise LedgerError('요청 식별자를 확인하세요.',422)
        usage=payload['usage'];fields={'input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens','service_tier'}
        extra={'speed','inference_geo','server_tool_use','cache_creation','output_tokens_details','unknown_usage_dimension'}
        if not isinstance(usage,dict) or not fields<=set(usage) or set(usage)-fields-extra:raise LedgerError('사용량 관측 필드를 확인하세요.',422)
        for name,value in usage.items():
            if not isinstance(value,dict) or set(value)-{'status','value'}:raise LedgerError('사용량 관측 값을 확인하세요.',422)
            status=value.get('status');item=value.get('value')
            if not isinstance(status,str):raise LedgerError('사용량 관측 상태를 확인하세요.',422)
            if name=='service_tier':
                valid=status=='valid' and isinstance(item,str) and item in {'default','standard','priority','batch','fast','flex','auto'}
                missing=status in {'absent','unsupported'} and set(value)=={'status'}
            elif name in {'speed','inference_geo'}:
                valid=status=='valid' and isinstance(item,str) and item in ({'standard','fast'} if name=='speed' else {'global','us'})
                missing=status=='unsupported' and set(value)=={'status'}
            elif name in extra:
                valid=status=='valid' and set(value)=={'status'} and name!='unknown_usage_dimension'
                missing=status=='unsupported' and set(value)=={'status'}
            else:
                valid=status=='valid' and isinstance(item,str) and bool(re.fullmatch(r'0|[1-9][0-9]{0,255}',item))
                missing=status in {'absent','invalid','too_large'} and set(value)=={'status'}
            if not (valid or missing):raise LedgerError('사용량 관측 상태를 확인하세요.',422)
    else:raise LedgerError('이 전송은 늦은 사용량 관측을 지원하지 않습니다.',422)
    encoded=json.dumps(payload,sort_keys=True,separators=(',',':'))
    if len(encoded)>2048:raise LedgerError('늦은 관측 크기를 확인하세요.',422)
    old=c.execute('SELECT request_hash,payload FROM provider_late_observations WHERE attempt=?',(identifier,)).fetchone()
    if old:
        if old!=(request_hash,encoded):raise LedgerError('기존 늦은 관측과 충돌합니다.')
        return
    c.execute('INSERT INTO provider_late_observations VALUES (?,?,?,?)',(identifier,request_hash,encoded,time.time()))
    c.execute('INSERT INTO provider_late_evidence_ids(attempt) VALUES (?)',(identifier,))


def totals(c,identifier):
    rows=c.execute('SELECT amount,actual,refunded,state FROM reservations WHERE budget=?',(identifier,)).fetchall()
    held=sum(r[0] for r in rows if r[3] in {'reserved','uncertain'})
    # An observed usage estimate consumes budget but is not a reconciled charge.
    spent=sum((r[1] or 0)-r[2] for r in rows if r[3] in {'settled','disputed','estimated','estimated_disputed'})
    active=sum(r[3] in {'reserved','uncertain'} for r in rows)
    return held,spent,active


def require_bounded_exposure(c,workspace,scope):
    """Check a paid admission or claim inside its caller's write transaction.

    Unknown costs may exceed their original hold. Until there is verified
    provider-specific evidence of a reliable bound, hold the affected budget.
    Ordinary reserved/sending work remains eligible for parallel processing.
    """
    if not c.in_transaction:raise LedgerError('예산 확인은 원장 트랜잭션이 필요합니다.')
    row=c.execute('SELECT id,ceiling FROM budgets WHERE workspace=? AND scope=?',(workspace,scope)).fetchone()
    if not row:raise LedgerError('공급자 예산을 먼저 설정하세요.',422)
    held,spent,_=totals(c,row[0])
    if held+spent>row[1]:raise BudgetExposureBlocked('예산 초과 상태입니다. 비용을 확인한 뒤 새 작업을 진행하세요.')
    if c.execute("SELECT 1 FROM reservations WHERE budget=? AND state='uncertain' LIMIT 1",(row[0],)).fetchone():
        raise BudgetExposureBlocked('미확정 비용을 먼저 대사해야 새 전송을 진행할 수 있습니다.')
    if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='general_chat_turns'").fetchone():
        rows=c.execute("""SELECT t.id,t.project,t.body,r.id FROM general_chat_turns t
            JOIN reservations r ON r.job=t.id
            WHERE r.budget=? AND r.state='reserved'""",(row[0],)).fetchall()
        for identifier,project,body,reservation in rows:
            turn=json.loads(body);binding=turn.get('binding',{});mode=binding.get('transport',{}).get('mode')
            prefix='project:' if mode=='anthropic-live' else 'rehearsal-live:project:' if mode=='contract-live-test' else 'rehearsal:project:'
            if (turn.get('id')==identifier and turn.get('reservation')==reservation and
                binding.get('workspace')==workspace and binding.get('project')==project and scope==prefix+project and
                turn.get('status')=='outcome_unknown' and turn.get('journal_failure')=='update_failed'):
                raise BudgetExposureBlocked('미확정 원장 기록을 먼저 확인해야 새 전송을 진행할 수 있습니다.')


def budget(c,workspace,scope):
    row=c.execute('SELECT id,currency,ceiling,max_jobs,retry,revision FROM budgets WHERE workspace=? AND scope=?',(workspace,scope)).fetchone()
    if not row:return None
    held,spent,active=totals(c,row[0])
    estimated=sum((r[0] or 0) for r in c.execute("SELECT actual FROM reservations WHERE budget=? AND state IN ('estimated','estimated_disputed')",(row[0],)))
    uncertain=c.execute("SELECT count(*) FROM reservations WHERE budget=? AND state='uncertain'",(row[0],)).fetchone()[0]
    return dict(id=row[0],revision=row[5],state='active',data=dict(scope=scope,limit=money(row[2],row[1]),
        reserved=money(held,row[1]),netConfirmed=money(spent-estimated,row[1]),netEstimated=money(estimated,row[1]),available=money(max(0,row[2]-held-spent),row[1]),overrun=money(max(0,held+spent-row[2]),row[1]),
        maxConcurrentJobs=row[3],allowAutomaticRetries=bool(row[4]),activeReservations=active,uncertainReservations=uncertain,
        costScope='provider-only; local compute unmetered'))


def patch_budget(c,workspace,scope,data,expected):
    value=units(data['limit']);current=budget(c,workspace,scope)
    if expected!=(current['revision'] if current else 0):raise LedgerError('예산 버전이 변경되었습니다.',412)
    if type(data['maxConcurrentJobs']) is not int or not 1<=data['maxConcurrentJobs']<=100 or type(data['allowAutomaticRetries']) is not bool:
        raise LedgerError('동시 작업 수와 재시도 설정을 확인하세요.',422)
    identifier=current['id'] if current else str(uuid.uuid4())
    held,spent,_=totals(c,identifier)
    if value<held+spent:raise LedgerError('예약·확정 사용액보다 예산을 낮출 수 없습니다.')
    if current and data['limit']['currency']!=current['data']['limit']['currency']:
        raise LedgerError('기존 예산의 통화는 변경할 수 없습니다.')
    c.execute('INSERT INTO budgets VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET ceiling=excluded.ceiling,max_jobs=excluded.max_jobs,retry=excluded.retry,revision=excluded.revision',
              (identifier,workspace,scope,data['limit']['currency'],value,data['maxConcurrentJobs'],int(data['allowAutomaticRetries']),expected+1))
    event(c,workspace,identifier,None,'budget_changed',value,'금액 설정은 실제 지출 또는 외부 전송 승인이 아님')
    return budget(c,workspace,scope)


def event(c,workspace,budget_id,reservation,kind,amount,note):
    c.execute('INSERT INTO ledger_events VALUES (?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),workspace,budget_id,reservation,kind,amount,time.time(),note))


def command(c,workspace,scope,kind,data,key):
    """Caller owns BEGIN IMMEDIATE. A replay is scoped by workspace and operation."""
    identity=f'{workspace}:{kind}:{key}'
    digest=hashlib.sha256(json.dumps(dict(scope=scope,data=data),sort_keys=True).encode()).hexdigest()
    prior=c.execute('SELECT digest,result FROM ledger_requests WHERE key=?',(identity,)).fetchone()
    if prior:
        if prior[0]!=digest:raise LedgerError('같은 멱등 키의 입력이 다릅니다.')
        return json.loads(prior[1])
    b=budget(c,workspace,scope)
    if not b:raise LedgerError('예산을 먼저 설정하세요.',422)
    if kind=='reserve':
        amount=units(data['money'])
        if data['money']['currency']!=b['data']['limit']['currency']:raise LedgerError('통화가 다릅니다.',422)
        if data['budget_revision']!=b['revision']:raise LedgerError('오래된 예산/견적입니다.')
        expiry=data.get('expires')
        if type(expiry) not in (int,float) or not math.isfinite(expiry):raise LedgerError('견적 만료 시각을 확인하세요.',422)
        if expiry<=time.time():raise LedgerError('견적이 만료됐습니다.')
        held,spent,active=totals(c,b['id'])
        if amount>units(b['data']['limit'])-held-spent:raise LedgerError('남은 예산을 초과합니다.')
        if active>=b['data']['maxConcurrentJobs']:raise LedgerError('동시 작업 한도입니다.',429)
        identifier=str(uuid.uuid4())
        c.execute('INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?)',(identifier,b['id'],amount,None,0,'reserved',data['job'],time.time()))
        event(c,workspace,b['id'],identifier,'reserved',amount,'요청액 예약; 실제 차감 아님')
    else:
        identifier=data['reservation']
        row=c.execute('SELECT amount,actual,refunded,state FROM reservations WHERE id=? AND budget=?',(identifier,b['id'])).fetchone()
        if not row:raise LedgerError('예약을 찾을 수 없습니다.',404)
        reserved,actual,refunded,state=row
        if kind=='uncertain':
            if state!='reserved':raise LedgerError('예약 상태에서만 미확정 전환 가능합니다.')
            c.execute("UPDATE reservations SET state='uncertain' WHERE id=?",(identifier,))
            event(c,workspace,b['id'],identifier,'uncertain',reserved,'접수/과금 미확정: 예약 유지, 재발행 금지')
        elif kind=='release':
            if state!='reserved':raise LedgerError('미확정·정산된 예약은 취소만으로 해제할 수 없습니다.')
            c.execute("UPDATE reservations SET state='cancelled' WHERE id=?",(identifier,))
            event(c,workspace,b['id'],identifier,'released',reserved,'미전송 예약 해제; 환불 아님')
        elif kind in {'estimate','settle'}:
            allowed={'reserved','uncertain','cancelled'} if kind=='estimate' else {'reserved','uncertain','cancelled','estimated','estimated_disputed'}
            if state not in allowed:raise LedgerError('이미 정산된 예약입니다.')
            actual=units(data['money'])
            if data['money']['currency']!=b['data']['limit']['currency']:raise LedgerError('통화가 다릅니다.',422)
            disputed=actual>reserved or state=='cancelled'
            next_state=('estimated_disputed' if disputed else 'estimated') if kind=='estimate' else ('disputed' if disputed else 'settled')
            c.execute('UPDATE reservations SET actual=?,state=? WHERE id=?',(actual,next_state,identifier))
            if kind=='estimate':event(c,workspace,b['id'],identifier,'usage_estimated',actual,'사용량 기반 추정; 실제 청구 확인 아님')
            else:event(c,workspace,b['id'],identifier,'late_settlement' if state=='cancelled' else 'settled',actual,'확인액 기록; 취소 뒤 도착/초과액은 disputed, 작업 재개 없음')
        elif kind=='refund':
            if state not in {'settled','disputed'}:raise LedgerError('확정 차감만 환급 기록할 수 있습니다.')
            amount=units(data['money'])
            if data['money']['currency']!=b['data']['limit']['currency'] or amount>actual-refunded:raise LedgerError('환급 금액/통화를 확인하세요.',422)
            c.execute('UPDATE reservations SET refunded=refunded+? WHERE id=?',(amount,identifier))
            event(c,workspace,b['id'],identifier,'refunded',amount,'확인된 환급 기록; 취소와 구분')
        else:raise LedgerError('지원하지 않는 원장 명령입니다.',422)
    result=dict(reservation=identifier,budget=budget(c,workspace,scope))
    c.execute('INSERT INTO ledger_requests VALUES (?,?,?)',(identity,digest,json.dumps(result)))
    return result
