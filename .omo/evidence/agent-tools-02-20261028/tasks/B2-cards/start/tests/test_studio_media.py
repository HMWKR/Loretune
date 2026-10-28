import json,re,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class StudioMediaTest(unittest.TestCase):
 def js(self,code):
  r=subprocess.run(['node','-e',"const assert=require('node:assert/strict');const m=require('./studio-media.js');"+code],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr)
 def test_proportional_ranges_absolute_mapping_and_reorder(self):
  self.js("const a=[{shot:'a',duration:2,trim:1},{shot:'b',duration:4,trim:.5}];assert.deepEqual(m.ranges(a).map(c=>[c.start,c.end]),[[0,2],[2,6]]);assert.equal(m.locate(a,2).shot,'b');assert.equal(m.locate(a,2).source,.5);assert.equal(m.locate(a,5).source,3.5);assert.equal(m.locate(a,99).source,4.5);assert.equal(m.locate(a,-1).source,1);assert.equal(m.locate(a.reverse(),1).source,1.5);")
 def test_fractional_frame_tail_is_not_rounded_in_preview(self):
  self.js("const a=Array.from({length:30},()=>({duration:.131}));assert.ok(Math.abs(m.locate(a,3.929).total-3.93)<1e-10);assert.equal(m.locate(a,3.929).index,29);assert.equal(m.timecode(3.93),'00:03.930');")
 def test_waveform_uses_only_measured_interval_offset_and_no_invention(self):
  self.js("const w={status:'measured',duration:4,peaks:[.1,.2,.7,.9]};assert.deepEqual(m.waveWindow(w,1,2,2),[.2,.7]);assert.deepEqual(m.waveWindow(w,3,2,2),[.9,null]);assert.equal(m.waveWindow(null,0,2),null);assert.equal(m.waveWindow({...w,status:'pending'},0,2),null);assert.equal(m.waveWindow({...w,peaks:[]},0,2),null);")
 def test_comparison_trim_common_duration_and_image_mixture(self):
  self.js("const a=m.auditionWindow({asset:'x.mp4',metadata:{duration:8}},{trim:2,duration:4}),b=m.auditionWindow({asset:'y.mp4',metadata:{duration:3}},{trim:.5,duration:4});assert.deepEqual(m.comparisonPosition([a,b],8),{duration:2.5,time:2.5,sources:[4.5,3]});const im=m.auditionWindow({asset:'x.png'});assert.deepEqual(m.comparisonPosition([im,a],1).sources,[null,3]);assert.equal(m.comparisonPosition([im,im],1).duration,0);assert.equal(m.auditionWindow({asset:'x.mp4',metadata:{duration:1}},{trim:3,duration:2}).duration,0);")
 def test_comparison_readiness_recomputed_after_seek(self):
  self.js("const a={readyState:1},b={readyState:4};assert.equal(m.comparisonReady([a,b]),false);a.readyState=4;assert.equal(m.comparisonReady([a,b]),true);b.error={code:4};assert.equal(m.comparisonReady([a,b]),false);assert.equal(m.comparisonReady([null]),true);")
 def test_input_immutability_and_empty_bad_values(self):
  self.js("const a=[{duration:2,trim:1}],before=JSON.stringify(a);m.ranges(a);m.locate(a,9);assert.equal(JSON.stringify(a),before);assert.equal(m.locate([],1),null);assert.equal(m.ranges([{duration:NaN}])[0].duration,0);assert.deepEqual(m.ticks(0),[0]);assert.equal(m.ticks(6).at(-1),6);")
 def test_audition_has_no_write_api_and_lifecycle_boundaries(self):
  source=(ROOT/'studio-media.js').read_text()
  for forbidden in ['fetch(',"act(",'XMLHttpRequest','localStorage','/api/']:
   self.assertNotIn(forbidden,source)
  for expected in ["addEventListener('close'","addEventListener('cancel'","addEventListener('visibilitychange'","addEventListener('pagehide'","url.startsWith('/assets/')","holder.isConnected"]:
   self.assertIn(expected,source)
 def test_static_modules_are_allowlisted_and_font_scale_is_role_based(self):
  app=(ROOT/'app.py').read_text();html=(ROOT/'index.html').read_text()
  self.assertIn("'/studio-media.js'",app)
  css=(ROOT/'studio.css').read_text()
  self.assertIn('--text-scale',css);self.assertNotRegex(css,r'font-size\s*:\s*\d+(?:\.\d+)?px')
  self.assertEqual(len(re.findall(r'<style(?:\s|>)',html)),0)
  self.assertIn('/studio.css',html)
