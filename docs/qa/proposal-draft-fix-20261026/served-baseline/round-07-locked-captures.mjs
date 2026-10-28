const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/proposal-draft-fix-20261026/served-baseline';
const task=await taskSpace(37),p=task.page('p1');
await p.click('button[data-step="3"]',{label:'동일 장면 작업대 비교'});
await p.evaluate(()=>{for(const d of document.querySelectorAll('dialog[open]'))d.close();for(const s of ['.lt-notice-detail','.management','.lt-production-progress']){const d=document.querySelector(s);if(d?.tagName==='DETAILS')d.open=false}window.scrollTo(0,0)});
await p.evaluate(()=>{
 const original=window.__baselineMetrics;
 window.__lockedMetrics=()=>({...original(),capturedAt:new Date().toISOString(),mode:document.querySelector('#previewMode').value,transportMode:document.querySelector('#sequenceTransport').dataset.mode,precisionOpen:document.querySelector('.lt-timeline-controls').open,noticeOpen:document.querySelector('.lt-notice-detail').open,selectedApproval:project().shots[shotName].reviews.at(-1)?.decision||project().shots[shotName].reviews.at(-1)?.status,projectUnchanged:JSON.stringify(project())===window.__baselineSaved.project});
});
async function stable(mode){
 await p.selectOption('#previewMode',mode);
 await p.evaluate(mode=>{
  if(mode==='sequence'){const seek=document.querySelector('#sequenceSeek');seek.value=.5;seek.dispatchEvent(new Event('input',{bubbles:true}))}
  else {const v=document.querySelector('#preview video');if(v){v.pause();v.currentTime=1}}
 },mode);
 await p.waitForFunction(mode=>{const v=document.querySelector('#preview video');return document.querySelector('#previewMode').value===mode&&v?.readyState>=2&&!v.seeking&&v.paused},mode,{timeout:10000});
 await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
}
async function capture(name,w,h,mode){
 const before=await p.evaluate(()=>window.__lockedMetrics());
 if(before.viewport[0]!==w||before.viewport[1]!==h||before.mode!==mode)throw Error('CAPTURE_CONDITION_MISMATCH');
 await p.screenshot({path:root+'/'+name+'.png'});
 const after=await p.evaluate(()=>window.__lockedMetrics());
 if(before.mode!==after.mode||before.media.currentTime!==after.media.currentTime||before.dirty!==after.dirty)throw Error('CAPTURE_STATE_DRIFT');
 await fs.writeFile(root+'/'+name+'.json',JSON.stringify({before,after,condition:'actual served current code; paused media; CSS viewport emulation; DPR1; app scale100%; browser visualViewport scale1; notice collapsed'},null,2));
 console.log({name,mode,media:after.media.content,document:after.document,dirty:after.dirty});
}
for(const [w,h] of [[1920,1080],[1280,900]]){
 await p.cdp('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:1,mobile:false});
 await p.evaluate(()=>{document.querySelector('.lt-timeline-controls').open=false;document.querySelector('#ltTimelineDock').scrollTop=0;document.querySelector('.lt-notice-detail').open=false});
 await stable('selected');await capture('locked-basic-approved-'+w,w,h,'selected');
 await p.click('.lt-timeline-controls > summary',{label:'정밀 편집 조건 펼치기'});
 await stable('sequence');await capture('locked-sequence-detailed-'+w,w,h,'sequence');
 await p.focus('#saveTimeline');
 const focus=await p.evaluate(()=>{const e=document.activeElement,r=e.getBoundingClientRect(),d=document.querySelector('.lt-timeline-controls'),dr=d.getBoundingClientRect();return {id:e.id,rect:{top:r.top,bottom:r.bottom,height:r.height},panel:{top:dr.top,bottom:dr.bottom,scrollTop:d.scrollTop,scrollHeight:d.scrollHeight,clientHeight:d.clientHeight},fullyInside:r.top>=dr.top&&r.bottom<=dr.bottom,documentHeight:document.documentElement.scrollHeight}});
 await fs.writeFile(root+'/precision-focus-'+w+'.json',JSON.stringify(focus,null,2));
 await p.evaluate(()=>{document.querySelector('.lt-timeline-controls').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0});
 await p.fill('#clips input[data-clip="0"][data-field="duration"]','1.1');
 await p.press('#clips input[data-clip="0"][data-field="duration"]','Tab');
 await p.waitForFunction(()=>dirty===true,undefined,{timeout:5000});
 await p.evaluate(()=>{document.querySelector('.lt-timeline-controls').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0});
 await stable('sequence');await capture('locked-dirty-'+w,w,h,'sequence');
 await p.click('#cancelTimelineDraft',{label:'시험 변경 취소 원본 유지'});
 await p.waitForFunction(()=>dirty===false,undefined,{timeout:5000});
 await p.evaluate(()=>{document.querySelector('.lt-notice-detail').open=false;document.querySelector('.lt-timeline-controls').scrollTop=0;document.querySelector('#ltTimelineDock').scrollTop=0});
 await p.click('#compareButton',{label:'두 비율 영상 비교 확인'});
 await p.selectOption('#compareLeft','1');await p.selectOption('#compareRight','2');
 await p.waitForFunction(()=>document.querySelectorAll('#compareDialog video').length===2&&[...document.querySelectorAll('#compareDialog video')].every(v=>v.readyState>=2),undefined,{timeout:10000});
 await p.evaluate(()=>{const s=document.querySelector('#compareSeek');s.value=.5;s.dispatchEvent(new Event('input',{bubbles:true}))});
 await p.waitForFunction(()=>[...document.querySelectorAll('#compareDialog video')].every(v=>!v.seeking&&v.paused),undefined,{timeout:5000});
 await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 const comparison=await p.evaluate(()=>({viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,time:new Date().toISOString(),scale:visualViewport.scale,selectedTake:project().shots[shotName].selected,videos:[...document.querySelectorAll('#compareDialog video')].map(v=>({time:v.currentTime,paused:v.paused,intrinsic:[v.videoWidth,v.videoHeight],box:[v.clientWidth,v.clientHeight],fit:getComputedStyle(v).objectFit})),shared:document.querySelector('#compareTime').textContent,projectUnchanged:JSON.stringify(project())===window.__baselineSaved.project}));
 await p.screenshot({path:root+'/locked-comparison-'+w+'.png'});
 await fs.writeFile(root+'/locked-comparison-'+w+'.json',JSON.stringify(comparison,null,2));
 await p.click('#compareDialog [data-close]',{label:'비교 종료 선택 보존'});
}
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await stable('sequence');
const declarations=await p.evaluate(()=>{
 const probes={'#sequenceTime':['font-family','font-size','font-weight'],'#compareTime':['font-family'],'.skip-link':['color','background-color','padding'],'.lt-timeline-controls>summary':['padding','font-size'],'.clip-row input':['padding','font-size'],'#compareButton':['padding','min-height','font-weight'],'#audioInfo svg':['background-color'],'#audioInfo polyline':['stroke'],'#preferenceForm input[name=value]':['color','padding'],'#preferencesDialog':['color']};
 return Object.entries(probes).map(([selector,props])=>{const el=document.querySelector(selector);if(!el)return {selector,missing:true};const computed=getComputedStyle(el),matches=[];
  function walk(rules,source){for(const rule of rules){if(rule instanceof CSSMediaRule&&!matchMedia(rule.conditionText).matches)continue;if(rule.cssRules){walk(rule.cssRules,source);continue}if(!rule.selectorText)continue;let match=false;try{match=el.matches(rule.selectorText)}catch{}if(!match)continue;const declarations=Object.fromEntries(props.map(prop=>[prop,rule.style.getPropertyValue(prop)]).filter(x=>x[1]));if(Object.keys(declarations).length)matches.push({source,selector:rule.selectorText,declarations})}}
  for(const sheet of document.styleSheets)walk(sheet.cssRules,sheet.href?new URL(sheet.href).pathname:'inline');
  return {selector,computed:Object.fromEntries(props.map(prop=>[prop,computed.getPropertyValue(prop)])),inline:el.getAttribute('style'),attributes:{stroke:el.getAttribute('stroke')},matchingRulesInSourceOrder:matches};
 });
});
await fs.writeFile(root+'/active-declaration-candidates.json',JSON.stringify(declarations,null,2));
console.log(await p.snapshot());
