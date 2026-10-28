import unittest
from editing import frame_timing
class FrameTimingTest(unittest.TestCase):
 def test_cumulative_boundary_error_is_bounded_not_accumulated(self):
  for durations in [[.13]*30,[.125,.13,.141]*10,[1.013]*30]:
   timing=frame_timing(durations);total=0
   for duration,clip in zip(durations,timing['clips']):
    total+=duration
    self.assertGreater(clip['frames'],0)
    self.assertLessEqual(abs(clip['end']-total),1/48+1e-9)
   self.assertLessEqual(abs(timing['duration']-sum(durations)),1/48+1e-9)
 def test_original_timebase_and_aligned_cuts_do_not_change(self):
  timing=frame_timing([1,2,3]);self.assertEqual([c['frames'] for c in timing['clips']],[24,48,72])
  self.assertEqual(timing['duration'],6)
