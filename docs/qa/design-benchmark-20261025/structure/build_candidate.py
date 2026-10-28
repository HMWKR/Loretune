"""Read-only source -> independent candidate + exact integration diff.

Run from the project root. Never writes index.html or server code.
"""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
source = (ROOT / 'index.html').read_text()
baseline_file = OUT / 'integration-base.json'
baseline = json.loads((baseline_file if baseline_file.exists() else OUT / 'source-start.json').read_text())['html_sha256']
actual = hashlib.sha256(source.encode()).hexdigest()
if actual != baseline:
    raise SystemExit(f'Source changed: expected {baseline}, found {actual}. Review before rebuilding.')
css = (OUT / 'design-workspace.css').read_text()
js = (OUT / 'workspace-layout.js').read_text()
assert source.count('<body class="lt-system">') == 1
assert source.count('</script></html>') == 1
candidate = source.replace('<body class="lt-system">', '<style id="loretuneWorkspaceLayout">\n' + css + '\n</style>\n<body class="lt-system">')
candidate = candidate.replace('</script></html>', '</script>\n<script id="loretuneWorkspaceStructure">\n' + js + '\n</script></html>')
(OUT / 'candidate-index.html').write_text(candidate)
patch = ''.join(difflib.unified_diff(source.splitlines(True), candidate.splitlines(True), fromfile='a/index.html', tofile='b/index.html'))
(OUT / 'integration-workspace.patch').write_text(patch)
(OUT / 'candidate-manifest.json').write_text(json.dumps({
    'base_html_sha256': actual,
    'candidate_html_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
    'css_sha256': hashlib.sha256(css.encode()).hexdigest(),
    'layout_js_sha256': hashlib.sha256(js.encode()).hexdigest(),
    'changes': 'DOM reparenting, disclosures, mobile panel navigation; original application handlers unchanged',
    'serving': 'app.py serves only index.html plus assets/exports; CSS/JS are embedded in this patch; no server change',
    'status': 'candidate, not integrated',
}, indent=2))
print('Built independent candidate and patch; root index.html unchanged.')
