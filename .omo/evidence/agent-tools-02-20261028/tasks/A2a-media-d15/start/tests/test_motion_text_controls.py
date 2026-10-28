"""Motion text draft controls; real browser and CoreText evidence are separate."""
import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import motion_renderer


def starter_scene():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(['node', 'tests/motion_text_controls.cjs'], cwd=root,
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


class MotionStarterNativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = tempfile.TemporaryDirectory(prefix='motion-starter-')
        cls.addClassCleanup(cls.runtime.cleanup)
        cls.scene = starter_scene()

    def test_new_starter_accepts_one_and_two_lines_at_default_size(self):
        scene = copy.deepcopy(self.scene)
        self.assertEqual(scene['layers'][0]['font_size'], 80)
        self.assertEqual(scene['layers'][0]['width'], 1500)
        for text in ['음원으로 시작하는', '음원으로 시작하는\n우리의 영상']:
            with self.subTest(text=text):
                scene['layers'][0]['text'] = text
                result = motion_renderer.validate_text(scene, self.runtime.name)
                self.assertFalse(result['text'][0]['glyph_missing'])
                self.assertEqual(len(result['text'][0]['bounds']), len(text.splitlines()))

    def test_old_two_line_box_remains_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['layers'][0]['height'] = 160
        with self.assertRaisesRegex(ValueError, '텍스트 상자'):
            motion_renderer.validate_text(scene, self.runtime.name)

    def test_single_line_visible_frame_is_unchanged(self):
        scene = copy.deepcopy(self.scene)
        scene['layers'][0]['text'] = '음원으로 시작하는'
        root = Path(self.runtime.name)
        motion_renderer.frame(scene, 24, root / 'new.png', root)
        scene['layers'][0]['height'] = 160
        motion_renderer.frame(scene, 24, root / 'old.png', root)
        self.assertEqual((root / 'new.png').read_bytes(), (root / 'old.png').read_bytes())


class MotionTextControlsTest(unittest.TestCase):
    def test_two_line_draft_bounds_scope_and_recovery(self):
        root = Path(__file__).resolve().parents[1]
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const elements=new Map(),images=[],calls=[];let detailOpened=false,focused='';
class E {constructor(){this.dataset={};this.style={};this.children=[];this.listeners={};this.selectors=new Map();this.value='';this.open=false}
 setAttribute(){} append(){} replaceChildren(){this.children=[]} addEventListener(e,f){this.listeners[e]=f} focus(){}
 querySelector(selector){if(!this.selectors.has(selector))this.selectors.set(selector,{focus(){focused=selector},closest(){return {setAttribute(){detailOpened=true}}}});return this.selectors.get(selector)}
 set innerHTML(s){this.html=s;this.children=s?[{}]:[];this.selectors=new Map();for(const m of s.matchAll(/id="([^"]+)"/g))get(m[1])}get innerHTML(){return this.html||''}
 showModal(){this.open=true}close(){this.open=false;this.listeners.close?.()}}
const get=id=>{if(!elements.has(id))elements.set(id,new E());return elements.get(id)};
const document={createElement:()=>{const e=new E();Object.defineProperty(e,'id',{set(v){elements.set(v,this)}});return e},getElementById:get,querySelector:()=>get('inspector'),body:get('body')};
const layer=(kind,id)=>({id,kind,text:kind==='text'?'원래 문구':'',font:'system-ko-regular',font_size:80,width:kind==='text'?1500:100,height:kind==='text'?160:100,color:'#F4F4F2',in_frame:0,out_frame:96,keyframes:[{frame:0,x:160,y:160,opacity:1,easing:'linear'}]});
const scene={schema_version:1,width:1920,height:1080,fps:24,frame_count:96,background:'#101010',layers:[layer('text','title'),layer('rect','box'),layer('text','second')]};
const A={active_conversation:{id:'A'},shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[{id:'one',shot:'s',base_revision:0,status:'proposed',scene:structuredClone(scene),source:{mode:'human-edit'}}]};
const B={active_conversation:{id:'B'},shots:{s:{stable_id:'s',motion_head:0}},motion_proposals:[]};let p=A;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ctx={document,Map,Image:class{constructor(){images.push(this)}},structuredClone,URLSearchParams,window:{},project:()=>p,song:()=> 'song',shotName:'s',state:{jobs:[]},busy:false,statuses:{},esc,
 act:async(action,data,_,outcome)=>{calls.push({action,data});if(action==='motion_review'){outcome({status:'rejected',reason:'입력을 확인하세요: 한글 glyph·텍스트 상자·모션 프레임을 확인하세요. 자동 폰트 대체 없음'});return false}p.motion_proposals.push({id:'saved',shot:'s',base_revision:0,status:'proposed',scene:structuredClone(data.scene),source:{mode:'human-edit'}});return true}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('motion-studio.js','utf8'),ctx);
const edit=(field,value,type='number')=>get('motionFields').oninput({target:{dataset:{motionField:field},type,value,closest:()=>null}});
async function run(){
 get('motionButton').onclick();assert.match(get('motionFields').innerHTML,/<textarea[^>]*rows="4"[^>]*maxlength="160"/);assert.match(get('motionFields').innerHTML,/텍스트 영역 조정/);
 for(const invalid of ['', '첫 줄\n\n셋째 줄', '첫 줄\n둘째 줄\n셋째 줄', '가'.repeat(81)]){
  edit('text',invalid,'textarea');get('motionLayer').onchange({target:{value:'2'}});focused='';await get('motionSave').onclick();
  assert.equal(calls.length,0);assert.equal(get('motionLayer').value,'0','the invalid text layer must be selected');assert.equal(focused,'[data-motion-field="text"]');assert(get('motionFields').innerHTML.includes(esc(invalid)),'the original text must be preserved');
 }
 edit('text','긴 한글 문구\n두 번째 줄','textarea');edit('font_size','23');await get('motionSave').onclick();assert.equal(calls.length,0);assert.match(get('motionStatus').textContent,/24–160/);
 edit('font_size','161');await get('motionSave').onclick();assert.equal(calls.length,0);edit('font_size','NaN');await get('motionSave').onclick();assert.equal(calls.length,0);
 edit('font_size','40');edit('width','1921');await get('motionSave').onclick();assert.equal(calls.length,0);edit('width','');await get('motionSave').onclick();assert.equal(calls.length,0);assert.equal(focused,'[data-motion-field="width"]');assert.equal(detailOpened,true);
 p=B;ctx.window.AethonMotion.refresh();p=A;ctx.window.AethonMotion.refresh();assert.match(get('motionFields').innerHTML,/긴 한글 문구\n두 번째 줄/);assert.match(get('motionFields').innerHTML,/data-motion-field="width"[^>]*value=""/);
 edit('width','1500');edit('height','1081');await get('motionSave').onclick();assert.equal(calls.length,0);edit('height','160');edit('text','첫 줄\n둘째 줄\n셋째 줄','textarea');await get('motionSave').onclick();assert.equal(calls.length,0);assert.match(get('motionStatus').textContent,/두 줄/);edit('text','긴 한글 문구\n두 번째 줄','textarea');await get('motionSave').onclick();assert.equal(calls.length,1);const saved=calls[0].data.scene;
 assert.equal(saved.layers[0].text,'긴 한글 문구\n두 번째 줄');assert.equal(saved.layers[0].font_size,40);assert.equal(saved.layers[0].width,1500);assert.deepEqual(saved.layers.slice(1),scene.layers.slice(1));assert.equal(A.motion_proposals[0].scene.layers[0].text,'원래 문구');
 get('motionPreview').onclick();images.at(-1).onerror();assert.match(get('motionStatus').textContent,/연결을 확인/);assert.match(get('motionStatus').textContent,/텍스트 영역/);
 await get('motionApprove').onclick();assert.match(get('motionStatus').textContent,/글자 크기와 텍스트 영역/);
 const decomposed='가나다',beforeNormalize=calls.length;edit('text',decomposed,'textarea');assert.equal(get('motionFields').querySelector('[data-motion-normalize]').hidden,false);p=B;ctx.window.AethonMotion.refresh();p=A;ctx.window.AethonMotion.refresh();assert(get('motionFields').innerHTML.includes(decomposed),'composition is unchanged before the explicit action');await get('motionSave').onclick();assert.equal(calls.length,beforeNormalize);assert.match(get('motionStatus').textContent,/문자 조합 정리/);
 get('motionFields').onclick({target:{closest:()=>({})}});assert.match(get('motionFields').innerHTML,/>가나다<\/textarea>/);assert.match(get('motionStatus').textContent,/저장 전 초안/);assert.equal(get('motionSave').disabled,false);assert.equal(calls.length,beforeNormalize);await get('motionSave').onclick();assert.equal(calls.length,beforeNormalize+1);assert.equal(calls.at(-1).data.scene.layers[0].text,'가나다');assert.deepEqual(calls.at(-1).data.scene.layers.slice(1),scene.layers.slice(1));
 edit('text','</textarea><img src=x onerror=alert(1)>','textarea');p=B;ctx.window.AethonMotion.refresh();p=A;ctx.window.AethonMotion.refresh();assert(!get('motionFields').innerHTML.includes('</textarea><img'));assert.match(get('motionFields').innerHTML,/&lt;\/textarea&gt;&lt;img/);
}
run().catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', script], cwd=root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
