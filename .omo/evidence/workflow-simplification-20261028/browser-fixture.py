"""Owned deterministic music workflow; no provider configuration or real data."""
from pathlib import Path
import base64
import hashlib
import io
import json
import math
import os
import signal
import struct
import sys
import tempfile
from threading import Event, Thread
import uuid
import wave

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import app
import scene_project
import scene_renderer

case = sys.argv[1]
assert case in ('before', 'after')
folder = Path(tempfile.mkdtemp(prefix='loretune-feedback-' + case + '-'))
native = json.loads((ROOT / 'docs/qa/codex-workflow-review-20261027/paired-assets-20261028/regression/preflight.json').read_text())['native']['environment']
binary = Path(native['LORETUNE_3D_BLENDER'])
renderer = scene_renderer.RendererConfig(native['LORETUNE_3D_IMAGE'], binary, native['LORETUNE_3D_BLENDER_SHA256'], 180, Path(native['LORETUNE_3D_DOCKER_SOCKET']))
http = app.server(folder / 'data', 0, scene_configuration=dict(renderer=renderer, quota_bytes=scene_project.RESERVATION_BYTES * 6, tree_sha256=native['LORETUNE_3D_TREE_SHA256']))
store = http.store

def call(action, **data):
    return store.mutate(dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex))

name, shot = '음원 제작 안내 검증', '첫 장면'
call('project', name=name, era='default', story=0)
audio = io.BytesIO()
with wave.open(audio, 'wb') as stream:
    stream.setnchannels(1)
    stream.setsampwidth(2)
    stream.setframerate(48000)
    stream.writeframes(b''.join(struct.pack('<h', round(6500 * math.sin(2 * math.pi * 440 * i / 48000))) for i in range(144000)))
call('audio', song=name, filename='직접 만든 세 초 음원.wav', content=base64.b64encode(audio.getvalue()).decode(), rights='직접 제작한 합성 음원')
call('shot', song=name, shot=shot, description='음원에 맞춘 자체 제작 장면')
image_path = ROOT / '.omo/evidence/paired-3d-benchmark-inputs-20261028/case-1-cube.png'
image = image_path.read_bytes()
assert hashlib.sha256(image).hexdigest() == '472c4e8e77d713e5bf8f8f46fc50f99ec468b8c775803e06050be433bd9b9033'
call('take', song=name, shot=shot, shot_revision=store.state()['projects'][name]['shots'][shot]['revision'], filename='직접 만든 장면.png', content=base64.b64encode(image).decode(), reason='직접 제작한 검증 장면', rights='직접 제작한 합성 입력')
call('select', song=name, shot=shot, take=1, shot_revision=store.state()['projects'][name]['shots'][shot]['revision'])
call('review_take', song=name, shot=shot, take=1, decision='approved', reason='자체 표본의 장면 검토')
call('timeline', song=name, timeline=dict(clips=[dict(shot=shot, take=1, duration=3, trim=0)], audio=1, audio_offset=0, profile='landscape', subtitles=[dict(start=0, end=3, text='음원에 맞춰 장면을 만들어요')]))
call('approve_timeline', song=name)

run_allowed, stop = Event(), Event()
Original = http.RequestHandlerClass
http.receipts = []

class Handler(Original):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == '/__fixture/run':
            run_allowed.set()
            return self.send(200, dict(worker_released=True))
        if self.path == '/__fixture/receipt':
            return self.send(200, dict(case=case, posts=http.receipts, providers_configured=False))
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/action':
            return super().do_POST()
        raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        value = json.loads(raw)
        self.request_receipt = dict(action=value.get('action'), request_id=value.get('request_id'), body_sha256=hashlib.sha256(raw).hexdigest())
        http.receipts.append(self.request_receipt)
        original = self.rfile
        self.rfile = io.BytesIO(raw)
        try:
            return super().do_POST()
        finally:
            self.rfile = original

    def send(self, status, value, *args, **kwargs):
        if self.path == '/api/action' and getattr(self, 'request_receipt', None) is not None:
            self.request_receipt['http_status'] = status
            if status >= 400:
                self.request_receipt['error'] = value.get('error')
        return super().send(status, value, *args, **kwargs)

http.RequestHandlerClass = Handler
Thread(target=http.serve_forever, daemon=True).start()

def work():
    while not stop.is_set():
        if not run_allowed.wait(.1):
            continue
        ran, failed = app.worker_cycle(store)
        if failed or not ran:
            stop.wait(.1)

worker = Thread(target=work, daemon=True)
worker.start()
for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, lambda *_: stop.set())
print(json.dumps(dict(case=case, pid=os.getpid(), url=f'http://127.0.0.1:{http.server_port}', root=str(folder), data=str(store.root), song=name, image_sha256=hashlib.sha256(image).hexdigest(), audio_sha256=hashlib.sha256(audio.getvalue()).hexdigest(), source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ('index.html', 'studio.css', 'scene_assets.py')}), ensure_ascii=False), flush=True)
try:
    while not stop.wait(1):
        pass
finally:
    http.shutdown()
    http.server_close()
    worker.join(10)
