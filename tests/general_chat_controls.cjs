'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8'), ui=fs.readFileSync('general-chat-ui.js','utf8');
const line=(source,prefix)=>source.split('\n').find(line=>line.startsWith(prefix));
const slice=(source,a,b)=>source.slice(source.indexOf(a),source.indexOf(b,source.indexOf(a)));
function fixture(mode,kind){
 const nodes=new Map(),memory=new Map();let requests=0;
 const get=id=>{if(!nodes.has(id))nodes.set(id,{disabled:false,hidden:false,dataset:{},textContent:'',hasAttribute:()=>false,focus(){}});return nodes.get(id)};
 const $=s=>get(s);const prepare=get('generalChatPrepare'),refreshButton=get('generalChatRefresh'),approval=get('approval');
 const capabilities={live:{available:true,mode:'anthropic-live',external_transmission:true},'invalid-live':{available:true,mode:'anthropic-live',external_transmission:false},'invalid-fixture':{available:true,mode:'contract-fake',external_transmission:true},disconnected:{available:false,mode:'disconnected',external_transmission:false}};
 const project={general_chat_connection:capabilities[mode]||{available:true,mode:'contract-fake',external_transmission:false},general_chat_previews:mode==='preview'?[{id:'review'}]:[],general_chat_turns:mode==='unknown'?[{status:'outcome_unknown'}]:[]};
 const c={console,Map,Set,Error,JSON,encodeURIComponent,state:{revision:1,token:'test',projects:{A:project}},stateReadEpoch:0,busy:false,dirty:false,inFlight:false,pendingRequest:null,activeMutationRequestId:null,$,el:get,project:()=>project,panel:{querySelectorAll:()=>[approval]},document:{querySelector:$,querySelectorAll:()=>[prepare,refreshButton,approval]},crypto:{randomUUID:()=> 'id'},sessionStorage:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)},requestCache:async()=>{},message(){},drawModelChat(){},renderTakeReview(){},song:()=> 'A',productionReviewErrors:new Map(),takeReviewStore:{clearRevision(){}},refresh:async()=>{},fetch:async()=>{requests++;if(kind==='network')throw Error('lost');return{ok:kind==='success',status:kind==='success'?200:400,json:async()=>kind==='success'?{}:{error:'invalid'}}}};
 vm.createContext(c);
 vm.runInContext(line(ui,' const allowed=')+'\n'+line(ui,' function controls()')+'\nglobalThis.LoretuneGeneralChat={syncControls:controls};',c);
 vm.runInContext(line(html,'function pendingId(')+'\n'+line(html,'function mutationRequestActive(')+'\n'+line(html,'function updateRecovery(')+'\n'+line(html,'function clearPending(')+'\n'+slice(html,'async function sendRequest(',"$('#recoverRequest').onclick="),c);
 return {c,prepare,refreshButton,approval,memory,requests:()=>requests};
}
(async()=>{
 for(const mode of ['disconnected','preview','unknown','ready','live','invalid-live','invalid-fixture'])for(const outcome of ['success','rejected','network','storage']){
  const f=fixture(mode,outcome);if(outcome==='storage')f.c.requestCache=async()=>{throw Error('storage denied')};
  await f.c.act('comment',{song:'A'});
  assert.equal(f.prepare.disabled,!['ready','live'].includes(mode)||outcome==='network',`${mode}/${outcome}`);
  assert.equal(f.approval.disabled,outcome==='network'||['disconnected','invalid-live','invalid-fixture'].includes(mode),`${mode}/${outcome} approval`);
  assert.equal(f.requests(),outcome==='storage'?0:1,`${mode}/${outcome} requests`);
  if(outcome==='network'){f.memory.delete('loretune-pending');f.c.pendingRequest=null;f.c.updateRecovery();assert.equal(f.prepare.disabled,!['ready','live'].includes(mode),`${mode}/recovery`)}
 }
 const view={};vm.createContext(view);vm.runInContext(line(html,'function usd(amount)'),view);vm.runInContext(line(ui,' const usageLabel=')+'\nglobalThis.usage=usageLabel;',view);assert.equal(view.usage({usage_cost_usd:'0.003687',pricing_status:'priced'}),'사용량 기준 금액 $0.003687','UI-r3 #41: the product usd() formats the usage amount');assert.doesNotMatch(view.usage({usage_cost_usd:null}),/\$0/,'unknown usage must not be displayed as zero');assert.doesNotMatch(view.usage({usage_cost_usd:'0',pricing_status:'insufficient_billing_evidence'}),/\$0/,'an unknown response can retain the initial zero placeholder');assert.match(view.usage({usage_cost_usd:'0',pricing_status:'priced'}),/\$0/,'a recorded zero is still a known value');assert.match(view.usage({usage_cost_usd:'0',message_status:'not_sent'}),/\$0/,'proven non-transmission retains a zero amount');
 for(const [cap,expected] of [[{available:true,mode:'anthropic-live',external_transmission:true},'대화 연결 설정됨'],[{available:true,mode:'contract-fake',external_transmission:false},'테스트 대화'],[{available:true,mode:'anthropic-live',external_transmission:false},'채팅 미연결'],[{available:false,mode:'anthropic-live',external_transmission:true},'채팅 미연결']]){const node={};const c={state:{capabilities:{}},project:()=>({general_chat_connection:cap}),$:()=>node};vm.createContext(c);vm.runInContext(line(html,'function drawProviderBadge(){')+'\ndrawProviderBadge();',c);assert.ok(node.textContent.startsWith(expected),'header must reflect the same connection as the chat controls')}
 console.log('28 general chat button states and unknown/zero cost distinction passed');
})().catch(error=>{console.error(error);process.exitCode=1});
