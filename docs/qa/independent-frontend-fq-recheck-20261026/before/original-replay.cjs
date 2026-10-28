'use strict';
// Synthetic VM only. Product sources are read from the immutable snapshot.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto'),{performance}=require('node:perf_hooks');
const ROOT=path.join(__dirname,'snapshot'),html=fs.readFileSync(path.join(ROOT,'index.html'),'utf8');
const {fixture:mediaFixture}=require('./snapshot/tests/media_async_harness.cjs');
const media=require('./snapshot/studio-media.js');
const results=[],ledger=[];
const sha=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const clone=x=>JSON.parse(JSON.stringify(x));
const line=prefix=>{const x=html.split('\n').find(x=>x.startsWith(prefix));assert.ok(x,prefix);return x;};
const slice=(start,end)=>{const a=html.indexOf(start),b=html.indexOf(end,a);assert.ok(a>=0&&b>a,start);return html.slice(a,b);};
const flush=async()=>{await Promise.resolve();await Promise.resolve();await Promise.resolve();};
function defer(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};}
function response(status,body){return {ok:status>=200&&status<300,status,json:async()=>clone(body)};}
function strictTransport(handler,caseId){
 return async(url,options={})=>{
  const method=options.method||'GET';let body;
  if(options.body)body=JSON.parse(options.body);
  const allowed=url==='/api/action'&&method==='POST'&&['comment','review_take','cancel_job','model_settings'].includes(body?.action)&&(!body.data?.song||['A','B'].includes(body.data.song))||/^\/api\/requests\/synthetic-/.test(url)&&method==='GET';
  ledger.push({caseId,url,method,action:body?.action,requestId:body?.request_id,scope:body?.data?.song,disposition:allowed?'synthetic-only':'blocked',forwarded:false});
  if(!allowed)throw Error('QA_TRANSPORT_BLOCKED');
  return handler(url,options,body);
 };
}
async function test(id,body){if(!['ASY01','ASY02','MED02','STO02'].includes(id))return;const observed={};try{await body(observed);results.push({id,status:'PASS',observed});}catch(e){results.push({id,status:'FAIL',observed,error:e.message,stack:e.stack.split('\n').slice(0,6)});}}
const mutationCode=slice('async function sendRequest(',"$('#recoverRequest').onclick=");
function requestFixture(id,handler=async()=>response(200,{})){
 const data=new Map(),nodes=new Map(),calls=[],messages=[],cache=new Map();let serial=0;
 const node=s=>{if(!nodes.has(s))nodes.set(s,{hidden:false,disabled:false,tabIndex:0,focus(){},hasAttribute(){return false;}});return nodes.get(s);};
 const ctx={console,Map,Set,Error,JSON,encodeURIComponent,crypto:{randomUUID:()=>`synthetic-${++serial}`},
  state:{revision:1,token:'SYNTHETIC-NON-CREDENTIAL',projects:{A:{},B:{}}},busy:false,dirty:false,pendingRequest:null,
  document:{querySelectorAll:()=>[],querySelector:()=>null},$:node,
  sessionStorage:{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)},
  requestCache:async(action,key,value)=>{calls.push({action,key});if(action==='put')cache.set(key,clone(value));if(action==='delete')cache.delete(key);return cache.get(key);},
  message:(...x)=>messages.push(x),drawModelChat(){},renderTakeReview(){},refresh:async()=>{},song:()=> 'A',
  productionReviewErrors:new Map(),takeReviewStore:{clearRevision(){}},fetch:strictTransport(handler,id)};
 Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);vm.runInContext(line('function pendingId(')+'\n'+line('function clearPending(')+'\n'+mutationCode,ctx);
 return {ctx,data,nodes,node,calls,messages,cache};
}
const reviewCode=slice('function createTakeReviewStore(', '// DOM glue.');
function reviewContext(){const ctx={};Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);vm.runInContext(reviewCode,ctx);return ctx;}
function memory(){const m=new Map();return {map:m,getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};}
function pollFixture(caseId){
 const waits=[],draws=[];let poll,current='A';
 const state=revision=>({revision,projects:Object.fromEntries(['A','B'].map(name=>[name,{chat_turns:revision===1?[]:[{text:name+' revision '+revision}],chat_connection:{state:'synthetic'},media_actions:[],media_connections:[],image_connection:null,model_settings:{revision}}])),jobs:[],generation_jobs:[]});
 const ctx={state:state(1),busy:false,dirty:false,song:()=>current,JSON,fetch:(url,options={})=>{const allowed=url==='/api/state'&&(!options.method||options.method==='GET');ledger.push({caseId,url,method:options.method||'GET',disposition:allowed?'synthetic-only':'blocked',forwarded:false});if(!allowed)throw Error('QA_TRANSPORT_BLOCKED');const d=defer();waits.push(d);return d.promise;},
  setInterval:fn=>poll=fn,drawModelChat:()=>draws.push(ctx.state.revision),drawCreationProposals(){},drawGuided(){},drawMediaCreator(){},drawImageConnection(){},drawJobs(){},drawGeneration(){},refresh:async()=>{throw Error('unexpected refresh');}};
 Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);const a=html.indexOf('setInterval(async()=>{'),b=html.indexOf('},1500);',a);assert.ok(a>=0&&b>a);vm.runInContext(html.slice(a,b+'},1500);'.length),ctx);
 return {ctx,waits,draws,poll,state,setProject:x=>current=x};
}
const loaded=(f,s,t=0)=>{s.seek(t);const v=f.q('#preview').children[0];v.onloadeddata();return v;};
(async()=>{
 await test('ENV01',async o=>{
  const expected='0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109';o.html=crypto.createHash('sha256').update(html).digest('hex');assert.equal(o.html,expected);
  const transport=strictTransport(async()=>response(200,{synthetic:true}),'ENV01');
  await transport('/api/action',{method:'POST',body:JSON.stringify({action:'comment',data:{song:'A'},request_id:'synthetic-1'})});
  await assert.rejects(()=>transport('/api/action',{method:'POST',body:JSON.stringify({action:'render_job',data:{song:'A'}})}),/BLOCKED/);
  await assert.rejects(()=>transport('https://api.example.invalid/provider',{method:'POST'}),/BLOCKED/);
  o.allowed=1;o.blocked=2;o.forwarded=0;
 });
 await test('FUN02',async o=>{
  const c=reviewContext(),store=c.createTakeReviewStore(memory()),pending=defer(),calls=[];
  let value={decision:'',reason:''};const long='가나다라마바사아자차'.repeat(1000),canonical={project:'A',shot:'s1',take:1,approved:false};const before=sha(canonical);
  const controller=c.createTakeReviewController({store,context:()=>({key:'A/s1/1',song:'A',shot:'s1',take:1}),inputs:()=>({...value}),save:(action,payload)=>{calls.push(clone({action,payload}));return pending.promise},render(){},notify(){return false}});
  await controller.submit();value={decision:'approved',reason:'  '};await controller.submit();assert.equal(calls.length,0);
  value={decision:'changes_requested',reason:long};const first=controller.submit();await controller.submit();assert.equal(calls.length,1);
  value={decision:'rejected',reason:'새 한국어 초안'};controller.capture();pending.resolve(true);await first;
  assert.equal(calls[0].payload.reason,long);assert.equal(store.get('A/s1/1').reason,'새 한국어 초안');assert.equal(sha(canonical),before);
  Object.assign(o,{submittedChars:long.length,calls:calls.length,newDraft:store.get('A/s1/1').reason,canonicalUnchanged:true});
 });
 await test('FUN03',async o=>{
  const calls=[],node={},p={model_settings:{revision:7},timeline_head:2,approval:'human-only'};const before=sha(p);
  const ctx={$:()=>node,project:()=>p,song:()=> 'A',FormData:class{constructor(form){this.rows=form.rows;}[Symbol.iterator](){return this.rows[Symbol.iterator]();}},act:async(action,payload)=>calls.push(clone({action,payload}))};
  Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);vm.runInContext(line("$('#modelSettingsForm').onsubmit="),ctx);
  await node.onsubmit({preventDefault(){},target:{rows:[['chat','synthetic-chat'],['image',''],['video','synthetic-blocked-video']]}});
  assert.deepEqual(calls[0].payload,{song:'A',selections:{chat:'synthetic-chat',image:null,video:'synthetic-blocked-video'},model_revision:7});assert.equal(sha(p),before);
  o.payload=calls[0];o.canonicalUnchanged=true;o.providerDispatch=0;
 });
 await test('STA02',async o=>{
  const nodes={},p={timeline_head:2,shots:{s1:{selected:2}}},job={id:'synthetic-output',song:'A',status:'completed',snapshot:{timeline:{id:1,clips:[{shot:'s1',take:1}]}},delivery_reviews:[],download:'/exports/synthetic-output.mp4'};
  const before=sha({p,job}),ctx={state:{jobs:[job]},project:()=>p,song:()=> 'A',drawChatProgress(){},creatorOutputTest:()=>true,creatorError:x=>({message:x}),esc:String,$:s=>nodes[s]||(nodes[s]={innerHTML:''})};
  Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);vm.runInContext(slice('function drawJobs(){','let pendingRequest=null;'),ctx);ctx.drawJobs();
  o.markup=nodes['#jobs'].innerHTML;assert.match(o.markup,/이전 편집 결과/);assert.match(o.markup,/출력 버전 1/);assert.match(o.markup,/테스트 미디어/);assert.doesNotMatch(o.markup,/출력 버전 2/);assert.equal(sha({p,job}),before);o.canonicalUnchanged=true;
 });
 await test('ASY01',async o=>{
  const f=pollFixture('ASY01'),first=f.poll(),second=f.poll();f.waits[1].resolve(response(200,f.state(3)));await second;o.afterNewer=f.ctx.state.revision;
  f.waits[0].resolve(response(200,f.state(2)));await first;o.afterLateOlder=f.ctx.state.revision;o.drawRevisions=f.draws;o.source='index.html:564';assert.equal(f.ctx.state.revision,3,'late older poll regressed state.revision');
 });
 await test('ASY02',async o=>{
  const f=pollFixture('ASY02'),pending=f.poll();f.ctx.busy=true;f.ctx.dirty=true;f.ctx.state=f.state(3);f.setProject('B');
  f.waits[0].resolve(response(200,f.state(2)));await pending;Object.assign(o,{expectedRevision:3,actualRevision:f.ctx.state.revision,busy:f.ctx.busy,dirty:f.ctx.dirty,drawRevisions:f.draws,source:'index.html:564'});
  assert.equal(f.ctx.state.revision,3,'poll that started idle overwrote current state while busy');
 });
 await test('ASY03',async o=>{
  const f=requestFixture('ASY03',async()=>{throw Error('synthetic cancel response lost');});const before=sha(f.ctx.state);
  const first=await f.ctx.act('cancel_job',{song:'A',job:'synthetic-job'}),pendingId=f.ctx.pendingId();assert.equal(first,false);assert.ok(pendingId);
  const second=await f.ctx.act('cancel_job',{song:'A',job:'synthetic-job'});assert.equal(second,false);
  f.ctx.fetch=strictTransport(async()=>response(404,{status:'unknown'}),'ASY03');await f.ctx.reconcilePendingRequest();assert.equal(f.ctx.pendingId(),pendingId);
  const own=ledger.filter(x=>x.caseId==='ASY03');assert.equal(own.filter(x=>x.method==='POST').length,1);assert.equal(own.filter(x=>x.method==='GET').length,1);assert.equal(sha(f.ctx.state),before);
  Object.assign(o,{pendingId,requests:own,cancellationReceipt:'unknown; no cancelled outcome inferred',canonicalUnchanged:true});
 });
 await test('MED02',async o=>{
  const details=[];
  {
   const f=mediaFixture(),s=f.api._audit.createSequence(f.p,f.d,0),v=loaded(f,s);v.play=()=>Promise.reject(Object.assign(Error('synthetic autoplay denied'),{name:'NotAllowedError'}));s.play();await flush();
   details.push({name:'current play rejection',label:f.q('#sequenceStatus').textContent,button:f.q('#sequencePlay').textContent,frames:f.frames.size});assert.equal(f.frames.size,0);assert.equal(f.q('#sequencePlay').textContent,'편집 재생');
  }
  {
   const f=mediaFixture(),s=f.api._audit.createSequence(f.p,f.d,0),v=loaded(f,s);s.play();v.onwaiting();const t=s.time;f.frame(4000);assert.equal(s.time,t);v.onplaying();v.currentTime=3;f.frame(4500);assert.equal(s.time,1);s.dispose();details.push({name:'waiting stalls clock and resumes',time:s.time,frames:f.frames.size});
  }
  for(const delta of [0,.025]){
   const f=mediaFixture();f.d.clips=[{shot:'A',take:1,trim:0,duration:3}];const before=sha({p:f.p,d:f.d});const s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const v=f.q('#preview').children[0];v.duration=3-delta;v.onloadeddata();s.play();
   v.currentTime=v.duration-.05;f.frame(2900);v.currentTime=v.duration;v.ended=true;v.paused=true;if(v.onended)v.onended();f.frame(3000);f.frame(8000);
   details.push({name:'ended delta '+delta,duration:v.duration,time:s.time,button:f.q('#sequencePlay').textContent,frames:f.frames.size,canonicalUnchanged:sha({p:f.p,d:f.d})===before});s.dispose();
  }
  o.details=details;const ends=details.filter(x=>x.name.startsWith('ended'));assert.ok(ends.every(x=>x.frames===0&&x.button==='편집 재생'),'terminal ended media leaves playing UI/RAF active');
 });
 await test('TIM01',async o=>{
  const clips=Array.from({length:30},(_,i)=>({shot:'s'+i,take:1,duration:.131,trim:.5})),before=sha(clips);const total=clips.reduce((n,c)=>n+c.duration,0);
  const mapping=[0,.130999,.131,3.929,total].map(t=>media.locate(clips,t));assert.equal(mapping[2].index,1);assert.equal(mapping[2].source,.5);assert.ok(Math.abs(mapping.at(-1).source-.631)<1e-10);assert.equal(sha(clips),before);
  const f=mediaFixture();f.d.subtitles=[{start:0,end:1,text:'첫 자막'},{start:1,end:3,text:'다음 자막'}];const s=f.api._audit.createSequence(f.p,f.d,0);const observed=[];
  for(const t of [0,.999,1,3]){s.seek(t);observed.push({time:t,caption:f.q('#sequenceCaption').textContent});}assert.deepEqual(observed.map(x=>x.caption),['첫 자막','첫 자막','다음 자막','']);s.dispose();
  Object.assign(o,{total,mapping,observed,sourceTimeOnly:'no decoded frame precision claimed',finite:!JSON.stringify(mapping).includes('NaN')});
 });
 await test('STO01',async o=>{
  const c=reviewContext(),storage=memory();storage.setItem('bad','{broken JSON');storage.setItem('old',JSON.stringify({reason:'old shape',decision:'yes'}));
  const store=c.createTakeReviewStore(storage);assert.equal(store.get('bad'),null);assert.equal(store.get('old'),null);store.set('A',{decision:'approved',reason:'한국어 보존'});assert.equal(c.createTakeReviewStore(storage).get('A').reason,'한국어 보존');assert.equal(store.get('B'),null);
  const denied=c.createTakeReviewStore({getItem(){throw Error('SecurityError')},setItem(){throw Error('QuotaExceededError')},removeItem(){throw Error('SecurityError')}});denied.set('A',{decision:'rejected',reason:'메모리 보존'});assert.equal(denied.get('A').reason,'메모리 보존');assert.equal(denied.failed,true);
  Object.assign(o,{badJSON:null,oldShape:null,scopedRestore:true,deniedDraft:denied.get('A'),failureFlag:denied.failed});
 });
 await test('STO02',async o=>{
  const f=requestFixture('STO02');f.ctx.sessionStorage.getItem=()=>{const e=Error('synthetic storage denied');e.name='SecurityError';throw e;};
  try{vm.runInContext("$('#recovery').hidden=!pendingId();",f.ctx);o.startup='graceful';}catch(e){o.startup={name:e.name,message:e.message};}
  try{await f.ctx.act('comment',{song:'A',text:'한국어'});o.submit='graceful';}catch(e){o.submit={name:e.name,message:e.message};}
  o.requests=ledger.filter(x=>x.caseId==='STO02').length;o.source='index.html:264,284,310';assert.equal(o.startup,'graceful','startup recovery visibility throws when storage access denied');assert.equal(o.submit,'graceful');
 });
 await test('STO03',async o=>{
  const f=requestFixture('STO03');f.ctx.indexedDB={open(){const req={error:Error('synthetic IndexedDB open failure')};queueMicrotask(()=>req.onerror());return req;}};
  vm.runInContext(line('async function requestCache('),f.ctx);const failed=await f.ctx.act('comment',{song:'A',text:'보존'});assert.equal(failed,false);assert.equal(f.ctx.busy,false);assert.equal(ledger.filter(x=>x.caseId==='STO03').length,0);
  const aborted=requestFixture('STO03-abort');let closed=0;
  aborted.ctx.indexedDB={open(){const tx={error:Error('synthetic transaction abort'),objectStore(){return{put(){const req={};queueMicrotask(()=>tx.onabort());return req;}}}};const open={result:{transaction:()=>tx,close(){closed++;}}};queueMicrotask(()=>open.onsuccess());return open;}};
  vm.runInContext(line('async function requestCache('),aborted.ctx);assert.equal(await aborted.ctx.act('comment',{song:'A',text:'보존'}),false);assert.equal(aborted.ctx.busy,false);assert.equal(ledger.filter(x=>x.caseId==='STO03-abort').length,0);assert.equal(closed,1);
  const g=requestFixture('STO03-duplicate'),cache=defer();g.ctx.requestCache=(action)=>action==='put'?cache.promise:Promise.resolve();const first=g.ctx.act('comment',{song:'A',text:'once'});const second=await g.ctx.act('comment',{song:'A',text:'duplicate'});cache.resolve();await first;assert.equal(second,false);assert.equal(ledger.filter(x=>x.caseId==='STO03-duplicate'&&x.method==='POST').length,1);
  Object.assign(o,{cacheFailureSent:0,cacheFailureBusy:f.ctx.busy,cacheFailureMessage:f.messages,transactionAbortSent:0,transactionClosed:closed,duplicatePostCount:1});
 });
 await test('PER01',async o=>{
  const f=mediaFixture(),samples=[],counts=[];let prior=[];
  f.p.shots={};f.d.clips=[];f.d.subtitles=[];
  for(let i=0;i<60;i++){const shot=`장면${i}-`+'가'.repeat(1000);f.p.shots[shot]={selected:1,takes:[1,2,3].map(id=>({id,asset:`fixture:${i}-${id}.mp4`,metadata:{duration:12}}))};f.d.clips.push({shot,take:1,trim:0,duration:1});f.d.subtitles.push({start:i,end:i+.5,text:'첫 한국어 자막 '+i},{start:i+.5,end:i+1,text:'둘째 한국어 자막 '+i});}
  const canonical=sha({p:f.p,d:f.d});
  for(let i=0;i<60;i++){
   const start=performance.now();const s=f.api._audit.createSequence(f.p,f.d,i),v=loaded(f,s,i);s.play();samples.push(performance.now()-start);
   const active=f.media.filter(m=>!m.paused).length,callbacks=f.media.filter(m=>m.onloadeddata||m.onerror).length;counts.push({cycle:i+1,active,callbacks,raf:f.frames.size});
   assert.ok(active<=1);assert.equal(f.frames.size,1);assert.ok(prior.every(m=>m.paused));prior=[...f.media];
  }
  f.api.stop();assert.equal(f.frames.size,0);assert.equal(sha({p:f.p,d:f.d}),canonical);
  const sorted=[...samples].sort((a,b)=>a-b);Object.assign(o,{fixture:{shots:60,takes:180,captions:120,labelCharsAtLeast:1000},cycles:60,checkpoints:counts.filter(x=>[1,30,31,60].includes(x.cycle)),maxActive:Math.max(...counts.map(x=>x.active)),maxCallbacks:Math.max(...counts.map(x=>x.callbacks)),rafAfterStop:f.frames.size,hostOnlyMs:{samples:samples.length,min:sorted[0],p95:sorted[Math.ceil(.95*sorted.length)-1],max:sorted.at(-1)},limitations:'Node VM fixture holds all created elements deliberately; no DOM/heap/leak/INP/cached-browser-shot p95 claim',canonicalUnchanged:true});
 });
 fs.writeFileSync(path.join(__dirname,'vm-results.json'),JSON.stringify({at:new Date().toISOString(),environment:{node:process.version,browser:null,viewport:null,zoom:null,network:'VM only'},results},null,2));
 fs.writeFileSync(path.join(__dirname,'request-ledger.json'),JSON.stringify({at:new Date().toISOString(),records:ledger,forwarded:0,credentials:'synthetic placeholder only; header values never recorded'},null,2));
 console.log(JSON.stringify(results.map(x=>({id:x.id,status:x.status,error:x.error,observed:x.observed})),null,2));
 process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=2;});
