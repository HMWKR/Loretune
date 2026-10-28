from pathlib import Path
from decimal import Decimal
import json,hashlib
HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'cc01-context-fix-20261026'
def load(p):return json.loads(p.read_text())
def digest(o):return hashlib.sha256(json.dumps(o,sort_keys=True).encode()).hexdigest()
provenance=load(SRC/'provider-provenance.json'); byid={p['request_id']:p for p in provenance}
checks=[]; usage=Decimal(0); inputs=outputs=0; reports=[]; allsteps=[]
for path in [*sorted((SRC/'live').glob('case-*/turn.json')),*sorted((SRC/'semantic-followup').glob('*/turn.json'))]:
 t=load(path); current=[]
 for step in t['steps']:
  rid=step['request_id'];p=byid[rid];req=load(path.parent/('request-'+step['input_sha256']+'.json'))
  cost=(Decimal(step['usage']['input_tokens'])*Decimal('.1')+Decimal(step['usage']['output_tokens'])*Decimal('.5'))/1000000
  check={'request_id':rid,'recorded_input_hash_links_match':step['input_sha256']==p['input_sha256']==req['input_hash'],'public_input_recomputable':digest(req['public_request'])==step['input_sha256'],'visible_output_hash_match':digest(step['visible_response'])==step['output_sha256']==p['output_sha256'],'usage_match':step['usage']==p['usage'],'count_match':step['input_tokens_counted']==p['counted_input'],'cost_match':cost==Decimal(step['usage_cost_usd'])==Decimal(p['usage_cost_usd']),'bytes_match':len(json.dumps(req['public_request'],ensure_ascii=False).encode())==req['request_bytes']}
  assert all(v for k,v in check.items() if k not in ['request_id','public_input_recomputable','bytes_match']),check
  if not check['public_input_recomputable']:check['limitation']='Prior provider thinking/redacted_thinking excluded by Recorder.count; original full request hash/byte count cannot be independently rebuilt from saved public body'
  assert len(json.dumps(req['public_request'],ensure_ascii=False).encode())<=req['request_bytes']
  checks.append(check);usage+=cost;inputs+=step['usage']['input_tokens'];outputs+=step['usage']['output_tokens'];allsteps.append(step);current.append(req['public_request'])
 h=t['handoff']['session_request_history'];assert h['digest']==digest({k:v for k,v in h.items() if k!='digest'})
 assert all(r['sequence']==i and r['source_hash']==hashlib.sha256(r['text'].encode()).hexdigest() for i,r in enumerate(h['requests'],1))
 wire=json.dumps(current,ensure_ascii=False)
 is_b=path.parent.name in ['case-4','B']
 assert ('SESSION-LONG-913' not in wire and 'synthetic-A-v2' not in wire) if is_b else 'B-ONLY-CANARY' not in wire
 reports.append({'file':str(path.relative_to(SRC)),'status':t['status'],'scope':h['scope'],'history_records':len(h['requests']),'history_integrity':True,'wire_isolation':True,'tool_names':[[x['call']['name'] for x in s['tool_calls']] for s in t['steps']],'semantic_followup_rules_in_request':all('Domain distinctions:' in x.get('system','') for x in current)})
fal=[]
for i in [1,2]:
 path=SRC/'live'/('case-'+str(i));t=load(path/'turn.json');e=load(path/'fake-fal-evidence.json')
 tool=[b for s in t['steps'] for b in s['visible_response'] if b['type']=='tool_use' and b['name']=='prepare_video_action'][0]
 authored=tool['input']['prompt'];assert authored==e['action']['inputs']['prompt']==e['payload']['prompt']==e['fake_transport']['body']['prompt']
 assert e['payload']==e['fake_transport']['body'] and digest(e['payload'])==e['payload_hash']
 assert e['real_fal_calls']==0 and e['fake_transport']['network_sent'] is False
 assert e['preapproval']['status'] in ['blocked','invalid_arguments'] and e['duplicate_job']==e['receipt']['job_id']
 fal.append({'case':i,'prompt_exact':True,'payload_exact':True,'wrong_grant_blocked':True,'duplicate_same_job':True,'network_sent':False,'model_id':tool['input']['model_id'],'prompt':authored})
write=load(SRC/'semantic-followup/write-boundary.json');assert write['before']==write['after']
summary={'basis':'Saved redacted records and source, not independent provider re-contact or invoice attestation','request_records':len(checks),'unique_request_ids':len(byid),'input_tokens':inputs,'output_tokens':outputs,'usage_cost_usd_at_recorded_rates':str(usage),'aggregate_with_recorded_prior_usd':str(usage+Decimal('.0077580')),'checks':checks,'turns':reports,'fake_fal':fal,'semantic_write_boundary_counts_match':True,'invoice_confirmed':False,'live_calls_by_this_audit':0}
assert len(checks)==14 and len(byid)==14
(HERE/'saved-evidence-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['checks','turns','fake_fal']},ensure_ascii=False,indent=2))
