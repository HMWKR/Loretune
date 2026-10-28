"""Consent UI uses the bound current prompt even when older history comes first."""
from pathlib import Path
import subprocess
import unittest


class GeneralChatHistoryUITest(unittest.TestCase):
    def test_history_approval_and_draft_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/general_chat_history_ui.cjs'], cwd=root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
