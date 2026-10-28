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

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
import app
import editing
import production_context
from tests.test_motion import scene

OUT = Path(__file__).resolve().parent
FOLDER = Path(tempfile.mkdtemp(prefix='loretune-actual-ui-probe-'))
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
    sock.bind(("127.0.0.1",0)); port=sock.getsockname()[1]
result=dict(folder=str(FOLDER),data=str(DATA),song=SONG,workspace_id=store.workspace_id,port=port,setup_actions=setup,setup_mode="explicit direct Store API fixture preparation only; no UI task counted")
(OUT/"fixture-setup.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(result,ensure_ascii=False))
