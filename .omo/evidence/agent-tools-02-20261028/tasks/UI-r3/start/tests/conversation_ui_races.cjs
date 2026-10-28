'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const source=html.slice(html.indexOf('async function switchConversation('),html.indexOf("$('#conversationSelect').onchange="));
function fixture(){
 const node={value:'A'},pending=[];let active='B';
 const make=id=>({workspace_id:'w',revision:2,projects:{song:{active_conversation:{id}}}});
 const c={state:make('B'),stateReadEpoch:0,conversationSwitching:0,busy:false,dirty:false,draft:null,URLSearchParams, song:()=> 'song',project:()=>c.state.projects.song,$:()=>node,message:()=>{},rememberConversation:()=>{},draw:()=>{},drawJobs:()=>{},fetch:()=>new Promise(resolve=>pending.push(resolve))};
 vm.createContext(c);vm.runInContext(source,c);
 return {c,node,pending,make};
}
(async()=>{
 {
  const f=fixture(),a=f.c.switchConversation('A');assert.notEqual(f.c.conversationSwitching,0);
  f.node.value='B';await f.c.switchConversation('B');
  f.pending[0]({ok:true,json:async()=>f.make('A')});await a;
  assert.equal(f.c.state.projects.song.active_conversation.id,'B');assert.equal(f.node.value,'B');assert.equal(f.c.conversationSwitching,0);
 }
 {
  const f=fixture(),a=f.c.switchConversation('A');f.c.dirty=true;
  f.pending[0]({ok:true,json:async()=>f.make('A')});await a;
  assert.equal(f.c.state.projects.song.active_conversation.id,'B');assert.equal(f.node.value,'B');
 }
 {
  const f=fixture(),a=f.c.switchConversation('A');f.node.value='A';
  f.pending[0]({ok:false,json:async()=>({error:'fixture error'})});await a;
  assert.equal(f.c.state.projects.song.active_conversation.id,'B');assert.equal(f.node.value,'B');
 }
 {
  let sent=0;const c={conversationSwitching:1,busy:false,message(){},fetch(){sent++}};
  vm.createContext(c);vm.runInContext(html.slice(html.indexOf('async function act('),html.indexOf('async function reconcilePendingRequest(')),c);
  assert.equal(await c.act('chat_plan',{song:'song',prompt:'draft'}),false);assert.equal(sent,0);
 }
 console.log('4 conversation race cases passed');
})().catch(e=>{console.error(e);process.exitCode=1});
