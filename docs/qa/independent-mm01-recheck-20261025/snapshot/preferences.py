"""Explicit local preference proposals, separate from canonical facts."""
from copy import deepcopy
import time

CATEGORIES={'color','texture','camera','editing'}


def propose(items, *, ip, song, category, value, evidence, reason, supersedes=None):
    if category not in CATEGORIES:raise ValueError('색감·질감·카메라·편집 중 하나를 선택하세요.')
    if supersedes is not None:
        old=next((x for x in items if x['id']==supersedes),None)
        if not old or (old['ip'],old['song'],old['category'])!=(ip,song,category):
            raise ValueError('같은 IP·범위·속성의 선호 버전만 정정할 수 있습니다.')
    item=dict(id=len(items)+1,ip=ip,song=song,category=category,value=value,
              evidence=evidence,reason=reason,supersedes=supersedes,status='proposed',events=[],created=time.time())
    items.append(item)
    return item


def review(items, identifier, decision, reason):
    item=next((x for x in items if x['id']==identifier),None)
    if not item:raise ValueError('선호 후보가 없습니다.')
    if decision not in {'active','rejected','paused'}:raise ValueError('승인·거절·중지를 선택하세요.')
    if decision=='active':
        others=[x for x in items if x['id']!=identifier and x['status']=='active'
                and (x['ip'],x['song'],x['category'])==(item['ip'],item['song'],item['category'])]
        if any(x['id']!=item['supersedes'] for x in others):
            raise ValueError('이미 활성 규칙이 있습니다. 현재 활성 버전을 지정해 정정 후보를 만드세요.')
        for old in others:
            old['status']='paused'
            old['events'].append(dict(decision='paused',reason=f'v{identifier} 승인으로 대체',at=time.time()))
    item['status']=decision
    item['events'].append(dict(decision=decision,reason=reason,at=time.time(),actor='local-owner'))
    return item


def resolve(items, ip, song):
    result={}
    for scope in [None,song]:
        for item in items:
            if item['ip']==ip and item['song']==scope and item['status']=='active':
                result[item['category']]=deepcopy(item)
    return list(result.values())
