import base64
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch

import app
from tests import test_motion_overlay

ROOT=Path(__file__).resolve().parents[1]


class CentralFramePreviewTest(unittest.TestCase):
 @unittest.skipUnless(shutil.which('ffmpeg') and Path('/opt/homebrew/lib/node_modules/puppeteer-core').exists() and Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome').exists(),'native media/headless tools unavailable')
 def test_actual_saved_png_full_fit_and_original_media_return(self):
  fixture=test_motion_overlay.MotionOverlayTest('test_actual_http_preview_transparency_timing_positions_render_and_reopen');fixture.setUp();self.addCleanup(fixture.doCleanups)
  base=Path(fixture.tmp.name)
  for filename,args in [('plate.png',['-frames:v','1']),('plate.mp4',['-t','3','-an','-c:v','libx264','-pix_fmt','yuv420p'])]:
   target=base/filename;subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=c=0x204080:s=640x360:r=24',*args,str(target)],check=True)
   fixture.call('take',shot='base',shot_revision=fixture.project()['shots']['base']['revision'],filename=filename,content=base64.b64encode(target.read_bytes()).decode(),reason='directly authored test plate',rights='directly authored')
  fixture.call('select',shot='base',take=3,shot_revision=fixture.project()['shots']['base']['revision'])
  timeline=fixture.timeline();timeline['clips'][0]['take']=2;timeline['clips'].append(dict(timeline['clips'][0],take=3));timeline['subtitles']=[dict(start=0,end=2,text='긴 한국어 자막 · 원본 재생과 최종 출력에서 확인')];fixture.call('timeline',timeline=timeline)
  for take in [2,3]:fixture.call('review_take',shot='base',take=take,decision='approved',reason='synthetic fixture review')
  fixture.call('approve_timeline');fixture.call('estimate_render');quote=fixture.project()['render_estimates'][-1]['id'];fixture.call('render_job',estimate=quote);fixture.store.process_next()
  fixture.call('timeline',timeline=timeline)
  evidence=os.environ.get('LORETUNE_CENTRAL_FRAME_EVIDENCE');modes=['before','after'] if os.environ.get('LORETUNE_CENTRAL_FRAME_BEFORE') else ['after']
  with tempfile.TemporaryDirectory() as static_dir:
   static=Path(static_dir)
   for source in [*ROOT.glob('*.js'),ROOT/'studio.css',ROOT/'index.html']:shutil.copyfile(source,static/source.name)
   before=ROOT/'.omo/evidence/first-demo-20261028/frontend/central-frame-preview/before'
   for name in ['index.html','studio.css','studio-media.js']:shutil.copyfile(before/name,static/name)
   for mode in modes:
    with patch.object(app,'ROOT',static if mode=='before' else ROOT):
     server=app.server(base,0);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
     try:
      command=['node','tests/central_frame_preview.cjs',f'http://127.0.0.1:{server.server_port}',mode]
      if evidence:Path(evidence).mkdir(parents=True,exist_ok=True);command.append(evidence)
      result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=100)
      if evidence:(Path(evidence)/(mode+'-invocation.log')).write_text(result.stdout+result.stderr)
      self.assertEqual(result.returncode,0,result.stdout+result.stderr)
     finally:server.shutdown();server.server_close();thread.join(5)
