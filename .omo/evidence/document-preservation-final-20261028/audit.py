"""Read project preservation baselines; write only this task's evidence."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
PRIOR = ROOT / 'docs/qa/codex-workflow-review-20261027/document-preservation-20261028/current-recheck-20261028'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(relative):
    p = ROOT / relative
    if p.is_absolute() and not p.is_relative_to(ROOT):
        raise ValueError('outside project')
    if '..' in Path(relative).parts or any(q.is_symlink() for q in [p, *p.parents] if q != ROOT.parent):
        raise ValueError('unsafe path')
    return p.read_bytes()


def record(path, expected=None):
    try:
        result = {'path': str(path), 'sha256': digest(read(path)), 'exists': True}
    except (OSError, ValueError) as e:
        return {'path': str(path), 'exists': False, 'error_type': type(e).__name__}
    if expected is not None:
        result['expected'] = expected
        result['match'] = result['sha256'].startswith(expected)
    return result


def load(path):
    return json.loads(read(path))


policy = load('.document-gate.json')
inventory_path = 'docs/qa/DOCUMENT-INVENTORY-20261027.md'
inventory = []
for line in read(inventory_path).decode().splitlines():
    path = re.match(r'^\|\[([^\]]+)\]\(<[^>]+>\)\|', line)
    sha = re.search(r'; `([0-9a-f]{12})`\|$', line)
    if path and sha:
        inventory.append(record(path[1], sha[1]))
if len(inventory) != 2156 or len({r['path'] for r in inventory}) != 2156:
    raise RuntimeError('inventory parser count mismatch')

classified = [record(item['path'], item.get('baseline_sha256')) for item in policy['documents']]
immutable = [r for r in classified if 'expected' in r or not r['exists']]
registries = []
governance_before = [record('.document-gate.json')]
for registry in policy['registries']:
    raw = load(registry['path'])
    documents = [record(str(Path(registry['base']) / item['file']), item['sha256'])
                 for item in raw['objects'] if item['kind'] == 'Document']
    registries.append({'name': registry['name'], 'registry': record(registry['path']),
                       'revision': raw['registry_revision'], 'documents': documents})
    governance_before.append(record(registry['path']))

before_entries = load(str((PRIOR / 'adoption-before-recheck.json').relative_to(ROOT)))['entries']
adoption = [record(r['preserved_before'], r['expected_sha256']) for r in before_entries]
imports = [record(r['actual_path'], r['expected_sha256'])
           for r in load(str((PRIOR / 'imports-recheck.json').relative_to(ROOT)))['entries']]
contexts = [record(r['path'], r['current_sha256']) for r in
            load(str((PRIOR / 'context-preservation-recheck.json').relative_to(ROOT)))['receipts']]
historical = [record(r['path'], r['current_sha256']) for r in
              load(str((PRIOR / 'audit.json').relative_to(ROOT)))['historical_observations']]

latest_before_path = 'docs/qa/codex-workflow-review-20261027/paired-assets-20261028/document-before.json'
latest = []
for path, before in load(latest_before_path).items():
    old = before['text']
    if digest(old.encode()) != before['sha256']:
        raise RuntimeError('before text digest mismatch')
    current = read(path).decode()
    old_lines = old.splitlines(keepends=True)
    current_lines = current.splitlines(keepends=True)
    opcodes = difflib.SequenceMatcher(None, old_lines, current_lines, autojunk=False).get_opcodes()
    reconstructed = ''.join(''.join(current_lines[c:d]) for tag, _, _, c, d in opcodes if tag == 'equal')
    latest.append({**record(path), 'before_sha256': before['sha256'],
                   'before_body_exact_substring': old in current,
                   'before_bytes_preserved_in_order': reconstructed == old,
                   'reconstructed_before_sha256': digest(reconstructed.encode()),
                   'deleted_lines': sum(j-i for tag, i, j, _, _ in opcodes if tag in ('delete', 'replace')),
                   'inserted_lines': sum(j-i for tag, _, _, i, j in opcodes if tag in ('insert', 'replace'))})

gate_command = [sys.executable, '/Users/leesungmin/.agents/skills/document-completion-gate/check.py', '--root', str(ROOT)]
gate = subprocess.run(gate_command, capture_output=True, check=False)
(OUT / 'document-gate.json').write_bytes(gate.stdout)
(OUT / 'document-gate.stderr.txt').write_bytes(gate.stderr)
gate_json = json.loads(gate.stdout)

proposal_path = 'docs/qa/codex-workflow-review-20261027/paired-assets-20261028/registration-plan.json'
proposal = load(proposal_path)
proposal_sources = [record(r['source'], r['source_sha256']) for r in proposal['proposed_snapshots']]
proposal_destinations = [{'path': r['proposed_immutable_file'], 'exists': (ROOT / r['proposed_immutable_file']).exists()}
                         for r in proposal['proposed_snapshots']]
governance_after = [record(r['path']) for r in governance_before]
summary = {
    'inventory_paths': len(inventory), 'inventory_missing': sum(not r['exists'] for r in inventory),
    'inventory_same_sha12': sum(r.get('match', False) for r in inventory),
    'inventory_changed': [r for r in inventory if r['exists'] and not r.get('match')],
    'classified': len(classified), 'classified_missing': sum(not r['exists'] for r in classified),
    'immutable': len(immutable), 'immutable_mismatches': [r for r in immutable if not r.get('match')],
    'original_immutable': sum(d['classification'] == 'original' and 'baseline_sha256' in d for d in policy['documents']),
    'registered_snapshots': sum(len(r['documents']) for r in registries),
    'registered_mismatches': [d for r in registries for d in r['documents'] if not d.get('match')],
    'adoption_before_count': len(adoption), 'adoption_before_mismatches': [r for r in adoption if not r.get('match')],
    'imports_count': len(imports), 'imports_mismatches': [r for r in imports if not r.get('match')],
    'contexts_count': len(contexts), 'contexts_changed': [r for r in contexts if not r.get('match')],
    'historical_observations_changed': [r for r in historical if not r.get('match')],
    'latest_documents': len(latest), 'latest_deleted_lines': sum(r['deleted_lines'] for r in latest),
    'latest_inserted_lines': sum(r['inserted_lines'] for r in latest),
    'latest_before_bytes_preserved_in_order': all(r['before_bytes_preserved_in_order'] for r in latest),
    'latest_diff_note': 'All latest supplements are inserted after the title. A contiguous full-text substring is therefore false; reconstruction after removing only inserted lines verifies original bytes and order.',
    'governance_unchanged_during_check': governance_before == governance_after,
    'proposal_source_mismatches': [r for r in proposal_sources if not r.get('match')],
    'proposal_destinations_already_exist': [r for r in proposal_destinations if r['exists']],
    'gate': {'exit_code': gate.returncode, 'status': gate_json.get('status'),
             'evidence_sha256': gate_json.get('evidence_sha256'),
             'findings': dict(Counter(r['code'] for r in gate_json.get('findings', []))),
             'warning_count': len(gate_json.get('warnings', []))},
}
result = {'schema': 'document-preservation-final-recheck/1', 'checked_at': datetime.now(timezone.utc).isoformat(),
          'project_root': str(ROOT), 'summary': summary, 'inventory': inventory, 'classified': classified,
          'registries': registries, 'adoption_before': adoption, 'imports': imports, 'context_receipts': contexts,
          'historical_observations': historical, 'latest_text_diff': latest,
          'governance_before': governance_before, 'governance_after': governance_after,
          'proposal': {'receipt': record(proposal_path), 'sources': proposal_sources, 'destinations': proposal_destinations},
          'gate_command': gate_command,
          'limitations': ['T0 inventory SHA12 is not complete historical byte proof.',
                         'No Git history; unknown preT0 deletions cannot be excluded.',
                         'Two known historical QA JSON T0 byte contents remain unrecovered.',
                         'No private/data/secrets/external backup/Trash inspection.',
                         'No document deletion/restoration/registration/promotion/context regeneration.',
                         'No product source change or product tests; preservation checks only.']}
(OUT / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
