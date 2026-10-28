'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const input=JSON.parse(fs.readFileSync(0,'utf8')),html=fs.readFileSync('index.html','utf8');
const slice=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const defer=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve}};
function fixture(){
 const nodes=new Map(),waits=[];let poll,name='A',fullDraws=0;
 const node=k=>{if(!nodes.has(k))nodes.set(k,{textContent:'',innerHTML:'',value:'새 입력 의도',selectionStart:1,selectionEnd:4,closest:()=>null,querySelectorAll:()=>[]});return nodes.get(k)};
 const c={state:structuredClone(input.before),stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'s',draft:null,busy:false,dirty:false,song:()=>name,project:()=>c.state.projects[name],modelChatScope:'same',modelChatKey:()=>'same',$:node,esc:s=>String(s??'').replaceAll('<','&lt;'),drawProviderBadge(){},document:{querySelectorAll:()=>[],activeElement:node('#modelChatPrompt')},creatorDiagnostic:()=>'',creatorError:()=>({message:''}),setInterval:f=>poll=f,fetch:()=>{const d=defer();waits.push(d);return d.promise},draw(){fullDraws++;throw Error('model-only polling must not perform a full redraw')},drawCreationProposals(){},drawGuided(){},drawMediaCreator(){},drawImageConnection(){},drawJobs(){},drawGeneration(){},drawModelSettings(){throw Error('must not redraw unsaved model selections')},refresh:()=>{throw Error('unexpected refresh')}};
 vm.createContext(c);vm.runInContext(slice('function chatModelName(','function creatorModelReason(')+slice('function receiptFacts(',"$('#modelChatPrompt').addEventListener"),c);
 vm.runInContext(slice('setInterval(async()=>{','},1500);')+'},1500);',c);c.drawModelChat();
 return {c,node,waits,poll:async()=>{await poll();assert.equal(fullDraws,0,'model-only and same-head polling must preserve the editor DOM')},resolve:(i,value)=>waits[i].resolve({json:async()=>structuredClone(value)}),switch:n=>name=n};
}
const results=[];
async function test(name,run){await run();results.push({name,status:'PASS'})}
(async()=>{
 for(const key of ['grok','cleared'])await test('no-motion model-only '+key,async()=>{
  const f=fixture(),prompt=f.node('#modelChatPrompt'),selected=f.node('select[name=chat]');selected.value='unsaved-choice';
  const before=JSON.stringify([f.c.state.projects.A.shots,f.c.state.projects.A.chat_turns,f.c.state.jobs]);
  const p=f.poll();f.resolve(0,input[key]);await p;
  assert.equal(f.node('#modelChatSelection').textContent,f.c.currentChatModelText(input[key].projects.A,input[key].model_catalog));
  assert.equal(f.c.state.revision,input[key].revision);assert.equal(prompt.value,'새 입력 의도');assert.equal(f.c.document.activeElement,prompt);assert.equal(prompt.selectionStart,1);assert.equal(prompt.selectionEnd,4);assert.equal(selected.value,'unsaved-choice');
  assert.equal(JSON.stringify([f.c.state.projects.A.shots,f.c.state.projects.A.chat_turns,f.c.state.jobs]),before);
 });
 await test('catalog-only human name refresh at same revision',async()=>{const f=fixture(),x=structuredClone(input.before);x.model_catalog.models.find(m=>m.id===input.gptId).display_name='새 표시 이름';const p=f.poll();f.resolve(0,x);await p;assert(f.node('#modelChatSelection').textContent.includes('새 표시 이름'))});
 await test('reverse response cannot restore old selection',async()=>{const f=fixture(),a=f.poll(),b=f.poll();f.resolve(1,input.cleared);await b;f.resolve(0,input.grok);await a;assert(f.node('#modelChatSelection').textContent.includes('미선택'));assert.equal(f.c.state.revision,input.cleared.revision)});
 for(const mode of ['old-revision','other-workspace','other-project','other-shot','epoch','dirty','busy'])await test('guard '+mode,async()=>{
  const f=fixture(),before=f.node('#modelChatSelection').textContent,p=f.poll(),x=structuredClone(input.grok);
  if(mode==='old-revision')x.revision=input.before.revision-1;
  if(mode==='other-workspace')x.workspace_id='other';
  if(mode==='other-project')f.switch('B');
  if(mode==='other-shot')f.c.shotName='different';
  if(mode==='epoch')f.c.stateReadEpoch++;
  if(mode==='dirty'||mode==='busy')f.c[mode]=true;
  f.resolve(0,x);await p;assert.equal(f.c.state.revision,input.before.revision);assert.equal(f.node('#modelChatSelection').textContent,before);assert.equal(f.node('#modelChatPrompt').value,'새 입력 의도');
 });
 await test('dirty guard releases to later fresh poll',async()=>{const f=fixture();f.c.dirty=true;const a=f.poll();f.resolve(0,input.grok);await a;f.c.dirty=false;const b=f.poll();f.resolve(1,input.grok);await b;assert(f.node('#modelChatSelection').textContent.includes('Grok 4.7'))});
 await test('terminal run-only update advances request revision without replacing a new prompt',async()=>{const f=fixture();let rendered=0;f.c.window={LoretuneGeneralChat:{refresh(){rendered++}}};const prompt=f.node('#generalChatPrompt');prompt.value='다음 질문 초안';f.c.document.activeElement=prompt;f.c.state.projects.A.production_runs=[{id:'run',state:'accepting_tools'}];const x=structuredClone(f.c.state);x.revision++;x.projects.A.production_runs[0].state='completed';const pending=f.poll();f.resolve(0,x);await pending;assert.equal(f.c.state.revision,x.revision,'next action must use the completed worker revision');assert.equal(f.c.state.projects.A.production_runs[0].state,'completed');assert.equal(rendered,1);assert.equal(prompt.value,'다음 질문 초안');assert.equal(f.c.document.activeElement,prompt)});
 console.log(JSON.stringify({results,count:results.length,network:'fake fetch only'},null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
