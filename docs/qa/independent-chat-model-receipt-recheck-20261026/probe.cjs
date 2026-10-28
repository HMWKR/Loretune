const fs=require('fs'),vm=require('vm'),assert=require('assert');
const input=JSON.parse(fs.readFileSync(0,'utf8')),html=fs.readFileSync('index.html','utf8'),results=[];
const slice=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const esc=s=>String(s??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
function fixture(initial){
 const nodes=new Map(),node=k=>{if(!nodes.has(k))nodes.set(k,{textContent:'',innerHTML:'',value:'합성 보존 초안',closest:()=>null,querySelectorAll:()=>[]});return nodes.get(k)};
 let poll,response=initial;
 const c={state:structuredClone(initial),stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'s',busy:false,dirty:false,song:()=>'A',project:()=>c.state.projects.A,modelChatScope:'same',modelChatKey:()=>'same',$:node,esc,drawProviderBadge(){},document:{querySelectorAll:()=>[],activeElement:null},creatorDiagnostic:()=>'',creatorError:()=>({message:''}),setInterval:f=>poll=f,fetch:async()=>({json:async()=>structuredClone(response)}),drawCreationProposals(){},drawGuided(){},drawMediaCreator(){},drawImageConnection(){},drawJobs(){},drawGeneration(){},refresh:()=>{throw Error('unexpected refresh')}};
 vm.createContext(c);vm.runInContext(slice('function chatModelName(','function creatorModelReason(')+slice('function receiptFacts(',"$('#modelChatPrompt').addEventListener"),c);
 vm.runInContext(slice('setInterval(async()=>{','},1500);')+'},1500);',c);
 return {c,node,render:()=>c.drawModelChat(),poll:async fresh=>{response=fresh;await poll()}};
}
async function test(name,run){try{const observation=await run();results.push({name,status:'PASS',...observation})}catch(e){results.push({name,status:'FAIL',error:e.message})}}
(async()=>{
 await test('current selected GPT and historical Claude remain distinct',()=>{
  const f=fixture(input.before);f.c.state.projects.A.chat_turns=[{id:'past',status:'completed',model:'Claude historical',mode:'contract-fake',answer:'old answer',steps:[]}];f.c.state.projects.A.chat_connection.model='Claude historical';
  const before=JSON.stringify(f.c.state);f.render();assert(f.node('#modelChatSelection').textContent.includes('GPT 6 Luna'));assert(!f.node('#modelChatSelection').textContent.includes('Claude'));assert(f.node('#modelChatTurns').innerHTML.includes('Claude historical'));assert.equal(JSON.stringify(f.c.state),before);assert(f.node('#modelChatSubmit').disabled);assert.equal(f.node('#modelChatPrompt').value,'합성 보존 초안');
 });
 await test('absent unknown wrong-role and hostile display use honest text only',()=>{
  const f=fixture(input.before),p=f.c.state.projects.A;
  for(const id of [null,'nonexistent',input.videoId]){p.model_settings.selections.chat=id;f.render();const text=f.node('#modelChatSelection').textContent;assert(text.includes(id?'정보 확인 필요':'미선택'));assert(!text.includes('GPT 6 Luna'));}
  p.model_settings.selections.chat=input.gptId;const name='한글'.repeat(100)+'<img src=x onerror=alert(1)>';f.c.state.model_catalog.models.find(x=>x.id===input.gptId).display_name=name;f.render();assert(f.node('#modelChatSelection').textContent.includes(name));assert.equal(f.node('#modelChatSelection').innerHTML,'');
 });
 await test('current false only first-line warning; historical facts unchanged',()=>{
  const f=fixture(input.before);const r={shot_name:'s',motion_revision:1,composition_saved:true,approval:{actor:'local-owner',scope:'local-motion-candidate',motion_revision:1},proposals:[]};
  for(const value of [true,false,null]){r.matches_current_context=value;const raw=JSON.stringify(r),current=f.c.receiptMarkup(r),past=f.c.receiptMarkup(r,true);assert.equal(current.includes('chat-receipt-stale'),value===false);assert(!past.includes('chat-receipt-stale'));assert(!current.includes('<button'));assert.equal(JSON.stringify(r),raw);if(value===false)assert(current.indexOf('이전 승인으로 실행할 수 없습니다.')<current.indexOf('로컬 작업자 승인:'));}
 });
 for(const [name,fresh] of [['Grok change',input.grok],['selection cleared',input.cleared]]){
  const f=fixture(input.before);f.render();const initial=f.node('#modelChatSelection').textContent;
  for(let i=0;i<3;i++)await f.poll(fresh);
  const actual=f.node('#modelChatSelection').textContent,expected=f.c.currentChatModelText(fresh.projects.A,fresh.model_catalog);
  results.push({name:'model-only polling / '+name,status:actual===expected?'PASS':'FAIL',serverRevision:fresh.revision,clientRevision:f.c.state.revision,serverSelection:fresh.projects.A.model_settings.selections.chat,clientSelection:f.c.state.projects.A.model_settings.selections.chat,initial,expected,actual,polls:3,draftPreserved:f.node('#modelChatPrompt').value==='합성 보존 초안'});
 }
 await test('same fresh model update applies when chat progression also changes',async()=>{
  const f=fixture(input.before);f.render();const fresh=structuredClone(input.grok);fresh.projects.A.chat_turns=[{id:'progress',status:'completed',answer:'',steps:[]}];await f.poll(fresh);assert.equal(f.node('#modelChatSelection').textContent,f.c.currentChatModelText(fresh.projects.A,fresh.model_catalog));
 });
 console.log(JSON.stringify({results,passed:results.filter(x=>x.status==='PASS').length,failed:results.filter(x=>x.status==='FAIL').length,network:'stubbed fetch; no HTTP'},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
