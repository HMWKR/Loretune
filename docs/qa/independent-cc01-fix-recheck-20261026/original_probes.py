"""Independent synthetic probes. No real credentials, network, or shared Store."""
import base64,copy,hashlib,json,socket,sys,tempfile,time,traceback,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,json.loads((HERE/'snapshot-manifest.json').read_text())['snapshot'])
def denied(*a,**k):raise RuntimeError('AUDIT_OFFLINE_NETWORK_FORBIDDEN')
socket.socket.connect=socket.socket.connect_ex=socket.socket.bind=denied
socket.create_connection=denied
from app import Store
import action_execution,chat_runtime,chat_protocols,contracts,guided,ledger,model_selection,ontology,production_context,production_tools,project_ontology
from fal_models import Contract,CONNECTION
from fal_model_adapter import FalModelAdapter
from fal_dispatch import FalDispatch
from image_adapter import SyntheticImageAdapter

results=[]
def record(id,run):
 observed={}
 try:run(observed);status='PASS'
 except AssertionError as e:status='FAIL';observed['error']=str(e);observed['trace']=traceback.format_exc()
 except Exception as e:status='HARNESS_ERROR';observed['error']=repr(e);observed['trace']=traceback.format_exc()
 results.append(dict(id=id,status=status,observed=observed));print(id,status,flush=True)
def response(text='Synthetic acknowledgement; no model reasoning evaluated.',tools=None):
 return dict(_request_id='synthetic-response',stop_reason='tool_use' if tools else 'end_turn',usage=dict(input_tokens=100,output_tokens=50),content=tools or [dict(type='text',text=text)])
class Fake:
 mode='contract-fake'
 def __init__(self,answers=()):self.answers=list(answers);self.messages=[]
 def count(self,body):return 100
 def complete(self,body):self.messages.append(copy.deepcopy(body));return self.answers.pop(0) if self.answers else response()
def call(st,action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
def project(st,n='A'):return st.state()['projects'][n]
def approve_chat(st,n,prompts,adapter):
 approval=dict(model='claude-haiku-5-5',workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,n),synthetic_only=True,expires=time.time()+600,context_hash=model_selection.snapshot(project(st,n))['sha256'],prompt_hashes=[hashlib.sha256(p.encode()).hexdigest() for p in prompts],price_revision='haiku-5-5-20261025',max_rounds=3)
 runtime=chat_runtime.ChatRuntime(st,adapter,approval,st.root/'fake-cost.sqlite3');st.chat_runtime=runtime;return runtime
def turn(st,runtime,n,prompt):
 tid=call(st,'chat_turn',song=n,prompt=prompt)['chat_turn']['id'];runtime.process_next()
 with st.connect() as c:return chat_runtime.get(c,tid)
def entity(scope,kind,key,description,unknown=False):
 return dict(id=ontology.stable_id(scope,kind,key),type=kind,label=key,description=description,provenance=[dict(source_id='synthetic-'+key,excerpt=description)],uncertainty=dict(status='unknown' if unknown else 'asserted',reason='synthetic author fixture; no real person'))
def graph(st,n):
 scope=project_ontology.scope(st.workspace_id,contracts.project_id(st.workspace_id,n));m=entity(scope,'character','Nari','A-CANARY: Nari wears teal. Age unknown.',True);a=entity(scope,'asset','prop','A-CANARY: copper compass reference')
 return dict(entities=[m,a],relations=[dict(id=str(uuid.uuid4()),type='references',source=m['id'],target=a['id'],provenance=[dict(source_id='synthetic-relation',excerpt='Nari references copper compass.')])])
def apply_graph(st,n,g,rev):
 scope=project_ontology.scope(st.workspace_id,contracts.project_id(st.workspace_id,n))
 with st.connect() as c:proposal=ontology.propose(c,scope,g,rev,'synthetic-human')
 return call(st,'ontology_apply',song=n,proposal=proposal['id'],ontology_revision=rev,approved=True)['ontology']
def basic(folder):
 st=Store(folder)
 for n in ['A','B']:call(st,'project',name=n,era='default',story=0);call(st,'model_settings',song=n,selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
 return st

def context_probe(o):
 with tempfile.TemporaryDirectory() as folder:
  st=basic(folder);ga=graph(st,'A');first=apply_graph(st,'A',ga,0);gb=graph(st,'B');gb['entities'][0]['description']='B-ONLY-CANARY: Nari wears saffron in an underwater laboratory.';apply_graph(st,'B',gb,0)
  p1='A dialogue canary: SESSION-A-481. Please keep the camera fixed.';f=Fake([response('Previous unreviewed answer: teal coat.')]);r=approve_chat(st,'A',[p1],f);t1=turn(st,r,'A',p1);assert t1['status']=='completed'
  newer=copy.deepcopy(ga);newer['entities'][0]['description']='A-CANARY-V2: Nari wears violet now. Age remains unknown.';newer['entities'][0]['provenance']=[dict(source_id='author-correction-v2',excerpt=newer['entities'][0]['description'])];second=apply_graph(st,'A',newer,1)
  st=Store(folder);p2='Resume and use the newly approved coat. What is unknown?';f2=Fake([response(tools=[dict(type='tool_use',id='lookup',name='search_project_context',input={'query':'Nari current approved canon'})]),response()]);r2=approve_chat(st,'A',[p2],f2);t2=turn(st,r2,'A',p2);assert t2['status']=='completed'
  handoff=t2['handoff'];current=handoff['context']['value']['context']['ontology'];assert current==second;assert current['graph']['entities'][0]['id']==first['graph']['entities'][0]['id'];assert current['graph']['relations']==first['graph']['relations'];assert current['revision']==2
  assert any(m['text']==p1 for m in handoff['messages']);assert any(m.get('review')=='unreviewed' for m in handoff['messages']);assert 'B-ONLY-CANARY' not in json.dumps(f2.messages)
  lookup=t2['steps'][0]['tool_calls'][0]['result'];assert lookup['context']['ontology']==second;assert lookup['context']['ontology']['graph']['entities'][0]['uncertainty']['status']=='unknown'
  with st.connect() as c:
   scope=project_ontology.scope(st.workspace_id,contracts.project_id(st.workspace_id,'A'));old=json.loads(c.execute('SELECT body FROM ontology_versions WHERE scope=? AND revision=1',(scope,)).fetchone()[0]);assert old==ga
  fb=Fake();rb=approve_chat(st,'B',['B query'],fb);tb=turn(st,rb,'B','B query');assert 'SESSION-A-481' not in json.dumps(fb.messages);assert 'A-CANARY-V2' not in json.dumps(fb.messages)
  o.update(restartPreservesPriorUserTurn=True,canonicalRevision=current['revision'],stableEntityAndRelation=True,currentProvenance=current['graph']['entities'][0]['provenance'],oldVersionPreserved=True,priorAssistantMarkedUnreviewed=True,foreignCanaryExcludedBothWays=True,claudeQuality='NOT RUN; fake text proves app payload only')
  (HERE/'context-payload-evidence.json').write_text(json.dumps({'handoff':handoff,'lookup':lookup,'fakeProviderBody':f2.messages[0]},ensure_ascii=False,indent=2))

def history_probe(o):
 with tempfile.TemporaryDirectory() as folder:
  st=basic(folder);prompts=['SESSION-LONG-913: For this session never orbit the camera.']+['Synthetic neutral turn '+str(i) for i in range(2,10)]+['Continue the scene using all session constraints.'];f=Fake();r=approve_chat(st,'A',prompts,f)
  for prompt in prompts[:9]:assert turn(st,r,'A',prompt)['status']=='completed'
  st=Store(folder);f2=Fake();r2=approve_chat(st,'A',[prompts[-1]],f2);t=turn(st,r2,'A',prompts[-1]);wire=json.dumps(f2.messages,ensure_ascii=False)
  with st.connect() as c:saved=[json.loads(x[0]) for x in c.execute('SELECT body FROM chat_turns WHERE project=?',(contracts.project_id(st.workspace_id,'A'),))]
  o.update(persistedTurns=len(saved),retainedPriorUserTurns=[m['text'] for m in t['handoff']['messages'] if m['role']=='user'],canaryStillInDatabase=any('SESSION-LONG-913' in x['prompt'] for x in saved),canaryInProviderRequest='SESSION-LONG-913' in wire,summaryOrStructuredSessionConstraintsInHandoff=sorted(t['handoff'].keys()),expected='Session prohibition survives history compaction, even if original turn is omitted')
  (HERE/'long-history-evidence.json').write_text(json.dumps(o,ensure_ascii=False,indent=2))
  assert 'SESSION-LONG-913' in wire,'CC01: turn 1 session prohibition is absent after 9 completed turns; only last 8 are re-sent, no summary/constraint channel'

def session_probe(o):
 with tempfile.TemporaryDirectory() as folder:
  st=basic(folder);f=Fake();r=approve_chat(st,'A',['SESSION-X-335 local note','New separate session'],f);turn(st,r,'A','SESSION-X-335 local note')
  try:call(st,'chat_turn',song='A',prompt='New separate session',session_id='separate')
  except ValueError:rejected=True
  else:rejected=False
  assert rejected
  t=turn(st,r,'A','New separate session');assert 'SESSION-X-335' in json.dumps(t['handoff'])
  o.update(observation='One conversation per project; new session_id is not accepted; natural-language new session does not reset history',separateSessionApi=False,sameProjectPriorCanaryIncluded=True,classification='UNIMPLEMENTED/GAP, not cross-project leakage')

def conflict_probe(o):
 with tempfile.TemporaryDirectory() as folder:
  st=basic(folder);g=graph(st,'A');g['entities'][0]['description']='Two unresolved supplied claims: source X says silver coat; source Y says black coat. Age unknown.';g['entities'][0]['provenance']=[{'source_id':'X','excerpt':'Nari wears silver.'},{'source_id':'Y','excerpt':'Nari wears black.'}];apply_graph(st,'A',g,0)
  run=call(st,'production_run',song='A')['run']['id'];lookup=call(st,'production_tool',song='A',run=run,call=dict(id='context',name='search_project_context',arguments={'query':'Resolve conflicting coat claims; what is age?'},complete=True))['tool']
  returned=lookup['context']['ontology']['graph']['entities'][0];assert returned['provenance']==g['entities'][0]['provenance'];assert returned['uncertainty']['status']=='unknown'
  try:call(st,'ontology_propose',song='A',ontology_revision=0,kind='character',label='stale',description='stale fact',evidence='stale author source')
  except ValueError:stale=True
  else:stale=False
  assert stale
  o.update(bothSourceClaimsPreserved=True,uncertaintyStatus='unknown',staleRevisionRejected=True,applicationSemanticConflictResolution='not implemented by this path; model behavior requires live review',searchMode=lookup['search_mode'])

def pipeline_probe(o):
 import io,wave
 with tempfile.TemporaryDirectory() as folder:
  st=basic(folder);call(st,'model_settings',song='A',selections={'image':'fal-flux-pro-1-1','video':'fal-kling-2-5-turbo'},model_revision=1)
  audio=io.BytesIO()
  with wave.open(audio,'wb') as w:w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*40000)
  call(st,'audio',song='A',filename='synthetic.wav',content=base64.b64encode(audio.getvalue()).decode(),rights='synthetic owned');call(st,'music_structure',song='A',audio=1,start=0,end=5,sections=[])
  plan=call(st,'guided_plan',song='A',goal='Nari synthetic scene',scenes='Nari at copper observatory',style='watercolor',constraints='preserve song',kind='narrative')['plan'];call(st,'apply_guided_plan',song='A',plan=plan)
  shot='장면 1';sh=lambda:project(st)['shots'][shot];raw=SyntheticImageAdapter().generate(dict(prompt='synthetic',width=32,height=32))['bytes']
  call(st,'take',song='A',shot=shot,shot_revision=sh()['revision'],filename='synthetic-reference.png',content=base64.b64encode(raw).decode(),reason='synthetic selected reference',rights='synthetic owned')
  take=sh()['takes'][0];call(st,'assign_reference',song='A',shot=shot,shot_revision=sh()['revision'],source_song='A',source_shot=shot,source_take=1,role='start_frame',reason='synthetic selected reference');call(st,'review_reference',song='A',shot=shot,shot_revision=sh()['revision'],version=1,decision='approved',reason='synthetic human')
  prompt='Nari in violet coat, watercolor copper observatory at dawn; slow forward dolly, no orbit, no lettering, preserve identity and original audio.'
  key='fal-kling-2-5-turbo';contract=Contract(key);payload=contract.payload(prompt,{'duration':5,'generate_audio':False},[raw]);calls=[];rid=str(uuid.uuid4());prefix='https://queue.fal.run/fal-ai/kling-video/requests/'+rid
  quote=lambda data:dict(provider='fal.ai',model=contract.MODEL,money={'amount':'0.01','currency':'USD'},input_sha256=guided.fingerprint(data),kind='fixture',price_revision='synthetic-only-price',source=contract.spec['source'],expires=time.time()+300)
  def transport(method,url,headers,body):
   calls.append({'method':method,'url':url,'body':copy.deepcopy(body),'headers':'not recorded; synthetic adapter only'});return dict(request_id=rid,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
  adapter=FalModelAdapter(key,quote=quote(payload),transport=transport);pipe=FalDispatch(st,[adapter]);st.media_dispatch=pipe
  sid=production_context.shot_id(project(st),shot);args=dict(shot_id=sid,model_id=key,prompt=prompt,duration=5,shot_revision=sh()['revision'],source_shot_id=sid,source_take_id=1,source_sha256=take['sha256'])
  user='Nari를 수채화 새벽 구리 천문대에서 천천히 전진 촬영해줘. 궤도 회전과 글자는 금지하고 원곡을 보존해.'
  fake=Fake([response(tools=[dict(type='tool_use',id='prepare',name='prepare_video_action',input=args)]),response()]);runtime=approve_chat(st,'A',[user],fake);t=turn(st,runtime,'A',user);assert t['status']=='completed'
  result=t['steps'][0]['tool_calls'][0]['result'];assert result['status']=='proposed';assert result['approval']=='required';aid=result['action_id'];pid=contracts.project_id(st.workspace_id,'A')
  with st.connect() as c:
   a=action_execution.get(c,'production_actions',st.workspace_id,pid,aid);assert c.execute('SELECT count(*) FROM reservations').fetchone()[0]==0;assert c.execute('SELECT count(*) FROM generation_jobs').fetchone()[0]==0
  assert calls==[];assert a['inputs']['prompt']==prompt;assert a['release_id']==contract.MODEL
  run=call(st,'production_run',song='A')['run']['id']
  def tool(name,arguments,identifier=None):return call(st,'production_tool',song='A',run=run,call=dict(id=identifier or uuid.uuid4().hex,name=name,arguments=arguments,complete=True))['tool']
  pre=tool('request_media_generation',dict(plan_id=plan,action_id=aid,grant_id='not-a-grant'));assert pre['status'] in ['invalid_arguments','blocked'];assert calls==[]
  pipe.gates[aid]=dict(workspace=st.workspace_id,project=pid,action_hash=a['hash'],input_sha256=guided.fingerprint(payload),model=contract.MODEL,output_policy=a['options']['output_policy'],maximum_units=10000,maximum_calls=1,expires=time.time()+200)
  with st.connect() as c:ledger.patch_budget(c,st.workspace_id,'project:'+pid,dict(limit={'amount':'0.02','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
  grant=call(st,'media_approve',song='A',action_id=aid)['media_grant'];args_submit=dict(plan_id=plan,action_id=aid,grant_id=grant['id']);accepted=tool('request_media_generation',args_submit);again=tool('request_media_generation',args_submit);assert accepted['job_id']==again['job_id'];assert calls==[]
  st.process_generation();job=st.generation.get(accepted['job_id']);assert job['state']=='accepted';assert len(calls)==1;assert calls[0]['body']==payload;assert calls[0]['url']=='https://queue.fal.run/'+contract.MODEL
  with st.connect() as c:assert c.execute('SELECT count(*) FROM reservations').fetchone()[0]==1
  corrected='Nari in violet coat, watercolor copper observatory at dusk; locked camera, no dolly, no orbit, no lettering; original audio preserved.'
  revised_payload=contract.payload(corrected,{'duration':5,'generate_audio':False},[raw]);adapter.contract.quote=quote(revised_payload);args2=dict(args,prompt=corrected)
  revised=tool('prepare_video_action',args2);assert revised['status']=='proposed';assert revised['action_id']!=aid
  with st.connect() as c:
   assert action_execution.get(c,'production_actions',st.workspace_id,pid,aid)['inputs']['prompt']==prompt
   assert action_execution.get(c,'production_actions',st.workspace_id,pid,revised['action_id'])['inputs']['prompt']==corrected
  reused=tool('request_media_generation',dict(plan_id=plan,action_id=revised['action_id'],grant_id=grant['id']));assert reused['status'] in ['blocked','invalid_arguments'];assert len(calls)==1
  try:chat_protocols.normalize('anthropic',response(tools=[dict(type='tool_use',id='bad',name='prepare_video_action',input=dict(args,approved=True))]),run)
  except ValueError:unsupported=True
  else:unsupported=False
  assert unsupported
  o.update(naturalLanguageInput=user,fakeAuthoredPrompt=prompt,quality='NOT EVALUATED: fake response manually authored',modelSlots=model_selection.settings(project(st))['selections'],exactFalPayload=True,actualModelEndpoint=calls[0]['url'],referenceBytesHash=hashlib.sha256(raw).hexdigest(),preApprovalProviderCalls=0,postApprovalFakeSubmits=1,duplicateSameJob=True,reservations=1,correctedPromptNewAction=True,oldPromptImmutable=True,oldGrantCannotApproveCorrection=True,unsupportedAuthorityFieldRejected=True)
  # The reference is a locally generated synthetic PNG, not user media.
  (HERE/'prompt-payload-evidence.json').write_text(json.dumps({'modelToolArgs':args,'prepared':result,'fakeTransport':calls,'corrected':revised,'oldGrantRejection':reused},ensure_ascii=False,indent=2))

