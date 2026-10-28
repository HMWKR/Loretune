import tempfile, unittest, uuid
from app import Store
from guided import propose, apply
from loretune import Studio

class GuidedTest(unittest.TestCase):
    def setup_project(self):
        s=Studio();s.new_song('곡',era='default',story=0)
        p=s.projects['곡'];p.update(music_head=1,music_versions=[dict(id=1,audio=1,start=32,end=47)])
        return s,p
    def test_authored_plan_mapping_idempotency_and_reload(self):
        s,p=self.setup_project();d=dict(goal='내 이야기',scenes='주인공은 그대로\n장면 둘',style='청색',constraints='얼굴 변경 금지')
        plan=propose(p,d);shots=apply(s,'곡',plan['id']);self.assertEqual(shots,apply(s,'곡',plan['id']))
        self.assertEqual(p['shots'][shots[0]]['description'],'주인공은 그대로')
        self.assertEqual([p['shots'][x]['music_start'] for x in shots],[32,39.5])
        self.assertEqual(sum(p['shots'][x]['planned_duration'] for x in shots),15)
        from editing import current
        timeline=current(p)
        self.assertEqual(timeline['audio_offset'],32)
        self.assertEqual(sum(x['duration'] for x in timeline['clips']),15)
        self.assertFalse(plan['approval']['cost_approval']);self.assertEqual(len(set(p['shots'][x]['stable_id'] for x in shots)),2)
        self.assertTrue(all(not p['shots'][x]['takes'] for x in shots))
    def test_missing_and_stale_music_block_apply_without_mutation(self):
        s,p=self.setup_project();p['music_head']=None
        plan=propose(p,dict(goal='이야기',scenes='설명'))
        self.assertTrue(plan['questions'])
        with self.assertRaises(ValueError):apply(s,'곡',plan['id'])
        self.assertFalse(p['shots']);p['music_head']=1
        plan=propose(p,dict(goal='이야기',scenes='설명'));p['music_versions'][0]['end']=48
        with self.assertRaises(ValueError):apply(s,'곡',plan['id'])
        self.assertFalse(p['shots'])
    def test_store_transaction_and_wrong_project(self):
        with tempfile.TemporaryDirectory() as folder:
            st=Store(folder)
            def call(a,d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
            for n in ['A','B']:call('project',dict(name=n,era='default',story=0))
            plan=call('guided_plan',dict(song='A',goal='직접 쓴 목표',scenes='그대로 보존'))['plan']
            self.assertEqual(Store(folder).state()['projects']['A']['guided_plans'][0]['goal'],'직접 쓴 목표')
            stored=Store(folder).state()['projects']['A']
            self.assertEqual(stored['production_runs'][0]['state'],'completed')
            self.assertEqual(stored['production_runs'][0]['calls'][0]['result']['plan']['id'],plan)
            self.assertFalse(stored['production_runs'][0]['live_model_called'])
            before=st.state()
            with self.assertRaises(ValueError):call('apply_guided_plan',dict(song='B',plan=plan))
            self.assertEqual(st.state(),before)
            with self.assertRaises(ValueError):call('guided_plan',dict(song='A',goal='목표',scenes='장면\n'*31))
            self.assertEqual(st.state(),before)
