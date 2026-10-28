'use strict';
// Exact production handlers/controller; synthetic DOM, storage and delayed HTTP doubles.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.env.LORETUNE_TEST_HTML||'index.html','utf8');
const line=prefix=>html.split('\n').find(x=>x.startsWith(prefix));
const slice=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const response=(body={},status=200)=>({ok:status<400,status,json:async()=>body});
const results=[];
async function test(name,run){try{await run();results.push({name,status:'PASS'})}catch(e){results.push({name,status:'FAIL',error:e.message})}}
function fixture(id){
 const nodes=new Map(),storage=new Map(),requests=[],pending=[];let sequence=0;
 function node(){return {hidden:false,disabled:false,textContent:'',dataset:{},handlers:{},data:{},resets:0,
  hasAttribute(){return false},focus(){},addEventListener(type,fn){(this.handlers[type]??=[]).push(fn)},
  dispatch(type){for(const fn of this.handlers[type]||[])fn({target:this})},
  reset(){this.dispatch('reset');this.data={};this.resets++}}}
 const $=selector=>{if(!nodes.has(selector))nodes.set(selector,node());return nodes.get(selector)};
 const state={revision:1,workspace_id:'synthetic-workspace',project_ids:{A:'p-a',B:'p-b'},projects:{A:{ip:'ip-a'},B:{ip:'ip-b'}},capabilities:{chat_plan:true}};
 const c={console,Map,Set,WeakMap,JSON,Error,state,stateReadEpoch:0,current:'A',busy:false,dirty:false,pendingRequest:null,activeMutationRequestId:null,
  $,song:()=>c.current,project:()=>c.state.projects[c.current],
  document:{querySelector:$,querySelectorAll:()=>[]},
  FormData:class{constructor(form){this.values=Object.entries(form.data)}get(key){return this.values.find(x=>x[0]===key)?.[1]??null}[Symbol.iterator](){return this.values[Symbol.iterator]()}},
  crypto:{randomUUID:()=>`synthetic-request-${++sequence}`},
  sessionStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},
  requestCache:async()=>{},message(){},drawModelChat(){},renderTakeReview(){},
  localChatKey:()=>`local-${c.current}`,draftWrite:(key,value)=>storage.set(key,value),
  productionReviewErrors:new Map(),takeReviewStore:{clearRevision(){}},refresh:async()=>{},
  fetch:async(url,options)=>{requests.push({url,options});if(!options)return response({status:'unknown'},404);return new Promise((resolve,reject)=>pending.push({resolve,reject}))}};
 vm.createContext(c);
 vm.runInContext([line('function pendingId('),line('function mutationRequestActive('),line('function updateRecovery('),line('function clearPending('),slice('async function sendRequest(',"$('#recoverRequest').onclick=")].join('\n'),c);
 // Absence on the before snapshot is intentional: run the same behavioural assertions red/green.
 if(html.includes('/* Proposal form draft guards */'))vm.runInContext(slice('/* Proposal form draft guards */','/* End proposal form draft guards */'),c);
 vm.runInContext(line("$('#"+id+"').onsubmit="),c);
 const form=$('#'+id),other=$('#'+(id==='chatForm'?'preferenceForm':'chatForm'));
 form.data=id==='chatForm'?{prompt:'원문'}:{scope:'song',category:'color',value:'원문',evidence:'합성 근거',reason:'시험',supersedes:''};
 const key=id==='chatForm'?'prompt':'value';
 function observe(){if(c.proposalFormContext)c.proposalFormContext()}
 observe();c.refresh=async()=>observe();
 return {c,form,other,key,requests,pending,storage,
  input(value,type='input'){form.data[key]=value;form.dispatch(type)},
  context(name){c.current=name;observe()},observe,
  submit:()=>form.onsubmit({target:form,preventDefault(){}}),
  async started(){for(let i=0;pending.length===0&&i<12;i++)await Promise.resolve();assert.equal(pending.length,1)},
  finish(body={},status=200){pending.shift().resolve(response(body,status))},
  assertSingle(){const writes=requests.filter(x=>x.options?.method==='POST');assert.equal(writes.length,1);const sent=JSON.parse(writes[0].options.body);assert.equal(sent.action,id==='chatForm'?'chat_plan':'preference_propose');assert.equal(sent.data.song,'A');assert.equal(sent.data[key],'원문')}};
}

(async()=>{
 for(const id of ['preferenceForm','chatForm']){
  await test(id+' unchanged success clears',async()=>{const f=fixture(id),p=f.submit();await f.started();f.finish();await p;assert.equal(f.form.resets,1);f.assertSingle()});
  for(const mode of ['edit','switch-edit','switch-only','ABA','same-content-intent','identical-input-event','change-event','programmatic','workspace','project-id','IP','conversation']){
   await test(id+' success preserves '+mode,async()=>{
    const f=fixture(id),p=f.submit();await f.started();
    if(mode==='edit')f.input('새 한글 초안 🎬');
    if(mode==='switch-edit'){f.context('B');f.input('B의 초안')}
    if(mode==='switch-only')f.context('B');
    if(mode==='ABA'){f.context('B');f.context('A')}
    if(mode==='same-content-intent'){f.input('변경');f.input('원문')}
    if(mode==='identical-input-event')f.input('원문');
    if(mode==='change-event'){if(id==='preferenceForm')f.form.data.scope='global';f.form.dispatch('change')}
    if(mode==='programmatic')f.form.data[f.key]='프로그램이 복원한 초안';
    if(mode==='workspace')f.c.state.workspace_id='other-workspace';
    if(mode==='project-id')f.c.state.project_ids.A='replacement-project';
    if(mode==='IP')f.c.state.projects.A.ip='other-ip';
    if(mode==='conversation')f.c.state.projects.A.active_conversation={id:'other-session'};
    const expected=JSON.stringify(f.form.data);f.finish();await p;
    assert.equal(JSON.stringify(f.form.data),expected);assert.equal(f.form.resets,0);f.assertSingle();
   });
  }
  await test(id+' rejection preserves new input',async()=>{const f=fixture(id),p=f.submit();await f.started();f.input('거절 후 남을 초안');f.finish({error:'synthetic rejection'},400);await p;assert.equal(f.form.data[f.key],'거절 후 남을 초안');assert.equal(f.form.resets,0);f.assertSingle()});
  await test(id+' unknown preserves and permits lookup only',async()=>{const f=fixture(id),p=f.submit();await f.started();f.input('미확정 초안');f.pending.shift().reject(Error('synthetic lost response'));await p;const requestId=f.c.pendingId();assert.ok(requestId);await f.submit();await f.c.reconcilePendingRequest();assert.equal(f.form.data[f.key],'미확정 초안');assert.equal(f.form.resets,0);f.assertSingle();assert.equal(f.requests.filter(x=>x.url==='/api/requests/'+requestId).length,1)});
  await test(id+' pending duplicate does not submit or clear',async()=>{const f=fixture(id),p=f.submit();await f.started();f.input('두번째 입력');await f.submit();assert.equal(f.form.resets,0);f.finish();await p;assert.equal(f.form.data[f.key],'두번째 입력');f.assertSingle()});
  await test(id+' committed refresh failure preserves',async()=>{const f=fixture(id);f.c.refresh=async()=>{throw Error('synthetic refresh failed')};const p=f.submit();await f.started();f.finish();await p;assert.equal(f.form.data[f.key],'원문');assert.equal(f.form.resets,0);f.assertSingle()});
  await test(id+' edit during committed refresh is preserved',async()=>{const f=fixture(id);let release;f.c.refresh=async()=>new Promise(resolve=>release=resolve);const p=f.submit();await f.started();f.finish();for(let i=0;!release&&i<12;i++)await Promise.resolve();assert.equal(typeof release,'function');f.input('저장 후 갱신 중 새 입력');release();await p;assert.equal(f.form.data[f.key],'저장 후 갱신 중 새 입력');assert.equal(f.form.resets,0);f.assertSingle()});
  await test(id+' unrelated form edits do not block normal clear',async()=>{const f=fixture(id),p=f.submit();await f.started();f.other.data={prompt:'다른 폼 초안'};f.other.dispatch('input');f.finish();await p;assert.equal(f.form.resets,1);assert.equal(f.other.data.prompt,'다른 폼 초안');f.assertSingle()});
  await test(id+' same-context refresh does not invalidate normal clear',async()=>{const f=fixture(id),p=f.submit();await f.started();f.c.state={...f.c.state,revision:2};f.observe();f.observe();f.finish();await p;assert.equal(f.form.resets,1);f.assertSingle()});
 }
 // All accepted project switches pass through draw; observe changes there, including A→B→A.
 await test('context observation is wired to real draw',async()=>{assert.match(line('function draw('),/proposalFormContext\(\)/)});
 console.log(JSON.stringify({evidence:'current-source Node VM with controlled doubles; not browser',results},null,2));
 process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});
