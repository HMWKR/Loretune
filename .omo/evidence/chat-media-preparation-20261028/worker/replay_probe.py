"""Actual HTTP replay with a new request ID and current CAS values, no provider."""
from pathlib import Path
from copy import deepcopy
import json
import sys
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tests.test_general_chat_media_preparation import GeneralChatMediaPreparationTest

case = GeneralChatMediaPreparationTest('test_image_prepare_saves_one_card_and_http_replay_is_idempotent')
case.setUp()
try:
    requests = []
    mutate = case.f.http.store.mutate
    def record(request):
        if request['action'] == 'production_tool': requests.append(deepcopy(request))
        return mutate(request)
    with patch.object(case.f.http.store, 'mutate', side_effect=record):
        project = case.send_tool('prepare_image_action', case.arguments())
    action = case.actions()[0]
    state = case.f.state()
    active = state['projects']['A']['active_conversation']
    replay = deepcopy(requests[0])
    replay.update(request_id=uuid.uuid4().hex, revision=state['revision'],
                  conversation_id=active['id'], conversation_revision=active['revision'], shared_version=active['shared_version'])
    code, result = case.f.send(replay)
    assert code == 400, (code, result)
    assert '승인과 실행 연결이 변경됐습니다' in result['error'], result
    assert case.actions() == [action]
    case.assert_no_media_execution()
    (OUT/'replay-new-request-guard.json').write_text(json.dumps(dict(status='PASS',
        original_request_id=requests[0]['request_id'], replay_request_id=replay['request_id'],
        current_CAS_supplied=True, same_tool_call_preserved=replay['data']['call']==requests[0]['data']['call'],
        http_status=code, reason=result['error'], saved_action_id=action['id'], action_count=1,
        media_grants_jobs_reservations_submissions=0), ensure_ascii=False, indent=2)+'\n')
finally:
    case.f.doCleanups()
