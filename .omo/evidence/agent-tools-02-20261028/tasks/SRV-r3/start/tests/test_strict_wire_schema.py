import json,unittest
from copy import deepcopy
import chat_models,chat_protocols,motion_scene,production_tools
from tests.test_motion import scene

class StrictWireSchemaTest(unittest.TestCase):
 def test_nested_bounds_become_descriptions_without_mutating_source(self):
  tools=chat_protocols.tool_definitions('anthropic')
  for tool in tools:tool['strict']=True
  original=deepcopy(tools)
  body=chat_models.body(chat_models.contract('anthropic-haiku-5-5'),[],tools,8192)
  def walk(value):
   if isinstance(value,dict):
    self.assertFalse(set(value)&{'minimum','maximum','maxItems','minLength','maxLength'})
    for v in value.values():walk(v)
   elif isinstance(value,list):
    for v in value:walk(v)
  walk(body['tools']);self.assertEqual(tools,original)
  self.assertTrue(all(x['strict'] for x in body['tools']))
  motion=next(x for x in body['tools'] if x['name']=='propose_motion_scene')['input_schema']['properties']['scene']
  self.assertIn('96',motion['properties']['frame_count']['description'])
  self.assertEqual(motion['properties']['layers']['minItems'],1)
  self.assertIn('8',motion['properties']['layers']['description'])
 def test_local_motion_and_edit_bounds_remain_enforced(self):
  value=scene();value['frame_count']=97
  with self.assertRaises(ValueError):motion_scene.validate(value)
  value=scene();value['layers'][0]['keyframes'][0]['opacity']=2
  with self.assertRaises(ValueError):production_tools.validate('propose_motion_scene',dict(shot_id='s',base_motion_revision=0,scene=value))
  with self.assertRaises(ValueError):production_tools.validate('propose_timeline_changes',dict(description='bad',timeline_version=1,commands=[dict(op='set_audio_offset',audio_version=1,source_offset_seconds=-1)]))
 def test_property_names_not_treated_as_schema_keywords(self):
  source=dict(type='object',properties={'minimum':dict(type='integer',minimum=2)},required=['minimum'],additionalProperties=False)
  out=chat_models.anthropic_wire_schema(source)
  self.assertIn('minimum',out['properties']);self.assertNotIn('minimum',out['properties']['minimum'])
  self.assertEqual(source['properties']['minimum']['minimum'],2)
 def test_other_provider_contracts_unchanged(self):
  for name in ['openai-gpt-6-luna','xai-grok-4-7']:
   spec=chat_models.contract(name);tools=chat_protocols.tool_definitions(spec['provider'])
   self.assertEqual(chat_models.body(spec,[],tools,8192)['tools'],tools)

if __name__=='__main__':unittest.main()
