/* A review only records the user's assessment; billing and reservations remain unchanged. */
(() => {
 'use strict';
 function mount({container, context}) {
  let serial=0, items=[], cursor=null, current=null, busy=false, message='', selected=null;
  const el=(tag,text)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node};
  const scope=()=>{const c=context();return c&&c.workspace&&c.projectId&&c.token?{workspace:c.workspace,projectId:c.projectId,token:c.token}:null};
  const same=(a,b)=>!!a&&!!b&&a.workspace===b.workspace&&a.projectId===b.projectId&&a.token===b.token;
  const base=c=>`/v1/workspaces/${encodeURIComponent(c.workspace)}/billing/late-observations`;
  const query=c=>`projectId=${encodeURIComponent(c.projectId)}`;
  const stateLabel=x=>({unreviewed:'확인 전',reviewed_pending_billing:'확인함 · 청구 확인 대기',conflicting_evidence:'내용 불일치 · 확인 필요'})[x]||'확인 필요';
  const kindLabel=x=>x==='generation_receipt'?'생성 요청 접수 관측':x==='chat_usage'?'대화 사용량 관측':'공급자 응답 관측';
  function date(value){const d=new Date(Number(value)*1000);return Number.isFinite(d.getTime())?d.toLocaleString('ko-KR'):'시간 확인 필요'}
  function safeCurrent(c,n){return n===serial&&same(c,scope())&&same(c,current)}
  async function get(url,c,options={}){
   const headers={Authorization:'Bearer '+c.token,...options.headers};
   const response=await fetch(url,{...options,headers});let body={};try{body=await response.json()}catch{}
   if(!response.ok){const e=new Error(body.message||'요청을 처리하지 못했습니다.');e.status=response.status;throw e}return body;
  }
  function render(focusId=null){
   let focusTarget=null;container.replaceChildren();container.hidden=!message&&!items.length&&!cursor&&!busy;
   if(container.hidden)return;
   const section=el('section');section.setAttribute('aria-label','확인할 공급자 응답');
   section.append(el('h3','확인할 공급자 응답'));
   section.append(el('p','늦게 도착한 응답의 확인 기록입니다. 확인만으로 실제 청구 금액이나 보류된 예산은 바뀌지 않습니다.'));
   const status=el('p',message||(busy?'불러오는 중입니다.':''));status.setAttribute('role','status');status.setAttribute('aria-live','polite');section.append(status);
   for(const item of items){
    const details=el('details');details.open=selected?.id===item.id;
    details.addEventListener('toggle',()=>{if(details.open&&!busy&&selected?.id!==item.id)openItem(item.id)});
    const summary=el('summary',`${kindLabel(item.kind)} · ${stateLabel(item.reviewState)} · ${date(item.observedAt)}`);details.append(summary);if(item.id===focusId)focusTarget=summary;
    if(details.open&&selected?.id===item.id){
     if(selected.error)details.append(el('p',selected.error));
     else if(selected.data){
      const v=selected.data,e=v.evidence||{};
      details.append(el('p',e.receiptObserved?'접수 정보가 관측됐습니다. 이 관측만으로 실제 청구를 확정할 수 없습니다.':'접수 정보가 확인되지 않았습니다. 실제 청구는 별도 확인이 필요합니다.'));
      if(v.reservationState==='uncertain')details.append(el('p','이 작업의 비용은 확인 중이며 예산에서 보류 중입니다.'));
      if(v.attemptState==='unknown')details.append(el('p','요청 결과를 확정하지 못했습니다. 자동으로 다시 요청하지 않습니다.'));
      if(e.usageStatuses){const statuses=Object.entries(e.usageStatuses).filter(([name])=>name!=='service_tier').map(([,value])=>value);details.append(el('p',statuses.includes('valid')?'사용량 응답의 일부가 관측되었습니다. 최종 청구 금액은 별도 확인이 필요합니다.':'유효한 사용량 정보가 확인되지 않았습니다.'))}
      details.append(el('p','이 기록의 내용만 확인합니다. 공급자에게 다시 요청하거나 작업을 재시작하지 않습니다.'));
      if(v.reviewState!=='reviewed_pending_billing'){
       const confirm=el('button','확인함 · 청구 확인 대기');confirm.type='button';confirm.disabled=busy;
       confirm.addEventListener('click',()=>review(v,'reviewed_pending_billing'));
       details.append(confirm);
      }else details.append(el('p','확인 기록이 저장되어 있습니다. 청구 확인은 아직 필요합니다.'));
     }else details.append(el('p','상세 내용을 불러오는 중입니다.'));
    }
    section.append(details);
   }
   if(cursor){const more=el('button','다음 항목 보기');more.type='button';more.disabled=busy;more.addEventListener('click',()=>load(true));section.append(more)}
   if(message&&!busy){const retry=el('button','상태 다시 확인');retry.type='button';retry.addEventListener('click',()=>refresh());section.append(retry)}
   container.append(section);focusTarget?.focus();
  }
  async function load(append=false){
   const c=scope(),n=++serial;if(!c){current=null;items=[];cursor=null;selected=null;busy=false;message='';render();return}
   if(!append||!same(c,current)){items=[];cursor=null;selected=null}current=c;busy=true;message='';render();
   const path=base(c)+'?'+query(c)+'&limit=20'+(append&&cursor?'&cursor='+encodeURIComponent(cursor):'');
   try{const data=await get(path,c);if(!safeCurrent(c,n))return;
    if(!Array.isArray(data.items)||!(data.nextCursor===null||typeof data.nextCursor==='string'))throw Error('invalid response');
    items=append?items.concat(data.items):data.items;cursor=data.nextCursor;
   }catch(e){if(!safeCurrent(c,n))return;message='확인 항목을 불러오지 못했습니다. 상태를 다시 확인하세요.'}
   finally{if(safeCurrent(c,n)){busy=false;render()}}
  }
  async function openItem(id){
   const c=scope();if(!same(c,current)||busy)return;const n=++serial;selected={id};busy=true;message='';render(id);
   try{const data=await get(base(c)+'/'+encodeURIComponent(id)+'?'+query(c),c);if(!safeCurrent(c,n))return;
    if(data.id!==id||typeof data.evidenceDigest!=='string'||!Number.isInteger(data.revision))throw Error('invalid response');selected={id,data};
   }catch(e){if(!safeCurrent(c,n))return;selected={id,error:'상세 내용을 불러오지 못했습니다. 상태를 다시 확인하세요.'}}
   finally{if(safeCurrent(c,n)){busy=false;render(id)}}
  }
  async function review(data,decision){
   const c=scope();if(busy||!same(c,current)||selected?.data!==data)return;
   if(!globalThis.crypto?.randomUUID){message='안전한 요청 식별자를 만들 수 없어 확인 기록을 저장하지 못했습니다.';render();return}
   const n=++serial;busy=true;message='';render(data.id);
   try{const result=await get(base(c)+'/'+encodeURIComponent(data.id)+'/reviews?'+query(c),c,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({decision,evidenceDigest:data.evidenceDigest,revision:data.revision})});
    if(!safeCurrent(c,n))return;
    if(result.id!==data.id||result.reviewState!==decision||result.revision!==data.revision+1)throw Error('invalid review response');
    selected=null;message='확인 기록을 저장했습니다. 실제 청구와 예산 보류는 별도로 확인해야 합니다.';
    const item=items.find(x=>x.id===data.id);if(item){item.reviewState=decision;item.revision=data.revision+1}
   }catch(e){if(!safeCurrent(c,n))return;selected=null;message=e.status===412?'다른 화면에서 기록이 바뀌었습니다. 상태를 다시 확인하세요.':'저장 결과를 확인하지 못했습니다. 다시 시도하기 전에 상태를 다시 확인하세요.'}
   finally{if(safeCurrent(c,n)){busy=false;render(data.id)}}
  }
  function refresh(){return load(false)}
  render();return {refresh};
 }
 window.LoretuneLateEvidence={mount};
})();
