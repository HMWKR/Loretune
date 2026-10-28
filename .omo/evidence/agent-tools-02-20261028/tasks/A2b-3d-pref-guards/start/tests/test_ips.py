import tempfile
import unittest
import uuid
from app import Store


class IPTest(unittest.TestCase):
    def test_ip_setting_isolation_and_restart(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            def call(action, **data):
                return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
            a=call('create_ip',name='A',description='첫 IP')['ip']
            b=call('create_ip',name='B',description='둘째 IP')['ip']
            for ip, value in [(a,'A의 달'),(b,'B의 별')]:
                call('setting',ip=ip,text=value,era='default',valid_from=0,valid_to=None)
                call('project',ip=ip,name=value,era='default',story=0)
            state=Store(root).state()
            self.assertEqual([s['text'] for s in state['projects']['A의 달']['snapshot']],['A의 달'])
            self.assertEqual([s['text'] for s in state['projects']['B의 별']['snapshot']],['B의 별'])
            self.assertEqual(len(state['ips']),3)
            with self.assertRaises(ValueError):
                call('setting_candidate',ip=b,text='잘못된 정정',era='default',valid_from=0,valid_to=None,supersedes=1,evidence='test',reason='test')
            with self.assertRaises(ValueError):call('create_ip',name='A',description='중복')
            self.assertEqual(state,store.state())
