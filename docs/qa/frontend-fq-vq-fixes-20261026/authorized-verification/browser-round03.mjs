const fs=await import('node:fs/promises');
const root='/Users/leesungmin/Desktop/Loretune/docs/qa/frontend-fq-vq-fixes-20261026/authorized-verification';
const task=await taskSpace(36),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.evaluate(()=>{
 window.__qaSavedDraft=structuredClone(draft);window.__qaSavedDirty=dirty;window.__qaProjectBefore=JSON.stringify(project());window.__qaNativeEvents=[];
 window.__qaNativeListener=e=>{if(e.target.tagName==='VIDEO')window.__qaNativeEvents.push({event:e.type,time:performance.now(),trusted:e.isTrusted,currentTime:e.target.currentTime,duration:e.target.duration,paused:e.target.paused,ended:e.target.ended,status:document.querySelector('#sequenceStatus').textContent,position:document.querySelector('#sequenceSeek').value});};
 document.addEventListener('ended',window.__qaNativeListener,true);document.addEventListener('loadeddata',window.__qaNativeListener,true);
 const names=Object.keys(project().shots);draft={...structuredClone(draft),audio:null,audio_offset:0,subtitles:[],clips:names.slice(0,2).map(shot=>({shot,take:1,duration:5,trim:0}))};dirty=true;drawTimeline();
});
await p.selectOption('#previewMode','sequence');
await p.waitForFunction(()=>document.querySelector('#preview video')?.readyState>=2);
await p.evaluate(()=>{const seek=document.querySelector('#sequenceSeek');seek.value='4.5';seek.dispatchEvent(new Event('input',{bubbles:true}));});
await p.click('#sequencePlay');
await p.waitForFunction(()=>Number(document.querySelector('#sequenceSeek').value)>=10&&document.querySelector('#sequencePlay').textContent==='편집 재생');
const result=await p.evaluate(()=>({case:'FQ02 actual decoder silent sequence EOF',temporaryDraft:true,startsAt:4.5,total:10,position:Number(document.querySelector('#sequenceSeek').value),button:document.querySelector('#sequencePlay').textContent,status:document.querySelector('#sequenceStatus').textContent,video:{paused:document.querySelector('#preview video').paused,ended:document.querySelector('#preview video').ended,currentTime:document.querySelector('#preview video').currentTime},nativeEvents:window.__qaNativeEvents,projectUnchanged:window.__qaProjectBefore===JSON.stringify(project()),errors:window.__fixtureErrors,time:new Date().toISOString()}));
await p.screenshot({path:root+'/fq02-silent-native-completed-1920.png'});
await fs.writeFile(root+'/browser-media-results.json',JSON.stringify(result,null,2));console.log(result);
await p.evaluate(()=>{LoretuneMedia.stop();document.removeEventListener('ended',window.__qaNativeListener,true);document.removeEventListener('loadeddata',window.__qaNativeListener,true);draft=window.__qaSavedDraft;dirty=window.__qaSavedDirty;draw();});
