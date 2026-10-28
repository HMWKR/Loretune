"""Two bounded read-only semantic follow-ups after observed domain confusion.
Existing synthetic DB only, actual Claude count/tool/result/answer; no fal.
No re-run of original trial, no retries, no source ingestion or customer data.
"""
import argparse,json,sqlite3,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import cc01_context_trial as trial
from app import Store
import chat_models,chat_runtime

PROMPTS={
 'A':'현재 문맥을 도구로 조회하고 간결히 답하세요. Nari의 현재 승인 의상·출처·모르는 나이는? 기존 두 제작 작업의 승인 기록과 현재 실행 가능성 및 최종 출력 승인 상태는 어떻게 다른가요? generate_audio=false가 원곡 보존 요청과 충돌하나요? 실제 영상이 생성됐다고 말하지 마세요. 새 제안·승인·작업 실행 없이 현재 서버 근거로만 설명하세요.',
 'B':'현재 B의 정식 문맥을 도구로 조회하세요. Nari의 기록된 의상·장소와 출처, 모르는 나이를 간결히 답하세요. 장면 목록이 비어 있는 것이 정식 온톨로지 승인이 없다는 뜻인가요? 현재 작품에 카메라 지시가 있나요? 다른 작품의 정보를 사용하거나 새 작업을 만들지 마세요.'
}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
 if not args.live:raise SystemExit('Explicit --live required; offline tests use the existing trial preflight.')
 out=trial.OUT/'semantic-followup';out.mkdir(exist_ok=True)
 with sqlite3.connect('file:'+str(trial.JOURNAL)+'?mode=ro',uri=True) as c:
  rows=c.execute('SELECT id,COALESCE(actual_micro,held_micro),metadata FROM trials').fetchall()
 assert sum(trial.STAGE['id']==json.loads(r[2]).get('stage') for r in rows)==10,'expected exactly the completed original ten responses'
 assert sum(r[1] for r in rows)+22940<=50_000_000
 with (out/'attempt.json').open('x') as f:json.dump(dict(at=time.time(),purpose='domain semantics regression after observed live errors',model=trial.MODEL,max_messages=4,stage=trial.STAGE,prior_conservative_micro=sum(r[1] for r in rows),system_hash=trial.digest(chat_models.SYSTEM),retries=0,real_fal_calls=0),f)
 folder=Path(json.loads((trial.OUT/'live/fixture.json').read_text())['directory'])
 assert folder.name.startswith('aethon-cc01-live-') and folder.parent==Path('/tmp').resolve() or folder.name.startswith('aethon-cc01-live-') and str(folder).startswith('/var/folders/')
 st=Store(folder);summary=[]
 with st.connect() as c:before={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['production_actions','execution_grants','generation_jobs','ontology_versions']}
 for name,prompt in PROMPTS.items():
  caseout=out/name;caseout.mkdir(exist_ok=True);adapter=trial.Recorder(caseout,True)
  approval=trial.approval(st,name,prompt,['search_project_context']);approval.update(max_rounds=2,turn_cap_micro=12000)
  runtime=chat_runtime.ChatRuntime(st,adapter,approval,trial.JOURNAL);st.chat_runtime=runtime
  identifier=trial.call(st,'chat_turn',song=name,prompt=prompt)['chat_turn']['id'];runtime.process_next()
  with st.connect() as c:turn=chat_runtime.get(c,identifier)
  trial.write(caseout/'turn.json',turn);trial.write(caseout/'transport.json',dict(counts=len(adapter.counts),messages=len(adapter.requests),sizes=[x['request_bytes'] for x in adapter.counts]))
  item=dict(project=name,status=turn['status'],turn_id=turn['id'],usage_usd=turn['usage_cost_usd'],messages=len(adapter.requests))
  summary.append(item);trial.write(out/'summary.json',summary);print(json.dumps(item),flush=True)
  if turn['status']!='completed':break
 with st.connect() as c:after={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before}
 assert before==after
 trial.write(out/'write-boundary.json',dict(before=before,after=after,new_actions_grants_jobs_or_canonical_versions=0,listeners=0,real_fal_calls=0))
if __name__=='__main__':main()
