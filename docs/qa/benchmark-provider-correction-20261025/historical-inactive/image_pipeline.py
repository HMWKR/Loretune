"""Inactive image controller on the SAME actions/grants/generation queue/ledger.
Trusted server runtime injection only; no public enable endpoint, key loading or default.
"""
from copy import deepcopy
import hashlib,json,os,time
from pathlib import Path
import action_assets,action_execution as actions,contracts,guided,ledger,media_bridge,model_selection
import runway_provider as runway
from fal_provider import ProviderError

class ImagePipeline:
    def __init__(self,store,adapter,gate=None):
        self.store=store;self.adapter=adapter;self.gate=deepcopy(gate)
        self.verification=None;self.recovery_approval=None
    def project(self,c,name):
        state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        p=state['projects'].get(name)
        if not p or p.get('archived'):raise ValueError('current non-archived project required')
        return p,contracts.project_id(self.store.workspace_id,name)
    def data(self,c,p,action):
        action_assets.validate(c,self.store,p,{'action':action})
        raw=[]
        for ref in action['inputs'].get('asset_refs',[]):
            t=next(x for x in p['shots'][ref['shot']]['takes'] if x['id']==ref['take'])
            with os.fdopen(os.open(t['asset'],os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:value=f.read(4*1024*1024)
            if hashlib.sha256(value).hexdigest()!=ref['sha256']:raise ValueError('reference changed')
            raw.append(value)
        return runway.payload(action['inputs']['prompt'],action['options']['ratio'],raw)
    def prepare(self,name,shot,prompt,ratio,refs=(),*,expected_revision):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');p,pid=self.project(c,name);target=p['shots'][shot]
            if target['revision']!=expected_revision:raise ValueError('stale shot')
            plan=next((x for x in p.get('guided_plans',[]) if x['id']==target.get('plan_id')),None)
            if not plan or plan['status']!='applied' or shot not in plan['shots'] or plan['context_hash']!=guided.fingerprint(guided.context(p)):raise ValueError('current applied plan required')
            if len(refs)>3:raise ValueError('maximum three references')
            if any(r.get('role') not in {'character','style'} for r in refs):raise ValueError('image generation accepts character/style guidance; never silently reinterpret start/end frames')
            quote=runway.estimate()
            action=actions.propose(c,self.store.workspace_id,pid,plan_id=plan['id'],plan_revision=plan['version'],
                context_hash=model_selection.media_snapshot(p)['sha256'],context_kind='media-v1',role='image',
                release_id=runway.MODEL,inputs=dict(prompt=prompt,asset_refs=deepcopy(list(refs))),
                options=dict(shot=shot,shot_revision=expected_revision,ratio=ratio,quote=quote,
                    output_policy='runway-signed-url-24-48h; local-copy; not-fal-private-1h'),mode='provider',connection_id=runway.CONNECTION)
            data=self.data(c,p,action)
            return dict(action=action,quote=quote,input_sha256=guided.fingerprint(data))
    def check_gate(self,name,pid,action,data):
        gate=self.gate or {};quote=action['options']['quote']
        required=dict(workspace=self.store.workspace_id,project=pid,action_hash=action['hash'],
            input_sha256=guided.fingerprint(data),model=runway.MODEL,output_policy=action['options']['output_policy'])
        if any(gate.get(k)!=v for k,v in required.items()) or gate.get('expires',0)<=time.time() or gate.get('maximum_units')!=80000 or gate.get('maximum_calls')!=1:raise ValueError('explicit image input/cost/output-policy gate required')
        if quote['expires']<=time.time():raise ValueError('expired image estimate')
        if self.adapter.mode!='contract-fake' and gate.get('live_approved') is not True:raise ValueError('image live verification not authorized')
    def admit(self,name,action_id,*,human_approved=False):
        if human_approved is not True:raise ValueError('human approval required; model cannot approve')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');p,pid=self.project(c,name);w=self.store.workspace_id
            a=actions.get(c,'production_actions',w,pid,action_id)
            if (a['mode'],a['role'],a['connection_id'],a['release_id'])!=('provider','image',runway.CONNECTION,runway.MODEL):raise ValueError('wrong image action')
            prior=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,a['id'])).fetchone()
            if prior:return self.store.generation.get(prior[0])
            data=self.data(c,p,a);self.check_gate(name,pid,a,data)
            quote=deepcopy(a['options']['quote']);price=guided.fingerprint(quote)
            g=actions.grant(c,w,pid,[a['id']],actor='local-owner',approved=True,expires=min(self.gate['expires'],quote['expires']),price_revision=price,money_by_action={a['id']:quote['money']})
            actions.validate(a,g,model_selection.action_context(p,a),price)
            scope='project:'+pid;b=ledger.budget(c,w,scope)
            if not b:raise ValueError('provider budget missing')
            quote['budget_revision']=b['revision']
            binding=dict(action_id=a['id'],action_hash=a['hash'],grant_id=g['id'],grant_hash=g['hash'],plan_id=a['plan_id'],plan_revision=a['plan_revision'],release_id=a['release_id'],connection_id=runway.CONNECTION,price_revision=price,workspace=w,project=pid)
            context=dict(song=name,shot=a['options']['shot'],shot_revision=a['options']['shot_revision'],reference_version=None,
                rights='사용권 미확인',output_kind='image',action_binding=binding,execution_mode=self.adapter.mode,
                submission_binding=dict(gate_hash=guided.fingerprint(self.gate),adapter_identity=id(self.adapter)))
            job=self.store.generation.admit(scope,data,quote,context,'image:'+w+':'+pid+':'+a['id'],approved=True,connection=c)
            media_bridge.bind(c,w,pid,job);return job
    def validate_submission(self,c,job):
        p,pid=self.project(c,job['context']['song']);b=job['context']['action_binding'];w=self.store.workspace_id
        if (b['workspace'],b['project'],b['connection_id'])!=(w,pid,runway.CONNECTION):raise ValueError('job scope mismatch')
        row=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,b['action_id'])).fetchone()
        if not row or row[0]!=job['id']:raise ValueError('job mapping mismatch')
        a=actions.get(c,'production_actions',w,pid,b['action_id']);g=actions.get(c,'execution_grants',w,pid,b['grant_id'])
        price=guided.fingerprint({k:v for k,v in job['quote'].items() if k!='budget_revision'})
        actions.validate(a,g,model_selection.action_context(p,a),price)
        if a['hash']!=b['action_hash'] or g['hash']!=b['grant_hash'] or g['money'][a['id']]!=job['quote']['money']:raise ValueError('grant changed')
        if not g['external_transmission'] or a['connection_id']!=runway.CONNECTION or a['role']!='image' or a['release_id']!=runway.MODEL:raise ValueError('wrong provider authority')
        if p['shots'][job['context']['shot']]['revision']!=job['context']['shot_revision']:raise ValueError('shot changed')
        data=self.data(c,p,a);self.check_gate(job['context']['song'],pid,a,data)
        if data!=job['input'] or job['context']['submission_binding']!=dict(gate_hash=guided.fingerprint(self.gate),adapter_identity=id(self.adapter)):raise ValueError('immutable input/runtime changed')
    def process(self):
        with self.store.connect() as c:jobs=[json.loads(r[0]) for r in c.execute('SELECT body FROM generation_jobs')]
        for j in jobs:
            if j['context'].get('output_kind')!='image':continue
            try:
                if j['state']=='image_recovery_pending':
                    import image_recovery
                    return image_recovery.execute(self,j['id'])
                if j['state']=='prepared':self.store.generation.dispatch(j['id'],self.adapter,pre_submit=self.validate_submission);return True
                if j['state'] in {'accepted','running'} and time.time()-j['updated']>=5:self.store.generation.poll(j['id'],self.adapter);return True
                if j['state']=='result_ready':self.store.generation.import_result(j['id'],self.adapter.download);return True
            except Exception as exc:
                with self.store.connect() as c:
                    c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(j['id'],)).fetchone()[0])
                    original_failure=latest.get('failure_code')
                    before_recovery=latest['state']=='image_recovery_pending'
                    latest['state']='import_blocked' if latest['state'] in {'result_ready','downloading'} or (before_recovery and latest.get('result')) else 'reconciliation_required'
                    latest['failure_code']=original_failure if before_recovery and original_failure else exc.code if isinstance(exc,ProviderError) else 'local_image_validation_failed'
                    latest['last_error']='이미지 결과 수집/조회 보류. 기존 요청 보존; 자동 재발행 없음.'
                    row=c.execute('SELECT state FROM reservations WHERE id=?',(latest['reservation'],)).fetchone()
                    if row and row[0]=='reserved':ledger.command(c,self.store.workspace_id,latest['scope'],'uncertain',{'reservation':latest['reservation']},j['id']+':image-uncertain')
                    self.store.generation.save(c,latest)
                return True
        return False
