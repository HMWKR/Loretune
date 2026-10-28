"""Conversation CAS over real HTTP with production activation and synthetic sockets."""
from copy import deepcopy
from decimal import Decimal
import unittest
import uuid
from unittest.mock import patch

from tests import test_general_chat_activation as activation


class GeneralChatConversationsTest(unittest.TestCase):
    def setUp(self):
        self.h = activation.GeneralChatActivationHTTPTest()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        self.a = self.h.project()['active_conversation']['id']
        self.b = self.h.post('conversation_create', song='A', title='B',
                             conversation=self.a)['conversation']['id']

    def payload(self, conversation, action, **data):
        state = self.h.http.store.state({'A': conversation})
        active = state['projects']['A']['active_conversation']
        return dict(action=action, data=dict(song='A', **data), revision=state['revision'],
                    request_id=uuid.uuid4().hex, conversation_id=conversation,
                    conversation_revision=active['revision'], shared_version=active['shared_version'])

    def send(self, body):
        return self.h.request('POST', '/api/action', body, {'Content-Type': 'application/json',
                             'X-Loretune-Token': self.h.state()['token']})

    def snapshot(self):
        with self.h.http.store.connect() as c:
            return {table: c.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                    for table in ('state', 'requests', 'general_chat_previews', 'general_chat_turns',
                                  'reservations', 'ledger_events', 'ledger_requests', 'provider_attempts')}

    def assert_rejected_atomically(self, body, status):
        before = self.snapshot()
        observed, result = self.send(body)
        self.assertEqual(observed, status, result)
        self.assertEqual(self.snapshot(), before)
        return result

    def approval(self, preview, conversation=None, **changes):
        data = dict(preview_id=preview['id'], manifest_sha256=preview['manifest_sha256'],
                    decision='approve', rights_confirmed=True)
        data.update(changes)
        return self.payload(conversation or self.b, 'general_chat_decide', **data)

    def prepare(self, action):
        if action == 'general_chat_preview':
            return self.payload(self.b, action, prompt='B의 음악 영상 제작',
                                maximum_micro=10000, total_maximum_micro=10000)
        preview = self.h.preview(conversation=self.b)
        approval = self.approval(preview)
        if action == 'general_chat_decide':
            return approval
        status, result = self.send(approval)
        self.assertEqual(status, 200, result)
        return self.payload(self.b, action, turn=result['turn']['id'])

    def sibling_change(self, body):
        self.h.preview(conversation=self.a)
        current = self.payload(self.b, body['action'])
        self.assertGreater(current['revision'], body['revision'])
        self.assertEqual(current['conversation_revision'], body['conversation_revision'])
        self.assertEqual(current['shared_version'], body['shared_version'])

    def test_preview_tolerates_sibling_revision_and_stays_private(self):
        body = self.prepare('general_chat_preview')
        self.sibling_change(body)
        status, result = self.send(body)
        self.assertEqual(status, 200, result)
        identifier = result['general_chat_preview']['id']
        a = self.h.http.store.state({'A': self.a})['projects']['A']
        b = self.h.http.store.state({'A': self.b})['projects']['A']
        self.assertNotIn(identifier, [x['id'] for x in a['general_chat_previews']])
        self.assertIn(identifier, [x['id'] for x in b['general_chat_previews']])
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_approval_tolerates_sibling_revision_and_replay_reserves_once(self):
        body = self.prepare('general_chat_decide')
        self.sibling_change(body)
        status, result = self.send(body)
        self.assertEqual(status, 200, result)
        self.assertEqual(result['turn']['status'], 'queued')
        self.assertEqual(result['turn']['conversation_id'], self.b)
        before = self.snapshot()
        self.assertEqual(self.send(body), (200, result))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(before['general_chat_turns']), 1)
        self.assertEqual(len(before['reservations']), 1)
        changed = deepcopy(body)
        changed['data']['decision'] = 'reject'
        self.assert_rejected_atomically(changed, 409)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_queued_cancel_tolerates_sibling_revision_and_releases_once(self):
        body = self.prepare('general_chat_cancel')
        self.sibling_change(body)
        status, result = self.send(body)
        self.assertEqual(status, 200, result)
        turn, held, attempts = self.h.reservation(body['data']['turn'])
        self.assertEqual((turn['status'], held, attempts), ('cancelled', ('cancelled', None), []))
        before = self.snapshot()
        self.assertEqual(self.send(body), (200, result))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def reject_stale(self, action, shared):
        body = self.prepare(action)
        if shared:
            self.h.post('shot', song='A', shot='공유 장면', description='새 공유 문맥', conversation=self.a)
        else:
            self.h.post('guided_plan', song='A', goal='B 수정', scenes='장면', style='', constraints='',
                        kind='narrative', conversation=self.b)
        result = self.assert_rejected_atomically(body, 409)
        self.assertIn('대화 또는 공유 설정', result['error'])
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_preview_rejects_stale_conversation(self):
        self.reject_stale('general_chat_preview', False)

    def test_approval_rejects_stale_conversation(self):
        self.reject_stale('general_chat_decide', False)

    def test_cancel_rejects_stale_conversation(self):
        self.reject_stale('general_chat_cancel', False)

    def test_preview_rejects_changed_shared_context(self):
        self.reject_stale('general_chat_preview', True)

    def test_approval_rejects_changed_shared_context(self):
        self.reject_stale('general_chat_decide', True)

    def test_cancel_rejects_changed_shared_context(self):
        self.reject_stale('general_chat_cancel', True)

    def test_unscoped_request_still_requires_global_revision(self):
        body = self.prepare('general_chat_preview')
        self.sibling_change(body)
        for field in ('conversation_id', 'conversation_revision', 'shared_version'):
            body.pop(field)
        result = self.assert_rejected_atomically(body, 409)
        self.assertIn('다른 화면', result['error'])

    def test_other_conversation_cannot_approve_or_reject_preview_or_cancel_turn(self):
        preview = self.h.preview(conversation=self.b)
        for decision in ('approve', 'reject'):
            self.assert_rejected_atomically(self.approval(preview, self.a, decision=decision), 400)
        status, result = self.send(self.approval(preview))
        self.assertEqual(status, 200, result)
        self.assert_rejected_atomically(self.payload(self.a, 'general_chat_cancel', turn=result['turn']['id']), 400)
        turn, held, _ = self.h.reservation(result['turn']['id'])
        self.assertEqual((turn['status'], held), ('queued', ('reserved', None)))

    def test_invalid_manifest_rights_and_new_request_replay_stay_atomic(self):
        preview = self.h.preview(conversation=self.b)
        for changes in ({'manifest_sha256': '0'*64}, {'rights_confirmed': False}):
            body = self.approval(preview, **changes)
            self.sibling_change(body)
            self.assert_rejected_atomically(body, 400)
        status, result = self.send(self.approval(preview))
        self.assertEqual(status, 200, result)
        self.assert_rejected_atomically(self.approval(preview), 400)
        self.assertEqual(len(self.snapshot()['reservations']), 1)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_changed_rights_registry_blocks_approval_after_sibling_drift(self):
        body = self.prepare('general_chat_decide')
        self.sibling_change(body)
        with self.h.http.store.connect() as c:
            c.execute('INSERT INTO asset_rights VALUES (?,?,?,?)', ('a'*64, 1, '권리 변경', 1))
        self.assert_rejected_atomically(body, 400)
        self.assertEqual(len(self.snapshot()['reservations']), 0)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_project_concurrency_cap_cannot_be_avoided_by_another_conversation(self):
        state = self.h.state()
        budget = next(x for x in state['budgets'] if x['data']['scope'] == 'project:'+self.h.pid)
        body = dict(period='project', projectId=self.h.pid, limit={'amount': '1', 'currency': 'USD'},
                    maxConcurrentJobs=1, allowAutomaticRetries=False)
        status, result = self.h.request('PATCH', '/v1/workspaces/'+state['workspace_id']+'/billing/budgets', body,
            {'Content-Type': 'application/json', 'Authorization': 'Bearer '+state['token'],
             'If-Match': '"'+str(budget['revision'])+'"'})
        self.assertEqual(status, 200, result)
        first = self.h.preview(conversation=self.a)
        second = self.h.preview(conversation=self.b)
        pending = self.approval(second)
        status, result = self.send(self.approval(first, self.a))
        self.assertEqual(status, 200, result)
        rejected = self.assert_rejected_atomically(pending, 400)
        self.assertIn('동시 작업 한도', rejected['error'])
        before = self.snapshot()
        self.assertEqual(len(before['general_chat_turns']), 1)
        self.assertEqual(len(before['reservations']), 1)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_project_money_cap_is_shared_across_conversations(self):
        quote = self.h.preview(conversation=self.a)
        ceiling = quote['reserve_micro'] * 3 // 2
        self.h.budget(format(Decimal(ceiling) / 1000000, '.6f'))
        first = self.h.preview(conversation=self.a)
        second = self.h.preview(conversation=self.b)
        self.assertLessEqual(first['reserve_micro'], ceiling)
        self.assertGreater(first['reserve_micro'] + second['reserve_micro'], ceiling)
        pending = self.approval(second)
        status, result = self.send(self.approval(first, self.a))
        self.assertEqual(status, 200, result)
        self.assert_rejected_atomically(pending, 400)
        self.assertEqual(len(self.snapshot()['reservations']), 1)
        self.assertEqual((self.h.socket.requests, self.h.keys), ([], []))

    def test_running_cancel_after_sibling_drift_prevents_message_dispatch(self):
        body = self.prepare('general_chat_cancel')
        original = self.h.socket.open
        observed = []

        def cancel_after_count(request, timeout):
            value = original(request, timeout)
            self.sibling_change(body)
            status, result = self.send(body)
            self.assertEqual(status, 200, result)
            turn, held, _ = self.h.reservation(body['data']['turn'])
            observed.append((turn['status'], held))
            return value

        with patch.object(self.h.socket, 'open', side_effect=cancel_after_count):
            self.h.process()
        self.assertEqual(observed, [('cancel_requested', ('reserved', None))])
        turn, held, attempts = self.h.reservation(body['data']['turn'])
        self.assertEqual((turn['status'], held), ('cancelled', ('cancelled', None)))
        self.assertEqual(attempts, [('chat-count', 'observed')])
        self.assertEqual(len(self.h.socket.requests), 1)

    def test_unknown_cancel_preserves_uncertain_reservation_and_never_retries(self):
        body = self.prepare('general_chat_cancel')
        self.h.socket.replies = [TimeoutError('synthetic timeout')]
        self.h.process()
        body = self.payload(self.b, 'general_chat_cancel', turn=body['data']['turn'])
        self.sibling_change(body)
        status, result = self.send(body)
        self.assertEqual(status, 200, result)
        turn, held, attempts = self.h.reservation(body['data']['turn'])
        self.assertEqual((turn['status'], held), ('outcome_unknown', ('uncertain', None)))
        self.assertIn(('chat-message', 'unknown'), attempts)
        self.assertFalse(self.h.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.h.socket.requests), 2)
        self.assert_rejected_atomically(self.payload(self.a, 'general_chat_cancel', turn=turn['id']), 400)
        preview = self.h.preview(conversation=self.a)
        self.assert_rejected_atomically(self.approval(preview, self.a), 400)
        self.assertEqual(len(self.snapshot()['reservations']), 1)
        self.assertEqual(len(self.h.socket.requests), 2)


if __name__ == '__main__':
    unittest.main()
