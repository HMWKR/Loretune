"""Three bounded live Messages turns against a synthetic, isolated Store only."""
import sys,json,sqlite3,hashlib,uuid
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Store
import anthropic_ontology as provider
import chat_protocols
from scripts.anthropic_smoke import credential,reserve,ROOT

FACTS=[dict(id='canon-mira-v1',text='Mira wears a blue coat by default.',scope='global',revision=1,approved=True),
       dict(id='song-A-exception-v1',text='Only in Song A studio scene, Mira wears a red coat. This does not replace her global blue coat.',scope='song-A',revision=1,approved=True)]
PROMPT=('Use the server context tool first; canon is owned by the server. This is synthetic Song A. '
        'Answer the approved global coat, the Song A exception, and whether Mira age is known. '
        'Do not access another project or invent missing facts. After context lookup, propose a one-scene studio plan '
        'using the local plan tool. The plan is a proposal only: never claim approval, generation or payment. '
        'Finally report only sourced facts and explicitly unknown age, and the actual saved plan ID.')

def fixture(folder):
 st=Store(Path(folder)/'store')
 def call(action,data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 call('project',dict(name='Synthetic Song A',era='default',story=0))
 call('project',dict(name='Foreign Song B',era='default',story=0))
 with st.connect() as c:
  state=json.loads(c.execute('SELECT body FROM state').fetchone()[0])
  state['projects']['Synthetic Song A']['snapshot']=FACTS
  graph=json.loads((ROOT/'docs/qa/anthropic-smoke-20261025/ontology-eval-002/proposal.json').read_text())
  state['projects']['Synthetic Song A']['ontology_snapshot']=dict(revision=1,graph=graph,origin='approved synthetic fixture for isolated evaluation')
  state['projects']['Foreign Song B']['snapshot']=[dict(id='foreign-secret',text='Mira wears a gold coat only in foreign project.',approved=True)]
  c.execute('UPDATE state SET body=?',(json.dumps(state),))
 run=call('production_run',{'song':'Synthetic Song A'})['run']['id']
 return st,call,run

def execute(folder,budget_path,env_path,*,count=None,message=None,key_supplier=None,batch='01'):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 st,call,run=fixture(folder)
 trace=[];messages=[dict(role='user',content=PROMPT)]
 definitions=[t for t in chat_protocols.tool_definitions('anthropic') if t['name'] in {'search_project_context','propose_media_plan'}]
 for t in definitions:
  t['strict']=True
  if t['name']=='propose_media_plan':t['input_schema']['properties']['kind']['enum']=['narrative','performance','visualizer']
 key=(key_supplier or credential)(env_path)
 headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
 count=count or provider.BoundedCountTransport();message=message or provider.BoundedMessagesTransport(timeout=60)
 db=sqlite3.connect(budget_path)
 try:
  for round_index,tool in enumerate(['search_project_context','propose_media_plan',None],1):
   body=dict(model=provider.MODEL,max_tokens=4096,system='Operate only on approved synthetic server context. Never fabricate facts, authority or work completion.',messages=messages,tools=definitions,tool_choice={'type':'tool','name':tool} if tool else {'type':'none'})
   digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest();identifier='claude-tools-representative-'+str(round_index) if batch=='01' else 'claude-tools-diagnostic-'+str(round_index)
   reserve(db,identifier,digest,2458)
   entry=dict(round=round_index,input_sha256=digest,model=provider.MODEL,state='count_started',reserved_usd='0.002458',billing_confirmed=False)
   trace.append(entry)
   def save():
    db.execute('UPDATE trials SET state=?,metadata=? WHERE id=?',(entry['state'],json.dumps(entry),identifier));db.commit()
    (folder/'trace.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2))
   save()
   tokens=count(provider.BoundedCountTransport.endpoint,headers,{k:v for k,v in body.items() if k!='max_tokens'})['input_tokens']
   if type(tokens) is not int or not 0<=tokens<=4096:raise ValueError('token limit')
   entry.update(input_tokens_counted=tokens,state='message_started');save()
   response=message(provider.ENDPOINT,headers,body)
   usage=response['usage'];cost=(Decimal(usage['input_tokens'])*Decimal('.1')+Decimal(usage['output_tokens'])*Decimal('.5'))/1000000
   entry.update(request_id=response.get('_request_id'),message_id=response.get('id'),stop_reason=response.get('stop_reason'),usage={k:usage[k] for k in ['input_tokens','output_tokens']},usage_cost_usd=str(cost),state='received')
   db.execute('UPDATE trials SET actual_micro=? WHERE id=?',(int((cost*1000000).to_integral_value(rounding=ROUND_CEILING)),identifier));db.commit();save()
   visible=[b for b in response.get('content',[]) if b.get('type') in {'text','tool_use'}]
   if key in json.dumps(visible):raise ValueError('sensitive output')
   entry['visible_response']=visible;entry['output_sha256']=hashlib.sha256(json.dumps(visible,sort_keys=True).encode()).hexdigest();save()
   if tool:
    normalized=chat_protocols.normalize('anthropic',response,run)
    if len(normalized['calls'])!=1 or normalized['calls'][0]['name']!=tool:raise ValueError('unexpected tool selection')
    tool_call=normalized['calls'][0]
    before=st.state()['revision'];result=call('production_tool',dict(song='Synthetic Song A',run=run,call=tool_call))['tool']
    replay=call('production_tool',dict(song='Synthetic Song A',run=run,call=tool_call))['tool']
    entry.update(tool=tool_call,tool_result=result,db_revision_before=before,db_revision_after=st.state()['revision'],idempotent_result=result==replay)
    if result['status'] not in {'succeeded','proposed'}:raise ValueError('local tool blocked')
    # Same-provider protocol blocks remain in memory only. Never log thinking.
    messages.append(dict(role='assistant',content=response['content']))
    messages.append(chat_protocols.result_message(normalized,tool_call['id'],result,provider='anthropic',run_id=run))
   else:
    if response['stop_reason']!='end_turn':raise ValueError('incomplete answer')
    answer='\n'.join(b['text'] for b in response['content'] if b['type']=='text')
    if key in answer:raise ValueError('sensitive output')
    (folder/'answer.txt').write_text(answer)
    entry['output_sha256']=hashlib.sha256(answer.encode()).hexdigest()
   entry['state']='verified_roundtrip' if tool else 'answer_received';save()
  snapshot=st.state();p=snapshot['projects']['Synthetic Song A']
  (folder/'db-result.json').write_text(json.dumps(dict(plan_count=len(p['guided_plans']),plans=p['guided_plans'],run=p['production_runs'][-1],foreign_plan_count=len(snapshot['projects']['Foreign Song B'].get('guided_plans',[])),external_media_calls=0),ensure_ascii=False,indent=2))
 except Exception as exc:
  if trace:
   entry.update(state='response_validation_failed' if entry['state']=='received' else 'blocked_or_unknown',error_class=type(exc).__name__)
   if str(exc) in {'INVALID_TOOL_ARGUMENTS','TOOL_NOT_ALLOWED','unexpected tool selection','incomplete answer','token limit','local tool blocked'}:entry['error_code']=str(exc)
   save()
  raise RuntimeError('bounded synthetic tool evaluation stopped; inspect redacted trace; no retry') from None
 finally:key=None;headers=None;db.close()
 return trace

if __name__=='__main__':
 if sys.argv[1:]!=['--execute-approved-diagnostic']:raise SystemExit('explicit approval flag required')
 try:
  result=execute(ROOT/'docs/qa/claude-tool-eval-20261025-diagnostic',ROOT/'docs/qa/anthropic-smoke-20261025/usage.sqlite3',ROOT/'.env',batch='02')
  print(json.dumps([dict(round=x['round'],state=x['state'],request_id=x.get('request_id'),usage_cost_usd=x.get('usage_cost_usd')) for x in result]))
 except Exception:raise SystemExit('Stopped safely; redacted trace retained; no automatic retry') from None
