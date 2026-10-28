/* Contract doubles complement browser tests; they are not visual evidence. */
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const elements=new Map(),storage=new Map();let focus='',pending=null,finishRead=null;
class SyntheticFileReader {readAsDataURL(file){this.result='data:model/gltf-binary;base64,Z2xURg==';if(file.delayed)finishRead=()=>this.onload();else this.onload()}}
class Element {
 constructor(id=''){this.id=id;this.dataset={};this.disabled=false;this.hidden=false;this.children=[];this.listeners={};this.open=false;this.value='';this.writes=0}
 setAttribute(){} after(){} append(){} reportValidity(){return true} querySelectorAll(){return []} focus(){focus=this.id}
 addEventListener(name,fn){this.listeners[name]=fn} showModal(){this.open=true} close(){this.open=false;this.listeners.close?.()}
 set innerHTML(value){this.html=value;this.writes++;this.children=value?[{}]:[];for(const match of value.matchAll(/id="([^"]+)"/g))get(match[1])}get innerHTML(){return this.html||''}
}
function get(id){if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id)}
const document={createElement(){const el=new Element();Object.defineProperty(el,'id',{get(){return this._id},set(value){this._id=value;elements.set(value,this)}});return el},getElementById:get,querySelector(){return get('inspector')},body:get('body')};
const sceneConnection={available:false,mode:'disconnected'};
const makeProject=name=>({name,shots:{s:{description:'합성 장면'}},active_conversation:{id:'conv-'+name},scenes_3d:[],scene_3d_jobs:[],scene_3d_connection:sceneConnection});
let a=makeProject('A'),b=makeProject('B'),current=a,name='A',sent=[];
const ctx={document,Map,structuredClone,JSON,Math,Number,FileReader:SyntheticFileReader,sessionStorage:{getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,value)},window:{},state:{workspace_id:'workspace'},project:()=>current,song:()=>name,shotName:'s',busy:false,esc:value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),pendingId:()=>pending};
ctx.act=async(action,data,_,notify)=>{
 sent.push({action,data:structuredClone(data)});
 if(action==='scene_create')current.scenes_3d=[{id:'scene',shot:'s',shot_id:'server-id',head:0,versions:[],proposals:[{id:'proposal-1',base_revision:0,scene:structuredClone(data.scene),status:'proposed'}]}];
 if(action==='scene_replace_draft'){const record=current.scenes_3d[0];record.proposals[0].status='superseded';record.proposals.push({id:'proposal-2',base_revision:0,scene:structuredClone(data.scene),status:'proposed'})}
 if(action==='scene_propose'){const record=current.scenes_3d[0],scene=structuredClone(record.versions.at(-1).scene);for(const op of data.operations){const target=op.target==='camera'?scene.camera:scene[op.target==='object'?'objects':'lights'].find(x=>x.id===op.id);if(op.field==='asset'){scene.schema_version=2;target.kind='mesh';delete target.color}target[op.field]=structuredClone(op.value)}record.proposals.push({id:'proposal-'+(record.proposals.length+1),base_revision:record.head,scene,status:'proposed'})}
 if(action==='scene_review'){const record=current.scenes_3d[0];const p=record.proposals.at(-1);p.status='applied';record.head++;record.versions.push({id:record.head,scene:structuredClone(p.scene),approval:{id:'grant-'+record.head}})}
 let result={};if(action==='scene_asset_import'){const asset={id:'asset-'+sent.length,filename:data.filename,sha256:'c'.repeat(64),profile:'gltf2-static-pbr-v1',rights:data.rights};current.scene_3d_assets=[...(current.scene_3d_assets||[]),asset];result={scene_asset:asset}}
 notify?.({status:'committed',result});return true;
};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('scene-studio.js','utf8'),ctx);
function input(path,value,type='number'){get('sceneStudioFields').oninput({target:{dataset:{scenePath:path},type,value}})}
async function run(){
 sceneConnection.available=true;get('sceneStudioButton').onclick();await get('sceneStudioSave').onclick();await get('sceneStudioApprove').onclick();
 const r=current.scenes_3d[0];current.shots.s.takes=[{id:'take1'}];current.scene_3d_jobs=[{id:'job1',scene_id:r.id,scene_revision:r.head,status:'completed',take:'take1',download:'/assets/scene-'+('a'.repeat(64))+'.png'}];ctx.window.AethonScene.refresh();assert.match(get('sceneStudioCapability').textContent,/현재 구도의 이미지 후보가 준비/);
 r.versions[0].requires_review=true;ctx.window.AethonScene.refresh();assert.equal(get('sceneStudioRender').disabled,true);assert.doesNotMatch(get('sceneStudioCapability').textContent,/현재 구도의 이미지 후보가 준비/);assert.match(get('sceneStudioSummary').textContent,/이전 승인과 결과는 보존/);assert.match(get('sceneStudioJobs').innerHTML,/이전 실행 기준의 후보/);assert.match(get('sceneStudioJobs').innerHTML,/<img/);const count=sent.length;await get('sceneStudioRender').onclick();assert.equal(sent.length,count);
 current=b;name='B';ctx.window.AethonScene.refresh();await get('sceneStudioSave').onclick();current.scenes_3d[0].proposals[0].requires_review=true;ctx.window.AethonScene.refresh();assert.equal(get('sceneStudioApprove').disabled,true);assert.equal(get('sceneStudioSave').disabled,false);await get('sceneStudioSave').onclick();assert.equal(sent.at(-1).action,'scene_replace_draft');assert.equal(get('sceneStudioApprove').disabled,false);
 console.log('PASS stale candidate hidden; previous image preserved; render handler guarded; initial stale draft recoverable');
}run().catch(e=>{console.error(e);process.exitCode=1});
