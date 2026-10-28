"""Human-reviewed local fixture pipeline. No credentials or external providers."""
import time
import action_execution as actions
import model_selection,guided,ledger
from image_adapter import SyntheticImageAdapter
from loretune import Conflict

ZERO={'amount':'0','currency':'USD'}

def handle(c,store,studio,name,project_id,command,data):
 p=studio.projects[name];w=store.workspace_id
 cards=p.setdefault('execution_cards',[])
 if command=='action_propose':
  if set(data)!={'song','plan','scene'}:raise ValueError('저장된 계획과 장면만 지정하세요.')
  plan=next((x for x in p.get('guided_plans',[]) if x['id']==data['plan']),None)
  if not plan or plan['status']!='applied':raise ValueError('계획을 승인해 샷에 반영한 후 준비하세요.')
  if plan['context_hash']!=guided.fingerprint(guided.context(p)):raise Conflict('계획의 음악·설정이 변경됐습니다.')
  scene=next((x for x in plan['scenes'] if x['id']==data['scene']),None)
  shot_name=next((n for n,s in p['shots'].items() if s.get('stable_id')==data['scene'] and s.get('plan_id')==plan['id']),None)
  if scene is None or shot_name is None:raise ValueError('현재 계획의 장면이 아닙니다.')
  shot=p['shots'][shot_name];context=model_selection.snapshot(p)['sha256']
  prior=next((x for x in cards if x['scene']==scene['id'] and x['context_hash']==context and x['decision']!='rejected'),None)
  if prior:return prior
  action=actions.propose(c,w,project_id,plan_id=plan['id'],plan_revision=plan['version'],context_hash=context,
      role='image',release_id='synthetic-solid-color-v1',inputs={'prompt':scene['description']},options={'width':128,'height':128})
  card=dict(id=action['id'],plan=plan['id'],scene=scene['id'],shot=shot_name,shot_revision=shot['revision'],description=scene['description'],context_hash=context,
      revision=1,decision='pending',mode='rehearsal',model='합성 단색 이미지 · AI 아님',money=ZERO.copy(),grant=None,job=None,take=None,history=[])
  cards.append(card);return card
 card=next((x for x in cards if x['id']==data.get('id')),None)
 if card is None:raise ValueError('현재 작품의 실행 카드가 아닙니다.')
 if type(data.get('card_revision')) is not int or card['revision']!=data['card_revision']:raise Conflict('실행 카드가 변경됐습니다.')
 shot=p['shots'].get(card['shot'])
 if command=='action_decide':
  if set(data)!={'song','id','card_revision','decision'} or data['decision'] not in {'approved','held','rejected'}:raise ValueError('승인·보류·거절을 선택하세요.')
  if card.get('take') is not None:raise ValueError('수집한 후보는 결과 검토를 사용하세요.')
  decision=data['decision']
  if decision=='approved':
   if card['decision']=='rejected':raise ValueError('거절된 작업은 새로 준비하세요.')
   if not shot or shot['revision']!=card['shot_revision'] or model_selection.snapshot(p)['sha256']!=card['context_hash']:raise Conflict('샷·문맥이 변경됐습니다. 새로 준비하세요.')
   if card['job']:raise ValueError('이미 접수한 작업입니다. 기존 영수증을 사용하세요.')
   scope='rehearsal:project:'+project_id
   if not ledger.budget(c,w,scope):ledger.patch_budget(c,w,scope,dict(limit=ZERO.copy(),maxConcurrentJobs=4,allowAutomaticRetries=False),0)
   g=actions.grant(c,w,project_id,[card['id']],actor='local-owner',approved=True,expires=time.time()+900,price_revision='rehearsal-v1',money_by_action={card['id']:ZERO.copy()})
   receipt=actions.request_from_plan(c,w,project_id,p,dict(plan_id=card['plan'],action_id=card['id'],grant_id=g['id']))
   card.update(grant=g['id'],job=receipt['job_id'])
  elif card['job']:
   job=actions.get(c,'action_jobs',w,project_id,card['job'])
   if job['state']!='prepared':raise ValueError('시작된 작업은 보류·거절로 되돌릴 수 없습니다.')
   g=actions.get(c,'execution_grants',w,project_id,card['grant']);actions.revoke(c,w,project_id,g['id'],g['revision'])
   actions.claim(c,w,project_id,job['id'],context_hash=card['context_hash'],price_revision='rehearsal-v1')
   # Admission identity stays consumed. A fresh reviewed action is required.
   card['decision']='rejected';decision='rejected'
  card['decision']=decision
 elif command=='action_execute':
  if set(data)!={'song','id','card_revision'}:raise ValueError('실행 인수를 확인하세요.')
  if card['decision']!='approved' or not card['job'] or not shot:raise ValueError('승인된 작업 영수증이 필요합니다.')
  job=actions.get(c,'action_jobs',w,project_id,card['job'])
  if job['state']=='collected':return card
  job=actions.claim(c,w,project_id,job['id'],context_hash=model_selection.snapshot(p)['sha256'],price_revision='rehearsal-v1',rights_valid=shot['revision']==card['shot_revision'])
  if job['state']=='blocked':card['decision']='blocked'
  elif job['state']=='claimed':
   output=SyntheticImageAdapter().generate(dict(prompt=job['action']['inputs']['prompt'],**job['action']['options']))
   path,metadata=store.save_media(output['bytes'],'.png','video')
   store.check_rights(c,[path.stem])
   take=studio.attach_take(name,card['shot'],path,reason='모의 합성 단색 이미지 · AI 생성 아님',expected_revision=shot['revision'])
   shot['takes'][-1].update(metadata=metadata,rights='로컬 합성 fixture',filename='synthetic-candidate.png',provenance=output['provenance'],action_id=card['id'])
   actions.record_result(c,w,project_id,job['id'],asset_hash=path.stem,output_slot='image')
   ledger.command(c,w,job['scope'],'settle',dict(reservation=job['reservation'],money=ZERO.copy()),job['id']+':fixture-settle')
   card['take']=take
  else:raise ValueError('기존 작업의 상태 확인이 필요합니다. 재실행하지 않습니다.')
 elif command=='action_review':
  if set(data)!={'song','id','card_revision','decision'} or data['decision'] not in {'approved','rejected'}:raise ValueError('결과 승인·거절을 선택하세요.')
  if card['take'] is None:raise ValueError('검토할 후보가 없습니다.')
  job=actions.get(c,'action_jobs',w,project_id,card['job'])
  if card.get('result_decision'):raise ValueError('이미 검토한 후보입니다. 샷 작업대에서 검토 이력을 확인하세요.')
  if data['decision']=='approved':
   store.check_rights(c,[job['result']['sha256']]);actions.approve_result(c,w,project_id,job['id'],actor='local-owner')
  card['result_decision']=data['decision']
  shot.setdefault('reviews',[]).append(dict(take=card['take'],decision=data['decision'],reason='모의 후보 직접 검토',at=time.time(),actor='local-owner'))
  # Result approval does not change selected Take or an existing export.
 else:raise ValueError('지원하지 않는 실행 카드 명령')
 card['history'].append(dict(command=command,decision=data.get('decision'),actor='local-owner',at=time.time()))
 card['revision']+=1
 return card
