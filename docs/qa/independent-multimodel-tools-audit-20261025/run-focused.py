import socket,sys,unittest
from unittest.mock import patch
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent/'snapshot'))
def denied(*a,**kw):raise AssertionError("AUDIT: network/listener prohibited")
names=['tests.test_multimodel_chat','tests.test_chat_protocols','tests.test_fal_multimodel','tests.test_local_creation_tools','tests.test_chat_runtime']
with patch.object(socket.socket,'connect',denied),patch.object(socket.socket,'bind',denied),patch('socket.create_connection',denied):
 suite=unittest.defaultTestLoader.loadTestsFromNames(names)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 sys.exit(not result.wasSuccessful())
