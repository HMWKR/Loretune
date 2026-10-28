import subprocess
import unittest
from pathlib import Path


class StudioNoticeTest(unittest.TestCase):
    def test_disclosure_diagnostics_and_request_focus(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', str(root / 'tests/studio_notice.cjs')],
            cwd=root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('request focus checks passed', result.stdout)
