from bridge_helpers import *
from unittest.mock import patch
R=[]
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder)
 first=tool('bad-one',dict(args,action_id='missing'));replay=tool('bad-one',dict(args,action_id='missing'))
 saved=next(x for x in st.state()['projects']['A']['production_runs'] if x['id']==run['id'])
 R.append(dict(case='semantic-error-replay-does-not-double-count',status='pass' if first==replay and saved['repair_count']==1 and len(saved['calls'])==1 else 'fail',repair_count=saved['repair_count'],calls=len(saved['calls'])))
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,tool,w,p,run,a,g,args=fixture(folder)
 real=ae.put
 def failure(c,table,*args,**kwargs):
  if table=='action_jobs':raise ValueError('synthetic fault after reserve')
  return real(c,table,*args,**kwargs)
 with patch.object(ae,'put',side_effect=failure):out=tool('fault')
 with st.connect() as c:
  counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['reservations','action_jobs','action_admissions']}
 saved=next(x for x in st.state()['projects']['A']['production_runs'] if x['id']==run['id'])
 R.append(dict(case='savepoint-rolls-back-effects-preserves-blocked-result',status='pass' if out['status']=='blocked' and all(n==0 for n in counts.values()) and len(saved['calls'])==1 else 'fail',result=out,counts=counts,repair_count=saved['repair_count'],calls=len(saved['calls'])))
(ROOT/'error-guard-results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2));print(json.dumps(R,ensure_ascii=False))
