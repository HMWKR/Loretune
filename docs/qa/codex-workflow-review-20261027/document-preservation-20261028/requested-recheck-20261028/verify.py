"""Verify document preservation; write only this task's new evidence folder."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def data(path):
    rel = Path(path)
    candidate = ROOT / rel
    if rel.is_absolute() or '..' in rel.parts or not candidate.resolve().is_relative_to(ROOT):
        raise ValueError('outside project')
    if any(p.is_symlink() for p in [candidate, *candidate.parents] if p != ROOT.parent):
        raise ValueError('symlink')
    return candidate.read_bytes()


def load(path):
    return json.loads(data(path))


def sha(path):
    return hashlib.sha256(data(path)).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


freeze_path = '.omo/evidence/document-preservation-live-20261028/post-mr1/document-hash-freeze.json'
baseline = load(freeze_path)['after']
frozen = [{'path': p, 'expected_sha256': h, 'current_sha256': sha(p)} for p, h in baseline.items()]
assert len(frozen) == 675 and all(x['expected_sha256'] == x['current_sha256'] for x in frozen)
policy = load('.document-gate.json')
registry_bases = {r['name']: r['base'] for r in policy['registries']}
contexts = []
for item in policy['contexts']:
    receipt = load(item['receipt'])
    payload_path = str(Path(registry_bases[item['registry']]) / receipt['context_file'])
    contexts.append({'receipt': item['receipt'], 'usage': item['usage'], 'payload': payload_path,
                     'receipt_matches_prior_freeze': sha(item['receipt']) == baseline[item['receipt']],
                     'payload_matches_receipt': sha(payload_path) == receipt['context_sha256']})
assert len(contexts) == 58 and all(x['receipt_matches_prior_freeze'] and x['payload_matches_receipt'] for x in contexts)

diffs = []
for label, path in [
    ('WF-before', 'docs/qa/codex-workflow-review-20261027/workflow-simplification-20261028/document-before-final.json'),
    ('MR1-before', 'docs/qa/codex-workflow-review-20261027/music-recovery-20261028/document-before.json'),
]:
    for relative, before in load(path).items():
        old = before['text']
        assert hashlib.sha256(old.encode()).hexdigest() == before['sha256']
        old_lines = old.splitlines(keepends=True)
        new_lines = data(relative).decode().splitlines(keepends=True)
        ops = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes()
        reconstructed = ''.join(''.join(new_lines[c:d]) for tag, _, _, c, d in ops if tag == 'equal')
        deleted = sum(b-a for tag, a, b, _, _ in ops if tag in ('delete', 'replace'))
        assert deleted == 0 and reconstructed == old
        diffs.append({'baseline': label, 'path': relative, 'before_sha256': before['sha256'],
                      'current_sha256': sha(relative), 'deleted_or_replaced_lines': deleted,
                      'inserted_lines': sum(d-c for tag, _, _, c, d in ops if tag in ('insert', 'replace')),
                      'prior_bytes_preserved_in_order': True})

previous = load('docs/qa/codex-workflow-review-20261027/document-preservation-20261028/current-recheck-20261028/audit.json')
requested = [{'path': item['path'], 'sha256': sha(item['path']), 'exists': True}
             for item in previous['requested_entry_documents']]
assert len(requested) == 18

proposal_path = 'docs/qa/codex-workflow-review-20261027/music-recovery-20261028/registration-plan.json'
proposal = load(proposal_path)
snapshots = [{'source': x['source'], 'source_matches': sha(x['source']) == x['source_sha256'],
              'destination': x['proposed_immutable_file'], 'destination_exists': (ROOT / x['proposed_immutable_file']).exists()}
             for x in proposal['proposed_snapshots']]
classifications = [{'path': p, 'sha256_matches': sha(p) == h}
                   for p, h in proposal['proposed_classification_hashes'].items()]
current_contexts = {x['receipt'] for x in policy['contexts'] if x['usage'] == 'current'}
proposed_contexts = {x['receipt'] for x in proposal['current_contexts_to_regenerate_after_approved_registration']}
assert len(snapshots) == 26 and len({x['source'] for x in snapshots}) == 13
assert all(x['source_matches'] and not x['destination_exists'] for x in snapshots)
assert len(classifications) == 4 and all(x['sha256_matches'] for x in classifications)
assert proposed_contexts == current_contexts and len(current_contexts) == 6

audit = load(str((OUT / 'audit.json').relative_to(ROOT)))
s = audit['summary']
assert s['inventory_paths'] == 2156 and s['inventory_missing'] == 0
assert len(s['inventory_changed']) == 18 and s['inventory_same_sha12'] == 2138
assert s['classified_missing'] == 0 and not s['immutable_mismatches'] and not s['registered_mismatches']
assert not s['adoption_before_mismatches'] and not s['imports_mismatches'] and not s['contexts_changed']
assert not s['historical_observations_changed'] and s['governance_unchanged_during_check']
assert sum(x['path'].endswith('.md') for x in s['inventory_changed']) == 14
historical = [x for x in previous['historical_observations'] if x.get('original_t0_restored') is False]
assert len(historical) == 2
for item in historical:
    assert sha(item['path']) == item['current_sha256']

write('verification.json', {'recorded_at': datetime.now(timezone.utc).isoformat(),
      'prior_freeze': freeze_path, 'frozen_paths': frozen, 'contexts': contexts,
      'before_text_diffs': diffs, 'requested_documents': requested,
      'proposal': {'path': proposal_path, 'sha256': sha(proposal_path), 'executed': False,
                   'snapshots': snapshots, 'classifications': classifications,
                   'current_contexts_to_regenerate': sorted(current_contexts)},
      'unrecovered_historical_json': historical,
      'product_tests': {'run': False, 'reason': 'Read-only document audit; no product behavior changed.'},
      'summary': {'frozen_paths_unchanged': len(frozen), 'contexts_preserved': len(contexts),
                  'requested_documents_present': len(requested), 'before_text_checks': len(diffs),
                  'deleted_or_replaced_lines': 0, 'proposal_sources_current': True}})
print(json.dumps({'verification': 'PASS for preservation checks only', 'frozen_paths': len(frozen),
                  'contexts': len(contexts), 'requested': len(requested), 'before_text_checks': len(diffs),
                  'unrecovered_historical_json': len(historical)}, ensure_ascii=False))
