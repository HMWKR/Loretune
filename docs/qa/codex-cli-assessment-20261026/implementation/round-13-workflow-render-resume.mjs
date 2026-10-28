const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/implementation/workflow',task=await taskSpace(42),p=task.page('p2');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
if(!await p.evaluate(()=>document.querySelector('.lt-timeline-controls').open))await p.click('.lt-timeline-controls>summary',{label:'시간과 음원 자막 편집'});
for(let i=0;i<4;i++){await p.fill(`#clips [data-clip="${i}"][data-field="duration"]`,i===3?'1.5':'0.5');await p.press(`#clips [data-clip="${i}"][data-field="duration"]`,'Tab');}
await p.selectOption('#profile','landscape');await p.selectOption('#audioVersion','1');await p.fill('#audioOffset','0.5');await p.press('#audioOffset','Tab');
for(let i=0;i<2;i++){await p.click('#addCaption',{label:'합성 한국어 자막 추가'});await p.fill(`#captions [data-caption="${i}"][data-field="start"]`,i===0?'0':'1.5');await p.fill(`#captions [data-caption="${i}"][data-field="end"]`,i===0?'1.5':'3');await p.fill(`#captions [data-caption="${i}"][data-field="text"]`,i===0?'Aethon 합성 제작 검증':'단색 시험 후보 · 실제 AI 생성 아님');}
const draftState=await p.evaluate(()=>({time:new Date().toISOString(),draft:structuredClone(draft),dirty,viewport:[innerWidth,innerHeight],document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight]}));
await fs.writeFile(root+'/timeline-draft.json',JSON.stringify(draftState,null,2));await p.screenshot({path:root+'/timeline-draft-1920.png'});
await p.click('#saveTimeline',{label:'시험 편집 새 버전 저장'});await p.waitForFunction(()=>!busy&&!dirty&&project().timeline_head===2,undefined,{timeout:10000});
await p.click('#review',{label:'저장된 시험 출력 버전 승인'});await p.waitForFunction(()=>!busy&&project().timeline_versions.at(-1).approval,undefined,{timeout:10000});
await p.click('#render',{label:'로컬 출력 내용 확인'});await p.waitForFunction(()=>document.querySelector('#renderConfirm').open);
await p.screenshot({path:root+'/render-confirm-1920.png'});await p.click('#dismissRender',{label:'출력 닫기 실행 안함'});
const noJobAfterClose=await p.evaluate(()=>state.jobs.length===0);if(!noJobAfterClose)throw Error('DISMISS_CREATED_JOB');
await p.click('#render',{label:'승인 출력 다시 확인'});await p.waitForFunction(()=>document.querySelector('#renderConfirm').open);
await p.click('#confirmRender',{label:'음악 자막 로컬 렌더 실행'});await p.waitForFunction(()=>!busy&&state.jobs.length===1,undefined,{timeout:10000});
await p.waitForFunction(()=>state.jobs.some(j=>['completed','failed','cancelled'].includes(j.status)),undefined,{timeout:30000});
const result=await p.evaluate(()=>({time:new Date().toISOString(),viewport:[innerWidth,innerHeight],job:state.jobs[0],project:project(),requests:__flow.requests,blocked:__flow.blocked,errors:__flow.errors}));
await fs.writeFile(root+'/render-result.json',JSON.stringify({...result,noJobAfterClose},null,2));console.log({status:result.job.status,error:result.job.error,verified:result.job.verified,job:result.job.id,blocked:result.blocked,errors:result.errors});console.log(await p.snapshot());
