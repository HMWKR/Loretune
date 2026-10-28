from pathlib import Path
import hashlib, difflib, re, json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = 'be3ff1634a396e378d320cb32020f94a9332e643d2128b5c92209af312ababf5'
source = (ROOT/'index.html').read_text()
assert hashlib.sha256(source.encode()).hexdigest() == BASE, 'Source changed: rebase before building'
old = re.search(r'^function drawExecutionCards\(\).*$',source,re.M).group()
new = old.replace('<article class="guided-card"><h2>${esc(c.shot)} · ${states[c.decision]||esc(c.decision)}</h2>', '<article class="guided-card lt-execution-card" data-decision="${esc(c.decision)}"><h2>${esc(c.shot)} <span class="lt-state-chip">${states[c.decision]||esc(c.decision)}</span></h2>')
new = new.replace('<p>${esc(c.model)} · 공급자 비용 $0 · 외부 전송 없음 · 로컬 연산비 미계측</p>', '<p class="lt-cost-facts">${esc(c.model)} · 공급자 비용 $0 · 외부 전송 없음 · 로컬 연산비 미계측</p>')
start='<p>이 작업은 제작 파이프라인 검증용 단색 이미지를 만듭니다.'
new=new.replace(start,'<details class="lt-provenance-detail"${c.job&&job?.state!==\'collected\'?\' open\':\'\'}><summary>모의 방식·작업 영수증</summary>'+start)
end="${t?`<img src=\"${asset(t)}\""
assert end in new
new=new.replace(end,'</details>'+end)
assert new != old and new.count('<details') == new.count('</details>') == 1
# Only rendered markup changes. Preserve all delegated action buttons verbatim.
assert old[old.index('<div class="toolbar">'):] == new[new.index('<div class="toolbar">'):]
dom=source.replace(old,new)
ui=(OUT/'craft-ui.js').read_text()
dom=dom.replace('</script></html>','</script>\n<script id="loretuneCraftUI">\n'+ui+'\n</script></html>')
css=(OUT/'design-craft.css').read_text()
candidate=dom
# Last stylesheet boundary, before body markup. Inline avoids changing server routes.
idx=candidate.rfind('</style>')+len('</style>')
candidate=candidate[:idx]+'\n<style id="loretuneCraft">\n'+css+'\n</style>'+candidate[idx:]
(OUT/'candidate-index.html').write_text(candidate)
(OUT/'preview-dom.js').write_text(new+'\ndrawExecutionCards();\n'+ui)
for name,text in [('integration-craft.patch',candidate),('dom-only.patch',dom)]:
 (OUT/name).write_text(''.join(difflib.unified_diff(source.splitlines(True),text.splitlines(True),fromfile='a/index.html',tofile='b/index.html')))
scripts=re.findall(r'<script[^>]*>(.*?)</script>',candidate,re.S)
for i,script in enumerate(scripts): (OUT/f'check-script-{i}.js').write_text(script)
(OUT/'manifest.json').write_text(json.dumps({'base_sha256':BASE,'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'script_count':len(scripts),'source_modified':False,'candidate_only':True},indent=2))
print({'source_unchanged':hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()==BASE,'scripts':len(scripts),'patch_ready':True})
