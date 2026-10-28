import re,subprocess,tempfile,unittest
from pathlib import Path

class StudioStateTest(unittest.TestCase):
 def run_ui(self,name,count):
  root=Path(__file__).resolve().parents[1]
  source=(root/'index.html').read_text()
  start=source.index('/* Scoped review drafts.')
  end=source.index("let commentDraftScope='';",start)
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);(p/'review-state.js').write_text(source[start:end])
   (p/name).write_text((root/'tests'/name).read_text())
   result=subprocess.run(['node',str(p/name)],capture_output=True,text=True,check=True)
   self.assertIn(str(count),result.stdout)
 def test_take_review_scope_delayed_save_and_new_revision(self):self.run_ui('test-review-state.mjs',9)
 def test_comparison_defaults_never_duplicate_take(self):self.run_ui('test-comparison.mjs',5)
