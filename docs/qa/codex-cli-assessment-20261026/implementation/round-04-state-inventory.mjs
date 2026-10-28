const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/implementation';
const task=await taskSpace(42),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
const records=[];
for(const [button,dialog] of [['newProject','projectDialog'],['settings','settingDialog'],['preferencesButton','preferencesDialog'],['ontologyButton','ontologyDialog'],['libraryButton','libraryDialog'],['rightsButton','rightsDialog'],['budgetButton','budgetDialog'],['archiveButton','archiveDialog']]){
 await p.evaluate(id=>{for(let e=document.getElementById(id)?.parentElement;e;e=e.parentElement)if(e.tagName==='DETAILS')e.open=true},button);
 await p.click('#'+button,{label:'기존 설정 화면 상태 확인'});
 await p.waitForFunction(id=>document.getElementById(id).open,dialog,{timeout:5000});
 const data=await p.evaluate(id=>{const d=document.getElementById(id),r=d.getBoundingClientRect();return{dialog:id,text:d.innerText,controls:[...d.querySelectorAll('button,input,select,textarea')].map(e=>({id:e.id,name:e.name,type:e.type,disabled:e.disabled,required:e.required})),box:{x:r.x,y:r.y,width:r.width,height:r.height},focused:document.activeElement.id||document.activeElement.tagName}},dialog);
 records.push(data);
 if(['ontologyDialog','libraryDialog','preferencesDialog'].includes(dialog))await p.screenshot({path:root+'/'+dialog+'-1920.png'});
 await p.keyboard.press('Escape');
 records.at(-1).closed=await p.evaluate(id=>!document.getElementById(id).open,dialog);
}
await p.click('#editModelSettings',{label:'미연결 모델 선택 검토'});
const models=[];
for(const [role,value] of [['chat','anthropic-haiku-5-5'],['image','fal-flux-schnell'],['video','fal-kling-2-6-pro'],['video','fal-kling-2-5-turbo'],['image','']]){
 await p.selectOption(`#modelSlots select[name="${role}"]`,value);
 models.push(await p.evaluate(role=>({role,value:document.querySelector(`#modelSlots select[name="${role}"]`).value,name:document.getElementById(`model-${role}-selected`).textContent,reason:document.getElementById(`model-${role}-reason`).textContent,stored:project().model_settings.selections[role]}),role));
}
await p.screenshot({path:root+'/model-unavailable-1920.png'});
await p.keyboard.press('Escape');
await p.evaluate(()=>drawModelSettings());
await p.click('button[data-step="2"]',{label:'모델 미연결 입력 보존 확인'});
await p.click('#modelChatPanel>summary',{label:'실제 모델 연결 상태 확인'});
await p.fill('#modelChatPrompt','합성 QA: 미연결 요청은 전송하지 않습니다.');
const chat=await p.evaluate(()=>({disabled:document.getElementById('modelChatSubmit').disabled,input:document.getElementById('modelChatPrompt').value,capability:document.getElementById('modelChatCapability').innerText,stored:sessionStorage.getItem(modelChatKey()),actualPosts:window.__baseline.requests.filter(x=>x.method!=='GET').length}));
await p.fill('#modelChatPrompt','');
await p.click('#modelChatPanel>summary',{label:'모델 상담 상태 접기'});
await fs.writeFile(root+'/core-state-inventory.json',JSON.stringify({time:new Date().toISOString(),records,models,chat,projectUnchanged:await p.evaluate(()=>JSON.stringify(project())===window.__parityOriginalProject)},null,2));
console.log({dialogs:records.map(x=>({id:x.dialog,closed:x.closed})),models,chat});
console.log(await p.snapshot());
