"""Durable admission and recovery for one approved provider request, no background dispatch."""
from contextlib import nullcontext
import hashlib
import json
import time
import uuid
import ledger
from fal_provider import ProviderError, MODEL, MAX_RESULT_BYTES


class GenerationQueue:
    def __init__(self,store):
        self.store=store
        with store.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS generation_jobs (id TEXT PRIMARY KEY, request_key TEXT UNIQUE, digest TEXT, body TEXT)')

    def get(self,identifier):
        with self.store.connect() as c:
            row=c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()
        if not row:raise ValueError('생성 작업을 찾을 수 없습니다.')
        return json.loads(row[0])

    @staticmethod
    def save(c,job):
        job['revision']+=1;job['updated']=time.time()
        c.execute('UPDATE generation_jobs SET body=? WHERE id=?',(json.dumps(job),job['id']))

    def admit(self,scope,data,quote,context,key,*,approved=False,connection=None):
        # This gate is controlled by a trusted runtime caller, never a client JSON flag.
        if not approved:raise ValueError('마지막 live gate의 전송·비용 승인이 필요합니다.')
        image=context.get('output_kind')=='image'
        if image:
            from runway_provider import MODEL as IMAGE_MODEL,validate_payload
            validate_payload(data)
            if quote.get('provider')!='runway' or quote.get('model')!=IMAGE_MODEL or quote.get('money')!={'amount':'0.08','currency':'USD'} or quote.get('output_count')!=1:raise ValueError('unapproved image quote')
        elif quote.get('model')!=MODEL or quote.get('money')!={'amount':'0.70','currency':'USD'} or quote.get('duration')!=10:
            raise ValueError('승인된 모델·10초 견적이 아닙니다.')
        if not image and (data.get('duration')!='10' or data.get('generate_audio') is not False):raise ValueError('승인된 출력 옵션이 아닙니다.')
        digest=hashlib.sha256(json.dumps(dict(scope=scope,data=data,context=context,quote=quote),sort_keys=True).encode()).hexdigest()
        with (nullcontext(connection) if connection is not None else self.store.connect()) as c:
            if connection is None:c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT digest,body FROM generation_jobs WHERE request_key=?',(key,)).fetchone()
            if row:
                if row[0]!=digest:raise ValueError('같은 생성 요청 키의 입력이 다릅니다.')
                return json.loads(row[1])
            identifier=str(uuid.uuid4())
            b=ledger.budget(c,self.store.workspace_id,scope)
            if not b:raise ValueError('공급자 예산을 먼저 설정하세요.')
            reserve=ledger.command(c,self.store.workspace_id,scope,'reserve',dict(money=quote['money'],budget_revision=quote['budget_revision'],expires=quote['expires'],job=identifier),identifier)
            job=dict(id=identifier,revision=1,state='prepared',scope=scope,context=context,input=data,quote=quote,
                     mode=context.get('execution_mode','provider-unverified'),external_calls=0,
                     reservation=reserve['reservation'],receipt=None,result=None,approved=False,cost_confirmed=False,
                     created=time.time(),updated=time.time())
            c.execute('INSERT INTO generation_jobs VALUES (?,?,?,?)',(identifier,key,digest,json.dumps(job)))
            return job

    def dispatch(self,identifier,adapter,*,pre_submit=None):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            if job['state']!='prepared':return job
            if job['quote']['expires']<=time.time():
                ledger.command(c,self.store.workspace_id,job['scope'],'release',{'reservation':job['reservation']},identifier+':expired')
                job.update(state='expired',verified_unsubmitted=True);self.save(c,job);return job
            validator=pre_submit or (self.store.validate_generation_submission if job['context'].get('submission_binding') or getattr(adapter,'live_enabled',False) else None)
            if validator:
                try:validator(c,job)
                except (ValueError,KeyError,OSError):
                    ledger.command(c,self.store.workspace_id,job['scope'],'release',{'reservation':job['reservation']},identifier+':submission-blocked')
                    job.update(state='submission_blocked',verified_unsubmitted=True,failure_code='submission_authority_changed',last_error='제출 전 권리·승인·입력·연결 재검사에서 차단됐습니다. 외부 제출 없음.')
                    self.save(c,job);return job
            job.update(state='submitting',verified_unsubmitted=False,submission_started_at=time.time(),
                       external_calls=0 if job.get('mode')=='contract-fake' else 1);self.save(c,job)
        try:receipt=adapter.submit(job['input'])
        except Exception as exc:
            # Even an unclassified transport failure cannot cause an automatic paid replay.
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
                job['state']='failed' if isinstance(exc,ProviderError) and exc.terminal else 'reconciliation_required'
                job['failure_code']=exc.code if isinstance(exc,ProviderError) else 'response_uncertain'
                job['last_error']='영구 요청 오류; 자동 재시도 없음·비용 미확정' if job['state']=='failed' else '접수 미확정; 자동 재발행 없음·예약 유지'
                ledger.command(c,self.store.workspace_id,job['scope'],'uncertain',{'reservation':job['reservation']},identifier+':uncertain')
                self.save(c,job)
            return job
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            job.update(receipt=receipt,state='cancel_pending' if job.get('cancel_requested') else 'accepted');self.save(c,job)
        return job

    @staticmethod
    def consumes_call_quota(c,job):
        # Only an explicit, persisted no-submission proof with a released unpaid
        # reservation can restore a slot. Legacy/unknown/started work still counts.
        if job.get('verified_unsubmitted') is not True or job['state'] not in {'submission_blocked','expired','cancelled'}:return True
        if job.get('submission_started_at') or job.get('receipt') or job.get('result') or job.get('cost_confirmed'):return True
        row=c.execute('SELECT state,actual,refunded FROM reservations WHERE id=?',(job['reservation'],)).fetchone()
        return not (row and row[0]=='cancelled' and row[1] is None and row[2]==0)

    def recover(self):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            for row in c.execute('SELECT body FROM generation_jobs').fetchall():
                job=json.loads(row[0])
                if job['state']=='downloading':
                    job.update(state='import_blocked',failure_code='download_interrupted',last_error='수신 중 재시작. 기존 요청 결과를 수동 재개하세요. 새 생성 없음.')
                    self.save(c,job)
                elif job['state']=='submitting':
                    job['state']='reconciliation_required'
                    ledger.command(c,self.store.workspace_id,job['scope'],'uncertain',{'reservation':job['reservation']},job['id']+':uncertain')
                    self.save(c,job)

    def poll(self,identifier,adapter):
        job=self.get(identifier)
        if job['state'] not in {'accepted','running','cancel_sent'}:return job
        status=adapter.status(job['receipt'])
        result=(status.get('result') or adapter.result(job['receipt'])) if status['result_ready'] else None
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            if latest['state'] not in {'accepted','running','cancel_sent'}:return latest
            latest['state']=('cancelled_result' if latest.get('cancel_requested') else 'result_ready') if result else ('cancel_sent' if latest.get('cancel_requested') else 'running' if status['state']=='IN_PROGRESS' else 'accepted')
            latest['result']=result
            if status.get('terminal_state'):latest['state']=status['terminal_state']
            latest['provider_state']=status.get('provider_state',status['state'])
            # A result URL is not a downloaded/decoded take, approval, or billing receipt.
            self.save(c,latest)
        if status.get('billing'):
            import provider_billing
            provider_billing.reconcile(self.store,identifier,'runway-task',status['billing'],evidence_class='fixture' if job['mode']=='contract-fake' else 'authenticated-provider')
            latest=self.get(identifier)
        return latest

    def import_result(self,identifier,download):
        """Download callable must enforce the approved provider host/size policy."""
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            if job['state'] in {'imported','downloading'}:return job
            if job['state']!='result_ready':raise ValueError('검증할 생성 결과가 없습니다.')
            claim=uuid.uuid4().hex
            job.update(state='downloading',download_claim=claim);self.save(c,job)
        context=job['context']
        raw=download(job['result']['url'])
        current=self.get(identifier)
        if current['state']!='downloading' or current.get('download_claim')!=claim:raise ValueError('수신 작업 소유권이 변경되었습니다.')
        image=context.get('output_kind')=='image'
        if image:
            extension='.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg'
            path,metadata=self.store.save_media(raw,extension,'video',max_bytes=16*1024*1024,expected_dimensions=tuple(map(int,job['input']['ratio'].split(':'))))
        else:path,metadata=self.store.save_media(raw,'.mp4','video',max_bytes=MAX_RESULT_BYTES,expected_duration=10)
        from loretune import Studio
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            if latest['state']=='imported':return latest
            if latest['state']!='downloading' or latest.get('download_claim')!=claim:raise ValueError('생성 결과 상태가 변경되었습니다.')
            revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            saved=json.loads(body);studio=Studio();studio.canon=saved['canon'];studio.projects=saved['projects']
            project=studio.projects[context['song']]
            if project.get('archived'):raise ValueError('보관 해제 후 결과를 연결하세요.')
            shot=project['shots'][context['shot']]
            stale=shot['revision']!=context['shot_revision']
            studio.attach_take(context['song'],context['shot'],path,reason='공급자 이미지 결과; 별도 검토 필요' if image else 'fal.ai Kling 생성 결과; 별도 검토 필요',expected_revision=shot['revision'])
            take=shot['takes'][-1]
            take.update(metadata=metadata,rights=context['rights'],filename=('runway-'+identifier+extension) if image else 'kling-'+identifier+'.mp4',
                provenance=dict(provider=job['quote'].get('provider','fal.ai'),model=job['quote']['model'],job=identifier,request_id=latest['receipt']['request_id']),
                reference_version_at_upload=context['reference_version'],stale_input=stale)
            binding=context.get('action_binding')
            if binding:
                take.update(action_id=binding['action_id'],plan_id=binding['plan_id'],plan_revision=binding['plan_revision'])
            take['provenance']['mode']=latest.get('mode','provider-unverified')
            latest.update(state='imported',take=take['id'],asset_sha256=take['sha256'],stale_input=stale)
            self.save(c,latest)
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(saved)))
            c.execute('INSERT INTO audit(created,action,revision) VALUES (?,?,?)',(time.time(),'import_generation_result',revision+1))
        return latest

    def request_cancel(self,identifier,reason,connection):
        c=connection
        row=c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()
        if not row:raise ValueError('생성 작업이 없습니다.')
        job=json.loads(row[0])
        if job.get('cancel_requested'):return job
        if job['context'].get('output_kind')=='image' and job['state']!='prepared':raise ValueError('Runway DELETE may delete completed output; post-submit cancellation is not enabled')
        if job['state'] not in {'prepared','accepted','running','submitting','reconciliation_required'}:raise ValueError('취소 가능한 진행 작업이 아닙니다.')
        job.update(cancel_requested=True,cancel_reason=reason)
        if job['state']=='prepared':
            ledger.command(c,self.store.workspace_id,job['scope'],'release',{'reservation':job['reservation']},identifier+':cancel-before-send')
            job.update(state='cancelled',verified_unsubmitted=True)
        elif job['receipt']:job['state']='cancel_pending'
        else:job['state']='reconciliation_required'
        self.save(c,job)
        return job

    def send_cancel(self,identifier,adapter):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
            if job['state']!='cancel_pending':return job
            job['state']='cancel_sent';self.save(c,job)
        try:adapter.cancel(job['receipt'])
        except Exception:
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                job=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(identifier,)).fetchone()[0])
                job['last_error']='취소 응답 미확정. 원본 요청 상태를 조회하며 환급으로 처리하지 않습니다.';self.save(c,job)
        return job
