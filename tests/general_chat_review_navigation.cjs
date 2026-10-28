'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ui=fs.readFileSync('general-chat-ui.js','utf8'),sidebar=fs.readFileSync('chat-sidebar.js','utf8'),html=fs.readFileSync('index.html','utf8');
const slice=(source,a,b)=>{const start=source.indexOf(a),end=source.indexOf(b,start);assert.ok(start>=0&&end>start,'marker missing: '+a);return source.slice(start,end)};
const line=(source,prefix)=>{const found=source.split('\n').find(value=>value.startsWith(prefix));assert.ok(found,'line missing: '+prefix);return found};
// The product escaper from index.html is injected instead of a test copy.
const productEsc='var '+slice(html,'esc=s=>',';let stateReadEpoch');
let completed=false;process.on('beforeExit',()=>{if(!completed){console.error('review navigation contracts did not complete');process.exitCode=1}});
const clone=value=>JSON.parse(JSON.stringify(value));
const turn={id:'turn',conversation_id:'current',run_id:'run',status:'completed',answer:'saved'};
const project={active_conversation:{id:'current'},general_chat_turns:[turn],shots:{target:{}},
 production_runs:[{id:'run',conversation_id:'current',calls:[{name:'prepare_image_action',result:{status:'proposed',role:'image',action_id:'action'}}]}],
 media_actions:[{id:'action',role:'image',shot:'target',approval:'required'}]};
const context={p:clone(project),scope:'scope-A',currentScope:'scope-A',project(){return this.p},key(){return this.currentScope}};
// Globals called as plain functions deliberately use closure access instead of this.
context.project=()=>context.p;context.key=()=>context.currentScope;
vm.createContext(context);vm.runInContext(slice(ui,' function reviewTargets(',' function controls(')+';globalThis.targets=reviewTargets;globalThis.current=currentReviewTarget;globalThis.label=reviewLabel;',context);
const plain=value=>JSON.parse(JSON.stringify(value));
assert.deepEqual(plain(context.targets(context.p,turn)),[{kind:'image',id:'action',shot:'target',approval:'required',job:false}]);
assert.equal(context.current('turn','action','scope-A','image').id,'action');
assert.equal(context.current('turn','action','scope-A','video'),null,'UI-r2: the stored kind must match as well as the id');
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
context.currentScope='scope-B';assert.equal(context.current('turn','action','scope-A','image'),null);context.currentScope='scope-A';

// Execute the real refresh body with a tiny DOM to check destination invalidation,
// product escaping, distinct names and focus restore, without exporting helpers.
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const document={activeElement:null};
function buttonsFrom(markup){return [...markup.matchAll(/<button type="button" ([^>]*)>([^<]*)<\/button>/g)].map(([,attrs,text])=>{const dataset={};for(const [,name,value] of attrs.matchAll(/data-general-([a-z-]+)="([^"]*)"/g))dataset['general'+name.split('-').map(w=>w[0].toUpperCase()+w.slice(1)).join('')]=decode(value);const described=attrs.match(/aria-describedby="([^"]*)"/);return{dataset,describedBy:described?decode(described[1]):null,text:decode(text),focus(){document.activeElement=this}}})}
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:false,required:false,textContent:'',innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null});return nodes.get(id)};
nodes.set('generalChatTurns',{innerHTML:'',querySelectorAll(){return buttonsFrom(this.innerHTML)}});
Object.assign(context,{p:clone(project),renderedReviews:'',renderedTurns:'',el:node,layout(){},allowed:()=>false,configured:()=>false,bounded:()=>false,label:()=> 'fixture',usageLabel:()=> 'unverified',historyLabel:()=>'',money:()=>'',controls(){},draftRead:()=>'',document,states:{completed:'complete'}});
vm.runInContext(productEsc,context);
// The product D15 fact helpers render the turn summary for media targets.
vm.runInContext(slice(html,'// D15/#41: one money format','function drawMediaCreator(){'),context);
vm.runInContext(slice(ui,' function refresh(){'," el('generalChatPrompt').addEventListener")+';globalThis.draw=refresh;',context);
const turns=()=>node('generalChatTurns').innerHTML;
context.draw();assert.match(turns(),/data-general-review-action="action"/);
assert.match(turns(),/<div class="general-chat-actions"><button type="button" data-general-review-action="action"[^>]*>요청 1 · target 이미지 제작안 검토<\/button><\/div>/,'review buttons use the existing action group');
context.p.media_actions=[];context.draw();assert.doesNotMatch(turns(),/data-general-review-action/,'same turns must invalidate after a destination disappears');assert.doesNotMatch(turns(),/general-chat-actions/,'no empty action group');
context.p=clone(project);const dangerous='긴 장면 <img src=x onerror=alert(1)> "검토"';context.p.shots={[dangerous]:{}};context.p.media_actions[0].shot=dangerous;context.draw();assert.doesNotMatch(turns(),/<img/);assert.match(turns(),/&lt;img/);
context.p=clone(project);context.currentScope='a" onfocus="x\' b';context.draw();assert.match(turns(),/data-general-review-scope="a&quot; onfocus=&quot;x&#39; b"/,'attribute boundary is escaped by the product esc');assert.equal(buttonsFrom(turns())[0].dataset.generalReviewScope,'a" onfocus="x\' b');context.currentScope='scope-A';context.draw();

// Several prepared actions in one turn: same-scene names differ by order and decision.
const many=clone(project);many.shots.other={};
many.production_runs[0].calls=['a1','a2','a3'].map(id=>({name:'prepare_image_action',result:{status:'proposed',role:'image',action_id:id}}));
many.media_actions=[{id:'a1',role:'image',shot:'target',approval:'required'},{id:'a2',role:'image',shot:'target',approval:'rejected'},{id:'a3',role:'image',shot:'other',approval:'approved',job:{id:'j',state:'prepared'}}];
context.p=many;context.draw();let names=buttonsFrom(turns()).map(b=>b.text);
assert.deepEqual(names,['요청 1 · target 이미지 제작안 1/2 검토','요청 1 · target 이미지 제작안 2/2 보기 (거절됨)','요청 1 · other 이미지 제작안 보기 (작업 생성됨)']);
assert.equal(new Set(names).size,names.length,'accessible names are unique');for(const name of names)assert.doesNotMatch(name,/a1|a2|a3|\bj\b/,'internal IDs stay out of names');
context.p.media_actions[0].approval='held';context.draw();assert.equal(buttonsFrom(turns())[0].text,'요청 1 · target 이미지 제작안 1/2 보기 (보류됨)','decision change re-renders the suffix');

// Two turns with one same-scene target each: names differ by request ordinal (I1, voice control), descriptions point at each turn's own prompt.
const twoTurns=clone(project);twoTurns.general_chat_turns=[{...turn,prompt:'첫 요청'},{...turn,id:'turn2',run_id:'run2',prompt:'둘째 요청'}];
twoTurns.production_runs.push({id:'run2',conversation_id:'current',calls:[{name:'prepare_image_action',result:{status:'proposed',role:'image',action_id:'action2'}}]});
twoTurns.media_actions.push({id:'action2',role:'image',shot:'target',approval:'required'});
const kept=context.p;context.p=twoTurns;context.draw();const pair=buttonsFrom(turns());
assert.deepEqual(pair.map(b=>b.text),['요청 1 · target 이미지 제작안 검토','요청 2 · target 이미지 제작안 검토'],'names are distinct across turns');
assert.notEqual(pair[0].describedBy,pair[1].describedBy,'turns are separated by aria-describedby');
const promptText=id=>{const all=[...turns().matchAll(/<p class="general-chat-text" id="([^"]*)">([^<]*)<\/p>/g)].filter(m=>decode(m[1])===id);assert.equal(all.length,1,'describedby target exists once: '+id);return decode(all[0][2])};
assert.deepEqual(pair.map(b=>promptText(b.describedBy)),['첫 요청','둘째 요청']);
// Identical prompts (e.g. a short retry): accessible names still differ, not only the descriptions.
twoTurns.general_chat_turns.forEach(t=>t.prompt='다시');context.draw();const same=buttonsFrom(turns());assert.equal(new Set(same.map(b=>b.text)).size,2,'identical prompts keep distinct names');assert.deepEqual(same.map(b=>promptText(b.describedBy)),['다시','다시']);
context.p=kept;context.draw();

// Focus survives a re-render on the same review or cancel button.
document.activeElement=buttonsFrom(turns())[1];const before=document.activeElement;context.p.media_actions[2].approval='rejected';context.draw();
assert.notEqual(document.activeElement,before,'markup was replaced');assert.equal(document.activeElement.dataset.generalReviewAction,'a2');assert.equal(document.activeElement.dataset.generalReviewTurn,'turn');
context.p.general_chat_turns[0].status='running';context.draw();document.activeElement=buttonsFrom(turns()).find(b=>b.dataset.generalCancel);context.p.media_actions[0].approval='rejected';context.draw();assert.equal(document.activeElement.dataset.generalCancel,'turn');
assert.match(turns(),/<div class="general-chat-actions">(<button[^>]*>[^<]*<\/button>){4}<\/div>/,'review and cancel share one action group');
document.activeElement=null;

// Source contracts: the arrival card is named by its own heading, next-step tool labels and the arrival outline token.
{const m={creatorDiagnostic:()=>'',mediaRightsDrafts:new Map(),mediaDraftKey:value=>value};vm.createContext(m);vm.runInContext(productEsc+';'+slice(html,'function mediaActionMarkup(x){','function drawMediaCreator(){')+';globalThis.card=mediaActionMarkup;',m);
 const markup=m.card({id:'act"1',shot:'장면',role:'image',approval:'required',model:'m',prompt:'p',estimate:{amount:'0.01',currency:'USD'},reason:'r',output_policy:'o'});
 const labelled=markup.match(/^<article class="guided-card media-action-card"[^>]* aria-labelledby="([^"]+)">/),heading=[...markup.matchAll(/<h3 id="([^"]+)">/g)];
 assert.ok(labelled,'card article carries aria-labelledby');assert.equal(heading.length,1);assert.equal(labelled[1],heading[0][1],'aria-labelledby matches the card heading id');assert.equal(decode(labelled[1]),'mediaActionTitle-act"1');}
{const m={};vm.createContext(m);vm.runInContext(line(ui,' const toolLabels=')+';globalThis.out=toolLabels;',m);
 assert.deepEqual(Object.fromEntries(['get_generation_job','estimate_media_plan','prepare_video_action','get_agent_settings','propose_preference_rule','propose_scene_3d'].map(name=>[name,m.out[name]])),
  {get_generation_job:'생성 작업 상태 조회 · 승인 아님',estimate_media_plan:'준비된 제작안 견적 합계 · 청구 아님',prepare_video_action:'영상 제작안 준비 · 실행 없음',get_agent_settings:'에이전트 설정 조회',propose_preference_rule:'선호 규칙 후보 제안 · 승인 전',propose_scene_3d:'3D 장면 변경 제안 · 승인 전'});}
{const css=fs.readFileSync('studio.css','utf8');assert.match(line(css,'.lt-ui .media-action-card[data-review-arrival] {'),/\{\s*outline:2px solid var\(--ui-focus\);/,'arrival outline uses the focus token');}

// controls(): review buttons follow busy/inFlight only, independent of connection or dirty drafts.
function controlFixture(values){const review={dataset:{generalReviewAction:'a1'},disabled:false},get=id=>({disabled:false});const c={busy:false,inFlight:false,dirty:true,pendingId:()=> 'pending',el:get,project:()=>({general_chat_connection:{available:false},general_chat_turns:[],general_chat_previews:[]}),panel:{querySelectorAll:selector=>{assert.match(selector,/\[data-general-review-action\]/);return [review]}},...values};vm.createContext(c);vm.runInContext(line(ui,' const allowed=')+'\n'+line(ui,' function controls()')+'\ncontrols();',c);return review.disabled}
assert.equal(controlFixture({}),false,'dirty/pending/disconnected do not block navigation');assert.equal(controlFixture({busy:true}),true);assert.equal(controlFixture({inFlight:true}),true);

function navigationFixture(){
 const events=[],p=clone(project),d={activeElement:null},card={dataset:{actionCard:'action'},getClientRects:()=>[{}],addEventListener(name,callback,options){assert.equal(name,'blur');assert.equal(options.once,true);card.blur=()=>{d.activeElement=null;callback()}}};
 const c={Promise,navigationSequence:0,currentScope:'scope-A',dirty:false,shotName:'other',activeDialog:null,dialogStack:[],project:()=>p,conversationDraftKey:()=>c.currentScope,document:d,syncDialogs(){},setStep(step,options){events.push('step:'+step+(options?.focus===false?':quiet':''))},choose(name){c.navigationSequence++;events.push('tab:'+name)},focusWorkTarget(target){d.activeElement=target;events.push('focus:'+target.dataset.actionCard)}};
 const shot={dataset:{shot:'target'},disabled:false,click(){c.shotName='target';events.push('shot:target'+('reviewNavigation' in this.dataset?':quiet':''))}};
 d.querySelectorAll=selector=>selector==='[data-action-card]'?[card]:selector==='#shotlist [data-shot]'?[shot]:[];
 vm.createContext(c);vm.runInContext(slice(sidebar,' async function reviewMediaAction(',' workRows.addEventListener')+';globalThis.navigate=reviewMediaAction;',c);
 return{c,p,card,shot,events,valid:()=>p.media_actions.length===1&&p.shots.target!=null};
}
function delayedDialog(f){let close;const dialog={open:true,addEventListener(name,callback){assert.equal(name,'close');close=callback},close(){this.open=false;f.events.push('close-request')},finish(){f.events.push('close-event');close()}};f.c.dialogStack=[dialog];return dialog;}
function handlerFixture(p,navigate){
 const status={textContent:'previous failure'},d={activeElement:null},c={busy:false,inFlight:false,scope:'scope-A',currentScope:'scope-A',p,calls:0,document:d};
 // Re-render replaces buttons: every query returns fresh nodes carrying the same data attributes.
 const turnsNode={querySelectorAll:()=>buttonsFrom('<button type="button" data-general-review-action="action" data-general-review-kind="image" data-general-review-turn="turn" data-general-review-scope="scope-A">x</button>').map(b=>(b.focus=function(){d.activeElement=this},b))};
 c.project=()=>c.p;c.key=()=>c.currentScope;c.song=()=> 'A';c.request=async()=>true;c.el=id=>id==='generalChatStatus'?status:id==='generalChatTurns'?turnsNode:{};
 c.window={LoretuneAgentSidebar:{reviewMediaAction:async(...args)=>{c.calls++;return navigate(...args)}}};
 vm.createContext(c);vm.runInContext(slice(ui,' function reviewTargets(',' function controls(')+'\n'+line(ui," el('generalChatTurns').onclick="),c);
 const button={dataset:{generalReviewAction:'action',generalReviewKind:'image',generalReviewTurn:'turn',generalReviewScope:'scope-A'}};
 return{c,status,d,click:()=>turnsNode.onclick({target:{closest:selector=>selector==='[data-general-review-action]'?button:null}})};
}
const messages={};{const m=line(ui,' const reviewMessages=');const c={};vm.createContext(c);vm.runInContext(m+';globalThis.out=reviewMessages;',c);Object.assign(messages,c.out)}
(async()=>{
 let f=navigationFixture();assert.equal(await f.c.navigate('action','scope-A',f.valid),'opened');assert.deepEqual(f.events,['step:3:quiet','shot:target:quiet','tab:settings','focus:action'],'step heading and mobile panel focus are skipped; only the card receives focus');assert.equal(f.c.document.activeElement,f.card);
 assert.equal('reviewNavigation' in f.shot.dataset,false,'navigation flag is removed after the programmatic click');
 // The real mobile #shotlist listener from index.html: review navigation switches the panel without focus, user clicks keep focus.
 {const panel=[];let listener;const m={mobile:{matches:true},choose:(name,focus)=>panel.push([name,focus]),q:selector=>{assert.equal(selector,'#shotlist');return{addEventListener:(type,callback)=>{assert.equal(type,'click');listener=callback}}}};
  vm.createContext(m);vm.runInContext(line(html,"  q('#shotlist').addEventListener('click'"),m);
  f=navigationFixture();f.shot.click=function(){f.c.shotName='target';listener({target:{closest:selector=>selector==='[data-shot]'?this:null}})};
  assert.equal(await f.c.navigate('action','scope-A',f.valid),'opened');assert.deepEqual(panel,[['preview',false]],'programmatic review click does not focus the preview tab');
  listener({target:{closest:selector=>selector==='[data-shot]'?f.shot:null}});assert.deepEqual(panel[1],['preview',true],'a real user shot click still focuses the preview tab');
  m.mobile.matches=false;listener({target:{closest:selector=>selector==='[data-shot]'?f.shot:null}});m.mobile.matches=true;listener({target:{closest:()=>null}});assert.equal(panel.length,2,'desktop and non-shot clicks do not switch panels');}
 assert.equal(f.card.dataset.reviewArrival,'','arrival mark is visible regardless of input method');f.card.blur();assert.equal('reviewArrival' in f.card.dataset,false,'arrival mark clears on blur');
 f=navigationFixture();f.c.dirty=true;assert.equal(await f.c.navigate('action','scope-A',f.valid),'dirty');assert.deepEqual(f.events,[]);
 f=navigationFixture();f.c.dirty=true;f.c.shotName='target';assert.equal(await f.c.navigate('action','scope-A',f.valid),'opened','dirty draft on the same scene is preserved and still reachable');assert.deepEqual(f.events,['step:3:quiet','tab:settings','focus:action']);
 f=navigationFixture();f.shot.disabled=true;let dialog=delayedDialog(f);assert.equal(await f.c.navigate('action','scope-A',f.valid),'blocked');assert.deepEqual(f.events,[],'missing scene control is detected before closing dialogs or switching steps');assert.equal(dialog.open,true);
 f=navigationFixture();dialog=delayedDialog(f);let pending=f.c.navigate('action','scope-A',f.valid);f.c.currentScope='scope-B';dialog.finish();assert.equal(await pending,'superseded');assert.deepEqual(f.events,['close-request','close-event']);
 f=navigationFixture();dialog=delayedDialog(f);const first=f.c.navigate('action','scope-A',f.valid);const second=f.c.navigate('action','scope-A',f.valid);assert.equal(await second,'opened');dialog.finish();assert.equal(await first,'superseded');assert.equal(f.c.document.activeElement,f.card);
 f=navigationFixture();dialog=delayedDialog(f);const removed=f.c.navigate('action','scope-A',f.valid);f.p.media_actions=[];dialog.finish();assert.equal(await removed,'missing');assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();dialog=delayedDialog(f);const superseded=f.c.navigate('action','scope-A',f.valid);f.c.choose('chat');dialog.finish();assert.equal(await superseded,'superseded');assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.c.setStep=()=>{f.c.currentScope='scope-B'};assert.equal(await f.c.navigate('action','scope-A',f.valid),'superseded');assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.c.document.querySelectorAll=selector=>selector==='#shotlist [data-shot]'?[f.shot]:[];assert.equal(await f.c.navigate('action','scope-A',f.valid),'blocked');assert.equal(f.c.document.activeElement,null);
 f=navigationFixture();f.p.media_actions.push(clone(f.p.media_actions[0]));assert.equal(await f.c.navigate('action','scope-A',()=>true),'missing');assert.deepEqual(f.events,[]);
 f=navigationFixture();f.card.getClientRects=()=>[];assert.equal(await f.c.navigate('action','scope-A',f.valid),'blocked');assert.deepEqual(f.events.slice(-2),['focus:action','tab:chat'],'final-step failure returns to the chat pane where the status is visible');assert.equal('reviewArrival' in f.card.dataset,false);
 f=navigationFixture();f.c.shotName='target';const details={tagName:'DETAILS',open:false,parentElement:null};f.card.parentElement=details;f.card.getClientRects=()=>details.open?[{}]:[];f.card.focus=()=>{f.c.document.activeElement=f.card};f.card.scrollIntoView=()=>{};
 vm.runInContext(slice(sidebar,' function focusWorkTarget(',' function viewWork('),f.c);
 assert.equal(await f.c.navigate('action','scope-A',f.valid),'opened','same-shot card inside collapsed details must be opened before visibility/focus checks');assert.equal(details.open,true);assert.equal(f.c.document.activeElement,f.card);

 // Click handler branches with the real onclick line.
 let h=handlerFixture(clone(project),async()=>'opened');h.c.busy=true;await h.click();assert.equal(h.status.textContent,messages.busy);assert.equal(h.c.calls,0);
 h=handlerFixture(clone(project),async()=>'opened');h.c.inFlight=true;await h.click();assert.equal(h.status.textContent,messages.busy);assert.equal(h.c.calls,0);
 h=handlerFixture(clone(project),async()=>'opened');await h.click();assert.equal(h.status.textContent,'','success clears an earlier failure');assert.equal(h.c.calls,1);
 const arrival={dataset:{actionCard:'action'}};h=handlerFixture(clone(project),async()=>{h.d.activeElement=arrival;return 'opened'});await h.click();assert.equal(h.d.activeElement,arrival,'success keeps focus on the arrival card; the chat button is not refocused');
 for(const reason of ['dirty','missing','blocked']){h=handlerFixture(clone(project),async()=>reason);await h.click();assert.equal(h.status.textContent,messages[reason],reason);assert.equal(h.d.activeElement?.dataset.generalReviewAction,'action',reason+' returns focus to the originating button');}
 assert.equal(new Set([messages.dirty,messages.missing,messages.blocked,messages.busy]).size,4,'each reason has its own guidance');
 h=handlerFixture(clone(project),async()=>undefined);await h.click();assert.equal(h.status.textContent,messages.blocked,'absent sidebar is reported');
 h=handlerFixture(clone(project),async()=>'opened');h.c.window={};await h.click();assert.equal(h.c.calls,0);assert.equal(h.status.textContent,messages.blocked,'window without LoretuneAgentSidebar is reported');assert.equal(h.d.activeElement?.dataset.generalReviewAction,'action','missing sidebar returns focus to the originating button');
 h=handlerFixture(clone(project),async()=>'superseded');await h.click();assert.equal(h.status.textContent,'previous failure','superseded navigation stays silent');assert.equal(h.d.activeElement,null);
 h=handlerFixture(clone(project),async()=>{h.c.scope='scope-B';return 'blocked'});await h.click();assert.equal(h.status.textContent,'previous failure','another conversation receives no message');
 const gone=clone(project);gone.media_actions=[];h=handlerFixture(gone,async()=>'opened');await h.click();assert.equal(h.status.textContent,messages.missing);assert.equal(h.c.calls,0);
 h=handlerFixture(gone,async()=>'opened');h.c.currentScope='scope-B';await h.click();assert.equal(h.status.textContent,'previous failure','stale scope stays silent');
 // Run removed while the real navigation waits for a dialog: the handler's stillCurrent reports it.
 f=navigationFixture();dialog=delayedDialog(f);h=handlerFixture(clone(project),(...args)=>f.c.navigate(...args));const clicked=h.click();h.c.p.production_runs=[];dialog.finish();await clicked;
 assert.equal(h.status.textContent,messages.missing);assert.equal(f.c.document.activeElement,null);assert.equal(h.d.activeElement?.dataset.generalReviewAction,'action');
 completed=true;
 console.log('Exact turn/run/action references, product escaping, distinct names, focus restore, reason codes and asynchronous scoped focus contracts passed');
})().catch(error=>{console.error(error);process.exitCode=1});
