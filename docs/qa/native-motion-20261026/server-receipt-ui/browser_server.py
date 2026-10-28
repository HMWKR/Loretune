"""Isolated synthetic UI replay. No credential/runtime, provider or worker."""
from pathlib import Path
import sys,json,sqlite3,tempfile,hashlib,uuid,datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from app import Store,server
import contracts,chat_runtime
OUT=Path(__file__).resolve().parent
source=Path('/private/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/aethon-native-motion-10khfdud')
root=Path(tempfile.mkdtemp(prefix='aethon-receipt-ui-'))
with sqlite3.connect('file:'+str(source/'studio.sqlite3')+'?mode=ro',uri=True) as src,sqlite3.connect(root/'studio.sqlite3') as dst:src.backup(dst)
st=Store(root)
def call(a,**data):return st.mutate(dict(action=a,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
call('project',name='B 격리 확인',era='default',story=0);call('shot',song='B 격리 확인',shot='모션',description='승인 없는 별도 합성 작품')
run=call('production_run',song='A')['run']['id']
receipt=call('production_tool',song='A',run=run,call=dict(id='ui-lookup',name='search_project_context',arguments={'query':'motion approval'},complete=True))['tool']
result=json.loads((OUT.parent/'quality-fix/live/final-clarification/result.json').read_text())
turn=dict(id='synthetic-replay',project=contracts.project_id(st.workspace_id,'A'),status='completed',mode='contract-fake',model='Claude Haiku 5.5 · 저장된 응답 재생',prompt='합성 UI 검증: 과거 Claude 원문과 이번 서버 조회를 함께 표시합니다. 이번 API 호출 없음.',answer=result['answer'],steps=[dict(status='fixture-replay',tool_calls=[dict(call=dict(name='search_project_context'),result=receipt)])],usage_cost_usd='0',billing_confirmed=False)
with st.connect() as c:chat_runtime.put(c,turn)
http=server(root,0)
info=dict(url=f'http://127.0.0.1:{http.server_port}',directory=str(root),source=str(source),synthetic_only=True,provider_runtime=False,media_files=0,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),answer_sha256=hashlib.sha256(result['answer'].encode()).hexdigest())
(OUT/'browser-server.json').write_text(json.dumps(info,indent=2));(OUT/'browser-db-before.json').write_text(json.dumps(st.state(),ensure_ascii=False,indent=2));print(json.dumps(info),flush=True)
try:http.serve_forever()
finally:http.server_close()
