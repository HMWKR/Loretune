"""Read one pinned public GLB in a temporary directory; emit numeric evidence only."""
import ast
import hashlib
import json
import math
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
receipts = json.loads((OUT / 'download-receipts.json').read_text())
receipt = next(x for x in receipts if x['url'].endswith('/sd_3d.glb'))
source = Path(receipt['temporary_path'])
assert not source.is_relative_to(ROOT), 'Do not store public media inside the repo'
raw = source.read_bytes()
assert len(raw) <= 12 * 1024 * 1024
metadata = json.loads((OUT / 'public-metadata.json').read_text())
claim = next(x for x in metadata['artifacts'] if x['path'].endswith('.glb'))
digest = hashlib.sha256(raw).hexdigest()
assert digest == claim['sha256'] == receipt['sha256']
assert len(raw) == claim['bytes'] == receipt['bytes']
magic, version, length = struct.unpack_from('<4sII', raw)
assert magic == b'glTF' and version == 2 and length == len(raw)
chunks = []
pos = 12
while pos < length:
    assert pos + 8 <= length
    size, kind = struct.unpack_from('<II', raw, pos)
    pos += 8
    assert size % 4 == 0 and pos + size <= length
    chunks.append((kind, raw[pos:pos + size]))
    pos += size
assert [x[0] for x in chunks] == [0x4E4F534A, 0x004E4942]
doc = json.loads(chunks[0][1])
binary = chunks[1][1]
assert len(doc['buffers']) == 1 and 'uri' not in doc['buffers'][0]
declared = doc['buffers'][0]['byteLength']
assert declared <= len(binary) <= declared + 3 and not any(binary[declared:])
binary = binary[:declared]
views = doc['bufferViews']
for view in views:
    assert view['buffer'] == 0
    assert 0 <= view.get('byteOffset', 0) <= len(binary)
    assert view['byteLength'] > 0
    assert view.get('byteOffset', 0) + view['byteLength'] <= len(binary)
formats = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
           5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
dimensions = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
decoded = []
accessors = []
for i, a in enumerate(doc['accessors']):
    assert 'sparse' not in a and a['count'] > 0
    view = views[a['bufferView']]
    code, size = formats[a['componentType']]
    dim = dimensions[a['type']]
    element = size * dim
    stride = view.get('byteStride', element)
    offset = a.get('byteOffset', 0)
    absolute = view.get('byteOffset', 0) + offset
    assert stride >= element and offset >= 0 and absolute % size == 0
    assert offset + (a['count'] - 1) * stride + element <= view['byteLength']
    values = [struct.unpack_from('<' + code * dim, binary, absolute + j * stride)
              for j in range(a['count'])]
    assert all(math.isfinite(x) for row in values for x in row)
    for key, operation in [('min', min), ('max', max)]:
        if key in a:
            assert all(math.isclose(a[key][j], operation(row[j] for row in values),
                                    rel_tol=1e-5, abs_tol=1e-6) for j in range(dim))
    decoded.append(values)
    accessors.append({'index': i, 'count': a['count'], 'type': a['type'],
                      'component_type': a['componentType'], 'scalar_values': a['count'] * dim,
                      'bytes_in_bounds': True, 'finite_values': True})
primitives = []
for mesh_index, mesh in enumerate(doc['meshes']):
    for primitive_index, p in enumerate(mesh['primitives']):
        attrs = p['attributes']
        vertices = len(decoded[attrs['POSITION']])
        assert all(len(decoded[index]) == vertices for index in attrs.values())
        assert p.get('mode', 4) == 4
        indices = [v[0] for v in decoded[p['indices']]] if 'indices' in p else list(range(vertices))
        assert len(indices) % 3 == 0 and all(0 <= x < vertices for x in indices)
        weights = decoded[attrs['WEIGHTS_0']] if 'WEIGHTS_0' in attrs else None
        joints = decoded[attrs['JOINTS_0']] if 'JOINTS_0' in attrs else None
        if joints:
            skin_indices = {n['skin'] for n in doc['nodes'] if n.get('mesh') == mesh_index and 'skin' in n}
            assert all(0 <= x < len(doc['skins'][s]['joints'])
                       for s in skin_indices for row in joints for x in row)
        primitives.append({'mesh': mesh_index, 'primitive': primitive_index, 'vertices': vertices,
                           'triangles': len(indices) // 3, 'index_count': len(indices),
                           'maximum_index': max(indices), 'attributes': list(attrs),
                           'indices_in_range': True,
                           'weight_sum_max_error': max(abs(sum(x) - 1) for x in weights) if weights else None,
                           'negative_weight_count': sum(x < 0 for row in weights for x in row) if weights else None})

def image_dimensions(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        assert data[12:16] == b'IHDR'
        return 'PNG', *struct.unpack_from('>II', data, 16)
    assert data.startswith(b'\xff\xd8')
    pos = 2
    while pos < len(data):
        assert data[pos] == 255
        while data[pos] == 255:
            pos += 1
        marker = data[pos]
        pos += 1
        if marker in [0xD8, 0xD9] or 0xD0 <= marker <= 0xD7:
            continue
        size = struct.unpack_from('>H', data, pos)[0]
        assert size >= 2 and pos + size <= len(data)
        if marker in [0xC0, 0xC1, 0xC2]:
            height, width = struct.unpack_from('>HH', data, pos + 3)
            return 'JPEG', width, height
        assert marker != 0xDA, 'No supported frame header before scan'
        pos += size
    raise ValueError('Image dimensions missing')

images = []
for i, img in enumerate(doc.get('images', [])):
    assert 'uri' not in img
    view = views[img['bufferView']]
    start = view.get('byteOffset', 0)
    data = binary[start:start + view['byteLength']]
    kind, width, height = image_dimensions(data)
    images.append({'index': i, 'format': kind, 'width': width, 'height': height,
                   'pixels': width * height, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'pixel_decode': 'not performed'})
scene_source = ROOT / 'scene_assets.py'
source_bytes = scene_source.read_bytes()
tree = ast.parse(source_bytes)
limits = {}
def number(node):
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.Name): return limits[node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult): return number(node.left) * number(node.right)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add): return number(node.left) + number(node.right)
    raise ValueError('Unsupported constant expression')
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('MAX_'):
        limits[node.targets[0].id] = number(node.value)
counts = {k: len(v) for k, v in doc.items() if isinstance(v, list)}
observations = {'MAX_BYTES': len(raw), 'MAX_JSON_BYTES': len(chunks[0][1]),
                'MAX_VERTICES': sum(p['vertices'] for p in primitives),
                'MAX_TRIANGLES': sum(p['triangles'] for p in primitives),
                'MAX_NODES': len(doc['nodes']), 'MAX_MESHES': len(doc['meshes']),
                'MAX_PRIMITIVES': len(primitives), 'MAX_ACCESSORS': len(accessors),
                'MAX_VIEWS': len(views), 'MAX_MATERIALS': len(doc.get('materials', [])),
                'MAX_IMAGES': len(images), 'MAX_TEXTURES': len(doc.get('textures', [])),
                'MAX_IMAGE_EDGE': max(max(x['width'], x['height']) for x in images),
                'MAX_IMAGE_PIXELS': sum(x['pixels'] for x in images),
                'MAX_ACCESSOR_VALUES': sum(x['scalar_values'] for x in accessors)}
report = {'scope': 'One public pinned output, numeric/static inspection only. No ingest, render, adoption or redistribution.',
          'invocation': 'python3 .omo/evidence/conversation-workflow-20261028/public-artifact/inspect_glb.py',
          'public_url': receipt['url'], 'temporary_input': str(source), 'bytes': len(raw), 'sha256': digest,
          'author_final_hash_and_size_match': True, 'glb_version': version, 'gltf_generator_label': doc['asset'].get('generator'),
          'binary_bounds_checks': 'passed for all bufferViews/accessors', 'counts': counts,
          'chunks': [{'kind': hex(k), 'bytes': len(v)} for k, v in chunks], 'primitives': primitives,
          'mesh_instances': [{'node': i, 'mesh': n['mesh']} for i, n in enumerate(doc['nodes']) if 'mesh' in n],
          'accessors': accessors, 'images': images,
          'skins': [{'joints': len(s['joints']), 'inverse_bind_accessor': s.get('inverseBindMatrices')} for s in doc.get('skins', [])],
          'animations': [{'name': a.get('name'), 'channels': len(a['channels']), 'samplers': len(a['samplers'])} for a in doc.get('animations', [])],
          'extensions_used': doc.get('extensionsUsed', []),
          'current_platform_source': {'path': str(scene_source), 'sha256': hashlib.sha256(source_bytes).hexdigest(),
                                      'imported_or_executed': False, 'limits': limits},
          'numeric_limit_comparison': {k: {'actual': v, 'limit': limits[k], 'within': v <= limits[k]} for k, v in observations.items()},
          'numeric_comparison_scope': 'Only listed metrics checked; no complete admission or decoder validation claimed.',
          'admission': {'mode': 'code-derived comparison only; validator not invoked',
                        'compatible': False, 'blockers': ['KHR_materials_specular material extension', 'top-level skins and animations',
                                                        'JOINTS_0 and WEIGHTS_0 attributes', 'MAT4 inverse-bind accessor', 'skin node field'],
                        'not_a_full_validator': True},
          'not_verified': ['Author provider/model identity and generation run', 'Exact generated front/back image bytes',
                           'Unedited raw generated GLB bytes and before/after diff', 'Claimed skin repair edit count',
                           'Source artwork pixel/hash verification', 'Image pixel decode', 'Visual/render quality',
                           'Full glTF conformance', 'Platform admission/render performance', 'Downstream commercial license'],
          'rights': {'author_status': metadata['rights']['status'], 'interpretation': 'Repository publication record only; no downstream grant inferred'},
          'scope_exclusions': ['No comparison across unrelated subjects', 'No commercial Tripo versus TripoSR parity claim',
                               'No platform workflow completion claim', 'No media copied to product or evidence directory']}
(OUT / 'inspection-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'status': 'inspection passed', 'sha256': digest, 'vertices': observations['MAX_VERTICES'],
                  'triangles': observations['MAX_TRIANGLES'], 'images': images,
                  'numeric_limits_within': all(v <= limits[k] for k, v in observations.items()),
                  'static_platform_compatible': False, 'report': str(OUT / 'inspection-report.json')}, indent=2))
