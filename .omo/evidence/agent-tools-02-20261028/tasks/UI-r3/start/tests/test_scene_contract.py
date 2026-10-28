import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import time
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

import scene_renderer
import scene_spec


def sample():
    return dict(schema_version=1, width=96, height=96, background=[0.1, 0.1, 0.1],
                objects=[dict(id='subject', kind='cube', position=[0, 0, 0], rotation_degrees=[0, 0, 0],
                              scale=[1, 1, 1], color=[0.05, 0.25, 0.8])],
                camera=dict(position=[5, -7, 5], target=[0, 0, 0], lens_mm=50),
                lights=[dict(id='key', position=[3, -4, 6], target=[0, 0, 0], energy_w=800,
                             size_m=3, color=[1, 1, 1])])


class SceneContractTest(unittest.TestCase):
    def test_scene_compiler_and_fingerprint_are_deterministic_and_detached(self):
        scene = sample()
        saved = scene_spec.validate(scene)
        before = scene_spec.fingerprint(scene)
        script = scene_renderer.compile_scene(scene)
        self.assertEqual(script, scene_renderer.compile_scene(copy.deepcopy(scene)))
        scene['objects'][0]['color'][0] = 0.8
        self.assertNotEqual(scene_spec.fingerprint(scene), before)
        self.assertEqual(saved['objects'][0]['color'][0], 0.05)
        self.assertNotIn(b'http://', script)
        self.assertAlmostEqual(scene_spec.horizontal_fov_degrees(saved), 39.5977527, places=5)

    def test_unknown_paths_scripts_nonfinite_invalid_bounds_and_duplicate_ids_rejected(self):
        examples = []
        scene = sample(); scene['objects'][0]['script'] = '__import__("os")'; examples.append(scene)
        scene = sample(); scene['objects'][0]['path'] = '/etc/passwd'; examples.append(scene)
        scene = sample(); scene['objects'][0]['kind'] = 'https://example.invalid'; examples.append(scene)
        scene = sample(); scene['lights'][0]['energy_w'] = float('nan'); examples.append(scene)
        scene = sample(); scene['camera']['lens_mm'] = float('inf'); examples.append(scene)
        scene = sample(); scene['objects'][0]['scale'][0] = 10**1000; examples.append(scene)
        scene = sample(); scene['width'] = 513; examples.append(scene)
        scene = sample(); scene['camera']['target'] = scene['camera']['position'][:]; examples.append(scene)
        scene = sample(); scene['lights'][0]['id'] = 'subject'; examples.append(scene)
        scene = sample(); scene['lights'][0]['energy_w'] = True; examples.append(scene)
        for scene in examples:
            with self.subTest(scene=repr(scene)[:100]), self.assertRaises(ValueError):
                scene_spec.validate(scene)

    def test_approval_binds_trusted_revision_context_and_scene(self):
        scene = sample()
        binding = dict(workspace_id='8a157783-1901-46bd-9b59-ea1b642768b1', project_id='project-1',
                       shot_id='31537a278cda453599c4e3185f4c734a', scene_id='scene-1', revision=3, ontology_revision=5)
        approval = dict(id='c7bd3bee-7f4c-4aae-b60e-682a9664fa37', actor='local-owner', scope='local-3d-still',
                        binding=copy.deepcopy(binding), scene_hash=scene_spec.fingerprint(scene))
        self.assertEqual(scene_spec.require_approval(scene, binding, approval), approval)
        stale = dict(binding, revision=4)
        with self.assertRaises(ValueError): scene_spec.require_approval(scene, stale, approval)
        scene['camera']['lens_mm'] = 51
        with self.assertRaises(ValueError): scene_spec.require_approval(scene, binding, approval)
        with self.assertRaises(ValueError): scene_spec.require_approval(sample(), binding, dict(approval, actor='model'))
        one = dict(binding, revision=1)
        boolean_approval = dict(approval, binding=dict(one, revision=True))
        with self.assertRaises(ValueError): scene_spec.require_approval(sample(), one, boolean_approval)

    def test_typed_proposals_preserve_unchanged_fields_and_enforce_scope_locks_and_revision(self):
        scene = sample()
        operation = dict(target='light', id='key', field='energy_w', value=400)
        scope = [('light', 'key', 'energy_w')]
        proposal = scene_spec.propose_changes(scene, [operation], base_revision=1, current_revision=1, allowed_fields=scope)
        self.assertEqual(proposal['changes'][0]['before'], 800)
        self.assertEqual(proposal['changes'][0]['after'], 400)
        self.assertEqual(proposal['scene']['camera'], scene['camera'])
        self.assertEqual(scene['lights'][0]['energy_w'], 800)
        with self.assertRaises(ValueError):
            scene_spec.propose_changes(scene, [operation], base_revision=1, current_revision=2, allowed_fields=scope)
        with self.assertRaises(ValueError):
            scene_spec.propose_changes(scene, [operation], base_revision=1, current_revision=1, allowed_fields=scope, locked_fields=scope)
        with self.assertRaises(ValueError):
            scene_spec.propose_changes(scene, [operation, operation], base_revision=1, current_revision=1, allowed_fields=scope)
        with self.assertRaises(ValueError):
            scene_spec.propose_changes(scene, [dict(operation, field='id', value='other')], base_revision=1, current_revision=1, allowed_fields=scope)
        with self.assertRaises(ValueError):
            scene_spec.propose_changes(scene, [dict(operation, value=-1)], base_revision=1, current_revision=1, allowed_fields=scope)

    def test_renderer_rejects_untrusted_configuration_before_publishing(self):
        with tempfile.TemporaryDirectory() as folder:
            config = scene_renderer.RendererConfig('latest', Path(folder), 'a'*64)
            with self.assertRaises(scene_renderer.RenderError):
                scene_renderer.render(sample(), config, folder, request_id=uuid.uuid4().hex)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_unconfirmed_container_creation_preserves_request_id_without_publishing(self):
        with tempfile.TemporaryDirectory() as folder:
            image = 'sha256:' + 'a'*64
            config = scene_renderer.RendererConfig(image, Path(folder), 'b'*64)
            request_id = uuid.uuid4().hex
            inspect = SimpleNamespace(stdout=('{"Id":"' + image + '","Os":"linux","Architecture":"amd64"}').encode())
            # Docker inspect returns a list; the second result represents no prior job.
            inspect.stdout = b'[' + inspect.stdout + b']'
            effects = [inspect, SimpleNamespace(stdout=''), subprocess.TimeoutExpired('docker create', 30)]
            with patch.object(scene_renderer, '_configuration', return_value=(Path(folder), ['docker'], 'ffmpeg')):
                with patch.object(scene_renderer.subprocess, 'run', side_effect=effects) as run:
                    with self.assertRaises(scene_renderer.RenderOutcomeUnknown) as failure:
                        scene_renderer.render(sample(), config, folder, request_id=request_id)
            self.assertEqual(failure.exception.request_id, request_id)
            self.assertIn('loretune.scene-request=' + request_id, run.call_args_list[-1].args[0])
            self.assertCountEqual([p.name for p in Path(folder).iterdir()], ['.scene-claims', '.scene-locks'])

    def test_existing_request_is_not_started_again(self):
        with tempfile.TemporaryDirectory() as folder:
            image = 'sha256:' + 'a'*64
            config = scene_renderer.RendererConfig(image, Path(folder), 'b'*64)
            request_id = uuid.uuid4().hex
            inspect = SimpleNamespace(stdout=('[{"Id":"' + image + '","Os":"linux","Architecture":"amd64"}]').encode())
            with patch.object(scene_renderer, '_configuration', return_value=(Path(folder), ['docker'], 'ffmpeg')):
                with patch.object(scene_renderer.subprocess, 'run', side_effect=[inspect, SimpleNamespace(stdout='ab12\n')]) as run:
                    with self.assertRaises(scene_renderer.RenderOutcomeUnknown) as failure:
                        scene_renderer.render(sample(), config, folder, request_id=request_id)
            self.assertEqual(failure.exception.request_id, request_id)
            self.assertEqual(run.call_count, 2)
            self.assertCountEqual([p.name for p in Path(folder).iterdir()], ['.scene-claims', '.scene-locks'])

    def test_create_connection_error_and_invalid_receipt_remain_unknown(self):
        for failure in (subprocess.CalledProcessError(1, 'docker create'), OSError('connection lost'),
                        SimpleNamespace(stdout='not-a-container-id')):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as folder:
                image = 'sha256:' + 'a'*64
                config = scene_renderer.RendererConfig(image, Path(folder), 'b'*64)
                request_id = uuid.uuid4().hex
                inspect = SimpleNamespace(stdout=('[{"Id":"' + image + '","Os":"linux","Architecture":"amd64"}]').encode())
                with patch.object(scene_renderer, '_configuration', return_value=(Path(folder), ['docker'], 'ffmpeg')):
                    with patch.object(scene_renderer.subprocess, 'run', side_effect=[inspect, SimpleNamespace(stdout=''), failure]) as run:
                        with self.assertRaises(scene_renderer.RenderOutcomeUnknown) as result:
                            scene_renderer.render(sample(), config, folder, request_id=request_id)
                self.assertEqual(result.exception.request_id, request_id)
                self.assertEqual(run.call_count, 3)  # Never clean up using an unverified receipt.
                self.assertEqual(list(Path(folder).glob('*.png')), [])

    def test_unverified_container_inspection_is_unknown_and_never_cleaned_up(self):
        with tempfile.TemporaryDirectory() as folder:
            image = 'sha256:' + 'a'*64
            config = scene_renderer.RendererConfig(image, Path(folder), 'b'*64)
            request_id = uuid.uuid4().hex
            inspect = SimpleNamespace(stdout=('[{"Id":"' + image + '","Os":"linux","Architecture":"amd64"}]').encode())
            results = [inspect, SimpleNamespace(stdout=''), SimpleNamespace(stdout='c'*64), SimpleNamespace(stdout=b'[null]')]
            with patch.object(scene_renderer, '_configuration', return_value=(Path(folder), ['docker'], 'ffmpeg')):
                with patch.object(scene_renderer.subprocess, 'run', side_effect=results) as run:
                    with self.assertRaises(scene_renderer.RenderOutcomeUnknown) as failure:
                        scene_renderer.render(sample(), config, folder, request_id=request_id)
            self.assertEqual(failure.exception.request_id, request_id)
            self.assertEqual(run.call_count, 4)  # A malformed or foreign receipt is never a cleanup target.


@unittest.skipUnless(os.environ.get('LORETUNE_3D_IMAGE') and os.environ.get('LORETUNE_3D_BLENDER')
                     and os.environ.get('LORETUNE_3D_BLENDER_SHA256') and os.environ.get('LORETUNE_3D_DOCKER_SOCKET'),
                     'trusted local Blender test environment not configured')
class SceneRealRendererTest(unittest.TestCase):
    def config(self, timeout=180):
        return scene_renderer.RendererConfig(os.environ['LORETUNE_3D_IMAGE'],
                                             Path(os.environ['LORETUNE_3D_BLENDER']),
                                             os.environ['LORETUNE_3D_BLENDER_SHA256'], timeout,
                                             Path(os.environ['LORETUNE_3D_DOCKER_SOCKET']))

    def test_real_png_and_camera_change(self):
        with tempfile.TemporaryDirectory() as folder:
            scene = sample()
            with patch.dict(os.environ, {'DOCKER_HOST': 'tcp://127.0.0.1:1', 'DOCKER_CONTEXT': 'not-a-local-context'}):
                first = scene_renderer.render(scene, self.config(), folder, request_id=uuid.uuid4().hex)
            scene['camera']['position'] = [7, -3, 2]
            second = scene_renderer.render(scene, self.config(), folder, request_id=uuid.uuid4().hex)
            self.assertNotEqual(first['sha256'], second['sha256'])
            self.assertNotEqual(first['scene_hash'], second['scene_hash'])
            self.assertEqual(first['kind'], 'local-3d-still')
            self.assertEqual(first['external_calls'], 0)
            self.assertTrue(Path(first['path']).is_file())
            self.assertTrue(Path(second['path']).is_file())
            self.assertEqual(len(list(Path(folder).glob('*.png'))), 2)

    def test_timeout_never_publishes_and_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as folder:
            existing = Path(folder) / 'existing.png'; existing.write_bytes(b'preserved')
            with self.assertRaisesRegex(scene_renderer.RenderError, 'timed out'):
                scene_renderer.render(sample(), self.config(0.01), folder, request_id=uuid.uuid4().hex)
            self.assertEqual(existing.read_bytes(), b'preserved')
            self.assertCountEqual([p.name for p in Path(folder).iterdir()], ['.scene-claims', '.scene-locks', 'existing.png'])

    def test_cancelled_render_never_publishes(self):
        with tempfile.TemporaryDirectory() as folder:
            calls = []
            def cancelled():
                calls.append(True)
                return len(calls) > 1
            with self.assertRaises(scene_renderer.RenderCancelled):
                scene_renderer.render(sample(), self.config(), folder, request_id=uuid.uuid4().hex, cancelled=cancelled)
            self.assertCountEqual([p.name for p in Path(folder).iterdir()], ['.scene-claims', '.scene-locks'])

    def test_concurrent_and_completed_retry_use_one_durable_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            def run():
                try:
                    return scene_renderer.render(sample(), self.config(), folder, request_id=identifier)
                except scene_renderer.RenderOutcomeUnknown:
                    return None
            calls = []
            original_run = subprocess.run
            def traced(command, **kwargs):
                if 'create' in command:
                    calls.append(command)
                return original_run(command, **kwargs)
            with patch.object(scene_renderer.subprocess, 'run', side_effect=traced):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: run(), range(2)))
                successes = [value for value in results if value is not None]
                self.assertTrue(successes)
                self.assertTrue(all(value == successes[0] for value in successes))
                self.assertEqual(scene_renderer.render(sample(), self.config(), folder, request_id=identifier), successes[0])
                self.assertEqual(len(calls), 1)
            self.assertEqual(len(list(Path(folder).glob('*.png'))), 1)
            modified = sample(); modified['camera']['lens_mm'] = 40
            with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                scene_renderer.render(modified, self.config(), folder, request_id=identifier)

    def test_output_overflow_fails_without_publishing_or_overwriting(self):
        # Synthetic test-only code fills a 16 MiB tmpfs and exposes only errno.
        script = ("import os, time\ntry:\n    with open('/output/large.bin', 'wb') as out:\n"
                  "        out.write(b'x' * (20 * 1024 * 1024))\nexcept OSError as error:\n"
                  "    os.unlink('/output/large.bin')\n    with open('/output/frame.png', 'w') as out: out.write(str(error.errno))\n"
                  "    with open('/output/ready', 'w') as out: out.write('done')\n"
                  "    while True: time.sleep(1)\n")
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / 'existing.png'; old.write_bytes(b'preserved')
            observed = []
            def inspect_frame(path, *args):
                observed.append(path.read_bytes())
                raise scene_renderer.RenderError('synthetic invalid image')
            with patch.object(scene_renderer, '_SCRIPT', script), patch.object(scene_renderer, '_check_png', side_effect=inspect_frame):
                with self.assertRaises(scene_renderer.RenderError):
                    scene_renderer.render(sample(), self.config(), folder, request_id=uuid.uuid4().hex)
            self.assertEqual(observed, [b'28'])  # Linux ENOSPC from the isolated tmpfs.
            self.assertEqual(old.read_bytes(), b'preserved')
            self.assertEqual([p.name for p in Path(folder).glob('*.png')], ['existing.png'])

    def test_host_copy_is_bounded_and_does_not_publish_oversized_frame(self):
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / 'existing.png'; old.write_bytes(b'preserved')
            with patch.object(scene_renderer, 'MAX_IMAGE_BYTES', 100):
                with self.assertRaisesRegex(scene_renderer.RenderError, 'size limit'):
                    scene_renderer.render(sample(), self.config(), folder, request_id=uuid.uuid4().hex)
            self.assertEqual(old.read_bytes(), b'preserved')
            self.assertEqual([p.name for p in Path(folder).glob('*.png')], ['existing.png'])

    def test_cancel_at_publication_requires_database_attachment_guard(self):
        # This reproduces the remaining cross-resource race; no Take or DB row is created.
        with tempfile.TemporaryDirectory() as folder:
            from threading import Event
            event = Event()
            real_link = os.link
            def cancel_at_link(*args, **kwargs):
                event.set()
                return real_link(*args, **kwargs)
            with patch.object(scene_renderer.os, 'link', side_effect=cancel_at_link):
                receipt = scene_renderer.render(sample(), self.config(), folder,
                                                request_id=uuid.uuid4().hex, cancelled=event.is_set)
            self.assertTrue(event.is_set())
            self.assertTrue(Path(receipt['path']).is_file())

    def test_publication_io_uncertainty_is_not_retried(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            real_link = os.link
            def link_then_error(*args, **kwargs):
                real_link(*args, **kwargs)
                raise OSError('synthetic acknowledgement loss')
            with patch.object(scene_renderer.os, 'link', side_effect=link_then_error):
                with self.assertRaises(scene_renderer.RenderOutcomeUnknown) as failure:
                    scene_renderer.render(sample(), self.config(), folder, request_id=identifier)
            self.assertEqual(failure.exception.request_id, identifier)
            self.assertTrue((Path(folder) / ('scene-' + identifier + '.png')).is_file())
            with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                scene_renderer.render(sample(), self.config(), folder, request_id=identifier)

    def test_host_kill_auto_removes_container_and_reconcile_does_not_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            marker = Path(folder) / 'test-copy-blocked'
            sentinel = Path(folder) / 'unrelated-user-file'; sentinel.write_bytes(b'preserved')
            code = '''import os, sys, time
from pathlib import Path
from test_scene_contract import sample
import scene_renderer
folder, request = sys.argv[1:]
config = scene_renderer.RendererConfig(os.environ['LORETUNE_3D_IMAGE'], Path(os.environ['LORETUNE_3D_BLENDER']),
  os.environ['LORETUNE_3D_BLENDER_SHA256'], 12, Path(os.environ['LORETUNE_3D_DOCKER_SOCKET']))
def stall(*args, **kwargs):
    (Path(folder) / 'test-copy-blocked').write_text('ready')
    time.sleep(120)
scene_renderer._copy_bounded = stall
scene_renderer.render(sample(), config, folder, request_id=request)
'''
            env = {k: os.environ[k] for k in ('PATH', 'LORETUNE_3D_IMAGE', 'LORETUNE_3D_BLENDER',
                                              'LORETUNE_3D_BLENDER_SHA256', 'LORETUNE_3D_DOCKER_SOCKET')}
            env.update(PYTHONPATH=os.pathsep.join([str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent)]),
                       PYTHONDONTWRITEBYTECODE='1')
            child = subprocess.Popen([sys.executable, '-c', code, folder, identifier], env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            docker = ['docker', '--host', 'unix://' + os.environ['LORETUNE_3D_DOCKER_SOCKET']]
            isolated = Path(folder) / 'query-config'; isolated.mkdir()
            docker_env = {'PATH': env['PATH'], 'HOME': str(isolated), 'DOCKER_CONFIG': str(isolated)}
            def containers():
                result = subprocess.run(docker + ['ps', '-aq', '--no-trunc', '--filter', 'name=^/loretune-scene-' + identifier + '$'],
                                        check=True, capture_output=True, text=True, timeout=10, env=docker_env)
                return result.stdout.strip()
            try:
                deadline = time.monotonic() + 35
                while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.1)
                if not marker.exists():
                    child.kill(); _, stderr = child.communicate(timeout=5)
                    self.fail('render did not reach blocked transfer: ' + stderr.decode(errors='replace')[-1200:])
                self.assertTrue(containers(), 'owned container must exist before SIGKILL')
                child.kill(); child.wait(timeout=5)
                deadline = time.monotonic() + 30
                while containers() and time.monotonic() < deadline:
                    time.sleep(0.25)
                self.assertEqual(containers(), '', 'hard lifetime should stop and auto-remove container')
                self.assertEqual(list(Path(folder).glob('scene-*.png')), [])
                claim = json.loads((Path(folder) / '.scene-claims' / (identifier + '.json')).read_text())
                self.assertEqual(claim['state'], 'claimed')
                before = scene_renderer.reconcile(self.config(), folder, request_id=identifier)
                self.assertEqual((before['status'], before['container'], before['staging']), ('outcome_unknown', 'absent', 'present'))
                after = scene_renderer.reconcile(self.config(), folder, request_id=identifier, cleanup=True)
                self.assertEqual((after['status'], after['container'], after['staging']), ('outcome_unknown', 'absent', 'removed'))
                self.assertEqual(sentinel.read_bytes(), b'preserved')
                with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                    scene_renderer.render(sample(), self.config(), folder, request_id=identifier)
                self.assertEqual(containers(), '')
            finally:
                if child.poll() is None:
                    child.kill(); child.wait(timeout=5)
                if child.stdout: child.stdout.close()
                if child.stderr: child.stderr.close()
                # Only the exact synthetic name created by this test is targeted.
                if containers():
                    subprocess.run(docker + ['rm', '-f', 'loretune-scene-' + identifier],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, env=docker_env)

    def test_recovery_never_deletes_container_without_matching_ownership(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            claims = Path(folder) / '.scene-claims'; claims.mkdir()
            config = self.config()
            record = dict(version=1, request_id=identifier, image_id=config.image_id,
                          blender_sha256=config.blender_sha256, scene_hash=scene_spec.fingerprint(sample()), state='claimed',
                          staging='.scene-render-' + identifier + '-aaaaaaaa')
            (claims / (identifier + '.json')).write_text(json.dumps(record))
            docker = ['docker', '--host', 'unix://' + os.environ['LORETUNE_3D_DOCKER_SOCKET']]
            isolated = Path(folder) / 'query-config'; isolated.mkdir()
            env = {'PATH': os.environ['PATH'], 'HOME': str(isolated), 'DOCKER_CONFIG': str(isolated)}
            name = 'loretune-scene-' + identifier
            created = subprocess.run(docker + ['create', '--name', name, '--label', 'loretune.scene-worker=1',
                                               '--label', 'loretune.scene-request=' + identifier,
                                               '--label', 'loretune.scene-store=' + '0'*64,
                                               '--label', 'loretune.scene-hash=' + scene_spec.fingerprint(sample()),
                                               config.image_id, '/bin/true'], check=True, capture_output=True, text=True,
                                     timeout=30, env=env).stdout.strip()
            self.assertEqual(len(created), 64)
            try:
                with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                    scene_renderer.reconcile(config, folder, request_id=identifier, cleanup=True)
                present = subprocess.run(docker + ['inspect', '--type', 'container', created],
                                         capture_output=True, timeout=10, env=env)
                self.assertEqual(present.returncode, 0, 'foreign container must remain')
            finally:
                subprocess.run(docker + ['rm', '-f', created], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10, env=env)

    def test_recovery_rejects_live_worker_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            (Path(folder) / '.scene-claims').mkdir()
            with scene_renderer._request_lock(Path(folder), identifier):
                with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                    scene_renderer.reconcile(self.config(), folder, request_id=identifier, cleanup=True)

    def test_recovery_rejects_symlink_owner_marker_without_touching_target(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            config = self.config()
            stage = '.scene-render-' + identifier + '-aaaaaaaa'
            stage_path = Path(folder) / stage; stage_path.mkdir()
            user_file = Path(folder) / 'user-file'; user_file.write_text(json.dumps({'request_id': identifier}))
            (stage_path / 'owner.json').symlink_to(user_file)
            claims = Path(folder) / '.scene-claims'; claims.mkdir()
            (claims / (identifier + '.json')).write_text(json.dumps(dict(version=1, request_id=identifier,
                image_id=config.image_id, blender_sha256=config.blender_sha256,
                scene_hash=scene_spec.fingerprint(sample()), state='claimed', staging=stage)))
            with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                scene_renderer.reconcile(config, folder, request_id=identifier, cleanup=True)
            self.assertTrue(stage_path.is_dir())
            self.assertEqual(json.loads(user_file.read_text()), {'request_id': identifier})

    def test_recovery_removes_only_verified_unstarted_owned_container(self):
        with tempfile.TemporaryDirectory() as folder:
            identifier = uuid.uuid4().hex
            config = self.config()
            stage = '.scene-render-' + identifier + '-aaaaaaaa'
            stage_path = Path(folder) / stage; stage_path.mkdir()
            (stage_path / 'owner.json').write_text(json.dumps({'request_id': identifier}))
            claims = Path(folder) / '.scene-claims'; claims.mkdir()
            record = dict(version=1, request_id=identifier, image_id=config.image_id,
                          blender_sha256=config.blender_sha256, scene_hash=scene_spec.fingerprint(sample()), state='claimed', staging=stage)
            (claims / (identifier + '.json')).write_text(json.dumps(record))
            sentinel = Path(folder) / 'other-user-file'; sentinel.write_bytes(b'preserved')
            docker = ['docker', '--host', 'unix://' + os.environ['LORETUNE_3D_DOCKER_SOCKET']]
            isolated = Path(folder) / 'query-config'; isolated.mkdir()
            env = {'PATH': os.environ['PATH'], 'HOME': str(isolated), 'DOCKER_CONFIG': str(isolated)}
            name = 'loretune-scene-' + identifier
            created = subprocess.run(docker + ['create', '--rm', '--name', name, '--label', 'loretune.scene-worker=1',
                                               '--label', 'loretune.scene-request=' + identifier,
                                               '--label', 'loretune.scene-store=' + hashlib.sha256(os.fsencode(str(Path(folder).resolve()))).hexdigest(),
                                               '--label', 'loretune.scene-hash=' + scene_spec.fingerprint(sample()),
                                               config.image_id, '/bin/true'], check=True, capture_output=True, text=True,
                                     timeout=30, env=env).stdout.strip()
            try:
                before = scene_renderer.reconcile(config, folder, request_id=identifier)
                self.assertEqual((before['status'], before['container'], before['staging']), ('outcome_unknown', 'created', 'present'))
                after = scene_renderer.reconcile(config, folder, request_id=identifier, cleanup=True)
                self.assertEqual((after['status'], after['container'], after['staging']), ('outcome_unknown', 'removed', 'removed'))
                self.assertEqual(sentinel.read_bytes(), b'preserved')
                present = subprocess.run(docker + ['inspect', '--type', 'container', created],
                                         capture_output=True, timeout=10, env=env)
                self.assertNotEqual(present.returncode, 0)
                with self.assertRaises(scene_renderer.RenderOutcomeUnknown):
                    scene_renderer.render(sample(), config, folder, request_id=identifier)
            finally:
                subprocess.run(docker + ['rm', '-f', created], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10, env=env)


if __name__ == '__main__':
    unittest.main()
