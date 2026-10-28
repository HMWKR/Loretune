'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const puppeteer=require('node:module').createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const OUT=__dirname,setup=JSON.parse(fs.readFileSync(path.join(OUT,'ready.json'),'utf8')),origin='http://127.0.0.1:'+setup.port;
const save=(name,value)=>fs.writeFileSync(path.join(OUT,name),JSON.stringify(value,null,2)+'\n');
async function main(){
 const denied=await new Promise(resolve=>{const socket=require('node:net').createConnection({host:'1.1.1.1',port:443});socket.setTimeout(500);socket.on('error',e=>{socket.destroy();resolve(e.code)});socket.on('connect',()=>{socket.destroy();resolve('CONNECTED')});socket.on('timeout',()=>{socket.destroy();resolve('TIMEOUT')});});assert.ok(['EPERM','EACCES'].includes(denied));
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,userDataDir:path.join(OUT,'browser-profile'),args:['--no-sandbox','--disable-background-networking','--disable-component-update','--no-first-run']});
 let page;const events=[],errors=[],blocked=[],failed=[];
 try{
  page=await browser.newPage();await page.setViewport({width:1920,height:1080});
  page.on('pageerror',e=>errors.push({name:e.name,message:e.message}));
  page.on('response',r=>{if(r.request().method()==='POST'){const v=JSON.parse(r.request().postData()||'{}');events.push({action:v.action,request_id:v.request_id,status:r.status()});}});
  page.on('requestfailed',r=>failed.push({method:r.method(),url:r.url(),error:r.failure()?.errorText}));
  await page.setRequestInterception(true);page.on('request',r=>{if(!r.url().startsWith(origin+'/')&&!r.url().startsWith('data:')&&!r.url().startsWith('blob:')&&r.url()!=='about:blank'){blocked.push({url:r.url()});return r.abort()}return r.continue()});
  const idle=()=>page.waitForFunction(()=>!busy&&!pendingId());
  const inspect=()=>page.evaluate(()=>({cards:project().media_actions,turns:project().general_chat_turns.map(t=>({id:t.id,status:t.status,round:t.round})),
   audio:project().audio_versions.map(a=>({id:a.id,sha256:a.sha256})),takes:project().shots['장면 1'].takes.length,generation_jobs:state.generation_jobs.length,local_jobs:state.jobs.length,
   settings:project().agent_preferences.current,scope:project().general_chat_previews.at(-1)?.tool_scope,viewport:innerWidth,scroll_width:document.documentElement.scrollWidth}));
  async function openCard(){
   await page.click('#agentSettingsTab');
   const closed=await page.$eval('#mediaActionCards',e=>{const a=[];for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)a.unshift(p.id);return a});
   for(const id of closed){assert.ok(id,'Disclosure needs observed public identifier');await page.click('#'+id+' > summary');}
   await page.waitForFunction(()=>document.querySelector('[data-action-card]')?.getBoundingClientRect().height>0);
  }
  await page.goto(origin+'/',{waitUntil:'networkidle0'});await page.waitForFunction(()=>project()?.media_actions?.length===1);await page.click('.flow-nav [data-step="3"]');await idle();
  const before=await inspect();assert.equal(before.cards.length,1);assert.equal(before.cards[0].approval,'required');assert.equal(before.turns.at(-1).status,'completed');
  const id=before.cards[0].id;assert.match(id,/^[a-f0-9]{32}$/);
  await openCard();const captures=[];
  for(const width of [1920,1280,375]){
   await page.setViewport({width,height:width===375?812:1080});
   await page.$eval('[data-action-card="'+id+'"]',e=>e.scrollIntoView({block:'center'}));await new Promise(r=>setTimeout(r,100));
   const rect=await page.$eval('[data-action-card="'+id+'"]',e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,text:e.innerText,scroll_width:e.scrollWidth,client_width:e.clientWidth,visible:!!r.width&&!!r.height}});
   assert.ok(rect.visible);assert.ok(rect.right<=width+1);assert.ok(rect.x>=-1);assert.ok(rect.scroll_width<=rect.client_width+1);
   captures.push({width,rect,state:await inspect()});await page.screenshot({path:path.join(OUT,'visible-card-'+width+'.png')});
  }
  await page.setViewport({width:1920,height:1080});await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>project()?.media_actions?.length===1);await page.click('.flow-nav [data-step="3"]');await idle();await openCard();
  const reopened=await inspect();assert.deepEqual(reopened.cards[0],before.cards[0]);
  const hold=await page.$('[data-media-decision="held"][data-action="'+id+'"]');await hold.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>project().media_actions[0].approval==='held');await idle();const held=await inspect();assert.equal(held.cards[0].can_execute,false);
  await page.click('[data-media-decision="rejected"][data-action="'+id+'"]');await page.waitForFunction(()=>project().media_actions[0].approval==='rejected');await idle();const rejected=await inspect();assert.equal(rejected.cards[0].can_execute,false);await page.screenshot({path:path.join(OUT,'visible-rejected-card.png')});
  await page.click('#agentChatTab');await page.click('.agent-preferences > summary');await page.select('#agentMode','read_only');await page.click('#agentPreferencesForm button');await page.waitForFunction(()=>project().agent_preferences.current.mode==='read_only');await idle();
  await page.click('#generalChatPrompt',{clickCount:3});await page.type('#generalChatPrompt','이미지 모델 목록만 확인합니다.');await page.click('#generalChatPrepare');await page.waitForFunction(()=>project().general_chat_previews.some(p=>p.state==='pending'));await idle();
  const readonly=await inspect();assert.ok(readonly.scope.includes('get_model_capabilities'));assert.ok(!readonly.scope.includes('prepare_image_action'));
  const preview=await page.evaluate(()=>project().general_chat_previews.at(-1).id);await page.click('[data-general-decision="reject"][data-preview="'+preview+'"]');await idle();const final=await inspect();
  assert.equal(final.cards.length,1);assert.equal(final.cards[0].approval,'rejected');assert.equal(final.generation_jobs,0);assert.equal(final.local_jobs,0);assert.equal(final.takes,0);assert.deepEqual(final.audio,before.audio);assert.deepEqual(errors,[]);assert.deepEqual(blocked,[]);
  save('actual-ui-result.json',{status:'PASS',engine:await browser.version(),origin,mode:'Actual isolated UI/HTTP/SQLite; deterministic synthetic chat+quote; not actual Claude/image generation',
   first_segment:{artifacts:['initial-manifest-labels.json','round-1.json','round-2.json','round-3.json','actual-ui-failure.json'],observer_failure:'Card pane was hidden because observer omitted public Work settings tab; original failed screenshots/zero rects preserved. No reset or repeat generation.'},
   before,reopened,held,rejected,readonly,final,responsive:captures,events,errors,failed,blocked,
   network:{external_probe:denied,policy:'OS all nonloopback IP denied, loopback IP/local Unix sockets allowed'},keyboard:'Prompt Tab in first segment; Enter on focused Hold button in this continuation',
   actual_models_called:0,actual_claude_semantics_token_fit_billing_verified:false,main_demo_or_user_workspace_touched:false});
  console.log(JSON.stringify({status:'PASS',same_action:id,visible_widths:captures.map(x=>x.width),events:events.length,errors,failed,blocked}));
 }catch(error){if(page){try{await page.screenshot({path:path.join(OUT,'continuation-failure.png')});save('continuation-failure-dom.json',await page.evaluate(()=>({text:document.body.innerText.slice(-18000),busy,dirty})));}catch{}}save('continuation-failure.json',{name:error.name,message:error.message,events,errors,failed,blocked});throw error;}finally{await browser.close();}
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
