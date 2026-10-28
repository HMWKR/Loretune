import tempfile
import unittest
import uuid
from copy import deepcopy
from app import Store


class PreferenceTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name)
        self.call('project',name='one',era='default',story=0)
        self.call('project',name='two',era='default',story=0)
    def call(self,action,**data):
        return self.store.mutate(dict(action=action,data=data,revision=self.store.state()['revision'],request_id=uuid.uuid4().hex))
    def propose(self,song,value,**kwargs):
        return self.call('preference_propose',song=song,ip='default',category='camera',value=value,evidence='명시적 원문',reason='검토 후보',**kwargs)['preference']
    def active(self,identifier):self.call('preference_review',id=identifier,decision='active',reason='명시적 승인')
    def plan(self,song):
        self.call('chat_plan',song=song,prompt='한 장면')
        return self.store.state()['projects'][song]['chat_plans'][-1]
    def test_explicit_review_scope_pause_and_frozen_context(self):
        base=self.propose(None,'느린 카메라')
        self.assertEqual(self.plan('one')['preferences'],[])
        self.active(base)
        exception=self.propose('one','빠른 카메라');self.active(exception)
        old=deepcopy(self.plan('one'))
        self.assertEqual(old['preferences'][0]['id'],exception)
        self.assertEqual(self.plan('two')['preferences'][0]['id'],base)
        self.call('preference_review',id=exception,decision='paused',reason='이번 곡 예외 중지')
        self.assertEqual(self.plan('one')['preferences'][0]['id'],base)
        persisted=Store(self.temp.name).state()
        self.assertIn(old,persisted['projects']['one']['chat_plans'])
        self.assertEqual(persisted['canon'],[])
    def test_conflicting_revision_and_cross_ip_do_not_change_active_rule(self):
        base=self.propose(None,'느림');self.active(base)
        unrelated=self.propose(None,'빠름')
        before=self.store.state()
        with self.assertRaises(ValueError):self.active(unrelated)
        self.assertEqual(before,self.store.state())
        new=self.propose(None,'중간',supersedes=base);self.active(new)
        self.assertEqual(self.plan('two')['preferences'][0]['id'],new)
        with self.assertRaises(ValueError):self.active(base)
        other=self.call('create_ip',name='other',description='별도 IP')['ip']
        with self.assertRaises(ValueError):self.call('preference_propose',ip=other,song='one',category='camera',value='x',evidence='x',reason='x')
