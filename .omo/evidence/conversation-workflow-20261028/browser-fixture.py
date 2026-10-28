"""Two real browser tabs against production handlers; provider sockets synthetic."""
from pathlib import Path
import base64
import hashlib
import io
import json
import os
import signal
import sys
import tempfile
import time
from threading import Event, Lock, Thread, current_thread
import uuid
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app
import anthropic_ontology as anthropic
import contracts
import ledger
from tests.test_general_chat_activation import FAKE_KEY, SyntheticResponse, reply, settings

EVIDENCE = Path(__file__).parent
folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='loretune-conversation-workflow-'))
port = int(sys.argv[2]) if len(sys.argv) > 2 else 0
mode = sys.argv[3] if len(sys.argv) > 3 else 'single'
if mode not in {'single', 'bulkhead'}:
    raise ValueError('Unknown fixture worker mode')
initial = app.Store(folder / 'data')
name = '두 대화 음악영상 검증'
release = Event()
held = Event()
lock = Lock()
wire_requests = []
posts = []
control = {'hold_next_message': True, 'fail_next_message': False}
key_reads = []
state_release = Event()
state_held = Event()
state_gate = {'armed': False, 'conversation': None, 'path': None, 'sent': False}


class Socket:
    def open(self, request, timeout):
        if request.full_url not in {anthropic.ENDPOINT, anthropic.BoundedCountTransport.endpoint}:
            raise AssertionError('Unexpected URL; synthetic fixture never forwards requests')
        if request.get_header('X-api-key') != FAKE_KEY:
            raise AssertionError('Synthetic key required')
        count = request.full_url.endswith('count_tokens')
        body = json.loads(request.data)
        messages = json.dumps(body.get('messages', []), ensure_ascii=False)
        with lock:
            index = len(wire_requests) + 1
            entry = {'sequence': index, 'kind': 'count' if count else 'messages',
                     'body_sha256': hashlib.sha256(request.data).hexdigest(),
                     'body': body, 'started': time.monotonic(), 'thread': current_thread().name}
            wire_requests.append(entry)
            hold = not count and control['hold_next_message']
            fail = not count and control['fail_next_message']
            if hold:
                control['hold_next_message'] = False
            if fail:
                control['fail_next_message'] = False
        if hold:
            held.set()
            if not release.wait(180):
                raise TimeoutError('Synthetic gate timeout; no remote request')
        if fail:
            entry['finished'] = time.monotonic()
            entry['outcome'] = 'synthetic-timeout'
            raise TimeoutError('Synthetic uncertain response; no remote request')
        marker = 'CS-A' if '[CS-A' in messages else 'CS-B' if '[CS-B' in messages else 'CS-OTHER'
        result = {'input_tokens': 100} if count else reply([{'type': 'text', 'text': marker + ' 합성 응답. 실제 Claude 호출 없음.'}])
        entry['finished'] = time.monotonic()
        entry['outcome'] = 'synthetic-response'
        return SyntheticResponse(result, request.full_url, index)


def supplier(key):
    assert key == 'Anthropic_KEY'
    key_reads.append(key)
    return FAKE_KEY


with patch.object(anthropic.urllib.request, 'build_opener', return_value=Socket()):
    http = app.server(folder / 'data', port, general_chat_configuration=settings(initial.workspace_id),
                      general_chat_credential_supplier=supplier)
    store = http.store
    seeds = []

    def seed(action, **data):
        result = store.mutate({'action': action, 'data': data, 'revision': store.state()['revision'],
                               'request_id': uuid.uuid4().hex})
        seeds.append(action)
        return result

    if name not in store.state()['projects']:
        seed('project', name=name, era='default', story=0)
        seed('model_settings', song=name, selections={'chat': 'anthropic-haiku-5-5'}, model_revision=0)
        seed('audio', song=name, filename='직접 제작한 합성 음원.wav',
             content=base64.b64encode((ROOT / '.omo/evidence/music-recovery-20261028/soundtrack.wav').read_bytes()).decode(),
             rights='직접 제작한 440Hz 검증 음원')
        seed('music_structure', song=name, audio=1, start=3, end=6, sections=[])
        seed('shot', song=name, shot='공유 컷', description='두 대화가 공유하는 직접 제작 타이포 영상')
        seed('take', song=name, shot='공유 컷', shot_revision=0, filename='직접 제작한 타이포.mp4',
             content=base64.b64encode((ROOT / '.omo/evidence/music-recovery-20261028/music-only-typography.mp4').read_bytes()).decode(),
             reason='MR1 실제 내부 렌더의 독립 합성 표본', rights='직접 제작한 검증용 모션')
        shot = store.state()['projects'][name]['shots']['공유 컷']
        seed('select', song=name, shot='공유 컷', take=1, shot_revision=shot['revision'])
        seed('review_take', song=name, shot='공유 컷', take=1, decision='approved', reason='합성 표본 내용 확인')
        seed('timeline', song=name, timeline={'clips': [{'shot': '공유 컷', 'take': 1, 'duration': 3, 'trim': 0}],
             'audio': 1, 'audio_offset': 3, 'profile': 'landscape', 'subtitles': []})
        seed('approve_timeline', song=name)
        with store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            ledger.patch_budget(db, store.workspace_id, 'project:' + contracts.project_id(store.workspace_id, name),
                                {'limit': {'amount': '1', 'currency': 'USD'}, 'maxConcurrentJobs': 4,
                                 'allowAutomaticRetries': False}, 0)

    Original = http.RequestHandlerClass

    class Handler(Original):
        def log_message(self, *_):
            pass

        def do_GET(self):
            if self.path.startswith('/__fixture/arm-state?'):
                if state_held.is_set() and not state_release.is_set():
                    return self.send(409, {'error': 'Existing state response gate is still held'})
                cid = parse_qs(urlsplit(self.path).query).get('conversation', [''])[0]
                if not cid:
                    return self.send(400, {'error': 'Conversation required'})
                state_release.clear(); state_held.clear()
                state_gate.update(armed=True, conversation=cid, path=None, sent=False)
                return self.send(200, {'next_state_response_for': cid})
            if self.path == '/__fixture/release-state':
                state_release.set()
                return self.send(200, {'state_response_released': True})
            if self.path == '/__fixture/release':
                release.set()
                return self.send(200, {'released': True})
            if self.path == '/__fixture/fail-next':
                control['fail_next_message'] = True
                return self.send(200, {'next_message': 'synthetic-timeout'})
            if self.path == '/__fixture/arm-hold':
                if held.is_set() and not release.is_set():
                    return self.send(409, {'error': 'An existing gate is still held'})
                release.clear(); held.clear(); control['hold_next_message'] = True
                return self.send(200, {'next_message': 'held'})
            if self.path == '/__fixture/stats':
                return self.send(200, {'provider_socket': 'synthetic only', 'actual_provider_calls': 0,
                                      'holding': held.is_set() and not release.is_set(),
                                      'worker_count': len(worker_threads), 'worker_mode': mode, 'seed_actions': seeds,
                                      'requests': wire_requests, 'posts': posts, 'key_reads': len(key_reads),
                                      'state_gate': dict(state_gate, holding=state_held.is_set() and not state_release.is_set())})
            return super().do_GET()

        def do_POST(self):
            if self.path != '/api/action':
                return super().do_POST()
            raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            value = json.loads(raw)
            self.current_receipt = {'action': value.get('action'), 'request_id': value.get('request_id'),
                                    'conversation_id': value.get('conversation_id'), 'started': time.monotonic()}
            posts.append(self.current_receipt)
            previous = self.rfile; self.rfile = io.BytesIO(raw)
            try:
                return super().do_POST()
            finally:
                self.rfile = previous

        def send(self, status, value, *args, **kwargs):
            should_hold = False
            if status == 200 and self.path.startswith('/api/state?'):
                cid = parse_qs(urlsplit(self.path).query).get('conversation', [''])[0]
                with lock:
                    if state_gate['armed'] and cid == state_gate['conversation']:
                        state_gate.update(armed=False, path=self.path)
                        should_hold = True
                if should_hold:
                    state_held.set()
                    if not state_release.wait(90):
                        state_gate['timeout'] = True
            if self.path == '/api/action' and getattr(self, 'current_receipt', None) is not None:
                self.current_receipt.update(http_status=status, finished=time.monotonic())
                if status >= 400:
                    self.current_receipt['error'] = value.get('error')
            result = super().send(status, value, *args, **kwargs)
            if should_hold:
                state_gate['sent'] = True
            return result

    http.RequestHandlerClass = Handler
    stop = Event()

    def worker():
        while not stop.is_set():
            worked, failed = app.worker_cycle(store)
            if failed or not worked:
                stop.wait(.1)

    if mode == 'single':
        worker_threads = (Thread(target=worker, name='actual-single-worker', daemon=True),)
        worker_threads[0].start()
    else:
        stop, worker_threads = app.start_workers(store, stop)
    Thread(target=http.serve_forever, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    print(json.dumps({'pid': os.getpid(), 'url': f'http://127.0.0.1:{http.server_port}/',
                      'root': str(folder), 'data': str(store.root), 'worker_count': len(worker_threads), 'worker_mode': mode,
                      'seed_actions': seeds, 'actual_provider_calls': 0}, ensure_ascii=False), flush=True)
    try:
        stop.wait()
    finally:
        stop.set(); release.set(); state_release.set()
        http.shutdown(); http.server_close()
        for thread in worker_threads:
            thread.join(3)
