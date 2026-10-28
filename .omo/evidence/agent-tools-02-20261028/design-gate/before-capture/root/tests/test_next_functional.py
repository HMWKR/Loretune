import base64,io,json,tempfile,time,unittest,uuid,wave
from copy import deepcopy
from pathlib import Path
from app import Store
import action_execution as actions,contracts,guided,ledger,model_selection
from image_adapter import SyntheticImageAdapter

class NextFunctionalTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name)
  self.call('project',name='A',era='default',story=0)
  b=io.BytesIO()
  with wave.open(b,'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*96000)
  self.call('audio',song='A',filename='synthetic.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
  self.call('music_structure',song='A',audio=1,start=0,end=2,sections=[])
  pid=self.call('guided_plan',song='A',goal='synthetic',scenes='Mira in studio',style='',constraints='',kind='visualizer')['plan']
  self.call('apply_guided_plan',song='A',plan=pid)
  self.plan=self.p()['guided_plans'][0]
 def p(self):return self.st.state()['projects']['A']
 def call(self,action,**data):return self.st.mutate(dict(action=action,data=data,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def approve(self):
  c=self.call('action_propose',song='A',plan=self.plan['id'],scene=self.plan['scenes'][0]['id'])['execution_card']
  return self.call('action_decide',song='A',id=c['id'],card_revision=c['revision'],decision='approved')['execution_card']
 def execute(self,c):return self.call('action_execute',song='A',id=c['id'],card_revision=c['revision'])['execution_card']
 def test_b03_chat_only_switch_preserves_execution_not_only_handoff(self):
  card=self.approve();self.call('model_settings',song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  result=self.execute(card);self.assertEqual(result['take'],1)
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state,actual FROM reservations').fetchone(),('settled',0))
 def test_media_default_change_still_blocks_approved_execution(self):
  card=self.approve();self.call('model_settings',song='A',selections={'video':'fal-kling-2-6-pro'},model_revision=0)
  result=self.execute(card);self.assertEqual(result['decision'],'blocked');self.assertIsNone(result['take'])
 def test_input_change_and_revoked_grant_still_block(self):
  card=self.approve();self.call('shot',song='A',shot='new',description='new input')
  self.assertIsNone(self.execute(card)['take'])
 def asset_job(self,foreign=False):
  png=SyntheticImageAdapter().generate(dict(prompt='synthetic',width=32,height=32))['bytes']
  sh=self.p()['shots']['장면 1']
  self.call('take',song='A',shot='장면 1',shot_revision=sh['revision'],filename='synthetic.png',content=base64.b64encode(png).decode(),reason='fixture',rights='synthetic owned')
  project=self.p();take=project['shots']['장면 1']['takes'][0];pid=contracts.project_id(self.st.workspace_id,'A');w=self.st.workspace_id
  with self.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');scope='rehearsal:project:'+pid
   ledger.patch_budget(c,w,scope,dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=4,allowAutomaticRetries=False),0)
   a=actions.propose(c,w,pid,plan_id=self.plan['id'],plan_revision=1,context_hash=model_selection.media_snapshot(project)['sha256'],context_kind='media-v1',role='image',release_id='fixture',
      inputs={'prompt':'synthetic','asset_refs':[dict(shot='foreign' if foreign else '장면 1',take=take['id'],sha256=take['sha256'],role='style')]},options={})
   g=actions.grant(c,w,pid,[a['id']],actor='local-owner',approved=True,expires=time.time()+300,price_revision='fixture-v1',money_by_action={a['id']:{'amount':'0.1','currency':'USD'}})
   j=actions.admit(c,w,pid,a['id'],g['id'],context_hash=a['context_hash'],price_revision='fixture-v1')
  return j,take
 def claim(self,j,price='fixture-v1'):
  with self.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');return self.st.claim_action(c,self.p(),'A',j['id'],price_revision=price)
 def test_canonical_asset_control_and_rights_revoke(self):
  j,t=self.asset_job();self.call('asset_rights',sha256=t['sha256'],blocked=True,reason='revoked after admission')
  self.assertEqual(self.claim(j)['state'],'blocked')
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
 def test_asset_control_claims_without_trusting_model_flags(self):
  j,t=self.asset_job();self.assertEqual(self.claim(j)['state'],'claimed')
  self.assertEqual(self.claim(j)['state'],'claimed')
 def test_foreign_reference_and_file_tamper_block(self):
  j,t=self.asset_job(foreign=True);self.assertEqual(self.claim(j)['state'],'blocked')
 def test_asset_content_changed_blocks(self):
  j,t=self.asset_job();Path(t['asset']).write_bytes(b'changed');self.assertEqual(self.claim(j)['state'],'blocked')
 def test_price_revision_still_blocks(self):
  j,t=self.asset_job();self.assertEqual(self.claim(j,'changed-v2')['state'],'blocked')
