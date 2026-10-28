"""Read-only current-project execution targets. Handles are references, not grants.
No paths, credentials or provider URLs. Execution always revalidates current state.
"""
import json,math,re,time,uuid
from copy import deepcopy
import chat_sessions
import contracts,editing,ontology,project_ontology

def shot_id(p,name):
 return p['shots'][name].get('stable_id') or uuid.uuid5(uuid.NAMESPACE_URL,'loretune-shot:'+json.dumps([p['name'],name])).hex

def shot_key(p,identifier):
 matches=[n for n in p['shots'] if shot_id(p,n)==identifier]
 # Preserve existing local UI/name-key contracts without ambiguous routing.
 if identifier in p['shots'] and identifier not in matches:matches.append(identifier)
 if len(matches)!=1:raise ValueError('current project shot identifier required')
 return matches[0]

def motion_grant_visible(p,name,version,identifier):
 # A missing owner is not evidence that a non-default grant belongs to the
 # default conversation. Preserve only unambiguous pre-conversation records.
 owners=p.get('conversation_owners',{});owner=owners.get(identifier)
 if owner is not None:return owner.get('conversation_id')==chat_sessions.current(p)
 if chat_sessions.current(p)!=chat_sessions.default_id(p):return False
 matches=[x for x in p.get('motion_proposals',[]) if x.get('shot')==name and x.get('status')=='applied' and x.get('applied_revision')==version['id'] and x.get('scene_hash')==version.get('scene_hash')]
 return len(matches)==1 and not matches[0].get('conversation_id') and matches[0].get('id') not in owners

def timeline_grant_visible(p,version,identifier):
 approval=version.get('approval',{})
 if approval.get('id')!=identifier or approval.get('actor')!='local-owner' or approval.get('execution_scope')!='local-render' or approval.get('timeline_version')!=version.get('id'):return False
 owner=p.get('conversation_owners',{}).get(identifier)
 recorded=approval.get('conversation_id')
 if owner is not None:
  cid=owner.get('conversation_id')
  return cid==chat_sessions.current(p) and (recorded is None or recorded==cid)
 if recorded is not None:return recorded==chat_sessions.current(p)
 # An older project with only its original conversation has no competing owner.
 return len(chat_sessions.entries(p))==1 and chat_sessions.current(p)==chat_sessions.default_id(p)

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
   visible=motion_grant_visible(p,name,version,a['id'])
   result.update(approval=dict(id=a['id'] if visible else None,actor=a['actor'],scope=a['scope'],motion_revision=version['id'],scene_hash=a['scene_hash'],matches_current_context=current,requires_revalidation=True),approval_status='recorded' if current else 'stale_context',grant_id=a['id'] if current and visible else None)
  else:result['approval_status']='invalid_record'
 result['proposals']=[dict(proposal_id=x['id'],base_revision=x['base_revision'],status=x['status'],applied=False,requires_human_review=x['status'] in {'proposed','held'}) for x in p.get('motion_proposals',[]) if x.get('shot')==name and x.get('shot_id')==shot_id(p,name) and x['status'] in {'proposed','held','rejected'}][-10:]
 return result

def motion_receipts(p,project_id,observed_revision):
 # A read-only projection of canonical records, never model-authored prose.
 # Keep lookup-time context matching separate from the executor's preflight.
 receipts=[]
 for name in p['shots']:
  m=motion_context(p,name)
  if not m['revision'] and not m['proposals']:continue
  a=m['approval']
  receipts.append(dict(kind='motion-approval-v1',project_id=project_id,
   shot_id=shot_id(p,name),shot_name=name,observed_revision=observed_revision,
   motion_revision=m['revision'],composition_saved=m['scene'] is not None,
   approval_status=m['approval_status'],approval=deepcopy(a),
   matches_current_context=a['matches_current_context'] if a else None,
   execution_check='not_run',proposals=deepcopy(m['proposals']),
   timeline_adoption='separate',final_delivery='outside_this_scope'))
 return receipts

def music_input(c,p,timeline):
 # Project audio is shared across its conversations. Disclose stored inspection
 # facts only; a selected source, a saved timeline and a user range can differ.
 def seconds(value):
  return type(value) in (int,float) and 0<=value<=2**53-1 and math.isfinite(value)
 def source(identifier):
  if type(identifier) is not int or identifier<1:return None
  audio=next((a for a in p.get('audio_versions',[]) if a.get('id')==identifier),{})
  metadata=audio.get('metadata');duration=metadata.get('duration') if isinstance(metadata,dict) else None
  valid=seconds(duration) and duration>0
  rights=audio.get('rights')
  row=c.execute('SELECT blocked FROM asset_rights WHERE sha256=?',(audio.get('sha256'),)).fetchone()
  return dict(audio_version=identifier,duration_seconds=duration if valid else None,
   metadata_status='recorded' if valid else 'unavailable',
   rights_status='recorded' if isinstance(rights,str) and rights.strip() and rights!='사용권 미확인' else 'unconfirmed',
   blocked=bool(row and row[0]) if audio else None)
 selected=source(p.get('audio_selected'));used=source(timeline.get('audio'))
 result=dict(scope='current-project-shared',selected_source=selected,timeline_source=used,
  range=dict(status='unconfirmed'),requires_revalidation=True)
 head=p.get('music_head')
 if head is None:return result
 version=next((v for v in p.get('music_versions',[]) if v.get('id')==head),{})
 audio=source(version.get('audio'));start=version.get('start');end=version.get('end')
 if (type(head) is not int or head<1 or version.get('source')!='user' or not audio or
     audio['metadata_status']!='recorded' or not seconds(start) or not seconds(end) or
     not start<end<=audio['duration_seconds']):
  result['range']=dict(status='invalid_record');return result
 result['range']=dict(status='confirmed',music_version=head,audio_version=version['audio'],
  start_seconds=start,end_seconds=end,source='user',
  matches_selected_source=version['audio']==p.get('audio_selected'),matches_timeline_source=version['audio']==timeline.get('audio'))
 return result

def overlay_page_offset(query):
 if not query or not query.startswith('motion-overlay-sources'):return 0
 match=re.fullmatch(r'motion-overlay-sources offset=(\d{1,7})',query)
 if not match:raise ValueError('motion-overlay-sources requires offset=0 or another bounded nonnegative integer')
 return int(match[1])

def motion_overlay_sources(p,query=None):
 # Metadata pages only: never duplicate full historical motion scenes or grants
 # into model context. The existing query tool can request the next bounded page.
 offset=overlay_page_offset(query);limit=32
 records=[(name,v) for name,shot in p['shots'].items() for v in shot.get('motion_versions',[])
          if type(v.get('id')) is int and isinstance(v.get('approval'),dict) and v['approval'].get('actor')=='local-owner'
          and v['approval'].get('scope')=='local-motion-candidate']
 records.sort(key=lambda item:(shot_id(p,item[0]),item[1]['id']))
 items=[]
 for name,version in records[offset:offset+limit]:
  item=dict(source_shot_id=shot_id(p,name),motion_revision=version['id'],requires_revalidation=True)
  try:
   validated=editing.approved_motion(version)
   item.update(scene_hash=validated['scene_hash'],duration_seconds=validated['scene']['frame_count']/24,
               layer_count=len(validated['scene']['layers']),approval_status='recorded_immutable_source')
  except (ValueError,KeyError,TypeError):item['approval_status']='invalid_record'
  items.append(item)
 next_offset=offset+limit
 return dict(items=items,offset=offset,limit=limit,total_records=len(records),
             next_query='motion-overlay-sources offset='+str(next_offset) if next_offset<len(records) else None,
             note='Approved immutable source metadata, not an execution grant. Match source_shot_id to shots[].name. Current font/scene/rights still revalidate. Source body is edited through a new motion proposal; source background is excluded when overlaying.')

def work_status(c,store,p,name,observed_revision):
 # Job observations are deliberately outside canonical project fingerprints.
 # Preserve per-table insertion order: older tables have no creation timestamp.
 started=time.time();transaction_snapshot=c.in_transaction
 limit=8;cid=chat_sessions.current(p);pid=contracts.project_id(store.workspace_id,name)
 states={'queued','running','completed','cancel_requested','cancelled','failed','interrupted','outcome_unknown',
         'prepared','claimed','collected','blocked','expired','submitting','submission_blocked','accepted',
         'cancel_pending','cancel_sent','result_ready','downloading','imported','import_blocked','cancelled_result',
         'reconciliation_required','image_recovery_pending','image_recovery_running','awaiting_continuation_approval','continuation_rejected','blocked_before_message',
         'response_validation_failed','limit_reached'}
 modes={'contract-fake','contract-live-test','anthropic-live','openai-live','xai-live','rehearsal','provider-unverified','live-unverified','disconnected'}
 def number(value,maximum=2**53-1):
  return value if type(value) in (int,float) and 0<=value<=maximum and math.isfinite(value) else None
 def integer(value):return value if type(value) is int and 0<=value<=2**53-1 else None
 def digest(value):return value if isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) else None
 def owned(job,*,registry=True):
  identifier=job.get('id');recorded=job.get('conversation_id')
  if not isinstance(identifier,str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}',identifier):return False
  owner=p.get('conversation_owners',{}).get(identifier)
  if owner is not None and owner.get('conversation_id')!=cid:return False
  if recorded is not None and recorded!=cid:return False
  return chat_sessions.owns(p,identifier) if registry else True
 def item(job,kind,mode,output_kind,version_kind=None,version=None,sha=None,registered=False):
  state=job.get('status',job.get('state'))
  return dict(id=job['id'],kind=kind,execution_mode=mode if isinstance(mode,str) and mode in modes|{'local-render','local-motion','local-3d-still'} else 'unrecognized',
   state=state if isinstance(state,str) and state in states else 'unavailable' if state is None else 'unrecognized_state',
   progress_percent=number(job.get('progress'),100),record_revision=integer(job.get('revision')),
   input_version=dict(kind=version_kind,value=integer(version)) if version_kind else None,
   output_kind=output_kind,output_sha256=digest(sha),output_registered=bool(registered and digest(sha)),
   created_at=number(job.get('created')),updated_at=number(job.get('updated')))
 groups=[]
 def collect(source,rows,projector):
  found=[]
  for row in rows:
   value=projector(json.loads(row[0]))
   if value is None:continue
   found.append(value)
   if len(found)>limit:break
  groups.append(dict(source=source,items=found[:limit],truncated=len(found)>limit,
                     ordering='source insertion order descending; not cross-source creation/update order'))
 def local(job):
  if job.get('song')!=name or not owned(job):return
  kind=job.get('kind','local-render');version_kind=None;version=None
  if kind not in ('local-render','local-motion','local-3d-still'):kind='unrecognized-local-job'
  if kind=='local-render':version_kind='timeline';version=job.get('snapshot',{}).get('timeline',{}).get('id')
  elif kind=='local-motion':version_kind='motion';version=job.get('motion',{}).get('id')
  elif kind=='local-3d-still':version_kind='scene_3d';version=job.get('scene_revision')
  output='image' if kind=='local-3d-still' else 'video' if kind in {'local-render','local-motion'} else 'unknown'
  download=job.get('download')
  return item(job,kind,kind,output,version_kind,version,job.get('sha256'),
              job.get('status')=='completed' and output!='unknown' and isinstance(download,str) and download.startswith(('/assets/','/exports/')))
 def provider(job):
  context=job.get('context',{});binding=context.get('action_binding')
  if context.get('song')!=name or not owned(job):return
  if context.get('conversation_id') is not None and context['conversation_id']!=cid:return
  if binding is not None and (not isinstance(binding,dict) or (binding.get('workspace'),binding.get('project'))!=(store.workspace_id,pid)):return
  output=context.get('output_kind');output=output if output in ('image','video') else 'unknown'
  return item(job,'provider-generation',job.get('mode'),output,'shot',context.get('shot_revision'),
              job.get('asset_sha256'),job.get('state')=='imported' and integer(job.get('take')) not in (None,0))
 def rehearsal(job):
  if not owned(job):return
  action=job.get('action',{});result=job.get('result') or {};output=result.get('output_slot',action.get('role'))
  return item(job,'rehearsal-media',job.get('mode'),output if output in ('image','video') else 'unknown',
              'plan',action.get('plan_revision'),result.get('sha256'),False)
 def general(job):
  if not owned(job,registry=False) or job.get('project') not in (None,pid):return
  return item(job,'general-chat',job.get('mode'),'text')
 def legacy(job):
  if not owned(job,registry=False) or (job.get('conversation_id') or chat_sessions.default_id(p))!=cid:return
  if job.get('project') not in (None,pid):return
  return item(job,'legacy-chat',job.get('mode'),'text')
 collect('local_jobs',c.execute('SELECT body FROM jobs ORDER BY rowid DESC'),local)
 collect('provider_jobs',c.execute('SELECT body FROM generation_jobs ORDER BY rowid DESC'),provider)
 collect('rehearsal_jobs',c.execute('SELECT body FROM action_jobs WHERE workspace=? AND project=? ORDER BY rowid DESC',(store.workspace_id,pid)),rehearsal)
 collect('general_chat',c.execute('SELECT body FROM general_chat_turns WHERE project=? AND conversation=? ORDER BY rowid DESC',(pid,cid)),general)
 collect('legacy_chat',c.execute('SELECT body FROM chat_turns WHERE project=? ORDER BY rowid DESC',(pid,)),legacy)
 return dict(scope='current-project-current-conversation',observation_started_at=started,observed_at=time.time(),observed_revision=observed_revision,
  transaction_snapshot=transaction_snapshot,
  limit_per_source=limit,sources=groups,collaboration=dict(available=False,reason='single-local-workspace; no authenticated team/presence data'),
  note='Stored status during this lookup, not a grant, model vision, verified file contents or final-output approval. Output SHA/registration are recorded metadata only. Caller transaction provides a snapshot when active; otherwise sources are sequential observations. Requery for newer status; no automatic retry or cost change.')

SCENE_STATUS_LIMIT=32

def scene_status(c,store,p,name,observed_revision):
 # Current conversation only. Never loads trusted 3D configuration or runs a renderer.
 import scene_project
 scenes=scene_project.status(c,store,p,name,chat_sessions.current(p))
 return dict(scope='current-project-current-conversation',observed_revision=observed_revision,
  scenes_3d=scenes[-SCENE_STATUS_LIMIT:],scenes_3d_total=len(scenes),scenes_3d_truncated=len(scenes)>SCENE_STATUS_LIMIT,
  connection=dict(available=scene_project.capability(store)['available'],external_transmission=False),
  note='Stored 3D scene heads and pending proposals, not an execution grant, render result or final-output approval. requires_review means the shot context or project ontology changed since that version or pending proposal was saved, so approval or rendering will be refused. Pending proposals are proposed/held ones based on the current head; stale_total counts older ones that can no longer be approved. head 0 means no approved version: its first draft is reviewed in Scene Studio and change proposals need base_revision equal to a head of 1 or more. Lists keep the latest '+str(SCENE_STATUS_LIMIT)+' scenes and 10 pending proposals per scene; *_total and *_truncated report omissions. Approval and rendering stay human actions in Scene Studio.')

def read(c,store,p,name,query=None):
 w=store.workspace_id;pid=contracts.project_id(w,name);shots=[]
 observed,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
 if query=='work-status':return dict(work_status=work_status(c,store,p,name,observed))
 if query=='scene-status':return dict(scene_status=scene_status(c,store,p,name,observed))
 source_projects=json.loads(body)['projects'];source_projects[name]=p
 projected={'shots':deepcopy(p['shots'])}
 chat_sessions.project_references(source_projects,projected,chat_sessions.current(p))
 for n,s in p['shots'].items():
  takes=[]
  for t in s['takes']:
   if not chat_sessions.take_visible(p,s,t):continue
   row=c.execute('SELECT blocked FROM asset_rights WHERE sha256=?',(t['sha256'],)).fetchone()
   takes.append(dict(take_id=t['id'],sha256=t['sha256'],rights=t.get('rights','사용권 미확인'),blocked=bool(row and row[0]),review=next((r['decision'] for r in reversed(s.get('reviews',[])) if r['take']==t['id']),None)))
  refs=projected['shots'][n]
  versions=deepcopy(refs.get('reference_versions',[]))
  for version in versions:
   for reference in version.get('roles',{}).values():reference.pop('asset',None)
  selected=s['selected'] if s['selected'] in {take['take_id'] for take in takes} else None
  shots.append(dict(shot_id=shot_id(p,n),name=n,revision=s['revision'],selected_take=selected,takes=takes,reference_head=refs.get('reference_head'),reference_versions=versions))
  shots[-1]['motion']=motion_context(p,n)
 t=editing.current(p);approval=t.get('approval',{})
 visible_takes={shot['name']:{take['take_id'] for take in shot['takes']} for shot in shots}
 timeline=dict(version=t['id'],clips=[dict(index=i,shot_id=shot_id(p,x['shot']),shot_name=x['shot'],take=x['take'] if x['take'] in visible_takes.get(x['shot'],set()) else None,trim=x['trim'],duration=x['duration']) for i,x in enumerate(t['clips'])],audio_version=t['audio'],audio_offset=t['audio_offset'],captions=deepcopy(t['subtitles']),profile=t['profile'],grant_id=approval.get('id') if timeline_grant_visible(p,t,approval.get('id')) else None)
 for projected_clip,clip in zip(timeline['clips'],t['clips']):
  if clip.get('motion_overlay'):
   overlay=deepcopy(clip['motion_overlay']);source=overlay.pop('shot')
   overlay.update(source_shot_name=source,source_shot_id=shot_id(p,source) if source in p['shots'] else None)
   projected_clip['motion_overlay']=overlay
 grants=[json.loads(r[0]) for r in c.execute('SELECT body FROM execution_grants WHERE workspace=? AND project=?',(w,pid))];actions=[]
 for row in c.execute('SELECT body FROM production_actions WHERE workspace=? AND project=?',(w,pid)):
  a=json.loads(row[0])
  if not chat_sessions.owns(p,a['id']):continue
  handles=[dict(grant_id=g['id'],expires=g['expires'],price_revision=g['price_revision'],money=g['money'].get(a['id'])) for g in grants if g['state']=='active' and g['expires']>time.time() and g['action_hashes'].get(a['id'])==a['hash']]
  actions.append(dict(action_id=a['id'],plan_id=a['plan_id'],plan_revision=a['plan_revision'],role=a['role'],model=a['release_id'],mode=a['mode'],shot_id=shot_id(p,a['options']['shot']) if a['options'].get('shot') in p['shots'] else None,approval_handles=handles))
 return dict(shots=shots,timeline=timeline,music_input=music_input(c,p,t),server_receipts=motion_receipts(p,pid,observed),
             supported_context_queries=[dict(query='work-status',purpose='Current conversation work status; bounded recorded metadata, not participant presence or video pixels'),
               dict(query='scene-status',purpose='Current conversation 3D scene heads, approval state and pending proposals; no grants, asset paths or scene bodies')],
             motion_overlay_sources=motion_overlay_sources(p,query),
             motion_overlay_contract=dict(commands=['set_motion_overlay','clear_motion_overlay'],clock='clip-local seconds; source frame0 starts at start; end is exclusive',
               offsets='translation in original1920x1080 logical pixels; aspect-fit to output',source_background='excluded; layer motion/alpha/in-out retained',
               sources_per_clip=1,source_layers_max=8,source_duration_seconds_range=[3,4],
               approval='review: proposal then human edit review; full_access: whitelisted non-deletion placement changes may save a new unapproved agent draft; remove/clear still require human review; final timeline/output approval is separate in every mode',
               preview='saved timeline UI frame preview, not a model execution tool',
               mesh_generation='not supported by these tools; optional internal3D workflows are separate capabilities'),
             plans=[dict(plan_id=x['id'],version=x['version'],state=x['status']) for x in p.get('guided_plans',[])],actions=actions,ontology_revision=ontology.snapshot(c,project_ontology.scope(w,pid))['revision'],note='현재 작품의 읽기 전용 대상. 조회된 승인도 실행 시 권리·입력·가격·만료를 다시 검사합니다. 승인 생성 권한이 아닙니다.')
