/* Presentation only. Backend capability and command handlers remain authoritative. */
const productionReviewErrors=new Map();
async function saveReviewWithFeedback(action,data){
 const key=takeReviewKey(state.workspace_id,data.song,data.shot,data.take);
 try{const ok=await act(action,data);if(ok)productionReviewErrors.delete(key);else productionReviewErrors.set(key,true);return ok}
 catch(error){productionReviewErrors.set(key,true);throw error}
}
function renderProductionReviewFeedback(c,local){
 const editor=document.getElementById('creatorReviewEditor');if(!editor)return;
 let note=document.getElementById('productionReviewError');if(!note){note=document.createElement('p');note.id='productionReviewError';note.className='production-review-error';note.setAttribute('role','alert');editor.prepend(note);const input=document.getElementById('reviewReason');input.setAttribute('aria-describedby','takeReviewDraftState productionReviewError')}
 const show=!!(c&&local&&productionReviewErrors.has(c.key));note.hidden=!show;note.textContent=show?'저장 확인 필요 · 입력은 보존했습니다. 상단 알림에서 저장 상태를 확인하세요.':'';
}
function productionModelView(p,role){
 const c=p?.media_connections?.[role],id=p?.model_settings?.selections?.[role];
 const raw=c?.model||id||'';
 const names={'fal-flux-schnell':'FLUX Schnell','fal-ai/flux/schnell':'FLUX Schnell','fal-kling-2-6-pro':'Kling 2.6 Pro','fal-ai/kling-video/v2.6/pro/image-to-video':'Kling 2.6 Pro'};
 let state='empty',label='모델 미선택',hint='모델 설정에서 사용할 모델을 고르세요.';
 if(raw){state='unverified';label='연결 확인 필요';hint='모델은 선택됐습니다. 실행 가능 여부는 별도로 확인합니다.'}
 if(raw&&c?.state==='blocked'){state='blocked';label='현재 사용 불가';hint='모델 설정의 사용 조건을 확인하세요.'}
 else if(raw&&c?.can_prepare){state='preparable';label=c.mode==='contract-fake'?'테스트 준비 가능':'입력·견적 준비 가능';hint=c.mode==='contract-fake'?'실제 AI 호출 없이 테스트합니다.':'작업별 입력·비용을 확인한 뒤 승인합니다.'}
 return {role,raw,name:names[raw]||raw||'선택하지 않음',state,label,hint};
}
function productionOverviewMarkup(p,name){
 const rows=['image','video'].map(role=>{const m=productionModelView(p,role);return `<div class="production-model" data-readiness="${m.state}"><div class="production-role">${role==='image'?'이미지':'영상'}</div><div class="production-model-copy"><span class="production-model-name">${esc(m.name)}</span><span class="production-readiness">${esc(m.label)}</span></div></div>`}).join('');
 return `<div class="production-context"><span>현재 장면</span><b>${esc(name||'선택한 장면 없음')}</b></div><div class="production-models">${rows}</div><p class="production-guidance">모델 선택은 실행 승인이 아닙니다. 제작 준비에서 입력과 예상 비용을 확인하세요.</p>`;
}
function initializeProductionPresentation(){
 document.body.classList.add('lt-finish');
 const inspector=document.querySelector('.inspector');if(!inspector)return;
 let tools=document.getElementById('productionTools');
 if(!tools){tools=document.createElement('details');tools.id='productionTools';tools.className='production-tools';tools.innerHTML='<summary>제작 도구 <span>미디어·참고·모델</span></summary>';const comments=document.getElementById('comments')?.closest('.lt-inspector-detail');inspector.insertBefore(tools,comments||null)}
 // Move the existing nodes, retaining inputs, IDs, listeners and scoped drafts.
 for(const id of ['upload','mediaConnections','executionCards','imageConnection','generationGateText','referenceVersions']){
  const node=document.getElementById(id);const d=node?.closest('.lt-inspector-detail')||node?.closest('details');
  if(d&&d!==tools&&!d.contains(tools))tools.append(d);
 }
 const prod=document.getElementById('mediaConnections')?.closest('.lt-inspector-detail');
 if(prod){prod.classList.add('production-card');prod.querySelector(':scope>summary').textContent='장면 제작';prod.open=true;
  const oldImage=document.getElementById('imageConnection')?.closest('.lt-inspector-detail'),oldVideo=document.getElementById('generationGateText')?.closest('.lt-inspector-detail');
  let history=document.getElementById('productionPrevious');if(!history){history=document.createElement('details');history.id='productionPrevious';history.innerHTML='<summary>이전 제작 경로·작업</summary>';prod.append(history)}
  for(const d of [oldImage,oldVideo])if(d&&d!==prod){d.classList.add('production-previous-path');history.append(d)}
  const old=document.getElementById('imageConnection');if(old)old.hidden=true;
  // The corrected media_connections summary is authoritative. Keep old diagnostics
  // and recovery controls in their existing containers; do not erase backend facts.
  if(!document.getElementById('productionModelsButton')){const b=document.createElement('button');b.id='productionModelsButton';b.type='button';b.className='production-model-button';b.textContent='모델 선택 확인';b.onclick=()=>document.getElementById('editModelSettings').click();document.getElementById('mediaConnections').after(b)}
 }
 syncProductionPresentation();
}
function syncProductionPresentation(){
 const tools=document.getElementById('productionTools');if(!tools)return;
 const p=project(),sh=p?.shots[shotName],cards=(p?.media_actions||[]).filter(x=>x.shot===shotName);
 // Pending approvals, running work and failures are discoverable even when the
 // user previously collapsed tools. This only changes disclosure, not permission.
 const attention=cards.some(x=>!x.job||!['imported','cancelled'].includes(x.job.state));
 const legacy=(state?.generation_jobs||[]).filter(j=>j.context?.song===song()&&j.context?.shot===shotName&&j.context?.dispatch!=='fal-model-queue-v1');
 const legacyAttention=legacy.some(j=>!['imported','cancelled'].includes(j.state));
 if(sh&&!sh.selected||attention||legacyAttention){tools.open=true;tools.dataset.autoOpen='true'}
 else if(tools.dataset.autoOpen){tools.open=false;delete tools.dataset.autoOpen}
 const history=document.getElementById('productionPrevious');if(history&&legacyAttention){history.open=true;for(const d of history.querySelectorAll('.lt-inspector-detail'))d.open=true}
 const summary=tools.querySelector(':scope>summary span');if(summary)summary.textContent=attention||legacyAttention?'진행·확인할 작업 있음':'미디어·참고·모델';
}
