"""Reproduce starter/native acceptance with persistent, isolated evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
import motion_renderer
import motion_scene

OUT = Path(__file__).resolve().parent
scene = json.loads(subprocess.check_output(['node', 'tests/motion_text_controls.cjs'], text=True))
(OUT / 'starter-scene.json').write_text(json.dumps(scene, ensure_ascii=False, indent=2))
binary = motion_renderer.helper(OUT)
receipts = []

def check(name, candidate, expected, png=False):
    payload = motion_scene.frame_state(candidate, 24 if png else 0, all_layers=not png)
    (OUT / (name + '-input.json')).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    command = [str(binary), 'png' if png else 'validate', str(OUT / (name + '.png'))]
    result = subprocess.run(command, input=json.dumps(payload), capture_output=True, text=True)
    receipt = dict(name=name, invocation=command, exit_code=result.returncode,
                   expected_exit_code=expected, stdout=result.stdout, stderr=result.stderr)
    receipts.append(receipt)
    (OUT / (name + '-receipt.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
    assert result.returncode == expected, receipt
    if not expected:
        assert not json.loads(result.stdout)['text'][0]['glyph_missing']

check('two-line-default', scene, 0)
check('two-line-default-visible', scene, 0, png=True)
old = copy.deepcopy(scene)
old['layers'][0]['height'] = 160
check('two-line-old-box', old, 1)
single = copy.deepcopy(scene)
single['layers'][0]['text'] = '음원으로 시작하는'
check('one-line-default', single, 0)
check('one-line-new-visible', single, 0, png=True)
single['layers'][0]['height'] = 160
check('one-line-old-visible', single, 0, png=True)
assert (OUT / 'one-line-new-visible.png').read_bytes() == (OUT / 'one-line-old-visible.png').read_bytes()
result = dict(status='PASS', source_sha256=hashlib.sha256((ROOT / 'motion-studio.js').read_bytes()).hexdigest(),
              binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(), manifest=motion_renderer.font_manifest(),
              single_line_visible_png_identical=True, checks=receipts,
              rationale='Two 80px lines require 2*80*1.3=208px; new starter 240px leaves 32px room. Existing user scenes are not migrated.',
              boundary='This verifies actual JS handlers in a DOM stub and actual CoreText binary; browser workflow acceptance remains with root.')
(OUT / 'native-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(dict(status=result['status'], native_cases=len(receipts), single_line_visible_png_identical=True)))
