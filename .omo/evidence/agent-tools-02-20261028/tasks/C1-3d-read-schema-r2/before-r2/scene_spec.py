"""Bounded data contract for *optional* local 3D stills.

This module does not grant user permissions or store versions. The caller must
bind and recheck the returned hash inside its own trusted revision/approval
transaction before queueing a render. Version 2 can reference a quarantined,
server-owned static asset; resolving that reference belongs to the host.
"""
from copy import deepcopy
import hashlib
import json
import math
import re
from scene_assets import SUPPORTED_PROFILES as ASSET_PROFILES

MAX_OBJECTS = 8
MAX_LIGHTS = 3
# Fields an existing scene target may change; ids, kinds and object/light
# membership never change (no add or delete).
CHANGE_FIELDS = {'camera': ('position', 'target', 'lens_mm'),
                 'object': ('position', 'rotation_degrees', 'scale', 'color', 'asset'),
                 'light': ('position', 'target', 'energy_w', 'size_m', 'color')}
# (three-component vector?, lower, upper), mirroring validate().
VALUE_BOUNDS = {'position': (True, -100, 100), 'target': (True, -100, 100), 'rotation_degrees': (True, -360, 360),
                'scale': (True, 0.05, 10), 'color': (True, 0, 1), 'lens_mm': (False, 18, 120),
                'energy_w': (False, 0, 5000), 'size_m': (False, 0.1, 20)}


def _exact(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('invalid scene fields')


def _number(value, lower, upper):
    if type(value) not in (int, float) or not lower <= value <= upper or not math.isfinite(value):
        raise ValueError('scene value outside supported range')


def _vector(value, lower, upper):
    if type(value) is not list or len(value) != 3:
        raise ValueError('expected a three-component vector')
    for part in value:
        _number(part, lower, upper)


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,31}', value):
        raise ValueError('invalid scene object id')


def _asset(value):
    _exact(value, ('id', 'sha256', 'profile'))
    if (type(value['id']) is not str or not re.fullmatch(r'[a-f0-9]{32}', value['id']) or
            type(value['sha256']) is not str or not re.fullmatch(r'[a-f0-9]{64}', value['sha256']) or
            value['profile'] not in ASSET_PROFILES):
        raise ValueError('invalid registered scene asset')
    return deepcopy(value)


def validate(scene):
    """Validate exact fields and return a detached copy, never arbitrary code."""
    _exact(scene, ('schema_version', 'width', 'height', 'background', 'objects', 'camera', 'lights'))
    if type(scene['schema_version']) is not int or scene['schema_version'] not in (1, 2):
        raise ValueError('unsupported scene schema')
    for name in ('width', 'height'):
        if type(scene[name]) is not int or not 64 <= scene[name] <= 512:
            raise ValueError('preview dimensions outside supported profile')
    _vector(scene['background'], 0, 1)
    if type(scene['objects']) is not list or not 1 <= len(scene['objects']) <= MAX_OBJECTS:
        raise ValueError('1–8 objects required')
    identifiers = set()
    for obj in scene['objects']:
        mesh = type(obj) is dict and obj.get('kind') == 'mesh'
        _exact(obj, ('id', 'kind', 'position', 'rotation_degrees', 'scale', 'asset' if mesh else 'color'))
        _id(obj['id'])
        if obj['id'] in identifiers or obj['kind'] not in ('cube', 'sphere', 'plane', 'mesh') or mesh and scene['schema_version'] != 2:
            raise ValueError('duplicate id or unsupported primitive')
        identifiers.add(obj['id'])
        _vector(obj['position'], -100, 100)
        _vector(obj['rotation_degrees'], -360, 360)
        _vector(obj['scale'], 0.05, 10)
        if mesh: _asset(obj['asset'])
        else: _vector(obj['color'], 0, 1)
    camera = scene['camera']
    _exact(camera, ('position', 'target', 'lens_mm'))
    _vector(camera['position'], -100, 100)
    _vector(camera['target'], -100, 100)
    _number(camera['lens_mm'], 18, 120)
    if sum((a-b)**2 for a, b in zip(camera['position'], camera['target'])) < 0.01:
        raise ValueError('camera position and target must differ')
    if type(scene['lights']) is not list or not 1 <= len(scene['lights']) <= MAX_LIGHTS:
        raise ValueError('1–3 lights required')
    for light in scene['lights']:
        _exact(light, ('id', 'position', 'target', 'energy_w', 'size_m', 'color'))
        _id(light['id'])
        if light['id'] in identifiers:
            raise ValueError('duplicate scene id')
        identifiers.add(light['id'])
        _vector(light['position'], -100, 100)
        _vector(light['target'], -100, 100)
        if sum((a-b)**2 for a, b in zip(light['position'], light['target'])) < 0.01:
            raise ValueError('light position and target must differ')
        _number(light['energy_w'], 0, 5000)
        _number(light['size_m'], 0.1, 20)
        _vector(light['color'], 0, 1)
    return deepcopy(scene)


def fingerprint(scene):
    """Hash the validated scene; revision/approval binding belongs to the caller."""
    encoded = json.dumps(validate(scene), ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def horizontal_fov_degrees(scene):
    """FOV for the fixed 36 mm horizontal sensor and validated lens."""
    lens = validate(scene)['camera']['lens_mm']
    return math.degrees(2 * math.atan(36 / (2 * lens)))


def asset_references(scene):
    """Return the exact unique asset references already bound into scene data."""
    references = {}
    for obj in validate(scene)['objects']:
        if obj['kind'] != 'mesh': continue
        ref = obj['asset']
        if ref['id'] in references and references[ref['id']] != ref:
            raise ValueError('conflicting scene asset reference')
        references[ref['id']] = ref
    return [references[key] for key in sorted(references)]


def propose_changes(scene, operations, *, base_revision, current_revision, allowed_fields, locked_fields=()):
    """Create a detached typed diff; the host provides revision, scope and locks.

    This is a proposal only. The host must recheck revision and authorization in
    the transaction applying it; none of these arguments authorizes a render.
    A field is represented by ``(target_kind, target_id, field)``.
    """
    for value in (base_revision, current_revision):
        if type(value) is not int or not 0 <= value <= 2**31-1:
            raise ValueError('invalid scene revision')
    if base_revision != current_revision:
        raise ValueError('stale scene revision')
    if type(operations) is not list or not 1 <= len(operations) <= 16:
        raise ValueError('1–16 scene changes required')
    allowed = set(allowed_fields)
    locked = set(locked_fields)
    updated = validate(scene)
    valid_fields = CHANGE_FIELDS
    changes, seen = [], set()
    for operation in operations:
        _exact(operation, ('target', 'id', 'field', 'value'))
        kind, identifier, field = operation['target'], operation['id'], operation['field']
        if not all(isinstance(x, str) for x in (kind, identifier, field)) or kind not in valid_fields or field not in valid_fields[kind]:
            raise ValueError('unsupported scene change')
        key = (kind, identifier, field)
        if key in seen or key not in allowed or key in locked:
            raise ValueError('duplicate, out-of-scope or locked scene change')
        seen.add(key)
        if kind == 'camera' and identifier == 'camera':
            target = updated['camera']
        elif kind in ('object', 'light'):
            matches = [item for item in updated['objects' if kind == 'object' else 'lights'] if item['id'] == identifier]
            if len(matches) != 1:
                raise ValueError('scene target not found')
            target = matches[0]
        else:
            raise ValueError('scene target not found')
        if kind == 'object' and field == 'asset':
            value = _asset(operation['value'])
            before = deepcopy(target['asset']) if target['kind'] == 'mesh' else dict(kind=target['kind'], color=deepcopy(target['color']))
            target['kind'] = 'mesh';target.pop('color', None);target['asset'] = value
            updated['schema_version'] = 2
        else:
            if field not in target: raise ValueError('unsupported field for this scene object')
            before = deepcopy(target[field])
            target[field] = deepcopy(operation['value'])
        changes.append(dict(target=kind, id=identifier, field=field, before=before, after=deepcopy(target[field])))
    updated = validate(updated)
    return dict(scene=updated, scene_hash=fingerprint(updated), changes=changes, base_revision=base_revision)


def _value_schema(field):
    if field == 'asset':
        return dict(type='object', properties=dict(id=dict(type='string', minLength=32, maxLength=32), sha256=dict(type='string', minLength=64, maxLength=64),
                    profile=dict(type='string', enum=list(ASSET_PROFILES))), required=['id', 'sha256', 'profile'], additionalProperties=False)
    vector, lower, upper = VALUE_BOUNDS[field]
    number = dict(type='number', minimum=lower, maximum=upper)
    return dict(type='array', minItems=3, maxItems=3, items=number) if vector else number


# Tool argument shape for a change proposal to an existing, approved scene.
PROPOSAL_SCHEMA = dict(type='object', properties=dict(
    shot_id=dict(type='string', minLength=1, maxLength=200),
    base_revision=dict(type='integer', minimum=1, maximum=2**31-1, description='Current approved scene head; 0 (no approved version) is rejected.'),
    operations=dict(type='array', minItems=1, maxItems=16, items=dict(anyOf=[
        dict(type='object', properties=dict(target=dict(type='string', enum=[kind]),
             id=dict(type='string', enum=['camera']) if kind == 'camera' else dict(type='string', minLength=1, maxLength=32),
             field=dict(type='string', enum=[field]), value=_value_schema(field)),
             required=['target', 'id', 'field', 'value'], additionalProperties=False)
        for kind, fields in CHANGE_FIELDS.items() for field in fields]))),
    required=['shot_id', 'base_revision', 'operations'], additionalProperties=False)


def validate_proposal(args):
    """Check tool arguments only; the host still resolves scope and applies propose_changes."""
    _exact(args, ('shot_id', 'base_revision', 'operations'))
    if type(args['shot_id']) is not str or not args['shot_id'].strip() or len(args['shot_id']) > 200:
        raise ValueError('invalid shot id')
    if type(args['base_revision']) is not int or not 0 <= args['base_revision'] <= 2**31-1:
        raise ValueError('invalid scene revision')
    if args['base_revision'] == 0:
        raise ValueError('no approved scene version; the first draft is reviewed in Scene Studio')
    if type(args['operations']) is not list or not 1 <= len(args['operations']) <= 16:
        raise ValueError('1–16 scene changes required')
    seen = set()
    for operation in args['operations']:
        _exact(operation, ('target', 'id', 'field', 'value'))
        kind, identifier, field, value = operation['target'], operation['id'], operation['field'], operation['value']
        if not all(isinstance(x, str) for x in (kind, identifier, field)) or kind not in CHANGE_FIELDS or field not in CHANGE_FIELDS[kind]:
            raise ValueError('unsupported scene change')
        if kind == 'camera':
            if identifier != 'camera': raise ValueError('scene target not found')
        else: _id(identifier)
        if (kind, identifier, field) in seen:
            raise ValueError('duplicate, out-of-scope or locked scene change')
        seen.add((kind, identifier, field))
        if field == 'asset': _asset(value)
        elif VALUE_BOUNDS[field][0]: _vector(value, *VALUE_BOUNDS[field][1:])
        else: _number(value, *VALUE_BOUNDS[field][1:])
    return deepcopy(args)


def require_approval(scene, binding, approval):
    """Check a server-provided exact approval; this does not authenticate callers.

    The integration must read both binding and approval from trusted storage and
    perform this check with the queue claim in the same transaction.
    """
    _exact(binding, ('workspace_id', 'project_id', 'shot_id', 'scene_id', 'revision', 'ontology_revision'))
    _exact(approval, ('id', 'actor', 'scope', 'binding', 'scene_hash'))
    for field in ('workspace_id', 'project_id', 'shot_id', 'scene_id'):
        value = binding[field]
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
            raise ValueError('invalid binding identifier')
    for field in ('revision', 'ontology_revision'):
        if type(binding[field]) is not int or not 0 <= binding[field] <= 2**31-1:
            raise ValueError('invalid revision')
    if not isinstance(approval['id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', approval['id']):
        raise ValueError('invalid approval identifier')
    approved_binding = approval['binding']
    if type(approved_binding) is not dict or set(approved_binding) != set(binding):
        raise ValueError('matching local still approval required')
    if any(type(approved_binding[k]) is not type(binding[k]) or approved_binding[k] != binding[k] for k in binding):
        raise ValueError('matching local still approval required')
    if approval['actor'] != 'local-owner' or approval['scope'] != 'local-3d-still':
        raise ValueError('matching local still approval required')
    if approval['scene_hash'] != fingerprint(scene):
        raise ValueError('approved scene changed')
    return deepcopy(approval)
