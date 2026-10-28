import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopRefinementTest(unittest.TestCase):
    def run_js(self, assertions):
        source = (ROOT / 'index.html').read_text()
        helpers = source[source.index('function chatModelName('):source.index('function creatorExecutionVisibility(')]
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

    def test_media_label_and_closed_lifecycle_guards_remain(self):
        current=(ROOT/'studio-media.js').read_text()
        self.assertIn('재생 장면: ${c.shot} · Take ${c.take}',current)
        self.assertIn('currentVideo()',current)
        self.assertIn('applyPendingSeek()',current)
        self.assertIn('sequence?.pause();compare?.dispose()',current)
        # Behaviour is covered by media_async_lifecycle and frontend_async regressions;
        # whole-file equality to the earlier presentation-only release is obsolete.
