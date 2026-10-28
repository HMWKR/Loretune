import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from copy import deepcopy
from music import save_music, waveform


class MusicTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
    def test_actual_waveform_quiet_and_tone(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'signal.wav'
            for signal,quiet in [('anullsrc=r=8000:cl=mono',True),('sine=frequency=440:sample_rate=8000',False)]:
                subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',signal,'-t','1',str(path)],check=True)
                result=waveform(path)
                self.assertEqual(result['status'],'measured')
                self.assertEqual(result['quiet'],quiet)
                self.assertAlmostEqual(result['duration'],1)
                self.assertLessEqual(len(result['peaks']),128)
    def test_versions_and_existing_timeline_preserved(self):
        p = dict(audio_versions=[dict(id=1, metadata=dict(duration=60))], timeline_versions=[dict(audio=1, audio_offset=0, approval=True)])
        before = deepcopy(p['timeline_versions'])
        data = dict(audio=1, start=32, end=47, sections=[dict(start=32, end=40, label='후렴')])
        first = deepcopy(save_music(p, data))
        data.update(start=33)
        data['sections'] = []
        save_music(p, data)
        self.assertEqual(p['music_versions'][0], first)
        self.assertEqual(p['timeline_versions'], before)
        self.assertEqual(p['music_versions'][-1]['source'], 'user')
        self.assertIsNone(p['music_versions'][-1]['engine'])

    def test_bad_ranges_and_overlaps(self):
        p = dict(audio_versions=[dict(id=1, metadata=dict(duration=60))])
        for start, end in [(0, 61), (5, 5), (-1, 5), (0, float('nan')), (True, 5)]:
            with self.assertRaises(ValueError):
                save_music(p, dict(audio=1, start=start, end=end))
        with self.assertRaises(ValueError):
            save_music(p, dict(audio=1, start=0, end=10, sections=[dict(start=0, end=6, label='절'),dict(start=5, end=8, label='후렴')]))
        self.assertNotIn('music_versions', p)
