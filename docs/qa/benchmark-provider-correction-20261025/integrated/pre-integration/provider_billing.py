"""Recorded provider evidence -> local ledger. No fetching, credentials or invoice claims.
Only trusted server reconciliation code calls this module; no model/public write tool.
"""
from decimal import Decimal,InvalidOperation,ROUND_CEILING
import hashlib,json,time
import ledger
from generation_queue import GenerationQueue

def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS provider_cost_observations (workspace TEXT, job TEXT, digest TEXT, body TEXT, PRIMARY KEY(workspace,job,digest))')

def nonnegative(value):
    if type(value) not in (int,float,str):raise ValueError('invalid provider amount')
    try:n=Decimal(str(value))
    except InvalidOperation:raise ValueError('invalid provider amount') from None
    if not n.is_finite() or n<0 or n>Decimal('9000000000'):raise ValueError('invalid provider amount')
    return n

def normalize(source,record,job):
    rid=(job.get('receipt') or {}).get('request_id')
    if not rid or record.get('request_id')!=rid:raise ValueError('billing request ownership mismatch')
    if source=='fal-billed':
        if job['quote']['provider']!='fal.ai' or record.get('endpoint_id')!=job['quote']['model']:raise ValueError('billing model mismatch')
        total=nonnegative(record['cost_total']);sub=nonnegative(record['cost_subtotal']);discount=nonnegative(record['cost_discount'])
        nano=record['cost_estimate_nano_usd']
        if type(nano) is not int or nano<0 or Decimal(nano)/1_000_000_000!=total or sub-discount!=total:raise ValueError('inconsistent billing amounts')
        # Local ledger precision is micro-USD: round upward conservatively; preserve exact nano evidence.
        micro=int((total*1_000_000).to_integral_value(rounding=ROUND_CEILING))
        return dict(kind='provider_reported_usd',
            exact_nano_usd=nano,ledger_money=ledger.money(micro,'USD'),rounding_nano_usd=micro*1000-nano,
            quantity=str(nonnegative(record['quantity'])) if record.get('quantity') is not None else None,
            unit=record.get('unit') if record.get('unit') in {'image','second','megapixel','video'} else None)
    if source=='runway-task':
        if job['quote']['provider']!='runway':raise ValueError('billing provider mismatch')
        terminal=record.get('provider_state') in {'SUCCEEDED','FAILED','CANCELLED'}
        value=record.get('credits') if terminal else record.get('estimated_credits')
        if value is None:return dict(kind='unknown')
        credit=nonnegative(value)
        if terminal and type(value) is not int:raise ValueError('terminal credits must be integer')
        # Credits paid at an account's historical purchase rate/tax are NOT a USD invoice.
        return dict(kind='provider_reported_credits' if terminal else 'estimated',credits=str(credit),
            nominal_usd=str(credit*Decimal('0.01')),invoice_confirmed=False)
    raise ValueError('unsupported cost source')

def reconcile(store,identifier,source,record,*,evidence_class):
    if evidence_class not in {'fixture','recorded-provider','authenticated-provider'}:raise ValueError('trusted evidence class required')
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE');initialize(c)
        row=c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()
        if not row:raise ValueError('unknown local job')
        job=json.loads(row[0]);binding=job.get('context',{}).get('action_binding')
        if binding and binding.get('workspace')!=store.workspace_id:raise ValueError('cross-workspace job')
        r=c.execute('SELECT r.state,r.actual,b.workspace,b.scope FROM reservations r JOIN budgets b ON b.id=r.budget WHERE r.id=? AND r.job=?',(job['reservation'],job['id'])).fetchone()
        if not r or (r[2],r[3])!=(store.workspace_id,job['scope']):raise ValueError('reservation ownership mismatch')
        fake=job.get('mode')=='contract-fake'
        if fake!=(evidence_class=='fixture'):raise ValueError('fixture/live billing evidence cannot cross')
        normalized=normalize(source,record,job)
        clean=dict(source=source,request_id=job['receipt']['request_id'],model=job['quote']['model'],
            evidence_class=evidence_class,**normalized)
        digest=hashlib.sha256(json.dumps(clean,sort_keys=True).encode()).hexdigest()
        prior=c.execute('SELECT body FROM provider_cost_observations WHERE workspace=? AND job=? AND digest=?',(store.workspace_id,identifier,digest)).fetchone()
        if prior:return json.loads(prior[0])
        clean.update(digest=digest,observed_at=time.time(),invoice_confirmed=False)
        if normalized['kind']=='provider_reported_usd':
            desired=ledger.units(normalized['ledger_money'])
            if r[0] in {'settled','disputed'}:
                # Timestamp is request time, not revision time. Changed records cannot order refunds safely.
                if r[1]!=desired:clean['reconciliation']='conflicting_record_requires_review'
                else:clean['reconciliation']='matched_existing_settlement'
            else:
                ledger.command(c,store.workspace_id,job['scope'],'settle',dict(reservation=job['reservation'],money=normalized['ledger_money']),'provider:'+identifier+':'+digest)
                clean['reconciliation']='settled_from_provider_record'
            if clean['reconciliation']!='conflicting_record_requires_review':job['cost_confirmed']=not fake
        else:
            clean['reconciliation']='reservation_retained'
            if normalized['kind']=='provider_reported_credits' and r[0]=='reserved':
                ledger.command(c,store.workspace_id,job['scope'],'uncertain',{'reservation':job['reservation']},identifier+':credits-unconverted')
        job['cost_evidence']=clean
        c.execute('INSERT INTO provider_cost_observations VALUES (?,?,?,?)',(store.workspace_id,identifier,digest,json.dumps(clean)))
        GenerationQueue.save(c,job)
        return clean


def record_fal_usage(store,response,*,evidence_class):
    """Official /models/usage time buckets: NEVER allocate aggregate cost to one job."""
    if evidence_class not in {'fixture','recorded-provider','authenticated-provider'}:raise ValueError('trusted evidence class required')
    if not isinstance(response,dict) or not isinstance(response.get('time_series'),list) or len(response['time_series'])>1000:raise ValueError('bounded usage page required')
    records=[]
    for bucket in response['time_series']:
        if not isinstance(bucket.get('bucket'),str) or len(bucket['bucket'])>64 or not isinstance(bucket.get('results'),list) or len(bucket['results'])>1000:raise ValueError('invalid usage bucket')
        for row in bucket['results']:
            endpoint=row.get('endpoint_id')
            if not isinstance(endpoint,str) or not 1<=len(endpoint)<=200 or row.get('currency')!='USD':raise ValueError('invalid usage endpoint/currency')
            total=nonnegative(row['cost_total']);sub=nonnegative(row['cost_subtotal']);discount=nonnegative(row['cost_discount'])
            if sub-discount!=total:raise ValueError('inconsistent usage totals')
            records.append(dict(source='fal-usage-estimate',kind='aggregate_estimate',bucket=bucket['bucket'],endpoint_id=endpoint,
                amount_usd=str(total),quantity=str(nonnegative(row['quantity'])),evidence_class=evidence_class,
                job_attribution=None,billing_confirmed=False,invoice_confirmed=False))
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('CREATE TABLE IF NOT EXISTS provider_usage_snapshots (workspace TEXT, digest TEXT, body TEXT, PRIMARY KEY(workspace,digest))')
        for record in records:
            digest=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
            c.execute('INSERT OR IGNORE INTO provider_usage_snapshots VALUES (?,?,?)',(store.workspace_id,digest,json.dumps(record)))
    return records
