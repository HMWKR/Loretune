'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {createRequire}=require('node:module');
const puppeteer=createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const OUT=__dirname,ROOT=path.resolve(OUT,'../../../../..');
const setup=JSON.parse(fs.readFileSync(path.join(OUT,'fixture-setup.json'),'utf8'));
const origin='http://127.0.0.1:'+setup.port;
const files=['index.html','studio.css','studio-media.js','general-chat-ui.js','chat-sidebar.js'];
const hashes=()=>Object.fromEntries(files.map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,f))).digest('hex')]));
const save=(name,v)=>fs.writeFileSync(path.join(OUT,name),JSON.stringify(v,null,2)+'\n');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--no-sandbox','--disable-background-networking']});
 const started=hashes(),events=[],errors=[],blocked=[];
 let page,checkpoint;
 try{
  page=await browser.newPage();await page.setViewport({width:1920,height:1080});
  page.on('pageerror',e=>errors.push({name:e.name,message:e.message}));
  await page.setRequestInterception(true);
  page.on('request',r=>{
   const url=r.url();if(!url.startsWith(origin+'/')&&!url.startsWith('data:')&&!url.startsWith('blob:')&&url!=='about:blank'){blocked.push({kind:'nonfixture-origin-request-blocked'});return r.abort();}
   if(r.method()==='POST')try{const value=JSON.parse(r.postData()||'{}');events.push({action:value.action,request_id:value.request_id,data_fields:Object.keys(value.data||{}),sha256:crypto.createHash('sha256').update(r.postData()||'').digest('hex')});}catch{}
   return r.continue();
  });
  const waitIdle=()=>page.waitForFunction(()=>!busy&&!pendingId());
  const inspect=()=>page.evaluate(()=>({head:project().timeline_head,draft_id:draft?.id,dirty,
   stored_overlay:project().timeline_versions.at(-1).clips[0].motion_overlay,draft_overlay:draft?.clips[0]?.motion_overlay,
   stored_caption:project().timeline_versions.at(-1).subtitles.at(-1)?.text,draft_caption:draft?.subtitles.at(-1)?.text,
   displayed_x:document.querySelector('[data-overlay-field="offset_x"]')?.value,displayed_y:document.querySelector('[data-overlay-field="offset_y"]')?.value,
   displayed_caption:document.querySelector('#captions input[data-field="text"]')?.value,
   displayed_versions:document.getElementById('versions').value,displayed_status:document.getElementById('timelineStatus').textContent,
   preflight:document.getElementById('preflight').textContent,sidebar_context:document.querySelector('.agent-scope-hint')?.textContent,
   stored_approval:!!project().timeline_versions.at(-1).approval,draft_approval:!!draft?.approval,
   current_settings:project().agent_preferences.current,turn_status:project().general_chat_turns.at(-1)?.status,
   pending_preview:project().general_chat_previews.at(-1)?.id}));
  await page.goto(origin+'/',{waitUntil:'networkidle0'});await page.waitForFunction(()=>!!project()&&!!draft);
  save('browser-start.json',{engine:await browser.version(),mode:'independent headless Chromium; separate user data',url:origin,source_hashes:started,start:await inspect()});
  // Continue the exact same DB left by the closed Ego92 lifecycle; no reset or duplicate seed.
  assert.equal(await page.evaluate(()=>project().agent_preferences.current.effort),'high');
  if(await page.evaluate(()=>project().agent_preferences.current.mode!=='full_access')){
   await page.click('.agent-preferences > summary');await page.select('#agentMode','full_access');await page.click('#agentPreferencesForm button');
   await page.waitForFunction(()=>project().agent_preferences.current.mode==='full_access');await waitIdle();
  }
  await page.click('.flow-nav [data-step="4"]');
  save('before-edit-ui.json',await inspect());await page.screenshot({path:path.join(OUT,'before-edit-ui.png')});
  let startRound=await page.evaluate(()=>project().general_chat_turns.at(-1)?.status==='awaiting_continuation_approval'?project().general_chat_turns.at(-1).round:0);
  if(startRound===0){
   await page.type('#generalChatPrompt','현재 작업을 확인하고 사진 위 타이포 위치와 마지막 자막을 바꿔줘');
   await page.click('#generalChatPrepare');await page.waitForFunction(()=>project().general_chat_previews.some(x=>x.state==='pending'));await waitIdle();
  }
  for(let round=startRound;round<3;round++){
   const id=await page.evaluate(()=>project().general_chat_previews.at(-1).id);
   await page.click('[data-rights="'+id+'"]');
   await page.click('[data-general-decision="approve"][data-preview="'+id+'"]');
   await page.waitForFunction(approved=>project().general_chat_turns.at(-1)?.status==='awaiting_continuation_approval'&&project().general_chat_previews.some(x=>x.state==='pending'&&x.id!==approved),{},id);
   await waitIdle();
   if(round<2)assert.equal((await inspect()).head,3);
   save('after-round-'+(round+1)+'.json',await inspect());
  }
  await page.waitForFunction(()=>project().timeline_head===4);
  checkpoint=await inspect();checkpoint.source_hashes=hashes();
  checkpoint.same_loaded_source=JSON.stringify(started)===JSON.stringify(checkpoint.source_hashes);
  checkpoint.match=checkpoint.head===checkpoint.draft_id&&checkpoint.displayed_x===String(checkpoint.stored_overlay.offset_x)&&checkpoint.displayed_caption===checkpoint.stored_caption;
  save('immediate-agent-draft-checkpoint.json',checkpoint);await page.screenshot({path:path.join(OUT,'immediate-agent-draft.png')});
  console.log(JSON.stringify({stage:'agent-draft-immediate-checkpoint',result:checkpoint}));
  const until=Date.now()+300000;
  while(!fs.existsSync(path.join(OUT,'continue-after-checkpoint.json'))&&Date.now()<until)await pause(200);
  if(Date.now()>=until)throw Error('Independent checkpoint continuation marker missing');
  const fourth=await page.evaluate(()=>project().general_chat_previews.at(-1).id);
  await page.click('[data-rights="'+fourth+'"]');await page.click('[data-general-decision="approve"][data-preview="'+fourth+'"]');
  await page.waitForFunction(()=>project().general_chat_turns.at(-1)?.status==='completed');await waitIdle();
  save('after-final-answer.json',await inspect());
  // A reload is recorded as a workaround only if the immediate rendered state was stale.
  let workaround=false;
  if(!(await inspect()).match&& (await inspect()).draft_id!==4){
   workaround=true;await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>draft?.id===4);await page.click('.flow-nav [data-step="4"]');
  }
  const current=await inspect();assert.equal(current.head,4);assert.equal(current.draft_id,4);assert.equal(current.displayed_x,'240');assert.equal(current.displayed_y,'120');assert.equal(current.displayed_caption,'음악의 여운을 이어서');assert.equal(current.stored_approval,false);assert.equal(current.draft_approval,false);
  save('before-separate-output-approval.json',{...current,reload_workaround:workaround});
  await page.click('#timelineFrameTime',{clickCount:3});await page.type('#timelineFrameTime','0.75');await page.click('#timelineFrameView');
  await page.waitForFunction(()=>!document.getElementById('timelineFrameImage').hidden&&document.getElementById('timelineFrameImage').naturalWidth>0);
  await page.screenshot({path:path.join(OUT,'draft-preview-before-output-approval.png')});
  await page.click('#review');await waitIdle();await page.waitForFunction(()=>!!project().timeline_versions.at(-1).approval);
  await page.click('#render');await page.waitForSelector('#renderConfirm[open]');await page.screenshot({path:path.join(OUT,'final-output-estimate.png')});
  await page.click('#confirmRender');await waitIdle();
  await page.waitForFunction(()=>state.jobs.some(j=>j.snapshot?.timeline?.id===4&&j.status==='completed'),{timeout:30000});
  const job=await page.evaluate(()=>state.jobs.find(j=>j.snapshot?.timeline?.id===4&&j.status==='completed'));
  await page.click('[data-play="'+job.download+'"]');await page.waitForSelector('#downloadPreview video');
  const video=await page.$('#downloadPreview video');await page.evaluate(video=>{video.muted=true;},video);
  await page.click('#downloadPreview video');await page.evaluate(video=>video.play(),video);
  await page.waitForFunction(()=>document.querySelector('#downloadPreview video')?.currentTime>.3);
  const playback=await page.$eval('#downloadPreview video',v=>({currentTime:v.currentTime,duration:v.duration,readyState:v.readyState,videoWidth:v.videoWidth,videoHeight:v.videoHeight,error:v.error?.code??null}));
  await page.screenshot({path:path.join(OUT,'actual-output-playing.png')});
  const client=await page.createCDPSession();await client.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.join(OUT,'downloads')});
  await page.click('a[href="'+job.download+'"][download]');
  const file=path.join(OUT,'downloads',job.id+'.mp4'),deadline=Date.now()+15000;
  while(!fs.existsSync(file)&&Date.now()<deadline)await pause(100);
  assert.ok(fs.existsSync(file));let sha=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');assert.equal(sha,job.sha256);
  await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>draft?.id===4);await page.click('.flow-nav [data-step="4"]');
  const reopened=await inspect();assert.equal(reopened.displayed_caption,'음악의 여운을 이어서');assert.equal(reopened.displayed_x,'240');
  save('result.json',{status:checkpoint.match?'PASS':'FAIL immediate UI state; remaining workflow passes after refresh/reload',checkpoint_match:checkpoint.match,reload_workaround:workaround,playback,job_id:job.id,output_sha256:sha,reopened,events,errors,blocked,source_start:started,source_end:hashes(),actual_provider_calls:0,main_data_accessed:false});
  console.log(JSON.stringify({stage:'finished',immediate_match:checkpoint.match,reload_workaround:workaround,playback,errors,blocked}));
 }catch(error){
  if(page){try{await page.screenshot({path:path.join(OUT,'failure.png')});save('failure-dom.json',await page.evaluate(()=>({url:location.href,visible:document.body.innerText.slice(-18000),stateHead:project()?.timeline_head,draftId:draft?.id,busy,dirty})));}catch{}}
  save('failure.json',{type:error.name,message:error.message,checkpoint,events,errors,blocked,source_start:started,source_end:hashes()});throw error;
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
