"""Declared sRGB colors must survive the real Mac rasterizer."""
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

import motion_renderer


@unittest.skipUnless(platform.system() == 'Darwin' and shutil.which('ffmpeg')
                     and Path('/usr/bin/swiftc').is_file()
                     and motion_renderer.FONT.is_file(), 'Mac CoreText/Swift/FFmpeg required')
class NativeMotionColorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='loretune-native-color-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def render(self):
        def layer(identifier, kind, color, x, opacity=1, text=''):
            return dict(id=identifier, kind=kind, text=text, font='system-ko-regular',
                        font_size=160 if text else 80, width=400 if text else 100,
                        height=220 if text else 100, color=color, in_frame=0, out_frame=72,
                        keyframes=[dict(frame=0, x=x, y=100, opacity=opacity, easing='linear')])
        scene = dict(schema_version=1, width=1920, height=1080, fps=24, frame_count=72,
                     background='#1A2A4A', layers=[layer('opaque', 'rect', '#4A2A1A', 100),
                     layer('alpha', 'circle', '#A7C7FF', 300, .5),
                     layer('text', 'text', '#A7C7FF', 600, text='가A')])
        path = self.root / 'frame.png'
        receipt = motion_renderer.frame(scene, 0, path, self.root)
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-frames:v', '1',
                                       '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'])
        self.assertEqual(len(raw), 1920 * 1080 * 3)
        return raw, receipt

    def pixel(self, raw, x, y):
        offset = (y * 1920 + x) * 3
        return tuple(raw[offset:offset + 3])

    def test_opaque_background_and_shape_match_declared_hex_channels(self):
        raw, _ = self.render()
        self.assertEqual(self.pixel(raw, 20, 20), (26, 42, 74))
        self.assertEqual(self.pixel(raw, 150, 150), (74, 42, 26))

    def test_opacity_geometry_and_korean_text_use_the_same_srgb_colors(self):
        raw, receipt = self.render()
        # Source-over in the declared sRGB bitmap; allow one 8-bit rounding step.
        expected = (96.5, 120.5, 164.5)
        actual = self.pixel(raw, 350, 150)
        self.assertTrue(all(abs(a - e) <= 1 for a, e in zip(actual, expected)), actual)
        self.assertEqual(self.pixel(raw, 301, 101), (26, 42, 74))
        colored = sum(self.pixel(raw, x, y) == (167, 199, 255)
                      for y in range(100, 320) for x in range(600, 1000))
        self.assertGreater(colored, 1000, 'Fully covered Korean/Latin glyph pixels must keep the requested color')
        self.assertFalse(receipt['text'][0]['glyph_missing'])


if __name__ == '__main__':
    unittest.main()
