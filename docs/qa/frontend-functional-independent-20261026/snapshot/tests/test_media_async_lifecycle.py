import subprocess,unittest
from pathlib import Path

class MediaAsyncLifecycleTest(unittest.TestCase):
 def test_controlled_media_lifecycle_regressions(self):
  root=Path(__file__).resolve().parents[1]
  result=subprocess.run(['node',str(root/'tests/media_async_lifecycle.cjs')],cwd=root,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
