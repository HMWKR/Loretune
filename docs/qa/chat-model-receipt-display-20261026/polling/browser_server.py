"""Two-tab polling QA: new synthetic Store, no media/provider/auth configuration."""
from pathlib import Path
import sys,tempfile,json,uuid,datetime
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from app import Store,server
out=Path(__file__).resolve().parent
data=Path(tempfile.mkdtemp(prefix='aethon-model-poll-'))
store=Store(data)
def call(action,**data):
 return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
for name in ['A','B']:
 call('project',name=name,era='default',story=0)
 call('shot',song=name,shot='s',description='합성 polling 검증 · 모션/미디어 없음')
call('model_settings',song='A',selections={'chat':'openai-gpt-6-luna'},model_revision=store.state()['projects']['A']['model_settings']['revision'])
(out/'state-before.json').write_text(json.dumps(store.state(),ensure_ascii=False,indent=2))
http=server(data,0)
info={'url':f'http://127.0.0.1:{http.server_port}','data':str(data),'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'synthetic_only':True,'provider_runtime':False,'media_files':0}
(out/'browser-server.json').write_text(json.dumps(info,indent=2));print(json.dumps(info),flush=True)
try:http.serve_forever()
finally:http.server_close()
