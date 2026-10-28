import hashlib,json,shutil,subprocess,tempfile,unittest,uuid
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from app import Store
import motion_scene as m,motion_renderer as raster,production_context,chat_protocols

def scene():
 def layer(id,kind,text,x,y,w,h):
  return dict(id=id,kind=kind,text=text,font='system-ko-regular',font_size=80,width=w,height=h,color='#F4F4F2' if kind=='text' else '#A7C7FF',in_frame=0,out_frame=96,keyframes=[dict(frame=0,x=x,y=y,opacity=1,easing='linear')])
 return dict(schema_version=1,width=1920,height=1080,fps=24,frame_count=96,background='#101010',layers=[layer('title','text','새로운 리듬',160,160,1500,160),layer('bar','rect','',160,700,600,100),layer('dot','circle','',1300,680,160,160)])

class MotionTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.st=Store(self.tmp.name)
  self.call('project',name='A',era='default',story=0);self.call('shot',shot='s',description='synthetic motion')
 def call(self,a,**d):
  if a!='project':d.setdefault('song','A')
  return self.st.mutate(dict(action=a,data=d,revision=self.st.state()['revision'],request_id=uuid.uuid4().hex))
 def p(self):return self.st.state()['projects']['A']
 def args(self,value=None):return dict(shot_id=production_context.shot_id(self.p(),'s'),base_motion_revision=self.p()['shots']['s'].get('motion_head',0),scene=value or scene())
 def proposal(self,value=None):return self.call('motion_propose',**self.args(value))['motion']['proposal_id']
 def approve(self,identifier):return self.call('motion_review',proposal_id=identifier,decision='approved')
 def queue(self):
  v=self.p()['shots']['s']['motion_versions'][-1]
  return self.call('motion_render',shot_id=self.args()['shot_id'],motion_revision=v['id'],grant_id=v['approval']['id'])['motion']
 def selected_fixture(self):
  # A real, synthetic PNG uploaded through the application preserves an existing Take.
  png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='
  self.call('take',shot='s',shot_revision=0,filename='prior.png',content=png,reason='기존 합성 이미지',rights='직접 제작')
  self.call('select',shot='s',shot_revision=1,take=1)
  return deepcopy(self.p()['shots']['s']['takes'][0])
 def fake_render_video(self):
  # The video is a synthetic fixture; the actual Store publication path still verifies it.
  path=Path(self.tmp.name)/'fake-render-input.mp4'
  subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','color=c=blue:s=1920x1080:r=24:d=4',
                  '-an','-c:v','libx264','-preset','ultrafast','-threads','1','-pix_fmt','yuv420p',str(path)],check=True)
  return path
 def test_schema_bounds_and_no_code_or_paths(self):
  m.validate(scene())
  for change in [lambda s:s.update(width=4096),lambda s:s.update(url='https://example.test'),lambda s:s['layers'][0].update(font='/tmp/font'),lambda s:s['layers'][0]['keyframes'][0].update(x=float('nan')),lambda s:s['layers'].append(deepcopy(s['layers'][0])),lambda s:s['layers'][0].update(text='<script>\x00'),lambda s:s['layers'][0].update(out_frame=97)]:
   s=scene();change(s)
   with self.assertRaises(ValueError):m.validate(s)
 def test_frame_clock_easing_interval_and_delayed_only_circle(self):
  s=scene();s['layers'][2]['keyframes']=[dict(frame=0,x=100,y=200,opacity=0,easing='linear'),dict(frame=24,x=340,y=200,opacity=1,easing='linear')]
  self.assertEqual(m.frame_state(s,12)['layers'][2]['x'],220)
  self.assertEqual(m.frame_state(s,12)['layers'][2]['opacity'],.5)
  changed=deepcopy(s);changed['layers'][2]['in_frame']=12
  for k in changed['layers'][2]['keyframes']:k['frame']+=12
  self.assertEqual(len(m.frame_state(changed,11)['layers']),2)
  self.assertEqual(m.frame_state(changed,24)['layers'][2],m.frame_state(s,12)['layers'][2])
  self.assertEqual(changed['layers'][:2],s['layers'][:2])
 def test_three_protocols_propose_idempotently_without_apply(self):
  for provider in ['anthropic','openai','xai']:
   run=self.call('production_run')['run']['id'];args=self.args()
   raw=dict(stop_reason='tool_use',content=[dict(type='tool_use',id='one',name='propose_motion_scene',input=args)]) if provider=='anthropic' else dict(status='completed',output=[dict(type='function_call',call_id='one',name='propose_motion_scene',arguments=json.dumps(args))])
   normalized=chat_protocols.normalize(provider,raw,run);call=normalized['calls'][0]
   first=self.call('production_tool',run=run,call=call)['tool'];second=self.call('production_tool',run=run,call=call)['tool']
   self.assertEqual(first,second);self.assertEqual(first['status'],'proposed');self.assertFalse(first['applied'])
   self.assertIn('proposed',json.dumps(chat_protocols.result_message(normalized,call['id'],first,provider=provider,run_id=run)))
  self.assertEqual(len(self.p()['motion_proposals']),3);self.assertNotIn('motion_head',self.p()['shots']['s']);self.assertEqual(self.st.state()['jobs'],[])
 def test_human_versions_hold_reject_stale_foreign_restore_and_original_preserved(self):
  with patch.object(raster,'validate_text',return_value={}):
   a=self.proposal();self.call('motion_review',proposal_id=a,decision='held');self.assertNotIn('motion_head',self.p()['shots']['s'])
   self.approve(a);old=deepcopy(self.p()['shots']['s']['motion_versions'][0]);stale=self.proposal()
   b=self.proposal();self.approve(b)
   with self.assertRaises(ValueError):self.approve(stale)
   self.call('project',name='B',era='default',story=0)
   with self.assertRaises(ValueError):self.call('motion_review',song='B',proposal_id=a,decision='approved')
   restored=self.call('motion_restore',shot_id=self.args()['shot_id'],base_motion_revision=2,version=1)['motion']
   self.assertEqual(self.p()['shots']['s']['motion_head'],2);self.approve(restored['proposal_id'])
   self.assertEqual(self.p()['shots']['s']['motion_head'],3);self.assertEqual(self.p()['shots']['s']['motion_versions'][0],old)
   self.assertEqual(Store(self.tmp.name).state()['projects']['A']['shots']['s']['motion_head'],3)
 def test_render_grant_cancel_reuse_and_font_change(self):
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  with self.assertRaises(ValueError):self.call('motion_render',shot_id=self.args()['shot_id'],motion_revision=1,grant_id='fake')
  first=self.queue();self.call('cancel_job',job=first['job_id']);self.assertFalse(self.st.process_next());self.assertEqual(self.queue()['job_id'],first['job_id'])
  self.assertEqual(self.p()['shots']['s']['takes'],[])
  with patch.object(raster,'font_manifest',return_value={'changed':True}):
   with self.assertRaises(ValueError):self.queue()
 def test_real_coretext_preview_export_candidate_and_reopen(self):
  s=scene();s['layers'][2]['keyframes'].append(dict(frame=95,x=1000,y=680,opacity=1,easing='linear'))
  evidence=raster.validate_text(s,self.st.root);self.assertFalse(evidence['text'][0]['glyph_missing'])
  a=self.proposal(s);self.approve(a);original=deepcopy(self.p()['shots']['s']);j=self.queue()
  self.assertFalse(j['finished_verified']);self.assertEqual(self.queue()['job_id'],j['job_id']);self.assertTrue(self.st.process_next())
  job=self.st.state()['jobs'][0];self.assertEqual(job['status'],'completed',job.get('error'));self.assertEqual(job['verified']['frames'],96)
  shot=self.p()['shots']['s'];self.assertIsNone(shot['selected']);self.assertEqual(len(shot['takes']),1);self.assertEqual(shot['takes'][0]['rights'],'사용권 미확인')
  self.assertEqual(shot['motion_versions'],original['motion_versions']);self.assertEqual(Store(self.tmp.name).state()['jobs'][0]['sha256'],job['sha256'])
  png=Path(self.tmp.name)/'preview.png';raster.frame(s,24,png,self.st.root)
  again=Path(self.tmp.name)/'again.png';raster.frame(s,24,again,self.st.root);self.assertEqual(png.read_bytes(),again.read_bytes())
  with self.assertRaises(ValueError):self.call('delivery_review',job=j['job_id'],decision='approved',reason='not final output')
 def test_cancel_during_frames_and_publication_rollback(self):
  from renderer import Cancelled
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  j=self.queue()
  with patch.object(raster,'render',side_effect=Cancelled('controlled cancellation')):self.assertTrue(self.st.process_next())
  self.assertEqual(self.st.state()['jobs'][0]['status'],'cancelled');self.assertEqual(self.p()['shots']['s']['takes'],[])
  self.assertFalse((self.st.root/'exports'/('parts-'+j['job_id'])).exists())
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  j=self.queue();raw=b'controlled-new-publication';dest=self.st.root/'assets'/(hashlib.sha256(raw).hexdigest()+'.mp4')
  def render(_,destination,*a):destination.write_bytes(raw);return {'frames':96}
  def publish(*a,**kw):dest.write_bytes(raw);return dest,{}
  with patch.object(raster,'render',side_effect=render),patch.object(self.st,'save_media',side_effect=publish),patch('loretune.Studio.attach_take',side_effect=ValueError('controlled DB publication failure')):self.assertTrue(self.st.process_next())
  self.assertEqual(next(x for x in self.st.state()['jobs'] if x['id']==j['job_id'])['status'],'failed');self.assertEqual(self.p()['shots']['s']['takes'],[]);self.assertFalse(dest.exists())
  # The same failure must never erase a pre-existing content-addressed asset.
  dest.write_bytes(raw)
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  self.queue()
  with patch.object(raster,'render',side_effect=render),patch.object(self.st,'save_media',side_effect=publish),patch('loretune.Studio.attach_take',side_effect=ValueError('controlled rollback')):self.st.process_next()
  self.assertEqual(dest.read_bytes(),raw)
 def test_font_bounds_preview_and_context_change_fail_closed(self):
  invalid=scene();invalid['layers'][0]['width']=10
  with self.assertRaises(ValueError):raster.validate_text(invalid,self.st.root)
  invalid=scene();invalid['layers'][0]['text']='\U0002ffff'
  with self.assertRaises(ValueError):raster.validate_text(invalid,self.st.root)
  a=self.proposal();self.assertTrue(self.st.motion_preview('A',a,24).startswith(b'\x89PNG'))
  with self.assertRaises(ValueError):self.st.motion_preview('A',a,96)
  with patch.object(raster,'validate_text',return_value={}):self.approve(a)
  self.queue()
  with self.st.connect() as c:
   r,b=c.execute('SELECT revision,body FROM state').fetchone();s=json.loads(b);s['projects']['A']['shots']['s']['description']='new context';c.execute('UPDATE state SET revision=?,body=?',(r+1,json.dumps(s)))
  with patch.object(raster,'render',side_effect=AssertionError('must not render')):self.assertTrue(self.st.process_next())
  self.assertEqual(self.st.state()['jobs'][0]['status'],'failed');self.assertEqual(self.p()['shots']['s']['takes'],[])
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg and FFprobe unavailable')
 def test_ontology_change_during_fake_render_rejects_candidate_without_losing_existing_take(self):
  prior=self.selected_fixture();prior_bytes=Path(prior['asset']).read_bytes();fixture=self.fake_render_video()
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  first=deepcopy(self.p()['shots']['s']['motion_versions'][0]);job=self.queue()
  assets_before={p.name for p in (self.st.root/'assets').iterdir()}
  def fake_render(_,destination,*args):
   self.assertEqual(next(j for j in self.st.state()['jobs'] if j['id']==job['job_id'])['status'],'running')
   proposal=self.call('ontology_propose',ontology_revision=0,kind='character',label='합성 인물',description='새 기준',evidence='시험용 입력')['ontology']
   self.call('ontology_apply',proposal=proposal['id'],ontology_revision=0,approved=True)
   shutil.copyfile(fixture,destination)
   return {'frames':96,'kind':'fake-render-transaction-test'}
  with patch.object(raster,'render',side_effect=fake_render),patch.object(self.st,'save_media',wraps=self.st.save_media) as publish:
   self.assertTrue(self.st.process_next())
  publish.assert_not_called()
  reopened=Store(self.tmp.name).state();shot=reopened['projects']['A']['shots']['s']
  result=next(j for j in reopened['jobs'] if j['id']==job['job_id'])
  self.assertEqual(result['status'],'failed');self.assertIn('문맥',result['error'])
  self.assertEqual(shot['takes'],[prior]);self.assertEqual(shot['selected'],1)
  self.assertEqual(shot['motion_head'],1);self.assertEqual(shot['motion_versions'][0],first)
  self.assertEqual(Path(prior['asset']).read_bytes(),prior_bytes)
  self.assertEqual({p.name for p in (self.st.root/'assets').iterdir()},assets_before)
  self.assertFalse((self.st.root/'exports'/('parts-'+job['job_id'])).exists())
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg and FFprobe unavailable')
 def test_new_motion_head_during_fake_render_publishes_only_frozen_unselected_candidate(self):
  prior=self.selected_fixture();prior_bytes=Path(prior['asset']).read_bytes();fixture=self.fake_render_video()
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  first=deepcopy(self.p()['shots']['s']['motion_versions'][0]);job=self.queue()
  def fake_render(_,destination,*args):
   self.assertEqual(next(j for j in self.st.state()['jobs'] if j['id']==job['job_id'])['status'],'running')
   changed=scene();changed['layers'][0]['text']='두 번째 버전'
   with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal(changed))
   self.assertEqual(self.p()['shots']['s']['motion_head'],2)
   shutil.copyfile(fixture,destination)
   return {'frames':96,'kind':'fake-render-transaction-test'}
  with patch.object(raster,'render',side_effect=fake_render):self.assertTrue(self.st.process_next())
  reopened=Store(self.tmp.name).state();shot=reopened['projects']['A']['shots']['s']
  result=next(j for j in reopened['jobs'] if j['id']==job['job_id'])
  self.assertEqual(result['status'],'completed',result.get('error'))
  self.assertEqual(shot['motion_head'],2);self.assertEqual(shot['motion_versions'][0],first)
  self.assertEqual(shot['motion_versions'][1]['scene']['layers'][0]['text'],'두 번째 버전')
  self.assertEqual(shot['selected'],1);self.assertEqual(shot['takes'][0],prior)
  self.assertEqual(len(shot['takes']),2);candidate=shot['takes'][1]
  self.assertEqual(result['take'],candidate['id']);self.assertEqual(candidate['rights'],'사용권 미확인')
  self.assertEqual(candidate['provenance']['kind'],'local-motion')
  self.assertEqual(candidate['provenance']['motion_revision'],1)
  self.assertEqual(candidate['provenance']['scene_hash'],first['scene_hash'])
  self.assertEqual(candidate['provenance']['job'],job['job_id'])
  self.assertEqual(hashlib.sha256(Path(candidate['asset']).read_bytes()).hexdigest(),candidate['sha256'])
  self.assertEqual(Path(prior['asset']).read_bytes(),prior_bytes)
 def test_restart_reuses_interrupted_job_and_running_motion_serializes_workers(self):
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  first=self.queue()
  with self.st.connect() as c:
   j=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(first['job_id'],)).fetchone()[0]);j['status']='running';c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(j),j['id']))
  reopened=Store(self.tmp.name);reopened.recover_jobs();self.st=reopened
  self.assertEqual(self.queue()['state'],'interrupted');self.assertFalse(self.st.process_next())
  with patch.object(raster,'validate_text',return_value={}):self.approve(self.proposal())
  second=self.queue()
  with self.st.connect() as c:
   j=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(first['job_id'],)).fetchone()[0]);j['status']='running';c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(j),j['id']))
  with patch.object(raster,'process',side_effect=AssertionError('second worker must not claim')):self.assertFalse(self.st.process_next())
  self.assertEqual(next(j for j in self.st.state()['jobs'] if j['id']==second['job_id'])['status'],'queued')

if __name__=='__main__':unittest.main()
