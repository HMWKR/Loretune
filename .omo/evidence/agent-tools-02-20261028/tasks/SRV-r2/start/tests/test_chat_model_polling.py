"""CQ-R01: real Store states, actual JS polling/draw, isolated database only."""
import json, subprocess, tempfile, unittest, uuid
from pathlib import Path
from app import Store

class ChatModelPollingTest(unittest.TestCase):
 def test_reopen_settings_reads_current_selection_before_opening(self):
  root=Path(__file__).resolve().parents[1]
  html=(root/'index.html').read_text()
  handler=next(line for line in html.splitlines() if line.startswith("$('#editModelSettings').onclick="))
  js="const assert=require('node:assert/strict'),events=[],opener={};const $=s=>s==='#editModelSettings'?opener:{showModal:()=>events.push('open')};const drawModelSettings=()=>events.push('current');"+handler+"opener.onclick();assert.deepEqual(events,['current','open']);"
  result=subprocess.run(['node','-e',js],text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_model_only_polling_and_guards(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(tmp)
   def call(action,**data):
    return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
   call('project',name='A',era='default',story=0)
   call('shot',song='A',shot='s',description='synthetic no-motion scene')
   def select(model):
    call('model_settings',song='A',selections={'chat':model},model_revision=store.state()['projects']['A']['model_settings']['revision'])
    return store.state()
   before=select('openai-gpt-6-luna');grok=select('xai-grok-4-7');cleared=select(None)
   for x in [grok,cleared]:
    self.assertEqual(before['projects']['A']['chat_receipts'],[])
    self.assertEqual(before['projects']['A']['chat_connection'],x['projects']['A']['chat_connection'])
   payload=dict(before=before,grok=grok,cleared=cleared,gptId='openai-gpt-6-luna')
   result=subprocess.run(['node','tests/chat_model_polling.cjs'],cwd=Path(__file__).resolve().parents[1],input=json.dumps(payload),text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertEqual(json.loads(result.stdout)['count'],13)
