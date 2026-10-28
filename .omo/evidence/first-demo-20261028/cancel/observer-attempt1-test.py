"""Real platform HTTP cancellation with synthetic provider sockets only."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import unittest
import uuid
from unittest.mock import patch

import chat_general
import ledger
from app import Store
from tests import test_general_chat_activation as activation
from tests.test_chat_runtime import use


class GeneralChatCancelReceivedTest(unittest.TestCase):
    def setUp(self):
        self.h = activation.GeneralChatActivationHTTPTest()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        self.turn_id = None
        self.cancel_body = None
        self.observed = None

    def admit(self, response=None):
        self.h.socket.replies = [activation.reply() if response is None else response]
        preview = self.h.preview()
        status, result = self.h.approve(preview)
        self.assertEqual(status, 200, result)
        self.turn_id = result['turn']['id']
        return preview

    def request_cancel(self):
        state = self.h.state()
        self.cancel_body = dict(action='general_chat_cancel', data=dict(song='A', turn=self.turn_id),
                                revision=state['revision'], request_id=uuid.uuid4().hex)
        status, result = self.h.request('POST', '/api/action', self.cancel_body,
            {'Content-Type': 'application/json', 'X-Loretune-Token': state['token']})
        self.assertEqual(status, 200, result)
        return result

    def cancel_during_message(self, *, failure=None):
        original = self.h.socket.open

        def intercepted(request, timeout):
            if request.full_url.endswith('count_tokens'):
                return original(request, timeout)
            value = None if failure else original(request, timeout)
            self.request_cancel()
            turn, reservation, _ = self.h.reservation(self.turn_id)
            self.observed = {'status': turn['status'], 'reservation': reservation}
            self.assertEqual(self.observed, {'status': 'cancel_requested', 'reservation': ('reserved', None)})
            if failure:
                # Record the attempted request without forwarding any network call.
                self.h.socket.requests.append((request.full_url, request.data, timeout))
                raise failure
            return value

        started = time.monotonic()
        with patch.object(self.h.socket, 'open', side_effect=intercepted):
            self.h.process()
        return time.monotonic() - started

    def record(self, label, elapsed=None):
        turn, reservation, attempts = self.h.reservation(self.turn_id)
        state = self.h.state()
        with self.h.http.store.connect() as c:
            events = c.execute('SELECT kind,body FROM ledger_events ORDER BY rowid').fetchall()
        result = dict(turn=turn, reservation=reservation, attempts=attempts,
                      budget=state['budgets'], during_cancel=self.observed,
                      ledger_events=events, synthetic_socket_requests=len(self.h.socket.requests),
                      actual_provider_calls=0, elapsed_seconds=elapsed)
        destination = os.environ.get('CANCEL_RECEIVED_EVIDENCE')
        if destination:
            out = Path(destination)
            out.mkdir(parents=True, exist_ok=True)
            (out / (label + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        return result

    def assert_unresolved_blocks_following_conversation(self):
        cid = self.h.post('conversation_create', song='A', title='미확정 보호 검증')['conversation']['id']
        preview = self.h.preview(conversation=cid)
        before = len(self.h.socket.requests)
        status, result = self.h.approve(preview, conversation=cid)
        self.assertEqual(status, 400, result)
        self.assertEqual(len(self.h.socket.requests), before)

    def test_received_priced_cancel_preserves_cost_and_allows_next_request(self):
        self.admit()
        elapsed = self.cancel_during_message()
        result = self.record('received-priced-cancel', elapsed)
        self.assertLess(elapsed, 30)
        self.assertEqual(result['turn']['status'], 'cancelled')
        self.assertIsNone(result['turn']['answer'])
        self.assertEqual(result['reservation'], ('estimated', 60))
        self.assertEqual(result['attempts'], [('chat-count', 'observed'), ('chat-message', 'observed')])
        self.assertEqual(result['turn']['usage'], {'input_tokens': 100, 'output_tokens': 100})
        self.assertEqual(result['turn']['steps'][-1]['usage_cost_usd'], '0.00006')
        self.assertFalse(result['turn']['billing_confirmed'])
        self.assertEqual(result['budget'][0]['data']['uncertainReservations'], 0)
        self.assertEqual(len(self.h.socket.requests), 2)
        following = self.h.preview()
        status, value = self.h.approve(following)
        self.assertEqual(status, 200, value)
        self.h.socket.replies = [activation.reply()]
        self.h.process()
        self.assertEqual(self.h.reservation(value['turn']['id'])[0]['status'], 'completed')

    def test_cancelled_received_tool_response_never_applies_tool(self):
        response = activation.reply([use('not-applied', 'propose_media_plan',
            dict(goal='자동 적용 금지', scenes='취소된 장면', style='', constraints='', kind='visualizer'))], 'tool_use')
        self.admit(response)
        self.cancel_during_message()
        result = self.record('received-tool-not-applied')
        self.assertEqual(result['turn']['status'], 'cancelled')
        self.assertEqual(result['reservation'], ('estimated', 60))
        self.assertNotIn('pending_tool', result['turn'])
        self.assertEqual(self.h.project().get('guided_plans', []), [])
        self.assertEqual(self.h.project().get('shots', {}), {})

    def test_incomplete_billing_usage_cancel_remains_unknown(self):
        self.admit(activation.response())
        self.cancel_during_message()
        result = self.record('incomplete-usage-remains-unknown')
        self.assertEqual(result['turn']['status'], 'outcome_unknown')
        self.assertEqual(result['reservation'], ('uncertain', None))
        self.assertEqual(result['turn']['pricing_status'], 'insufficient_billing_evidence')
        self.assert_unresolved_blocks_following_conversation()

    def test_timeout_cancel_remains_unknown_and_never_retries(self):
        self.admit()
        self.cancel_during_message(failure=TimeoutError('synthetic unknown response'))
        result = self.record('timeout-remains-unknown')
        self.assertEqual(result['turn']['status'], 'outcome_unknown')
        self.assertEqual(result['reservation'], ('uncertain', None))
        self.assertIn(('chat-message', 'unknown'), result['attempts'])
        self.assertFalse(self.h.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.h.socket.requests), 2)
        self.assert_unresolved_blocks_following_conversation()

    def test_received_cancel_with_ledger_failure_keeps_unknown_hold(self):
        self.admit()
        original = ledger.command

        def fail_estimate(c, workspace, scope, kind, data, key):
            if kind == 'estimate':
                raise sqlite3.OperationalError('synthetic accounting failure')
            return original(c, workspace, scope, kind, data, key)

        with patch.object(ledger, 'command', side_effect=fail_estimate):
            self.cancel_during_message()
        result = self.record('ledger-failure-remains-unknown')
        self.assertEqual(result['turn']['status'], 'outcome_unknown')
        self.assertEqual(result['turn']['pricing_status'], 'ledger_update_failed')
        self.assertEqual(result['turn']['journal_failure'], 'update_failed')
        self.assertEqual(result['reservation'], ('uncertain', None))
        self.assert_unresolved_blocks_following_conversation()

    def test_queued_cancel_has_no_provider_attempt_or_cost(self):
        self.admit()
        self.request_cancel()
        self.assertFalse(self.h.http.store.general_chat_runtime.process_next())
        result = self.record('queued-cancel')
        self.assertEqual(result['turn']['status'], 'cancelled')
        self.assertEqual(result['reservation'], ('cancelled', None))
        self.assertEqual(result['attempts'], [])
        self.assertEqual(self.h.socket.requests, [])

    def test_cancel_after_count_still_prevents_message_dispatch(self):
        self.admit()
        original = self.h.socket.open

        def after_count(request, timeout):
            value = original(request, timeout)
            self.request_cancel()
            return value

        with patch.object(self.h.socket, 'open', side_effect=after_count):
            self.h.process()
        result = self.record('cancel-after-count')
        self.assertEqual(result['turn']['status'], 'cancelled')
        self.assertEqual(result['reservation'], ('cancelled', None))
        self.assertEqual(result['attempts'], [('chat-count', 'observed')])
        self.assertEqual(len(self.h.socket.requests), 1)

    def test_received_cancel_replay_and_reopen_preserve_observed_state(self):
        self.admit()
        self.cancel_during_message()
        before = self.record('replay-reopen-before')
        self.assertEqual(before['turn']['status'], 'cancelled')
        token = self.h.state()['token']
        status, result = self.h.request('POST', '/api/action', self.cancel_body,
            {'Content-Type': 'application/json', 'X-Loretune-Token': token})
        self.assertEqual(status, 200, result)
        self.assertFalse(self.h.http.store.general_chat_runtime.process_next())
        after = self.record('replay-reopen-after')
        self.assertEqual(after['turn'], before['turn'])
        self.assertEqual(after['reservation'], before['reservation'])
        self.assertEqual(after['attempts'], before['attempts'])
        self.assertEqual(after['ledger_events'], before['ledger_events'])
        self.assertEqual(len(self.h.socket.requests), 2)
        reopened = Store(self.h.tmp.name)
        with reopened.connect() as c:
            retained = chat_general.get_row(c, 'general_chat_turns', self.turn_id)
            held = c.execute('SELECT state,actual FROM reservations WHERE id=?', (retained['reservation'],)).fetchone()
        self.assertEqual(retained, before['turn'])
        self.assertEqual(held, before['reservation'])


if __name__ == '__main__':
    unittest.main()
