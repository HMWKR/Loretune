"""Requirement QA: adversarial local inputs, not organization authorization tests."""
import tempfile
import unittest
import uuid
from app import Store, Conflict


class BoundaryQA(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)

    def call(self, action, **data):
        return self.store.mutate(dict(action=action, data=data,
            revision=self.store.state()['revision'], request_id=uuid.uuid4().hex))

    def test_inheritance_rejects_cross_ip_and_unknown_revisions_atomically(self):
        self.call('setting', text='달', era='default', valid_from=0, valid_to=None)
        self.call('project', name='원본', era='default', story=0)
        other = self.call('create_ip', name='다른 IP', description='QA')['ip']
        before = self.store.state()
        for extra in [dict(ip=other, inherit_revisions=[1]),
                      dict(inherit_revisions=[999]), dict(inherit_revisions=[1,1]),
                      dict(inherit_revisions=[True])]:
            with self.assertRaises(ValueError):
                self.call('project', name='실패해야 함', era='default', story=0,
                          source_song='원본', inherit_reason='QA', **extra)
            self.assertEqual(self.store.state(), before)

    def test_chat_empty_over_limit_and_apply_retry(self):
        self.call('project', name='QA', era='default', story=0)
        before = self.store.state()
        for value in ['', '  ', 'x'*2001, '\n'.join(['장면']*31)]:
            with self.assertRaises(ValueError): self.call('chat_plan', song='QA', prompt=value)
            self.assertEqual(self.store.state(), before)
        plan = self.call('chat_plan', song='QA', prompt='달\n도시')
        identifier = self.store.state()['projects']['QA']['chat_plans'][0]['id']
        self.call('apply_chat_plan', song='QA', plan=identifier)
        self.call('apply_chat_plan', song='QA', plan=identifier)
        p = self.store.state()['projects']['QA']
        self.assertEqual(len(p['shots']), 2)
        self.assertTrue(all(not s['takes'] for s in p['shots'].values()))

    def test_request_id_payload_mismatch_is_not_a_second_write(self):
        req = dict(action='project', data=dict(name='첫 요청', era='default', story=0),
                   revision=0, request_id='stable-request')
        self.store.mutate(req)
        before = self.store.state()
        req['data']['name'] = '변조 요청'
        with self.assertRaises(Conflict): self.store.mutate(req)
        self.assertEqual(self.store.state(), before)
