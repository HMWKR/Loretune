import tempfile,unittest,json,sqlite3
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock
from scripts.anthropic_smoke import run,credential,reserve

class AnthropicSmokeTest(unittest.TestCase):
 def test_small_stage_cap_and_cumulative_prior_cost(self):
  c=sqlite3.connect(':memory:');self.addCleanup(c.close)
  reserve(c,'ontology-smoke-001','hash');c.execute('UPDATE trials SET actual_micro=1153');c.commit()
  for i in range(3):reserve(c,'ontology-eval-'+str(i),'hash',4506)
  with self.assertRaises(ValueError):reserve(c,'ontology-eval-extra','hash',4506)
  c.rollback()
  self.assertEqual(c.execute('SELECT SUM(COALESCE(actual_micro,held_micro)) FROM trials').fetchone()[0],14671)
 def test_single_attempt_usage_and_no_secret_persistence(self):
  with tempfile.TemporaryDirectory() as folder:
   count=Mock(return_value={'input_tokens':700})
   message=Mock(return_value={'id':'msg_fixture','_request_id':'req_fixture','stop_reason':'end_turn','usage':{'input_tokens':700,'output_tokens':30},'content':[{'type':'text','text':json.dumps({'entities':[],'relations':[]})}]})
   result=run(folder,'unused',count_transport=count,message_transport=message,key_supplier=lambda p:'secret-canary')
   self.assertEqual(result['state'],'validated');self.assertFalse(result['applied'])
   self.assertEqual(result['usage_cost_usd'],'0.000085')
   with self.assertRaises(ValueError):run(folder,'unused',count_transport=count,message_transport=message,key_supplier=lambda p:'secret-canary')
   self.assertEqual(message.call_count,1)
   for path in Path(folder).iterdir():self.assertNotIn(b'secret-canary',path.read_bytes())
 def test_over_limit_and_unknown_never_submit_again(self):
  for count in [Mock(return_value={'input_tokens':4097}),Mock(side_effect=TimeoutError('secret-canary'))]:
   with tempfile.TemporaryDirectory() as folder:
    message=Mock();result=run(folder,'unused',count_transport=count,message_transport=message,key_supplier=lambda p:'secret-canary')
    self.assertEqual(result['state'],'blocked_or_unknown');message.assert_not_called()
    with closing(sqlite3.connect(Path(folder)/'usage.sqlite3')) as c:self.assertEqual(c.execute('SELECT held_micro,actual_micro FROM trials').fetchone(),(1434,None))
 def test_exact_mixed_case_literal_only(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture'
   path.write_text('OTHER=unrelated\nAnthropic_KEY="synthetic-key-123"\n')
   self.assertEqual(credential(path),'synthetic-key-123')
   path.write_text('Anthropic_KEY=$(bad)\n')
   with self.assertRaises(ValueError):credential(path)
 def test_truncated_response_is_received_but_never_applied(self):
  with tempfile.TemporaryDirectory() as folder:
   result=run(folder,'unused',count_transport=lambda *a:{'input_tokens':1283},message_transport=lambda *a:{'id':'msg_fixture','stop_reason':'max_tokens','usage':{'input_tokens':1283,'output_tokens':2048},'content':[]},key_supplier=lambda p:'secret-canary')
   self.assertEqual(result['state'],'response_validation_failed')
   self.assertEqual(result['usage_cost_usd'],'0.0011523')
   self.assertFalse((Path(folder)/'proposal.json').exists())
