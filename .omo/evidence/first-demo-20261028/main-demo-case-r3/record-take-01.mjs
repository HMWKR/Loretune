const fs=await import('node:fs/promises'),crypto=await import('node:crypto');
const base='/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028';
const {recordScreen}=await import('file://'+base+'/record-screen.mjs');
const {musicOnlyDemo,optionalPhotoAndOverlayDemo,reopenDemo}=await import('file://'+base+'/main-demo-actions.mjs');
const options={projectName:'1차 시연 · 음악에서 영상까지',evidenceDir:base+'/main-demo-case-r3',inputDir:base+'/inputs'};
const toolSources={};for(const name of ['record-screen.mjs','main-demo-actions.mjs','encode-recording-sampled-v2.py']){const bytes=await fs.readFile(base+'/'+name);toolSources[name]=crypto.createHash('sha256').update(bytes).digest('hex');await fs.writeFile(options.evidenceDir+'/'+name+'.source',bytes);}
await fs.writeFile(options.evidenceDir+'/recording-tool-sources.json',JSON.stringify(toolSources,null,2));
const task=await taskSpace(91),page=task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await page.goto('http://127.0.0.1:57888/');
await page.waitForFunction(()=>document.querySelector('#agentSidebar')&&document.querySelector('#emptyNewProject')&&!busy);
const productSources={};for(const item of await fs.readdir('/Users/leesungmin/Desktop/Loretune',{withFileTypes:true})){if(item.isFile()&&/\.(py|js|html|css)$/.test(item.name))productSources[item.name]=crypto.createHash('sha256').update(await fs.readFile('/Users/leesungmin/Desktop/Loretune/'+item.name)).digest('hex');}
await fs.writeFile(options.evidenceDir+'/product-sources-at-start.json',JSON.stringify(productSources,null,2));
console.log(await recordScreen(page,options.evidenceDir+'/take-01',async rawMark=>{
 const mark=async(name,detail)=>{await rawMark(name,detail);await new Promise(resolve=>setTimeout(resolve,650));};
 const ui=await musicOnlyDemo(page,mark,options);
 const output=await optionalPhotoAndOverlayDemo(page,mark,options,ui);
 await reopenDemo(page,mark,options,output);
 await mark('phase1-core-ui-workflow-completed',{realModelCalls:0,actualPlatformOutput:output.id,scope:'Music-only and optional-photo native workflow; not actual Claude/video model or whole release acceptance'});
}));
console.log(await page.snapshot());
