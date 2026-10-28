const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/implementation/workflow',task=await taskSpace(42),p=task.page('p2');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
if(!await p.evaluate(()=>!!project().timeline_versions.at(-1).approval)){await p.focus('#review');await p.keyboard.press('Enter');await p.waitForFunction(()=>!busy&&project().timeline_versions.at(-1).approval,undefined,{timeout:10000});}
await p.focus('#render');await p.keyboard.press('Enter');await p.waitForFunction(()=>document.querySelector('#renderConfirm').open);
await p.screenshot({path:root+'/render-confirm-1920.png'});await p.click('#dismissRender',{label:'출력 닫기 실행 안함'});
const noJobAfterClose=await p.evaluate(()=>state.jobs.length===0);if(!noJobAfterClose)throw Error('DISMISS_CREATED_JOB');
await p.focus('#render');await p.keyboard.press('Enter');await p.waitForFunction(()=>document.querySelector('#renderConfirm').open);
await p.click('#confirmRender',{label:'음악 자막 로컬 렌더 실행'});await p.waitForFunction(()=>!busy&&state.jobs.length===1,undefined,{timeout:10000});
await p.waitForFunction(()=>state.jobs.some(j=>['completed','failed','cancelled'].includes(j.status)),undefined,{timeout:30000});
const result=await p.evaluate(()=>({time:new Date().toISOString(),viewport:[innerWidth,innerHeight],job:state.jobs[0],project:project(),requests:__flow.requests,blocked:__flow.blocked,errors:__flow.errors}));
await fs.writeFile(root+'/render-result.json',JSON.stringify({...result,noJobAfterClose},null,2));console.log({status:result.job.status,error:result.job.error,verified:result.job.verified,job:result.job.id,blocked:result.blocked,errors:result.errors});console.log(await p.snapshot());
