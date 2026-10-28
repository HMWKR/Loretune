"""Saved plan/action authority for the existing gated fal queue.

No credentials, transport, second worker, or second budget reservation. An AI
tool may retrieve an already admitted receipt; it cannot approve or dispatch.
The legacy start_generation human controller is the only admission path.
"""
from copy import deepcopy
import json
import time
import action_execution as actions
import fal_provider as fal
import guided
import ledger
import model_selection
from loretune import Conflict

CONNECTION = 'fal-kling-queue-v1'


def prepare(c, workspace, project_id, project, shot, prep):
    plan_id = shot.get('plan_id')
    if not plan_id:
        return None  # Legacy manually authored shots keep their existing path.
    plan = next((p for p in project.get('guided_plans', []) if p['id'] == plan_id), None)
    if not plan or plan['status'] != 'applied' or prep['shot'] not in plan['shots']:
        raise ValueError('승인된 현재 작품의 계획과 샷 연결이 필요합니다.')
    if plan['context_hash'] != guided.fingerprint(guided.context(project)):
        raise Conflict('계획 문맥이 변경되었습니다. 다시 검토하세요.')
    action = actions.propose(c, workspace, project_id, plan_id=plan_id,
        plan_revision=plan['version'], context_hash=model_selection.media_snapshot(project)['sha256'],
        context_kind='media-v1', role='video', release_id=fal.MODEL,
        inputs=dict(preparation=prep['id'], shot=prep['shot'], shot_revision=prep['shot_revision'],
            reference_version=prep['reference_version'], image_sha256=prep['source']['sha256'],
            prompt=prep['prompt']),
        options=dict(duration=10, generate_audio=False, enable_safety_checker=True,
            privacy='private', retention_seconds=3600, price_revision=guided.fingerprint(prep['estimate'])),
        mode='provider', connection_id=CONNECTION)
    prep.update(action_id=action['id'], plan_id=plan_id, plan_revision=plan['version'])
    return action


def authorize(c, workspace, project_id, project, prep, gate):
    """Called only after the Store's pinned live gate, rights and budget checks."""
    if not prep.get('action_id'):
        return None
    action = actions.get(c, 'production_actions', workspace, project_id, prep['action_id'])
    expected = dict(preparation=prep['id'], shot=prep['shot'], shot_revision=prep['shot_revision'],
        reference_version=prep['reference_version'], image_sha256=prep['source']['sha256'], prompt=prep['prompt'])
    if (action['mode'], action['connection_id'], action['release_id'], action['role']) != ('provider', CONNECTION, fal.MODEL, 'video'):
        raise ValueError('고정된 공급자 실행 계약이 아닙니다.')
    if action['inputs'] != expected or action['dependencies']:
        raise ValueError('승인할 준비 입력과 작업이 다릅니다.')
    price = guided.fingerprint(prep['estimate'])
    if action['options'] != dict(duration=10, generate_audio=False, enable_safety_checker=True,
            privacy='private', retention_seconds=3600, price_revision=price):
        raise ValueError('출력·개인정보·가격 조건이 변경됐습니다.')
    g = actions.grant(c, workspace, project_id, [action['id']], actor='local-owner', approved=True,
        expires=min(gate['expires'], prep['estimate']['expires'], time.time()+3599),
        price_revision=price, money_by_action={action['id']:prep['estimate']['money']})
    actions.validate(action, g, model_selection.action_context(project, action), price)
    return dict(action_id=action['id'], action_hash=action['hash'], grant_id=g['id'], grant_hash=g['hash'],
        plan_id=action['plan_id'], plan_revision=action['plan_revision'], release_id=action['release_id'],
        connection_id=CONNECTION, price_revision=price, workspace=workspace, project=project_id)


def bind(c, workspace, project_id, job):
    binding = job['context'].get('action_binding')
    if binding:
        c.execute('INSERT INTO provider_action_jobs VALUES (?,?,?,?)',
            (workspace, project_id, binding['action_id'], job['id']))


def validate_submission(c, workspace, project_id, project, job):
    b = job['context'].get('action_binding')
    if not b:
        return
    if (b['workspace'], b['project'], b['connection_id']) != (workspace, project_id, CONNECTION):
        raise ValueError('공급자 작업 소유 범위가 다릅니다.')
    row = c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',
        (workspace, project_id, b['action_id'])).fetchone()
    if not row or row[0] != job['id']:
        raise ValueError('작업 접수 연결이 다릅니다.')
    action = actions.get(c, 'production_actions', workspace, project_id, b['action_id'])
    g = actions.get(c, 'execution_grants', workspace, project_id, b['grant_id'])
    price = guided.fingerprint({k:v for k,v in job['quote'].items() if k != 'budget_revision'})
    actions.validate(action, g, model_selection.action_context(project, action), price)
    if action['hash'] != b['action_hash'] or g['hash'] != b['grant_hash'] or g['money'][action['id']] != job['quote']['money']:
        raise ValueError('등록 후 승인·견적이 변경됐습니다.')
    if not g['external_transmission'] or action['mode'] != 'provider' or action['release_id'] != fal.MODEL:
        raise ValueError('공급자 전송 승인 불일치')


def projection(c, job):
    b = job['context'].get('action_binding') or {}
    row = c.execute('SELECT state,actual FROM reservations WHERE id=?', (job.get('reservation'),)).fetchone()
    money = job.get('quote',{}).get('money')
    return dict(id=job['id'], state=job['state'], mode=job.get('mode','provider-unverified'),
        context={'song':job['context']['song']}, failure_code=job.get('failure_code'),
        **{k:b.get(k) for k in ('action_id','plan_id','plan_revision','release_id','grant_id')},
        external_calls=job.get('external_calls'), provider_completed=bool(job.get('result')),
        result=dict(sha256=job['asset_sha256'],output_slot=job.get('context',{}).get('output_kind','video')) if job.get('asset_sha256') else None,
        result_approved=False, cost=dict(reservation_state=row[0] if row else 'unknown',
            estimate=deepcopy(money), actual=ledger.money(row[1],money['currency']) if row and row[1] is not None and money else None,
            billing_confirmed=job.get('cost_confirmed',False),evidence=deepcopy(job.get('cost_evidence'))))


def receipt(c, workspace, project_id, project, action, grant_id):
    row = c.execute('SELECT job FROM provider_action_jobs WHERE workspace=? AND project=? AND action=?',
        (workspace, project_id, action['id'])).fetchone()
    if not row:
        raise actions.ExecutionBlocked('사람의 전송·비용 승인 후 작업대에서 먼저 접수하세요. 외부 전송 없음.')
    job = json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?', row).fetchone()[0])
    b = job['context']['action_binding']
    if b['grant_id'] != grant_id or b['action_hash'] != action['hash']:
        raise actions.ExecutionBlocked('다른 작업 또는 승인 영수증입니다.')
    # Read an already admitted job even after model handoff or grant expiry.
    # No re-admission, transport, reservation or state transition occurs here.
    return dict(status='existing',job_id=job['id'], **{k:v for k,v in projection(c,job).items() if k not in {'id','context'}},
        note='기존 접수 작업을 조회했습니다. 새 생성·추가 예약은 실행하지 않았습니다.')
