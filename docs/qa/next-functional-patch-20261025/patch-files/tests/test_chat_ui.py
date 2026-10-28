"""Behavioral regression for the discovered disclosure/cancel event collision."""
import json,subprocess,unittest
from pathlib import Path
class ChatUITest(unittest.TestCase):
 def test_disclosure_click_does_not_rerender_but_cancel_is_dispatched_once(self):
  html=(Path(__file__).resolve().parents[1]/'index.html').read_text()
  handler=next(line for line in html.splitlines() if line.startswith("$('#modelChatTurns').onclick="))
  script="""const vm=require('node:vm');const target={};let redraws=0,calls=[];
const ctx={$:()=>target,song:()=> 'synthetic',act:async(a,d)=>calls.push({a,d}),drawModelChat:()=>redraws++};
vm.runInNewContext(HANDLER,ctx);
(async()=>{await target.onclick({target:{closest:()=>null}});const afterDisclosure={redraws,calls:calls.length};
await target.onclick({target:{closest:()=>({dataset:{chatCancel:'turn'}})}});console.log(JSON.stringify({afterDisclosure,redraws,calls}));})();
""".replace('HANDLER',json.dumps(handler))
  result=json.loads(subprocess.check_output(['node','-e',script],text=True))
  self.assertEqual(result['afterDisclosure'],dict(redraws=0,calls=0))
  self.assertEqual(result['redraws'],1);self.assertEqual(result['calls'],[dict(a='chat_cancel',d=dict(song='synthetic',turn='turn'))])
