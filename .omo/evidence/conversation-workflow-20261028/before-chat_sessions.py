"""Conversation ownership over existing local Store transactions, not tenant auth.

No migration on read. Legacy records belong to a deterministic default. Private
proposals are projected into existing services and merged under BEGIN IMMEDIATE.
Shared settings still use their original version/approval services.
"""
from copy import deepcopy
import json,time,uuid
from loretune import Conflict
import guided

LISTS=('conversation','chat_plans','guided_plans','production_runs',
       'timeline_edit_proposals','motion_proposals','render_estimates','execution_cards')
TABLES=('chat_turns','production_actions','execution_grants','action_jobs',
        'generation_jobs','jobs','ontology_proposals')
LOCAL_ACTIONS={'conversation_create','conversation_model','chat_turn','chat_cancel',
 'production_run','production_tool','model_handoff','guided_plan','chat_plan',
 'ontology_propose','motion_propose','motion_restore','media_prepare','prepare_action'}

def default_id(p):
 if 'name' not in p:return 'project-default'
 return uuid.uuid5(uuid.NAMESPACE_URL,'loretune-conversation-default:'+p['name']).hex

def entries(p):
 return deepcopy(p.get('chat_sessions') or [dict(id=default_id(p),title='기존 대화',revision=0,chat_selection=None,model_revision=0)])

def resolve(p,identifier=None):
 identifier=identifier or default_id(p)
 value=next((x for x in entries(p) if x['id']==identifier),None)
 if value is None:raise ValueError('현재 작품의 대화를 선택하세요.')
 return value

def current(p):return p.get('_conversation_id') or default_id(p)

def selected_chat(p,identifier=None):
 session=resolve(p,identifier or current(p))
 if session.get('chat_override'):return session['chat_selection']
 return p.get('model_settings',{}).get('selections',{}).get('chat')

def general_chat_active(c,pid,conversation=None):
 if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='general_chat_turns'").fetchone():return False
 return any((conversation is None or t.get('conversation_id')==conversation) and
            t.get('status') in {'queued','running','cancel_requested','outcome_unknown','awaiting_continuation_approval'}
            for t in (json.loads(row[0]) for row in c.execute('SELECT body FROM general_chat_turns WHERE project=?',(pid,))))

def change_model(c,p,pid,selection,expected):
 import model_selection
 model_selection.validate_selection('chat',selection)
 session=resolve(p,current(p))
 if type(expected) is not int or expected!=session['model_revision']:raise Conflict('대화 모델 선택이 변경됐습니다.')
 turns=[json.loads(row[0]) for row in c.execute('SELECT body FROM chat_turns WHERE project=?',(pid,))]
 active=[t for t in turns if (t.get('conversation_id') or default_id(p))==current(p) and t['status'] in {'queued','running','cancel_requested','outcome_unknown'}]
 general=[]
 if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='general_chat_turns'").fetchone():
  general=[json.loads(row[0]) for row in c.execute('SELECT body FROM general_chat_turns WHERE project=?',(pid,))]
  general=[t for t in general if t.get('conversation_id')==current(p) and t['status'] in {'queued','running','cancel_requested','outcome_unknown','awaiting_continuation_approval'}]
 active+=general
 if any(t['status'] in {'cancel_requested','outcome_unknown'} for t in active):
  raise ValueError('취소 중이거나 결과 미확정인 응답을 먼저 확인하세요. 실행 모델은 바꾸지 않았습니다.')
 if len(active)>1:raise ValueError('진행 중인 대화 상태를 먼저 확인하세요.')
 p.setdefault('chat_sessions',entries(p))
 item=next(x for x in p['chat_sessions'] if x['id']==current(p))
 if active:
  item.update(pending_chat_selection=dict(selection=selection,after_turn=active[0]['id']),model_revision=expected+1)
  if general:
   item['pending_chat_selection'].update(execution_model_revision=general[0]['binding']['model_revision'],reserved_model_revision=expected+1,execution_run=general[0]['run'],execution_selection=general[0]['binding']['selection'])
  return deepcopy(item)
 item.pop('pending_chat_selection',None)
 item.update(chat_override=True,chat_selection=selection,model_revision=expected+1)
 for run in p.get('production_runs',[]):
  if run['state']=='accepting_tools':run['state']='superseded'
 return deepcopy(item)

def execution_model_revision(p,run):
 """Honor only a server-bound reservation; general claim_tool also checks the SQL turn."""
 session=resolve(p,current(p));pending=session.get('pending_chat_selection') or {}
 if (run.get('conversation_id')==current(p) and pending.get('after_turn') and
     p.get('conversation_owners',{}).get(pending['after_turn'],{}).get('conversation_id')==current(p) and
     pending.get('execution_run')==run['id'] and
     pending.get('execution_selection')==selected_chat(p) and
     pending.get('reserved_model_revision')==session['model_revision'] and
     pending.get('execution_model_revision')==run.get('conversation_model_revision')):
  return pending['execution_model_revision']
 return session['model_revision']


def apply_completed_selection(p,turn):
 """Apply only the choice tied to this completed turn inside its DB transaction."""
 cid=turn.get('conversation_id') or default_id(p)
 item=next((x for x in p.get('chat_sessions',[]) if x['id']==cid),None)
 pending=item.get('pending_chat_selection') if item else None
 if not pending or pending.get('after_turn')!=turn['id']:return False
 item.update(chat_override=True,chat_selection=pending['selection'],revision=item['revision']+1)
 item.pop('pending_chat_selection',None)
 for run in p.get('production_runs',[]):
  if run['id']!=turn['run'] and run['state']=='accepting_tools' and owner(p,run['id'])==cid:run['state']='superseded'
 return True

def owner(p,identifier):
 return p.get('conversation_owners',{}).get(identifier,{}).get('conversation_id',default_id(p))

def owns(p,identifier):return owner(p,identifier)==current(p)

def item_owner(p,item):return item.get('conversation_id') or owner(p,item.get('id',''))

def own_items(p,items):return [x for x in items if item_owner(p,x)==current(p)]

def shared_fingerprint(p):
 # Exclude only explicitly conversation-local records. All shared source,
 # approval and version changes remain conflicts, including another tab's edits.
 return guided.fingerprint({k:v for k,v in p.items() if k not in LISTS and k not in
  {'chat_sessions','conversation_owners'} and not k.startswith('_')})

def row_ids(c):
 return {table:{r[0] for r in c.execute('SELECT id FROM '+table)} for table in TABLES}

def create(p,title):
 if not isinstance(title,str) or not 1<=len(title.strip())<=80:raise ValueError('대화 이름은 1–80자입니다.')
 p.setdefault('chat_sessions',entries(p))
 item=dict(id=uuid.uuid4().hex,title=title.strip(),revision=0,chat_selection=None,model_revision=0,created=time.time())
 p['chat_sessions'].append(item)
 return deepcopy(item)

def guard_refs(p,data):
 if isinstance(data,dict):
  for k,v in data.items():
   if k in {'run','plan','plan_id','proposal','proposal_id','turn','job','job_id','action_id','grant_id','preparation'} and isinstance(v,str):
    if k=='grant_id':
     timelines=[version for version in p.get('timeline_versions',[]) if version.get('approval',{}).get('id')==v]
     if timelines:
      import production_context
      if len(timelines)!=1 or not production_context.timeline_grant_visible(p,timelines[0],v):
       raise ValueError('현재 대화에서 확인한 출력 승인만 사용할 수 있습니다.')
      continue
     matches=[(name,version) for name,shot in p.get('shots',{}).items() for version in shot.get('motion_versions',[]) if version.get('approval',{}).get('id')==v]
     if matches:
      import production_context
      if len(matches)!=1 or not production_context.motion_grant_visible(p,matches[0][0],matches[0][1],v):
       raise ValueError('현재 대화에서 확인한 모션 승인만 사용할 수 있습니다.')
    if not owns(p,v):raise ValueError('다른 대화의 미승인 제안·작업은 이 대화에서 변경할 수 없습니다.')
   if isinstance(v,(dict,list)):guard_refs(p,v)
 elif isinstance(data,list):
  for v in data:guard_refs(p,v)

def enter(p,identifier):
 session=resolve(p,identifier);before=deepcopy(p)
 p['_conversation_id']=session['id']
 for key in LISTS:
  if key in p:p[key]=own_items(p,p[key])
 # Preserve project settings and media approvals; chat override is resolved
 # separately and never rewrites the shared settings snapshot.
 return before

def leave(c,p,before,rows):
 cid=current(p);owners=p.setdefault('conversation_owners',{})
 for table,prior in rows.items():
  for identifier in {r[0] for r in c.execute('SELECT id FROM '+table)}-prior:
   owners[identifier]=dict(conversation_id=cid,kind=table)
 for key in LISTS:
  old=before.get(key,[]);visible=p.get(key,[])
  for x in visible:
   # Legacy records keep their bytes. Only new records receive explicit scope.
   if x not in old and not any(x.get('id') and x.get('id')==y.get('id') for y in old):
    x['conversation_id']=cid
    if isinstance(x.get('id'),str):owners[x['id']]=dict(conversation_id=cid,kind=key)
  hidden=[x for x in old if item_owner(before,x)!=cid]
  if hidden or key in p:p[key]=hidden+visible
 # Attach new local uploads to their originating conversation without changing
 # IDs or hiding records from services that allocate monotonically numbered Takes.
 for name,shot in p.get('shots',{}).items():
  prior={t['id'] for t in before.get('shots',{}).get(name,{}).get('takes',[])}
  for take in shot['takes']:
   if take['id'] not in prior:take.setdefault('conversation_id',cid)
  prior_preparations={x['id'] for x in before.get('shots',{}).get(name,{}).get('generation_preparations',[])}
  for preparation in shot.get('generation_preparations',[]):
   if preparation['id'] not in prior_preparations:
    preparation.setdefault('conversation_id',cid)
    owners[preparation['id']]=dict(conversation_id=cid,kind='generation_preparations')
 p.pop('_conversation_id',None)
 p.setdefault('chat_sessions',entries(p))
 resolve_item=next(x for x in p['chat_sessions'] if x['id']==cid)
 resolve_item['revision']+=1

def scoped(p,identifier=None):
 result=deepcopy(p);enter(result,identifier)
 return result

def take_owner(p,take):
 return take.get('conversation_id') or owner(p,take.get('action_id') or take.get('provenance',{}).get('job',''))

def take_visible(p,shot,take):
 # Pre-conversation assets remain shared compatibility records. New candidates
 # become shared only after an explicit approved review.
 origin=take.get('conversation_id') or p.get('conversation_owners',{}).get(take.get('action_id') or take.get('provenance',{}).get('job',''),{}).get('conversation_id')
 approved=next((r['decision']=='approved' for r in reversed(shot.get('reviews',[])) if r['take']==take['id']),False)
 return origin is None or origin==current(p) or approved

def source_take_visible(projects,source_song,source_shot,source_take,conversation_id,sha256=None):
 project=projects.get(source_song)
 shot=project.get('shots',{}).get(source_shot) if project else None
 take=next((t for t in shot.get('takes',[]) if t['id']==source_take),None) if shot else None
 if take is None or sha256 is not None and take.get('sha256')!=sha256:return False
 return take_visible({**project,'_conversation_id':conversation_id},shot,take)

def reference_visible(projects,version,conversation_id):
 return all(source_take_visible(projects,r.get('song'),r.get('shot'),r.get('take'),conversation_id,r.get('sha256'))
            for r in version.get('roles',{}).values())

def project_references(projects,project,conversation_id):
 """Keep stored references intact; only expose versions whose sources are visible."""
 for shot in project.get('shots',{}).values():
  if 'generation_preparations' in shot:
   shot['generation_preparations']=[x for x in shot['generation_preparations']
    if item_owner(project,x)==conversation_id and source_take_visible(projects,x['source'].get('song'),
      x['source'].get('shot'),x['source'].get('take'),conversation_id,x['source'].get('sha256'))]
  if 'reference_versions' not in shot:continue
  versions=shot['reference_versions']
  visible=[v for v in versions if reference_visible(projects,v,conversation_id)]
  if len(visible)!=len(versions):
   shot['reference_visibility']={'hidden_versions':len(versions)-len(visible)}
   if shot.get('reference_head') not in {v['id'] for v in visible}:shot['reference_head']=None
  shot['reference_versions']=visible

def check_takes(p,data):
 def check(name,number):
  shot=p.get('shots',{}).get(name)
  if not shot:return
  take=next((x for x in shot['takes'] if x['id']==number),None)
  if take and not take_visible(p,shot,take):raise ValueError('다른 대화의 미승인 Take는 먼저 해당 대화에서 검토하세요.')
 if isinstance(data,dict):
  if 'shot' in data and 'take' in data:check(data['shot'],data['take'])
  if 'source_shot_id' in data:
   import production_context
   check(production_context.shot_key(p,data['source_shot_id']),data.get('source_take_id'))
  for v in data.values():
   if isinstance(v,(dict,list)):check_takes(p,v)
 elif isinstance(data,list):
  for x in data:check_takes(p,x)

def public_project(p,identifier=None):
 full=p;out=scoped(p,identifier);cid=current(out)
 out['conversations']=entries(full)
 out['active_conversation']=dict(resolve(full,cid),shared_version=shared_fingerprint({k:v for k,v in full.items() if k not in PUBLIC_FIELDS}))
 for field in ('chat_turns','ontology_proposals','media_actions','rehearsal_jobs'):
  if field in out:out[field]=own_items(out,out[field])
 for name,shot in out.get('shots',{}).items():
  shot['takes']=[t for t in shot['takes'] if take_visible(out,shot,t)]
  if shot.get('selected') not in {t['id'] for t in shot['takes']}:shot['selected']=None
  import production_context
  motion=production_context.motion_context(out,name)
  shot['motion_grant_available']=bool(motion['grant_id'])
  for version in shot.get('motion_versions',[]):
   approval=version.get('approval',{});identifier=approval.get('id')
   if isinstance(identifier,str) and not production_context.motion_grant_visible(out,name,version,identifier):approval['id']=None
 import production_context
 for version in out.get('timeline_versions',[]):
  approval=version.get('approval',{});identifier=approval.get('id')
  if isinstance(identifier,str) and not production_context.timeline_grant_visible(out,version,identifier):approval['id']=None
 for receipt in out.get('chat_receipts',[]):receipt['proposals']=[x for x in receipt.get('proposals',[]) if owns(out,x['proposal_id'])]
 out.pop('conversation_owners',None);out.pop('chat_sessions',None);out.pop('_conversation_id',None)
 return out

# Enriched Store.state fields are not persisted source/version inputs.
PUBLIC_FIELDS={'ontology','ontology_proposals','lineage','chat_turns','chat_receipts','chat_connection',
 'media_connections','image_connection','media_actions','rehearsal_jobs','preflight'}
