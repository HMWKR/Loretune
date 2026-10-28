import unittest,json
import chat_protocols as c
class ChatProtocolsTest(unittest.TestCase):
 def response(self,p,args=None):
  args=args if args is not None else {'role':'image'}
  if p=='anthropic':return dict(stop_reason='tool_use',content=[dict(type='tool_use',id='external',name='get_model_capabilities',input=args)])
  return dict(status='completed',output=[dict(type='function_call',call_id='external',name='get_model_capabilities',arguments=json.dumps(args))])
 def test_three_protocols_preserve_call_link_and_do_not_execute(self):
  for p in c.PROVIDERS:
   n=c.normalize(p,self.response(p),'run');call=n['calls'][0]
   self.assertNotEqual(call['id'],'external');self.assertEqual(call['arguments'],{'role':'image'})
   result=c.result_message(n,call['id'],{'status':'blocked'},provider=p,run_id='run')
   self.assertIn('external',str(result))
   with self.assertRaises(ValueError):c.result_message(n,call['id'],{},provider=p,run_id='other')
   with self.assertRaises(ValueError):c.result_message(n,call['id'],{},provider='xai' if p!='xai' else 'openai',run_id='run')
 def test_incomplete_refusal_bad_args_and_builtin_tools_never_normalize(self):
  for p in c.PROVIDERS:
   bad=self.response(p,{'role':'image','approved':True})
   with self.assertRaises(ValueError):c.normalize(p,bad,'r')
   bad=self.response(p);bad['stop_reason' if p=='anthropic' else 'status']='incomplete'
   with self.assertRaises(ValueError):c.normalize(p,bad,'r')
  for block in [dict(type='refusal'),dict(type='web_search_call')]:
   with self.assertRaises(ValueError):c.normalize('openai',dict(status='completed',output=[block]),'r')
 def test_duplicate_json_and_partial_arguments_rejected(self):
  for raw in ['{"role":"image","role":"video"}','{"role":']:
   r=self.response('xai');r['output'][0]['arguments']=raw
   with self.assertRaises(ValueError):c.normalize('xai',r,'r')
 def test_handoff_omits_reasoning_provider_ids_and_foreign_jobs(self):
  p=dict(snapshot=[{'text':'blue coat'}],shots={},conversation=[dict(role='user',text='keep coat',provider_call_id='private'),dict(role='reasoning',text='hidden')],embedding={'revision':7})
  original=json.dumps(p,sort_keys=True)
  result=c.handoff(p,'A',[dict(id='one',state='accepted',context={'song':'A'},receipt='secret'),dict(id='foreign',state='running',context={'song':'B'})])
  self.assertNotIn('secret',str(result));self.assertNotIn('hidden',str(result));self.assertNotIn('private',str(result));self.assertNotIn('foreign',str(result))
  self.assertEqual(result['jobs'],[{'id':'one','state':'accepted','mode':'provider-unverified'}]);self.assertEqual(json.dumps(p,sort_keys=True),original)
 def test_three_provider_envelopes_use_same_persisted_local_plan_tool(self):
  import tempfile,uuid
  from app import Store
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder)
   def act(action,data):return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
   act('project',dict(name='A',era='default',story=0))
   args=dict(goal='same goal',scenes='Mira keeps blue coat',style='',constraints='',kind='narrative')
   for provider in c.PROVIDERS:
    run=act('production_run',{'song':'A'})['run']
    response=self.response(provider)
    block=response['content' if provider=='anthropic' else 'output'][0];block['name']='propose_media_plan';block['input' if provider=='anthropic' else 'arguments']=args if provider=='anthropic' else json.dumps(args)
    normalized=c.normalize(provider,response,run['id']);call=normalized['calls'][0]
    result=act('production_tool',dict(song='A',run=run['id'],call=call))['tool']
    self.assertEqual(result['plan']['scenes'][0]['description'],'Mira keeps blue coat')
    self.assertIn('proposed',str(c.result_message(normalized,call['id'],result,provider=provider,run_id=run['id'])))
   state=Store(folder).state();self.assertEqual(len(state['projects']['A']['guided_plans']),3);self.assertEqual(state['generation_jobs'],[])
 def test_definitions_are_strict_and_malformed_blocks_fail_closed(self):
  for provider in c.PROVIDERS:
   definitions=c.tool_definitions(provider);self.assertEqual(len(definitions),11)
   self.assertTrue({'prepare_image_action','prepare_video_action'} <= {d['name'] for d in definitions})
   for d in definitions:
    schema=d.get('input_schema',d.get('parameters'));self.assertFalse(schema['additionalProperties']);self.assertEqual(set(schema['required']),set(schema['properties']))
  for blocks in [[None],[{'type':'message','content':None}]]:
   with self.assertRaises(ValueError):c.normalize('openai',dict(status='completed',output=blocks),'run')
