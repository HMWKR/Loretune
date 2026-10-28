"""Fresh empty local workspace for an actual audio-only creation walkthrough."""
from pathlib import Path
from threading import Event, Thread
import io
import json
import math
import os
import signal
import struct
import sys
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='loretune-music-recovery-'))
port = int(sys.argv[2]) if len(sys.argv) > 2 else 0
soundtrack = Path(__file__).parent / 'soundtrack.wav'
if not soundtrack.exists():
    with wave.open(str(soundtrack), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(48000)
        stream.writeframes(b''.join(struct.pack('<h', round(6500 * math.sin(2 * math.pi * 440 * i / 48000))) for i in range(480000)))

http = app.server(folder / 'data', port)
original = http.RequestHandlerClass
http.receipts = []


class Handler(original):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == '/__fixture/receipt':
            return self.send(200, dict(posts=http.receipts, fixture_seed_actions=0, providers_configured=False))
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/action':
            return super().do_POST()
        raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        value = json.loads(raw)
        self.current_receipt = dict(action=value.get('action'), request_id=value.get('request_id'))
        http.receipts.append(self.current_receipt)
        previous = self.rfile
        self.rfile = io.BytesIO(raw)
        try:
            return super().do_POST()
        finally:
            self.rfile = previous

    def send(self, status, value, *args, **kwargs):
        if self.path == '/api/action' and getattr(self, 'current_receipt', None) is not None:
            self.current_receipt['http_status'] = status
            if status >= 400:
                self.current_receipt['error'] = value.get('error')
        return super().send(status, value, *args, **kwargs)


http.RequestHandlerClass = Handler
stop = Event()
Thread(target=http.serve_forever, daemon=True).start()


def work():
    while not stop.is_set():
        ran, failed = app.worker_cycle(http.store)
        if failed or not ran:
            stop.wait(.1)


worker = Thread(target=work, daemon=True)
worker.start()
for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, lambda *_: stop.set())
print(json.dumps(dict(pid=os.getpid(), url=f'http://127.0.0.1:{http.server_port}', data=str(http.store.root), soundtrack=str(soundtrack), fixture_seed_actions=0, providers_configured=False), ensure_ascii=False), flush=True)
try:
    while not stop.wait(1):
        pass
finally:
    http.shutdown()
    http.server_close()
    worker.join(10)
