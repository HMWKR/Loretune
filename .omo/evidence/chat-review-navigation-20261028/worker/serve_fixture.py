"""Owned isolated fixture server; no keys or external model/provider calls."""
from pathlib import Path
import base64
import errno
import hashlib
import io
import json
import signal
import socket
import sys
import threading
import time
import uuid
import wave

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
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
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

with socket.socket() as probe:
    probe.settimeout(.5)
    denied = probe.connect_ex(('1.1.1.1', 443))
if denied not in {errno.EPERM, errno.EACCES}:
    raise RuntimeError('OS external-network denial not verified: '+str(denied))

DATA = OUT/'workspace/data'
if DATA.exists():
    raise RuntimeError('Fresh owned workspace required; preserve existing attempt data')
SONG = '음원에서 제작안 검토 이동 · 합성 검증'
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
    stream.writeframes(b'\0\0' * 40000)
seed('audio', filename='owned-fixture.wav', content=base64.b64encode(audio.getvalue()).decode(), rights='self-authored fixture silence')
seed('music_structure', audio=1, start=0, end=5, sections=[])
plan = seed('guided_plan', goal='음원에서 시작', scenes='푸른 음악 무대\n고요한 간주 무대', kind='visualizer')['plan']
seed('apply_guided_plan', plan=plan)
project = store.state()['projects'][SONG]
prompt = '음원의 리듬을 담은 푸른 음악 무대'
model = Contract('fal-flux-schnell')
payload = model.payload(prompt, {'ratio':'16:9'})
quote = dict(provider='fal.ai', model=model.MODEL, money={'amount':'0.01','currency':'USD'},
             input_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
             kind='fixture', price_revision='synthetic-not-real', source=model.spec['source'], expires=time.time()+1800)
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
sources = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
           for p in ('chat_general.py','general-chat-ui.js','chat-sidebar.js','production_tools.py','fal_dispatch.py','media_creator.py','index.html')}
save('fixture-start.json', dict(pid=__import__('os').getpid(), port=http.server_port, data=str(DATA), song=SONG,
     workspace_id=store.workspace_id, source_hashes=sources, setup_actions=setup,
     setup_mode='Direct Store fixture preparation before UI, not user workflow proof',
     input='5s self-authored silence; no photo/3D required', media_quote='fixture, not observed market pricing or charge',
     provider_models_executed=0, network_external_connect_errno=denied,
     synthetic_transport='in-memory deterministic response envelopes; not actual Claude'))
trace = []
original = store.mutate
def record(request):
    try:
        result = original(request)
    except Exception as error:
        trace.append(dict(action=request.get('action'), request_id=request.get('request_id'), result=type(error).__name__))
        raise
    else:
        trace.append(dict(action=request['action'], request_id=request['request_id'], revision=request['revision'],
                          call_name=request.get('data',{}).get('call',{}).get('name'), committed=True))
        return result
store.mutate = record
stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *unused: stop.set())
signal.signal(signal.SIGINT, lambda *unused: stop.set())
thread = threading.Thread(target=http.serve_forever, daemon=True)
thread.start()
_, workers = app.start_workers(store, stop)
save('ready.json', dict(port=http.server_port, song=SONG))
try:
    while not stop.wait(.2): pass
finally:
    http.shutdown(); http.server_close(); thread.join(10)
    for worker in workers: worker.join(10)
    current = store.state()
    with store.connect() as c:
        table_counts = {table:c.execute('SELECT count(*) FROM '+table).fetchone()[0]
                        for table in ('production_actions','execution_grants','generation_jobs','provider_action_jobs')}
        media_reservations = c.execute("SELECT count(*) FROM reservations r JOIN budgets b ON b.id=r.budget WHERE b.scope LIKE 'project:%'").fetchone()[0]
    save('fixture-stop.json', dict(trace=trace, provider_submissions=submissions, counted=len(transport.counted),
         synthetic_messages=len(transport.messages), table_counts=table_counts, media_reservations=media_reservations,
         source_hashes_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items()),
         worker_threads_still_alive=[worker.name for worker in workers if worker.is_alive()],
         project=current['projects'][SONG], state_jobs=current['jobs'], generation_jobs=current['generation_jobs'],
         no_actual_provider_credentials_or_billing=True))
