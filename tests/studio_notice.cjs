const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
function extract(start,end){const i=html.indexOf(start);assert.ok(i>=0,start);const j=html.indexOf(end,i);assert.ok(j>i,end);return html.slice(i,j)}

let update;
const notice={textContent:'로컬 저장소 연결됨 · 선택과 승인을 분리해 안전하게 제작하세요.',dataset:{},error:false,classList:{contains:()=>notice.error}};
const detail={open:false};
const summary={attributes:{},listeners:{},setAttribute(k,v){this.attributes[k]=v},addEventListener(k,v){this.listeners[k]=v}};
const presentation=vm.createContext({MutationObserver:class{constructor(fn){update=fn}observe(){}}});
vm.runInContext(extract('function installStudioNotice(', 'ensureStudioReviewDOM();')+extract('function creatorError(', 'function creatorDiagnostic('),presentation);
presentation.installStudioNotice(notice,detail,summary);
assert.equal(summary.textContent,'불러옴');assert.equal(detail.open,false);
assert.equal(summary.attributes['aria-live'],'polite');assert.equal(summary.attributes['aria-atomic'],'true');assert.equal(summary.attributes.role,undefined);
for(const [text,label] of [['저장 중…','저장 중…'],['저장했습니다.','저장됨'],['승인 버전으로 렌더 작업을 등록했습니다.','출력 접수됨']]){
 notice.textContent=text;update();assert.equal(summary.textContent,label);assert.equal(detail.open,false);
}
summary.listeners.click();detail.open=true;update();assert.equal(detail.open,true);
summary.listeners.click();detail.open=false;update();assert.equal(detail.open,false);
notice.error=true;update();assert.equal(detail.open,true);assert.equal(summary.textContent,'오류 · '+notice.textContent,'#45: error summary names the cause');
notice.textContent='가'.repeat(60);update();assert.equal(summary.textContent,'오류 · '+'가'.repeat(40)+'…','long causes are shortened');notice.textContent='';update();assert.equal(summary.textContent,'오류');notice.textContent='로컬 저장소 연결됨 · 선택과 승인을 분리해 안전하게 제작하세요.';
notice.textContent='처리 결과 미확정 · 기존 요청을 확인하세요.';update();assert.equal(detail.open,true);assert.match(notice.textContent,/미확정/);
notice.error=false;notice.textContent='사용권 재확인이 필요합니다.';update();assert.equal(detail.open,true);assert.equal(summary.textContent,'알림','non-error notices keep the generic label');
notice.dataset.inlineFeedback='true';notice.textContent='장면 안에서 저장 상태를 확인하세요.';update();assert.equal(detail.open,false);assert.equal(summary.textContent,notice.textContent);
notice.dataset.inlineFeedback='false';notice.textContent='저장했습니다.';update();assert.equal(detail.open,false);
const complexity='GLB 모델이 너무 복잡해 가져올 수 없습니다. 더 단순한 정적 GLB 파일을 선택하세요.';
for(const message of [complexity,'입력을 확인하세요: '+complexity]){const result=presentation.creatorError(message);assert.equal(result.message,complexity);assert.equal(result.detail,'')}
const malformed=presentation.creatorError('입력을 확인하세요: 지원하지 않거나 손상된 GLB 모델입니다.');assert.match(malformed.detail,/손상된 GLB/);assert.notEqual(malformed.message,complexity);
for(const prefix of ['', '입력을 확인하세요: ']){
 const music=presentation.creatorError(prefix+'선택 구간은 원곡 길이 안에서 시작 < 끝이어야 합니다.');
 assert.match(music.message,/음악 구간.*시작.*끝.*원곡 길이/);assert.equal(music.detail,'');
}
const unknown=presentation.creatorError('입력을 확인하세요: unknown internal validation');assert.match(unknown.message,/작업을 완료하지 못했습니다/);assert.equal(unknown.detail,'입력을 확인하세요: unknown internal validation');

const body={},focused=[],noticeDetail={tagName:'DETAILS',open:false},status={parentElement:noticeDetail,focus(){if(noticeDetail.open){focused.push('status');document.activeElement=this}}},dialogStatus={focus(){focused.push('dialog');document.activeElement=this}};
const document={body,activeElement:body,querySelectorAll:()=>[],querySelector:()=>dialogOpen?dialogStatus:null};
let dialogOpen=false,pending='id',refreshAction=()=>{},response={ok:true,json:async()=>({})};
const context=vm.createContext({document,$:()=>status,state:{token:'synthetic'},pendingId:()=>pending,clearPending:()=>{pending=null},message:()=>{},drawModelChat:()=>{},renderTakeReview:()=>{},updateRecovery:()=>{},refresh:async()=>refreshAction(),fetch:async()=>{if(response instanceof Error)throw response;return response}});
vm.runInContext(extract('async function sendRequest(', 'async function act('),context);
function initiator(){return {isConnected:true,disabled:false,focus(){focused.push('initiator');document.activeElement=this}}}
async function attempt(before,after,{reply,dialog=false}={}){
 focused.length=0;pending='id';document.activeElement=before;dialogOpen=dialog;noticeDetail.open=false;
 refreshAction=typeof after==='function'?after:()=>{document.activeElement=after};
 response=reply||{ok:true,status:200,json:async()=>({})};
 return context.sendRequest({action:'render_job',request_id:'id'});
}
(async()=>{
 const button=initiator(),input={};
 assert.equal(await attempt(button,body),true);assert.deepEqual(focused,['initiator']);assert.equal(document.activeElement,button);
 assert.equal(await attempt(button,input),true);assert.deepEqual(focused,[]);assert.equal(document.activeElement,input);
 const removed=initiator();removed.isConnected=false;assert.equal(await attempt(removed,body),true);assert.deepEqual(focused,[]);
 const blocked=initiator();blocked.disabled=true;assert.equal(await attempt(blocked,body),true);assert.deepEqual(focused,[]);
 assert.equal(await attempt(button,body,{reply:{ok:false,status:400,json:async()=>({error:'invalid input'})}}),false);assert.deepEqual(focused,['status']);assert.equal(pending,null);
 assert.equal(await attempt(button,body,{reply:new Error('lost response'),dialog:true}),false);assert.deepEqual(focused,['dialog']);assert.equal(pending,'id');
 assert.equal(await attempt(button,()=>{throw Error('refresh failed')}),false);assert.deepEqual(focused,['status']);assert.equal(pending,null);
 // act disables the initiating button before its asynchronous recovery-cache write.
 // Exercise that public entry path, including the browser's native button blur.
 vm.runInContext(extract('async function act(', 'async function reconcilePendingRequest('),context);
 Object.assign(context,{dirty:false,stateReadEpoch:0,requestCache:async()=>{},crypto:{randomUUID:()=> 'actual-entry-id'},sessionStorage:{setItem(){pending='actual-entry-id'}}});
 context.state.projects={};context.state.revision=1;
 let disabled=false;
 const actionButton={isConnected:true,hasAttribute:()=>false,get disabled(){return disabled},set disabled(value){disabled=value;if(value&&document.activeElement===this)document.activeElement=body},focus(){focused.push('action');document.activeElement=this}};
 document.querySelectorAll=()=>[actionButton];
 for(const moved of [false,true]){
  focused.length=0;pending=null;document.activeElement=actionButton;
  refreshAction=()=>{if(moved)document.activeElement=input};
  response={ok:true,status:200,json:async()=>({})};
  assert.equal(await context.act('estimate_render',{song:'work'}),true);
  assert.equal(document.activeElement,moved?input:actionButton);
  assert.deepEqual(focused,moved?[]:['action']);
 }
 console.log('studio notice, diagnosis presentation and request focus checks passed');
})().catch(error=>{console.error(error);process.exitCode=1});
