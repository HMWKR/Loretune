import unittest,json
from copy import deepcopy
from tests import test_local_creation_tools as fx
import editing,local_creation_tools as local

class TimelineCommandsTest(unittest.TestCase):
 setUp=fx.LocalToolsTest.setUp
 call=fx.LocalToolsTest.call
 project=fx.LocalToolsTest.project
 tool=fx.LocalToolsTest.tool
 def args(self):return dict(description='순서·자막·원음 시작 검토',timeline_version=self.project()['timeline_head'],commands=[dict(op='reorder_clips',order=[1,0]),dict(op='set_captions',cues=[dict(start=0,end=1,text='새 한글 자막')]),dict(op='set_audio_offset',audio_version=1,source_offset_seconds=1)])
 def test_protocols_human_apply_preserves_sources_invalidates_approval_and_restore(self):
  before=deepcopy(self.project());args=self.args()
  for provider in ['anthropic','openai','xai']:
   out,_=self.tool('propose_timeline_changes',args,provider);self.assertEqual(out['status'],'proposed');self.assertFalse(out['applied']);self.assertFalse(out['captions_preserved'])
   self.assertEqual(editing.current(self.project()),editing.current(before))
  self.call('review_timeline_proposal',proposal_id=out['proposal_id'],timeline_version=1,decision='approved')
  after=self.project();t=editing.current(after)
  self.assertEqual(t['clips'],list(reversed(editing.current(before)['clips'])))
  self.assertEqual(t['subtitles'],args['commands'][1]['cues']);self.assertEqual(t['audio_offset'],1);self.assertNotIn('approval',t)
  self.assertEqual(after['shots'],before['shots']);self.assertEqual(after['audio_versions'],before['audio_versions']);self.assertEqual(after['timeline_versions'][0],before['timeline_versions'][0])
  self.call('restore_timeline',version=1);restored=editing.current(self.project());restored.pop('id');original=editing.current(before);original.pop('id');original.pop('approval')
  self.assertEqual(restored,original)
 def test_order_only_keeps_caption_absolute_times_and_audio(self):
  before=editing.current(self.project());args=self.args();args['commands']=args['commands'][:1]
  out,_=self.tool('propose_timeline_changes',args);proposal=next(x for x in self.project()['timeline_edit_proposals'] if x['id']==out['proposal_id'])
  self.assertEqual(proposal['timeline']['subtitles'],before['subtitles']);self.assertEqual(proposal['timeline']['audio_offset'],before['audio_offset'])
 def test_invalid_scope_permutation_cues_audio_and_duplicates_do_not_mutate(self):
  cases=[[dict(op='reorder_clips',order=[0])],[dict(op='reorder_clips',order=[0,0])],[dict(op='set_audio_offset',audio_version=99,source_offset_seconds=1)],[dict(op='set_captions',cues=[dict(start=0,end=5,text='too long')])],[dict(op='set_captions',cues=[])]*2,[dict(op='set_audio_offset',audio_version=1,source_offset_seconds=float('nan'))]]
  for commands in cases:
   before=deepcopy(self.project()['timeline_versions']);args=self.args();args['commands']=commands
   try:result,_=self.tool('propose_timeline_changes',args);self.assertEqual(result['status'],'blocked')
   except ValueError:pass
   self.assertEqual(self.project()['timeline_versions'],before)
 def test_clip_edits_address_base_occurrence_before_reorder(self):
  args=self.args();args['commands']=[dict(op='reorder_clips',order=[1,0]),dict(op='set_clip',clip_index=0,take=1,trim=.25,duration=.5)]
  result,_=self.tool('propose_timeline_changes',args);self.assertEqual(result['status'],'proposed')
  p=self.project()['timeline_edit_proposals'][-1]['timeline'];self.assertEqual(p['clips'][1]['trim'],.25);self.assertEqual(p['clips'][0]['trim'],0)

if __name__=='__main__':unittest.main()
