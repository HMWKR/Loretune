import tempfile,unittest,json
from pathlib import Path
from scripts.claude_tool_eval import execute

class ClaudeToolEvalTest(unittest.TestCase):
 def test_synthetic_tool_protocol_db_roundtrip_and_memory_only_secret(self):
  observed=[]
  def message(endpoint,headers,body):
   observed.append(body)
   choice=body['tool_choice'];name=choice.get('name')
   args={'query':'Mira'} if name=='search_project_context' else dict(goal='Studio scene',scenes='Mira wears red in studio only',style='',constraints='Global blue remains',kind='narrative')
   content=[dict(type='tool_use',id='tool_'+str(len(observed)),name=name,input=args)] if name else [dict(type='text',text='Global blue. Studio exception red. Age unknown.')]
   return dict(stop_reason='tool_use' if name else 'end_turn',content=content,usage={'input_tokens':1000,'output_tokens':100},id='msg_fixture',_request_id='req_fixture')
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);trace=execute(root/'run',root/'budget.sqlite3','unused',count=lambda *a:{'input_tokens':1000},message=message,key_supplier=lambda p:'synthetic-secret-canary')
   self.assertEqual(len(trace),3);self.assertTrue(all(x['idempotent_result'] for x in trace[:2]))
   self.assertEqual(observed[1]['messages'][2]['content'][0]['type'],'tool_result')
   result=json.loads((root/'run/db-result.json').read_text());self.assertEqual(result['plan_count'],1);self.assertEqual(result['foreign_plan_count'],0)
   for p in (root/'run').glob('*.json'):self.assertNotIn('synthetic-secret-canary',p.read_text())
