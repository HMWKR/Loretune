"""Approved single supplemental live experiment; explicit phases, no replay."""
import json,time,hashlib,sys
from pathlib import Path
from urllib.request import Request,build_opener
from urllib.error import HTTPError
from app import Store
from fal_provider import payload,estimate,NoRedirect,ProviderError
from live_launcher import load_runtime,validate_approval
import ledger
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/qa/live-kling-explicit-reader-20261025'
SCOPE='approved-test:explicit-reader-20261025'

def main(phase):
    gate=json.loads((OUT/'approval.json').read_text());validate_approval(gate)
    store=Store(ROOT/'data');q=store.generation
    if store.workspace_id!=gate['workspace_id']:raise ValueError('workspace_mismatch')
    if phase=='submit':
        summary=json.loads((ROOT/'docs/qa/20261025/summary.json').read_text())
        if summary['failed'] or summary['tests']!=95:raise ValueError('qa_gate')
        raw=(ROOT/'docs/qa/fixtures/kling-live-v1/start-frame.png').read_bytes();prompt=(ROOT/'docs/qa/fixtures/kling-live-v1/prompt.txt').read_text().strip()
        if hashlib.sha256(raw).hexdigest()!=gate['image_sha256'] or hashlib.sha256(prompt.encode()).hexdigest()!=gate['prompt_sha256']:raise ValueError('input_hash')
        with store.connect() as c:
            previous=[json.loads(r[0]) for r in c.execute('select body from generation_jobs')]
            if len(previous)!=1 or previous[0]['id']!='0de9b6ee-8a50-4aaf-a54f-ed8a5d4c193c' or previous[0]['state']!='import_blocked':raise ValueError('existing_request_gate')
            if c.execute('select 1 from budgets where scope=?',(SCOPE,)).fetchone():raise ValueError('already_admitted')
        with (OUT/'one-attempt.json').open('x') as f:json.dump({'started':time.time(),'scope':SCOPE},f)
        shot=store.state()['projects'][gate['song']]['shots'][gate['shot']]
        with store.connect() as c:ledger.patch_budget(c,store.workspace_id,SCOPE,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
        context=dict(song=gate['song'],shot=gate['shot'],shot_revision=shot['revision'],reference_version=shot['reference_head'],rights='directly created synthetic geometry; user approved',approval_scope=SCOPE,lifecycle_sha256=gate['lifecycle_sha256'])
        j=q.admit(SCOPE,payload(prompt,raw),dict(estimate(),budget_revision=1),context,SCOPE,approved=True)
        (OUT/'job.json').write_text(json.dumps({'job':j['id']}))
        adapter=load_runtime(ROOT/'.env',gate,approved=True)
        j=q.dispatch(j['id'],adapter)
    else:
        identifier=json.loads((OUT/'job.json').read_text())['job'];j=q.get(identifier)
        if j['scope']!=SCOPE:raise ValueError('scope_mismatch')
        adapter=load_runtime(ROOT/'.env',gate,approved=True)
        if phase=='poll':j=q.poll(identifier,adapter)
        elif phase=='import':
            if j['state']!='result_ready':raise ValueError('not_ready')
            try:j=q.import_result(identifier,adapter.download)
            except Exception as e:
                with store.connect() as c:
                    j=q.get(identifier);j.update(state='import_blocked',failure_code=e.code if isinstance(e,ProviderError) else 'local_validation_failed',last_error='수신/검증 차단. 추가 생성 및 자동 재시도 없음.');q.save(c,j)
                    ledger.command(c,store.workspace_id,SCOPE,'uncertain',{'reservation':j['reservation']},identifier+':import-uncertain')
        elif phase=='anonymous':
            if j['state']!='imported':raise ValueError('not_imported')
            with (OUT/'anonymous-once.json').open('x') as f:json.dump({'started':time.time()},f)
            try:
                with build_opener(NoRedirect()).open(Request(j['result']['url']),timeout=30) as response:status=response.status
            except HTTPError as e:status=e.code;e.close()
            (OUT/'anonymous-once.json').write_text(json.dumps({'http_status':status,'blocked':status in (403,404)}))
        else:raise ValueError('unknown_phase')
    public={k:j.get(k) for k in ['id','state','failure_code','take','asset_sha256','cost_confirmed','created','updated']}
    public['request_id']=(j.get('receipt') or {}).get('request_id');public['phase']=phase;public['observed']=time.time()
    (OUT/'status.json').write_text(json.dumps(public,indent=2));print(json.dumps(public),flush=True)
if __name__=='__main__':
    try:main(sys.argv[1])
    except Exception as e:print(json.dumps({'stopped':True,'error_class':type(e).__name__,'detail':'redacted; no automatic retry'}));sys.exit(1)
