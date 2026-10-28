'use strict';
// Controlled event ordering, not a browser timing claim. Uses production bodies via an export seam.
const assert=require('node:assert/strict'),{fixture}=require('./media_async_harness.cjs');
const cases=[];
const test=(name,body)=>cases.push({name,body});
const loaded=(f,s,time=0)=>{s.seek(time);const v=f.q('#preview').children[0];v.onloadeddata();return v;};
function pair(f){
 if(f.p.shots.A.takes.length===1)f.p.shots.A.takes.push({id:2,asset:'fixture:C.mp4',metadata:{duration:5}});
 f.q('#compareLeft').value='1';f.q('#compareRight').value='2';
 const a=new f.Element('video'),b=new f.Element('video');f.nodes.set('#compareLeftPreview video',a);f.nodes.set('#compareRightPreview video',b);f.api.comparison();return [a,b];
}
test('DM01 pending seek applies latest trimmed frame without play',()=>{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0);s.seek(0);const a=f.q('#preview').children[0];s.seek(1.5);a.onloadeddata();assert.equal(a.currentTime,3.5);assert.equal(s.time,1.5);assert.equal(a.paused,true);
});
test('DM02 old cut error waiting playing and loaded callbacks are inert',()=>{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0),a=loaded(f,s),late={error:a.onerror,waiting:a.onwaiting,playing:a.onplaying,loaded:a.onloadeddata};
 const b=loaded(f,s,3);s.play();const label=f.q('#sequenceStatus').textContent;late.error();late.waiting();late.playing();late.loaded();b.currentTime=2;f.frame(1000);
 assert.equal(b.paused,false);assert.equal(s.time,4);assert.equal(f.q('#sequenceStatus').textContent,label);assert.equal(f.frames.size,1);
});
test('DM02 replacement disposes old controller including detached Audio',()=>{
 const f=fixture();f.p.audio_versions.push({id:1,asset:'fixture:audio.wav'});f.d.audio=1;
 const old=f.api._audit.createSequence(f.p,f.d,0),a=loaded(f,old),audio=f.media.find(m=>m.tagName==='audio'),lateError=a.onerror,lateAudio=audio.onerror;
 old.play();const current=f.api._audit.createSequence(f.p,f.d,3),b=loaded(f,current,3);current.play();const label=f.q('#sequenceStatus').textContent;
 lateError();lateAudio();old.seek(1);old.play();assert.equal(audio.paused,true);assert.equal(b.paused,false);assert.equal(f.q('#sequenceStatus').textContent,label);assert.equal(f.q('#sequencePlay').textContent,'일시 정지');assert.equal(f.frames.size,1);
});
test('DM02 old compare canplay/error/loaded cannot change new pair',async()=>{
 const f=fixture(),old=pair(f),late={ready:old[0].oncanplay,error:old[0].onerror,loaded:old[0].onloadeddata},current=pair(f);
 current[0].oncanplay();await f.api._audit.getCompare().play();const label=f.q('#compareSyncStatus').textContent;old[0].readyState=0;late.ready();late.error();late.loaded();assert.equal(f.q('#compareTogether').disabled,false);assert.equal(f.q('#compareSyncStatus').textContent,label);assert.equal(current[0].paused,false);assert.equal(f.frames.size,1);
});
test('DM03 entering comparison stops detached music and sequence RAF',async()=>{
 const f=fixture();f.p.audio_versions.push({id:1,asset:'fixture:audio.wav'});f.d.audio=1;const s=f.api._audit.createSequence(f.p,f.d,0);loaded(f,s);s.play();const audio=f.media.find(m=>m.tagName==='audio');assert.equal(audio.paused,false);
 const videos=pair(f);assert.equal(audio.paused,true);assert.equal(f.frames.size,0);await f.api._audit.getCompare().play();audio.currentTime=1;f.frame(1000);assert.equal(s.time,0);assert.equal(videos.every(v=>v.muted),true);assert.equal(audio.paused,true);
});
test('DM03 reverse transition stops compare before sequence plays',async()=>{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0);loaded(f,s);const videos=pair(f);await f.api._audit.getCompare().play();s.play();assert.equal(videos.every(v=>v.paused),true);assert.equal(f.frames.size,1);
});
test('late rejected play Promise cannot fail a later sequence attempt',async()=>{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0),v=loaded(f,s);let reject;v.play=()=>{v.paused=false;return new Promise((_,r)=>reject=r);};s.play();const pending=reject;s.pause();v.play=()=>{v.paused=false;return Promise.resolve();};s.play();const label=f.q('#sequenceStatus').textContent;pending(new Error('stale synthetic rejection'));await Promise.resolve();await Promise.resolve();assert.equal(v.paused,false);assert.equal(f.q('#sequenceStatus').textContent,label);assert.equal(f.frames.size,1);
});
test('late compare Promise completion cannot start a disposed loop',async()=>{
 const f=fixture(),videos=pair(f);let resolve;videos[0].play=()=>{videos[0].paused=false;return new Promise(r=>resolve=r);};const old=f.api._audit.getCompare(),pending=old.play();const current=pair(f);resolve();await pending;assert.equal(f.frames.size,0);assert.equal(current.every(v=>v.paused),true);assert.equal(f.q('#compareTogether').textContent,'함께 재생');
});
test('late compare Promise rejection cannot fail a replacement pair',async()=>{
 const f=fixture(),videos=pair(f);let reject;videos[0].play=()=>{videos[0].paused=false;return new Promise((_,r)=>reject=r);};const pending=f.api._audit.getCompare().play();const current=pair(f);await f.api._audit.getCompare().play();const label=f.q('#compareSyncStatus').textContent;reject(new Error('stale synthetic rejection'));await pending;assert.equal(current[0].paused,false);assert.equal(f.q('#compareSyncStatus').textContent,label);assert.equal(f.frames.size,1);
});
test('normal audio offset caption switch and canonical data remain intact',()=>{
 const f=fixture();f.p.audio_versions.push({id:1,asset:'fixture:audio.wav'});f.d.audio=1;f.d.audio_offset=2;f.d.subtitles=[{start:0,end:2,text:'첫 줄'},{start:3,end:6,text:'둘째 줄'}];const before=JSON.stringify({p:f.p,d:f.d});const s=f.api._audit.createSequence(f.p,f.d,0);s.play();const a=f.q('#preview').children[0];a.onloadeddata();const audio=f.media.find(x=>x.tagName==='audio');assert.equal(audio.currentTime,2);assert.equal(a.currentTime,2);audio.currentTime=5;f.frame(3000);const b=f.q('#preview').children[0];b.onloadeddata();assert.equal(b.currentTime,1);assert.equal(f.q('#sequenceCaption').textContent,'둘째 줄');assert.equal(JSON.stringify({p:f.p,d:f.d}),before);
});
test('compare common trimmed duration ends both and preserves approvals',async()=>{
 const f=fixture(),before=JSON.stringify(f.d),videos=pair(f);await f.api._audit.getCompare().play();f.frame(3000);assert.equal(videos[0].currentTime,5);assert.equal(videos[1].currentTime,3);assert.equal(videos.every(v=>v.paused),true);assert.equal(JSON.stringify(f.d),before);
});
test('current error is still reported, not hidden by stale guards',()=>{
 const f=fixture(),s=f.api._audit.createSequence(f.p,f.d,0),v=loaded(f,s);s.play();v.onerror();assert.equal(v.paused,true);assert.equal(f.frames.size,0);assert.match(f.q('#sequenceStatus').textContent,/영상을 읽지 못/);
});
(async()=>{const results=[];for(const {name,body} of cases){try{await body();results.push({name,status:'pass'});}catch(error){results.push({name,status:'fail',error:error.message});}}console.log(JSON.stringify({kind:'controlled Node VM events; no browser/media IO',results},null,2));if(results.some(r=>r.status==='fail'))process.exitCode=1;})();
