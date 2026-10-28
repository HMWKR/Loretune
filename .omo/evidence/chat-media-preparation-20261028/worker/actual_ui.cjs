'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {createRequire}=require('node:module');
const puppeteer=createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const OUT=__dirname,ROOT=path.resolve(OUT,'../../../..');
const setup=JSON.parse(fs.readFileSync(path.join(OUT,'ready.json'),'utf8'));
const origin='http://127.0.0.1:'+setup.port;
const save=(name,value)=>fs.writeFileSync(path.join(OUT,name),JSON.stringify(value,null,2)+'\n');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,p))).digest('hex');
async function main(){
 const denied=await new Promise(resolve=>{const socket=require('node:net').createConnection({host:'1.1.1.1',port:443});socket.setTimeout(500);socket.on('error',error=>{socket.destroy();resolve(error.code)});socket.on('connect',()=>{socket.destroy();resolve('CONNECTED')});socket.on('timeout',()=>{socket.destroy();resolve('TIMEOUT')});});
 assert.ok(['EPERM','EACCES'].includes(denied),'Browser harness external IP must be denied by OS policy');
 save('browser-network-denial.json',{external_ip_probe_error:denied,policy:'Loopback IP and local Unix sockets only; all other network denied'});
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,userDataDir:path.join(OUT,'browser-profile'),args:['--no-sandbox','--disable-background-networking','--disable-component-update','--no-first-run']});
 save('browser-start.json',{pid:browser.process().pid,source_hashes:{'chat_general.py':hash('chat_general.py'),'general-chat-ui.js':hash('general-chat-ui.js')}});
 const events=[],errors=[],failed=[],blocked=[];let page;
 try{
  page=await browser.newPage();await page.setViewport({width:1920,height:1080});
  page.on('pageerror',error=>errors.push({name:error.name,message:error.message}));
  page.on('requestfailed',request=>failed.push({method:request.method(),url:request.url(),error:request.failure()?.errorText}));
  page.on('response',response=>{if(response.request().method()==='POST'){const body=JSON.parse(response.request().postData()||'{}');events.push({action:body.action,request_id:body.request_id,status:response.status(),data_fields:Object.keys(body.data||{})});}});
  await page.setRequestInterception(true);
  page.on('request',request=>{
   const url=request.url();
   if(!url.startsWith(origin+'/')&&!url.startsWith('data:')&&!url.startsWith('blob:')&&url!=='about:blank'){blocked.push({url});return request.abort();}
   return request.continue();
  });
  const idle=()=>page.waitForFunction(()=>!busy&&!pendingId());
  const inspect=()=>page.evaluate(()=>({project:song(),conversation:project().active_conversation.id,settings:project().agent_preferences.current,
   cards:project().media_actions,card_text:document.getElementById('mediaActionCards').innerText,
   turns:project().general_chat_turns.map(t=>({id:t.id,status:t.status,round:t.round,billing_confirmed:t.billing_confirmed})),
   preview_scope:project().general_chat_previews.at(-1)?.tool_scope,source_audio_count:project().audio_versions.length,
   image_takes:project().shots['장면 1'].takes.length,generation_jobs:state.generation_jobs.length,local_jobs:state.jobs.length,
   active_element:document.activeElement.id||document.activeElement.textContent.slice(0,80),
   body_scroll_width:document.documentElement.scrollWidth,viewport_width:innerWidth}));
  await page.goto(origin+'/',{waitUntil:'networkidle0'});await page.waitForFunction(()=>!!project());
  await page.click('.flow-nav [data-step="3"]');await idle();
  const before=await inspect();assert.equal(before.cards.length,0);assert.equal(before.image_takes,0);
  await page.focus('#generalChatPrompt');await page.type('#generalChatPrompt','현재 음원 장면의 이미지 제작안을 준비해 주세요. 생성은 실행하지 마세요.');
  await page.keyboard.press('Tab');
  const keyboard=await page.evaluate(()=>({focus:document.activeElement.id,prompt:document.getElementById('generalChatPrompt').value}));
  await page.click('#generalChatPrepare');
  await page.waitForFunction(()=>project().general_chat_previews.some(p=>p.state==='pending'));await idle();
  const label=await page.$eval('#generalChatReviews',e=>e.innerText);
  assert.ok(label.includes('모델 기능 목록 조회'));assert.ok(label.includes('이미지 제작안 준비 · 실행 없음'));assert.ok(!label.includes('확인 필요'));
  save('initial-manifest-labels.json',{keyboard,label,scope:await page.evaluate(()=>project().general_chat_previews.at(-1).tool_scope)});
  for(let round=0;round<3;round++){
   const id=await page.evaluate(()=>project().general_chat_previews.at(-1).id);
   await page.click('[data-rights="'+id+'"]');
   await page.click('[data-general-decision="approve"][data-preview="'+id+'"]');
   if(round<2)await page.waitForFunction(old=>project().general_chat_turns.at(-1)?.status==='awaiting_continuation_approval'&&project().general_chat_previews.some(p=>p.state==='pending'&&p.id!==old),{},id);
   else await page.waitForFunction(()=>project().general_chat_turns.at(-1)?.status==='completed');
   await idle();save('round-'+(round+1)+'.json',await inspect());
  }
  const prepared=await inspect();assert.equal(prepared.cards.length,1);assert.equal(prepared.cards[0].approval,'required');assert.equal(prepared.cards[0].can_execute,false);assert.equal(prepared.cards[0].can_approve,false);
  assert.equal(prepared.image_takes,0);assert.equal(prepared.generation_jobs,0);assert.equal(prepared.local_jobs,0);
  const id=prepared.cards[0].id;
  const capture=[];
  for(const width of [1920,1280,375]){
   await page.setViewport({width,height:width===375?812:1080});
   await page.$eval('[data-action-card="'+id+'"]',e=>e.scrollIntoView({block:'center'}));
   await new Promise(resolve=>setTimeout(resolve,100));
   const rect=await page.$eval('[data-action-card="'+id+'"]',e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,scroll_width:e.scrollWidth,client_width:e.clientWidth,text:e.innerText};});
   const state=await inspect();capture.push({width,rect,body_scroll_width:state.body_scroll_width,viewport_width:state.viewport_width});
   await page.screenshot({path:path.join(OUT,'prepared-card-'+width+'.png')});
  }
  save('responsive-card-observations.json',capture);
  await page.setViewport({width:1920,height:1080});
  await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>project()?.media_actions?.length===1);
  await page.click('.flow-nav [data-step="3"]');await idle();
  const reopened=await inspect();assert.equal(reopened.cards[0].id,id);assert.equal(reopened.cards[0].prompt,prepared.cards[0].prompt);
  assert.deepEqual(reopened.cards[0].estimate,prepared.cards[0].estimate);
  await page.click('[data-media-decision="held"][data-action="'+id+'"]');await page.waitForFunction(()=>project().media_actions[0].approval==='held');await idle();
  const held=await inspect();assert.equal(held.cards[0].can_execute,false);
  await page.click('[data-media-decision="rejected"][data-action="'+id+'"]');await page.waitForFunction(()=>project().media_actions[0].approval==='rejected');await idle();
  const rejected=await inspect();assert.equal(rejected.cards[0].can_execute,false);await page.screenshot({path:path.join(OUT,'rejected-card.png')});
  await page.click('.agent-preferences > summary');await page.select('#agentMode','read_only');await page.click('#agentPreferencesForm button');
  await page.waitForFunction(()=>project().agent_preferences.current.mode==='read_only');await idle();
  await page.click('#generalChatPrompt',{clickCount:3});await page.type('#generalChatPrompt','사용 가능한 이미지 모델 목록만 확인합니다.');await page.click('#generalChatPrepare');
  await page.waitForFunction(()=>project().general_chat_previews.some(p=>p.state==='pending'));await idle();
  const readonly=await inspect();assert.ok(readonly.preview_scope.includes('get_model_capabilities'));assert.ok(!readonly.preview_scope.includes('prepare_image_action'));
  const preview=await page.evaluate(()=>project().general_chat_previews.at(-1).id);
  await page.click('[data-general-decision="reject"][data-preview="'+preview+'"]');await idle();
  const final=await inspect();assert.equal(final.cards.length,1);assert.equal(final.cards[0].approval,'rejected');assert.equal(final.generation_jobs,0);assert.equal(final.image_takes,0);assert.equal(final.source_audio_count,before.source_audio_count);
  assert.deepEqual(errors,[]);assert.deepEqual(blocked,[]);
  save('actual-ui-result.json',{status:'PASS',engine:await browser.version(),origin,
   mode:'Real isolated platform UI and HTTP/SQLite; deterministic in-memory Claude and synthetic price adapter, no actual model execution',
   before,prepared,reopened,held,rejected,readonly,final,keyboard,events,errors,failed,blocked,
   responsive:capture,source_hashes:{'chat_general.py':hash('chat_general.py'),'general-chat-ui.js':hash('general-chat-ui.js')},
   actual_provider_calls:0,user_review_workspace_accessed:false,actual_token_fit_or_model_understanding_verified:false});
  console.log(JSON.stringify({status:'PASS',cards:final.cards.length,approval:final.cards[0].approval,events:events.length,errors:errors.length,failed:failed.length,blocked:blocked.length}));
 }catch(error){
  if(page){try{await page.screenshot({path:path.join(OUT,'actual-ui-failure.png')});save('actual-ui-failure-dom.json',await page.evaluate(()=>({url:location.href,text:document.body.innerText.slice(-22000),project:song(),busy,dirty})));}catch{}}
  save('actual-ui-failure.json',{name:error.name,message:error.message,events,errors,failed,blocked});throw error;
 }finally{await browser.close();}
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
