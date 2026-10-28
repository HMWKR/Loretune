"""Same refused-write mutant against the pre-SRV-r2 matrix test (start/ copy): shows the old observed() missed it."""
import importlib.util, io, sys, unittest
from unittest.mock import patch
sys.path[:0] = ['.', 'tests']
import agent_preferences, production_tools
spec = importlib.util.spec_from_file_location('old_matrix', '.omo/evidence/agent-tools-02-20261028/tasks/SRV-r2/start/tests/test_general_chat_tool_permission_matrix.py')
old = importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
original = production_tools.execute
def mutant(project, run_id, call, **kwargs):
    result = original(project, run_id, call, **kwargs)
    if result.get('code') == 'AGENT_READ_ONLY' and call['name'] == 'propose_scene_3d':
        with patch.object(agent_preferences, 'authorize', lambda *args:None):original(project, run_id, dict(call, id=call['id']+'-mutant'), **kwargs)
    return result
with patch.object(production_tools, 'execute', mutant):
    r = unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite([old.ToolPermissionMatrixTest('test_every_tool_in_every_mode_and_scenario')]))
print('old matrix observed(): refused propose_scene_3d still saves: ran=%d failures=%d errors=%d -> %s' % (r.testsRun, len(r.failures), len(r.errors), 'SURVIVED' if r.wasSuccessful() else 'KILLED'))
