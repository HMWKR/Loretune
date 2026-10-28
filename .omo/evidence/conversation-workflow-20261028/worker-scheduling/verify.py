"""Capture bounded-worker test results and synthetic runtime artifacts."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tests import test_worker_scheduling as worker_tests

EVIDENCE = Path(__file__).resolve().parent
records = []

def capture(self):
    target = EVIDENCE / self._testMethodName
    target.mkdir(exist_ok=True)
    store = self.store
    with store.connect() as connection:
        data = {name: [dict(zip([col[0] for col in cursor.description], row)) for row in cursor]
                for name in ('general_chat_turns', 'reservations', 'provider_attempts', 'jobs')
                for cursor in [connection.execute('SELECT * FROM ' + name)]}
    (target / 'runtime-state.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    exports = []
    for path in (store.root / 'exports').glob('*.mp4'):
        destination = target / path.name
        shutil.copyfile(path, destination)
        exports.append({'path': str(destination.relative_to(ROOT)), 'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (target / 'artifacts.json').write_text(json.dumps({'exports': exports,
         'workers': [t.name for t in self.threads], 'fake_provider_only': True}, indent=2) + '\n')

original_setup = worker_tests.WorkerConversationTest.setUp

def setup_with_release_receipt(self):
    original_setup(self)
    original_release = self.release.set
    def release_with_receipt():
        if not self.release.is_set():
            target = EVIDENCE / self._testMethodName
            target.mkdir(exist_ok=True)
            with self.store.connect() as c:
                turns = [json.loads(row[0]) for row in c.execute('SELECT body FROM general_chat_turns ORDER BY rowid')]
                jobs = [json.loads(row[0]) for row in c.execute('SELECT body FROM jobs')]
            (target / 'before-release.json').write_text(json.dumps({
                'release_event_is_set': self.release.is_set(), 'turns': turns, 'jobs': jobs,
                'worker_names': [t.name for t in self.threads]
            }, ensure_ascii=False, indent=2) + '\n')
        original_release()
    self.release.set = release_with_receipt

worker_tests.WorkerConversationTest.setUp = setup_with_release_receipt
worker_tests.WorkerConversationTest.tearDown = capture

class EvidenceResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        records.append({'scenario': test.id(), 'result': 'PASS'})
    def addFailure(self, test, error):
        super().addFailure(test, error)
        records.append({'scenario': test.id(), 'result': 'FAIL', 'error': self._exc_info_to_string(error, test)})
    def addError(self, test, error):
        super().addError(test, error)
        records.append({'scenario': test.id(), 'result': 'ERROR', 'error': self._exc_info_to_string(error, test)})
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        records.append({'scenario': test.id(), 'result': 'UNVERIFIED', 'reason': reason})

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromModule(worker_tests),
    unittest.defaultTestLoader.loadTestsFromName('tests.test_app'),
])
result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
(EVIDENCE / 'verification.json').write_text(json.dumps({
    'invocation': 'python3 .omo/evidence/conversation-workflow-20261028/worker-scheduling/verify.py',
    'result': 'PASS' if result.wasSuccessful() and not result.skipped else 'NOT_PASS',
    'tests_run': result.testsRun, 'skipped': len(result.skipped), 'cases': records,
    'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                      for name in ('app.py', 'tests/test_worker_scheduling.py')},
    'scope': 'Local HTTP, SQLite, production scheduler and FFmpeg; synthetic provider response only, no real Claude calls.'
}, ensure_ascii=False, indent=2) + '\n')
sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
