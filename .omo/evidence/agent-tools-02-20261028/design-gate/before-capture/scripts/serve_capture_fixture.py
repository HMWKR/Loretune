"""Owned isolated fixture server for before/after visual capture.

Modeled on chat-review-navigation-20261028/worker/serve_fixture.py.
No keys, no .env, no external model/provider calls. Run under sandbox-exec with
network-loopback-only.sb. Usage:
  sandbox-exec -f network-loopback-only.sb python3 -u serve_capture_fixture.py <ROOT> <OUT>
ROOT = application source tree to serve (before: before-capture/root, after: project root).
OUT  = fresh output folder (must not contain workspace/data yet).
"""
from pathlib import Path
import base64
import errno
import hashlib
import io
import json
import os
import signal
import socket
import sys
import threading
import time
import uuid
import wave

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app
import contracts
import ledger
import production_context
from fal_dispatch import FalDispatch
from fal_model_adapter import FalModelAdapter
from fal_models import Contract
from tests.test_chat_runtime import response, use

def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n')

with socket.socket() as probe:
    probe.settimeout(.5)
    denied = probe.connect_ex(('1.1.1.1', 443))
if denied not in {errno.EPERM, errno.EACCES}:
    raise RuntimeError('OS external-network denial not verified: '+str(denied))

DATA = OUT/'workspace/data'
if DATA.exists():
    raise RuntimeError('Fresh owned workspace required; preserve existing attempt data')
SONG = '디자인 비교 캡처 · 합성 검증'
SCENES = '푸른 음악 무대\n고요한 간주 무대\n후렴 군무 무대\n엔딩 실루엣'
CHAT_PROMPT = '장면 1 이미지 제작안을 준비해 주세요. 생성은 하지 말고 견적만 보여 주세요.'
http = app.server(DATA, 0, general_chat_fixture=[])
store = http.store
setup = []

def seed(action, **data):
    if action != 'project': data.setdefault('song', SONG)
    request = dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex)
    result = store.mutate(request)
    setup.append(dict(action=action, request_id=request['request_id'], data_fields=sorted(data)))
    return result

seed('project', name=SONG, era='default', story=0)
seed('model_settings', selections={'chat':'anthropic-haiku-5-5','image':'fal-flux-schnell'}, model_revision=0)
audio = io.BytesIO()
with wave.open(audio, 'wb') as stream:
    stream.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
    stream.writeframes(b'\0\0' * 80000)
seed('audio', filename='owned-fixture.wav', content=base64.b64encode(audio.getvalue()).decode(), rights='self-authored fixture silence')
seed('music_structure', audio=1, start=0, end=10, sections=[])
plan = seed('guided_plan', goal='음원에서 시작', scenes=SCENES, kind='visualizer')['plan']
seed('apply_guided_plan', plan=plan)
project = store.state()['projects'][SONG]
prompt = '음원의 리듬을 담은 푸른 음악 무대'
model = Contract('fal-flux-schnell')
payload = model.payload(prompt, {'ratio':'16:9'})
quote = dict(provider='fal.ai', model=model.MODEL, money={'amount':'0.01','currency':'USD'},
             input_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
             kind='fixture', price_revision='synthetic-not-real', source=model.spec['source'], expires=time.time()+86400)
submissions = []
def forbid_submission(*args):
    submissions.append(dict(at=time.time(), attempted=True))
    raise AssertionError('No image provider execution authorized')
adapter = FalModelAdapter('fal-flux-schnell', quote=quote, transport=forbid_submission)
store.media_dispatch = FalDispatch(store, [adapter])
args = dict(shot_id=production_context.shot_id(project, '장면 1'), model_id='fal-flux-schnell',
            prompt=prompt, ratio='16:9', shot_revision=project['shots']['장면 1']['revision'])
transport = store.general_chat_runtime.transport
transport.responses = [response([use('capabilities', 'get_model_capabilities', {'role':'image'})], 'tool_use'),
                       response([use('prepare-image', 'prepare_image_action', args)], 'tool_use'),
                       response()]
transport.responses[-1]['content'] = [dict(type='text', text='합성 시험 응답입니다. 이미지 제작안만 저장했고 생성은 실행하지 않았습니다. 견적과 입력을 검토하세요.')]
pid = contracts.project_id(store.workspace_id, SONG)
with store.connect() as c:
    ledger.patch_budget(c, store.workspace_id, 'rehearsal:project:'+pid,
                        dict(limit={'amount':'1','currency':'USD'}, maxConcurrentJobs=1, allowAutomaticRetries=False), 0)

stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *unused: stop.set())
signal.signal(signal.SIGINT, lambda *unused: stop.set())
_, workers = app.start_workers(store, stop)

# Drive the synthetic general chat through the same mutations the UI sends
# (general_chat_preview -> general_chat_decide), approving continuations, so the
# media action card exists before any browser capture. No UI mutation needed.
chat_log = []
def chat_state():
    p = store.state()['projects'][SONG]
    return p.get('general_chat_previews') or [], p.get('general_chat_turns') or [], p
deadline = time.time() + 60
previews, turns, p = chat_state()
seed('general_chat_preview', prompt=CHAT_PROMPT, maximum_micro=100000)
while time.time() < deadline:
    previews, turns, p = chat_state()
    pending = [v for v in previews if v.get('state') == 'pending']
    if pending:
        v = pending[0]
        seed('general_chat_decide', preview_id=v['id'], manifest_sha256=v['manifest_sha256'], decision='approve', rights_confirmed=True)
        chat_log.append(dict(approved=v['id'], turn=v.get('turn_id')))
        continue
    statuses = [t.get('status') for t in turns]
    if turns and not any(s in {'queued','running','cancel_requested'} for s in statuses):
        break
    time.sleep(.3)
previews, turns, p = chat_state()
media_actions = p.get('media_actions') or []
save('seed-result.json', dict(chat_log=chat_log, turn_statuses=[t.get('status') for t in turns],
     previews=[dict(id=v.get('id'), state=v.get('state')) for v in previews],
     media_actions=[dict(id=a.get('id'), shot=a.get('shot'), state=a.get('state'), kind=a.get('kind'),
                         quote=a.get('quote') or a.get('estimate')) for a in media_actions],
     shots=sorted((p.get('shots') or {}).keys()), timeline_clip_count=len(((p.get('timeline') or {}).get('clips')) or []),
     provider_submissions=submissions, counted=len(transport.counted)))

sources = {}
for path in sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('*.js')) + sorted(ROOT.glob('*.css')) + sorted(ROOT.glob('*.py')):
    sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
thread = threading.Thread(target=http.serve_forever, daemon=True)
thread.start()
save('fixture-start.json', dict(pid=os.getpid(), port=http.server_port, root=str(ROOT), data=str(DATA), song=SONG,
     scenes=SCENES.split('\n'), chat_prompt=CHAT_PROMPT, workspace_id=store.workspace_id, source_hashes=sources, setup_actions=setup,
     setup_mode='Direct Store fixture preparation before UI, not user workflow proof',
     input='10s self-authored silence; no photo/3D required', media_quote='fixture, not observed market pricing or charge',
     provider_models_executed=0, network_external_connect_errno=denied,
     synthetic_transport='in-memory deterministic response envelopes; not actual Claude'))
save('ready.json', dict(port=http.server_port, song=SONG))
try:
    while not stop.wait(.2): pass
finally:
    http.shutdown(); http.server_close(); thread.join(10)
    for worker in workers: worker.join(10)
    save('fixture-stop.json', dict(provider_submissions=submissions, counted=len(transport.counted),
         synthetic_messages=len(transport.messages),
         source_hashes_unchanged=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in sources.items()),
         worker_threads_still_alive=[worker.name for worker in workers if worker.is_alive()],
         no_actual_provider_credentials_or_billing=True))
