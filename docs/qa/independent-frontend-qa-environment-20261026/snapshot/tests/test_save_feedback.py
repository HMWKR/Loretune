import subprocess,unittest
from pathlib import Path
class SaveFeedbackTest(unittest.TestCase):
 def test_request_outcomes_recovery_and_scoped_drafts(self):
  root=Path(__file__).resolve().parents[1]
  result=subprocess.run(['node',str(root/'tests/save_feedback.mjs')],cwd=root,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn('13 checks passed',result.stdout)
