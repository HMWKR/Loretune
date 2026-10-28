from pathlib import Path
import sys,unittest,socket
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'snapshot'))
def deny(*a,**kw):raise AssertionError('audit network/listener forbidden')
with patch.object(socket.socket,'bind',deny),patch.object(socket.socket,'connect',deny):
 suite=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_studio_media','tests.test_comment_draft','tests.test_studio_state'])
 r=unittest.TextTestRunner(verbosity=2).run(suite)
 sys.exit(not r.wasSuccessful())
