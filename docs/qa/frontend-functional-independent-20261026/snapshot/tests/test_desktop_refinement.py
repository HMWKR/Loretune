import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopRefinementTest(unittest.TestCase):
    def run_js(self, assertions):
        source = (ROOT / 'index.html').read_text()
        helpers = source[source.index('function modelChoiceStatus('):source.index('function creatorExecutionVisibility(')]
        stub = """
const assert=require('node:assert/strict');
const nodes=new Map();
for(const role of ['image','video','chat'])for(const kind of ['reason','selected'])
 nodes.set(`model-${role}-${kind}`,{textContent:'',hidden:false,after(n){nodes.set(n.id,n)}});
const document={getElementById:id=>nodes.get(id),createElement:()=>({hidden:false})};
const creatorDiagnostic=(label,value)=>JSON.stringify({label,value});
"""
        result = subprocess.run(['node', '-e', stub + helpers + assertions], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_selection_and_inactive_selection_are_distinct(self):
        self.run_js("""
creatorModelReason('image',null);
assert.equal(modelChoiceStatus(null),'미선택');
assert.equal(nodes.get('model-image-selected').hidden,true);
assert.equal(nodes.get('model-image-diagnostic').hidden,true);
for(const state of ['integration_unverified','integration_blocked','disabled','unavailable','retired']){
 const model={model:'Selected synthetic model',state,reason:'Synthetic restriction'};
 const before=JSON.stringify(model);creatorModelReason('image',model);
 assert.notEqual(modelChoiceStatus(model),'미선택');
 assert.equal(nodes.get('model-image-selected').textContent,model.model);
 assert.equal(nodes.get('model-image-diagnostic').hidden,false);
 assert.match(nodes.get('model-image-diagnostic').innerHTML,/Synthetic restriction/);
 assert.equal(JSON.stringify(model),before);
}
""")

    def test_long_name_is_complete_and_short_name_not_duplicated(self):
        self.run_js("""
for(const name of ['FLUX Schnell','긴 모델 이름 <script> 태그를 포함한 합성 문자열 / '.repeat(5)]){
 const model={model:name,state:'integration_unverified'};creatorModelReason('image',model);
 assert.equal(nodes.get('model-image-selected').textContent,name);
 assert.equal(nodes.get('model-image-selected').hidden,name.length<=45);
}
""")

    def test_available_copy_still_requires_execution_approval(self):
        self.run_js("""
const model={state:'active',model:'Synthetic verified model'};
assert.equal(modelChoiceStatus(model),'연결됨');
assert.match(modelChoiceHint('video',model),/실행 전에.*입력과 비용/);
assert.match(modelChoiceHint('video',{state:'retired'}),/지원이 종료/);
assert.match(modelChoiceHint('video',{state:'unavailable'}),/현재 사용할 수 없/);
""")

    def test_media_lifecycle_is_unchanged_except_presentation_label(self):
        baseline=(ROOT/'docs/qa/desktop-refinement-20261026/before/studio-media.js').read_text()
        current=(ROOT/'studio-media.js').read_text()
        old="${c.shot} · Take ${c.take} · 편집 미리보기"
        new="재생 장면: ${c.shot} · Take ${c.take}"
        self.assertIn(old,baseline)
        self.assertEqual(current.replace(new,old),baseline)
