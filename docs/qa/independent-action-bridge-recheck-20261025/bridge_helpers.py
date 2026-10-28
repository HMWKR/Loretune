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

