"""SRV-r3 mutants for the settings invariant (successor of SRV-r2/mutants.py).

Changes from SRV-r2:
- Every settings-write mutant is active only inside the per-tool loop (after build_fixture), so a kill
  comes from the loop's own assertions; propose_motion_scene is no longer caught by a fixture HTTP step.
- Each run is repeated REPEAT times and the log records the distinct failure counts seen, so a varying
  count is visible instead of silently differing between runs.
- No bytecode is written even if started without -B (set before any project import).

Run from the project root:
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests /opt/homebrew/opt/python@3.15/bin/python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/SRV-r3/mutants.py
Patches are in-process (unittest.mock); no source file is edited.
"""
import sys
sys.dont_write_bytecode = True
import io, unittest
from unittest.mock import patch
sys.path[:0] = ['.', 'tests']
import agent_preferences, fal_dispatch, local_creation_tools, motion_scene, production_tools
from tests import test_general_chat_media_d15 as d15
from tests import test_general_chat_tool_permission_matrix as matrix

REPEAT = 3
LOOP = {'active': False}

def change_model(p):p['model_settings']['selections']['image'] = 'fal-flux-pro-1-1'
def change_agent(p):
    for session in p.get('chat_sessions', []):
        for value in session.get('agent_settings', {}).values():value['effort'] = 'high'

def wrap(original, index, mutate):
    def mutant(*args, **kwargs):
        result = original(*args, **kwargs)
        if LOOP['active']:mutate(args[index])
        return result
    return mutant

original_build = d15.DirectToolInvariantTest.build_fixture
def build_then_arm(self):
    original_build(self)
    LOOP['active'] = True  # from here on only the per-tool loop runs

MUTANTS = [
    ('propose_timeline_changes -> model_settings', local_creation_tools, 'propose_timeline_commands', 0, change_model),
    ('propose_timeline_changes -> agent_settings', local_creation_tools, 'propose_timeline_commands', 0, change_agent),
    ('propose_memory_update -> agent_settings', local_creation_tools, 'propose_memory', 3, change_agent),
    ('propose_memory_update -> model_settings', local_creation_tools, 'propose_memory', 3, change_model),
    ('propose_motion_scene -> model_settings (loop only)', motion_scene, 'propose', 0, change_model),
    ('propose_motion_scene -> agent_settings (loop only)', motion_scene, 'propose', 0, change_agent),
    ('request_render -> agent_settings', local_creation_tools, 'request_render', 2, lambda studio: change_agent(studio.projects['A'])),
    ('prepare_video_action -> model_settings', fal_dispatch.FalDispatch, 'prepare_tool', 2, change_model),
]

def run_once(test):
    LOOP['active'] = False
    with patch.object(d15.DirectToolInvariantTest, 'build_fixture', build_then_arm):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(unittest.TestSuite([test()]))
    LOOP['active'] = False
    lines = [line.strip() for _, trace in result.failures for line in trace.splitlines() if line.strip().startswith('self.assert')]
    return result.testsRun, len(result.failures), len(result.errors), sorted(set(lines))

def run(test):
    outcomes = [run_once(test) for _ in range(REPEAT)]
    failures = sorted({o[1] for o in outcomes});errors = sorted({o[2] for o in outcomes});where = sorted({l for o in outcomes for l in o[3]})
    verdict = 'KILLED' if all(o[1] and not o[2] for o in outcomes) else 'SURVIVED' if all(not o[1] and not o[2] for o in outcomes) else 'MIXED/ERROR'
    return failures, errors, where, verdict

invariant = lambda:d15.DirectToolInvariantTest('test_settings_unchanged_after_every_tool_in_every_mode')
lines = []
failures, errors, where, verdict = run(invariant)
lines.append('control (no mutant) x%d: failures=%s errors=%s -> %s' % (REPEAT, failures, errors, 'PASS' if verdict == 'SURVIVED' else 'UNEXPECTED'))
for label, owner, attribute, index, mutate in MUTANTS:
    with patch.object(owner, attribute, wrap(getattr(owner, attribute), index, mutate)):
        failures, errors, where, verdict = run(invariant)
    lines.append('%s x%d: failures=%s errors=%s -> %s; failing assertions: %s' % (label, REPEAT, failures, errors, verdict, where))

# Part 2 (unchanged from SRV-r2): the permission matrix observed() catches a refused write that still saves.
def saves_despite_refusal(names):
    original = production_tools.execute
    def mutant(project, run_id, call, **kwargs):
        result = original(project, run_id, call, **kwargs)
        if result.get('code') == 'AGENT_READ_ONLY' and call['name'] in names:
            with patch.object(agent_preferences, 'authorize', lambda *args:None):
                original(project, run_id, dict(call, id=call['id']+'-mutant'), **kwargs)
        return result
    return mutant
matrix_test = lambda:matrix.ToolPermissionMatrixTest('test_every_tool_in_every_mode_and_scenario')
failures, errors, where, verdict = run(matrix_test)
lines.append('matrix control (no mutant) x%d: failures=%s errors=%s -> %s' % (REPEAT, failures, errors, 'PASS' if verdict == 'SURVIVED' else 'UNEXPECTED'))
for names in (('propose_scene_3d',), ('propose_preference_rule',), ('propose_timeline_changes',)):
    with patch.object(production_tools, 'execute', saves_despite_refusal(names)):
        failures, errors, where, verdict = run(matrix_test)
    lines.append('matrix: refused %s still saves x%d: failures=%s errors=%s -> %s; failing assertions: %s' % (names[0], REPEAT, failures, errors, verdict, where))
print('\n'.join(lines))
