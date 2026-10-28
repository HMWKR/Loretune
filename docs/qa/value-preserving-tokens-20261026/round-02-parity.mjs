const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/value-preserving-tokens-20261026';
const task=await taskSpace(39),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.evaluate(()=>{
 window.__parityOriginalProject=JSON.stringify(project());
 window.__measureTokenParity=()=>{
  const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}};
  const measure=()=>Object.fromEntries(['#audioInfo svg','#audioInfo polyline','#sequenceTime','#compareTime'].map(selector=>{
   const e=document.querySelector(selector),c=getComputedStyle(e),range=document.createRange();range.selectNodeContents(e);
   const ctx=document.createElement('canvas').getContext('2d');ctx.font=c.font;
   return[selector,{background:c.backgroundColor,stroke:c.stroke,fontFamily:c.fontFamily,fontSize:c.fontSize,fontWeight:c.fontWeight,lineHeight:c.lineHeight,fontVariantNumeric:c.fontVariantNumeric,rect:rect(e),textWidth:range.getBoundingClientRect().width,numeralWidths:['00:00.000','11:11.111','88:88.888','00:00.500 / 00:07.000'].map(text=>({text,width:ctx.measureText(text).width})),points:e.getAttribute('points')}];
  }));
  const current=measure(),svg=document.querySelector('#audioInfo svg'),line=document.querySelector('#audioInfo polyline'),times=[...document.querySelectorAll('.lt-timecode')],originals=[svg.getAttribute('style'),line.getAttribute('stroke'),...times.map(e=>e.getAttribute('style'))];
  // Controlled in-memory legacy value reference, not a second product implementation.
  svg.style.background='#101010';line.setAttribute('stroke','#ddd');times.forEach(e=>e.style.fontFamily='ui-monospace,monospace');
  const legacy=measure();
  const restore=(e,name,v)=>v===null?e.removeAttribute(name):e.setAttribute(name,v);
  restore(svg,'style',originals[0]);restore(line,'stroke',originals[1]);times.forEach((e,i)=>restore(e,'style',originals[i+2]));
  const restored=measure();
  return {time:new Date().toISOString(),viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,appScale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),current,legacy,restored,identical:JSON.stringify(current)===JSON.stringify(legacy)&&JSON.stringify(current)===JSON.stringify(restored)};
 };
 window.__layoutMetrics=()=>{
  const selectors=['.lt-studio-shell','.lt-stage-bar','.lt-media-pane','.lt-preview-stage','.lt-shot-header','.creator-scene-description','#preview','#sequenceTransport','#sequenceStatus','#sequenceCaption','.lt-take-row','#ltTimelineDock','#ltTimelineDock>h2','.lt-timeline-controls','.lt-timeline-controls>summary','#timelineStatus','#timeAxis','#timeRuler','#timeWave','#track','#timeAudioLabel','.inspector','.lt-scene-rail'];
  const boxes=Object.fromEntries(selectors.map(s=>{const e=document.querySelector(s);if(!e)return[s,null];const r=e.getBoundingClientRect(),c=getComputedStyle(e);return[s,{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,marginTop:c.marginTop,marginBottom:c.marginBottom,padding:c.padding,gap:c.gap,border:c.border,fontSize:c.fontSize,lineHeight:c.lineHeight}]}));
  const v=document.querySelector('#preview video'),r=v.getBoundingClientRect(),k=Math.min(r.width/v.videoWidth,r.height/v.videoHeight);
  return {time:new Date().toISOString(),viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,appScale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),visualViewportScale:visualViewport.scale,mode:document.querySelector('#previewMode').value,precisionOpen:document.querySelector('.lt-timeline-controls').open,document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],boxes,media:{content:[v.videoWidth*k,v.videoHeight*k],intrinsic:[v.videoWidth,v.videoHeight],time:v.currentTime,paused:v.paused,readyState:v.readyState},selected:project().shots[shotName].selected,projectUnchanged:JSON.stringify(project())===window.__parityOriginalProject};
 };
});
const wave=await p.evaluate(()=>window.__measureTokenParity());
if(!wave.identical)throw Error('WAVE_PARITY_FAIL');
await fs.writeFile(root+'/waveform-visible-parity.json',JSON.stringify(wave,null,2));
await p.screenshot({path:root+'/waveform-visible-1920.png'});
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
  const label=`${w}-${mode}-${precision?'detail':'basic'}`,metrics=await p.evaluate(()=>window.__layoutMetrics()),parity=await p.evaluate(()=>window.__measureTokenParity());
  if(!parity.identical)throw Error('TOKEN_PARITY_FAIL '+label);
  await fs.writeFile(root+'/'+label+'.json',JSON.stringify({metrics,parity},null,2));
  await p.screenshot({path:root+'/'+label+'.png'});
  results.push({label,identical:parity.identical,viewport:metrics.viewport,media:metrics.media.content,document:metrics.document});
  console.log(results.at(-1));
 }
}
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.click('#compareButton',{label:'비교 시간표시 값 확인'});
await p.selectOption('#compareLeft','1');await p.selectOption('#compareRight','2');
await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].length===2&&[...document.querySelectorAll('#compareDialog video')].every(v=>v.readyState>=2),undefined,{timeout:10000});
await p.evaluate(()=>{const s=document.querySelector('#compareSeek');s.value=.5;s.dispatchEvent(new Event('input',{bubbles:true}))});
await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].every(v=>!v.seeking&&v.paused),undefined,{timeout:5000});
const compare=await p.evaluate(()=>window.__measureTokenParity());
if(!compare.identical)throw Error('COMPARE_PARITY_FAIL');
await fs.writeFile(root+'/comparison-visible-parity.json',JSON.stringify(compare,null,2));
await p.screenshot({path:root+'/comparison-1920.png'});
await p.click('#compareDialog [data-close]',{label:'비교 종료 선택 유지'});
await fs.writeFile(root+'/browser-summary.json',JSON.stringify({results,waveform:wave.identical,comparison:compare.identical},null,2));
console.log(await p.snapshot());
