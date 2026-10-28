'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ui=fs.readFileSync('general-chat-ui.js','utf8'),sidebar=fs.readFileSync('chat-sidebar.js','utf8');
const slice=(source,a,b)=>source.slice(source.indexOf(a),source.indexOf(b,source.indexOf(a)));
const clone=value=>JSON.parse(JSON.stringify(value));
const turn={id:'turn',conversation_id:'current',run_id:'run',status:'completed',answer:'saved'};
const project={active_conversation:{id:'current'},general_chat_turns:[turn],shots:{target:{}},
 production_runs:[{id:'run',conversation_id:'current',calls:[{name:'prepare_image_action',result:{status:'proposed',role:'image',action_id:'action'}}]}],
 media_actions:[{id:'action',role:'image',shot:'target',approval:'required'}]};
const context={p:clone(project),scope:'scope-A',currentScope:'scope-A',project(){return this.p},key(){return this.currentScope}};
// Globals called as plain functions deliberately use closure access instead of this.
context.project=()=>context.p;context.key=()=>context.currentScope;
vm.createContext(context);vm.runInContext(slice(ui,' function reviewTargets(',' function controls(')+';globalThis.targets=reviewTargets;globalThis.current=currentReviewTarget;',context);
const plain=value=>JSON.parse(JSON.stringify(value));
assert.deepEqual(plain(context.targets(context.p,turn)),[{id:'action',shot:'target'}]);
assert.equal(context.current('turn','action','scope-A').id,'action');
for(const mutate of [
 p=>delete p.general_chat_turns[0].run_id,
 p=>p.general_chat_turns[0].conversation_id='foreign',
 p=>p.production_runs=[],
 p=>p.production_runs.push(clone(p.production_runs[0])),
 p=>p.production_runs[0].conversation_id='foreign',
 p=>p.production_runs[0].calls[0].result.status='invalid_arguments',
 p=>p.production_runs[0].calls[0].result.role='video',
 p=>p.production_runs[0].calls.push(clone(p.production_runs[0].calls[0])),
 p=>p.media_actions=[],
 p=>p.media_actions.push(clone(p.media_actions[0])),
 p=>p.media_actions[0].role='video',
 p=>delete p.shots.target
]){const p=clone(project);mutate(p);assert.deepEqual(plain(context.targets(p,p.general_chat_turns[0])),[]);}
context.currentScope='scope-B';assert.equal(context.current('turn','action','scope-A'),null);context.currentScope='scope-A';

// Execute the real refresh body with a tiny DOM to check destination invalidation
// and escaping, without exporting implementation-only helpers in the product.
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:false,required:false,textContent:'',innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null});return nodes.get(id)};
Object.assign(context,{p:clone(project),renderedReviews:'',renderedTurns:'',el:node,layout(){},allowed:()=>false,configured:()=>false,bounded:()=>false,label:()=> 'fixture',usageLabel:()=> 'unverified',historyLabel:()=>'',money:()=>'',controls(){},draftRead:()=>'',document:{activeElement:null},states:{completed:'complete'},esc:value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))});
vm.runInContext(slice(ui,' function refresh(){'," el('generalChatPrompt').addEventListener")+';globalThis.draw=refresh;',context);
context.draw();assert.match(node('generalChatTurns').innerHTML,/data-general-review-action="action"/);
context.p.media_actions=[];context.draw();assert.doesNotMatch(node('generalChatTurns').innerHTML,/data-general-review-action/,'same turns must invalidate after a destination disappears');
context.p=clone(project);const dangerous='긴 장면 <img src=x onerror=alert(1)> "검토"';context.p.shots={[dangerous]:{}};context.p.media_actions[0].shot=dangerous;context.draw();assert.doesNotMatch(node('generalChatTurns').innerHTML,/<img/);assert.match(node('generalChatTurns').innerHTML,/&lt;img/);

function navigationFixture(){
 const events=[],p=clone(project),card={dataset:{actionCard:'action'},getClientRects:()=>[{}]},d={activeElement:null};
 const c={Promise,navigationSequence:0,currentScope:'scope-A',dirty:false,shotName:'other',activeDialog:null,dialogStack:[],project:()=>p,conversationDraftKey:()=>c.currentScope,document:d,syncDialogs(){},setStep(step){events.push('step:'+step)},choose(name){c.navigationSequence++;events.push('tab:'+name)},focusWorkTarget(target){d.activeElement=target;events.push('focus:'+target.dataset.actionCard)}};
 d.querySelectorAll=selector=>selector==='[data-action-card]'?[card]:selector==='#shotlist [data-shot]'?[{dataset:{shot:'target'},disabled:false,click(){c.shotName='target';events.push('shot:target')}}]:[];
 vm.createContext(c);vm.runInContext(slice(sidebar,' async function reviewMediaAction(',' workRows.addEventListener')+';globalThis.navigate=reviewMediaAction;',c);
 return{c,p,card,events,valid:()=>p.media_actions.length===1&&p.shots.target!=null};
}
function delayedDialog(f){let close;const dialog={open:true,addEventListener(name,callback){assert.equal(name,'close');close=callback},close(){this.open=false;f.events.push('close-request')},finish(){f.events.push('close-event');close()}};f.c.dialogStack=[dialog];return dialog;}
(async()=>{
 let f=navigationFixture();assert.equal(await f.c.navigate('action','scope-A',f.valid),true);assert.deepEqual(f.events,['step:3','shot:target','tab:settings','focus:action']);assert.equal(f.c.document.activeElement,f.card);
 f=navigationFixture();f.c.dirty=true;assert.equal(await f.c.navigate('action','scope-A',f.valid),false);assert.deepEqual(f.events,[]);
 f=navigationFixture();let dialog=delayedDialog(f);const pending=f.c.navigate('action','scope-A',f.valid);f.c.currentScope='scope-B';dialog.finish();assert.equal(await pending,false);assert.deepEqual(f.events,['close-request','close-event']);
 f=navigationFixture();dialog=delayedDialog(f);const first=f.c.navigate('action','scope-A',f.valid);const second=f.c.navigate('action','scope-A',f.valid);assert.equal(await second,true);dialog.finish();assert.equal(await first,false);assert.equal(f.c.document.activeElement,f.card);
 f=navigationFixture();dialog=delayedDialog(f);const removed=f.c.navigate('action','scope-A',f.valid);f.p.media_actions=[];dialog.finish();assert.equal(await removed,false);assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();dialog=delayedDialog(f);const superseded=f.c.navigate('action','scope-A',f.valid);f.c.choose('chat');dialog.finish();assert.equal(await superseded,false);assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.c.setStep=()=>{f.c.currentScope='scope-B'};assert.equal(await f.c.navigate('action','scope-A',f.valid),false);assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.c.document.querySelectorAll=()=>[];assert.equal(await f.c.navigate('action','scope-A',f.valid),false);assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.p.media_actions.push(clone(f.p.media_actions[0]));assert.equal(await f.c.navigate('action','scope-A',()=>true),false);assert.deepEqual(f.events,[]);
 f=navigationFixture();f.c.shotName='target';const details={tagName:'DETAILS',open:false,parentElement:null};f.card.parentElement=details;f.card.getClientRects=()=>details.open?[{}]:[];f.card.focus=()=>{f.c.document.activeElement=f.card};f.card.scrollIntoView=()=>{};
 vm.runInContext(slice(sidebar,' function focusWorkTarget(',' function viewWork('),f.c);
 assert.equal(await f.c.navigate('action','scope-A',f.valid),true,'same-shot card inside collapsed details must be opened before visibility/focus checks');assert.equal(details.open,true);assert.equal(f.c.document.activeElement,f.card);
 console.log('Exact turn/run/action references, escaping/invalidation and asynchronous scoped focus contracts passed');
})().catch(error=>{console.error(error);process.exitCode=1});
