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
(async()=>{
 const x=make();x.ctx.state.projects.A.guided_plans=[{id:'p',version:1,status:'proposed',goal:'g',style:'',constraints:'',explanation:'synthetic',scenes:[{description:'s',duration:null}],questions:[]}];vm.runInContext(line('function drawGuided('),x.ctx);vm.runInContext('drawGuided()',x.ctx);
 record('F05-missing-duration-markup',x.nodes['#guidedPlans'].innerHTML.includes('disabled data-plan-blocked="true"'),{html:x.nodes['#guidedPlans'].innerHTML});
 for(const mode of ['success','server-error','transport-error','refresh-error','cache-error']){
  const x=make();vm.runInContext(send,x.ctx);
  if(mode==='server-error')x.ctx.fetch=async()=>({ok:false,json:async()=>({error:'synthetic rejection'})});
  if(mode==='transport-error')x.ctx.fetch=async()=>{throw Error('synthetic transport')};
  if(mode==='refresh-error')x.ctx.refresh=async()=>{throw Error('synthetic refresh')};
  if(mode==='cache-error')x.ctx.requestCache=async()=>{throw Error('synthetic storage')};
  const answer=await vm.runInContext(mode==='cache-error'?"act('comment',{song:'A'})":"sendRequest({action:'comment'},'A')",x.ctx);
  record('F05-button-policy-'+mode,x.flags[0].disabled&&!x.flags[1].disabled,{answer,blockedDisabled:x.flags[0].disabled,ordinaryDisabled:x.flags[1].disabled});
 }
 {
  const x=make();x.restore();x.input('1.25','한글 초안');const y=make(x.map);y.restore();
  record('F06-reload-restores-draft',JSON.stringify(y.read())===JSON.stringify(x.read()),{afterReload:y.read()});
  y.ctx.current='B';y.restore();const bEmpty=y.read().text==='';y.input('2.5','B 초안');y.ctx.current='A';y.restore();
  record('F06-project-scope',bEmpty&&y.read().text==='한글 초안',{restoredA:y.read(),storedB:JSON.parse(y.map.get('loretune-comment-draft:synthetic-w1:B'))});
  y.ctx.state.workspace_id='synthetic-w2';y.restore();record('F06-workspace-scope',y.read().text==='',{newWorkspace:y.read()});
 }
 for(const success of [false,true]){
  const x=make();x.restore();x.input('1.25','보존할 의견');x.ctx.act=async()=>success;await x.submit();
  record('F06-'+(success?'successful-save-clears':'failed-save-preserves'),success?(x.map.size===0&&x.read().text===''):(x.map.size===1&&x.read().text==='보존할 의견'),{field:x.read(),stored:[...x.map]});
 }
 {
  const x=make();x.restore();x.input('1.25','first submitted draft');let finish;let submitted;let entered;
  const requestStarted=new Promise(r=>entered=r);
  vm.runInContext(line('function pendingId(')+'\n'+line('function clearPending(')+'\n'+send,x.ctx);
  x.ctx.refresh=async()=>x.restore();
  x.ctx.fetch=async(url,args)=>{submitted=JSON.parse(args.body);entered();return new Promise(r=>finish=r)};
  const pending=x.submit();await requestStarted;x.input('2.5','second unsent draft while save pending');finish({ok:true,json:async()=>({})});await pending;
  record('F06-adjacent-pending-save-must-preserve-new-edit',x.read().text==='second unsent draft while save pending'&&[...x.map.values()].some(v=>v.includes('second unsent')),{submitted,expectedNewText:'second unsent draft while save pending',actualField:x.read(),actualStorage:[...x.map],execution:'VM with delayed fake fetch; exact snapshot submit, act, sendRequest, pending helpers, input listener'});
 }
 fs.writeFileSync(path.join(__dirname,'ui-results.json'),JSON.stringify(out,null,2)+'\n');for(const x of out)console.log(JSON.stringify(x));
})().catch(e=>{console.error(e);process.exit(1)});
