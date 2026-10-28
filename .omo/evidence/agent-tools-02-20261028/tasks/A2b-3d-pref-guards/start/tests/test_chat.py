import tempfile
import unittest
import uuid
from app import Store


class ChatTest(unittest.TestCase):
    def test_persist_apply_and_no_duplicate_or_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(folder)
            def call(action, data):
                return store.mutate(dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex))
            call('project', dict(name='곡', era='default', story=0))
            plan = call('chat_plan', dict(song='곡', prompt='도시\n하늘'))['plan']
            self.assertEqual(store.state()['projects']['곡']['shots'], {})
            call('shot', dict(song='곡', shot='장면 1', description='기존 장면'))
            first = call('apply_chat_plan', dict(song='곡', plan=plan))
            second = call('apply_chat_plan', dict(song='곡', plan=plan))
            self.assertEqual(first['shots'], second['shots'])
            project = Store(folder).state()['projects']['곡']
            self.assertEqual(len(project['shots']), 3)
            self.assertEqual(project['shots']['장면 1']['description'], '기존 장면')
            self.assertTrue(all(s['selected'] is None and not s['takes'] for s in project['shots'].values()))
            self.assertIsNone(project['timeline_head'])
            self.assertEqual(len(project['conversation']), 3)
            before = store.state()
            with self.assertRaises(ValueError):
                call('chat_plan', dict(song='곡', prompt='장면\n' * 31))
            self.assertEqual(before, store.state())
