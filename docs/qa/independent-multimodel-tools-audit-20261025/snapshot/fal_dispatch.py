"""Saved action -> authorized admission -> model-specific fal queue.
No credentials loaded here. Runtime connections and one-action gates are trusted
server injection. Catalog metadata alone cannot enable execution.
"""
from copy import deepcopy
import hashlib,json,os,time
import action_assets,action_execution as actions,contracts,guided,ledger,media_bridge,model_selection
from fal_models import CONNECTION,MODELS
from fal_provider import ProviderError

class FalDispatch:
 def __init__(self,store,adapters):
  self.store=store;self.adapters={};self.gates={}
  for adapter in adapters:
   key=adapter.contract.spec['id']
   if key in self.adapters or adapter.connection_id!=CONNECTION:raise ValueError('duplicate/unsupported connection')
   self.adapters[key]=adapter
 def adapter(self,action):
  if action['connection_id']!=CONNECTION:raise ValueError('wrong dispatch connection')
  ad=next((a for a in self.adapters.values() if a.contract.MODEL==action['release_id']),None)
  if ad is None:raise actions.ExecutionBlocked('선택한 모델 연결을 검증해야 합니다.')
  return ad
 def project(self,c,name):
  state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);p=state['projects'].get(name)
  if not p or p.get('archived'):raise ValueError('current project required')
  return p,contracts.project_id(self.store.workspace_id,name)
 def data(self,c,p,a):
  ad=self.adapter(a);action_assets.validate(c,self.store,p,{'action':a})
  refs=a['inputs']['asset_refs'];frames=[]
  if ad.contract.role=='image' and refs:raise ValueError('text-to-image model cannot accept references')
  if ad.contract.role=='video' and (len(refs)!=1 or refs[0]['role']!='start_frame'):raise ValueError('one start frame required')
  if ad.contract.role=='video':
   shot=p['shots'][a['options']['shot']];version=next((v for v in shot.get('reference_versions',[]) if v['id']==shot.get('reference_head')),None)
   source=version.get('roles',{}).get('start_frame',{}) if version else {}
   if not version or version['status']!='approved' or any(source.get(k)!=refs[0][k] for k in ('shot','take','sha256')):raise ValueError('approved current start frame required')
  for ref in refs:
   take=next(t for t in p['shots'][ref['shot']]['takes'] if t['id']==ref['take'])
   with os.fdopen(os.open(take['asset'],os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:raw=f.read(4*1024*1024+1)
   if hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('reference changed')
   frames.append(raw)
  return ad.contract.payload(a['inputs']['prompt'],a['options']['generation'],frames)
 def prepare(self,c,p,name,shot,prompt,options,refs,expected_revision,explicit=None):
  if not isinstance(options,dict) or not isinstance(refs,list) or type(expected_revision) is not int or expected_revision<0:raise ValueError('typed media input required')
  role='video' if 'duration' in options else 'image'
  resolved=model_selection.resolve(role,explicit=explicit,project=model_selection.settings(p)['selections'][role])
  item=resolved['selection'];ad=self.adapters.get(item['id']) if item else None
  if ad is None:raise actions.ExecutionBlocked('선택 모델의 서버 연결·견적이 없습니다.')
  target=p['shots'][shot]
  if target['revision']!=expected_revision:raise ValueError('stale shot')
  plan=next((x for x in p.get('guided_plans',[]) if x['id']==target.get('plan_id')),None)
  if not plan or plan['status']!='applied' or shot not in plan['shots'] or plan['context_hash']!=guided.fingerprint(guided.context(p)):raise ValueError('current applied plan required')
  # Compute and validate input before persisting an immutable action.
  skeleton=dict(connection_id=CONNECTION,release_id=ad.contract.MODEL,inputs=dict(prompt=prompt,asset_refs=deepcopy(refs)),options=dict(generation=deepcopy(options),shot=shot))
  data=self.data(c,p,skeleton);quote=ad.contract.estimate(data)
  output_policy=deepcopy(ad._lifecycle)
  a=actions.propose(c,self.store.workspace_id,contracts.project_id(self.store.workspace_id,name),plan_id=plan['id'],plan_revision=plan['version'],context_hash=model_selection.media_snapshot(p)['sha256'],context_kind='media-v1',role=role,release_id=ad.contract.MODEL,inputs=skeleton['inputs'],options=dict(shot=shot,shot_revision=expected_revision,generation=deepcopy(options),quote=quote,output_policy=output_policy,selection_origin=resolved['origin']),mode='provider',connection_id=CONNECTION)
  return dict(action=a,estimate=quote,input_sha256=guided.fingerprint(data),state='needs_approval',mode=ad.mode)
 def prepare_tool(self,c,p,name,tool,args):
  if tool=='prepare_image_action':options={'ratio':args['ratio']};refs=[]
  elif tool=='prepare_video_action':
   options={'duration':args['duration'],'generate_audio':False};refs=[dict(shot=args['source_shot_id'],take=args['source_take_id'],sha256=args['source_sha256'],role='start_frame')]
  else:raise ValueError('unsupported media preparation')
  prepared=self.prepare(c,p,name,args['shot_id'],args['prompt'],options,refs,args['shot_revision'],args['model_id']);a=prepared['action']
  return dict(status='proposed',action_id=a['id'],plan_id=a['plan_id'],plan_revision=a['plan_revision'],model=a['release_id'],role=a['role'],prompt=a['inputs']['prompt'],output_options=a['options']['generation'],estimate=prepared['estimate']['money'],price_kind=prepared['estimate']['kind'],approval='required',mode=prepared['mode'],external_calls=0)
 def estimate_plan(self,c,p,name,plan_id):
  if not any(x['id']==plan_id for x in p.get('guided_plans',[])):return dict(status='not_found')
  pid=contracts.project_id(self.store.workspace_id,name)
  rows=c.execute('SELECT body FROM production_actions WHERE workspace=? AND project=?',(self.store.workspace_id,pid)).fetchall()
  items=[]
  for row in rows:
   a=json.loads(row[0])
   if a['plan_id']!=plan_id or a['connection_id']!=CONNECTION:continue
   q=a['options']['quote'];items.append(dict(action_id=a['id'],model=a['release_id'],role=a['role'],money=q['money'],price_kind=q['kind'],expired=q['expires']<=time.time()))
  return dict(status='estimated' if items and not any(x['expired'] for x in items) else 'incomplete',actions=items,total=ledger.money(sum(ledger.units(x['money']) for x in items),'USD') if items and not any(x['expired'] for x in items) else None,billing_confirmed=False,approval=False)
 def gate(self,pid,a,data):
  ad=self.adapter(a);g=self.gates.get(a['id'],{});q=a['options']['quote']
  required=dict(workspace=self.store.workspace_id,project=pid,action_hash=a['hash'],input_sha256=guided.fingerprint(data),model=a['release_id'],output_policy=a['options']['output_policy'],maximum_units=ledger.units(q['money']),maximum_calls=1)
  if any(g.get(k)!=v for k,v in required.items()) or g.get('expires',0)<=time.time():raise actions.ExecutionBlocked('고정 입력·비용·비공개 정책 전송 승인이 필요합니다.')
  if a['options']['output_policy']!=ad._lifecycle or ad.contract.estimate(data)!=q:raise ValueError('input/price/privacy changed')
  if ad.mode!='contract-fake' and (g.get('live_approved') is not True or (g.get('integration_verified') is not True and g.get('synthetic_verification_trial') is not True) or q['kind']!='documented-estimate'):raise actions.ExecutionBlocked('계정·실제 모델·출력 수신 검증 전입니다.')
  return g
 def approve(self,c,p,name,action_id):
  pid=contracts.project_id(self.store.workspace_id,name);a=actions.get(c,'production_actions',self.store.workspace_id,pid,action_id);data=self.data(c,p,a);gate=self.gate(pid,a,data);q=a['options']['quote']
  return actions.grant(c,self.store.workspace_id,pid,[a['id']],actor='local-owner',approved=True,expires=min(gate['expires'],q['expires'],time.time()+3599),price_revision=guided.fingerprint(q),money_by_action={a['id']:q['money']})
 def authorize(self,c,p,name,a,grant_id):
  pid=contracts.project_id(self.store.workspace_id,name);g=actions.get(c,'execution_grants',self.store.workspace_id,pid,grant_id);ad=self.adapter(a)
  data=self.data(c,p,a);self.gate(pid,a,data);q=a['options']['quote'];price=guided.fingerprint(q)
  actions.validate(a,g,model_selection.action_context(p,a),price)
  if not g['external_transmission'] or g['money'][a['id']]!=q['money'] or p['shots'][a['options']['shot']]['revision']!=a['options']['shot_revision']:raise ValueError('grant/input scope changed')
  return ad,data,g,price
 def request(self,c,w,pid,p,a,grant_id):
  row=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,a['id'])).fetchone()
  if row:return media_bridge.receipt(c,w,pid,p,a,grant_id)
  name=next((name for name in json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'] if contracts.project_id(w,name)==pid),None)
  if w!=self.store.workspace_id or name is None:raise ValueError('scope mismatch')
  ad,data,g,price=self.authorize(c,p,name,a,grant_id);quote=deepcopy(a['options']['quote']);scope='project:'+pid;b=ledger.budget(c,w,scope)
  if not b:raise actions.ExecutionBlocked('프로젝트 생성 예산이 필요합니다.')
  quote['budget_revision']=b['revision']
  binding=dict(action_id=a['id'],action_hash=a['hash'],grant_id=g['id'],grant_hash=g['hash'],plan_id=a['plan_id'],plan_revision=a['plan_revision'],release_id=a['release_id'],connection_id=CONNECTION,price_revision=price,workspace=w,project=pid)
  context=dict(song=name,shot=a['options']['shot'],shot_revision=a['options']['shot_revision'],reference_version=None,rights='사용권 미확인',output_kind=a['role'],action_binding=binding,execution_mode=ad.mode,dispatch=CONNECTION,expected_duration=int(data['duration']) if a['role']=='video' else None,expected_dimensions=[data['image_size']['width'],data['image_size']['height']] if a['role']=='image' else None,submission_binding=dict(gate_hash=guided.fingerprint(self.gates[a['id']]),adapter_identity=id(ad)))
  job=self.store.generation.admit(scope,data,quote,context,'fal-action:'+w+':'+pid+':'+a['id'],approved=True,connection=c);media_bridge.bind(c,w,pid,job)
  return dict(status='accepted',job_id=job['id'],**{k:v for k,v in media_bridge.projection(c,job).items() if k not in {'id','context'}})
 def validate_admission(self,data,quote,context):
  a=next((a for a in self.adapters.values() if a.contract.MODEL==quote['model']),None)
  if a is None or context['execution_mode']!=a.mode:raise ValueError('model route unavailable')
  q={k:v for k,v in quote.items() if k!='budget_revision'}
  if a.contract.estimate(data)!=q:raise ValueError('quote mismatch')
 def validate_submission(self,c,job):
  p,pid=self.project(c,job['context']['song']);b=job['context']['action_binding'];w=self.store.workspace_id
  if (b['workspace'],b['project'],b['connection_id'])!=(w,pid,CONNECTION):raise ValueError('scope mismatch')
  a=actions.get(c,'production_actions',w,pid,b['action_id']);ad,data,g,price=self.authorize(c,p,job['context']['song'],a,b['grant_id'])
  row=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,a['id'])).fetchone()
  if not row or row[0]!=job['id'] or a['hash']!=b['action_hash'] or g['hash']!=b['grant_hash'] or price!=b['price_revision'] or job['input']!=data or {k:v for k,v in job['quote'].items() if k!='budget_revision'}!=a['options']['quote'] or job['quote']['money']!=g['money'][a['id']]:raise ValueError('immutable job binding changed')
  if job['context']['submission_binding']!=dict(gate_hash=guided.fingerprint(self.gates[a['id']]),adapter_identity=id(ad)):raise ValueError('runtime approval changed')
 def process(self):
  with self.store.connect() as c:jobs=[json.loads(row[0]) for row in c.execute('SELECT body FROM generation_jobs')]
  for j in jobs:
   if j['context'].get('dispatch')!=CONNECTION:continue
   ad=next((a for a in self.adapters.values() if a.contract.MODEL==j['quote']['model']),None)
   if ad is None:continue
   try:
    if j['state']=='prepared':self.store.generation.dispatch(j['id'],ad,pre_submit=self.validate_submission);return True
    if j['state']=='cancel_pending':self.store.generation.send_cancel(j['id'],ad);return True
    if j['state'] in {'accepted','running','cancel_sent'} and time.time()-j['updated']>=5:self.store.generation.poll(j['id'],ad);return True
    if j['state']=='result_ready':self.store.generation.import_result(j['id'],ad.download);return True
   except Exception as exc:
    with self.store.connect() as c:
     c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(j['id'],)).fetchone()[0])
     latest.update(state='import_blocked' if latest['state'] in {'result_ready','downloading'} else 'reconciliation_required',failure_code=exc.code if isinstance(exc,ProviderError) else 'local_media_validation_failed',last_error='기존 요청 확인·수집 보류. 자동 재생성 없음.')
     row=c.execute('SELECT state FROM reservations WHERE id=?',(latest['reservation'],)).fetchone()
     if row and row[0]=='reserved':ledger.command(c,self.store.workspace_id,latest['scope'],'uncertain',{'reservation':latest['reservation']},j['id']+':dispatch-uncertain')
     self.store.generation.save(c,latest)
    return True
  return False


def public_actions(c,w,pid):
 result=[]
 for row in c.execute('SELECT body FROM production_actions WHERE workspace=? AND project=? ORDER BY rowid',(w,pid)):
  a=json.loads(row[0])
  if a.get('connection_id')!=CONNECTION:continue
  q=a['options']['quote'];mapping=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(w,pid,a['id'])).fetchone()
  g=next((json.loads(r[0]) for r in reversed(c.execute('SELECT body FROM execution_grants WHERE workspace=? AND project=?',(w,pid)).fetchall()) if a['id'] in json.loads(r[0]).get('action_hashes',{})),None)
  result.append(dict(id=a['id'],shot=a['options']['shot'],role=a['role'],model=a['release_id'],prompt=a['inputs']['prompt'],options=a['options']['generation'],estimate=q['money'],estimate_kind=q['kind'],mode='contract-fake' if q['kind']=='fixture' else 'provider-unverified',estimate_expired=q['expires']<=time.time(),approval='approved' if g and g['state']=='active' and g['expires']>time.time() else 'required',job_id=mapping[0] if mapping else None))
 return result
