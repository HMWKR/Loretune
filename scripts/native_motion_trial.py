"""Single bounded synthetic Claude trial. Default is offline preparation only.

No fal, customer files, generated-code execution, listener, retry or fallback.
Local-owner review steps below are explicit synthetic test actions, never AI grants.
"""
import argparse,base64,hashlib,json,sqlite3,subprocess,sys,tempfile,time,uuid
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import Store
from scripts.cc01_context_trial import Recorder,call,digest,write,safe_state,response
import chat_runtime,contracts,editing,model_selection,motion_scene,motion_renderer,production_context

OUT=ROOT/'docs/qa/native-motion-20261026'
JOURNAL=ROOT/'docs/qa/anthropic-smoke-20261025/usage.sqlite3'
STAGE={'id':'native-motion-edit-20261026','cap_micro':75000}
MODEL='claude-haiku-5-5'
PROMPTS=[
 'Synthetic test: query current project context, then propose exactly one original motion scene for shot 모션. You author all composition, colors, positions and timing. Use exactly three stable layers: title text "새로운 리듬", bar rectangle, dot circle. Four seconds, 1920x1080, 24fps, 96 frames. Title font_size 80 and textbox at least 800x150; keep visible content within canvas. Font system-ko-regular for all layers, shapes text empty. Give title and bar visible intervals 0..96 and animate their opacity or position. Give dot interval in_frame=0,out_frame=72, and at least two moving keyframes at frame 0 and frame 60, with no keys later than 60, so a future 12-frame shift fits. Use supported keyframes and easing only. Do not approve, render or execute code. After saved tool receipt explain in Korean what you proposed and that it still needs human approval.',
 'Query the current approved motion version in shot 모션. Propose a new version that delays ONLY the dot circle by exactly 12 frames: add 12 to its in_frame, out_frame and every keyframe frame. Preserve every other dot value, and all scene settings, title and bar byte-for-byte as data. Do not move positions, change color/text, approve or render. Explain the actual saved proposal and unchanged layers in Korean after the tool receipt.',
 'Query current project timeline. Propose, do not apply, exactly these three changes using propose_timeline_changes: reorder all three base clips to 3 → 1 → 2 (zero-based order [2,0,1]); replace all captions with 0..1 seconds "시작", 1..2 seconds "움직임", 2..3 seconds "완성"; keep original audio version 1 but start from source offset 1 second. Preserve all clip Takes, trims and durations, and other settings. Do not approve or render. Explain the saved proposal in Korean; changing cut order does not automatically move captions.'
]
def p(st):return st.state()['projects']['A']
def act(st,a,**d):return call(st,a,song='A',**d)
def tool_result(turn,name):
 results=[x['result'] for step in turn['steps'] for x in step['tool_calls'] if x['call']['name']==name]
 assert len(results)==1 and results[0]['status']=='proposed','exactly one valid proposal required'
 return results[0]
def fixture():
 folder=Path(tempfile.mkdtemp(prefix='aethon-native-motion-'));st=Store(folder)
 call(st,'project',name='A',era='default',story=0)
 act(st,'model_settings',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
 act(st,'shot',shot='모션',description='Synthetic Korean motion composition: text, rectangle and circle; no customer data.')
 return st
def run_turn(st,case,out,live):
 out.mkdir();answers=[]
 if not live:
  if case<2:
   from tests.test_motion import scene
   value=scene() if case==0 else deepcopy(p(st)['shots']['모션']['motion_versions'][-1]['scene'])
   dot=value['layers'][2]
   if case==0:dot['out_frame']=72;dot['keyframes'].append(dict(frame=60,x=1000,y=680,opacity=1,easing='linear'))
   else:
    dot['in_frame']+=12;dot['out_frame']+=12
    for key in dot['keyframes']:key['frame']+=12
   args=dict(shot_id=production_context.shot_id(p(st),'모션'),base_motion_revision=p(st)['shots']['모션'].get('motion_head',0),scene=value);tool='propose_motion_scene'
  else:
   args=dict(description='합성 편집',timeline_version=p(st)['timeline_head'],commands=[dict(op='reorder_clips',order=[2,0,1]),dict(op='set_captions',cues=[dict(start=i,end=i+1,text=s) for i,s in enumerate(['시작','움직임','완성'])]),dict(op='set_audio_offset',audio_version=1,source_offset_seconds=1)]);tool='propose_timeline_changes'
  answers=[response(tool=('search_project_context',dict(query='current project execution targets'))),response(tool=(tool,args)),response()]
 adapter=Recorder(out,live,answers)
 if not live:adapter.preflight=__import__('anthropic_ontology').BoundedMessagesTransport(max_request_bytes=65536).encode_body
 tools=['search_project_context','propose_motion_scene' if case<2 else 'propose_timeline_changes']
 approval=dict(model=MODEL,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,'A'),synthetic_only=True,expires=time.time()+900,context_hash=model_selection.snapshot(p(st))['sha256'],prompt_hashes=[digest(PROMPTS[case])],price_revision='haiku-5-5-20261025',max_rounds=3,max_input_tokens=16384,max_output_tokens=8192,turn_cap_micro=18000,stage=STAGE,one_per_prompt=True,tools=tools)
 runtime=chat_runtime.ChatRuntime(st,adapter,approval,JOURNAL if live else st.root/'fake-usage.sqlite3');st.chat_runtime=runtime
 turn_id=act(st,'chat_turn',prompt=PROMPTS[case])['chat_turn']['id'];runtime.process_next()
 with st.connect() as c:turn=chat_runtime.get(c,turn_id)
 write(out/'turn.json',turn);write(out/'transport.json',dict(count_calls=len(adapter.counts),messages=len(adapter.requests),input_hashes=adapter.requests,request_bytes=[x['request_bytes'] for x in adapter.counts],private_thinking_removed_from_public_request=True))
 assert turn['status']=='completed','provider turn not completed: '+turn['status']
 return turn
def approve_render(st,result,out):
 assert not p(st)['shots']['모션']['takes'] or p(st)['shots']['모션']['selected'] is None
 act(st,'motion_review',proposal_id=result['proposal_id'],decision='approved')
 v=p(st)['shots']['모션']['motion_versions'][-1]
 args=dict(shot_id=production_context.shot_id(p(st),'모션'),motion_revision=v['id'],grant_id=v['approval']['id'])
 receipt=act(st,'motion_render',**args)['motion'];assert act(st,'motion_render',**args)['motion']['job_id']==receipt['job_id']
 assert st.process_next();j=next(j for j in st.state()['jobs'] if j['id']==receipt['job_id']);write(out/'render.json',j)
 assert j['status']=='completed',j.get('error');assert p(st)['shots']['모션']['selected'] is None
 assert p(st)['shots']['모션']['takes'][-1]['rights']=='사용권 미확인'
 for frame in [0,12,24,36,48,60,72,84,95]:motion_renderer.frame(v['scene'],frame,out/f'frame-{frame:02}.png',st.root)
 return v,j
def setup_edit(st):
 # Human fixture review after inspecting motion; no automatic rights grant from model.
 shot=p(st)['shots']['모션'];act(st,'declare_take_rights',shot='모션',take=1,sha256=shot['takes'][0]['sha256'],shot_revision=shot['revision'],evidence='합성 검증용 직접 제작')
 act(st,'select',shot='모션',take=1,shot_revision=p(st)['shots']['모션']['revision'])
 act(st,'review_take',shot='모션',take=1,decision='approved',reason='synthetic human test review')
 for name,color in [('빨강','red'),('파랑','blue')]:
  path=st.root/(name+'.png');subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',f'color=c={color}:s=1920x1080','-frames:v','1',str(path)],check=True)
  act(st,'shot',shot=name,description='Synthetic '+color+' test card');act(st,'take',shot=name,shot_revision=0,filename=name+'.png',content=base64.b64encode(path.read_bytes()).decode(),reason='synthetic fixture',rights='직접 제작')
  act(st,'select',shot=name,take=1,shot_revision=1);act(st,'review_take',shot=name,take=1,decision='approved',reason='synthetic human')
 audio=st.root/'source-tone.wav';subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',r'aevalsrc=if(lt(t\,1)\,0\,0.25*sin(2*PI*440*t)):s=48000:d=8',str(audio)],check=True)
 act(st,'audio',filename=audio.name,content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 제작')
 t=editing.current(p(st));t.update(clips=[dict(shot=n,take=1,trim=0,duration=1) for n in ['모션','빨강','파랑']],audio=1,audio_offset=0,subtitles=[dict(start=0,end=3,text='수정 전')],profile='landscape')
 act(st,'timeline',timeline=t);act(st,'approve_timeline');return deepcopy(editing.current(p(st)))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--schema-corrected-live',action='store_true');parser.add_argument('--offline-fixture',action='store_true');args=parser.parse_args();assert sum([args.live,args.schema_corrected_live,args.offline_fixture])<=1
 corrected=args.schema_corrected_live;args.live=args.live or corrected
 prep=dict(model=MODEL,stage=STAGE,max_messages=9,max_input_tokens=16384,max_output_tokens=8192,max_round_cost_usd='0.0057344',max_nine_cost_usd='0.0516096',prompts=PROMPTS,prompt_hashes=list(map(digest,PROMPTS)),tools=['search_project_context','propose_motion_scene','propose_timeline_changes'],real_fal_calls=0,retries=0,synthetic_only=True)
 write(OUT/'trial-preflight.json',prep)
 if not (args.live or args.offline_fixture):print('Offline plan saved; no credentials or network used.');return
 out=OUT/(('live-schema-corrected' if corrected else 'live') if args.live else 'offline-'+str(int(time.time())));out.mkdir(exist_ok=True)
 if args.live:
  with sqlite3.connect('file:'+str(JOURNAL)+'?mode=ro',uri=True) as c:rows=c.execute('SELECT state,COALESCE(actual_micro,held_micro),metadata FROM trials').fetchall()
  prior=[r for r in rows if json.loads(r[2]).get('stage')==STAGE['id']]
  if corrected:
   # One explicit contract-corrected experiment, not an unknown-paid retry.
   # Old rows and attempt markers remain intact. Any prior Messages stops it.
   assert prior and all(r[0]=='blocked_before_message' and r[1]==0 and json.loads(r[2]).get('messages_submitted') is False for r in prior),'prior stage not proven unsubmitted'
   diagnostic=json.loads((OUT/'count-followup/result.json').read_text())
   assert diagnostic['messages']==0 and diagnostic['failure']['http_status']==400
  else:assert not prior,'stage previously attempted; do not retry'
  assert sum(r[1] for r in rows)+STAGE['cap_micro']<=50_000_000
  with (out/'attempt.json').open('x') as f:json.dump(dict(prep,at=time.time(),prior_conservative_micro=sum(r[1] for r in rows)),f)
 st=fixture();write(out/'fixture.json',dict(directory=str(st.root),synthetic_only=True));write(out/'before-state.json',safe_state(st));summary=[]
 try:
  first=run_turn(st,0,out/'case-1',args.live);result=tool_result(first,'propose_motion_scene');original=deepcopy(result['scene']);motion_scene.validate(original)
  assert {x['id'] for x in original['layers']}=={'title','bar','dot'} and next(x for x in original['layers'] if x['id']=='title')['text']=='새로운 리듬'
  v1,j1=approve_render(st,result,out/'case-1');old_hash=j1['sha256'];summary.append(dict(case=1,status='passed',turn=first['id'],usage_usd=first['usage_cost_usd'],job=j1['id'],sha256=old_hash));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
  st=Store(st.root);assert p(st)['shots']['모션']['motion_versions'][0]==v1
  second=run_turn(st,1,out/'case-2',args.live);result2=tool_result(second,'propose_motion_scene');expected=deepcopy(original);dot=next(x for x in expected['layers'] if x['id']=='dot');dot['in_frame']+=12;dot['out_frame']+=12
  for key in dot['keyframes']:key['frame']+=12
  assert result2['scene']==expected,'Claude edit changed other fields or did not delay exactly 12 frames'
  v2,j2=approve_render(st,result2,out/'case-2');assert p(st)['shots']['모션']['motion_versions'][0]==v1
  assert hashlib.sha256(Path(p(st)['shots']['모션']['takes'][0]['asset']).read_bytes()).hexdigest()==old_hash
  summary.append(dict(case=2,status='passed',turn=second['id'],usage_usd=second['usage_cost_usd'],job=j2['id'],only_circle_shift_12=True,original_preserved=True));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
  restored=act(st,'motion_restore',shot_id=production_context.shot_id(p(st),'모션'),base_motion_revision=2,version=1)['motion'];act(st,'motion_review',proposal_id=restored['proposal_id'],decision='approved');assert p(st)['shots']['모션']['motion_versions'][-1]['scene']==original
  base=setup_edit(st);before=deepcopy(p(st));third=run_turn(st,2,out/'case-3',args.live);r=tool_result(third,'propose_timeline_changes');assert editing.current(p(st))==base
  proposal=next(x for x in p(st)['timeline_edit_proposals'] if x['id']==r['proposal_id']);t=proposal['timeline'];assert t['clips']==[base['clips'][i] for i in [2,0,1]];assert t['subtitles']==[dict(start=i,end=i+1,text=s) for i,s in enumerate(['시작','움직임','완성'])];assert t['audio']==1 and t['audio_offset']==1
  act(st,'review_timeline_proposal',proposal_id=r['proposal_id'],timeline_version=base['id'],decision='approved');act(st,'approve_timeline');j=act(st,'render_job')['job'];assert st.process_next();job=next(x for x in st.state()['jobs'] if x['id']==j);assert job['status']=='completed',job.get('error')
  write(out/'case-3'/'render.json',job);assert p(st)['shots']==before['shots'] and p(st)['audio_versions']==before['audio_versions']
  srt=(st.root/'exports'/(j+'.srt')).read_text();assert all(x in srt for x in ['시작','움직임','완성'])
  assert Store(st.root).state()['projects']['A']['timeline_head']==p(st)['timeline_head']
  summary.append(dict(case=3,status='passed',turn=third['id'],usage_usd=third['usage_cost_usd'],job=j,proposal_only_before_human=True,sources_preserved=True,output_sha256=job['sha256']));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
 except Exception as exc:
  summary.append(dict(status='stopped',error_type=type(exc).__name__,message=str(exc)[:240]));write(out/'summary.json',summary);print(json.dumps(summary[-1]),flush=True)
 finally:
  write(out/'after-state.json',safe_state(st));write(out/'cleanup.json',dict(listeners=0,subprocesses_remaining=0,canonical_data_touched=False,real_fal_calls=0,isolated_data=str(st.root)))
if __name__=='__main__':main()
