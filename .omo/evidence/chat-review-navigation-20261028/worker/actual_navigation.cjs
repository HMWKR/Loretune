'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {createRequire}=require('node:module'),{execFileSync}=require('node:child_process');
const puppeteer=createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const OUT=__dirname,ROOT=path.resolve(OUT,'../../../..');
const setup=JSON.parse(fs.readFileSync(path.join(OUT,'ready.json'),'utf8'));
const origin='http://127.0.0.1:'+setup.port;
const attempt='attempt-'+new Date().toISOString().replaceAll(':','-').replaceAll('.','-');
const E=path.join(OUT,attempt);fs.mkdirSync(E);
const save=(name,value)=>fs.writeFileSync(path.join(E,name),JSON.stringify(value,null,2)+'\n');
const digest=value=>crypto.createHash('sha256').update(value).digest('hex');
const sources=()=>Object.fromEntries(['chat_general.py','general-chat-ui.js','chat-sidebar.js','index.html','motion-studio.js','scene-studio.js'].map(p=>[p,digest(fs.readFileSync(path.join(ROOT,p)))]));
const database=()=>JSON.parse(execFileSync('python3',[path.join(OUT,'read_snapshot.py')],{encoding:'utf8'}));
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function main(){
 const denied=await new Promise(resolve=>{const socket=require('node:net').createConnection({host:'1.1.1.1',port:443});socket.setTimeout(500);socket.on('error',error=>{socket.destroy();resolve(error.code)});socket.on('connect',()=>{socket.destroy();resolve('CONNECTED')});socket.on('timeout',()=>{socket.destroy();resolve('TIMEOUT')});});
 assert.ok(['EPERM','EACCES'].includes(denied),'OS network restriction required');
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,userDataDir:path.join(E,'browser-profile'),args:['--no-sandbox','--disable-background-networking','--disable-component-update','--no-first-run']});
 const sourceStart=sources();save('start.json',{browser_pid:browser.process().pid,source_hashes:sourceStart,network_deny:denied,origin});
 let page,recording=false,captureTask,record;const events=[],errors=[],failed=[],blocked=[],observations=[],marks=[];
 const mark=label=>{const value={label,elapsed_seconds:record?(Date.now()-record.startedAt)/1000:null,post_count:events.length};marks.push(value);console.log(label);};
 try{
  page=await browser.newPage();await page.setViewport({width:1920,height:1080});
  page.on('pageerror',error=>errors.push(error.message));
  page.on('requestfailed',request=>failed.push({method:request.method(),url:request.url(),error:request.failure()?.errorText}));
  page.on('response',response=>{if(response.request().method()==='POST'){const body=JSON.parse(response.request().postData()||'{}');events.push({action:body.action,request_id:body.request_id,status:response.status(),data_fields:Object.keys(body.data||{})});}});
  await page.setRequestInterception(true);
  page.on('request',request=>{const url=request.url();if(!url.startsWith(origin+'/')&&!url.startsWith('data:')&&!url.startsWith('blob:')&&url!=='about:blank'){blocked.push(url);return request.abort();}return request.continue();});
  const idle=()=>page.waitForFunction(()=>!busy&&!pendingId());
  const chat=async()=>{if(await page.$eval('#agentChatTab',e=>e.getAttribute('aria-selected'))!=='true'||await page.$eval('#agentSidebar',e=>e.hidden))await page.click('#agentToggle');await page.waitForSelector('#generalChatPrompt',{visible:true});};
  const shot=async name=>{await page.$eval('#agentSidebar',e=>e.hidden).then(async hidden=>{if(!hidden&&await page.evaluate(()=>innerWidth<=900))await page.click('#agentToggle');});await page.click('#shotlist [data-shot="'+name+'"]');await page.waitForFunction(name=>shotName===name,{},name);};
  const cardState=()=>page.evaluate(()=>({shot:shotName,step:document.body.dataset.step,selected:document.getElementById('agentSettingsTab').getAttribute('aria-selected'),focused:document.activeElement.dataset.actionCard||document.activeElement.id,chat_draft:document.getElementById('generalChatPrompt').value,open_dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>e.id),cards:project().media_actions.map(a=>({id:a.id,approval:a.approval,shot:a.shot})),turns:project().general_chat_turns.map(t=>({id:t.id,run_id:t.run_id,status:t.status})),jobs:state.jobs.length,generation_jobs:state.generation_jobs.length}));
  const capture=async name=>{await page.screenshot({path:path.join(E,name+'.png')});save(name+'.json',await cardState());};
  const startRecording=()=>{record={startedAt:Date.now(),frames:[],audio:'Silent actual platform screen capture; input fixture is 5s self-authored silence; no narration, editing, speedup, or omitted intervals.',captureError:null};recording=true;captureTask=(async()=>{try{while(recording){const capturedTimestamp=Date.now()/1000,filename='frame-'+String(record.frames.length).padStart(5,'0')+'.jpg';const bytes=await page.screenshot({type:'jpeg',quality:70});fs.writeFileSync(path.join(E,filename),bytes);record.frames.push({filename,sha256:digest(bytes),capturedTimestamp});await pause(160);}}catch(error){record.captureError=String(error);recording=false;}})();};
  const stopRecording=async()=>{if(!record)return;recording=false;await captureTask;record.finishedAt=Date.now();record.elapsedSeconds=(record.finishedAt-record.startedAt)/1000;record.markers=marks;save('recording.json',record);};
  await page.goto(origin+'/',{waitUntil:'networkidle0'});await page.waitForFunction(()=>!!project());
  await page.click('.flow-nav [data-step="3"]');await idle();await chat();
  assert.deepEqual(await page.evaluate(()=>Object.keys(project().shots)),['장면 1','장면 2']);
  await capture('baseline-platform-1920');
  const hasAction=await page.evaluate(()=>project().media_actions.length>0);
  startRecording();mark('시작 조건: 자체 5초 무음 음원, 사진 없음, 두 장면, 실제 Claude·이미지 생성 없음');await pause(700);
  if(!hasAction){
   await page.type('#generalChatPrompt','현재 음원 장면의 이미지 제작안을 준비해 주세요. 생성은 실행하지 마세요.',{delay:8});await page.click('#generalChatPrepare');
   await page.waitForFunction(()=>project().general_chat_previews.some(p=>p.state==='pending'));await idle();
   for(let round=0;round<3;round++){
    const id=await page.evaluate(()=>project().general_chat_previews.at(-1).id);
    mark('합성 대화 '+(round+1)+'차: 입력·권리·예산 범위 검토 후 승인');await pause(650);
    await page.click('[data-rights="'+id+'"]');await page.click('[data-general-decision="approve"][data-preview="'+id+'"]');
    if(round<2)await page.waitForFunction(old=>project().general_chat_turns.at(-1)?.status==='awaiting_continuation_approval'&&project().general_chat_previews.some(p=>p.state==='pending'&&p.id!==old),{},id);
    else await page.waitForFunction(()=>project().general_chat_turns.at(-1)?.status==='completed');
    await idle();
   }
  }else mark('재시도: 앞선 시도에서 저장한 합성 제작안과 완료 대화를 재사용');
  const action=await page.evaluate(()=>project().media_actions[0]),id=action.id,review='[data-general-review-action="'+id+'"]';
  assert.equal(action.role,'image');assert.equal(action.shot,'장면 1');
  await page.evaluate(()=>{window.reviewPromptNode=document.getElementById('generalChatPrompt');window.reviewChatNode=document.getElementById('agentChatPane');window.reviewFocusEvents=[];document.addEventListener('focusin',event=>reviewFocusEvents.push({kind:'focus',target:event.target.dataset.actionCard||event.target.id,at:performance.now()}));for(const d of document.querySelectorAll('dialog'))d.addEventListener('close',()=>reviewFocusEvents.push({kind:'close',dialog:d.id,at:performance.now()}));});
  await page.$eval('#generalChatPrompt',e=>{e.value='저장하지 않은 다음 대화 초안 · 이동 후에도 보존';e.dispatchEvent(new Event('input',{bubbles:true}));});
  const draft=await page.$eval('#generalChatPrompt',e=>e.value);
  await idle();const dbBefore=database(),postsBefore=events.length;save('navigation-database-before.json',dbBefore);
  const activate=async(key='Enter')=>{await page.focus(review);await page.keyboard.press(key);await page.waitForFunction(id=>document.activeElement.dataset.actionCard===id&&!document.getElementById('agentSettingsPane').hidden,{},id);await pause(120);assert.equal(await page.$eval('#generalChatPrompt',e=>e.value),draft);assert.equal(await page.evaluate(()=>reviewPromptNode===document.getElementById('generalChatPrompt')&&reviewChatNode===document.getElementById('agentChatPane')),true);};
  mark('제작안 저장 완료: 대화 결과의 명시적 장면 1 제작안 검토 버튼');await pause(650);
  await activate();mark('같은 장면의 정확한 기존 제작안 카드로 이동·포커스');observations.push({case:'same-shot Enter',state:await cardState()});await pause(700);
  // Close both real ancestor details by their existing summary controls.
  for(const selector of ['.production-card','#productionTools'])if(await page.$eval(selector,e=>e.open))await page.click(selector+' > summary');
  await chat();await page.focus(review);mark('접어 둔 제작 도구·장면 제작에서 같은 장면 검토 재진입');await pause(500);await activate();
  assert.equal(await page.$$eval('#productionTools,.production-card',nodes=>nodes.every(e=>e.open)),true);observations.push({case:'same-shot closed details opens and focuses',state:await cardState()});await pause(650);
  await shot('장면 2');await chat();mark('현재 장면 2에서 장면 1 제작안 검토 · Space');await pause(500);await activate('Space');
  assert.equal(await page.evaluate(()=>shotName),'장면 1');observations.push({case:'different-shot Space exact target',state:await cardState()});await pause(650);
  // Existing local-only editors: no save/render/approval operations.
  for(const [kind,dialog,launcher,selector,value] of [['motion','motionDialog','motionButton','[data-motion-field="text"]','저장 전 모션 초안 · 제작안 검토 후에도 유지'],['scene','sceneStudioDialog','sceneStudioButton','[data-scene-path="camera.lens_mm"]','73']]){
   await page.click('#agentSettingsTab');
   await page.click('#'+launcher);await page.waitForSelector('#'+dialog+'[open]');
   if(kind==='motion')await page.click('#motionStart');
   await page.$eval(selector,(input,value)=>{for(let p=input.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));},value);
   await page.click('#'+dialog+' .agent-dialog-launcher');await page.waitForSelector(review,{visible:true});
   mark((kind==='motion'?'모션 문구':'3D 카메라')+' 미저장 초안에서 대화 검토 버튼 이동');await pause(500);await activate();
   assert.equal(await page.$eval('#'+dialog,e=>e.open),false);observations.push({case:kind+' native close then exact card focus',state:await cardState()});
   await page.click('#'+launcher);await page.waitForSelector('#'+dialog+'[open]');assert.equal(await page.$eval(selector,e=>e.value),value);mark((kind==='motion'?'모션':'3D')+' 재열기: 미저장 초안 보존');await pause(450);
   await page.evaluate(id=>document.getElementById(id).close(),dialog);await page.waitForFunction(()=>!document.getElementById('agentChatPane').closest('dialog'));await pause(70);await chat();
  }
  assert.equal(events.length,postsBefore,'review movement/modal drafts must create no POST');const dbAfter=database();assert.deepEqual(dbAfter,dbBefore,'view and draft navigation must not mutate SQLite');save('navigation-database-after.json',dbAfter);
  await activate();mark('검토 이동만으로 승인·생성·예약·저장 API 호출 0');await pause(500);
  // Hold/reject are existing explicit decisions, distinct from view navigation.
  if(action.approval!=='rejected'){
   await page.click('[data-media-decision="held"][data-action="'+id+'"]');await page.waitForFunction(()=>project().media_actions[0].approval==='held');await idle();mark('명시적 보류: 생성 없음');
   await chat();const n=events.length;await activate();assert.equal(events.length,n);observations.push({case:'held saved card remains navigable without execution',state:await cardState()});await pause(500);
   await page.click('[data-media-decision="rejected"][data-action="'+id+'"]');await page.waitForFunction(()=>project().media_actions[0].approval==='rejected');await idle();mark('명시적 거절: 생성 없음');
  }
  await chat();const n=events.length;await activate();assert.equal(events.length,n);observations.push({case:'rejected saved card remains navigable without execution',state:await cardState()});mark('거절한 저장 카드도 정확하게 열림 · 대화 초안·기존 결과 보존');await pause(800);
  await stopRecording();
  save('navigation-observations.json',{observations,posts_before_navigation:postsBefore,posts_after_navigation:postsBefore,db_unchanged:true,focus_events:await page.evaluate(()=>reviewFocusEvents)});
  await capture('review-card-final-1920');
  const responsive=[];
  for(const width of [1920,1280,375]){
   await page.setViewport({width,height:width===375?900:1080});await pause(150);await chat();await page.focus(review);await page.keyboard.press('Enter');await page.waitForFunction(id=>document.activeElement.dataset.actionCard===id,{},id);await pause(150);
   const item=await page.$eval('[data-action-card="'+id+'"]',e=>{const r=e.getBoundingClientRect();return{rect:{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right},visible:!!e.getClientRects().length,body_scroll_width:document.documentElement.scrollWidth,viewport_width:innerWidth,focused:document.activeElement===e,text:e.innerText};});
   assert.ok(item.visible&&item.focused);assert.ok(item.rect.x>=-1&&item.rect.right<=width+1,'review card inside viewport');assert.ok(item.body_scroll_width<=width+1,'no horizontal body overflow');responsive.push({width,...item});await capture('review-card-'+width);
   await chat();await capture('review-button-'+width);assert.equal(await page.$eval('#generalChatPrompt',e=>e.value),draft);
  }
  await page.setViewport({width:1280,height:1080});
  // 200% page zoom through the installed Chrome protocol; no product styles changed.
  const cdp=await page.createCDPSession();await cdp.send('Emulation.setDeviceMetricsOverride',{width:640,height:540,deviceScaleFactor:1,mobile:false,scale:2});await pause(150);await chat();await page.focus(review);await page.keyboard.press('Enter');await page.waitForFunction(id=>document.activeElement.dataset.actionCard===id,{},id);await capture('review-card-200-percent');
  const zoom=await page.$eval('[data-action-card="'+id+'"]',e=>({focused:document.activeElement===e,visible:!!e.getClientRects().length,innerWidth,scrollWidth:document.documentElement.scrollWidth,visualScale:visualViewport.scale}));assert.ok(zoom.focused&&zoom.visible&&zoom.scrollWidth<=zoom.innerWidth+1);await cdp.send('Emulation.clearDeviceMetricsOverride');
  await page.setViewport({width:1920,height:1080});await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>project()?.media_actions?.length===1);await page.click('.flow-nav [data-step="3"]');await chat();assert.equal(await page.$eval('#generalChatPrompt',e=>e.value),draft);await page.evaluate(()=>{window.reviewPromptNode=document.getElementById('generalChatPrompt');window.reviewChatNode=document.getElementById('agentChatPane');});await activate();
  const final=await cardState();assert.equal(final.cards[0].id,id);assert.equal(final.cards[0].approval,'rejected');assert.equal(final.jobs,0);assert.equal(final.generation_jobs,0);assert.deepEqual(errors,[]);assert.deepEqual(blocked,[]);assert.deepEqual(sources(),sourceStart);
  save('actual-ui-result.json',{status:'PASS',engine:await browser.version(),mode:'Actual isolated platform DOM/UI + loopback HTTP + persisted SQLite. Synthetic deterministic Claude envelopes and quote only; no actual Claude/image/video/model/billing.',source_hashes:sourceStart,events,errors,failed,blocked,observations,responsive,zoom,final,recording:'recording.json',actual_provider_calls:0,no_user_workspace_access:true,no_new_approvals_or_jobs_by_navigation:true,post_navigation:0,database_unchanged_during_navigation:true,limits:['No actual model understanding or billing verified','Closed details regression verified in same-shot actual UI','200% uses Chrome device metrics scale=2 with half CSS viewport, equivalent reflow condition; not native browser menu zoom']});
  fs.writeFileSync(path.join(OUT,'successful-attempt.txt'),attempt+'\n');console.log(JSON.stringify({status:'PASS',attempt,frames:record.frames.length,seconds:record.elapsedSeconds,events:events.length}));
 }catch(error){
  if(recording){recording=false;await captureTask;record.finishedAt=Date.now();record.elapsedSeconds=(record.finishedAt-record.startedAt)/1000;record.markers=marks;save('recording.json',record);}
  if(page){try{await page.screenshot({path:path.join(E,'failure.png')});save('failure-dom.json',await page.evaluate(()=>({text:document.body.innerText.slice(-20000),shot:shotName,dirty,busy,focused:document.activeElement.outerHTML.slice(0,2000),openDialogs:[...document.querySelectorAll('dialog[open]')].map(x=>x.id)})));}catch{}}
  save('failure.json',{name:error.name,message:error.message,stack:error.stack,events,errors,failed,blocked,observations,marks});throw error;
 }finally{await browser.close();save('browser-stop.json',{closed:true,source_hashes:sources()});}
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
