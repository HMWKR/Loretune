"""Empty, isolated production server for the first recorded demonstration."""
from pathlib import Path
from threading import Lock, Thread
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import signal
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app

folder = Path(sys.argv[1]).resolve()
evidence = Path(sys.argv[2]).resolve()
port = int(sys.argv[3]) if len(sys.argv) > 3 else 0
evidence.mkdir(parents=True, exist_ok=False)
lock = Lock()
external_attempts = []


def deny_external(event, args):
    if event == 'socket.connect':
        address = args[1]
        if isinstance(address, tuple) and address[0] not in {'127.0.0.1', '::1'}:
            with lock:
                external_attempts.append({'event': event, 'denied': True})
            raise PermissionError('First demonstration forbids external network calls')


sys.addaudithook(deny_external)
http = app.server(folder / 'data', port)
assert http.store.chat_runtime is None and http.store.general_chat_runtime is None
Original = http.RequestHandlerClass


def append(value):
    with lock:
        with (evidence / 'http-actions.jsonl').open('a') as f:
            f.write(json.dumps(value, ensure_ascii=False) + '\n')


class Handler(Original):
    def log_message(self, *_):
        pass

    def do_POST(self):
        if self.path != '/api/action':
            return super().do_POST()
        raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        value = json.loads(raw)
        body = value.get('data', {})
        self.action_receipt = {'at': datetime.now(timezone.utc).isoformat(),
            'action': value.get('action'), 'request_id': value.get('request_id'),
            'conversation_id': value.get('conversation_id'), 'revision': value.get('revision'),
            'input_sha256': hashlib.sha256(raw).hexdigest(), 'data_fields': list(body),
            'song': body.get('song'), 'shot': body.get('shot')}
        previous = self.rfile
        self.rfile = io.BytesIO(raw)
        try:
            return super().do_POST()
        finally:
            self.rfile = previous

    def send(self, status, value, *args, **kwargs):
        if self.path == '/api/action' and getattr(self, 'action_receipt', None) is not None:
            result = dict(self.action_receipt, http_status=status)
            if isinstance(value, dict):
                result['output_fields'] = list(value)
                result['stored_revision'] = value.get('revision')
                result['error'] = value.get('error')
                if isinstance(value.get('job'), dict):
                    result['job_id'] = value['job'].get('id')
            append(result)
        return super().send(status, value, *args, **kwargs)


http.RequestHandlerClass = Handler
stop, workers = app.start_workers(http.store)
signal.signal(signal.SIGTERM, lambda *_: stop.set())
signal.signal(signal.SIGINT, lambda *_: stop.set())
Thread(target=http.serve_forever, daemon=True).start()
receipt = {'pid': os.getpid(), 'url': f'http://127.0.0.1:{http.server_port}/',
           'data': str(http.store.root), 'workspace_id': http.store.workspace_id,
           'projects_at_start': len(http.store.state()['projects']), 'seed_actions': [],
           'workers': len(workers), 'real_provider_configured': False,
           'python_external_network': 'denied by runtime audit hook',
           'credentials_or_env_file_loaded': False}
(evidence / 'start.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False), flush=True)
try:
    stop.wait()
finally:
    http.shutdown()
    http.server_close()
    stop.set()
    for worker in workers:
        worker.join(3)
    (evidence / 'stop.json').write_text(json.dumps({'external_attempts': external_attempts,
        'worker_threads_still_alive': [w.name for w in workers if w.is_alive()]}, indent=2) + '\n')
