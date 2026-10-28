"""Node contract checks complement, but do not replace, real browser testing."""
from pathlib import Path
import shutil
import subprocess
import unittest
from urllib.error import HTTPError


class SceneUIContractTest(unittest.TestCase):
    def test_drafts_approval_capability_and_pending_requests(self):
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run(['node','tests/scene_ui_contract.cjs'],cwd=root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
    def test_cancel_requires_current_project_and_conversation_on_actual_http(self):
        # Exercise the same {song, job} shape as the UI against the real local
        # server, including the non-default conversation ownership boundary.
        from tests.test_scene_workflow import SceneWorkflowTest
        from test_scene_contract import sample
        fixture=SceneWorkflowTest('test_http_create_review_render_commit_download_and_restart')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        other=fixture.post('conversation_create',song='A',title='다른 대화')['conversation']['id']
        created=fixture.post_conversation(other,'scene_create',song='A',shot_id=fixture.shot_id(),scene=sample())['scene']
        fixture.post_conversation(other,'scene_review',song='A',scene_proposal_id=created['proposal_id'],decision='approved')
        current=fixture.state(other)['projects']['A']['scenes_3d'][0]
        job=fixture.post_conversation(other,'scene_render',song='A',scene_id=current['id'],scene_revision=current['head'],grant_id=current['versions'][-1]['approval']['id'])['scene']['job_id']
        with self.assertRaises(HTTPError) as missing:
            fixture.post_conversation(other,'cancel_job',job=job)
        self.assertEqual(missing.exception.code,400);missing.exception.close()
        with self.assertRaises(HTTPError) as wrong:
            fixture.post('cancel_job',song='A',job=job)
        self.assertEqual(wrong.exception.code,400);wrong.exception.close()
        result=fixture.post_conversation(other,'cancel_job',song='A',job=job)
        self.assertEqual(result['job'],job)
        p=fixture.state(other)['projects']['A']
        self.assertEqual(next(j for j in p['scene_3d_jobs'] if j['id']==job)['status'],'cancelled')
        self.assertEqual(p['shots']['shot']['takes'],[])
        self.assertEqual(fixture.state()['projects']['A']['scene_3d_jobs'],[])


if __name__=='__main__':
    unittest.main()
