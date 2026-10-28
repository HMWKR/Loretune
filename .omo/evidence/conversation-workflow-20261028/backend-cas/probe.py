"""HTTP CAS reproduction against production transport activation, no provider calls."""
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tests.test_general_chat_activation import GeneralChatActivationHTTPTest


def request(case, cid, action, **data):
    state = case.http.store.state({'A': cid})
    active = state['projects']['A']['active_conversation']
    return dict(action=action, data=dict(song='A', **data), revision=state['revision'],
                request_id=uuid.uuid4().hex, conversation_id=cid,
                conversation_revision=active['revision'], shared_version=active['shared_version'])


def send(case, payload):
    return case.request('POST', '/api/action', payload, {'Content-Type': 'application/json',
                         'X-Loretune-Token': case.state()['token']})


def snapshot(case):
    with case.http.store.connect() as c:
        return {table: [list(row) for row in c.execute('SELECT * FROM '+table+' ORDER BY rowid')]
                for table in ('state', 'requests', 'general_chat_previews', 'general_chat_turns', 'reservations')}


def run(action):
    case = GeneralChatActivationHTTPTest()
    case.setUp()
    try:
        first = case.project()['active_conversation']['id']
        other = case.post('conversation_create', song='A', title='B', conversation=first)['conversation']['id']
        data = dict(prompt='B의 음악 영상 제작을 도와줘', maximum_micro=10000, total_maximum_micro=10000)
        if action != 'general_chat_preview':
            preview = case.preview(conversation=other)
            data = dict(preview_id=preview['id'], manifest_sha256=preview['manifest_sha256'],
                        decision='approve', rights_confirmed=True)
            if action == 'general_chat_cancel':
                status, approved = case.approve(preview, conversation=other)
                assert status == 200, approved
                data = dict(turn=approved['turn']['id'])
        pending = request(case, other, action, **data)
        case.preview(conversation=first)
        current = request(case, other, action, **data)
        assert current['revision'] > pending['revision']
        assert current['conversation_revision'] == pending['conversation_revision']
        assert current['shared_version'] == pending['shared_version']
        before = snapshot(case)
        status, body = send(case, pending)
        after = snapshot(case)
        assert status == 409, (status, body)
        assert before == after, 'Rejected request wrote state'
        assert not case.socket.requests and not case.keys
        fresh_status, fresh_body = send(case, current)
        assert fresh_status == 200, fresh_body
        return dict(action=action, stale_global_status=status, response=body,
                    fresh_global_status=fresh_status, same_conversation_revision=True,
                    same_shared_fingerprint=True, rejected_atomic=True, provider_calls=0,
                    old_revision=pending['revision'], current_revision=current['revision'])
    finally:
        case.doCleanups()


if __name__ == '__main__':
    output = dict(invocation='python3 .omo/evidence/conversation-workflow-20261028/backend-cas/probe.py',
                  transport='production activation with synthetic provider socket; no worker',
                  source_sha256=hashlib.sha256((ROOT/'chat_sessions.py').read_bytes()).hexdigest(),
                  cases=[run(action) for action in ('general_chat_preview','general_chat_decide','general_chat_cancel')])
    path = Path(__file__).with_name('baseline.json')
    if path.exists():
        raise RuntimeError('Refusing to overwrite baseline')
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(output, ensure_ascii=False))
