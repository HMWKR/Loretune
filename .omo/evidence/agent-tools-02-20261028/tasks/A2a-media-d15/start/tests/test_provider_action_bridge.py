"""Actual FalKling methods + fake HTTP/CDN; real isolated SQLite and MP4. No keys/network."""
import base64,hashlib,io,json,subprocess,tempfile,time,unittest,uuid,wave
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from app import Store
import action_execution as actions,contracts,fal_provider as fal,guided,ledger,media_bridge
from image_adapter import SyntheticImageAdapter

class ProviderActionBridgeTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.media=tempfile.TemporaryDirectory();p=Path(cls.media.name)/'clip.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x64:d=10','-c:v','libx264','-pix_fmt','yuv420p',str(p)],check=True)
  cls.video=p.read_bytes()
 @classmethod
 def tearDownClass(cls):cls.media.cleanup()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name);self.calls=[]
  self.call('project',name='synthetic',era='default',story=0)
  b=io.BytesIO()
  with wave.open(b,'wb') as f:f.setparams((1,2,8000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*80000)
  self.call('audio',song='synthetic',filename='synthetic.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
  self.call('music_structure',song='synthetic',audio=1,start=0,end=10,sections=[])
  plan=self.call('guided_plan',song='synthetic',goal='synthetic',scenes='red geometry',kind='visualizer')['plan']
  self.call('apply_guided_plan',song='synthetic',plan=plan);self.plan=plan
  png=SyntheticImageAdapter().generate(dict(prompt='synthetic',width=32,height=32))['bytes']
  self.call('take',song='synthetic',shot='장면 1',shot_revision=self.sh()['revision'],filename='synthetic.png',content=base64.b64encode(png).decode(),reason='fixture',rights='synthetic owned')
  self.call('assign_reference',song='synthetic',shot='장면 1',shot_revision=self.sh()['revision'],source_song='synthetic',source_shot='장면 1',source_take=1,role='start_frame',reason='fixture')
  self.call('review_reference',song='synthetic',shot='장면 1',shot_revision=self.sh()['revision'],version=1,decision='approved',reason='fixture')
  self.prep_id=self.call('prepare_generation',song='synthetic',shot='장면 1',shot_revision=self.sh()['revision'],prompt='red geometry')['preparation']
  self.prep=self.sh()['generation_preparations'][0];self.w=self.st.workspace_id;self.p=contracts.project_id(self.w,'synthetic')
  self.rid='11111111-1111-4111-8111-111111111111';prefix=fal.BASE+'fal-ai/kling-video/requests/'+self.rid
  self.receipt=dict(request_id=self.rid,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
 def pstate(self):return self.st.state()['projects']['synthetic']
 def sh(self):return self.pstate()['shots']['장면 1']
 def call(self,action,**data):return self.st.mutate(dict(action=action,data=data,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def transport(self,method,url,headers,body):
  self.calls.append((method,url,headers,body))
  if url==fal.BASE+fal.MODEL:return self.receipt
  if url==self.receipt['status_url']:return {'status':'COMPLETED'}
  if url==self.receipt['response_url']:return {'video':{'url':'https://v3b.fal.media/synthetic.mp4','content_type':'video/mp4'}}
  if url==fal.TOKEN_URL:return {'token':'synthetic-short-token-canary'}
  if url==self.receipt['cancel_url']:return {}
  raise AssertionError('unexpected request')
 def enable(self):
  self.st.provider_adapter=fal.FalKling(live_enabled=True,transport=self.transport,private_reader='synthetic-owner')
  self.st.generation_approval=dict(model=fal.MODEL,workspace_id=self.w,song='synthetic',shot='장면 1',image_sha256=self.prep['source']['sha256'],prompt_sha256=hashlib.sha256(b'red geometry').hexdigest(),privacy='private',retention_seconds=3600,duration=10,generate_audio=False,price_money={'amount':'0.70','currency':'USD'},price_checked_at=time.time(),maximum_calls=1,maximum_units=700000,expires=time.time()+300)
  with self.st.connect() as c:ledger.patch_budget(c,self.w,'project:'+self.p,dict(limit={'amount':'0.70','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
 def start(self):return self.call('start_generation',song='synthetic',shot='장면 1',preparation=self.prep_id)['job']
 def tool_receipt(self,j):
  b=self.st.generation.get(j)['context']['action_binding']
  with self.st.connect() as c:
   c.execute('BEGIN IMMEDIATE');return actions.request_from_plan(c,self.w,self.p,self.pstate(),dict(plan_id=self.plan,action_id=b['action_id'],grant_id=b['grant_id']))
 def complete(self,j):
  self.st.process_generation();self.st.generation.poll(j,self.st.provider_adapter)
  response=io.BytesIO(self.video);response.headers={'Content-Type':'video/mp4','Content-Length':str(len(self.video))}
  with patch('fal_provider.build_opener') as opener:
   opener.return_value.open.return_value=response
   self.assertTrue(self.st.process_generation())
   req=opener.return_value.open.call_args.args[0]
   self.assertEqual(req.get_header('Authorization'),'Bearer synthetic-short-token-canary')
  return self.st.generation.get(j)
 def test_disabled_and_ai_only_requests_cannot_admit(self):
  self.assertFalse(self.st.state()['capabilities']['provider_generation']);self.assertIn('action_id',self.prep)
  with self.assertRaises(ValueError):self.start()
  with self.st.connect() as c:
   with self.assertRaises(actions.ExecutionBlocked):actions.request_from_plan(c,self.w,self.p,self.pstate(),dict(plan_id=self.plan,action_id=self.prep['action_id'],grant_id='model-invented'))
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
   a=actions.get(c,'production_actions',self.w,self.p,self.prep['action_id'])
   self.assertEqual(a['mode'],'provider');self.assertEqual(a['role'],'video')
 def test_actual_adapter_fake_roundtrip_one_reservation_registered_take_and_safe_receipt(self):
  self.enable();j=self.start();self.assertEqual(self.start(),j)
  before=self.sh()['takes'][0];out=self.complete(j)
  self.assertEqual(out['state'],'imported');self.assertEqual(self.sh()['takes'][0],before)
  take=self.sh()['takes'][1];self.assertEqual(take['action_id'],self.prep['action_id']);self.assertEqual(take['plan_id'],self.plan)
  self.assertEqual(take['metadata']['duration'],10);self.assertEqual(take['provenance']['mode'],'contract-fake');self.assertIsNone(self.sh()['selected'])
  with self.st.connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
   self.assertEqual(c.execute('SELECT count(*) FROM action_jobs').fetchone()[0],0)
   self.assertEqual(c.execute('SELECT count(*) FROM provider_action_jobs').fetchone()[0],1)
  receipt=self.tool_receipt(j);self.assertEqual(receipt['state'],'imported');self.assertEqual(receipt['external_calls'],0)
  self.assertEqual(receipt['result']['sha256'],take['sha256']);self.assertEqual(receipt['cost']['reservation_state'],'reserved');self.assertIsNone(receipt['cost']['actual']);self.assertFalse(receipt['cost']['billing_confirmed'])
  self.assertEqual(len(self.calls),4);submit=self.calls[0];self.assertEqual(submit[1],fal.BASE+fal.MODEL)
  self.assertEqual(json.loads(submit[2]['X-Fal-Object-Lifecycle-Preference']),fal.private_lifecycle_candidate('synthetic-owner'))
  self.assertEqual(submit[2]['X-Fal-No-Retry'],'1');self.assertFalse(submit[3]['generate_audio'])
  restored=Store(self.tmp.name);self.assertIsNone(restored.provider_adapter);self.assertEqual(restored.state()['projects']['synthetic']['shots']['장면 1']['takes'][1],take)
  public=json.dumps(self.st.state())+json.dumps(receipt)
  self.assertNotIn('synthetic-short-token-canary',public);self.assertNotIn('v3b.fal.media',public)
 def test_grant_rights_media_and_price_rechecked_before_submit(self):
  for change in ('grant','rights','media','price'):
   with self.subTest(change=change):
    self.setUp();self.enable();j=self.start();b=self.st.generation.get(j)['context']['action_binding']
    if change=='rights':self.call('asset_rights',sha256=self.prep['source']['sha256'],blocked=True,reason='fixture revoked')
    if change=='media':self.call('model_settings',song='synthetic',selections={'video':'fal-kling-2-6-pro'},model_revision=0)
    with self.st.connect() as c:
     if change=='grant':actions.revoke(c,self.w,self.p,b['grant_id'],1)
     if change=='price':
      job=self.st.generation.get(j);job['quote']['money']['amount']='0.69';self.st.generation.save(c,job)
    self.st.process_generation();self.assertEqual(self.calls,[]);self.assertEqual(self.st.generation.get(j)['state'],'submission_blocked')
    with self.st.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'cancelled')
 def test_chat_handoff_and_concurrent_dispatch_keep_same_job(self):
  self.enable();j=self.start();self.call('model_settings',song='synthetic',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:self.st.process_generation(),range(2)))
  self.assertEqual(len(self.calls),1);self.assertEqual(self.st.generation.get(j)['state'],'accepted')
  for _ in range(2):self.assertEqual(self.tool_receipt(j)['job_id'],j)
  with self.st.connect() as c:
   jobs=actions.project_jobs(c,self.w,self.p,'synthetic');self.assertEqual(jobs[0]['plan_id'],self.plan)
   self.assertEqual(actions.project_jobs(c,self.w,'foreign','synthetic'),[])
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
 def test_mapping_failure_rolls_back_job_grant_and_reservation(self):
  self.enable()
  with patch('media_bridge.bind',side_effect=RuntimeError('synthetic crash')):
   with self.assertRaises(RuntimeError):self.start()
  with self.st.connect() as c:
   for table in ['execution_grants','generation_jobs','reservations','provider_action_jobs']:
    self.assertEqual(c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
  self.assertNotIn('job',self.sh()['generation_preparations'][0])
 def test_lost_submission_receipt_preserves_unknown_and_does_not_reissue(self):
  self.enable();j=self.start()
  def timeout(*args):self.calls.append(args);raise TimeoutError()
  self.st.provider_adapter._transport=timeout;self.st.process_generation();self.st.generation.recover();self.st.process_generation()
  receipt=self.tool_receipt(j);self.assertEqual(receipt['state'],'reconciliation_required');self.assertEqual(receipt['cost']['reservation_state'],'uncertain');self.assertEqual(len(self.calls),1)
  self.assertEqual(self.start(),j)
 def test_permission_denial_and_invalid_video_never_register_or_resubmit(self):
  for fault in ('403','truncated'):
   with self.subTest(fault=fault):
    self.setUp();self.enable();j=self.start();self.st.process_generation();self.st.generation.poll(j,self.st.provider_adapter)
    if fault=='403':
     def denied(*args):self.calls.append(args);raise fal.ProviderError('provider_http_403')
     self.st.provider_adapter._transport=denied
     with patch('fal_provider.build_opener',side_effect=AssertionError('must not reach CDN')):self.st.process_generation()
    else:
     response=io.BytesIO(b'bad');response.headers={'Content-Type':'video/mp4','Content-Length':'20'}
     with patch('fal_provider.build_opener') as opener:
      opener.return_value.open.return_value=response;self.st.process_generation()
    self.assertFalse(self.st.process_generation());r=self.tool_receipt(j)
    self.assertEqual(r['state'],'import_blocked');self.assertTrue(r['provider_completed']);self.assertIsNone(r['result']);self.assertEqual(r['cost']['reservation_state'],'uncertain');self.assertEqual(len(self.sh()['takes']),1)
    if fault=='403':
     self.assertEqual(r['failure_code'],'cdn_token_http_403')
     with self.assertRaises(ValueError):self.call('resume_generation_result',song='synthetic',job=j)
 def test_cancel_contract_retains_unconfirmed_cost_after_submit(self):
  self.enable();j=self.start();self.st.process_generation();self.call('cancel_generation',song='synthetic',job=j,reason='fixture')
  self.st.process_generation();self.assertEqual(self.calls[-1][0:2],('PUT',self.receipt['cancel_url']))
  self.st.generation.poll(j,self.st.provider_adapter);r=self.tool_receipt(j)
  self.assertEqual(r['state'],'cancelled_result');self.assertIsNone(r['cost']['actual']);self.assertFalse(self.st.process_generation())
  self.assertEqual(len(self.sh()['takes']),1)
 def test_cancel_before_submit_releases_once(self):
  self.enable();j=self.start();self.call('cancel_generation',song='synthetic',job=j,reason='fixture')
  self.assertFalse(self.st.process_generation());self.assertEqual(self.calls,[])
  r=self.tool_receipt(j);self.assertEqual(r['state'],'cancelled');self.assertEqual(r['cost']['reservation_state'],'cancelled');self.assertIsNone(r['cost']['actual'])
