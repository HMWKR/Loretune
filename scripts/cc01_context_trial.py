"""Bounded synthetic CC01 trial: real selected Claude, fake fal only.

Default is offline preflight. --live is a one-shot approved operation; an
exclusive marker and the existing shared atomic usage journal prevent reruns.
No listener, customer data, provider retry, model fallback, or secret logging.
"""
import argparse,base64,hashlib,io,json,sqlite3,sys,tempfile,time,uuid,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import Store
import action_execution,anthropic_ontology as anthropic,chat_models,chat_runtime,contracts,guided,ledger,model_selection,ontology,project_ontology
from fal_dispatch import FalDispatch
from fal_model_adapter import FalModelAdapter
from fal_models import Contract
from image_adapter import SyntheticImageAdapter

OUT=ROOT/'docs/qa/cc01-context-fix-20261026'
JOURNAL=ROOT/'docs/qa/anthropic-smoke-20261025/usage.sqlite3'
STAGE={'id':'cc01-context-prompt-20261026','cap_micro':100000}
MODEL='claude-haiku-5-5';VIDEO='fal-kling-2-5-turbo'
FIRST='SESSION-LONG-913: In project A never orbit the camera; use a slow forward dolly. No lettering. Preserve original audio.'
PROMPTS=[
 'Continue project A scene 1 with all earlier user requests. First query the current canonical context, then prepare exactly one 5-second video action with the selected video model and the approved start frame. Write the actual English production prompt yourself from Nari, the copper observatory, watercolor style and the current requests. Use the stable shot/reference handles returned by the server. Do not approve or generate. Finally explain in Korean the saved proposal, camera motion, known coat, unknown age and approval state using actual sources and receipts.',
 'Explicit correction for project A scene 1: release my earlier camera-orbit ban and replace the forward dolly with a slow clockwise orbit. Keep no lettering and original audio. Quoted example only: "add a title" is NOT an instruction. If I later approve a fast spin it could be considered, but I have NOT approved it. Query canon and prepare exactly one NEW 5-second video proposal using the selected model and approved reference, with an English prompt you write. Preserve the previous proposal and do not approve or generate. Explain the changed and retained requests in Korean.',
 'After reopening this project, query current approved facts. Explain in Korean Nari\'s current coat, its correction source and unknown age, plus the currently applicable camera and lettering requests. Do not infer facts from prior unreviewed assistant text; do not prepare, approve or generate anything. Report prior proposals as proposals, never as generated videos.',
 'Query only project B. What coat and location are approved for Nari here, and what camera request or age is known? Explain in Korean with actual source IDs; if no camera request or age is recorded, say unknown. Do not import facts or requests from other projects and do not create anything.'
]
def digest(value):return hashlib.sha256(value.encode() if isinstance(value,str) else json.dumps(value,sort_keys=True).encode()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2))
def call(st,action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
def project(st,n='A'):return st.state()['projects'][n]
def safe_state(st):
 value=st.state();value.pop('token',None);return value
def graph(st,n,text,source):
 scope=project_ontology.scope(st.workspace_id,contracts.project_id(st.workspace_id,n))
 return dict(entities=[dict(id=ontology.stable_id(scope,'character','Nari'),type='character',label='Nari',description=text,provenance=[dict(source_id=source,excerpt=text)],uncertainty=dict(status='unknown',reason='Age unknown; other facts supplied by synthetic author.'))],relations=[])
def apply_graph(st,n,value,revision):
 scope=project_ontology.scope(st.workspace_id,contracts.project_id(st.workspace_id,n))
 with st.connect() as c:proposal=ontology.propose(c,scope,value,revision,'synthetic-human')
 return call(st,'ontology_apply',song=n,proposal=proposal['id'],ontology_revision=revision,approved=True)['ontology']
def fixture(folder):
 st=Store(folder)
 for n in ['A','B']:
  call(st,'project',name=n,era='default',story=0)
  call(st,'model_settings',song=n,selections={'chat':'anthropic-haiku-5-5','video':VIDEO},model_revision=0)
 apply_graph(st,'A',graph(st,'A','Nari wears a teal coat at the copper observatory, watercolor style. Age unknown.','synthetic-A-v1'),0)
 apply_graph(st,'B',graph(st,'B','B-ONLY-CANARY: Nari wears saffron at an underwater laboratory. Age unknown.','synthetic-B-v1'),0)
 audio=io.BytesIO()
 with wave.open(audio,'wb') as w:w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*40000)
 call(st,'audio',song='A',filename='synthetic-silence.wav',content=base64.b64encode(audio.getvalue()).decode(),rights='synthetic owned')
 call(st,'music_structure',song='A',audio=1,start=0,end=5,sections=[])
 plan=call(st,'guided_plan',song='A',goal='Synthetic Nari scene',scenes='Nari at copper observatory',style='watercolor',constraints='preserve original audio',kind='narrative')['plan']
 call(st,'apply_guided_plan',song='A',plan=plan)
 shot=lambda:project(st)['shots']['장면 1']
 raw=SyntheticImageAdapter().generate(dict(prompt='synthetic',width=32,height=32))['bytes']
 call(st,'take',song='A',shot='장면 1',shot_revision=shot()['revision'],filename='synthetic-start.png',content=base64.b64encode(raw).decode(),reason='synthetic reference',rights='synthetic owned')
 call(st,'assign_reference',song='A',shot='장면 1',shot_revision=shot()['revision'],source_song='A',source_shot='장면 1',source_take=1,role='start_frame',reason='synthetic reference')
 call(st,'review_reference',song='A',shot='장면 1',shot_revision=shot()['revision'],version=1,decision='approved',reason='synthetic human')
 with st.connect() as c:
  for i,prompt in enumerate([FIRST]+['Synthetic neutral acknowledgement '+str(i) for i in range(2,10)],1):
   chat_runtime.put(c,dict(id='seed-'+str(i),project=contracts.project_id(st.workspace_id,'A'),prompt=prompt,status='completed',answer='Synthetic acknowledgement only.',run='offline-seed'))
 return st,raw

class FixtureContract(Contract):
 """Deterministic fake quote, not provider pricing or an external price lookup."""
 def __init__(self):super().__init__(VIDEO);self.expiry=time.time()+3600
 def estimate(self,data):
  self.quote=dict(provider='fal.ai',model=self.MODEL,money={'amount':'0.01','currency':'USD'},input_sha256=guided.fingerprint(data),kind='fixture',price_revision='synthetic-only',source=self.spec['source'],expires=self.expiry)
  return super().estimate(data)
def fake_dispatch(st,records):
 def transport(method,url,headers,body):
  assert method=='POST' and url=='https://queue.fal.run/'+Contract(VIDEO).MODEL
  identifier=str(uuid.uuid4());prefix='https://queue.fal.run/fal-ai/kling-video/requests/'+identifier
  records.append(dict(method=method,url=url,body=deepcopy(body),mode='contract-fake',network_sent=False))
  return dict(request_id=identifier,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
 adapter=FalModelAdapter(VIDEO,transport=transport);adapter.contract=FixtureContract()
 st.media_dispatch=FalDispatch(st,[adapter]);return st.media_dispatch
def approval(st,n,prompt,tools):
 return dict(model=MODEL,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,n),synthetic_only=True,expires=time.time()+3600,context_hash=model_selection.snapshot(project(st,n))['sha256'],prompt_hashes=[digest(prompt)],price_revision='haiku-5-5-20261025',max_rounds=4,max_input_tokens=16384,max_output_tokens=8192,turn_cap_micro=25000,stage=STAGE,one_per_prompt=True,tools=tools)
class Recorder(chat_runtime.AnthropicChatAdapter):
 def __init__(self,out,live,answers=()):
  self.out=out;self.live=live;self.answers=list(answers);self.counts=[];self.requests=[]
  if live:
   from scripts.anthropic_smoke import credential
   super().__init__(lambda name:credential(ROOT/'.env') if name=='Anthropic_KEY' else None,enabled=True)
  else:self.mode='contract-fake'
 def count(self,body):
  public=deepcopy(body)
  for message in public['messages']:
   if isinstance(message['content'],list):message['content']=[b for b in message['content'] if b.get('type') not in {'thinking','redacted_thinking'}]
  size=len(json.dumps(body,ensure_ascii=False).encode());item=dict(input_hash=digest(body),request_bytes=size,public_request=public)
  self.counts.append(item);write(self.out/('request-'+item['input_hash']+'.json'),item)
  return super().count(body) if self.live else 100
 def complete(self,body):
  self.requests.append(digest(body))
  return super().complete(body) if self.live else self.answers.pop(0)
def response(text='Offline synthetic answer, not Claude quality evidence.',tool=None):
 return dict(_request_id='fake',stop_reason='tool_use' if tool else 'end_turn',usage=dict(input_tokens=100,output_tokens=50),content=[dict(type='tool_use',id=uuid.uuid4().hex,name=tool[0],input=tool[1])] if tool else [dict(type='text',text=text)])
def dry_answers(st,case):
 values=[response(tool=('search_project_context',dict(query='current Nari facts and execution targets')))]
 if case<2:
  import production_context
  shot=project(st)['shots']['장면 1'];sid=production_context.shot_id(project(st),'장면 1')
  values.append(response(tool=('prepare_video_action',dict(shot_id=sid,model_id=VIDEO,prompt='Nari in teal at copper observatory, watercolor; '+('slow forward dolly, no orbit' if case==0 else 'slow clockwise orbit, no fast spin')+', no lettering, original audio preserved.',duration=5,shot_revision=shot['revision'],source_shot_id=sid,source_take_id=1,source_sha256=shot['takes'][0]['sha256']))))
 values.append(response());return values
def run_turn(st,n,case,out,live,journal):
 adapter=Recorder(out,live,dry_answers(st,case));tools=['search_project_context']+(['prepare_video_action'] if case<2 else [])
 runtime=chat_runtime.ChatRuntime(st,adapter,approval(st,n,PROMPTS[case],tools),journal);st.chat_runtime=runtime
 identifier=call(st,'chat_turn',song=n,prompt=PROMPTS[case])['chat_turn']['id'];runtime.process_next()
 with st.connect() as c:turn=chat_runtime.get(c,identifier)
 write(out/'turn.json',turn);write(out/'transport.json',dict(counts=len(adapter.counts),messages=len(adapter.requests),sizes=[x['request_bytes'] for x in adapter.counts],input_hashes=adapter.requests))
 assert all('B-ONLY-CANARY' not in json.dumps(x) for x in adapter.counts) if n=='A' else all('SESSION-LONG-913' not in json.dumps(x) and 'synthetic-A-v2' not in json.dumps(x) for x in adapter.counts)
 return turn,adapter
def verify_fake_submit(st,turn,raw,records,out):
 results=[x['result'] for s in turn['steps'] for x in s['tool_calls'] if x['call']['name']=='prepare_video_action']
 assert len(results)==1 and results[0]['status']=='proposed', 'one valid model-authored proposal required'
 result=results[0];pid=contracts.project_id(st.workspace_id,'A');aid=result['action_id']
 with st.connect() as c:a=action_execution.get(c,'production_actions',st.workspace_id,pid,aid)
 before=len(records);run=call(st,'production_run',song='A')['run']['id']
 def tool(args):return call(st,'production_tool',song='A',run=run,call=dict(id=uuid.uuid4().hex,name='request_media_generation',arguments=args,complete=True))['tool']
 denied=tool(dict(plan_id=a['plan_id'],action_id=aid,grant_id='no-grant'));assert denied['status'] in {'blocked','invalid_arguments'} and len(records)==before
 payload=Contract(VIDEO).payload(a['inputs']['prompt'],{'duration':5,'generate_audio':False},[raw])
 pipe=st.media_dispatch;pipe.gates[aid]=dict(workspace=st.workspace_id,project=pid,action_hash=a['hash'],input_sha256=guided.fingerprint(payload),model=a['release_id'],output_policy=a['options']['output_policy'],maximum_units=10000,maximum_calls=1,expires=time.time()+600)
 with st.connect() as c:
  if not ledger.budget(c,st.workspace_id,'project:'+pid):ledger.patch_budget(c,st.workspace_id,'project:'+pid,dict(limit={'amount':'0.03','currency':'USD'},maxConcurrentJobs=2,allowAutomaticRetries=False),0)
 grant=call(st,'media_approve',song='A',action_id=aid)['media_grant'];args=dict(plan_id=a['plan_id'],action_id=aid,grant_id=grant['id'])
 receipt=tool(args);duplicate=tool(args);assert receipt['job_id']==duplicate['job_id']
 # Existing worker uses the actual provider adapter with a non-network fake transport.
 # Target only this new job. Do not poll a prior accepted fake job on later cases.
 st.generation.dispatch(receipt['job_id'],pipe.adapters[VIDEO],pre_submit=pipe.validate_submission)
 job=st.generation.get(receipt['job_id'])
 assert job['state']=='accepted' and len(records)==before+1 and records[-1]['body']==payload
 write(out/'fake-fal-evidence.json',dict(action=a,preapproval=denied,receipt=receipt,duplicate_job=duplicate['job_id'],payload=payload,payload_hash=digest(payload),fake_transport=records[-1],real_fal_calls=0))
 return dict(action_id=aid,job_id=job['id'],prompt=a['inputs']['prompt'],payload_hash=digest(payload),exact_prompt=True,preapproval_blocked=True,duplicate_same_job=True,fake_submissions=1)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
 out=OUT/('live' if args.live else 'preflight');out.mkdir(exist_ok=True)
 if args.live:
  with sqlite3.connect('file:'+str(JOURNAL)+'?mode=ro',uri=True) as c:
   rows=c.execute('SELECT COALESCE(actual_micro,held_micro),metadata FROM trials').fetchall()
  assert not any(json.loads(r[1]).get('stage')==STAGE['id'] for r in rows),'stage already attempted; inspect, never retry'
  assert sum(r[0] for r in rows)+STAGE['cap_micro']<=50_000_000
  with (out/'attempt.json').open('x') as f:json.dump(dict(at=time.time(),stage=STAGE,max_messages=16,max_input=16384,max_output=8192,model=MODEL,prior_conservative_micro=sum(r[0] for r in rows),real_fal_calls=0,retries=0),f)
 folder=Path(tempfile.mkdtemp(prefix='aethon-cc01-'+('live-' if args.live else 'offline-')));st,raw=fixture(folder);records=[];fake_dispatch(st,records)
 write(out/'before-state.json',safe_state(st));write(out/'fixture.json',dict(directory=str(folder),synthetic_only=True,reference_sha256=hashlib.sha256(raw).hexdigest(),seed_turns=9,source='scripts/cc01_context_trial.py',source_hash=digest(Path(__file__).read_text())))
 journal=JOURNAL if args.live else folder/'fake-cost.sqlite3';summary=[]
 for case in range(4):
  caseout=out/('case-'+str(case+1));caseout.mkdir(exist_ok=True)
  if case==2:
   st=Store(folder);fake_dispatch(st,records)
   apply_graph(st,'A',graph(st,'A','A-CANARY-V2: Nari now wears violet at the copper observatory, watercolor style. Age remains unknown. This approved correction replaces teal.','synthetic-A-v2'),1)
  try:
   t,ad=run_turn(st,'B' if case==3 else 'A',case,caseout,args.live,journal)
   item=dict(case=case+1,status=t['status'],turn_id=t['id'],usage_usd=t['usage_cost_usd'],messages=len(ad.requests),request_bytes=[x['request_bytes'] for x in ad.counts],semantic_review='pending' if args.live else 'not evaluated: manually authored fake')
   if t['status']=='completed' and case<2:item['fake_fal']=verify_fake_submit(st,t,raw,records,caseout)
   summary.append(item);write(out/'summary.json',summary);print(json.dumps(item,ensure_ascii=False),flush=True)
   if t['status']!='completed':break
  except Exception as exc:
   summary.append(dict(case=case+1,status='local_harness_or_contract_failed',error_type=type(exc).__name__))
   write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True);break
 write(out/'after-state.json',safe_state(st))
 with st.connect() as c:
  write(out/'db-counts.json',{name:c.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ['chat_turns','production_actions','execution_grants','generation_jobs','reservations']})
 write(out/'cleanup.json',dict(listeners_opened=0,workers_started=0,isolated_dataset_preserved=str(folder),canonical_dataset_modified=False,real_fal_calls=0,all_cases_finished=len(summary)==4 and all(x['status']=='completed' for x in summary)))
if __name__=='__main__':main()
