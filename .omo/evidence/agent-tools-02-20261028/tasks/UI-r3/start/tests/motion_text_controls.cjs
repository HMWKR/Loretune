// Execute the actual starter/input/save handlers; native validation runs in Python.
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const elements=new Map();let submitted;
class Element {
 constructor(){this.dataset={};this.style={};this.children=[];this.open=false}
 setAttribute(){} append(){} addEventListener(){} focus(){}
 replaceChildren(){this.children=[]}
 querySelector(){return {focus(){}}}
 set innerHTML(value){this.html=value;this.children=value?[{}]:[]}
 get innerHTML(){return this.html||''}
 showModal(){this.open=true} close(){this.open=false}
}
const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id)};
const document={createElement:()=>{const element=new Element();Object.defineProperty(element,'id',{set(id){elements.set(id,this)}});return element},getElementById:get,querySelector:()=>get('inspector'),body:get('body')};
const project={active_conversation:{id:'starter'},shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[]};
const context={document,Map,structuredClone,window:{},project:()=>project,song:()=>'song',shotName:'s',state:{jobs:[]},busy:false,statuses:{},esc:value=>String(value??''),
 act:async(action,data)=>{assert.equal(action,'motion_propose');submitted=structuredClone(data.scene);project.motion_proposals.push({id:'saved',shot:'s',base_revision:0,status:'proposed',scene:structuredClone(submitted),source:{mode:'human-edit'}});return true}};
vm.createContext(context);vm.runInContext(fs.readFileSync('motion-studio.js','utf8'),context);
async function run(){
 get('motionButton').onclick();get('motionStart').onclick();
 get('motionFields').oninput({target:{dataset:{motionField:'text'},type:'textarea',value:'음원으로 시작하는\n우리의 영상',closest:()=>null}});
 await get('motionSave').onclick();assert(submitted,'starter save must submit its scene');
 assert.equal(project.motion_proposals.length,1,'starter save must create one proposal');
 process.stdout.write(JSON.stringify(submitted));
}
run().catch(error=>{console.error(error);process.exit(1)});
