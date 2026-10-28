const fs=await import('node:fs/promises');
const base='/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028',dir=base+'/main-demo-case-r3';
const {recordScreen,observeUntil}=await import('file://'+base+'/record-screen.mjs');
const {demoControls}=await import('file://'+base+'/main-demo-actions.mjs');
const task=await taskSpace(91),page=task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
const options={projectName:'1차 시연 · 음악에서 영상까지',evidenceDir:dir};
const before=JSON.parse((await page.fetch('/api/state?song='+encodeURIComponent(options.projectName))).body);
if(before.projects[options.projectName].timeline_head!==4)throw Error('Inspect current edit before layout refinement');
console.log(await recordScreen(page,dir+'/layout-refinement-take-01',async rawMark=>{
 const mark=async(name,detail={})=>{await rawMark(name,detail);await new Promise(r=>setTimeout(r,900));};
 const ui=demoControls(page,mark,options);
 await mark('manual-layout-refinement-start',{reason:'Recorded last-shot typography visually overlaps native subtitle. Reposition title layer, preserving captions, music and source versions.',realModelCalls:0});
 await ui.stage('4 편집·출력');
 for(const [clip,offset]of [[0,[-320,-200]],[2,[500,0]]]){
  const panel='details[data-overlay-panel="'+clip+'"] > summary';
  if(!await page.evaluate(i=>document.querySelector('details[data-overlay-panel="'+i+'"]').open,clip))await ui.button(panel);
  await ui.fill('[data-overlay-clip="'+clip+'"][data-overlay-field="offset_x"]',offset[0]);
  await ui.fill('[data-overlay-clip="'+clip+'"][data-overlay-field="offset_y"]',offset[1]);
 }
 await ui.button('#saveTimeline');await ui.stored(s=>s.projects[options.projectName].timeline_head===5);
 await ui.choose('#timelineFrameClip',2);await ui.fill('#timelineFrameTime',1.5);await ui.button('#timelineFrameView');
 await observeUntil(page,()=>!document.querySelector('#savedFramePreview').hidden&&!document.querySelector('#timelineFrameImage').hidden);
 await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:dir+'/layout-refined-video-frame.png'});
 await mark('separate-title-positions-saved',{timeline:5,clip:2,offset:[500,0]});
 const output=await ui.output(5,'layout-refined-output');
 await ui.saveState('after-layout-refinement.json');await page.reload();
 await observeUntil(page,()=>project()?.timeline_head===5&&draft?.id===5&&!busy&&!pendingId());
 await ui.stage('4 편집·출력');await ui.button('#jobs [data-play="'+output.download+'"]');
 await observeUntil(page,()=>document.querySelector('#downloadPreview video')?.readyState>=2);
 const after=await ui.saveState('after-layout-refinement-reopen.json'),p=after.projects[options.projectName],old=before.projects[options.projectName];
 if(JSON.stringify(p.shots)!==JSON.stringify(old.shots)||JSON.stringify(p.audio_versions)!==JSON.stringify(old.audio_versions)||old.timeline_versions.some((v,i)=>JSON.stringify(v)!==JSON.stringify(p.timeline_versions[i])))throw Error('Earlier sources/history changed during layout refinement');
 await fs.writeFile(dir+'/layout-refinement-preservation.json',JSON.stringify({priorVersions:4,finalVersion:5,priorSourcesAudioAndVersionsPreserved:true,outputId:output.id,outputSha256:output.sha256,realModelCalls:0,scope:'Manual platform UI composition adjustment after synthetic chat test; not another AI generation'},null,2));
 await mark('manual-layout-output-download-reopen-completed',{timeline:5,output:output.id,realModelCalls:0});
}));
console.log(await page.snapshot());
