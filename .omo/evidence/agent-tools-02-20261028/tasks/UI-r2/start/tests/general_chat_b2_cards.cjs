'use strict';
// B2: D15 facts on the model card, chat turn summary, work status and agent settings; chat review
// navigation to video (S5), 3D and motion (S8) proposals; design #41 #44 #45 #46 #49; I1 names.
// Runs the product functions sliced from the shipped files. Optional argv[2]: JSON of real server
// projections written by tests/test_general_chat_b2_cards.py.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ui=fs.readFileSync('general-chat-ui.js','utf8'),sidebar=fs.readFileSync('chat-sidebar.js','utf8'),html=fs.readFileSync('index.html','utf8'),css=fs.readFileSync('studio.css','utf8');
const scene=fs.readFileSync('scene-studio.js','utf8'),motion=fs.readFileSync('motion-studio.js','utf8');
const slice=(source,a,b)=>{const start=source.indexOf(a),end=source.indexOf(b,start);assert.ok(start>=0&&end>start,'marker missing: '+a);return source.slice(start,end)};
const line=(source,prefix)=>{const found=source.split('\n').find(value=>value.startsWith(prefix));assert.ok(found,'line missing: '+prefix);return found};
const productEsc='var '+slice(html,'esc=s=>',';let stateReadEpoch');
const productFacts=slice(html,'function mediaActionMarkup(x){','function drawMediaCreator(){');
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const clone=value=>JSON.parse(JSON.stringify(value));
let completed=false;process.on('beforeExit',()=>{if(!completed){console.error('B2 card contracts did not complete');process.exitCode=1}});

// Product card + fact helpers.
const cards={creatorDiagnostic:()=>'',mediaRightsDrafts:new Map(),mediaDraftKey:value=>value};vm.createContext(cards);
vm.runInContext(productEsc+';'+productFacts+';globalThis.card=mediaActionMarkup;globalThis.facts=mediaFacts;globalThis.factsLine=mediaFactsLine;globalThis.money=usd;',cards);
const text=markup=>decode(markup.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ');
const outsideDetails=markup=>markup.replace(/<details[\s\S]*?<\/details>/g,'');
const insideDetails=markup=>(markup.match(/<details class="lt-provenance-detail">[\s\S]*?<\/details>/)||[''])[0];

// #41: one money format.
for(const [value,expected] of [['0.010000','$0.01'],['.1','$0.1'],[0.003687,'$0.003687'],[0.4,'$0.4'],['0','$0'],['0.35','$0.35'],['12','$12'],['abc','금액 확인 필요'],[null,'금액 확인 필요']])assert.equal(cards.money(value),expected,String(value));
assert.equal(line(ui,' const money='),' const money=n=>usd(Number(n)/1000000);','chat review card uses the shared money format');

// D15 card: agent proposal with a different model, documented-estimate quote and a priced unit.
const unit={amount:'0.07',currency:'USD',unit:'second',source:'https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video',fetched_at:'2026-10-28T09:28:18Z',revision:'fal-public-model-pages-20261028',kind:'documented-estimate'};
const agentVideo={id:'v1',shot:'장면 1',role:'video',model:'fal-ai/kling-video/v2.6/pro/image-to-video',prompt:'blue',options:{duration:5,generate_audio:false},estimate:{amount:'0.35',currency:'USD'},estimate_kind:'documented-estimate',mode:'provider-unverified',estimate_expired:false,approval:'required',can_approve:true,can_execute:false,can_decide:true,reason:'입력·모델·예상 비용을 검토하세요.',output_policy:'비공개 출력',
 price:{unit_price:unit,quantity:5,expected_total:{amount:'0.35',currency:'USD'},formula:'0.07 USD/초 × 5초 = 0.35 USD',quote_total:{amount:'0.35',currency:'USD'},matches_quote:true},price_source:'https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api',price_revision:'quote-r1',quote_expires:4102444800,quote_expired:false,
 record:'recorded',actor:'agent',model_reason:'움직임 품질이 더 높습니다.',model_reason_label:'모델이 제시한 이유(검증 안 됨)',provenance:{engine:'contract-fake',chat_model:'claude-haiku-5-5',permission_mode:'review',effort:'medium',run:'r',call:'c'},project_selection:'fal-kling-2-5-turbo',differs_from_project:true};
let markup=cards.card(agentVideo),front=text(outsideDetails(markup)),detail=text(insideDetails(markup));
for(const fact of ['견적 총액 $0.35 · 문서 기준 추정','단가 $0.07/초 · 문서 기준 추정','5초 · 무음','만료 시각','모델 fal-ai/kling-video/v2.6/pro/image-to-video · 프로젝트 선택과 다름 (프로젝트: fal-kling-2-5-turbo)','모델이 제시한 이유(검증 안 됨): 움직임 품질이 더 높습니다.'])assert.ok(front.includes(fact),'decision point shows: '+fact);
for(const fact of ['단가 출처 '+unit.source,'개정 fal-public-model-pages-20261028','조회 2026-10-28T09:28:18Z','견적 출처 '+agentVideo.price_source,'개정 quote-r1','계산 0.07 USD/초 × 5초 = 0.35 USD','대화 모델 claude-haiku-5-5 · 권한 검토 후 편집 · 추론 강도 보통'])assert.ok(detail.includes(fact),'provenance detail shows: '+fact);
assert.ok(!front.includes('대화 모델 claude'),'#46: provenance stays in the disclosure');
assert.match(markup,/<a href="https:\/\/fal\.ai\/models\/fal-ai\/kling-video\/v2\.6\/pro\/image-to-video" target="_blank" rel="noopener noreferrer">/,'source is a link');
assert.match(markup,/<p class="lt-cost-facts">견적 총액/,'#41/#46: cost facts use the shared one-line class');
assert.equal((markup.match(/<details/g)||[]).length,1,'one disclosure for price, source, provenance and transfer conditions (diagnostic stubbed)');
assert.ok(markup.indexOf('lt-cost-facts')<markup.indexOf('lt-provenance-detail'),'cost precedes secondary detail');
assert.match(markup,/<div class="toolbar media-action-decisions"><button data-media-decision="approved" data-action="v1">이 조건 승인 · \$0\.35<\/button><button data-media-decision="held"[^>]*>보류<\/button><button data-media-decision="rejected"[^>]*>거절<\/button><\/div><button class="media-action-edit" data-media-edit="v1">/,'#41 amount on approve, #44 one primary then secondary decisions then a text action');
markup=cards.card({...agentVideo,can_approve:false,can_execute:true,approval:'approved'});assert.match(markup,/data-media-decision="execute"[^>]*>승인한 작업 실행 · \$0\.35</);
// Mismatch and fixture labels stay visible; an expired quote says so first.
markup=cards.card({...agentVideo,mode:'contract-fake',estimate_kind:'fixture',estimate_expired:true,price:{...agentVideo.price,matches_quote:false,mismatch:'견적 총액과 단가×수량이 다릅니다. 둘 다 표시하며 어느 쪽도 자동 선택하지 않습니다.'}});
front=text(outsideDetails(markup));assert.ok(front.includes('견적 만료 · 재확인 필요 · 견적 총액 $0.35 · 시험 견적 · 실제 청구 아님'));assert.ok(front.includes('견적 총액과 단가×수량이 다릅니다.'));assert.ok(front.includes('모의 전송 · 실제 AI 호출 없음'));
// Job state: billing status joins the same cost line.
markup=cards.card({...agentVideo,job:{id:'j',state:'running',cost:{billing_confirmed:false},recovery:{}}});assert.ok(text(outsideDetails(markup)).includes('실청구 확인 중 · 추정과 다를 수 있음'));assert.doesNotMatch(markup,/data-media-decision/);
// Human preparation and a pre-D15 action.
markup=cards.card({...agentVideo,actor:'local-owner',model_reason:null,model_reason_label:'프로젝트에서 사용자가 선택한 모델',provenance:dict0(),differs_from_project:false});
front=text(outsideDetails(markup));assert.ok(front.includes('프로젝트 선택과 같음'));assert.ok(front.includes('프로젝트에서 사용자가 선택한 모델'));assert.ok(text(insideDetails(markup)).includes('사람이 직접 준비 · 대화 출처 없음'));assert.ok(!front.includes('검증 안 됨'));
function dict0(){return {engine:null,chat_model:null,permission_mode:null,effort:null,run:null,call:null}}
const old={...agentVideo,record:'출처 기록 없음(변경 전 준비)',actor:null,model_reason:null,model_reason_label:null,provenance:null,project_selection:null,differs_from_project:null};
markup=cards.card(old);front=text(outsideDetails(markup));assert.ok(front.includes('출처 기록 없음(변경 전 준비)'));assert.ok(!front.includes('프로젝트 선택과'),'no comparison is invented for old actions');assert.ok(front.includes('단가 $0.07/초'));assert.ok(!text(insideDetails(markup)).includes('제안 출처'));
// Fixture shapes without D15 fields (older tests) still render with explicit unknowns.
markup=cards.card({id:'a',shot:'s',role:'image',model:'m',prompt:'p',estimate:{amount:'0.01',currency:'USD'},mode:'contract-fake',can_approve:true,can_decide:true});assert.ok(text(markup).includes('단가 기록 없음'));assert.ok(text(markup).includes('출처 기록 없음(변경 전 준비)'));
// Reopen: the same projection after a JSON round trip renders identical markup.
assert.equal(cards.card(clone(agentVideo)),cards.card(agentVideo));
assert.equal(cards.factsLine(agentVideo),'모델 fal-ai/kling-video/v2.6/pro/image-to-video · 프로젝트 선택과 다름 (프로젝트: fal-kling-2-5-turbo) · 견적 $0.35 (문서 기준 추정) · 모델이 제시한 이유(검증 안 됨): 움직임 품질이 더 높습니다.');

// #49 and #44 source contracts.
assert.match(html,/<button id="prepareMedia" aria-describedby="mediaPreparationHint" data-runtime-blocked disabled>/,'#49 disabled reason is programmatically linked');
const primary=slice(css,'.lt-ui .lt-execution-card [data-action="action_execute"],','{ background:var(--ui-strong); color:var(--ui-chrome); }');
for(const selector of ['.media-action-card [data-media-decision="approved"]','.media-action-card [data-media-decision="execute"]','.general-chat-card [data-general-decision="approve"]'])assert.ok(primary.includes(selector),'#44 primary emphasis: '+selector);
assert.match(line(css,'.lt-ui .media-action-card .media-action-edit {'),/background:transparent; border-color:transparent; text-decoration:underline;/);

// Chat turn rendering (real refresh body).
const turn={id:'turn',conversation_id:'current',run_id:'run',status:'completed',prompt:'요청'};
const base={active_conversation:{id:'current'},general_chat_turns:[turn],shots:{target:{},other:{}},media_actions:[],motion_proposals:[],scenes_3d:[],
 production_runs:[{id:'run',conversation_id:'current',calls:[]}]};
function buttonsFrom(markup){return [...markup.matchAll(/<button type="button" ([^>]*)>([^<]*)<\/button>/g)].map(([,attrs,label])=>{const dataset={};for(const [,name,value] of attrs.matchAll(/data-general-([a-z-]+)="([^"]*)"/g))dataset['general'+name.split('-').map(w=>w[0].toUpperCase()+w.slice(1)).join('')]=decode(value);return{dataset,text:decode(label),focus(){}}})}
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:false,required:false,textContent:'',innerHTML:'',querySelectorAll:()=>[],querySelector:()=>null});return nodes.get(id)};
nodes.set('generalChatTurns',{innerHTML:'',querySelectorAll(){return buttonsFrom(this.innerHTML)}});
const view={p:clone(base),scope:'scope-A',renderedReviews:'',renderedTurns:'',el:node,layout(){},allowed:()=>true,configured:()=>false,bounded:()=>false,label:()=> 'fixture',usageLabel:()=> 'unverified',historyLabel:()=>'',controls(){},draftRead:()=>'',document:{activeElement:null},states:{completed:'complete'},key:()=> 'scope-A'};
view.project=()=>view.p;vm.createContext(view);vm.runInContext(productEsc+';'+productFacts,view);
vm.runInContext(line(ui,' const money=')+'\n'+line(ui,' const toolLabels=')+'\n'+slice(ui,' function reviewTargets(',' function controls(')+';globalThis.targets=reviewTargets;',view);
vm.runInContext(slice(ui,' function refresh(){'," el('generalChatPrompt').addEventListener")+';globalThis.draw=refresh;',view);
const turnsHTML=()=>node('generalChatTurns').innerHTML;
function call(name,result){return {name,result:{status:'proposed',...result}}}

// S5 video target and D15 turn summary.
let p=clone(base);p.production_runs[0].calls=[call('prepare_video_action',{role:'video',action_id:'v1'})];p.media_actions=[{...agentVideo,shot:'target'}];
assert.deepEqual(clone(view.targets(p,turn)),[{kind:'video',id:'v1',shot:'target',approval:'required',job:false}]);
for(const mutate of [q=>q.production_runs[0].calls[0].result.role='image',q=>q.media_actions[0].role='image',q=>q.production_runs[0].calls[0].name='prepare_image_action',q=>q.media_actions.push(clone(q.media_actions[0]))]){const m=clone(p);mutate(m);assert.deepEqual(clone(view.targets(m,turn)),[]);}
view.p=p;view.draw();
assert.deepEqual(buttonsFrom(turnsHTML()).map(b=>b.text),['요청 1 · target 영상 제작안 검토']);
assert.match(turnsHTML(),/<ul class="lt-cost-facts general-chat-facts"><li>target 영상 · 모델 fal-ai\/kling-video\/v2\.6\/pro\/image-to-video · 프로젝트 선택과 다름 \(프로젝트: fal-kling-2-5-turbo\) · 견적 \$0\.35 \(문서 기준 추정\) · 모델이 제시한 이유\(검증 안 됨\): 움직임 품질이 더 높습니다\.<\/li><\/ul>/);
assert.ok(text(insideDetails(turnsHTML())).includes('대화 모델 claude-haiku-5-5 · 권한 검토 후 편집 · 추론 강도 보통'),'turn summary keeps provenance in the disclosure');
// A price change re-renders the same turn.
view.p=clone(p);view.p.media_actions[0].estimate={amount:'0.7',currency:'USD'};view.draw();assert.match(turnsHTML(),/견적 \$0\.7 /);

// S8 motion and 3D targets.
p=clone(base);p.production_runs[0].calls=[call('propose_motion_scene',{proposal_id:'m1'}),call('propose_scene_3d',{scene_id:'s1',proposal_id:'p1'}),call('propose_scene_3d',{scene_id:'s1',proposal_id:'p2'})];
p.motion_proposals=[{id:'m1',shot:'target',status:'applied'}];p.scenes_3d=[{id:'s1',shot:'other',proposals:[{id:'p1',status:'proposed'},{id:'p2',status:'rejected'}]}];
assert.deepEqual(clone(view.targets(p,turn)),[{kind:'motion',id:'m1',shot:'target',approval:'applied',job:false},{kind:'scene',id:'p1',shot:'other',approval:'proposed',job:false},{kind:'scene',id:'p2',shot:'other',approval:'rejected',job:false}]);
view.p=p;view.draw();assert.deepEqual(buttonsFrom(turnsHTML()).map(b=>b.text),['요청 1 · target 모션 변경안 보기 (적용됨)','요청 1 · other 3D 변경안 1/2 검토','요청 1 · other 3D 변경안 2/2 보기 (거절됨)']);
assert.doesNotMatch(turnsHTML(),/general-chat-facts/,'no media facts for 3D or motion targets');
for(const mutate of [q=>q.motion_proposals.push(clone(q.motion_proposals[0])),q=>delete q.shots.target,q=>q.scenes_3d.push(clone(q.scenes_3d[0])),q=>q.scenes_3d[0].shot=null,q=>q.production_runs[0].conversation_id='foreign',q=>q.production_runs[0].calls.forEach(c=>c.result.status='blocked')]){
 const m=clone(p);mutate(m);const kinds=clone(view.targets(m,turn)).map(t=>t.kind);assert.ok(kinds.length<3,'mutation drops a target: '+kinds);}

// I1: identical prompts in two turns keep distinct names.
p=clone(base);p.general_chat_turns=[{...turn,prompt:'다시'},{...turn,id:'turn2',run_id:'run2',prompt:'다시'}];
p.production_runs=[{id:'run',conversation_id:'current',calls:[call('propose_motion_scene',{proposal_id:'m1'})]},{id:'run2',conversation_id:'current',calls:[call('propose_motion_scene',{proposal_id:'m2'})]}];
p.motion_proposals=[{id:'m1',shot:'target',status:'proposed'},{id:'m2',shot:'target',status:'proposed'}];view.p=p;view.draw();
assert.deepEqual(buttonsFrom(turnsHTML()).map(b=>b.text),['요청 1 · target 모션 변경안 검토','요청 2 · target 모션 변경안 검토']);

// #41 chat send review card: amount on approve, cost facts line, policy sentence in the disclosure.
view.p=clone(base);view.p.general_chat_previews=[{id:'pv',mode:'contract-fake',binding:{model:'claude-haiku-5-5'},data_scope:'scope',maximum_micro:10000,reserve_micro:3687,total_maximum_micro:40000,tool_scope:['prepare_video_action'],message_body:{},count_body:{}}];view.draw();
const review=node('generalChatReviews').innerHTML;
assert.match(review,/data-general-decision="approve"[^>]*>확인한 내용 승인 · 최대 \$0\.003687<\/button>/);
assert.match(review,/<p class="lt-cost-facts">최대 예약 \$0\.003687 · 한 회차 상한 \$0\.01 · 이번 요청 총 상한 \$0\.04 · 청구 금액 아님<\/p>/);
assert.match(review,/<details class="lt-provenance-detail"><summary>비용 상한 적용 방식<\/summary><p>총 상한은/);

// Navigation: video media actions use the image route (S5).
const navBase=(extra)=>{const events=[],d={activeElement:null};const c={Promise,navigationSequence:0,currentScope:'scope-A',dirty:false,shotName:'other',activeDialog:null,dialogStack:[],document:d,syncDialogs(){},setStep(step){events.push('step:'+step)},choose(name){c.navigationSequence++;events.push('tab:'+name)},focusWorkTarget(target){d.activeElement=target;events.push('focus:'+(target.id||target.dataset.actionCard))},conversationDraftKey:()=>c.currentScope,...extra};c.events=events;return c};
const shotButton=c=>({dataset:{shot:'target'},disabled:false,click(){c.shotName='target';c.events.push('shot:target'+('reviewNavigation' in this.dataset?':quiet':''))}});
(async()=>{
 {const c=navBase({});const p=clone(base);p.media_actions=[{id:'v1',role:'video',shot:'target'}];c.project=()=>p;const card={dataset:{actionCard:'v1'},getClientRects:()=>[{}],addEventListener(){}},shot=shotButton(c);
  c.document.querySelectorAll=selector=>selector==='[data-action-card]'?[card]:selector==='#shotlist [data-shot]'?[shot]:[];vm.createContext(c);vm.runInContext(slice(sidebar,' async function reviewMediaAction(',' async function reviewStudioProposal(')+';globalThis.go=reviewMediaAction;',c);
  assert.equal(await c.go('v1','scope-A',()=>true),'opened');assert.equal(c.document.activeElement,card);
  p.media_actions[0].role='audio';assert.equal(await c.go('v1','scope-A',()=>true),'missing');}

 // Navigation to 3D / motion proposals (S8) with the real reviewStudioProposal.
 function studioFixture(kind,{reveal='opened',launcherDisabled=false,dirty=false}={}){
  const c=navBase({dirty});const p=clone(base);p.motion_proposals=[{id:'m1',shot:'target',status:'proposed'}];p.scenes_3d=[{id:'s1',shot:'target',proposals:[{id:'p1',status:'proposed'}]}];c.project=()=>p;c.p=p;
  const shot=shotButton(c),targets={};for(const id of ['#motionProposal','#sceneStudioSummary','#motionStatus','#sceneStudioStatus'])targets[id]={id,dataset:{},addEventListener(name,callback){assert.equal(name,'blur');targets[id].blur=callback}};
  const launcher={disabled:launcherDisabled,click(){c.events.push('launch:'+kind)}};
  c.q=selector=>selector==='#sceneStudioButton'||selector==='#motionButton'?(selector===(kind==='scene'?'#sceneStudioButton':'#motionButton')?launcher:null):targets[selector]||null;
  c.document.querySelectorAll=selector=>selector==='#shotlist [data-shot]'?[shot]:[];
  c.window={AethonScene:{reveal:id=>{c.events.push('reveal:'+id);return reveal}},AethonMotion:{reveal:id=>{c.events.push('reveal:'+id);return reveal}}};
  vm.createContext(c);vm.runInContext(slice(sidebar,' async function reviewStudioProposal(',' workRows.addEventListener')+';globalThis.go=reviewStudioProposal;',c);c.targets=targets;return c;
 }
 let c=studioFixture('motion');assert.equal(await c.go('motion','m1','scope-A',()=>true),'opened');
 assert.deepEqual(c.events,['step:3','shot:target:quiet','tab:settings','launch:motion','reveal:m1','focus:#motionProposal'],'scene switch is quiet, the studio opens and only the proposal control takes focus');
 assert.equal(c.targets['#motionProposal'].dataset.reviewArrival,'','arrival mark');c.targets['#motionProposal'].blur();assert.equal('reviewArrival' in c.targets['#motionProposal'].dataset,false);
 c=studioFixture('scene');assert.equal(await c.go('scene','p1','scope-A',()=>true),'opened');assert.equal(c.document.activeElement.id,'#sceneStudioSummary');
 c=studioFixture('scene',{reveal:'kept'});assert.equal(await c.go('scene','p1','scope-A',()=>true),'kept');assert.equal(c.document.activeElement.id,'#sceneStudioStatus','kept input: focus goes to the studio status that explains it');
 c=studioFixture('motion',{dirty:true});assert.equal(await c.go('motion','m1','scope-A',()=>true),'dirty');assert.deepEqual(c.events,[],'unsaved timeline edit on another scene blocks before any change');
 c=studioFixture('motion',{dirty:true});c.shotName='target';assert.equal(await c.go('motion','m1','scope-A',()=>true),'opened','dirty edit on the same scene does not block opening');
 c=studioFixture('motion',{launcherDisabled:true});assert.equal(await c.go('motion','m1','scope-A',()=>true),'blocked');assert.equal(c.document.activeElement,null);
 c=studioFixture('motion');assert.equal(await c.go('motion','missing','scope-A',()=>true),'missing');assert.deepEqual(c.events,[]);
 c=studioFixture('motion');assert.equal(await c.go('motion','m1','scope-A',()=>false),'missing','stale chat reference');
 c=studioFixture('motion');c.setStep=()=>{c.currentScope='scope-B'};assert.equal(await c.go('motion','m1','scope-A',()=>true),'superseded');assert.equal(c.document.activeElement,null);
 c=studioFixture('scene',{reveal:'missing'});assert.equal(await c.go('scene','p1','scope-A',()=>true),'missing');
 c=studioFixture('motion');c.focusWorkTarget=()=>{};assert.equal(await c.go('motion','m1','scope-A',()=>true),'blocked','target that cannot take focus is reported');assert.equal('reviewArrival' in c.targets['#motionProposal'].dataset,false);
 c=studioFixture('motion');c.p.motion_proposals[0].shot='nowhere';assert.equal(await c.go('motion','m1','scope-A',()=>true),'missing');

 // Real studio reveal(): unsaved dialog input is kept, otherwise the proposal is selected.
 {const m={structuredClone,dialog:{open:true},shotName:'target',scope:'k',key:()=> 'k',dirty:true,source:'mine',editing:{draft:true},layerIndex:2,version:1,previewGeneration:0,statusText:'',fields(){m.fielded=true},refresh(){}};
  m.el=()=>({hidden:false});m.status=value=>{m.statusText=value};m.project=()=>({motion_proposals:[{id:'m1',shot:'target',scene:{layers:[]}}]});vm.createContext(m);
  vm.runInContext(slice(motion,' function reveal(id){',' window.AethonMotion=')+';globalThis.reveal=reveal;',m);
  assert.equal(m.reveal('m1'),'kept');assert.deepEqual(m.editing,{draft:true});assert.equal(m.source,'mine');assert.match(m.statusText,/저장하지 않은 모션 수정을 유지/);
  m.dirty=false;assert.equal(m.reveal('m1'),'opened');assert.equal(m.source,'m1');assert.deepEqual(clone(m.editing),{layers:[]});assert.equal(m.fielded,true);
  assert.equal(m.reveal('other'),'missing');m.dialog.open=false;assert.equal(m.reveal('m1'),'missing');}
 {const s={dialog:{open:true},dirty:true,source:'draft-source',statusText:''};s.status=value=>{s.statusText=value};
  s.record=()=>({head:2,proposals:[{id:'p1',status:'proposed',base_revision:2},{id:'p0',status:'rejected',base_revision:1}]});s.replaceable=r=>r.proposals[0];
  vm.createContext(s);vm.runInContext(slice(scene,' function reveal(id){',' window.AethonScene=')+';globalThis.reveal=reveal;',s);
  assert.equal(s.reveal('p1'),'kept','dirty 3D input is preserved');assert.equal(s.source,'draft-source');assert.match(s.statusText,/저장하지 않은 3D 입력을 유지/);
  s.dirty=false;assert.equal(s.reveal('p1'),'opened');assert.match(s.statusText,/대화에서 연 변경안입니다/);
  assert.equal(s.reveal('p0'),'opened');assert.match(s.statusText,/현재 검토 대상이 아닙니다\(상태: 거절\)/);assert.equal(s.reveal('none'),'missing');}
 // Scene Studio shows the agent origin of a pending proposal.
 assert.match(scene,/모델 제안 · \$\{o\.model_reason_label\|\|'모델이 제시한 이유\(검증 안 됨\)'\}/);

 // Chat click handler dispatches by kind; 'kept' keeps focus in the studio and explains.
 {const status={textContent:''},d={activeElement:null},calls=[];const h={busy:false,inFlight:false,scope:'scope-A',currentScope:'scope-A',document:d,request:async()=>true,song:()=> 'A'};
  h.p=clone(base);h.p.production_runs[0].calls=[call('propose_scene_3d',{scene_id:'s1',proposal_id:'p1'})];h.p.scenes_3d=[{id:'s1',shot:'target',proposals:[{id:'p1',status:'proposed'}]}];
  h.project=()=>h.p;h.key=()=>h.currentScope;const turnsNode={querySelectorAll:()=>buttonsFrom('<button type="button" data-general-review-action="p1" data-general-review-turn="turn" data-general-review-scope="scope-A">x</button>').map(b=>(b.focus=function(){d.activeElement=this},b))};
  h.el=id=>id==='generalChatStatus'?status:id==='generalChatTurns'?turnsNode:{};
  h.window={LoretuneAgentSidebar:{reviewMediaAction:async()=>{calls.push('media');return 'opened'},reviewStudioProposal:async(kind,id)=>{calls.push(kind+':'+id);return h.answer}}};
  vm.createContext(h);vm.runInContext(slice(ui,' function reviewTargets(',' function controls(')+'\n'+line(ui," el('generalChatTurns').onclick="),h);
  const button={dataset:{generalReviewAction:'p1',generalReviewTurn:'turn',generalReviewScope:'scope-A'}},click=()=>turnsNode.onclick({target:{closest:selector=>selector==='[data-general-review-action]'?button:null}});
  const messages={};{const m={};vm.createContext(m);vm.runInContext(line(ui,' const reviewMessages=')+';globalThis.out=reviewMessages;',m);Object.assign(messages,m.out)}
  h.answer='kept';await click();assert.deepEqual(calls,['scene:p1']);assert.equal(status.textContent,messages.kept);assert.equal(d.activeElement,null,'kept: focus stays in the studio');
  h.answer='blocked';await click();assert.equal(status.textContent,messages.blocked);assert.equal(d.activeElement?.dataset.generalReviewAction,'p1');
  h.answer='opened';await click();assert.equal(status.textContent,'');}

 // Work status rows carry the card's D15 facts (provider group only).
 {const make=(tag,className,textValue)=>({tag,className,textContent:textValue||'',dataset:{},children:[],append(...nodes){this.children.push(...nodes)},setAttribute(){}});
  const rows={children:[],contains:()=>false,replaceChildren(){this.children=[]},append(n){this.children.push(n)},querySelector:()=>null};
  const w={make,workRows:rows,workStatus:{},workEmpty:{},workDetails:{},workSummaryText:{},workStatusSignature:'',shotName:'target',document:{activeElement:null},song:()=> 'A',conversationDraftKey:()=> 'k'};
  w.p=clone(base);w.p.media_actions=[{...agentVideo,shot:'target',job:{id:'j',state:'running'}}];w.state={generation_jobs:[{id:'j',context:{song:'A',shot:'target'},state:'running'}],jobs:[]};w.project=()=>w.p;
  vm.createContext(w);vm.runInContext(productEsc+';'+productFacts,w);vm.runInContext(slice(sidebar,' function workGroups(',' function focusWorkTarget(')+';globalThis.render=renderWorkStatus;',w);w.render();
  const row=rows.children.find(r=>r.children.some(n=>n.dataset.agentWork==='provider'));assert.ok(row,'provider row');
  assert.deepEqual(row.children.filter(n=>n.className==='lt-cost-facts').map(n=>n.textContent),['target 영상 · '+cards.factsLine(agentVideo)]);}

 // Agent settings summary (D21) from the projection fields built by A2a.
 {const make=(tag,className,textValue)=>({tag,className,textContent:textValue||'',value:'',children:[],append(...n){this.children.push(...n)},replaceChildren(){this.children=[]}});
  const el=()=>make('x');const a={make,preferences:{},modeSelect:el(),effortSelect:el(),preferenceStatus:el(),preferenceSummary:el(),preferenceActive:el(),preferenceRoute:el(),preferenceSave:{},preferenceCost:el(),preferencePrice:el(),preferenceSource:{hidden:true},preferenceScope:'',preferenceChoices:'',busy:false,dirty:false,pendingId:()=>null,conversationDraftKey:k=>k};
  vm.createContext(a);vm.runInContext(productEsc+';'+productFacts,a);vm.runInContext(slice(sidebar,' const modeNames = ',' modeSelect.addEventListener(')+';globalThis.render=renderPreferences;',a);
  const capability={model:'claude-haiku-5-5',effort_options:['low','medium','high'],unsupported_efforts:[],general_route_supported:true,general_route_configured:true,
   token_price:{input_rate:'.1',output_rate:'.5',unit:'USD per 1M tokens',long_context:{threshold_input_tokens:100000,input_rate:'.5',output_rate:'2.5'},source:'https://platform.claude.com/docs/en/about-claude/pricing',revision:'haiku-5-5-20261027-tiered'},
   reservation:{max_input_tokens:16384,max_output_tokens:4096,worst_per_round_micro:3687,conversation_cap_micro:400000,worst_case_rounds_within_cap:108}};
  a.render({agent_preferences:{current:{selection:'anthropic-haiku-5-5',mode:'review',effort:'medium',revision:1},capabilities:{modes:[{id:'review'}],models:{'anthropic-haiku-5-5':capability}}}});
  assert.equal(a.preferenceCost.textContent,'대화 모델 claude-haiku-5-5 · 사용자가 선택한 모델 · 입력 $0.1 / 출력 $0.5 (100만 토큰당 · 문서 기준 · 청구 아님) · 회차당 최대 예약 $0.003687 · 대화 상한 $0.4 안 최대 108회차');
  assert.equal(a.preferencePrice.textContent,'단가 개정 haiku-5-5-20261027-tiered · 입력 100000토큰 초과 시 입력 $0.5 / 출력 $2.5 · 회차 상한 입력 16384 / 출력 4096토큰 · 권한 검토 후 편집 · 추론 강도 보통 · 에이전트는 모델·권한·추론 강도를 바꿀 수 없습니다.');
  assert.equal(a.preferenceSource.hidden,false);assert.equal(a.preferenceSource.href,capability.token_price.source);
  a.preferenceScope='';a.render({agent_preferences:{current:{selection:'x',mode:'review',effort:'low',revision:2},capabilities:{modes:[{id:'review'}],models:{x:{...capability,token_price:null,reservation:null}}}}});
  assert.equal(a.preferenceCost.textContent,'대화 모델 claude-haiku-5-5 · 사용자가 선택한 모델 · 단가 기록 없음 · 예약 기준 기록 없음');assert.equal(a.preferenceSource.hidden,true);
  assert.match(sidebar,/preferenceDetail\.append\(make\('summary', '', '대화 모델 가격 출처·권한 범위'\), preferencePrice, preferenceSource, preferencePolicy\);/,'#46 policy note moved into the disclosure');}

 // Real server projections (optional input from the Python wrapper).
 if(process.argv[2]){
  const real=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
  const agent=real.agent_project.media_actions[0],reopened=real.agent_reopened.media_actions[0];
  markup=cards.card(agent);front=text(outsideDetails(markup));
  for(const fact of ['프로젝트 선택과 다름 (프로젝트: fal-flux-schnell)','견적 총액 $0.04 · 시험 견적 · 실제 청구 아님','단가 $0.04/MP · 문서 기준 추정','모델이 제시한 이유(검증 안 됨): '+real.reason])assert.ok(front.includes(fact),'real agent card: '+fact);
  assert.ok(text(insideDetails(markup)).includes('대화 모델 claude-haiku-5-5 · 권한 전체 편집 · 추론 강도 높음'),'real provenance');
  assert.ok(text(insideDetails(markup)).includes('개정 fal-public-model-pages-20261028'));
  assert.equal(cards.card(reopened),markup,'reopen renders the same card from the stored projection');
  view.p=real.agent_project;view.renderedTurns='';view.draw();
  assert.ok(text(turnsHTML()).includes('장면 1 이미지 · '+cards.factsLine(agent)),'real chat turn summary');
  assert.ok(buttonsFrom(turnsHTML()).some(b=>b.text==='요청 1 · 장면 1 이미지 제작안 검토'),'real review button');
  front=text(outsideDetails(cards.card(real.owner_card)));assert.ok(front.includes('프로젝트에서 사용자가 선택한 모델'));assert.ok(front.includes('프로젝트 선택과 같음'));
  front=text(outsideDetails(cards.card(real.old_card)));assert.ok(front.includes('출처 기록 없음(변경 전 준비)'));assert.ok(front.includes('단가 $0.003/MP · 문서 기준 추정'));
  markup=cards.card(real.video_card);front=text(outsideDetails(markup));
  for(const fact of ['장면 1 · 영상','견적 총액 $0.35','단가 $0.07/초 · 문서 기준 추정','5초 · 무음','프로젝트 선택과 다름 (프로젝트: fal-kling-2-5-turbo)','모델이 제시한 이유(검증 안 됨): '+real.video_reason])assert.ok(text(markup).includes(fact)||front.includes(fact),'real video card: '+fact);
  assert.ok(text(insideDetails(markup)).includes('권한 검토 후 편집'));
  console.log('real projections rendered: agent image, reopened, chat turn, owner, old, video');
 }
 completed=true;console.log('B2 D15 surfaces, review navigation kinds, design #41 #44 #45 #46 #49 and I1 names passed');
})().catch(error=>{console.error(error);process.exitCode=1});
