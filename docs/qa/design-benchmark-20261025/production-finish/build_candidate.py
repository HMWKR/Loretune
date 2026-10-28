from pathlib import Path
import difflib,hashlib,json,re
D=Path(__file__).parent
s=(D/'baseline-staged.html').read_text(); base=s
def change(old,new):
 global s
 assert s.count(old)==1, (old[:100],s.count(old))
 s=s.replace(old,new)
change('<body', '<style id="loretuneProductionFinish">\n'+(D/'production-finish.css').read_text()+'\n</style>\n<body')
change('function mediaPreparation(p,role){',(D/'production-presentation.js').read_text()+'\nfunction mediaPreparation(p,role){')
start=s.index(" $('#mediaConnections').innerHTML=['image','video']")
end=s.index('\n',start)
change(s[start:end]," $('#mediaConnections').innerHTML=productionOverviewMarkup(p,shotName);")
change(" if(state)renderTakeReview();\n}"," initializeProductionPresentation();\n if(state)renderTakeReview();\n}")
change("const labels={approved:'Take 승인됨',rejected:'Take 거절',changes_requested:'Take 수정 요청'};return {review,decision:review?.decision||'pending',label:labels[review?.decision]||'Take 검토 대기'}", "const labels={approved:'승인됨',rejected:'거절됨',changes_requested:'수정 요청'};return {review,decision:review?.decision||'pending',label:labels[review?.decision]||'검토 전'}")
change('return `<span class="lt-review-state" data-review="${esc(r.decision)}">${esc(r.label)}</span>`', 'return `<span class="lt-review-state" data-review="${esc(r.decision)}" aria-label="Take ${esc(id)} 검토: ${esc(r.label)}"><span class="review-state-symbol" aria-hidden="true">${({approved:\'✓\',pending:\'○\',rejected:\'×\',changes_requested:\'↺\'})[r.decision]||\'○\'}</span>${esc(r.label)}</span>`')
change("${image(t)?`<img style=\"width:100%\" src=\"${asset(t)}\" alt=\"${esc(shotName)} Take ${t.id}\">`:`<video style=\"width:100%\" src=\"${asset(t)}\" controls></video>`}<div class=\"creator-comparison-facts\">", "<div class=\"comparison-media-stage\">${image(t)?`<img src=\"${asset(t)}\" alt=\"${esc(shotName)} Take ${t.id}\">`:`<video src=\"${asset(t)}\" controls></video>`}</div><div class=\"creator-comparison-facts\">")
change('`${Number(meta.duration.toFixed(3))}초`','`원본 ${Number(meta.duration.toFixed(3))}초`')
change("d.open=true;\n}\n$('#mediaRole').onchange", "d.open=true;\n syncProductionPresentation();\n}\n$('#mediaRole').onchange")
# Keep review priority, and make no-Take tools visible even without a media refresh.
change("'미디어 연결 전'}</small>`;\n}\nfunction creatorModelReason", "'미디어 연결 전'}</small>`;\n syncProductionPresentation();\n renderProductionReviewFeedback(c,local);\n}\nfunction creatorModelReason")
change('save:(action,data)=>act(action,data),render:renderTakeReview','save:saveReviewWithFeedback,render:renderTakeReview')
(D/'candidate-index.html').write_text(s)
(D/'integration-presentation.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),s.splitlines(True),fromfile='a/index.html',tofile='b/index.html')))
for i,js in enumerate(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)):(D/f'candidate-script-{i}.js').write_text(js)
(D/'candidate.json').write_text(json.dumps({'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'baseline_sha256':hashlib.sha256(base.encode()).hexdigest(),'runtime_edited':False},indent=2))
print(json.dumps({'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'patch_bytes':(D/'integration-presentation.patch').stat().st_size}))
