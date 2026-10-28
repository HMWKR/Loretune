"""Bounded production scheduling with real local HTTP/SQLite and synthetic AI."""
import base64
import json
import shutil
import subprocess
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

import chat_general
import editing
import ledger
from app import start_workers
from tests import test_chat_general_http as general_http
from tests.test_chat_runtime import response


class WorkerSchedulingTest(unittest.TestCase):
    def test_fixed_domains_and_preset_stop_never_process(self):
        calls = []
        process = lambda: calls.append('unexpected')
        store = SimpleNamespace(process_next=process, process_generation=process,
                                chat_runtime=SimpleNamespace(process_next=process),
                                general_chat_runtime=SimpleNamespace(process_next=process))
        stopped = threading.Event(); stopped.set()
        stop, threads = start_workers(store, stopped)
        self.assertIs(stop, stopped)
        self.assertEqual(len(threads), 5)
        self.assertEqual(len({t.name for t in threads}), 5)
        self.assertEqual(sum('general-chat' in t.name for t in threads), 2)
        for thread in threads:
            thread.join(1)
            self.assertFalse(thread.is_alive())
        self.assertEqual(calls, [])
        store.chat_runtime = store.general_chat_runtime = None
        _, threads = start_workers(store, stopped)
        self.assertEqual(len(threads), 2)
        for thread in threads: thread.join(1)

    def test_failed_queue_recovers_without_private_error_or_stalling_others(self):
        stop = threading.Event(); recovered = threading.Event(); other = threading.Event()
        calls = []
        def render():
            calls.append(1)
            if len(calls) == 1: raise OSError('secret provider prompt and key')
            recovered.set(); return False
        def generation(): other.set(); return False
        store = SimpleNamespace(process_next=render, process_generation=generation,
                                chat_runtime=None, general_chat_runtime=None)
        with self.assertLogs('app', level='ERROR') as logs:
            _, threads = start_workers(store, stop)
            try:
                self.assertTrue(other.wait(2))
                self.assertTrue(recovered.wait(2))
            finally:
                stop.set()
                for thread in threads: thread.join(2)
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertIn('OSError', ' '.join(logs.output))
        self.assertNotIn('secret provider prompt and key', ' '.join(logs.output))


class WorkerConversationTest(unittest.TestCase):
    def setUp(self):
        self.f = general_http.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store
        self.release = threading.Event()
        self.stop = threading.Event()
        self.threads = ()
        self.addCleanup(self.shutdown_workers)
        self.default = self.f.state()['projects']['A']['active_conversation']['id']

    def shutdown_workers(self):
        self.stop.set(); self.release.set()
        for thread in self.threads:
            thread.join(5)
            self.assertFalse(thread.is_alive(), thread.name)

    def start(self):
        self.stop, self.threads = start_workers(self.store, self.stop)

    def post(self, action, **data):
        status, result = self.f.action(action, **data)
        self.assertEqual(status, 200, result)
        return result

    def conversation(self, title):
        return self.post('conversation_create', song='A', title=title)['conversation']['id']

    def enqueue(self, cid, prompt):
        status, result = self.f.session_action(cid, 'general_chat_preview', song='A', prompt=prompt, maximum_micro=10000)
        self.assertEqual(status, 200, result)
        preview = result['general_chat_preview']
        status, result = self.f.session_action(cid, 'general_chat_decide', song='A', preview_id=preview['id'],
                                             manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
        return status, result

    def turn(self, identifier):
        with self.store.connect() as c:
            return chat_general.get_row(c, 'general_chat_turns', identifier)

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate(): return
            time.sleep(.02)
        self.fail('condition did not become true within timeout')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'local media tools required')
    def test_held_conversation_does_not_block_other_dispatch_or_actual_render(self):
        image = Path(self.f.tmp.name) / 'worker-fixture.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64',
                        '-frames:v', '1', str(image)], check=True)
        self.post('shot', song='A', shot='s', description='synthetic local render')
        self.post('take', song='A', shot='s', shot_revision=0, filename=image.name,
                  content=base64.b64encode(image.read_bytes()).decode(), reason='worker test', rights='직접 제작')
        self.post('select', song='A', shot='s', take=1, shot_revision=1)
        self.post('review_take', song='A', shot='s', take=1, decision='approved', reason='fixture')
        project = self.f.state()['projects']['A']
        self.post('timeline', song='A', timeline=editing.current(project))
        self.post('approve_timeline', song='A')
        other = self.conversation('B')
        entered = threading.Event(); second = threading.Event(); calls = []; lock = threading.Lock()
        def complete(body):
            with lock:
                calls.append(body)
                number = len(calls)
            if number == 1:
                entered.set()
                if not self.release.wait(10): raise TimeoutError('held fixture not released')
            else: second.set()
            return response()
        self.store.general_chat_runtime.transport.complete = complete
        status, first = self.enqueue(self.default, 'A 음악 장면 제안')
        self.assertEqual(status, 200, first)
        self.start()
        self.assertTrue(entered.wait(3))
        status, second_turn = self.enqueue(other, 'B 음악 장면 제안')
        self.assertEqual(status, 200, second_turn)
        job = self.post('render_job', song='A')['job']
        self.assertTrue(second.wait(3), 'B must actually dispatch before A is released')
        self.wait_for(lambda: self.turn(second_turn['turn']['id'])['status'] == 'completed')
        output = self.store.root / 'exports' / (job + '.mp4')
        self.wait_for(lambda: any(j['id'] == job and j['status'] == 'completed' for j in self.f.state()['jobs']), 10)
        self.assertFalse(self.release.is_set())
        self.assertEqual(self.turn(first['turn']['id'])['status'], 'running')
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                                   'format=duration', '-of', 'json', str(output)]))
        self.assertAlmostEqual(float(probe['format']['duration']), 3, places=1)
        self.release.set()
        self.wait_for(lambda: self.turn(first['turn']['id'])['status'] == 'completed')
        self.assertEqual(len(calls), 2)
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM general_chat_turns').fetchone()[0], 2)
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 2)
            attempts = c.execute('SELECT operation,count(*) FROM provider_attempts GROUP BY operation').fetchall()
            self.assertCountEqual(attempts, [('chat-count', 2), ('chat-message', 2)])

    def test_two_slots_keep_third_queued_and_cancelled_work_never_dispatches(self):
        ids = [self.default, self.conversation('B'), self.conversation('C')]
        identifiers = []
        for n, cid in enumerate(ids):
            status, result = self.enqueue(cid, f'{n} 음악 장면')
            self.assertEqual(status, 200, result)
            identifiers.append(result['turn']['id'])
        entered = threading.Event(); calls = []; lock = threading.Lock()
        def complete(body):
            with lock:
                calls.append(body)
                if len(calls) == 2: entered.set()
            if not self.release.wait(10): raise TimeoutError('held fixture not released')
            return response()
        self.store.general_chat_runtime.transport.complete = complete
        self.start()
        self.assertTrue(entered.wait(3))
        self.assertEqual(len(self.threads), 4)
        self.assertEqual(self.turn(identifiers[2])['status'], 'queued')
        status, result = self.f.session_action(ids[2], 'general_chat_cancel', song='A', turn=identifiers[2])
        self.assertEqual(status, 200, result)
        self.assertEqual(self.turn(identifiers[2])['status'], 'cancelled')
        self.release.set()
        self.wait_for(lambda: all(self.turn(i)['status'] == 'completed' for i in identifiers[:2]))
        self.stop.set()
        for thread in self.threads: thread.join(3)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.turn(identifiers[2])['status'], 'cancelled')
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 3)
            self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',
                                      (self.turn(identifiers[2])['reservation'],)).fetchone()[0], 'cancelled')

    def test_global_reservation_cap_still_rejects_another_conversation(self):
        other = self.conversation('B')
        with self.store.connect() as c:
            ledger.patch_budget(c, self.store.workspace_id, 'rehearsal:project:' + self.f.pid,
                                dict(limit={'amount':'1','currency':'USD'}, maxConcurrentJobs=1, allowAutomaticRetries=False), 1)
        status, first = self.enqueue(self.default, 'A 음악 장면')
        self.assertEqual(status, 200, first)
        entered = threading.Event()
        def complete(body):
            entered.set()
            if not self.release.wait(10): raise TimeoutError('held fixture not released')
            return response()
        self.store.general_chat_runtime.transport.complete = complete
        self.start(); self.assertTrue(entered.wait(3))
        status, second = self.enqueue(other, 'B 음악 장면')
        self.assertEqual(status, 400, second)
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT count(*) FROM general_chat_turns').fetchone()[0], 1)
        self.release.set()
        self.wait_for(lambda: self.turn(first['turn']['id'])['status'] == 'completed')


if __name__ == '__main__': unittest.main()
