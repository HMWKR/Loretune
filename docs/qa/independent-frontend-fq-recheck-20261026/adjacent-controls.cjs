'use strict';
// Independent controls. Load copied production function bodies without changing them.
require('./offline-node-guard.cjs');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.join(__dirname,'after/snapshot');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
assert.equal(crypto.createHash('sha256').update(html).digest('hex'),'07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3');
const {fixture}=require('./after/snapshot/tests/media_async_harness.cjs');
const copy=x=>JSON.parse(JSON.stringify(x)),fingerprint=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const line=p=>{const s=html.split('\n').find(x=>x.startsWith(p));assert.ok(s,p);return s;};
const between=(a,b)=>{const i=html.indexOf(a),j=html.indexOf(b,i);assert.ok(i>=0&&j>i,a);return html.slice(i,j);};
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve};};
const response=(body,status=200)=>({ok:status>=200&&status<300,status,json:async()=>copy(body)});
const results=[],ledger=[];
async function test(id,description,run){const observed={};try{await run(observed);results.push({id,description,status:'PASS',observed});}catch(e){results.push({id,description,status:'FAIL',observed,error:e.stack});}}
function canonical(){return{workspace_id:'synthetic-workspace',revision:7,projects:{A:{chat_turns:[],chat_connection:{status:'idle'},media_actions:[],media_connections:[],image_connection:null,model_settings:{revision:2,chat:'fake-chat',image:null,video:'fake-video'},shots:{S1:{selected:2,approval:'human'}},timeline_head:3},B:{chat_turns:[],media_actions:[]}},jobs:[],generation_jobs:[]};}
function polling(id){
 const pending=[],draws=[];let callback,name='A';
 const c={state:canonical(),stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'S1',busy:false,dirty:false,song:()=>name,JSON,
  setInterval:fn=>callback=fn,fetch:async(url,options={})=>{assert.equal(url,'/api/state');assert.equal(options.method||'GET','GET');ledger.push({id,url,method:'GET',forwarded:false});const d=deferred();pending.push(d);return d.promise;},refresh:async()=>{throw Error('UNEXPECTED_REFRESH');}};
 for(const fn of ['drawModelChat','drawCreationProposals','drawGuided','drawJobs','drawGeneration','drawMediaCreator','drawImageConnection'])c[fn]=()=>draws.push(fn);
 vm.createContext(c);vm.runInContext(between('setInterval(async()=>{','},1500);')+'},1500);',c);
 return{c,pending,draws,poll:()=>callback(),switch:x=>name=x};
}
function requests(id){
 const memory=new Map(),cache=new Map(),nodes=new Map(),notices=[],clears=[];let serial=0;
 const $=s=>{if(!nodes.has(s))nodes.set(s,{hidden:false,disabled:false,textContent:'',dataset:{},focus(){},hasAttribute(){return false;}});return nodes.get(s);};
 const c={state:canonical(),stateReadEpoch:0,busy:false,dirty:false,pendingRequest:null,Map,Set,Error,JSON,encodeURIComponent,crypto:{randomUUID:()=>`synthetic-${id}-${++serial}`},$,
  document:{querySelector:$,querySelectorAll:()=>[]},sessionStorage:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)},
  requestCache:async(op,key,value)=>{if(op==='put')cache.set(key,copy(value));if(op==='delete')cache.delete(key);return cache.get(key);},message:(...x)=>notices.push(x),
  drawModelChat(){},renderTakeReview(){},refresh:async()=>{},song:()=> 'A',productionReviewErrors:new Map(),takeReviewStore:{clearRevision:(...x)=>clears.push(x)}};
 let transport=async()=>response({});
 c.fetch=async(url,options={})=>{const method=options.method||'GET';assert.ok(url==='/api/action'&&method==='POST'||/^\/api\/requests\/synthetic-/.test(url)&&method==='GET');ledger.push({id,url,method,requestId:options.body?JSON.parse(options.body).request_id:null,forwarded:false});return transport(url,options);};
 vm.createContext(c);vm.runInContext(['function pendingId(','function updateRecovery(','function clearPending('].map(line).join('\n')+'\n'+between('async function sendRequest(',"$('#recoverRequest').onclick="),c);
 return{c,memory,cache,$,notices,clears,transport:fn=>transport=fn};
}
function media(options={}){
 const f=fixture();f.d.clips=options.two?[{shot:'A',take:1,trim:2,duration:3},{shot:'B',take:1,trim:1,duration:3}]:[{shot:'A',take:1,trim:2,duration:3}];
 if(options.audio){f.d.audio=1;f.d.audio_offset=1;f.p.audio_versions=[{id:1,asset:'fixture:synthetic-audio.wav'}];}
 const before=fingerprint([f.p,f.d]),s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const v=f.q('#preview').children[0];v.duration=5;v.onloadeddata();
 return{...f,s,v,before,unchanged(){assert.equal(fingerprint([f.p,f.d]),before);},audio:f.media.find(x=>x.tagName==='audio')};
}
const ownRequests=id=>ledger.filter(x=>x.id===id);
(async()=>{
 for(const kind of ['jobs','generation','chat','media'])await test('P-'+kind,'Same revision '+kind+' update independently applies',async o=>{
  const f=polling('P-'+kind),fresh=canonical(),base=fingerprint({shots:f.c.state.projects.A.shots,timeline:f.c.state.projects.A.timeline_head,models:f.c.state.projects.A.model_settings});
  if(kind==='jobs')fresh.jobs=[{id:'synthetic-render',status:'running',progress:65}];
  if(kind==='generation')fresh.generation_jobs=[{id:'synthetic-generation',status:'running',progress:70}];
  if(kind==='chat')fresh.projects.A.chat_turns=[{role:'assistant',content:'합성 응답'}];
  if(kind==='media')fresh.projects.A.media_actions=[{id:'synthetic-action',status:'running'}];
  const p=f.poll();f.pending[0].resolve(response(fresh));await p;
  const pick=s=>kind==='jobs'?s.jobs:kind==='generation'?s.generation_jobs:kind==='chat'?s.projects.A.chat_turns:s.projects.A.media_actions;
  assert.deepEqual(pick(f.c.state),pick(fresh));assert.equal(f.c.state.revision,7);
  assert.equal(fingerprint({shots:f.c.state.projects.A.shots,timeline:f.c.state.projects.A.timeline_head,models:f.c.state.projects.A.model_settings}),base);
  Object.assign(o,{revision:7,value:pick(f.c.state),draws:f.draws,selectionApprovalTimelineModelsUnchanged:true});
 });
 await test('P-guards','Shot/workspace/epoch/busy/dirty changes reject in-flight response',async o=>{
  o.variants=[];for(const kind of ['shot','workspace','epoch','busy','dirty']){const f=polling('P-guards'),fresh=canonical(),p=f.poll();fresh.jobs=[{id:'synthetic-late'}];
   if(kind==='shot')f.c.shotName='S2';if(kind==='workspace')fresh.workspace_id='foreign';if(kind==='epoch')f.c.stateReadEpoch++;if(kind==='busy')f.c.busy=true;if(kind==='dirty')f.c.dirty=true;
   const before=fingerprint(f.c.state);f.pending[0].resolve(response(fresh));await p;assert.equal(fingerprint(f.c.state),before);assert.equal(f.c.pollReadsInFlight,0);assert.equal(f.draws.length,0);o.variants.push(kind);
  }
 });
 await test('P-bound','At most two reads; first response may progress before second; sequence rejects late stale equal-revision update',async o=>{
  const f=polling('P-bound'),a=f.poll(),b=f.poll();await f.poll();assert.equal(f.pending.length,2);
  const x=canonical();x.jobs=[{progress:20}];f.pending[0].resolve(response(x));await a;assert.equal(f.c.state.jobs[0].progress,20);
  const y=canonical();y.jobs=[{progress:80}];f.pending[1].resolve(response(y));await b;assert.equal(f.c.state.jobs[0].progress,80);
  const c=f.poll(),d=f.poll();f.pending[3].resolve(response(y));await d;f.pending[2].resolve(response(x));await c;assert.equal(f.c.state.jobs[0].progress,80);assert.equal(f.c.pollReadsInFlight,0);
  Object.assign(o,{peakInFlight:2,firstCompletionProgress:20,finalProgress:80,revision:7});
 });
 await test('M-late','Actual ended=true callbacks are inert after pause, clip switch, dispose, and controller replacement',async o=>{
  o.variants=[];for(const kind of ['pause','clip','dispose','controller']){const f=media({two:true});f.s.play();const late=f.v.onended;f.v.ended=true;f.v.paused=true;f.v.currentTime=5;
   let replacement;if(kind==='pause')f.s.pause();if(kind==='clip')f.s.seek(3);if(kind==='dispose')f.s.dispose();if(kind==='controller')replacement=f.api._audit.createSequence(f.p,f.d,1);
   const at=f.s.time,button=f.q('#sequencePlay').textContent,frames=f.frames.size;late();assert.equal(f.s.time,at);assert.equal(f.q('#sequencePlay').textContent,button);assert.equal(f.frames.size,frames);if(replacement)assert.equal(replacement.time,1);f.unchanged();f.s.dispose();replacement?.dispose();o.variants.push({kind,ended:true,time:at});
  }
 });
 await test('M-trim','Native ended uses trim and advances exactly one current cut without selection or approval writes',async o=>{
  const f=media({two:true});f.s.play();f.v.ended=f.v.paused=true;f.v.currentTime=5;f.v.onended();assert.equal(f.s.time,3);const next=f.q('#preview').children[0];assert.notEqual(next,f.v);assert.equal(next.src,'fixture:B.mp4');next.duration=4;next.onloadeddata();assert.equal(next.currentTime,1);next.ended=next.paused=true;next.currentTime=4;next.onended();assert.equal(f.s.time,6);assert.equal(f.frames.size,0);assert.equal(f.q('#sequencePlay').textContent,'편집 재생');f.unchanged();Object.assign(o,{secondSourceTimeAfterLoad:1,finalTimelineTime:6,canonicalUnchanged:true});f.s.dispose();
 });
 await test('M-short','25ms deficit stays in existing tolerance; >50ms deficit fails without fabricated completion',async o=>{
  o.variants=[];for(const deficit of [.025,.051]){const f=media();f.v.duration=5-deficit;f.v.onloadeddata();f.s.play();f.v.ended=f.v.paused=true;f.v.currentTime=f.v.duration;f.v.onended();assert.equal(f.frames.size,0);
   if(deficit<.05)assert.equal(f.s.time,3);else{assert.equal(f.s.time,0);assert.match(f.q('#sequenceStatus').textContent,/짧습니다/);}f.unchanged();o.variants.push({deficit,time:f.s.time,status:f.q('#sequenceStatus').textContent});f.s.dispose();
  }
 });
 await test('M-audio','Active original audio remains clock, manual pause freezes it, EOF allows video completion',async o=>{
  const f=media({audio:true});f.audio.duration=4;f.s.play();f.v.ended=f.v.paused=true;f.v.currentTime=5;f.audio.currentTime=3.4;f.v.onended();assert.equal(f.s.time,0);f.frame(2400);assert.ok(Math.abs(f.s.time-2.4)<1e-12);
  f.s.pause();const paused=f.s.time;f.audio.currentTime=3.8;f.v.onended();f.frame(2800);assert.equal(f.s.time,paused);assert.equal(f.frames.size,0);
  f.s.play();f.audio.currentTime=4;f.audio.ended=f.audio.paused=true;f.v.ended=f.v.paused=true;f.v.onended();assert.equal(f.s.time,3);assert.equal(f.frames.size,0);f.unchanged();Object.assign(o,{audioOffset:1,activeTimeline:paused,manualPausePreserved:true,finalTimeline:3,canonicalUnchanged:true});f.s.dispose();
 });
 await test('S-empty','Empty storage and denied storage have distinct recovery UI and submit behavior',async o=>{
  const f=requests('S-empty');f.c.updateRecovery();assert.equal(f.$('#recovery').hidden,true);assert.equal(f.c.pendingId.failed,false);
  f.c.sessionStorage.getItem=()=>{throw Error('synthetic SecurityError');};f.c.updateRecovery();assert.equal(f.$('#recovery').hidden,false);assert.equal(f.$('#recoverRequest').disabled,true);assert.equal(f.c.pendingId.failed,true);assert.equal(await f.c.act('comment',{song:'A',text:'새 초안'}),false);assert.equal(ownRequests('S-empty').length,0);
  Object.assign(o,{emptyHidden:true,deniedHidden:false,deniedRecoverDisabled:true,requests:0,notice:f.notices.at(-1)});
 });
 await test('S-known','Known IDs from cached read or in-memory request survive denied read, permit lookup only',async o=>{
  o.variants=[];for(const origin of ['cached-read','pending-request']){const id='S-known-'+origin,f=requests(id),requestId='synthetic-known-'+origin;
   if(origin==='cached-read'){f.memory.set('loretune-pending',requestId);assert.equal(f.c.pendingId(),requestId);}else f.c.pendingRequest={request_id:requestId,action:'comment',data:{song:'A'}};
   f.c.sessionStorage.getItem=()=>{throw Error('synthetic SecurityError');};f.transport(async()=>response({status:'unknown'},404));f.c.updateRecovery();assert.equal(f.c.pendingId(),requestId);assert.equal(f.$('#recoverRequest').disabled,false);await f.c.act('comment',{song:'A'});await f.c.reconcilePendingRequest();assert.equal(f.c.pendingId(),requestId);assert.deepEqual(ownRequests(id).map(x=>x.method),['GET']);o.variants.push({origin,requestId,methods:['GET'],stillPending:true});
  }
 });
 await test('S-settled','Definite committed/rejected receipt stays definite if cleanup denied; no new write until recovery',async o=>{
  o.variants=[];for(const status of [200,400]){const id='S-settled-'+status,f=requests(id),outcomes=[];f.c.sessionStorage.removeItem=()=>{throw Error('synthetic cleanup denied');};f.transport(async()=>response(status===200?{}:{error:'synthetic validation rejected'},status));
   const ok=await f.c.act('comment',{song:'A',text:'보존'},null,x=>outcomes.push(x.status));assert.equal(ok,status===200);assert.equal(outcomes.at(-1),status===200?'committed':'rejected');assert.ok(!outcomes.includes('unknown'));assert.equal(f.c.pendingId.failed,true);assert.equal(f.$('#recoverRequest').disabled,true);
   await f.c.act('comment',{song:'A'});await f.c.reconcilePendingRequest();assert.deepEqual(ownRequests(id).map(x=>x.method),['POST']);f.c.sessionStorage.removeItem=k=>f.memory.delete(k);f.c.updateRecovery();assert.equal(f.c.pendingId(),null);assert.equal(f.c.pendingId.failed,false);assert.equal(f.$('#recovery').hidden,true);o.variants.push({status,outcomes,networkMethods:['POST'],recoveryCleared:true});
  }
 });
 await test('S-unknown','Failed lookup never infers a committed receipt or clears pending draft',async o=>{
  const id='S-unknown',f=requests(id),requestId='synthetic-unresolved';f.memory.set('loretune-pending',requestId);f.c.productionReviewErrors.set('scope',{requestId,draftRevision:9,status:'unknown'});f.transport(async()=>{f.c.sessionStorage.getItem=()=>{throw Error('synthetic read denied');};throw Error('synthetic lost response');});
  await f.c.reconcilePendingRequest();assert.equal(f.c.productionReviewErrors.get('scope').status,'unknown_checked');assert.equal(f.c.pendingId(),requestId);assert.equal(f.clears.length,0);assert.deepEqual(ownRequests(id).map(x=>x.method),['GET']);Object.assign(o,{status:'unknown_checked',knownRequestId:requestId,draftClearCalls:0,methods:['GET']});
 });
 await test('S-draft','Throwing sessionStorage property getter still preserves scoped in-memory Take draft',async o=>{
  const c={Map,Set,JSON,Number};Object.defineProperty(c,'sessionStorage',{get(){throw Error('synthetic property SecurityError');}});vm.createContext(c);
  vm.runInContext(between('function createTakeReviewStore(','function takeReviewKey(')+'\n'+line('const takeReviewStore=createTakeReviewStore(')+'\nglobalThis.auditStore=takeReviewStore;',c);
  const store=c.auditStore;store.set('A/S1/1',{decision:'changes_requested',reason:'입력을 지웠다가 다시 작성한 한국어 초안'});assert.equal(store.failed,true);assert.equal(store.get('A/S1/1').reason,'입력을 지웠다가 다시 작성한 한국어 초안');assert.equal(store.get('B/S1/1'),null);
  Object.assign(o,{draft:copy(store.get('A/S1/1')),foreignProjectDraft:null,storageFailed:true,persistenceAcrossReload:'NOT VERIFIED / memory only'});
 });
 const out={at:new Date().toISOString(),sourceHtmlSha256:crypto.createHash('sha256').update(html).digest('hex'),environment:{node:process.version,browser:null,viewport:null,zoom:null,network:'offline VM fake only',realMediaDecode:false},results};
 fs.writeFileSync(path.join(__dirname,'adjacent-results.json'),JSON.stringify(out,null,2));fs.writeFileSync(path.join(__dirname,'adjacent-request-ledger.json'),JSON.stringify({forwarded:0,records:ledger},null,2));console.log(JSON.stringify(out,null,2));process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=2;});
