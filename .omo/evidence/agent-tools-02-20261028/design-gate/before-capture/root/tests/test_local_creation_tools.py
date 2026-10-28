import base64,hashlib,json,subprocess,time,unittest,uuid
from copy import deepcopy
from pathlib import Path
from app import Store
import chat_protocols,chat_runtime,contracts,editing,model_selection,ontology,project_ontology
from tests import test_editing as editing_fixture
from tests.test_chat_runtime import Fake,response,use

class LocalToolsTest(unittest.TestCase):
 def setUp(self):
  self.fixture=editing_fixture.EditingTest();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.st=self.fixture.store
  self.fixture.call('audio',filename='song.wav',content=base64.b64encode(self.fixture.wav.read_bytes()).decode(),rights='synthetic owned')
  timeline=self.fixture.timeline();timeline.update(audio=1,audio_offset=.5,subtitles=[dict(start=0,end=1,text='합성 자막 Mira')])
  for clip in timeline['clips']:clip['duration']=1
  self.fixture.save_approve(timeline)
 def call(self,a,**d):return self.fixture.call(a,**d)
 def project(self):return self.fixture.p()
 def tool(self,name,args,provider='anthropic',run=None,identifier=None):
  run=run or self.call('production_run')['run']['id'];external=identifier or uuid.uuid4().hex
  if provider=='anthropic':raw=dict(stop_reason='tool_use',content=[dict(type='tool_use',id=external,name=name,input=args)])
  else:raw=dict(status='completed',output=[dict(type='function_call',call_id=external,name=name,arguments=json.dumps(args))])
  normalized=chat_protocols.normalize(provider,raw,run);call=normalized['calls'][0]
  result=self.call('production_tool',run=run,call=call)['tool']
  receipt=chat_protocols.result_message(normalized,call['id'],result,provider=provider,run_id=run)
  self.assertIn(result['status'],json.dumps(receipt));return result,run
 def timeline_args(self):return dict(description='첫 컷만 트림 검토',timeline_version=self.project()['timeline_head'],changes=[dict(clip_index=0,take=1,trim=.25,duration=1)])
 def test_three_protocols_propose_without_applying_and_human_apply_preserves_other_inputs(self):
  before=deepcopy(self.project());args=self.timeline_args()
  for provider in ('anthropic','openai','xai'):
   result,_=self.tool('propose_timeline_edit',args,provider);self.assertEqual(result['status'],'proposed');self.assertFalse(result['applied']);self.assertEqual(self.project()['timeline_versions'],before['timeline_versions'])
  proposal=result['proposal_id']
  self.call('review_timeline_proposal',proposal_id=proposal,timeline_version=args['timeline_version'],decision='held');self.assertEqual(self.project()['timeline_head'],before['timeline_head'])
  out=self.call('review_timeline_proposal',proposal_id=proposal,timeline_version=args['timeline_version'],decision='approved')['timeline_proposal'];self.assertTrue(out['applied']);self.assertFalse(out['output_approved'])
  after=self.project();t=editing.current(after);old=editing.current(before)
  self.assertEqual(t['clips'][0]['trim'],.25);self.assertEqual(t['clips'][1],old['clips'][1]);self.assertNotIn('approval',t)
  for field in ('audio','audio_offset','subtitles','profile'):self.assertEqual(t[field],old[field])
  self.assertEqual(after['audio_versions'],before['audio_versions']);self.assertEqual(after['shots'],before['shots']);self.assertEqual(after['timeline_versions'][0],before['timeline_versions'][0])
  # Duplicate review doesn't append another timeline version.
  self.call('review_timeline_proposal',proposal_id=proposal,timeline_version=args['timeline_version'],decision='approved');self.assertEqual(len(self.project()['timeline_versions']),2)
  with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=proposal,timeline_version=args['timeline_version'],decision='rejected')
  self.assertEqual(len(self.project()['timeline_versions']),2)
 def test_stale_edit_and_foreign_proposal_rejected_without_mutation(self):
  result,_=self.tool('propose_timeline_edit',self.timeline_args());p=self.project();self.call('timeline',timeline=editing.current(p));before=deepcopy(self.project())
  with self.assertRaises(ValueError):self.call('review_timeline_proposal',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
  self.assertEqual(self.project(),before)
  self.call('project',name='other',era='default',story=0)
  with self.assertRaises(ValueError):self.call('review_timeline_proposal',song='other',proposal_id=result['proposal_id'],timeline_version=1,decision='approved')
 def memory_args(self):return dict(description='Mira wears blue in this project.',kind='character',label='Mira',entity_id='',source_id='canon:1',excerpt='Mira wears blue.',ontology_revision=0)
 def seed_memory_source(self):
  # Fixture uses the existing canonical project snapshot, no remote model/data.
  with self.st.connect() as c:
   rev,body=c.execute('SELECT revision,body FROM state').fetchone();state=json.loads(body);state['projects']['song']['snapshot']=[dict(id=1,text='Mira wears blue.')];c.execute('UPDATE state SET revision=?,body=?',(rev+1,json.dumps(state)))
 def test_memory_exact_provenance_human_application_and_global_canon_unchanged(self):
  self.seed_memory_source();before=deepcopy(self.st.state()['canon']);lookup,run=self.tool('search_project_context',{'query':'Mira'});self.assertIn({'id':'canon:1','text':'Mira wears blue.'},lookup['sources'])
  result,_=self.tool('propose_memory_update',self.memory_args(),run=run);self.assertEqual(result['status'],'proposed');self.assertFalse(result['canonical_approved']);self.assertEqual(self.project()['ontology']['revision'],0)
  self.call('ontology_apply',proposal=result['proposal_id'],ontology_revision=0,approved=True)
  entity=self.project()['ontology']['graph']['entities'][0];self.assertEqual(entity['uncertainty']['status'],'inferred');self.assertEqual(entity['provenance'],[dict(source_id='canon:1',excerpt='Mira wears blue.')]);self.assertEqual(self.st.state()['canon'],before)
 def test_memory_missing_source_stale_version_foreign_identity_and_actor_injection_blocked(self):
  self.seed_memory_source()
  for change in ({'source_id':'foreign:1'},{'excerpt':'Mira wears red.'},{'ontology_revision':3},{'entity_id':str(uuid.uuid4())}):
   args=self.memory_args();args.update(change);result,_=self.tool('propose_memory_update',args);self.assertEqual(result['status'],'blocked')
  self.assertEqual(self.project()['ontology_proposals'],[])
  args=self.memory_args();args['approved']=True
  with self.assertRaises(ValueError):self.tool('propose_memory_update',args)
 def grant(self):return editing.current(self.project())['approval']['id']
 def test_render_real_audio_caption_output_receipt_reuse_and_final_approval_separate(self):
  args=dict(timeline_version=self.project()['timeline_head'],grant_id=self.grant());receipt,_=self.tool('request_render',args)
  self.assertEqual(receipt['state'],'queued');self.assertFalse(receipt['finished_verified']);self.assertFalse(receipt['output_approved']);j=receipt['job_id']
  other,_=self.tool('request_render',args,'xai');self.assertEqual(other['job_id'],j)
  self.assertTrue(self.st.process_next());completed,_=self.tool('request_render',args,'openai');self.assertTrue(completed['finished_verified']);self.assertFalse(completed['output_approved'])
  result,_=self.tool('get_generation_job',{'job_id':j});self.assertEqual(result['job']['state'],'completed');self.assertEqual(result['job']['mode'],'local-render');self.assertTrue(result['job']['result']['sha256']);self.assertFalse(result['job']['result_approved'])
  out=self.st.root/'exports'/(j+'.mp4');metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));self.assertEqual({s['codec_type'] for s in metadata['streams']},{'video','audio','subtitle'});self.assertAlmostEqual(float(metadata['format']['duration']),2,places=2)
  text=subprocess.check_output(['ffmpeg','-v','error','-i',str(out),'-map','0:s:0','-f','srt','-']).decode();self.assertIn('합성 자막 Mira',text)
  self.call('delivery_review',job=j,decision='approved',reason='human reviewed synthetic output');last,_=self.tool('request_render',args);self.assertTrue(last['output_approved'])
  self.assertEqual(Store(self.fixture.temp.name).state()['jobs'][0]['sha256'],hashlib.sha256(out.read_bytes()).hexdigest())
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],1);self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
 def test_render_approval_stale_revoked_rights_and_cancellation_keep_existing_jobs(self):
  version=self.project()['timeline_head'];grant=self.grant();bad,_=self.tool('request_render',dict(timeline_version=version,grant_id='invented'));self.assertEqual(bad['status'],'blocked')
  bad,_=self.tool('request_render',dict(timeline_version=version+1,grant_id=grant));self.assertEqual(bad['code'],'STALE_VERSION')
  receipt,_=self.tool('request_render',dict(timeline_version=version,grant_id=grant));self.call('cancel_job',job=receipt['job_id']);self.assertFalse(self.st.process_next())
  same,_=self.tool('request_render',dict(timeline_version=version,grant_id=grant));self.assertEqual(same['state'],'cancelled');self.assertEqual(same['job_id'],receipt['job_id'])
  self.call('approve_timeline');newgrant=self.grant();sha=self.project()['shots']['a']['takes'][0]['sha256'];self.call('asset_rights',sha256=sha,blocked=True,reason='fixture revoke')
  denied,_=self.tool('request_render',dict(timeline_version=version,grant_id=newgrant));self.assertEqual(denied['status'],'blocked')
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],1)
 def test_fake_chat_runtime_roundtrip_uses_tools_not_prose_execution(self):
  self.call('model_settings',selections={'chat':'anthropic-haiku-5-5'},model_revision=0);prompt='Synthetic: propose a trim and queue the approved local render.'
  args=dict(timeline_version=self.project()['timeline_head'],grant_id=self.grant());fake=Fake([response([use('edit','propose_timeline_edit',self.timeline_args())],'tool_use'),response([use('render','request_render',args)],'tool_use'),response([dict(type='text',text='Edit proposed; current approved version queued, not finished or approved output.')])])
  approval=dict(model='claude-haiku-5-5',workspace_id=self.st.workspace_id,project_id=contracts.project_id(self.st.workspace_id,'song'),synthetic_only=True,expires=time.time()+300,context_hash=model_selection.snapshot(self.project())['sha256'],prompt_hashes=[hashlib.sha256(prompt.encode()).hexdigest()],price_revision='haiku-5-5-20261027-tiered',max_rounds=4)
  runtime=chat_runtime.ChatRuntime(self.st,fake,approval,self.st.root/'fake-usage.sqlite3');self.st.chat_runtime=runtime
  self.call('chat_turn',prompt=prompt);runtime.process_next();turn=self.project()['chat_turns'][-1];self.assertEqual(turn['status'],'completed');self.assertIn('queued',turn['answer']);self.assertEqual(len(self.project()['timeline_edit_proposals']),1)
  self.assertIn('proposal_id',json.dumps(fake.messages[1]));self.assertIn('job_id',json.dumps(fake.messages[2]));self.assertEqual(self.project()['timeline_head'],1)
 def test_duplicate_tool_call_does_not_duplicate_proposal(self):
  run=self.call('production_run')['run']['id'];first,_=self.tool('propose_timeline_edit',self.timeline_args(),run=run,identifier='same');second,_=self.tool('propose_timeline_edit',self.timeline_args(),run=run,identifier='same');self.assertEqual(first,second);self.assertEqual(len(self.project()['timeline_edit_proposals']),1)
 def test_render_transaction_rolls_back_estimate_when_existing_service_rejects(self):
  from unittest.mock import patch
  original=self.st.edit;before=deepcopy(self.project().get('render_estimates',[]))
  def fail(c,s,action,data):
   if action=='render_job':raise ValueError('synthetic fault after estimate')
   return original(c,s,action,data)
  with patch.object(self.st,'edit',side_effect=fail):result,_=self.tool('request_render',dict(timeline_version=1,grant_id=self.grant()))
  self.assertEqual(result['status'],'blocked');self.assertEqual(self.project().get('render_estimates',[]),before)
  with self.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],0)
 def test_render_snapshot_preserves_approved_audio_captions_while_editor_advances(self):
  receipt,_=self.tool('request_render',dict(timeline_version=1,grant_id=self.grant()));j=receipt['job_id']
  current=editing.current(self.project());current['clips'][0]['duration']=.5;current['subtitles'][0]['text']='아직 승인 안 된 새 자막';self.call('timeline',timeline=current)
  denied,_=self.tool('request_render',dict(timeline_version=2,grant_id=receipt['job_id']));self.assertEqual(denied['status'],'blocked')
  self.assertTrue(self.st.process_next())
  with self.st.connect() as c:job=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(j,)).fetchone()[0])
  self.assertEqual(job['snapshot']['timeline']['id'],1);self.assertEqual(job['snapshot']['audio_offset'],.5);self.assertEqual(job['snapshot']['subtitles'][0]['text'],'합성 자막 Mira');self.assertEqual(job['status'],'completed')
  self.assertEqual(self.project()['timeline_head'],2)
 def test_memory_duplicate_identity_preservation_and_foreign_render_job_isolation(self):
  self.seed_memory_source();run=self.call('production_run')['run']['id'];first,_=self.tool('propose_memory_update',self.memory_args(),run=run,identifier='one');again,_=self.tool('propose_memory_update',self.memory_args(),run=run,identifier='one');self.assertEqual(first,again);self.assertEqual(len(self.project()['ontology_proposals']),1)
  self.call('ontology_apply',proposal=first['proposal_id'],ontology_revision=0,approved=True);eid=self.project()['ontology']['graph']['entities'][0]['id'];args=self.memory_args();args.update(entity_id=eid,ontology_revision=1,description='Mira keeps blue clothes in this project.')
  update,_=self.tool('propose_memory_update',args);self.assertEqual(self.project()['ontology']['revision'],1)
  candidate=next(p for p in self.project()['ontology_proposals'] if p['id']==update['proposal_id']);self.assertEqual([e['id'] for e in candidate['graph']['entities']],[eid])
  job,_=self.tool('request_render',dict(timeline_version=1,grant_id=self.grant()));self.call('project',name='other',era='default',story=0);foreign_run=self.call('production_run',song='other')['run']['id']
  out=self.call('production_tool',song='other',run=foreign_run,call=dict(id='foreign',name='get_generation_job',arguments={'job_id':job['job_id']},complete=True))['tool'];self.assertEqual(out['status'],'not_found')
