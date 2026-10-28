"""Server-owned, persisted local tool runs. No provider transport or paid execution."""
from copy import deepcopy
import uuid
import guided
import model_selection
from loretune import Conflict

TOOLS={
 'search_project_context': {'query':str},
 'get_model_capabilities': {'role':str},
 'propose_media_plan': {'goal':str,'scenes':str,'style':str,'constraints':str,'kind':str},
 'estimate_media_plan': {'plan_id':str},
 'request_media_generation': {'plan_id':str,'action_id':str,'grant_id':str},
 'get_generation_job': {'job_id':str},
 'propose_timeline_edit': {'description':str},
 'request_render': {'timeline_version':int,'grant_id':str},
 'propose_memory_update': {'description':str},
}

def begin(project):
    run=dict(id=uuid.uuid4().hex,state='accepting_tools',engine='local-contract-rehearsal',
             snapshot=model_selection.snapshot(project),calls=[],repair_count=0,
             limits=dict(tool_rounds=8,repairs=2),live_model_called=False)
    project.setdefault('production_runs',[]).append(run)
    return deepcopy(run)

def validate(name,args):
    if not isinstance(name,str) or name not in TOOLS:raise ValueError('TOOL_NOT_ALLOWED')
    schema=TOOLS[name]
    if not isinstance(args,dict) or set(args)!=set(schema):raise ValueError('INVALID_TOOL_ARGUMENTS')
    for k,t in schema.items():
        if type(args[k]) is not t or (t is str and (not args[k].strip() or len(args[k])>2000)):
            # Empty optional prose is permitted in a plan, never an ID or query.
            if t is str and k in {'style','constraints'} and args[k]=='':continue
            raise ValueError('INVALID_TOOL_ARGUMENTS')
        if t is int and args[k]<1:raise ValueError('INVALID_TOOL_ARGUMENTS')
    if name=='propose_media_plan':guided.propose({},args)
    if name=='get_model_capabilities' and args['role'] not in model_selection.ROLES:raise ValueError('INVALID_TOOL_ARGUMENTS')

def execute(project,run_id,call,*,jobs=(),request_generation=None):
    """Caller already scoped project from authenticated local Store. Model cannot supply scope."""
    run=next((x for x in project.get('production_runs',[]) if x['id']==run_id),None)
    if run is None:raise ValueError('RUN_NOT_FOUND')
    if not isinstance(call,dict) or set(call)!={'id','name','arguments','complete'}:raise ValueError('INVALID_TOOL_REQUEST')
    if not isinstance(call['id'],str) or not 1<=len(call['id'])<=128:raise ValueError('INVALID_TOOL_REQUEST')
    digest=guided.fingerprint(call)
    prior=next((x for x in run['calls'] if x['id']==call['id']),None)
    if prior:
        if prior['digest']!=digest:raise Conflict('동일 도구 호출 ID의 내용이 다릅니다.')
        return deepcopy(prior['result'])
    if run['state']!='accepting_tools':raise ValueError('RUN_NOT_ACCEPTING_TOOLS')
    if call['complete'] is not True:raise ValueError('INCOMPLETE_TOOL_ARGUMENTS')
    if len(run['calls'])>=run['limits']['tool_rounds']:raise ValueError('TOOL_ROUND_LIMIT')
    if run['snapshot']['sha256']!=model_selection.snapshot(project)['sha256']:
        raise Conflict('제작 문맥이 변경됐습니다. 새 실행 문맥에서 검토하세요.')
    try:validate(call['name'],call['arguments'])
    except ValueError as exc:
        run['repair_count']+=1
        if run['repair_count']>=run['limits']['repairs']:run['state']='invalid_arguments'
        result=dict(status='invalid_arguments',code=str(exc),retryable=run['state']=='accepting_tools')
    else:
        name=call['name'];args=call['arguments']
        if name=='get_model_capabilities':
            result=dict(status='succeeded',models=[m for m in model_selection.catalog()['models'] if m['role']==args['role']],live_execution=False)
        elif name=='search_project_context':
            result=dict(status='succeeded',context=deepcopy(run['snapshot']['value']['context']),search_mode='scoped-snapshot',note='현재 작품의 승인 문맥 전체 반환; 의미 검색·임베딩 검색 아님')
        elif name=='propose_media_plan':
            # Reuse deterministic plan implementation, preserving authored text.
            result=dict(status='proposed',plan=guided.propose(project,args),cost_approval=False)
        elif name=='get_generation_job':
            job=next((j for j in jobs if j['id']==args['job_id']),None)
            result=dict(status='not_found') if job is None else dict(status='succeeded',job={k:deepcopy(job.get(k)) for k in ['id','state','failure_code']})
        elif name=='request_media_generation' and request_generation is not None:
            # Injected by the server controller, never supplied by model arguments.
            result=request_generation(deepcopy(args))
        else:
            result=dict(status='blocked',code='LOCAL_TOOL_NOT_CONNECTED',note='이 도구는 실행 연결 전입니다. 승인·비용 예약·외부 제출을 수행하지 않았습니다.')
    run['calls'].append(dict(id=call['id'],digest=digest,name=call['name'],result=deepcopy(result)))
    return result
