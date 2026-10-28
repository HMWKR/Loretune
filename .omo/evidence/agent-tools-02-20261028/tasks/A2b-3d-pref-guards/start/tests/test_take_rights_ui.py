"""Selected Take rights input: scoped drafts and asynchronous submission."""
import subprocess
import unittest
from pathlib import Path


class TakeRightsUITest(unittest.TestCase):
    def test_draft_isolation_and_async_target(self):
        root = Path(__file__).resolve().parents[1]
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('const takeRightsDrafts=');
const end=html.indexOf('function ensureCreatorReview()',start);
assert(start>=0&&end>start);
const elements={},element=()=>({hidden:false,disabled:false,listeners:{},addEventListener(k,f){this.listeners[k]=f},focus(){}}),input=Object.assign(element(),{value:''}),button=element(),cancel=element(),status=element();
const document={createElement(kind){const e=element();if(kind==='form')Object.defineProperty(e,'innerHTML',{set(x){elements.creatorTakeRightsEvidence=input;elements.creatorTakeRightsSubmit=button;elements.creatorTakeRightsCancel=cancel;elements.creatorTakeRightsStatus=status}});return e}};
let current='one',conversation='a',resolveSave,calls=[];
const shot={revision:7,selected:1,takes:[{id:1,sha256:'hash1',rights:'사용권 미확인'},{id:2,sha256:'hash2',rights:'사용권 미확인'}]};
const p={active_conversation:{id:'a'},shots:{scene:shot}};
const state={workspace_id:'workspace',asset_rights:{}};
const ctx={document,state,Map,Set,JSON,busy:false,project:()=>p,
  currentTakeReview:()=>({song:'song',shot:'scene',take:shot.selected}),
  $:s=>elements[s.slice(1)],act:(action,data)=>{calls.push({action,data});return new Promise(r=>resolveSave=r)}};
vm.createContext(ctx);vm.runInContext(html.slice(start,end),ctx);
ctx.ensureCreatorTakeRights({after(edit,f){elements.creatorTakeRightsEdit=edit;elements.creatorTakeRights=f}});
const edit=elements.creatorTakeRightsEdit;
const form=elements.creatorTakeRights;ctx.renderTakeRights();
assert.equal(form.hidden,false);assert.equal(button.disabled,true);
input.value='  ';input.listeners.input();assert.equal(button.disabled,true);
input.value='사용권 근거 A';input.listeners.input();assert.equal(button.disabled,false);
const first=form.listeners.submit({preventDefault(){}});
assert.deepEqual(JSON.parse(JSON.stringify(calls[0])),{action:'declare_take_rights',data:{song:'song',shot:'scene',take:1,sha256:'hash1',shot_revision:7,evidence:'사용권 근거 A'}});
assert.equal(button.disabled,true);
p.active_conversation.id='b';ctx.renderTakeRights();assert.equal(input.value,'');
input.value='대화 B 초안';input.listeners.input();resolveSave(true);
first.then(()=>{
 assert.equal(input.value,'대화 B 초안');assert.equal(button.disabled,false);
 shot.selected=2;ctx.renderTakeRights();assert.equal(input.value,'');
 state.asset_rights.hash2={blocked:true};ctx.renderTakeRights();assert.equal(form.hidden,true);
 state.asset_rights.hash2.blocked=false;shot.takes[1].rights='근거 확인됨';ctx.renderTakeRights();assert.equal(form.hidden,true);assert.equal(edit.hidden,false);
 edit.listeners.click();assert.equal(form.hidden,false);assert.equal(input.value,'근거 확인됨');
 input.value='취소할 정정';input.listeners.input();cancel.listeners.click();assert.equal(form.hidden,true);assert.equal(edit.hidden,false);
 edit.listeners.click();assert.equal(input.value,'근거 확인됨');input.value='대화 B의 정정';input.listeners.input();
 p.active_conversation.id='a';ctx.renderTakeRights();assert.equal(form.hidden,true);edit.listeners.click();assert.equal(input.value,'근거 확인됨');
 input.value='대화 A의 정정';input.listeners.input();p.active_conversation.id='b';ctx.renderTakeRights();assert.equal(input.value,'대화 B의 정정');
 state.asset_rights.hash2.blocked=true;ctx.renderTakeRights();assert.equal(form.hidden,true);assert.equal(edit.hidden,true);
 form.listeners.submit({preventDefault(){}});assert.equal(calls.length,1);state.asset_rights.hash2.blocked=false;ctx.renderTakeRights();
 const failed=form.listeners.submit({preventDefault(){}});assert.equal(calls[1].data.shot_revision,7);resolveSave(false);
 return failed;
}).then(()=>{
 assert.equal(form.hidden,false);assert.equal(input.value,'대화 B의 정정');
 shot.revision=8;ctx.renderTakeRights();assert.equal(button.disabled,true);assert.match(status.textContent,/변경/);form.listeners.submit({preventDefault(){}});assert.equal(calls.length,2);
 cancel.listeners.click();edit.listeners.click();input.value='대화 B의 정정';input.listeners.input();const retry=form.listeners.submit({preventDefault(){}});assert.equal(calls[2].data.shot_revision,8);
 shot.takes[1].rights='대화 B의 정정';resolveSave(true);return retry;
}).then(()=>{
 assert.equal(form.hidden,true);assert.equal(edit.hidden,false);edit.listeners.click();assert.equal(input.value,'대화 B의 정정');cancel.listeners.click();
 shot.takes[1].rights='사용권 미확인';ctx.renderTakeRights();assert.equal(form.hidden,false);
 shot.selected=1;ctx.renderTakeRights();assert.equal(input.value,'대화 B 초안');
 console.log('take rights isolation and async target PASS');
}).catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', script], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS', result.stdout)


if __name__ == '__main__':
    unittest.main()
