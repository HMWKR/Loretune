const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/context-header-space-20261026/after';
const task=await taskSpace(40),p=task.page('p1');
const results=[];
await p.evaluate(()=>{
 window.__headerOriginal={title:document.querySelector('#shotTitle').textContent,description:document.querySelector('#description').textContent};
 window.__headerInspect=()=>{
  const box=e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return{x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,fontSize:c.fontSize,lineHeight:c.lineHeight,wrap:c.overflowWrap,outline:c.outline,visible:r.width>0&&r.height>0}};
  const detail=document.querySelector('.creator-scene-description'),summary=detail.querySelector('summary'),title=document.querySelector('#shotTitle');
  return{time:new Date().toISOString(),viewport:[innerWidth,innerHeight],scale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),shell:document.body.dataset.desktopShell,document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],title:{text:title.textContent,...box(title)},description:{text:document.querySelector('#description').textContent,...box(document.querySelector('#description'))},summary:box(summary),open:detail.open,focused:document.activeElement===summary,focusVisible:summary.matches(':focus-visible'),projectUnchanged:JSON.stringify(project())===window.__parityOriginalProject,selected:project().shots[shotName].selected,dirty,pending:!!pendingRequest};
 };
 document.querySelector('.creator-scene-description').open=false;
 document.querySelector('.lt-preview-stage').scrollTop=0;
});
await p.focus('.creator-scene-description>summary');await p.keyboard.press('Enter');
let x=await p.evaluate(()=>window.__headerInspect());results.push({case:'keyboard Enter opens with focus',pass:x.open&&x.focused&&x.focusVisible&&x.summary.height>=44,data:x});
await p.screenshot({path:root+'/keyboard-description-open-1920.png'});
await p.keyboard.press('Space');x=await p.evaluate(()=>window.__headerInspect());results.push({case:'keyboard Space closes with same focus',pass:!x.open&&x.focused&&x.focusVisible,data:x});
for(const[w,h,scale]of[[1920,1080,'1'],[1280,900,'1'],[1280,900,'2']]){
 await p.cdp('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:1,mobile:false});
 await p.evaluate(()=>document.querySelector('.management').open=true);await p.selectOption('#textScale',scale);await p.evaluate(()=>document.querySelector('.management').open=false);
 await p.waitForFunction(s=>document.body.dataset.desktopShell===(s==='2'?'flow':'bounded'),scale,{timeout:3000});
 for(const[kind,text]of[['korean','아주 긴 한글 장면 제목 · 빛과 시간 속에서 서로 다른 이야기를 이어가는 주인공의 새로운 시선과 기억'],['unbroken','LongUnbrokenSceneName'.repeat(8)]]){
  await p.evaluate(t=>{document.querySelector('#shotTitle').textContent=t;document.querySelector('.creator-scene-description').open=false;document.querySelector('.lt-preview-stage').scrollTop=0},text);
  x=await p.evaluate(()=>window.__headerInspect());
  results.push({case:`${w} app${scale} ${kind} title`,pass:x.title.scrollWidth<=x.title.clientWidth+1&&x.document[0]===w,data:x});
  await p.screenshot({path:root+`/title-${kind}-${w}-app${scale}.png`});
 }
 await p.evaluate(()=>{document.querySelector('#description').textContent='긴 설명을 끝까지 확인하는 합성 표시 fixture. '.repeat(12)+'UnbrokenDescription'.repeat(10);document.querySelector('.creator-scene-description').open=true});
 await p.focus('.creator-scene-description>summary');x=await p.evaluate(()=>window.__headerInspect());
 results.push({case:`${w} app${scale} expanded long description`,pass:x.description.scrollWidth<=x.description.clientWidth+1&&x.document[0]===w&&x.open&&x.focused,data:x});
 await p.screenshot({path:root+`/description-long-${w}-app${scale}.png`});
 await p.evaluate(()=>{document.querySelector('#shotTitle').textContent=window.__headerOriginal.title;document.querySelector('#description').textContent=window.__headerOriginal.description;document.querySelector('.creator-scene-description').open=false});
}
await p.evaluate(()=>document.querySelector('.management').open=true);await p.selectOption('#textScale','1');await p.evaluate(()=>document.querySelector('.management').open=false);
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await fs.writeFile(root+'/boundary-results.json',JSON.stringify(results,null,2));console.log(results.map(({case:c,pass,data})=>({case:c,pass,document:data.document,titleWidth:[data.title.clientWidth,data.title.scrollWidth]})));console.log(await p.snapshot());
