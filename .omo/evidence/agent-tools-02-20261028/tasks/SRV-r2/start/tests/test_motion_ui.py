"""Controlled Node DOM doubles; not browser/pixel accessibility evidence."""
import subprocess,unittest
from pathlib import Path

class MotionUITest(unittest.TestCase):
 def test_context_edit_versions_preview_generation_and_poll_preservation(self):
  root=Path(__file__).resolve().parents[1]
  script=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const elements=new Map(),images=[];let focus='',pending=null;
class E {constructor(id){this.id=id;this.dataset={};this.style={};this.children=[];this.listeners={};this.open=false;this.writes=0;this.hidden=false;this.value='0'}
 setAttribute(){} append(){} replaceChildren(){this.children=[]} addEventListener(e,f){this.listeners[e]=f} focus(){focus=this.id}
 querySelector(selector){return get(this.id+':'+selector)} closest(){return null}
 set innerHTML(s){this.html=s;this.writes++;this.children=s?[{}]:[];for(const m of s.matchAll(/id="([^"]+)"/g))get(m[1])}get innerHTML(){return this.html||''}
 showModal(){this.open=true}close(){this.open=false;this.listeners.close?.()}}
const get=id=>{if(!elements.has(id))elements.set(id,new E(id));return elements.get(id)};
const document={createElement:()=>{const e=new E('');Object.defineProperty(e,'id',{get(){return this._id},set(v){this._id=v;elements.set(v,this)}});return e},getElementById:get,querySelector:()=>get('inspector'),body:get('body')};
const scene=text=>({schema_version:1,width:1920,height:1080,fps:24,frame_count:96,background:'#101010',layers:[{id:'title',kind:'text',text,font:'system-ko-regular',font_size:80,width:1500,height:160,in_frame:0,out_frame:96,color:'#FFFFFF',keyframes:[{frame:0,x:1,y:1,opacity:1,easing:'linear'}]}]});
const proposal=(id,text)=>({id,shot:'s',base_revision:0,status:'proposed',scene:scene(text),source:{mode:'contract-fake'}});
let A={shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[proposal('a','처음')]},B={shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[proposal('b','다른 작품')]},current=A,name='A';
const ctx={document,Map,Image:class{constructor(){images.push(this)}},structuredClone,URLSearchParams,window:{},project:()=>current,song:()=>name,shotName:'s',state:{jobs:[]},busy:false,statuses:{},esc:String,act:()=>new Promise(resolve=>pending=resolve)};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('motion-studio.js','utf8'),ctx);get('motionButton').onclick();
function input(value){get('motionFields').oninput({target:{dataset:{motionField:'text'},type:'text',value,closest:()=>null}})}
async function run(){
 input('저장 요청');const save=get('motionSave').onclick();input('저장 요청');pending(true);await save;
 assert.equal(get('motionSave').disabled,false,'identical-content new input must remain dirty');
 get('motionCancel').onclick();input('A 초안');const crossing=get('motionSave').onclick();current=B;name='B';ctx.window.AethonMotion.refresh();input('B 초안');pending(true);await crossing;
 assert.equal(get('motionSave').disabled,false);assert.match(get('motionFields').innerHTML,/다른 작품/);
 current=A;name='A';ctx.window.AethonMotion.refresh();assert.match(get('motionFields').innerHTML,/A 초안/);get('motionCancel').onclick();
 get('motionPreview').onclick();const old=images.at(-1);current=B;name='B';ctx.window.AethonMotion.refresh();old.onload();assert.equal(get('motionImage').hidden,true,'old context frame cannot appear');
 get('motionCancel').onclick();get('motionPreview').onclick();images.at(-1).onload();assert.equal(get('motionImage').hidden,false);
 input('미저장');get('motionPreview').onclick();assert.equal(images.length,2,'dirty preview does not imply saved frame');
 const writes=get('motionFields').writes;ctx.window.AethonMotion.refresh();assert.equal(get('motionFields').writes,writes,'poll keeps focused inputs');
 get('motionClose').onclick();assert.equal(focus,'motionButton');
 get('motionButton').onclick();get('motionCancel').onclick();input('거부 후 보존');
 ctx.act=async(a,d,p,notify)=>{notify({status:'rejected'});for(const e of elements.values())e.disabled=false;return false};
 await get('motionSave').onclick();assert.equal(get('motionApprove').disabled,true,'blanket re-enable must not override dirty approval guard');
 assert.equal(get('motionSave').disabled,false);assert.match(get('motionStatus').textContent,/거부.*입력은 유지/);
 let uncertain='existing-request';ctx.pendingId=()=>uncertain;
 ctx.act=async(a,d,p,notify)=>{notify({status:'unknown'});for(const e of elements.values())e.disabled=false;return false};
 await get('motionSave').onclick();assert.equal(get('motionSave').disabled,true);assert.equal(get('motionApprove').disabled,true);
 assert.equal(get('motionRecover').hidden,false);assert.match(get('motionStatus').textContent,/새로 제출하지 말고/);
 ctx.reconcilePendingRequest=async()=>{uncertain=null};await get('motionRecover').onclick();assert.equal(get('motionSave').disabled,false);assert.equal(get('motionApprove').disabled,true,'reconcile must not discard draft');
 ctx.act=async(a,d,p,notify)=>{notify({status:'committed_refresh_failed'});return false};
 await get('motionSave').onclick();assert.match(get('motionStatus').textContent,/저장은 완료/);assert.equal(get('motionApprove').disabled,true);
 ctx.act=async(a,d,p,notify)=>{current=A;name='A';ctx.window.AethonMotion.refresh();get('motionStatus').textContent='A 상태';notify({status:'rejected'});return false};
 await get('motionSave').onclick();assert.equal(get('motionStatus').textContent,'A 상태','late failure cannot replace new context status');
 console.log('same-text edit, crossing response, per-context draft, stale frame, dirty preview, poll preservation, focus return: pass');
}run().catch(e=>{console.error(e);process.exit(1)});
'''
  result=subprocess.run(['node','-e',script],cwd=root,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
