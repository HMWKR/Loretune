import hashlib,json,tempfile,time,unittest,uuid
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from app import Store
import chat_runtime,chat_models,chat_adapters,contracts,model_selection

class MultiChatTest(unittest.TestCase):
 def scenario(self,key):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);st=Store(temp.name)
  def call(a,**d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
  call('project',name='Synthetic',era='default',story=0);call('model_settings',song='Synthetic',selections={'chat':key},model_revision=0)
  spec=chat_models.contract(key);sent=[];args=dict(goal='Mira synthetic',scenes='Mira in studio',style='',constraints='',kind='narrative')
  def transport(endpoint,headers,body):
   self.assertEqual(endpoint,spec['endpoint']);self.assertNotIn('Authorization',headers);sent.append(deepcopy(body))
   block=dict(type='function_call',call_id='same-call',id='item-id',name='propose_media_plan',arguments=json.dumps(args))
   output=[block,dict(type='reasoning',id='r',encrypted_content='PRIVATE_EPHEMERAL')] if len(sent)==1 else [dict(type='message',role='assistant',content=[dict(type='output_text',text='Proposal saved; not approved or generated.')])]
   return dict(id='response-id',status='completed',output=output,usage=dict(input_tokens=100,output_tokens=100),_request_id='fixture-request')
  ad=chat_adapters.ResponsesAdapter(key,lambda _:self.fail('secret read'),transport=transport,counter=lambda _:100)
  approval=dict(model=spec['model'],provider=spec['provider'],selection=key,workspace_id=st.workspace_id,project_id=contracts.project_id(st.workspace_id,'Synthetic'),synthetic_only=True,expires=time.time()+300,context_hash=model_selection.snapshot(st.state()['projects']['Synthetic'])['sha256'],prompt_hashes=[hashlib.sha256(b'Plan synthetic').hexdigest()],price_revision=spec['price_revision'],max_rounds=3,turn_cap_micro=100000)
  runtime=chat_runtime.ChatRuntime(st,ad,approval,Path(temp.name)/'usage.sqlite3');st.chat_runtime=runtime
  call('chat_turn',song='Synthetic',prompt='Plan synthetic');runtime.process_next()
  return st,runtime,sent,call
 def test_openai_and_grok_tool_results_reach_same_store(self):
  for key in ('openai-gpt-6-luna','xai-grok-4-7'):
   with self.subTest(key=key):
    st,rt,sent,_=self.scenario(key);p=st.state()['projects']['Synthetic'];turn=p['chat_turns'][-1]
    self.assertEqual(turn['status'],'completed');self.assertEqual(len(p['guided_plans']),1);self.assertEqual(len(sent),2)
    self.assertEqual(sent[1]['input'][-1]['type'],'function_call_output');self.assertEqual(sent[1]['input'][-1]['call_id'],'same-call')
    self.assertIn('PRIVATE_EPHEMERAL',json.dumps(sent[1]));self.assertNotIn('PRIVATE_EPHEMERAL',json.dumps(turn))
    self.assertEqual(p['guided_plans'][0]['source']['model'],rt.spec['model']);self.assertEqual(st.state()['generation_jobs'],[])
 def test_missing_counter_and_disabled_provider_never_reads_secret(self):
  for key in ('openai-gpt-6-luna','xai-grok-4-7'):
   ad=chat_adapters.ResponsesAdapter(key,lambda _:self.fail('secret read'))
   with self.assertRaises(ValueError):ad.count({})
   with self.assertRaises(ValueError):ad.complete({'model':ad.model,'store':False})
 def test_credentials_not_forwarded_to_redirect_or_logs(self):
  from urllib.error import HTTPError
  ad=chat_adapters.ResponsesAdapter('openai-gpt-6-luna',lambda _:'SECRET_CANARY',enabled=True,counter=lambda _:1)
  class Opener:
   def open(self,request,**kw):
    if request.full_url!='https://api.openai.com/v1/responses':raise AssertionError()
    raise HTTPError(request.full_url,302,'SECRET_CANARY',{},None)
  with patch('chat_adapters.build_opener',return_value=Opener()):
   with self.assertRaises(ValueError) as caught:ad.complete({'model':ad.model,'store':False})
  self.assertNotIn('SECRET_CANARY',str(caught.exception))
 def test_old_anthropic_grant_does_not_authorize_other_provider(self):
  st,rt,sent,call=self.scenario('xai-grok-4-7');rt.approval.pop('provider')
  with self.assertRaises(ValueError):call('chat_turn',song='Synthetic',prompt='Plan synthetic')
  self.assertEqual(len(sent),2)
 def test_router_never_falls_back(self):
  st,rt,sent,call=self.scenario('openai-gpt-6-luna')
  router=chat_runtime.ChatRouter(st,[]);st.chat_runtime=router
  self.assertFalse(router.capability('Synthetic',st.state()['projects']['Synthetic'])['available'])
  with self.assertRaises(ValueError):call('chat_turn',song='Synthetic',prompt='Plan synthetic')
 def test_handoff_contains_public_prior_answer_never_provider_state(self):
  st,rt,sent,call=self.scenario('xai-grok-4-7')
  call('chat_turn',song='Synthetic',prompt='Plan synthetic')
  with st.connect() as c:rows=c.execute('SELECT body FROM chat_turns ORDER BY rowid').fetchall()
  handoff=json.loads(rows[-1][0])['handoff'];text=json.dumps(handoff)
  self.assertIn('Proposal saved',text);self.assertNotIn('PRIVATE_EPHEMERAL',text);self.assertNotIn('same-call',text)
