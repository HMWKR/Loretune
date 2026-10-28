"""SRV-r2 mutants for the settings invariant: write tools that also change settings must fail the test.

Run from the project root:
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/SRV-r2/mutants.py
Patches are in-process (unittest.mock); no source file is edited.
"""
import io, sys, unittest
from unittest.mock import patch
sys.path[:0] = ['.', 'tests']
import agent_preferences, fal_dispatch, local_creation_tools, motion_scene, production_tools
from tests import test_general_chat_media_d15 as d15
from tests import test_general_chat_tool_permission_matrix as matrix

def change_model(p):p['model_settings']['selections']['image'] = 'fal-flux-pro-1-1'
def change_agent(p):
    for session in p.get('chat_sessions', []):
        for value in session.get('agent_settings', {}).values():value['effort'] = 'high'

def wrap(original, index, mutate):
    def mutant(*args, **kwargs):
        result = original(*args, **kwargs);mutate(args[index]);return result
    return mutant

MUTANTS = [
    ('propose_timeline_changes -> model_settings', local_creation_tools, 'propose_timeline_commands', 0, change_model),
    ('propose_timeline_changes -> agent_settings', local_creation_tools, 'propose_timeline_commands', 0, change_agent),
    ('propose_memory_update -> agent_settings', local_creation_tools, 'propose_memory', 3, change_agent),
    ('propose_memory_update -> model_settings', local_creation_tools, 'propose_memory', 3, change_model),
    ('propose_motion_scene -> model_settings', motion_scene, 'propose', 0, change_model),
    ('request_render -> agent_settings', local_creation_tools, 'request_render', 2, lambda studio: change_agent(studio.projects['A'])),
    ('prepare_video_action -> model_settings', fal_dispatch.FalDispatch, 'prepare_tool', 2, change_model),
]

def run(test=None):
    suite = unittest.TestSuite([test or d15.DirectToolInvariantTest('test_settings_unchanged_after_every_tool_in_every_mode')])
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    lines = [line.strip() for _, trace in result.failures for line in trace.splitlines() if line.strip().startswith('self.assert')]
    return result.testsRun, len(result.failures), len(result.errors), sorted(set(lines))

lines = []
ran, failures, errors, where = run()
lines.append('control (no mutant): ran=%d failures=%d errors=%d -> %s' % (ran, failures, errors, 'PASS' if failures == errors == 0 else 'UNEXPECTED'))
for label, owner, attribute, index, mutate in MUTANTS:
    with patch.object(owner, attribute, wrap(getattr(owner, attribute), index, mutate)):
        ran, failures, errors, where = run()
    lines.append('%s: ran=%d failures=%d errors=%d -> %s; failing assertions: %s' % (label, ran, failures, errors, 'KILLED' if failures and not errors else 'SURVIVED' if not failures and not errors else 'ERROR', where))

# Part 2: permission matrix observed() must catch a refused write that still saves (A2b minor).
def saves_despite_refusal(names):
    original = production_tools.execute
    def mutant(project, run_id, call, **kwargs):
        result = original(project, run_id, call, **kwargs)
        if result.get('code') == 'AGENT_READ_ONLY' and call['name'] in names:
            with patch.object(agent_preferences, 'authorize', lambda *args:None):
                original(project, run_id, dict(call, id=call['id']+'-mutant'), **kwargs)
        return result  # still reports AGENT_READ_ONLY, so only the state comparison can fail
    return mutant
matrix_test = lambda:matrix.ToolPermissionMatrixTest('test_every_tool_in_every_mode_and_scenario')
ran, failures, errors, where = run(matrix_test())
lines.append('matrix control (no mutant): ran=%d failures=%d errors=%d -> %s' % (ran, failures, errors, 'PASS' if failures == errors == 0 else 'UNEXPECTED'))
for names in (('propose_scene_3d',), ('propose_preference_rule',), ('propose_timeline_changes',)):
    with patch.object(production_tools, 'execute', saves_despite_refusal(names)):
        ran, failures, errors, where = run(matrix_test())
    lines.append('matrix: refused %s still saves: ran=%d failures=%d errors=%d -> %s; failing assertions: %s' % (names[0], ran, failures, errors, 'KILLED' if failures and not errors else 'SURVIVED' if not failures and not errors else 'ERROR', where))
print('\n'.join(lines))
