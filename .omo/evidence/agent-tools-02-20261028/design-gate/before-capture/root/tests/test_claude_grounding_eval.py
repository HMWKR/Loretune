import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from scripts.claude_grounding_eval import build,execute,verify,ROOT
from scripts.anthropic_smoke import reserve

TRACE=ROOT/'docs/qa/claude-tool-eval-20261025-diagnostic/trace.json'

class GroundingEvalTest(unittest.TestCase):
 def setUp(self):self.trace=json.loads(TRACE.read_text())
 def answer(self):
  return dict(global_coat='blue coat',studio_coat='red coat',age='unknown',global_changed=False,
   plan_id=self.trace[1]['tool_result']['plan']['id'],plan_status='proposed',approved=False,generated=False,paid=False,
   evidence=[dict(source_id=f['id'],excerpt=f['text']) for f in self.trace[0]['tool_result']['context']['snapshot']])
 def test_receipt_compaction_preserves_protocol_and_canonical_read(self):
  body=build(self.trace)
  first=json.loads(body['messages'][2]['content'][0]['content']);last=json.loads(body['messages'][4]['content'][0]['content'])
  self.assertIn('ontology',first['context']);self.assertNotIn('context',last['plan'])
  self.assertEqual(last['plan']['id'],self.answer()['plan_id']);self.assertEqual(body['tool_choice'],{'type':'none'})
  for a,b in [(1,2),(3,4)]:self.assertEqual(body['messages'][a]['content'][0]['id'],body['messages'][b]['content'][0]['tool_use_id'])
 def test_source_and_authority_hallucinations_rejected(self):
  answer=self.answer();self.assertTrue(all(verify(answer,self.trace).values()))
  for key,value in [('global_coat','gold coat'),('age','20'),('approved',True),('plan_id','fabricated')]:
   bad=copy.deepcopy(answer);bad[key]=value;self.assertFalse(all(verify(bad,self.trace).values()))
  bad=copy.deepcopy(answer);bad['evidence'][0]['excerpt']='Invented source';self.assertFalse(verify(bad,self.trace)['exact_sources'])
 def test_colour_alias_and_extra_real_provenance_are_valid_not_arbitrary_sources(self):
  answer=self.answer();answer.update(global_coat='blue',studio_coat='red')
  answer['evidence'].append(dict(source_id='brief-2',excerpt='It is unknown whether this replaces the rooftop costume.'))
  self.assertTrue(all(verify(answer,self.trace).values()))
  answer['evidence'][-1]['excerpt']='This is the global costume now.'
  self.assertFalse(verify(answer,self.trace)['exact_sources'])
 def test_count_overflow_is_known_unsubmitted_and_releases_hold(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   def forbidden(*args):raise AssertionError('must not submit')
   result=execute(root/'result',root/'ledger.sqlite3',TRACE,'unused',count=lambda *a:{'input_tokens':5000},message=forbidden,key_supplier=lambda p:'synthetic-secret-canary')
   self.assertEqual(result['state'],'blocked_before_message');self.assertEqual(result['input_tokens_counted'],5000)
   c=sqlite3.connect(root/'ledger.sqlite3')
   self.assertEqual(c.execute('SELECT held_micro FROM trials').fetchone()[0],0);c.close()
 def test_answer_usage_and_stage_limit_no_secret_persistence(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   response=lambda *a:dict(stop_reason='end_turn',content=[dict(type='text',text=json.dumps(self.answer()))],usage={'input_tokens':2000,'output_tokens':200},_request_id='req_fixture')
   result=execute(root/'result',root/'ledger.sqlite3',TRACE,'unused',count=lambda *a:{'input_tokens':2000},message=response,key_supplier=lambda p:'synthetic-secret-canary')
   self.assertEqual(result['state'],'verified');self.assertEqual(result['usage_cost_usd'],'0.0003')
   c=sqlite3.connect(root/'ledger.sqlite3')
   with self.assertRaisesRegex(ValueError,'stage limit'):reserve(c,'claude-answer-v1-002','other',2458)
   c.close()
   for p in (root/'result').glob('*.json'):self.assertNotIn('synthetic-secret-canary',p.read_text())
