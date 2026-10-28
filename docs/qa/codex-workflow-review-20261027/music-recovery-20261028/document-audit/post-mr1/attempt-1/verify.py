"""Read-only MR1 document/evidence audit; writes only this follow-up directory."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from urllib.parse import urlsplit, unquote
import difflib
import hashlib
import json
import re
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
PRIOR = OUT.parent
EVIDENCE = ROOT / 'docs/qa/codex-workflow-review-20261027/music-recovery-20261028'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def run(command, name):
    result = subprocess.run(command, capture_output=True, check=False)
    write(name + '-command.json', {'command': command, 'exit_code': result.returncode,
                                 'stdout_bytes': len(result.stdout),
                                 'stderr': result.stderr.decode(errors='replace')})
    if result.returncode:
        raise RuntimeError(f'{name} exited {result.returncode}')
    return result.stdout


before = load(ROOT / '.omo/evidence/music-recovery-20261028/document-before.json')
baseline = load(PRIOR / 'documents-final.json')
expected_docs = {'README.md', 'docs/qa/codex-workflow-review-20261027/REPORT-ko.md',
                 'docs/qa/REMAINING-WORK.md'}
assert set(before) == expected_docs
document_hashes_at_start = {p: sha(ROOT / p) for p in baseline}
changed_from_prior = sorted(p for p, h in baseline.items() if document_hashes_at_start[p] != h)
assert set(changed_from_prior) == expected_docs

prior_artifacts = []
for item in load(PRIOR / 'manifest.json')['files']:
    p = PRIOR / item['path']
    prior_artifacts.append({'path': item['path'], 'match': p.is_file() and sha(p) == item['sha256']})
assert all(item['match'] for item in prior_artifacts)

document_changes = []
links = []
added_texts = {}
for relative, entry in before.items():
    old = entry['text']
    assert hashlib.sha256(old.encode()).hexdigest() == entry['sha256'] == baseline[relative]
    current = (ROOT / relative).read_text()
    old_lines, new_lines = old.splitlines(keepends=True), current.splitlines(keepends=True)
    opcodes = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes()
    reconstructed = ''.join(''.join(new_lines[c:d]) for tag, _, _, c, d in opcodes if tag == 'equal')
    added = ''.join(''.join(new_lines[c:d]) for tag, _, _, c, d in opcodes if tag == 'insert')
    deleted = sum(b-a for tag, a, b, _, _ in opcodes if tag in ('delete', 'replace'))
    assert reconstructed == old and deleted == 0
    added_texts[relative] = added
    document_changes.append({'path': relative, 'before_sha256': entry['sha256'],
                             'after_sha256': sha(ROOT / relative),
                             'deleted_or_replaced_lines': deleted,
                             'inserted_lines': len(added.splitlines()),
                             'before_bytes_reconstructed_in_order': True})
    for match in re.finditer(r'\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)', added):
        target = match[1] or match[2]
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        p = ((ROOT / relative).parent / unquote(parsed.path)).resolve()
        assert p.is_relative_to(ROOT)
        links.append({'source': relative, 'target': target,
                      'path': str(p.relative_to(ROOT)), 'exists': p.exists()})
assert all(item['exists'] for item in links)
write('document-diff-and-links.json', {'documents': document_changes, 'added_local_links': links,
                                     'link_scope': 'Local targets in inserted Markdown only; external URLs/heading anchors not verified'})

policy = load(ROOT / '.document-gate.json')
immutable = [{'path': item['path'], 'match': sha(ROOT / item['path']) == item['baseline_sha256']}
             for item in policy['documents'] if 'baseline_sha256' in item]
registered = []
bases = {}
for registry in policy['registries']:
    bases[registry['name']] = Path(registry['base'])
    raw = load(ROOT / registry['path'])
    for item in raw['objects']:
        if item['kind'] == 'Document':
            p = ROOT / registry['base'] / item['file']
            registered.append({'path': str(p.relative_to(ROOT)), 'match': sha(p) == item['sha256']})
contexts = []
for item in policy['contexts']:
    receipt = load(ROOT / item['receipt'])
    p = ROOT / bases[item['registry']] / receipt['context_file']
    contexts.append({'receipt': item['receipt'], 'receipt_preserved': sha(ROOT / item['receipt']) == baseline[item['receipt']],
                     'path': str(p.relative_to(ROOT)), 'payload_matches_receipt': sha(p) == receipt['context_sha256']})
assert len(immutable) == 544 and all(x['match'] for x in immutable)
assert len(registered) == 285 and all(x['match'] for x in registered)
assert len(contexts) == 58 and all(x['receipt_preserved'] and x['payload_matches_receipt'] for x in contexts)
write('preservation.json', {'prior_artifacts': prior_artifacts, 'changed_since_prior': changed_from_prior,
                          'immutable': immutable, 'registered': registered, 'contexts': contexts})

proposal_file = EVIDENCE / 'registration-plan.json'
proposal = load(proposal_file)
assert sha(proposal_file) == 'd0b340899f73fbfc9bdc43eae649b1b4609b0e932dcbace0a8385fb779791d68'
proposal_checks = []
for item in proposal['proposed_snapshots']:
    proposal_checks.append({'source': item['source'], 'sha256': sha(ROOT / item['source']),
                            'source_match': sha(ROOT / item['source']) == item['source_sha256'],
                            'destination': item['proposed_immutable_file'],
                            'destination_exists': (ROOT / item['proposed_immutable_file']).exists()})
classifications = [{'path': p, 'match': sha(ROOT / p) == h}
                   for p, h in proposal['proposed_classification_hashes'].items()]
expected_contexts = {x['receipt'] for x in policy['contexts'] if x['usage'] == 'current'}
proposed_contexts = {x['receipt'] for x in proposal['current_contexts_to_regenerate_after_approved_registration']}
assert len(proposal_checks) == 26 and len({x['source'] for x in proposal_checks}) == 13
assert all(x['source_match'] and not x['destination_exists'] for x in proposal_checks)
assert len(classifications) == 4 and all(x['match'] for x in classifications)
assert proposed_contexts == expected_contexts and len(expected_contexts) == 6
write('proposal-check.json', {'path': str(proposal_file.relative_to(ROOT)), 'sha256': sha(proposal_file),
                             'snapshot_links': proposal_checks, 'classifications': classifications,
                             'contexts_match_current_policy': True, 'current_context_receipts': sorted(proposed_contexts),
                             'registration_or_context_generation_performed': False})

source_before = load(EVIDENCE / 'focused-source-before.json')
source_after = load(EVIDENCE / 'focused-source-after.json')
source_current = load(EVIDENCE / 'source-current.json')
assert source_before == source_after == source_current and len(source_current) == 214
actual_source = {p: sha(ROOT / p) for p in source_current}
assert actual_source == source_current
old_source = load(EVIDENCE / 'task-contract.json')['source_before']
source_changes = sorted(p for p, h in old_source.items() if actual_source.get(p) != h)
driver = load(EVIDENCE / 'driver-acceptance.json')
assert source_changes == sorted(driver['changed_sources']) and len(source_changes) == 6
log = (EVIDENCE / 'focused-regression.log').read_text()
count_time = re.search(r'^Ran (\d+) tests in ([\d.]+)s$', log, re.M)
assert count_time and (int(count_time[1]), float(count_time[2])) == (57, 24.683)
assert log.rstrip().endswith('OK') and not re.search(r'\b(skipped|FAILED|ERROR|FAIL:)\b', log)
result = load(EVIDENCE / 'focused-regression-result.json')
assert result['exit'] == 0 and not result['source_changed_during_run']
write('test-and-source-claim-check.json', {'tests': 57, 'unittest_seconds': 24.683,
                                        'process_wall_seconds_separate': result['seconds'],
                                        'original_test_command': result['command'],
                                        'log_sha256': sha(EVIDENCE / 'focused-regression.log'),
                                        'source_count': len(actual_source), 'source_before_after_current_match': True,
                                        'changed_since_S819': source_changes,
                                        'full819_rerun_claimed': False,
                                        'this_auditor_reran_57_tests': False})

media = EVIDENCE / 'music-only-typography.mp4'
claimed_media = load(EVIDENCE / 'media-verification.json')
assert sha(media) == claimed_media['output_sha256'] == '919136cd796418dfdcbc1cf682da0caf96914ae1a29743cf1446a459b7a5dfdd'
assert media.stat().st_size == claimed_media['output_bytes'] == 45481
probe = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(media)], 'ffprobe'))
write('actual-media-ffprobe.json', probe)
video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
caption = next(s for s in probe['streams'] if s['codec_type'] == 'subtitle')
assert (video['width'], video['height'], video['r_frame_rate'], int(video['nb_read_frames'])) == (1920, 1080, '24/1', 72)
assert float(probe['format']['duration']) == 3 and int(audio['sample_rate']) == 48000
assert caption['codec_name'] == 'mov_text'
pcm = run(['ffmpeg', '-v', 'error', '-i', str(media), '-map', '0:a:0', '-ac', '1', '-ar', '48000', '-t', '3', '-f', 's16le', '-'], 'ffmpeg-pcm')
assert len(pcm) // 2 == 144000
srt = run(['ffmpeg', '-v', 'error', '-i', str(media), '-map', '0:s:0', '-f', 'srt', '-'], 'ffmpeg-srt').decode()
assert srt == claimed_media['srt']
playback = load(EVIDENCE / 'actual-browser-playback.json')
assert playback['currentTime'] > 1 and not playback['paused'] and not playback['muted']
assert playback['tracks'][0]['mode'] == 'showing' and playback['tracks'][0]['cues'][0]['text'] == '음원만으로 시작한 영상'
reopened = load(EVIDENCE / 'reopened-state.json')
project = next(iter(reopened['projects'].values()))
shot = next(iter(project['shots'].values()))
exports = [j for j in reopened['jobs'] if j.get('download', '').startswith('/exports/')]
assert len(exports) == 1 and exports[0]['status'] == 'completed' and exports[0]['sha256'] == sha(media)
assert shot['takes'][0]['metadata']['duration'] == 4 and shot['motion_head'] == 2
assert project['timeline_head'] == 1 and project['timeline_versions'][0]['audio_offset'] == 3
assert project['preflight']['music_selection_warning'] is None
warnings = [load(EVIDENCE / f'selection-warning-{w}.json') for w in [1920, 1280, 375]]
assert all(x['width'] == w and x['overflow'] == 0 and '3.000–4.000초' in x['text'] and '3.000–6.000초' in x['text'] for x, w in zip(warnings, [1920, 1280, 375]))
write('media-and-receipt-claim-check.json', {'file': str(media.relative_to(ROOT)), 'sha256': sha(media),
                                         'bytes': media.stat().st_size, 'duration': 3, 'frames_decoded': 72,
                                         'resolution': [1920, 1080], 'fps': '24/1', 'audio_rate': 48000,
                                         'pcm_decoded_for_declared_3seconds': len(pcm) // 2,
                                         'pcm_sha256': hashlib.sha256(pcm).hexdigest(), 'captions': srt,
                                         'driver_receipts_consistent': True, 'native_candidate_duration': 4,
                                         'export_jobs': len(exports), 'reported_native_playback_seconds': playback['currentTime'],
                                         'captured_widths_verified': [1920, 1280, 375],
                                         'this_auditor_reexecuted_browser_or_user_test': False})

gate_command = ['python3', '/Users/leesungmin/.agents/skills/document-completion-gate/check.py', '--root', str(ROOT)]
gate = subprocess.run(gate_command, capture_output=True, check=False)
(OUT / 'document-gate.json').write_bytes(gate.stdout)
parsed_gate = json.loads(gate.stdout)
gate_receipt = {'command': gate_command, 'exit_code': gate.returncode, 'stderr': gate.stderr.decode(),
                'status': parsed_gate['status'], 'evidence_sha256': parsed_gate['evidence_sha256'],
                'findings': dict(Counter(x['code'] for x in parsed_gate['findings'])),
                'warnings': dict(Counter(x['code'] for x in parsed_gate['warnings']))}
write('document-gate-invocation.json', gate_receipt)
assert gate.returncode == 1 and parsed_gate['status'] == 'blocked'
assert gate_receipt['findings'] == {'REGISTERED_SOURCE_OUTDATED': 26, 'UNCLASSIFIED_DOCUMENT': 4}
document_hashes_at_end = {p: sha(ROOT / p) for p in baseline}
assert document_hashes_at_start == document_hashes_at_end
write('document-hash-freeze.json', {'before': document_hashes_at_start, 'after': document_hashes_at_end,
                                   'paths': len(baseline), 'changes_during_this_followup': []})
report = {'schema': 'post-mr1-document-preservation-audit/1', 'recorded_at': datetime.now(timezone.utc).isoformat(),
          'status': 'REPORTED; driver acceptance pending', 'source_documents_changed_by_auditor': [],
          'whole_platform_complete': False, 'prior_evidence_files_preserved': len(prior_artifacts),
          'changed_from_prior_freeze': changed_from_prior, 'document_changes': document_changes,
          'added_local_link_count': len(links), 'missing_added_local_links': [],
          'immutable_sha256_matches': len(immutable), 'registered_sha256_matches': len(registered),
          'context_receipt_and_payload_matches': len(contexts), 'frozen_existing_paths': len(baseline),
          'source_test_claim_consistency': '57 tests/24.683s log; 214 sources before/after/current identical; six changed since S819',
          'media_claim_consistency': 'Actual ffprobe/FFmpeg decode corroborates declared 3-second MP4 and one Korean subtitle; browser receipts are consistent, not rerun by auditor',
          'proposal': {'sha256': sha(proposal_file), 'sources': 13, 'links': 26, 'classifications': 4,
                       'current_contexts': 6, 'destinations_created': 0, 'executed': False},
          'gate': gate_receipt,
          'limitations': ['Two historical QA JSON T0 bytes and unknown preT0 history remain unresolved.',
                          'No private/external/provider accesses; no registration, promotion, context regeneration, or MD changes.',
                          'Standard local link destinations in added text verified; external pages and heading anchors not checked.',
                          'Browser receipt consistency is not an independent live browser replay, visual review, or real-user acceptance.',
                          '57 tests were not rerun during this document audit; their retained log and exact current source provenance were checked.',
                          'Full819 baseline not represented as current regression.'],
          'fablize_narrow_verification': 'This verifier directly checked preservation, source/log provenance, actual media decode, proposal scope and the read-only document gate.'}
write('report.json', report)
print(json.dumps({'report': str(OUT / 'report.json'), 'documents': len(document_changes),
                  'insertions': [x['inserted_lines'] for x in document_changes], 'local_links': len(links),
                  'gate': gate_receipt, 'existing_paths_preserved_during_followup': len(baseline)}, ensure_ascii=False))
