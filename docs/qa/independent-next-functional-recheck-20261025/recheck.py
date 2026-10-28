"""Independent bridge checks. Snapshot imports; no bind/connect/real provider."""
import sys,socket,tempfile,json,uuid,time,hashlib,base64
from pathlib import Path
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'snapshot'));tempfile.tempdir=str(ROOT)
def deny(*a,**k):raise AssertionError('Network/listener denied by audit harness')
socket.socket.connect=deny;socket.socket.bind=deny;socket.create_connection=deny
from app import Store
import action_execution as ae,guided,model_selection as ms,production_tools as pt,chat_protocols as cp,ledger
from loretune import Conflict
OUT=[]
def record(case,passed,**e):
 OUT.append(dict(case=case,status='pass' if passed else 'fail',**e));print(json.dumps(OUT[-1],ensure_ascii=False))
def fixture(folder,amount='0.40'):
 st=Store(folder)
 def call(action,**data):return st.mutate(dict(action=action,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
 call('project',name='A',era='default',story=0);call('project',name='B',era='default',story=0)
 plan_id=call('guided_plan',song='A',goal='Keep blue',scenes='Mira at lake',style='',constraints='',kind='visualizer')['plan']
 run=call('production_run',song='A')['run'];w=st.workspace_id;p=st.state()['project_ids']['A']
 project=st.state()['projects']['A'];plan=next(x for x in project['guided_plans'] if x['id']==plan_id)
 # Mimic the human server controller, which has no UI yet, with frozen prepared data.
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');ledger.patch_budget(c,w,'rehearsal:project:'+p,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
  a=ae.propose(c,w,p,plan_id=plan_id,plan_revision=plan['version'],context_hash=ms.snapshot(project)['sha256'],role='image',release_id='synthetic-fixture',inputs={'prompt':'Mira at lake'},options={'width':32,'height':32})
  g=ae.grant(c,w,p,[a['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='rehearsal-v1',money_by_action={a['id']:{'amount':amount,'currency':'USD'}})
 args=dict(plan_id=plan_id,action_id=a['id'],grant_id=g['id'])
 def tool(id='call',arguments=None,name='request_media_generation'):
  return call('production_tool',song='A',run=run['id'],call=dict(id=id,name=name,arguments=args if arguments is None else arguments,complete=True))['tool']
 return st,call,tool,w,p,run,a,g,args

with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder);receipt=tool();again=tool('another-call')
 with st.connect() as c:
  jobs=[json.loads(r[0]) for r in c.execute('SELECT body FROM action_jobs WHERE workspace=? AND project=?',(w,p))]
  count=c.execute('SELECT count(*) FROM reservations').fetchone()[0]
 record('single-job-reservation-mock-receipt',receipt['job_id']==again['job_id'] and len(jobs)==count==1 and receipt['mode']=='rehearsal' and receipt['external_calls']==0,receipt=receipt,job_count=len(jobs),reservations=count)
 before=deepcopy(st.state()['canon']);record('grant-does-not-approve-ip',before==[] and not st.state()['projects']['A'].get('ontology_snapshot'))
 handoff=call('model_handoff',song='A')['handoff']
 record('B01-new-action-job-handoff',len(handoff['jobs'])==1,expected_job=receipt['job_id'],actual_jobs=handoff['jobs'],source_job_state=jobs[0]['state'])
 # Idempotent key conflict through actual Store execution path.
 bad={**args,'action_id':'other-action'}
 try:tool('call',bad);blocked=False
 except Conflict:blocked=True
 record('different-action-same-call-key-conflict',blocked)
 with st.connect() as c:
  ae.revoke(c,w,p,g['id'],1)
 try:blocked=tool('after-revoke').get('status')=='blocked'
 except ValueError:blocked=True
 record('revoked-grant-new-call-rejected',blocked)
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');claimed=ae.claim(c,w,p,receipt['job_id'],context_hash=a['context_hash'],price_revision='rehearsal-v1')
  reservation=c.execute('SELECT state FROM reservations').fetchone()[0]
 record('revoke-before-claim-release-only-unsent',claimed['state']=='blocked' and reservation=='cancelled',job_state=claimed['state'],reservation=reservation)

with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder);errors=[]
 structured=[]
 for i in range(10):
  try:structured.append(tool(str(i),dict(args,action_id='missing-action')))
  except ValueError as e:errors.append(str(e))
 saved=next(r for r in st.state()['projects']['A']['production_runs'] if r['id']==run['id'])
 with st.connect() as c:counts=dict(jobs=c.execute('SELECT count(*) FROM action_jobs').fetchone()[0],reservations=c.execute('SELECT count(*) FROM reservations').fetchone()[0])
 record('B02-semantic-invalid-arguments-bounded',saved['state']!='accepting_tools',attempts=len(errors)+len(structured),structured=structured,state=saved['state'],repair_count=saved['repair_count'],call_count=len(saved['calls']),counts=counts,error=errors[0])

# action/grant tampering, current settings, and injected roles are checked independently.
for mutation in ['action-input','action-model','grant-price','settings','role-injection','endpoint-injection']:
 with tempfile.TemporaryDirectory(dir=ROOT) as folder:
  st,call,tool,w,p,run,a,g,args=fixture(folder)
  if mutation.startswith('action-'):
   with st.connect() as c:
    changed=deepcopy(a)
    if mutation=='action-input':changed['inputs']['prompt']='changed'
    else:changed['release_id']='arbitrary-model'
    ae.put(c,'production_actions',w,p,changed)
  elif mutation=='grant-price':
   with st.connect() as c:
    changed=deepcopy(g);changed['money'][a['id']]['amount']='0.01';ae.put(c,'execution_grants',w,p,changed)
  elif mutation=='settings':call('model_settings',song='A',model_revision=0,selections={'chat':'anthropic-haiku-5-5'})
  else:args={**args,('actor' if mutation=='role-injection' else 'endpoint'):('local-owner' if mutation=='role-injection' else 'https://untrusted.invalid')}
  try:result=tool(arguments=args);blocked=result.get('status') in {'invalid_arguments','blocked'}
  except ValueError:blocked=True
  with st.connect() as c:count=c.execute('SELECT count(*) FROM reservations').fetchone()[0]
  record(mutation+'-rejected-before-reservation',blocked and count==0,reservations=count)

with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder);receipt=tool();jid=receipt['job_id']
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');j=ae.claim(c,w,p,jid,context_hash=a['context_hash'],price_revision='rehearsal-v1',rights_valid=False)
  reservation=c.execute('SELECT state FROM reservations').fetchone()[0]
 record('explicit-rights-revocation-before-claim',j['state']=='blocked' and reservation=='cancelled')

with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder);receipt=tool();jid=receipt['job_id']
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');ae.claim(c,w,p,jid,context_hash=a['context_hash'],price_revision='rehearsal-v1');ae.recover(c,w,p)
 reopened=Store(folder)
 with reopened.connect() as c:
  c.execute('BEGIN IMMEDIATE');j=ae.claim(c,w,p,jid,context_hash=a['context_hash'],price_revision='rehearsal-v1')
  reservation=c.execute('SELECT state FROM reservations').fetchone()[0]
 record('unknown-recovery-keeps-reservation-no-reclaim',j['state']=='outcome_unknown' and reservation=='uncertain',job_state=j['state'],reservation=reservation)

# Independent simultaneous admission with two distinct approved actions against one cap.
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder,amount='0.70')
 with st.connect() as c:
  c.execute('BEGIN IMMEDIATE');b=ae.propose(c,w,p,plan_id=a['plan_id'],plan_revision=1,context_hash=a['context_hash'],role='image',release_id='synthetic-fixture',inputs={'prompt':'second'},options={})
  gb=ae.grant(c,w,p,[b['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='rehearsal-v1',money_by_action={b['id']:{'amount':'0.70','currency':'USD'}})
 def admit(pair):
  action,grant=pair
  with st.connect() as c:
   c.execute('BEGIN IMMEDIATE')
   try:return ae.admit(c,w,p,action['id'],grant['id'],context_hash=a['context_hash'],price_revision='rehearsal-v1')['id']
   except ledger.LedgerError:return 'blocked'
 with ThreadPoolExecutor(2) as pool:results=list(pool.map(admit,[(a,g),(b,gb)]))
 with st.connect() as c:reserved=ledger.budget(c,w,'rehearsal:project:'+p)['data']['reserved']['amount']
 record('concurrent-actions-respect-cap',results.count('blocked')==1 and float(reserved)==.7,results=results,reserved=reserved)
(ROOT/'audit-results.json').write_text(json.dumps(OUT,ensure_ascii=False,indent=2))
