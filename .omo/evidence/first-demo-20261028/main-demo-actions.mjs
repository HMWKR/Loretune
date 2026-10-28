// Actual UI actions only. This module does not seed app data or create media.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {observeUntil} from './record-screen.mjs';

export function demoControls(page, mark, {projectName, evidenceDir}) {
 const query='/api/state?song='+encodeURIComponent(projectName);
 const state=async()=>JSON.parse((await page.fetch(query)).body);
 const project=async()=>(await state()).projects[projectName];
 const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
 async function stored(predicate, timeout=45000) {
  const end=Date.now()+timeout;
  while(Date.now()<end) {const value=await state();if(predicate(value)){await observeUntil(page,()=>!busy&&!pendingId());return value;}await sleep(120);}
  throw Error('Stored-state observation timed out; inspect before repeating any action.');
 }
 async function expose(selector) {
  await observeUntil(page,s=>{const node=document.querySelector(s);return !!node&&!busy&&!pendingId()&&!node.disabled;},selector);
  if(await page.evaluate(s=>!!document.querySelector(s)?.closest('#agentSettingsPane'),selector))await page.click('#agentSettingsTab');
  const closed=await page.evaluate(s=>{
   const target=document.querySelector(s);if(!target)throw Error('Missing UI target: '+s);
   const path=n=>{if(n.id)return '//*[@id="'+n.id+'"]';let parts=[];while(n&&n.nodeType===1){let i=1;for(let p=n.previousElementSibling;p;p=p.previousElementSibling)if(p.tagName===n.tagName)i++;parts.unshift(n.tagName.toLowerCase()+'['+i+']');n=n.parentElement;}return '/'+parts.join('/');};
   let n=target.parentElement,results=[];while(n){if(n.tagName==='DETAILS'&&!n.open)results.unshift('xpath='+path(n)+'/summary[1]');n=n.parentElement;}return results;
  },selector);
  for(const summary of closed){await page.focus(summary);await page.press(summary,'Enter');}
 }
 async function button(s){await expose(s);await page.focus(s);await page.press(s,'Enter');}
 async function fill(s,v){await expose(s);await page.focus(s);await page.fill(s,String(v));}
 async function choose(s,v){await expose(s);await page.focus(s);await page.selectOption(s,{value:String(v)});}
 async function stage(label){await page.click('loc=role:button[name="'+label+'"]');}
 async function saveState(filename){const value=await state();delete value.token;await fs.writeFile(evidenceDir+'/'+filename,JSON.stringify(value,null,2));return value;}
 async function approveTake(take,rights,reason) {
  await observeUntil(page,take=>!!document.querySelector('#takes [data-take="'+take+'"]')&&!busy&&!pendingId(),take);
  await button('#takes [data-take="'+take+'"]');
  await fill('#creatorTakeRightsEvidence',rights);await button('#creatorTakeRightsSubmit');
  await stored(s=>s.projects[projectName].shots['장면 1'].takes.find(t=>t.id===take)?.rights!=='사용권 미확인');
  if(await page.evaluate(()=>document.querySelector('#creatorReviewEditor').hidden))await button('#creatorEditReview');
  await fill('#reviewReason',reason);await choose('#takeDecision','approved');await button('#reviewTake');
  await stored(s=>s.projects[projectName].shots['장면 1'].reviews.some(r=>r.take===take&&r.decision==='approved'));
 }
 async function output(version,label) {
  await mark(label+'-approve-output',{timelineVersion:version});
  await button('#review');await button('#render');
  await observeUntil(page,()=>document.querySelector('#renderConfirm').open);
  await fs.writeFile(evidenceDir+'/'+label+'-confirmation.txt',await page.evaluate(()=>document.querySelector('#renderConfirm').innerText));
  await button('#confirmRender');
  const saved=await stored(s=>s.jobs.some(j=>!j.kind&&j.status==='completed'&&j.snapshot?.timeline?.id===version),90000);
  const job=saved.jobs.find(j=>!j.kind&&j.status==='completed'&&j.snapshot?.timeline?.id===version);
  await mark(label+'-output-completed',{jobId:job.id,timelineVersion:version,sha256:job.sha256});
  await button('#jobs [data-play="'+job.download+'"]');
  await observeUntil(page,()=>document.querySelector('#downloadPreview video')?.readyState>=2);
  await page.focus('#downloadPreview video');await page.press('#downloadPreview video','Space');
  await observeUntil(page,()=>document.querySelector('#downloadPreview video').currentTime>1&&!document.querySelector('#downloadPreview video').paused);
  await mark(label+'-actual-native-playback');
  await observeUntil(page,()=>document.querySelector('#downloadPreview video').ended,undefined,20000);
  const downloadPromise=page.waitForEvent('download',{timeout:30000});
  await page.click('#jobs a[href="'+job.download+'"][download]');const download=await downloadPromise;
  const dest=evidenceDir+'/'+label+'.mp4';await download.saveAs(dest);
  const bytes=await fs.readFile(dest),sha=crypto.createHash('sha256').update(bytes).digest('hex');
  if(sha!==job.sha256)throw Error('Downloaded output does not match persisted SHA');
  await fs.writeFile(evidenceDir+'/'+label+'-result.json',JSON.stringify({job,download:{path:dest,bytes:bytes.length,sha256:sha}},null,2));
  await mark(label+'-download-verified',{sha256:sha,bytes:bytes.length});return job;
 }
 return {state,project,stored,expose,button,fill,choose,stage,saveState,approveTake,output};
}

export async function musicOnlyDemo(page,mark,options) {
 const ui=demoControls(page,mark,options),name=options.projectName;
 const initial=JSON.parse((await page.fetch('/api/state')).body);if(Object.keys(initial.projects).length)throw Error('Main demo requires an actual empty workspace');
 await mark('empty-workspace-start',{projectCount:0,inputs:'Self-authored12s instrumental; optional NASA photograph not added yet; no AI model configured'});
 await ui.button('#emptyNewProject');await ui.fill('#project [name="name"]',name);await ui.button('#project button');
 await ui.stored(s=>!!s.projects[name]);
 await ui.button('#agentChatTab');await ui.fill('#generalChatPrompt','현재 음원과 편집 상태를 바탕으로 개선안을 제안해 주세요.');
 await ui.button('.agent-close');await ui.button('#agentToggle');
 const preserved=await page.evaluate(()=>document.querySelector('#generalChatPrompt').value);
 if(preserved!=='현재 음원과 편집 상태를 바탕으로 개선안을 제안해 주세요.')throw Error('Agent toggle lost the conversation draft');
 await page.focus('.agent-resizer');await page.press('.agent-resizer','ArrowLeft');await page.press('.agent-resizer','ArrowLeft');
 await ui.choose('#conversationModelSelect','anthropic-haiku-5-5');await ui.button('#conversationModel button');
 await ui.stored(s=>s.projects[name].agent_preferences?.current?.selection==='anthropic-haiku-5-5');
 await ui.choose('#agentMode','review');await ui.choose('#agentEffort','high');await ui.button('#agentPreferencesForm button');
 await ui.stored(s=>s.projects[name].agent_preferences.current.effort==='high');
 await mark('agent-panel-toggle-resize-and-model-settings',{mode:'review',effort:'high',selectedModel:'anthropic-haiku-5-5',externalModelCalls:0,draftPreserved:true});
 await ui.stage('1 음악 입력');await ui.expose('#audioUpload [name="file"]');
 await page.setInputFiles('#audioUpload [name="file"]',[options.inputDir+'/original-demo-music.wav']);
 await ui.fill('#audioUpload [name="rights"]','시연용 직접 작곡·합성 음원. AI 모델 미사용.');await ui.button('#audioUpload button');
 await ui.stored(s=>s.projects[name].audio_versions.length===1);
 await mark('audio-only-uploaded',{audioVersion:1,photos:0,models3D:0});
 await ui.fill('#musicStructure [name="start"]',1);await ui.fill('#musicStructure [name="end"]',13);await ui.button('#musicStructure button');
 await observeUntil(page,()=>document.querySelector('#notice')?.classList.contains('error'));
 await mark('music-range-error-visible',{inputEnd:13,sourceDuration:12});
 await ui.fill('#musicStructure [name="end"]',10);await ui.fill('#musicStructure [name="sections"]','1,4,인트로\n4,10,주제');await ui.button('#musicStructure button');
 await ui.stored(s=>s.projects[name].music_head===1);await mark('music-range-recovered',{musicVersion:1,start:1,end:10});
 await ui.stage('2 계획 검토');
 for(const [field,value]of Object.entries({goal:'음원에서 시작하는 음악 영상 · 사진과3D는 선택',style:'밝은 한글 타이포와 차분한 움직임',constraints:'음원·원본·이전 결과 보존. 실제AI모델 호출 없음.',scenes:'제목 타이포그래피\n사진을 선택하는 장면'}))await ui.fill('#guidedBrief [name="'+field+'"]',value);
 await ui.button('#guidedBrief button');await ui.stored(s=>s.projects[name].guided_plans?.length===1);
 await page.click('text="계획 승인·장면 추가"');await ui.stored(s=>Object.keys(s.projects[name].shots).length===2);
 await ui.stage('3 장면 제작·검토');await page.click('loc=role:button[name*="01 장면 1"]');await ui.button('#motionButton');await ui.button('#motionStart');
 for(const [field,value]of Object.entries({text:'함께 만드는\n우리의 리듬',font_size:96,height:280}))await ui.fill('[data-motion-field="'+field+'"]',value);
 for(const [key,values]of [[0,{x:160,y:160}],[1,{frame:24,x:240,y:220}]])for(const [field,value]of Object.entries(values))await ui.fill('[data-motion-key="'+key+'"] [data-motion-property="'+field+'"]',value);
 await ui.button('#motionSave');await ui.stored(s=>s.projects[name].motion_proposals?.length>0);
 await page.click('#motionFrame');await ui.button('#motionPreview');
 await observeUntil(page,()=>!document.querySelector('#motionImage').hidden&&document.querySelector('#motionImage').naturalWidth===1920);
 await mark('editable-typography-preview',{text:'함께 만드는 / 우리의 리듬',fontSize:96});
 await ui.button('#motionApprove');await ui.stored(s=>s.projects[name].shots['장면 1'].motion_head===1);
 await ui.button('#motionRender');await ui.stored(s=>s.projects[name].shots['장면 1'].takes.length===1,60000);
 await ui.button('#motionClose');await ui.approveTake(1,'직접 입력한 문구와 플랫폼 내부 렌더로 제작한 시연 후보','타이포·움직임과 자체 제작 근거 확인');
 await mark('native-take-one-selected-reviewed',{motionVersion:1,take:1});
 await ui.stage('4 편집·출력');await ui.expose('#clips [data-remove-clip="1"]');await ui.button('#clips [data-remove-clip="1"]');
 await ui.fill('#clips [data-clip="0"][data-field="duration"]',3);await ui.fill('#clips [data-clip="0"][data-field="trim"]',0);await ui.choose('#audioVersion',1);await ui.fill('#audioOffset',1);await ui.choose('#profile','landscape');
 await ui.button('#addCaption');for(const [field,value]of Object.entries({start:0,end:3,text:'함께 만드는 우리의 리듬'}))await ui.fill('#captions [data-caption="0"][data-field="'+field+'"]',value);
 await ui.button('#saveTimeline');await ui.stored(s=>s.projects[name].timeline_head===1);
 await ui.choose('#timelineFrameClip',0);await ui.fill('#timelineFrameTime',1.5);await ui.button('#timelineFrameView');
 await observeUntil(page,()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920);
 await mark('music-only-saved-frame-before-output-approval',{timelineVersion:1});
 const firstOutput=await ui.output(1,'music-only');await ui.saveState('after-music-only.json');
 return {...ui,firstOutput};
}

export async function optionalPhotoAndOverlayDemo(page,mark,options,ui) {
 const name=options.projectName;
 await ui.stage('3 장면 제작·검토');await page.click('loc=role:button[name*="01 장면 1"]');await ui.button('#motionButton');
 await ui.choose('#motionVersions',1);const old=await page.evaluate(()=>document.querySelector('#motionProposal').value);
 await ui.button('#motionRestore');await observeUntil(page,old=>!!document.querySelector('#motionProposal').value&&document.querySelector('#motionProposal').value!==old,old);
 for(const [field,value]of Object.entries({text:'음악 위에\n떠오르는 글자',font_size:112,height:336,color:'#E6C58B',out_frame:84}))await ui.fill('[data-motion-field="'+field+'"]',value);
 for(const [key,values]of [[0,{x:240,y:240}],[1,{frame:24,x:480,y:280}]])for(const [field,value]of Object.entries(values))await ui.fill('[data-motion-key="'+key+'"] [data-motion-property="'+field+'"]',value);
 const restored=await page.evaluate(()=>document.querySelector('#motionProposal').value);await ui.button('#motionSave');await observeUntil(page,old=>document.querySelector('#motionProposal').value!==old,restored);
 await page.click('#motionFrame');await ui.button('#motionPreview');await observeUntil(page,()=>!document.querySelector('#motionImage').hidden&&document.querySelector('#motionImage').naturalWidth===1920);
 await mark('typography-source-edited-preview',{fontSize:112,color:'#E6C58B',text:'음악 위에 / 떠오르는 글자',newPosition:[480,280],outFrame:84});
 await ui.button('#motionApprove');await ui.stored(s=>s.projects[name].shots['장면 1'].motion_head===2);
 await ui.button('#motionRender');await ui.stored(s=>s.projects[name].shots['장면 1'].takes.length===2,60000);
 await observeUntil(page,()=>project()?.shots?.['장면 1']?.takes?.length===2&&!busy&&!pendingId(),undefined,20000);await ui.button('#motionClose');
 await observeUntil(page,()=>!!document.querySelector('#takes [data-take="2"]')&&!busy&&!pendingId());
 await ui.button('#compareButton');await observeUntil(page,()=>document.querySelector('#compareDialog').open);await ui.choose('#compareLeft',1);await ui.choose('#compareRight',2);await ui.button('#compareTogether');
 await observeUntil(page,()=>{const a=document.querySelector('#compareLeftPreview video'),b=document.querySelector('#compareRightPreview video');return a&&b&&!a.paused&&!b.paused&&a.currentTime>1&&b.currentTime>1;});
 const compare=await page.evaluate(()=>['#compareLeftPreview','#compareRightPreview'].map(s=>{const v=document.querySelector(s+' video');return{time:v.currentTime,duration:v.duration,paused:v.paused,width:v.videoWidth,height:v.videoHeight}}));
 await fs.writeFile(options.evidenceDir+'/actual-take-comparison.json',JSON.stringify(compare,null,2));await mark('actual-two-take-comparison',{takes:[1,2],playback:compare});
 await ui.button('#compareTogether');await ui.button('#compareDialog [data-close]');
 await ui.approveTake(2,'직접 수정한 원본으로 플랫폼 내부에서 렌더한 시연 후보','문구·크기·색·위치·움직임 수정 전후 비교 완료');
 await page.click('loc=role:button[name*="02 장면 2"]');await ui.expose('#upload [name="asset"]');
 await page.setInputFiles('#upload [name="asset"]',[options.inputDir+'/nasa-earth-demo.jpg']);
 await ui.fill('#upload [name="reason"]','음원 단독 경로를 완료한 뒤 선택적으로 사진 추가');await ui.fill('#upload [name="rights"]','NASA PIA18033 · NASA/JPL-Caltech/Suomi NPP/VIIRS · 출처 표기 시연용; 보증·홍보 연계 없음.');await ui.button('#upload button');
 await ui.stored(s=>s.projects[name].shots['장면 2'].takes.length===1);await ui.button('#takes [data-take="1"]');
 if(await page.evaluate(()=>document.querySelector('#creatorReviewEditor').hidden))await ui.button('#creatorEditReview');
 await ui.fill('#reviewReason','선택한 사진과 출처·표시를 확인했습니다.');await ui.choose('#takeDecision','approved');await ui.button('#reviewTake');
 await ui.stored(s=>s.projects[name].shots['장면 2'].reviews.some(r=>r.take===1&&r.decision==='approved'));
 await mark('optional-photo-added-after-music-only-output',{shot:'장면 2',take:1});
 await ui.stage('4 편집·출력');await ui.choose('#clips [data-clip="0"][data-field="take"]',2);
 for(const shot of ['장면 2','장면 1']){await ui.choose('#addClipShot',shot);await ui.button('#addClip');}
 await ui.choose('#clips [data-clip="2"][data-field="take"]',1);await ui.button('#clips [data-move="1"][data-dir="-1"]');
 for(const i of [0,1,2])await ui.fill('#clips [data-clip="'+i+'"][data-field="duration"]',3);
 for(const i of [0,2]){
  const selector='details[data-overlay-panel="'+i+'"] > summary';
  if(!await page.evaluate(i=>document.querySelector('details[data-overlay-panel="'+i+'"]').open,i))await ui.button(selector);
  await ui.choose('[data-overlay-clip="'+i+'"][data-overlay-field="source"]',JSON.stringify(['장면 1',2]));
  for(const [field,value]of Object.entries({start:i===0?.5:0,end:i===0?2.5:2,offset_x:i===0?260:-80,offset_y:i===0?500:300}))await ui.fill('[data-overlay-clip="'+i+'"][data-overlay-field="'+field+'"]',value);
 }
 await ui.fill('#captions [data-caption="0"][data-field="text"]','음악으로 시작하는 나의 영상');
 for(const [i,start,end,text]of [[1,3,6,'타이포 원본을 수정하고'],[2,6,9,'사진과 영상 위에 글자를 배치해요']]){
  await ui.button('#addCaption');for(const [field,value]of Object.entries({start,end,text}))await ui.fill('#captions [data-caption="'+i+'"][data-field="'+field+'"]',value);
 }
 await ui.button('#saveTimeline');await ui.stored(s=>s.projects[name].timeline_head===2);
 await ui.choose('#timelineFrameClip',0);await ui.fill('#timelineFrameTime',1.5);await ui.button('#timelineFrameView');
 await observeUntil(page,()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920);
 await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:options.evidenceDir+'/photo-overlay-before.png'});
 await mark('photo-overlay-before-position-time-edit',{timelineVersion:2,clip:0,time:1.5,offset:[260,500],start:.5,end:2.5});
 for(const [field,value]of Object.entries({offset_x:-320,offset_y:-200,start:.75,end:2.75}))await ui.fill('[data-overlay-clip="0"][data-overlay-field="'+field+'"]',value);
 const guard=await page.evaluate(()=>({hidden:document.querySelector('#timelineFrameImage').hidden,disabled:document.querySelector('#timelineFrameView').disabled}));
 if(!guard.hidden||!guard.disabled)throw Error('Unsaved overlay displayed as saved preview');await mark('unsaved-composite-preview-protected',guard);
 await ui.button('#saveTimeline');await ui.stored(s=>s.projects[name].timeline_head===3);await ui.button('#timelineFrameView');
 await observeUntil(page,()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920);
 await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:options.evidenceDir+'/photo-overlay-after.png'});
 await mark('photo-overlay-after-position-time-edit',{timelineVersion:3,clip:0,time:1.5,offset:[-320,-200],start:.75,end:2.75});
 await ui.choose('#timelineFrameClip',2);await ui.fill('#timelineFrameTime',1.5);await ui.button('#timelineFrameView');
 await observeUntil(page,()=>!document.querySelector('#timelineFrameImage').hidden&&document.querySelector('#timelineFrameImage').naturalWidth===1920);
 await page.fetch(await page.evaluate(()=>document.querySelector('#timelineFrameImage').src),{saveAs:options.evidenceDir+'/video-overlay.png'});await mark('actual-existing-video-overlay-before-output-approval',{timelineVersion:3,clip:2,time:1.5});
 const output=await ui.output(3,'music-photo-typography');await ui.saveState('after-music-photo-overlay.json');return output;
}

export async function reopenDemo(page,mark,options,output) {
 const before=JSON.parse((await page.fetch('/api/state?song='+encodeURIComponent(options.projectName))).body);
 await mark('reload-and-reopen-start',{timelineVersion:3,outputJob:output.id});
 await page.reload();
 await observeUntil(page,()=>!!document.querySelector('#agentSidebar')&&document.querySelector('#songs')?.value,undefined,20000);
 const ui=demoControls(page,mark,options);const after=await ui.stored(s=>s.projects[options.projectName]?.timeline_head===3);
 const project=after.projects[options.projectName],old=before.projects[options.projectName];
 if(JSON.stringify(project.timeline_versions)!==JSON.stringify(old.timeline_versions)||project.shots['장면 1'].motion_head!==2||project.shots['장면 1'].takes.length!==2)throw Error('Reopen did not preserve editable source/timeline');
 const persisted=after.jobs.find(j=>j.id===output.id);if(persisted?.status!=='completed'||persisted.sha256!==output.sha256)throw Error('Reopened output changed');
 await ui.stage('4 편집·출력');await ui.button('#jobs [data-play="'+output.download+'"]');
 await observeUntil(page,()=>document.querySelector('#downloadPreview video')?.readyState>=2);
 await ui.button('#agentChatTab');
 const values=await page.evaluate(()=>({prompt:document.querySelector('#generalChatPrompt').value,mode:document.querySelector('#agentMode').value,effort:document.querySelector('#agentEffort').value,model:document.querySelector('#conversationModelSelect').value,width:document.querySelector('.agent-resizer').getAttribute('aria-valuenow')}));
 if(values.effort!=='high'||values.model!=='anthropic-haiku-5-5')throw Error('Model settings changed on reopen');
 await fs.writeFile(options.evidenceDir+'/reopen-result.json',JSON.stringify({sourceVersion:2,timelineVersion:3,outputId:output.id,sha256:output.sha256,agent:values},null,2));
 await ui.saveState('after-reopen.json');await mark('reopen-preserves-source-edit-output-and-chat',values);
}
