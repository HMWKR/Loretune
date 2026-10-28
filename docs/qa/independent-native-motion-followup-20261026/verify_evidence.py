from pathlib import Path
from copy import deepcopy
from decimal import Decimal,ROUND_CEILING
import json,hashlib,subprocess,datetime

out=Path(__file__).resolve().parent
root=out.parents[2];qa=root/'docs/qa/native-motion-20261026';live=qa/'live-schema-corrected'
read=lambda p:json.loads(p.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda v:sha(json.dumps(v,sort_keys=True).encode())
manifest=read(qa/'FOLLOWUP-MANIFEST.json');record={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[]}
def check(name,condition,**details):
 record['checks'].append(dict(name=name,status='PASS' if condition else 'FAIL',**details))

check('frozen_source_hashes',all(sha((root/n).read_bytes())==h for n,h in manifest['source'].items()),files=len(manifest['source']))
check('saved_artifact_hashes_excluding_database',all(sha((qa/n).read_bytes())==v['sha256'] for n,v in manifest['artifacts'].items() if not n.endswith('.sqlite3')),database_opened=False)
after=read(live/'after-state.json');p=after['projects']['A'];steps=[];turns=[];rehashable=0;request_links=0;call_matches=0;counted=messages=0;rounded=0
for n in (1,2,3):
 t=read(live/f'case-{n}/turn.json');turns.append(t);tr=read(live/f'case-{n}/transport.json');counted+=tr['count_calls'];messages+=tr['messages']
 check(f'case_{n}_completed_live_record',t['status']=='completed' and t['mode']=='anthropic-live' and t['model']=='claude-haiku-5-5')
 for s in t['steps']:
  steps.append(s);req=read(live/f'case-{n}'/('request-'+s['input_sha256']+'.json'));body=req['public_request']
  request_links+=req['input_hash']==s['input_sha256'] and s['input_sha256'] in tr['input_hashes']
  rehashable+=canonical(body)==s['input_sha256']
  check(f'case_{n}_round_{s["round"]}_visible_hash',canonical(s['visible_response'])==s['output_sha256'])
  check(f'case_{n}_round_{s["round"]}_wire_strict',all(x.get('strict') is True for x in body['tools']))
  cost=(Decimal(s['usage']['input_tokens'])*Decimal('.1')+Decimal(s['usage']['output_tokens'])*Decimal('.5'))/1000000
  rounded+=int((cost*1000000).to_integral_value(rounding=ROUND_CEILING))
  check(f'case_{n}_round_{s["round"]}_recorded_cost',cost==Decimal(s['usage_cost_usd']))
  for x in s['tool_calls']:
   matches=[b for b in s['visible_response'] if b.get('type')=='tool_use' and b['name']==x['call']['name'] and b['input']==x['call']['arguments']]
   call_matches+=len(matches)==1
   check(f'case_{n}_{x["call"]["name"]}_input_link',len(matches)==1)
  if n==2 and s['round']==2:
   results=[json.loads(b['content']) for m in body['messages'] if isinstance(m.get('content'),list) for b in m['content'] if b.get('type')=='tool_result']
   motion=next(x for x in results if 'execution_targets' in x)['execution_targets']['shots'][0]['motion']
   check('approval_handle_present_in_actual_last_request',motion['grant_id']==p['shots']['모션']['motion_versions'][0]['approval']['id'])
   record['narrative_input']={'motion_keys':list(motion),'revision':motion['revision'],'authority_fields_absent':all(k not in motion for k in ['actor','scope','approval','status']),'server_approval':p['shots']['모션']['motion_versions'][0]['approval']}
totals={k:sum(s['usage'][k] for s in steps) for k in ['input_tokens','output_tokens']}
total=sum(Decimal(t['usage_cost_usd']) for t in turns);prov=read(qa/'live-provenance.json')
record['provider']={'stored_responses':len(steps),'corrected_count_invocations':counted,'messages':messages,'linked_requests':request_links,'visible_tool_calls_linked':call_matches,'fully_rehashable_public_inputs':rehashable,'redacted_inputs':len(steps)-rehashable,'token_totals':totals,'recomputed_usage_usd':str(total),'sum_ceil_per_response_micro':rounded,'prior_usage_from_record_usd':prov['prior_usage_usd'],'aggregate_usage_usd':str(total+Decimal(prov['prior_usage_usd'])),'conservative_total_micro_record_only':prov['conservative_total_micro'],'stage_unknown_micro_record_only':prov['stage_unknown_held_micro'],'shared_ledger_opened':False,'billing_confirmed':False,'initial_count_invocations':1,'diagnostic_count_invocations':read(qa/'count-followup/result.json')['count_invocations'],'all_motion_count_invocations_in_records':1+1+counted}
check('usage_total_matches_report',total==Decimal(prov['this_usage_usd']))
check('request_ids_unique',len({s['request_id'] for s in steps})==9)

def tool(t,name):return next(x for s in t['steps'] for x in s['tool_calls'] if x['call']['name']==name)
motion=[]
for i in (1,2):
 x=tool(turns[i-1],'propose_motion_scene');scene=x['call']['arguments']['scene'];r=read(live/f'case-{i}/render.json');v=p['shots']['모션']['motion_versions'][i-1];proposal=next(a for a in p['motion_proposals'] if a['id']==x['result']['proposal_id']);take=p['shots']['모션']['takes'][i-1];motion.append(scene)
 check(f'case_{i}_authored_scene_to_version_job',scene==x['result']['scene']==proposal['scene']==v['scene']==r['motion']['scene'])
 check(f'case_{i}_proposed_before_human',x['result']['applied'] is False and x['result']['rendered'] is False and proposal['reviews'][0]['actor']=='local-owner')
 check(f'case_{i}_authorship_provenance',v['source']['run']==turns[i-1]['run'] and v['source']['call']==x['call']['id'] and v['source']['mode']=='anthropic-live' and take['provenance']['source']==v['source'])
 check(f'case_{i}_take_file_binding',take['sha256']==r['sha256']==sha((qa/'artifacts'/f'claude-motion-v{i}.mp4').read_bytes()))
expected=deepcopy(motion[0]);dot=next(l for l in expected['layers'] if l['id']=='dot');dot['in_frame']+=12;dot['out_frame']+=12
for key in dot['keyframes']:key['frame']+=12
check('only_dot_exact_12_frame_edit',motion[1]==expected)
check('restore_keeps_three_immutable_versions',len(p['shots']['모션']['motion_versions'])==3 and p['shots']['모션']['motion_versions'][2]['scene']==motion[0] and p['shots']['모션']['motion_versions'][0]['scene']==motion[0])
third=tool(turns[2],'propose_timeline_changes');proposal=p['timeline_edit_proposals'][0];base=p['timeline_versions'][0];final=p['timeline_versions'][1];r=read(live/'case-3/render.json');expected=deepcopy(base);expected.pop('approval',None);expected['clips']=[base['clips'][i] for i in [2,0,1]];expected['subtitles']=[dict(start=i,end=i+1,text=t) for i,t in enumerate(['시작','움직임','완성'])];expected['audio_offset']=1
check('timeline_proposal_exact_expected',proposal['timeline']==expected and proposal['commands']==third['call']['arguments']['commands'])
final_without_authority={k:v for k,v in final.items() if k not in ['id','approval']};expected_without_id={k:v for k,v in expected.items() if k!='id'}
check('timeline_applied_version_matches_proposal',final_without_authority==expected_without_id and r['snapshot']['timeline']==final)
check('timeline_proposed_before_human',third['result']['applied'] is False and third['result']['output_approved'] is False and proposal['reviews'][0]['actor']=='local-owner')
record['edit_receipt']={'changes':third['result']['changes'],'commands':third['result']['commands'],'base_version':third['result']['base_version'],'applied':third['result']['applied'],'output_approved':third['result']['output_approved']}

record['media_metadata']=[]
for name in ['claude-motion-v1.mp4','claude-motion-v2.mp4','claude-edited-audio-captions.mp4']:
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(qa/'artifacts'/name)]))
 streams=[{k:s.get(k) for k in ['codec_type','codec_name','width','height','r_frame_rate','nb_read_frames','duration','sample_rate']} for s in data['streams']]
 record['media_metadata'].append({'file':name,'duration':data['format']['duration'],'streams':streams})
 check(name+'_metadata',streams[0]['width']==1920 and streams[0]['height']==1080 and streams[0]['r_frame_rate']=='24/1' and int(streams[0]['nb_read_frames'])==(72 if 'edited' in name else 96))
record['failed_checks']=[x['name'] for x in record['checks'] if x['status']=='FAIL']
(out/'evidence-checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(record['checks']),'failed':record['failed_checks'],'provider':record['provider']},ensure_ascii=False))
