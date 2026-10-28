const fs=await import('node:fs/promises');
const root='/Users/leesungmin/Desktop/Loretune/docs/qa/proposal-draft-fix-20261026/served-baseline';
// Preserve the first capture: the previous round's emulation did not persist.
for(const ext of ['png','json'])await fs.rename(root+'/basic-1920.'+ext,root+'/observed-900x845-not-1920.'+ext);
const task=await taskSpace(37),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.waitForFunction(()=>innerWidth===1920&&innerHeight===1080,undefined,{timeout:5000});
await p.evaluate(()=>{window.scrollTo(0,0);document.querySelectorAll('video,audio').forEach(m=>m.pause());const v=document.querySelector('#preview video');if(v)v.currentTime=1});
await p.waitForFunction(()=>!document.querySelector('#preview video')?.seeking,undefined,{timeout:5000});
async function capture(name){
 const metrics=await p.evaluate(()=>window.__baselineMetrics());
 if(metrics.viewport[0]!==1920||metrics.viewport[1]!==1080)throw Error('INVALID_CAPTURE_VIEWPORT');
 await p.screenshot({path:root+'/'+name+'.png'});
 const after=await p.evaluate(()=>[innerWidth,innerHeight]);if(after[0]!==1920||after[1]!==1080)throw Error('VIEWPORT_CHANGED_DURING_CAPTURE');
 await fs.writeFile(root+'/'+name+'.json',JSON.stringify(metrics,null,2));
 console.log({name,document:metrics.document,media:metrics.media?.content,timeline:metrics.boxes['.lt-timeline'],errors:metrics.errors});
}
await capture('basic-1920');
await p.click('.lt-timeline-controls > summary',{label:'정밀 편집 공간 확인'});
await capture('detailed-1920');
console.log(await p.snapshot());
