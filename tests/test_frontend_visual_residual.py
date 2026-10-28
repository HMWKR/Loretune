import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class VisualResidualTest(unittest.TestCase):
 def test_focus_reveals_full_take_without_selecting_or_saving(self):
  source=(ROOT/'index.html').read_text();helper=next(l for l in source.splitlines() if l.startswith('function revealTakeFocus('))
  script="""
const assert=require('node:assert/strict');
const strip={scrollLeft:0,clientLeft:0,clientWidth:529,getBoundingClientRect:()=>({left:220.28})};
const target={getBoundingClientRect:()=>({left:681.32,right:838.92})};
"""+helper+"""
revealTakeFocus(strip,target);assert.ok(Math.abs(strip.scrollLeft-93.64)<.01);
strip.scrollLeft=93.64;target.getBoundingClientRect=()=>({left:126.64,right:280});revealTakeFocus(strip,target);assert.ok(Math.abs(strip.scrollLeft+4)<.01); // browser clamps to zero
strip.scrollLeft=0;target.getBoundingClientRect=()=>({left:224.28,right:400});revealTakeFocus(strip,target);assert.equal(strip.scrollLeft,0);
"""
  r=subprocess.run(['node','-e',script],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  self.assertNotIn('act(',helper);self.assertNotIn('selected=',helper)
 def test_unbroken_title_keeps_full_text_and_emergency_wrap(self):
  css=(ROOT/'studio.css').read_text();self.assertIn('.lt-ui .lt-scene-copy>b { overflow-wrap:anywhere;',css)
  source=(ROOT/'index.html').read_text();helper=next(l for l in source.splitlines() if l.startswith('function renderStudioShots('))
  self.assertIn('esc(creatorSceneLabel(name,i))',helper);self.assertNotIn('.slice(',helper)
