"""Deterministic briefs: preserve authored scenes, disclose rules, never call AI."""
from copy import deepcopy
import hashlib
import json
import time
import uuid


def context(project):
    return dict(music=deepcopy(project.get('music_versions', [])[-1]) if project.get('music_head') else None,
                snapshot=deepcopy(project.get('snapshot', [])),ontology=deepcopy(project.get('ontology_snapshot')))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def propose(project, data):
    def field(name, limit=2000):
        value=data.get(name, '')
        if not isinstance(value,str) or len(value)>limit:raise ValueError('입력 길이·형식을 확인하세요: '+name)
        return value.strip()
    goal=field('goal'); scenes=field('scenes').splitlines(); scenes=[x.strip() for x in scenes if x.strip()]
    if not goal:raise ValueError('만들 영상의 목표를 입력하세요.')
    if not scenes or len(scenes)>30:raise ValueError('직접 검토할 장면을 1–30줄 입력하세요. 목표에서 장면을 자동 추정하지 않습니다.')
    style=field('style'); constraints=field('constraints')
    kind=data.get('kind','narrative')
    if kind not in {'narrative','performance','visualizer'}:raise ValueError('제작 목적을 선택하세요.')
    ctx=context(project); music=ctx['music']; count=len(scenes)
    questions=[]
    if not music:questions.append('음원을 연결하고 시작·끝 구간을 확정해 주세요. 시간 배치는 아직 미정입니다.')
    if kind=='performance':questions.append('립싱크는 현재 지원하지 않습니다. 가창 동기화 없이 진행할지 검토하세요.')
    plan=dict(id=uuid.uuid4().hex,version=len(project.get('guided_plans',[]))+1,engine='structured-local',status='proposed',
              goal=goal,style=style,constraints=constraints,kind=kind,context=ctx,context_hash=fingerprint(ctx),created=time.time(),questions=questions,
              scenes=[dict(id=uuid.uuid4().hex,description=s,duration=(music['end']-music['start'])/count if music else None,
                           music_start=music['start']+i*(music['end']-music['start'])/count if music else None) for i,s in enumerate(scenes)],
              explanation='입력한 장면 순서와 문구를 보존합니다. 확정 음악 구간이 있으면 장면 수로 균등 배분합니다. AI 추출·분석·생성은 실행하지 않습니다.')
    project.setdefault('guided_plans',[]).append(plan)
    return plan


def apply(studio, name, identifier):
    project=studio.projects[name]
    plan=next((p for p in project.get('guided_plans',[]) if p['id']==identifier),None)
    if not plan:raise ValueError('현재 작품의 계획이 아닙니다.')
    if plan['status']=='applied':return plan['shots']
    if plan['context_hash']!=fingerprint(context(project)):raise ValueError('음악 또는 기준 설정이 변경됐습니다. 새 계획으로 검토하세요.')
    if not plan['context']['music']:raise ValueError('음악 구간 확정 후 새 계획을 검토하세요.')
    shots=[]
    for scene in plan['scenes']:
        i=len(project['shots'])+1
        while f'장면 {i}' in project['shots']:i+=1
        shot=f'장면 {i}';studio.plan_shot(name,shot,scene['description'])
        project['shots'][shot].update(stable_id=scene['id'],plan_id=plan['id'],planned_duration=scene['duration'],music_start=scene['music_start'],music_version=plan['context']['music']['id'])
        shots.append(shot)
    plan.update(status='applied',shots=shots,approval=dict(actor='local-owner',scope='shot-plan',version=plan['version'],at=time.time(),cost_approval=False))
    return shots
