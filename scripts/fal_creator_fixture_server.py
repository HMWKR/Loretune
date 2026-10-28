"""Isolated browser fixture. NO credentials/network to providers, NO production data.
Use only for QA: canned chat and fal HTTP envelopes, local synthetic media bytes.
It injects fixture-price/transmission evidence, never user grants or Take approvals.
"""
import sys,tempfile,hashlib,base64,subprocess,time,json,uuid,io
from pathlib import Path
from threading import Thread
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import server
from fal_models import Contract,CONNECTION
from fal_model_adapter import FalModelAdapter
from fal_provider import BASE,ProviderError
from fal_dispatch import FalDispatch
import contracts,guided,ledger,chat_runtime,chat_models,model_selection

root=Path(tempfile.mkdtemp(prefix='loretune-fal-creator-fixture-'));events=[]
for name,args in [('image.png',['-f','lavfi','-i','color=blue:s=1024x576','-frames:v','1']),('video.mp4',['-f','lavfi','-i','testsrc2=s=320x180:r=24:d=5','-c:v','libx264','-pix_fmt','yuv420p']),('tone.wav',['-f','lavfi','-i','sine=frequency=440:duration=5','-c:a','pcm_s16le'])]:
 subprocess.run(['ffmpeg','-v','error',*args,str(root/name)],check=True)
http=server(root/'data',0);st=http.store
name='합성 모델 제작 QA'
def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
call('project',name=name,era='default',story=0)
call('audio',song=name,filename='합성 신호 5초.wav',content=base64.b64encode((root/'tone.wav').read_bytes()).decode(),rights='QA synthetic generated tone')
call('music_structure',song=name,audio=1,start=0,end=5,sections=[])
call('model_settings',song=name,selections={'chat':'anthropic-haiku-5-5','image':'fal-flux-schnell','video':'fal-kling-2-5-turbo'},model_revision=0)
pid=contracts.project_id(st.workspace_id,name)
with st.connect() as c:ledger.patch_budget(c,st.workspace_id,'project:'+pid,dict(limit={'amount':'0.05','currency':'USD'},maxConcurrentJobs=2,allowAutomaticRetries=False),0)

def event(**v):events.append(v);(root/'events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
def adapter(key,prompt,options,frames=()):
 contract=Contract(key);payload=contract.payload(prompt,options,frames);rid=str(uuid.uuid4());prefix=BASE+'/'.join(contract.MODEL.split('/')[:2])+'/requests/'+rid
 quote=dict(provider='fal.ai',model=contract.MODEL,money={'amount':'0.01','currency':'USD'},input_sha256=guided.fingerprint(payload),kind='fixture',price_revision='synthetic-only',source=contract.spec['source'],expires=time.time()+3600)
 def transport(method,url,headers,body):
  assert 'Authorization' not in headers
  event(kind='fake-HTTP',method=method,model=key,operation='submit' if method=='POST' else 'status' if url.endswith('/status') else 'result' if method=='GET' else 'cancel')
  if method=='POST':return dict(request_id=rid,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
  if method=='PUT':return {}
  if url.endswith('/status'):return {'status':'COMPLETED'}
  asset=dict(url='https://v3b.fal.media/fixture-'+key+('.png' if contract.role=='image' else '.mp4'),content_type='image/png' if contract.role=='image' else 'video/mp4')
  return dict(images=[asset],has_nsfw_concepts=[False]) if contract.role=='image' else dict(video=asset)
 ad=FalModelAdapter(key,quote=quote,transport=transport);downloads=0
 def download(url):
  nonlocal downloads
  downloads+=1;event(kind='fake-download',model=key,attempt=downloads)
  if contract.role=='image' and downloads==1:raise ProviderError('download_interrupted')
  raw=(root/('image.png' if contract.role=='image' else 'video.mp4')).read_bytes()
  class Response(io.BytesIO):pass
  r=Response(raw);r.headers={'Content-Type':'image/png' if contract.role=='image' else 'video/mp4','Content-Length':str(len(raw))}
  return ad.read_video(r)
 ad.download=download;return ad
adapters=[adapter('fal-flux-schnell','blue geometry',{'ratio':'16:9'}),adapter('fal-kling-2-5-turbo','slow geometry',{'duration':5,'generate_audio':False},[(root/'image.png').read_bytes()])]
st.media_dispatch=FalDispatch(st,adapters)
prompt='합성 장면을 계획하고 파란 기하학 이미지 제작을 준비해줘'
class FakeChat:
 mode='contract-fake'
 def count(self,body):return 100
 def complete(self,body):
  p=st.state()['projects'][name];plans=p.get('guided_plans',[]);action=None
  if not plans:action=('propose_media_plan',dict(goal='기하학 테스트 영상',scenes='파란 기하학 도형이 놓인 스튜디오',style='',constraints='원본 음악 유지',kind='visualizer'))
  elif plans[-1]['status']=='applied' and not p['media_actions']:
   n=plans[-1]['shots'][0];sh=p['shots'][n];action=('prepare_image_action',dict(shot_id=sh['stable_id'],model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9',shot_revision=sh['revision']))
  content=[dict(type='tool_use',id=uuid.uuid4().hex,name=action[0],input=action[1])] if action else [dict(type='text',text='저장된 계획과 제작 요청을 검토해 주세요. 승인 전에는 실행하지 않았습니다. 모의 전송 검증입니다.')]
  event(kind='fake-chat',tool=action[0] if action else None)
  return dict(_request_id='synthetic-chat',stop_reason='tool_use' if action else 'end_turn',usage={'input_tokens':100,'output_tokens':100},content=content)
approval=dict(model='claude-haiku-5-5',workspace_id=st.workspace_id,project_id=pid,synthetic_only=True,expires=time.time()+3600,context_hash=model_selection.snapshot(st.state()['projects'][name])['sha256'],prompt_hashes=[hashlib.sha256(prompt.encode()).hexdigest()],price_revision=chat_models.contract('anthropic-haiku-5-5')['price_revision'],max_rounds=4)
st.chat_runtime=chat_runtime.ChatRuntime(st,FakeChat(),approval,root/'fake-chat-usage.sqlite3')
def worker():
 while True:
  try:
   with st.connect() as c:
    p,_=st.media_dispatch.project(c,name)
    for row in c.execute('SELECT body FROM production_actions'):
     a=json.loads(row[0])
     if a['connection_id']!=CONNECTION:continue
     q=a['options']['quote'];data=st.media_dispatch.data(c,p,a)
     st.media_dispatch.gates.setdefault(a['id'],dict(workspace=st.workspace_id,project=pid,action_hash=a['hash'],input_sha256=guided.fingerprint(data),model=a['release_id'],output_policy=a['options']['output_policy'],maximum_units=ledger.units(q['money']),maximum_calls=1,expires=q['expires']))
    for row in c.execute('SELECT body FROM generation_jobs'):
     j=json.loads(row[0])
     if j['state']=='import_blocked' and j.get('failure_code')=='download_interrupted':
      st.media_dispatch.recovery_approvals.setdefault(j['id'],dict(id=uuid.uuid4().hex,evidence='controlled synthetic interruption cleared',workspace=st.workspace_id,project=pid,connection_id=CONNECTION,model=j['quote']['model'],job=j['id'],request_id=j['receipt']['request_id'],operation='collect',result_sha256=guided.fingerprint(j['result']),expires=time.time()+600))
   st.chat_runtime.approval['context_hash']=model_selection.snapshot(st.state()['projects'][name])['sha256']
   if not st.process_next() and not st.process_generation() and not st.chat_runtime.process_next():time.sleep(.2)
  except Exception as e:event(kind='worker-error',type=type(e).__name__,message=str(e)[:100]);time.sleep(.5)
Thread(target=worker,daemon=True).start()
meta=dict(url=f'http://127.0.0.1:{http.server_port}',root=str(root),source=str(Path(__file__).resolve().parents[1]),prompt=prompt,external_calls=0,real_credentials=False)
(root/'runtime.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False),flush=True)
http.serve_forever()
