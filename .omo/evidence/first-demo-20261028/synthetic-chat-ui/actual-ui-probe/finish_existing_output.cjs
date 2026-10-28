'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const puppeteer=require('node:module').createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const out=__dirname,setup=JSON.parse(fs.readFileSync(path.join(out,'fixture-setup.json'))),origin='http://127.0.0.1:'+setup.port;
const save=(n,v)=>fs.writeFileSync(path.join(out,n),JSON.stringify(v,null,2)+'\n');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--no-sandbox','--disable-background-networking']});
 let page;const errors=[];
 try{
  page=await browser.newPage();await page.setViewport({width:1920,height:1080});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin+'/',{waitUntil:'networkidle0'});await page.waitForFunction(()=>draft?.id===4);
  await page.click('#generalChatRefresh');await page.waitForFunction(()=>!busy&&!pendingId());
  await page.click('.flow-nav [data-step="4"]');
  const job=await page.evaluate(()=>state.jobs.find(j=>j.snapshot?.timeline?.id===4&&j.status==='completed'));
  assert.ok(job);
  await page.click('#agentSettingsTab');
  const details=await page.$eval('#jobs',e=>{const d=e.closest('details');return d?{open:d.open,id:d.id}:null});
  save('output-details-state.json',details);
  if(details&&!details.open)await page.click('details:has(#jobs)>summary');
  await page.click('[data-play="'+job.download+'"]');await page.waitForSelector('#downloadPreview video',{visible:true});
  await page.$eval('#downloadPreview video',v=>{v.muted=true;return v.play()});
  await page.waitForFunction(()=>document.querySelector('#downloadPreview video')?.currentTime>.4);
  const playback=await page.$eval('#downloadPreview video',v=>({currentTime:v.currentTime,duration:v.duration,readyState:v.readyState,videoWidth:v.videoWidth,videoHeight:v.videoHeight,error:v.error?.code??null}));
  await page.screenshot({path:path.join(out,'actual-output-playing.png')});
  const session=await page.createCDPSession();await session.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:path.join(out,'downloads')});
  await page.click('a[href="'+job.download+'"][download]');
  const file=path.join(out,'downloads',job.id+'.mp4'),until=Date.now()+15000;
  while((!fs.existsSync(file)||fs.existsSync(file+'.crdownload'))&&Date.now()<until)await pause(100);
  assert.ok(fs.existsSync(file));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),job.sha256);
  await page.reload({waitUntil:'networkidle0'});await page.waitForFunction(()=>draft?.id===4);await page.click('.flow-nav [data-step="4"]');
  const reopened=await page.evaluate(()=>({head:project().timeline_head,draft_id:draft.id,stored:project().timeline_versions.at(-1).clips[0].motion_overlay,
    displayed_x:document.querySelector('[data-overlay-field="offset_x"]').value,displayed_y:document.querySelector('[data-overlay-field="offset_y"]').value,
    displayed_caption:document.querySelector('#captions input[data-field="text"]').value,approval:!!draft.approval,turn:project().general_chat_turns.at(-1).status}));
  assert.equal(reopened.head,4);assert.equal(reopened.draft_id,4);assert.equal(reopened.displayed_x,'240');assert.equal(reopened.displayed_y,'120');assert.equal(reopened.displayed_caption,'음악의 여운을 이어서');
  save('output-play-download-reopen.json',{status:'PASS remaining actual UI workflow after resynchronization',job_id:job.id,download:job.download,sha256:job.sha256,playback,reopened,errors,
    playback_method:'actual result-review UI created video element; native HTMLMediaElement.play() with muted audio in isolated headless browser',
    download_method:'actual UI download anchor, awaited completed file and matched SHA',
    limits:'Immediate stale UI remains a separate failure; no product fix made. Version4 unapproved render branch was not executed in this specific UI run; separate existing actual API probe covers it.',actual_provider_calls:0,main_data_accessed:false});
  console.log(JSON.stringify({status:'PASS',playback,reopened,sha256:job.sha256,errors}));
 }catch(e){if(page)await page.screenshot({path:path.join(out,'finish-output-failure.png')});throw e;}
 finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
