'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ui=fs.readFileSync(process.argv[2]||'general-chat-ui.js','utf8'),html=fs.readFileSync(process.argv[3]||'index.html','utf8');
const line=(source,prefix)=>source.split('\n').find(value=>value.startsWith(prefix))||'';
function controls(cap,status){
 const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,{disabled:false,dataset:{}});return nodes.get(id)};
 const approve={dataset:{generalDecision:'approve'}},reject={dataset:{generalDecision:'reject'}},cancel={dataset:{generalCancel:'turn'}};
 const c={busy:false,inFlight:false,dirty:false,pendingId:()=>null,el:get,project:()=>({general_chat_connection:cap,general_chat_turns:status?[{status}]:[],general_chat_previews:[]}),panel:{querySelectorAll:()=>[approve,reject,cancel]}};
 vm.createContext(c);vm.runInContext(line(ui,' const allowed=')+'\n'+line(ui,' const configured=')+'\n'+line(ui,' function controls()')+'\ncontrols();globalThis.isConfigured=typeof configured==="function"?configured:()=>false;',c);
 return{prepare:get('generalChatPrepare'),approve,reject,cancel,configured:c.isConfigured(cap)};
}
async function decision(cap,kind){
 const calls=[],nodes=new Map();const get=id=>{if(!nodes.has(id))nodes.set(id,{value:'현재 요청',textContent:'',querySelectorAll:()=>[{dataset:{rights:'preview'},checked:true}]});return nodes.get(id)};
 const c={Number,busy:false,inFlight:false,scope:'A',key:()=> 'A',el:get,song:()=> 'A',project:()=>({general_chat_connection:cap,general_chat_previews:[{id:'preview',prompt:'현재 요청',manifest_sha256:'bound',turn_id:null}]}),request:async(action,data)=>{calls.push({action,data});return true}};
 vm.createContext(c);vm.runInContext([line(ui,' const allowed='),line(ui,' const previewPrompt='),line(ui," el('generalChatReviews').onclick=")].join('\n'),c);
 await get('generalChatReviews').onclick({target:{closest:()=>({dataset:{generalDecision:kind,preview:'preview'}})}});return calls;
}
function modelControls(status,general=true,pending=true){
 const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',value:'',disabled:false,textContent:'',dataset:{},querySelector:()=>get(id+' button')});return nodes.get(id)};
 const p={conversations:[{id:'A',title:'대화 A'}],active_conversation:{id:'A',model_revision:1,chat_override:true,...(pending?{pending_chat_selection:{selection:'next',after_turn:'turn'}}:{})},effective_chat_selection:'current',chat_turns:general?[]:[{id:'turn',status}],general_chat_turns:general?[{id:'turn',status}]:[]};
 const c={JSON,Number,busy:false,conversationModelScope:'',state:{workspace_id:'workspace',model_catalog:{models:[]}},project:()=>p,song:()=> 'song',esc:String,modelChoiceName:x=>x.id,modelChoiceStatus:()=> '설정 필요',$:get};vm.createContext(c);
 const begin=html.indexOf('function drawConversationControls(){'),end=html.indexOf('async function switchConversation(',begin);assert.ok(begin>=0&&end>begin);vm.runInContext(html.slice(begin,end)+'\ndrawConversationControls();',c);
 return{status:get('#conversationModelStatus').textContent,model:get('#conversationModelSelect'),button:get('#conversationModel button')};
}
(async()=>{
 const ready={configured:true,available:true,mode:'anthropic-live',external_transmission:true};
 const unavailable={...ready,available:false,reason:'현재 선택 모델은 이 연결을 사용할 수 없습니다.'};
 let result=controls(unavailable);assert.equal(result.prepare.disabled,true);assert.equal(result.approve.disabled,true);assert.equal(result.reject.disabled,false,'unavailable selection can reject a stale review');assert.equal(result.cancel.disabled,false,'local stop remains possible');assert.equal(result.configured,true);
 result=controls({...ready,new_preview_available:false});assert.equal(result.prepare.disabled,true,'unapplied selection blocks a new request');assert.equal(result.approve.disabled,false,'pending next model must not block an approved continuation');
 result=controls(ready,'awaiting_continuation_approval');assert.equal(result.prepare.disabled,true);assert.equal(result.approve.disabled,false);
 assert.equal(controls({...ready,external_transmission:false}).configured,false,'inconsistent transport flags are not trusted configuration');
 assert.equal((await decision(unavailable,'approve')).length,0);const rejected=await decision(unavailable,'reject');assert.equal(rejected.length,1);assert.equal(rejected[0].data.decision,'reject');
 for(const status of ['queued','running','awaiting_continuation_approval']){result=modelControls(status);assert.match(result.status,/다음 응답부터/);assert.equal(result.button.disabled,false)}
 for(const status of ['cancel_requested','outcome_unknown']){result=modelControls(status,true,false);assert.match(result.status,/먼저 확인/);assert.equal(result.button.disabled,true);assert.equal(result.model.disabled,true)}
 result=modelControls('cancelled');assert.match(result.status,/예약을 적용하지 않았습니다/);assert.equal(result.button.disabled,false,'known cancellation permits explicit reselection');
 assert.match(modelControls('running',false).status,/다음 응답부터/,'legacy scheduling remains represented');
 const badge={textContent:''},c={state:{capabilities:{}},project:()=>({general_chat_connection:unavailable}),$:()=>badge};vm.createContext(c);vm.runInContext(line(html,'function drawProviderBadge(){')+'\ndrawProviderBadge();',c);assert.match(badge.textContent,/대화 모델 확인 필요/);
 assert.match(html,/if\(generalChatChanged\)\{if\(!chatChanged&&typeof drawConversationControls/,'general-only transitions refresh reservation controls');
 console.log('scoped model availability, local recovery, and general/legacy reservation UI scenarios passed');
})().catch(error=>{console.error(error);process.exitCode=1});
