import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import scene_config
import scene_project


class LocalConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.install = self.root / 'trusted-install'
        self.install.mkdir(mode=0o755)
        self.binary = self.install / 'blender'
        self.binary.write_bytes(b'synthetic blender binary')
        self.binary.chmod(0o755)
        self.sockpath = self.root / 'local.sock'
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.bind(str(self.sockpath))
        self.addCleanup(self.socket.close)
        self.path = self.root / 'scene-config.json'
        self.image = 'sha256:' + 'a' * 64
        self.data = dict(version=1, image_id=self.image, blender_root=str(self.install),
                         blender_sha256=hashlib.sha256(self.binary.read_bytes()).hexdigest(),
                         tree_sha256=scene_project.tree_manifest(self.install),
                         docker_socket=str(self.sockpath), timeout_seconds=60,
                         quota_bytes=scene_project.RESERVATION_BYTES * 2)
        self.write(self.data)

    def write(self, value):
        self.path.write_text(json.dumps(value), encoding='utf-8')
        self.path.chmod(0o600)

    def load(self):
        def which(tool):
            return '/synthetic/bin/' + tool if tool in {'docker', 'ffmpeg'} else None
        def inspect(args, **kwargs):
            self.assertEqual(args[1:3], ['--host', 'unix://' + str(self.sockpath)])
            self.assertEqual(args[3:5], ['image', 'inspect'])
            self.assertEqual(args[-1], self.image)
            self.assertNotIn('DOCKER_HOST', kwargs['env'])
            self.assertNotIn('DOCKER_CONTEXT', kwargs['env'])
            self.assertNotIn('SCENE_TEST_SECRET', kwargs['env'])
            return subprocess.CompletedProcess(args, 0, (self.image + ' linux amd64\n').encode())
        with patch('scene_renderer.shutil.which', side_effect=which), \
             patch('scene_config.subprocess.run', side_effect=inspect), \
             patch.dict(os.environ, {'DOCKER_HOST': 'tcp://example.invalid',
                                     'DOCKER_CONTEXT': 'untrusted-context',
                                     'SCENE_TEST_SECRET': 'synthetic-not-a-key'}):
            return scene_config.load(self.path)

    def rejected(self):
        with self.assertRaises(scene_config.SceneConfigError) as error:
            self.load()
        self.assertNotIn(str(self.root), str(error.exception))
        self.assertNotIn('synthetic-not-a-key', str(error.exception))

    def test_valid_configuration_uses_pinned_values_and_isolates_docker_environment(self):
        value = self.load()
        self.assertEqual(value['renderer'].image_id, self.image)
        self.assertEqual(value['renderer'].blender_root, self.install)
        self.assertEqual(value['renderer'].docker_socket, self.sockpath)
        self.assertEqual(value['renderer'].blender_sha256, self.data['blender_sha256'])
        self.assertEqual(value['tree_sha256'], self.data['tree_sha256'])
        self.assertEqual(value['quota_bytes'], self.data['quota_bytes'])

    def test_invalid_shape_types_numbers_and_hashes_are_rejected(self):
        for update in ({'version': True}, {'version': 2}, {'quota_bytes': True},
                       {'quota_bytes': 0}, {'timeout_seconds': True}, {'timeout_seconds': 181},
                       {'timeout_seconds': float('nan')}, {'image_id': 'latest'},
                       {'image_id': 'sha256:'+'A'*64}, {'tree_sha256': 'x'*64},
                       {'blender_sha256': 'x'*64}, {'unknown': 1}):
            with self.subTest(update=update):
                self.write({**self.data, **update}); self.rejected()
        self.write({k: v for k, v in self.data.items() if k != 'tree_sha256'}); self.rejected()
        self.path.write_text('{"version":1,"version":1}', encoding='utf-8'); self.path.chmod(0o600); self.rejected()
        self.path.write_bytes(b'{' + b' ' * scene_config.MAX_CONFIG_BYTES + b'}'); self.path.chmod(0o600); self.rejected()

    def test_resource_number_boundaries_and_large_integers(self):
        for timeout in (10**400, -(10**400), 0, -1, math.inf, -math.inf,
                        math.nan, math.nextafter(scene_config.scene_renderer.TIMEOUT_SECONDS, math.inf)):
            with self.subTest(timeout=timeout):
                self.write({**self.data, 'timeout_seconds': timeout})
                self.rejected()
        for quota in (10**400, -(10**400), scene_project.RESERVATION_BYTES - 1, 2**53 + 1):
            with self.subTest(quota=quota):
                self.write({**self.data, 'quota_bytes': quota})
                self.rejected()
        for timeout in (math.nextafter(0.0, 1.0), scene_config.scene_renderer.TIMEOUT_SECONDS):
            for quota in (scene_project.RESERVATION_BYTES, 2**53):
                with self.subTest(timeout=timeout, quota=quota):
                    self.write({**self.data, 'timeout_seconds': timeout, 'quota_bytes': quota})
                    loaded = self.load()
                    self.assertEqual(loaded['renderer'].timeout_seconds, timeout)
                    self.assertEqual(loaded['quota_bytes'], quota)

    def test_config_file_permissions_symlink_and_untrusted_parent_are_rejected(self):
        self.path.chmod(0o644); self.rejected()
        self.path.chmod(0o600)
        link = self.root / 'config-link'; link.symlink_to(self.path)
        with self.assertRaises(scene_config.SceneConfigError): scene_config.load(link)
        fifo = self.root / 'config-fifo'; os.mkfifo(fifo, 0o600)
        with self.assertRaises(scene_config.SceneConfigError): scene_config.load(fifo)
        self.root.chmod(0o777)
        try: self.rejected()
        finally: self.root.chmod(0o700)

    def test_install_permissions_hash_and_escaping_symlink_are_rejected(self):
        link = self.root / 'install-link'; link.symlink_to(self.install, target_is_directory=True)
        self.write({**self.data, 'blender_root': str(link)}); self.rejected(); self.write(self.data)
        self.binary.chmod(0o775); self.rejected(); self.binary.chmod(0o755)
        self.binary.chmod(0o644); self.rejected(); self.binary.chmod(0o755)
        self.binary.write_bytes(b'changed'); self.rejected()
        self.binary.write_bytes(b'synthetic blender binary')
        external = self.root / 'external'; external.write_text('untrusted')
        link = self.install / 'external-link'; link.symlink_to(external)
        self.rejected(); link.unlink()
        extra = self.install / 'new-file'; extra.write_bytes(b'changed tree')
        self.rejected()

    def test_only_absolute_real_restricted_local_socket_is_accepted(self):
        for path in ('relative.sock', str(self.binary)):
            with self.subTest(path=path):
                self.write({**self.data, 'docker_socket': path}); self.rejected()
        link = self.root / 'socket-link'; link.symlink_to(self.sockpath)
        self.write({**self.data, 'docker_socket': str(link)}); self.rejected()
        self.write(self.data); self.sockpath.chmod(0o777); self.rejected()

    def test_inspection_failure_and_wrong_platform_are_fail_closed(self):
        def which(tool): return '/synthetic/bin/' + tool
        for result in (subprocess.CompletedProcess([], 0, (self.image+' linux arm64\n').encode()),
                       subprocess.CompletedProcess([], 0, ('sha256:'+'b'*64+' linux amd64\n').encode()),
                       subprocess.TimeoutExpired('docker', 20),
                       subprocess.CalledProcessError(1, 'docker')):
            with self.subTest(result=type(result).__name__):
                with patch('scene_renderer.shutil.which', side_effect=which), \
                     patch('scene_config.subprocess.run', side_effect=result if isinstance(result, Exception) else None,
                           return_value=None if isinstance(result, Exception) else result):
                    with self.assertRaises(scene_config.SceneConfigError): scene_config.load(self.path)


@unittest.skipUnless(all(os.environ.get(x) for x in ('LORETUNE_3D_IMAGE', 'LORETUNE_3D_BLENDER',
                       'LORETUNE_3D_BLENDER_SHA256', 'LORETUNE_3D_TREE_SHA256', 'LORETUNE_3D_DOCKER_SOCKET')),
                     'trusted local QA environment not configured')
class RealLocalConfigurationTest(unittest.TestCase):
    def test_real_pinned_docker_and_blender_configuration(self):
        value = dict(version=1, image_id=os.environ['LORETUNE_3D_IMAGE'],
                     blender_root=os.environ['LORETUNE_3D_BLENDER'],
                     blender_sha256=os.environ['LORETUNE_3D_BLENDER_SHA256'],
                     tree_sha256=os.environ['LORETUNE_3D_TREE_SHA256'],
                     docker_socket=os.environ['LORETUNE_3D_DOCKER_SOCKET'],
                     timeout_seconds=120, quota_bytes=scene_project.RESERVATION_BYTES*3)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / 'trusted-config.json'
            path.write_text(json.dumps(value), encoding='utf-8'); path.chmod(0o600)
            loaded = scene_config.load(path)
            self.assertEqual(loaded['renderer'].image_id, value['image_id'])
            self.assertEqual(loaded['tree_sha256'], value['tree_sha256'])


if __name__ == '__main__':
    unittest.main()
