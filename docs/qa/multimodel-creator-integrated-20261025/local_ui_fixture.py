"""Bounded synthetic local UI QA; no network provider/credentials. Not app configuration."""
import sys,json,base64,uuid,time,hashlib,subprocess,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import app,chat_runtime,contracts,model_selection,editing
OUT=Path(__file__).parent;DATA=Path('/tmp/loretune-ms-qa-20261025');NAME='QA 통합 제작 20261025';PROMPT='합성 검증: Mira wears a blue coat. 두 장면 계획과 첫 컷 편집 변경안, Mira 설정 변경 제안을 저장해 주세요.'
st=app.Store(DATA)
def call(a,**d):
 d.setdefault('song',NAME);return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
if NAME not in st.state()['projects']:
 call('project',name=NAME,era='default',story=0)
 for color,name in [('blue','옥상'),('orange','스튜디오')]:
  file=OUT/(color+'.png');subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c='+color+':s=640x360','-frames:v','1','-y',str(file)],check=True)
  call('shot',shot=name,description='합성 '+name+' 장면');call('take',shot=name,shot_revision=0,filename=file.name,content=base64.b64encode(file.read_bytes()).decode(),reason='테스트 미디어 · synthetic fixture',rights='검증용 직접 제작');call('select',shot=name,take=1,shot_revision=1);call('review_take',shot=name,take=1,decision='approved',reason='합성 파일 검토')
 wave=OUT/'synthetic.wav';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=5','-y',str(wave)],check=True)
 call('audio',filename='synthetic.wav',content=base64.b64encode(wave.read_bytes()).decode(),rights='합성 테스트 음원')
 call('music_structure',audio=1,start=0,end=2,sections=[])
 p=st.state()['projects'][NAME];t=editing.current(p);t.update(audio=1,audio_offset=0,profile='preview',subtitles=[dict(start=0,end=1.5,text='Mira의 합성 자막')]);[c.update(duration=1) for c in t['clips']];call('timeline',timeline=t);call('approve_timeline')
 call('model_settings',selections={'chat':'anthropic-haiku-5-5','image':'fal-flux-schnell','video':'fal-kling-2-6-pro'},model_revision=0)
class Fake:
 mode='contract-fake'
 def __init__(self):self.messages=[]
 def count(self,body):return 200
 def complete(self,body):
  self.messages.append(body);n=len(self.messages)
  def use(id,name,args):return dict(type='tool_use',id=id,name=name,input=args)
  if n==1:blocks=[use('lookup','search_project_context',{'query':'현재 작품의 승인된 제작 대상과 출처'})]
  elif n==2:
   result=json.loads(body['messages'][-1]['content'][0]['content']);targets=result['execution_targets'];source=next(s for s in result['sources'] if 'Mira wears a blue coat.' in s['text']);clip=targets['timeline']['clips'][0]
   blocks=[use('plan','propose_media_plan',dict(goal='Mira의 두 장면',scenes='Mira가 옥상에서 하늘을 바라본다\nMira가 스튜디오에서 음악을 듣는다',style='청색과 따뜻한 조명',constraints='파란 코트 유지',kind='narrative')),use('edit','propose_timeline_edit',dict(description='첫 컷의 시작점만 0.125초로 조정',timeline_version=targets['timeline']['version'],changes=[dict(clip_index=0,take=clip['take'],trim=.125,duration=clip['duration'])])),use('memory','propose_memory_update',dict(description='Mira는 이 작품에서 파란 코트를 입는다.',kind='character',label='Mira',entity_id='',source_id=source['id'],excerpt='Mira wears a blue coat.',ontology_revision=targets['ontology_revision']))]
  elif n==3:
   receipts=[json.loads(x['content']) for x in body['messages'][-1]['content']];assert all(x['status']=='proposed' for x in receipts)
   blocks=[dict(type='text',text='두 장면 계획, 첫 컷 편집 변경안과 Mira 설정 변경 제안을 저장했습니다. 모두 검토 전이며 아직 적용하거나 영상을 생성하지 않았습니다. 기존 음원·자막·다른 컷은 유지됩니다.')]
  else:raise AssertionError('bounded fake fixture exhausted')
  return dict(_request_id='synthetic-ui-'+str(n),stop_reason='end_turn' if n==3 else 'tool_use',usage=dict(input_tokens=200,output_tokens=200),content=blocks)
server=app.server(DATA,8773);p=server.store.state()['projects'][NAME]
# Exact prompt/project/context, same normal runtime validation; fake transport only.
approval=dict(model='claude-haiku-5-5',workspace_id=server.store.workspace_id,project_id=contracts.project_id(server.store.workspace_id,NAME),synthetic_only=True,expires=time.time()+3600,context_hash=model_selection.snapshot(p)['sha256'],prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],price_revision='haiku-5-5-20261025',max_rounds=3,one_per_prompt=True)
server.store.chat_runtime=chat_runtime.ChatRuntime(server.store,Fake(),approval,OUT/'synthetic-usage.sqlite3')
def work():
 while True:
  if not server.store.process_next() and not server.store.process_generation() and not server.store.chat_runtime.process_next():time.sleep(.15)
threading.Thread(target=work,daemon=True).start();print('Loretune local fixture: http://127.0.0.1:8773 · synthetic only',flush=True);server.serve_forever()
