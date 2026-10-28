"""First-party Claude text-price boundaries; no live provider or credentials."""
import unittest
from decimal import Decimal
from unittest.mock import patch

import chat_models
import tests.test_chat_runtime as runtime_tests
import tests.test_chat_general_http as general_tests


class ChatPricingTest(unittest.TestCase):
    def test_haiku_threshold_applies_higher_rate_to_the_entire_request(self):
        spec = chat_models.contract('anthropic-haiku-5-5')
        for tokens, expected in [(99999, '0.0104999'), (100000, '0.0105'), (100001, '0.0525005')]:
            with self.subTest(tokens=tokens):
                self.assertEqual(chat_models.cost(spec, tokens, 1000), Decimal(expected))
        self.assertEqual(chat_models.cost(spec, 100001, 1000000), Decimal('2.5500005'))

    def test_other_models_remain_unchanged_and_invalid_counts_are_rejected(self):
        spec = chat_models.contract('xai-grok-4-7')
        self.assertEqual(chat_models.cost(spec, 100001, 1000), Decimal('0.206002'))
        for invalid in (-1, True, 1.5, '100'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                chat_models.cost(spec, invalid, 0)

    def test_extremely_large_counts_are_not_rounded_down(self):
        spec = chat_models.contract('anthropic-haiku-5-5')
        amount = 10**80 + 1
        # 0.5 per million means dividing the integer token count by 2,000,000.
        # Construct an exact string independently of Decimal's default precision.
        expected = Decimal(f'{amount // 2000000}.{(amount % 2000000) * 5:07d}')
        self.assertEqual(chat_models.cost(spec, amount, 0), expected)

    def runtime(self):
        helper = runtime_tests.ChatRuntimeTest('runTest')
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        return helper

    def test_excess_usage_is_priced_at_upper_tier_and_no_tool_runs(self):
        helper = self.runtime()
        upstream = runtime_tests.response([runtime_tests.use('plan','propose_media_plan',runtime_tests.ARGS)],'tool_use')
        upstream['usage'] = {'input_tokens': 100001, 'output_tokens': 1000}
        helper.connect(runtime_tests.Fake([upstream]))
        helper.enqueue()
        self.assertTrue(helper.runtime.process_next())
        turn = helper.turn()
        self.assertEqual(turn['status'], 'response_validation_failed')
        self.assertEqual(turn['steps'][0]['failure']['category'], 'usage_limit_exceeded')
        self.assertEqual(turn['steps'][0]['usage_cost_usd'], '0.0525005')
        self.assertFalse(turn['billing_confirmed'])
        self.assertEqual(helper.rows()[0][2], 52501)
        self.assertFalse(helper.st.state()['projects']['A'].get('guided_plans'))
        self.assertEqual(len(helper.adapter.messages), 1)
        self.assertFalse(helper.runtime.process_next())

    def test_old_price_approval_is_rejected_before_provider_call(self):
        helper = self.runtime()
        helper.connect(runtime_tests.Fake())
        helper.runtime.approval['price_revision'] = 'haiku-5-5-20261025'
        with self.assertRaisesRegex(ValueError, 'limits unavailable'):
            helper.enqueue()
        self.assertEqual(helper.adapter.counts, [])
        self.assertEqual(helper.adapter.messages, [])
        self.assertFalse(helper.journal.exists())

    def test_unconsumed_manifest_from_old_price_revision_is_rejected(self):
        helper = general_tests.GeneralChatHTTPTest('runTest')
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        with patch.dict(chat_models.MODELS['anthropic-haiku-5-5'], price_revision='haiku-5-5-20261025'):
            old_preview = helper.preview()
        status, _ = helper.approve(old_preview)
        self.assertEqual(status, 400)
        self.assertEqual(helper.http.store.general_chat_runtime.transport.counted, [])
        self.assertEqual(helper.http.store.general_chat_runtime.transport.messages, [])
        with helper.http.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reservations').fetchone()[0], 0)

    def test_general_chat_excess_usage_records_tier_in_disputed_reservation(self):
        helper = general_tests.GeneralChatHTTPTest('runTest')
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        upstream = runtime_tests.response([runtime_tests.use('plan','propose_media_plan',runtime_tests.ARGS)],'tool_use')
        upstream['usage'] = {'input_tokens': 100001, 'output_tokens': 1000}
        transport = helper.http.store.general_chat_runtime.transport
        transport.responses = [upstream]
        first = helper.preview()
        self.assertEqual(helper.approve(first)[0], 200)
        self.assertTrue(helper.http.store.general_chat_runtime.process_next())
        project = helper.state()['projects']['A']
        turn = project['general_chat_turns'][-1]
        self.assertEqual(turn['status'], 'outcome_unknown')
        self.assertEqual(turn['usage_cost_usd'], '0.0525005')
        self.assertFalse(turn['billing_confirmed'])
        self.assertFalse(project.get('guided_plans'))
        with helper.http.store.connect() as db:
            self.assertEqual(db.execute('SELECT state,actual FROM reservations').fetchone(), ('disputed', 52501))
        self.assertEqual(len(transport.messages), 1)
        self.assertFalse(helper.http.store.general_chat_runtime.process_next())


if __name__ == '__main__':
    unittest.main()
