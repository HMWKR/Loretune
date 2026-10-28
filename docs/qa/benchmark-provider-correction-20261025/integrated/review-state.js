/* Scoped review drafts. No provider calls; existing act() owns writes/recovery. */
function createTakeReviewStore(storage) {
 const cache=new Map(); let failed=false;
 return {
  get failed(){return failed},
  get(key){
   if(!key)return null;
   if(cache.has(key))return cache.get(key);
   let value=null;
   try{const x=JSON.parse(storage.getItem(key)||'null');if(x&&typeof x.reason==='string'&&['','approved','rejected','changes_requested'].includes(x.decision)&&Number.isSafeInteger(x.revision))value=x}catch{failed=true}
   cache.set(key,value);return value;
  },
  set(key,value){const next={decision:value.decision,reason:value.reason,revision:(this.get(key)?.revision||0)+1};cache.set(key,next);try{storage.setItem(key,JSON.stringify(next))}catch{failed=true}return next},
  clear(key){cache.set(key,null);try{storage.removeItem(key)}catch{failed=true}},
  clearRevision(key,revision){if(this.get(key)?.revision===revision)this.clear(key)}
 };
}
function takeReviewKey(workspace,name,shot,take){return 'loretune-take-review-v1:'+JSON.stringify([workspace,name,shot,take])}
function createTakeReviewController({store,context,inputs,save,render,notify}) {
 const pending=new Set();
 return {
  pending,
  capture(){const c=context();if(c)store.set(c.key,inputs());render()},
  async submit(){
   const c=context();if(!c)return notify('Take를 먼저 선택하세요.',true);
   if(pending.has(c.key))return false;
   const value=inputs();
   if(!['approved','rejected','changes_requested'].includes(value.decision))return notify('이번에 기록할 검토 결정을 선택하세요.',true);
   if(!value.reason.trim())return notify('검토 이유를 입력하세요.',true);
   if(c.review?.decision===value.decision&&c.review?.reason===value.reason)return notify('이미 저장된 검토입니다. 변경할 내용이 있으면 먼저 수정하세요.');
   const submitted=store.set(c.key,value);pending.add(c.key);render();
   try{
    const ok=await save('review_take',{song:c.song,shot:c.shot,take:c.take,decision:value.decision,reason:value.reason});
    if(ok)store.clearRevision(c.key,submitted.revision);
    return ok;
   }finally{pending.delete(c.key);render()}
  }
 };
}
// DOM glue. IDs and backend payload/approval contracts remain unchanged.
const takeReviewStore=createTakeReviewStore(sessionStorage);
let takeReviewScope='';
function studioReview(s,id){const review=[...(s?.reviews||[])].reverse().find(r=>r.take===id);const labels={approved:'Take 승인됨',rejected:'Take 거절',changes_requested:'Take 수정 요청'};return {review,decision:review?.decision||'pending',label:labels[review?.decision]||'Take 검토 대기'}}
function currentTakeReview(){const p=project(),s=p?.shots[shotName],take=s?.selected;if(!take||!s.takes.some(t=>t.id===take))return null;return {key:takeReviewKey(state.workspace_id,song(),shotName,take),song:song(),shot:shotName,take,review:studioReview(s,take).review}}
function studioBadge(s,id){const r=studioReview(s,id);return `<span class="lt-review-state" data-review="${esc(r.decision)}">${esc(r.label)}</span>`}
function studioAdopted(p,name,id){const timeline=draft||(p.timeline_head?p.timeline_versions[p.timeline_head-1]:null);return !!timeline?.clips.some(c=>c.shot===name&&c.take===id)}
function studioUseLabel(p,name,id){return studioAdopted(p,name,id)?(dirty?'미저장 편집에 사용':'편집에 사용'):''}
function renderStudioShots(p){return Object.entries(p.shots).map(([name,s],i)=>{const t=s.takes.find(t=>t.id===s.selected);return `<button class="shot ${name===shotName?'active':''}" data-shot="${esc(name)}" aria-pressed="${name===shotName}">${t&&image(t)?`<img class="thumb" src="${asset(t)}" alt="">`:`<span class="thumb lt-media-kind">${t?'영상':'미연결'}</span>`}<span class="lt-scene-copy"><b>${String(i+1).padStart(2,'0')} ${esc(name)}</b><small>${s.takes.length}개 · ${t?'선택 Take '+t.id:'선택 없음'}</small>${t?studioBadge(s,t.id):'<small>미디어를 연결하세요</small>'}</span></button>`}).join('')}
function renderStudioTakes(s){const p=project();return s?s.takes.map(t=>`<button data-take="${t.id}" class="${s.selected===t.id?'active':''}" aria-pressed="${s.selected===t.id}">${image(t)?`<img src="${asset(t)}" alt="">`:'<span class="lt-take-kind">영상</span>'}<span class="lt-take-copy"><b>Take ${t.id}</b><small>${s.selected===t.id?'현재 선택':'선택하기'}${studioAdopted(p,shotName,t.id)?' · '+studioUseLabel(p,shotName,t.id):''}</small>${studioBadge(s,t.id)}</span></button>`).join(''):''}
function renderStudioTrack(p){return draft.clips.map(c=>`<span class="lt-track-clip" data-current="${c.shot===shotName&&c.take===p.shots[shotName]?.selected}" style="flex:${Math.max(c.duration,.125)}" title="${esc(c.shot)}"><b>${esc(c.shot)}</b><small>Take ${c.take??'미선택'} · ${c.duration}초${c.shot===shotName&&c.take===p.shots[shotName]?.selected?' · 미리보기 중':''}</small>${c.take?studioBadge(p.shots[c.shot],c.take):'<small>Take 선택 필요</small>'}</span>`).join('')}
function ensureStudioReviewDOM(){
 document.body.classList.add('lt-studio-states');
 const reason=document.querySelector('#reason');
 if(!document.querySelector('#takeReviewStatus')){const box=document.createElement('div');box.id='takeReviewStatus';reason.before(box)}
 const decision=document.querySelector('#takeDecision');
 if(!decision.querySelector('option[value=""]')){const option=document.createElement('option');option.value='';option.textContent='검토 결정 선택';decision.prepend(option)}
 decision.setAttribute('aria-label','이번에 기록할 검토 결정');
 if(!document.querySelector('label[for="takeDecision"]')){const label=document.createElement('label');label.htmlFor='takeDecision';label.textContent='이번에 기록할 검토 결정';decision.before(label)}
 let input=document.querySelector('#reviewReason');if(input.tagName==='INPUT'){const area=document.createElement('textarea');area.id=input.id;area.value=input.value;area.rows=3;input.replaceWith(area);input=area}input.placeholder='이 Take의 검토 이유를 입력하세요';input.maxLength=2000;
 input.setAttribute('aria-describedby','takeReviewDraftState');decision.setAttribute('aria-describedby','takeReviewDraftState');
 if(!document.querySelector('#takeReviewDraftState')){const hint=document.createElement('p');hint.id='takeReviewDraftState';hint.setAttribute('role','status');const discard=document.createElement('button');discard.id='discardTakeReviewDraft';discard.type='button';discard.textContent='미저장 검토 초안 지우기';document.querySelector('#reviewTake').after(hint,discard);discard.onclick=()=>{const c=currentTakeReview();if(c){takeReviewStore.clear(c.key);takeReviewScope='';renderTakeReview()}}}
}
function renderTakeReview(){
 if(!document.querySelector('#takeReviewStatus'))return;
 const c=currentTakeReview(),local=c?takeReviewStore.get(c.key):null;
 const reason=document.querySelector('#reviewReason'),decision=document.querySelector('#takeDecision'),button=document.querySelector('#reviewTake');
 if(takeReviewScope!==(c?.key||'')||!local){const value=local||{decision:c?.review?.decision||'',reason:c?.review?.reason||''};reason.value=value.reason;decision.value=value.decision;takeReviewScope=c?.key||''}
 const s=project()?.shots[shotName];
 document.querySelector('#takeReviewStatus').innerHTML=c?`<b>Take ${c.take}</b>${studioBadge(s,c.take)}<small>${esc(studioUseLabel(project(),c.shot,c.take)||'편집에 미사용')} · 출력 승인과 별도</small>`:'<p>Take를 선택하면 검토할 수 있습니다.</p>';
 const section=button.closest('section');if(section?.querySelector('h2'))section.querySelector('h2').textContent=c?`Take ${c.take} 검토`:'Take 검토';
 const unchanged=c?.review?.decision===decision.value&&c?.review?.reason===reason.value;
 button.textContent=c?`Take ${c.take} ${c.review?'검토 변경 기록':'검토 기록'}`:'Take 검토 기록';
 button.disabled=!!busy||!c||!decision.value||!reason.value.trim()||unchanged||takeReviewController.pending.has(c?.key);
 reason.disabled=decision.disabled=!c;
 document.querySelector('#takeReviewDraftState').textContent=!c?'선택과 검토 승인은 별개입니다.':takeReviewStore.failed?'초안을 이 탭 메모리에만 보존 중입니다. 브라우저 저장소를 확인하세요.':local?'이 Take의 미저장 검토 초안 · 다른 Take와 분리해 보존됩니다.':c.review?'저장된 검토입니다. 변경할 결정이나 이유를 수정하세요.':'결정과 이유를 입력한 뒤 검토를 기록하세요.';
 document.querySelector('#discardTakeReviewDraft').disabled=!local||takeReviewController.pending.has(c?.key);
}
const takeReviewController=createTakeReviewController({store:takeReviewStore,context:currentTakeReview,inputs:()=>({decision:document.querySelector('#takeDecision').value,reason:document.querySelector('#reviewReason').value}),save:(action,data)=>act(action,data),render:renderTakeReview,notify:(text,error)=>message(text,error)});
function openStudioComparison(){
 const sh=project()?.shots[shotName];
 if(!sh?.takes.length)return message('비교할 Take가 없습니다. 기존 미디어를 먼저 연결하세요.',true);
 if(sh.takes.length<2)return message('비교하려면 같은 장면에 Take가 2개 이상 필요합니다. 현재 Take는 그대로 유지됩니다.');
 for(const side of ['Left','Right'])$('#compare'+side).innerHTML=sh.takes.map(t=>`<option value="${t.id}">Take ${t.id} · ${esc(studioReview(sh,t.id).label)}</option>`).join('');
 $('#compareLeft').value=sh.selected||sh.takes[0].id;
 $('#compareRight').value=sh.takes.filter(t=>String(t.id)!==$('#compareLeft').value).at(-1).id;
 drawComparison();$('#compareDialog').showModal();
}
function installStudioNotice(notice,detail,summary){
 const baseline='로컬 저장소 연결됨 · 선택과 승인을 분리해 안전하게 제작하세요.';
 let userOpen=false;
 summary.addEventListener('click',()=>{userOpen=!detail.open});
 const update=()=>{const value=notice.textContent.trim(),routine=!notice.classList.contains('error')&&[baseline,'저장했습니다.','저장 중…',''].includes(value);summary.textContent=routine?(value===baseline?'로컬 연결됨':value==='저장했습니다.'?'저장됨':value||'저장 상태'):'알림';detail.open=routine?userOpen:true;};
 new MutationObserver(update).observe(notice,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});update();
}
ensureStudioReviewDOM();
document.querySelector('#reviewReason').addEventListener('input',()=>takeReviewController.capture());
document.querySelector('#takeDecision').addEventListener('change',()=>takeReviewController.capture());

