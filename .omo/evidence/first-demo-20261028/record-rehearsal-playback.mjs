const {recordScreen}=await import('file:///Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/record-screen.mjs');
const t=await taskSpace(91),p=t.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.waitForFunction(()=>document.body.dataset.desktopShell==='bounded');
const saved=await p.evaluate(()=>({src:document.querySelector('#downloadPreview video')?.getAttribute('src'),paused:document.querySelector('#downloadPreview video')?.paused}));
if(!saved.src?.includes('1ef5ec0c6e7445f790977e57dee64ddd'))throw Error('Wrong output open; inspect before recording');
const result=await recordScreen(p,'/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/rehearsal-playback-recording',async mark=>{
 await mark('rehearsal-existing-output-only',{notMainDemonstration:true,outputJob:'1ef5ec0c6e7445f790977e57dee64ddd',note:'Existing saved9s composition, not the complete empty-project workflow; old frontend loaded before sidebar implementation.'});
 await p.focus('#downloadPreview video');
 await p.press('#downloadPreview video','Home');
 await p.press('#downloadPreview video','Space');
 await p.waitForFunction(()=>document.querySelector('#downloadPreview video').currentTime>1&&!document.querySelector('#downloadPreview video').paused);
 await mark('actual-platform-playback-started');
 await p.waitForFunction(()=>document.querySelector('#downloadPreview video').ended,undefined,{timeout:15000});
 await mark('actual-platform-nine-second-output-ended');
});
console.log(result);
