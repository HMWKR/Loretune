import tempfile,unittest,uuid
from copy import deepcopy
from app import Store
from loretune import Conflict
import model_selection as m

class ModelSelectionTest(unittest.TestCase):
    def test_role_independence_preserves_existing_media_and_context(self):
        p=dict(shots={'one':dict(selected='take1',revision=2)},snapshot=[{'text':'blue coat'}],jobs=[{'id':'inflight'}],embedding={'version':1})
        before=deepcopy(p);m.update(p,{'video':'fal-kling-2-6-pro'},0)
        frozen=m.snapshot(p)
        m.update(p,{'chat':'anthropic-haiku-5-5'},1)
        self.assertEqual(p['model_settings']['selections']['video'],'fal-kling-2-6-pro')
        self.assertIsNone(p['model_settings']['selections']['image'])
        for k in before:self.assertEqual(p[k],before[k])
        self.assertEqual(frozen['value']['model_settings']['revision'],1)
        self.assertNotEqual(frozen['sha256'],m.snapshot(p)['sha256'])
    def test_wrong_role_unknown_and_stale_are_atomic(self):
        p={};m.update(p,{'chat':'anthropic-haiku-5-5'},0);old=deepcopy(p)
        for patch in [{'image':'anthropic-haiku-5-5'},{'chat':'arbitrary'},{'approved':True},{'chat':{'endpoint':'http://bad'}}]:
            with self.assertRaises(ValueError):m.update(p,patch,1)
            self.assertEqual(p,old)
        with self.assertRaises(Conflict):m.update(p,{'chat':None},0)
        self.assertEqual(p,old)
    def test_policy_precedes_execution_no_fallback_or_metadata_activation(self):
        key='anthropic-haiku-5-5'
        self.assertEqual(m.resolve('chat',explicit=key,project=key)['origin'],'explicit')
        with self.assertRaisesRegex(ValueError,'POLICY_BLOCKED'):m.resolve('chat',explicit=key,service=key,forbidden=[key])
        with self.assertRaisesRegex(ValueError,'MODEL_NOT_AVAILABLE'):m.resolve('chat',project=key,execute=True)
        self.assertFalse(m.catalog()['live_execution'])
        self.assertFalse(any(x['state']=='active' for x in m.catalog()['models']))
    def test_change_rejects_late_run_without_modifying_job_snapshot(self):
        p={'production_runs':[dict(state='accepting_tools'),dict(state='completed')],'generation_jobs':[dict(state='running',model='old')]}
        m.update(p,{'chat':'anthropic-haiku-5-5'},0)
        self.assertEqual([r['state'] for r in p['production_runs']],['superseded','completed'])
        self.assertEqual(p['generation_jobs'][0]['model'],'old')
    def test_store_persistence_isolation_duplicate_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            st=Store(folder)
            def req(a,d):return dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex)
            for n in ['A','B']:st.mutate(req('project',dict(name=n,era='default',story=0)))
            r=req('model_settings',dict(song='A',selections={'chat':'anthropic-haiku-5-5'},model_revision=0))
            first=st.mutate(r);self.assertEqual(first,st.mutate(r))
            persisted=Store(folder).state()['projects']
            self.assertEqual(persisted['A']['model_settings']['revision'],1)
            self.assertEqual(persisted['B']['model_settings']['revision'],0)
            bad=req('model_settings',dict(song='A',selections={'chat':None},model_revision=1,approved=True))
            with self.assertRaises(ValueError):st.mutate(bad)
            self.assertEqual(Store(folder).state()['projects'],persisted)
