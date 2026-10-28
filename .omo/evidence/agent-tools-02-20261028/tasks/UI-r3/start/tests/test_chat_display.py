"""CQ-01/02: presentation reads selection/facts without changing authority."""
import json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ChatDisplayTest(unittest.TestCase):
 def js(self,assertions):
  html=(ROOT/'index.html').read_text()
  helpers=html[html.index('function chatModelName('):html.index('function creatorModelReason(')]
  helpers+=html[html.index('function receiptFacts('):html.index('function scopedReceipts(')]
  code="const assert=require('node:assert/strict');const esc=s=>String(s??'').replace(/[<>&]/g,x=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[x]));\n"+helpers+assertions
  r=subprocess.run(['node','-e',code],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_saved_selection_empty_unknown_and_unavailable(self):
  self.js("""
const p={model_settings:{selections:{chat:'selected'}},chat_turns:[{model:'old-Claude'}],chat_connection:{model:'old-Claude',available:false}};
const c={models:[{id:'selected',role:'chat',model:'gpt-6-luna',state:'integration_unverified'}]};
const before=JSON.stringify({p,c});
for(const status of ['active','integration_unverified','integration_blocked','retired','disabled','unavailable']){
 c.models[0].state=status;const text=currentChatModelText(p,c);
 assert.match(text,/GPT 6 Luna.*작품 기본값.*다음 요청 기준/);assert(!text.includes('old-Claude'));assert(!text.includes('gpt-6-luna'));
}
c.models[0].state='integration_unverified';assert.equal(JSON.stringify({p,c}),before);
p.model_settings.selections.chat=null;assert.match(currentChatModelText(p,c),/미선택/);
p.model_settings.selections.chat='missing';assert.match(currentChatModelText(p,c),/정보 확인 필요/);assert(!currentChatModelText(p,c).includes('missing'));
assert.match(currentChatModelText(null,c),/작품을 먼저/);
""")
 def test_long_display_name_preserved_and_role_is_not_inferred(self):
  self.js("""
const name='긴 한글 모델 이름과무공백문자열'.repeat(20)+'<script>example</script>';
const c={models:[{id:'chosen',role:'chat',model:'gpt-6-luna',display_name:name}]};
const p={model_settings:{selections:{chat:'chosen'}}};
assert(currentChatModelText(p,c).includes(name));assert.equal(modelChoiceName(c.models[0]),name);
c.models[0].role='video';assert.match(currentChatModelText(p,c),/정보 확인 필요/);
""")
 def test_current_stale_priority_does_not_rewrite_facts_or_history(self):
  self.js("""
const r={shot_name:'합성 장면',motion_revision:1,composition_saved:true,approval:{actor:'local-owner',scope:'local-motion-candidate',motion_revision:1},proposals:[]};
for(const match of [true,false,null]){
 r.matches_current_context=match;const before=JSON.stringify(r),facts=receiptFacts(r),current=receiptMarkup(r),past=receiptMarkup(r,true);
 assert.equal(JSON.stringify(r),before);for(const line of facts){assert(current.includes(esc(line)));assert(past.includes(esc(line)));}
 assert.equal(current.includes('chat-receipt-stale'),match===false);assert(!past.includes('chat-receipt-stale'));
 assert(!current.includes('<button'));assert(current.includes('실행 허용 확정이 아닙니다.'));assert(current.includes('최종 출력·납품 승인을 포함하지 않습니다.'));
 if(match===false)assert(current.indexOf(esc(facts[2]))<current.indexOf(esc(facts[1])));
}
""")
 def test_form_description_and_text_only_assignment(self):
  html=(ROOT/'index.html').read_text()
  self.assertIn('aria-describedby="modelChatSelection modelChatCapability"',html)
  self.assertIn("$('#modelChatSelection').textContent=currentChatModelText(p,state?.model_catalog)",html)
  self.assertLess(html.index('id="modelChatSelection"'),html.index('id="modelChatPrompt"'))
  self.assertIn('overflow-wrap:anywhere',(ROOT/'studio.css').read_text())

if __name__=='__main__':unittest.main()
