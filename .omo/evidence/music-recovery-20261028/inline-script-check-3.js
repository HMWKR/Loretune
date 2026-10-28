
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
  installStudioNotice(notice,detail,summary);
 }
 const upload=document.querySelector('#upload'),hint=document.querySelector('.lt-take-review>small');
 if (upload && hint) upload.after(hint);
})();

