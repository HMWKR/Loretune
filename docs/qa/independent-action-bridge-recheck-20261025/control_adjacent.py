from helpers import *
import math,struct,wave,random
import editing,renderer
R=[]
def check(name,ok,**e):
 R.append(dict(case=name,status='pass' if ok else 'fail',**e));print(json.dumps(R[-1],ensure_ascii=False))
def budget(st,jid):
 j=st.generation.get(jid)
 with st.connect() as c:
  row=c.execute('SELECT state,amount,actual FROM reservations WHERE id=?',(j['reservation'],)).fetchone()
  events=[x[0] for x in c.execute('SELECT kind FROM ledger_events WHERE reservation=?',(j['reservation'],))]
 return dict(state=row[0],amount=row[1],actual=row[2],events=events)

for mode in ['revoke-restore','unknown-revoke','accepted-revoke','cancel-before-submit','legacy-prepared']:
 with tempfile.TemporaryDirectory(dir=ROOT) as f:
  st,call,jid,fake,sha,prep_id=prepared(f);gate=deepcopy(st.generation_approval)
  if mode=='revoke-restore':
   st.generation_approval=None;st.process_generation();first=budget(st,jid)
   st.generation_approval=gate;st.process_generation()
   check(mode,len(fake.calls)==0 and first['state']=='cancelled' and st.generation.get(jid)['state']=='submission_blocked',submits=len(fake.calls),budget=budget(st,jid),job=st.generation.get(jid)['state'])
  elif mode=='unknown-revoke':
   # Same bound adapter instance loses receipt; do not bypass binding with a new adapter.
   def timeout(data):fake.calls.append(deepcopy(data));raise TimeoutError('synthetic accepted but receipt lost')
   fake.submit=timeout;st.process_generation();st.generation_approval=None
   call('asset_rights',sha256=sha,blocked=True,reason='after unknown submit')
   st.process_generation();st.generation.recover();st.generation_approval=gate;st.process_generation();b=budget(st,jid)
   check(mode,len(fake.calls)==1 and b['state']=='uncertain' and 'released' not in b['events'],submits=len(fake.calls),budget=b,job=st.generation.get(jid)['state'])
  elif mode=='accepted-revoke':
   st.process_generation();st.generation_approval=None;call('asset_rights',sha256=sha,blocked=True,reason='after accepted')
   st.process_generation();b=budget(st,jid)
   check(mode,len(fake.calls)==1 and b['state']=='reserved' and 'released' not in b['events'],budget=b)
  elif mode=='cancel-before-submit':
   call('cancel_generation',song='synthetic',job=jid,reason='cancel before submission');st.process_generation();b=budget(st,jid)
   check(mode,len(fake.calls)==0 and b['state']=='cancelled' and 'refunded' not in b['events'],budget=b)
  else:
   # Simulate persisted pre-migration job: remove only the newly introduced binding.
   with st.connect() as c:
    j=st.generation.get(jid);j['context'].pop('submission_binding');st.generation.save(c,j)
   st.process_generation();b=budget(st,jid)
   check(mode,len(fake.calls)==0 and st.generation.get(jid)['state']=='submission_blocked',budget=b)

# Explicit fresh request after a no-submit block: budget was returned, old record stays immutable.
with tempfile.TemporaryDirectory(dir=ROOT) as f:
 st,call,jid,fake,sha,prep_id=prepared(f);gate=deepcopy(st.generation_approval)
 st.generation_approval=None;st.process_generation();st.generation_approval=gate
 shot=st.state()['projects']['synthetic']['shots']['one']
 newprep=call('prepare_generation',song='synthetic',shot='one',shot_revision=shot['revision'],prompt='synthetic')['preparation']
 try:
  newjob=call('start_generation',song='synthetic',shot='one',preparation=newprep)['job'];st.process_generation();outcome='admitted';error=None
 except ValueError as e:outcome='blocked';error=str(e)
 check('fresh-action-after-unsent-release',outcome=='admitted' and len(fake.calls)==1,outcome=outcome,error=error,actual_submits=len(fake.calls),old_budget=budget(st,jid),note='Restored exact gate; fresh explicit preparation, not replay of blocked action')

# New graph versions; independent provenance/deletion cases retain exact historic snapshots.
with tempfile.TemporaryDirectory(dir=ROOT) as f:
 st,_=fixture(f)
 def ent(k):return dict(id=ontology.stable_id('audit','character',k),type='character',label=k,description=k,provenance=[dict(source_id='doc1',excerpt=k)],uncertainty=dict(status='asserted',reason='synthetic'))
 a,b,c=ent('A'),ent('B'),ent('C')
 rel=dict(id=str(uuid.uuid4()),type='derived_from',source=a['id'],target=b['id'],provenance=a['provenance'])
 graph=dict(entities=[a,b,c],relations=[rel]);bound={'revision':0}
 with st.connect() as db:
  pid=ontology.propose(db,'audit',graph,0,'human')['id'];original=ontology.apply(db,'audit',pid,0,'human',True)
  project_ontology.bind(bound,original,[a['id']]);pinned=deepcopy(bound)
  modified=deepcopy(graph);modified['relations'][0]['provenance']=[dict(source_id='doc2',excerpt='correction')]
  pid=ontology.propose(db,'audit',modified,1,'human')['id'];new=ontology.apply(db,'audit',pid,1,'human',True)
  check('relation-provenance-change',bool(project_ontology.impact(bound,new)) and bound==pinned)
  modified['relations']=[];pid=ontology.propose(db,'audit',modified,2,'human')['id'];deleted=ontology.apply(db,'audit',pid,2,'human',True)
  historical=json.loads(db.execute('SELECT body FROM ontology_versions WHERE scope=? AND revision=1',('audit',)).fetchone()[0])
  check('relation-delete-historic-preservation',bool(project_ontology.impact(bound,deleted)) and historical==graph and bound==pinned)
  restored=ontology.rollback(db,'audit',1,3,'human',True)
  check('relation-restore-new-revision',restored['revision']==4 and not project_ontology.impact(bound,restored) and bound==pinned)
  unrelated=deepcopy(restored);unrelated['graph']['entities'][2]['description']='unrelated change'
  check('unrelated-entity-no-invalidation',project_ontology.impact(bound,unrelated)==[])

rng=random.Random(20261025);maxerr=0;count=0
for _ in range(500):
 ds=[rng.randint(125,9000)/1000 for _ in range(rng.randint(1,30))];timing=editing.frame_timing(ds);total=0
 for index,(d,clip) in enumerate(zip(ds,timing['clips'])):
  total+=d;count+=1
  if index<len(ds)-1:maxerr=max(maxerr,abs(total-clip['end']))
  else:assert -1e-10<=clip['end']-total<1/24+1e-10
  assert clip['frames']>=3
check('quantization-500-sequences-internal-half-frame-final-ceil',maxerr<=1/48+1e-10,boundaries=count,max_error_seconds=maxerr)

# Real media with a click near the end and Korean caption beyond a rounded-down video boundary.
media=ROOT/'media';media.mkdir(exist_ok=True)
image=media/'synthetic.png'
subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=blue:s=32x32','-frames:v','1',str(image)],check=True)
rate=48000;audio=media/'clicks.wav'
with wave.open(str(audio),'wb') as w:
 w.setparams((1,2,rate,0,'NONE','not compressed'))
 w.writeframes(b''.join(struct.pack('<h',int(20000*math.sin(2*math.pi*1000*i/rate)) if any(t<=i/rate<t+.005 for t in [.25,1.25,3.925]) else 0) for i in range(rate*4)))
for duration in [.130,.131]:
 total=round(duration*30,3);laststart=3.88 if duration==.130 else 3.92;lastend=3.89 if duration==.130 else 3.93
 p=dict(profile='preview',shots={str(i):dict(selected=1,duration=duration,takes=[dict(id=1,asset=str(image))]) for i in range(30)},audio={'asset':str(audio)},audio_offset=0,subtitles=[dict(start=.2,end=.4,text='첫 박자'),dict(start=laststart,end=lastend,text='끝 자막')])
 out=media/f'fractional-{duration:.3f}.mp4';renderer.render(p,out);verified=renderer.verify_output(out,p)
 subtitle=subprocess.check_output(['ffmpeg','-v','error','-i',str(out),'-map','0:s:0','-f','srt','-']).decode()
 pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(out),'-map','0:a:0','-ac','1','-ar',str(rate),'-f','s16le','-'])
 samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
 onsets=[]
 for expected in [.25,1.25]:
  start=int((expected-.04)*rate);window=samples[start:int((expected+.04)*rate)]
  first=next(i for i,x in enumerate(window) if abs(x)>5000);onsets.append((start+first)/rate)
 check(f'audio-early-sync-{duration}',all(abs(a-b)<.002 for a,b in zip(onsets,[.25,1.25])),onsets=onsets)
 check(f'caption-tail-{duration}', '끝 자막' in subtitle,requested_duration=total,verified=verified,subtitle=subtitle,sha256=hashlib.sha256(out.read_bytes()).hexdigest())
 if duration==.131:
  tail=samples[int(3.92*rate):int(3.94*rate)]
  check('audio-tail-preservation-rounded-down',bool(tail) and max(map(abs,tail))>5000,tail_peak=max(map(abs,tail),default=0),requested_event_seconds=3.925,video_end=verified['frame_timing']['duration'])
(ROOT/'adjacent-results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
