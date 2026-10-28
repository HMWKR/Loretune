import shutil
import subprocess
import unittest

class TimelineUiSafetyTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required')
    def test_timeline_draft_and_selection_contract(self):
        subprocess.run(['node', 'tests/timeline_ui_safety.cjs'], check=True)
