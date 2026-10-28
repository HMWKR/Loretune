"""UI-r2: E1/B2 rework contracts (375 header select, visibility poll, playhead writes, verb-only labels,
toggle state, one money format, notice pattern, decision-point facts, work-status price detail, spacing tokens).

Runs tests/ui_r2_contracts.cjs against the shipped files. No browser, server, model or provider call.
"""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UIR2ContractsTest(unittest.TestCase):
    def test_ui_r2_contracts(self):
        result = subprocess.run(['node', 'tests/ui_r2_contracts.cjs'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(result.stdout.count('PASS '), 11, result.stdout)


if __name__ == '__main__':
    unittest.main()
