from bridge_helpers import *
import io,wave
RESULT=[]
for switch in [False,True]:
 with tempfile.TemporaryDirectory(dir=ROOT) as folder:
  st=Store(folder)
  def call(command,**data):return st.mutate(dict(action=command,data=data,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
  call('project',name='A',era='default',story=0);call('project',name='B',era='default',story=0)
  b=io.BytesIO()
  with wave.open(b,'wb') as out:out.setparams((1,2,48000,0,'NONE','not compressed'));out.writeframes(b'\0\0'*96000)
  call('audio',song='A',filename='synthetic.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
  call('music_structure',song='A',audio=1,start=0,end=2,sections=[])
  pid=call('guided_plan',song='A',goal='fixture',scenes='Mira at lake',style='',constraints='',kind='visualizer')['plan']
  call('apply_guided_plan',song='A',plan=pid)
  plan=st.state()['projects']['A']['guided_plans'][0]
  card=call('action_propose',song='A',plan=pid,scene=plan['scenes'][0]['id'])['execution_card']
  card=call('action_decide',song='A',id=card['id'],card_revision=card['revision'],decision='approved')['execution_card']
  if switch:call('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  handoff=call('model_handoff',song='A')['handoff'];foreign=call('model_handoff',song='B')['handoff']
  card=call('action_execute',song='A',id=card['id'],card_revision=card['revision'])['execution_card']
  with st.connect() as c:
   j=ae.get(c,'action_jobs',st.workspace_id,st.state()['project_ids']['A'],card['job'])
   res=c.execute('SELECT state,actual FROM reservations WHERE id=?',(j['reservation'],)).fetchone()
  value=dict(case='B03-approved-media-after-chat-switch' if switch else 'human-flow-control',status='pass' if j['state']=='collected' else 'fail',chat_switched=switch,handoff_jobs=handoff['jobs'],foreign_jobs=foreign['jobs'],card_decision=card['decision'],job_state=j['state'],take=card['take'],reservation=res,canon=st.state()['canon'])
  RESULT.append(value);print(json.dumps(value,ensure_ascii=False))
(ROOT/'human-flow-results.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
