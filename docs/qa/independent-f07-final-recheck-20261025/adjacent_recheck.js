// Executes exact snapshot functions in a synthetic VM DOM; never opens a browser.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'snapshot/index.html'),'utf8');
const line=prefix=>html.split('\n').find(x=>x.startsWith(prefix));
const draftCode=[line("let commentDraftScope="),line('function commentDraftKey('),line('function restoreCommentDraft('),line("$('#comment').addEventListener")].join('\n');
const submit=html.slice(html.indexOf("$('#comment').onsubmit="),html.indexOf(";$('#comments').onclick="))+';';
const send=html.slice(html.indexOf('async function sendRequest('),html.indexOf("$('#recoverRequest').onclick="));
const out=[];function record(test,ok,detail){out.push({case:test,status:ok?'pass':'fail',...detail});}
function make(map=new Map()){
 const form={elements:{at:{value:'0'},text:{value:''}},handlers:{},reset(){this.elements.at.value='0';this.elements.text.value='';},addEventListener(e,fn){this.handlers[e]=fn;}};
 const nodes={'#comment':form,'#notice':{focus(){}},'#recovery':{},'#guidedPlans':{}};
 const flags=[{blocked:true,disabled:true},{blocked:false,disabled:false}];flags.forEach(x=>x.hasAttribute=n=>n==='data-plan-blocked'&&x.blocked);
 const storage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};
 const ctx={state:{workspace_id:'synthetic-w1',projects:{A:{},B:{}},revision:1,token:'synthetic-ui-token'},current:'A',shotName:'Shot A1',busy:false,dirty:false,pendingRequest:null,
 $:s=>nodes[s],song:()=>ctx.current,sessionStorage:storage,FormData:class{constructor(f){this.values=Object.entries(f.elements).map(([k,v])=>[k,v.value]);}get(k){return this.values.find(x=>x[0]===k)?.[1];}[Symbol.iterator](){return this.values[Symbol.iterator]();}},
 message(){},act:async()=>false,document:{querySelectorAll:()=>flags,querySelector:()=>null},drawModelChat(){},clearPending(){},pendingId:()=>null,refresh:async()=>{},fetch:async()=>({ok:true,json:async()=>({})}),requestCache:async()=>{},crypto:{randomUUID:()=> 'synthetic-id'},project:()=>ctx.state.projects[ctx.current],restoreBrief(){},esc:x=>String(x??'')};
 vm.createContext(ctx);vm.runInContext(draftCode+'\n'+submit,ctx);
 return {ctx,form,map,nodes,flags,restore:()=>vm.runInContext('restoreCommentDraft()',ctx),input:(at,text)=>{form.elements.at.value=at;form.elements.text.value=text;form.handlers.input();},read:()=>({at:form.elements.at.value,text:form.elements.text.value}),submit:()=>form.onsubmit({preventDefault(){},target:form})};
}

// Independent edge cases; the implementation under test still comes only from snapshot/index.html.
function net(x){
 vm.runInContext(line('function pendingId(')+'\n'+line('function clearPending(')+'\n'+send,x.ctx);
 x.ctx.refresh=async()=>x.restore();let seq=0;x.ctx.crypto.randomUUID=()=> 'synthetic-'+(++seq);
}
function stored(x,project='A',workspace='synthetic-w1'){
 const v=x.map.get('loretune-comment-draft:'+workspace+':'+project);return v===undefined?null:JSON.parse(v);
}
async function pending(x){
 let entered,finish,fail,submitted;
 const started=new Promise(r=>entered=r);
 x.ctx.fetch=async(url,args)=>{submitted=JSON.parse(args.body);entered();return new Promise((resolve,reject)=>{finish=resolve;fail=reject})};
 const work=x.submit();await started;
 return {submitted,work,ok:async()=>{finish({ok:true,json:async()=>({})});await work},bad:async()=>{finish({ok:false,json:async()=>({error:'synthetic rejection'})});await work},lost:async()=>{fail(Error('synthetic lost response'));await work}};
}
function fixture(){const x=make();x.restore();x.input('1.25','original submitted');net(x);return x;}
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const inspect=x=>({field:x.read(),draftA:stored(x),draftB:stored(x,'B'),pending:x.map.get('loretune-pending')||null});
(async()=>{
 for(const mode of ['clear-then-different','clear-then-same','clear-only']){
  const x=fixture(),p=await pending(x);x.input('0','');
  if(mode==='clear-then-different')x.input('2.5','new rewritten draft');
  if(mode==='clear-then-same')x.input('1.25','original submitted');
  const expected=x.read();await p.ok();record(mode,eq(x.read(),expected)&&eq(stored(x),expected),{submitted:p.submitted,expected,...inspect(x)});
 }
 {
  const x=fixture();x.ctx.current='B';x.restore();x.input('8','B existing unsent');x.ctx.current='A';x.restore();
  const p=await pending(x);x.ctx.current='B';x.restore();const expected=x.read();await p.ok();
  record('project-switch-preserves-existing-B-draft',eq(x.read(),expected)&&eq(stored(x,'B'),expected)&&stored(x)===null,{expected,...inspect(x)});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.current='B';x.restore();x.input('2','B new unsent');const expected=x.read();await p.ok();
  record('project-switch-preserves-new-B-draft',eq(x.read(),expected)&&eq(stored(x,'B'),expected)&&stored(x)===null,{expected,...inspect(x)});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.current='B';x.restore();x.input('2','B other unsent');x.ctx.current='A';x.restore();x.input('3','A returned new unsent');const expected=x.read();await p.ok();
  record('project-return-preserves-new-A-and-B',eq(x.read(),expected)&&eq(stored(x),expected)&&stored(x,'B').text==='B other unsent',{expected,...inspect(x)});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.current='B';x.restore();x.input('2','B other unsent');x.ctx.current='A';x.restore();await p.ok();
  record('project-return-clears-only-unchanged-submitted-A',x.read().text===''&&stored(x)===null&&stored(x,'B').text==='B other unsent',inspect(x));
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.shotName='Shot A2';x.restore();x.input('3','new shot-context draft');const expected=x.read();await p.ok();
  record('shot-switch-preserves-new-draft',eq(x.read(),expected)&&eq(stored(x),expected),{expected,...inspect(x)});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.shotName='Shot A2';x.restore();const expected=x.read();await p.ok();
  record('shot-switch-does-not-reset-different-context-form',eq(x.read(),expected),{expected,...inspect(x),note:'No new edit: old submitted storage may be cleared; form reset must be scoped.'});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.shotName='Shot A2';x.input('4','transient');x.ctx.shotName='Shot A1';x.input('1.25','original submitted');const expected=x.read();await p.ok();
  record('shot-return-identical-value-is-still-new-edit',eq(x.read(),expected)&&eq(stored(x),expected),{expected,...inspect(x)});
 }
 for(const mode of ['server-rejection','lost-response','refresh-failure']){
  const x=fixture(),p=await pending(x);x.input('7','new draft survives '+mode);const expected=x.read();
  if(mode==='server-rejection')await p.bad();
  else if(mode==='lost-response')await p.lost();
  else{x.ctx.refresh=async()=>{throw Error('synthetic refresh failure')};await p.ok();}
  record(mode+'-preserves-new-draft',eq(x.read(),expected)&&eq(stored(x),expected),{expected,...inspect(x)});
 }
 {
  const x=fixture(),p=await pending(x);x.ctx.state.workspace_id='synthetic-w2';x.restore();x.input('5','other workspace unsent');const expected=x.read();await p.ok();
  record('workspace-switch-preserves-new-draft',eq(x.read(),expected)&&eq(stored(x,'A','synthetic-w2'),expected)&&stored(x)===null,{expected,field:x.read(),otherWorkspaceDraft:stored(x,'A','synthetic-w2')});
 }
 {
  const x=fixture(),p1=await pending(x);x.input('2','second draft');await x.submit();const duplicateHeld=eq(x.read(),stored(x))&&x.read().text==='second draft';await p1.ok();
  const firstKept=x.read().text==='second draft'&&stored(x).text==='second draft';
  const p2=await pending(x);x.input('3','third draft');await p2.ok();const secondKept=x.read().text==='third draft'&&stored(x).text==='third draft';
  const p3=await pending(x);await p3.ok();
  record('repeated-saves-and-duplicate-click-preserve-newer-drafts',duplicateHeld&&firstKept&&secondKept&&p2.submitted.data.text==='second draft'&&p3.submitted.data.text==='third draft'&&stored(x)===null&&x.read().text==='',{duplicateHeld,firstKept,secondKept,requests:[p1.submitted,p2.submitted,p3.submitted],...inspect(x)});
 }
 {
  const x=fixture(),p1=await pending(x);x.input('2','retry draft');await p1.bad();const p2=await pending(x);x.input('3','after retry unsent');await p2.ok();
  record('failed-save-then-success-preserves-later-edit',p2.submitted.data.text==='retry draft'&&x.read().text==='after retry unsent'&&stored(x).text==='after retry unsent',{retried:p2.submitted,...inspect(x)});
 }
 fs.writeFileSync(path.join(__dirname,'adjacent-results.json'),JSON.stringify(out,null,2)+'\n');for(const row of out)console.log(JSON.stringify(row));
 if(out.some(x=>x.status!=='pass'))process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
