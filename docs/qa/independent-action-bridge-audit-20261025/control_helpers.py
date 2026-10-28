"""Independent synthetic counterexamples; snapshot imports only; all network denied."""
import sys, tempfile, json, time, uuid, base64, subprocess, hashlib, socket
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parent
tempfile.tempdir=str(ROOT)
sys.path.insert(0,str(ROOT/'snapshot'))
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

def prepared(folder):
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
 return st,call,jid,fake,sha,prep_id
