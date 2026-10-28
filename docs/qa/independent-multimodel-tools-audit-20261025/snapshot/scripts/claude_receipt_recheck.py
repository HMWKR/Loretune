"""One approved actual answer check; existing synthetic receipt, no writes/tools/retry."""
import hashlib,json,sqlite3,sys
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import anthropic_ontology as a,chat_runtime,action_execution,production_tools
from scripts.anthropic_smoke import ROOT,credential
SOURCE=ROOT/'docs/qa/claude-chat-ui-live-20261025'
OUT=ROOT/'docs/qa/claude-receipt-recheck-20261025'
ID='claude-receipt-recheck-20261025-001'
SCHEMA=a.obj({'plan_id':a.TEXT,'plan_revision':{'type':'integer'},'job_id':a.TEXT,'release_id':a.TEXT,'take':{'type':'integer'},'sha256':a.TEXT,'result_approved':{'type':'boolean'},'external_calls':{'type':'integer'},'global_coat':a.TEXT,'studio_coat':a.TEXT,'global_changed':{'type':'boolean'},'age':a.TEXT,'evidence':a.EVIDENCE})

def build():
 info=json.loads((SOURCE/'runtime.json').read_text());gate=json.loads((SOURCE/'phase2-gate.json').read_text())
 with sqlite3.connect('file:'+info['data']+'/studio.sqlite3?mode=ro',uri=True) as c:
  p=json.loads(c.execute('SELECT body FROM state').fetchone()[0])['projects'][info['name']]
  jobs=action_execution.project_jobs(c,gate['approval']['workspace_id'],gate['approval']['project_id'],info['name'])
 run=production_tools.begin(p)
 receipt=production_tools.execute(p,run['id'],dict(id='receipt-read-only',name='get_generation_job',arguments={'job_id':gate['job']},complete=True),jobs=jobs)
 assert receipt['job']['mode']=='rehearsal' and receipt['job']['external_calls']==0
 candidates=[]
 for path in SOURCE.glob('request-*.json'):
  body=json.loads(path.read_text())['public_request']
  if 'get_generation_job' in [t['name'] for t in body['tools']] and len(body['messages'])==3:candidates.append(body)
 if len(candidates)!=1:raise ValueError('ambiguous prior synthetic tool exchange')
 body=candidates[0];uses={b['id']:b['name'] for b in body['messages'][1]['content'] if b['type']=='tool_use'}
 for block in body['messages'][2]['content']:
  if uses[block['tool_use_id']]=='get_generation_job':block['content']=json.dumps(receipt,ensure_ascii=False)
 body.update(max_tokens=4096,tool_choice={'type':'none'},system='Answer only from these actual synthetic canonical and persisted job tool results. Return concise JSON. Use English blue/red coat and age unknown. Preserve global versus song-scoped facts. Quote exact provenance source_id/excerpt pairs. The job is a local rehearsal, not paid media generation. Do not infer missing facts.',output_config={'effort':'low','format':{'type':'json_schema','schema':SCHEMA}})
 return body,receipt,p

def verify(answer,receipt,p):
 j=receipt['job'];take=j['registered_takes'][0]
 allowed={(v['source_id'],v['excerpt']) for e in p['ontology_snapshot']['graph']['entities'] for v in e['provenance']}
 return {'plan_and_revision':answer.get('plan_id')==j['plan_id'] and answer.get('plan_revision')==j['plan_revision'],
 'job_release_take_hash':all(answer.get(k)==v for k,v in [('job_id',j['id']),('release_id',j['release_id']),('take',take['take']),('sha256',take['sha256'])]),
 'approval_and_external_calls':answer.get('result_approved') is False and answer.get('external_calls')==0,
 'scope_and_unknown':answer.get('global_coat','').lower() in ['blue','blue coat'] and answer.get('studio_coat','').lower() in ['red','red coat'] and answer.get('global_changed') is False and answer.get('age')=='unknown',
 'exact_provenance':isinstance(answer.get('evidence'),list) and bool(answer['evidence']) and {(x.get('source_id'),x.get('excerpt')) for x in answer['evidence']}==allowed}

def execute():
 body,receipt,p=build();OUT.mkdir(exist_ok=False)
 digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest();journal=chat_runtime.UsageJournal(SOURCE.parent/'anthropic-smoke-20261025/usage.sqlite3')
 journal.reserve(ID,digest,ID,2868,2868,{'id':'claude-receipt-recheck-20261025','cap_micro':50000})
 report=dict(state='reserved',input_sha256=digest,model=a.MODEL,max_input_tokens=8192,max_output_tokens=4096,reserved_usd='0.002868',stage_cap_usd='0.05',prior_usage_usd='0.0072619',billing_confirmed=False,messages_submitted=False,retries=0)
 def save():
  journal.update(ID,report['state'],report);(OUT/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 adapter=chat_runtime.AnthropicChatAdapter(lambda name:credential(ROOT/'.env'),enabled=True)
 try:
  (OUT/'request.json').write_text(json.dumps(body,ensure_ascii=False,indent=2));(OUT/'actual-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));save()
  counted=adapter.count(body);report['input_tokens_counted']=counted
  if type(counted) is not int or not 0<=counted<=8192:raise ValueError('input_cap')
  report.update(state='message_started',messages_submitted=True);save()
  result=adapter.complete(body);report.update(state='response_received',request_id=result.get('_request_id'),stop_reason=result.get('stop_reason'))
  usage=result.get('usage',{});assert all(type(usage.get(k)) is int and usage[k]>=0 for k in ['input_tokens','output_tokens'])
  cost=(Decimal(usage['input_tokens'])*Decimal('.1')+Decimal(usage['output_tokens'])*Decimal('.5'))/1000000
  report.update(usage={k:usage[k] for k in ['input_tokens','output_tokens']},usage_cost_usd=str(cost),cumulative_usage_usd=str(Decimal('.0072619')+cost))
  journal.update(ID,'response_received',report,actual=int((cost*1000000).to_integral_value(rounding=ROUND_CEILING)));save()
  if result['stop_reason']!='end_turn':raise ValueError('incomplete')
  text=''.join(b.get('text','') for b in result.get('content',[]) if b['type']=='text');answer=json.loads(text);checks=verify(answer,receipt,p)
  (OUT/'answer.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2));report.update(state='verified' if all(checks.values()) else 'semantic_failed',checks=checks,output_sha256=hashlib.sha256(text.encode()).hexdigest());save()
 except Exception as exc:
  report['error_class']=type(exc).__name__
  report['state']='response_validation_failed' if report['state']=='response_received' else 'unknown' if report['messages_submitted'] else 'blocked_before_message'
  journal.update(ID,report['state'],report,release=not report['messages_submitted']);save()
 return report
if __name__=='__main__':
 if sys.argv[1:]!=['--execute-approved-receipt-check']:raise SystemExit('explicit execution flag required')
 r=execute();print(json.dumps(r,ensure_ascii=False))
