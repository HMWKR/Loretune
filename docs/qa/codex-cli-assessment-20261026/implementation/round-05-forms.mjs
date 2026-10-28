const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/implementation';
const task=await taskSpace(42),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.evaluate(()=>{
 window.__guardQA={queue:[],calls:[],lookups:0,results:[],originalFetch:window.fetch};
 const qa=window.__guardQA;
 window.fetch=(url,options={})=>{
  const u=new URL(url,location.href);
  if(u.origin===location.origin&&u.pathname==='/api/action'&&options.method==='POST'){
   const body=JSON.parse(options.body);
   if(!['preference_propose','chat_plan'].includes(body.action))throw Error('UNEXPECTED_QA_ACTION');
   qa.calls.push({action:body.action,data:body.data});
   return new Promise((resolve,reject)=>qa.queue.push({resolve,reject}));
  }
  if(u.origin===location.origin&&u.pathname.startsWith('/api/requests/')){qa.lookups++;return Promise.resolve(new Response(JSON.stringify({status:'committed'}),{status:200,headers:{'Content-Type':'application/json'}}))}
  return qa.originalFetch(url,options);
 };
});
const cases=['unchanged-success','new-input-success','identical-content-edit','context-away-back','confirmed-rejection','unknown-result'];
for(const form of ['preferenceForm','chatForm']){
 for(const scenario of cases){
  if(form==='preferenceForm'){
   await p.evaluate(()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();let e=document.querySelector('#preferencesButton');for(let n=e.parentElement;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true});
   // Use the actual application entry handler; its containing settings surface may be collapsed.
   await p.evaluate(()=>document.querySelector('#preferencesButton').click());
   await p.fill('#preferenceForm [name=evidence]','합성 시험 문장 · 실제 사용자 자료 없음');
   await p.fill('#preferenceForm [name=reason]','지연된 응답의 초안 보존 검증');
  }else{
   await p.evaluate(()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close()});
   await p.click('button[data-step="2"]',{label:'로컬 계획 폼 확인'});
   await p.evaluate(()=>document.querySelector('#chatForm').closest('details').open=true);
  }
  const selector='#'+form+' [name='+(form==='chatForm'?'prompt':'value')+']';
  const original='합성 입력 원문',newText='응답 대기 중 작성한 새 합성 입력';
  await p.fill(selector,original);
  const before=await p.evaluate(()=>window.__guardQA.calls.length);
  await p.click('#'+form+' button',{label:'통제 응답으로 초안 검증'});
  await p.waitForFunction(()=>window.__guardQA.queue.length===1,undefined,{timeout:5000});
  if(scenario==='new-input-success')await p.fill(selector,newText);
  if(scenario==='identical-content-edit'){await p.fill(selector,'임시 수정');await p.fill(selector,original)}
  if(scenario==='context-away-back')await p.evaluate(()=>{const old=state.workspace_id;state.workspace_id=old+':controlled-context';proposalFormContext();state.workspace_id=old;proposalFormContext()});
  await p.evaluate(kind=>{
   const pending=window.__guardQA.queue.shift();
   if(kind==='unknown-result')pending.reject(new Error('QA_CONTROLLED_UNKNOWN'));
   else pending.resolve(new Response(JSON.stringify(kind==='confirmed-rejection'?{error:'합성 검증: 저장 요청이 거절됐습니다. 입력은 유지됩니다.'}:{}),{status:kind==='confirmed-rejection'?422:200,headers:{'Content-Type':'application/json'}}));
  },scenario);
  await p.waitForFunction(()=>busy===false,undefined,{timeout:10000});
  const result=await p.evaluate(({form,selector,scenario,before,original,newText})=>{
   const value=document.querySelector(selector).value,expected=scenario==='unchanged-success'?'':scenario==='new-input-success'?newText:original;
   return {form,scenario,value,expected,preserved:value===expected,submitted:window.__guardQA.calls.length-before,pending:!!pendingId(),revision:state.revision,time:new Date().toISOString(),contextTest:scenario==='context-away-back'?'controlled in-memory workspace identity away/back; not real project navigation':null};
  },{form,selector,scenario,before,original,newText});
  if(scenario==='confirmed-rejection'&&form==='preferenceForm')await p.screenshot({path:root+'/controlled-preference-rejection-1920.png'});
  if(scenario==='unknown-result'){
   await p.click('#'+form+' button',{label:'미확정 요청 중복 차단 확인'});
   result.noDuplicate=await p.evaluate(n=>window.__guardQA.calls.length===n,before+1);
   if(form==='preferenceForm')await p.screenshot({path:root+'/controlled-preference-unknown-1920.png'});
   await p.evaluate(()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close()});
   await p.click('#recoverRequest',{label:'모의 기존 요청만 확인'});
   await p.waitForFunction(()=>!busy&&!pendingId(),undefined,{timeout:10000});
   result.reconciled=await p.evaluate(selector=>({pending:!!pendingId(),value:document.querySelector(selector).value,lookups:window.__guardQA.lookups}),selector);
  }
  result.pass=result.preserved&&result.submitted===1&&(scenario!=='unknown-result'||result.pending&&result.noDuplicate&&!result.reconciled.pending&&result.reconciled.value===original);
  await p.evaluate(r=>window.__guardQA.results.push(r),result);
  await fs.writeFile(root+'/browser-form-results.json',JSON.stringify(await p.evaluate(()=>window.__guardQA.results),null,2));
  console.log({form,scenario,pass:result.pass});
  if(!result.pass)throw Error('FORM_GUARD_ASSERTION_FAILED');
 }
}
await p.evaluate(()=>{window.fetch=window.__guardQA.originalFetch;document.querySelector('#preferenceForm').reset();document.querySelector('#chatForm').reset()});
console.log(await p.snapshot());
