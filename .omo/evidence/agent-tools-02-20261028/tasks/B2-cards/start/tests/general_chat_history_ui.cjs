'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ui=fs.readFileSync(process.argv[2]||'general-chat-ui.js','utf8');
const line=prefix=>ui.split('\n').find(value=>value.startsWith(prefix))||'';
const current='두 번째 안으로 진행해 주세요.';
const history=[{role:'user',content:'이전 요청과 검토 전 답변의 기록'}, {role:'assistant',content:'첫 번째 안과 두 번째 안'}, {role:'user',content:current}];
async function decide(preview,{draft=current,rights=true,decision='approve'}={}){
 const requests=[],nodes=new Map();
 const el=id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',querySelectorAll:()=>[{dataset:{rights:'preview'},checked:rights}]});return nodes.get(id)};
 el('generalChatPrompt').value=draft;
 const context={Number,console,inFlight:false,busy:false,scope:'same-conversation',key:()=> 'same-conversation',song:()=> 'A',el,project:()=>({general_chat_connection:{available:true,mode:'anthropic-live',external_transmission:true},general_chat_previews:[{id:'preview',manifest_sha256:'bound',turn_id:null,...preview}]}),request:async(action,data)=>{requests.push({action,data});return true}};
 vm.createContext(context);
 vm.runInContext([line(' const allowed='),line(' const previewPrompt='),line(' const historyLabel='),line(" el('generalChatReviews').onclick=")].join('\n'),context);
 await el('generalChatReviews').onclick({target:{closest:()=>({dataset:{generalDecision:decision,preview:'preview'}})}});
 return{requests,status:el('generalChatStatus').textContent,context};
}
(async()=>{
 const preview={prompt:current,message_body:{messages:history}};
 let result=await decide(preview);assert.equal(result.requests.length,1,'scoped history prefix must not block an unchanged current request');assert.equal(result.requests[0].data.decision,'approve');
 result=await decide(preview,{draft:'변경한 새 초안'});assert.equal(result.requests.length,0,'changed draft must not authorize old content');assert.match(result.status,/거절하고/);
 result=await decide({message_body:{messages:history}});assert.equal(result.requests.length,0,'multi-message content without a bound current prompt is ambiguous');
 result=await decide({message_body:{messages:[{role:'user',content:current}]}});assert.equal(result.requests.length,1,'single-message older previews remain usable');
 result=await decide({message_body:{messages:[{role:'assistant',content:current}]}});assert.equal(result.requests.length,0,'assistant text is not the current user request');
 result=await decide(preview,{rights:false});assert.equal(result.requests.length,0,'history is still covered by explicit transmission rights');
 result=await decide(preview,{draft:'다른 초안',rights:false,decision:'reject'});assert.equal(result.requests.length,1,'a stale draft can still reject the old review');assert.equal(result.requests[0].data.decision,'reject');
 result=await decide({...preview,turn_id:'turn'},{draft:'다음 질문 초안'});assert.equal(result.requests.length,1,'tool-result continuation does not replace the next draft');
 vm.runInContext('globalThis.historyText=historyLabel;',result.context);
 const label=result.context.historyText({history_context:{request_count:9,answer_count:8,sha256:'private-hash'}});assert.match(label,/이전 요청 9개/);assert.match(label,/최근 답변 8개/);assert.match(label,/승인된 작품 기준이 아닙니다/);assert.doesNotMatch(label,/private-hash/);
 assert.equal(result.context.historyText({history_context:{request_count:'<img src=x>',answer_count:8}}),'');
 assert.match(ui,/이번 요청 총 비용 상한/);assert.doesNotMatch(ui,/전체 대화 비용 상한/);
 console.log('8 history approval scenarios and scoped history/cost copy passed');
})().catch(error=>{console.error(error);process.exitCode=1});
