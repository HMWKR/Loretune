const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('index.html','utf8');
function block(start,end){const i=source.indexOf(start),j=source.indexOf(end,i+start.length);assert(i>=0&&j>i,start);return source.slice(i,j)}
const helpers=block('/* Timeline motion overlays:', '/* End timeline motion overlays. */');
const handlers=block("$('#clips').onchange=", "$('#clips').onclick=");
const save=block("$('#saveTimeline').onclick=", "$('#restore').onclick=");
const frameHandlers=block("$('#timelineFrameView').onclick=", '/* Creator proposal views:');
const clone=value=>JSON.parse(JSON.stringify(value));

function fixture(){
 const nodeMap=new Map(),queries=new Map(),messages=[],calls=[],requests=[],images=[],revoked=[];let draws=0,previews=0;
 function node(selector){if(nodeMap.has(selector))return nodeMap.get(selector);const n={value:'',dataset:{},hidden:true,disabled:false,max:'',textContent:'',options:[],focusCount:0,open:false,focus(){this.focusCount++},querySelector(){return node('#source-focus')}};let html='';Object.defineProperty(n,'innerHTML',{get:()=>html,set:v=>{html=v;n.options=[...v.matchAll(/<option value="([^"]*)"/g)].map(m=>({value:m[1]}));if(!n.options.some(x=>x.value===n.value))n.value=n.options[0]?.value||''}});nodeMap.set(selector,n);return n}
 const approved=(id,frames=72,grant='private-grant')=>({id,scene_hash:'scene-'+id,scene:{frame_count:frames,layers:[{kind:'text',text:'한글 <타이포> '+id}]},approval:{id:grant,actor:'local-owner',scope:'local-motion-candidate',scene_hash:'scene-'+id}});
 const p={timeline_head:5,active_conversation:{id:'conversation-A'},shots:{background:{selected:1,takes:[{id:1}]},'타이포 원본':{motion_head:2,motion_versions:[approved(1),approved(2,96,null),{...approved(3),approval:null},{...approved(4),approval:{actor:'remote',scope:'local-motion-candidate',scene_hash:'scene-4'}}]}},timeline_versions:[]};
 const timeline={id:5,clips:[{shot:'background',take:1,duration:3,trim:0}],subtitles:[],audio:1,audio_offset:0,profile:'landscape'};p.timeline_versions=[clone(timeline)];
 const c={state:{workspace_id:'workspace'},draft:clone(timeline),dirty:false,busy:false,p,project:()=>p,song:()=> '음원 제작',structuredClone,Number,JSON,Object,Array,Math,String,Set,AbortController,setTimeout,clearTimeout,URL:{createObjectURL:()=> 'blob:frame-'+images.length,revokeObjectURL:url=>revoked.push(url)},URLSearchParams,$:node,esc:s=>String(s??'').replace(/[&<>"']/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[k])),message:(text,error)=>messages.push({text,error}),act:(action,data)=>calls.push({action,data:clone(data)}),drawTimeline:()=>draws++,updateClipPreview:()=>previews++,document:{querySelectorAll:selector=>queries.get(selector)||[]},fetch:async(url,options)=>{requests.push({url,options});return {ok:true,blob:async()=>({type:'image/png'})}},Image:class{set src(value){this._src=value;images.push(this)}get src(){return this._src}}};
 vm.createContext(c);vm.runInContext(helpers,c);vm.runInContext(handlers,c);vm.runInContext(save,c);vm.runInContext(frameHandlers,c);
 return {c,p,node,queries,messages,calls,requests,images,revoked,draws:()=>draws,previews:()=>previews,sourceValue:JSON.stringify(['타이포 원본',1])};
}

function placement(f){assert.equal(f.c.changeTimelineOverlaySource(0,f.sourceValue),true);return f.c.draft.clips[0].motion_overlay}
async function run(){let checks=0;async function test(name,fn){await fn();checks++;console.log('PASS '+name)}
 await test('approved immutable sources include hidden-grant versions without leaking grant IDs',()=>{
  const f=fixture(),before=clone(f.p),choices=clone(f.c.timelineMotionSources(f.p));assert.deepEqual(choices.map(x=>x.revision),[1,2]);assert(!JSON.stringify(choices).includes('private-grant'));assert.deepEqual(f.p,before);
  const overlay=placement(f);assert.deepEqual(clone(overlay),{start:0,end:3,offset_x:0,offset_y:0,shot:'타이포 원본',motion_revision:1});
  const html=f.c.timelineOverlayMarkup(f.p,f.c.draft.clips[0],0);assert.match(html,/한글 &lt;타이포&gt;/);assert(!html.includes('private-grant'));assert.match(html,/data-overlay-field="start"/);assert.match(html,/data-overlay-field="offset_y"/);
 });
 await test('source version changes preserve timing and offsets; explicit clear restores absent-field contract',()=>{
  const f=fixture(),before=clone(f.c.draft);const o=placement(f);Object.assign(o,{start:.5,end:2.5,offset_x:123,offset_y:-90});
  assert.equal(f.c.changeTimelineOverlaySource(0,JSON.stringify(['타이포 원본',2])),true);assert.deepEqual(clone(f.c.draft.clips[0].motion_overlay),{start:.5,end:2.5,offset_x:123,offset_y:-90,shot:'타이포 원본',motion_revision:2});
  assert.equal(f.c.changeTimelineOverlaySource(0,'["foreign",1]'),false);assert.equal(f.c.draft.clips[0].motion_overlay.motion_revision,2);
  f.c.changeTimelineOverlaySource(0,'');assert(!Object.hasOwn(f.c.draft.clips[0],'motion_overlay'));assert.deepEqual(clone(f.c.draft),before);
 });
 await test('invalid duration, source, blank values and offset ranges are explained without clamping',()=>{
  const f=fixture(),o=placement(f),clip=f.c.draft.clips[0];assert.equal(f.c.timelineOverlayIssue(f.p,clip),'');
  o.start=null;assert.match(f.c.timelineOverlayIssue(f.p,clip),/모두 입력/);o.start=0;o.end=4;assert.match(f.c.timelineOverlayIssue(f.p,clip),/이 컷/);assert.equal(o.end,4);
  clip.duration=5;assert.match(f.c.timelineOverlayIssue(f.p,clip),/원본 3초/);o.end=3;o.offset_y=1081;assert.match(f.c.timelineOverlayIssue(f.p,clip),/세로 이동/);o.offset_y=0;o.motion_revision=999;assert.match(f.c.timelineOverlayIssue(f.p,clip),/찾을 수 없습니다/);
 });
 await test('numeric editing sets dirty and preserves source and focused control without redraw',()=>{
  const f=fixture();placement(f);const saved=clone(f.p.shots);const input={dataset:{overlayClip:'0',overlayField:'offset_x'},value:'350'};
  f.node('#clips').oninput({target:input});assert.equal(f.c.draft.clips[0].motion_overlay.offset_x,350);assert.equal(f.c.dirty,true);assert.equal(f.draws(),0);assert.equal(f.previews(),1);assert.equal(input.value,'350');assert.deepEqual(f.p.shots,saved);
 });
 await test('save reads current unblurred overlay fields and preserves original source versions',()=>{
  const f=fixture();placement(f);const before=clone(f.p.shots);f.queries.set('[data-overlay-clip][data-overlay-field]',[{dataset:{overlayClip:'0',overlayField:'offset_x'},value:'620'},{dataset:{overlayClip:'0',overlayField:'start'},value:'0.25'},{dataset:{overlayClip:'0',overlayField:'end'},value:'2.5'}]);
  f.node('#saveTimeline').onclick();assert.equal(f.calls.length,1);assert.equal(f.calls[0].action,'timeline');assert.equal(f.calls[0].data.timeline.clips[0].motion_overlay.offset_x,620);assert.equal(f.calls[0].data.timeline.clips[0].motion_overlay.start,.25);assert.deepEqual(f.p.shots,before);
 });
 await test('invalid save keeps input and source while withholding the mutation',()=>{
  const f=fixture();placement(f);const input={dataset:{overlayClip:'0',overlayField:'offset_y'},value:''};f.queries.set('[data-overlay-clip][data-overlay-field]',[input]);
  f.node('#saveTimeline').onclick();assert.equal(f.calls.length,0);assert.equal(f.messages.length,1);assert.match(f.messages[0].text,/모두 입력/);assert.equal(input.value,'');assert.equal(f.c.draft.clips[0].motion_overlay.offset_y,null);assert.equal(f.node('#source-focus').focusCount,1);
 });
 await test('actual saved-frame request includes exact version, clip, frame and conversation',async()=>{
  const f=fixture();f.c.updateTimelineFrameControls();f.node('#timelineFrameTime').value='0.5';await f.c.showTimelineFrame();assert.equal(f.requests.length,1);const q=new URL(f.requests[0].url,'http://localhost');assert.equal(q.pathname,'/api/timeline-frame');assert.equal(q.searchParams.get('timeline_revision'),'5');assert.equal(q.searchParams.get('clip_index'),'0');assert.equal(q.searchParams.get('frame'),'12');assert.equal(q.searchParams.get('conversation'),'conversation-A');assert.equal(f.calls.length,0);assert.equal(f.images.length,1);f.images[0].onload();assert.equal(f.node('#timelineFrameImage').hidden,false);assert.match(f.node('#timelineFrameStatus').textContent,/0\.500초/);assert.match(f.node('#timelineFrameStatus').textContent,/출력 승인은 별도/);
 });
 await test('unsaved draft cannot request a misleading saved-frame preview',async()=>{
  const f=fixture();f.c.dirty=true;await f.c.showTimelineFrame();assert.equal(f.requests.length,0);assert.equal(f.node('#timelineFrameView').disabled,true);assert.match(f.node('#timelineFrameStatus').textContent,/먼저 저장/);
 });
 await test('late network response cannot replace preview after a draft edit',async()=>{
  const f=fixture();let release;f.c.fetch=url=>{f.requests.push({url});return new Promise(resolve=>release=resolve)};f.c.updateTimelineFrameControls();f.node('#timelineFrameTime').value='0.5';const pending=f.c.showTimelineFrame();f.c.dirty=true;f.c.draft.clips[0].duration=2;f.c.updateTimelineFrameControls();release({ok:true,blob:async()=>({type:'image/png'})});await pending;assert.equal(f.images.length,0);assert.equal(f.node('#timelineFrameImage').hidden,true);assert.match(f.node('#timelineFrameStatus').textContent,/먼저 저장/);
 });
 await test('late decoded image cannot cross conversation or requested-time boundaries',async()=>{
  const f=fixture();f.c.updateTimelineFrameControls();f.node('#timelineFrameTime').value='0.5';await f.c.showTimelineFrame();assert.equal(f.images.length,1);f.p.active_conversation.id='conversation-B';f.c.updateTimelineFrameControls();f.images[0].onload();assert.equal(f.node('#timelineFrameImage').hidden,true);assert.equal(f.revoked.length,1);
  const g=fixture();g.c.updateTimelineFrameControls();g.node('#timelineFrameTime').value='0.5';await g.c.showTimelineFrame();g.node('#timelineFrameTime').value='1';g.node('#timelineFrameTime').oninput();g.images[0].onload();assert.equal(g.node('#timelineFrameImage').hidden,true);assert.equal(g.revoked.length,1);
 });
 await test('server preview rejection preserves editing inputs and exposes recovery message',async()=>{
  const f=fixture();f.c.fetch=async()=>({ok:false,json:async()=>({error:'저장 버전이 변경됐습니다. 다시 확인하세요.'})});f.c.updateTimelineFrameControls();f.node('#timelineFrameTime').value='1';await f.c.showTimelineFrame();assert.match(f.node('#timelineFrameStatus').textContent,/저장 버전이 변경/);assert.equal(f.node('#timelineFrameTime').value,'1');assert.equal(f.images.length,0);assert.equal(f.calls.length,0);assert.equal(f.node('#timelineFrameView').disabled,false);
 });
 await test('saved-frame range rejects empty and out-of-clip time without a request',async()=>{
  const f=fixture();f.c.updateTimelineFrameControls();for(const value of ['', '-1', '3']){f.node('#timelineFrameTime').value=value;await f.c.showTimelineFrame()}assert.equal(f.requests.length,0);assert.equal(f.node('#timelineFrameTime').focusCount,3);
 });
 await test('fractional final cut permits its last preserved media and caption-tail frame',async()=>{
  const f=fixture();f.p.timeline_versions[0].clips[0].duration=.130;f.p.timeline_versions[0].subtitles=[{start:.125,end:.130,text:'마지막 음절'}];f.c.draft=clone(f.p.timeline_versions[0]);const before=clone(f.c.draft);f.c.updateTimelineFrameControls();assert.equal(Number(f.node('#timelineFrameTime').max),.125);f.node('#timelineFrameTime').value='0.125';await f.c.showTimelineFrame();assert.equal(f.requests.length,1);assert.equal(new URL(f.requests[0].url,'http://localhost').searchParams.get('frame'),'3');assert.deepEqual(clone(f.c.draft),before);
 });
 await test('cumulative cut boundaries give each saved clip its actual frame range',()=>{
  const f=fixture();const clips=[.130,.200,.130].map(duration=>({shot:'background',take:1,duration,trim:0}));f.p.timeline_versions[0].clips=clips;f.c.draft=clone(f.p.timeline_versions[0]);f.c.updateTimelineFrameControls();const expected=[2/24,4/24,3/24];for(let i=0;i<clips.length;i++){f.node('#timelineFrameClip').value=String(i);f.c.updateTimelineFrameControls();assert.equal(Number(f.node('#timelineFrameTime').max),expected[i]);}
  const whole=fixture();whole.c.updateTimelineFrameControls();assert.equal(Number(whole.node('#timelineFrameTime').max),71/24);
 });
 await test('central frame view opens only for the current decoded PNG and hides on return/invalidation',async()=>{
  const f=fixture(),shown=[],hidden=[];f.c.LoretuneMedia={showSavedFrame:label=>shown.push(label),hideSavedFrame:()=>hidden.push(true)};
  f.c.updateTimelineFrameControls();f.node('#timelineFrameTime').value='0.5';await f.c.showTimelineFrame();assert.equal(shown.length,0,'HTTP response alone is not rendered success');f.images[0].onload();assert.equal(shown.length,1);assert.match(shown[0],/저장 버전 5.*1번 컷 0\.500초/);f.c.invalidateTimelineFrame();assert.equal(f.node('#timelineFrameImage').hidden,true);assert.ok(hidden.length>0);f.images[0].onload();assert.equal(shown.length,1,'late callback after user return cannot reopen the canvas');
  const g=fixture(),late=[];g.c.LoretuneMedia={showSavedFrame:label=>late.push(label),hideSavedFrame:()=>{}};g.c.updateTimelineFrameControls();g.node('#timelineFrameTime').value='1';await g.c.showTimelineFrame();g.p.timeline_head=6;g.c.updateTimelineFrameControls();g.images[0].onload();assert.equal(late.length,0,'stale saved version cannot open the canvas');
  const h=fixture(),failed=[];h.c.LoretuneMedia={showSavedFrame:label=>failed.push(label),hideSavedFrame:()=>{}};h.c.updateTimelineFrameControls();h.node('#timelineFrameTime').value='1';await h.c.showTimelineFrame();h.images[0].onerror();assert.equal(failed.length,0);assert.match(h.node('#timelineFrameStatus').textContent,/읽지 못/);assert.equal(h.calls.length,0);
 });
 console.log(`Timeline motion overlay: ${checks} contract/state/race checks passed (synthetic DOM/network; real browser and rendering verified separately).`);
}
run().catch(error=>{console.error(error);process.exitCode=1});
