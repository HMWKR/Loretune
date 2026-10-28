const fs=await import('node:fs/promises');
const root='/Users/leesungmin/Desktop/Loretune/docs/qa/proposal-draft-fix-20261026/served-baseline';
const task=await taskSpace(37),p=task.page('p1');
await p.click('button[data-step="3"]',{label:'장면 검토 기준선 열기'});
await p.waitForFunction(()=>{const m=document.querySelector('#preview video,#preview img');return m&&(m.tagName==='IMG'?m.complete:m.readyState>=2)},undefined,{timeout:10000});
await p.evaluate(()=>{
 window.__baselineSaved={draft:structuredClone(draft),shot:shotName,project:JSON.stringify(project()),stateRevision:state.revision};
 window.__baselineMetrics=()=>{
 const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom,scrollWidth:e.scrollWidth,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight}};
 const selectors=['.lt-studio-shell','main','#preview','.lt-preview-stage','.lt-timeline','.lt-timeline-controls','#sequencePlay','#saveTimeline','#render','#review','#takes','#shotlist','.lt-inspector','#timelineStatus'];
 const boxes=Object.fromEntries(selectors.map(s=>[s,rect(document.querySelector(s))]));
 const m=document.querySelector('#preview video,#preview img');let media=null;
 if(m){const r=m.getBoundingClientRect(),w=m.videoWidth||m.naturalWidth,h=m.videoHeight||m.naturalHeight,k=Math.min(r.width/w,r.height/h);media={tag:m.tagName,element:rect(m),intrinsic:[w,h],content:[w*k,h*k],currentTime:m.currentTime??null,paused:m.paused??null,readyState:m.readyState??null,objectFit:getComputedStyle(m).objectFit,src:new URL(m.currentSrc||m.src,location.href).pathname}}
 const roles=['body','button.primary','#reviewTake','#saveTimeline','.lt-scene-copy>b','.lt-scene-copy small','#timelineStatus','.lt-timeline-controls summary','input','#audioInfo svg','#audioInfo polyline'];
 const computed=Object.fromEntries(roles.map(s=>{const e=document.querySelector(s);if(!e)return[s,null];const c=getComputedStyle(e);return[s,Object.fromEntries(['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor','borderColor','borderWidth','borderRadius','padding','gap','minHeight','overflow','stroke'].map(k=>[k,c[k]]))]}));
 const tokens=Object.fromEntries([...document.styleSheets].flatMap(sheet=>{try{return[...sheet.cssRules].filter(r=>r.selectorText?.includes(':root')).flatMap(r=>[...r.style].filter(x=>x.startsWith('--')).map(x=>[x,getComputedStyle(document.documentElement).getPropertyValue(x).trim()]))}catch{return[]}}));
 return{time:new Date().toISOString(),url:location.href,viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,visualViewportScale:visualViewport.scale,appScale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),document:{width:document.documentElement.clientWidth,height:document.documentElement.clientHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight},boxes,media,computed,tokens,selectedShot:shotName,selectedTake:project().shots[shotName]?.selected,timelineHead:project().timeline_head,dirty,errors:window.__baseline.errors};
 };
 const media=document.querySelector('#preview video');if(media){media.pause();media.currentTime=1}
});
await p.waitForFunction(()=>{const v=document.querySelector('#preview video');return !v||(!v.seeking&&Math.abs(v.currentTime-1)<.02)},undefined,{timeout:10000});
await p.screenshot({path:root+'/basic-1920.png'});
const metrics=await p.evaluate(()=>window.__baselineMetrics());
await fs.writeFile(root+'/basic-1920.json',JSON.stringify(metrics,null,2));
console.log({document:metrics.document,media:metrics.media,appScale:metrics.appScale,errors:metrics.errors});
console.log(await p.snapshot());
