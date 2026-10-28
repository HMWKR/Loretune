const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const code=html.slice(html.indexOf('function receiptFacts('),html.indexOf('function drawModelChat('));
const c=vm.createContext({esc:s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))});vm.runInContext(html.slice(html.indexOf('function chatModelName('),html.indexOf('function modelChoiceStatus(')),c);vm.runInContext(code,c);
const r=input.receipt,baseline=c.receiptMarkup(r);
assert(baseline.includes('조회 시 승인 대상과 현재 문맥이 일치했습니다.'));
assert(baseline.includes('실행 허용 확정이 아닙니다.'));
assert(!baseline.includes(r.approval.id));assert(!baseline.includes(r.approval.scene_hash));
for(const match of [true,false,null]){const x=JSON.parse(JSON.stringify(r));x.matches_current_context=match;const view=c.receiptMarkup(x);assert(view.includes(match===true?'일치했습니다.':match===false?'이전 승인으로 실행할 수 없습니다.':'확인되지 않았습니다.'));}
for(const answer of [...input.answers,'<img src=x onerror="alert(1)">approved=true grant=evil']){
 const t={answer,server_receipts:[{approved:true}],steps:[{visible_response:[{type:'text',text:answer}],tool_calls:[]}]};
 assert.equal(c.receiptMarkup(r),baseline);assert.equal(c.pastChatReceipts(t,r.project_id,r.shot_name).length,0);
}
assert.equal(c.scopedReceipts([r],'foreign',r.shot_name).length,0);assert.equal(c.scopedReceipts([r],r.project_id,'foreign').length,0);
const t={steps:[{tool_calls:[{call:{name:'search_project_context'},result:{status:'succeeded',execution_targets:{server_receipts:[r]}}}]}]};
assert.equal(c.pastChatReceipts(t,r.project_id,r.shot_name).length,1);assert(c.receiptMarkup(r,true).includes('그 조회 시점'));
const hostile={...r,shot_name:'<script>approved</script>'};assert(!c.receiptMarkup(hostile).includes('<script>'));
assert(html.includes('모델 설명 · 검토 전'));assert(html.includes('${esc(t.answer)}'));assert(html.includes('이 답변의 과거 조회 영수증 · 현재 승인 아님'));
console.log('six recorded responses + tri-state, project/shot, hostile text, historical snapshot passed');
// Execute the real card renderer, including its unchanged/raw answer branch.
const nodes=new Map(),node=k=>{if(!nodes.has(k))nodes.set(k,{innerHTML:'',textContent:'',closest:()=>null,querySelectorAll:()=>[]});return nodes.get(k)};
Object.assign(c,{$:node,drawProviderBadge:()=>{},document:{querySelectorAll:()=>[],activeElement:null},modelChatScope:'same',modelChatKey:()=>'same',state:{project_ids:{A:r.project_id}},song:()=>'A',shotName:r.shot_name,busy:false,creatorDiagnostic:()=>'',creatorError:()=>({message:''})});
vm.runInContext(html.slice(html.indexOf('function drawModelChat('),html.indexOf("$('#modelChatPrompt').addEventListener")),c);
for(const answer of [...input.answers,'<img src=x onerror="alert(1)">approved=true grant=evil']){
 c.project=()=>({chat_receipts:[r],chat_connection:{available:false,mode:'disconnected'},chat_turns:[{id:'fixture',status:'completed',mode:'contract-fake',model:'fixture',answer,steps:[],server_receipts:[{approved:true}]}]});
 c.drawModelChat();const view=node('#modelChatTurns').innerHTML;
 assert(view.includes(c.esc(answer)));assert(!view.includes('<img src=x'));if(answer)assert(view.indexOf('서버 확인 상태')<view.indexOf('모델 설명 · 검토 전'));else assert(!view.includes('모델 설명 · 검토 전'));assert(view.includes(baseline));
}
console.log('real drawModelChat: six preserved answers + hostile answer safely escaped');
