// @renderer message
function message(t,error=false){
 const presentation=error?creatorError(t):{message:t,detail:''};
 for(const node of [$('#notice'),document.querySelector('dialog[open] .dialog-status')].filter(Boolean)){
  node.textContent=presentation.message;node.className=(node.id==='notice'?'':'dialog-status ')+(error?'error':'');
  const old=node.nextElementSibling;if(old?.dataset.creatorError)old.remove();
  if(presentation.detail&&presentation.detail!==presentation.message){const holder=document.createElement('div');holder.dataset.creatorError='true';holder.innerHTML=creatorDiagnostic('오류 상세',presentation.detail);node.after(holder)}
 }
}
// @renderer drawComparison
function drawComparison(){
 const sh=project()?.shots[shotName];$('#compareTitle').textContent=shotName+' · Take 비교';
 for(const side of ['Left','Right']){const t=sh?.takes.find(t=>t.id===Number($('#compare'+side).value)),target=$('#compare'+side+'Preview');if(!t){target.textContent='Take 없음';continue}
  target.innerHTML=`<div class="creator-comparison-identity"><b>Take ${t.id}</b><span>${sh.selected===t.id?'현재 선택':'미선택'}</span>${studioBadge(sh,t.id)}</div>${image(t)?`<img style="width:100%" src="${asset(t)}" alt="${esc(shotName)} Take ${t.id}">`:`<video style="width:100%" src="${asset(t)}" controls></video>`}<div class="creator-comparison-facts">${creatorMediaMarkup(t)}</div>`;
 }
}
// @renderer drawJobs
function drawJobs(){drawChatProgress();const p=project(),jobs=(state.jobs||[]).filter(j=>j.song===song());
 $('#jobs').innerHTML=jobs.map(j=>{const previous=j.snapshot.timeline.id!==p?.timeline_head||j.snapshot.timeline.clips.some(c=>p?.shots[c.shot]?.selected!==c.take),test=creatorOutputTest(j);return `<div class="job creator-output-card"><header><b>${statuses[j.status]||'상태 확인 필요'}</b>${previous?'<span class="badge">이전 편집 결과</span>':''}</header><p>출력 버전 ${j.snapshot.timeline.id}${test?' · <span class="creator-test-badge">테스트 미디어</span>':''}</p>${j.status!=='completed'?`<progress max="100" value="${j.progress}" aria-label="출력 진행"></progress><p>${j.progress}%</p>`:''}${j.error?`<p class="error">${esc(creatorError(j.error).message)}</p>`:''}${j.download?`<button data-play="${j.download}">결과 검토</button><p class="creator-downloads"><a href="${j.download}" download>영상 저장</a><a href="/exports/${j.id}.srt" download>자막 저장</a></p><p>납품 검토: ${j.delivery_reviews?.at(-1)?.decision==='approved'?'승인됨':'검토 전'}</p><button data-delivery="${j.id}">납품 검토 승인</button>`:''}${['queued','running'].includes(j.status)?`<button data-cancel="${j.id}">출력 취소</button>`:''}<details class="creator-diagnostic"><summary>출력 기록</summary><p>${esc(j.id)}</p><p>${esc(j.error||'오류 기록 없음')}</p>${j.download?`<a href="/exports/${j.id}.json" download>제작 기록 다운로드</a>`:''}</details></div>`}).join('')||'<p>편집을 저장하고 승인하면 영상을 출력할 수 있습니다.</p>';
}
// @renderer imageConnectionMarkup
function imageConnectionMarkup(cap){const labels={unconfigured:'이미지 모델 미선택',unverified:'이미지 연결 확인 필요',blocked:'이미지 연결 차단',available:'승인 범위에서 사용 가능'};return `<p><b>${labels[cap.state]||'이미지 연결 확인 필요'}</b>${cap.model?' · '+esc(cap.model):''}</p><p>${cap.available?'작업별 입력과 예상 비용을 확인한 뒤 승인하세요.':'지금은 기존 이미지를 연결할 수 있습니다.'}</p>${cap.mode==='contract-fake'?'<span class="creator-test-badge">테스트 연결 · 실제 AI 호출 없음</span>':''}${creatorDiagnostic('연결 상세',{reason:cap.reason,policy:cap.policy,checks:cap.checks})}`}
// @renderer imageRecoveryMarkup
function imageRecoveryMarkup(j){const labels={imported:'Take 연결 완료',import_blocked:'결과를 연결하지 못했습니다',reconciliation_required:'접수 여부 확인 필요',image_recovery_pending:'기존 결과 확인 대기',image_recovery_running:'기존 결과 확인 중'},r=j.image_recovery||{};return `<section class="creator-recovery-card"><h3>${labels[j.state]||'작업 상태 확인 필요'}</h3>${j.mode==='contract-fake'?'<span class="creator-test-badge">테스트 미디어</span>':''}${j.state!=='imported'?`<p>${esc(creatorError(j.last_error||r.reason||'결과 상태 미확정').message)}</p>`:''}${j.retention_notice?`<p>${esc(j.retention_notice)}</p>`:''}<p>기존 결과를 확인합니다. 새 생성이나 환불은 실행하지 않습니다.</p>${r.can_status?`<button data-image-recovery="status" data-job="${esc(j.id)}">기존 요청 확인</button>`:''}${r.can_collect?`<button data-image-recovery="collect" data-job="${esc(j.id)}">기존 결과 연결</button>`:''}${!r.can_status&&!r.can_collect&&j.state!=='imported'?'<p>연결 권한을 확인해야 계속할 수 있습니다.</p>':''}${creatorDiagnostic('작업 상세',{job:j.id,request:j.provider_request_id,state:j.state,error:j.last_error,recovery:r.reason})}</section>`}
// @renderer drawModelSettings
function drawModelSettings(){const p=project(),roles={chat:'채팅·기획',image:'이미지',video:'영상'},m=p?.model_settings;
 $('#modelSlots').innerHTML=Object.entries(roles).map(([role,label])=>`<section class="creator-model-slot"><label>${label} 모델<select name="${role}" aria-describedby="model-${role}-selected model-${role}-reason" ${!p?'disabled':''}><option value="">미선택</option>${(state.model_catalog?.models||[]).filter(x=>x.role===role).map(x=>`<option value="${esc(x.id)}" ${m?.selections[role]===x.id?'selected':''}>${esc(x.model)} · ${x.state==='integration_blocked'?'사용 불가':'연결 확인 필요'}</option>`).join('')}</select></label><p id="model-${role}-selected" class="lt-model-name">${esc((state.model_catalog?.models||[]).find(x=>x.id===m?.selections[role])?.model||'선택된 모델 없음')}</p><p id="model-${role}-reason" class="muted"></p></section>`).join('');
 for(const role of Object.keys(roles))creatorModelReason(role,(state.model_catalog?.models||[]).find(x=>x.id===m?.selections[role]));
 $('#modelDefaultsSummary').textContent=Object.entries(roles).map(([r,label])=>label+': '+((state.model_catalog?.models||[]).find(x=>x.id===m?.selections[r])?.model||'미선택')).join(' / ');
 $('#modelSettingsForm button').disabled=!p||!state.model_catalog;
 $('#modelSettingsStatus').textContent=!p?'작품을 먼저 선택하세요.':!state.model_catalog?'지금은 모델을 선택할 수 없습니다. 기존 미디어로 제작을 계속할 수 있습니다.':'선택만 저장합니다. 실행 전에 입력과 비용에 대한 별도 승인이 필요합니다.';
}
// @renderer renderStudioShots
function renderStudioShots(p){return Object.entries(p.shots).map(([name,s],i)=>{const t=s.takes.find(t=>t.id===s.selected);return `<button class="shot ${name===shotName?'active':''}" data-shot="${esc(name)}" aria-pressed="${name===shotName}">${t&&image(t)?`<img class="thumb" src="${asset(t)}" alt="">`:`<span class="thumb lt-media-kind">${t?'영상':'미연결'}</span>`}<span class="lt-scene-copy"><b>${esc(creatorSceneLabel(name,i))}</b><small>${esc(creatorSceneFacts(p,name,s))}</small>${t?studioBadge(s,t.id):'<small>미디어 연결 전</small>'}</span></button>`}).join('')}
// @renderer showBudget
function showBudget(){budgetProject=state.project_ids[song()];const b=(state.budgets||[]).find(b=>b.data.scope==='project:'+budgetProject);budgetRevision=b?.revision||0;const d=b?.data;$('#budgetSummary').innerHTML=d?`<p>한도 ${esc(d.limit.amount)} ${esc(d.limit.currency)} · 사용 가능 ${esc(d.available.amount)}</p><p>기록된 사용액 ${esc(d.netConfirmed.amount)} · 진행 중 작업 금액 ${esc(d.reserved.amount)}</p>${d.overrun.amount!=='0'?`<p>한도 초과 ${esc(d.overrun.amount)}</p>`:''}${creatorDiagnostic('예산 상세',{revision:b.revision,maxConcurrentJobs:d.maxConcurrentJobs,overrun:d.overrun})}`:'설정된 제작 예산이 없습니다.';return b}
