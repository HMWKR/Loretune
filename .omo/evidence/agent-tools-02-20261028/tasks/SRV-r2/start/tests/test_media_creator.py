import json,time,uuid,unittest,subprocess,tempfile
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from tests import test_fal_multimodel as fixtures
import action_execution as actions,contracts,guided,media_recovery
from fal_models import CONNECTION
from fal_provider import ProviderError

class MediaCreatorTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixtures.FalMultiTest.setUpClass()
 def setUp(self):
  self.f=fixtures.FalMultiTest();self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.setup_model('fal-flux-schnell');self.st=self.f.st;self.pipe=self.f.pipe
 def decide(self,d):return self.f.call('media_action_decide',song='synthetic',action_id=self.f.action['id'],decision=d)
 def card(self):return self.f.project()['media_actions'][0]
 def blocked(self,code='download_interrupted'):
  j=self.decide('execute')['job'];self.st.process_generation();job=self.st.generation.poll(j,self.f.ad);job.update(state='import_blocked',failure_code=code)
  with self.st.connect() as c:self.st.generation.save(c,job)
  return job
 def gate(self,j,op='collect',**extra):
  self.pipe.recovery_approvals[j['id']]=dict(id=uuid.uuid4().hex,evidence='synthetic only',workspace=self.st.workspace_id,project=self.f.pid,connection_id=CONNECTION,model=self.f.ad.contract.MODEL,job=j['id'],request_id=j['receipt']['request_id'],operation=op,result_sha256=guided.fingerprint(j.get('result')),expires=time.time()+30,**extra)
 def recover(self,j,op='collect'):return self.f.call('recover_media_job',song='synthetic',job=j['id'],operation=op)
 def test_human_hold_reject_reapprove_and_single_reservation(self):
  self.decide('held');self.assertFalse(self.card()['can_execute']);self.assertEqual(self.card()['approval'],'held')
  with self.assertRaises(ValueError):self.decide('execute')
  self.decide('rejected');self.assertEqual(self.card()['approval'],'rejected');self.decide('approved');self.assertTrue(self.card()['can_execute'])
  with self.st.connect() as c:self.f.grant=json.loads(c.execute('SELECT body FROM execution_grants ORDER BY rowid DESC LIMIT 1').fetchone()[0])
  j=self.decide('execute')['job'];self.assertEqual(self.decide('execute')['job'],j);self.assertEqual(self.f.request()['job_id'],j)
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],1)
  self.assertFalse(self.f.calls);out=self.f.finish(j);self.assertEqual(out['state'],'imported');self.assertIsNone(self.f.shot()['selected']);self.assertFalse(self.card()['candidate']['selected']);self.assertFalse(self.card()['candidate']['rights_known'])
 def test_stale_model_cannot_be_reapproved_and_no_fallback(self):
  self.decide('held');self.f.call('model_settings',song='synthetic',selections={'image':'fal-flux-pro-1-1'},model_revision=self.f.project()['model_settings']['revision'])
  with self.assertRaises(ValueError):self.decide('approved')
  self.assertFalse(self.card()['can_execute']);self.assertFalse(self.card()['can_approve']);self.assertFalse(self.f.calls)
 def test_unknown_repeated_human_execute_only_returns_existing_job(self):
  j=self.decide('execute')['job'];self.f.ad._transport=lambda *a:(_ for _ in ()).throw(TimeoutError());self.st.process_generation();self.st.generation.recover()
  self.assertEqual(self.decide('execute')['job'],j);self.assertEqual(self.st.generation.get(j)['state'],'reconciliation_required');self.assertFalse(self.st.process_generation());self.assertFalse(self.card()['job']['recovery']['can_collect'])
 def test_collect_double_click_workers_preserve_original_selection(self):
  j=self.blocked();self.gate(j);self.recover(j);self.recover(j)
  with patch.object(self.f.ad,'download',return_value=self.f.image) as download:
   with ThreadPoolExecutor(2) as pool:list(pool.map(lambda _:self.st.process_generation(),range(2)))
   self.assertEqual(download.call_count,1)
  out=self.st.generation.get(j['id']);self.assertEqual(out['state'],'imported');self.assertEqual(out['receipt'],j['receipt']);self.assertIsNone(self.f.shot()['selected']);self.assertEqual(len(self.f.shot()['takes']),1);self.assertEqual(sum(x[0]=='POST' for x in self.f.calls),1)
  with self.assertRaises(ValueError):self.recover(out)
 def test_403_new_permission_evidence_only_one_retry(self):
  j=self.blocked('download_http_403');self.gate(j)
  with self.assertRaisesRegex(ValueError,'접근 거절'):self.recover(j)
  self.gate(j,resolves_permission=True,resolved_failure='download_http_403');self.recover(j)
  with patch.object(self.f.ad,'download',side_effect=ProviderError('download_http_403')) as download:self.st.process_generation();self.st.process_generation();self.assertEqual(download.call_count,1)
  self.assertFalse(self.card()['job']['recovery']['can_collect']);self.assertEqual(self.st.generation.get(j['id'])['state'],'import_blocked')
 def test_local_recovery_error_cannot_erase_prior_permission_denial(self):
  j=self.blocked('cdn_token_http_403');self.gate(j,resolves_permission=True,resolved_failure='cdn_token_http_403');self.recover(j)
  self.pipe.recovery_approvals[j['id']]['evidence']='changed after enqueue'
  with patch.object(self.f.ad,'download',side_effect=AssertionError('no IO')):self.st.process_generation()
  out=self.st.generation.get(j['id']);self.assertEqual(out['retrieval_permission_failure'],'cdn_token_http_403')
  self.gate(out)
  with self.assertRaisesRegex(ValueError,'접근 거절'):self.recover(out)
  self.assertFalse(self.card()['job']['recovery']['can_collect'])
 def test_status_query_needs_separate_collection_approval(self):
  j=self.blocked('download_http_410');self.gate(j,'status');self.recover(j,'status')
  with patch.object(self.f.ad,'download',side_effect=AssertionError('not approved')):self.st.process_generation();self.st.process_generation()
  out=self.st.generation.get(j['id']);self.assertEqual(out['state'],'import_blocked');self.assertEqual(out['failure_code'],'collection_requires_approval');self.assertFalse(self.card()['job']['recovery']['can_collect']);self.assertEqual(sum(x[0]=='POST' for x in self.f.calls),1)
  self.gate(out);self.recover(out)
  with patch.object(self.f.ad,'download',return_value=self.f.image):self.st.process_generation()
  self.assertEqual(self.st.generation.get(j['id'])['state'],'imported')
 def test_gate_changes_and_grant_revoke_prevent_collection(self):
  j=self.blocked();self.gate(j);self.recover(j);self.pipe.recovery_approvals[j['id']]['evidence']='changed'
  with patch.object(self.f.ad,'download',side_effect=AssertionError('no IO')):self.st.process_generation()
  out=self.st.generation.get(j['id']);self.assertEqual(out['state'],'import_blocked');self.gate(out);self.recover(out)
  with self.st.connect() as c:actions.revoke(c,self.st.workspace_id,self.f.pid,j['context']['action_binding']['grant_id'],1)
  with patch.object(self.f.ad,'download',side_effect=AssertionError('no IO')):self.st.process_generation()
  self.assertEqual(self.f.shot()['takes'],[])
 def test_recovery_restart_no_resubmit_and_legacy_bypasses_blocked(self):
  j=self.blocked();j['state']='image_recovery_running'
  with self.st.connect() as c:self.st.generation.save(c,j)
  self.st.generation.recover();self.assertFalse(self.st.process_generation());self.assertEqual(self.st.generation.get(j['id'])['state'],'reconciliation_required')
  for action in ('resume_generation_result','resume_generation_status','recover_image_job'):
   with self.assertRaises(ValueError):self.f.call(action,song='synthetic',job=j['id'],operation='collect')
 def test_cross_project_and_wrong_payload_cannot_gain_authority(self):
  j=self.blocked();self.gate(j);self.f.call('project',name='foreign',era='default',story=0)
  with self.assertRaises(ValueError):self.f.call('recover_media_job',song='foreign',job=j['id'],operation='collect')
  with self.assertRaises(ValueError):self.f.call('media_action_decide',song='foreign',action_id=self.f.action['id'],decision='execute')
  with self.assertRaises(ValueError):self.f.call('media_action_decide',song='synthetic',action_id=self.f.action['id'],decision='execute',approved=True)
  self.assertEqual(sum(x[0]=='POST' for x in self.f.calls),1)
 def test_model_connection_truth_and_secret_free_projection(self):
  p=self.f.project();self.assertEqual(p['image_connection']['model'],self.f.ad.contract.MODEL);self.assertFalse(p['image_connection']['available']);self.assertTrue(p['image_connection']['can_prepare'])
  self.st.media_dispatch=None;p=self.f.project();self.assertEqual(p['image_connection']['state'],'unverified');self.assertFalse(p['image_connection']['can_prepare']);self.assertFalse(p['media_actions'][0]['can_execute'])
  serialized=json.dumps(p['media_actions']);self.assertNotIn('grant_id',serialized);self.assertNotIn('sha256',serialized);self.assertNotIn('Authorization',serialized)
 def test_empty_selected_disabled_retired_and_unverified_remain_distinct(self):
  import media_creator,model_selection
  self.st.media_dispatch=None;p=self.f.project();selected=model_selection.validate_selection('image','fal-flux-schnell')
  for status in ('integration_unverified','integration_blocked','retired','disabled','unavailable'):
   with self.subTest(status=status),patch('model_selection.validate_selection',return_value=dict(selected,state=status,reason='synthetic status explanation')):
    value=media_creator.capability(self.st,p,'image');self.assertEqual(value['model'],selected['model']);self.assertFalse(value['available']);self.assertFalse(value['can_prepare']);self.assertEqual(value['state'],'unverified' if status=='integration_unverified' else 'blocked');self.assertEqual(value['reason'],'synthetic status explanation')
  self.f.call('model_settings',song='synthetic',selections={'image':None},model_revision=p['model_settings']['revision'])
  value=self.f.project()['image_connection'];self.assertEqual(value['state'],'unconfigured');self.assertIsNone(value['model'])
 def test_cancel_before_submission_no_fake_network(self):
  j=self.decide('execute')['job'];self.f.call('cancel_generation',song='synthetic',job=j,reason='synthetic user cancellation');self.st.process_generation();self.assertEqual(self.card()['job']['state'],'cancelled');self.assertFalse(self.f.calls)

class MediaCreatorUITest(unittest.TestCase):
 def test_test_media_badge_uses_saved_provenance_not_only_reason_text(self):
  source=(Path(__file__).resolve().parents[1]/'index.html').read_text();line=next(x for x in source.splitlines() if x.startswith('function creatorTestMedia('))
  code="const assert=require('assert/strict');"+line+";assert(creatorTestMedia({reason:'file',provenance:{mode:'contract-fake'}}));assert(!creatorTestMedia({reason:'real file',provenance:{mode:'provider-unverified'}}));assert(!creatorTestMedia(null));"
  subprocess.run(['node','-e',code],check=True,capture_output=True)
 def test_actual_ui_markup_actions_model_rights_and_recovery(self):
  source=(Path(__file__).resolve().parents[1]/'index.html').read_text();code=source[source.index('function mediaPreparation('):source.index('function drawMediaCreator(')]
  script="const assert=require('assert/strict');const esc=x=>String(x).replaceAll('<','&lt;'),creatorDiagnostic=()=>'',shotName='scene',mediaRightsDrafts=new Map(),mediaDraftKey=x=>x;\n"+code+'''
const p={shots:{scene:{plan_id:'p',reference_head:1,reference_versions:[]}},guided_plans:[{id:'p',status:'applied'}],media_connections:{image:{can_prepare:true},video:{can_prepare:true}}};
assert(mediaPreparation(p,'image').ready);assert(!mediaPreparation(p,'video').ready);
p.shots.scene.reference_versions=[{id:1,status:'approved',roles:{start_frame:{shot:'scene',take:1,sha256:'x'}}}];assert(mediaPreparation(p,'video').ready);
const x={id:'a',shot:'scene',role:'image',model:'fal-example',prompt:'<unsafe>',options:{ratio:'16:9'},estimate:{amount:'0.01',currency:'USD'},can_approve:true,can_decide:true,mode:'contract-fake'};
let html=mediaActionMarkup(x);assert(html.includes('data-media-decision="approved"'));assert(!html.includes('data-media-decision="execute"'));assert(!html.includes('<unsafe>'));assert(html.includes('실제 AI 호출 없음'));
x.can_approve=false;x.can_execute=true;html=mediaActionMarkup(x);assert(html.includes('승인한 모의 작업 실행'));
x.job={id:'j',state:'import_blocked',recovery:{can_collect:true}};html=mediaActionMarkup(x);assert(html.includes('data-media-recover="collect"'));assert(!html.includes('data-media-decision'));
x.job={id:'j',state:'reconciliation_required',recovery:{}};html=mediaActionMarkup(x);assert(!html.includes('data-media-recover'));assert(!html.includes('data-media-decision'));
x.job.state='imported';x.candidate={take:1,selected:false,rights_known:false};html=mediaActionMarkup(x);assert(html.includes('아직 선택하지 않음'));assert(html.includes('data-media-rights'));assert(!html.includes('data-media-decision'));
'''
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'check.cjs';path.write_text(script);subprocess.run(['node',str(path)],check=True,capture_output=True)
  for token in ("act('media_action_decide'","act('recover_media_job'","act('declare_take_rights'","j.context.dispatch!=='fal-model-queue-v1'") :self.assertIn(token,source)
