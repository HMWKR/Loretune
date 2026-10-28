/* Actual client recovery code with a small DOM double; optional real local HTTP. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {webcrypto,createHash}=require('node:crypto');
const html=fs.readFileSync('index.html','utf8');
const slice=(start,end)=>html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));
const line=start=>html.split('\n').find(value=>value.startsWith(start));
const helper=slice('/* Only explicit, same-body local scene retries;', 'function pendingId(');
const methods=line('function pendingId(')+'\n'+line('function mutationRequestActive(')+'\n'+line('function updateRecovery(')+'\n'+line('function clearPending(')+'\n'+slice('async function sendRequest(', 'async function upload(');
const response=(body,status=200)=>({ok:status<400,status,json:async()=>body});
const makeState=()=>({workspace_id:'workspace-a',revision:4,token:'synthetic-only',projects:{A:{active_conversation:{id:'conversation-a',revision:2,shared_version:'a'.repeat(64)}}}});
function fixture(initial=makeState()){
 const nodes=new Map(),storage=new Map(),cache=new Map(),notices=[],calls=[];let count=0;
 const $=id=>{if(!nodes.has(id))nodes.set(id,{hidden:false,disabled:false,textContent:'',dataset:{},hasAttribute:()=>false,focus(){}});return nodes.get(id)};
 const c={console,Map,Set,Error,JSON,Number,Object,Uint8Array,TextEncoder,encodeURIComponent,crypto:webcrypto,state:initial,stateReadEpoch:0,busy:false,dirty:false,conversationSwitching:false,pendingRequest:null,activeMutationRequestId:null,$,song:()=> 'A',document:{querySelector:$,querySelectorAll:()=>[],getElementById:id=>$('#'+id)},sessionStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value),removeItem:key=>storage.delete(key)},requestCache:async(action,id,value)=>{if(action==='put')cache.set(id,structuredClone(value));if(action==='delete')cache.delete(id);return cache.has(id)?structuredClone(cache.get(id)):undefined},message:(...values)=>notices.push(values),drawModelChat(){},renderTakeReview(){},productionReviewErrors:new Map(),takeReviewStore:{clearRevision(){}},refresh:async()=>{},fetch:async(url,options)=>{calls.push({url,options});if(options)throw Error('synthetic request not delivered');return response({status:'unknown'},404)}};
 vm.createContext(c);vm.runInContext(helper+methods,c);
 return {c,storage,cache,notices,calls,$,count:()=>count};
}
const scene=()=>({schema_version:1,width:96,height:96,background:[0.1,0.1,0.1],objects:[{id:'subject',kind:'cube',position:[0,0,0],rotation_degrees:[0,0,0],scale:[1,1,1],color:[0.05,0.25,0.8]}],camera:{position:[5,-7,5],target:[0,0,0],lens_mm:50},lights:[{id:'key',position:[3,-4,6],target:[0,0,0],energy_w:800,size_m:3,color:[1,1,1]}]});
async function unknown(action='scene_create'){
 const f=fixture();assert.equal(await f.c.act(action,{song:'A',shot_id:'s',scene:scene()}),false);const id=f.c.pendingId();await f.c.reconcilePendingRequest();return {...f,id};
}
async function checks(){
 let f=await unknown();assert.equal(f.c.LoretuneSceneRecovery.canRetry(),true);assert.equal(f.$('#retrySceneRequest').hidden,false);assert.equal(f.calls.filter(x=>x.options).length,1,'lookup must not resend');
 let original=f.cache.get(f.id);assert.equal(original.schema,'loretune-local-scene-recovery/1');assert.equal(original.workspace_id,'workspace-a');assert.equal(JSON.parse(original.body).request_id,f.id);assert.equal(original.sha256,createHash('sha256').update(original.body).digest('hex'));
 for(const mode of ['workspace','conversation','project','storage-read']){
  f=await unknown();const before=f.calls.filter(x=>x.options).length;
  if(mode==='workspace')f.c.state.workspace_id='workspace-b';
  if(mode==='conversation')f.c.state.projects.A.active_conversation.id='conversation-b';
  if(mode==='project')f.c.song=()=> 'B';
  if(mode==='storage-read')f.c.sessionStorage.getItem=()=>{throw Error('storage unavailable')};
  assert.equal(f.c.LoretuneSceneRecovery.canRetry(),false,mode);assert.equal(await f.c.LoretuneSceneRecovery.retry(),false,mode);assert.equal(f.calls.filter(x=>x.options).length,before,mode);
 }
 for(const mode of ['body','body-and-digest','noncanonical','duplicate-key','broken-json','wrong-id','missing-cache','legacy-cache','cache-failure']){
  f=await unknown();const before=f.calls.filter(x=>x.options).length,item=f.cache.get(f.id);
  if(mode==='body')item.body+=' ';
  if(mode==='body-and-digest'){const altered=JSON.parse(item.body);altered.data.scene.width=128;item.body=JSON.stringify(altered);item.sha256=createHash('sha256').update(item.body).digest('hex')}
  if(mode==='noncanonical'){item.body+=' ';item.sha256=createHash('sha256').update(item.body).digest('hex')}
  if(mode==='duplicate-key'){item.body=item.body.replace('"action":"scene_create"','"action":"scene_create","action":"scene_create"');item.sha256=createHash('sha256').update(item.body).digest('hex')}
  if(mode==='broken-json'){item.body='{';item.sha256=createHash('sha256').update(item.body).digest('hex')}
  if(mode==='wrong-id')item.request_id='different';
  f.cache.set(f.id,item);
  if(mode==='missing-cache')f.cache.delete(f.id);
  if(mode==='legacy-cache')f.cache.set(f.id,JSON.parse(item.body));
  if(mode==='cache-failure')f.c.requestCache=async()=>{throw Error('cache inaccessible')};
  assert.equal(await f.c.LoretuneSceneRecovery.retry(),false,mode);assert.equal(f.calls.filter(x=>x.options).length,before,mode);assert.equal(f.c.pendingId(),f.id,mode);
 }
 for(const action of ['comment','chat_submit','generation_submit','cancel_job']){f=await unknown(action);assert.equal(f.c.LoretuneSceneRecovery.canRetry(),false,action)}
 f=await unknown();let posts=0;f.c.fetch=async(url,options)=>{if(options)posts++;return response({status:'committed',result:{scene:{id:'existing'}}})};let recovered;
 assert.equal(await f.c.LoretuneSceneRecovery.retry(outcome=>recovered=outcome),true);assert.equal(posts,0,'commit found before retry must not repost');assert.equal(recovered.request.action,'scene_create');assert.equal(f.c.pendingId(),null);
 for(const status of [200,401,500]){f=await unknown();f.c.fetch=async()=>response({status:'unknown'},status);await f.c.reconcilePendingRequest();assert.equal(f.c.LoretuneSceneRecovery.canRetry(),false,status)}
 f=await unknown();const body=f.cache.get(f.id).body;f.c.fetch=async(url,options)=>{f.calls.push({url,options});if(!options)return response({status:'unknown'},404);assert.equal(options.body,body,'retry must use byte-identical original JSON');assert.equal(JSON.parse(options.body).request_id,f.id);assert.equal(Object.hasOwn(JSON.parse(options.body),'schema'),false);return response({scene:{id:'new'}})};
 assert.equal(await f.c.LoretuneSceneRecovery.retry(),true);assert.equal(f.c.pendingId(),null);assert.equal(f.calls.filter(x=>x.options).length,2);
 return 'scope/cache/allowlist/404/commit/same-body recovery checks passed';
}
async function realHttp(base){
 const readState=async()=>{const response=await fetch(base+'/api/state');assert.equal(response.status,200);return response.json()};
 const initial=await readState(),f=fixture(initial);f.c.refresh=async()=>{f.c.state=await readState()};
 let failure='before',actualPosts=0,attempts=0;const bodies=[];
 f.c.fetch=async(url,options)=>{
  if(options){attempts++;bodies.push(options.body);if(failure==='before'){failure=null;throw Error('synthetic loss before sending')}actualPosts++;const result=await fetch(base+url,options);if(failure==='after'){failure=null;assert.equal(result.status,200);await result.text();throw Error('synthetic response lost after server commit')}return result}
  return fetch(base+url,options);
 };
 const shot=f.c.state.projects.A.shots.s,shotId=shot.stable_id||'s';
 assert.equal(await f.c.act('scene_create',{song:'A',shot_id:shotId,scene:scene()}),false);const first=f.c.pendingId();assert.equal(actualPosts,0);
 await f.c.reconcilePendingRequest();assert.equal(f.c.LoretuneSceneRecovery.canRetry(),true);assert.equal(actualPosts,0);
 assert.equal(await f.c.LoretuneSceneRecovery.retry(),true);assert.equal(actualPosts,1);assert.equal(bodies[0],bodies[1]);assert.equal(f.c.pendingId(),null);
 let state=await readState(),record=state.projects.A.scenes_3d[0];assert.equal(state.projects.A.scenes_3d.length,1);assert.equal(record.proposals.length,1);
 const original=JSON.parse(bodies[0]),repeat=await fetch(base+'/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Loretune-Token':state.token},body:bodies[0]});assert.equal(repeat.status,200);
 const changed=structuredClone(original);changed.data.scene.width=128;const conflict=await fetch(base+'/api/action',{method:'POST',headers:{'Content-Type':'application/json','X-Loretune-Token':state.token},body:JSON.stringify(changed)});assert.equal(conflict.status,409);
 f.c.state=state;failure='after';const revised=scene();revised.camera.lens_mm=63;
 assert.equal(await f.c.act('scene_replace_draft',{song:'A',scene_id:record.id,scene_proposal_id:record.proposals[0].id,base_revision:0,scene:revised}),false);const second=f.c.pendingId();assert.ok(second);assert.equal(actualPosts,2);
 await f.c.reconcilePendingRequest();assert.equal(f.c.pendingId(),null);assert.equal(f.c.LoretuneSceneRecovery.canRetry(),false);assert.equal(actualPosts,2,'committed lookup cannot submit again');state=await readState();record=state.projects.A.scenes_3d[0];assert.equal(record.proposals.length,2);assert.equal(record.proposals.at(-1).scene.camera.lens_mm,63);
 return {first,second,actualPosts,attempts,sceneCount:state.projects.A.scenes_3d.length,proposalCount:record.proposals.length};
}
(async()=>{const contracts=await checks();const evidence=process.argv[2]?await realHttp(process.argv[2]):null;console.log(JSON.stringify({contracts,evidence}))})().catch(error=>{console.error(error);process.exit(1)});
