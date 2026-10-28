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
 'prepare_image_action': {'shot_id':str,'model_id':str,'prompt':str,'ratio':str,'shot_revision':int},
 'prepare_video_action': {'shot_id':str,'model_id':str,'prompt':str,'duration':int,'shot_revision':int,'source_shot_id':str,'source_take_id':int,'source_sha256':str},
 'request_media_generation': {'plan_id':str,'action_id':str,'grant_id':str},
 'get_generation_job': {'job_id':str},
 'propose_timeline_edit': {'description':str,'timeline_version':int,'changes':list},
 'request_render': {'timeline_version':int,'grant_id':str},
 'propose_memory_update': {'description':str,'kind':str,'label':str,'entity_id':str,'source_id':str,'excerpt':str,'ontology_revision':int},
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
            if t is str and k in {'style','constraints','entity_id'} and args[k]=='':continue
            raise ValueError('INVALID_TOOL_ARGUMENTS')
        if t is int and args[k]<(0 if k in {'shot_revision','timeline_version','ontology_revision'} else 1):raise ValueError('INVALID_TOOL_ARGUMENTS')
    if name=='propose_timeline_edit':
        import local_creation_tools
        local_creation_tools.validate_changes(args['changes'])
    if name=='propose_media_plan':guided.propose({},args)
    if name=='get_model_capabilities' and args['role'] not in model_selection.ROLES:raise ValueError('INVALID_TOOL_ARGUMENTS')

def execute(project,run_id,call,*,jobs=(),request_generation=None,prepare_media=None,estimate_plan=None,local_tool=None):
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
            if local_tool is not None:result['sources']=local_tool('sources',{},run,call)
        elif name=='propose_media_plan':
            # Reuse deterministic plan implementation, preserving authored text.
            result=dict(status='proposed',plan=guided.propose(project,args),cost_approval=False)
            if run['engine'] in {'anthropic-live','openai-live','xai-live','contract-fake'}:
                result['plan']['source']=dict(mode=run['engine'],model=run.get('provider_model'),run=run['id'],call=call['id'])
                result['plan']['engine']='model-authored' if run['engine']!='contract-fake' else 'contract-fake'
                result['plan']['explanation']='모델 도구 인수로 제안된 장면을 저장했습니다. 확정 음악 구간은 서버가 균등 배분합니다. 사람의 검토·승인 전이며 미디어 생성은 실행하지 않았습니다.' if run['engine']!='contract-fake' else '도구 계약 검증용 모의 제안입니다. 실제 AI·외부 미디어 호출은 없습니다.'
        elif name in {'prepare_image_action','prepare_video_action'} and prepare_media is not None:
            from action_execution import ExecutionBlocked
            try:result=prepare_media(name,deepcopy(args))
            except ExecutionBlocked:result=dict(status='blocked',code='MODEL_CONNECTION_OR_PRICE_REQUIRED',retryable=False)
            except (ValueError,KeyError):
                run['repair_count']+=1
                if run['repair_count']>=run['limits']['repairs']:run['state']='invalid_arguments'
                result=dict(status='invalid_arguments',code='INVALID_MEDIA_INPUT',retryable=run['state']=='accepting_tools')
        elif name=='estimate_media_plan' and estimate_plan is not None:
            result=estimate_plan(args['plan_id'])
        elif name in {'propose_timeline_edit','request_render','propose_memory_update'} and local_tool is not None:
            try:result=local_tool(name,deepcopy(args),run,call)
            except Conflict:
                result=dict(status='blocked',code='STALE_VERSION',retryable=False)
            except (ValueError,KeyError):
                result=dict(status='blocked',code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED',retryable=False)
        elif name=='get_generation_job':
            job=next((j for j in jobs if j['id']==args['job_id']),None)
            result=dict(status='not_found') if job is None else dict(status='succeeded',job={k:deepcopy(job.get(k)) for k in ['id','state','failure_code','mode','action_id','plan_id','plan_revision','release_id','grant_id','external_calls','result','result_approved','provider_completed','cost']})
            if job is not None:
                result['job']['registered_takes']=[dict(shot=n,take=t['id'],sha256=t['sha256']) for n,s in project.get('shots',{}).items() for t in s['takes'] if t.get('action_id')==job.get('action_id') and t.get('action_id') is not None]
                if job.get('mode')!='rehearsal' and result['job']['registered_takes']:
                    result['job']['result_approved']=all(next((r['decision']=='approved' for r in reversed(project['shots'][t['shot']].get('reviews',[])) if r['take']==t['take']),False) for t in result['job']['registered_takes'])
        elif name=='request_media_generation' and request_generation is not None:
            # Injected by the server controller, never supplied by model arguments.
            from action_execution import ExecutionBlocked
            try:result=request_generation(deepcopy(args))
            except Conflict:
                run['state']='stale_context';result=dict(status='blocked',code='STALE_CONTEXT',retryable=False)
            except ExecutionBlocked:
                result=dict(status='blocked',code='APPROVAL_OR_DEPENDENCY_REQUIRED',retryable=False)
            except ValueError:
                run['repair_count']+=1
                if run['repair_count']>=run['limits']['repairs']:run['state']='invalid_arguments'
                result=dict(status='invalid_arguments',code='INVALID_ACTION_REFERENCE',retryable=run['state']=='accepting_tools')
        else:
            result=dict(status='blocked',code='LOCAL_TOOL_NOT_CONNECTED',note='이 도구는 실행 연결 전입니다. 승인·비용 예약·외부 제출을 수행하지 않았습니다.')
    run['calls'].append(dict(id=call['id'],digest=digest,name=call['name'],result=deepcopy(result)))
    return result
