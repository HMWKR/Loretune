"""Model proposals and human-authorized local rendering through existing services.
No model can apply an edit, approve canon/output, or introduce external costs.
Caller owns the Store transaction; normal Store request/tool idempotency applies.
"""
from copy import deepcopy
import json,time,uuid
import contracts,editing,guided,ontology,project_ontology
from loretune import Conflict

CHANGE_SCHEMA={'type':'array','minItems':1,'maxItems':30,'items':{'type':'object','properties':{'clip_index':{'type':'integer','minimum':0},'take':{'type':'integer','minimum':1},'trim':{'type':'number','minimum':0},'duration':{'type':'number','minimum':0.125}},'required':['clip_index','take','trim','duration'],'additionalProperties':False}}

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

def propose_timeline(p,args,run,call):
 validate_changes(args['changes']);base=editing.current(p)
 if args['timeline_version']!=base['id']:raise Conflict('타임라인 버전이 변경됐습니다.')
 candidate=deepcopy(base);candidate.pop('approval',None)
 for change in args['changes']:
  if change['clip_index']>=len(candidate['clips']):raise ValueError('clip outside current timeline')
  clip=candidate['clips'][change['clip_index']]
  clip.update({k:change[k] for k in ('take','trim','duration')})
 editing.validate(p,candidate)
 proposal=dict(id=uuid.uuid4().hex,status='proposed',description=args['description'],base_version=base['id'],base_context=edit_context(p),timeline=candidate,changes=deepcopy(args['changes']),source=dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']),created=time.time())
 p.setdefault('timeline_edit_proposals',[]).append(proposal)
 return dict(status='proposed',proposal_id=proposal['id'],base_version=base['id'],changes=deepcopy(args['changes']),audio_version=base['audio'],captions_preserved=True,applied=False,output_approved=False)

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
 if tool=='propose_memory_update':
  result=propose_memory(c,store.workspace_id,contracts.project_id(store.workspace_id,name),p,args,run,call)
  return dict(status='proposed',proposal_id=result['id'],base_revision=result['base_revision'],scope='current-project',applied=False,canonical_approved=False)
 if tool=='request_render':return request_render(store,c,studio,name,args)
 raise ValueError('unsupported local tool')


def execute(store,c,studio,name,tool,args,run,call):
 p=studio.projects[name];keys=('timeline_edit_proposals','render_estimates');before={k:deepcopy(p[k]) for k in keys if k in p}
 c.execute('SAVEPOINT local_creation_tool')
 try:result=_execute(store,c,studio,name,tool,args,run,call)
 except Exception:
  c.execute('ROLLBACK TO local_creation_tool');c.execute('RELEASE local_creation_tool')
  for key in keys:
   if key in before:p[key]=before[key]
   else:p.pop(key,None)
  raise
 c.execute('RELEASE local_creation_tool');return result
