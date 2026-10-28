
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

