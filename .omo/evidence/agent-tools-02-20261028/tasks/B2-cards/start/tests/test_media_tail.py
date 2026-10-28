import unittest,subprocess,sys,json,hashlib,os,shutil,tempfile
from pathlib import Path
class MediaTailTest(unittest.TestCase):
 def test_store_export_preserves_last_caption_and_audio_click(self):
  root=Path(__file__).resolve().parents[1];evidence=root/'docs/qa/tail-quota-fixes-20261025'
  protected={str(p.relative_to(evidence)):hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
  # The historical script uses its own directory as the output root. Execute a
  # copy with just the synthetic inputs so regression runs cannot rewrite QA.
  with tempfile.TemporaryDirectory(prefix='loretune-tail-regression-') as folder:
   work=Path(folder);(work/'media').mkdir()
   for name in ('store_media_after.py','helpers.py'):shutil.copyfile(evidence/name,work/name)
   for name in ('synthetic.png','clicks.wav'):shutil.copyfile(evidence/'media'/name,work/'media'/name)
   env=os.environ.copy();env['PYTHONPATH']=str(root)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '');env['PYTHONDONTWRITEBYTECODE']='1'
   subprocess.run([sys.executable,str(work/'store_media_after.py')],cwd=root,env=env,check=True,capture_output=True,timeout=120)
   result=json.loads((work/'store-media-after.json').read_text())
   self.assertEqual(result['state'],'completed');self.assertIn('끝 자막',result['actual_srt'])
   self.assertIn('00:00:03,930',result['actual_srt']);self.assertGreaterEqual(result['verified']['duration'],3.93)
   self.assertGreater(json.loads((work/'tail-audio-peak.json').read_text())['peak'],5000)
   from renderer import verify_output
   expected=dict(profile='preview',shots={str(i):dict(duration=.131) for i in range(30)},audio={'fixture':True},subtitles=[dict(start=3.92,end=3.93,text='다른 자막')])
   with self.assertRaisesRegex(ValueError,'자막 내용'):verify_output(work/'media/store-tail-preserved.mp4',expected)
  after={str(p.relative_to(evidence)):hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
  self.assertEqual(after,protected,'regression must preserve every historical evidence file')
