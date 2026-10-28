import tempfile
import unittest
import uuid
from app import Store


class ArchiveTest(unittest.TestCase):
    def test_archive_freezes_edits_and_clone_resets_media_approval_budget(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            def call(action,**data):
                return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
            call('project',name='source',era='default',story=0)
            call('shot',song='source',shot='intro',description='새벽')
            call('archive_project',song='source',archived=True,reason='마감')
            before=store.state()
            with self.assertRaises(ValueError):call('shot',song='source',shot='late',description='차단')
            self.assertEqual(before,store.state())
            call('project',name='next',era='default',story=0,source_song='source',inherit_revisions=[],inherit_reason='구성만',clone_structure=True)
            p=Store(root).state()['projects']['next']
            self.assertEqual(p['shots']['intro']['description'],'새벽')
            self.assertEqual(p['shots']['intro']['takes'],[])
            self.assertIsNone(p['shots']['intro']['selected'])
            self.assertIsNone(p['timeline_head'])
            self.assertEqual(p['audio_versions'],[])
            self.assertNotIn('render_estimates',p)
            self.assertFalse(p.get('archived',False))
            call('archive_project',song='source',archived=False,reason='재개')
            call('shot',song='source',shot='late',description='재개 후 편집')
