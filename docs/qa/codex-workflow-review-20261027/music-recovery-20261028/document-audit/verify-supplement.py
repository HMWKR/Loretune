from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,unquote
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
DOCUMENTS=[
'README.md','docs/qa/codex-cli-assessment-20261026/PLAN-ko.md','docs/design/CHAT-SESSION-PLAN.md','docs/qa/OMISSION-REGISTER.md','docs/qa/REMAINING-WORK.md','docs/qa/SPEC-MS-001-ACCEPTANCE-TRACE.md','docs/design/CURRENT-DESIGN-QA-PLAN.md','docs/qa/design-system-redesign-20261026/REFERENCE-LOCK.md','docs/qa/design-system-redesign-20261026/SEMANTIC-TOKEN-SPEC.md','docs/qa/design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md','docs/qa/design-system-redesign-20261026/INDEX.md','docs/design/AI-MODELING-PLAN.md','docs/design/AETHONSAAS-ADOPTION-PROPOSAL.md','docs/design/PRODUCT-IDENTITY-AMENDMENT-20261027.md','docs/qa/adoption-docs-20261027/REPORT-ko.md','docs/qa/DOCUMENT-INVENTORY-20261027.md','docs/qa/ONTOLOGY-COVERAGE-AUDIT-20261027.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
rows=[]; links=[]; skipped=[]
for relative in DOCUMENTS:
 p=ROOT/relative
 rows.append({'path':relative,'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else None,'sha256':sha(p) if p.is_file() else None})
 if not p.is_file():continue
 # Blank fenced-code and inline-code contents to avoid treating examples as authored links.
 lines=p.read_text().splitlines(); visible=[]; fence=None
 for line in lines:
  m=re.match(r'^\s*(`{3,}|~{3,})',line)
  if m:
   mark=m[1][0]
   if fence is None:fence=mark
   elif fence==mark:fence=None
   visible.append('');continue
  visible.append('' if fence else re.sub(r'`[^`]*`','',line))
 references={}
 for n,line in enumerate(visible,1):
  m=re.match(r'^\s*\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))',line)
  if m:references[m[1].casefold()]=(m[2] or m[3])
 extracted=[]
 for n,line in enumerate(visible,1):
  for m in re.finditer(r'!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[\"\x27][^\"\x27]*[\"\x27])?\s*\)',line):
   extracted.append((n,m[1] or m[2],'inline'))
  for m in re.finditer(r'!?\[([^\]]+)\]\[([^\]]*)\]',line):
   key=(m[2] or m[1]).casefold()
   if key in references:extracted.append((n,references[key],'reference'))
 for n,target,kind in extracted:
  parsed=urlsplit(target)
  if parsed.scheme or parsed.netloc or not parsed.path:
   skipped.append({'source':relative,'line':n,'target':target,'reason':'external-or-anchor-only'});continue
  raw=unquote(parsed.path)
  q=Path(raw) if raw.startswith('/') else p.parent/raw
  q=q.resolve(strict=False)
  if not q.is_relative_to(ROOT) or (q.is_relative_to(ROOT/'docs/private')):
   skipped.append({'source':relative,'line':n,'target':target,'reason':'outside-scope'});continue
  links.append({'source':relative,'line':n,'target':target,'resolved':str(q.relative_to(ROOT)),'exists':q.exists(),'kind':kind,'fragment':parsed.fragment,'fragment_verified':False if parsed.fragment else None})
policy=load('.document-gate.json'); bases={r['name']:Path(r['base']) for r in policy['registries']}
contexts=[]
for item in policy['contexts']:
 receipt=load(item['receipt']); p=ROOT/bases[item['registry']]/receipt['context_file']
 contexts.append({'receipt':item['receipt'],'usage':item['usage'],'context_path':str(p.relative_to(ROOT)),'expected_sha256':receipt['context_sha256'],'current_sha256':sha(p) if p.is_file() else None,'exists':p.is_file(),'match':p.is_file() and sha(p)==receipt['context_sha256']})
proposal_path='docs/qa/codex-workflow-review-20261027/workflow-simplification-20261028/registration-plan.json'
proposal=load(proposal_path)
classifications=[{'path':p,'expected':h,'actual':sha(ROOT/p),'match':sha(ROOT/p)==h} for p,h in proposal['proposed_classification_hashes'].items()]
before=load(str((OUT/'documents-before.json').relative_to(ROOT)))
after={p:sha(ROOT/p) if (ROOT/p).is_file() else None for p in before}
(OUT/'documents-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
diff=[{'path':p,'before':h,'after':after[p]} for p,h in before.items() if after[p]!=h]
result={'schema':'document-preservation-live-supplement/1','checked_at':datetime.now(timezone.utc).isoformat(),'summary':{'requested_documents':len(rows),'requested_missing':sum(not x['exists'] for x in rows),'local_link_occurrences':len(links),'local_link_unique_destinations':len({x['resolved'] for x in links}),'local_links_missing':sum(not x['exists'] for x in links),'skipped_links':len(skipped),'context_payloads':len(contexts),'context_payload_mismatches':sum(not x['match'] for x in contexts),'classification_proposal_matches':sum(x['match'] for x in classifications),'frozen_files':len(before),'changed_during_audit':len(diff)},'requested_documents':rows,'local_links':links,'missing_local_links':[x for x in links if not x['exists']],'skipped_links':skipped,'context_payloads':contexts,'proposal':{'path':proposal_path,'sha256':sha(ROOT/proposal_path),'classifications':classifications,'snapshots_requested':len(proposal['proposed_snapshots']),'contexts_requested':len(proposal['current_contexts_to_regenerate_after_approved_registration'])},'changed_during_audit':diff,'limitations':['Local link target existence only; external URLs and heading anchors were not executed or verified.','Parser covers standard inline and full-reference Markdown links, excluding fenced and inline code. Shortcut references and raw HTML links are not included.','No source/product tests apply: the agent only created scoped audit evidence.','No restoration or proof about unknown preT0 history.']}
(OUT/'supplement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['summary'],ensure_ascii=False,indent=2));print('missing links:',json.dumps(result['missing_local_links'],ensure_ascii=False)[:5000]);print('changed:',diff)
