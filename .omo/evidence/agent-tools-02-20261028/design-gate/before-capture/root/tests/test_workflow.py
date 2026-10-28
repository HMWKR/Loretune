import json
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from loretune import Studio, Conflict

class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.asset = Path(self.tmp.name)/'asset.txt'
        self.asset.write_text('existing asset fixture')
        self.s = Studio()
        self.s.approve_setting('blue moon', era='first', valid_from=1, valid_to=5)
        self.s.new_song('one', era='first', story=2)
        for shot in ['intro', 'chorus']:
            self.s.plan_shot('one', shot, shot)
            self.s.attach_take('one', shot, self.asset, expected_revision=0)
            self.s.select_take('one', shot, 1, expected_revision=1)

    def test_end_to_end_partial_revision_and_reuse(self):
        original = deepcopy(self.s.projects['one'])
        old_estimate = self.s.estimate('one')
        self.s.attach_take('one', 'chorus', self.asset, reason='this song only: calmer cut', expected_revision=2)
        self.s.select_take('one', 'chorus', 2, expected_revision=3)
        self.assertEqual(original['shots']['intro'], self.s.projects['one']['shots']['intro'])
        with self.assertRaises(Conflict): self.s.export('one', old_estimate)
        result = json.loads(self.s.export('one', self.s.estimate('one')))
        self.assertEqual(result['project']['shots']['chorus']['selected'], 2)
        self.s.approve_setting('silver sea', era='second')
        self.s.new_song('two', era='first', story=3)
        self.assertEqual(original['snapshot'], self.s.projects['two']['snapshot'])
        self.assertEqual(original['snapshot'], self.s.projects['one']['snapshot'])
        self.s.new_song('outside', era='first', story=6)
        self.assertEqual([], self.s.projects['outside']['snapshot'])

    def test_selection_conflict(self):
        with self.assertRaises(Conflict): self.s.select_take('one', 'intro', 1, expected_revision=1)

    def test_missing_take_and_unreviewed_shot(self):
        with self.assertRaises(ValueError): self.s.select_take('one', 'intro', 9, expected_revision=2)
        self.s.plan_shot('one', 'outro', 'outro')
        with self.assertRaises(ValueError): self.s.estimate('one')

    def test_modified_asset_rejected(self):
        e = self.s.estimate('one')
        self.asset.write_text('changed')
        with self.assertRaises(Conflict): self.s.export('one', e)

    def test_budget_and_scope(self):
        with self.assertRaises(Conflict): self.s.export('one', self.s.estimate('one'), -1)
        with self.assertRaises(ValueError): self.s.approve_setting('local', scope='song')

if __name__ == '__main__': unittest.main()
