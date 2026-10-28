"""Conversation/model preferences and server-owned agent execution ceilings.

These settings do not confer account, billing, file-delete or output approval.
Vendor capability is distinct from an installed route or a verified account.
"""
from copy import deepcopy
import json
import time
from decimal import ROUND_CEILING

import chat_models
from loretune import Conflict

MODES={'read_only':0,'review':1,'full_access':2}
READ_TOOLS={'search_project_context','get_model_capabilities','get_generation_job','estimate_media_plan','get_agent_settings'}
AUTO_DRAFT_COMMANDS={'set_clip','reorder_clips','set_captions','set_audio_offset','set_motion_overlay'}
ACCOUNT_DELETE_TOOLS={'delete_account','account_delete'}
FILE_DELETE_TOOLS={'delete_file','delete_asset','delete_project','file_delete','asset_delete','project_delete'}
EFFORTS={
    'anthropic-haiku-5-5':['low','medium','high'],
    'openai-gpt-6-luna':['none','low','medium','high','xhigh','max'],
    'xai-grok-4-7':['low','medium','high','xhigh'],
}


def profile(project,selection=None):
    import chat_sessions
    selection=chat_sessions.selected_chat(project) if selection is None else selection
    session=chat_sessions.resolve(project,chat_sessions.current(project))
    stored=session.get('agent_settings',{}).get(selection,{})
    value=dict(selection=selection,revision=stored.get('revision',0),mode=stored.get('mode','review'),effort=stored.get('effort','low'))
    validate_snapshot(value)
    return value


def validate_snapshot(value):
    if not isinstance(value,dict) or set(value)!={'selection','revision','mode','effort'}:raise ValueError('에이전트 설정의 고정 입력이 불완전합니다.')
    if value['selection'] is not None and value['selection'] not in chat_models.MODELS:raise ValueError('등록된 채팅 모델 설정이 필요합니다.')
    if type(value['revision']) is not int or value['revision']<0 or value['mode'] not in MODES:raise ValueError('에이전트 설정 버전·권한을 확인하세요.')
    if value['effort'] not in EFFORTS.get(value['selection'],['low']):raise ValueError('해당 모델의 현재 실행 경로가 지원하는 추론 강도를 선택하세요.')
    return deepcopy(value)


def legacy_settings(project,record=None):
    import chat_sessions
    record=record or {};binding=record.get('binding',{})
    binding=binding if isinstance(binding,dict) else {}
    selected=binding.get('selection')
    if selected not in chat_models.MODELS:
        model=record.get('provider_model') or record.get('model')
        selected=next((identifier for identifier,spec in chat_models.MODELS.items() if spec['model']==model),None)
    if selected is None:selected=chat_sessions.selected_chat(project)
    return dict(selection=selected,revision=0,mode='review',effort='low')


def frozen(project,record):
    value=record.get('agent_settings')
    if value is None and isinstance(record.get('binding'),dict):value=record['binding'].get('agent_settings')
    return validate_snapshot(value) if value is not None else legacy_settings(project,record)


def effective_mode(project,run):
    saved=frozen(project,run)
    ceiling=run.get('agent_permission_ceiling','review' if 'agent_settings' not in run else saved['mode'])
    if ceiling not in MODES:raise ValueError('에이전트 권한 상한을 확인하세요.')
    current=profile(project,saved['selection'])
    level=min(MODES[saved['mode']],MODES[ceiling],MODES[current['mode']])
    return next(name for name,value in MODES.items() if value==level)


def tools_for(project,run,names):
    mode=effective_mode(project,run)
    return [name for name in names if name in READ_TOOLS] if mode=='read_only' else list(names)


def authorize(project,run,name):
    if not isinstance(name,str):raise ValueError('TOOL_NOT_ALLOWED')
    if name in ACCOUNT_DELETE_TOOLS:raise ValueError('ACCOUNT_DELETION_PROHIBITED')
    if name in FILE_DELETE_TOOLS:raise ValueError('DELETE_TOOL_UNSUPPORTED_EXPLICIT_TARGET_APPROVAL_REQUIRED')
    if effective_mode(project,run)=='read_only' and name not in READ_TOOLS:raise ValueError('AGENT_READ_ONLY')


def update(project,selection,expected,mode,effort):
    import chat_sessions
    if selection not in chat_models.MODELS:raise ValueError('등록된 채팅 모델별 설정을 선택하세요.')
    old=profile(project,selection)
    if type(expected) is not int or expected!=old['revision']:raise Conflict('이 모델의 에이전트 설정이 변경됐습니다. 최신 값을 확인하세요.')
    value=validate_snapshot(dict(selection=selection,revision=expected+1,mode=mode,effort=effort))
    if (old['mode'],old['effort'])==(mode,effort):return old
    project.setdefault('chat_sessions',chat_sessions.entries(project))
    cid=chat_sessions.current(project);session=next(x for x in project['chat_sessions'] if x['id']==cid)
    session.setdefault('agent_settings',{})[selection]=dict(value,updated=time.time())
    session.setdefault('agent_settings_history',[]).append(dict(value,actor='local-owner',at=time.time()))
    for run in project.get('production_runs',[]):
        if run.get('state')!='accepting_tools' or (run.get('conversation_id') or chat_sessions.default_id(project))!=cid:continue
        saved=frozen(project,run)
        if saved['selection']!=selection:continue
        ceiling=run.get('agent_permission_ceiling','review' if 'agent_settings' not in run else saved['mode'])
        if ceiling not in MODES:raise ValueError('에이전트 권한 상한을 확인하세요.')
        if MODES[mode]<MODES[ceiling]:run['agent_permission_ceiling']=mode
    return value


def token_price(selection):
    """D21: standard text rates per 1M tokens from the chat contract, not a billing claim."""
    if selection not in chat_models.MODELS:return None
    spec=chat_models.contract(selection)
    long=dict(threshold_input_tokens=spec['long_context_threshold'],input_rate=spec['long_input_rate'],output_rate=spec['long_output_rate']) if 'long_context_threshold' in spec else None
    return dict(input_rate=spec['input_rate'],output_rate=spec['output_rate'],unit='USD per 1M tokens',long_context=long,
                source=spec['source'],revision=spec['price_revision'])


def reservation(selection):
    """D20: general-chat worst-case hold per round and how many fit the conversation cap."""
    import chat_general
    if selection not in chat_models.MODELS:return None
    worst=int((chat_models.cost(chat_models.contract(selection),chat_general.MAX_INPUT,chat_general.MAX_OUTPUT)*1000000).to_integral_value(rounding=ROUND_CEILING))
    return dict(max_input_tokens=chat_general.MAX_INPUT,max_output_tokens=chat_general.MAX_OUTPUT,worst_per_round_micro=worst,
                conversation_cap_micro=chat_general.CONVERSATION_CAP_MICRO,worst_case_rounds_within_cap=chat_general.CONVERSATION_CAP_MICRO//worst)


def settings_summary(project,run):
    """S9/D21 read-only view of the frozen settings for this run; the agent cannot change them."""
    saved=frozen(project,run);selection=saved['selection']
    spec=chat_models.contract(selection) if selection in chat_models.MODELS else None
    return dict(status='succeeded',
                chat_model=dict(id=selection,model=spec['model'],provider=spec['provider'],selection_reason='사용자가 선택한 모델',price=token_price(selection)) if spec else None,
                effort=saved['effort'],permission=dict(saved=profile(project,selection)['mode'] if selection else saved['mode'],frozen=saved['mode'],effective=effective_mode(project,run)),
                reservation=reservation(selection),agent_can_change=False,note='권한·effort·모델은 사용자만 바꿀 수 있습니다. 이 결과는 읽기 전용입니다.')


def capability(selection,store=None):
    spec=chat_models.contract(selection);provider=spec['provider']
    general=bool(store and store.general_chat_runtime is not None and provider=='anthropic')
    router=getattr(store,'chat_runtime',None)
    legacy=bool(router and (selection in getattr(router,'runtimes',{}) or getattr(router,'spec',{}).get('id')==selection))
    unavailable=[]
    if provider=='anthropic':
        unavailable=[dict(value=value,reason='공급자는 지원하지만 현재 disabled thinking 경로는 high까지만 지원합니다. adaptive thinking은 미구현입니다.') for value in ['xhigh','max']]
    return dict(provider=provider,model=spec['model'],effort_options=list(EFFORTS[selection]),unsupported_efforts=unavailable,
                general_route_supported=provider=='anthropic',general_route_configured=general,
                legacy_route_supported=True,legacy_route_configured=legacy,
                token_price=token_price(selection),reservation=reservation(selection),
                account_verified=False,billing_verified=False,
                reason='일반 채팅은 현재 Claude 경로만 지원합니다. 다른 모델은 별도 legacy 연결·검증이 필요합니다.' if provider!='anthropic' else '현재 일반 경로는 low/medium/high와 disabled thinking을 사용합니다. 실제 계정·청구는 별도 검증입니다.')


def public(c,store,project,name):
    import chat_sessions,contracts
    cid=chat_sessions.current(project);pid=contracts.project_id(store.workspace_id,name)
    current=profile(project);active=[]
    for table in ['general_chat_turns','chat_turns']:
        for row in c.execute('SELECT body FROM '+table+' WHERE project=?',(pid,)):
            turn=json.loads(row[0])
            if (turn.get('conversation_id') or chat_sessions.default_id(project))!=cid or turn.get('status') not in {'queued','running','cancel_requested','outcome_unknown','awaiting_continuation_approval'}:continue
            saved=frozen(project,turn)
            run=next((r for r in project.get('production_runs',[]) if r['id']==turn.get('run')),None)
            active.append(dict(saved,turn_id=turn['id'],status=turn['status'],effective_mode=effective_mode(project,run or {}),
                               permission_ceiling=(run or {}).get('agent_permission_ceiling','review')))
    response=active[0] if len(active)==1 else None
    pending_selection=chat_sessions.resolve(project,cid).get('pending_chat_selection')
    next_request=profile(project,pending_selection['selection']) if pending_selection and pending_selection.get('selection') else current
    pending=bool(response and {k:response[k] for k in ('selection','revision','mode','effort')}!=next_request)
    return dict(current=current,by_model={selection:profile(project,selection) for selection in chat_models.MODELS},
                active_response=response,active_response_conflict=len(active)>1,next_request=next_request,settings_pending=pending,
                capabilities=dict(models={selection:capability(selection,store) for selection in chat_models.MODELS},
                    modes=[dict(id=identifier,label=label) for identifier,label in [('read_only','읽기 전용'),('review','검토 후 편집'),('full_access','FullAccess')]],
                    full_auto_draft_commands=sorted(AUTO_DRAFT_COMMANDS),human_review_only_commands=['remove_clips','clear_motion_overlay','append_clips'],
                    account_deletion=False,file_deletion=False,destructive_scope='삭제 도구는 제공하지 않습니다. 계정 삭제는 항상 금지하며 파일 등 삭제는 대상별 별도 명시 허가가 필요합니다.',
                    final_output_approval='always separate',provider_cost_and_transmission_consent='always separate'),
                note='현재 응답의 추론·본문은 고정합니다. 권한 축소는 즉시 적용하며 확장은 다음 새 요청부터 적용합니다.')
