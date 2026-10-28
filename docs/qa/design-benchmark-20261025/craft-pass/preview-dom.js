function drawExecutionCards(){const p=project();$('#executionCards').innerHTML=(p?.execution_cards||[]).map(c=>{const t=p.shots[c.shot]?.takes.find(t=>t.id===c.take),job=p.rehearsal_jobs?.find(j=>j.id===c.job),states={pending:'승인 대기',held:'보류',rejected:'거절',approved:'실행 승인됨',blocked:'문맥 변경으로 차단'};return `<article class="guided-card lt-execution-card" data-decision="${esc(c.decision)}"><h2>${esc(c.shot)} <span class="lt-state-chip">${states[c.decision]||esc(c.decision)}</span></h2><p>${esc(c.description)}</p><p class="lt-cost-facts">${esc(c.model)} · 공급자 비용 $0 · 외부 전송 없음 · 로컬 연산비 미계측</p><details class="lt-provenance-detail"${c.job&&job?.state!=='collected'?' open':''}><summary>모의 방식·작업 영수증</summary><p>이 작업은 제작 파이프라인 검증용 단색 이미지를 만듭니다. 장면 내용을 그리거나 실제 모델을 호출하지 않습니다.</p>${c.job?`<p>작업 영수증 ${esc(c.job)} · ${esc(job?.state||'상태 확인 중')}</p>`:''}</details>${t?`<img src="${asset(t)}" alt="모의 합성 단색 후보" width="128" height="128"><p>Take ${t.id} · 선택본과 이전 출력은 유지됩니다.</p>`:''}<div class="toolbar">${['pending','held'].includes(c.decision)&&!c.job?`<button data-card="${c.id}" data-action="action_decide" data-decision="approved">$0 모의 작업 승인</button><button data-card="${c.id}" data-action="action_decide" data-decision="held">보류</button><button data-card="${c.id}" data-action="action_decide" data-decision="rejected">거절</button>`:''}${c.decision==='approved'&&!t?`<button data-card="${c.id}" data-action="action_execute">승인한 모의 작업 실행</button><button data-card="${c.id}" data-action="action_decide" data-decision="rejected">실행 전 승인 철회</button>`:''}${t&&!c.result_decision?`<button data-card="${c.id}" data-action="action_review" data-decision="approved">후보 검토 승인</button><button data-card="${c.id}" data-action="action_review" data-decision="rejected">후보 거절</button>`:''}${t?`<button data-card="${c.id}" data-open-shot>작업대에서 Take 비교·선택</button>`:''}</div>${c.result_decision?`<p>후보 ${c.result_decision==='approved'?'승인됨':'거절됨'} · 타임라인 선택은 별도입니다.</p>`:''}</article>`}).join('')}
drawExecutionCards();
/* UI-only enhancement; original nodes, event handlers and values remain intact. */
(() => {
 if (document.body.classList.contains('lt-craft')) return;
 document.body.classList.add('lt-craft');
 const shortStages={'1':'1 음악','2':'2 계획','3':'3 장면','4':'4 출력'};
 document.querySelectorAll('.flow-nav button[data-step]').forEach(button=>{
  const label=button.textContent,short=shortStages[button.dataset.step]; if(!short)return;
  button.setAttribute('aria-label',label);
  const full=document.createElement('span'); full.className='lt-stage-full';full.textContent=label;
  const compact=document.createElement('span');compact.className='lt-stage-short';compact.textContent=short;compact.setAttribute('aria-hidden','true');
  button.replaceChildren(full,compact);
 });
 const notice = document.querySelector('#notice');
 if (notice) {
  const detail = document.createElement('details'); detail.className='lt-notice-detail';
  const summary = document.createElement('summary'); summary.textContent='저장 상태';
  notice.before(detail); detail.append(summary,notice);
  const baseline='로컬 저장소 연결됨 · 선택과 승인을 분리해 안전하게 제작하세요.';
  const reveal = () => {
   const routine=notice.textContent.trim()===baseline && !notice.classList.contains('error');
   summary.textContent=routine?'저장 상태':'알림';
   if (!routine) detail.open=true;
  };
  // Initial routine connection detail is collapsed. New errors or messages are
  // immediately expanded; their original live region and wording are retained.
  new MutationObserver(reveal).observe(notice,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});
  reveal();
 }
 const upload=document.querySelector('#upload'),hint=document.querySelector('.lt-take-review>small');
 if (upload && hint) upload.after(hint);
})();
