'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),path=require('path');
const original=fs.readFileSync(path.join(__dirname,'snapshot/studio-media.js'),'utf8');
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
const evidence=[];
{
 const f=fixture(),before=JSON.stringify({p:f.p,d:f.d}),s=f.api._audit.createSequence(f.p,f.d,0);
 s.seek(0);const a=f.q('#preview').children[0];s.seek(1.5);a.onloadeddata();
 const loadedSource=a.currentTime;s.play();f.frame(16);
 evidence.push({case:'DM01-seek-while-loading',expected_source:3.5,actual_loaded_source:loadedSource,expected_timeline:1.5,actual_timeline_after_play:s.time,play_reseeks_correctly:a.currentTime===3.5,unchanged:before===JSON.stringify({p:f.p,d:f.d})});
 assert.equal(loadedSource,2);assert.equal(s.time,1.5);
}
{
 const f=fixture(),before=JSON.stringify({p:f.p,d:f.d}),s=f.api._audit.createSequence(f.p,f.d,0);
 s.seek(0);const a=f.q('#preview').children[0];a.onloadeddata();s.seek(3);const b=f.q('#preview').children[0];b.onloadeddata();s.play();assert.equal(b.paused,false);
 a.onerror();evidence.push({case:'DM02-detached-old-video-error',old_connected:a.isConnected,active_video_paused:b.paused,active_label:f.q('#sequenceStatus').textContent,scheduled_frames:f.frames.size,unchanged:before===JSON.stringify({p:f.p,d:f.d})});assert.equal(b.paused,true);assert.equal(f.frames.size,0);
}
{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const a=f.q('#preview').children[0];a.onloadeddata();s.seek(3);const b=f.q('#preview').children[0];b.onloadeddata();s.play();a.onwaiting();b.currentTime=2;f.frame(1000);
 evidence.push({case:'DM02-detached-old-video-waiting',old_connected:a.isConnected,expected_timeline:4,actual_timeline:s.time,active_video_source:b.currentTime});assert.equal(s.time,3);
}
{
 const f=fixture(),old=f.api._audit.createSequence(f.p,f.d,0);old.seek(0);const a=f.q('#preview').children[0];old.pause();
 const current=f.api._audit.createSequence(f.p,f.d,3);current.seek(3);const b=f.q('#preview').children[0];b.onloadeddata();current.play();const before=f.q('#sequenceStatus').textContent;a.onerror();
 evidence.push({case:'DM02-replaced-controller-error',before,after:f.q('#sequenceStatus').textContent,new_video_still_playing:!b.paused,button:f.q('#sequencePlay').textContent});assert.notEqual(f.q('#sequenceStatus').textContent,before);
}
{
 const f=fixture();f.p.shots.A.takes.push({id:2,asset:'fixture:C.mp4',metadata:{duration:5}});f.q('#compareLeft').value='1';f.q('#compareRight').value='2';
 const a=new f.Element('video'),b=new f.Element('video');f.nodes.set('#compareLeftPreview video',a);f.nodes.set('#compareRightPreview video',b);f.api.comparison();
 const oldHandler=a.oncanplay;const c=new f.Element('video'),d=new f.Element('video');f.nodes.set('#compareLeftPreview video',c);f.nodes.set('#compareRightPreview video',d);f.api.comparison();c.oncanplay();assert.equal(f.q('#compareTogether').disabled,false);a.readyState=0;oldHandler();
 evidence.push({case:'DM02-replaced-compare-canplay',new_ready:[c.readyState,d.readyState],button_disabled:f.q('#compareTogether').disabled});assert.equal(f.q('#compareTogether').disabled,true);
}
{
 const f=fixture();f.p.audio_versions.push({id:1,asset:'fixture:audio.wav'});f.d.audio=1;const s=f.api._audit.createSequence(f.p,f.d,0);s.play();f.q('#preview').children[0].onloadeddata();const audio=f.media.find(m=>m.tagName==='audio');assert.equal(audio.paused,false);
 f.p.shots.A.takes.push({id:2,asset:'fixture:C.mp4',metadata:{duration:5}});f.q('#compareLeft').value='1';f.q('#compareRight').value='2';const a=new f.Element('video'),b=new f.Element('video');f.nodes.set('#compareLeftPreview video',a);f.nodes.set('#compareRightPreview video',b);f.api.comparison();f.api._audit.getCompare().play();audio.currentTime=1;f.frame(1000);
 evidence.push({case:'DM03-comparison-does-not-stop-sequence-audio',detached_audio:!audio.isConnected,sequence_audio_still_playing:!audio.paused,sequence_time:s.time,comparison_videos_muted:a.muted&&b.muted});assert.equal(audio.paused,false);assert.equal(s.time,1);
}
console.log(JSON.stringify({fixture:'Node VM minimal DOM; controlled asynchronous media events; no browser or media IO',source_change:'exports only',findings:evidence},null,2));
