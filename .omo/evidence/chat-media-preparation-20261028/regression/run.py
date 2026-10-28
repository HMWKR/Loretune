"""One scoped current-source regression; never edits project/test sources."""
from pathlib import Path
import collections
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path('/Users/leesungmin/Desktop/Loretune')
OUT = ROOT / '.omo/evidence/chat-media-preparation-20261028/regression'
PRIOR = ROOT / 'docs/qa/codex-workflow-review-20261027/workflow-simplification-20261028/regression/preflight.json'
FREEZE = OUT / 'source-delta-vs-S850.json'
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / 'preflight.json').exists() or (OUT / 'receipt.json').exists():
    raise SystemExit('Existing run evidence: refusing to restart or overwrite')

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(name, value):
    target = OUT / name
    temporary = target.with_suffix(target.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)

def sources():
    paths = {p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.py', '.js', '.html', '.css'}}
    paths.update(p for p in (ROOT / 'tests').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'})
    paths.update(p for p in (ROOT / 'native').glob('*.swift') if p.is_file())
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}

def protected():
    roots = [ROOT / '.omo/evidence/scene-vertex-colors-20261028/native', ROOT / 'docs/qa/tail-quota-fixes-20261025', ROOT / '.omo/evidence/paired-assets-platform-20261028/regression/native', ROOT / '.omo/evidence/asset-color-controlled-20261028/output', ROOT / 'docs/qa/codex-workflow-review-20261027/music-recovery-20261028', ROOT / 'docs/qa/codex-workflow-review-20261027/workflow-simplification-20261028', ROOT / '.omo/evidence/conversation-workflow-20261028']
    result = {str(p.relative_to(ROOT)): sha(p) for base in roots for p in sorted(base.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    demo = ROOT / '.omo/evidence/first-demo-20261028/main-demo-case-r3'
    paths = [demo / n for n in ['first-demo-native-workflow.mp4', 'first-demo-synthetic-chat.mp4', 'first-demo-layout-refinement.mp4', 'layout-refined-output.mp4']]
    proposal_path = ROOT / '.omo/evidence/chat-document-audit-current-20261028/registration-review-current.json'
    proposal = json.loads(proposal_path.read_text())
    paths.extend(ROOT / n for n in sorted({x['source'] for x in proposal['proposed_snapshots']}))
    paths.extend([proposal_path, ROOT / '.document-gate.json'])
    result.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    return result

def group_members(pgid):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,comm='], text=True, capture_output=True, check=True)
    members = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 3)
        if len(fields) == 4 and int(fields[2]) == pgid:
            members.append({'pid': int(fields[0]), 'ppid': int(fields[1]), 'pgid': int(fields[2]), 'command': fields[3]})
    return members

previous = json.loads(PRIOR.read_text())
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR')}
env.update(previous['native']['environment'])
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['SCENE_VERTEX_EVIDENCE'] = str(OUT / 'native')
python = previous['python']['path']
assert sha(python) == previous['python']['sha256'], 'Python bytes changed'
python_version = subprocess.run([python, '-c', 'import sys;print(sys.version)'], env=env, capture_output=True, text=True, check=True).stdout.strip()
assert python_version == previous['python']['version']
tools = {}
for name, args in [('node', ['--version']), ('ffmpeg', ['-version']), ('docker', ['--version']), ('swiftc', ['--version'])]:
    path = shutil.which(name, path=env['PATH'])
    assert path and sha(path) == previous['toolchain'][name]['sha256'], (name, 'tool changed')
    result = subprocess.run([path, *args], env=env, capture_output=True, text=True, check=True)
    tools[name] = {'path': path, 'resolved_path': str(Path(path).resolve()), 'sha256': sha(path), 'version_lines': (result.stdout + result.stderr).strip().splitlines()[:3], 'matches_S819': True}
font = previous['font']['path']
assert sha(font) == previous['font']['sha256'], 'Font bytes changed'
blender_root = Path(env['LORETUNE_3D_BLENDER'])
assert sha(blender_root / 'blender') == env['LORETUNE_3D_BLENDER_SHA256'], 'Blender binary changed'
sys.path.insert(0, str(ROOT))
from scene_project import tree_manifest
actual_tree = tree_manifest(blender_root)
assert actual_tree == env['LORETUNE_3D_TREE_SHA256'], 'Pinned Blender installation tree changed'
docker = tools['docker']['path']
image_result = subprocess.run([docker, '--host', 'unix://' + env['LORETUNE_3D_DOCKER_SOCKET'], 'image', 'inspect', env['LORETUNE_3D_IMAGE']], env=env, capture_output=True, text=True, check=True)
image = json.loads(image_result.stdout)[0]
image = {k: image.get(k) for k in ('Id', 'Os', 'Architecture', 'RepoDigests')}
assert image == previous['native']['actual_image'], 'Pinned local image metadata changed'
before = sources()
declared = json.loads(FREEZE.read_text())
assert declared and all(before.get(p) == h for p, h in declared.items()), 'Declared agent-workspace source freeze changed'
complete = json.loads((OUT / 'source-complete-freeze.json').read_text())
assert before == complete, 'Complete current source inventory changed'
old = json.loads((ROOT / '.omo/evidence/conversation-workflow-20261028/regression/receipt.json').read_text())['source_after']
added = sorted(set(before) - set(old))
removed = sorted(set(old) - set(before))
changed = sorted(p for p in old if p in before and old[p] != before[p])
assert set(added) | set(changed) == set(declared), (added, changed)
assert not removed, removed
assert len(old) == 217 and len(before) >= 221, 'Baseline/current complete inventory size unexpected'
protected_before = protected()
collection_script = '''
import collections,json,pathlib,sys,unittest
suite=unittest.defaultTestLoader.discover('tests')
def leaves(value):
    for item in value:
        if isinstance(item,unittest.TestSuite):yield from leaves(item)
        else:yield item
identifiers=[item.id() for item in leaves(suite)]
counts=collections.Counter(identifiers)
value={'tests_collected':len(identifiers),'unique_ids':len(counts),'duplicates':{k:v for k,v in counts.items() if v>1},'failed_imports':[x for x in identifiers if '_FailedTest.' in x],'test_ids':identifiers}
pathlib.Path(sys.argv[1]).write_text(json.dumps(value,indent=2)+'\\n')
sys.exit(0 if len(identifiers)>=874 and not value['duplicates'] and not value['failed_imports'] else 1)
'''
collection = subprocess.run([python, '-c', collection_script, str(OUT / 'collection.json')], cwd=ROOT, env=env, capture_output=True)
(OUT / 'collection.stdout.log').write_bytes(collection.stdout)
(OUT / 'collection.stderr.log').write_bytes(collection.stderr)
assert collection.returncode == 0, 'Collection/import/duplicate failure before test execution; inspect retained collection files'
command = [python, '-m', 'unittest', 'discover', '-s', 'tests', '-q']
preflight = {'task_id': 'chat-media-preparation-full-regression-20261028', 'attempt': 1, 'verified_at': stamp(), 'cwd': str(ROOT), 'command': command, 'prior_S819_preflight': str(PRIOR.relative_to(ROOT)), 'prior_S819_preflight_sha256': sha(PRIOR), 'python': {'path': python, 'version': python_version, 'sha256': sha(python), 'matches_S819': True}, 'toolchain': tools, 'font': {'path': font, 'sha256': sha(font), 'matches_S819': True}, 'native': {'environment': previous['native']['environment'], 'actual_binary_sha256': sha(blender_root / 'blender'), 'actual_tree_sha256': actual_tree, 'actual_image': image, 'matches_S819': True}, 'source_freeze_evidence': str(FREEZE.relative_to(ROOT)), 'source_freeze_sha256': sha(FREEZE), 'declared_freeze_matches': True, 'source_scope': previous['source_scope'], 'source_count': len(before), 'source_before': before, 'changed_vs_S850': changed, 'added_vs_S850': added, 'removed_vs_S850': removed, 'environment': env, 'environment_policy': 'Explicit PATH/HOME/LANG/LC_*/TMPDIR + pinned native vars + PYTHONDONTWRITEBYTECODE + own SCENE_VERTEX_EVIDENCE; no .env, provider key or live activation environment inherited.', 'protected_evidence_before': protected_before, 'runtime': 'root driver; inherited session model/reasoning; provider identity not independently observed'}
write('preflight.json', preflight)
receipt = {'schema': 'loretune-regression-receipt/1', 'task_id': preflight['task_id'], 'attempt': 1, 'lifecycle': 'RUNNING', 'status': 'running', 'command': command, 'cwd': str(ROOT), 'started_at': stamp(), 'preflight_path': str((OUT / 'preflight.json').relative_to(ROOT)), 'preflight_sha256': sha(OUT / 'preflight.json'), 'source_count': len(before), 'source_before': before, 'test_execution_count': 1, 'reruns': 0, 'actual_provider_calls_authorized': 0, 'test_data': 'existing isolated test temporary stores; separate SCENE_VERTEX_EVIDENCE output; root app/Ego surfaces not accessed', 'native_evidence_directory': env['SCENE_VERTEX_EVIDENCE']}
start = time.monotonic()
with (OUT / 'full-regression.log').open('xb') as log:
    process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    receipt['test_pid'] = process.pid
    receipt['test_pgid'] = process.pid
    receipt['runner_pid'] = os.getpid()
    write('receipt.json', receipt)
    print(json.dumps({'event': 'test-started', 'pid': process.pid, 'pgid': process.pid, 'source_count': len(before), 'time': stamp()}), flush=True)
    observed = {}
    tick = 0
    while process.poll() is None:
        if tick % 10 == 0:
            members = group_members(process.pid)
            for member in members:
                observed[member['pid']] = member
            write('live-status.json', {'checked_at': stamp(), 'test_pid': process.pid, 'test_alive': process.poll() is None, 'elapsed_seconds': round(time.monotonic() - start, 3), 'log_bytes': (OUT / 'full-regression.log').stat().st_size, 'own_process_group': members})
        tick += 1
        time.sleep(1)
    exit_code = process.wait()
after = sources()
text = (OUT / 'full-regression.log').read_text(errors='replace')
summary = re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$', text, re.M)
skip_match = re.search(r'^OK(?: \(skipped=(\d+)\))?$', text, re.M)
warning_lines = [line for line in text.splitlines() if re.search(r'\b(?:[A-Za-z]+Warning|WARNING)\b', line)]
final_members = group_members(process.pid)
protected_after = protected()
changed_sources = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
changed_protected = sorted(p for p in set(protected_before) | set(protected_after) if protected_before.get(p) != protected_after.get(p))
receipt.update(lifecycle='REPORTED', status='passed' if exit_code == 0 and not changed_sources and not changed_protected and not final_members else 'failed-or-review-required', finished_at=stamp(), exit_code=exit_code, elapsed_seconds=round(time.monotonic() - start, 3), tests_run=int(summary[-1][0]) if summary else None, unittest_seconds=float(summary[-1][1]) if summary else None, skip_count=int(skip_match.group(1) or 0) if skip_match else None, warning_line_count=len(warning_lines), warning_lines=warning_lines, source_after=after, source_before_after_equal=before == after, changed_sources=changed_sources, log_sha256=sha(OUT / 'full-regression.log'), log_bytes=(OUT / 'full-regression.log').stat().st_size, protected_evidence_after=protected_after, protected_evidence_unchanged=protected_before == protected_after, changed_protected_evidence=changed_protected, own_process_group_remaining=final_members, process_cleanup_scope='Own test process group only; no global container/user-process cleanup claimed', observed_own_processes=sorted(observed.values(), key=lambda x: x['pid']))
write('receipt.json', receipt)
write('live-status.json', {'checked_at': stamp(), 'test_pid': process.pid, 'test_alive': False, 'exit_code': exit_code, 'elapsed_seconds': receipt['elapsed_seconds'], 'log_bytes': receipt['log_bytes'], 'own_process_group': final_members})
print(json.dumps({'event': 'test-finished', 'pid': process.pid, 'exit_code': exit_code, 'status': receipt['status'], 'tests_run': receipt['tests_run'], 'unittest_seconds': receipt['unittest_seconds'], 'skip_count': receipt['skip_count'], 'warning_line_count': receipt['warning_line_count'], 'source_count': len(before), 'changed_sources': changed_sources, 'protected_evidence_unchanged': receipt['protected_evidence_unchanged'], 'own_process_group_remaining': final_members}), flush=True)
sys.exit(0 if receipt['status'] == 'passed' else 1)
