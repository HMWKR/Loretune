from pathlib import Path
import subprocess
import unittest


class ActiveRequestPresentationTest(unittest.TestCase):
    def test_active_saving_and_unknown_recovery_remain_distinct(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/active_request_presentation.cjs'],
                                cwd=root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
