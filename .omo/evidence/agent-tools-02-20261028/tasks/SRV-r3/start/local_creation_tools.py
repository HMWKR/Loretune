"""Model proposals and explicitly bounded agent drafts through existing services.
Agent drafts never approve canon/output, forge human reviews, or add provider costs.
Caller owns the Store transaction; normal Store request/tool idempotency applies.
"""
from copy import deepcopy
import json,time,uuid
import contracts,editing,guided,ontology,project_ontology
import action_assets,chat_sessions,production_context
from loretune import Conflict

CHANGE_SCHEMA={'type':'array','minItems':1,'maxItems':30,'items':{'type':'object','properties':{'clip_index':{'type':'integer','minimum':0},'take':{'type':'integer','minimum':1},'trim':{'type':'number','minimum':0},'duration':{'type':'number','minimum':0.125}},'required':['clip_index','take','trim','duration'],'additionalProperties':False}}
def _command_schema(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
OVERLAY_OPERATIONS={'set_motion_overlay','clear_motion_overlay'}
COMMAND_SCHEMA=dict(type='array',minItems=1,maxItems=30,items=dict(anyOf=[
 _command_schema(dict(op=dict(type='string',enum=['reorder_clips']),order=dict(type='array',minItems=1,maxItems=30,items=dict(type='integer',minimum=0)))),
 _command_schema(dict(op=dict(type='string',enum=['set_captions']),cues=dict(type='array',maxItems=100,items=_command_schema(dict(start=dict(type='number',minimum=0),end=dict(type='number',minimum=0),text=dict(type='string')))))),
 _command_schema(dict(op=dict(type='string',enum=['set_audio_offset']),audio_version=dict(type='integer',minimum=1),source_offset_seconds=dict(type='number',minimum=0))),
 _command_schema(dict(op=dict(type='string',enum=['set_clip']),**deepcopy(CHANGE_SCHEMA['items']['properties']))),
 _command_schema(dict(op=dict(type='string',enum=['remove_clips']),clip_indices=dict(type='array',minItems=1,maxItems=30,items=dict(type='integer',minimum=0)))),
 _command_schema(dict(op=dict(type='string',enum=['append_clips']),clips=dict(type='array',minItems=1,maxItems=30,items=_command_schema(dict(source_shot_id=dict(type='string',minLength=1,maxLength=200),source_take_id=dict(type='integer',minimum=1),trim=dict(type='number',minimum=0),duration=dict(type='number',minimum=0.125)))))),
 _command_schema(dict(op=dict(type='string',enum=['set_motion_overlay']),clip_index=dict(type='integer',minimum=0),
   source_shot_id=dict(type='string',minLength=1,maxLength=200,description='Same-project approved immutable motion source from motion_overlay_sources, not a Take or execution grant.'),
   motion_revision=dict(type='integer',minimum=1),start=dict(type='number',minimum=0,description='Clip-local start seconds; source motion starts at frame0 here.'),
   end=dict(type='number',minimum=0,description='Exclusive clip-local end seconds, within clip and source duration.'),
   offset_x=dict(type='number',minimum=-1920,maximum=1920,description='Horizontal translation in the original1920x1080 logical canvas pixels.'),
   offset_y=dict(type='number',minimum=-1080,maximum=1080,description='Vertical translation in the original1920x1080 logical canvas pixels. Source background is excluded; source layer motion/alpha stays.'))),
 _command_schema(dict(op=dict(type='string',enum=['clear_motion_overlay']),clip_index=dict(type='integer',minimum=0)))
]))

def validate_commands(commands):
 if not isinstance(commands,list) or not 1<=len(commands)<=30:raise ValueError('1–30 commands required')
 seen=set()
 for c in commands:
  if not isinstance(c,dict):raise ValueError('typed command required')
  op=c.get('op')
  if not isinstance(op,str):raise ValueError('typed edit operation required')
  fields={'reorder_clips':{'op','order'},'set_captions':{'op','cues'},'set_audio_offset':{'op','audio_version','source_offset_seconds'},'set_clip':{'op','clip_index','take','trim','duration'},'remove_clips':{'op','clip_indices'},'append_clips':{'op','clips'},'set_motion_overlay':{'op','clip_index','source_shot_id','motion_revision','start','end','offset_x','offset_y'},'clear_motion_overlay':{'op','clip_index'}}.get(op)
  if fields is None or set(c)!=fields:raise ValueError('unknown edit command/fields')
  if op=='set_clip':validate_changes([{k:v for k,v in c.items() if k!='op'}])
  key=('motion_overlay' if op in OVERLAY_OPERATIONS else op,c.get('clip_index'))
  if key in seen:raise ValueError('duplicate edit target')
  seen.add(key)
  if op in OVERLAY_OPERATIONS:
   if type(c['clip_index']) is not int or c['clip_index']<0:raise ValueError('explicit base clip index required')
   if op=='set_motion_overlay':
    if not isinstance(c['source_shot_id'],str) or not 1<=len(c['source_shot_id'])<=200:raise ValueError('explicit current-project motion source required')
    editing.motion_overlay(dict(shot=c['source_shot_id'],**{k:c[k] for k in ('motion_revision','start','end','offset_x','offset_y')}),600)
  if op=='reorder_clips':
   if not isinstance(c['order'],list) or not 1<=len(c['order'])<=30 or any(type(i) is not int or i<0 for i in c['order']) or len(set(c['order']))!=len(c['order']):raise ValueError('explicit permutation required')
  elif op=='remove_clips':
   if not isinstance(c['clip_indices'],list) or not 1<=len(c['clip_indices'])<=30 or any(type(i) is not int or i<0 for i in c['clip_indices']) or len(set(c['clip_indices']))!=len(c['clip_indices']):raise ValueError('distinct base clip indices required')
  elif op=='append_clips':
   if not isinstance(c['clips'],list) or not 1<=len(c['clips'])<=30:raise ValueError('1–30 explicit source clips required')
   for clip in c['clips']:
    if not isinstance(clip,dict) or set(clip)!={'source_shot_id','source_take_id','trim','duration'} or not isinstance(clip['source_shot_id'],str) or not 1<=len(clip['source_shot_id'])<=200 or type(clip['source_take_id']) is not int or clip['source_take_id']<1:raise ValueError('explicit project shot and take required')
    editing.seconds(clip['trim'])
    if editing.seconds(clip['duration'])<0.125:raise ValueError('minimum clip duration required')
  elif op=='set_audio_offset':
   if type(c['audio_version']) is not int or c['audio_version']<1:raise ValueError('current audio version required')
   editing.seconds(c['source_offset_seconds'])
  elif op=='set_captions':
   if not isinstance(c['cues'],list) or len(c['cues'])>100:raise ValueError('bounded explicit caption replacement required')
   for cue in c['cues']:
    if not isinstance(cue,dict) or set(cue)!={'start','end','text'}:raise ValueError('explicit caption fields required')
    editing.seconds(cue['start']);editing.seconds(cue['end'])
    if not isinstance(cue['text'],str) or not 1<=len(cue['text'])<=500:raise ValueError('caption text invalid')

def validate_changes(changes):
 if not isinstance(changes,list) or not 1<=len(changes)<=30:raise ValueError('1–30 explicit clip changes required')
 seen=set()
 for change in changes:
  if not isinstance(change,dict) or set(change)!={'clip_index','take','trim','duration'}:raise ValueError('explicit clip fields required')
  if type(change['clip_index']) is not int or change['clip_index']<0 or change['clip_index'] in seen or type(change['take']) is not int or change['take']<1:raise ValueError('invalid/duplicate clip target')
  editing.seconds(change['trim']);editing.seconds(change['duration']);seen.add(change['clip_index'])

def edit_context(p):
 t=editing.current(p)
 return guided.fingerprint(dict(timeline=t,shots={c['shot']:dict(selected=p['shots'][c['shot']]['selected'],revision=p['shots'][c['shot']]['revision'],takes=[dict(id=x['id'],sha256=x['sha256']) for x in p['shots'][c['shot']]['takes']]) for c in t['clips']},audio_versions=[dict(id=a['id'],sha256=a['sha256']) for a in p.get('audio_versions',[])]))

def check_changed_take_visibility(p,base,changes):
 """Resolve clip-index edits against the base shot, not a model-supplied name."""
 for change in changes:
  index=change.get('clip_index');take_id=change.get('take')
  if type(index) is not int or index<0 or index>=len(base['clips']) or type(take_id) is not int:raise ValueError('기준 컷과 Take를 확인하세요.')
  shot=p['shots'][base['clips'][index]['shot']]
  take=next((t for t in shot['takes'] if t['id']==take_id),None)
  if take is None or not chat_sessions.take_visible(p,shot,take):raise ValueError('현재 대화에서 확인할 수 있는 Take를 선택하세요.')

def propose_timeline(p,args,run,call):
 validate_changes(args['changes']);base=editing.current(p)
 if args['timeline_version']!=base['id']:raise Conflict('타임라인 버전이 변경됐습니다.')
 check_changed_take_visibility(p,base,args['changes'])
 candidate=deepcopy(base);candidate.pop('approval',None)
 for change in args['changes']:
  if change['clip_index']>=len(candidate['clips']):raise ValueError('clip outside current timeline')
  clip=candidate['clips'][change['clip_index']]
  clip.update({k:change[k] for k in ('take','trim','duration')})
 return save_timeline_proposal(p,args,candidate,run,call,deepcopy(args['changes']))

def timeline_diff(base,candidate,order=None,removed=None,added=None):
 # Occurrence identity is the base index, not a shot name or Take (duplicates
 # are legal). Only the validated command executor supplies the permutation.
 indices=list(range(len(base['clips'])));removed=[] if removed is None else removed
 if len(set(removed))!=len(removed) or any(type(i) is not int or i not in indices for i in removed):raise ValueError('invalid removed occurrence mapping')
 remaining=[i for i in indices if i not in removed];order=remaining if order is None else order
 added=[] if added is None else added
 if sorted(order)!=remaining or len(candidate['clips'])!=len(remaining)+len(added):raise ValueError('invalid timeline occurrence mapping')
 if candidate['clips'][len(remaining):]!=added:raise ValueError('invalid appended occurrence mapping')
 clips=[];overlays=[]
 for after_index,before_index in enumerate(order):
  before=base['clips'][before_index];after=candidate['clips'][after_index]
  if before['shot']!=after['shot']:raise ValueError('timeline occurrence changed shot')
  a={k:deepcopy(before[k]) for k in ('take','trim','duration')};b={k:deepcopy(after[k]) for k in a}
  if a!=b:clips.append(dict(base_clip_index=before_index,proposed_clip_index=after_index,before=a,after=b))
  if before.get('motion_overlay')!=after.get('motion_overlay'):
   overlays.append(dict(base_clip_index=before_index,proposed_clip_index=after_index,
                        before=deepcopy(before.get('motion_overlay')),after=deepcopy(after.get('motion_overlay'))))
 def difference(a,b):return dict(changed=False) if a==b else dict(changed=True,before=deepcopy(a),after=deepcopy(b))
 result=dict(base_version=base['id'],clip_order=difference(indices,order),clips=clips,captions=difference(base['subtitles'],candidate['subtitles']),audio=difference(dict(version=base['audio'],source_offset_seconds=base['audio_offset']),dict(version=candidate['audio'],source_offset_seconds=candidate['audio_offset'])))
 if overlays:result['motion_overlays']=overlays
 if removed:result['removed_clips']=[dict(base_clip_index=i,before={k:deepcopy(base['clips'][i][k]) for k in ('shot','take','trim','duration')}) for i in indices if i in removed]
 if added:result['added_clips']=[dict(proposed_clip_index=len(remaining)+i,after=deepcopy(clip)) for i,clip in enumerate(added)]
 return result

def save_timeline_proposal(p,args,candidate,run,call,changes,commands=None,order=None,removed=None,added=None,added_sources=None,overlay_sources=None):
 base=editing.current(p);editing.validate(p,candidate)
 proposal=dict(id=uuid.uuid4().hex,status='proposed',description=args['description'],base_version=base['id'],base_context=edit_context(p),timeline=candidate,changes=deepcopy(args['changes']),source=dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']),created=time.time())
 proposal['changes']=changes
 proposal['changes_scope']='clip_take_trim_duration'
 proposal['timeline_diff']=timeline_diff(base,candidate,order,removed,added)
 if commands is not None:proposal['commands']=deepcopy(commands)
 if added_sources is not None:proposal['added_sources']=deepcopy(added_sources)
 if overlay_sources is not None:proposal['overlay_sources']=deepcopy(overlay_sources)
 p.setdefault('timeline_edit_proposals',[]).append(proposal)
 return dict(status='proposed',proposal_id=proposal['id'],base_version=base['id'],changes=deepcopy(changes),changes_scope=proposal['changes_scope'],changes_semantics='legacy requested clip fields; no-op entries possible; timeline_diff is computed from base and candidate',timeline_diff=deepcopy(proposal['timeline_diff']),commands=deepcopy(commands),audio_version=candidate['audio'],audio_offset=candidate['audio_offset'],captions_preserved=candidate['subtitles']==base['subtitles'],applied=False,output_approved=False)

def append_source(store,c,p,clip):
 """Resolve a visible project Take and bind it to current server-owned evidence."""
 if store is None or c is None:raise ValueError('source validation requires the project transaction')
 name=production_context.shot_key(p,clip['source_shot_id']);shot=p['shots'][name]
 take=next((t for t in shot['takes'] if t['id']==clip['source_take_id']),None)
 if take is None:raise ValueError('current project take required')
 if not chat_sessions.take_visible(p,shot,take):raise ValueError('다른 대화의 미승인 Take는 먼저 해당 대화에서 검토하세요.')
 try:
  action_assets.validate(c,store,p,{'action':{'inputs':{'asset_refs':[dict(shot=name,take=take['id'],sha256=take['sha256'],role='start_frame')]}}})
 except (OSError,KeyError,TypeError) as exc:raise ValueError('추가할 원본 파일 또는 권리를 확인하세요.') from exc
 review=next((r['decision'] for r in reversed(shot.get('reviews',[])) if r['take']==take['id']),None)
 evidence=dict(shot_id=production_context.shot_id(p,name),shot=name,shot_revision=shot['revision'],take=take['id'],sha256=take['sha256'],rights=take['rights'],review=review)
 value=dict(shot=name,take=take['id'],trim=editing.seconds(clip['trim']),duration=editing.seconds(clip['duration']))
 return value,evidence

def overlay_scope(c,run,commands,project_id=None):
 """New operations require a new run and the actual approved manifest schema."""
 requested={x['op'] for x in commands if x['op'] in OVERLAY_OPERATIONS}
 if not requested:return True
 if type(run.get('timeline_command_revision')) is not int or run['timeline_command_revision']!=2:return False
 if c is None or not isinstance(project_id,str):return False
 turns=[json.loads(row[0]) for row in c.execute('SELECT body FROM general_chat_turns WHERE project=?',(project_id,)) if json.loads(row[0]).get('run')==run['id']]
 if not turns:return True
 if len(turns)!=1:return False
 row=c.execute('SELECT body FROM general_chat_previews WHERE id=?',(turns[0]['preview_id'],)).fetchone()
 if row is None:return False
 preview=json.loads(row[0])
 if preview.get('state')!='consumed' or preview.get('rights_confirmed') is not True:return False
 if preview.get('binding',{}).get('project')!=project_id or preview['binding'].get('conversation')!=run.get('conversation_id'):return False
 definitions=[x for x in preview.get('message_body',{}).get('tools',[]) if x.get('name')=='propose_timeline_changes']
 if len(definitions)!=1:return False
 schema=definitions[0].get('input_schema',{}).get('properties',{}).get('commands',{}).get('items',{})
 approved={op for branch in schema.get('anyOf',[]) for op in branch.get('properties',{}).get('op',{}).get('enum',[])}
 return requested<=approved

def overlay_source(store,c,p,clip):
 value=editing.resolve_motion_overlay(p,clip['motion_overlay'],clip['duration'],runtime=True)
 _,background=append_source(store,c,p,dict(source_shot_id=production_context.shot_id(p,clip['shot']),
                                         source_take_id=clip['take'],trim=clip['trim'],duration=clip['duration']))
 return dict(motion_source_sha256=guided.fingerprint(value['motion']),background=background)

def propose_timeline_commands(p,args,run,call,store=None,c=None):
 validate_commands(args['commands']);base=editing.current(p)
 if not overlay_scope(c,run,args['commands'],contracts.project_id(store.workspace_id,p['name']) if store else None):return dict(status='blocked',code='TOOL_SCHEMA_REVIEW_REQUIRED',retryable=False)
 if args['timeline_version']!=base['id']:raise Conflict('타임라인 버전이 변경됐습니다.')
 candidate=deepcopy(base);candidate.pop('approval',None);order=None;changes=[];removed=[];added=[];added_sources=[];overlay_commands=[]
 for cmd in args['commands']:
  if cmd['op']=='set_clip':
   if cmd['clip_index']>=len(base['clips']):raise ValueError('clip outside current base timeline')
   change={k:v for k,v in cmd.items() if k!='op'};changes.append(change)
   candidate['clips'][cmd['clip_index']].update({k:cmd[k] for k in ['take','trim','duration']})
  elif cmd['op']=='reorder_clips':
   if sorted(cmd['order'])!=list(range(len(base['clips']))):raise ValueError('order must include every base clip occurrence once')
   order=cmd['order']
  elif cmd['op']=='set_audio_offset':
   if cmd['audio_version']!=base['audio']:raise ValueError('cannot replace current source audio')
   candidate['audio_offset']=cmd['source_offset_seconds']
  elif cmd['op']=='remove_clips':removed=cmd['clip_indices']
  elif cmd['op']=='append_clips':
   for clip in cmd['clips']:
    value,evidence=append_source(store,c,p,clip);added.append(value);added_sources.append(evidence)
  elif cmd['op'] in OVERLAY_OPERATIONS:overlay_commands.append(cmd)
  else:candidate['subtitles']=deepcopy(cmd['cues'])
 if added and (order is not None or removed):raise ValueError('cannot append with reorder or remove in one proposal')
 for cmd in overlay_commands:
  if cmd['clip_index']>=len(base['clips']):raise ValueError('overlay outside current base timeline')
  clip=candidate['clips'][cmd['clip_index']]
  if cmd['op']=='clear_motion_overlay':clip.pop('motion_overlay',None)
  else:
   source=production_context.shot_key(p,cmd['source_shot_id'])
   clip['motion_overlay']=dict(shot=source,**{k:cmd[k] for k in ('motion_revision','start','end','offset_x','offset_y')})
 if removed:
  if order is not None:raise ValueError('cannot reorder and remove in one proposal')
  if any(i>=len(base['clips']) for i in removed) or len(removed)>=len(base['clips']):raise ValueError('remove must retain at least one base clip')
  if any(x['clip_index'] in removed for x in changes):raise ValueError('cannot edit a removed base clip')
  if any(x['clip_index'] in removed for x in overlay_commands):raise ValueError('cannot overlay a removed base clip')
  order=[i for i in range(len(base['clips'])) if i not in removed]
 check_changed_take_visibility(p,base,changes)
 if order is not None:candidate['clips']=[candidate['clips'][i] for i in order]
 candidate['clips'].extend(added)
 overlay_sources=[]
 for cmd in overlay_commands:
  if cmd['op']!='set_motion_overlay':continue
  index=order.index(cmd['clip_index']) if order is not None else cmd['clip_index']
  overlay_sources.append(dict(proposed_clip_index=index,**overlay_source(store,c,p,candidate['clips'][index])))
 return save_timeline_proposal(p,dict(args,changes=changes),candidate,run,call,changes,args['commands'],order,removed,added,added_sources if added else None,overlay_sources if overlay_sources else None)

def validate_timeline_proposal(store,c,p,item,version):
 if item['base_version']!=version or editing.current(p)['id']!=item['base_version'] or edit_context(p)!=item['base_context']:raise Conflict('편집 대상이 변경됐습니다. 새 제안을 검토하세요.')
 check_changed_take_visibility(p,editing.current(p),item.get('changes',[]))
 append=next((cmd for cmd in item.get('commands',[]) if cmd.get('op')=='append_clips'),None)
 if append is not None:
  sources=item.get('added_sources')
  if not isinstance(sources,list) or len(sources)!=len(append['clips']):raise ValueError('추가 원본의 저장된 근거를 확인하세요.')
  for clip,expected in zip(append['clips'],sources):
   _,current_source=append_source(store,c,p,clip)
   if current_source!=expected:raise Conflict('추가할 원본이 변경됐습니다. 새 제안을 검토하세요.')
 sets=[cmd for cmd in item.get('commands',[]) if cmd.get('op')=='set_motion_overlay']
 if sets:
  sources=item.get('overlay_sources')
  if not isinstance(sources,list) or len(sources)!=len(sets):raise ValueError('겹칠 모션 원본의 저장된 근거를 확인하세요.')
  for expected in sources:
   index=expected['proposed_clip_index'];current_source=dict(proposed_clip_index=index,**overlay_source(store,c,p,item['timeline']['clips'][index]))
   if current_source!=expected:raise Conflict('겹칠 모션 또는 배경 원본이 변경됐습니다. 새 제안을 검토하세요.')

def review_timeline(store,c,studio,name,data):
 if set(data)!={'song','proposal_id','timeline_version','decision'}:raise ValueError('saved proposal and decision required')
 p=studio.projects[name];item=next((x for x in p.get('timeline_edit_proposals',[]) if x['id']==data['proposal_id']),None)
 if item is None:raise ValueError('proposal not in this project')
 if data['decision'] not in {'approved','held','rejected'}:raise ValueError('invalid decision')
 if item['status']=='applied':
  if data['decision']!='approved':raise ValueError('이미 적용한 편집은 새 버전 또는 복원으로 변경하세요.')
  return dict(proposal_id=item['id'],timeline_version=item['applied_version'],applied=True,output_approved=False)
 if data['decision']=='approved':
  validate_timeline_proposal(store,c,p,item,data['timeline_version'])
  # Same save/validation/versioning service as the editor, never direct EDL mutation.
  store.edit(c,studio,'timeline',dict(song=name,timeline=deepcopy(item['timeline'])))
  item.update(status='applied',applied_version=p['timeline_head'])
 else:item['status']=data['decision']
 item.setdefault('reviews',[]).append(dict(actor='local-owner',decision=data['decision'],at=time.time(),scope='apply-edit-only'))
 return dict(proposal_id=item['id'],timeline_version=item.get('applied_version'),applied=item['status']=='applied',output_approved=False)

def apply_agent_timeline_draft(store,c,p,args,run,call):
 import agent_preferences
 if agent_preferences.effective_mode(p,run)!='full_access':raise ValueError('FullAccess 편집 권한이 없습니다.')
 item=next((x for x in p.get('timeline_edit_proposals',[]) if x['id']==args['proposal_id']),None)
 if item is None or item.get('status')!='proposed' or item.get('source',{}).get('run')!=run['id'] or item['source'].get('call')!=call['id']:raise ValueError('이 실행이 만든 편집 제안만 초안으로 적용할 수 있습니다.')
 commands=item.get('commands')
 if not isinstance(commands,list) or not commands or any(cmd.get('op') not in agent_preferences.AUTO_DRAFT_COMMANDS for cmd in commands):raise ValueError('이 편집은 개별 사람 검토가 필요합니다.')
 validate_timeline_proposal(store,c,p,item,item['base_version'])
 snapshot=editing.render_project(p,item['timeline'])
 store.check_rights(c,store.snapshot_hashes(snapshot))
 value=editing.save_timeline(p,deepcopy(item['timeline']))
 provenance=dict(actor='agent-draft',mode='full_access',settings=agent_preferences.frozen(p,run),run=run['id'],call=call['id'],proposal_id=item['id'],at=time.time())
 value['agent_draft']=deepcopy(provenance)
 item.update(status='applied',applied_version=value['id'],applied_by='agent-draft',agent_application=provenance)
 return dict(status='applied_draft',proposal_id=item['id'],timeline_version=value['id'],applied=True,
             agent_draft_created=True,application_actor='agent-draft',output_approved=False,
             timeline_diff=deepcopy(item['timeline_diff']),commands=deepcopy(commands))

def evidence_sources(c,p,run):
 sources={}
 for item in p.get('snapshot',[]):
  if isinstance(item.get('text'),str) and 'id' in item:sources['canon:'+str(item['id'])]=item['text']
 for e in (p.get('ontology_snapshot') or {}).get('graph',{}).get('entities',[]):sources['ontology:'+e['id']]=e['description']
 for row in c.execute('SELECT body FROM chat_turns'):
  turn=json.loads(row[0])
  if turn['run']==run['id']:sources['turn:'+turn['id']]=turn['prompt']
 return sources

def propose_memory(c,w,pid,p,args,run,call):
 namespace=project_ontology.scope(w,pid);current=ontology.snapshot(c,namespace)
 if current['revision']!=args['ontology_revision']:raise Conflict('승인된 기억 버전이 변경됐습니다.')
 source=evidence_sources(c,p,run).get(args['source_id']);excerpt=args['excerpt']
 if not source or not excerpt or excerpt not in source:raise ValueError('exact current-project source excerpt required')
 # Reuse the scoped ontology validator/proposal repository; never use manual-owner attribution.
 return project_ontology.model_proposal(c,namespace,dict(kind=args['kind'],entity=args['entity_id'],label=args['label'],description=args['description'],source_id=args['source_id'],excerpt=excerpt,ontology_revision=args['ontology_revision']),run=run['id'],model=run.get('provider_model'))

def request_render(store,c,studio,name,args):
 p=studio.projects[name];timeline=editing.current(p);approval=timeline.get('approval',{})
 if timeline['id']!=args['timeline_version']:raise Conflict('출력할 타임라인 버전이 변경됐습니다.')
 if approval.get('id')!=args['grant_id'] or approval.get('actor')!='local-owner' or approval.get('execution_scope')!='local-render':raise ValueError('human timeline render approval required')
 # Return a prior receipt even after cancellation/failure; no silent fresh render.
 for row in c.execute('SELECT body FROM jobs'):
  job=json.loads(row[0])
  if job.get('kind')=='local-motion':continue
  if job['song']==name and job['snapshot']['timeline'].get('approval',{}).get('id')==args['grant_id']:
   return render_receipt(job,existing=True)
 quote=store.edit(c,studio,'estimate_render',{'song':name})
 result=store.edit(c,studio,'render_job',{'song':name,'estimate':quote['estimate']})
 job=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(result['job'],)).fetchone()[0])
 return render_receipt(job)

def render_receipt(job,existing=False):
 return dict(status='existing' if existing else 'accepted',job_id=job['id'],state=job['status'],mode='local-render',finished_verified=job['status']=='completed' and bool(job.get('sha256')),output_approved=bool(job.get('delivery_reviews') and job['delivery_reviews'][-1]['decision']=='approved'),cost=deepcopy(job['cost']),external_calls=0)

def agent_origin(p,run,call,model_reason):
 """Server-frozen origin of an agent proposal (same keys as the D15/S15 media provenance)."""
 import agent_preferences
 return dict(actor='agent',model_reason=model_reason,model_reason_label='모델이 제시한 이유(검증 안 됨)',
             provenance=dict(engine=run['engine'],chat_model=run.get('provider_model'),permission_mode=agent_preferences.effective_mode(p,run),
                             effort=agent_preferences.frozen(p,run)['effort'],run=run['id'],call=call['id']))

def propose_scene(store,c,p,name,args,run,call):
 """S7b: a change proposal for an approved scene of the current conversation; never approved or rendered here."""
 import scene_project
 blocked=dict(status='blocked',code='SCENE_NOT_FOUND',retryable=False,note='현재 대화에 이 장면의 3D 구도가 없습니다. scene-status로 확인하세요.')
 try:shot=production_context.shot_key(p,args['shot_id'])
 except ValueError:return blocked
 row=c.execute('SELECT id FROM scene_records WHERE project=? AND conversation=? AND shot=?',
               (contracts.project_id(store.workspace_id,name),chat_sessions.current(p),production_context.shot_id(p,shot))).fetchone()
 if row is None:return blocked
 origin=agent_origin(p,run,call,args['model_reason'])
 # The scene handler rechecks scope, current head (Conflict when stale), allowed fields and asset scope/blocked rights.
 saved=scene_project.handle(c,store,p,name,'scene_propose',dict(song=name,scene_id=row[0],base_revision=args['base_revision'],operations=deepcopy(args['operations'])),origin=origin)
 return dict(status='proposed',scene_id=saved['scene_id'],proposal_id=saved['proposal_id'],base_revision=args['base_revision'],
             changes=[dict(target=x['target'],id=x['id'],field=x['field']) for x in args['operations']],
             applied=False,approval_required=True,render_requested=False,external_calls=0,**origin,duplicate=saved.get('duplicate',False),
             note=('같은 내용의 대기 중 변경안이 이미 있어 새로 저장하지 않았습니다(proposal_id가 기존 변경안). ' if saved.get('duplicate') else '')+
                  'Scene Studio에서 사람이 승인해야 적용됩니다. 승인·렌더·자산 사용권 확인은 하지 않았습니다.')

def propose_preference(p,name,args,run,call,items):
 """S10: one pending candidate for this project; never activated by an agent in any mode."""
 import preferences
 if items is None:raise ValueError('preference store unavailable')
 ip=p.get('ip','default')
 active=[x for x in items if (x['ip'],x['song'],x['category'])==(ip,name,args['category']) and x['status']=='active']
 # With an active rule in the same scope/category, approval of this candidate replaces it (existing review rule).
 supersedes=active[0]['id'] if len(active)==1 else None
 origin=agent_origin(p,run,call,args['model_reason'])
 # Identical arguments from the agent reuse the pending candidate instead of stacking copies.
 same=next((x for x in items if x['status']=='proposed' and (x.get('origin') or {}).get('actor')=='agent' and
            (x['ip'],x['song'],x['category'],x['value'],x['evidence'],x['reason'],x['supersedes'])==(ip,name,args['category'],args['value'],args['evidence'],args['model_reason'],supersedes)),None)
 if same:
  return dict(status='proposed',preference_id=same['id'],category=same['category'],scope='current-project',replaces_active=supersedes,
              applied=False,active=False,approval_required=True,**origin,duplicate=True,
              note='같은 내용의 대기 중 후보가 이미 있어 새로 저장하지 않았습니다(preference_id가 기존 후보). 사용자가 연출 취향에서 승인해야 활성화됩니다.')
 item=preferences.propose(items,ip=ip,song=name,category=args['category'],value=args['value'],evidence=args['evidence'],reason=args['model_reason'],supersedes=supersedes)
 item['origin']=deepcopy(origin)
 return dict(status='proposed',preference_id=item['id'],category=item['category'],scope='current-project',replaces_active=supersedes,
             applied=False,active=False,approval_required=True,**origin,duplicate=False,
             note=('사용자가 연출 취향에서 승인해야 활성화됩니다.'+(f' 승인하면 같은 속성의 활성 규칙 v{supersedes}는 중지됩니다.' if supersedes else '')+
                   ' 권한·모델·effort 설정은 바꾸지 않습니다.'))

def _execute(store,c,studio,name,tool,args,run,call,preferences=None):
 p=studio.projects[name]
 if p.get('archived'):raise ValueError('archived project')
 # Grant visibility moved from the HTTP preflight for model tools; human endpoints keep it.
 if tool in {'request_render','request_motion_render'}:chat_sessions.guard_refs(p,dict(grant_id=args['grant_id']))
 if tool=='execution_context':return __import__('production_context').read(c,store,p,name,query=args.get('query'))
 if tool=='sources':return [dict(id=k,text=v) for k,v in evidence_sources(c,p,run).items()]
 if tool=='propose_timeline_edit':return propose_timeline(p,args,run,call)
 if tool=='propose_timeline_changes':return propose_timeline_commands(p,args,run,call,store,c)
 if tool=='agent_apply_timeline_draft':return apply_agent_timeline_draft(store,c,p,args,run,call)
 if tool=='propose_motion_scene':return __import__('motion_scene').propose(p,args,dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']))
 if tool=='request_motion_render':return __import__('motion_scene').request_render(store,c,p,name,args)
 if tool=='propose_memory_update':
  result=propose_memory(c,store.workspace_id,contracts.project_id(store.workspace_id,name),p,args,run,call)
  return dict(status='proposed',proposal_id=result['id'],base_revision=result['base_revision'],scope='current-project',applied=False,canonical_approved=False)
 if tool=='request_render':return request_render(store,c,studio,name,args)
 if tool=='propose_scene_3d':return propose_scene(store,c,p,name,args,run,call)
 if tool=='propose_preference_rule':return propose_preference(p,name,args,run,call,preferences)
 raise ValueError('unsupported local tool')


def execute(store,c,studio,name,tool,args,run,call,preferences=None):
 p=studio.projects[name];keys=('timeline_edit_proposals','render_estimates','motion_proposals');before={k:deepcopy(p[k]) for k in keys if k in p}
 if tool=='agent_apply_timeline_draft':
  keys+=('timeline_versions','timeline_head','revision')
  before={k:deepcopy(p[k]) for k in keys if k in p}
 count=len(preferences) if preferences is not None else 0
 c.execute('SAVEPOINT local_creation_tool')
 try:result=_execute(store,c,studio,name,tool,args,run,call,preferences)
 except Exception:
  c.execute('ROLLBACK TO local_creation_tool');c.execute('RELEASE local_creation_tool')
  for key in keys:
   if key in before:p[key]=before[key]
   else:p.pop(key,None)
  if preferences is not None:del preferences[count:]
  raise
 c.execute('RELEASE local_creation_tool');return result
