import tempfile
import unittest
import uuid
from app import Store, Conflict


class SettingsTest(unittest.TestCase):
    def test_candidate_correction_and_snapshot_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            def call(action, data):
                return store.mutate(dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex))
            call('setting', dict(text='푸른 달', era='default', valid_from=0, valid_to=None))
            call('project', dict(name='이전 곡', era='default', story=0))
            data = dict(text='은빛 달', era='default', valid_from=0, valid_to=None, supersedes=1, evidence='아트 가이드 2판', reason='공식 설정 정정')
            candidate = call('setting_candidate', data)['candidate']
            second = call('setting_candidate', dict(data, text='경합 정정'))['candidate']
            call('project', dict(name='검토중 곡', era='default', story=0))
            self.assertEqual(store.state()['projects']['검토중 곡']['snapshot'][0]['text'], '푸른 달')
            result = call('review_setting', dict(candidate=candidate, decision='approved', reason='확인'))
            self.assertIn('이전 곡', result['affected_projects'])
            call('project', dict(name='새 곡', era='default', story=0))
            state = store.state()
            self.assertEqual(state['projects']['이전 곡']['snapshot'][0]['text'], '푸른 달')
            self.assertEqual(state['projects']['새 곡']['snapshot'][0]['text'], '은빛 달')
            with self.assertRaises(Conflict):
                call('review_setting', dict(candidate=second, decision='approved', reason='경합'))
            self.assertEqual(state, store.state())
            call('project',dict(name='선택 계승 곡',era='default',story=0,source_song='이전 곡',inherit_revisions=[1],inherit_reason='원작 설정 유지'))
            derived=store.state()['projects']['선택 계승 곡']
            self.assertEqual(derived['snapshot'][0]['text'],'푸른 달')
            self.assertEqual(derived['shots'],{})
            self.assertEqual(derived['audio_versions'],[])
            self.assertIsNone(derived['timeline_head'])
            self.assertEqual(derived['derived_from']['setting_revisions'],[1])
