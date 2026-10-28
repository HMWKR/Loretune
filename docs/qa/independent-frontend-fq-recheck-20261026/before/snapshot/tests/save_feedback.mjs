import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const html=fs.readFileSync('index.html','utf8');const css=fs.readFileSync('studio.css','utf8');
const extract=(start,end)=>html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{disabled:false,hidden:false,dataset:{},textContent:'검토 변경 저장',hasAttribute:()=>false,focus(){},setAttribute(){}});return nodes.get(id)};
let pending='r1',calls=[],refreshFail=false,cleared=[];
const context=vm.createContext({console,Map,Set,Error,encodeURIComponent,document:{querySelectorAll:()=>[],querySelector:s=>node(s),getElementById:()=>null},$:node,state:{token:'synthetic'},busy:false,pendingId:()=>pending,clearPending:()=>{pending=null},refresh:async()=>{if(refreshFail)throw Error('refresh')},message:()=>{},drawModelChat:()=>{},renderTakeReview:()=>{},productionReviewErrors:new Map(),takeReviewStore:{clearRevision:(key,rev)=>cleared.push([key,rev])},fetch:async()=>{throw Error('unconfigured')}});
vm.runInContext(extract('async function sendRequest(', 'async function act(')+extract('async function reconcilePendingRequest()',"$('#recoverRequest').onclick=")+extract('function reviewSaveFeedback(', 'function renderProductionReviewFeedback('),context);
async function attempt(response){pending='r1';let outcomes=[];context.fetch=async()=>{if(response instanceof Error)throw response;return response};const ok=await context.sendRequest({request_id:'r1',action:'review_take'},undefined,x=>outcomes.push(x));return {ok,outcomes}}
let x=await attempt({ok:false,status:400,json:async()=>({error:'invalid input'})});assert.equal(x.outcomes[0].status,'rejected');assert.equal(pending,null);
x=await attempt({ok:false,status:403,json:async()=>({error:'expired'})});assert.equal(x.outcomes[0].httpStatus,403);
x=await attempt(new Error('lost response'));assert.equal(x.outcomes[0].status,'unknown');assert.equal(pending,'r1');
x=await attempt({ok:false,status:503,json:async()=>({error:'unavailable'})});assert.equal(x.outcomes[0].status,'unknown');assert.equal(pending,'r1');
x=await attempt({ok:true,status:200,json:async()=>{throw Error('truncated')}});assert.equal(x.outcomes[0].status,'unknown');
refreshFail=true;x=await attempt({ok:true,status:200,json:async()=>({})});assert.equal(x.outcomes.at(-1).status,'committed_refresh_failed');assert.equal(pending,null);refreshFail=false;
pending='r1';context.productionReviewErrors.set('scene-A',{status:'unknown',requestId:'r1',draftRevision:3});context.productionReviewErrors.set('scene-B',{status:'unknown',requestId:'r2',draftRevision:8});
context.fetch=async(url,options)=>{calls.push({url,options});return {ok:false,status:404,json:async()=>({status:'unknown'})}};
await context.reconcilePendingRequest();assert.equal(calls.length,1);assert.equal(calls[0].options,undefined);assert.equal(pending,'r1');assert.equal(context.productionReviewErrors.get('scene-A').status,'unknown_checked');
context.fetch=async()=>({ok:true,status:200,json:async()=>({status:'committed'})});await context.reconcilePendingRequest();assert.deepEqual(cleared,[['scene-A',3]]);assert.equal(context.productionReviewErrors.get('scene-B').status,'unknown');assert.equal(pending,null);
assert.match(context.reviewSaveFeedback({status:'rejected',httpStatus:400},'검토 변경 저장'),/입력은 보존.*검토 변경 저장/);
assert.match(context.reviewSaveFeedback({status:'unknown'},'저장'),/확인되지.*기존 저장 확인/);assert.doesNotMatch(context.reviewSaveFeedback({status:'unknown'},'저장'),/실패|다시 제출/);
for(const status of ['unknown','unknown_checked']){
 const before=pending,message=context.reviewSaveFeedback({status},'저장');
 assert.match(message,/입력은 보존.*기존 저장 확인.*같은 요청.*확인 전에는 새로 제출하지 않습니다/);
 assert.doesNotMatch(message,/연결이|네트워크|서버 장애|실패|다시 제출/);
 assert.equal(pending,before);
}
assert.match(html,/button.disabled=!!busy\|\|!!pendingId\(\)/);assert.match(html,/clearRevision\(key,value.draftRevision\)/);
assert.match(css,/creator-source\[open\]>summary::before/);assert.match(css,/creator-source>summary:focus-visible/);assert.doesNotMatch(html,/상단 알림에서 저장 상태를 확인하세요/);
pending='r3';refreshFail=true;context.productionReviewErrors.set('scene-C',{status:'unknown',requestId:'r3',draftRevision:4});
context.fetch=async()=>({ok:true,status:200,json:async()=>({status:'committed'})});await context.reconcilePendingRequest();assert.equal(context.productionReviewErrors.get('scene-C').status,'committed_refresh_failed');assert.equal(pending,null);refreshFail=false;
console.log('13 checks passed');
