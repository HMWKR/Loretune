import json,unittest,uuid
from copy import deepcopy
from unittest.mock import patch
from tests import test_motion as mf,test_local_creation_tools as tf
import chat_models,editing,production_context,production_tools,local_creation_tools

class MotionApprovalContextTest(unittest.TestCase):
 setUp=mf.MotionTest.setUp
 call=mf.MotionTest.call
 p=mf.MotionTest.p
 args=mf.MotionTest.args
 proposal=mf.MotionTest.proposal
 approve=mf.MotionTest.approve
 def approved(self):
  with patch.object(mf.raster,'validate_text',return_value={}):self.approve(self.proposal())
  return deepcopy(self.p()['shots']['s']['motion_versions'][0])
 def context(self,p=None):
  with self.st.connect() as c:return production_context.read(c,self.st,p or self.p(),'A')['shots'][0]['motion']
 def test_recorded_approval_and_pending_proposal_are_distinct_in_search_and_handoff(self):
  v=self.approved();pending=self.proposal();before=deepcopy(self.p())
  h=self.call('model_handoff')['handoff']['execution_targets']['shots'][0]['motion']
  run=self.call('production_run')['run']['id']
  result=self.call('production_tool',run=run,call=dict(id='read',name='search_project_context',arguments={'query':'current motion approval'},complete=True))['tool']
  self.assertEqual(h,result['execution_targets']['shots'][0]['motion'])
  self.assertEqual(h['approval']['actor'],'local-owner');self.assertEqual(h['approval']['scope'],'local-motion-candidate');self.assertEqual(h['approval']['motion_revision'],1)
  self.assertEqual(h['approval']['scene_hash'],v['scene_hash']);self.assertTrue(h['approval']['requires_revalidation']);self.assertEqual(h['approval_status'],'recorded')
  self.assertEqual(h['proposals'],[dict(proposal_id=pending,base_revision=1,status='proposed',applied=False,requires_human_review=True)])
  self.assertEqual(self.p()['shots'],before['shots']);self.assertEqual(self.p()['motion_proposals'],before['motion_proposals']);self.assertEqual(self.st.state()['jobs'],[])
 def test_unapproved_foreign_and_rejected_are_not_approval(self):
  item=self.proposal();self.call('motion_review',proposal_id=item,decision='rejected')
  self.assertIsNone(self.context()['approval']);self.assertIsNone(self.context()['grant_id']);self.assertFalse(self.context()['proposals'][0]['requires_human_review'])
  v=self.approved();self.call('project',name='B',era='default',story=0);self.call('shot',song='B',shot='s',description='foreign')
  h=self.call('model_handoff',song='B')['handoff']['execution_targets']
  self.assertNotIn(v['approval']['id'],json.dumps(h));self.assertIsNone(h['shots'][0]['motion']['approval'])
 def test_stale_context_and_broken_bindings_never_expose_current_grant(self):
  self.approved();p=self.p();p['shots']['s']['description']='changed context'
  h=self.context(p);self.assertEqual(h['approval_status'],'stale_context');self.assertFalse(h['approval']['matches_current_context']);self.assertIsNone(h['grant_id'])
  for field,value in [('actor','model'),('scope','final-delivery'),('scene_hash','wrong')]:
   p=self.p();p['shots']['s']['motion_versions'][0]['approval'][field]=value
   h=self.context(p);self.assertIsNone(h['approval']);self.assertIsNone(h['grant_id'])
  p=self.p();p['shots']['s']['motion_head']=999;self.assertIsNone(self.context(p)['approval'])
  p=self.p();p['shots']['s']['motion_versions'][0]['scene']['background']='#FFFFFF';self.assertIsNone(self.context(p)['grant_id'])
 def test_model_cannot_inject_approval_and_old_grant_stays_rejected(self):
  v=self.approved()
  for field,value in [('actor','local-owner'),('approved',True),('scope','local-motion-candidate')]:
   with self.assertRaises(ValueError):production_tools.validate('propose_motion_scene',dict(self.args(),**{field:value}))
  with patch.object(mf.raster,'validate_text',return_value={}):self.approve(self.proposal())
  for revision,grant in [(1,v['approval']['id']),(2,v['approval']['id']),(2,'foreign')]:
   with self.assertRaises(ValueError):self.call('motion_render',shot_id=self.args()['shot_id'],motion_revision=revision,grant_id=grant)
  self.assertEqual(self.st.state()['jobs'],[])
 def test_system_distinguishes_motion_ontology_and_new_proposals(self):
  self.assertIn('motion.approval',chat_models.SYSTEM);self.assertIn('ontology is null',chat_models.SYSTEM);self.assertIn('timeline_diff',chat_models.SYSTEM)
  self.assertIn('already saved/applied composition version',chat_models.SYSTEM);self.assertIn('does not require an adopted timeline Take or project audio',chat_models.SYSTEM)

class TimelineDiffTest(unittest.TestCase):
 setUp=tf.LocalToolsTest.setUp
 call=tf.LocalToolsTest.call
 project=tf.LocalToolsTest.project
 tool=tf.LocalToolsTest.tool
 def args(self,commands):return dict(description='synthetic request description is not authoritative diff',timeline_version=self.project()['timeline_head'],commands=commands)
 def test_order_caption_audio_before_after_without_apply_and_duplicate_same_receipt(self):
  before=deepcopy(self.project());base=editing.current(before)
  commands=[dict(op='reorder_clips',order=[1,0]),dict(op='set_captions',cues=[dict(start=0,end=1,text='새 자막')]),dict(op='set_audio_offset',audio_version=1,source_offset_seconds=1)]
  r,run=self.tool('propose_timeline_changes',self.args(commands),identifier='same')
  again,_=self.tool('propose_timeline_changes',self.args(commands),run=run,identifier='same');self.assertEqual(r,again)
  d=r['timeline_diff'];self.assertEqual(r['changes'],[]);self.assertEqual(r['changes_scope'],'clip_take_trim_duration')
  self.assertEqual(d['clip_order'],dict(changed=True,before=[0,1],after=[1,0]));self.assertEqual(d['clips'],[])
  self.assertEqual(d['captions'],dict(changed=True,before=base['subtitles'],after=commands[1]['cues']))
  self.assertEqual(d['audio'],dict(changed=True,before=dict(version=1,source_offset_seconds=.5),after=dict(version=1,source_offset_seconds=1)))
  self.assertEqual(self.project()['timeline_versions'],before['timeline_versions']);self.assertFalse(r['applied']);self.assertFalse(r['output_approved']);self.assertEqual(len(self.project()['timeline_edit_proposals']),1)
  self.assertEqual(self.project()['timeline_edit_proposals'][0]['timeline_diff'],d)
 def test_single_category_changes_do_not_invent_others(self):
  cases=[('clip_order',dict(op='reorder_clips',order=[1,0])),('captions',dict(op='set_captions',cues=[])),('audio',dict(op='set_audio_offset',audio_version=1,source_offset_seconds=1))]
  for category,command in cases:
   r,_=self.tool('propose_timeline_changes',self.args([command]));d=r['timeline_diff']
   for key in ['clip_order','captions','audio']:self.assertEqual(d[key]['changed'],key==category)
   self.assertEqual(d['clips'],[])
 def test_clip_plus_reorder_tracks_base_occurrence_and_filters_noops(self):
  cmds=[dict(op='set_clip',clip_index=0,take=1,trim=.25,duration=.5),dict(op='reorder_clips',order=[1,0])]
  r,_=self.tool('propose_timeline_changes',self.args(cmds));d=r['timeline_diff'];self.assertEqual(d['clips'],[dict(base_clip_index=0,proposed_clip_index=1,before=dict(take=1,trim=0,duration=1),after=dict(take=1,trim=.25,duration=.5))])
  r,_=self.tool('propose_timeline_changes',self.args([dict(op='set_clip',clip_index=0,take=1,trim=0,duration=1),dict(op='reorder_clips',order=[0,1])]))
  self.assertEqual(r['timeline_diff']['clips'],[]);self.assertEqual(r['timeline_diff']['clip_order'],dict(changed=False))
  self.assertNotIn('before',r['timeline_diff']['captions'])
 def test_duplicate_shot_occurrences_are_identified_by_base_index(self):
  base=editing.current(self.project());base['clips'][1]=deepcopy(base['clips'][0]);candidate=deepcopy(base)
  d=local_creation_tools.timeline_diff(base,candidate,[1,0]);self.assertEqual(d['clip_order']['after'],[1,0]);self.assertEqual(d['clips'],[])
 def test_hold_reject_stale_and_applied_receipts_keep_approval_boundaries(self):
  args=self.args([dict(op='reorder_clips',order=[1,0])]);r,_=self.tool('propose_timeline_changes',args)
  for state in ['held','rejected']:
   out=self.call('review_timeline_proposal',proposal_id=r['proposal_id'],timeline_version=1,decision=state)['timeline_proposal'];self.assertFalse(out['applied']);self.assertFalse(out['output_approved'])
  out=self.call('review_timeline_proposal',proposal_id=r['proposal_id'],timeline_version=1,decision='approved')['timeline_proposal'];self.assertTrue(out['applied']);self.assertFalse(out['output_approved'])
  stale,_=self.tool('propose_timeline_changes',args);self.assertEqual(stale['status'],'blocked')
  self.assertEqual(len(self.project()['timeline_edit_proposals']),1)

if __name__=='__main__':unittest.main()
