import base64,hashlib,io,json,subprocess,tempfile,time,unittest,uuid,wave
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from app import Store
import action_execution as actions,contracts,guided,ledger,model_selection,chat_protocols
from fal_model_adapter import FalModelAdapter
from fal_models import Contract,MODELS,CONNECTION
from fal_dispatch import FalDispatch
from fal_provider import ProviderError,BASE,LIFECYCLE
from image_adapter import SyntheticImageAdapter

class FalMultiTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=64x64:d=5','-c:v','libx264','-pix_fmt','yuv420p',str(p)],check=True);cls.video=p.read_bytes()
   p=Path(folder)/'image.png';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=1024x576','-frames:v','1',str(p)],check=True);cls.image=p.read_bytes()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name);self.calls=[]
  self.call('project',name='synthetic',era='default',story=0)
  buf=io.BytesIO()
  with wave.open(buf,'wb') as w:w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*40000)
  self.call('audio',song='synthetic',filename='synthetic.wav',content=base64.b64encode(buf.getvalue()).decode(),rights='synthetic owned')
  self.call('music_structure',song='synthetic',audio=1,start=0,end=5,sections=[])
  self.plan=self.call('guided_plan',song='synthetic',goal='geometry',scenes='blue studio',kind='visualizer')['plan'];self.call('apply_guided_plan',song='synthetic',plan=self.plan)
 def call(self,a,**d):return self.st.mutate(dict(action=a,data=d,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def project(self):return self.st.state()['projects']['synthetic']
 def shot(self):return self.project()['shots']['장면 1']
 def setup_model(self,key):
  c=Contract(key);role=c.role;refs=[];frames=[];options={'ratio':'16:9'} if role=='image' else {'duration':5,'generate_audio':False}
  self.call('model_settings',song='synthetic',selections={role:key},model_revision=self.project()['model_settings']['revision'])
  if role=='video':
   png=SyntheticImageAdapter().generate(dict(prompt='fixture',width=32,height=32))['bytes'];frames=[png]
   self.call('take',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],filename='start.png',content=base64.b64encode(png).decode(),reason='fixture',rights='synthetic owned')
   t=self.shot()['takes'][-1];refs=[dict(shot='장면 1',take=t['id'],sha256=t['sha256'],role='start_frame')]
   self.call('assign_reference',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],source_song='synthetic',source_shot='장면 1',source_take=t['id'],role='start_frame',reason='fixture')
   self.call('review_reference',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],version=1,decision='approved',reason='fixture')
  payload=c.payload('blue geometry',options,frames)
  quote=dict(provider='fal.ai',model=c.MODEL,money={'amount':'0.01','currency':'USD'},input_sha256=guided.fingerprint(payload),kind='fixture',price_revision='synthetic-price-not-real',source=c.spec['source'],expires=time.time()+300)
  self.rid=str(uuid.uuid4());prefix=BASE+'/'.join(c.MODEL.split('/')[:2])+'/requests/'+self.rid
  self.receipt=dict(request_id=self.rid,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
  def transport(method,url,headers,body):
   self.calls.append((method,url,headers,body))
   if method=='POST':return self.receipt
   if url.endswith('/status'):return {'status':'COMPLETED'}
   if method=='PUT':return {}
   asset={'url':'https://v3b.fal.media/synthetic.'+('png' if role=='image' else 'mp4'),'content_type':'image/png' if role=='image' else 'video/mp4'}
   return {'images':[asset],'has_nsfw_concepts':[False]} if role=='image' else {'video':asset}
  self.ad=FalModelAdapter(key,quote=quote,transport=transport);self.pipe=FalDispatch(self.st,[self.ad]);self.st.media_dispatch=self.pipe
  prep=self.call('media_prepare',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],prompt='blue geometry',options=options,refs=refs)['media_action'];self.action=prep['action'];self.refs=refs
  self.w=self.st.workspace_id;self.pid=contracts.project_id(self.w,'synthetic')
  self.pipe.gates[self.action['id']]=dict(workspace=self.w,project=self.pid,action_hash=self.action['hash'],input_sha256=prep['input_sha256'],model=c.MODEL,output_policy=self.action['options']['output_policy'],maximum_units=10000,maximum_calls=1,expires=time.time()+200)
  with self.st.connect() as db:ledger.patch_budget(db,self.w,'project:'+self.pid,dict(limit={'amount':'0.01','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
  self.grant=self.call('media_approve',song='synthetic',action_id=self.action['id'])['media_grant'];return payload
 def request(self,provider='anthropic'):
  run=self.call('production_run',song='synthetic')['run']['id'];args=dict(plan_id=self.plan,action_id=self.action['id'],grant_id=self.grant['id'])
  if provider=='anthropic':response=dict(stop_reason='tool_use',content=[dict(type='tool_use',id='tool',name='request_media_generation',input=args)])
  else:response=dict(status='completed',output=[dict(type='function_call',call_id='tool',name='request_media_generation',arguments=json.dumps(args))])
  call=chat_protocols.normalize(provider,response,run)['calls'][0]
  return self.call('production_tool',song='synthetic',run=run,call=call)['tool']
 def finish(self,j):
  self.st.process_generation();self.st.generation.poll(j,self.ad)
  with patch.object(self.ad,'download',return_value=self.image if self.ad.contract.role=='image' else self.video):self.st.process_generation()
  return self.st.generation.get(j)
 def test_four_official_contracts_share_queue_and_import(self):
  for key in MODELS:
   with self.subTest(key=key):
    self.setUp();payload=self.setup_model(key);before=self.shot()['takes'][:];receipt=self.request();self.assertEqual(receipt['status'],'accepted');j=receipt['job_id']
    # Three provider envelopes use identical saved grant: no second reservation/job.
    for provider in ('openai','xai'):self.assertEqual(self.request(provider)['job_id'],j)
    out=self.finish(j);self.assertEqual(out['state'],'imported');self.assertEqual(self.shot()['takes'][:-1],before);self.assertIsNone(self.shot()['selected'])
    self.assertEqual(self.shot()['takes'][-1]['provenance']['model'],self.ad.contract.MODEL);self.assertEqual(self.calls[0][3],payload)
    self.assertEqual(json.loads(self.calls[0][2]['X-Fal-Object-Lifecycle-Preference']),LIFECYCLE);self.assertEqual(self.calls[0][2]['X-Fal-No-Retry'],'1')
    with self.st.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
    self.assertFalse(out['cost_confirmed']);self.assertEqual(out['external_calls'],0)
 def test_fresh_grant_required_and_no_ai_authority(self):
  self.setup_model('fal-flux-schnell');self.grant['id']='invented';result=self.request();self.assertEqual(result['status'],'invalid_arguments');self.assertEqual(self.st.state()['generation_jobs'],[]);self.assertEqual(self.calls,[])
 def test_rights_revoke_before_submit_is_verified_unsubmitted(self):
  self.setup_model('fal-kling-2-5-turbo');j=self.request()['job_id'];self.call('asset_rights',sha256=self.refs[0]['sha256'],blocked=True,reason='fixture revoke');self.st.process_generation()
  out=self.st.generation.get(j);self.assertEqual(out['state'],'submission_blocked');self.assertTrue(out['verified_unsubmitted']);self.assertEqual(self.calls,[])
 def test_chat_switch_preserves_media_grant_but_media_switch_blocks(self):
  self.setup_model('fal-flux-schnell');j=self.request()['job_id'];self.call('model_settings',song='synthetic',selections={'chat':'xai-grok-4-7'},model_revision=self.project()['model_settings']['revision']);self.st.process_generation();self.assertEqual(self.st.generation.get(j)['state'],'accepted')
  self.setUp();self.setup_model('fal-flux-schnell');j=self.request()['job_id'];self.call('model_settings',song='synthetic',selections={'image':'fal-flux-pro-1-1'},model_revision=self.project()['model_settings']['revision']);self.st.process_generation();self.assertEqual(self.st.generation.get(j)['state'],'submission_blocked');self.assertFalse(self.calls)
 def test_unknown_submit_never_duplicates_after_restart(self):
  self.setup_model('fal-flux-schnell');j=self.request()['job_id']
  def lost(*args):self.calls.append(args);raise TimeoutError()
  self.ad._transport=lost;self.st.process_generation();self.st.generation.recover();self.st.process_generation();self.assertEqual(len(self.calls),1);self.assertEqual(self.request()['job_id'],j);self.assertEqual(self.st.generation.get(j)['state'],'reconciliation_required')
 def test_model_receipt_and_private_output_cannot_cross_hosts(self):
  self.setup_model('fal-flux-pro-1-1');self.ad._transport=lambda *args:dict(self.receipt,response_url='https://queue.fal.run/fal-ai/flux/requests/'+self.rid)
  with self.assertRaises(ProviderError):self.ad.submit(self.ad.contract.payload('blue geometry',{'ratio':'16:9'}))
  self.ad._transport=lambda *args:{'images':[{'url':'https://public.example/image.png'}]}
  with self.assertRaises(ProviderError):self.ad.result(self.receipt)
 def test_t2i_ref_roles_and_private_url_not_silently_forwarded(self):
  for key in MODELS:
   c=Contract(key)
   with self.assertRaises(ValueError):c.payload('x',{'ratio':'16:9'} if c.role=='image' else {'duration':5,'generate_audio':False},[b'https://v3b.fal.media/private.png'])
 def test_expired_quote_and_absent_runtime_never_enable_catalog(self):
  self.assertFalse(any(x['state']=='active' for x in model_selection.catalog()['models']))
  c=Contract('fal-flux-schnell')
  with self.assertRaises(ValueError):c.estimate(c.payload('x',{'ratio':'16:9'}))
  with self.assertRaises(ValueError):self.call('media_prepare',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],prompt='x',options={'ratio':'16:9'},refs=[])

 def test_model_tool_prepares_action_and_quote_but_cannot_grant_or_spend(self):
  self.setup_model('fal-flux-schnell');run=self.call('production_run',song='synthetic')['run']['id']
  args=dict(shot_id='장면 1',model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9',shot_revision=self.shot()['revision'])
  result=self.call('production_tool',song='synthetic',run=run,call=dict(id='prepare',name='prepare_image_action',arguments=args,complete=True))['tool']
  self.assertEqual(result['status'],'proposed');self.assertEqual(result['approval'],'required');self.assertEqual(self.calls,[])
  with self.st.connect() as db:
   self.assertEqual(db.execute('SELECT count(*) FROM generation_jobs').fetchone()[0],0);self.assertEqual(db.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
  estimate=self.call('production_tool',song='synthetic',run=run,call=dict(id='quote',name='estimate_media_plan',arguments={'plan_id':self.plan},complete=True))['tool']
  self.assertEqual(estimate['status'],'estimated');self.assertFalse(estimate['approval']);self.assertEqual(len(estimate['actions']),2)
 def test_parallel_tool_admission_reserves_once(self):
  self.setup_model('fal-flux-schnell')
  def request(_):
   with self.st.connect() as db:
    db.execute('BEGIN IMMEDIATE');p,_=self.pipe.project(db,'synthetic')
    return self.pipe.request(db,self.w,self.pid,p,self.action,self.grant['id'])
  with ThreadPoolExecutor(2) as pool:receipts=list(pool.map(request,range(2)))
  self.assertEqual(receipts[0]['job_id'],receipts[1]['job_id'])
  with self.st.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM reservations').fetchone()[0],1)

 def test_creator_projection_omits_internal_grants_hashes_and_paths(self):
  self.setup_model('fal-flux-schnell');cards=self.project()['media_actions'];self.assertEqual(cards[0]['approval'],'approved');self.assertEqual(cards[0]['mode'],'contract-fake')
  serialized=json.dumps(cards);self.assertNotIn('action_hash',serialized);self.assertNotIn('grant_id',serialized);self.assertNotIn('input_sha256',serialized);self.assertNotIn(str(self.st.root),serialized)

 def test_generated_private_image_uses_local_bytes_for_video_after_human_rights_review(self):
  self.setup_model('fal-flux-schnell');image_job=self.request()['job_id'];self.finish(image_job);take=self.shot()['takes'][-1];original_sha=take['sha256']
  with self.assertRaises(ValueError):self.call('assign_reference',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],source_song='synthetic',source_shot='장면 1',source_take=take['id'],role='start_frame',reason='not reviewed')
  self.call('declare_take_rights',song='synthetic',shot='장면 1',take=take['id'],sha256=original_sha,shot_revision=self.shot()['revision'],evidence='Synthetic fixture created locally for this test')
  self.call('assign_reference',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],source_song='synthetic',source_shot='장면 1',source_take=take['id'],role='start_frame',reason='approved synthetic image')
  self.call('review_reference',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],version=1,decision='approved',reason='frame reviewed')
  self.call('model_settings',song='synthetic',selections={'video':'fal-kling-2-5-turbo'},model_revision=self.project()['model_settings']['revision'])
  contract=Contract('fal-kling-2-5-turbo');options={'duration':5,'generate_audio':False};payload=contract.payload('blue geometry',options,[self.image])
  quote=dict(provider='fal.ai',model=contract.MODEL,money={'amount':'0.01','currency':'USD'},input_sha256=guided.fingerprint(payload),kind='fixture',price_revision='synthetic-price-not-real',source=contract.spec['source'],expires=time.time()+300)
  adapter=FalModelAdapter('fal-kling-2-5-turbo',quote=quote,transport=lambda *args:self.fail('no submission before grant'))
  self.pipe.adapters['fal-kling-2-5-turbo']=adapter
  refs=[dict(shot='장면 1',take=take['id'],sha256=original_sha,role='start_frame')]
  prep=self.call('media_prepare',song='synthetic',shot='장면 1',shot_revision=self.shot()['revision'],prompt='blue geometry',options=options,refs=refs)['media_action']
  with self.st.connect() as c:actual=self.pipe.data(c,self.project(),prep['action'])
  self.assertEqual(actual,payload);self.assertTrue(actual['image_url'].startswith('data:image/png;base64,'));self.assertNotIn('fal.media',actual['image_url'])
  self.assertEqual(self.shot()['takes'][-1]['sha256'],original_sha);self.assertEqual(self.shot()['takes'][-1]['provenance']['model'],'fal-ai/flux/schnell')
