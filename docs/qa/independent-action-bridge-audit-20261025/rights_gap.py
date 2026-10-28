"""Gap probe: explicit rights_valid unit gate is not a Store rights integration."""
import sys,socket,tempfile,uuid,time,json,base64
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'snapshot'));tempfile.tempdir=str(R)
def deny(*a,**k):raise AssertionError('no networking')
socket.socket.connect=deny;socket.socket.bind=deny
from app import Store
from image_adapter import SyntheticImageAdapter
import action_execution as ae,model_selection as ms,ledger
with tempfile.TemporaryDirectory(dir=R) as folder:
 st=Store(folder)
 def call(a,**d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 call('project',name='A',era='default',story=0);call('shot',song='A',shot='one',description='synthetic')
 raw=SyntheticImageAdapter().generate({'prompt':'synthetic','width':32,'height':32})['bytes']
 call('take',song='A',shot='one',shot_revision=0,filename='synthetic.png',content=base64.b64encode(raw).decode(),reason='audit',rights='synthetic owned')
 pid=call('guided_plan',song='A',goal='use input',scenes='synthetic',style='',constraints='',kind='visualizer')['plan']
 state=st.state();sha=state['projects']['A']['shots']['one']['takes'][0]['sha256'];w=st.workspace_id;p=state['project_ids']['A'];context=ms.snapshot(state['projects']['A'])['sha256']
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');ledger.patch_budget(c,w,'rehearsal:project:'+p,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=2,allowAutomaticRetries=False),0)
  a=ae.propose(c,w,p,plan_id=pid,plan_revision=1,context_hash=context,role='video',release_id='synthetic-video',inputs={'asset_sha256':sha},options={})
  g=ae.grant(c,w,p,[a['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='rehearsal-v1',money_by_action={a['id']:{'amount':'0.40','currency':'USD'}})
  j=ae.admit(c,w,p,a['id'],g['id'],context_hash=context,price_revision='rehearsal-v1')
 call('asset_rights',sha256=sha,blocked=True,reason='synthetic revoke')
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');out=ae.claim(c,w,p,j['id'],context_hash=ms.snapshot(st.state()['projects']['A'])['sha256'],price_revision='rehearsal-v1')
 value=dict(status='integration-gap-not-live-exploit',asset_rights_blocked=st.state()['asset_rights'][sha]['blocked'],action_state=out['state'],external_calls=out['external_calls'],note='claim defaults rights_valid=True; no Store claim/dispatch controller exists. Caller must supply rights recheck; only explicit false unit gate tested.')
 (R/'rights-integration-gap.json').write_text(json.dumps(value,ensure_ascii=False,indent=2));print(value)
