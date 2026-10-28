"""CC01: request evidence survives the recent-dialogue window; no live calls."""
import hashlib,json
from copy import deepcopy
from app import Store
import chat_runtime as chat,contracts,model_selection
from tests import test_chat_runtime as fixture
Fake,response,PROMPT=fixture.Fake,fixture.response,fixture.PROMPT

class RequestHistoryTest(__import__('unittest').TestCase):
 setUp=fixture.ChatRuntimeTest.setUp
 call=fixture.ChatRuntimeTest.call
 connect=fixture.ChatRuntimeTest.connect
 turn=fixture.ChatRuntimeTest.turn
 rows=fixture.ChatRuntimeTest.rows
 def send(self,prompt,adapter=None):
  self.connect(adapter or Fake([response()]))
  self.runtime.approval['prompt_hashes']=[hashlib.sha256(prompt.encode()).hexdigest()]
  identifier=self.call('chat_turn',song='A',prompt=prompt)['chat_turn']['id']
  self.runtime.process_next()
  with self.st.connect() as c:return chat.get(c,identifier)
 def seed(self,prompts,status='completed',name='A'):
  project=contracts.project_id(self.st.workspace_id,name)
  with self.st.connect() as c:
   for i,p in enumerate(prompts):chat.put(c,dict(id=name+':seed:'+str(i),project=project,prompt=p,status=status,answer='Unreviewed synthetic answer',run='seed'))
 def test_original_nine_turn_counterexample_and_store_resume(self):
  first='SESSION-LONG-913: For this session never orbit the camera.'
  for prompt in [first]+['Synthetic neutral turn '+str(i) for i in range(2,10)]:self.assertEqual(self.send(prompt)['status'],'completed')
  self.st=Store(self.root);t=self.send('Continue with all prior session requests.')
  self.assertIn(first,json.dumps(self.adapter.messages,ensure_ascii=False))
  history=t['handoff']['session_request_history'];self.assertEqual(len(history['requests']),9)
  self.assertEqual(history['requests'][0]['text'],first)
  self.assertEqual(len([m for m in t['handoff']['messages'] if m['role']=='user']),8)
  self.assertEqual(history['scope'],dict(workspace_id=self.st.workspace_id,project_id=t['project'],conversation='project-default'))
  self.assertEqual(history['schema_version'],1)
  self.assertEqual(history['digest'],__import__('guided').fingerprint({k:v for k,v in history.items() if k!='digest'}))
 def test_quoted_conditional_corrected_and_retracted_requests_are_evidence_not_canon(self):
  prompts=['Never orbit the camera.','Quotation only: "orbit the camera" is a bad example.',
           'If I approve a later alternative, then permit orbit; no such approval yet.',
           'Correction: the ban applies only to scene 1.',
           'Release my scene 1 camera-orbit prohibition; keep the no-text rule.']
  self.seed(prompts);before=deepcopy(self.st.state()['projects']['A']['ontology'])
  t=self.send(PROMPT);records=t['handoff']['session_request_history']['requests']
  self.assertEqual([r['text'] for r in records],prompts)
  for i,r in enumerate(records,1):
   self.assertEqual(set(r),{'turn_id','sequence','text','source_hash','status'})
   self.assertEqual(r['sequence'],i);self.assertEqual(r['source_hash'],hashlib.sha256(r['text'].encode()).hexdigest())
  self.assertEqual(self.st.state()['projects']['A']['ontology'],before)
  self.assertNotIn('active_constraints',t['handoff'])
 def test_failed_cancelled_and_unreviewed_answers_never_become_canonical(self):
  self.seed(['Cancelled request'],status='cancelled');self.seed(['Failed request'],status='failed',name='B')
  t=self.send(PROMPT);h=t['handoff']['session_request_history']
  self.assertEqual(h['requests'][0]['status'],'cancelled')
  self.assertNotIn('Failed request',json.dumps(t['handoff']))
  self.assertNotIn('Unreviewed synthetic answer',json.dumps(h))
 def test_project_isolation_and_explicit_order_after_record_update(self):
  self.seed(['A first','A second']);self.seed(['FOREIGN-B-CANARY'],name='B')
  with self.st.connect() as c:
   t=chat.get(c,'A:seed:0');t['status']='cancelled';chat.put(c,t)
  t=self.send(PROMPT);h=t['handoff']['session_request_history']
  self.assertEqual([r['text'] for r in h['requests']],['A first','A second'])
  self.assertNotIn('FOREIGN-B-CANARY',json.dumps(self.adapter.messages))
 def test_count_over_limit_keeps_history_and_never_calls_messages(self):
  first='OLD-RETAINED-CANARY';self.seed([first]+['neutral '+str(i) for i in range(9)])
  fake=Fake();fake.tokens=4097;t=self.send(PROMPT,fake)
  self.assertEqual(t['status'],'blocked_before_message');self.assertEqual(fake.messages,[])
  self.assertIn(first,json.dumps(fake.counts));self.assertEqual(self.rows()[0][1],0)
  self.assertEqual(len(t['handoff']['session_request_history']['requests']),10)
 def test_handoff_is_frozen_when_persisted_history_changes(self):
  self.seed(['Original request']);self.connect(Fake([response()]))
  identifier=self.call('chat_turn',song='A',prompt=PROMPT)['chat_turn']['id']
  with self.st.connect() as c:
   prior=chat.get(c,'A:seed:0');prior['prompt']='Later test mutation';chat.put(c,prior)
  self.runtime.process_next()
  with self.st.connect() as c:t=chat.get(c,identifier)
  self.assertEqual(t['handoff']['session_request_history']['requests'][0]['text'],'Original request')
 def test_same_project_independent_session_still_not_advertised(self):
  self.connect(Fake())
  with self.assertRaises(ValueError):self.call('chat_turn',song='A',prompt=PROMPT,session_id='invented')
