"""Explicit synthetic-only UI harness: no network adapter or credentials loaded."""
from pathlib import Path
import base64,hashlib,io,json,sys,tempfile,threading,time,uuid,wave
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from app import Store,server
import chat_runtime,contracts,model_selection,anthropic_ontology
PROMPT='Mira의 승인된 의상 설정을 조회하고 스튜디오 장면을 제안한 뒤 저장한 계획 번호를 알려주세요.'
NAME='합성 채팅 계약 QA'
class ContractAdapter:
 mode='contract-fake'
 def count(self,body):return 300
 def complete(self,body):
  assistant=[m for m in body['messages'] if m['role']=='assistant'];round_number=len(assistant)
  if round_number==0:blocks=[dict(type='tool_use',id='lookup',name='search_project_context',input={'query':'Mira'})]
  elif round_number==1:blocks=[dict(type='tool_use',id='plan',name='propose_media_plan',input=dict(goal='합성 Mira 장면',scenes='Mira가 파란 코트를 입고 스튜디오에 서 있다.',style='기하학 합성 검증',constraints='승인된 파란 코트 보존',kind='narrative'))]
  else:
   receipt=json.loads(body['messages'][-1]['content'][0]['content']);blocks=[dict(type='text',text='모의 도구 계약 검증입니다. 승인된 합성 설정은 파란 코트이며, 계획 '+receipt['plan']['id']+'를 검토 전 상태로 저장했습니다. 실제 Claude·영상 생성·과금은 없습니다.')]
  return dict(_request_id='contract-fixture-'+str(round_number),usage=dict(input_tokens=300,output_tokens=80),stop_reason='tool_use' if round_number<2 else 'end_turn',content=blocks)
root=Path(tempfile.mkdtemp(prefix='loretune-chat-ui-synthetic-'));st=Store(root)
def call(a,**d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
call('setting',text='Mira는 파란 코트를 입는다. 합성 검증 설정.',era='default',valid_from=0,valid_to=2)
call('project',name=NAME,era='default',story=0)
b=io.BytesIO()
with wave.open(b,'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*96000)
call('audio',song=NAME,filename='synthetic-silence.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
call('music_structure',song=NAME,audio=1,start=0,end=2,sections=[])
call('model_settings',song=NAME,selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
a=dict(model=anthropic_ontology.MODEL,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,NAME),synthetic_only=True,expires=time.time()+1800,context_hash=model_selection.snapshot(st.state()['projects'][NAME])['sha256'],prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],price_revision='haiku-5-5-20261025',max_rounds=4)
app=server(root,0,chat_configuration=dict(adapter=ContractAdapter(),approval=a,journal_path=root/'fake-usage.sqlite3'));stop=threading.Event()
def worker():
 while not stop.is_set():
  if not app.store.chat_runtime.process_next():stop.wait(.1)
threading.Thread(target=worker,daemon=True).start()
info=dict(url='http://127.0.0.1:'+str(app.server_port),data=str(root),prompt=PROMPT,mode='contract-fake',external_calls=0)
(Path(__file__).parent/'contract-ui-runtime.json').write_text(json.dumps(info,ensure_ascii=False,indent=2));print(json.dumps(info,ensure_ascii=False),flush=True)
try:app.serve_forever()
finally:stop.set();app.server_close()
