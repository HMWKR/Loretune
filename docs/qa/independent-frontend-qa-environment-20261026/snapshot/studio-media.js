/* Local audition only. This module never saves, selects a Take, or grants approval. */
(function (root) {
 'use strict';
 const clamp=(n,a,b)=>Math.min(b,Math.max(a,Number(n)||0));
 const safe=n=>Number.isFinite(Number(n))?Math.max(0,Number(n)):0;
 function ranges(clips){let at=0;return clips.map((c,index)=>{const start=at;at+=safe(c.duration);return {...c,index,start,end:at,duration:at-start,trim:safe(c.trim)};});}
 function locate(clips,time){const list=ranges(clips),total=list.at(-1)?.end||0,t=clamp(time,0,total);const clip=list.find(c=>t<c.end)||list.at(-1);return clip?{...clip,time:t,local:Math.min(clip.duration,t-clip.start),source:clip.trim+Math.min(clip.duration,t-clip.start),total}:null;}
 function ticks(total){if(!(total>0))return [0];const raw=total/5,power=10**Math.floor(Math.log10(raw)),unit=[1,2,5,10].find(n=>n*power>=raw)*power;const result=[0];for(let n=unit;n<total-Math.min(unit*.55,total*.13);n+=unit)result.push(Number(n.toFixed(6)));result.push(total);return result;}
 function waveWindow(w,offset,duration,bins=200){
  if(w?.status!=='measured'||!Array.isArray(w.peaks)||!w.peaks.length||!(w.duration>0)||!(duration>0))return null;
  return Array.from({length:bins},(_,i)=>{const from=offset+i*duration/bins,to=offset+(i+1)*duration/bins;
   if(from<0||to>w.duration+1e-8)return null;
   const a=Math.floor(from/w.duration*w.peaks.length),b=Math.max(a+1,Math.ceil(to/w.duration*w.peaks.length));
   return clamp(Math.max(...w.peaks.slice(a,b)),0,1);
  });
 }
 function auditionWindow(t,clip){const image=/\.(png|jpe?g)$/i.test(t?.asset||'');const total=safe(t?.metadata?.duration);const trim=image?0:safe(clip?.trim);return {image,trim,duration:image?safe(clip?.duration||3):Math.min(safe(clip?.duration||total),Math.max(0,total-trim))};}
 function comparisonReady(videos){return videos.every(v=>!v||(!v.error&&v.readyState>=2));}
 function comparisonPosition(windows,time){const end=Math.min(...windows.filter(w=>!w.image).map(w=>w.duration));return {duration:Number.isFinite(end)?Math.max(0,end):0,time:clamp(time,0,Number.isFinite(end)?end:0),sources:windows.map(w=>w.image?null:w.trim+clamp(time,0,end))};}
 function timecode(s){const ms=Math.round(safe(s)*1000);return `${String(Math.floor(ms/60000)).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')}.${String(ms%1000).padStart(3,'0')}`;}
 const api={ranges,locate,ticks,waveWindow,auditionWindow,comparisonPosition,comparisonReady,timecode};
 if(typeof module!=='undefined')module.exports=api;
 root.LoretuneMedia=api;
 if(typeof document==='undefined')return;
 const q=s=>document.querySelector(s),escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 let bridge,sequence,compare,posters=new Map(),posterQueue=Promise.resolve(),lastContext='',selectedPositions=new Map();
 const mediaPause=()=>document.querySelectorAll('video,audio').forEach(m=>m.pause());
 const err=(el,text)=>{el.textContent=text;el.setAttribute('role','status');};
 function stop(){sequence?.pause();compare?.pause();}
 function poster(url){
  if(posters.has(url))return posters.get(url);
  // Same local asset route and existing server rights checks. No provider URLs.
  if(!url.startsWith('/assets/'))return Promise.resolve(null);
  const work=posterQueue.then(()=>new Promise(resolve=>{
   const v=document.createElement('video');v.muted=true;v.preload='auto';let done=false;
   const finish=value=>{if(done)return;done=true;clearTimeout(timer);v.pause();v.removeAttribute('src');v.load();resolve(value);};
   const capture=()=>{try{if(!v.videoWidth)return finish(null);const c=document.createElement('canvas');c.width=240;c.height=Math.max(1,Math.round(v.videoHeight/v.videoWidth*240));c.getContext('2d').drawImage(v,0,0,c.width,c.height);finish(c.toDataURL('image/jpeg',.8));}catch{finish(null);}};
   const timer=setTimeout(()=>finish(null),8000);v.onerror=()=>finish(null);v.onloadeddata=capture;v.src=url;
  }));
  posterQueue=work.catch(()=>null);posters.set(url,work);return work;
 }
 function decoratePosters(){
  if(!bridge)return;
  const p=bridge.project();if(!p)return;
  for(const button of document.querySelectorAll('#shotlist [data-shot],#takes [data-take]')){
   const sh=button.dataset.shot?p.shots[button.dataset.shot]:p.shots[bridge.shot()];const t=sh?.takes.find(t=>t.id===Number(button.dataset.take||sh.selected));
   const holder=button.querySelector('.lt-media-kind,.lt-take-kind');if(!t||!holder||bridge.image(t)||!bridge.allowed(t))continue;
   const url=bridge.asset(t);holder.dataset.poster='pending';holder.setAttribute('aria-label','영상 첫 프레임 준비 중');
   poster(url).then(src=>{if(!holder.isConnected||!bridge.allowed(t))return;holder.dataset.poster=src?'ready':'unavailable';holder.setAttribute('aria-label',src?'영상 실제 첫 프레임':'첫 프레임을 표시할 수 없는 영상');if(src){const im=document.createElement('img');im.src=src;im.alt='';holder.replaceChildren(im);}});
  }
  const currentTake=p.shots[bridge.shot()]?.takes.find(t=>t.id===p.shots[bridge.shot()].selected);const video=q('#preview video');if(video&&currentTake&&bridge.allowed(currentTake)){const pos=selectedPositions.get(bridge.context());if(pos>0){const restore=()=>{if(video.isConnected)video.currentTime=Math.min(pos,video.duration||pos);};if(video.readyState>=1)restore();else video.addEventListener('loadedmetadata',restore,{once:true});}const url=video.getAttribute('src');poster(url||'').then(src=>{if(src&&video.isConnected&&bridge.allowed(currentTake)&&video.getAttribute('src')===url)video.poster=src;});}
 }
 function timeline(){
  if(!bridge)return;sequence?.dispose();compare?.dispose();sequence=null;compare=null;
  const p=bridge.project(),d=bridge.draft();if(!p||!d)return;
  const context=bridge.context(),list=ranges(d.clips),total=list.at(-1)?.end||0;
  const oldTime=context===lastContext?Number(q('#sequenceSeek')?.value)||0:0;lastContext=context;
  const track=q('#track');track.classList.add('time-clips');track.setAttribute('aria-label','시간 비례 장면 · 선택하면 해당 위치를 미리봅니다');
  track.innerHTML=list.map(c=>`<button type="button" data-time="${c.start}" style="width:${total?c.duration/total*100:0}%" aria-label="${escape(c.shot)} · ${timecode(c.start)}부터 ${timecode(c.end)} · ${c.duration.toFixed(3)}초" title="${escape(c.shot)} · ${c.duration.toFixed(3)}초"><b>${escape(c.shot)}</b><small>${c.duration.toFixed(2)}초</small></button>`).join('');
  let axis=q('#timeAxis');if(!axis){axis=document.createElement('div');axis.id='timeAxis';track.before(axis);axis.innerHTML='<div id="timeRuler"></div><div id="timeWave"></div><div id="timePlayhead" aria-hidden="true"></div>';axis.append(track);const note=document.createElement('p');note.id='waveNote';axis.after(note);}
  q('#timeRuler').innerHTML=ticks(total).map((t,i,all)=>`<span style="left:${total?t/total*100:0}%" data-edge="${i===0?'start':i===all.length-1?'end':'middle'}">${timecode(t)}</span>`).join('');
  const audio=p.audio_versions.find(a=>a.id===d.audio),w=waveWindow(audio?.metadata?.waveform,safe(d.audio_offset),total);
  q('#timeWave').innerHTML=w?`<svg viewBox="0 0 ${w.length} 40" preserveAspectRatio="none" role="img" aria-label="선택 음악 구간의 측정 진폭 파형">${w.map((v,i)=>v===null?'':`<path d="M${i+.5} ${20-v*19}V${20+v*19}"/>`).join('')}</svg>`:'';
  q('#waveNote').textContent=!audio?'음원 미선택 · 무음 미리보기':!w?'파형 미분석 · 음원은 재생할 수 있습니다.':w.some(x=>x===null)?'측정되지 않은 음원 구간은 비워 표시합니다. 자동 비트 분석은 아닙니다.':`음원 ${timecode(safe(d.audio_offset))}–${timecode(safe(d.audio_offset)+total)} · 실제 진폭`;
  q('#sequenceSeek').max=total;q('#sequenceSeek').value=clamp(oldTime,0,total);q('#sequencePlay').disabled=!total;
  q('#previewMode').value='selected';q('#sequenceTransport').dataset.mode='selected';q('#sequenceSeek').disabled=true;q('#sequencePlay').disabled=true;
  sequence=createSequence(p,d,clamp(oldTime,0,total));updatePlayhead(oldTime,total);decoratePosters();
 }
 function updatePlayhead(t,total){q('#timePlayhead').style.left=`${total?t/total*100:0}%`;q('#sequenceSeek').value=t;q('#sequenceTime').textContent=`${timecode(t)} / ${timecode(total)}`;}
 function createSequence(p,d,initial){
  sequence?.dispose();
  let at=initial,playing=false,raf=0,last=0,clipIndex=-1,video=null,image=null,loading=false,serial=0,disposed=false,playEpoch=0;
  const active=()=>!disposed;
  const total=ranges(d.clips).at(-1)?.end||0,a=p.audio_versions.find(a=>a.id===d.audio),audio=new Audio(a?bridge.asset(a):undefined);audio.preload='metadata';
  const label=q('#sequenceStatus'),caption=q('#sequenceCaption');
  const pause=()=>{if(!active())return;playEpoch++;playing=false;cancelAnimationFrame(raf);raf=0;audio.pause();video?.pause();q('#sequencePlay').textContent='편집 재생';};
  const detachVideo=()=>{if(video){video.pause();video.onloadedmetadata=video.onloadeddata=video.onwaiting=video.onplaying=video.onerror=null;}if(image)image.onerror=null;};
  const dispose=()=>{if(!active())return;pause();disposed=true;serial++;detachVideo();audio.onerror=null;audio.removeAttribute('src');audio.load();};
  const fail=text=>{if(!active())return;pause();err(label,text);};
  function playMedia(media,message,valid=active){const epoch=playEpoch,cut=serial;media.play().catch(()=>{if(active()&&valid()&&playing&&epoch===playEpoch&&cut===serial)fail(message);});}
  audio.onerror=()=>{if(active())fail('음원을 재생하지 못했습니다. 기존 편집은 유지됩니다. 원본 파일을 확인하세요.');};
  function alignAudio(){if(!active()||!a)return;const target=safe(d.audio_offset)+at;if(Number.isFinite(audio.duration)&&target>=audio.duration){audio.pause();return;}if(Math.abs(audio.currentTime-target)>.15)audio.currentTime=target;if(playing&&audio.paused)playMedia(audio,'음원 재생이 차단됐습니다. 재생 버튼으로 다시 시작하세요.');}
  function seek(t){
   if(!active())return;
   at=clamp(t,0,total);updatePlayhead(at,total);const c=locate(d.clips,at);if(!c)return;
   caption.textContent=(d.subtitles||[]).filter(x=>at>=x.start&&at<x.end).map(x=>x.text).join('\n');
   const take=p.shots[c.shot]?.takes.find(t=>t.id===c.take);
   if(take&&!bridge.allowed(take)){fail('이 미디어의 사용이 중지됐습니다. 사용권을 확인하세요.');return;}
   if(!take){fail(`${c.shot}에 편집할 Take가 없습니다. 원본과 승인 상태는 유지됩니다.`);return;}
   label.textContent=`재생 장면: ${c.shot} · Take ${c.take}${bridge.dirty()?' · 저장 전':d.approval?' · 승인 버전':' · 출력 승인 전'}`;
   if(clipIndex!==c.index){
    detachVideo();clipIndex=c.index;serial++;const current=serial;const box=q('#preview');box.replaceChildren();video=null;image=null;
    const live=()=>active()&&current===serial;
    if(bridge.image(take)){const img=document.createElement('img');image=img;img.src=bridge.asset(take);img.alt=c.shot;img.onerror=()=>{if(live())fail('장면 이미지를 표시할 수 없습니다. 원본 파일을 확인하세요.');};box.append(img);loading=false;}
    else{
     video=document.createElement('video');const v=video;v.muted=true;v.playsInline=true;v.preload='auto';box.append(v);loading=true;audio.pause();
     const currentVideo=()=>live()&&video===v;
     const applyPendingSeek=()=>{if(!currentVideo())return;const wanted=locate(d.clips,at);if(wanted?.index===clipIndex)v.currentTime=wanted.source;};
     v.onloadedmetadata=applyPendingSeek;
     v.onloadeddata=()=>{if(!currentVideo())return;loading=false;if(c.trim+c.duration>v.duration+.05){fail(`${c.shot}의 길이가 영상 범위를 넘습니다. 길이·시작값을 수정하세요.`);return;}applyPendingSeek();alignAudio();if(playing)playMedia(v,'영상 재생이 차단됐습니다. 재생 버튼으로 다시 시작하세요.',currentVideo);};
     v.onwaiting=()=>{if(currentVideo()){loading=true;audio.pause();}};v.onplaying=()=>{if(currentVideo())loading=false;};v.onerror=()=>{if(currentVideo()){loading=false;fail('영상을 읽지 못했습니다. 다른 장면과 편집은 유지됩니다.');}};v.src=bridge.asset(take);
     poster(bridge.asset(take)).then(src=>{if(src&&currentVideo()&&v.isConnected)v.poster=src;});
    }
   }else if(video&&!loading&&Math.abs(video.currentTime-c.source)>.1)video.currentTime=c.source;
   if(!loading)alignAudio();
  }
  function tick(now,epoch){if(!active()||!playing||epoch!==playEpoch)return;const elapsed=(now-last)/1000;last=now;if(!loading){const c=locate(d.clips,at);const audioActive=a&&(!Number.isFinite(audio.duration)||safe(d.audio_offset)+at<audio.duration);const next=audioActive?(audio.paused||audio.readyState<3?at:Math.max(at,audio.currentTime-safe(d.audio_offset))):video?(video.paused?at:c.start+Math.max(0,video.currentTime-c.trim)):at+Math.min(elapsed,.1);seek(next);if(at>=total){pause();return;}}if(active()&&playing&&epoch===playEpoch)raf=requestAnimationFrame(now=>tick(now,epoch));}
  function play(){if(!active())return;if(playing){pause();return;}compare?.pause();mediaPause();if(at>=total)at=0;const epoch=++playEpoch;playing=true;q('#sequencePlay').textContent='일시 정지';seek(at);if(!playing)return;if(video&&!loading)playMedia(video,'영상 재생이 차단됐습니다.');alignAudio();last=performance.now();raf=requestAnimationFrame(now=>tick(now,epoch));}
  return sequence={pause,dispose,play,seek,get time(){return at;}};
 }
 function comparison(){
  sequence?.pause();compare?.dispose();compare=null;mediaPause();if(!bridge)return;
  const p=bridge.project(),sh=p?.shots[bridge.shot()],d=bridge.draft();if(!sh)return;
  const selected=['Left','Right'].map(side=>sh.takes.find(t=>t.id===Number(q('#compare'+side).value)));
  if(selected.some(t=>!t))return;
  if(selected.some(t=>!bridge.allowed(t))){q('#compareTogether').disabled=true;err(q('#compareSyncStatus'),'사용이 중지된 미디어는 비교 재생할 수 없습니다.');return;}
  const windows=selected.map(t=>auditionWindow(t,d?.clips.find(c=>c.shot===bridge.shot()&&c.take===t.id)));
  for(const [i,side] of ['Left','Right'].entries()){const facts=q('#compare'+side+'Preview .creator-comparison-facts'),note=document.createElement('p');note.className='comparison-window';note.textContent=windows[i].image?'정지 이미지':`비교 원본 시작 ${timecode(windows[i].trim)} · 사용 구간 ${timecode(windows[i].duration)}`;facts?.querySelector('.comparison-window')?.remove();facts?.append(note);}
  const position=comparisonPosition(windows,0),videos=['Left','Right'].map(s=>q('#compare'+s+'Preview video'));
  const total=position.duration;let playing=false,raf=0,last=0,at=0,disposed=false,playEpoch=0;
  const active=()=>!disposed;
  const label=q('#compareSyncStatus');q('#compareSeek').max=total;q('#compareSeek').value=0;q('#compareTogether').disabled=!total;
  label.textContent=total?`공통 재생 구간 ${timecode(total)} · 각 Take의 편집 시작점 기준 · 무음 비교`:'정지 이미지 비교 · 함께 재생할 영상이 없습니다.';
  const pause=()=>{if(!active())return;playEpoch++;playing=false;cancelAnimationFrame(raf);raf=0;videos.forEach(v=>v?.pause());q('#compareTogether').textContent='함께 재생';};
  const dispose=()=>{if(!active())return;pause();disposed=true;videos.forEach(v=>{if(v)v.onloadeddata=v.oncanplay=v.onseeked=v.onerror=null;});};
  function seek(t){if(!active())return;at=clamp(t,0,total);const pos=comparisonPosition(windows,at);videos.forEach((v,i)=>{if(v&&v.readyState>=1)v.currentTime=pos.sources[i];});q('#compareSeek').value=at;q('#compareTime').textContent=`${timecode(at)} / ${timecode(total)}`;}
  function fail(){if(!active())return;pause();err(label,'비교 영상을 읽지 못했습니다. 선택·승인·편집은 바뀌지 않았습니다.');}
  videos.forEach((v,i)=>{if(!v)return;v.muted=true;v.playsInline=true;v.controls=false;v.onloadeddata=()=>{if(active())seek(at);};v.oncanplay=()=>{if(active())q('#compareTogether').disabled=!total||!comparisonReady(videos);};v.onseeked=v.oncanplay;v.onerror=()=>{if(active())fail();};poster(bridge.asset(selected[i])).then(src=>{if(src&&active()&&v.isConnected)v.poster=src;});});
  function tick(now,epoch){if(!active()||!playing||epoch!==playEpoch)return;const waiting=videos.some(v=>v&&v.readyState<3);if(waiting){videos.forEach(v=>v?.pause());last=now;raf=requestAnimationFrame(now=>tick(now,epoch));return;}at=clamp(at+(now-last)/1000,0,total);last=now;
   videos.forEach((v,i)=>{if(!v)return;const target=windows[i].trim+at;if(Math.abs(v.currentTime-target)>.08)v.currentTime=target;if(v.paused&&at<total)v.play().catch(()=>{if(active()&&playing&&epoch===playEpoch)fail();});});
   q('#compareSeek').value=at;q('#compareTime').textContent=`${timecode(at)} / ${timecode(total)}`;if(at>=total){seek(total);pause();return;}if(active()&&playing&&epoch===playEpoch)raf=requestAnimationFrame(now=>tick(now,epoch));
  }
  async function play(){if(!active())return;if(playing)return pause();if(!comparisonReady(videos))return err(label,'비교 영상이 준비 중입니다. 준비 후 함께 재생하세요.');sequence?.pause();mediaPause();if(at>=total)seek(0);label.textContent=`공통 재생 구간 ${timecode(total)} · 각 Take의 편집 시작점 기준 · 무음 비교`;const epoch=++playEpoch;playing=true;try{await Promise.all(videos.filter(Boolean).map(v=>v.play()));}catch{if(active()&&playing&&epoch===playEpoch)fail();return;}if(!active()||!playing||epoch!==playEpoch)return;last=performance.now();q('#compareTogether').textContent='함께 일시 정지';raf=requestAnimationFrame(now=>tick(now,epoch));}
  compare={pause,dispose,play,seek};seek(0);
 }
 function setup(b){
  bridge=b;
  const transport=document.createElement('div');transport.id='sequenceTransport';transport.innerHTML='<label class="preview-mode-label">미리보기 <select id="previewMode"><option value="selected">선택한 Take</option><option value="sequence">편집 순서 + 음악</option></select></label><div class="sequence-controls"><button id="sequencePlay" type="button" disabled>편집 재생</button><output id="sequenceTime" class="lt-timecode"></output></div><label class="sr-only" for="sequenceSeek">편집 미리보기 위치</label><input id="sequenceSeek" type="range" min="0" max="0" step="0.001" value="0" disabled><p id="sequenceStatus" role="status">선택한 원본 Take를 확인합니다. 선택·승인은 별도입니다.</p><div id="sequenceCaption" aria-label="편집 자막 미리보기"></div>';
  q('#preview').after(transport);
  q('#previewMode').onchange=e=>{stop();q('#sequenceTransport').dataset.mode=e.target.value;if(e.target.value==='selected'){bridge.redraw();return;}const native=q('#preview video');if(native)selectedPositions.set(bridge.context(),native.currentTime);q('#sequenceSeek').disabled=false;q('#sequencePlay').disabled=false;sequence?.seek(Number(q('#sequenceSeek').value));};
  q('#sequencePlay').onclick=()=>sequence?.play();q('#sequenceSeek').oninput=e=>{sequence?.pause();sequence?.seek(e.target.value);};
  q('#track').addEventListener('click',e=>{const button=e.target.closest('[data-time]');if(!button)return;if(q('#previewMode').value==='selected'){const native=q('#preview video');if(native)selectedPositions.set(bridge.context(),native.currentTime);}q('#previewMode').value='sequence';q('#sequenceTransport').dataset.mode='sequence';q('#sequenceSeek').disabled=false;q('#sequencePlay').disabled=false;sequence?.pause();sequence?.seek(Number(button.dataset.time));});
  const controls=document.createElement('div');controls.id='comparisonTransport';controls.innerHTML='<button id="compareTogether" type="button">함께 재생</button><output id="compareTime" class="lt-timecode"></output><label class="sr-only" for="compareSeek">Take 공통 재생 위치</label><input id="compareSeek" type="range" min="0" max="0" step="0.001"><p id="compareSyncStatus" role="status"></p>';
  q('#compareHelp').after(controls);q('#compareTogether').onclick=()=>compare?.play();q('#compareSeek').oninput=e=>{compare?.pause();compare?.seek(e.target.value);};
  const closeCompare=()=>{compare?.dispose();compare=null;};q('#compareDialog').addEventListener('close',closeCompare);q('#compareDialog').addEventListener('cancel',closeCompare);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});window.addEventListener('pagehide',stop);
  // Preserve review nodes/drafts: mobile moves the existing player, never clones it.
  const mobile=matchMedia('(max-width:900px)'),anchor=document.createComment('player-home');q('#preview').before(anchor);
  const dock=document.createElement('details');dock.id='mobileReviewPreview';dock.open=true;const summary=document.createElement('summary');summary.textContent='선택한 Take 미리보기';dock.append(summary);q('.inspector').prepend(dock);
  const move=()=>{const review=q('[data-panel="review"]')?.getAttribute('aria-selected')==='true';dock.dataset.active=String(mobile.matches&&review);if(mobile.matches&&review){if(q('#previewMode').value==='sequence'){stop();bridge.redraw();}dock.append(q('#preview'),transport);}else{anchor.after(q('#preview'));q('#preview').after(transport);}};
  new MutationObserver(move).observe(q('.lt-panel-nav'),{subtree:true,attributes:true,attributeFilter:['aria-selected']});mobile.addEventListener('change',move);move();timeline();
 }
 Object.assign(api,{setup,timeline,comparison,stop,decoratePosters});
})(typeof globalThis!=='undefined'?globalThis:this);
