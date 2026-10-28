"""Regression for user correction: competitor != provider requirement."""
import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from app import Store
import model_selection,action_execution,runway_provider
class BenchmarkExclusionTest(unittest.TestCase):
 def test_runway_absent_from_catalog_and_resolver_rejects(self):
  self.assertNotIn('runway',json.dumps(model_selection.catalog()).lower())
  with self.assertRaises(ValueError):model_selection.resolve('image',explicit='runway-gen4-image',execute=True)
 def test_retired_stub_fails_before_transport(self):
  with patch('urllib.request.build_opener',side_effect=AssertionError('no I/O')):
   with self.assertRaises(ValueError):runway_provider.RunwayImage(key='synthetic-canary',live_enabled=True)
 def test_new_competitor_action_blocked_but_old_data_preserved(self):
  with tempfile.TemporaryDirectory() as root:
   s=Store(root)
   with s.connect() as c:
    with self.assertRaises(ValueError):action_execution.propose(c,s.workspace_id,'p',plan_id='plan',plan_revision=1,context_hash='ctx',role='image',release_id='gen4_image',inputs={},options={},mode='provider',connection_id='runway-gen4-image-v1')
    self.assertEqual(c.execute('SELECT count(*) FROM production_actions').fetchone()[0],0)
   project={'model_settings':{'revision':1,'selections':{'image':'runway-gen4-image','chat':None,'video':None},'history':[{'preserve':True}]}}
   self.assertEqual(model_selection.settings(project),project['model_settings'])
 def test_runtime_has_no_competitor_import_or_endpoint(self):
  root=Path(__file__).resolve().parents[1]
  for name in ['image_pipeline.py','generation_queue.py','image_recovery.py','index.html']:
   self.assertNotIn('runway',(root/name).read_text().lower())

 def test_old_competitor_job_remains_readable_and_is_not_routed_to_new_worker(self):
  from tests.test_image_pipeline import ImagePipelineTest
  ImagePipelineTest.setUpClass();f=ImagePipelineTest();f.setUp();self.addCleanup(f.doCleanups)
  j=f.start();j['context']['action_binding']['connection_id']='runway-gen4-image-v1'
  with f.store.connect() as c:f.store.generation.save(c,j)
  before=f.store.generation.get(j['id'])
  self.assertFalse(f.store.process_generation());self.assertEqual(f.calls,[])
  self.assertEqual(f.store.generation.get(j['id']),before)
  f.store.image_pipeline=None
  with patch.object(f.store,'provider_adapter',f.adapter):self.assertFalse(f.store.process_generation())
  self.assertEqual(f.calls,[])
