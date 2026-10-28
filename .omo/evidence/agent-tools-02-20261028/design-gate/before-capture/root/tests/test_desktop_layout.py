import re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DesktopLayoutTest(unittest.TestCase):
 def js(self,code):
  source=(ROOT/'index.html').read_text().split('<script id="loretuneDesktopLayout">')[1].split('(() => {')[0]
  p=subprocess.run(['node','-e',"const assert=require('node:assert/strict');"+source+code],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr)
 def test_label_collision_keeps_endpoints_and_time_coordinates(self):
  self.js("const b=[{left:0,right:120},{left:160,right:280},{left:360,right:480},{left:560,right:680},{left:620,right:740}],before=JSON.stringify(b);assert.deepEqual(visibleTimelineLabels(b),[0,1,2,4]);assert.equal(JSON.stringify(b),before);assert.deepEqual(visibleTimelineLabels([]),[]);assert.deepEqual(visibleTimelineLabels([{left:0,right:120}]),[0]);")
 def test_labels_reappear_when_width_available(self):
  self.js("const b=[{left:0,right:120},{left:200,right:320},{left:400,right:520}];assert.deepEqual(visibleTimelineLabels(b),[0,1,2]);assert.deepEqual(visibleTimelineLabels([{left:0,right:120},{left:90,right:210},{left:180,right:300}]),[0,2]);")
 def test_expanded_type_or_small_window_uses_accessible_flow(self):
  self.js("assert.equal(desktopShellMode(1920,1080,1),'bounded');assert.equal(desktopShellMode(1280,900,1),'bounded');for(const x of [[1920,1080,2],[1920,1080,1.5],[1000,900,1],[1920,600,1],[390,844,1]])assert.equal(desktopShellMode(...x),'flow');")
 def test_layout_adapter_cannot_submit_or_replace_media(self):
  source=(ROOT/'index.html').read_text().split('<script id="loretuneDesktopLayout">')[1].split('</script>')[0]
  for word in ['fetch(', 'act(', 'innerHTML', 'cloneNode', '.currentTime', '.play(', 'localStorage', '/api/', 'replaceChildren']:
   self.assertNotIn(word,source)
  self.assertIn('stage.append(node)',source)
