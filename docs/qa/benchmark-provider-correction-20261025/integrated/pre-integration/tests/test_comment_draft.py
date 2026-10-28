import json,subprocess,unittest
from pathlib import Path
class CommentDraftRaceTest(unittest.TestCase):
 def test_real_handlers_preserve_pending_edits_and_scope(self):
  script=Path(__file__).resolve().parents[1]/'docs/qa/f07-comment-draft-20261025/ui_controls.js'
  result=subprocess.run(['node',str(script)],capture_output=True,text=True,check=True)
  rows=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
  self.assertEqual(len(rows),16)
  self.assertEqual([r['case'] for r in rows if r['status']!='pass'],[])
