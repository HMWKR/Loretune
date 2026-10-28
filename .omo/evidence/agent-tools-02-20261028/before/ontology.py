"""Scoped, reviewed runtime ontology snapshots; caller supplies authorized scope.

This is a local domain model, not the project knowledge registry or an auth layer.
No function commits the caller's transaction. Application uses a savepoint so it
also composes atomically with Studio state updates in the same connection.
"""
import hashlib
import json
import sqlite3
import uuid

TYPES = frozenset('project ip character place style song segment shot asset take approval export'.split())
RELATIONS = {
    'belongs_to': ({'project'}, {'ip'}),
    'contains': ({'project', 'song', 'segment'}, {'song', 'segment', 'shot'}),
    'depicts': ({'shot'}, {'character', 'place', 'style'}),
    'references': ({'character', 'place', 'style', 'shot'}, {'asset'}),
    'has_take': ({'shot'}, {'take'}),
    'uses_asset': ({'take', 'song'}, {'asset'}),
    'approves': ({'approval'}, {'take', 'character', 'place', 'style', 'shot'}),
    'includes': ({'export'}, {'take', 'song', 'asset'}),
    'derived_from': (TYPES, TYPES),
}


class OntologyError(ValueError):
    pass


class Conflict(OntologyError):
    pass


def stable_id(scope, kind, source_key):
    """Persist source_key independently of display names; never key on labels."""
    if kind not in TYPES or not all(isinstance(v, str) and v for v in (scope, source_key)):
        raise OntologyError('invalid identity')
    return str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([scope, kind, source_key])))


def _text(value, maximum=4000):
    return isinstance(value, str) and 0 < len(value.strip()) <= maximum


def _exact(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise OntologyError('unknown or missing fields')


def _evidence(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 100:
        raise OntologyError('provenance required')
    for item in value:
        _exact(item, 'source_id excerpt')
        if not _text(item['source_id'], 200) or not _text(item['excerpt']):
            raise OntologyError('invalid provenance')


def validate(graph):
    _exact(graph, 'entities relations')
    if not isinstance(graph['entities'], list) or len(graph['entities']) > 1000:
        raise OntologyError('invalid entities')
    if not isinstance(graph['relations'], list) or len(graph['relations']) > 5000:
        raise OntologyError('invalid relations')
    entities = {}
    ids = set()
    for entity in graph['entities']:
        _exact(entity, 'id type label description provenance uncertainty')
        try:
            if str(uuid.UUID(entity['id'])) != entity['id']:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise OntologyError('invalid UUID') from None
        if entity['id'] in ids or not isinstance(entity['type'], str) or entity['type'] not in TYPES:
            raise OntologyError('duplicate ID or unsupported entity type')
        ids.add(entity['id'])
        entities[entity['id']] = entity
        if not _text(entity['label'], 200) or not isinstance(entity['description'], str) or len(entity['description']) > 10000:
            raise OntologyError('invalid entity text')
        _evidence(entity['provenance'])
        uncertainty = entity['uncertainty']
        _exact(uncertainty, 'status reason')
        if uncertainty['status'] not in ('asserted', 'inferred', 'unknown') or not _text(uncertainty['reason']):
            raise OntologyError('explicit uncertainty required')
    derivations = {}
    for relation in graph['relations']:
        _exact(relation, 'id type source target provenance')
        try:
            if str(uuid.UUID(relation['id'])) != relation['id']:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise OntologyError('invalid relation UUID') from None
        if relation['id'] in ids or not isinstance(relation['type'], str) or relation['type'] not in RELATIONS:
            raise OntologyError('duplicate ID or unsupported relation')
        ids.add(relation['id'])
        if not isinstance(relation['source'], str) or not isinstance(relation['target'], str):
            raise OntologyError('invalid endpoint ID')
        source, target = entities.get(relation['source']), entities.get(relation['target'])
        if not source or not target or source['id'] == target['id']:
            raise OntologyError('dangling or self reference')
        allowed_source, allowed_target = RELATIONS[relation['type']]
        if source['type'] not in allowed_source or target['type'] not in allowed_target:
            raise OntologyError('relation endpoint type mismatch')
        _evidence(relation['provenance'])
        if relation['type'] == 'derived_from':
            if source['type'] != target['type']:
                raise OntologyError('derivation type mismatch')
            derivations.setdefault(source['id'], []).append(target['id'])
    def visit(node, path):
        if node in path:
            raise OntologyError('cyclic derivation')
        for other in derivations.get(node, []):
            visit(other, path | {node})
    for node in derivations:
        visit(node, set())
    # Round-trip both rejects non-JSON values and detaches callers' mutable input.
    return json.loads(json.dumps(graph, allow_nan=False))


def initialize(conn):
    for sql in (
        'CREATE TABLE IF NOT EXISTS ontology_heads(scope TEXT PRIMARY KEY, revision INTEGER NOT NULL)',
        'CREATE TABLE IF NOT EXISTS ontology_versions(scope TEXT, revision INTEGER, body TEXT NOT NULL, digest TEXT NOT NULL, actor TEXT NOT NULL, restored_from INTEGER, PRIMARY KEY(scope,revision))',
        'CREATE TABLE IF NOT EXISTS ontology_proposals(id TEXT PRIMARY KEY, scope TEXT NOT NULL, base_revision INTEGER NOT NULL, body TEXT NOT NULL, digest TEXT NOT NULL, actor TEXT NOT NULL, applied_revision INTEGER)',
    ):
        conn.execute(sql)


def snapshot(conn, scope):
    row = conn.execute('SELECT v.revision,v.body,v.digest FROM ontology_heads h JOIN ontology_versions v ON v.scope=h.scope AND v.revision=h.revision WHERE h.scope=?', (scope,)).fetchone()
    return {'revision': row[0], 'graph': json.loads(row[1]), 'digest': row[2]} if row else {'revision': 0, 'graph': {'entities': [], 'relations': []}, 'digest': None}


def _body(graph):
    body = json.dumps(validate(graph), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return body, hashlib.sha256(body.encode()).hexdigest()


def propose(conn, scope, graph, expected_revision, actor):
    if not _text(scope, 300) or not _text(actor, 200):
        raise OntologyError('scope and actor required')
    if snapshot(conn, scope)['revision'] != expected_revision:
        raise Conflict('ontology changed; review again')
    body, digest = _body(graph)
    proposal_id = str(uuid.uuid4())
    conn.execute('INSERT INTO ontology_proposals VALUES(?,?,?,?,?,?,NULL)', (proposal_id, scope, expected_revision, body, digest, actor))
    return {'id': proposal_id, 'digest': digest, 'base_revision': expected_revision}


def _write(conn, scope, graph, expected_revision, actor, restored_from=None):
    previous = snapshot(conn, scope)
    if previous['revision'] != expected_revision:
        raise Conflict('ontology changed; review again')
    # IDs retain their type forever, including versions no longer at the head.
    types = {}
    for (body,) in conn.execute('SELECT body FROM ontology_versions WHERE scope=?', (scope,)):
        types.update({e['id']: e['type'] for e in json.loads(body)['entities']})
    if any(e['id'] in types and types[e['id']] != e['type'] for e in graph['entities']):
        raise Conflict('stable entity ID cannot change type')
    body, digest = _body(graph)
    revision = expected_revision + 1
    conn.execute('INSERT OR IGNORE INTO ontology_heads VALUES(?,?)', (scope, expected_revision))
    updated = conn.execute('UPDATE ontology_heads SET revision=? WHERE scope=? AND revision=?', (revision, scope, expected_revision))
    if updated.rowcount != 1:
        raise Conflict('concurrent update')
    conn.execute('INSERT INTO ontology_versions VALUES(?,?,?,?,?,?)', (scope, revision, body, digest, actor, restored_from))
    return {'revision': revision, 'graph': json.loads(body), 'digest': digest}


def apply(conn, scope, proposal_id, expected_revision, approved_by, approved=False):
    if approved is not True or not _text(approved_by, 200):
        raise OntologyError('explicit user approval required')
    conn.execute('SAVEPOINT ontology_apply')
    try:
        row = conn.execute('SELECT base_revision,body,applied_revision FROM ontology_proposals WHERE id=? AND scope=?', (proposal_id, scope)).fetchone()
        if not row:
            raise OntologyError('proposal not found in authorized scope')
        if row[2] is not None:
            raise Conflict('proposal already applied')
        if row[0] != expected_revision:
            raise Conflict('proposal review is stale')
        result = _write(conn, scope, json.loads(row[1]), expected_revision, approved_by)
        conn.execute('UPDATE ontology_proposals SET applied_revision=? WHERE id=?', (result['revision'], proposal_id))
        conn.execute('RELEASE ontology_apply')
        return result
    except BaseException:
        conn.execute('ROLLBACK TO ontology_apply')
        conn.execute('RELEASE ontology_apply')
        raise


def rollback(conn, scope, target_revision, expected_revision, approved_by, approved=False):
    if approved is not True or not _text(approved_by, 200):
        raise OntologyError('explicit user approval required')
    row = conn.execute('SELECT body FROM ontology_versions WHERE scope=? AND revision=?', (scope, target_revision)).fetchone()
    if not row:
        raise OntologyError('version not found in authorized scope')
    conn.execute('SAVEPOINT ontology_restore')
    try:
        result = _write(conn, scope, json.loads(row[0]), expected_revision, approved_by, target_revision)
        conn.execute('RELEASE ontology_restore')
        return result
    except BaseException:
        conn.execute('ROLLBACK TO ontology_restore')
        conn.execute('RELEASE ontology_restore')
        raise
