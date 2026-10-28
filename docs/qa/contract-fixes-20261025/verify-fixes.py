"""Independent synthetic counterexamples; snapshot imports only; all network denied."""
import sys, tempfile, json, time, uuid, base64, subprocess, hashlib, socket
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parent
tempfile.tempdir=str(ROOT)
sys.path.insert(0,str(ROOT.parents[2]))
# Reject accidental outbound access, including localhost: this audit needs no server.
def deny(*a,**k):raise AssertionError('Network prohibited by independent audit')
socket.socket.connect=deny;socket.create_connection=deny
import app, ledger, fal_provider as fal, ontology, project_ontology
RESULTS=[]
def record(id,**data):RESULTS.append(dict(id=id,**data));print(json.dumps(RESULTS[-1],ensure_ascii=False))
def fixture(folder):
 st=app.Store(folder)
 def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 return st,call
class Fake:
 def __init__(self):self.calls=[]
 def submit(self,data):self.calls.append(deepcopy(data));return {'request_id':'synthetic-request'}
 def status(self,receipt):return {'state':'COMPLETED','result_ready':True}
 def result(self,receipt):return {'url':'https://v3b.fal.media/synthetic-only'}

def queue_fixture(folder):
 st,call=fixture(folder)
 with st.connect() as c:ledger.patch_budget(c,st.workspace_id,'fixture',dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
 j=st.generation.admit('fixture',fal.payload('synthetic',b'\x89PNG\r\n\x1a\nfixture'),dict(fal.estimate(),budget_revision=1),{'song':'synthetic','shot':'one'},'synthetic',approved=True)
 return st,j

# End-to-end admission via Store, then normal asset-rights revocation before worker.
with tempfile.TemporaryDirectory(prefix='independent-contract-',dir=ROOT) as folder:
 st,call=fixture(folder);image=Path(folder)/'synthetic.png'
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=32x32','-frames:v','1',str(image)],check=True)
 call('project',name='synthetic',era='default',story=0)
 call('shot',song='synthetic',shot='one',description='synthetic')
 call('take',song='synthetic',shot='one',shot_revision=0,filename='synthetic.png',content=base64.b64encode(image.read_bytes()).decode(),reason='audit fixture',rights='synthetic owned')
 def shot():return st.state()['projects']['synthetic']['shots']['one']
 call('assign_reference',song='synthetic',shot='one',shot_revision=shot()['revision'],source_song='synthetic',source_shot='one',source_take=1,role='start_frame',reason='audit')
 call('review_reference',song='synthetic',shot='one',shot_revision=shot()['revision'],version=1,decision='approved',reason='audit')
 prep_id=call('prepare_generation',song='synthetic',shot='one',shot_revision=shot()['revision'],prompt='synthetic')['preparation']
 prep=shot()['generation_preparations'][0];sha=prep['source']['sha256']
 gate=dict(model=fal.MODEL,workspace_id=st.workspace_id,song='synthetic',shot='one',image_sha256=sha,prompt_sha256=hashlib.sha256(b'synthetic').hexdigest(),privacy='private',retention_seconds=3600,duration=10,generate_audio=False,price_money={'amount':'0.70','currency':'USD'},price_checked_at=time.time(),maximum_calls=1,maximum_units=700000,expires=time.time()+300)
 st.generation_approval=gate;fake=Fake();st.provider_adapter=fake
 scope='project:'+app.contracts.project_id(st.workspace_id,'synthetic')
 with st.connect() as c:ledger.patch_budget(c,st.workspace_id,scope,dict(limit={'amount':'0.70','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
 jid=call('start_generation',song='synthetic',shot='one',preparation=prep_id)['job']
 call('asset_rights',sha256=sha,blocked=True,reason='audit revoke before submit')
 st.process_generation()
 record('F01',expected='zero provider submits after input rights revoke',actual_submits=len(fake.calls),job_state=st.generation.get(jid)['state'],rights_blocked=st.state()['asset_rights'][sha]['blocked'])
 assert len(fake.calls)==0 and st.generation.get(jid)['state']=='submission_blocked'

# Deterministic interleaving: cancellation HTTP response arrives after completion poll.
with tempfile.TemporaryDirectory(prefix='independent-contract-',dir=ROOT) as folder:
 st,j=queue_fixture(folder);q=st.generation;fake=Fake();q.dispatch(j['id'],fake)
 with st.connect() as c:q.request_cancel(j['id'],'audit cancel',c)
 class Racing(Fake):
  def cancel(self,receipt):
   completed=q.poll(j['id'],self)
   assert completed['state']=='cancelled_result' and completed['result']
   raise TimeoutError('synthetic delayed cancel response')
 q.send_cancel(j['id'],Racing());after=q.get(j['id'])
 record('F02',expected='preserve cancelled_result and collected result URL',actual_state=after['state'],actual_result=after['result'],revision=after['revision'])
 assert after['state']=='cancelled_result' and after['result']

# Valid graph relationship changes must invalidate bound dependencies, not just entity text.
with tempfile.TemporaryDirectory(prefix='independent-contract-',dir=ROOT) as folder:
 st,_=fixture(folder)
 def entity(kind,key):return dict(id=ontology.stable_id('synthetic',kind,key),type=kind,label=key,description='synthetic',provenance=[dict(source_id='synthetic',excerpt='synthetic')],uncertainty=dict(status='asserted',reason='synthetic author'))
 person=entity('character','Mira');a=entity('asset','blue-reference');b=entity('asset','red-reference')
 graph=dict(entities=[person,a,b],relations=[dict(id=str(uuid.uuid4()),type='references',source=person['id'],target=a['id'],provenance=person['provenance'])])
 with st.connect() as c:
  p=ontology.propose(c,'synthetic',graph,0,'human');first=ontology.apply(c,'synthetic',p['id'],0,'human',True)
  bound={'revision':0};project_ontology.bind(bound,first,[person['id']])
  graph['relations'][0]['target']=b['id']
  p=ontology.propose(c,'synthetic',graph,1,'human');second=ontology.apply(c,'synthetic',p['id'],1,'human',True)
 impacts=project_ontology.impact(bound,second)
 record('F03',expected='reference relationship change is review impact; old context pins relation',actual_impacts=impacts,bound_context_keys=list(bound['semantic_context']),graph_digest_changed=first['digest']!=second['digest'])
 assert impacts and 'relations' in bound['semantic_context']

# Non-frame-aligned clip duration accumulation, real local FFmpeg only.
with tempfile.TemporaryDirectory(prefix='independent-contract-',dir=ROOT) as folder:
 import renderer
 image=Path(folder)/'synthetic.png';out=Path(folder)/'out.mp4'
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=32x32','-frames:v','1',str(image)],check=True)
 p=dict(profile='preview',shots={str(i):dict(selected=1,duration=.13,takes=[dict(id=1,asset=str(image))]) for i in range(30)},audio=None,subtitles=[])
 renderer.render(p,out)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(out)]))
 actual=float(probe['format']['duration'])
 try:renderer.verify_output(out,p);error=None
 except ValueError as exc:error=str(exc)
 assert error is None and abs(actual-3.9)<=1/24
 record('F04',expected_duration=3.9,actual_duration=actual,verification_error=error,case='30 legal 0.130 second still clips at 24fps')
(ROOT/'counterexamples-after.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
