"""Model proposals and human-authorized local rendering through existing services.
No model can apply an edit, approve canon/output, or introduce external costs.
Caller owns the Store transaction; normal Store request/tool idempotency applies.
"""
from copy import deepcopy
import json,time,uuid
import contracts,editing,guided,ontology,project_ontology
import action_assets,chat_sessions,production_context
from loretune import Conflict

CHANGE_SCHEMA={'type':'array','minItems':1,'maxItems':30,'items':{'type':'object','properties':{'clip_index':{'type':'integer','minimum':0},'take':{'type':'integer','minimum':1},'trim':{'type':'number','minimum':0},'duration':{'type':'number','minimum':0.125}},'required':['clip_index','take','trim','duration'],'additionalProperties':False}}
def _command_schema(properties):return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)
COMMAND_SCHEMA=dict(type='array',minItems=1,maxItems=30,items=dict(anyOf=[
 _command_schema(dict(op=dict(type='string',enum=['reorder_clips']),order=dict(type='array',minItems=1,maxItems=30,items=dict(type='integer',minimum=0)))),
 _command_schema(dict(op=dict(type='string',enum=['set_captions']),cues=dict(type='array',maxItems=100,items=_command_schema(dict(start=dict(type='number',minimum=0),end=dict(type='number',minimum=0),text=dict(type='string')))))),
 _command_schema(dict(op=dict(type='string',enum=['set_audio_offset']),audio_version=dict(type='integer',minimum=1),source_offset_seconds=dict(type='number',minimum=0))),
 _command_schema(dict(op=dict(type='string',enum=['set_clip']),**deepcopy(CHANGE_SCHEMA['items']['properties']))),
 _command_schema(dict(op=dict(type='string',enum=['remove_clips']),clip_indices=dict(type='array',minItems=1,maxItems=30,items=dict(type='integer',minimum=0)))),
 _command_schema(dict(op=dict(type='string',enum=['append_clips']),clips=dict(type='array',minItems=1,maxItems=30,items=_command_schema(dict(source_shot_id=dict(type='string',minLength=1,maxLength=200),source_take_id=dict(type='integer',minimum=1),trim=dict(type='number',minimum=0),duration=dict(type='number',minimum=0.125))))))
]))

def validate_commands(commands):
 if not isinstance(commands,list) or not 1<=len(commands)<=30:raise ValueError('1–30 commands required')
 seen=set()
 for c in commands:
  if not isinstance(c,dict):raise ValueError('typed command required')
  op=c.get('op')
  if not isinstance(op,str):raise ValueError('typed edit operation required')
  fields={'reorder_clips':{'op','order'},'set_captions':{'op','cues'},'set_audio_offset':{'op','audio_version','source_offset_seconds'},'set_clip':{'op','clip_index','take','trim','duration'},'remove_clips':{'op','clip_indices'},'append_clips':{'op','clips'}}.get(op)
  if fields is None or set(c)!=fields:raise ValueError('unknown edit command/fields')
  if op=='set_clip':validate_changes([{k:v for k,v in c.items() if k!='op'}])
  key=(op,c.get('clip_index'))
  if key in seen:raise ValueError('duplicate edit target')
  seen.add(key)
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
 clips=[]
 for after_index,before_index in enumerate(order):
  before=base['clips'][before_index];after=candidate['clips'][after_index]
  if before['shot']!=after['shot']:raise ValueError('timeline occurrence changed shot')
  a={k:deepcopy(before[k]) for k in ('take','trim','duration')};b={k:deepcopy(after[k]) for k in a}
  if a!=b:clips.append(dict(base_clip_index=before_index,proposed_clip_index=after_index,before=a,after=b))
 def difference(a,b):return dict(changed=False) if a==b else dict(changed=True,before=deepcopy(a),after=deepcopy(b))
 result=dict(base_version=base['id'],clip_order=difference(indices,order),clips=clips,captions=difference(base['subtitles'],candidate['subtitles']),audio=difference(dict(version=base['audio'],source_offset_seconds=base['audio_offset']),dict(version=candidate['audio'],source_offset_seconds=candidate['audio_offset'])))
 if removed:result['removed_clips']=[dict(base_clip_index=i,before={k:deepcopy(base['clips'][i][k]) for k in ('shot','take','trim','duration')}) for i in indices if i in removed]
 if added:result['added_clips']=[dict(proposed_clip_index=len(remaining)+i,after=deepcopy(clip)) for i,clip in enumerate(added)]
 return result

def save_timeline_proposal(p,args,candidate,run,call,changes,commands=None,order=None,removed=None,added=None,added_sources=None):
 base=editing.current(p);editing.validate(p,candidate)
 proposal=dict(id=uuid.uuid4().hex,status='proposed',description=args['description'],base_version=base['id'],base_context=edit_context(p),timeline=candidate,changes=deepcopy(args['changes']),source=dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']),created=time.time())
 proposal['changes']=changes
 proposal['changes_scope']='clip_take_trim_duration'
 proposal['timeline_diff']=timeline_diff(base,candidate,order,removed,added)
 if commands is not None:proposal['commands']=deepcopy(commands)
 if added_sources is not None:proposal['added_sources']=deepcopy(added_sources)
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

def propose_timeline_commands(p,args,run,call,store=None,c=None):
 validate_commands(args['commands']);base=editing.current(p)
 if args['timeline_version']!=base['id']:raise Conflict('타임라인 버전이 변경됐습니다.')
 candidate=deepcopy(base);candidate.pop('approval',None);order=None;changes=[];removed=[];added=[];added_sources=[]
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
  else:candidate['subtitles']=deepcopy(cmd['cues'])
 if added and (order is not None or removed):raise ValueError('cannot append with reorder or remove in one proposal')
 if removed:
  if order is not None:raise ValueError('cannot reorder and remove in one proposal')
  if any(i>=len(base['clips']) for i in removed) or len(removed)>=len(base['clips']):raise ValueError('remove must retain at least one base clip')
  if any(x['clip_index'] in removed for x in changes):raise ValueError('cannot edit a removed base clip')
  order=[i for i in range(len(base['clips'])) if i not in removed]
 check_changed_take_visibility(p,base,changes)
 if order is not None:candidate['clips']=[candidate['clips'][i] for i in order]
 candidate['clips'].extend(added)
 return save_timeline_proposal(p,dict(args,changes=changes),candidate,run,call,changes,args['commands'],order,removed,added,added_sources if added else None)

def review_timeline(store,c,studio,name,data):
 if set(data)!={'song','proposal_id','timeline_version','decision'}:raise ValueError('saved proposal and decision required')
 p=studio.projects[name];item=next((x for x in p.get('timeline_edit_proposals',[]) if x['id']==data['proposal_id']),None)
 if item is None:raise ValueError('proposal not in this project')
 if data['decision'] not in {'approved','held','rejected'}:raise ValueError('invalid decision')
 if item['status']=='applied':
  if data['decision']!='approved':raise ValueError('이미 적용한 편집은 새 버전 또는 복원으로 변경하세요.')
  return dict(proposal_id=item['id'],timeline_version=item['applied_version'],applied=True,output_approved=False)
 if data['decision']=='approved':
  if item['base_version']!=data['timeline_version'] or editing.current(p)['id']!=item['base_version'] or edit_context(p)!=item['base_context']:raise Conflict('편집 대상이 변경됐습니다. 새 제안을 검토하세요.')
  check_changed_take_visibility(p,editing.current(p),item.get('changes',[]))
  append=next((cmd for cmd in item.get('commands',[]) if cmd.get('op')=='append_clips'),None)
  if append is not None:
   sources=item.get('added_sources')
   if not isinstance(sources,list) or len(sources)!=len(append['clips']):raise ValueError('추가 원본의 저장된 근거를 확인하세요.')
   for clip,expected in zip(append['clips'],sources):
    _,current_source=append_source(store,c,p,clip)
    if current_source!=expected:raise Conflict('추가할 원본이 변경됐습니다. 새 제안을 검토하세요.')
  # Same save/validation/versioning service as the editor, never direct EDL mutation.
  store.edit(c,studio,'timeline',dict(song=name,timeline=deepcopy(item['timeline'])))
  item.update(status='applied',applied_version=p['timeline_head'])
 else:item['status']=data['decision']
 item.setdefault('reviews',[]).append(dict(actor='local-owner',decision=data['decision'],at=time.time(),scope='apply-edit-only'))
 return dict(proposal_id=item['id'],timeline_version=item.get('applied_version'),applied=item['status']=='applied',output_approved=False)

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

def _execute(store,c,studio,name,tool,args,run,call):
 p=studio.projects[name]
 if p.get('archived'):raise ValueError('archived project')
 if tool=='execution_context':return __import__('production_context').read(c,store,p,name)
 if tool=='sources':return [dict(id=k,text=v) for k,v in evidence_sources(c,p,run).items()]
 if tool=='propose_timeline_edit':return propose_timeline(p,args,run,call)
 if tool=='propose_timeline_changes':return propose_timeline_commands(p,args,run,call,store,c)
 if tool=='propose_motion_scene':return __import__('motion_scene').propose(p,args,dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']))
 if tool=='request_motion_render':return __import__('motion_scene').request_render(store,c,p,name,args)
 if tool=='propose_memory_update':
  result=propose_memory(c,store.workspace_id,contracts.project_id(store.workspace_id,name),p,args,run,call)
  return dict(status='proposed',proposal_id=result['id'],base_revision=result['base_revision'],scope='current-project',applied=False,canonical_approved=False)
 if tool=='request_render':return request_render(store,c,studio,name,args)
 raise ValueError('unsupported local tool')


def execute(store,c,studio,name,tool,args,run,call):
 p=studio.projects[name];keys=('timeline_edit_proposals','render_estimates','motion_proposals');before={k:deepcopy(p[k]) for k in keys if k in p}
 c.execute('SAVEPOINT local_creation_tool')
 try:result=_execute(store,c,studio,name,tool,args,run,call)
 except Exception:
  c.execute('ROLLBACK TO local_creation_tool');c.execute('RELEASE local_creation_tool')
  for key in keys:
   if key in before:p[key]=before[key]
   else:p.pop(key,None)
  raise
 c.execute('RELEASE local_creation_tool');return result
