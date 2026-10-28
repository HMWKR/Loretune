import unittest
from copy import deepcopy
from references import assign, review


class ReferenceTest(unittest.TestCase):
    def test_versions_separate_approval_and_preserve_take(self):
        shot=dict(revision=0,takes=[dict(id=1,asset='original')],selected=1)
        old=deepcopy(shot['takes'])
        assign(shot,'start_frame',dict(sha256='a',asset='a.png'),'기준 프레임')
        review(shot,1,'approved','얼굴·의상·배경·구도 확인')
        approved=deepcopy(shot['reference_versions'][0])
        assign(shot,'character',dict(sha256='b',asset='b.png'),'정체성 변경')
        self.assertEqual(shot['reference_versions'][0],approved)
        self.assertEqual(shot['reference_versions'][1]['status'],'unreviewed')
        self.assertEqual(shot['takes'],old)
        self.assertEqual(shot['selected'],1)
        with self.assertRaises(ValueError):review(shot,1,'approved','오래된 화면')
        with self.assertRaises(ValueError):assign(shot,'unsupported',{},'test')
