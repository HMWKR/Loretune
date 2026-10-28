"""One bounded answer completion of a verified synthetic tool roundtrip.

No Store writes, new plan, media generation, retries or model fallback. The
original tool results remain on disk; the wire receipt omits repeated context.
"""
import hashlib,json,sqlite3,sys
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import anthropic_ontology as provider
import chat_protocols
from scripts.anthropic_smoke import ROOT,credential,reserve
from scripts.claude_tool_eval import PROMPT

IDENTIFIER='claude-answer-v1-001'
SCHEMA={'type':'object','additionalProperties':False,'properties':{
 'global_coat':{'type':'string'},'studio_coat':{'type':'string'},
 'age':{'type':'string'},'global_changed':{'type':'boolean'},
 'plan_id':{'type':'string'},'plan_status':{'type':'string'},
 'approved':{'type':'boolean'},'generated':{'type':'boolean'},'paid':{'type':'boolean'},
 'evidence':{'type':'array','items':{'type':'object','additionalProperties':False,
   'properties':{'source_id':{'type':'string'},'excerpt':{'type':'string'}},'required':['source_id','excerpt']}}
},'required':['global_coat','studio_coat','age','global_changed','plan_id','plan_status','approved','generated','paid','evidence']}

def build(trace):
 if len(trace)<2 or any(r['state']!='verified_roundtrip' for r in trace[:2]):raise ValueError('verified tools required')
 if [r['tool']['name'] for r in trace[:2]]!=['search_project_context','propose_media_plan']:raise ValueError('tool sequence')
 messages=[{'role':'user','content':PROMPT}]
 for row in trace[:2]:
  blocks=row['visible_response'];uses=[b for b in blocks if b['type']=='tool_use']
  if len(uses)!=1:raise ValueError('one tool required')
  result=row['tool_result']
  if row['tool']['name']=='propose_media_plan':
   p=result['plan'];result={'status':result['status'],'plan':{k:p[k] for k in ['id','version','status','scenes','questions']},'cost_approval':False}
  messages.extend([{'role':'assistant','content':blocks}, {'role':'user','content':[{'type':'tool_result','tool_use_id':uses[0]['id'],'content':json.dumps(result,ensure_ascii=False)}]}])
 tools=[t for t in chat_protocols.tool_definitions('anthropic') if t['name'] in {'search_project_context','propose_media_plan'}]
 return dict(model=provider.MODEL,max_tokens=4096,messages=messages,tools=tools,tool_choice={'type':'none'},
   system='Complete the factual answer from these actual synthetic server tool results. Canon is server owned. Return concise JSON only. Use English coat names and age "unknown" when absent. Evidence must quote the exact approved source text. A saved proposal is not approval, generation or payment. Do not infer missing facts.',
   output_config={'effort':'low','format':{'type':'json_schema','schema':SCHEMA}})

def verify(answer,trace):
 p=trace[1]['tool_result']['plan'];facts=trace[0]['tool_result']['context']['snapshot']
 sources={f['id']:f['text'] for f in facts}
 allowed={(k,v) for k,v in sources.items()}
 for entity in trace[0]['tool_result']['context'].get('ontology',{}).get('graph',{}).get('entities',[]):
  allowed.update((s['source_id'],s['excerpt']) for s in entity.get('provenance',[]))
 def colour(value,expected):return type(value) is str and value.strip().casefold() in {expected,expected+' coat'}
 evidence=answer.get('evidence',[])
 checks={
  'global_coat':colour(answer.get('global_coat'),'blue'),
  'scoped_coat':colour(answer.get('studio_coat'),'red') and answer.get('global_changed') is False,
  'unknown_age':answer.get('age')=='unknown',
  'actual_plan_receipt':answer.get('plan_id')==p['id'] and answer.get('plan_status')=='proposed',
  'no_authority_or_generation_claim':all(answer.get(k) is False for k in ['approved','generated','paid']),
  'exact_sources':type(evidence) is list and all(type(e) is dict for e in evidence)
     and set(sources).issubset({e.get('source_id') for e in evidence})
     and all((e.get('source_id'),e.get('excerpt')) in allowed for e in evidence),
  'no_foreign_data':'gold coat' not in json.dumps(answer).lower()
 }
 return checks

def execute(folder,budget_path,trace_path,env_path,*,count=None,message=None,key_supplier=None):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 trace=json.loads(Path(trace_path).read_text());body=build(trace)
 digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
 report={'state':'reserved','input_sha256':digest,'model':provider.MODEL,'reserved_usd':'0.002458',
   'max_input_tokens':4096,'max_output_tokens':4096,'automatic_retries':0,'billing_confirmed':False,'messages_submitted':False,
   'scope':'synthetic existing tool results only; no new plan or media job'}
 db=sqlite3.connect(budget_path);key=None;headers=None
 try:
  reserve(db,IDENTIFIER,digest,2458)
  def save():
   db.execute('UPDATE trials SET state=?,metadata=? WHERE id=?',(report['state'],json.dumps(report),IDENTIFIER));db.commit()
   (folder/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
  save();(folder/'request.json').write_text(json.dumps(body,ensure_ascii=False,indent=2))
  key=(key_supplier or credential)(env_path)
  headers={'x-api-key':key,'anthropic-version':'2023-06-01','content-type':'application/json'}
  report['state']='count_started';save()
  counted=(count or provider.BoundedCountTransport())(provider.BoundedCountTransport.endpoint,headers,{k:v for k,v in body.items() if k!='max_tokens'})
  tokens=counted.get('input_tokens');report['input_tokens_counted']=tokens
  if type(tokens) is not int or not 0<=tokens<=4096:raise ValueError('input token limit')
  report.update(state='message_started',messages_submitted=True);save()
  response=(message or provider.BoundedMessagesTransport(timeout=60))(provider.ENDPOINT,headers,body)
  report.update(state='response_received',request_id=response.get('_request_id'),stop_reason=response.get('stop_reason'))
  usage=response.get('usage',{})
  if any(type(usage.get(k)) is not int or usage[k]<0 for k in ['input_tokens','output_tokens']):raise ValueError('usage unavailable')
  cost=(Decimal(usage['input_tokens'])*Decimal('.1')+Decimal(usage['output_tokens'])*Decimal('.5'))/1000000
  report.update(usage={k:usage[k] for k in ['input_tokens','output_tokens']},usage_cost_usd=str(cost))
  db.execute('UPDATE trials SET actual_micro=? WHERE id=?',(int((cost*1000000).to_integral_value(rounding=ROUND_CEILING)),IDENTIFIER));db.commit();save()
  if response.get('stop_reason')!='end_turn':raise ValueError('incomplete answer')
  text=''.join(b.get('text','') for b in response.get('content',[]) if b.get('type')=='text')
  if key in text:raise ValueError('sensitive output')
  answer=json.loads(text);checks=verify(answer,trace)
  (folder/'answer.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2))
  report.update(output_sha256=hashlib.sha256(text.encode()).hexdigest(),checks=checks,state='verified' if all(checks.values()) else 'semantic_failed');save()
 except Exception as exc:
  if 'save' in locals():
   report['error_class']=type(exc).__name__
   if str(exc) in ['input token limit','usage unavailable','incomplete answer','sensitive output']:report['error_code']=str(exc)
   if not report['messages_submitted']:
    report['state']='blocked_before_message';db.execute('UPDATE trials SET held_micro=0 WHERE id=?',(IDENTIFIER,))
   else:report['state']='response_validation_failed' if report['state']=='response_received' else 'unknown'
   save()
  else:raise
 finally:key=None;headers=None;db.close()
 return report

if __name__=='__main__':
 if sys.argv[1:]!=['--execute-approved-final-answer']:raise SystemExit('explicit approved flag required')
 result=execute(ROOT/'docs/qa/claude-grounding-20261025',ROOT/'docs/qa/anthropic-smoke-20261025/usage.sqlite3',
   ROOT/'docs/qa/claude-tool-eval-20261025-diagnostic/trace.json',ROOT/'.env')
 print(json.dumps({k:v for k,v in result.items() if k in ['state','request_id','usage_cost_usd','checks','input_tokens_counted','error_class','error_code']}))
