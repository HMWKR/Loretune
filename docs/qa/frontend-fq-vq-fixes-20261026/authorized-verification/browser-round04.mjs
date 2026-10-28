const fs=await import('node:fs/promises');
const root='/Users/leesungmin/Desktop/Loretune/docs/qa/frontend-fq-vq-fixes-20261026/authorized-verification';
const task=await taskSpace(36),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.evaluate(()=>{
 window.__qaOriginalFetch=window.fetch;window.__qaOriginalState=structuredClone(state);window.__qaPollWaits=[];
 window.fetch=(url,options={})=>{window.__fixtureRequests.push({url,method:options.method||'GET',controlled:true});if(url!=='/api/state'||(options.method&&options.method!=='GET'))throw Error('CONTROLLED_NO_EXTERNAL_REQUEST');return new Promise(resolve=>window.__qaPollWaits.push(resolve));};
});
await p.waitForFunction(()=>window.__qaPollWaits.length===2);
await p.evaluate(()=>{const newer=structuredClone(window.__qaOriginalState);newer.revision+=2;newer.projects[song()].chat_connection.reason='controlled newer response';window.__qaPollWaits[1]({ok:true,json:async()=>newer});});
await p.waitForFunction(()=>state.revision===window.__qaOriginalState.revision+2);
await p.evaluate(()=>{const older=structuredClone(window.__qaOriginalState);older.revision+=1;older.projects[song()].chat_connection.reason='controlled older response';window.__qaPollWaits[0]({ok:true,json:async()=>older});});
await p.waitForFunction(()=>pollReadsInFlight===0);
const stale=await p.evaluate(()=>({case:'FQ01 controlled reversed real browser fetch promises',base:window.__qaOriginalState.revision,current:state.revision,expected:window.__qaOriginalState.revision+2,reason:project().chat_connection.reason,pass:state.revision===window.__qaOriginalState.revision+2}));
await p.evaluate(()=>{window.__qaPollWaits=[];});
await p.waitForFunction(()=>window.__qaPollWaits.length>=1);
await p.evaluate(()=>{const equal=structuredClone(state);equal.projects[song()].chat_connection.reason='controlled equal revision update';window.__qaPollWaits[0]({ok:true,json:async()=>equal});});
await p.waitForFunction(()=>project().chat_connection.reason==='controlled equal revision update');
const equal=await p.evaluate(()=>({case:'FQ01 equal-revision chat connection update',revision:state.revision,pass:project().chat_connection.reason==='controlled equal revision update'}));
await p.evaluate(()=>{window.fetch=window.__qaOriginalFetch;state=window.__qaOriginalState;stateReadEpoch++;draw();});
const denial=await p.evaluate(async()=>{
 const field=document.querySelector('#reviewReason');field.value='저장소 거부 중 보존할 합성 검토 초안';field.dispatchEvent(new Event('input',{bubbles:true}));
 const originalGet=sessionStorage.getItem;const originalPending={failed:pendingId.failed,last:pendingId.last,settled:pendingId.settled};const before=JSON.stringify(project());const postCount=window.__fixtureRequests.filter(x=>x.method==='POST').length;
 sessionStorage.getItem=()=>{throw new DOMException('Controlled storage read denial','SecurityError');};
 let thrown=null,result;try{updateRecovery();result=await act('select',{song:song(),shot:shotName,take:2,shot_revision:project().shots[shotName].revision});}catch(e){thrown=e.name;}
 const observation={case:'FQ03 controlled storage denial in actual browser',thrown,result,requestBlocked:window.__fixtureRequests.filter(x=>x.method==='POST').length===postCount,draft:field.value,recovery:document.querySelector('#recovery span').textContent,recoveryVisible:!document.querySelector('#recovery').hidden,projectUnchanged:before===JSON.stringify(project()),failed:pendingId.failed};
 sessionStorage.getItem=originalGet;Object.assign(pendingId,originalPending);updateRecovery();
 return observation;
});
const meta=await p.evaluate(()=>({time:new Date().toISOString(),errors:window.__fixtureErrors,nonGet:window.__fixtureRequests.filter(x=>x.method!=='GET'),pageResourceOrigins:[...new Set(performance.getEntriesByType('resource').map(x=>{try{return new URL(x.name).protocol}catch{return 'unparsed'}}))]}));
await fs.writeFile(root+'/browser-async-results.json',JSON.stringify({stale,equal,denial,...meta},null,2));console.log({stale,equal,denial,...meta});
