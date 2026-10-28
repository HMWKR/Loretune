import unittest,tempfile,subprocess,base64,time,hashlib,uuid
from pathlib import Path
from copy import deepcopy
from app import Store
import app,ledger,fal_provider as fal

class Fake:
 def __init__(self):self.calls=[]
 def submit(self,data):self.calls.append(deepcopy(data));return {'request_id':'synthetic'}

def fixture(folder):
 st=Store(folder)
 def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 return st,call

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
 return st,call,jid,fake,sha

class SubmissionAuthorityTest(unittest.TestCase):
 def test_rights_gate_connection_and_input_changes_block_only_unsent(self):
  for mutation in ['control','rights','gate-replaced','gate-revoked','connection','input']:
   with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as folder:
    st,call,jid,fake,sha=prepared(folder)
    if mutation=='rights':call('asset_rights',sha256=sha,blocked=True,reason='revoke')
    elif mutation=='gate-replaced':st.generation_approval=dict(st.generation_approval,maximum_calls=2)
    elif mutation=='gate-revoked':st.generation_approval=None
    elif mutation=='connection':st.provider_adapter=Fake()
    elif mutation=='input':
     asset=st.generation.get(jid)['context']['submission_binding']['preparation']['source']['asset'];Path(asset).write_bytes(b'changed')
    current=st.provider_adapter;st.process_generation();j=st.generation.get(jid)
    self.assertEqual(len(current.calls),1 if mutation=='control' else 0)
    self.assertEqual(j['state'],'accepted' if mutation=='control' else 'submission_blocked')
    self.assertNotIn('submission_binding',st.state()['generation_jobs'][0]['context'])
    with st.connect() as c:
     self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(j['reservation'],)).fetchone()[0],'reserved' if mutation=='control' else 'cancelled')
    if mutation=='control':
     call('asset_rights',sha256=sha,blocked=True,reason='after-submit');st.process_generation()
     self.assertEqual(len(fake.calls),1)
     with st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(j['reservation'],)).fetchone()[0],'reserved')
