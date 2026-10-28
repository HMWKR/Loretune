"""Real image adapter/queue/SQLite/filesystem with synthetic HTTP and PNG. No live calls."""
import base64,hashlib,io,json,subprocess,tempfile,time,unittest,uuid,wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from app import Store
import action_execution as actions,contracts,guided,ledger,model_selection,runway_provider as rw
from image_pipeline import ImagePipeline
from image_adapter import SyntheticImageAdapter
from fal_provider import ProviderError

class ImagePipelineTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture.png'
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=1920x1080','-frames:v','1',str(path)],check=True)
   cls.png=path.read_bytes()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(self.tmp.name);self.calls=[]
  self.call('project',name='synthetic',era='default',story=0)
  b=io.BytesIO()
  with wave.open(b,'wb') as f:f.setparams((1,2,8000,0,'NONE','not compressed'));f.writeframes(b'\0\0'*8000)
  self.call('audio',song='synthetic',filename='synthetic.wav',content=base64.b64encode(b.getvalue()).decode(),rights='synthetic owned')
  self.call('music_structure',song='synthetic',audio=1,start=0,end=1,sections=[])
  self.plan=self.call('guided_plan',song='synthetic',goal='synthetic',scenes='blue geometry',kind='visualizer')['plan']
  self.call('apply_guided_plan',song='synthetic',plan=self.plan)
  self.adapter=rw.RunwayImage(transport=self.transport,output_hosts={'dnznrvs05pmza.cloudfront.net'})
  self.pipeline=ImagePipeline(self.store,self.adapter);self.store.image_pipeline=self.pipeline
  self.rid='11111111-1111-4111-8111-111111111111'
  self.url='https://dnznrvs05pmza.cloudfront.net/synthetic.png?_jwt=synthetic-signed-canary'
 def call(self,action,**data):return self.store.mutate(dict(action=action,data=data,revision=self.store.state()['revision'],request_id=uuid.uuid4().hex))
 def project(self):return self.store.state()['projects']['synthetic']
 def shot(self):return self.project()['shots']['장면 1']
 def transport(self,method,url,headers,body):
  self.calls.append((method,url,headers,body))
  if method=='POST':return {'id':self.rid}
  return dict(id=self.rid,status='SUCCEEDED',output=[self.url],cost={'credits':8})
 def prepare(self,refs=()):
  result=self.pipeline.prepare('synthetic','장면 1','blue geometry','1920:1080',refs,expected_revision=self.shot()['revision']);self.prep=result
  self.pipeline.gate=dict(workspace=self.store.workspace_id,project=contracts.project_id(self.store.workspace_id,'synthetic'),
   action_hash=result['action']['hash'],input_sha256=result['input_sha256'],model=rw.MODEL,output_policy=result['action']['options']['output_policy'],
   maximum_units=80000,maximum_calls=1,expires=time.time()+240)
  with self.store.connect() as c:ledger.patch_budget(c,self.store.workspace_id,'project:'+self.pipeline.gate['project'],dict(limit={'amount':'0.08','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
  return result['action']['id']
 def start(self,refs=()):return self.pipeline.admit('synthetic',self.prepare(refs),human_approved=True)
 def finish(self,j):
  self.store.process_generation();self.store.generation.poll(j['id'],self.adapter)
  response=io.BytesIO(self.png);response.headers={'Content-Type':'image/png','Content-Length':str(len(self.png))}
  with patch('runway_provider.build_opener') as opener:
   opener.return_value.open.return_value=response;self.store.process_generation()
   req=opener.return_value.open.call_args.args[0];self.assertNotIn('Authorization',req.headers)
  return self.store.generation.get(j['id'])
 def test_real_adapter_contract_registers_unapproved_take_and_same_action_receipt(self):
  j=self.start();self.assertEqual(self.pipeline.admit('synthetic',self.prep['action']['id'],human_approved=True)['id'],j['id'])
  out=self.finish(j);self.assertEqual(out['state'],'imported')
  take=self.shot()['takes'][0];self.assertEqual(take['sha256'],hashlib.sha256(self.png).hexdigest());self.assertIsNone(self.shot()['selected'])
  self.assertEqual(take['rights'],'사용권 미확인');self.assertEqual(take['provenance']['model'],'gen4_image');self.assertEqual(take['metadata']['width'],1920)
  self.assertEqual(self.calls[0][1],rw.BASE+'text_to_image');self.assertEqual(self.calls[0][2]['X-Runway-Version'],'2024-11-06')
  self.assertEqual(self.calls[0][3],{'model':'gen4_image','promptText':'blue geometry','ratio':'1920:1080'})
  with self.store.connect() as c:
   self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
   receipt=actions.request_from_plan(c,self.store.workspace_id,self.pipeline.gate['project'],self.project(),dict(plan_id=self.plan,action_id=self.prep['action']['id'],grant_id=j['context']['action_binding']['grant_id']))
  self.assertEqual(receipt['result']['output_slot'],'image');self.assertFalse(receipt['cost']['billing_confirmed']);self.assertIsNone(receipt['cost']['actual'])
  self.assertEqual(receipt['cost']['evidence']['kind'],'provider_reported_credits')
  self.assertNotIn('synthetic-signed-canary',json.dumps(self.store.state())+json.dumps(receipt))
  self.assertEqual(Store(self.tmp.name).state()['projects']['synthetic']['shots']['장면 1']['takes'][0],take)
 def test_concurrent_admit_and_worker_only_submit_once(self):
  aid=self.prepare()
  with ThreadPoolExecutor(max_workers=2) as pool:jobs=list(pool.map(lambda _:self.pipeline.admit('synthetic',aid,human_approved=True),range(2)))
  self.assertEqual(jobs[0]['id'],jobs[1]['id'])
  with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:self.store.process_generation(),range(2)))
  self.assertEqual(len(self.calls),1)
 def test_revoked_rights_grant_and_changed_media_block_before_submit(self):
  for case in ['rights','grant','media','price']:
   with self.subTest(case=case):
    self.setUp()
    raw=SyntheticImageAdapter().generate(dict(prompt='fixture',width=32,height=32))['bytes']
    self.call('take',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],filename='fixture.png',content=base64.b64encode(raw).decode(),reason='fixture',rights='synthetic owned')
    t=self.shot()['takes'][0];ref=dict(shot='장면 1',take=t['id'],sha256=t['sha256'],role='style');j=self.start([ref])
    if case=='rights':self.call('asset_rights',sha256=t['sha256'],blocked=True,reason='fixture revoke')
    if case=='media':self.call('model_settings',song='synthetic',selections={'image':'runway-gen4-image'},model_revision=0)
    with self.store.connect() as c:
     if case=='grant':actions.revoke(c,self.store.workspace_id,self.pipeline.gate['project'],j['context']['action_binding']['grant_id'],1)
     if case=='price':j['quote']['money']['amount']='0.07';self.store.generation.save(c,j)
    self.store.process_generation();self.assertEqual(self.calls,[]);self.assertEqual(self.store.generation.get(j['id'])['state'],'submission_blocked')
 def test_chat_handoff_does_not_invalidate_media(self):
  j=self.start();self.call('model_settings',song='synthetic',selections={'chat':'anthropic-haiku-5-5'},model_revision=0)
  self.store.process_generation();self.assertEqual(self.store.generation.get(j['id'])['state'],'accepted')
 def test_unknown_submit_survives_restart_without_reissue(self):
  j=self.start()
  def lost(*args):self.calls.append(args);raise TimeoutError()
  self.adapter._transport=lost;self.store.process_generation();self.store.generation.recover();self.store.process_generation()
  self.assertEqual(len(self.calls),1);self.assertEqual(self.store.generation.get(j['id'])['state'],'reconciliation_required')
  with self.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
 def test_cancel_before_submit_only_and_post_submit_never_deletes(self):
  j=self.start()
  with self.store.connect() as c:self.store.generation.request_cancel(j['id'],'fixture',c)
  self.store.process_generation();self.assertEqual(self.calls,[])
  self.setUp();j=self.start();self.store.process_generation()
  with self.store.connect() as c:
   with self.assertRaisesRegex(ValueError,'DELETE'):self.store.generation.request_cancel(j['id'],'fixture',c)
  with self.assertRaises(ProviderError):self.adapter.cancel({'request_id':self.rid})
  self.assertEqual(len(self.calls),1)
 def test_provider_failure_and_cancelled_are_terminal_but_not_free(self):
  for state in ['FAILED','CANCELLED']:
   with self.subTest(state=state):
    self.setUp();j=self.start();self.store.process_generation();self.adapter._transport=lambda *a:dict(id=self.rid,status=state,cost={'credits':3})
    out=self.store.generation.poll(j['id'],self.adapter);self.assertIn(out['state'],{'failed','provider_cancelled'});self.assertFalse(out['cost_confirmed'])
    self.assertFalse(self.store.process_generation());self.assertEqual(self.shot()['takes'],[])
 def test_wrong_dimensions_or_truncation_never_publish_asset(self):
  for raw in [self.png[:30],SyntheticImageAdapter().generate(dict(prompt='x',width=32,height=32))['bytes']]:
   self.setUp();j=self.start();self.store.process_generation();self.store.generation.poll(j['id'],self.adapter)
   with patch.object(self.adapter,'download',return_value=raw):self.store.process_generation()
   self.assertEqual(self.store.generation.get(j['id'])['state'],'import_blocked');self.assertEqual(self.shot()['takes'],[])
   self.assertFalse((self.store.root/'assets'/(hashlib.sha256(raw).hexdigest()+'.png')).exists())
 def test_role_scope_and_human_gate_not_model_flags(self):
  aid=self.prepare()
  with self.assertRaises(ValueError):self.pipeline.admit('synthetic',aid)
  self.call('project',name='foreign',era='default',story=0)
  with self.assertRaises(ValueError):self.pipeline.admit('foreign',aid,human_approved=True)
  self.pipeline.gate['input_sha256']='wrong'
  with self.assertRaises(ValueError):self.pipeline.admit('synthetic',aid,human_approved=True)
  with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
 def test_payload_and_output_security_boundaries(self):
  for prompt in ['', '😀'*501]:
   with self.assertRaises(ValueError):rw.payload(prompt,'1920:1080')
  for url in ['http://dnznrvs05pmza.cloudfront.net/x','https://127.0.0.1/x','https://evil.cloudfront.net/x','https://u@dnznrvs05pmza.cloudfront.net/x','https://dnznrvs05pmza.cloudfront.net:444/x']:
   with self.assertRaises(ProviderError):self.adapter.validate_output_url(url)
  with self.assertRaises(ProviderError):rw.RunwayImage().submit(rw.payload('test','1920:1080'))
  self.assertFalse(model_selection.resolve('image',explicit='runway-gen4-image')['executable'])

 def test_image_denied_download_cannot_use_legacy_resume_endpoint(self):
  j=self.start();self.store.process_generation();self.store.generation.poll(j['id'],self.adapter)
  with patch.object(self.adapter,'download',side_effect=ProviderError('download_http_403')):self.store.process_generation()
  self.assertEqual(self.store.generation.get(j['id'])['state'],'import_blocked')
  with self.assertRaisesRegex(ValueError,'복구 연결'):self.call('resume_generation_result',song='synthetic',job=j['id'])
  self.assertEqual(len(self.calls),2);self.assertEqual(self.shot()['takes'],[])
 def test_result_registration_rollback_is_recoverable_same_request_no_auto_submit(self):
  j=self.start();self.store.process_generation();self.store.generation.poll(j['id'],self.adapter)
  with patch('loretune.Studio.attach_take',side_effect=RuntimeError('fixture registration crash')):
   with self.assertRaises(RuntimeError):self.store.generation.import_result(j['id'],lambda url:self.png)
  self.assertEqual(self.shot()['takes'],[]);self.assertEqual(self.store.generation.get(j['id'])['state'],'downloading')
  self.store.generation.recover();self.assertEqual(self.store.generation.get(j['id'])['state'],'import_blocked')
  self.assertFalse(self.store.process_generation());self.assertEqual(len(self.calls),2)
 def test_image_http_faults_redirect_and_body_boundaries_are_bounded(self):
  from urllib.error import HTTPError
  for code in [301,401,403,404,410,429,503]:
   with patch('runway_provider.build_opener') as opener:
    opener.return_value.open.side_effect=HTTPError(self.url,code,'fixture',{},None)
    with self.assertRaises(ProviderError):self.adapter.download(self.url)
    self.assertEqual(opener.return_value.open.call_count,1)
  for raw,headers in [(b'bad',{'Content-Type':'text/html'}),(self.png,{'Content-Type':'image/jpeg'}),(self.png,{'Content-Type':'image/png','Content-Length':str(len(self.png)+1)}),(self.png,{'Content-Type':'image/png','Content-Length':str(rw.MAX_BYTES+1)})]:
   with patch('runway_provider.build_opener') as opener:
    response=io.BytesIO(raw);response.headers=headers;opener.return_value.open.return_value=response
    with self.assertRaises(ProviderError):self.adapter.download(self.url)
 def test_api_credential_only_on_exact_host_and_never_saved(self):
  response=io.BytesIO(json.dumps({'id':self.rid}).encode());response.headers={'Content-Type':'application/json'}
  with patch('runway_provider.build_opener') as opener:
   opener.return_value.open.return_value=response
   adapter=rw.RunwayImage(key='synthetic-secret-canary',live_enabled=True)
   result=adapter.submit(rw.payload('synthetic','1920:1080'));request=opener.return_value.open.call_args.args[0]
   self.assertEqual(request.host,'api.dev.runwayml.com');self.assertEqual(request.headers['Authorization'],'Bearer synthetic-secret-canary')
   self.assertNotIn('canary',json.dumps(result))
