"""Check general chat controls after unrelated request and recovery paths."""
from pathlib import Path
import subprocess
import unittest


class GeneralChatControlsTest(unittest.TestCase):
    def test_controls_follow_current_state_after_request_completion(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/general_chat_controls.cjs'], cwd=root,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
