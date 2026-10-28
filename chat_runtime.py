"""Bounded, disabled-by-default Anthropic tool loop over the canonical Store.

Server injects a synthetic-only approval, shared usage journal and credential
supplier. Browser/model inputs cannot enable a provider, grant money or select
an endpoint. No automatic retries, fallback, .env reads or private reasoning logs.
"""
import hashlib,json,sqlite3,time,uuid
from copy import deepcopy
from decimal import Decimal,ROUND_CEILING
import anthropic_ontology as anthropic
import chat_sessions
import chat_models
import agent_preferences
import chat_protocols,contracts,guided,model_selection,production_tools

# D1: explicit legacy default scope; a model may not submit media generation.
LEGACY_DEFAULT_TOOLS=['search_project_context','get_model_capabilities','propose_media_plan','estimate_media_plan','prepare_image_action','prepare_video_action','get_generation_job','propose_timeline_edit','propose_timeline_changes','propose_motion_scene','request_motion_render','request_render','propose_memory_update']

def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS chat_turns (id TEXT PRIMARY KEY, project TEXT NOT NULL, body TEXT NOT NULL)')

def put(c,turn):
 c.execute('INSERT INTO chat_turns VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(turn['id'],turn['project'],json.dumps(turn)))

def get(c,identifier):
 row=c.execute('SELECT body FROM chat_turns WHERE id=?',(identifier,)).fetchone()
 if not row:raise ValueError('대화 작업이 없습니다.')
 return json.loads(row[0])

def public(turn):
 return {k:deepcopy(turn.get(k)) for k in ['id','conversation_id','status','mode','model','prompt','answer','answer_review','steps','error','usage_cost_usd','billing_confirmed']}

def cancel(c,project_id,identifier,conversation_id=None):
 t=get(c,identifier)
 if conversation_id is not None and (t.get('conversation_id') or chat_sessions.default_id({'name':t['name']}))!=conversation_id:raise ValueError('다른 대화의 요청입니다.')
 if t['project']!=project_id:raise ValueError('현재 작품의 대화가 아닙니다.')
 if t['status'] in {'queued','running'}:
  t['status']='cancelled' if t['status']=='queued' else 'cancel_requested';put(c,t)
 return public(t)

def claim_tool(c,store,project_id,run_id,call,request_id,project):
 """Fence chat tool execution in the same transaction as its side effect."""
 turns=[json.loads(row[0]) for row in c.execute('SELECT body FROM chat_turns WHERE project=?',(project_id,))]
 turns=[t for t in turns if t.get('run')==run_id]
 if not turns:return
 if len(turns)!=1 or store.chat_runtime is None:raise ValueError('대화 도구 실행 문맥을 확인하세요.')
 t=turns[0]
 runtime=store.chat_runtime.selected(project) if isinstance(store.chat_runtime,ChatRouter) else store.chat_runtime
 if t['status']!='running' or (t.get('conversation_id') or chat_sessions.default_id(project))!=chat_sessions.current(project):raise ValueError('취소되었거나 진행 중이 아닌 대화입니다.')
 runtime.guard(t['name'],project,t['prompt'])
 if t.get('binding')!=guided.fingerprint(runtime.approval) or t.get('model')!=runtime.spec['model']:raise ValueError('대화 승인 문맥이 변경됐습니다.')
 run=next((x for x in project.get('production_runs',[]) if x['id']==run_id),None)
 if run is None or agent_preferences.frozen(project,run)!=agent_preferences.frozen(project,t):raise ValueError('에이전트 실행에 고정한 설정이 변경됐습니다.')
 pending=t.get('pending_tool')
 if not isinstance(pending,dict) or pending.get('call')!=call or pending.get('request_id')!=request_id or call.get('name') not in runtime.limits()['tools']:
  raise ValueError('승인된 대화 도구 요청이 아닙니다.')
 t.pop('pending_tool');put(c,t)

def recover(c):
 for row in c.execute('SELECT body FROM chat_turns').fetchall():
  t=json.loads(row[0])
  if t['status'] in {'running','cancel_requested'}:
   t.update(status='outcome_unknown',error='프로세스가 중단됐습니다. 기존 도구 결과와 원장을 확인하세요. 자동 재호출하지 않습니다.');put(c,t)

def compact_result(result):
 """Retain truth/receipt; don't repeat the entire canon inside a saved plan."""
 if result.get('status')=='proposed' and isinstance(result.get('plan'),dict):
  p=result['plan'];return dict(status='proposed',plan={k:deepcopy(p[k]) for k in ['id','version','status','scenes','questions']},cost_approval=False)
 return deepcopy(result)

def request_history(workspace_id,project_id,turns,conversation_id=None):
 """Lossless accepted user-request evidence, separate from recent dialogue.

 Callers supply project-scoped rows in insertion order. Status is processing
 history, not approval or an automatically extracted active constraint.
 """
 records=[dict(turn_id=t['id'],sequence=i,text=t['prompt'],
               source_hash=hashlib.sha256(t['prompt'].encode('utf-8')).hexdigest(),
               status=t['status']) for i,t in enumerate(turns,1)]
 value=dict(schema_version=1,scope=dict(workspace_id=workspace_id,project_id=project_id,
            conversation='project-default'),requests=records)
 if conversation_id is not None:value['schema_version']=2;value['scope']['conversation']=conversation_id
 return dict(value,digest=guided.fingerprint(value))

class AnthropicChatAdapter:
 selection='anthropic-haiku-5-5'
 provider='anthropic'
 model=anthropic.MODEL
 mode='anthropic-live'
 def __init__(self,credential_supplier,*,enabled=False,count_transport=None,message_transport=None):
  self.supplier=credential_supplier;self.enabled=enabled
  # Ordered request evidence and tool results exceed extraction's 12 KB envelope.
  # This independent byte ceiling never replaces the counted token/budget gates.
  self.count_transport=count_transport or anthropic.BoundedCountTransport(max_request_bytes=65536)
  self.message_transport=message_transport or anthropic.BoundedMessagesTransport(timeout=60,max_request_bytes=65536)
 def preflight(self,body):
  # Count omits max_tokens. Check the full Messages body before any request or
  # credential read; known local rejection must not become an unknown charge.
  encode=getattr(self.message_transport,'encode_body',None)
  if encode is None:encode=anthropic.BoundedMessagesTransport(max_request_bytes=65536).encode_body
  encode(body)
 def _call(self,body,*,count):
  if not self.enabled:raise ValueError('provider disabled')
  key=None;headers=None;failure_category='credentials'
  try:
   key=self.supplier('Anthropic_KEY')
   if not isinstance(key,str) or not key:raise ValueError()
   headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
   failure_category='transport'
   result=(self.count_transport if count else self.message_transport)(anthropic.BoundedCountTransport.endpoint if count else anthropic.ENDPOINT,headers,body)
   failure_category='malformed_response'
   # Never persist provider private reasoning or a response echoing a credential.
   visible=[b for b in result.get('content',[]) if b.get('type') in {'text','tool_use'}]
   if key in json.dumps({'content':visible,'request_id':result.get('_request_id'),'usage':result.get('usage')}):raise ValueError()
   return result
  except Exception as exc:
   failure=anthropic.safe_failure(**exc.failure) if isinstance(exc,anthropic.ProposalError) else anthropic.safe_failure(failure_category)
   if isinstance(key,str) and key and key in failure.get('request_id',''):failure.pop('request_id')
   raise anthropic.ProposalError('provider request/response unavailable; no automatic retry',**failure) from None
  finally:key=None;headers=None
 def count(self,body):
  result=self._call({k:v for k,v in body.items() if k!='max_tokens'},count=True)
  tokens=result.get('input_tokens')
  if type(tokens) is not int or tokens<0:
   raise anthropic.ProposalError('provider count response invalid',category='malformed_response',request_id=result.get('_request_id'))
  return tokens
 def complete(self,body):return self._call(body,count=False)

class UsageJournal:
 """Shared with earlier approved synthetic trials; unknowns retain reservations."""
 def __init__(self,path,mode='anthropic-live'):
  self.path=path;self.mode=mode
 def _require_known_exposure(self,c,exclude=None):
  if self.mode=='contract-fake':return
  # Check and claim under one SQLite write lock. Existing holds are untouched.
  for identifier,state,amount,actual,raw in c.execute('SELECT id,state,held_micro,actual_micro,metadata FROM trials'):
   if identifier==exclude:continue
   if type(amount) is not int or amount<0 or (actual is not None and (type(actual) is not int or actual<0)):raise ValueError('invalid journal exposure')
   if actual is not None or amount==0:continue
   meta=json.loads(raw);submitted=meta.get('messages_submitted')
   before_message=(state in {'reserved','preflight_started','count_started'} and ('messages_submitted' not in meta or submitted is False)) or (state=='blocked_before_message' and submitted is False)
   if not before_message:raise ValueError('unresolved message usage blocks new live reservation or claim')
 def reserve(self,identifier,digest,turn,held,turn_cap,stage=None):
  c=sqlite3.connect(self.path,timeout=30)
  try:
   c.execute('BEGIN IMMEDIATE')
   c.execute('CREATE TABLE IF NOT EXISTS trials (id TEXT PRIMARY KEY,input_hash TEXT,state TEXT,held_micro INTEGER,actual_micro INTEGER,metadata TEXT)')
   if c.execute('SELECT 1 FROM trials WHERE id=?',(identifier,)).fetchone():raise ValueError('attempt already recorded')
   rows=c.execute('SELECT id,COALESCE(actual_micro,held_micro),metadata FROM trials').fetchall()
   if any(json.loads(r[2]).get('mode','anthropic-live')!=self.mode for r in rows):raise ValueError('live and fake usage journals must be separate')
   self._require_known_exposure(c)
   if sum(r[1] for r in rows)+held>50_000_000:raise ValueError('cumulative cap')
   if sum(r[1] for r in rows if r[0].startswith('chat:'+turn+':'))+held>turn_cap:raise ValueError('turn cap')
   if stage and sum(r[1] for r in rows if json.loads(r[2]).get('stage')==stage['id'])+held>stage['cap_micro']:raise ValueError('stage cap')
   c.execute('INSERT INTO trials VALUES (?,?,?,?,?,?)',(identifier,digest,'reserved',held,None,json.dumps({'mode':self.mode,'stage':stage['id'] if stage else None})));c.commit()
  finally:c.close()
 def update(self,identifier,state,metadata,*,actual=None,release=False):
  c=sqlite3.connect(self.path,timeout=30)
  try:
   c.execute('BEGIN IMMEDIATE')
   old=c.execute('SELECT metadata,state,held_micro,actual_micro FROM trials WHERE id=?',(identifier,)).fetchone()
   if state=='message_started':
    if not old:raise ValueError('attempt unavailable')
    if old[1] not in {'reserved','preflight_started','count_started'} or type(old[2]) is not int or old[2]<=0 or old[3] is not None:raise ValueError('attempt already submitted or unavailable')
    previous=json.loads(old[0])
    if 'messages_submitted' in previous and previous['messages_submitted'] is not False:raise ValueError('attempt already submitted or unavailable')
    self._require_known_exposure(c,exclude=identifier)
   combined=json.loads(old[0]) if old else {};combined.update(metadata)
   c.execute('UPDATE trials SET state=?,metadata=?,actual_micro=COALESCE(?,actual_micro),held_micro=CASE WHEN ? THEN 0 ELSE held_micro END WHERE id=?',(state,json.dumps(combined),actual,int(release),identifier));c.commit()
  finally:c.close()

class ChatRuntime:
 def __init__(self,store,adapter,approval,journal_path):
  if isinstance(adapter,AnthropicChatAdapter) and adapter.mode!='anthropic-live':raise ValueError('Anthropic adapter requires live journal')
  self.store=store;self.adapter=adapter;self.approval=deepcopy(approval);self.spec=chat_models.contract(getattr(adapter,'selection','anthropic-haiku-5-5'));self.journal=UsageJournal(journal_path,adapter.mode)
 def limits(self):
  a=self.approval
  value=dict(input=a.get('max_input_tokens',4096),output=a.get('max_output_tokens',4096),turn=a.get('turn_cap_micro',10000),tools=a.get('tools',list(LEGACY_DEFAULT_TOOLS)))
  if any(type(value[k]) is not int or not 1<=value[k]<=16384 for k in ['input','output']):raise ValueError('token limits unavailable')
  if type(value['turn']) is not int or not 1<=value['turn']<=100000:raise ValueError('turn budget unavailable')
  if not isinstance(value['tools'],list) or not value['tools'] or any(t not in production_tools.TOOLS for t in value['tools']) or len(set(value['tools']))!=len(value['tools']):raise ValueError('tool scope unavailable')
  stage=a.get('stage')
  if stage and (set(stage)!={'id','cap_micro'} or not isinstance(stage['id'],str) or not stage['id'] or type(stage['cap_micro']) is not int or not 1<=stage['cap_micro']<=100000):raise ValueError('stage budget unavailable')
  if 'max_turns' in a and (type(a['max_turns']) is not int or not 1<=a['max_turns']<=4):raise ValueError('turn count unavailable')
  return value
 def capability(self,name,project):
  try:self.guard(name,project,None)
  except ValueError:return dict(available=False,mode='disconnected',reason='승인된 합성 문맥·모델 연결이 없습니다. 외부 전송 없음')
  return dict(available=True,mode=self.adapter.mode,model=self.spec['model'],reason='합성 검증 범위만 허용; 답변·계획은 검토 전',maximum_usd=str(Decimal(self.limits()['turn'])/1000000),external_transmission=self.adapter.mode!='contract-fake')
 def guard(self,name,p,prompt):
  a=self.approval
  self.limits()
  if isinstance(self.adapter,AnthropicChatAdapter) and (self.adapter.mode!='anthropic-live' or self.journal.mode!='anthropic-live'):raise ValueError('Anthropic adapter requires live journal')
  if self.adapter.mode not in {self.spec['provider']+'-live','contract-fake'} or a.get('model')!=self.spec['model']:raise ValueError('model/adapter not approved')
  if a.get('workspace_id')!=self.store.workspace_id or a.get('project_id')!=contracts.project_id(self.store.workspace_id,name):raise ValueError('project not approved')
  if a.get('synthetic_only') is not True or a.get('expires',0)<=time.time() or p.get('archived'):raise ValueError('scope unavailable')
  selected=model_selection.resolve('chat',explicit=chat_sessions.selected_chat(p))['selection']
  if selected is None or selected['id']!=self.spec['id']:raise ValueError('selected model unavailable')
  if self.spec['provider']!='anthropic' and (a.get('provider')!=self.spec['provider'] or a.get('selection')!=self.spec['id']):raise ValueError('provider-specific approval required')
  if model_selection.snapshot(p)['sha256']!=a.get('context_hash'):raise ValueError('context changed')
  if prompt is not None and hashlib.sha256(prompt.encode()).hexdigest() not in a.get('prompt_hashes',[]):raise ValueError('unapproved input')
  if a.get('price_revision')!=self.spec['price_revision'] or type(a.get('max_rounds')) is not int or not 1<=a['max_rounds']<=4:raise ValueError('limits unavailable')
 def prepare(self,c,p,name,data):
  if set(data)!={'song','prompt'} or not isinstance(data['prompt'],str) or not 1<=len(data['prompt'].strip())<=2000:raise ValueError('대화 입력을 확인하세요.')
  if chat_sessions.resolve(p,chat_sessions.current(p)).get('pending_chat_selection'):
   raise ValueError('완료되지 않은 응답의 모델 예약을 확인하고 다시 선택하세요.')
  self.guard(name,p,data['prompt'])
  project_id=contracts.project_id(self.store.workspace_id,name)
  if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='general_chat_turns'").fetchone():
   if any(json.loads(r[0])['status'] in {'queued','running','cancel_requested','outcome_unknown','awaiting_continuation_approval'}
          for r in c.execute('SELECT body FROM general_chat_turns WHERE project=? AND conversation=?',(project_id,chat_sessions.current(p)))):
    raise ValueError('진행 중이거나 결과 미확정인 대화를 먼저 확인하세요.')
  existing=[json.loads(row[0]) for row in c.execute('SELECT body FROM chat_turns WHERE project=? ORDER BY rowid',(project_id,))]
  if 'max_turns' in self.approval and len(existing)>=self.approval['max_turns']:raise ValueError('승인된 대화 횟수를 모두 사용했습니다.')
  if self.approval.get('one_per_prompt') and any(t['prompt']==data['prompt'] for t in existing):raise ValueError('이미 접수한 입력입니다. 기존 대화 결과를 확인하세요.')
  all_existing=existing
  existing=[t for t in existing if (t.get('conversation_id') or chat_sessions.default_id(p))==chat_sessions.current(p)]
  if any(t['status'] in {'queued','running','cancel_requested','outcome_unknown'} for t in existing):raise ValueError('진행 중이거나 결과 미확정인 대화를 먼저 확인하세요.')
  run=production_tools.begin(p);p['production_runs'][-1].update(engine=self.adapter.mode,provider_model=self.spec['model'])
  t=dict(id=uuid.uuid4().hex,conversation_id=chat_sessions.current(p),project=contracts.project_id(self.store.workspace_id,name),name=name,run=run['id'],
         prompt=data['prompt'],status='queued',mode=self.adapter.mode,model=self.spec['model'],binding=guided.fingerprint(self.approval),
         answer=None,answer_review='unreviewed',steps=[],usage_cost_usd='0',billing_confirmed=False)
  t['agent_settings']=deepcopy(run['agent_settings'])
  import action_execution
  handoff=chat_protocols.handoff(p,name,action_execution.project_jobs(c,self.store.workspace_id,project_id,name),__import__('production_context').read(c,self.store,p,name))
  cid=chat_sessions.current(p)
  handoff['session_request_history']=request_history(self.store.workspace_id,project_id,existing,None if cid==chat_sessions.default_id(p) else cid)
  for x in [v for v in existing if v['status']=='completed'][-8:]:
   handoff['messages'].append(dict(role='user',text=x['prompt']))
   if x.get('answer'):handoff['messages'].append(dict(role='assistant',text=x['answer'],review='unreviewed'))
  t['handoff']=handoff
  put(c,t);return public(t)
 def _save(self,t):
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE');old=get(c,t['id'])
   # Cancellation cannot settle an already submitted request whose result or
   # accounting is unknown. Keep it blocked until it can be reconciled.
   if old['status']=='cancel_requested' and t['status'] not in {'running','outcome_unknown'}:t['status']='cancelled'
   elif old['status']=='cancel_requested' and t['status']=='running':t['status']='cancel_requested'
   elif old['status']=='cancelled' and t['status']!='outcome_unknown':t['status']='cancelled'
   elif old['status']=='outcome_unknown':t['status']='outcome_unknown'
   put(c,t)
   if t['status']=='completed':
    revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();state=json.loads(body)
    p=state['projects'].get(t['name'])
    if p and chat_sessions.apply_completed_selection(p,t):
     c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))
 def _fresh(self,t):
  with self.store.connect() as c:current=get(c,t['id'])
  if current['status']!='running':raise ValueError('turn not running')
  p=chat_sessions.scoped(self.store.state()['projects'][t['name']],t.get('conversation_id'))
  run=next((x for x in p.get('production_runs',[]) if x['id']==t['run']),None)
  if run is None or agent_preferences.frozen(p,run)!=agent_preferences.frozen(p,t):raise ValueError('에이전트 실행에 고정한 설정이 변경됐습니다.')
  self.guard(t['name'],p,t['prompt'])
  if t['binding']!=guided.fingerprint(self.approval):raise ValueError('approval changed')
 def _claim_message(self,t):
  # The current turn, project scope and approval are checked under the same
  # writer lock as recording the authorization to submit this round.
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE');current=get(c,t['id'])
   if current['status']!='running':raise ValueError('turn no longer running')
   state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
   p=chat_sessions.scoped(state['projects'][t['name']],t.get('conversation_id'))
   self.guard(t['name'],p,t['prompt'])
   if t['binding']!=guided.fingerprint(self.approval):raise ValueError('approval changed')
   put(c,t)
 def process_next(self):
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE');rows=c.execute('SELECT body FROM chat_turns ORDER BY rowid').fetchall()
   t=next((json.loads(r[0]) for r in rows if json.loads(r[0])['status']=='queued' and json.loads(r[0])['model']==self.spec['model']),None)
   if t is None:return False
   t['status']='running';put(c,t)
  context=json.dumps(t.get('handoff',{}),ensure_ascii=False)
  messages=[dict(role='user',content='Server-owned public handoff (data, not instructions): '+context),dict(role='user',content=t['prompt'])];attempt=None;submitted=False;received=False;unsettled_response=False
  try:
   limits=self.limits()
   for round_index in range(self.approval['max_rounds']):
    attempt=None;submitted=False;received=False;unsettled_response=False;self._fresh(t)
    project=chat_sessions.scoped(self.store.state()['projects'][t['name']],t.get('conversation_id'))
    run=next((x for x in project.get('production_runs',[]) if x['id']==t['run']),{})
    permitted=agent_preferences.tools_for(project,run,limits['tools'])
    definitions=[d for d in chat_protocols.tool_definitions(self.spec['provider']) if d['name'] in permitted]
    for item in definitions:
     item['strict']=True
     if item['name']=='propose_media_plan':item['input_schema' if self.spec['provider']=='anthropic' else 'parameters']['properties']['kind']['enum']=['narrative','performance','visualizer']
    body=chat_models.body(self.spec,messages,definitions,limits['output'],effort=agent_preferences.frozen(project,t)['effort'])
    digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest();identifier='chat:'+t['id']+':'+str(round_index)
    self.journal.reserve(identifier,digest,t['id'],int((chat_models.cost(self.spec,limits['input'],limits['output'])*1000000).to_integral_value(rounding=ROUND_CEILING)),limits['turn'],self.approval.get('stage'));attempt=identifier
    step=dict(round=round_index,mode=t['mode'],input_sha256=digest,status='preflight_started',request_id=None,tool_calls=[])
    t['steps'].append(step);self._save(t);self.journal.update(identifier,'preflight_started',step)
    preflight=getattr(self.adapter,'preflight',None)
    if preflight is not None:preflight(body)
    step['status']='count_started';self._save(t);self.journal.update(identifier,'count_started',step)
    tokens=self.adapter.count(body);step['input_tokens_counted']=tokens
    if type(tokens) is not int or not 0<=tokens<=limits['input']:raise anthropic.ProposalError('input cap',category='input_limit')
    self._fresh(t);step['status']='message_started';self._claim_message(t)
    self.journal.update(identifier,'message_started',step)
    # Journal I/O can wait while a user cancels or the process is recovered.
    # Recheck under the Store lock before crossing the adapter boundary.
    self._claim_message(t);submitted=True
    response=self.adapter.complete(body);received=True;unsettled_response=True
    live=isinstance(self.adapter,AnthropicChatAdapter) or self.adapter.mode!='contract-fake'
    usage=chat_models.usage(self.spec,response,require_model=live,require_billing_evidence=live)
    cost=chat_models.cost(self.spec,usage['input_tokens'],usage['output_tokens'])
    step.update(status='response_received',request_id=response.get('_request_id'),usage={k:usage[k] for k in ['input_tokens','output_tokens']},usage_cost_usd=str(cost),stop_reason=response.get('stop_reason',response.get('status')))
    t['usage_cost_usd']=str(Decimal(t['usage_cost_usd'])+cost)
    self.journal.update(identifier,'response_received',step,actual=int((cost*1000000).to_integral_value(rounding=ROUND_CEILING)))
    unsettled_response=False
    # Provider-reported usage remains recorded even when it violates the
    # requested limits. Do not execute tools or submit another round after an
    # over-limit response; the amount is an estimate, not a billing receipt.
    if usage['input_tokens']>limits['input'] or usage['output_tokens']>limits['output']:
     step['failure']={'stage':'response','category':'usage_limit_exceeded'}
     raise ValueError('provider usage exceeds approved token limits')
    visible=chat_models.visible(self.spec,response)
    step['output_sha256']=hashlib.sha256(json.dumps(visible,sort_keys=True).encode()).hexdigest();step['visible_response']=visible;self._save(t)
    self._fresh(t);normalized=chat_protocols.normalize(self.spec['provider'],response,t['run'])
    if not normalized['calls']:
     t['answer']=chat_models.text(self.spec,response)
     if not t['answer'].strip():raise ValueError('answer missing')
     t['status']='completed';step['status']='answer_received'
     self.journal.update(identifier,'completed',step);self._save(t);break
    tool_results=[]
    for call in normalized['calls']:
     if call['name'] not in limits['tools']:raise ValueError('tool outside approved scope')
     self._fresh(t)
     request=dict(action='production_tool',data=dict(song=t['name'],run=t['run'],call=call),revision=self.store.state()['revision'],request_id=t['id']+':'+str(round_index)+':'+call['id'])
     if t.get('conversation_id'):
      with self.store.connect() as c:
       raw=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'][t['name']]
      request.update(conversation_id=t['conversation_id'],conversation_revision=chat_sessions.resolve(raw,t['conversation_id'])['revision'],shared_version=chat_sessions.shared_fingerprint(raw))
     t['pending_tool']=dict(call=deepcopy(call),request_id=request['request_id']);self._save(t);t.pop('pending_tool',None)
     result=self.store.mutate(request)['tool'];step['tool_calls'].append(dict(call=call,result=compact_result(result)));self._save(t)
     tool_results.append(chat_protocols.result_message(normalized,call['id'],compact_result(result),provider=self.spec['provider'],run_id=t['run']))
    messages=chat_models.continuation(self.spec,messages,response,tool_results)
    step['status']='tools_applied';self.journal.update(identifier,'completed',step);self._save(t)
   else:t.update(status='limit_reached',error='허용한 도구 회차에 도달했습니다. 저장된 결과를 검토하세요.');self._save(t)
  except Exception as exc:
   status='outcome_unknown' if unsettled_response else 'response_validation_failed' if received else 'outcome_unknown' if submitted else 'blocked_before_message'
   if attempt:
    metadata={'turn':t['id'],'messages_submitted':submitted}
    if unsettled_response:step['failure']={'stage':'response','category':'usage_unsettled'}
    if step.get('failure'):metadata['failure']=step['failure']
    if isinstance(exc,anthropic.ProposalError):
     failure=dict(stage={'preflight_started':'preflight','count_started':'count','message_started':'messages'}.get(step['status'],'response'),**anthropic.safe_failure(**exc.failure))
     step['failure']=failure;metadata['failure']=failure
    try:self.journal.update(attempt,status,metadata,release=not submitted)
    except Exception:
     # The journal may have failed before or after committing. Never assume a
     # reservation was released or usage settled; preserve the turn separately.
     status='outcome_unknown'
     step['journal_failure']={'stage':'journal','category':'update_failed'}
   error=('비용 원장 갱신 여부를 확인할 수 없습니다. 예약과 요청을 확인하세요. 자동 재시도하지 않습니다.'
          if attempt and step.get('journal_failure') else '요청을 안전하게 중단했습니다. 기존 결과·비용 상태를 확인하세요. 자동 재시도하지 않습니다.')
   t.update(status=status,error=error);self._save(t)
  self._close_run(t)
  return True
 def _close_run(self,t):
  with self.store.connect() as c:
   c.execute('BEGIN IMMEDIATE');revision,body=c.execute('SELECT revision,body FROM state').fetchone();state=json.loads(body)
   p=state['projects'].get(t['name']);run=next((r for r in p.get('production_runs',[]) if r['id']==t['run']),None) if p else None
   if run:
    run['state']=t['status'];run['live_model_called']=t['mode']!='contract-fake' and any(s.get('request_id') for s in t['steps'])
    c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state)))


class ChatRouter:
 """Trusted runtime map; the selected model resolves to exactly one adapter.
 Missing or unverified connections never silently route to another provider.
 """
 def __init__(self,store,configurations):
  self.store=store;self.runtimes={}
  for config in configurations:
   runtime=ChatRuntime(store,**config);key=runtime.spec['id']
   if key in self.runtimes:raise ValueError('duplicate chat connection')
   self.runtimes[key]=runtime
 def selected(self,p):
  selection=model_selection.resolve('chat',explicit=chat_sessions.selected_chat(p))['selection']
  runtime=self.runtimes.get(selection['id']) if selection else None
  if runtime is None:raise ValueError('selected chat connection unavailable; no fallback')
  return runtime
 def capability(self,name,p):
  try:return self.selected(p).capability(name,p)
  except ValueError:return dict(available=False,mode='disconnected',reason='선택한 채팅 모델의 연결·검증이 필요합니다.')
 def prepare(self,c,p,name,data):return self.selected(p).prepare(c,p,name,data)
 def process_next(self):
  for runtime in self.runtimes.values():
   if runtime.process_next():return True
  return False
