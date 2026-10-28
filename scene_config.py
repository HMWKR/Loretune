"""Load an explicitly trusted local 3D renderer configuration.

This is an administrator-supplied startup contract, not an installer or a
source of trusted hashes.  It does not create a Store or access user data.
The installation and local daemon remain inside the administrator's trust
boundary; checks cannot stop a hostile same-user concurrent file replacement.
"""

import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

import scene_project
import scene_renderer


MAX_CONFIG_BYTES = 16 * 1024
FIELDS = frozenset({
    'version', 'image_id', 'blender_root', 'blender_sha256', 'tree_sha256',
    'docker_socket', 'timeout_seconds', 'quota_bytes',
})


class SceneConfigError(ValueError):
    """Configuration could not be safely accepted; never embeds input values."""


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('duplicate key')
        value[key] = item
    return value


def _constant(_):
    raise ValueError('non-finite JSON number')


def _secure_directory(path):
    """Check resolved ancestors; root-owned sticky temporary dirs are allowed."""
    for part in (path, *path.parents):
        info = part.stat()
        mode = info.st_mode
        if not stat.S_ISDIR(mode) or info.st_uid not in (0, os.geteuid()):
            raise ValueError('untrusted directory owner or type')
        if mode & 0o022 and not (info.st_uid == 0 and mode & stat.S_ISVTX):
            raise ValueError('untrusted directory permissions')


def _path(value, *, kind):
    if type(value) is not str or not value or len(value) > 4096 or '\x00' in value:
        raise ValueError('invalid path')
    raw = Path(value)
    if not raw.is_absolute() or raw.is_symlink():
        raise ValueError('path must be absolute and not a symlink')
    path = raw.resolve(strict=True)
    info = path.stat()
    if info.st_uid not in (0, os.geteuid()):
        raise ValueError('untrusted owner')
    if kind == 'directory':
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('directory required')
        _secure_directory(path)
    else:
        if not stat.S_ISSOCK(info.st_mode) or info.st_mode & stat.S_IWOTH:
            raise ValueError('local restricted socket required')
        _secure_directory(path.parent)
    return path


def _read_config(path):
    raw = Path(path)
    if not raw.is_absolute() or raw.is_symlink():
        raise ValueError('invalid configuration path')
    parent = raw.parent.resolve(strict=True)
    _secure_directory(parent)
    before = (parent / raw.name).lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('configuration must be a regular file')
    flags = (os.O_RDONLY | getattr(os, 'O_CLOEXEC', 0) | getattr(os, 'O_NOFOLLOW', 0) |
             getattr(os, 'O_NONBLOCK', 0))
    fd = os.open(parent / raw.name, flags)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (before.st_dev, before.st_ino) or
                info.st_uid not in (0, os.geteuid()) or
                info.st_mode & 0o077 or info.st_size > MAX_CONFIG_BYTES):
            raise ValueError('unsafe configuration file')
        content = stream.read(MAX_CONFIG_BYTES + 1)
    if len(content) > MAX_CONFIG_BYTES:
        raise ValueError('configuration too large')
    return json.loads(content.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)


def _trusted_tree(root):
    """Reject writable/unowned members; tree_manifest separately checks links."""
    def fail(error):
        raise error
    for folder, dirs, files in os.walk(root, followlinks=False, onerror=fail):
        for name in dirs + files:
            path = Path(folder) / name
            info = path.lstat()
            if info.st_uid not in (0, os.geteuid()):
                raise ValueError('untrusted installation owner')
            if not stat.S_ISLNK(info.st_mode) and info.st_mode & 0o022:
                raise ValueError('untrusted installation permissions')


def _verify_image(docker, image_id):
    # Do not inherit Docker contexts, credentials, proxies or provider keys.
    with tempfile.TemporaryDirectory(prefix='scene-config-docker-') as config_dir:
        env = {'PATH': os.defpath, 'DOCKER_CONFIG': config_dir}
        result = subprocess.run(
            docker + ['image', 'inspect', '--format', '{{.Id}} {{.Os}} {{.Architecture}}', image_id],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20, check=True, env=env,
        )
    if len(result.stdout) > 1024:
        raise ValueError('invalid image inspection')
    if result.stdout.decode('ascii').strip() != image_id + ' linux amd64':
        raise ValueError('unavailable or incompatible local image')


def load(path):
    """Return the trusted server configuration, or raise a value-free error.

    The expected hashes must be provided by the administrator; computing and
    recording the currently installed hashes as trusted values is not done.
    No image pull, network access, credential access, or Store creation occurs.
    """
    try:
        value = _read_config(path)
        if type(value) is not dict or set(value) != FIELDS or type(value['version']) is not int or value['version'] != 1:
            raise ValueError('invalid configuration shape')
        if (type(value['image_id']) is not str or not re.fullmatch(r'sha256:[a-f0-9]{64}', value['image_id']) or
                type(value['blender_sha256']) is not str or not re.fullmatch(r'[a-f0-9]{64}', value['blender_sha256']) or
                type(value['tree_sha256']) is not str or not re.fullmatch(r'[a-f0-9]{64}', value['tree_sha256'])):
            raise ValueError('invalid expected hash')
        timeout, quota = value['timeout_seconds'], value['quota_bytes']
        if (type(timeout) not in (int, float) or
                not 0 < timeout <= scene_renderer.TIMEOUT_SECONDS or not math.isfinite(timeout) or type(quota) is not int or
                not scene_project.RESERVATION_BYTES <= quota <= 2**53):
            raise ValueError('invalid resource limits')
        root = _path(value['blender_root'], kind='directory')
        socket = _path(value['docker_socket'], kind='socket')
        _trusted_tree(root)
        renderer = scene_renderer.RendererConfig(value['image_id'], root, value['blender_sha256'], timeout, socket)
        verified_root, docker, _ = scene_renderer._configuration(renderer)
        if not (root / 'blender').stat().st_mode & stat.S_IXOTH:
            raise ValueError('Blender is not executable by the isolated worker')
        if verified_root != root or scene_project.tree_manifest(root) != value['tree_sha256']:
            raise ValueError('installation hash changed')
        _verify_image(docker, value['image_id'])
        return dict(renderer=renderer, quota_bytes=quota, tree_sha256=value['tree_sha256'])
    except (TypeError, ValueError, OverflowError, OSError, RuntimeError, subprocess.SubprocessError, UnicodeError):
        raise SceneConfigError('로컬 3D 관리자 설정 또는 실행 환경을 확인하세요.') from None
