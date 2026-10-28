"""Read-only current-project execution targets. Handles are references, not grants.
No paths, credentials or provider URLs. Execution always revalidates current state.
"""
import json,time,uuid
from copy import deepcopy
import contracts,editing,ontology,project_ontology

def shot_id(p,name):
 return p['shots'][name].get('stable_id') or uuid.uuid5(uuid.NAMESPACE_URL,'loretune-shot:'+json.dumps([p['name'],name])).hex

def shot_key(p,identifier):
 matches=[n for n in p['shots'] if shot_id(p,n)==identifier]
 # Preserve existing local UI/name-key contracts without ambiguous routing.
 if identifier in p['shots'] and identifier not in matches:matches.append(identifier)
 if len(matches)!=1:raise ValueError('current project shot identifier required')
 return matches[0]

def motion_context(p,name):
 # Approval is a stored, version-bound record, never inferred from ontology or
 # a pending proposal. Even a matching record is not a completed execution check.
 import guided,motion_scene
 s=p['shots'][name];head=s.get('motion_head',0)
 version=next((v for v in s.get('motion_versions',[]) if v['id']==head),None)
 result=dict(revision=head,scene=deepcopy(version['scene']) if version else None,grant_id=None,approval=None,approval_status='none',requires_revalidation=True)
 if version:
  a=version.get('approval',{});digest=guided.fingerprint(version['scene'])
  if a.get('actor')=='local-owner' and a.get('scope')=='local-motion-candidate' and isinstance(a.get('id'),str) and a['id'] and digest==version.get('scene_hash')==a.get('scene_hash'):
   current=version.get('context')==motion_scene.context(p,name)
   result.update(approval=dict(id=a['id'],actor=a['actor'],scope=a['scope'],motion_revision=version['id'],scene_hash=a['scene_hash'],matches_current_context=current,requires_revalidation=True),approval_status='recorded' if current else 'stale_context',grant_id=a['id'] if current else None)
  else:result['approval_status']='invalid_record'
 result['proposals']=[dict(proposal_id=x['id'],base_revision=x['base_revision'],status=x['status'],applied=False,requires_human_review=x['status'] in {'proposed','held'}) for x in p.get('motion_proposals',[]) if x.get('shot')==name and x.get('shot_id')==shot_id(p,name) and x['status'] in {'proposed','held','rejected'}][-10:]
 return result

def read(c,store,p,name):
 w=store.workspace_id;pid=contracts.project_id(w,name);shots=[]
 for n,s in p['shots'].items():
  takes=[]
  for t in s['takes']:
   row=c.execute('SELECT blocked FROM asset_rights WHERE sha256=?',(t['sha256'],)).fetchone()
   takes.append(dict(take_id=t['id'],sha256=t['sha256'],rights=t.get('rights','사용권 미확인'),blocked=bool(row and row[0]),review=next((r['decision'] for r in reversed(s.get('reviews',[])) if r['take']==t['id']),None)))
  shots.append(dict(shot_id=shot_id(p,n),name=n,revision=s['revision'],selected_take=s['selected'],takes=takes,reference_head=s.get('reference_head'),reference_versions=deepcopy(s.get('reference_versions',[]))))
  shots[-1]['motion']=motion_context(p,n)
 t=editing.current(p);approval=t.get('approval',{})
 timeline=dict(version=t['id'],clips=[dict(index=i,shot_id=shot_id(p,x['shot']),shot_name=x['shot'],take=x['take'],trim=x['trim'],duration=x['duration']) for i,x in enumerate(t['clips'])],audio_version=t['audio'],audio_offset=t['audio_offset'],captions=deepcopy(t['subtitles']),profile=t['profile'],grant_id=approval.get('id') if approval.get('actor')=='local-owner' and approval.get('execution_scope')=='local-render' else None)
 grants=[json.loads(r[0]) for r in c.execute('SELECT body FROM execution_grants WHERE workspace=? AND project=?',(w,pid))];actions=[]
 for row in c.execute('SELECT body FROM production_actions WHERE workspace=? AND project=?',(w,pid)):
  a=json.loads(row[0]);handles=[dict(grant_id=g['id'],expires=g['expires'],price_revision=g['price_revision'],money=g['money'].get(a['id'])) for g in grants if g['state']=='active' and g['expires']>time.time() and g['action_hashes'].get(a['id'])==a['hash']]
  actions.append(dict(action_id=a['id'],plan_id=a['plan_id'],plan_revision=a['plan_revision'],role=a['role'],model=a['release_id'],mode=a['mode'],shot_id=shot_id(p,a['options']['shot']) if a['options'].get('shot') in p['shots'] else None,approval_handles=handles))
 return dict(shots=shots,timeline=timeline,plans=[dict(plan_id=x['id'],version=x['version'],state=x['status']) for x in p.get('guided_plans',[])],actions=actions,ontology_revision=ontology.snapshot(c,project_ontology.scope(w,pid))['revision'],note='현재 작품의 읽기 전용 대상. 조회된 승인도 실행 시 권리·입력·가격·만료를 다시 검사합니다. 승인 생성 권한이 아닙니다.')
