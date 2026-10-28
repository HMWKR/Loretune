'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url'),{createRequire}=require('node:module');
const puppeteer=createRequire('/opt/homebrew/lib/noop.js')('puppeteer-core');
const OUT=__dirname;
(async()=>{
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,userDataDir:path.join(OUT,'playback-profile'),args:['--no-sandbox','--disable-background-networking','--disable-component-update','--no-first-run']});
 const errors=[],events=[];
 try{
  const page=await browser.newPage();await page.setViewport({width:1920,height:1080});page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(path.join(OUT,'playback.html')).href);
  await page.waitForFunction(()=>document.querySelector('video').readyState>=2);
  await page.$eval('video',v=>{window.playbackEvents=[];for(const event of ['playing','timeupdate','ended','error'])v.addEventListener(event,()=>playbackEvents.push({event,time:v.currentTime,at:performance.now()}));v.playbackRate=1;});
  const before=Date.now();await page.$eval('video',v=>v.play());
  await page.waitForFunction(()=>document.querySelector('video').currentTime>3);await page.screenshot({path:path.join(OUT,'recording-native-playback.png')});
  await page.waitForFunction(()=>document.querySelector('video').ended,{timeout:25000});
  const result=await page.$eval('video',v=>({ended:v.ended,duration:v.duration,currentTime:v.currentTime,videoWidth:v.videoWidth,videoHeight:v.videoHeight,error:v.error,playbackRate:v.playbackRate,frames:v.getVideoPlaybackQuality(),events:playbackEvents}));
  assert.equal(result.ended,true);assert.equal(result.error,null);assert.equal(result.playbackRate,1);assert.equal(result.videoWidth,1920);assert.equal(result.videoHeight,1080);assert.deepEqual(errors,[]);assert.ok((Date.now()-before)/1000>=result.duration-.3);
  fs.writeFileSync(path.join(OUT,'recording-playback-receipt.json'),JSON.stringify({status:'PASS',method:'Native HTML video element and Chrome decoder. HTMLMediaElement.play; normal 1x playback waited to ended, no seeking.',file:'review-navigation-demo.mp4',engine:await browser.version(),wall_elapsed_seconds:(Date.now()-before)/1000,result,errors},null,2)+'\n');
  console.log(JSON.stringify({status:'PASS',ended:result.ended,duration:result.duration,frames:result.frames.totalVideoFrames}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
