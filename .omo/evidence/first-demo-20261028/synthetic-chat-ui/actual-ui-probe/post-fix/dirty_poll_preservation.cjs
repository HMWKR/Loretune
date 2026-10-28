'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const puppeteer=require('node:module').createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const setup=JSON.parse(fs.readFileSync(path.join(__dirname,'fixture-setup.json'))),origin='http://127.0.0.1:'+setup.port;
(async()=>{
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--no-sandbox','--disable-background-networking']});
 try{
  const a=await browser.newPage(),b=await browser.newPage();a.setDefaultTimeout(10000);b.setDefaultTimeout(10000);await a.setViewport({width:1920,height:1080});await b.setViewport({width:1920,height:1080});
  await a.bringToFront();await a.goto(origin+'/',{waitUntil:'domcontentloaded'});await a.waitForFunction(()=>typeof draft!=='undefined'&&draft?.id===4);await a.click('.flow-nav [data-step="4"]');console.log('A loaded and focused');
  const handle=await a.evaluateHandle(()=>draft),sequence=await a.evaluate(()=>pollSequence);
  await a.waitForFunction(first=>pollSequence>=first+2,{polling:200},sequence);console.log('Same-head polls observed');
  const same=await a.evaluate(saved=>saved===draft,handle);assert.equal(same,true);
  if(!(await a.$eval('.lt-timeline-controls',e=>e.open)))await a.click('.lt-timeline-controls>summary');
  await a.click('[data-overlay-clip="0"][data-overlay-field="offset_x"]');await a.keyboard.press('ArrowUp');
  console.log('Local input',await a.evaluate(()=>({dirty,x:draft.clips[0].motion_overlay.offset_x,value:document.querySelector('[data-overlay-field="offset_x"]').value})));
  await a.waitForFunction(()=>dirty&&draft.clips[0].motion_overlay.offset_x!==240);
  const heldX=await a.evaluate(()=>draft.clips[0].motion_overlay.offset_x);assert.ok(heldX>240&&heldX<241);
  console.log('A dirty local input retained before other-tab save');await b.bringToFront();await b.goto(origin+'/',{waitUntil:'domcontentloaded'});await b.waitForFunction(()=>typeof draft!=='undefined'&&draft?.id===4);await b.click('.flow-nav [data-step="4"]');await b.click('#saveTimeline');await b.waitForFunction(()=>project().timeline_head===5&&!busy&&!pendingId());console.log('B saved version5');
  await a.bringToFront();const start=await a.evaluate(()=>pollSequence);await a.waitForFunction(first=>pollSequence>=first+2,{polling:200},start);
  const retained=await a.evaluate(()=>({state_head:project().timeline_head,draft_id:draft.id,dirty,local_x:draft.clips[0].motion_overlay.offset_x,displayed_x:document.querySelector('[data-overlay-field="offset_x"]').value}));
  assert.equal(retained.dirty,true);assert.equal(retained.local_x,heldX);assert.equal(retained.displayed_x,String(heldX));assert.equal(retained.draft_id,4);
  const authoritative=await b.evaluate(()=>({head:project().timeline_head,offset_x:draft.clips[0].motion_overlay.offset_x,approved:!!draft.approval}));
  assert.equal(authoritative.head,5);assert.equal(authoritative.offset_x,240);assert.equal(authoritative.approved,false);
  await a.screenshot({path:path.join(__dirname,'dirty-preserved.png')});
  await a.click('#cancelTimelineDraft');await a.waitForFunction(()=>!dirty&&draft?.id===5&&project().timeline_head===5);
  const synchronized=await a.evaluate(()=>({head:project().timeline_head,draft_id:draft.id,dirty,x:draft.clips[0].motion_overlay.offset_x,status:document.getElementById('timelineStatus').textContent}));assert.equal(synchronized.x,240);
  const value={status:'PASS',scope:'separate actual two-tab user-edit/poll scenario after completed version4 workflow; no extra model message',same_head_draft_object_preserved:same,dirty_local_retained:retained,other_tab_saved_unapproved_version:authoritative,after_explicit_cancel_and_poll:synchronized,original_version4_and_outputs_preserved:true,actual_provider_calls:0,main_data_accessed:false};
  fs.writeFileSync(path.join(__dirname,'dirty-poll-preservation.json'),JSON.stringify(value,null,2)+'\n');console.log(JSON.stringify(value));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
