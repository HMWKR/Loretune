import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import Request, urlopen
import uuid

from test_scene_contract import sample

ROOT = Path(__file__).resolve().parents[1]
REAL_KEYS = ('LORETUNE_3D_IMAGE', 'LORETUNE_3D_BLENDER', 'LORETUNE_3D_BLENDER_SHA256',
             'LORETUNE_3D_TREE_SHA256', 'LORETUNE_3D_DOCKER_SOCKET')


class SceneCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.data = self.root / 'data'
        self.config = self.root / 'sensitive-config-name.json'
        self.process = None
        self.addCleanup(self.stop_server)

    def stop_server(self):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
            try:
                self.process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate(timeout=5)
            self.process = None

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'app.py'), *map(str, args)],
                              cwd=ROOT, capture_output=True, text=True, timeout=30)

    def start_server(self, *args):
        self.process = subprocess.Popen(
            [sys.executable, '-B', str(ROOT / 'app.py'), '--port', '0', '--data', str(self.data), *map(str, args)],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        ready, _, _ = select.select([self.process.stdout], [], [], 45)
        if not ready:
            self.fail('server did not start within 45 seconds')
        line = self.process.stdout.readline().strip()
        self.assertTrue(line.startswith('Aethon: http://127.0.0.1:'), line)
        self.base = line.removeprefix('Aethon: ')

    def state(self):
        with urlopen(self.base + '/api/state', timeout=10) as response:
            return json.load(response)

    def post(self, action, **data):
        state = self.state()
        body = dict(action=action, data=data, revision=state['revision'], request_id=uuid.uuid4().hex)
        request = Request(self.base + '/api/action', data=json.dumps(body, ensure_ascii=False).encode(),
                          headers={'Content-Type': 'application/json', 'X-Loretune-Token': state['token']})
        with urlopen(request, timeout=15) as response:
            return json.load(response)

    def write_config(self, body, mode=0o600):
        self.config.write_text(body, encoding='utf-8')
        self.config.chmod(mode)

    def test_help_and_unconfigured_server(self):
        help_result = self.run_cli('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertIn('--scene-config PATH', help_result.stdout)
        self.assertFalse(self.data.exists())
        self.start_server()
        self.post('project', name='합성 QA', era='default', story=0)
        connection = self.state()['projects']['합성 QA']['scene_3d_connection']
        self.assertFalse(connection['available'])
        self.assertFalse(connection['external_transmission'])

    def test_bad_configuration_exits_before_database_and_hides_path(self):
        cases = [None, '{not-json', json.dumps({'version': 1})]
        for body in cases:
            with self.subTest(body=body):
                if body is None:
                    self.config.unlink(missing_ok=True)
                else:
                    self.write_config(body)
                result = self.run_cli('--data', self.data, '--scene-config', self.config)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('로컬 3D 관리자 설정', result.stderr)
                self.assertNotIn(str(self.config), result.stderr)
                self.assertNotIn('sensitive-config-name', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(self.data.exists())

    def test_config_file_with_unsafe_permissions_exits_before_database(self):
        self.write_config('{}', 0o644)
        result = self.run_cli('--data', self.data, '--scene-config', self.config)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(str(self.config), result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(self.data.exists())

    def test_extreme_numeric_limits_exit_before_database(self):
        value = dict(version=1, image_id='sha256:' + 'a'*64,
                     blender_root='/missing/trusted-blender', blender_sha256='a'*64,
                     tree_sha256='b'*64, docker_socket='/missing/trusted-socket',
                     timeout_seconds=120, quota_bytes=100_000_000)
        for change in ({'timeout_seconds': 10**400}, {'timeout_seconds': -1},
                       {'quota_bytes': 2**53+1}):
            with self.subTest(change=list(change)):
                self.write_config(json.dumps({**value, **change}))
                result = self.run_cli('--data', self.data, '--scene-config', self.config)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(str(self.config), result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(self.data.exists())

    @unittest.skipUnless(all(os.environ.get(k) for k in REAL_KEYS), 'trusted local Blender QA environment not configured')
    def test_changed_tree_fails_before_database(self):
        value = dict(version=1, image_id=os.environ['LORETUNE_3D_IMAGE'],
                     blender_root=os.environ['LORETUNE_3D_BLENDER'],
                     blender_sha256=os.environ['LORETUNE_3D_BLENDER_SHA256'],
                     tree_sha256='0'*64, docker_socket=os.environ['LORETUNE_3D_DOCKER_SOCKET'],
                     timeout_seconds=120, quota_bytes=100_000_000)
        self.write_config(json.dumps(value))
        result = self.run_cli('--data', self.data, '--scene-config', self.config)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(str(self.config), result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse(self.data.exists())

    @unittest.skipUnless(all(os.environ.get(k) for k in REAL_KEYS), 'trusted local Blender QA environment not configured')
    def test_configured_process_renders_candidate_and_reopens(self):
        value = dict(version=1, image_id=os.environ['LORETUNE_3D_IMAGE'],
                     blender_root=os.environ['LORETUNE_3D_BLENDER'],
                     blender_sha256=os.environ['LORETUNE_3D_BLENDER_SHA256'],
                     tree_sha256=os.environ['LORETUNE_3D_TREE_SHA256'],
                     docker_socket=os.environ['LORETUNE_3D_DOCKER_SOCKET'],
                     timeout_seconds=120, quota_bytes=100_000_000)
        self.write_config(json.dumps(value))
        self.start_server('--scene-config', self.config)
        self.post('project', name='합성 QA', era='default', story=0)
        self.post('shot', song='합성 QA', shot='합성 장면', description='CLI 3D test')
        project = self.state()['projects']['합성 QA']
        self.assertTrue(project['scene_3d_connection']['available'])
        self.assertEqual(project['scene_3d_connection']['mode'], 'configured-preflight-required')
        scene = self.post('scene_create', song='합성 QA', shot_id='합성 장면', scene=sample())['scene']
        self.post('scene_review', song='합성 QA', scene_proposal_id=scene['proposal_id'], decision='approved')
        scene = self.state()['projects']['합성 QA']['scenes_3d'][0]
        self.post('scene_render', song='합성 QA', scene_id=scene['id'], scene_revision=1,
                  grant_id=scene['versions'][-1]['approval']['id'])
        deadline = time.monotonic() + 100
        while time.monotonic() < deadline:
            project = self.state()['projects']['합성 QA']
            job = project['scene_3d_jobs'][-1]
            if job['status'] not in ('queued', 'running'):
                break
            time.sleep(0.2)
        self.assertEqual(job['status'], 'completed', job.get('error'))
        take = project['shots']['합성 장면']['takes'][0]
        self.assertIsNone(project['shots']['합성 장면']['selected'])
        self.assertEqual(take['rights'], '사용권 미확인')
        with urlopen(self.base + '/assets/' + take['filename'], timeout=10) as response:
            image = response.read()
        self.assertTrue(image.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(hashlib.sha256(image).hexdigest(), take['sha256'])
        self.stop_server()
        self.start_server('--scene-config', self.config)
        project = self.state()['projects']['합성 QA']
        self.assertEqual(project['shots']['합성 장면']['takes'][0]['sha256'], take['sha256'])
        with urlopen(self.base + '/assets/' + take['filename'], timeout=10) as response:
            self.assertEqual(hashlib.sha256(response.read()).hexdigest(), take['sha256'])


if __name__ == '__main__':
    unittest.main()
