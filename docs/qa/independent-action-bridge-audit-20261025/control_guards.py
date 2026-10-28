from helpers import *
import renderer
R=[]
def record(name,ok,**kw):R.append(dict(case=name,status='pass' if ok else 'fail',**kw))
with tempfile.TemporaryDirectory(dir=ROOT) as f:
 st,call,jid,fake,sha,prep=prepared(f);st.generation_approval=None;st.process_generation();base=st.generation.get(jid)
 with st.connect() as c:
  record('quota-return-requires-unsubmitted-unpaid-release',not st.generation.consumes_call_quota(c,base))
  for name,change in [('legacy',{'verified_unsubmitted':None}),('started',{'submission_started_at':1}),('receipt',{'receipt':{'id':'synthetic'}}),('result',{'result':{'url':'synthetic'}}),('cost-confirmed',{'cost_confirmed':True}),('unknown',{'state':'reconciliation_required'})]:
   j=deepcopy(base);j.update(change);record('quota-retained-'+name,st.generation.consumes_call_quota(c,j))
  ledger.command(c,st.workspace_id,base['scope'],'settle',{'reservation':base['reservation'],'money':{'amount':'0.70','currency':'USD'}},'synthetic-late-bill')
  record('late-bill-after-release-restores-quota-occupancy',st.generation.consumes_call_quota(c,base))
# Lost response plus attempted new preparation cannot free cost/call quota.
with tempfile.TemporaryDirectory(dir=ROOT) as f:
 st,call,jid,fake,sha,prep=prepared(f)
 def timeout(data):fake.calls.append(deepcopy(data));raise TimeoutError('synthetic lost receipt')
 fake.submit=timeout;st.process_generation()
 shot=st.state()['projects']['synthetic']['shots']['one']
 newprep=call('prepare_generation',song='synthetic',shot='one',shot_revision=shot['revision'],prompt='synthetic')['preparation']
 try:call('start_generation',song='synthetic',shot='one',preparation=newprep);blocked=False
 except ValueError:blocked=True
 with st.connect() as c:
  j=st.generation.get(jid);reservation=c.execute('SELECT state,amount FROM reservations WHERE id=?',(j['reservation'],)).fetchone()
  consumes=st.generation.consumes_call_quota(c,j)
 record('unknown-new-submit-blocked-reservation-held',blocked and len(fake.calls)==1 and reservation==('uncertain',700000) and consumes,submits=len(fake.calls),reservation=reservation,consumes_quota=consumes)
media=ROOT/'media';source=media/'fractional-0.131.mp4'
p=dict(profile='preview',shots={str(i):dict(duration=.131) for i in range(30)},audio={'asset':'synthetic'},subtitles=[dict(start=.2,end=.4,text='첫 박자'),dict(start=3.92,end=3.93,text='끝 자막')])
wrong=deepcopy(p);wrong['subtitles'][-1]['text']='변조한 자막'
try:renderer.verify_output(source,wrong);error=None
except ValueError as e:error=str(e)
record('wrong-caption-content-rejected',error is not None and '자막' in error,error=error)
wrong=deepcopy(p);wrong['subtitles'][-1]['end']=3.929
try:renderer.verify_output(source,wrong);error=None
except ValueError as e:error=str(e)
record('wrong-caption-time-rejected',error is not None and '자막' in error,error=error)
out=media/'short-audio-negative.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-i',str(source),'-map','0:v:0','-map','0:a:0','-map','0:s:0','-c:v','copy','-c:s','copy','-af','atrim=end=3.90','-c:a','aac',str(out)],check=True)
try:renderer.verify_output(out,p);error=None
except ValueError as e:error=str(e)
record('short-audio-tail-rejected',error is not None and '음원' in error,error=error)
(ROOT/'guard-results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
print(json.dumps(R,ensure_ascii=False,indent=2))
