import unittest,tempfile
from app import Store
from image_adapter import SyntheticImageAdapter
class ImageAdapterTest(unittest.TestCase):
 def test_actual_png_decodes_and_is_labelled_fake(self):
  adapter=SyntheticImageAdapter();result=adapter.generate(dict(prompt='synthetic geometry',width=64,height=32))
  with tempfile.TemporaryDirectory() as folder:
   path,metadata=Store(folder).save_media(result['bytes'],'.png','video')
   self.assertEqual(path.stem,result['sha256']);self.assertEqual((metadata['width'],metadata['height']),(64,32))
  self.assertIn('not AI',result['provenance']);self.assertEqual(result['external_calls'],0)
 def test_arbitrary_url_reference_and_unsupported_dimensions_are_rejected(self):
  for request in [dict(prompt='x',width=64,height=64,url='http://localhost/private'),dict(prompt='x',width=10000,height=64)]:
   with self.assertRaises(ValueError):SyntheticImageAdapter().generate(request)
