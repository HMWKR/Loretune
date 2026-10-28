const fs = await import('node:fs/promises');
const out='/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028';
const task=await taskSpace(91), page=task.page('p1');
const name='1차 시연 리허설';
const state=async()=>JSON.parse((await page.fetch('/api/state?song='+encodeURIComponent(name))).body);
async function keyButton(selector){await page.focus(selector);await page.press(selector,'Enter');}
async function stored(version){await page.waitForFunction(async ({name,version})=>{const s=await(await fetch('/api/state?song='+encodeURIComponent(name))).json();return s.projects[name]?.timeline_head===version;},{name,version});}
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await page.waitForFunction(()=>document.body.dataset.desktopShell==='bounded');
await page.click('loc=role:button[name="4 편집·출력"]');
if(!await page.evaluate(()=>document.querySelector('details.lt-timeline-controls').open))await page.click('details.lt-timeline-controls > summary');
console.log({stage:'three-cuts'});
await page.selectOption('#clips [data-clip="0"][data-field="take"]',{value:'2'});
await page.selectOption('#addClipShot',{value:'장면 2'});await keyButton('#addClip');
await page.selectOption('#addClipShot',{value:'장면 1'});await keyButton('#addClip');
await page.selectOption('#clips [data-clip="2"][data-field="take"]',{value:'1'});
await page.click('#clips [data-move="1"][data-dir="-1"]');
for(const index of [0,1,2])await page.fill(`#clips [data-clip="${index}"][data-field="duration"]`,'3');
console.log({stage:'image-and-video-overlays'});
for(const index of [0,2]){
  await page.click(`details[data-overlay-panel="${index}"] > summary`);
  await page.selectOption(`[data-overlay-clip="${index}"][data-overlay-field="source"]`,{value:JSON.stringify(['장면 1',2])});
  await page.fill(`[data-overlay-clip="${index}"][data-overlay-field="start"]`,index===0?'0.5':'0');
  await page.fill(`[data-overlay-clip="${index}"][data-overlay-field="end"]`,index===0?'2.5':'2');
  await page.fill(`[data-overlay-clip="${index}"][data-overlay-field="offset_x"]`,index===0?'260':'-80');
  await page.fill(`[data-overlay-clip="${index}"][data-overlay-field="offset_y"]`,index===0?'500':'300');
}
await page.fill('#captions [data-caption="0"][data-field="text"]','음악으로 시작하는 나의 영상');
for(const [index,start,end,text] of [[1,3,6,'타이포 원본을 수정하고'],[2,6,9,'숫자로 위치와 시간을 바꿔요']]){
  await keyButton('#addCaption');
  await page.fill(`#captions [data-caption="${index}"][data-field="start"]`,String(start));
  await page.fill(`#captions [data-caption="${index}"][data-field="end"]`,String(end));
  await page.fill(`#captions [data-caption="${index}"][data-field="text"]`,text);
}
await keyButton('#saveTimeline');await stored(2);
await page.selectOption('#timelineFrameClip',{value:'0'});await page.fill('#timelineFrameTime','1.5');await keyButton('#timelineFrameView');
await page.waitForFunction(()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920,undefined,{timeout:15000});
await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:out+'/rehearsal-photo-overlay-before.png'});
console.log({stage:'change-position-and-display-time'});
await page.fill('[data-overlay-clip="0"][data-overlay-field="offset_y"]','300');
await page.fill('[data-overlay-clip="0"][data-overlay-field="start"]','0.75');
await page.fill('[data-overlay-clip="0"][data-overlay-field="end"]','2.75');
const dirty=await page.evaluate(()=>({oldPreviewHidden:document.querySelector('#timelineFrameImage').hidden,previewDisabled:document.querySelector('#timelineFrameView').disabled,status:document.querySelector('#timelineFrameStatus').textContent}));
await fs.writeFile(out+'/rehearsal-overlay-dirty-guard.json',JSON.stringify(dirty,null,2));
if(!dirty.oldPreviewHidden||!dirty.previewDisabled)throw new Error('Unsaved preview guard failed');
await keyButton('#saveTimeline');await stored(3);await keyButton('#timelineFrameView');
await page.waitForFunction(()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920,undefined,{timeout:15000});
await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:out+'/rehearsal-photo-overlay-after.png'});
const saved=await state();delete saved.token;
await fs.writeFile(out+'/rehearsal-overlay-state.json',JSON.stringify(saved,null,2));
console.log({stage:'saved-overlay-v3',timeline:saved.projects[name].timeline_versions.at(-1)});
