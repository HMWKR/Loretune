from pathlib import Path
import re, hashlib, json, difflib
D=Path(__file__).resolve().parent
base=(D/'baseline-index.html').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='0a8ef8436b8d751c4581c648beeaa688f054217b5781d1a9528c30d2cca5c6ae'
s=base
changes=[]
def swap(a,b,label=None):
 global s
 assert a in s, f'Missing {label or a[:100]}'
 s=s.replace(a,b)
 changes.append(label or a[:70])
def editfn(name, fn):
 global s
 pat=rf'^function {name}\([^\n]*'
 m=re.search(pat,s,re.M)
 assert m,name
 old=m.group(0);new=fn(old)
 assert new!=old,name
 s=s[:m.start()]+new+s[m.end():]
 changes.append(name)
helpers=(D/'creator-ui.js').read_text()
swap("let commentDraftScope='';",helpers+"\nlet commentDraftScope='';",'insert presentation helpers')
blocks=re.split(r'^// @renderer (\w+)\n',(D/'creator-renderers.js').read_text(),flags=re.M)
for i in range(1,len(blocks),2):
 name,body=blocks[i],blocks[i+1].strip()
 editfn(name,lambda _,body=body:body)
swap(" document.querySelector('#discardTakeReviewDraft').disabled=!local||takeReviewController.pending.has(c?.key);", " document.querySelector('#discardTakeReviewDraft').disabled=!local||takeReviewController.pending.has(c?.key);\n renderCreatorReview(c,local);",'compose review read/edit view with existing controller')
swap("document.getElementById(`model-${role}-reason`).textContent=model?.reason||(role==='image'?'이미지 공급자 미선택 · 기존 이미지 업로드를 이용하세요.':'미선택 · 외부 실행 없음');",'creatorModelReason(role,model);','model change explanation')
swap("value===baseline?'로컬 연결됨'", "value===baseline?'불러옴'", 'routine save status')
editfn('executionDisclosureOpen',lambda x:x.replace("if(card.job&&job?.state!=='collected')return true;",''))
editfn('drawExecutionCards',lambda x:x.replace('${esc(c.model)} · 공급자 비용 $0 · 외부 전송 없음 · 로컬 연산비 미계측','<span class="creator-test-badge">테스트 미디어</span> · 외부 모델 비용 $0 · 외부 전송 없음 · 로컬 처리비 미계측').replace('<summary>모의 방식·작업 영수증</summary>','<summary>작업 상세</summary><p>${esc(c.model)}</p>').replace('$0 모의 작업 승인','$0 테스트 작업 승인').replace('승인한 모의 작업 실행','승인한 테스트 작업 실행').replace('모의 합성 단색 후보','테스트 미디어 후보').replace(".join('')}",".join('');creatorExecutionVisibility()}"))
editfn('drawGuided',lambda x:x.replace('<p>${esc(plan.explanation)}</p>','<details><summary>계획 설명</summary><p>${esc(plan.explanation)}</p></details>').replace('모의 후보 작업 준비 · AI 아님','테스트 미디어 준비').replace('샷 반영됨','장면 추가됨').replace('이 버전 승인·샷 추가','계획 승인·장면 추가'))
editfn('drawGeneration',lambda x:x.replace('실제 호출은 시스템·디자인 QA 후 마지막 승인 단계입니다. 현재는 입력과 견적만 로컬에 저장합니다.','영상 생성은 현재 사용할 수 없습니다. 입력과 예상 비용 확인은 가능합니다.').replace('문서 견적','예상 비용').replace('<p class="muted">계획 v${p.plan_revision} · 영상 작업 ${esc(p.action_id.slice(0,8))} · ${p.grant_id?\'전송 승인 연결됨\':\'전송·비용 승인 전\'}</p>','<p>${p.grant_id?\'전송·비용 승인 연결됨\':\'전송·비용 승인 전\'}</p>${creatorDiagnostic(\'계획 연결 상세\',{plan:p.plan_revision,action:p.action_id})}').replace('시작 참고 v${p.reference_version} · ${p.shot_revision===sh.revision?\'준비 당시 샷 버전과 동일\':\'이후 샷 변경됨: 실행 전 재검토 필요\'}','시작 참고 v${p.reference_version} · ${p.shot_revision===sh.revision?\'준비한 장면과 일치\':\'장면이 바뀌었습니다. 실행 전 다시 확인하세요.\'}').replace("reconciliation_required:'접수 미확정 · 대사 필요'","reconciliation_required:'접수 여부 확인 필요'").replace("import_blocked:'공급자 생성 완료 · 로컬 수신/검증 차단'","import_blocked:'결과를 연결하지 못했습니다'").replace("downloading:'결과 수신·파일 검증 중'","downloading:'결과 연결 중'").replace("imported:'take 연결 완료'","imported:'Take 연결 완료'").replace("<p>${esc(j.last_error||'')}</p>","${j.last_error?`<p class=\"error\">${esc(creatorError(j.last_error).message)}</p>`:''}").replace("${j.provider_request_id?`<small>공급자 요청 ID: ${esc(j.provider_request_id)}</small>`:''}","${creatorDiagnostic('작업 상세',{request:j.provider_request_id,error:j.last_error,state:j.state})}").replace("'전송 전 예약 해제 · 환불 아님':'미확정 · 예약 유지'","'전송 전 취소 · 환불 아님':'확인 중 · 사용 가능 예산에서 보류'").replace('새 T','새 Take ').replace('기존 승인 take 유지','기존 승인 Take 유지'))
swap("'contract-fake':'도구 계약 모의 검증 · 실제 AI 호출 없음','anthropic-live':'실제 Anthropic · 승인된 합성 입력만'","'contract-fake':'테스트 대화 · 실제 AI 호출 없음','anthropic-live':'승인된 테스트 입력만 사용 가능'",'chat capability language')
swap("$('#modelChatCapability').textContent=(labels[cap.mode]||'연결 확인 필요')+' · '+cap.reason+(cap.available?' · 요청당 제한 $'+cap.maximum_usd:'');","$('#modelChatCapability').innerHTML='<p>'+esc(labels[cap.mode]||'연결 확인 필요')+(cap.available?' · 요청당 한도 $'+esc(cap.maximum_usd):' · 지금은 요청할 수 없습니다.')+'</p>'+creatorDiagnostic('연결 상세',cap.reason);",'chat concise availability with original diagnostic')
swap("cap.mode==='contract-fake'?'모의 도구 계약 검증':'승인 범위로 Anthropic 요청'","cap.mode==='contract-fake'?'테스트 대화 요청':'승인 범위로 모델 요청'",'chat button')
swap("${t.error?`<p>${esc(t.error)}</p>`:''}","${t.error?`<p class=\"error\">${esc(creatorError(t.error).message)}</p>${creatorDiagnostic('오류 상세',t.error)}`:''}",'chat error')
swap('<summary>도구 실행 근거 ${(t.steps||[]).length}회</summary>','<summary>진단 기록 ${(t.steps||[]).length}회</summary>','tool traces explicit diagnostic')
editfn('drawProviderBadge',lambda x:x.replace('채팅 모의','테스트 대화').replace('채팅 합성 검증','테스트 입력 전용').replace('영상 모의','테스트 영상'))
editfn('audioWave',lambda x:x.replace("${w.duration.toFixed(1)}초 간이 진폭 · ${w.quiet?'무음 또는 매우 작은 음량 감지':'실제 PCM 측정'}<br>비트·BPM 분석 아님","앞 ${w.duration.toFixed(1)}초 음량${w.quiet?' · 무음 또는 작은 음량':''}</small><details><summary>음량 분석 정보</summary><p>원본 PCM 진폭을 측정했습니다. 비트·BPM 분석은 아닙니다.</p></details><small>"))
editfn('drawFlow',lambda x:x.replace(' · AI 영상 수신은 별도 공급자 검증 대기','').replace('선택된 영상/이미지','선택된 Take'))
editfn('drawOntology',lambda x:x.replace('체크한 승인 개체를 선택 샷에 연결','선택한 설정을 현재 장면에 연결').replace('이 개체 수정 제안','설정 수정 제안').replace('승인된 개체 없음','저장된 설정이 없습니다.').replace('<small>${esc(e.id)} · ${esc(e.uncertainty.reason)}</small>','<small>${esc(e.uncertainty.reason)}</small>${creatorDiagnostic(\'설정 식별 정보\',e.id)}').replace('대상 샷:','현재 장면:').replace('선택 샷 참고로 연결','현재 장면에 연결'))
swap('같은 원본 해시를 사용하는 모든 작품에 적용됩니다.','같은 파일을 사용하는 모든 작품에 적용됩니다.','rights scope in user terms')
swap('실제 호출은 시스템·디자인 QA 후 마지막 승인 단계입니다. 현재는 입력과 견적만 로컬에 저장합니다.','영상 생성은 현재 사용할 수 없습니다. 입력과 예상 비용 확인은 가능합니다.','initial generation gate')
swap('현재 실제 미디어 모델은 미연결입니다. 승인된 계획의 장면으로 로컬 단색 후보 흐름을 검증할 수 있습니다.','테스트 미디어는 단색 이미지입니다. 실제 AI 생성이나 외부 전송은 없습니다.','honest concise synthetic limitation')
swap('실제 제작 객체 계보','설정·제작 연결 기록','ontology lineage title')
# Keep technical data and transaction gates intact; revise only presentation strings.
s=s.replace("'새 개체 제안'","'새 설정'").replace("'동일 개체 수정 · ID 보존'","'기존 설정 수정'")
s=s.replace('<label>IP<select','<label>세계관<select').replace('IP 기준 설정</h2>','세계관 설정</h2>').replace('로컬 IP 만들기</summary>','새 세계관 만들기</summary>').replace('IP 이름<input','세계관 이름<input').replace('>IP 만들기</button>','>세계관 만들기</button>')
s=s.replace('<p>제공자·저장 정책 선택, 계정·설정, 실제 통합 검증, 정확한 입력·비용 전송 승인 순서로 확인합니다. 이 화면은 키를 받거나 권한을 설정하지 않습니다.</p>','<p>사용할 모델의 연결 상태를 확인하세요. 실행 전에 입력·예상 비용·전송 범위를 검토하고 승인해야 합니다.</p>')
s=s.replace('>모델 선택 상태 보기 · 호출 없음</button>','>모델 선택 확인</button>')
swap('<h2>실제 렌더 결과</h2>', """<h2>출력 미리보기</h2>${creatorOutputTest(j)?'<span class="creator-test-badge">테스트 미디어 포함</span>':''}""", 'output provenance badge from immutable snapshot')
# CSS remains standalone in delivery, embedded in the precise HTML integration patch.
pos=s.rfind('</style>')+8
s=s[:pos]+'\n<style id="loretuneCreator">\n'+(D/'creator.css').read_text()+'\n</style>'+s[pos:]
s=s.replace('</html>','<script>initializeCreatorUI();</script>\n</html>')
(D/'candidate-index.html').write_text(s)
(D/'integration-creator.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),s.splitlines(True),fromfile='a/index.html',tofile='b/index.html')))
for i,js in enumerate(re.findall(r'<script[^>]*>([\s\S]*?)</script>',s)):(D/f'candidate-script-{i}.js').write_text(js)
(D/'manifest.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(base.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'source_modified':False,'changes':changes},ensure_ascii=False,indent=2))
print(json.dumps({'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'changes':len(changes)}))
