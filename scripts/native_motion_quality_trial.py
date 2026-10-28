"""Bounded approval/receipt explanation recheck; default is offline preparation.

Reuses approved synthetic motion assets, not private customer material. No fal,
new render, automatic retry/fallback, listener, provider changes or upload.
"""
import argparse,base64,hashlib,json,sqlite3,sys,time
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.cc01_context_trial import Recorder,call,digest,write,safe_state,response
from scripts.native_motion_trial import fixture,p,act,setup_edit,JOURNAL,MODEL
import chat_runtime,contracts,editing,model_selection,production_context

OUT=ROOT/'docs/qa/native-motion-20261026/quality-fix'
STAGE=dict(id='native-motion-quality-20261026',cap_micro=100000)
PROMPTS=[
 '현재 합성 작품의 모션 장면을 서버에서 조회해 주세요. 저장된 모션 버전과 대기 중 변경안 각각에 대해 승인 주체, 승인 범위, 적용 버전과 아직 필요한 검토를 한국어로 설명해 주세요. 이 승인이 최종 영상 납품까지 허용하는지와 지금 렌더할 수 있다고 확정할 수 있는지도 구분해 주세요. 온톨로지 유무를 모션 승인 여부와 혼동하지 말고 조회된 근거만 쓰세요. 새 제안·승인·렌더·적용은 하지 마세요.',
 '현재 타임라인을 조회한 다음 변경안 하나를 저장해 주세요. 세 컷을 3→1→2 순서로 바꾸고, 전체 자막을 0–1초 "시작", 1–2초 "움직임", 2–3초 "완성"으로 교체하세요. 원음 버전1은 유지하고 원곡 시작점을1초로 바꿔 주세요. 각 컷의 Take, trim, duration과 나머지 설정은 유지하세요. 적용·승인·렌더는 하지 마세요. 저장 후 서버가 계산한 영수증을 바탕으로 각 before/after와 그대로인 항목, 현재 적용·출력 승인 상태를 한국어로 설명해 주세요.'
]

class BoundedRecorder(Recorder):
 def __init__(self,out,live,answers,counter):super().__init__(out,live,answers);self.counter=counter
 def complete(self,body):
  if self.counter['messages']>=6:raise ValueError('stage response limit')
  self.counter['messages']+=1
  return super().complete(body)

def project_invariants(st):
 value=deepcopy(p(st))
 for key in ['production_runs','conversation','timeline_edit_proposals','chat_connection','chat_turns']:value.pop(key,None)
 return value

def run(st,case,out,live,counter):
 out.mkdir();tools=['search_project_context']+(['propose_timeline_changes'] if case==1 else [])
 answers=[response(tool=('search_project_context',dict(query='current execution targets and approval state')))]
 if case==1:answers.append(response(tool=('propose_timeline_changes',dict(description='synthetic quality check',timeline_version=p(st)['timeline_head'],commands=[dict(op='reorder_clips',order=[2,0,1]),dict(op='set_captions',cues=[dict(start=i,end=i+1,text=t) for i,t in enumerate(['시작','움직임','완성'])]),dict(op='set_audio_offset',audio_version=1,source_offset_seconds=1)]))))
 answers.append(response())
 adapter=BoundedRecorder(out,live,answers,counter)
 if not live:adapter.preflight=__import__('anthropic_ontology').BoundedMessagesTransport(max_request_bytes=65536).encode_body
 approval=dict(model=MODEL,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,'A'),synthetic_only=True,expires=time.time()+900,context_hash=model_selection.snapshot(p(st))['sha256'],prompt_hashes=[digest(PROMPTS[case])],price_revision='haiku-5-5-20261025',max_rounds=3,max_input_tokens=16384,max_output_tokens=8192,turn_cap_micro=18000,stage=STAGE,one_per_prompt=True,max_turns=2,tools=tools)
 runtime=chat_runtime.ChatRuntime(st,adapter,approval,JOURNAL if live else st.root/'fake-quality-usage.sqlite3');st.chat_runtime=runtime
 before=project_invariants(st);identifier=act(st,'chat_turn',prompt=PROMPTS[case])['chat_turn']['id'];runtime.process_next()
 with st.connect() as c:turn=chat_runtime.get(c,identifier)
 write(out/'turn.json',turn);write(out/'transport.json',dict(count_calls=len(adapter.counts),messages=len(adapter.requests),input_hashes=adapter.requests,private_thinking_removed=True))
 assert turn['status']=='completed',turn['status']
 assert project_invariants(st)==before,'source/canonical/approval state mutated'
 assert st.state()['jobs']==[],'unexpected render'
 calls=[x for step in turn['steps'] for x in step['tool_calls']]
 assert any(x['call']['name']=='search_project_context' for x in calls),'missing server lookup'
 if case==0:
  assert all(x['call']['name']=='search_project_context' for x in calls)
  motion=next(x for x in calls if x['call']['name']=='search_project_context')['result']['execution_targets']['shots'][0]['motion']
  assert motion['approval_status']=='recorded' and motion['approval']['motion_revision']==1 and motion['approval']['requires_revalidation']
  assert len(motion['proposals'])==1 and motion['proposals'][0]['status']=='proposed'
 else:
  results=[x['result'] for x in calls if x['call']['name']=='propose_timeline_changes'];assert len(results)==1
  r=results[0];assert r['status']=='proposed' and not r['applied'] and not r['output_approved']
  d=r['timeline_diff'];assert d['clip_order']==dict(changed=True,before=[0,1,2],after=[2,0,1])
  assert d['clips']==[] and d['captions']['before']==[dict(start=0,end=3,text='수정 전')]
  assert d['captions']['after']==[dict(start=i,end=i+1,text=t) for i,t in enumerate(['시작','움직임','완성'])]
  assert d['audio']==dict(changed=True,before=dict(version=1,source_offset_seconds=0),after=dict(version=1,source_offset_seconds=1))
 return dict(case=case+1,contract_result='passed',answer_quality='pending_manual_review' if live else 'not_live',turn=identifier,count_calls=len(adapter.counts),messages=len(adapter.requests),usage_usd=turn['usage_cost_usd'])

def main():
 parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group();g.add_argument('--live',action='store_true');g.add_argument('--offline-fixture',action='store_true');args=parser.parse_args()
 plan=dict(model=MODEL,endpoint='https://api.anthropic.com/v1/messages',count_endpoint='https://api.anthropic.com/v1/messages/count_tokens',stage=STAGE,max_messages=6,max_input_tokens=16384,max_output_tokens=8192,max_response_usd='0.0057344',max_six_usd='0.0344064',aggregate_cap_usd=50,prompts=PROMPTS,prompt_hashes=list(map(digest,PROMPTS)),synthetic_only=True,retries=0,fallbacks=0,fal_calls=0)
 if not(args.live or args.offline_fixture):write(OUT/'trial-plan.json',plan);print('Offline plan only; no credential/network use.');return
 out=OUT/('live' if args.live else 'offline-'+str(int(time.time())));out.mkdir(exist_ok=True)
 if args.live:
  with sqlite3.connect('file:'+str(JOURNAL)+'?mode=ro',uri=True) as c:rows=c.execute('SELECT COALESCE(actual_micro,held_micro),metadata FROM trials').fetchall()
  assert not any(json.loads(r[1]).get('stage')==STAGE['id'] for r in rows),'stage already attempted; inspect, never retry'
  assert sum(r[0] for r in rows)+STAGE['cap_micro']<=50_000_000
  with (out/'attempt.json').open('x') as f:json.dump(dict(plan,at=time.time(),prior_conservative_micro=sum(r[0] for r in rows)),f)
 st=fixture();counter={'messages':0};summary=[]
 try:
  original=json.loads((ROOT/'docs/qa/native-motion-20261026/live-schema-corrected/case-1/render.json').read_text())['motion']['scene']
  edited=deepcopy(original);dot=next(x for x in edited['layers'] if x['id']=='dot');dot['in_frame']+=12;dot['out_frame']+=12
  for key in dot['keyframes']:key['frame']+=12
  sid=production_context.shot_id(p(st),'모션')
  proposed=act(st,'motion_propose',shot_id=sid,base_motion_revision=0,scene=original)['motion'];act(st,'motion_review',proposal_id=proposed['proposal_id'],decision='approved')
  act(st,'motion_propose',shot_id=sid,base_motion_revision=1,scene=edited)
  write(out/'fixture.json',dict(directory=str(st.root),synthetic_only=True,prior_claude_scene_sha256=digest(original)));write(out/'before-state.json',safe_state(st))
  summary.append(run(st,0,out/'case-1',args.live,counter));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
  raw=(ROOT/'docs/qa/native-motion-20261026/artifacts/claude-motion-v1.mp4').read_bytes()
  act(st,'take',shot='모션',shot_revision=p(st)['shots']['모션']['revision'],filename='synthetic-prior-claude.mp4',content=base64.b64encode(raw).decode(),reason='Reuse approved synthetic trial asset; no new generation',rights='직접 제작')
  setup_edit(st);write(out/'before-edit-state.json',safe_state(st))
  summary.append(run(st,1,out/'case-2',args.live,counter));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
 except Exception as exc:
  summary.append(dict(status='stopped',error_type=type(exc).__name__))
  write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
 finally:
  write(out/'after-state.json',safe_state(st));write(out/'cleanup.json',dict(listeners=0,canonical_data_touched=False,real_fal_calls=0,messages=counter['messages'],isolated_data=str(st.root)))
if __name__=='__main__':main()
