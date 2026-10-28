"""Cross-flow budget checks with loopback chat and a direct fixture generation queue.

The shared rehearsal scope below is injected into the generation queue by this
test. The production generation HTTP route uses a different scope today.
"""
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

import fal_provider
import ledger
from app import server
from tests import test_chat_live_contract


class CrossFlowBudgetTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_chat_live_contract.LiveContractHTTPTest('test_exact_approved_bytes_and_estimate_is_not_confirmed')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.store = self.fixture.http.store
        self.scope = 'rehearsal-live:project:' + self.fixture.pid

    def budget(self, amount):
        with self.store.connect() as c:
            current = ledger.budget(c, self.store.workspace_id, self.scope)
            return ledger.patch_budget(c, self.store.workspace_id, self.scope, {
                'limit': {'amount': amount, 'currency': 'USD'},
                'maxConcurrentJobs': 4, 'allowAutomaticRetries': False,
            }, current['revision'])

    def generation(self, key):
        with self.store.connect() as c:
            b = ledger.budget(c, self.store.workspace_id, self.scope)
        quote = dict(fal_provider.estimate(), budget_revision=b['revision'])
        data = fal_provider.payload('abstract landscape', b'\x89PNG\r\n\x1a\nfixture')
        return self.store.generation.admit(
            self.scope, data, quote, {'shot': 'fixture', 'revision': 1, 'execution_mode': 'contract-fake'},
            key, approved=True,
        )

    def test_competing_admissions_have_only_one_winner(self):
        self.budget('0.70')
        preview = self.fixture.preview()
        gate = threading.Barrier(2)

        def admit_chat():
            gate.wait(5)
            return self.fixture.approve(preview)

        def admit_generation():
            gate.wait(5)
            try:
                return self.generation('generation-race')
            except ledger.LedgerError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            chat_future = pool.submit(admit_chat)
            generation_future = pool.submit(admit_generation)
            chat = chat_future.result(timeout=10)
            generation = generation_future.result(timeout=10)
        self.assertEqual(int(chat[0] == 200) + int(generation is not None), 1)
        submits = []

        class Adapter:
            def submit(self, data):
                submits.append(data)
                return {'request_id': 'fixture'}

        if generation:
            self.assertEqual(self.store.generation.dispatch(generation['id'], Adapter())['state'], 'accepted')
            self.assertEqual(len(submits), 1)
            self.assertEqual(self.fixture.provider.requests, [])
        else:
            self.assertTrue(self.store.general_chat_runtime.process_next())
            self.assertEqual([r[0] for r in self.fixture.provider.requests], ['/count_tokens', '/messages'])
            self.assertEqual(submits, [])
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM reservations').fetchone()[0], 1)

    def test_generation_reservation_blocks_chat_approval(self):
        self.budget('0.70')
        preview = self.fixture.preview()
        job = self.generation('generation-first')
        self.assertEqual(self.fixture.approve(preview)[0], 400)
        self.assertEqual(self.fixture.provider.requests, [])
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT job,state FROM reservations').fetchall(), [(job['id'], 'reserved')])

    def test_chat_reservation_blocks_generation_admission(self):
        self.budget('0.70')
        preview = self.fixture.preview()
        self.assertEqual(self.fixture.approve(preview)[0], 200)
        with self.assertRaises(ledger.LedgerError):
            self.generation('chat-first')
        self.assertEqual(self.fixture.provider.requests, [])
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM reservations').fetchone()[0], 1)

    def test_unknown_generation_blocks_queued_chat_and_no_retry_after_restart(self):
        job = self.generation('generation-unknown')
        preview = self.fixture.preview()
        self.assertEqual(self.fixture.approve(preview)[0], 200)
        calls = []

        class Adapter:
            def submit(self, data):
                calls.append(data)
                raise TimeoutError('fixture transport failure')

        self.assertEqual(self.store.generation.dispatch(job['id'], Adapter())['state'], 'reconciliation_required')
        self.assertTrue(self.store.general_chat_runtime.process_next())
        self.assertEqual(self.fixture.provider.requests, [])
        with self.store.connect() as c:
            states = dict(c.execute('SELECT job,state FROM reservations').fetchall())
            self.assertEqual(states[job['id']], 'uncertain')
            self.assertIn('cancelled', states.values())
        reopened = server(self.fixture.tmp.name, 0, general_chat_live=self.store.general_chat_runtime.transport)
        try:
            reopened.store.generation.recover()
            self.assertEqual(reopened.store.generation.dispatch(job['id'], Adapter())['state'], 'reconciliation_required')
            self.assertFalse(reopened.store.general_chat_runtime.process_next())
            self.assertEqual(len(calls), 1)
            self.assertEqual(self.fixture.provider.requests, [])
        finally:
            reopened.server_close()


if __name__ == '__main__':
    unittest.main()
