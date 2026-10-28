import subprocess,unittest
from pathlib import Path
class FrontendAsyncTest(unittest.TestCase):
 def test_poll_media_storage_regressions(self):
  root=Path(__file__).resolve().parents[1]
  result=subprocess.run(['node','tests/frontend_async_regressions.cjs'],cwd=root,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
