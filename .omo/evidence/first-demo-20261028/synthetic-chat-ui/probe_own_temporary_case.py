"""Programmatic localhost probe on entirely new owned fixture data, not a UI demo."""
from pathlib import Path
from copy import deepcopy
import base64
import hashlib
import json
import math
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid
import wave

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app
import editing
import production_context
from tests.test_motion import scene

OUT = Path(__file__).resolve().parent
FOLDER = Path(tempfile.mkdtemp(prefix='loretune-synthetic-ui-probe-'))
DATA = FOLDER / 'data'
SONG = 'new isolated synthetic UI harness probe'
store = app.Store(DATA)
setup = []


def seed(action, **data):
    if action != 'project':
        data.setdefault('song', SONG)
    request = dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex)
    setup.append(dict(action=action, request_id=request['request_id'], data_fields=sorted(data)))
    return store.mutate(request)


seed('project', name=SONG, era='default', story=0)
seed('model_settings', selections={'chat': 'anthropic-haiku-5-5'}, model_revision=0)
seed('shot', shot='photo', description='entirely new owned image fixture')
seed('take', shot='photo', shot_revision=0, filename='owned.png',
     content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
     reason='new own fixture', rights='directly authored synthetic fixture')
seed('select', shot='photo', take=1, shot_revision=1)
seed('review_take', shot='photo', take=1, decision='approved', reason='new fixture reviewed')
audio = FOLDER / 'owned-audio.wav'
with wave.open(str(audio), 'wb') as stream:
    stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(24000)
    stream.writeframes(b''.join(struct.pack('<h', int(1200 * math.sin(2 * math.pi * 220 * n / 24000))) for n in range(96000)))
seed('audio', filename='owned-audio.wav', content=base64.b64encode(audio.read_bytes()).decode(), rights='new generated fixture tone')
for revision in range(2):
    value = scene(); value['layers'] = value['layers'][:1]
    value['layers'][0].update(text='새 임시 모션 ' + str(revision + 1), color='#222222')
    project = store.state()['projects'][SONG]
    proposal = seed('motion_propose', shot_id=production_context.shot_id(project, 'photo'),
                    base_motion_revision=revision, scene=value)['motion']['proposal_id']
    seed('motion_review', proposal_id=proposal, decision='approved')
timeline = editing.current(store.state()['projects'][SONG])
timeline.update(profile='preview', subtitles=[dict(start=0, end=2.5, text='변경 전 마지막 자막')])
timeline['clips'][0].update(duration=3, motion_overlay=dict(shot='photo', motion_revision=2,
                                                         start=.5, end=2.5, offset_x=0, offset_y=0))
for _ in range(3):
    seed('timeline', timeline=deepcopy(timeline))
seed('approve_timeline')
job = seed('render_job')['job']
assert store.process_next()
before_job = next(x for x in store.state()['jobs'] if x['id'] == job)
assert before_job['status'] == 'completed', before_job
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
run_evidence = FOLDER / 'run-evidence'
process = subprocess.Popen([sys.executable, str(OUT / 'serve_synthetic_chat.py'), 'serve',
    '--data', str(DATA), '--evidence', str(run_evidence), '--song', SONG, '--port', str(port),
    '--expected-workspace-id', store.workspace_id,
    '--authorize-existing-data-after-main-stop', '--seed-rehearsal-budget'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
origin = f'http://127.0.0.1:{port}'
trace = []


def state():
    with urlopen(origin + '/api/state', timeout=5) as response:
        return json.load(response)


def post(action, expected=200, **data):
    current = state(); data.setdefault('song', SONG)
    request = dict(action=action, data=data, revision=current['revision'], request_id=uuid.uuid4().hex)
    wire = Request(origin + '/api/action', data=json.dumps(request).encode(),
                   headers={'Content-Type': 'application/json', 'X-Loretune-Token': current['token']})
    try:
        with urlopen(wire, timeout=15) as response:
            code, value = response.status, json.load(response)
    except HTTPError as response:
        code, value = response.code, json.load(response)
    trace.append(dict(action=action, request_id=request['request_id'], http_status=code))
    assert code == expected, (action, code, sorted(value))
    return value


def wait(predicate, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            value = state()
        except URLError as error:
            if not isinstance(error.reason, ConnectionRefusedError):
                raise
            time.sleep(.1)
            continue
        if predicate(value):
            return value
        time.sleep(.1)
    raise AssertionError('Timed out waiting for explicit stored-state predicate')


try:
    wait(lambda value: bool(value['projects']), 10)
    post('conversation_agent_settings', selection='anthropic-haiku-5-5', settings_revision=0, mode='review', effort='high')
    post('conversation_agent_settings', selection='anthropic-haiku-5-5', settings_revision=1, mode='full_access', effort='high')
    preview = post('general_chat_preview', prompt='현재 작업을 확인하고 사진 위 타이포 위치와 마지막 자막을 바꿔줘',
                   maximum_micro=10000, total_maximum_micro=40000)['general_chat_preview']
    before = state()['projects'][SONG]
    for index in range(4):
        assert preview['message_body']['model'] == 'claude-haiku-5-5'
        assert preview['message_body']['output_config']['effort'] == 'high'
        post('general_chat_decide', preview_id=preview['id'], manifest_sha256=preview['manifest_sha256'],
             decision='approve', rights_confirmed=True)
        expected_status = 'completed' if index == 3 else 'awaiting_continuation_approval'
        current = wait(lambda value: value['projects'][SONG]['general_chat_turns'][-1]['status'] == expected_status)
        project = current['projects'][SONG]
        if index < 2:
            assert project['timeline_head'] == 3
        if index == 2:
            assert project['timeline_head'] == 4
            assert editing.current(project)['agent_draft']['actor'] == 'agent-draft'
            assert 'approval' not in editing.current(project)
        if index < 3:
            next_preview = project['general_chat_previews'][-1]
            time.sleep(.4)
            assert state()['projects'][SONG]['general_chat_turns'][-1]['status'] == expected_status
            preview = next_preview
    after_edit = state()['projects'][SONG]
    assert after_edit['timeline_versions'][:3] == before['timeline_versions']
    assert editing.current(after_edit)['subtitles'][-1]['text'] == '음악의 여운을 이어서'
    assert editing.current(after_edit)['clips'][0]['motion_overlay']['offset_x'] == 240
    assert editing.current(after_edit)['clips'][0]['motion_overlay']['offset_y'] == 120
    assert after_edit['general_chat_turns'][-1]['billing_confirmed'] is False
    assert after_edit['general_chat_turns'][-1]['answer'].startswith('합성 시험 응답입니다.')
    post('render_job', expected=400)
    post('approve_timeline')
    final_job = post('render_job')['job']
    current = wait(lambda value: next(x for x in value['jobs'] if x['id'] == final_job)['status'] in {'completed', 'failed'})
    completed = next(x for x in current['jobs'] if x['id'] == final_job)
    assert completed['status'] == 'completed'
    with urlopen(origin + completed['download'], timeout=10) as response:
        movie = response.read()
    assert hashlib.sha256(movie).hexdigest() == completed['sha256']
    (OUT / 'own-temp-probe-output.mp4').write_bytes(movie)
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(OUT / 'own-temp-probe-output.mp4'), '-f', 'null', '-'], check=True)
    result = dict(status='PASS', scope='programmatic HTTP probe on entirely new data; not a recorded UI demo',
        folder=str(FOLDER), setup_actions=setup, action_trace=trace, initial_timeline=3, new_timeline=4,
        exact_user_prompt='designated fixture prompt', synthetic_messages=4, human_consent_requests=4,
        self_effect='new unapproved actor-agent-draft; final render blocked until distinct human final approval',
        final_job=final_job, output_sha256=completed['sha256'], fully_decoded=True,
        actual_provider_calls=0, real_credentials_read=0, real_billing_calls=0, main_data_accessed=False)
    (OUT / 'own-temp-probe.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
finally:
    process.send_signal(signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=20)
    (OUT / 'own-temp-child-stdout.log').write_text(stdout)
    (OUT / 'own-temp-child-stderr.log').write_text(stderr)
    assert process.returncode == 0, (process.returncode, stderr[-1000:])
stop = json.loads((run_evidence / 'stop.json').read_text())
assert stop['distinct_synthetic_messages'] == 4 and stop['external_attempts'] == []
assert not stop['worker_threads_still_alive']
assert stop['source_changed_during_run'] == []
preservation = json.loads((run_evidence / 'data-after.json').read_text())['original_assets_and_outputs_preserved']
assert preservation and all(preservation.values())
structured = json.loads((run_evidence / 'data-after.json').read_text())['structured_preservation']
assert structured['original_timeline_versions_preserved'] and structured['original_shots_and_motion_sources_preserved'] and structured['original_audio_versions_preserved']
reopened = app.Store(DATA).state()['projects'][SONG]
assert reopened['timeline_head'] == 4
print(json.dumps(dict(status='PASS', main_data_accessed=False, fixture_run_evidence=str(run_evidence),
                      four_messages=stop['distinct_synthetic_messages'], old_assets_preserved=True), ensure_ascii=False))
