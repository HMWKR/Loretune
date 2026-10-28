import copy
import sqlite3
import tempfile
import unittest
import uuid
from pathlib import Path
import ontology as o


def graph():
    def entity(kind):
        return {'id': o.stable_id('fixture-project', kind, 'original-key'), 'type': kind,
                'label': kind, 'description': '', 'provenance': [{'source_id': 'brief-1', 'excerpt': 'synthetic brief'}],
                'uncertainty': {'status': 'asserted', 'reason': 'user supplied'}}
    shot, take = entity('shot'), entity('take')
    return {'entities': [shot, take], 'relations': [{'id': str(uuid.uuid4()), 'type': 'has_take', 'source': shot['id'], 'target': take['id'], 'provenance': shot['provenance']}]}


class OntologyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'fixture.sqlite'
        self.db = sqlite3.connect(self.path)
        o.initialize(self.db)
        self.db.commit()
    def tearDown(self):
        self.db.close()
        self.temp.cleanup()
    def add(self, body, revision=0):
        return o.propose(self.db, 'project-A', body, revision, 'fixture-user')['id']
    def test_approval_revision_restart_and_rollback(self):
        original = graph()
        pid = self.add(original)
        with self.assertRaises(o.OntologyError):
            o.apply(self.db, 'project-A', pid, 0, 'human')
        first = o.apply(self.db, 'project-A', pid, 0, 'human', True)
        original['entities'][0]['label'] = 'changed label'
        second = o.apply(self.db, 'project-A', self.add(original, 1), 1, 'human', True)
        restored = o.rollback(self.db, 'project-A', 1, 2, 'human', True)
        self.assertEqual(restored['digest'], first['digest'])
        self.assertNotEqual(second['digest'], first['digest'])
        self.assertEqual(restored['revision'], 3)
        self.db.commit()
        other = sqlite3.connect(self.path)
        self.assertEqual(o.snapshot(other, 'project-A'), restored)
        other.close()
    def test_duplicate_apply_and_stale_proposals(self):
        a, b = self.add(graph()), self.add(graph())
        o.apply(self.db, 'project-A', a, 0, 'human', True)
        for pid in (a, b):
            with self.assertRaises(o.Conflict):
                o.apply(self.db, 'project-A', pid, 0, 'human', True)
        self.assertEqual(o.snapshot(self.db, 'project-A')['revision'], 1)
    def test_scope_and_dangling_references(self):
        pid = self.add(graph())
        with self.assertRaises(o.OntologyError):
            o.apply(self.db, 'project-B', pid, 0, 'human', True)
        value = graph(); value['entities'].pop()
        with self.assertRaises(o.OntologyError): o.validate(value)
        self.assertEqual(o.snapshot(self.db, 'project-B')['revision'], 0)
    def test_strict_schema_uncertainty_and_type(self):
        for mutate in (lambda x: x.update({'approved': True}),
                       lambda x: x['entities'][0].update({'type': 'invented'}),
                       lambda x: x['entities'][0].update({'provenance': []}),
                       lambda x: x['entities'][0].update({'uncertainty': {}}),
                       lambda x: x['relations'][0].update({'type': 'includes'})):
            value = graph(); mutate(value)
            with self.assertRaises(o.OntologyError): o.validate(value)
    def test_stable_ids_and_cycle(self):
        self.assertEqual(o.stable_id('s', 'shot', 'key'), o.stable_id('s', 'shot', 'key'))
        self.assertNotEqual(o.stable_id('s', 'shot', 'key'), o.stable_id('other', 'shot', 'key'))
        value = graph(); value['entities'][1]['type'] = 'shot'
        a = value['relations'][0]; a['type'] = 'derived_from'
        value['relations'].append(dict(a, id=str(uuid.uuid4()), source=a['target'], target=a['source']))
        with self.assertRaises(o.OntologyError): o.validate(value)
    def test_sql_failure_is_atomic(self):
        pid = self.add(graph())
        self.db.execute("CREATE TRIGGER fail_write BEFORE INSERT ON ontology_versions BEGIN SELECT RAISE(ABORT,'injected fault'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            o.apply(self.db, 'project-A', pid, 0, 'human', True)
        self.assertEqual(o.snapshot(self.db, 'project-A')['revision'], 0)
        self.assertIsNone(self.db.execute('SELECT applied_revision FROM ontology_proposals WHERE id=?', (pid,)).fetchone()[0])
    def test_stable_type_cannot_be_rebound(self):
        value = graph(); o.apply(self.db, 'project-A', self.add(value), 0, 'human', True)
        value['relations'] = []; value['entities'][0]['type'] = 'song'
        with self.assertRaises(o.Conflict):
            o.apply(self.db, 'project-A', self.add(value, 1), 1, 'human', True)
    def test_outer_transaction_rollback_preserves_studio_atomicity(self):
        self.db.execute('BEGIN')
        pid = self.add(graph())
        o.apply(self.db, 'project-A', pid, 0, 'human', True)
        self.db.rollback()
        self.assertEqual(o.snapshot(self.db, 'project-A')['revision'], 0)

if __name__ == '__main__': unittest.main()
