import json,unittest,uuid
from tests import test_local_creation_tools as local_fixture,test_fal_multimodel as fal_fixture
import production_context

class ExecutionContextTest(unittest.TestCase):
 def test_handoff_lookup_render_uses_only_server_visible_handles_after_model_switch(self):
  f=local_fixture.LocalToolsTest();f.setUp();self.addCleanup(f.doCleanups)
  for selection in ('anthropic-haiku-5-5','openai-gpt-6-luna'):
   f.call('model_settings',selections={'chat':selection},model_revision=f.project()['model_settings']['revision'])
   h=f.call('model_handoff')['handoff']['execution_targets'];lookup,run=f.tool('search_project_context',{'query':'current approved targets'})
   self.assertEqual(h,lookup['execution_targets']);t=h['timeline'];self.assertTrue(t['grant_id']);self.assertEqual(len(t['clips']),2)
   result,_=f.tool('request_render',{'timeline_version':t['version'],'grant_id':t['grant_id']},run=run);self.assertIn(result['status'],['accepted','existing'])
  with f.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],1)
  self.assertNotIn('asset',h['shots'][0]['takes'][0]);self.assertNotIn(str(f.st.root),json.dumps(h))
 def test_unsubmitted_action_grant_and_stable_shot_are_discoverable_and_route_after_switch(self):
  fal_fixture.FalMultiTest.setUpClass();f=fal_fixture.FalMultiTest();f.setUp();self.addCleanup(f.doCleanups);f.setup_model('fal-flux-schnell')
  f.call('model_settings',song='synthetic',selections={'chat':'openai-gpt-6-luna'},model_revision=f.project()['model_settings']['revision'])
  h=f.call('model_handoff',song='synthetic')['handoff']['execution_targets'];a=next(x for x in h['actions'] if x['action_id']==f.action['id']);self.assertEqual(a['approval_handles'][0]['grant_id'],f.grant['id'])
  run=f.call('production_run',song='synthetic')['run']['id'];shot=next(x for x in h['shots'] if x['shot_id']==a['shot_id'])
  def tool(n,args):return f.call('production_tool',song='synthetic',run=run,call=dict(id=uuid.uuid4().hex,name=n,arguments=args,complete=True))['tool']
  proposed=tool('prepare_image_action',dict(shot_id=shot['shot_id'],shot_revision=shot['revision'],model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9'));self.assertEqual(proposed['status'],'proposed')
  receipt=tool('request_media_generation',dict(plan_id=a['plan_id'],action_id=a['action_id'],grant_id=a['approval_handles'][0]['grant_id']));self.assertEqual(receipt['status'],'accepted')
  f.call('project',name='foreign',era='default',story=0)
  foreign=f.call('model_handoff',song='foreign')['handoff']['execution_targets'];self.assertEqual(foreign['actions'],[]);self.assertEqual(foreign['shots'],[])
 def test_canonical_shot_mapping_rejects_ambiguous_and_foreign_id(self):
  p={'name':'A','shots':{'first':{'stable_id':'stable'},'second':{'stable_id':'other'}}}
  self.assertEqual(production_context.shot_key(p,'stable'),'first');self.assertEqual(production_context.shot_key(p,'first'),'first')
  with self.assertRaises(ValueError):production_context.shot_key(p,'foreign')
  p['shots']['stable']={'stable_id':'third'}
  with self.assertRaises(ValueError):production_context.shot_key(p,'stable')
