'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),path=require('path');
const original=fs.readFileSync(process.argv[2] || path.join(__dirname,'snapshot/studio-media.js'),'utf8');
// Test-only export seam. No function bodies/guards/control flow are changed.
const source=original.replace('Object.assign(api,{setup,timeline,comparison,stop,decoratePosters});','Object.assign(api,{setup,timeline,comparison,stop,decoratePosters,_audit:{setBridge:b=>bridge=b,createSequence,getCompare:()=>compare}});');
assert.notEqual(source,original);
function fixture(){
 const nodes=new Map(),media=[],frames=new Map();let next=0,now=0;
 class Element{
  constructor(tag='div'){this.tagName=tag;this.children=[];this.style={};this.dataset={};this.attributes={};this.isConnected=true;this.textContent='';this.value='0';this.currentTime=0;this.duration=12;this.readyState=4;this.paused=true;this.error=null;this.playCalls=0;this.pauseCalls=0;}
  pause(){this.paused=true;this.pauseCalls++;}play(){this.paused=false;this.playCalls++;return Promise.resolve();}
  append(...els){this.children.push(...els);}replaceChildren(...els){for(const c of this.children)c.isConnected=false;this.children=els;}
  setAttribute(k,v){this.attributes[k]=v;}getAttribute(k){return this.attributes[k];}removeAttribute(k){delete this.attributes[k];}load(){}querySelector(){return null;}remove(){}addEventListener(){}
 }
 const document={querySelector:s=>{if(!nodes.has(s))nodes.set(s,new Element());return nodes.get(s);},querySelectorAll:s=>s==='video,audio'?media.filter(m=>m.isConnected):[],createElement:t=>{const e=new Element(t);if(t==='video')media.push(e);return e;}};
 class Audio extends Element{constructor(src){super('audio');this.src=src;this.isConnected=false;media.push(this);}}
 const ctx={console,document,Audio,Promise,Map,Math,Number,String,Object,Array,performance:{now:()=>now},requestAnimationFrame:f=>{frames.set(++next,f);return next;},cancelAnimationFrame:i=>frames.delete(i),setTimeout:()=>0,clearTimeout:()=>{}};vm.createContext(ctx);vm.runInContext(source,ctx);
 const p={shots:{A:{selected:1,takes:[{id:1,asset:'fixture:A.mp4',metadata:{duration:12},reviews:[]}]},B:{selected:1,takes:[{id:1,asset:'fixture:B.mp4',metadata:{duration:12},reviews:[]}]}},audio_versions:[]};
 const d={clips:[{shot:'A',take:1,trim:2,duration:3},{shot:'B',take:1,trim:1,duration:3}],audio:null,audio_offset:0,subtitles:[],approval:{id:'human-approval'}};
 const bridge={project:()=>p,draft:()=>d,shot:()=> 'A',context:()=> 'project:A',asset:t=>t.asset,image:t=>t.asset.endsWith('.png'),allowed:()=>true,dirty:()=>false};ctx.LoretuneMedia._audit.setBridge(bridge);
 return {api:ctx.LoretuneMedia,p,d,bridge,media,nodes,q:document.querySelector,frame(t){now=t;const pending=[...frames.values()];frames.clear();for(const f of pending)f(t);},frames,Element};
}

module.exports={fixture};
