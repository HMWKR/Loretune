import pathlib
import shutil
import subprocess
import tempfile
import threading
import unittest

import app

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ChatSidebarUITest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node') and pathlib.Path('/opt/homebrew/lib/node_modules/puppeteer-core').exists() and pathlib.Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome').exists(), 'installed isolated headless browser unavailable')
    def test_actual_sidebar_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            server = app.server(pathlib.Path(directory), 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = subprocess.run(['node', str(ROOT/'tests/chat_sidebar.cjs'), f'http://127.0.0.1:{server.server_port}'], cwd=ROOT, capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_overlay_proposal_before_after_gate(self):
        source = (ROOT/'index.html').read_text()
        start = source.index('function timelineProposalView')
        end = source.index('function drawCreationProposals', start)
        fixture = r'''
const assert=require('node:assert/strict'),esc=s=>String(s).replaceAll('<','&lt;'),creatorDiagnostic=()=>'';
const before={shot:'타이포<원본',motion_revision:1,start:0,end:2,offset_x:0,offset_y:0};
const after={...before,motion_revision:2,start:.5,end:2.5,offset_x:100,offset_y:-40};
const p={timeline_head:3,timeline_versions:[{id:3,clips:[{motion_overlay:before}]}]};
const x={id:'p',status:'proposed',description:'겹침 수정',base_version:3,commands:[{op:'set_motion_overlay',clip_index:0}],timeline:{clips:[{shot:'A',motion_overlay:after}]},timeline_diff:{motion_overlays:[{base_clip_index:0,proposed_clip_index:0,before,after}]}};
assert.equal(timelineProposalView(p,x).canApply,true);let html=timelineProposalMarkup(p,x);assert.match(html,/원본 버전 1/);assert.match(html,/원본 버전 2/);assert.match(html,/0.5–2.5초/);assert.match(html,/가로 100px \/ 세로 -40px/);assert.match(html,/타이포&lt;원본/);
x.timeline_diff.motion_overlays[0].after={...after,motion_revision:9};assert.equal(timelineProposalView(p,x).canApply,false);
x.timeline_diff.motion_overlays=[{base_clip_index:0,proposed_clip_index:0,before,after}];x.commands=[{op:'clear_motion_overlay',clip_index:0}];assert.equal(timelineProposalView(p,x).canApply,false);x.timeline.clips[0].motion_overlay=null;x.timeline_diff.motion_overlays[0].after=null;assert.equal(timelineProposalView(p,x).canApply,true);assert.match(timelineProposalMarkup(p,x),/겹침 없음/);
delete x.timeline_diff.motion_overlays;assert.equal(timelineProposalView(p,x).canApply,false);assert.match(timelineProposalMarkup(p,x),/변경 전후 정보를 확인할 수 없습니다/);
x.timeline.clips[0].motion_overlay=before;x.commands=[{op:'set_motion_overlay',clip_index:0}];assert.equal(timelineProposalView(p,x).canApply,true,'verified same-state no-op remains reviewable');
x.timeline_diff.motion_overlays={};assert.equal(timelineProposalView(p,x).canApply,false);
'''
        with tempfile.TemporaryDirectory() as directory:
            script = pathlib.Path(directory)/'test.cjs'
            script.write_text(source[start:end] + fixture)
            result = subprocess.run(['node', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
