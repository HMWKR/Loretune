"""Exercise actual control handlers and reservation copy for both chat runtimes."""
from pathlib import Path
import subprocess
import unittest


class GeneralModelScheduleUITest(unittest.TestCase):
    def test_availability_recovery_and_reservation_controls(self):
        result = subprocess.run(['node', 'tests/general_model_schedule_ui.cjs'],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
