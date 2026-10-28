"""Explicit approved synthetic UI trial. No key copy, retry or media provider.
Run once; browser triggers each of two bounded turns. Type phase2 on stdin only
once after human-controller review/execution to bind the changed synthetic state.
"""
import base64,hashlib,io,json,sys,tempfile,threading,time,wave
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import Store,server
import chat_runtime,contracts,model_selection,anthropic_ontology
from scripts.anthropic_smoke import credential
OUT=ROOT/'docs/qa/claude-chat-ui-live-20261025'
NAME='Claude 실제 채팅 · Synthetic Song A'
PROMPT='합성 Song A의 승인 온톨로지를 도구로 먼저 조회하세요. Mira의 기본 의상과 이 곡 스튜디오 장면의 예외를 구분하고, 모르는 나이는 모른다고 답하세요. Mira가 스튜디오에서 빨간 코트를 입은 장면 한 개를 propose_media_plan으로 검토 전 계획에 저장하세요. 기본 파란 코트 설정은 변경하지 마세요. 최종 답변은 한국어로 출처 ID와 실제 저장된 계획 ID, 검토 전임을 명시하세요. 영상 생성이나 비용 승인은 요청하지 않습니다. 도구 조회의 출처만 근거로 사용하세요.'
STAGE={'id':'claude-chat-ui-live-20261025','cap_micro':100000}
JOURNAL=ROOT/'docs/qa/anthropic-smoke-20261025/usage.sqlite3'

def write(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
def approval(st,prompt,tools):
 return dict(model=anthropic_ontology.MODEL,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,NAME),synthetic_only=True,expires=time.time()+3600,context_hash=model_selection.snapshot(st.state()['projects'][NAME])['sha256'],prompt_hashes=[hashlib.sha256(prompt.encode()).hexdigest()],price_revision='haiku-5-5-20261025',max_rounds=4,max_input_tokens=8192,max_output_tokens=4096,turn_cap_micro=12000,stage=STAGE,max_turns=2,one_per_prompt=True,tools=tools)

class RecordedAdapter(chat_runtime.AnthropicChatAdapter):
 def count(self,body):
  # Private thinking is transmitted only within the same provider turn, never logged.
  public=deepcopy(body)
  for message in public['messages']:
   if isinstance(message['content'],list):message['content']=[b for b in message['content'] if b.get('type') not in {'thinking','redacted_thinking'}]
  digest=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
  write('request-'+digest+'.json',dict(sha256=digest,public_request=public))
  return super().count(body)

def main():
 OUT.mkdir(exist_ok=True)
 # Immutable attempt marker protects accidental reruns before a key is read.
 marker=OUT/'attempt.json'
 with marker.open('x') as f:json.dump({'created':time.time(),'state':'setup','stage':STAGE},f)
 root=Path(tempfile.mkdtemp(prefix='loretune-claude-live-ui-'));st=Store(root)
 def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id='fixture-'+str(st.state()['revision'])))
 call('setting',text='Mira wears a blue coat by default. Age is unknown.',era='default',valid_from=0,valid_to=2)
 call('project',name=NAME,era='default',story=0)
 call('project',name='Foreign synthetic project',era='other',story=0)
 for label,kind,description in [('Mira','character','Global canon: Mira wears a blue coat by default. Age is unknown. Only in Song A studio scene, Mira wears a red coat; this does not replace the global blue coat.'),('Studio — Song A only','place','Only in Song A studio scene, Mira wears a red coat; this does not replace the global blue coat.')]:
  p=st.state()['projects'][NAME];proposal=call('ontology_propose',song=NAME,kind=kind,label=label,description=description,evidence=description,ontology_revision=p['ontology']['revision'])['ontology']
  call('ontology_apply',song=NAME,proposal=proposal['id'],ontology_revision=p['ontology']['revision'],approved=True)
 b=io.BytesIO()
 with wave.open(b,'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*96000)
 call('audio',song=NAME,filename='synthetic-silence-2s.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
 call('music_structure',song=NAME,audio=1,start=0,end=2,sections=[])
 call('model_settings',song=NAME,selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
 a=approval(st,PROMPT,['search_project_context','propose_media_plan'])
 write('phase1-gate.json',dict(approval=a,prompt=PROMPT,prior_usage_usd='0.0049575',max_messages=8,worst_case_usd='0.022944',billing_confirmed=False,external_media_calls=0))
 state=st.state();state.pop('token',None);write('before-state.json',state)
 adapter=RecordedAdapter(lambda name:credential(ROOT/'.env') if name=='Anthropic_KEY' else None,enabled=True)
 app=server(root,0,chat_configuration=dict(adapter=adapter,approval=a,journal_path=JOURNAL));stop=threading.Event()
 def worker():
  while not stop.is_set():
   if not app.store.chat_runtime.process_next():stop.wait(.15)
 def control():
  for command in sys.stdin:
   if command.strip()!='phase2':continue
   try:
    p=app.store.state()['projects'][NAME]
    assert len(p['chat_turns'])==1 and p['chat_turns'][0]['status']=='completed'
    assert len(p['execution_cards'])==1
    card=p['execution_cards'][0];assert card['decision']=='approved' and card['take'] is not None
    prompt='합성 Song A의 승인 온톨로지와 작업 '+card['job']+'를 각각 도구로 조회하세요. 실제 저장된 계획 '+card['plan']+'와 후보 Take를 확인해서 최종 상태를 한국어로 설명하세요. 기본 파란 코트와 곡 한정 빨간 코트가 유지됐는지 출처 ID로 설명하고 작업 ID·Take 번호·자산 SHA256을 정확히 인용하세요. 모의 단색 이미지 작업은 실제 AI 영상 생성이 아니며 외부 미디어 호출은 0회임을 명시하세요. 결과 승인은 작업 영수증 그대로 설명하고 새 계획이나 생성은 요청하지 마세요.'
    a=approval(app.store,prompt,['search_project_context','get_generation_job'])
    app.store.chat_runtime.approval=a
    write('phase2-gate.json',dict(approval=a,prompt=prompt,job=card['job'],plan=card['plan']))
    print(json.dumps({'phase2':'ready','prompt_file':str(OUT/'phase2-gate.json')},ensure_ascii=False),flush=True)
   except Exception:print('{"phase2":"blocked: review persisted synthetic state"}',flush=True)
 threading.Thread(target=worker,daemon=True).start();threading.Thread(target=control,daemon=True).start()
 info=dict(url='http://127.0.0.1:'+str(app.server_port),data=str(root),name=NAME,prompt=PROMPT,mode='anthropic-live',stage=STAGE)
 write('runtime.json',info);print(json.dumps(info,ensure_ascii=False),flush=True)
 try:app.serve_forever()
 finally:stop.set();app.server_close()
if __name__=='__main__':main()
