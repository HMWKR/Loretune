"""Build two self-authored, local-only inputs; never run an AI model."""
from pathlib import Path
import datetime
import hashlib
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import scene_project
import scene_renderer
import scene_spec


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def vector_sub(a, b):
    return [x - y for x, y in zip(a, b)]


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    return [x / length for x in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def projected_box_bounds(scene):
    camera = scene['camera']
    forward = normalize(vector_sub(camera['target'], camera['position']))
    right = normalize(cross(forward, [0, 0, 1]))
    up = cross(right, forward)
    tangent = 36 / (2 * camera['lens_mm'])
    pixels = []
    for obj in scene['objects']:
        assert obj['kind'] == 'cube' and obj['rotation_degrees'] == [0, 0, 0]
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    point = [obj['position'][i] + sign * obj['scale'][i] for i, sign in enumerate((x, y, z))]
                    relative = vector_sub(point, camera['position'])
                    depth = dot(relative, forward)
                    assert depth > 0, 'object behind camera'
                    pixels.append([scene['width'] * (0.5 + dot(relative, right) / (2 * depth * tangent)),
                                   scene['height'] * (0.5 - dot(relative, up) / (2 * depth * tangent))])
    bounds = [min(p[0] for p in pixels), min(p[1] for p in pixels), max(p[0] for p in pixels), max(p[1] for p in pixels)]
    assert 0 < bounds[0] < bounds[2] < scene['width'] and 0 < bounds[1] < bounds[3] < scene['height'], 'projected geometry clipped'
    return bounds


def box(name, position, scale, color):
    return dict(id=name, kind='cube', position=position, rotation_degrees=[0, 0, 0], scale=scale, color=color)


def make_scene(objects):
    return scene_spec.validate(dict(
        schema_version=1, width=512, height=512, background=[1, 1, 1], objects=objects,
        camera=dict(position=[4, -6, 4], target=[0, 0, 1.15], lens_mm=65),
        lights=[dict(id='key', position=[-3, -4, 7], target=[0, 0, 1.15], energy_w=650, size_m=3, color=[1, 1, 1]),
                dict(id='fill', position=[4, -1, 5], target=[0, 0, 1.15], energy_w=350, size_m=3, color=[1, 1, 1])] ))


def inspect_png(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', raw[16:24])
    assert (width, height) == (512, 512)
    result = subprocess.run([shutil.which('ffmpeg'), '-v', 'error', '-i', str(path), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                            capture_output=True, check=True, timeout=20)
    assert not result.stderr and len(result.stdout) == width * height * 3
    pixels = result.stdout
    def pixel(x, y):
        start = (y * width + x) * 3
        return list(pixels[start:start + 3])
    corners = {name: pixel(x, y) for name, x, y in [('top_left', 0, 0), ('top_right', width - 1, 0),
                 ('bottom_left', 0, height - 1), ('bottom_right', width - 1, height - 1)]}
    background = corners['top_left']
    foreground = []
    for y in range(height):
        for x in range(width):
            value = pixel(x, y)
            if max(abs(a - b) for a, b in zip(value, background)) > 10:
                foreground.append((x, y))
    assert foreground, 'blank render'
    bounds = [min(p[0] for p in foreground), min(p[1] for p in foreground), max(p[0] for p in foreground), max(p[1] for p in foreground)]
    return dict(width=width, height=height, byte_length=len(raw), sha256=sha(path), corner_rgb=corners,
                foreground_bbox_rgb_difference_gt_10=bounds,
                bbox_method='Observed RGB distance from top-left background; a framing diagnostic, not a quality metric.',
                png_decode='ffmpeg full RGB24 decode succeeded')


def main():
    for name in ('case-1-cube.scene.json', 'case-2-chair.scene.json', 'case-1-cube.png', 'case-2-chair.png', 'manifest.json'):
        if (OUT / name).exists():
            raise RuntimeError('single-run inputs already exist; do not duplicate render execution')
    prior_path = ROOT / '.omo/evidence/optional-glb-acceptance-20261027/regression-receipt.json'
    prior = json.loads(prior_path.read_text())['environment']
    blender_root = Path(prior['LORETUNE_3D_BLENDER'])
    socket = Path(prior['LORETUNE_3D_DOCKER_SOCKET']).resolve(strict=True)
    binary_hash = sha(blender_root / 'blender')
    tree_hash = scene_project.tree_manifest(blender_root)
    assert binary_hash == prior['LORETUNE_3D_BLENDER_SHA256']
    assert tree_hash == prior['LORETUNE_3D_TREE_SHA256']
    with tempfile.TemporaryDirectory(prefix='paired-3d-inspect-') as temp:
        environment = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': temp, 'DOCKER_CONFIG': temp}
        inspected = subprocess.run(['docker', '--host', 'unix://' + str(socket), 'image', 'inspect', prior['LORETUNE_3D_IMAGE']],
                                   env=environment, capture_output=True, text=True, check=True, timeout=20)
        image = json.loads(inspected.stdout)[0]
    assert image['Id'] == prior['LORETUNE_3D_IMAGE']
    config = scene_renderer.RendererConfig(image['Id'], blender_root, binary_hash, 180, socket)
    source_paths = ['scene_renderer.py', 'scene_spec.py', 'scene_assets.py', 'scene_project.py']
    source_before = {name: sha(ROOT / name) for name in source_paths}
    color = [0.35, 0.12, 0.045]
    chair = [box('seat', [0, 0, 1.05], [0.9, 0.8, 0.12], color),
             box('backrest', [0, 0.7, 1.7], [0.9, 0.1, 0.65], color)]
    for name, x, y in [('front-left', -0.7, -0.6), ('front-right', 0.7, -0.6), ('rear-left', -0.7, 0.6), ('rear-right', 0.7, 0.6)]:
        chair.append(box(name, [x, y, 0.465], [0.075, 0.075, 0.465], color))
    cases = [('case-1-cube', make_scene([box('cube', [0, 0, 1.15], [0.8, 0.8, 0.8], [0.05, 0.25, 0.65])])),
             ('case-2-chair', make_scene(chair))]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = dict(task_id='paired-3d-benchmark-inputs-20261028', attempt=1, lifecycle='REPORTED',
                    started_at_utc=started, command=[sys.executable, str(Path(__file__).relative_to(ROOT))],
                    cwd=str(ROOT), python=sys.version, script_sha256=sha(__file__),
                    environment=dict(blender_root=str(blender_root), blender_sha256=binary_hash, tree_sha256=tree_hash,
                                     docker_socket=str(socket), docker_image={k: image.get(k) for k in ('Id', 'Os', 'Architecture', 'RepoDigests')},
                                     matches_accepted_environment=True, prior_receipt_sha256=sha(prior_path)),
                    renderer=dict(api='scene_renderer.render', product_source_modified=False, compiler_override=False,
                                  source_before=source_before, device='CPU', engine='CYCLES', samples=4, seed=0,
                                  world_rgb_specified=[1, 1, 1], view_transform='not explicitly set by native compiler; effective Blender default not separately inspected',
                                  png_background='Measured pixels below; no pure RGB255 claim, no postprocessing.'),
                    rights=dict(source='self-authored deterministic primitive scenes; no third-party input or mesh',
                                scope='internal evaluation inputs only', public_redistribution_permission_granted=False),
                    comparison=dict(common_input='Pass these exact PNG bytes to each future image-conditioned method.',
                                    ground_truth='Preserved original SceneSpec; deterministic geometry is not itself an AI reconstruction result.',
                                    native_best='Must remain a separate condition from common single-image input.',
                                    benchmark_completed=False, ai_model_outputs=0, quality_equivalence_claim=False), cases=[])
    for name, scene in cases:
        spec_path = OUT / (name + '.scene.json')
        spec_path.write_text(json.dumps(scene, ensure_ascii=False, indent=2) + '\n')
        record = dict(id=name, scene_path=spec_path.name, scene_file_sha256=sha(spec_path),
                      scene_hash=scene_spec.fingerprint(scene), compiled_sha256=hashlib.sha256(scene_renderer.compile_scene(scene)).hexdigest(),
                      primitive_count=len(scene['objects']), projected_geometry_bounds_px=projected_box_bounds(scene),
                      request_id=uuid.uuid4().hex, started_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        print(json.dumps(dict(event='render_start', **record)), flush=True)
        render_start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='paired-3d-native-') as publish:
            receipt = scene_renderer.render(scene, config, publish, request_id=record['request_id'])
            target = OUT / (name + '.png')
            shutil.copyfile(receipt['path'], target)
            assert sha(target) == receipt['sha256']
        record['elapsed_seconds'] = round(time.monotonic() - render_start, 3)
        record['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record['renderer_receipt'] = {key: value for key, value in receipt.items() if key != 'path'}
        record['output_path'] = target.name
        record['png'] = inspect_png(target)
        record['manual_visual_review'] = 'pending direct view_image inspection after script completion'
        manifest['cases'].append(record)
        print(json.dumps(dict(event='render_complete', **record)), flush=True)
    manifest['renderer']['source_after'] = {name: sha(ROOT / name) for name in source_paths}
    assert manifest['renderer']['source_after'] == source_before
    manifest['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest['boundaries'] = dict(native_renders=2, external_ai_calls=0, model_inference_calls=0, weights_downloads=0,
                                  user_data_access=0, product_imports=0, production_data_changes=0, servers_started=0,
                                  renderer_postprocessing=0)
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(event='complete', manifest_sha256=sha(OUT / 'manifest.json'))), flush=True)


if __name__ == '__main__':
    main()
