'use strict';
// UI-r2 contracts: E1 375 header select, #23 visibility poll, #3 playhead writes, #7 verb-only labels,
// #8 toggle state, #41 one money format, #46 notice pattern at the named locations, approval and
// transmission facts outside disclosures, S16 work-status/turn price facts, provider count parity,
// tokenized spacing. Product code is sliced from the shipped files; no browser, server or model call.
// UI-r3: exact position on pause/end/redraw, throttled comparison writes, verb labels without parenthetical
// disclaimers, cost-facts only for cost/transmission (warning token at spend decisions), widened notice and money checks.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const read=f=>fs.readFileSync(f,'utf8');
const html=read('index.html'),css=read('studio.css'),sidebar=read('chat-sidebar.js'),ui=read('general-chat-ui.js'),media=read('studio-media.js'),scene=read('scene-studio.js'),motion=read('motion-studio.js');
const slice=(source,a,b)=>{const start=source.indexOf(a),end=source.indexOf(b,start);assert.ok(start>=0&&end>start,'marker missing: '+a);return source.slice(start,end)};
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const text=markup=>decode(markup.replace(/<[^>]+>/g,' ')).replace(/\s+/g,' ');
const outsideDetails=markup=>markup.replace(/<details[\s\S]*?<\/details>/g,'');
const productEsc='var '+slice(html,'esc=s=>',';let stateReadEpoch');
const productFacts=slice(html,'function mediaActionMarkup(x){','function drawMediaCreator(){');
const done=[];

// ---- E1 serious: the 375px header select keeps a readable basis (cascade reasoning over studio.css).
{
 const source=css.replace(/\/\*[\s\S]*?\*\//g,'');
 const viewport={width:375,height:812};
 const mediaOk=cond=>cond.split(/\band\b/).every(part=>{const m=part.match(/\(\s*(min|max)-(width|height)\s*:\s*(\d+)px\s*\)/);if(!m)return /^\s*(screen|all)?\s*$/.test(part);const v=viewport[m[2]],n=Number(m[3]);return m[1]==='min'?v>=n:v<=n});
 const rules=[];let order=0;
 (function walk(block,active){let i=0;while(i<block.length){const open=block.indexOf('{',i);if(open<0)break;const head=block.slice(i,open).trim();let depth=1,j=open+1;while(depth&&j<block.length){if(block[j]==='{')depth++;else if(block[j]==='}')depth--;j++}const body=block.slice(open+1,j-1);
  if(head.startsWith('@media'))walk(body,active&&mediaOk(head.slice(6).trim()));else if(!head.startsWith('@'))rules.push({selectors:head,body,active,order:order++});i=j}})(source,true);
 const split=list=>{const out=[];let depth=0,start=0;for(let k=0;k<list.length;k++){const c=list[k];if(c==='(')depth++;else if(c===')')depth--;else if(c===','&&!depth){out.push(list.slice(start,k));start=k+1}}out.push(list.slice(start));return out.map(s=>s.trim())};
 const specificity=sel=>{const s=sel.replace(/:where\([^)]*\)/g,'');return [(s.match(/#[\w-]+/g)||[]).length,(s.match(/\.[\w-]+|\[[^\]]+\]|:(?!:)[\w-]+/g)||[]).length,(s.replace(/[#.:][\w-]+|\[[^\]]+\]/g,' ').match(/(^|[\s>+~])[a-z][\w-]*/gi)||[]).length]};
 const cmp=(a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2];
 function winner(lastCompound,prop){let best=null;for(const r of rules){if(!r.active)continue;for(const sel of split(r.selectors)){const last=sel.split(/[\s>+~]+/).pop();if(!lastCompound.test(last))continue;for(const decl of r.body.split(';')){const k=decl.indexOf(':');if(k<0||decl.slice(0,k).trim()!==prop)continue;const value=decl.slice(k+1).trim(),important=/!important$/.test(value),cand={value:value.replace(/\s*!important$/,''),important,spec:specificity(sel),order:r.order,sel};
   if(!best||important>best.important||important===best.important&&(cmp(cand.spec,best.spec)>0||cmp(cand.spec,best.spec)===0&&cand.order>best.order))best=cand}}}return best}
 const flex=winner(/^#songs$/,'flex'),minWidth=winner(/^#songs$/,'min-width'),width=winner(/^#songs$/,'width'),wrap=winner(/^\.lt-studio-shell$/,'flex-wrap');
 assert.equal(flex.value,'1 1 12rem','winning flex for #songs at 375x812 keeps a 12rem basis ('+flex.sel+')');
 assert.equal(minWidth.value,'0');assert.equal(width.value,'auto','the 240px desktop width is overridden at <=900px');
 assert.equal(wrap.value,'wrap','the shell wraps, so the select is never shrunk below its basis on a shared line');
 assert.equal(winner(/^#songs$/,'max-width').value,'none');
 done.push('E1 375 #songs cascade: flex '+flex.value+' from "'+flex.sel+'", shell flex-wrap '+wrap.value);
}

// ---- #23: a standalone listener polls once when the tab becomes visible; hidden tabs skip.
{
 const code=slice(html,'const pollState=async()=>{',"refresh().then(()=>{document.body.dataset.step='1'");
 assert.ok(slice(html,'const pollState=async()=>{','};setInterval(pollState,1500);').includes('globalThis.document?.hidden'),'interval body still skips hidden tabs');
 const listeners={};let fetches=0,interval=null;
 const c={busy:false,state:{workspace_id:'w',revision:1,projects:{}},pollReadsInFlight:0,stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,shotName:'s',song:()=> 'A',
  fetch:()=>{fetches++;return new Promise(()=>{})},setInterval:(fn,ms)=>{interval=[fn,ms]},document:{hidden:true,addEventListener:(type,fn)=>{listeners[type]=fn}}};
 vm.createContext(c);vm.runInContext(code,c);
 assert.equal(interval[1],1500);assert.equal(typeof listeners.visibilitychange,'function','visibilitychange listener registered');
 listeners.visibilitychange();assert.equal(fetches,0,'still hidden: no poll');
 c.document.hidden=false;listeners.visibilitychange();assert.equal(fetches,1,'visible again: one immediate poll');
 assert.equal(interval[0],vm.runInContext('pollState',c),'interval and listener share the same poll');
 done.push('#23 visibilitychange: hidden 0 polls, visible 1 poll');
}

// ---- #3: during playback the time text and seek value change at most ~10 times a second.
{
 const nodes={'#timePlayhead':{style:{}},'#sequenceSeek':{v:'0',writes:0,get value(){return this.v},set value(x){this.v=String(x);this.writes++}},'#sequenceTime':{t:'',writes:0,get textContent(){return this.t},set textContent(x){this.t=x;this.writes++}}};
 const c={q:s=>nodes[s]};vm.createContext(c);
 vm.runInContext('const safe=n=>Number.isFinite(Number(n))?Math.max(0,Number(n)):0;'+slice(media,' function timecode(',' const api=')+slice(media,' function updatePlayhead(',' function createSequence(')+';globalThis.update=updatePlayhead;',c);
 for(let frame=0;frame<=60;frame++)c.update(1+frame/60,30,true);
 const playingText=nodes['#sequenceTime'].writes,playingSeek=nodes['#sequenceSeek'].writes;
 assert.ok(playingText<=11,'61 frames over 1 s write the time text '+playingText+' times');assert.ok(playingSeek<=11,'seek value writes '+playingSeek);
 c.update(2.04,30,true);assert.equal(nodes['#sequenceTime'].writes,playingText,'unchanged frame writes nothing');assert.equal(nodes['#sequenceSeek'].writes,playingSeek);
 c.update(3.929,30,false);assert.equal(nodes['#sequenceTime'].textContent,'00:03.929 / 00:30.000','paused seeks stay exact to the millisecond');assert.equal(nodes['#sequenceSeek'].value,'3.929');
 assert.match(media,/updatePlayhead\(at,total,playing\)/,'the sequence seek passes its playing state');
 done.push('#3 playhead: 61 playing frames -> text '+playingText+' writes, seek '+playingSeek+' writes');
}
// ---- UI-r3 #3: pause and the end of playback show the exact position; a redraw restores the live position.
const {fixture:mediaFixture}=require('./media_async_harness.cjs');
const mediaHarness=()=>{const f=mediaFixture();f.Element.prototype.classList={add(){}};f.d.clips[1].duration=3.033;return f};
const videos=f=>f.media.filter(m=>m.tagName==='video');
{
 const f=mediaHarness(),seq=f.api._audit.createSequence(f.p,f.d,0),time=()=>f.q('#sequenceTime').textContent,seek=()=>String(f.q('#sequenceSeek').value);
 seq.play();seq.seek(4.567);assert.equal(time(),'00:04.500 / 00:06.033','playing: 0.1 s steps');assert.equal(seek(),'4.5');
 seq.pause();assert.equal(time(),'00:04.567 / 00:06.033','pause shows the exact position');assert.equal(seek(),'4.567');
 const writes=f.q('#sequenceTime');let count=0;const old=writes.textContent;Object.defineProperty(writes,'textContent',{get(){return this._t},set(v){this._t=v;count++},configurable:true});writes._t=old;
 seq.pause();assert.equal(count,0,'pausing an already paused sequence writes nothing');
 done.push('#3 pause: playing 00:04.500 -> paused '+time());
}
{
 const f=mediaHarness(),seq=f.api._audit.createSequence(f.p,f.d,0),time=()=>f.q('#sequenceTime').textContent;
 seq.play();videos(f).at(-1).onloadeddata();
 seq.seek(5.5);const second=videos(f).at(-1);second.onloadeddata();
 second.currentTime=1+3.033+.05;f.frame(16);
 assert.ok(Math.abs(seq.time-6.033)<1e-9,'tick clamps to the end: '+seq.time);assert.equal(time(),'00:06.033 / 00:06.033','end of playback shows the exact total, not 00:06.000');assert.ok(Math.abs(Number(f.q('#sequenceSeek').value)-6.033)<1e-9,'seek value is the exact total, not 6.0');
 assert.equal(f.q('#sequencePlay').textContent,'편집 재생','playback stopped');
 done.push('#3 end of playback: '+time());
}
{
 const f=mediaHarness();f.api.timeline();const seq=f.api._audit.createSequence(f.p,f.d,0);
 seq.play();seq.seek(4.567);assert.equal(String(f.q('#sequenceSeek').value),'4.5');
 f.api.timeline();
 assert.equal(f.q('#sequenceTime').textContent,'00:04.567 / 00:06.033','redraw restores the live position, not the 0.1 s display value');assert.equal(String(f.q('#sequenceSeek').value),'4.567');
 assert.match(media,/const prior=sequence\?\.time;sequence\?\.dispose\(\)/,'timeline reads the live position before disposing');
 done.push('#3 redraw restore: 4.567 -> '+String(f.q('#sequenceSeek').value));
}

// ---- #7: no remaining ' · ' disclaimer on button labels; disclaimers are linked help text.
{
 const offenders=[];
 for(const [file,source] of [['index.html',html],['scene-studio.js',scene],['motion-studio.js',motion],['chat-sidebar.js',sidebar],['general-chat-ui.js',ui],['studio-media.js',media]]){
  for(const m of source.matchAll(/<button\b[^>]*>([^<]{0,160}?)<\/button>/g))if(m[1].includes(' · ')&&!/승인 · (최대 )?\$\{/.test(m[1]))offenders.push(file+': '+m[1]);
  for(const m of source.matchAll(/(?:button|Button)\w*\.textContent\s*=\s*'([^']*)'/g))if(m[1].includes(' · '))offenders.push(file+': '+m[1]);}
 assert.deepEqual(offenders,[],'only amount-bearing approve labels (#41) keep a middle dot');
 for(const [source,button,help] of [[html,'aria-describedby="modelSettingsSaveHelp">기본 선택 저장<','id="modelSettingsSaveHelp" class="muted"'],[html,'id="prepareGeneration" aria-describedby="prepareGenerationHelp">10초 입력·견적 준비<','id="prepareGenerationHelp" class="muted"'],[motion,'aria-describedby="motionNormalizeHelp"','id="motionNormalizeHelp" class="muted"'],[scene,"button.setAttribute('aria-describedby',help.id)","help.id='sceneStudioButtonHelp';help.className='muted'"]]){assert.ok(source.includes(button),button);assert.ok(source.includes(help),help)}
 assert.ok(scene.includes("button.textContent='3D 장면 만들기';"));assert.ok(motion.includes('>문자 조합 정리</button>'));
 const paren=[];
 for(const [file,source] of [['index.html',html],['scene-studio.js',scene],['motion-studio.js',motion],['chat-sidebar.js',sidebar],['general-chat-ui.js',ui],['studio-media.js',media]])for(const m of source.matchAll(/<button\b[^>]*>([^<]{0,160}?)<\/button>/g))if(/\([^)]*(없음|아님|별도|안 함)[^)]*\)/.test(m[1]))paren.push(file+': '+m[1]);
 assert.deepEqual(paren,[],'UI-r3: no parenthetical disclaimer in button labels');
 done.push('#7 dot-joined and parenthetical disclaimer buttons: 0 left');
}

// ---- #8: the toggle label and aria-expanded agree in every state.
{
 const c={};vm.createContext(c);vm.runInContext(slice(sidebar,' function toggleState(',' function apply(')+';globalThis.state=toggleState;',c);
 assert.deepEqual({...c.state(true,'chat')},{expanded:'true',label:'AI 대화 닫기'});
 assert.deepEqual({...c.state(true,'settings')},{expanded:null,label:'AI 대화 보기'},'switching tabs is not a disclosure: no aria-expanded');
 assert.deepEqual({...c.state(false,'chat')},{expanded:'false',label:'AI 대화 열기'});assert.deepEqual({...c.state(false,'settings')},{expanded:'false',label:'AI 대화 열기'});
 assert.match(sidebar,/if \(toggleView\.expanded === null\) toggle\.removeAttribute\('aria-expanded'\); else toggle\.setAttribute\('aria-expanded', toggleView\.expanded\); toggle\.textContent = toggleView\.label;/);
 done.push('#8 toggle: chat open=닫기/expanded, settings open=보기/no aria-expanded, closed=열기/collapsed');
}

// ---- #41: Kling preparation card and budget summary use usd().
{
 const node=()=>({textContent:'',innerHTML:''}),nodes={};const c={drawImageConnection(){},drawMediaCreator(){},drawProviderBadge(){},creatorDiagnostic:()=>'',shotName:'s',song:()=> 'A',$:s=>nodes[s]||(nodes[s]=node()),
  state:{capabilities:{provider_generation:false},generation_jobs:[]}};
 c.project=()=>({shots:{s:{revision:1,generation_preparations:[{id:'g',estimate:{model:'kling',money:{amount:'0.70',currency:'USD'},expires:4102444800},prompt:'p',reference_version:1,shot_revision:1}]}}});
 vm.createContext(c);vm.runInContext(productEsc+';'+productFacts+';'+slice(html,'function drawGeneration(){','\n'),c);c.drawGeneration();
 assert.match(nodes['#generationPreparations'].innerHTML,/<p>예상 비용 \$0\.7 · /,'same "$0.7" as usd(), not "$0.70"');
 assert.deepEqual([...html.matchAll(/\$\$\{esc\(([^)]*)\)/g)].map(m=>m[1]),[],'no hand-built dollar amounts left in index.html');
 // UI-r3: also catch string concatenation ('$'+x, '... $'+x) in every write-set script; usd() itself is the one exception.
 const concat=[];for(const [file,source] of [['index.html',html],['chat-sidebar.js',sidebar],['general-chat-ui.js',ui],['studio-media.js',media],['scene-studio.js',scene],['motion-studio.js',motion]])for(const m of source.matchAll(/[^\n]{0,40}\$['"`]\s*\+[^\n]{0,30}/g))if(!m[0].includes("return '$'+(s.includes('.')"))concat.push(file+': '+m[0]);
 assert.deepEqual(concat,[],'no "$"+value concatenation outside usd()');
 assert.ok(html.includes("' · 요청당 한도 '+usd(cap.maximum_usd)"),'request cap line uses usd()');assert.ok(ui.includes("'사용량 기준 금액 '+usd(turn.usage_cost_usd)"));
 // UI-r3 #7-type: recheck/resume buttons carry verb labels and one linked muted help.
 c.state.generation_jobs=[{id:'j<1>',state:'reconciliation_required',context:{song:'A',shot:'s',output_kind:'video'},can_recheck:true,can_resume_result:true}];c.drawGeneration();
 const jobs=nodes['#generationPreparations'].innerHTML;
 assert.ok(jobs.includes('<button data-generation-recheck="j&lt;1&gt;" aria-describedby="generationNoNew-j&lt;1&gt;">기존 접수 상태 다시 조회</button>'),jobs);
 assert.ok(jobs.includes('<button data-generation-resume="j&lt;1&gt;" aria-describedby="generationNoNew-j&lt;1&gt;">기존 결과 검토용 연결 재시도</button>'));
 assert.equal((jobs.match(/<p class="muted" id="generationNoNew-j&lt;1&gt;">기존 요청만 확인하며 새로 생성하지 않습니다\.<\/p>/g)||[]).length,1,'one help line per job');assert.ok(!jobs.includes('새 생성 없음'));
 c.state.generation_jobs=[{id:'j2',state:'running',context:{song:'A',shot:'s',output_kind:'video'}}];c.drawGeneration();assert.ok(!nodes['#generationPreparations'].innerHTML.includes('generationNoNew-'),'no orphan help without the buttons');assert.ok(html.includes("${usd(t.usage_cost_usd||'0')}"),'legacy model-chat usage line also uses usd()');
 done.push('#41 Kling card renders '+nodes['#generationPreparations'].innerHTML.match(/예상 비용 [^ ]+/)[0]);
}

// ---- #46: the named locations use one facts line and move secondary notes into a disclosure.
{
 const staticHtml=html.split('<script>')[0];
 const count=(source,re)=>(source.match(re)||[]).length;
 // UI-r3: the notice check also catches '전송 없이', '전송은 없습니다', '전송하지 않습니다' and '호출하지 않습니다'.
 const NOTICE=/<p(?![^>]*\bclass="(?:lt-cost-facts[^"]*|muted)")(?: [^>]*)?>[^<]*(별도|별개|미계측|전송(?:은|이)? 없|전송하지 않|호출(?:은|이)? 없|호출하지 않)/g;
 // UI-r3: cost/transmission facts keep the facts line; non-cost scope notes are muted text; the ontology note is a disclosure
 // because the runtime replaces the dialog's first <p> with its intro (index.html, ontologyIntro) and the old screen showed only that.
 for(const [dialog,fact,kind] of [['modelSettingsPanel',null],['ontologyDialog','외부로 전송하지 않습니다. 설정을 승인해도 기존 영상과 출력은 바뀌지 않습니다.','disclosure'],['budgetDialog','이 설정은 외부 전송·유료 호출 승인이 아닙니다.','facts'],['operationsDialog','외부 공급자는 미연결이며 로컬 연산비는 미계측입니다.','facts'],['renderConfirm','외부 공급자 호출비 0','facts'],['settingDialog','새 승인 설정은 이후 작품에만 적용합니다.','muted'],['libraryDialog','원본과 사용권 근거만 연결하고 승인·선택 상태는 가져오지 않습니다.','muted'],['rightsDialog','같은 파일을 사용하는 모든 작품에 적용됩니다.','muted'],['archiveDialog','보관하면 제작 변경을 차단하고','muted'],['preferencesDialog','공식 설정·사용권을 바꾸지 않습니다.','muted']]){
  const body=slice(staticHtml,'<dialog id="'+dialog+'"','</dialog>');
  if(kind==='facts'){assert.ok(body.includes('<p class="lt-cost-facts">'),dialog+' has a facts line');assert.ok(text(outsideDetails(body)).includes(fact),dialog+' keeps its cost fact visible: '+fact)}
  if(kind==='muted'){assert.ok(!body.includes('lt-cost-facts'),dialog+': a non-cost scope note is not a cost-facts line');assert.ok(new RegExp('<p class="muted">[^<]*'+fact.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(body),dialog+' shows its scope note as muted text: '+fact)}
  if(kind==='disclosure'){assert.ok(!body.includes('lt-cost-facts'),dialog);assert.ok(!text(outsideDetails(body)).includes(fact),dialog+': note is not visible outside the disclosure');assert.ok(text(body).includes(fact),dialog+' keeps the note in a disclosure')}
  assert.equal(count(outsideDetails(body),NOTICE),0,dialog+': no plain notice paragraph repeats separate/unmeasured/no-transfer outside a disclosure');}
 assert.equal(count(outsideDetails(staticHtml),NOTICE),0,'whole static page: no plain notice paragraph (widened variants) outside disclosures');
 assert.ok(!staticHtml.includes('직접 계획은 외부 전송 없이 저장됩니다.'),'chat intro no longer repeats the 계획 미리보기 help');
 assert.ok(staticHtml.includes('<p class="lt-cost-facts">테스트 미디어는 단색 이미지입니다. 실제 AI 생성이나 외부 전송은 없습니다.</p>'));
 // Every static or literal facts line states cost or transmission.
 const factLines=[...[html,scene,motion].join('\n').matchAll(/<p class="lt-cost-facts"(?: id="[^"]*")?>((?:(?!<\/p>)[\s\S])*)<\/p>/g)].map(m=>text(m[1]));
 assert.ok(factLines.length>=8,'facts lines found: '+factLines.length);for(const line of factLines)assert.match(line,/비용|비 0|연산비|전송|호출|청구|결제|\$/,'facts line states cost or transmission: '+line);
 assert.ok(staticHtml.includes('<p class="lt-cost-facts">이 채팅 초안 작업은 외부 전송·공급자 호출이 없습니다.</p><details class="lt-provenance-detail"><summary>기존 작업 비용 확인 위치</summary>'));
 assert.ok(staticHtml.includes('<p class="lt-cost-facts">참고 승인은 결과 take 승인과 별개이며 외부로 전송하지 않습니다.'));
 assert.ok(staticHtml.includes('<p class="lt-cost-facts">외부 생성비 0, 로컬 연산 비용 미계측</p><details class="lt-provenance-detail"><summary>자막 제공 형식</summary>'));
 assert.equal(count(html,/출력 승인과 별도<\/small>/g),0,'135/259: the scope is no longer glued to the usage label');
 assert.equal(count(html,/<p class="muted">Take 검토는 출력 승인과 별도입니다\.<\/p>/g),2,'135/259: one muted scope line in the review status (UI-r3: not a cost fact)');assert.match(css,/\.lt-ui #takeReviewStatus>\.muted \{ width:100%; margin:0; font-size:var\(--ui-meta\); \}/);
 assert.ok(!html.includes("의 컷과 시각을 선택하세요. 출력 승인은 별도입니다."),'409: the chooser prompt drops the repeat');
 assert.ok(!html.includes('출력 승인은 별도입니다.'),'UI-r3 418: the loaded-frame label drops the repeat');assert.ok(html.includes("초의 실제 합성 프레임입니다.';"));
 assert.ok(!motion.includes('영상 출력은 별도입니다'),'motion-studio frame status drops the repeat');
 const sceneDialog=slice(scene,'dialog.innerHTML=`','`;\n');
 assert.equal(count(outsideDetails(sceneDialog),/별도|별개/g),1,'scene dialog: one approval-scope line outside disclosures');
 assert.ok(sceneDialog.includes('<p class="muted" id="sceneStudioApprovalScope">'),'UI-r3: scene approval scope is muted text, not a cost fact');
 assert.ok(!scene.includes('구성 승인은 별도입니다.'),'UI-r3 scene:154 recovery status drops the repeat');assert.ok(scene.includes("status('기존 변경안 저장을 확인했습니다. 입력은 그대로입니다.')"));
 assert.ok(!media.includes('선택·승인은 별도입니다'),'UI-r3: initial sequence status drops the repeat');
 assert.ok(!ui.includes('모델 답변과 변경안의 적용·출력 승인은 별도입니다.'),'UI-r3: chat turns no longer repeat the approval scope');assert.equal(count(ui,/출력 승인은 별도입니다/g),1,'the one line lives in #generalChatHelp');assert.ok(sceneDialog.includes('id="sceneStudioApprove" aria-describedby="sceneStudioApprovalScope"'));
 assert.ok(scene.includes("status('구도를 승인했습니다.')"),'approve status no longer repeats the summary line');
 done.push('#46 index.html static notes: plain p with widened notice words outside disclosures '+count(outsideDetails(staticHtml),NOTICE)+'; facts lines '+factLines.length+' all cost/transmission');
}

// ---- Approval/transmission facts are back at the decision point (outside disclosures).
{
 const dialog=slice(motion,"dialog.innerHTML='","';\n");
 assert.ok(!/<details[^>]*>[\s\S]*승인과 Take·최종 출력 승인은 별개[\s\S]*?<\/details>/.test(dialog),'motion approval scope not in a disclosure');
 assert.ok(dialog.includes('<p id="motionApprovalScope" class="muted">모션 후보 생성 승인과 Take·최종 출력 승인은 별개입니다.</p><div class="toolbar"><button type="button" id="motionApprove" aria-describedby="motionApprovalScope">'));
 assert.ok(sidebar.includes("preferenceForm.append(modeLabel, modeSelect, preferenceScopeNote, effortLabel"),'agent settings scope note sits in the form');
 assert.ok(sidebar.includes("'편집 권한과 관계없이 최종 출력·비용·전송·사용권 승인은 별도입니다. 계정 삭제는 금지합니다.'"));assert.ok(sidebar.includes("modeSelect.setAttribute('aria-describedby', preferenceScopeNote.id)"));
 assert.ok(!slice(sidebar,' const preferencePolicy = ','\n').includes('사용권 승인'),'disclosure keeps only edit mechanics');
 // Chat send review: transfer scope visible and linked to approve.
 const view={el:id=>({innerHTML:'',textContent:'',value:'',querySelectorAll:()=>[]})};
 const review=slice(ui,'el(\'generalChatReviews\').innerHTML=reviews.map(v=>`','`).join(\'\');');
 assert.ok(text(outsideDetails(review)).includes('자료 파일 자체는 전달하지 않습니다.'),'review card: transfer statement outside the disclosure');
 assert.ok(review.includes('aria-describedby="generalChatTransfer-${esc(v.id)} generalChatApproveNote-${esc(v.id)}"'));
 // Media card: transfer scope visible; sources stay inside.
 const cards={creatorDiagnostic:()=>'',mediaRightsDrafts:new Map(),mediaDraftKey:v=>v};vm.createContext(cards);vm.runInContext(productEsc+';'+productFacts+';globalThis.card=mediaActionMarkup;',cards);
 const markup=cards.card({id:'v1',shot:'s',role:'video',model:'m',prompt:'p',estimate:{amount:'0.35',currency:'USD'},mode:'provider-unverified',can_approve:true,can_decide:true,output_policy:'비공개 출력'});
 assert.ok(text(outsideDetails(markup)).includes('표시된 지시와 승인된 시작 프레임만 전송합니다.'));assert.ok(!text(outsideDetails(markup)).includes('비공개 출력'));
 assert.match(markup,/<p class="lt-cost-facts lt-cost-warning">견적 총액/,'UI-r3: a real estimate at the decision uses the warning token');
 assert.match(cards.card({id:'v2',shot:'s',role:'video',model:'m',prompt:'p',estimate:{amount:'0',currency:'USD'},mode:'contract-fake',can_approve:true,output_policy:'x'}),/<p class="lt-cost-facts">견적 총액/,'contract-fake test card stays neutral');
 assert.ok(review.includes('<p class="lt-cost-facts${v.mode===\'contract-fake\'?\'\':\' lt-cost-warning\'}">최대 예약'),'chat send review: reservation uses the warning token outside the synthetic mode');
 assert.match(css,/\.lt-ui \.lt-cost-facts\.lt-cost-warning \{ color:var\(--ui-warning\); \}/);assert.match(css,/--ui-warning:#[0-9A-F]{6};/);
 void view;done.push('approval/transfer facts outside disclosures: motion, agent settings, chat review, media card; warning token on real spend decisions');
}

// ---- S16 + parity: work-status rows and chat turns carry unit, kind, source link, revision, expiry, provenance.
const unit={amount:'0.07',currency:'USD',unit:'second',source:'https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video',fetched_at:'2026-10-28T09:28:18Z',revision:'fal-public-model-pages-20261028',kind:'documented-estimate'};
const agentVideo={id:'v1',shot:'target',role:'video',model:'fal-ai/kling-video/v2.6/pro/image-to-video',prompt:'blue',options:{duration:5},estimate:{amount:'0.35',currency:'USD'},estimate_kind:'documented-estimate',mode:'provider-unverified',
 price:{unit_price:unit,quantity:5,formula:'0.07 USD/초 × 5초 = 0.35 USD'},price_source:'https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api',price_revision:'quote-r1',quote_expires:4102444800,
 record:'recorded',actor:'agent',model_reason:'움직임 품질이 더 높습니다.',model_reason_label:'모델이 제시한 이유(검증 안 됨)',provenance:{chat_model:'claude-haiku-5-5',permission_mode:'review',effort:'medium'},project_selection:'fal-kling-2-5-turbo',differs_from_project:true};
function workStatus(p,state){
 const make=(tag,className,textValue)=>({tag,className,textContent:textValue||'',innerHTML:'',dataset:{},children:[],append(...nodes){this.children.push(...nodes)},setAttribute(){}});
 const rows={children:[],contains:()=>false,replaceChildren(){this.children=[]},append(n){this.children.push(n)},querySelector:()=>null};
 const w={make,workRows:rows,workStatus:{},workEmpty:{},workDetails:{},workSummaryText:{},workStatusSignature:'',shotName:'target',document:{activeElement:null},song:()=> 'A',conversationDraftKey:()=> 'k',state,project:()=>p};
 vm.createContext(w);vm.runInContext(productEsc+';'+productFacts,w);vm.runInContext(slice(sidebar,' function workGroups(',' function focusWorkTarget(')+';globalThis.render=renderWorkStatus;globalThis.groups=workGroups;',w);w.render();
 return {row:rows.children.find(r=>r.children.some(n=>n.dataset.agentWork==='provider')),groups:w.groups(state,p,'A','target')};
}
{
 const p={active_conversation:{id:'c'},shots:{target:{}},media_actions:[{...agentVideo,job:{id:'j1',state:'running'}},{...agentVideo,id:'v2',job:{id:'j9',state:'running',conversation_id:'foreign'}}]};
 const state={generation_jobs:[{id:'j1',context:{song:'A',shot:'target'},state:'running'},{id:'legacy',context:{song:'A',shot:'target'},state:'prepared'}],jobs:[]};
 const {row,groups}=workStatus(p,state);const provider=groups.find(g=>g.key==='provider');
 assert.equal(provider.count,2,'group counts j1 and the legacy job; the foreign-conversation action job is excluded');
 const facts=row.children.filter(n=>n.className==='lt-cost-facts'),note=row.children.find(n=>n.className==='agent-work-note'),detail=row.children.find(n=>n.className==='lt-provenance-detail');
 assert.equal(facts.length,1,'facts come from the same visible job set (the foreign action is not listed)');
 assert.equal(note.textContent,'준비 기록이 없는 작업 1건은 가격 정보를 표시하지 않습니다.','facts + note = group count');
 const d=text(detail.innerHTML);
 for(const fact of ['가격·출처 상세','target 영상','단가 $0.07/초 · 문서 기준 추정','단가 출처 '+unit.source,'개정 fal-public-model-pages-20261028','견적 출처 '+agentVideo.price_source,'개정 quote-r1','만료 ','제안 출처 · 대화 모델 claude-haiku-5-5 · 권한 검토 후 편집 · 추론 강도 보통'])assert.ok(d.includes(fact),'work-status detail shows: '+fact);
 assert.match(detail.innerHTML,/<a href="https:\/\/fal\.ai\/models\/fal-ai\/kling-video\/v2\.6\/pro\/image-to-video" target="_blank" rel="noopener noreferrer">/,'source is a link');
 // Without a legacy job there is no note; without priced actions there is no disclosure.
 const clean=workStatus(p,{generation_jobs:[state.generation_jobs[0]],jobs:[]});assert.equal(clean.row.children.some(n=>n.className==='agent-work-note'),false);
 const none=workStatus({...p,media_actions:[]},{generation_jobs:[state.generation_jobs[1]],jobs:[]});assert.equal(none.row.children.some(n=>n.className==='lt-provenance-detail'),false);assert.equal(none.row.children.find(n=>n.className==='agent-work-note').textContent,'준비 기록이 없는 작업 1건은 가격 정보를 표시하지 않습니다.');
 done.push('S16 work status: facts 1 + unpriced note 1 = group count 2; detail has unit/kind/source/revision/expiry/provenance');
}
{
 const c={};vm.createContext(c);vm.runInContext(productEsc+';'+productFacts+';globalThis.detail=mediaFactsDetail;globalThis.facts=mediaFacts;',c);
 const withUnit=text(c.detail(c.facts(agentVideo),true)),card=text(c.detail(c.facts(agentVideo)));
 assert.ok(withUnit.startsWith(' 단가 $0.07/초 · 문서 기준 추정 ')||withUnit.startsWith('단가 $0.07/초 · 문서 기준 추정 '),withUnit);assert.ok(!card.includes('단가 $0.07/초'),'card detail does not repeat the unit already on its cost line');
 assert.ok(ui.includes('detail:mediaFactsDetail(mediaFacts(x),true)'),'turn disclosure passes the unit');
 done.push('S16 turn detail: unit price + kind label included');
}

// ---- monotonous-spacing: spacing properties carry tokens, not px literals (sr-only clip excepted).
{
 const literal=[...css.replace(/\/\*[\s\S]*?\*\//g,'').matchAll(/(?<![\w-])(padding|margin|gap|row-gap|column-gap)(-[a-z-]+)?\s*:\s*([^;}]*)/g)].filter(m=>/\d+px/.test(m[3])&&m[0]!=='margin:-1px').map(m=>m[0]);
 assert.deepEqual(literal,[],'px spacing literals');assert.match(css,/--ui-space-half:\.125rem;/);
 done.push('spacing px literals: 0');
}

// ---- UI-r3: comparison playback writes the seek value and time text at most ~10 times a second; pause/end exact.
(async()=>{
 const f=mediaHarness();f.d.clips[0].duration=2.987;f.q('#compareLeft').value='1';f.q('#compareRight').value='1';
 const counted=sel=>{const n=f.q(sel),k=sel==='#compareTime'?'textContent':'value';let v=n[k];n.writes=0;Object.defineProperty(n,k,{get(){return v},set(x){v=String(x);n.writes++},configurable:true});return n};
 const timeNode=counted('#compareTime'),seekNode=counted('#compareSeek');
 f.api.comparison();assert.equal(timeNode.textContent,'00:00.000 / 00:02.987');
 f.frame(1000);await f.api._audit.getCompare().play();timeNode.writes=0;seekNode.writes=0;
 for(let k=1;k<=60;k++)f.frame(1000+k*1000/60);
 assert.ok(timeNode.writes<=11,'61 compare frames write the time text '+timeNode.writes+' times');assert.ok(seekNode.writes<=11,'compare seek writes '+seekNode.writes);
 const playingWrites=timeNode.writes,playingSeek=seekNode.writes;f.frame(2234.6);f.api._audit.getCompare().pause();
 assert.equal(timeNode.textContent,'00:01.235 / 00:02.987','compare pause shows the exact position');
 await f.api._audit.getCompare().play();f.frame(5000);
 assert.equal(timeNode.textContent,'00:02.987 / 00:02.987','compare end shows the exact total');assert.equal(f.q('#compareTogether').textContent,'함께 재생');
 done.push('compare playback: 61 frames -> text '+playingWrites+' writes, seek '+playingSeek+' writes; pause/end exact');
 for(const line of done)console.log('PASS',line);
})().catch(error=>{console.error(error);process.exit(1)});
