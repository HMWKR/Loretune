import json
import unittest
from pathlib import Path
from cost_model import calculate


class CostModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path(__file__).with_name('cost_model.json').read_text(encoding='utf-8'))

    def test_hand_calculated_180_second_hybrid(self):
        result = calculate(self.config, 180)
        self.assertEqual(result['generated_shot_count'], 18)
        self.assertEqual(result['billed_video_seconds'], 180)
        self.assertEqual(result['video_generation_usd'], 9)
        self.assertEqual(result['variable_external_cost_usd'], 13.88)
        self.assertEqual(result['customer_cash_excluding_tax_krw'], 87511.6)

    def test_short_shot_rounds_up_instead_of_undercounting_cost(self):
        result = calculate(self.config, 11, mode='gen', candidates=1)
        self.assertEqual(result['billed_video_seconds'], 15)

    def test_provided_assets_do_not_incur_video_or_keyframe_generation(self):
        result = calculate(self.config, 180, mode='asset')
        self.assertEqual(result['billed_video_seconds'], 0)
        self.assertEqual(result['keyframe_image_count'], 0)
        self.assertGreater(result['variable_external_cost_krw'], 0)

    def test_monthly_output_allocation_does_not_hide_full_subscription(self):
        one = calculate(self.config, 60, monthly_outputs=1)
        four = calculate(self.config, 60, monthly_outputs=4)
        self.assertEqual(one['allocated_subscription_krw'], 249000)
        self.assertEqual(four['allocated_subscription_krw'] * 4, 249000)
        self.assertEqual(one['usage_charge_hypothesis_krw'], four['usage_charge_hypothesis_krw'])

    def test_invalid_counts_and_approval_cap_are_rejected(self):
        for kwargs in [{'seconds': 0}, {'monthly_outputs': 0}, {'monthly_outputs': 1.5}, {'candidates': 0}, {'candidates': 4}, {'support_minutes': -1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                calculate(self.config, **kwargs)

    def test_customer_work_is_separate_from_platform_cash(self):
        first = calculate(self.config, 60, first_project=True)
        repeat = calculate(self.config, 60)
        self.assertEqual(first['customer_cash_excluding_tax_krw'], repeat['customer_cash_excluding_tax_krw'])
        self.assertEqual(first['customer_labor_cost_assumption_krw'] - repeat['customer_labor_cost_assumption_krw'], 10000)

    def test_results_cannot_be_mislabeled_as_measured(self):
        result = calculate(self.config)
        self.assertEqual(result['evidence_state'], 'modeled_not_measured')
        self.assertFalse(result['quality_equivalence_verified'])
        self.assertFalse(result['product_support_verified'])

    def test_support_overrun_reduces_contribution_without_hiding_cost(self):
        ordinary = calculate(self.config, support_minutes=10)
        overrun = calculate(self.config, support_minutes=120)
        self.assertEqual(overrun['platform_support_cost_krw'], 60000)
        self.assertLess(overrun['contribution_margin_pct'], ordinary['contribution_margin_pct'])

    def test_calculation_identity_changes_with_financial_inputs(self):
        base = calculate(self.config, 180)
        self.assertEqual(base['calculation_id'], calculate(self.config, 180)['calculation_id'])
        for kwargs in [{'candidates': 3}, {'monthly_outputs': 1}, {'model': 'gen4.5'}, {'support_minutes': 120}]:
            with self.subTest(kwargs=kwargs):
                changed = calculate(self.config, 180, **kwargs)
                self.assertEqual(base['scenario_id'], changed['scenario_id'])
                self.assertNotEqual(base['calculation_id'], changed['calculation_id'])

    def test_nonfinite_financial_inputs_are_rejected(self):
        for kwargs in [{'seconds': float('inf')}, {'support_minutes': float('nan')}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                calculate(self.config, **kwargs)


if __name__ == '__main__':
    unittest.main()
