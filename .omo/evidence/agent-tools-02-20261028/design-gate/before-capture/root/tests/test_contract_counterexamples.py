"""Regression of independently observed failures; child harness blocks all sockets."""
import json,subprocess,sys,unittest
from pathlib import Path

class IndependentCounterexamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        output=subprocess.check_output([sys.executable,str(root/'docs/qa/contract-fixes-20261025/verify-fixes.py')],cwd=root,text=True,timeout=120)
        cls.results={r['id']:r for r in map(json.loads,output.splitlines())}
    def test_f01_revoked_asset_never_submits(self):
        r=self.results['F01'];self.assertEqual(r['actual_submits'],0);self.assertEqual(r['job_state'],'submission_blocked')
    def test_f02_cancel_failure_keeps_completed_result(self):
        r=self.results['F02'];self.assertEqual(r['actual_state'],'cancelled_result');self.assertIsNotNone(r['actual_result'])
    def test_f03_relation_change_is_in_dependency_impact(self):
        r=self.results['F03'];self.assertTrue(r['actual_impacts']);self.assertIn('relations',r['bound_context_keys'])
    def test_f04_fractional_cuts_keep_global_clock(self):
        r=self.results['F04'];self.assertIsNone(r['verification_error']);self.assertLessEqual(abs(r['actual_duration']-3.9),1/24)
