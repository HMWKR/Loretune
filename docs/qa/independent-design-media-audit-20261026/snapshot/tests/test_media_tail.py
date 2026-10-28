import unittest,subprocess,sys,json
from pathlib import Path
class MediaTailTest(unittest.TestCase):
 def test_store_export_preserves_last_caption_and_audio_click(self):
  root=Path(__file__).resolve().parents[1];evidence=root/'docs/qa/tail-quota-fixes-20261025'
  subprocess.run([sys.executable,str(evidence/'store_media_after.py')],cwd=root,check=True,capture_output=True,timeout=120)
  result=json.loads((evidence/'store-media-after.json').read_text())
  self.assertEqual(result['state'],'completed');self.assertIn('끝 자막',result['actual_srt'])
  self.assertIn('00:00:03,930',result['actual_srt']);self.assertGreaterEqual(result['verified']['duration'],3.93)
  self.assertGreater(json.loads((evidence/'tail-audio-peak.json').read_text())['peak'],5000)

  from renderer import verify_output
  expected=dict(profile='preview',shots={str(i):dict(duration=.131) for i in range(30)},audio={'fixture':True},subtitles=[dict(start=3.92,end=3.93,text='다른 자막')])
  with self.assertRaisesRegex(ValueError,'자막 내용'):verify_output(evidence/'media/store-tail-preserved.mp4',expected)
