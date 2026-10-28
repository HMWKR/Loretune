"""Transactional provider-cost ledger. Integer micro-units; no payment/provider calls."""
import hashlib
import json
import math
import re
import time
import uuid
from decimal import Decimal


class LedgerError(ValueError):
    def __init__(self, message, status=409):super().__init__(message);self.status=status


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


def totals(c,identifier):
    rows=c.execute('SELECT amount,actual,refunded,state FROM reservations WHERE budget=?',(identifier,)).fetchall()
    held=sum(r[0] for r in rows if r[3] in {'reserved','uncertain'})
    spent=sum((r[1] or 0)-r[2] for r in rows if r[3] in {'settled','disputed'})
    active=sum(r[3] in {'reserved','uncertain'} for r in rows)
    return held,spent,active


def budget(c,workspace,scope):
    row=c.execute('SELECT id,currency,ceiling,max_jobs,retry,revision FROM budgets WHERE workspace=? AND scope=?',(workspace,scope)).fetchone()
    if not row:return None
    held,spent,active=totals(c,row[0])
    return dict(id=row[0],revision=row[5],state='active',data=dict(scope=scope,limit=money(row[2],row[1]),
        reserved=money(held,row[1]),netConfirmed=money(spent,row[1]),available=money(max(0,row[2]-held-spent),row[1]),overrun=money(max(0,held+spent-row[2]),row[1]),
        maxConcurrentJobs=row[3],allowAutomaticRetries=bool(row[4]),activeReservations=active,
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
        elif kind=='settle':
            if state not in {'reserved','uncertain','cancelled'}:raise LedgerError('이미 정산된 예약입니다.')
            actual=units(data['money'])
            if data['money']['currency']!=b['data']['limit']['currency']:raise LedgerError('통화가 다릅니다.',422)
            c.execute('UPDATE reservations SET actual=?,state=? WHERE id=?',(actual,'disputed' if actual>reserved or state=='cancelled' else 'settled',identifier))
            event(c,workspace,b['id'],identifier,'late_settlement' if state=='cancelled' else 'settled',actual,'확인액 기록; 취소 뒤 도착/초과액은 disputed, 작업 재개 없음')
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
