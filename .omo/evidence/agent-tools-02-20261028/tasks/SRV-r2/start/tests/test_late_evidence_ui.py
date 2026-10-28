"""Exercise the review module's state transitions and project isolation."""
from pathlib import Path
import subprocess
import unittest


class LateEvidenceUITest(unittest.TestCase):
    def test_ui_interactions(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/late_evidence_ui.cjs'], cwd=root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
