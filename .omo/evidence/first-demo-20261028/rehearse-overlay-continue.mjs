const fs=await import('node:fs/promises');
const out='/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028';
const t=await taskSpace(91),p=t.page('p1'),name='1차 시연 리허설';
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.waitForFunction(()=>document.body.dataset.desktopShell==='bounded');
const before=JSON.parse((await p.fetch('/api/state?song='+encodeURIComponent(name))).body);
if(before.projects[name].timeline_head!==1)throw Error('Stored timeline changed; inspect before continuing');
const draft=await p.evaluate(()=>[...document.querySelectorAll('#clips [data-field="duration"]')].map(n=>({index:n.dataset.clip,duration:n.value,take:document.querySelector(`#clips [data-clip="${n.dataset.clip}"][data-field="take"]`).value})));
if(JSON.stringify(draft)!==JSON.stringify([{index:'0',duration:'3',take:'1'},{index:'1',duration:'3',take:'2'},{index:'2',duration:'3',take:'1'}]))throw Error('Unexpected live draft; no replay');
async function key(s){await p.focus(s);await p.press(s,'Enter');}
for(const i of [0,2]){
 const summary=`details[data-overlay-panel="${i}"] > summary`;
 if(!await p.evaluate(i=>document.querySelector(`details[data-overlay-panel="${i}"]`).open,i))await key(summary);
 await p.focus(`[data-overlay-clip="${i}"][data-overlay-field="source"]`);
 await p.selectOption(`[data-overlay-clip="${i}"][data-overlay-field="source"]`,{value:JSON.stringify(['장면 1',2])});
 for(const [field,value] of Object.entries({start:i===0?'0.5':'0',end:i===0?'2.5':'2',offset_x:i===0?'260':'-80',offset_y:i===0?'500':'300'})){
  const s=`[data-overlay-clip="${i}"][data-overlay-field="${field}"]`;await p.focus(s);await p.fill(s,value);
 }
}
await p.focus('#captions [data-caption="0"][data-field="text"]');await p.fill('#captions [data-caption="0"][data-field="text"]','음악으로 시작하는 나의 영상');
for(const [i,start,end,text] of [[1,3,6,'타이포 원본을 수정하고'],[2,6,9,'숫자로 위치와 시간을 바꿔요']]){
 await key('#addCaption');
 for(const [field,value] of Object.entries({start:String(start),end:String(end),text})){const s=`#captions [data-caption="${i}"][data-field="${field}"]`;await p.focus(s);await p.fill(s,value);}
}
await key('#saveTimeline');
await p.waitForFunction(async name=>(await(await fetch('/api/state?song='+encodeURIComponent(name))).json()).projects[name].timeline_head===2,name);
await p.focus('#timelineFrameClip');await p.selectOption('#timelineFrameClip',{value:'0'});await p.fill('#timelineFrameTime','1.5');await key('#timelineFrameView');
await p.waitForFunction(()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920,undefined,{timeout:15000});
await p.fetch(await p.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:out+'/rehearsal-photo-overlay-before.png'});
console.log({stage:'saved-v2-preview-before'});
const overlaySummary='details[data-overlay-panel="0"] > summary';
if(!await p.evaluate(()=>document.querySelector('details[data-overlay-panel="0"]').open))await key(overlaySummary);
for(const [field,value] of Object.entries({offset_y:'300',start:'0.75',end:'2.75'})){const s=`[data-overlay-clip="0"][data-overlay-field="${field}"]`;await p.focus(s);await p.fill(s,value);}
const dirty=await p.evaluate(()=>({oldPreviewHidden:document.querySelector('#timelineFrameImage').hidden,previewDisabled:document.querySelector('#timelineFrameView').disabled,status:document.querySelector('#timelineFrameStatus').textContent}));
await fs.writeFile(out+'/rehearsal-overlay-dirty-guard.json',JSON.stringify(dirty,null,2));if(!dirty.oldPreviewHidden||!dirty.previewDisabled)throw Error('Dirty preview guard failed');
await key('#saveTimeline');await p.waitForFunction(async name=>(await(await fetch('/api/state?song='+encodeURIComponent(name))).json()).projects[name].timeline_head===3,name);
await key('#timelineFrameView');await p.waitForFunction(()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920,undefined,{timeout:15000});
await p.fetch(await p.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:out+'/rehearsal-photo-overlay-after.png'});
await p.focus('#timelineFrameClip');await p.selectOption('#timelineFrameClip',{value:'2'});await p.fill('#timelineFrameTime','1.5');await key('#timelineFrameView');
await p.waitForFunction(()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920,undefined,{timeout:15000});
await p.fetch(await p.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:out+'/rehearsal-video-overlay.png'});
const after=JSON.parse((await p.fetch('/api/state?song='+encodeURIComponent(name))).body);delete after.token;
await fs.writeFile(out+'/rehearsal-overlay-state.json',JSON.stringify(after,null,2));
console.log({stage:'saved-v3-photo-and-video-overlay',timeline:after.projects[name].timeline_versions.at(-1)});
console.log(await p.snapshot());
