import subprocess
import unittest
from pathlib import Path


class ProposalDraftTest(unittest.TestCase):
    def test_real_forms_preserve_new_intent_and_context(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', 'tests/frontend_proposal_drafts.cjs'], cwd=root,
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
