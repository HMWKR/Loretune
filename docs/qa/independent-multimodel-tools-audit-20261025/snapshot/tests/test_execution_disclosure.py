import json,subprocess,unittest
from pathlib import Path
class ExecutionDisclosureTest(unittest.TestCase):
 def test_actual_renderer_persists_completed_details_and_forces_unfinished_visible(self):
  root=Path(__file__).resolve().parents[1]
  code=r"""const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8'),storage=new Map(),node={};let songName='a';
let p={execution_cards:[{id:'one',shot:'shot',description:'fixture',model:'synthetic AI 아님',decision:'approved',job:'job'}],shots:{shot:{takes:[]}},rehearsal_jobs:[{id:'job',state:'collected'}]};
const ctx={state:{workspace_id:'w',project_ids:{a:'p1',b:'p2'}},project:()=>p,song:()=>songName,$:()=>node,sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},esc:s=>String(s),asset:()=>''};
vm.createContext(ctx);
for(const name of ['executionDisclosureKey','executionDisclosureOpen','drawExecutionCards']){const line=html.split('\n').find(x=>x.startsWith('function '+name+'('));vm.runInContext(line,ctx)}
ctx.drawExecutionCards();assert(!node.innerHTML.includes(' open>'));storage.set(ctx.executionDisclosureKey('one'),'open');ctx.drawExecutionCards();assert(node.innerHTML.includes(' open>'));
songName='b';ctx.drawExecutionCards();assert(!node.innerHTML.includes(' open>'));songName='a';ctx.drawExecutionCards();assert(node.innerHTML.includes(' open>'));
for(const state of ['running','prepared','failed',undefined]){p.rehearsal_jobs[0].state=state;storage.set(ctx.executionDisclosureKey('one'),'closed');ctx.drawExecutionCards();assert(node.innerHTML.includes(' open>'));assert(node.innerHTML.includes('공급자 비용 $0'))}
console.log(JSON.stringify({status:'pass',scenarios:8}));"""
  r=subprocess.run(['node','-e',code],cwd=root,capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(r.stdout)['status'],'pass')
