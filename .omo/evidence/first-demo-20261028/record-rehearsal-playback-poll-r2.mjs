const {recordScreen,observeUntil}=await import('file:///Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/record-screen.mjs');
const t=await taskSpace(91),p=t.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.waitForFunction(()=>document.body.dataset.desktopShell==='bounded');
const current=await p.evaluate(()=>({src:document.querySelector('#downloadPreview video')?.getAttribute('src'),ended:document.querySelector('#downloadPreview video')?.ended}));
if(!current.src?.includes('1ef5ec0c6e7445f790977e57dee64ddd')||!current.ended)throw Error('Inspect player state before new probe');
console.log(await recordScreen(p,'/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/rehearsal-playback-recording-poll-r2',async mark=>{
 await mark('rehearsal-existing-output-only',{notMainDemonstration:true,outputJob:'1ef5ec0c6e7445f790977e57dee64ddd',note:'Existing9s output in platform UI, no production actions or edits; poll-based capture validation.'});
 await p.focus('#downloadPreview video');await p.press('#downloadPreview video','Home');await p.press('#downloadPreview video','Space');
 await observeUntil(p,()=>document.querySelector('#downloadPreview video').currentTime>1&&!document.querySelector('#downloadPreview video').paused);
 await mark('actual-platform-playback-started');
 await observeUntil(p,()=>document.querySelector('#downloadPreview video').ended);
 await mark('actual-platform-nine-second-output-ended');
}));
