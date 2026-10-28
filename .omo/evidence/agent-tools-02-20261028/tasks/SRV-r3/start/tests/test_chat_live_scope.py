import unittest
import test_chat_runtime as base
from test_chat_runtime import Fake,response,use,ARGS,PROMPT
import json,sqlite3
from contextlib import closing
import production_tools,action_execution

class LiveScopeTest(unittest.TestCase):
 setUp=base.ChatRuntimeTest.setUp
 call=base.ChatRuntimeTest.call
 connect=base.ChatRuntimeTest.connect
 enqueue=base.ChatRuntimeTest.enqueue
 turn=base.ChatRuntimeTest.turn
 rows=base.ChatRuntimeTest.rows
 def test_configured_scope_token_bound_and_stage_cap(self):
  self.connect(Fake([response()]));self.runtime.approval.update(tools=['search_project_context'],max_input_tokens=8192,max_output_tokens=4096,turn_cap_micro=12000,stage={'id':'UI','cap_micro':100000},max_turns=2,one_per_prompt=True)
  self.adapter.tokens=5000;self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'completed');self.assertEqual(self.rows()[0][1],2868)
  self.assertEqual([t['name'] for t in self.adapter.messages[0]['tools']],['search_project_context'])
  with self.assertRaises(ValueError):self.enqueue()
 def test_model_cannot_invoke_tool_omitted_from_server_scope(self):
  self.connect(Fake([response([use('plan','propose_media_plan',ARGS)],'tool_use')]))
  self.runtime.approval['tools']=['search_project_context'];self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'response_validation_failed');self.assertFalse(self.st.state()['projects']['A'].get('guided_plans'))
 def test_stage_budget_counts_prior_turns_and_unknowns(self):
  self.connect(Fake());stage={'id':'UI','cap_micro':3000}
  self.runtime.journal.reserve('chat:old:0','digest','old',2868,12000,stage)
  self.runtime.approval['stage']=stage;self.enqueue();self.runtime.process_next()
  self.assertEqual(self.turn()['status'],'blocked_before_message');self.assertFalse(self.adapter.counts)
 def test_job_receipt_includes_registered_take_without_path(self):
  p=self.st.state()['projects']['A'];p['shots']={'s':{'takes':[{'id':1,'sha256':'a'*64,'asset':'SECRET_LOCAL_PATH','action_id':'a'}]}}
  run=production_tools.begin(p);job={'id':'j','state':'collected','mode':'rehearsal','action_id':'a','grant_id':'g','external_calls':0,'result':{'sha256':'a'*64,'slot':'image'},'result_approved':False}
  result=production_tools.execute(p,run['id'],dict(id='one',name='get_generation_job',arguments={'job_id':'j'},complete=True),jobs=[job])
  self.assertEqual(result['job']['registered_takes'],[dict(shot='s',take=1,sha256='a'*64)])
  self.assertNotIn('SECRET_LOCAL_PATH',json.dumps(result));self.assertEqual(result['job']['external_calls'],0)
