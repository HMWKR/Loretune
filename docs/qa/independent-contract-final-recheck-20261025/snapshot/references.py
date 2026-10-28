"""Versioned reference assignments. These are planning inputs, not AI output."""
from copy import deepcopy
import time

ROLES = {'character', 'style', 'start_frame', 'end_frame'}


def assign(shot, role, source, reason):
    if role not in ROLES:
        raise ValueError('캐릭터·스타일·시작 프레임·끝 프레임 역할을 선택하세요.')
    versions = shot.setdefault('reference_versions', [])
    roles = deepcopy(versions[-1]['roles']) if versions else {}
    roles[role] = deepcopy(source)
    version = dict(id=len(versions)+1, roles=roles, reason=reason, created=time.time(), status='unreviewed')
    versions.append(version)
    shot['reference_head'] = version['id']
    shot['revision'] += 1
    return version


def review(shot, version, decision, reason):
    if version != shot.get('reference_head'):
        raise ValueError('참고 버전이 변경되었습니다. 현재 버전을 다시 검토하세요.')
    if decision not in {'approved', 'changes_requested', 'rejected'}:
        raise ValueError('검토 상태를 확인하세요.')
    item=shot['reference_versions'][version-1]
    item.setdefault('reviews', []).append(dict(decision=decision,reason=reason,at=time.time(),actor='local-owner'))
    item['status']=decision
    shot['revision']+=1
    return item
