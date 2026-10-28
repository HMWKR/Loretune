"""Independent media-v1/rights checks. All stores and assets are synthetic/temp."""
from bridge_helpers import *
from image_adapter import SyntheticImageAdapter
import contracts,os
RESULT=[]
def rec(case,ok,**data):
 value=dict(case=case,status='pass' if ok else 'fail',**data);RESULT.append(value);print(json.dumps(value,ensure_ascii=False))

def setup(folder,variant='valid'):
 st=Store(folder)
 def call(command,**data):return st.mutate(dict(action=command,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 for name,width in [('A',32),('B',33)]:
  call('project',name=name,era='default',story=0);call('shot',song=name,shot='same shot',description='synthetic')
  raw=SyntheticImageAdapter().generate(dict(prompt='fixture',width=width,height=32))['bytes']
  call('take',song=name,shot='same shot',shot_revision=0,filename='fixture.png',content=base64.b64encode(raw).decode(),reason='synthetic fixture',rights='사용권 미확인' if variant=='missing-rights' and name=='A' else 'synthetic owned')
 plan=call('guided_plan',song='A',goal='synthetic',scenes='same shot',style='',constraints='',kind='visualizer')['plan']
 p=st.state()['projects']['A'];take=p['shots']['same shot']['takes'][0];foreign=st.state()['projects']['B']['shots']['same shot']['takes'][0]
 w=st.workspace_id;pid=contracts.project_id(w,'A');ref=dict(shot='same shot',take=1,sha256=take['sha256'],role='style')
 if variant=='foreign-asset':ref['sha256']=foreign['sha256']
 if variant=='forged-rights-flag':ref['rights_valid']=True
 if variant=='wrong-hash':ref['sha256']='0'*64
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');scope='rehearsal:project:'+pid
  ledger.patch_budget(c,w,scope,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
  a=ae.propose(c,w,pid,plan_id=plan,plan_revision=1,context_hash=ms.media_snapshot(p)['sha256'],context_kind='media-v1',role='image',release_id='synthetic-fixture',inputs={'prompt':'fixture','asset_refs':[ref]},options={'width':32,'height':32})
  g=ae.grant(c,w,pid,[a['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='fixture-v1',money_by_action={a['id']:{'amount':'0.10','currency':'USD'}})
  j=ae.admit(c,w,pid,a['id'],g['id'],context_hash=a['context_hash'],price_revision='fixture-v1')
 return st,call,w,pid,a,g,j,take,foreign

def claim(st,j,price='fixture-v1',project='A'):
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');result=st.claim_action(c,st.state()['projects'][project],project,j['id'],price_revision=price)
  row=c.execute('SELECT state,actual FROM reservations WHERE id=?',(j['reservation'],)).fetchone()
 return result,row

cases=['valid','chat-only','video-change','shot-change','foreign-asset','wrong-hash','missing-rights','forged-rights-flag','revoked-rights','changed-bytes','symlink','missing-file','price-change','grant-revoke','job-input-tamper','job-model-tamper','job-options-tamper','job-context-kind-tamper','grant-money-tamper','foreign-job','unknown-then-rights-revoke']
for case in cases:
 with tempfile.TemporaryDirectory(dir=ROOT) as folder:
  st,call,w,pid,a,g,j,take,foreign=setup(folder,case)
  before=ms.media_snapshot(st.state()['projects']['A'])['sha256']
  if case=='chat-only':call('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  if case=='video-change':call('model_settings',song='A',selections={'video':'fal-kling-2-6-pro'},model_revision=0)
  if case=='shot-change':call('select',song='A',shot='same shot',take=1,shot_revision=1)
  if case=='revoked-rights':call('asset_rights',sha256=take['sha256'],blocked=True,reason='synthetic revoked after admission')
  if case=='changed-bytes':Path(take['asset']).write_bytes(b'synthetic changed content')
  if case=='symlink':
   path=Path(take['asset']);target=Path(folder)/'original.png';path.rename(target);path.symlink_to(target)
  if case=='missing-file':Path(take['asset']).unlink()
  if case=='grant-revoke':
   with st.connect() as c:ae.revoke(c,w,pid,g['id'],1)
  if case.startswith('job-'):
   if case=='job-input-tamper':j['action']['inputs']['prompt']='changed'
   if case=='job-model-tamper':j['action']['release_id']='different-model'
   if case=='job-options-tamper':j['action']['options']['width']=64
   if case=='job-context-kind-tamper':j['action']['context_kind']='full-v1'
   with st.connect() as c:ae.put(c,'action_jobs',w,pid,j)
  if case=='grant-money-tamper':
   g['money'][a['id']]['amount']='0.01'
   with st.connect() as c:ae.put(c,'execution_grants',w,pid,g)
  if case=='unknown-then-rights-revoke':
   claim(st,j)
   with st.connect() as c:ae.recover(c,w,pid)
   call('asset_rights',sha256=take['sha256'],blocked=True,reason='synthetic revocation after unknown')
  if case=='foreign-job':
   try:claim(st,j,project='B');rejected=False
   except ValueError:rejected=True
   with st.connect() as c:
    saved=ae.get(c,'action_jobs',w,pid,j['id']);reservation=c.execute('SELECT state FROM reservations WHERE id=?',(j['reservation'],)).fetchone()[0]
   rec(case,rejected and saved['state']=='prepared' and reservation=='reserved',rejected=rejected,original_job=saved['state'],reservation=reservation);continue
  result,reservation=claim(st,j,price='changed' if case=='price-change' else 'fixture-v1')
  expected=('claimed','reserved') if case in ['valid','chat-only'] else ('outcome_unknown','uncertain') if case=='unknown-then-rights-revoke' else ('blocked','cancelled')
  current=ms.media_snapshot(st.state()['projects']['A'])['sha256']
  rec(case,(result['state'],reservation[0])==expected and result['external_calls']==0,expected=list(expected),job=result['state'],reservation=reservation,media_context_changed=current!=before,actual_external_calls=0)

# A dependency must be collected, human-approved, locally registered and still permitted.
for case in ['dependency-valid','dependency-revoked-rights','dependency-unapproved','dependency-changed-result','dependency-foreign-result']:
 with tempfile.TemporaryDirectory(dir=ROOT) as folder:
  st,call,w,pid,a,g,j,take,foreign=setup(folder)
  claim(st,j)
  with st.connect() as c:
   c.execute('BEGIN IMMEDIATE')
   parent=ae.record_result(c,w,pid,j['id'],asset_hash=foreign['sha256'] if case=='dependency-foreign-result' else take['sha256'],output_slot='image')
   ae.approve_result(c,w,pid,j['id'],actor='local-owner')
   child=ae.propose(c,w,pid,plan_id=a['plan_id'],plan_revision=1,context_hash=a['context_hash'],context_kind='media-v1',role='video',release_id='synthetic-video',inputs={'prompt':'synthetic'},options={},dependencies=[a['id']])
   grant=ae.grant(c,w,pid,[child['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='fixture-v1',money_by_action={child['id']:{'amount':'0.1','currency':'USD'}})
   cj=ae.admit(c,w,pid,child['id'],grant['id'],context_hash=a['context_hash'],price_revision='fixture-v1')
   if case=='dependency-unapproved':parent['result_approved']=False;ae.put(c,'action_jobs',w,pid,parent)
   if case=='dependency-changed-result':parent['result_approved']=True;parent['result']['sha256']=foreign['sha256'];ae.put(c,'action_jobs',w,pid,parent)
  if case=='dependency-revoked-rights':call('asset_rights',sha256=take['sha256'],blocked=True,reason='synthetic revoked dependency')
  result,reservation=claim(st,cj);expected=('claimed','reserved') if case=='dependency-valid' else ('blocked','cancelled')
  rec(case,(result['state'],reservation[0])==expected,expected=list(expected),job=result['state'],reservation=reservation)
(ROOT/'next-contract-results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2)+'\n')
if any(x['status']=='fail' for x in RESULT):raise SystemExit(1)
