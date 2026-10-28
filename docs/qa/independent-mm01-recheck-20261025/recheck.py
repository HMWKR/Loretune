import sys,socket,unittest,json,uuid
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent/'snapshot'))
from tests.test_local_creation_tools import LocalToolsTest
from tests.test_fal_multimodel import FalMultiTest
import action_execution as actions,editing
E={}
class Recheck(unittest.TestCase):
 def local(self):
  f=LocalToolsTest();f.setUp();self.addCleanup(f.doCleanups);return f
 def media(self):
  f=FalMultiTest();f.setUp();self.addCleanup(f.doCleanups);f.setup_model('fal-flux-schnell');return f
 def test_render_handles_after_switch_and_stale_timeline(self):
  f=self.local();ids=[]
  for model in ['anthropic-haiku-5-5','xai-grok-4-7']:
   f.call('model_settings',selections={'chat':model},model_revision=f.project()['model_settings']['revision'])
   ctx,run=f.tool('search_project_context',{'query':'current approved timeline'})
   target=ctx['execution_targets']['timeline'];args={'timeline_version':target['version'],'grant_id':target['grant_id']}
   result,_=f.tool('request_render',args,run=run);self.assertIn(result['status'],['accepted','existing']);ids.append(result['job_id'])
  self.assertEqual(ids[0],ids[1]);E['render_lookup_only']={'status':'pass','same_job_after_switch':True,'args_from':'search_project_context.execution_targets.timeline'}
  f.call('timeline',timeline=editing.current(f.project()));result,_=f.tool('request_render',args);self.assertEqual(result['code'],'STALE_VERSION')
  E['stale_timeline']=result
 def test_approved_media_lookup_then_foreign_and_revoke(self):
  f=self.media();f.call('model_settings',song='synthetic',selections={'chat':'xai-grok-4-7'},model_revision=f.project()['model_settings']['revision'])
  run=f.call('production_run',song='synthetic')['run']['id']
  def tool(name,args,song='synthetic',run=run):return f.call('production_tool',song=song,run=run,call=dict(id=uuid.uuid4().hex,name=name,arguments=args,complete=True))['tool']
  ctx=tool('search_project_context',{'query':'approved actions'})['execution_targets'];a=next(a for a in ctx['actions'] if a['approval_handles']);g=a['approval_handles'][0];shot=next(s for s in ctx['shots'] if s['shot_id']==a['shot_id'])
  prep=tool('prepare_image_action',dict(shot_id=shot['shot_id'],shot_revision=shot['revision'],model_id='fal-flux-schnell',prompt='blue geometry',ratio='16:9'));self.assertEqual(prep['status'],'proposed')
  args=dict(plan_id=a['plan_id'],action_id=a['action_id'],grant_id=g['grant_id']);result=tool('request_media_generation',args);self.assertEqual(result['status'],'accepted')
  E['media_lookup_only']={'stable_shot_preparation':prep['status'],'approved_action':result['status'],'external_calls':len(f.calls)}
  f.call('project',name='foreign',era='default',story=0);fr=f.call('production_run',song='foreign')['run']['id'];foreign=tool('search_project_context',{'query':'actions'},'foreign',fr)['execution_targets'];self.assertEqual(foreign['actions'],[])
  denied=tool('request_media_generation',args,'foreign',fr);self.assertNotIn(denied['status'],['accepted','existing']);E['foreign_action']=denied
  with f.st.connect() as c:actions.revoke(c,f.w,f.pid,g['grant_id'],1)
  now=tool('search_project_context',{'query':'actions'})['execution_targets'];self.assertFalse(next(x for x in now['actions'] if x['action_id']==a['action_id'])['approval_handles'])
  f.st.process_generation();self.assertEqual(f.st.generation.get(result['job_id'])['state'],'submission_blocked');self.assertEqual(f.calls,[]);E['revoke_after_lookup']='submission_blocked; zero transport calls'
 def test_foreign_render_handle_rejected_and_readonly_lookup(self):
  f=self.local();before=f.project();lookup,run=f.tool('search_project_context',{'query':'targets'});target=lookup['execution_targets']['timeline']
  after=f.project();self.assertEqual(before['timeline_versions'],after['timeline_versions']);self.assertEqual(before['ontology'],after['ontology'])
  f.call('project',name='other',era='default',story=0);fr=f.call('production_run',song='other')['run']['id']
  res=f.call('production_tool',song='other',run=fr,call=dict(id='foreign',name='request_render',arguments=dict(timeline_version=target['version'],grant_id=target['grant_id']),complete=True))['tool'];self.assertEqual(res['status'],'blocked');E['foreign_render']=res
  with f.st.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0],0)
def no_network(*a,**kw):raise AssertionError('network/listener prohibited')
if __name__=='__main__':
 with patch.object(socket.socket,'connect',no_network),patch.object(socket.socket,'bind',no_network),patch('socket.create_connection',no_network):
  suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Recheck),unittest.defaultTestLoader.loadTestsFromNames(['tests.test_execution_context','tests.test_local_creation_tools','tests.test_chat_protocols','tests.test_execution_disclosure'])]);res=unittest.TextTestRunner(verbosity=2).run(suite)
 Path(__file__).with_name('evidence.json').write_text(json.dumps(E,ensure_ascii=False,indent=2));sys.exit(not res.wasSuccessful())
