from pathlib import Path
import json
import subprocess
import unittest


class TimelineMotionOverlayUiTest(unittest.TestCase):
    def test_overlay_editing_and_saved_frame_response_guards(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ['node', 'tests/timeline_motion_overlay.cjs'],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ui_preview_boundaries_match_server_cumulative_frame_policy(self):
        from editing import frame_timing
        root = Path(__file__).resolve().parents[1]
        cases = [
            [.125], [.130], [3], [1, 2, 3], [.130, .130],
            [.130, .200, .130], [3.02, 3.02, 3.02], [.145, .145, .145],
            [1.11, 1.11, 1.11], [.125] * 30, [.126] * 30,
            [19.999, .125, .126], [.125, .130, .146, .166, .167],
        ]
        expected = [[clip['frames'] for clip in frame_timing(case)['clips']] for case in cases]
        script = r"""
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('index.html','utf8');
const helper=source.split('\n').find(line=>line.startsWith('function timelineClipFrameCounts('));
if(!helper)throw Error('UI cumulative frame helper missing');
vm.runInThisContext(helper);
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(cases.map(values=>timelineClipFrameCounts(values.map(duration=>({duration}))))));
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps(cases), cwd=root,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), expected)
