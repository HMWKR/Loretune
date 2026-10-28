"""Restore verifies copied bytes even when a backup changes after verification."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app import Store
from backup import create, restore


class BackupCopyIntegrityTest(unittest.TestCase):
    def test_backup_changed_after_verify_is_rejected_and_partial_restore_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();store=Store(root/'original')
            (store.root/'assets'/'sample.png').write_bytes(b'original')
            backup=create(store.root,root/'backup')
            copyfile=shutil.copyfile
            changed=[]
            def raced_copy(source,destination):
                if Path(source).name=='sample.png':
                    Path(source).write_bytes(b'changed after verification')
                    changed.append(True)
                return copyfile(source,destination)
            with patch('backup.shutil.copyfile',side_effect=raced_copy):
                with self.assertRaisesRegex(ValueError,'복원 중 백업 파일이 변경'):
                    restore(backup,root/'restored')
            self.assertEqual(changed,[True])
            self.assertFalse((root/'restored').exists())
            self.assertEqual((store.root/'assets'/'sample.png').read_bytes(),b'original')


if __name__=='__main__':unittest.main()
