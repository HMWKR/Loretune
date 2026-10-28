"""Creator-facing projections and human commands over existing saved fal actions."""
import json,time
import action_execution as actions,contracts,guided,ledger,media_bridge,model_selection,media_recovery
from fal_models import CONNECTION

def capability(store,p,role):
 item=model_selection.validate_selection(role,model_selection.settings(p)['selections'][role]);pipe=store.media_dispatch
 result=dict(state='unconfigured',available=False,can_prepare=False,mode='disconnected',model=item['model'] if item else None,reason='모델을 선택하면 연결 상태를 확인할 수 있습니다.',policy='출력 접근·보관 조건과 비용은 준비된 작업에서 확인합니다.')
 if not item:return result
 result.update(state='blocked' if item['state'] in {'integration_blocked','retired','unavailable','disabled'} else 'unverified',reason=item.get('reason') or '선택한 모델의 서버 연결·가격·결과 수신 검증이 필요합니다.')
 ad=pipe.adapters.get(item['id']) if pipe else None
 if ad:
  result.update(mode=ad.mode,can_prepare=bool(ad.contract.quote and ad.contract.quote.get('expires',0)>time.time()),reason='모의 전송으로 계약만 시험합니다. 실제 모델은 활성화되지 않았습니다.' if ad.mode=='contract-fake' else '입력·견적은 준비할 수 있습니다. 고정 전송 허가와 사람 승인이 필요합니다.')
 return result

def grants(c,w,pid,a):
 return [g for row in c.execute('SELECT body FROM execution_grants WHERE workspace=? AND project=? ORDER BY rowid DESC',(w,pid)) if (g:=json.loads(row[0])).get('action_hashes',{}).get(a['id'])==a['hash']]

def valid_grant(c,store,p,name,a):
 pipe=store.media_dispatch;pid=contracts.project_id(store.workspace_id,name)
 if pipe is None:raise ValueError('선택 모델의 서버 연결이 없습니다.')
 for g in grants(c,store.workspace_id,pid,a):
  try:pipe.authorize(c,p,name,a,g['id']);return g
  except ValueError:pass
 raise ValueError('유효한 작업 승인이 필요합니다.')

def guard(p,a):
 if p.get('media_action_reviews',{}).get(a['id'],{}).get('decision') in {'held','rejected'}:raise ValueError('사용자가 보류·거절한 작업입니다. 다시 검토해야 합니다.')

def handle(c,store,p,name,command,d):
 if command=='recover_media_job':
  if set(d)!={'song','job','operation'}:raise ValueError('기존 작업 복구 대상만 지정하세요.')
  row=c.execute('SELECT body FROM generation_jobs WHERE id=?',(d['job'],)).fetchone()
  if not row:raise ValueError('작업이 없습니다.')
  j=json.loads(row[0])
  if j['context']['song']!=name:raise ValueError('현재 작품의 작업이 아닙니다.')
  return dict(job=media_recovery.enqueue(c,store,j,d['operation'])['id'])
 if set(d)!={'song','action_id','decision'}:raise ValueError('저장된 작업과 검토 결정만 지정하세요.')
 pid=contracts.project_id(store.workspace_id,name);a=actions.get(c,'production_actions',store.workspace_id,pid,d['action_id'])
 if a['connection_id']!=CONNECTION:raise ValueError('지원하는 저장 작업이 아닙니다.')
 prior=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(store.workspace_id,pid,a['id'])).fetchone()
 decision=d['decision'];reviews=p.setdefault('media_action_reviews',{})
 if decision=='execute':
  if prior:
   j=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',prior).fetchone()[0]);return dict(job=j['id'],existing=True)
  guard(p,a);g=valid_grant(c,store,p,name,a)
  result=actions.request_with_savepoint(c,store.workspace_id,pid,p,dict(plan_id=a['plan_id'],action_id=a['id'],grant_id=g['id']),provider_request=store.media_dispatch.request)
  return dict(job=result['job_id'],existing=result['status']=='existing')
 if prior:raise ValueError('이미 접수된 작업입니다. 진행 상태·취소·기존 결과 회수를 사용하세요.')
 if decision in {'held','rejected'}:
  for g in grants(c,store.workspace_id,pid,a):
   if g['state']=='active':actions.revoke(c,store.workspace_id,pid,g['id'],g['revision'])
  reviews[a['id']]=dict(decision=decision,actor='local-owner',at=time.time());return dict(decision=decision)
 if decision!='approved':raise ValueError('허용되지 않은 결정입니다.')
 if store.media_dispatch is None:raise ValueError('선택 모델의 서버 연결이 없습니다.')
 reviews[a['id']]=dict(decision='reviewing',actor='local-owner',at=time.time())
 try:g=valid_grant(c,store,p,name,a)
 except ValueError:g=store.media_dispatch.approve(c,p,name,a['id'])
 reviews[a['id']]=dict(decision='approved',actor='local-owner',at=time.time());return dict(decision='approved')

def project_actions(c,store,p,name):
 pid=contracts.project_id(store.workspace_id,name);result=[]
 for row in c.execute('SELECT body FROM production_actions WHERE workspace=? AND project=? ORDER BY rowid DESC',(store.workspace_id,pid)):
  a=json.loads(row[0])
  if a['connection_id']!=CONNECTION:continue
  q=a['options']['quote'];mapping=c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',(store.workspace_id,pid,a['id'])).fetchone()
  j=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',mapping).fetchone()[0]) if mapping else None
  card=dict(id=a['id'],shot=a['options']['shot'],role=a['role'],model=a['release_id'],prompt=a['inputs']['prompt'],options=a['options']['generation'],estimate=q['money'],estimate_kind=q['kind'],mode='contract-fake' if q['kind']=='fixture' else 'provider-unverified',estimate_expired=q['expires']<=time.time(),approval=p.get('media_action_reviews',{}).get(a['id'],{}).get('decision','required'),job_id=j['id'] if j else None,can_approve=False,can_execute=False,can_decide=not j,reason='입력·모델·예상 비용을 검토하세요.',output_policy='비공개 출력 · 1시간 만료 요청. 정확한 서버 삭제 시각 미확인.')
  if j:
   card['job']={k:j.get(k) for k in ('id','state','failure_code','take','stale_input','cancel_requested')};card['job'].update(recovery=media_recovery.describe(c,store,j),cost=media_bridge.projection(c,j)['cost'],can_cancel=j['state'] in {'prepared','accepted','running','submitting','reconciliation_required'} and not j.get('cancel_requested'))
   if j.get('take'):
    sh=p['shots'].get(card['shot'],{});t=next((t for t in sh.get('takes',[]) if t['id']==j['take']),None)
    if t:card['candidate']=dict(take=t['id'],selected=sh.get('selected')==t['id'],review=next((r['decision'] for r in reversed(sh.get('reviews',[])) if r['take']==t['id']),None),rights_known=bool(t.get('rights') and t['rights']!='사용권 미확인'))
  else:
   pipe=store.media_dispatch
   try:
    if pipe is None:raise ValueError('선택 모델의 서버 연결·견적 검증이 필요합니다.')
    data=pipe.data(c,p,a);pipe.gate(pid,a,data)
    if p['shots'][a['options']['shot']]['revision']!=a['options']['shot_revision'] or model_selection.action_context(p,a)!=a['context_hash']:raise ValueError('장면·입력·모델이 변경되었습니다. 현재 조건으로 다시 준비하세요.')
    plan=next((x for x in p.get('guided_plans',[]) if x['id']==a['plan_id']),None)
    if not plan or plan['context_hash']!=guided.fingerprint(guided.context(p)):raise ValueError('계획 문맥이 변경되었습니다.')
    card['can_approve']=True
    try:valid_grant(c,store,p,name,a);guard(p,a);card.update(approval='approved',can_execute=True,can_approve=False)
    except ValueError:pass
    if not ledger.budget(c,store.workspace_id,'project:'+pid):card.update(can_execute=False,reason='제작 예산을 먼저 설정하세요. 새 지출은 실행하지 않았습니다.')
   except (ValueError,KeyError):card['reason']='연결·전송 허가·입력·견적을 확인해야 합니다. 현재 실행할 수 없습니다.'
  result.append(card)
 return result
