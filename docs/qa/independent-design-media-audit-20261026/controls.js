'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const prefix=fs.readFileSync(path.join(__dirname,'async-media-repro.js'),'utf8').split('const evidence=[];')[0];
const fixture=new Function('require','__dirname',prefix+'\nreturn fixture;')(require,__dirname);
const results=[];
async function main(){
 {
 const f=fixture();f.p.audio_versions.push({id:1,asset:'fixture:audio.wav'});f.d.audio=1;f.d.audio_offset=2;f.d.subtitles=[{start:0,end:2,text:'A caption'},{start:3,end:6,text:'B caption'}];const before=JSON.stringify({p:f.p,d:f.d});
 const s=f.api._audit.createSequence(f.p,f.d,0);s.play();const a=f.q('#preview').children[0];a.onloadeddata();const audio=f.media.find(x=>x.tagName==='audio');assert.equal(audio.currentTime,2);assert.equal(a.currentTime,2);assert.equal(f.q('#sequenceCaption').textContent,'A caption');audio.currentTime=3.5;f.frame(1500);assert.equal(s.time,1.5);assert.equal(a.currentTime,3.5);audio.currentTime=5;f.frame(3000);const b=f.q('#preview').children[0];b.onloadeddata();assert.equal(s.time,3);assert.equal(b.currentTime,1);assert.equal(f.q('#sequenceCaption').textContent,'B caption');assert.equal(before,JSON.stringify({p:f.p,d:f.d}));
 results.push({case:'normal-sequence-audio-offset-trim-captions-immutable',status:'pass'});
 // The old loadeddata callback DOES have a serial guard.
 b.currentTime=1.25;a.onloadeddata();assert.equal(b.currentTime,1.25);results.push({case:'old-loadeddata-current-serial-guard',status:'pass'});
 }
 {
 const f=fixture();f.p.shots.A.takes.push({id:2,asset:'fixture:C.mp4',metadata:{duration:5}});f.q('#compareLeft').value='1';f.q('#compareRight').value='2';const a=new f.Element('video'),b=new f.Element('video');f.nodes.set('#compareLeftPreview video',a);f.nodes.set('#compareRightPreview video',b);const before=JSON.stringify({p:f.p,d:f.d});f.api.comparison();assert.equal(a.currentTime,2);assert.equal(b.currentTime,0);await f.api._audit.getCompare().play();f.frame(3000);assert.equal(a.currentTime,5);assert.equal(b.currentTime,3);assert.equal(a.paused,true);assert.equal(b.paused,true);assert.equal(before,JSON.stringify({p:f.p,d:f.d}));results.push({case:'compare-trim-min-duration-end-immutable',status:'pass'});
 }
 {
 const f=fixture();f.p.shots.A.takes[0].asset='fixture:still.png';f.p.shots.A.takes.push({id:2,asset:'fixture:C.mp4',metadata:{duration:5}});f.q('#compareLeft').value='1';f.q('#compareRight').value='2';const b=new f.Element('video');f.nodes.set('#compareLeftPreview video',null);f.nodes.set('#compareRightPreview video',b);f.api.comparison();await f.api._audit.getCompare().play();f.frame(5000);assert.equal(b.currentTime,5);assert.equal(b.paused,true);results.push({case:'compare-static-image-plus-video',status:'pass'});
 }
 {
 const f=fixture();let allowed=true;f.bridge.allowed=()=>allowed;const t=f.p.shots.A.takes[0];t.asset='/assets/synthetic-sha.mp4';const native=new f.Element('video');native.setAttribute('src',t.asset);f.nodes.set('#preview video',native);f.api.decoratePosters();await Promise.resolve();const decoder=f.media.at(-1);assert.equal(decoder.src,t.asset);allowed=false;decoder.onerror();await Promise.resolve();await Promise.resolve();await Promise.resolve();assert.equal(native.poster,undefined);results.push({case:'poster-load-failure-after-rights-revoke-no-application',status:'pass'});
 }
 {
 const html=fs.readFileSync(path.join(__dirname,'snapshot/index.html'),'utf8'),css=fs.readFileSync(path.join(__dirname,'snapshot/studio.css'),'utf8');const line=html.split('\n').find(x=>x.startsWith("$('#textScale').onchange="));let applied;const node={};const doc={documentElement:{style:{setProperty:(k,v)=>applied={k,v}}}};new Function('$','document',line)(()=>node,doc);for(const value of ['1','1.5','2']){node.onchange({target:{value}});assert.deepEqual(applied,{k:'--text-scale',v:value});}assert(!/font-size\s*:\s*\d+(\.\d+)?px/.test(css));results.push({case:'text-scale-real-handler-100-150-200-static-css',status:'pass',limit:'no computed layout or browser zoom test'});
 }
 console.log(JSON.stringify({controls:results},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
