"""Trusted, bounded Blender still renderer for platform scenes and static assets.

Only a server administrator may configure the verified local image and a
trusted Blender installation. The executable hash alone does not verify its
libraries or the rest of the mounted directory. This module neither downloads
dependencies nor authenticates users. The app must revalidate the scene and
approval atomically at job claim and before attaching the published result.
"""
from dataclasses import dataclass
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import shutil
import stat
import struct
import subprocess
import tempfile
import time
import uuid

import scene_spec
import scene_assets


_SCRIPT = '''import bpy, json, math, time
from mathutils import Vector
scene_data = json.loads(SCENE_JSON)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 4
scene.cycles.seed = 0
scene.render.resolution_x = scene_data['width']
scene.render.resolution_y = scene_data['height']
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = '/output/frame.png'
scene.world.color = tuple(scene_data['background'])
for data in scene_data['objects']:
    if data['kind'] == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=2, location=data['position'])
    elif data['kind'] == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=data['position'])
    elif data['kind'] == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=2, location=data['position'])
    obj = bpy.context.object
    obj.name = data['id']
    obj.rotation_euler = [math.radians(v) for v in data['rotation_degrees']]
    obj.scale = data['scale']
    material = bpy.data.materials.new('material-' + data['id'])
    material.use_nodes = True
    material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*data['color'], 1)
    obj.data.materials.append(material)
for data in scene_data['lights']:
    bpy.ops.object.light_add(type='AREA', location=data['position'])
    light = bpy.context.object
    light.name = data['id']
    light.data.energy = data['energy_w']
    light.data.size = data['size_m']
    light.data.color = data['color']
    light.rotation_euler = (Vector(data['target']) - light.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add(location=scene_data['camera']['position'])
camera = bpy.context.object
camera.rotation_euler = (Vector(scene_data['camera']['target']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'PERSP'
camera.data.sensor_fit = 'HORIZONTAL'
camera.data.sensor_width = 36
camera.data.lens = scene_data['camera']['lens_mm']
scene.camera = camera
bpy.ops.render.render(write_still=True)
with open('/output/ready', 'x', encoding='ascii') as marker:
    marker.write('complete')
# The output tmpfs disappears when a container stops. Keep this trusted process
# alive while the host copies the verified-size result; the host then removes it.
while True:
    time.sleep(1)
'''

_MESH_IMPORT = '''    if data['kind'] == 'mesh':
        with open('/input/assets.json', encoding='ascii') as metadata_file:
            expected_images = json.load(metadata_file)[data['asset']['sha256']]['images']
        for filename in expected_images:
            image = bpy.data.images.load('/input/' + filename, check_existing=False)
            try:
                check_embedded_image(image)
            finally:
                bpy.data.images.remove(image)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath='/input/model-' + data['asset']['sha256'] + '.glb')
        imported = set(bpy.data.objects) - before
        if not imported or not any(o.type == 'MESH' for o in imported):
            raise ValueError('Imported asset contains no mesh')
        if any(o.type not in {'MESH', 'EMPTY'} for o in imported):
            raise ValueError('Imported asset contains unsupported scene objects')
        images = set()
        for item in imported:
            if item.type != 'MESH': continue
            for slot in item.material_slots:
                material = slot.material
                if material and material.use_nodes:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE':
                            if node.image is None: raise ValueError('Missing embedded image')
                            images.add(node.image)
        if expected_images and not images:
            raise ValueError('Imported textures are missing')
        for image in images:
            check_embedded_image(image)
        root = bpy.data.objects.new('asset-root-' + data['id'], None)
        scene.collection.objects.link(root)
        for item in imported:
            if item.parent not in imported:
                world = item.matrix_world.copy()
                item.parent = root
                item.matrix_world = world
        obj = root
    elif data['kind'] == 'cube':
'''

_IMAGE_CHECK = '''def check_embedded_image(image):
    width, height = image.size
    if width < 1 or height < 1:
        raise ValueError('Embedded texture did not decode')
    values = image.pixels
    if len(values) not in {width * height * channels for channels in (1, 2, 3, 4)}:
        raise ValueError('Embedded texture did not decode')
    if not math.isfinite(values[0]) or not math.isfinite(values[-1]) or not image.has_data:
        raise ValueError('Embedded texture did not decode')
'''

MEMORY_BYTES = 1536 * 1024 * 1024
TIMEOUT_SECONDS = 180
CONTAINER_GRACE_SECONDS = 5
MAX_IMAGE_BYTES = 8 * 1024 * 1024
OUTPUT_TMPFS_BYTES = 16 * 1024 * 1024


class RenderError(RuntimeError):
    pass


class RenderCancelled(RenderError):
    pass


class RenderOutcomeUnknown(RenderError):
    """A durable job must be reconciled by request ID before any retry."""
    def __init__(self, request_id):
        super().__init__('renderer outcome unknown; reconcile the existing request before retry')
        self.request_id = request_id


@dataclass(frozen=True)
class RendererConfig:
    image_id: str
    blender_root: Path
    blender_sha256: str
    timeout_seconds: float = TIMEOUT_SECONDS
    docker_socket: Path = None


def compile_scene(scene):
    """Produce trusted code with validated data only; no user-supplied code."""
    scene=scene_spec.validate(scene)
    data = json.dumps(scene, sort_keys=True, separators=(',', ':'), allow_nan=False)
    script=_SCRIPT
    if scene_spec.asset_references(scene):
        script=script.replace("for data in scene_data['objects']:\n",_IMAGE_CHECK+"for data in scene_data['objects']:\n")
        script=script.replace("    if data['kind'] == 'cube':\n",_MESH_IMPORT)
        script=script.replace('    obj = bpy.context.object\n',"    if data['kind'] != 'mesh': obj = bpy.context.object\n",1)
        original="""    material = bpy.data.materials.new('material-' + data['id'])
    material.use_nodes = True
    material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*data['color'], 1)
    obj.data.materials.append(material)
"""
        script=script.replace(original,"    if data['kind'] != 'mesh':\n"+''.join('    '+line+'\n' for line in original.splitlines()))
    return ('SCENE_JSON = ' + repr(data) + '\n' + script).encode('utf-8')


def _sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _local_docker(config):
    if not isinstance(config, RendererConfig):
        raise RenderError('trusted renderer configuration required')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', config.image_id or ''):
        raise RenderError('immutable local image id required')
    try:
        socket = Path(config.docker_socket).resolve(strict=True)
        if not stat.S_ISSOCK(socket.stat().st_mode):
            raise RenderError('a local Docker Unix socket is required')
    except (OSError, TypeError) as exc:
        raise RenderError('a local Docker Unix socket is required') from exc
    docker = shutil.which('docker')
    if not docker:
        raise RenderError('local Docker is required')
    return [docker, '--host', 'unix://' + str(socket)]


def _configuration(config):
    docker = _local_docker(config)
    if not re.fullmatch(r'[a-f0-9]{64}', config.blender_sha256 or ''):
        raise RenderError('trusted Blender executable hash required')
    if type(config.timeout_seconds) not in (int, float) or not 0 < config.timeout_seconds <= TIMEOUT_SECONDS:
        raise RenderError('invalid renderer timeout')
    try:
        root = Path(config.blender_root).resolve(strict=True)
    except (OSError, TypeError) as exc:
        raise RenderError('trusted Blender installation unavailable') from exc
    binary = root / 'blender'
    if not root.is_dir() or binary.is_symlink() or not binary.is_file() or _sha256(binary) != config.blender_sha256:
        raise RenderError('trusted Blender installation does not match')
    if ',' in str(root):
        raise RenderError('unsupported mount path')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RenderError('local Docker and FFmpeg are required')
    return root, docker, ffmpeg


def _check_png(path, width, height, ffmpeg):
    if path.is_symlink() or not path.is_file() or not 33 <= path.stat().st_size <= MAX_IMAGE_BYTES:
        raise RenderError('renderer output missing or invalid')
    with path.open('rb') as stream:
        head = stream.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n' or head[12:16] != b'IHDR' or struct.unpack('>II', head[16:24]) != (width, height):
        raise RenderError('renderer output dimensions or format invalid')
    try:
        result = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path), '-frames:v', '1', '-f', 'null', '-'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RenderError('renderer output could not be decoded') from exc
    if result.returncode:
        raise RenderError('renderer output could not be decoded')


def _remove_container(docker, container, env):
    try:
        result = subprocess.run(docker + ['rm', '-f', container], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=20, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RenderError('renderer container cleanup failed') from exc
    if result.returncode:
        try:
            remaining = subprocess.run(docker + ['ps', '-aq', '--no-trunc', '--filter', 'id=' + container],
                                       capture_output=True, text=True, timeout=20, env=env)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RenderError('renderer container cleanup failed') from exc
        if remaining.returncode or remaining.stdout.strip():
            raise RenderError('renderer container cleanup failed')


def _copy_bounded(docker, container, frame, env, deadline, cancelled):
    """Stream a single file without `docker cp` or an unbounded host write."""
    process = subprocess.Popen(docker + ['exec', container, '/bin/cat', '/output/frame.png'],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    size = 0
    try:
        with frame.open('xb') as dest:
            while True:
                if cancelled():
                    raise RenderCancelled('render cancelled during output transfer')
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise RenderError('render timed out')
                readable, _, _ = select.select([process.stdout], [], [], min(0.2, remaining))
                if not readable:
                    continue
                chunk = os.read(process.stdout.fileno(), min(65536, MAX_IMAGE_BYTES-size+1))
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_IMAGE_BYTES:
                    raise RenderError('renderer output exceeds size limit')
                dest.write(chunk)
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            raise RenderError('render timed out')
        if process.wait(timeout=remaining) != 0:
            raise RenderError('renderer output could not be copied')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if process.stdout:
            process.stdout.close()


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def _request_lock(publish, request_id):
    """Serialize worker/recovery for one local request; the OS releases on kill."""
    locks = publish / '.scene-locks'
    locks.mkdir(mode=0o700, exist_ok=True)
    if locks.is_symlink() or not locks.is_dir():
        raise RenderOutcomeUnknown(request_id)
    path = locks / (request_id + '.lock')
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            os.close(fd)
            raise RenderOutcomeUnknown(request_id) from exc
    except OSError as exc:
        raise RenderOutcomeUnknown(request_id) from exc
    try:
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _claim(publish, request_id, scene_hash, compiler_hash, config, ffmpeg, width, height, staging, assets=None):
    """Durably claim one ID per output store; never auto-retry unknown work."""
    claims = publish / '.scene-claims'
    claims.mkdir(mode=0o700, exist_ok=True)
    if claims.is_symlink() or not claims.is_dir():
        raise RenderError('invalid request store')
    _fsync_dir(publish)
    path = claims / (request_id + '.json')
    binding = dict(version=1, request_id=request_id, scene_hash=scene_hash,
                   image_id=config.image_id, blender_sha256=config.blender_sha256)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
                raise RenderOutcomeUnknown(request_id)
            record = json.loads(path.read_text(encoding='utf8'))
            if not isinstance(record, dict) or any(type(record.get(k)) is not type(v) or record.get(k) != v for k, v in binding.items()):
                raise RenderOutcomeUnknown(request_id)
            if record.get('state') != 'completed' or not isinstance(record.get('receipt'), dict):
                raise RenderOutcomeUnknown(request_id)
            receipt = record['receipt']
            expected = dict(request_id=request_id, scene_hash=scene_hash, compiler_sha256=compiler_hash,
                            image_id=config.image_id, blender_sha256=config.blender_sha256,
                            width=width, height=height, kind='local-3d-still', assets=assets or [], external_calls=0)
            if any(type(receipt.get(k)) is not type(v) or receipt.get(k) != v for k, v in expected.items()):
                raise RenderOutcomeUnknown(request_id)
            final = publish / ('scene-' + request_id + '.png')
            if receipt.get('path') != str(final):
                raise RenderOutcomeUnknown(request_id)
            _check_png(final, width, height, ffmpeg)
            if _sha256(final) != receipt.get('sha256'):
                raise RenderOutcomeUnknown(request_id)
            return path, binding, receipt
        except (OSError, ValueError, RenderError) as exc:
            raise RenderOutcomeUnknown(request_id) from exc
    try:
        with os.fdopen(fd, 'w', encoding='utf8') as stream:
            json.dump(dict(binding, state='claimed', staging=staging), stream, sort_keys=True, separators=(',', ':'))
            stream.flush()
            os.fsync(stream.fileno())
        _fsync_dir(claims)
    except OSError as exc:
        raise RenderOutcomeUnknown(request_id) from exc
    return path, binding, None


def _complete_claim(path, binding, receipt, staging):
    """Publish a complete receipt atomically; a failed update stays unknown."""
    temp = path.parent / ('.' + path.stem + '-' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('x', encoding='utf8') as stream:
            json.dump(dict(binding, state='completed', receipt=receipt, staging=staging), stream, sort_keys=True, separators=(',', ':'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        _fsync_dir(path.parent)
    finally:
        temp.unlink(missing_ok=True)


def render(scene, config, publish_root, *, request_id, cancelled=lambda: False, assets=None):
    """Render a validated scene and publish a unique verified PNG.

    ``config``, ``publish_root`` and ``cancelled`` are trusted host inputs, not
    model/user arguments. The host must persist the unique request ID and perform
    permission and revision checks before calling. The output store must be a
    trusted local filesystem with reliable flock/fsync semantics; one store is
    the claim namespace. OutcomeUnknown must not be automatically retried.
    Cancellation checks do not provide an atomic DB commit: integration must
    recheck before attaching a verified result.
    """
    scene = scene_spec.validate(scene)
    references=scene_spec.asset_references(scene)
    if assets is None:assets=[]
    if type(assets) is not list or len(assets)!=len(references):raise RenderError('exact registered 3D assets required')
    for asset,ref in zip(assets,references):
        if type(asset) is not dict or set(asset)!=set(ref)|{'path'} or {k:asset[k] for k in ref}!=ref or type(asset['path']) is not str:
            raise RenderError('exact registered 3D assets required')
    if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id):
        raise RenderError('persisted unique request id required')
    root, docker, ffmpeg = _configuration(config)
    try:
        publish = Path(publish_root).resolve(strict=True)
    except (OSError, TypeError) as exc:
        raise RenderError('output directory unavailable') from exc
    if not publish.is_dir() or ',' in str(publish):
        raise RenderError('invalid output directory')
    if cancelled():
        raise RenderCancelled('render cancelled before start')
    with _request_lock(publish, request_id):
        return _render_locked(scene, config, publish, request_id, cancelled, root, docker, ffmpeg,assets)


def _render_locked(scene, config, publish, request_id, cancelled, root, docker, ffmpeg,assets):
    compiled = compile_scene(scene)
    scene_hash = scene_spec.fingerprint(scene)
    store_hash = hashlib.sha256(os.fsencode(str(publish))).hexdigest()
    container = None
    process = None
    with tempfile.TemporaryDirectory(prefix='.scene-render-' + request_id + '-', dir=publish) as temp:
        temp = Path(temp)
        marker = temp / 'owner.json'
        with marker.open('x', encoding='utf8') as stream:
            json.dump({'request_id': request_id}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        _fsync_dir(temp)
        input_dir, output_dir = temp / 'input', temp / 'output'
        input_dir.mkdir(mode=0o755)
        output_dir.mkdir(mode=0o700)
        isolated_config = temp / 'docker-config'
        isolated_config.mkdir(mode=0o700)
        # Do not inherit remote Docker contexts, registry credentials or model
        # keys. The explicitly configured Unix socket is the sole endpoint.
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
               'HOME': str(isolated_config), 'DOCKER_CONFIG': str(isolated_config)}
        # No host-writable output mount is provided to the container.
        script = input_dir / 'scene.py'
        script.write_bytes(compiled)
        script.chmod(0o644)
        asset_metadata={}
        for asset in assets:
            source=Path(asset['path'])
            if not source.is_absolute() or source.is_symlink():raise RenderError('invalid private 3D asset')
            try:
                fd=os.open(source,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
                with os.fdopen(fd,'rb') as stream:
                    info=os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size>scene_assets.MAX_BYTES:raise RenderError('invalid private 3D asset')
                    raw=stream.read(scene_assets.MAX_BYTES+1)
                metadata=scene_assets.validate_glb(raw)
                if metadata['sha256']!=asset['sha256'] or metadata['profile']!=asset['profile']:raise RenderError('3D asset changed before rendering')
                target=input_dir/('model-'+asset['sha256']+'.glb')
                if not target.exists():target.write_bytes(raw);target.chmod(0o444)
                if _sha256(target)!=asset['sha256']:raise RenderError('3D input copy changed')
                image_files=[]
                for index,image in enumerate(scene_assets.embedded_images(raw)):
                    suffix='.png' if image['mime_type']=='image/png' else '.jpg'
                    filename='texture-'+asset['sha256']+'-'+str(index)+suffix
                    image_path=input_dir/filename
                    if not image_path.exists():image_path.write_bytes(image['data']);image_path.chmod(0o444)
                    if image_path.read_bytes()!=image['data']:raise RenderError('embedded 3D image copy changed')
                    image_files.append(filename)
                asset_metadata[asset['sha256']]=dict(images=image_files)
            except (OSError,ValueError) as exc:raise RenderError('private 3D asset validation failed') from exc
        if assets:
            (input_dir/'assets.json').write_text(json.dumps(asset_metadata,sort_keys=True,separators=(',',':')),encoding='ascii')
            (input_dir/'assets.json').chmod(0o444)
        container_name = 'loretune-scene-' + request_id
        lifetime = math.ceil(config.timeout_seconds) + CONTAINER_GRACE_SECONDS
        args = docker + ['create', '--pull=never', '--rm', '--name', container_name, '--log-driver=none',
                '--entrypoint', '/usr/bin/timeout', '--label', 'loretune.scene-worker=1',
                '--label', 'loretune.scene-request=' + request_id, '--label', 'loretune.scene-store=' + store_hash,
                '--label', 'loretune.scene-hash=' + scene_hash, '--platform=linux/amd64', '--network=none',
                '--read-only', '--user=65534:65534', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                '--ipc=private', '--memory=1536m', '--memory-swap=1536m', '--cpus=1', '--pids-limit=64',
                '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777', '--env', 'HOME=/tmp', '--env', 'TMPDIR=/tmp',
                '--tmpfs', '/output:rw,noexec,nosuid,nodev,size=16m,mode=1777',
                '--mount', f'type=bind,src={root},dst=/opt/blender,readonly',
                '--mount', f'type=bind,src={input_dir},dst=/input,readonly',
                config.image_id, '--signal=TERM', '--kill-after=2s', str(lifetime) + 's',
                '/opt/blender/blender', '--background', '--factory-startup', '--disable-autoexec',
                '--threads', '1', '--python-exit-code', '3', '--python', '/input/scene.py']
        try:
            query = subprocess.run(docker + ['image', 'inspect', config.image_id], check=True, capture_output=True, timeout=20, env=env)
            try:
                image = json.loads(query.stdout)[0]
            except (ValueError, IndexError, KeyError) as exc:
                raise RenderError('trusted local renderer image unavailable') from exc
            if image.get('Id') != config.image_id or image.get('Os') != 'linux' or image.get('Architecture') != 'amd64':
                raise RenderError('trusted image does not match required platform')
            claim_path, binding, cached = _claim(publish, request_id, scene_hash, hashlib.sha256(compiled).hexdigest(),
                                                 config, ffmpeg, scene['width'], scene['height'], temp.name,scene_spec.asset_references(scene))
            if cached is not None:
                return cached
            prior = subprocess.run(docker + ['ps', '-aq', '--filter', 'label=loretune.scene-request=' + request_id],
                                   capture_output=True, text=True, timeout=20, check=True, env=env)
            if prior.stdout.strip():
                raise RenderOutcomeUnknown(request_id)
            try:
                result = subprocess.run(args, capture_output=True, text=True, timeout=30, check=True, env=env)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as exc:
                # Once create was submitted, daemon acceptance can be unknown.
                raise RenderOutcomeUnknown(request_id) from exc
            if not isinstance(result.stdout, str):
                raise RenderOutcomeUnknown(request_id)
            receipt_id = result.stdout.strip()
            if not re.fullmatch(r'[a-f0-9]{64}', receipt_id):
                raise RenderOutcomeUnknown(request_id)
            try:
                received = subprocess.run(docker + ['inspect', '--type', 'container', receipt_id],
                                          check=True, capture_output=True, timeout=20, env=env)
                info = json.loads(received.stdout)[0]
            except (OSError, subprocess.SubprocessError, ValueError, IndexError, KeyError, TypeError) as exc:
                raise RenderOutcomeUnknown(request_id) from exc
            if type(info) is not dict or type(info.get('Config')) is not dict:
                raise RenderOutcomeUnknown(request_id)
            labels = info['Config'].get('Labels')
            if (type(labels) is not dict or info.get('Id') != receipt_id or info.get('Name') != '/' + container_name or
                info.get('Image') != config.image_id or labels.get('loretune.scene-worker') != '1' or
                labels.get('loretune.scene-request') != request_id or labels.get('loretune.scene-store') != store_hash or
                labels.get('loretune.scene-hash') != scene_hash):
                raise RenderOutcomeUnknown(request_id)
            # Only a verified, uniquely named container can be cleaned up.
            container = receipt_id
            host = info.get('HostConfig', {})
            if type(host) is not dict or type(info.get('Mounts')) is not list:
                raise RenderError('renderer isolation configuration mismatch')
            tmpfs = host.get('Tmpfs') or {}
            if type(tmpfs) is not dict or any(type(m) is not dict for m in info['Mounts']):
                raise RenderError('renderer isolation configuration mismatch')
            mounts = [m for m in info.get('Mounts', []) if m.get('Type') == 'bind']
            if (host.get('NetworkMode') != 'none' or host.get('ReadonlyRootfs') is not True or
                host.get('Memory') != MEMORY_BYTES or host.get('MemorySwap') != MEMORY_BYTES or host.get('AutoRemove') is not True or
                (host.get('RestartPolicy') or {}).get('Name') != 'no' or
                host.get('NanoCpus') != 1_000_000_000 or host.get('PidsLimit') != 64 or
                'ALL' not in (host.get('CapDrop') or []) or (host.get('LogConfig') or {}).get('Type') != 'none' or
                'no-new-privileges' not in (host.get('SecurityOpt') or []) or
                info.get('Config', {}).get('User') != '65534:65534' or 'size=16m' not in tmpfs.get('/output', '') or
                info.get('Path') != '/usr/bin/timeout' or info.get('Args', [])[:3] != ['--signal=TERM', '--kill-after=2s', str(lifetime) + 's'] or
                len(mounts) != 2 or {m.get('Destination') for m in mounts} != {'/input', '/opt/blender'} or
                any(m.get('RW') is not False for m in mounts)):
                raise RenderError('renderer isolation configuration mismatch')
            process = subprocess.Popen(docker + ['start', '-a', container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            deadline = time.monotonic() + config.timeout_seconds
            while True:
                if cancelled():
                    raise RenderCancelled('render cancelled')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RenderError('render timed out')
                if process.poll() is not None:
                    raise RenderError('renderer stopped before producing output')
                try:
                    ready = subprocess.run(docker + ['exec', container, '/bin/test', '-f', '/output/ready'],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                           timeout=min(5, remaining), env=env)
                except subprocess.TimeoutExpired as exc:
                    raise RenderError('renderer readiness check timed out') from exc
                if ready.returncode == 0:
                    break
                time.sleep(min(0.2, max(0, deadline-time.monotonic())))
            frame = output_dir / 'frame.png'
            _copy_bounded(docker, container, frame, env, deadline, cancelled)
            _remove_container(docker, container, env)
            container = None
            if cancelled():
                raise RenderCancelled('render cancelled before publication')
            _check_png(frame, scene['width'], scene['height'], ffmpeg)
            digest = _sha256(frame)
            if cancelled():
                raise RenderCancelled('render cancelled before publication')
            final = publish / ('scene-' + request_id + '.png')
            # An atomic hard link publishes only a fully verified file and never
            # overwrites an existing file; staging lives on the same volume.
            try:
                os.link(frame, final, follow_symlinks=False)
                _fsync_dir(publish)
            except OSError as exc:
                # The link or its durability may have succeeded despite the
                # failure. The claim remains and must be reconciled.
                raise RenderOutcomeUnknown(request_id) from exc
            receipt = dict(path=str(final), request_id=request_id, sha256=digest, scene_hash=scene_hash,
                           compiler_sha256=hashlib.sha256(compiled).hexdigest(), image_id=config.image_id,
                           blender_sha256=config.blender_sha256, width=scene['width'], height=scene['height'],
                           kind='local-3d-still', assets=scene_spec.asset_references(scene), external_calls=0)
            try:
                _complete_claim(claim_path, binding, receipt, temp.name)
            except OSError as exc:
                raise RenderOutcomeUnknown(request_id) from exc
            return receipt
        except (OSError, subprocess.SubprocessError) as exc:
            raise RenderError('local renderer could not run') from exc
        finally:
            cleanup_error = None
            if container:
                try:
                    _remove_container(docker, container, env)
                except RenderError as exc:
                    cleanup_error = exc
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if cleanup_error:
                raise RenderOutcomeUnknown(request_id) from cleanup_error


def reconcile(config, publish_root, *, request_id, cleanup=False):
    """Inspect one durable claim, optionally remove only its owned leftovers.

    The host must authorize cleanup and call this after worker restart. A local
    lock prevents racing a live renderer sharing this output store. Unknown is
    deliberately not converted into permission to render again or attach output.
    Absence on one lookup does not prove an in-flight create cannot appear later;
    recheck the same ID before treating cleanup as final. A recorded completion
    is not verified here and is not authorization to attach the output.
    """
    if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9]{32}', request_id) or type(cleanup) is not bool:
        raise RenderError('invalid recovery request')
    docker = _local_docker(config)
    try:
        publish = Path(publish_root).resolve(strict=True)
    except (OSError, TypeError) as exc:
        raise RenderError('output directory unavailable') from exc
    if not publish.is_dir():
        raise RenderError('invalid output directory')
    claims = publish / '.scene-claims'
    if claims.is_symlink() or not claims.is_dir():
        raise RenderOutcomeUnknown(request_id)
    with _request_lock(publish, request_id):
        claim = claims / (request_id + '.json')
        try:
            fd = os.open(claim, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'rb') as stream:
                st = os.fstat(stream.fileno())
                if not stat.S_ISREG(st.st_mode) or st.st_size > 16384:
                    raise RenderOutcomeUnknown(request_id)
                record = json.loads(stream.read(16385))
        except (OSError, ValueError) as exc:
            raise RenderOutcomeUnknown(request_id) from exc
        if (type(record) is not dict or type(record.get('version')) is not int or record['version'] != 1 or
            record.get('request_id') != request_id or record.get('image_id') != config.image_id or
            type(record.get('blender_sha256')) is not str or not re.fullmatch(r'[a-f0-9]{64}', record['blender_sha256']) or
            record['blender_sha256'] != config.blender_sha256 or type(record.get('scene_hash')) is not str or
            not re.fullmatch(r'[a-f0-9]{64}', record['scene_hash']) or type(record.get('state')) is not str or
            record['state'] not in {'claimed', 'completed'}):
            raise RenderOutcomeUnknown(request_id)
        staging = record.get('staging')
        if not isinstance(staging, str) or not re.fullmatch(r'\.scene-render-' + request_id + r'-[a-z0-9_]{8}', staging):
            raise RenderOutcomeUnknown(request_id)
        stage_path = publish / staging
        stage_present = stage_path.exists() or stage_path.is_symlink()
        if stage_present:
            try:
                if stage_path.is_symlink() or not stage_path.is_dir():
                    raise RenderOutcomeUnknown(request_id)
                marker_fd = os.open(stage_path / 'owner.json', os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
                with os.fdopen(marker_fd, 'rb') as marker:
                    st = os.fstat(marker.fileno())
                    if not stat.S_ISREG(st.st_mode) or st.st_size > 2048:
                        raise RenderOutcomeUnknown(request_id)
                    if json.loads(marker.read(2049)) != {'request_id': request_id}:
                        raise RenderOutcomeUnknown(request_id)
            except (OSError, ValueError) as exc:
                raise RenderOutcomeUnknown(request_id) from exc
        with tempfile.TemporaryDirectory(prefix='.scene-recover-', dir=publish) as tmp:
            env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': tmp, 'DOCKER_CONFIG': tmp}
            try:
                found = subprocess.run(docker + ['ps', '-aq', '--no-trunc', '--filter',
                                       'name=^/loretune-scene-' + request_id + '$'],
                                       check=True, capture_output=True, text=True, timeout=20, env=env)
                ids = found.stdout.splitlines()
                if len(ids) > 1 or any(not re.fullmatch(r'[a-f0-9]{64}', item) for item in ids):
                    raise RenderOutcomeUnknown(request_id)
                info = None
                if ids:
                    raw = subprocess.run(docker + ['inspect', '--type', 'container', ids[0]],
                                         check=True, capture_output=True, timeout=20, env=env)
                    info = json.loads(raw.stdout)[0]
            except (OSError, subprocess.SubprocessError, ValueError, IndexError, TypeError) as exc:
                raise RenderOutcomeUnknown(request_id) from exc
            container_state = 'absent'
            if info is not None:
                if type(info) is not dict or type(info.get('Config')) is not dict:
                    raise RenderOutcomeUnknown(request_id)
                labels = info['Config'].get('Labels')
                state = info.get('State')
                if (type(labels) is not dict or type(state) is not dict or info.get('Id') != ids[0] or
                    info.get('Name') != '/loretune-scene-' + request_id or info.get('Image') != config.image_id or
                    labels.get('loretune.scene-request') != request_id or labels.get('loretune.scene-worker') != '1' or
                    labels.get('loretune.scene-store') != hashlib.sha256(os.fsencode(str(publish))).hexdigest() or
                    labels.get('loretune.scene-hash') != record['scene_hash']):
                    raise RenderOutcomeUnknown(request_id)
                container_state = state.get('Status')
                if container_state not in {'created', 'running', 'paused', 'restarting', 'removing', 'exited', 'dead'}:
                    raise RenderOutcomeUnknown(request_id)
                if cleanup:
                    try:
                        _remove_container(docker, ids[0], env)
                    except RenderError as exc:
                        raise RenderOutcomeUnknown(request_id) from exc
                    container_state = 'removed'
        if cleanup and stage_present:
            try:
                shutil.rmtree(stage_path)
                _fsync_dir(publish)
            except OSError as exc:
                raise RenderOutcomeUnknown(request_id) from exc
        return dict(request_id=request_id, status='completed-recorded' if record['state'] == 'completed' else 'outcome_unknown',
                    container=container_state, staging='removed' if cleanup and stage_present else 'present' if stage_present else 'absent')
