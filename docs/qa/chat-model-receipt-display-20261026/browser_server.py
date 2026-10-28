"""Synthetic receipt replay only. No credentials, providers or worker threads."""
from pathlib import Path
import sys,sqlite3,tempfile,json,hashlib,uuid,datetime
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from app import Store,server
import chat_runtime,contracts
OUT=Path(__file__).resolve().parent
LONG_NAME='--long-name' in sys.argv
if LONG_NAME:
 OUT=OUT/'long-name'
 OUT.mkdir(exist_ok=True)
SOURCE=Path('/private/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/aethon-native-motion-10khfdud/studio.sqlite3')
data=Path(tempfile.mkdtemp(prefix='aethon-model-display-'))
with sqlite3.connect('file:'+str(SOURCE)+'?mode=ro',uri=True) as src,sqlite3.connect(data/'studio.sqlite3') as dst:src.backup(dst)
store=Store(data)
def call(action,**values):return store.mutate(dict(action=action,data=values,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
p=store.state()['projects']['A']
call('model_settings',song='A',selections={'chat':'openai-gpt-6-luna'},model_revision=p['model_settings']['revision'])
run=call('production_run',song='A')['run']['id']
receipt=call('production_tool',song='A',run=run,call=dict(id='display-lookup',name='search_project_context',arguments={'query':'motion approval'},complete=True))['tool']
answer=json.loads((ROOT/'docs/qa/native-motion-20261026/quality-fix/live/final-clarification/result.json').read_text())['answer']
with store.connect() as c:
 chat_runtime.put(c,dict(id='display-replay',project=contracts.project_id(store.workspace_id,'A'),status='completed',mode='contract-fake',model='Claude Haiku 5.5 · 저장 응답 재생',prompt='합성 UI 검증 · 실제 모델 호출 없음',answer=answer,steps=[dict(status='fixture-replay',tool_calls=[dict(call=dict(name='search_project_context'),result=receipt)])],usage_cost_usd='0',billing_confirmed=False))
 # Make the current context stale while retaining the earlier true receipt.
 revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();saved=json.loads(body)
 shot=next(s for s in saved['projects']['A']['shots'].values() if s.get('motion_head'))
 shot['description']+=' · 표시 검증용 변경'
 c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(saved)))
http=server(data,0)
if LONG_NAME:
 # Controlled HTTP display fixture only; no selection, readiness or routing change.
 real_state=http.store.state
 def display_state(*args,**kwargs):
  value=real_state(*args,**kwargs)
  for model in value['model_catalog']['models']:
   if model['id']=='openai-gpt-6-luna':
    model['display_name']='합성 긴 기획 모델 이름 · '+('긴한글무공백모델이름'*18)+' · 끝'
  return value
 http.store.state=display_state
info=dict(url=f'http://127.0.0.1:{http.server_port}',data=str(data),synthetic_only=True,media_files=0,provider_runtime=False,source_database_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'browser-server.json').write_text(json.dumps(info,indent=2))
(OUT/'state-before.json').write_text(json.dumps(store.state(),ensure_ascii=False,indent=2))
print(json.dumps(info),flush=True)
try:http.serve_forever()
finally:http.server_close()
