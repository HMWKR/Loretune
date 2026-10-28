"""Isolated production-branch UI QA; every provider socket is synthetic."""
import base64
import hashlib
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
from threading import Event, Thread
import uuid
import wave
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import app
import anthropic_ontology as anthropic
import contracts
import ledger
from tests.test_chat_runtime import use
from tests.test_general_chat_activation import FAKE_KEY, ProviderSocket, reply, settings

folder = Path(tempfile.mkdtemp(prefix='loretune-schedule-ui-synthetic-'))
data = folder / 'data'
initial = app.Store(data)
key = [FAKE_KEY]
key_reads = []
wire = ProviderSocket()
release = Event()
held = Event()
original_open = wire.open
def controlled_open(request, timeout):
    if request.full_url == anthropic.ENDPOINT and not held.is_set():
        held.set()
        if not release.wait(90):
            raise TimeoutError('synthetic UI gate timeout; no remote request')
    return original_open(request, timeout)
wire.open = controlled_open
def responses():
    return [reply([use('read-music', 'search_project_context', {'query': '선택 음원 길이와 구간'})], 'tool_use'),
            reply([{'type': 'text', 'text': '합성 답변입니다. 첫 번째 안은 검정 배경, 두 번째 안은 파랑 배경입니다. 실제 Claude는 호출하지 않았습니다.'}])]
wire.replies = responses()
def supplier(name):
    assert name == 'Anthropic_KEY'
    key_reads.append(name)
    return key[0]

with patch.object(anthropic.urllib.request, 'build_opener', return_value=wire):
    http = app.server(data, 0, general_chat_configuration=settings(initial.workspace_id),
                      general_chat_credential_supplier=supplier)
    store = http.store
    def mutate(action, **values):
        return store.mutate(dict(action=action, data=values,
                                 revision=store.state()['revision'], request_id=uuid.uuid4().hex))
    name = '모델 예약 검증'
    mutate('project', name=name, era='default', story=0)
    mutate('model_settings', song=name, selections={'chat': 'anthropic-haiku-5-5'}, model_revision=0)
    audio = io.BytesIO()
    with wave.open(audio, 'wb') as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(8000)
        output.writeframes(b'\x00\x00' * 24000)
    mutate('audio', song=name, filename='자체 합성 음원.wav',
           content=base64.b64encode(audio.getvalue()).decode(), rights='직접 제작한 합성 검증 음원')
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        ledger.patch_budget(c, store.workspace_id, 'project:' + contracts.project_id(store.workspace_id, name),
                            dict(limit={'amount': '1', 'currency': 'USD'}, maxConcurrentJobs=4,
                                 allowAutomaticRetries=False), 0)
    Original = http.RequestHandlerClass
    class Handler(Original):
        def do_GET(self):
            if self.path == '/__fixture/release':
                release.set()
                return self.send(200, {'synthetic_hold_released': True})
            if self.path == '/__fixture/fail-next':
                wire.replies = [TimeoutError('synthetic uncertain response')]
                release.set()
                return self.send(200, {'synthetic_next_response_unknown': True})
            if self.path == '/__fixture/missing-key':
                key[0] = None
                return self.send(200, {'fixture_key_present': False})
            if self.path == '/__fixture/reset':
                key[0] = FAKE_KEY; wire.replies = responses()
                return self.send(200, {'fixture_key_present': True})
            if self.path == '/__fixture/stats':
                return self.send(200, dict(provider_network='synthetic stdlib socket only', actual_provider_calls=0,
                    key_reads=len(key_reads), holding=held.is_set() and not release.is_set(), requests=[dict(url=url, sha256=hashlib.sha256(body).hexdigest())
                                                       for url, body, timeout in wire.requests]))
            return super().do_GET()
    http.RequestHandlerClass = Handler
    stop = Event()
    def worker():
        while not stop.is_set():
            worked, failed = app.worker_cycle(store)
            if failed or not worked: stop.wait(.1)
    Thread(target=http.serve_forever, daemon=True).start()
    Thread(target=worker, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    print(json.dumps(dict(url=f'http://127.0.0.1:{http.server_port}/', root=str(folder), data=str(data),
                          provider='synthetic sockets only; actual provider calls0', key_reads=len(key_reads))), flush=True)
    try:
        stop.wait()
    finally:
        http.shutdown(); http.server_close()
