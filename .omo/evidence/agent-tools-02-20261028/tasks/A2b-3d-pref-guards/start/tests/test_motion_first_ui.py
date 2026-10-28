"""Local motion starter behavior with controlled DOM; browser evidence is separate."""
import subprocess
import unittest
from pathlib import Path


class MotionFirstUITest(unittest.TestCase):
    def test_first_text_draft_validation_and_conversation_isolation(self):
        root = Path(__file__).resolve().parents[1]
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const elements=new Map(),images=[];let calls=[];
class E {constructor(){this.dataset={};this.style={};this.children=[];this.listeners={};this.value='';this.open=false}
 setAttribute(){} append(){} replaceChildren(){this.children=[]} addEventListener(e,f){this.listeners[e]=f} focus(){} querySelector(){return {focus(){}}}
 set innerHTML(s){this.html=s;this.children=s?[{}]:[];for(const m of s.matchAll(/id="([^"]+)"/g))get(m[1])}get innerHTML(){return this.html||''}
 showModal(){this.open=true}close(){this.open=false;this.listeners.close?.()}}
const get=id=>{if(!elements.has(id))elements.set(id,new E());return elements.get(id)};
const document={createElement:()=>{const e=new E();Object.defineProperty(e,'id',{set(v){elements.set(v,this)}});return e},getElementById:get,querySelector:()=>get('inspector'),body:get('body')};
const A={active_conversation:{id:'A'},shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[]};
const B={active_conversation:{id:'B'},shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[]};let p=A;
const ctx={document,Map,Image:class{constructor(){images.push(this)}},structuredClone,URLSearchParams,window:{},project:()=>p,song:()=> 'song',shotName:'s',state:{jobs:[]},busy:false,statuses:{},esc:String,
 act:async(action,data)=>{calls.push({action,data});p.motion_proposals.push({id:'saved',shot:'s',base_revision:0,status:'proposed',scene:data.scene,source:{mode:'human-edit'}});return true}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('motion-studio.js','utf8'),ctx);
function input(text){get('motionFields').oninput({target:{dataset:{motionField:'text'},type:'text',value:text,closest:()=>null}})}
async function run(){
 get('motionButton').onclick();get('motionStart').onclick();
 assert.equal(get('motionApprove').disabled,true);await get('motionSave').onclick();assert.equal(calls.length,0);assert.match(get('motionStatus').textContent,/문구를 입력/);
 input('첫 문구');p=B;ctx.window.AethonMotion.refresh();get('motionStart').onclick();input('다른 대화 문구');
 p=A;ctx.window.AethonMotion.refresh();assert.match(get('motionFields').innerHTML,/첫 문구/);await get('motionSave').onclick();
 assert.equal(calls.length,1);assert.equal(calls[0].action,'motion_propose');const scene=calls[0].data.scene;
 assert.equal(scene.layers[0].text,'첫 문구');assert.equal(scene.layers[0].keyframes.length,2);assert.equal(scene.layers[0].keyframes[0].opacity,0);assert.equal(scene.layers[0].keyframes[1].opacity,1);
 get('motionPreview').onclick();assert.equal(new URLSearchParams(images.at(-1).src.split('?')[1]).get('conversation'),'A');
 p=B;ctx.window.AethonMotion.refresh();assert.match(get('motionFields').innerHTML,/다른 대화 문구/);get('motionCancel').onclick();assert.equal(get('motionSave').disabled,true);assert.equal(calls.length,1);
 B.shots.s.motion_head=1;B.shots.s.motion_grant_available=false;ctx.window.AethonMotion.refresh();assert.equal(get('motionRender').disabled,true);assert.match(get('motionContext').textContent,/이 대화에서 사용할 승인이 없습니다/);assert.equal(get('motionRestore').disabled,false);
 B.shots.s.motion_grant_available=true;ctx.window.AethonMotion.refresh();assert.equal(get('motionRender').disabled,false);assert.doesNotMatch(get('motionContext').textContent,/이 대화에서 사용할 승인이 없습니다/);
}
run().catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', script], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
