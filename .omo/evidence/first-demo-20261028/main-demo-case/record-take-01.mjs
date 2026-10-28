const {recordScreen}=await import('file:///Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/record-screen.mjs');
const {musicOnlyDemo,optionalPhotoAndOverlayDemo,reopenDemo}=await import('file:///Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/main-demo-actions.mjs');
const options={projectName:'1차 시연 · 음악에서 영상까지',evidenceDir:'/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/main-demo-case',inputDir:'/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/inputs'};
const task=await taskSpace(91),page=task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await page.goto('http://127.0.0.1:58759/');
await page.waitForFunction(()=>document.querySelector('#agentSidebar')&&document.querySelector('#emptyNewProject')&&!busy);
const result=await recordScreen(page,options.evidenceDir+'/take-01',async mark=>{
 const ui=await musicOnlyDemo(page,mark,options);
 const output=await optionalPhotoAndOverlayDemo(page,mark,options,ui);
 await reopenDemo(page,mark,options,output);
 await mark('phase1-core-ui-workflow-completed',{realModelCalls:0,actualPlatformOutput:output.id,scope:'Music-only and optional-photo native workflow; not actual Claude/video model or whole release acceptance'});
});
console.log(result);
console.log(await page.snapshot());
