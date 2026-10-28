const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/context-header-space-20261026/after';
const task=await taskSpace(40),p=task.page('p1'),results=[];
const save=async entry=>{results.push(entry);await fs.writeFile(root+'/state-keyboard-results.json',JSON.stringify(results,null,2));console.log({case:entry.case,pass:entry.pass})};
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.evaluate(()=>{
 window.__targetVisibility=selector=>{const e=document.querySelector(selector),r=e.getBoundingClientRect();let left=Math.max(0,r.left),top=Math.max(0,r.top),right=Math.min(innerWidth,r.right),bottom=Math.min(innerHeight,r.bottom);for(let a=e.parentElement;a;a=a.parentElement){const c=getComputedStyle(a),b=a.getBoundingClientRect();if(/auto|scroll|hidden|clip/.test(c.overflowX)){left=Math.max(left,b.left);right=Math.min(right,b.right)}if(/auto|scroll|hidden|clip/.test(c.overflowY)){top=Math.max(top,b.top);bottom=Math.min(bottom,b.bottom)}}return{height:r.height,width:r.width,visibleHeight:Math.max(0,bottom-top),visibleWidth:Math.max(0,right-left),focus:document.activeElement===e,focusVisible:e.matches(':focus-visible'),text:e.textContent,disabled:e.disabled,outline:getComputedStyle(e).outline}};
 document.querySelector('.creator-scene-description').open=false;document.querySelector('.lt-notice-detail').open=false;
});
for(const[w,h]of[[1920,1080],[1280,900]]){
 await p.cdp('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:1,mobile:false});
 await p.focus('.creator-scene-description>summary');await p.keyboard.press('Enter');
 let d=await p.evaluate(()=>({open:document.querySelector('.creator-scene-description').open,description:document.querySelector('#description').textContent,v:window.__targetVisibility('.creator-scene-description>summary'),document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight]}));
 await save({case:`${w} keyboard opens disclosure fully visible`,pass:d.open&&d.v.focus&&d.v.focusVisible&&d.v.height>=44&&d.v.visibleHeight>=d.v.height-.5&&d.description===await p.evaluate(()=>window.__headerOriginal.description),data:d});
 await p.screenshot({path:root+`/keyboard-open-${w}.png`});await p.keyboard.press('Space');
 d=await p.evaluate(()=>({open:document.querySelector('.creator-scene-description').open,v:window.__targetVisibility('.creator-scene-description>summary')}));
 await save({case:`${w} keyboard closes disclosure fully visible`,pass:!d.open&&d.v.focus&&d.v.focusVisible&&d.v.visibleHeight>=d.v.height-.5,data:d});
 await p.keyboard.press('Tab');const next=await p.evaluate(()=>({tag:document.activeElement.tagName,id:document.activeElement.id}));await save({case:`${w} Tab leaves summary`,pass:next.tag!=='SUMMARY',data:next});
 await p.evaluate(()=>document.querySelector('.lt-timeline-controls').open=true);
 for(const selector of ['#saveTimeline']){await p.focus(selector);const v=await p.evaluate(s=>window.__targetVisibility(s),selector);await save({case:`${w} precision save focus visible`,pass:v.focus&&v.visibleHeight>=v.height-.5,data:v})}
}
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.fill('#clips input[data-clip="0"][data-field="duration"]','1.1');await p.keyboard.press('Tab');
await p.waitForFunction(()=>dirty&&draft.clips[0].duration===1.1,undefined,{timeout:4000});
await p.focus('.creator-scene-description>summary');await p.keyboard.press('Enter');await p.keyboard.press('Space');
await p.evaluate(()=>{document.querySelector('.lt-preview-stage').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0});
let data=await p.evaluate(()=>({dirty,duration:draft.clips[0].duration,selected:project().shots[shotName].selected,unchanged:JSON.stringify(project())===window.__parityOriginalProject}));
await save({case:'dirty edit survives disclosure open and close',pass:data.dirty&&data.duration===1.1&&data.selected===1&&data.unchanged,data});await p.screenshot({path:root+'/dirty-header-1920.png'});
await p.evaluate(()=>{
 window.__headerNativeFetch=window.fetch;window.__headerMockRequests=[];
 window.fetch=(url,options={})=>{if(new URL(url,location.href).pathname==='/api/action'){window.__headerMockRequests.push({action:JSON.parse(options.body).action,method:options.method});return Promise.resolve(new Response(JSON.stringify({error:'합성 QA: 편집 저장을 거절한 통제 응답입니다.'}),{status:422,headers:{'Content-Type':'application/json'}}))}return window.__headerNativeFetch(url,options)};
});
await p.click('#saveTimeline',{label:'통제 거절로 초안 보존 검증'});
await p.waitForFunction(()=>!busy&&window.__headerMockRequests.length===1,undefined,{timeout:5000});
await p.focus('.creator-scene-description>summary');await p.keyboard.press('Enter');await p.keyboard.press('Space');
await p.evaluate(()=>{document.querySelector('.lt-notice-detail').open=true;document.querySelector('.lt-preview-stage').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0});
data=await p.evaluate(()=>({dirty,duration:draft.clips[0].duration,pending:!!pendingRequest,request:window.__headerMockRequests,notice:document.querySelector('#notice').textContent,unchanged:JSON.stringify(project())===window.__parityOriginalProject,document:[document.documentElement.scrollWidth,document.documentElement.scrollHeight]}));
await save({case:'controlled 422 preserves draft through disclosure',pass:data.dirty&&data.duration===1.1&&!data.pending&&data.request.length===1&&data.unchanged,data});await p.screenshot({path:root+'/controlled-422-header-1920.png'});
await p.focus('#cancelTimelineDraft');let v=await p.evaluate(()=>window.__targetVisibility('#cancelTimelineDraft'));await save({case:'dirty cancel focus fully visible',pass:v.focus&&v.visibleHeight>=v.height-.5,data:v});
await p.click('#cancelTimelineDraft',{label:'합성 초안 취소 원본 유지'});
await p.waitForFunction(()=>!dirty,undefined,{timeout:3000});
data=await p.evaluate(()=>{window.fetch=window.__headerNativeFetch;return{dirty,duration:draft.clips[0].duration,unchanged:JSON.stringify(project())===window.__parityOriginalProject,pending:!!pendingRequest}});
await save({case:'cancel restores approved local state without writes',pass:!data.dirty&&data.duration===1&&data.unchanged&&!data.pending,data});
await p.evaluate(()=>document.querySelector('.lt-notice-detail').open=false);
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
await p.click('#compareButton',{label:'보조 뷰포트 비교 보존 확인'});
await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].length===2&&[...document.querySelectorAll('#compareDialog video')].every(v=>v.readyState>=2),undefined,{timeout:6000});
data=await p.evaluate(()=>({stages:[...document.querySelectorAll('#compareDialog .compare-stage')].map(e=>{const r=e.getBoundingClientRect();return[r.width,r.height]}),selected:project().shots[shotName].selected,unchanged:JSON.stringify(project())===window.__parityOriginalProject}));
await save({case:'1280 comparison preserves selection and project',pass:data.selected===1&&data.unchanged,data});await p.screenshot({path:root+'/comparison-1280.png'});await p.click('#compareDialog [data-close]',{label:'비교 닫기 상태 유지'});
console.log(await p.snapshot());
