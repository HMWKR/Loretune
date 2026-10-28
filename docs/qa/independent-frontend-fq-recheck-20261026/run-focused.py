"""Explicit offline regression subset; never discover or start HTTP tests."""
import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'after' / 'snapshot'
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'tests'))
os.environ['NODE_OPTIONS'] = '--require=' + str(HERE / 'offline-node-guard.cjs')

def denied(*args, **kwargs):
    raise RuntimeError('AUDIT_OFFLINE_NETWORK_FORBIDDEN')

socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.socket.bind = denied
socket.create_connection = denied
subprocess_evidence = []
original_run = subprocess.run

def record_run(*args, **kwargs):
    result = original_run(*args, **kwargs)
    subprocess_evidence.append({
        'argv': args[0], 'returncode': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr,
    })
    return result

subprocess.run = record_run
MODULES = ['test_comment_draft', 'test_media_async_lifecycle',
           'test_studio_state', 'test_save_feedback', 'test_studio_media',
           'test_frontend_async']
suite = unittest.TestLoader().loadTestsFromNames(MODULES)
class EvidenceResult(unittest.TextTestResult):
    def startTest(self, test):
        self.current_id = test.id()
        super().startTest(test)
    def addSuccess(self, test):
        passed.append(test.id())
        super().addSuccess(test)

passed = []
result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
payload = {
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python': sys.version, 'modules': MODULES, 'testsRun': result.testsRun,
    'passed': passed, 'errors': [(t.id(), e) for t, e in result.errors],
    'failures': [(t.id(), e) for t, e in result.failures],
    'skipped': [(t.id(), e) for t, e in result.skipped],
    'subprocesses': subprocess_evidence,
    'network': 'Python socket connect/bind and Node net/http/fetch guarded; no HTTP/browser',
}
(HERE / 'focused-regression-results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
