'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
class Node {
 constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.textContent='';this.hidden=false;this.open=false;this.disabled=false;this.attributes={}}
 append(...nodes){this.children.push(...nodes)}
 replaceChildren(...nodes){this.children=nodes}
 setAttribute(k,v){this.attributes[k]=v}
 focus(){this.focused=true}
 async fire(name){for(const f of this.listeners[name]||[])await f({target:this})}
 addEventListener(name,f){(this.listeners[name]??=[]).push(f)}
}
const all=(node,tag)=>[...(node.tag===tag?[node]:[]),...node.children.flatMap(x=>all(x,tag))];
const body=node=>[node.textContent,...node.children.map(body)].join(' ');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const row={id:1,kind:'chat_usage',observedAt:1790000000,reviewState:'unreviewed',revision:0,attemptState:'unknown',reservationState:'uncertain'};
async function main(){
 let scope={workspace:'w',projectId:'p',token:'secret'},requests=[],mode='normal',resolveDeferred;
 const root=new Node('div');let c;
 const fetch=async(url,options)=>{requests.push({url,options});
  if(mode==='defer')return new Promise(resolve=>{resolveDeferred=resolve});
  if(mode==='defer-post'&&options.method==='POST')return new Promise(resolve=>{resolveDeferred=resolve});
  if(mode==='network'&&options.method==='POST')throw Error('connection lost');
  if(mode==='failure')return {ok:false,status:403,json:async()=>({message:'no'})};
  if(mode==='stale'&&options.method==='POST')return {ok:false,status:412,json:async()=>({message:'stale'})};
  if(options.method==='POST'){
   if(['malformed','mismatch-id','mismatch-decision','mismatch-revision'].includes(mode)){
    row.reviewState='reviewed_pending_billing';row.revision=1;
    if(mode==='malformed')return {ok:true,json:async()=>{throw Error('truncated')}};
    return {ok:true,json:async()=>({id:mode==='mismatch-id'?2:1,reviewState:mode==='mismatch-decision'?'conflicting_evidence':'reviewed_pending_billing',revision:mode==='mismatch-revision'?2:1})};
   }
   return {ok:true,json:async()=>({id:1,reviewState:'reviewed_pending_billing',revision:1})};
  }
  if(url.includes('/1?'))return {ok:true,json:async()=>({...row,evidenceDigest:'a'.repeat(64),evidence:{receiptObserved:true,usageStatuses:{input_tokens:'valid'}}})};
  return {ok:true,json:async()=>({items:mode==='empty'?[]:[{...row}],nextCursor:mode==='pages'?'1':null})};
 };
 c={window:{},document:{createElement:tag=>new Node(tag)},fetch,crypto:{randomUUID:()=> 'valid-idempotency-key'},Date,Number,Array,Object,Error,encodeURIComponent};c.globalThis=c;vm.createContext(c);vm.runInContext(fs.readFileSync('late-evidence-ui.js','utf8'),c);
 const ui=c.window.LoretuneLateEvidence.mount({container:root,context:()=>scope});assert(root.hidden);
 mode='empty';await ui.refresh();assert(root.hidden,'empty state hidden');
 mode='normal';await ui.refresh();assert(!root.hidden);assert.match(body(root),/실제 청구 금액이나 보류된 예산은 바뀌지 않습니다/);assert(!body(root).includes('unknown'));
 let detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();assert.match(body(root),/접수 정보가 관측/);assert.match(body(root),/최종 청구 금액은 별도 확인/);
 let button=all(root,'button').find(x=>x.textContent==='확인함 · 청구 확인 대기');await button.fire('click');await tick();const post=requests.find(x=>x.options.method==='POST');assert(post);assert.equal(post.options.headers['Idempotency-Key'],'valid-idempotency-key');assert.deepEqual(JSON.parse(post.options.body),{decision:'reviewed_pending_billing',evidenceDigest:'a'.repeat(64),revision:0});assert.match(body(root),/실제 청구와 예산 보류는 별도로/);
 mode='defer-post';await ui.refresh();detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();button=all(root,'button').find(x=>x.textContent==='확인함 · 청구 확인 대기');const postCount=requests.filter(x=>x.options.method==='POST').length;const waiting=button.fire('click');await tick();await button.fire('click');assert.equal(requests.filter(x=>x.options.method==='POST').length,postCount+1,'in-flight double click must not send twice');resolveDeferred({ok:true,json:async()=>({id:1,reviewState:'reviewed_pending_billing',revision:1})});await waiting;
 mode='stale';await ui.refresh();detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();button=all(root,'button').find(x=>x.textContent==='확인함 · 청구 확인 대기');await button.fire('click');await tick();assert.match(body(root),/다른 화면에서 기록이 바뀌었습니다/);assert(!all(root,'button').some(x=>x.textContent==='확인함 · 청구 확인 대기'));
 mode='network';await ui.refresh();detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();button=all(root,'button').find(x=>x.textContent==='확인함 · 청구 확인 대기');await button.fire('click');await tick();assert.match(body(root),/저장 결과를 확인하지 못했습니다/);assert(!all(root,'button').some(x=>x.textContent==='확인함 · 청구 확인 대기'));
 for(const invalid of ['malformed','mismatch-id','mismatch-decision','mismatch-revision']){
  row.reviewState='unreviewed';row.revision=0;mode=invalid;await ui.refresh();detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();button=all(root,'button').find(x=>x.textContent==='확인함 · 청구 확인 대기');await button.fire('click');await tick();
  assert.match(body(root),/저장 결과를 확인하지 못했습니다/,invalid);assert(!body(root).includes('확인 기록을 저장했습니다'),invalid);assert(!body(root).includes('확인함 · 청구 확인 대기'),invalid);
  const before=requests.length;mode='normal';button=all(root,'button').find(x=>x.textContent==='상태 다시 확인');await button.fire('click');await tick();assert.equal(requests.length,before+1,invalid+' refresh fetch');assert.match(body(root),/확인함 · 청구 확인 대기/,invalid+' authoritative state');
 }
 mode='normal';await ui.refresh();detail=all(root,'details')[0];detail.open=true;await detail.fire('toggle');await tick();assert.match(body(root),/확인 기록이 저장되어 있습니다/);assert(!all(root,'button').some(x=>x.textContent==='확인함 · 청구 확인 대기'),'reviewed item must not offer duplicate confirmation');
 row.reviewState='unreviewed';row.revision=0;
 mode='failure';await ui.refresh();assert.match(body(root),/불러오지 못했습니다/);assert(!root.hidden);
 mode='pages';await ui.refresh();button=all(root,'button').find(x=>x.textContent==='다음 항목 보기');assert(button);await button.fire('click');await tick();assert(requests.at(-1).url.includes('cursor=1'));
 mode='defer';const pending=ui.refresh();await tick();scope={workspace:'w',projectId:'other',token:'secret'};resolveDeferred({ok:true,json:async()=>({items:[row],nextCursor:null})});await pending;assert(!body(root).includes('대화 사용량 관측'),'old project chat row must not render after scope switch');assert.equal(all(root,'details').length,0,'old project detail must not render after scope switch');
 mode='empty';await ui.refresh();assert(root.hidden);assert(requests.at(-1).url.includes('projectId=other'));
 console.log('late evidence UI state, scope, approval, conflict and paging checks passed');
}
main().catch(e=>{console.error(e);process.exitCode=1});
