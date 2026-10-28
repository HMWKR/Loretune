'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(__dirname+'/snapshot/index.html','utf8');
const {fixture}=require('./snapshot/tests/media_async_harness.cjs');
const rows=[];
(async()=>{
 const state=n=>({revision:n,projects:{A:{chat_turns:[{text:'r'+n}],media_actions:[],media_connections:[]}},jobs:[],generation_jobs:[]});
 let poll,reads=0;const ctx={state:state(1),busy:true,dirty:false,song:()=> 'A',setInterval:fn=>poll=fn,fetch:async()=>{reads++;return{json:async()=>state(2)}},drawModelChat(){},drawCreationProposals(){},drawGuided(){},drawJobs(){},drawGeneration(){},drawMediaCreator(){},drawImageConnection(){},refresh:async()=>{}};
 vm.createContext(ctx);const start=html.indexOf('setInterval(async()=>{'),end=html.indexOf('},1500);',start);vm.runInContext(html.slice(start,end+8),ctx);
 await poll();assert.equal(reads,0);ctx.busy=false;await poll();assert.equal(ctx.state.revision,2);rows.push({case:'FQ01 control: start-busy skips, single fresh poll applies',status:'PASS',reads,revision:ctx.state.revision});
 {
  const f=fixture();f.d.clips=[{shot:'A',take:1,trim:0,duration:3}];const s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const v=f.q('#preview').children[0];v.duration=3;v.onloadeddata();s.play();v.currentTime=3;v.paused=false;f.frame(3000);assert.equal(s.time,3);assert.equal(f.frames.size,0);rows.push({case:'FQ02 control: RAF sees exact end before native pause',status:'PASS',time:s.time,frames:f.frames.size,button:f.q('#sequencePlay').textContent});
 }
 {
  const f=fixture();f.d.clips=[{shot:'A',take:1,trim:0,duration:3},{shot:'B',take:1,trim:0,duration:3}];const s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const v=f.q('#preview').children[0];v.duration=3;v.onloadeddata();s.play();v.currentTime=2.95;f.frame(2950);v.currentTime=3;v.paused=true;v.ended=true;if(v.onended)v.onended();f.frame(3000);f.frame(8000);const observed={time:s.time,clipSrc:f.q('#preview').children[0].src,frames:f.frames.size};assert.equal(s.time,2.95);assert.equal(f.q('#preview').children[0],v);rows.push({case:'FQ02 reproduction control: first cut ended cannot reach next cut',status:'REPRODUCED',observed});s.dispose();
 }
 {
  const nodes={},ctx={sessionStorage:{getItem:()=>null},$:s=>nodes[s]||(nodes[s]={})};vm.createContext(ctx);vm.runInContext(html.split('\n').find(l=>l.startsWith('function pendingId('))+"\n$('#recovery').hidden=!pendingId();",ctx);assert.equal(nodes['#recovery'].hidden,true);rows.push({case:'FQ03 control: ordinary empty storage initializes recovery',status:'PASS',hidden:true});
 }
 fs.writeFileSync(__dirname+'/finding-controls.json',JSON.stringify({at:new Date().toISOString(),scope:'positive controls and bounded reproduction, no source changes or browser',rows},null,2));console.log(JSON.stringify(rows,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
