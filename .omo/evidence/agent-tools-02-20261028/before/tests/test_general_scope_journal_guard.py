"""Reserved holds with failed journal updates must block only their own scope."""
import json
import sqlite3
import time
import unittest
import uuid
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import urlopen

import ledger
from tests import test_budget_crossflow


class GeneralScopeJournalGuardTest(unittest.TestCase):
    def setUp(self):
        self.cross = test_budget_crossflow.CrossFlowBudgetTest('test_competing_admissions_have_only_one_winner')
        self.cross.setUp()
        self.addCleanup(self.cross.doCleanups)
        self.f = self.cross.fixture
        self.store = self.cross.store
        self.scope = self.cross.scope

    def fail_after_response(self):
        first = self.f.preview()
        self.assertEqual(self.f.approve(first)[0], 200)
        original = ledger.command

        def fail(c, workspace, scope, kind, data, key):
            if kind in {'estimate', 'uncertain'}:
                raise sqlite3.OperationalError('synthetic persistent journal failure')
            return original(c, workspace, scope, kind, data, key)

        with patch.object(ledger, 'command', side_effect=fail):
            self.assertTrue(self.store.general_chat_runtime.process_next())
        with self.store.connect() as c:
            row = json.loads(c.execute('SELECT body FROM general_chat_turns ORDER BY rowid DESC LIMIT 1').fetchone()[0])
            reservation = c.execute('SELECT state,actual,amount FROM reservations WHERE id=?', (row['reservation'],)).fetchone()
        self.assertEqual((row['status'], row['journal_failure']), ('outcome_unknown', 'update_failed'))
        self.assertEqual(reservation[0:2], ('reserved', None))
        return row, reservation

    def session_action(self, cid, action, **data):
        with urlopen(self.f.base + '/api/state?' + urlencode({'song': 'A', 'conversation': cid})) as response:
            state = json.load(response)
        active = state['projects']['A']['active_conversation']
        return self.f.send(dict(action=action, data=data, revision=state['revision'], request_id=uuid.uuid4().hex,
                                conversation_id=cid, conversation_revision=active['revision'],
                                shared_version=active['shared_version']))

    def test_persistent_failure_blocks_other_conversation(self):
        row, original_reservation = self.fail_after_response()
        prior_requests = len(self.f.provider.requests)
        status, value = self.f.action('conversation_create', song='A', title='다른 대화')
        self.assertEqual(status, 200, value)
        cid = value['conversation']['id']
        status, value = self.session_action(cid, 'general_chat_preview', song='A', prompt='다음 장면', maximum_micro=10000, total_maximum_micro=10000)
        self.assertEqual(status, 200, value)
        preview = value['general_chat_preview']
        status, _ = self.session_action(cid, 'general_chat_decide', song='A', preview_id=preview['id'],
                                        manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
        self.assertEqual(status, 400)
        self.assertEqual(len(self.f.provider.requests), prior_requests)
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual,amount FROM reservations WHERE id=?', (row['reservation'],)).fetchone(), original_reservation)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM reservations').fetchone()[0], 1)
        self.assertEqual(self.f.state()['projects']['A'].get('guided_plans', []), [])

    def test_persistent_failure_blocks_same_scope_generation(self):
        row, original_reservation = self.fail_after_response()
        prior_requests = len(self.f.provider.requests)
        with self.assertRaises(ledger.BudgetExposureBlocked):
            self.cross.generation('after-general-journal-failure')
        self.assertEqual(len(self.f.provider.requests), prior_requests)
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual,amount FROM reservations WHERE id=?', (row['reservation'],)).fetchone(), original_reservation)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM reservations').fetchone()[0], 1)

    def test_already_queued_generation_is_not_dispatched_after_failure(self):
        queued = self.cross.generation('already-queued')
        row, original_reservation = self.fail_after_response()
        calls = []

        class Adapter:
            def submit(self, data):
                calls.append(data)
                return {'request_id': 'fixture'}

        result = self.store.generation.dispatch(queued['id'], Adapter())
        self.assertEqual((result['state'], result['verified_unsubmitted']), ('submission_blocked', True))
        self.assertEqual(calls, [])
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?', (queued['reservation'],)).fetchone()[0], 'cancelled')
            self.assertEqual(c.execute('SELECT state,actual,amount FROM reservations WHERE id=?', (row['reservation'],)).fetchone(), original_reservation)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts WHERE job=?', (queued['id'],)).fetchone()[0], 0)

    def test_already_queued_other_conversation_is_blocked_before_count(self):
        first = self.f.preview()
        self.assertEqual(self.f.approve(first)[0], 200)
        status, value = self.f.action('conversation_create', song='A', title='대기 중인 다른 대화')
        self.assertEqual(status, 200, value)
        cid = value['conversation']['id']
        status, value = self.session_action(cid, 'general_chat_preview', song='A', prompt='다음 장면', maximum_micro=10000, total_maximum_micro=10000)
        self.assertEqual(status, 200, value)
        preview = value['general_chat_preview']
        status, value = self.session_action(cid, 'general_chat_decide', song='A', preview_id=preview['id'],
                                            manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
        self.assertEqual(status, 200, value)
        queued_id = value['turn']['id']
        original = ledger.command

        def fail(c, workspace, scope, kind, data, key):
            if kind in {'estimate', 'uncertain'}:
                raise sqlite3.OperationalError('synthetic persistent journal failure')
            return original(c, workspace, scope, kind, data, key)

        with patch.object(ledger, 'command', side_effect=fail):
            self.assertTrue(self.store.general_chat_runtime.process_next())
        previous_requests = len(self.f.provider.requests)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.f.provider.requests), previous_requests)
        with self.store.connect() as c:
            turn = json.loads(c.execute('SELECT body FROM general_chat_turns WHERE id=?', (queued_id,)).fetchone()[0])
            self.assertEqual(turn['status'], 'blocked_before_message')
            self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?', (turn['reservation'],)).fetchone()[0], 'cancelled')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts WHERE job=?', (queued_id,)).fetchone()[0], 0)

    def test_unrelated_scope_and_normal_reserved_hold_are_not_blocked(self):
        row, _ = self.fail_after_response()
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            other = 'rehearsal-live:project:another-project'
            ledger.patch_budget(c, self.store.workspace_id, other, dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False), 0)
            ledger.require_bounded_exposure(c, self.store.workspace_id, other)
            ledger.patch_budget(c, 'other-workspace', self.scope, dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False), 0)
            ledger.require_bounded_exposure(c, 'other-workspace', self.scope)
            c.execute("UPDATE general_chat_turns SET body=? WHERE id=?", (json.dumps(dict(row, status='running')), row['id']))
            ledger.require_bounded_exposure(c, self.store.workspace_id, self.scope)

    def test_missing_chat_table_keeps_existing_ledger_behavior(self):
        c = sqlite3.connect(':memory:')
        self.addCleanup(c.close)
        ledger.initialize(c)
        c.commit()
        c.execute('BEGIN IMMEDIATE')
        ledger.patch_budget(c, 'workspace', 'scope', dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False), 0)
        ledger.require_bounded_exposure(c, 'workspace', 'scope')

    def test_project_live_scope_requires_matching_turn_and_reservation(self):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            scope = 'project:' + self.f.pid
            ledger.patch_budget(c, self.store.workspace_id, scope, dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False), 0)
            reservation = ledger.command(c, self.store.workspace_id, scope, 'reserve',
                                         dict(money={'amount': '0.1', 'currency': 'USD'}, budget_revision=1,
                                              expires=time.time() + 60, job='live-fixture'), 'live-fixture')['reservation']
            turn = dict(id='live-fixture', reservation=reservation, status='outcome_unknown', journal_failure='update_failed',
                        binding=dict(workspace=self.store.workspace_id, project=self.f.pid, transport=dict(mode='anthropic-live')))
            c.execute('INSERT INTO general_chat_turns VALUES (?,?,?,?)', ('live-fixture', self.f.pid, 'fixture', json.dumps(turn)))
            with self.assertRaises(ledger.BudgetExposureBlocked):
                ledger.require_bounded_exposure(c, self.store.workspace_id, scope)
            turn['reservation'] = 'other-reservation'
            c.execute('UPDATE general_chat_turns SET body=? WHERE id=?', (json.dumps(turn), 'live-fixture'))
            ledger.require_bounded_exposure(c, self.store.workspace_id, scope)


if __name__ == '__main__':
    unittest.main()
