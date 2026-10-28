import json
import tempfile
import unittest
import uuid
from pathlib import Path
from app import Store
from backup import create, restore, verify


class BackupTest(unittest.TestCase):
    def test_restore_relocates_asset_preserves_text_and_detects_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            store = Store(root / 'data')
            asset = store.root / 'assets' / 'sample.png'
            asset.write_bytes(b'fixture')
            project = dict(name='test', shots={}, snapshot=[], asset=str(asset), note=str(asset))
            with store.connect() as db:
                db.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(dict(canon=[], projects={'test':project})),))
            create(store.root, root / 'backup')
            verify(root / 'backup')
            restore(root / 'backup', root / 'restored')
            restored = Store(root / 'restored').state()['projects']['test']
            self.assertEqual(restored['asset'], str(root / 'restored/assets/sample.png'))
            self.assertEqual(restored['note'], str(asset))
            self.assertEqual(Path(restored['asset']).read_bytes(), b'fixture')
            with self.assertRaises(ValueError):
                restore(root / 'backup', store.root)
            (root / 'backup/assets/sample.png').write_bytes(b'tamper')
            with self.assertRaises(ValueError):
                restore(root / 'backup', root / 'bad')
            self.assertFalse((root / 'bad').exists())

    def test_reject_active_jobs_and_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            store = Store(root / 'data')
            with store.connect() as db:
                db.execute('INSERT INTO jobs VALUES (?,?)', (uuid.uuid4().hex, json.dumps(dict(status='queued'))))
            with self.assertRaises(ValueError):
                create(store.root, root / 'backup')
            with store.connect() as db:
                db.execute('DELETE FROM jobs')
            create(store.root, root / 'backup')
            manifest = root / 'backup/backup-manifest.json'
            body = json.loads(manifest.read_text())
            body['files']['../escape'] = 'anything'
            manifest.write_text(json.dumps(body))
            with self.assertRaises(ValueError):
                restore(root / 'backup', root / 'restored')

    def test_active_generation_blocks_offline_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=Store(root/'data')
            with store.connect() as db:db.execute('INSERT INTO generation_jobs(id,body) VALUES (?,?)',('fake',json.dumps(dict(state='downloading'))))
            with self.assertRaises(ValueError):create(store.root,root/'backup')
            self.assertFalse((root/'backup').exists())
