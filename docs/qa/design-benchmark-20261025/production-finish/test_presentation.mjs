import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const D=new URL('.',import.meta.url),read=n=>fs.readFileSync(new URL(n,D),'utf8');
const ctx=vm.createContext({esc:x=>String(x??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))});
vm.runInContext(read('production-presentation.js'),ctx);
const results=[];function test(name,f){f();results.push({name,passed:true})}
const p=(selection,cap)=>({model_settings:{selections:{image:selection}},media_connections:{image:cap}});
test('empty selection stays empty',()=>assert.equal(ctx.productionModelView(p(null,null),'image').state,'empty'));
test('saved selection survives missing connection projection',()=>{const x=ctx.productionModelView(p('fal-flux-schnell',null),'image');assert.equal(x.name,'FLUX Schnell');assert.equal(x.state,'unverified')});
test('unverified is not active',()=>assert.equal(ctx.productionModelView(p('a',{model:'a',state:'unverified',available:false}),'image').label,'연결 확인 필요'));
test('blocked wins over inconsistent can_prepare',()=>assert.equal(ctx.productionModelView(p('a',{model:'a',state:'blocked',can_prepare:true}),'image').state,'blocked'));
test('test preparation is explicit and not real activation',()=>assert.equal(ctx.productionModelView(p('a',{model:'a',state:'unverified',can_prepare:true,mode:'contract-fake'}),'image').label,'테스트 준비 가능'));
test('preparable is not execution approval',()=>assert.equal(ctx.productionModelView(p('a',{model:'a',state:'unverified',can_prepare:true}),'image').label,'입력·견적 준비 가능'));
test('available alone never invents permission',()=>assert.equal(ctx.productionModelView(p('a',{model:'a',state:'available',available:true}),'image').state,'unverified'));
test('unknown model identity preserved',()=>assert.equal(ctx.productionModelView(p('new/model',null),'image').name,'new/model'));
test('model and scene text is escaped',()=>{const h=ctx.productionOverviewMarkup(p('<img>',null),'<script>');assert(!h.includes('<script>'));assert(h.includes('&lt;script&gt;'));assert(h.includes('&lt;img&gt;'))});
const base=read('baseline-staged.html'),candidate=read('candidate-index.html');
ctx.state={workspace_id:'qa'};ctx.takeReviewKey=(w,p,s,t)=>JSON.stringify([w,p,s,t]);
const data={song:'qa-project',shot:'A',take:1};let called;
ctx.act=async(action,payload)=>{called={action,payload};return false};
await ctx.saveReviewWithFeedback('review_take',data);
test('feedback retains original command and payload',()=>{assert.equal(called.action,'review_take');assert.equal(called.payload,data)});
test('failed feedback is scoped to original context',()=>{assert.equal(vm.runInContext('productionReviewErrors.size',ctx),1);assert(vm.runInContext('productionReviewErrors.has(JSON.stringify(["qa","qa-project","A",1]))',ctx))});
ctx.act=async()=>true;await ctx.saveReviewWithFeedback('review_take',data);
test('successful save clears only matching feedback',()=>assert.equal(vm.runInContext('productionReviewErrors.size',ctx),0));
function slice(s,a,b){const i=s.indexOf(a);assert(i>=0);return s.slice(i,s.indexOf(b,i+1))}
for(const [name,a,b]of [
 ['preparation authority','function mediaPreparation(','function mediaActionMarkup('],
 ['action markup and permissions','function mediaActionMarkup(','function drawMediaCreator('],
 ['media command handlers',"$('#mediaRole').onchange=",'function imageConnectionMarkup('],
 ['F07 scoped review controller','function createTakeReviewStore(','// DOM glue.'],
 ['review actions',"$('#clips').onchange=",'function drawComparison(']
])test(name+' unchanged',()=>assert.equal(slice(candidate,a,b),slice(base,a,b)));
test('all source IDs preserved',()=>{for(const m of base.matchAll(/\bid="([\w-]+)"/g))assert(candidate.includes(m[0]),m[1])});
test('comparison media is contained with native video controls',()=>{const x=slice(candidate,'function drawComparison()',"$('#compareButton').onclick");assert(x.includes('comparison-media-stage'));assert(x.includes(' controls>'));assert(!x.includes('object-fit:cover'))});
fs.writeFileSync(new URL('focused-tests.json',D),JSON.stringify({passed:results.length,results},null,2));console.log(JSON.stringify({passed:results.length}));
