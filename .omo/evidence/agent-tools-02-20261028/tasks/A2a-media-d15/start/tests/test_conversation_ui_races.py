"""Exercise real conversation-switch code against delayed/error responses."""
import subprocess
import unittest
from pathlib import Path

class ConversationUiRaceTest(unittest.TestCase):
    def test_selection_is_not_replaced_by_stale_or_failed_responses(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/conversation_ui_races.cjs'], cwd=root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
