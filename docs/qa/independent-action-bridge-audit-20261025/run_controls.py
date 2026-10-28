"""Snapshot-only regression controls with no socket access or credential reads."""
import sys,socket,tempfile,unittest,os
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'snapshot'));sys.path.insert(1,str(root/'snapshot'/'tests'));tempfile.tempdir=str(root)
def deny(*a,**k):raise AssertionError('network disabled for audit')
socket.socket.connect=deny;socket.create_connection=deny;socket.socket.bind=deny
names=['test_ontology','test_project_ontology','test_anthropic_ontology','test_anthropic_transport','test_generation_queue','test_ledger','test_fal_provider','test_model_selection','test_media_roundtrip','test_preferences','test_settings','test_workflow','test_frame_timing','test_submission_authority','test_action_execution','test_action_tool_bridge','test_chat_protocols','test_image_adapter']
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName('tests.'+n) for n in names)
def flatten(s):
 for t in s:
  if isinstance(t,unittest.TestSuite):yield from flatten(t)
  else:yield t
suite=unittest.TestSuite(t for t in flatten(suite) if 'test_http_stale_ontology' not in t.id())
with (root/'controls.log').open('w') as out:
 result=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
print(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)))
sys.exit(not result.wasSuccessful())
