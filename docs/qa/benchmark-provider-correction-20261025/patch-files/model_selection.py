"""Role-specific selection contracts. No credential access or network execution."""
from copy import deepcopy
import time
from loretune import Conflict
from guided import fingerprint

ROLES=('chat','image','video')
CATALOG=(
    dict(id='anthropic-haiku-5-5',release_id='anthropic:claude-haiku-5-5',connection_id=None,revision_pinning='unverified',role='chat',provider='anthropic',model='claude-haiku-5-5',
         state='integration_unverified',reason='서버 도구 실행·합성 검증 경로 구현; 일반 프로젝트 실제 채팅 연결 미검증',capabilities=None),
    dict(id='fal-kling-2-6-pro',release_id='fal:kling-video-v2.6-pro-i2v',connection_id=None,revision_pinning='unverified',role='video',provider='fal',model='fal-ai/kling-video/v2.6/pro/image-to-video',
         state='integration_blocked',reason='공급자 완료 후 비공개 파일 수신 차단; 통합 검증 미완료',
         capabilities=dict(task='image-to-video',durations=[5,10],generated_audio=False)),
)

def catalog():
    return dict(models=deepcopy(CATALOG),roles=list(ROLES),image_notice='이미지 공급자 미선택 · 기존 이미지 업로드 사용',
                live_execution=False,scope='single-local-workspace',automatic_routing=False)

def settings(project):
    return deepcopy(project.get('model_settings',dict(revision=0,selections={r:None for r in ROLES},history=[])))

def validate_selection(role, identifier):
    if role not in ROLES:raise ValueError('알 수 없는 모델 역할입니다.')
    if identifier is None:return None
    item=next((m for m in CATALOG if m['id']==identifier),None)
    if item is None or item['role']!=role:raise ValueError('해당 역할의 등록된 모델을 선택하세요.')
    return item

def update(project, patch, expected_revision):
    if not isinstance(patch,dict) or not patch or set(patch)-set(ROLES):raise ValueError('세 모델 역할만 변경할 수 있습니다.')
    old=settings(project)
    if type(expected_revision) is not int or expected_revision!=old['revision']:raise Conflict('모델 설정이 변경됐습니다. 최신 선택값을 확인하세요.')
    for role,identifier in patch.items():validate_selection(role,identifier)
    new=deepcopy(old);new['selections'].update(patch);new['revision']+=1
    new['history'].append(dict(revision=new['revision'],actor='local-owner',changed=deepcopy(patch),at=time.time()))
    project['model_settings']=new
    # Settings changes invalidate unfinished chat requests, never media jobs or prior snapshots.
    for run in project.get('production_runs',[]):
        if run['state']=='accepting_tools':run['state']='superseded'
    return deepcopy(new)

def resolve(role, *, explicit=None, conversation=None, project=None, organization=None, service=None, forbidden=(), execute=False):
    if role not in ROLES:raise ValueError('알 수 없는 모델 역할입니다.')
    for origin,identifier in [('explicit',explicit),('conversation',conversation),('project',project),('organization',organization),('service',service)]:
        if identifier is None:continue
        item=validate_selection(role,identifier)
        if identifier in forbidden:raise ValueError('POLICY_BLOCKED: 정책에서 금지된 모델입니다. 자동 대체하지 않습니다.')
        if execute and item['state']!='active':raise ValueError('MODEL_NOT_AVAILABLE: '+item['reason'])
        return dict(selection=deepcopy(item),origin=origin,executable=item['state']=='active')
    return dict(selection=None,origin=None,executable=False)

def snapshot(project):
    """Only server-owned public context; excludes provider IDs, tokens and hidden reasoning."""
    import guided
    value=dict(model_settings=settings(project),context=guided.context(project),
               approved_shots=[dict(id=s.get('stable_id',n),selected=s.get('selected'),revision=s.get('revision'))
                               for n,s in project.get('shots',{}).items()])
    return dict(value=deepcopy(value),sha256=fingerprint(value))

def media_snapshot(project):
    """Media approval freshness excludes unrelated chat selection/history.

    Media selections and canonical inputs remain approval dependencies. Old
    full-v1 approvals are not silently rehashed or granted broader authority.
    """
    value=snapshot(project)['value']
    value['model_settings']={'selections':{r:settings(project)['selections'][r] for r in ('image','video')}}
    return dict(value=value,sha256=fingerprint(value))

def action_context(project,action):
    kind=action.get('context_kind','full-v1')
    if kind not in {'full-v1','media-v1'}:raise ValueError('알 수 없는 승인 문맥 계약입니다.')
    return (media_snapshot if kind=='media-v1' else snapshot)(project)['sha256']
