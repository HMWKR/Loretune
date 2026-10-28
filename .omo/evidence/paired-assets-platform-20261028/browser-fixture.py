"""Owned synthetic music project for real UI checks; not normal startup."""
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
import time
import uuid
import wave

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import app
import scene_project
import scene_renderer

prior = json.loads((ROOT / '.omo/evidence/general-model-schedule-20261028/regression/preflight.json').read_text())
native = prior['native']['environment']
binary = Path(native['LORETUNE_3D_BLENDER'])
assert hashlib.sha256((binary / 'blender').read_bytes()).hexdigest() == native['LORETUNE_3D_BLENDER_SHA256']
assert scene_project.tree_manifest(binary) == native['LORETUNE_3D_TREE_SHA256']
folder = Path(tempfile.mkdtemp(prefix='loretune-actual-asset-ui-'))
renderer = scene_renderer.RendererConfig(native['LORETUNE_3D_IMAGE'], binary, native['LORETUNE_3D_BLENDER_SHA256'], 180, Path(native['LORETUNE_3D_DOCKER_SOCKET']))
http = app.server(folder / 'data', 0, scene_configuration=dict(renderer=renderer, quota_bytes=scene_project.RESERVATION_BYTES * 12, tree_sha256=native['LORETUNE_3D_TREE_SHA256']))
store = http.store

def mutate(action, **data):
    return store.mutate(dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex))

name = '음원과 실제 생성 자산 검증'
mutate('project', name=name, era='default', story=0)
audio = io.BytesIO()
with wave.open(audio, 'wb') as stream:
    stream.setnchannels(1)
    stream.setsampwidth(2)
    stream.setframerate(48000)
    stream.writeframes(b''.join(struct.pack('<h', round(6500 * math.sin(2 * math.pi * 440 * i / 48000))) for i in range(288000)))
mutate('audio', song=name, filename='직접 만든 여섯 초 음원.wav', content=base64.b64encode(audio.getvalue()).decode(), rights='직접 제작한 합성 음원')
mutate('shot', song=name, shot='선택 장면', description='음원을 먼저 준비하고 실제 공개 모델 자산을 선택해 구도를 편집하는 검증')
(folder / 'invalid.glb').write_bytes(b'invalid-glb-negative-input')

Original = http.RequestHandlerClass
http.fixture_posts = []

class Handler(Original):
    def do_GET(self):
        if self.path == '/__fixture/receipt':
            return self.send(200, dict(posts=http.fixture_posts, live_ai_configured=False, provider_transport_injected=False, data=str(store.root)))
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/action':
            return super().do_POST()
        raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        value = json.loads(raw)
        http.fixture_posts.append(dict(action=value.get('action'), request_id=value.get('request_id'), body_sha256=hashlib.sha256(raw).hexdigest(), observed_at=time.time()))
        original = self.rfile
        self.rfile = io.BytesIO(raw)
        try:
            return super().do_POST()
        finally:
            self.rfile = original

http.RequestHandlerClass = Handler
stop = Event()
Thread(target=http.serve_forever, daemon=True).start()

def work():
    while not stop.is_set():
        ran, failed = app.worker_cycle(store)
        if failed or not ran:
            stop.wait(.1)

worker = Thread(target=work, daemon=True)
worker.start()
for sig in (signal.SIGTERM, signal.SIGINT):
    signal.signal(sig, lambda *_: stop.set())
print(json.dumps(dict(pid=os.getpid(), url=f'http://127.0.0.1:{http.server_port}', root=str(folder), data=str(store.root), song=name, invalid_asset=str(folder / 'invalid.glb'), source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ('scene_renderer.py', 'scene_project.py', 'scene-studio.js')}), ensure_ascii=False), flush=True)
try:
    while not stop.wait(1):
        pass
finally:
    http.shutdown()
    http.server_close()
    worker.join(10)
