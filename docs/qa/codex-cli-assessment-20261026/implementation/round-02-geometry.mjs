const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/codex-cli-assessment-20261026/implementation';
const task=await taskSpace(42),p=task.page('p1');
await p.evaluate(()=>{window.__parityOriginalProject=JSON.stringify(project());
 window.__layoutMetrics=()=>{
  const selectors=['.lt-studio-shell','.lt-stage-bar','.lt-media-pane','.lt-preview-stage','.lt-shot-header','.lt-scene-context','.creator-scene-description>summary','#shotTitle','.creator-scene-description','#preview','#sequenceTransport','#sequenceStatus','#sequenceCaption','.lt-take-row','#ltTimelineDock','#ltTimelineDock>h2','.lt-timeline-controls','.lt-timeline-controls>summary','#timelineStatus','#timeAxis','#timeRuler','#timeWave','#track','#timeAudioLabel','.inspector','.lt-scene-rail'];
  const boxes=Object.fromEntries(selectors.map(s=>{const e=document.querySelector(s);if(!e)return[s,null];const r=e.getBoundingClientRect(),c=getComputedStyle(e);return[s,{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,marginTop:c.marginTop,marginBottom:c.marginBottom,padding:c.padding,gap:c.gap,border:c.border,fontSize:c.fontSize,lineHeight:c.lineHeight}]}));
  const v=document.querySelector('#preview video'),r=v.getBoundingClientRect(),k=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);
  return {time:new Date().toISOString(),viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,appScale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),visualViewportScale:visualViewport.scale,mode:document.querySelector('#previewMode').value,precisionOpen:document.querySelector('.lt-timeline-controls').open,document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],boxes,media:{content:[v.videoWidth*k,v.videoHeight*k],intrinsic:[v.videoWidth,v.videoHeight],time:v.currentTime,paused:v.paused,readyState:v.readyState},selected:project().shots[shotName].selected,projectUnchanged:JSON.stringify(project())===window.__parityOriginalProject};
 };
});
await p.click('button[data-step="3"]',{label:'토큰 변경 작업대 확인'});
const results=[];
for(const [w,h] of [[1920,1080],[1280,900]]){
 await p.cdp('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:1,mobile:false});
 for(const precision of [false,true])for(const mode of ['selected','sequence']){
  await p.evaluate(open=>{document.querySelector('.lt-timeline-controls').open=open;document.querySelector('.lt-timeline-controls').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0;document.querySelector('.lt-notice-detail').open=false},precision);
  await p.selectOption('#previewMode',mode);
  await p.evaluate(mode=>{const v=document.querySelector('#preview video');if(mode==='sequence'){const s=document.querySelector('#sequenceSeek');s.value=.5;s.dispatchEvent(new Event('input',{bubbles:true}))}else if(v){v.pause();v.currentTime=1}},mode);
  await p.waitForFunction(mode=>{const v=document.querySelector('#preview video');return document.querySelector('#previewMode').value===mode&&v?.readyState>=2&&!v.seeking&&v.paused},mode,{timeout:10000});
  await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const label=`${w}-${mode}-${precision?'detail':'basic'}`,metrics=await p.evaluate(()=>window.__layoutMetrics());
  await fs.writeFile(root+'/'+label+'.json',JSON.stringify({metrics},null,2));
  await p.screenshot({path:root+'/'+label+'.png'});
  results.push({label,viewport:metrics.viewport,media:metrics.media.content,document:metrics.document});
  console.log(results.at(-1));
 }
}
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.click('#compareButton',{label:'비교 시간표시 값 확인'});
await p.selectOption('#compareLeft','1');await p.selectOption('#compareRight','2');
await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].length===2&&[...document.querySelectorAll('#compareDialog video')].every(v=>v.readyState>=2),undefined,{timeout:10000});
await p.evaluate(()=>{const s=document.querySelector('#compareSeek');s.value=.5;s.dispatchEvent(new Event('input',{bubbles:true}))});
await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].every(v=>!v.seeking&&v.paused),undefined,{timeout:5000});
const compare=await p.evaluate(()=>({time:new Date().toISOString(),videos:[...document.querySelectorAll('#compareDialog video')].map(v=>{const r=v.getBoundingClientRect();return{width:r.width,height:r.height,time:v.currentTime,paused:v.paused}}),selected:project().shots[shotName].selected}));
await fs.writeFile(root+'/comparison.json',JSON.stringify(compare,null,2));
await p.screenshot({path:root+'/comparison-1920.png'});
await p.click('#compareDialog [data-close]',{label:'비교 종료 선택 유지'});

await p.evaluate(()=>{document.querySelector('.creator-scene-description').open=true;document.querySelector('.lt-preview-stage').scrollTop=0});
await fs.writeFile(root+'/1920-expanded.json',JSON.stringify(await p.evaluate(()=>window.__layoutMetrics()),null,2));
await p.screenshot({path:root+'/1920-expanded.png'});
await fs.writeFile(root+'/browser-summary.json',JSON.stringify({results,compare},null,2));
const final=await p.evaluate(()=>({time:new Date().toISOString(),projectUnchanged:JSON.stringify(project())===window.__parityOriginalProject,errors:window.__baseline.errors,blocked:window.__baseline.blocked,nonGet:window.__baseline.requests.filter(x=>x.method!=='GET'),dirty,pending:!!pendingRequest}));
await fs.writeFile(root+'/browser-final.json',JSON.stringify(final,null,2));console.log(final);
console.log(await p.snapshot());
