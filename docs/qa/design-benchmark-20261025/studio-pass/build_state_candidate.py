from pathlib import Path
import re,hashlib,difflib,json
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
source=(ROOT/'index.html').read_text()
BASE='4f1805f00abb1ba2b5f7d6012727b4736e97cd4c35a007942ef6550781ae30dd'
assert hashlib.sha256(source.encode()).hexdigest()==BASE,'Shared source changed: rebase explicitly'
candidate=source
def replace_once(old,new):
 global candidate
 assert candidate.count(old)==1,old[:80]
 candidate=candidate.replace(old,new,1)
old_draw=re.search(r'^function draw\(\).*$',source,re.M).group()
draw=old_draw
a=draw.index("$('#shotlist').innerHTML=");b=draw.index("$('#snapshot').innerHTML=",a)
draw=draw[:a]+draw[b:]
a=draw.index("$('#takes').innerHTML=");b=draw.index('const review=',a)
draw=draw[:a]+draw[b:]
draw=draw.replace(" · ${review?({approved:'승인됨',changes_requested:'수정 요청',rejected:'거절'})[review.decision]:'검토 대기'}",'')
replace_once(old_draw,draw)
old_timeline=re.search(r'^function drawTimeline\(\).*$',source,re.M).group()
timeline=old_timeline
a=timeline.index("$('#track').innerHTML=");b=timeline.index("$('#clips').innerHTML=",a)
timeline=timeline[:a]+"$('#track').innerHTML=renderStudioTrack(p);"+timeline[b:]
timeline=timeline.replace("draft.approval?' · 승인됨':' · 승인 대기'","draft.approval?' · 출력 승인됨':' · 출력 승인 대기'")
timeline=timeline[:-1]+";$('#shotlist').innerHTML=renderStudioShots(p);$('#takes').innerHTML=renderStudioTakes(p.shots[shotName]);renderTakeReview()}"
replace_once(old_timeline,timeline)
old_review="$('#reviewTake').onclick=()=>{const sh=project()?.shots[shotName];if(sh?.selected)act('review_take',{song:song(),shot:shotName,take:sh.selected,decision:$('#takeDecision').value,reason:$('#reviewReason').value});else message('take를 먼저 선택하세요.',true)};"
replace_once(old_review,"$('#reviewTake').onclick=()=>takeReviewController.submit();")
old_compare=re.search(r"\$\('#compareButton'\)\.onclick=\(\)=>\{.*?\};(?=\$\('#compareLeft'\))",source).group()
replace_once(old_compare,"$('#compareButton').onclick=openStudioComparison;")
old_compare_draw=re.search(r'^function drawComparison\(\).*$',source,re.M).group()
compare_draw=old_compare_draw.replace('take 없음','Take 없음').replace('T${t.id} ·','Take ${t.id} ·').replace('alt="비교 T${t.id}"','alt="비교 Take ${t.id}"')
compare_draw=compare_draw.replace("${esc(({approved:'승인됨',rejected:'거절',changes_requested:'수정 요청'})[review?.decision]||'검토 대기')}","${studioBadge(sh,t.id)}")
replace_once(old_compare_draw,compare_draw)
replace_once('drawModelChat();const status=document.querySelector', 'drawModelChat();renderTakeReview();const status=document.querySelector')
replace_once("drawModelChat();message('요청 복구 정보를", "drawModelChat();renderTakeReview();message('요청 복구 정보를")
replace_once("reviewSection.querySelector('h2').after(reason);", "reviewSection.querySelector('h2').after(q('#takeReviewStatus'),reason);")
a=candidate.index("  const baseline='로컬 저장소 연결됨",candidate.index('<script id="loretuneCraftUI">'))
b=candidate.index('  reveal();',a)+len('  reveal();')
candidate=candidate[:a]+'  installStudioNotice(notice,detail,summary);'+candidate[b:]
helper=(OUT/'review-state.js').read_text()
replace_once("let commentDraftScope='';",helper+"\nlet commentDraftScope='';")
replace_once('<input id="reviewReason" value="검토 완료">','<textarea id="reviewReason" rows="3" maxlength="2000">검토 완료</textarea>')
candidate=candidate.replace('take 나란히 비교</button>','Take 나란히 비교</button>')
candidate=candidate.replace('같은 샷의 take 비교','같은 장면의 Take 비교').replace('왼쪽 take<select','왼쪽 Take<select').replace('오른쪽 take<select','오른쪽 Take<select')
css=(OUT/'studio-state.css').read_text();pos=candidate.rfind('</style>')+len('</style>')
candidate=candidate[:pos]+'\n<style id="loretuneStudioStates">\n'+css+'\n</style>'+candidate[pos:]
(OUT/'state-candidate-index.html').write_text(candidate)
(OUT/'integration-studio-states.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),candidate.splitlines(True),fromfile='a/index.html',tofile='b/index.html')))
# Browser preview runs only these UI functions; no bootstrap/refresh replay.
preview=helper+'\n'+draw+'\n'+timeline+'\n'+compare_draw+"\n$('#reviewTake').onclick=()=>takeReviewController.submit();$('#compareButton').onclick=openStudioComparison;\n"
preview+="const oldNotice=document.querySelector('#notice'),newNotice=oldNotice.cloneNode(true);oldNotice.replaceWith(newNotice);installStudioNotice(newNotice,newNotice.parentElement,newNotice.parentElement.querySelector('summary'));\n"
preview+="document.querySelector('#compareButton').textContent='Take 나란히 비교';document.querySelector('#compareDialog h2').textContent='같은 장면의 Take 비교';document.querySelector('#compareLeft').parentElement.firstChild.textContent='왼쪽 Take';document.querySelector('#compareRight').parentElement.firstChild.textContent='오른쪽 Take';\n"
preview+="const reviewBox=document.querySelector('#takeReviewStatus'),reasonBox=document.querySelector('#reason');reasonBox.before(reviewBox);draw();\n"
(OUT/'state-preview.js').write_text(preview)
scripts=re.findall(r'<script[^>]*>(.*?)</script>',candidate,re.S)
for i,script in enumerate(scripts):(OUT/f'state-check-{i}.js').write_text(script)
(OUT/'state-manifest.json').write_text(json.dumps({'base':BASE,'candidate':hashlib.sha256(candidate.encode()).hexdigest(),'scripts':len(scripts),'source_modified':False},indent=2))
print({'base':BASE,'candidate_ready':True})
