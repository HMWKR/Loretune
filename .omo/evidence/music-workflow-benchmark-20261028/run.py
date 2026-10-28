"""Bounded native music workflow benchmark; no external model or private data."""
import array
import base64
from copy import deepcopy
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from threading import Thread
import time
import traceback
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid
import wave

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
OUT = BASE / 'attempt3'
OUT.mkdir(exist_ok=False)
sys.path.insert(0, str(ROOT))
import app
import backup
import editing
import production_context
from tests.test_motion import scene as sample_scene

SOURCE_NAMES = ['app.py', 'editing.py', 'renderer.py', 'motion_scene.py',
                'motion_renderer.py', 'motion-raster.swift', 'backup.py',
                'loretune.py', 'tests/test_motion.py']
SOURCE_NAMES = [n for n in SOURCE_NAMES if (ROOT / n).is_file()]
RESULT = {'schema': 'native-music-workflow-benchmark/1', 'task_id': 'music-native-workflow-benchmark-20261028',
          'attempt': 3, 'status': 'RUNNING', 'actual_provider_calls': 0,
          'prior_attempt': '../attempt2/REPORT.json',
          'private_data_access': False, 'credential_access': False,
          'methodology': 'Deterministic real HTTP actions, paired native outputs and artifact provenance',
          'scope': '30-second self-authored audio, 12 approved shot IDs; partial original07 dataset only. '
                   'Two native motion source clips reused through supported API. Optional image is a '
                   'self-authored test pattern, not an artist photo or AI quality benchmark.',
          'source_before': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in SOURCE_NAMES},
          'requests': [], 'checks': [], 'jobs': []}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def check(name, condition, details):
    RESULT['checks'].append(dict(name=name, passed=bool(condition), details=details))
    save_json('progress.json', RESULT)
    if not condition:
        raise AssertionError(name + ': ' + str(details))


def command(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def network_scope(event, args):
    if event == 'socket.connect':
        address = args[1]
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1'):
            raise RuntimeError('External network disabled for native workflow benchmark')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        parts = Path(str(args[0])).parts
        if any(p == '.env' or p.startswith('.env.') for p in parts):
            raise RuntimeError('Environment file access disabled')


sys.addaudithook(network_scope)


class HTTP:
    def __init__(self, data):
        self.http = app.server(data, 0)
        self.thread = Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.http.server_port)

    def close(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()

    def fetch(self, path):
        try:
            with urlopen(self.base + path, timeout=20) as reply:
                return reply.status, reply.read(), dict(reply.headers)
        except HTTPError as exc:
            with exc:
                return exc.code, exc.read(), dict(exc.headers)

    def state(self):
        code, raw, _ = self.fetch('/api/state')
        assert code == 200
        return json.loads(raw)

    def project(self):
        return self.state()['projects']['음원 중심 30초 벤치마크']

    def post(self, action, expected=200, **data):
        state = self.state()
        body = dict(action=action, data=data, revision=state['revision'], request_id=uuid.uuid4().hex)
        req = Request(self.base + '/api/action', json.dumps(body).encode(),
                      {'Content-Type': 'application/json', 'X-Loretune-Token': state['token']})
        started = time.monotonic()
        try:
            with urlopen(req, timeout=120) as reply:
                code, raw = reply.status, reply.read()
        except HTTPError as exc:
            with exc:
                code, raw = exc.code, exc.read()
        value = json.loads(raw)
        RESULT['requests'].append(dict(action=action, request_id=body['request_id'],
                                       body_sha256=digest(json.dumps(body).encode()), status=code,
                                       elapsed_seconds=round(time.monotonic() - started, 6),
                                       error=value.get('error')))
        save_json('progress.json', RESULT)
        assert code == expected, (action, code, value)
        return value

    def action(self, name, **data):
        return self.post(name, song='음원 중심 30초 벤치마크', **data)

    def process_job(self, identifier):
        started = time.monotonic()
        worked = self.http.store.process_next()
        job = next(j for j in self.state()['jobs'] if j['id'] == identifier)
        RESULT['jobs'].append(dict(id=identifier, kind=job.get('kind', 'final-render'),
                                   status=job['status'], elapsed_seconds=round(time.monotonic() - started, 6),
                                   error=job.get('error'), verified=job.get('verified')))
        check('job completed ' + identifier, worked and job['status'] == 'completed', RESULT['jobs'][-1])
        return job

    def download_job(self, job, label):
        saved = {}
        for suffix in ('.mp4', '.srt', '.json'):
            url = job['download'].rsplit('.', 1)[0] + suffix
            code, raw, headers = self.fetch(url)
            check(label + suffix + ' download', code == 200, dict(status=code, bytes=len(raw)))
            target = OUT / (label + suffix)
            target.write_bytes(raw)
            saved[suffix] = dict(file=target.name, sha256=digest(raw), bytes=len(raw),
                                 integrity=headers.get('X-Loretune-Integrity'))
            if suffix == '.mp4':
                check(label + ' MP4 hash', digest(raw) == job['sha256'], saved[suffix])
        return saved


def inspect_video(label):
    path = OUT / (label + '.mp4')
    metadata = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                  '-of', 'json', str(path)]).stdout)
    save_json(label + '-probe.json', metadata)
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    check(label + ' 30s1080p24', (video['width'], video['height'], video['r_frame_rate']) == (1920, 1080, '24/1')
          and abs(float(metadata['format']['duration']) - 30) < 1 / 24
          and set(s['codec_type'] for s in metadata['streams']) == {'video', 'audio', 'subtitle'},
          dict(width=video['width'], height=video['height'], rate=video['r_frame_rate'],
               duration=metadata['format']['duration']))
    raw = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ac', '1', '-ar', '48000',
                   '-f', 's16le', '-']).stdout
    samples = array.array('h');samples.frombytes(raw)
    middle = samples[48000:48000 * 29]
    rms = math.sqrt(sum(s * s for s in middle) / len(middle))
    crossings = sum(a <= 0 < b for a, b in zip(middle, middle[1:]))
    hz = crossings / (len(middle) / 48000)
    check(label + ' actual audio', 439 < hz < 441 and 5000 < rms < 6500,
          dict(samples=len(samples), frequency_hz=hz, rms=rms))
    colors = []
    for index in range(12):
        at = index * 2.5 + 1.0
        color = command(['ffmpeg', '-v', 'error', '-ss', str(at), '-i', str(path), '-frames:v', '1',
                         '-vf', 'crop=2:2:20:20,scale=1:1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-']).stdout
        colors.append(list(color))
    for at, suffix in ((1.0, 'first'), (28.5, 'last')):
        command(['ffmpeg', '-v', 'error', '-ss', str(at), '-i', str(path), '-frames:v', '1',
                 str(OUT / (label + '-' + suffix + '.png'))])
    cues = command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:s:0', '-f', 'srt', '-']).stdout.decode()
    save_json(label + '-decoded.json', dict(colors=colors, decoded_cues=cues, audio_pcm_sha256=digest(raw),
                                           audio_frequency_hz=hz, audio_rms=rms))
    return colors, cues, raw


def main():
    prior = json.loads((BASE / 'attempt2/REPORT.json').read_text())
    folder = Path(prior['owned_temporary_root'])
    assert folder.name.startswith('loretune-native-music-benchmark-')
    RESULT['owned_temporary_root'] = str(folder)
    RESULT['started_at_unix'] = time.time()
    RESULT['known_product_finding'] = dict(id='NATIVE-COLOR-01', status='unresolved in historical candidate', evidence='../color-probe/receipt.json', description='Declared sRGB HEX differs from actual native candidate. Sequence tests below compare export to its actual candidate, not to the incorrect assumption of untransformed source pixels.')
    name = '음원 중심 30초 벤치마크'
    api = HTTP(folder / 'data')
    try:
        RESULT['url'] = api.base
        project = api.project()
        check('resume first completed30s output without replay', project['timeline_head'] == 1 and len(project['shots']['장면12']['takes']) == 1, dict(timeline_version=project['timeline_head']))
        before_timeline = deepcopy(editing.current(project))
        timeline = {k: deepcopy(before_timeline[k]) for k in ['clips','audio','audio_offset','profile','subtitles']}
        before_job = next(j for j in api.state()['jobs'] if j['id'] == prior['jobs'][-1]['id'])
        first = before_job['id']
        check('existing first MP4 remains completed', before_job['status'] == 'completed', dict(job=first))
        RESULT['before'] = api.download_job(before_job, 'before')
        check('first saved output unchanged from attempt2', RESULT['before']['.mp4']['sha256'] == prior['before']['.mp4']['sha256'], RESULT['before']['.mp4'])
        before_colors, before_cues, before_pcm = inspect_video('before')
        native_colors=[]
        for shot in ['장면01','장면02']:
            candidate=project['shots'][shot]['takes'][0]
            raw=command(['ffmpeg','-v','error','-ss','1','-i',candidate['asset'],'-frames:v','1','-vf','crop=2:2:20:20,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
            native_colors.append(list(raw))
        expected=[native_colors[i%2] for i in range(12)]
        check('before12 cut order matches actual native sources', all(max(abs(a-b) for a,b in zip(c,e)) < 4 for c,e in zip(before_colors,expected)), dict(output=before_colors,native_source_colors=native_colors))
        inputs_before = {a['sha256']: hashlib.sha256(Path(a['asset']).read_bytes()).hexdigest() for a in project['audio_versions']}
        for shot in project['shots'].values():
            for take in shot['takes']:
                inputs_before[take['sha256']] = hashlib.sha256(Path(take['asset']).read_bytes()).hexdigest()
        image = OUT / 'optional-owned-image.png'
        command(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0x10C080:s=640x360', '-frames:v', '1', str(image)])
        api.action('take', shot='장면12', shot_revision=api.project()['shots']['장면12']['revision'],
                   filename='직접 제작한 선택 이미지.png', content=base64.b64encode(image.read_bytes()).decode(),
                   rights='직접 작성한 단색 테스트 패턴; 실제 인물 사진 아님', reason='사진 선택 입력 경로의 합성 표본')
        api.action('review_take', shot='장면12', take=2, decision='approved', reason='선택 이미지 별도 내용 검토')
        api.action('select', shot='장면12', take=2, shot_revision=api.project()['shots']['장면12']['revision'])
        failure = api.post('render_job', expected=400, song=name)
        check('selection change invalidates old output approval', bool(failure.get('error')), failure)
        changed = deepcopy(timeline)
        changed['clips'] = list(reversed(changed['clips']))
        changed['clips'][0]['take'] = 2
        changed['subtitles'] = [dict(start=0, end=2, text='선택 이미지를 더한 새 편집'),
                                dict(start=28, end=30, text='수정 후 마지막 자막')]
        api.action('timeline', timeline=changed)
        api.post('render_job', expected=400, song=name)
        api.action('approve_timeline')
        second = api.action('render_job')['job']
        after_job = api.process_job(second)
        RESULT['after'] = api.download_job(after_job, 'after')
        after_colors, after_cues, after_pcm = inspect_video('after')
        after_expected = [[16, 192, 128]] + list(reversed(expected))[1:]
        check('after optional image and reverse order', all(max(abs(a-b) for a,b in zip(c,e)) < 8
                                                          for c,e in zip(after_colors, after_expected)), after_colors)
        check('after Korean embedded captions', '선택 이미지를 더한 새 편집' in after_cues
              and '수정 후 마지막 자막' in after_cues and '첫 번째 음원 중심 편집' not in after_cues, after_cues)
        check('music unchanged across edit', digest(before_pcm) == digest(after_pcm),
              dict(before_sha256=digest(before_pcm), after_sha256=digest(after_pcm)))
        project = api.project()
        check('original approved timeline immutable', project['timeline_versions'][0] == before_timeline,
              dict(original_id=before_timeline['id'], current_id=project['timeline_head']))
        hashes_now = {a['sha256']: hashlib.sha256(Path(a['asset']).read_bytes()).hexdigest()
                      for a in project['audio_versions']}
        for shot in project['shots'].values():
            for take in shot['takes']:
                hashes_now[take['sha256']] = hashlib.sha256(Path(take['asset']).read_bytes()).hexdigest()
        check('input assets unchanged', all(hashes_now[k] == v == k for k,v in inputs_before.items()),
              dict(original_assets=len(inputs_before), current_assets=len(hashes_now)))
        image_sha = project['shots']['장면12']['takes'][1]['sha256']
        api.action('asset_rights', sha256=image_sha, blocked=True, reason='검증용 사용 중지')
        api.post('render_job', expected=400, song=name)
        code, _, _ = api.fetch(after_job['download'])
        check('revoked image blocks dependent MP4 download', code != 200, dict(status=code))
        code, raw, _ = api.fetch(before_job['download'])
        check('unrelated prior output remains downloadable', code == 200 and digest(raw) == before_job['sha256'], dict(status=code))
        api.action('asset_rights', sha256=image_sha, blocked=False, reason='검증 후 사용 중지 해제')
        code, raw, _ = api.fetch(after_job['download'])
        check('rights recovery reuses exact saved output', code == 200 and digest(raw) == after_job['sha256'], dict(status=code))
        api.action('delivery_review', job=second, decision='approved', reason='검증 산출물 프레임·음원·자막 확인')
        RESULT['job_ids'] = dict(before=first, after=second)
        save_json('state-before-backup.json', {k:v for k,v in api.state().items() if k != 'token'})
    finally:
        api.close()
    backup_started = time.monotonic()
    backup.create(folder / 'data', folder / 'backup')
    verified = backup.verify(folder / 'backup')
    backup.restore(folder / 'backup', folder / 'restored')
    RESULT['backup'] = dict(files=len(verified['files']), elapsed_seconds=time.monotonic()-backup_started)
    restored = HTTP(folder / 'restored')
    try:
        for label, identifier in RESULT['job_ids'].items():
            job = next(j for j in restored.state()['jobs'] if j['id'] == identifier)
            for suffix in ('.mp4', '.srt', '.json'):
                code, raw, headers = restored.fetch(job['download'].rsplit('.', 1)[0] + suffix)
                check('restored exact ' + label + suffix, code == 200 and digest(raw) == RESULT[label][suffix]['sha256'],
                      dict(status=code, sha256=digest(raw), integrity=headers.get('X-Loretune-Integrity')))
        save_json('state-after-restore.json', {k:v for k,v in restored.state().items() if k != 'token'})
    finally:
        restored.close()
    RESULT['source_after'] = {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCE_NAMES}
    RESULT['changed_sources'] = [n for n,h in RESULT['source_before'].items() if RESULT['source_after'][n] != h]
    RESULT['finished_at_unix'] = time.time()
    RESULT['status'] = 'REPORTED'
    RESULT['limits'] = ['Actual HTTP, native CoreText/FFmpeg and backup/reopen only; no browser/user test.',
                       'Two native clips reused across12 shot IDs; not12 independently generated scenes.',
                       'No actual AI model, artist image, commercial output or production throughput claim.',
                       'The original07 group/member/era/settings/other-organization dataset is not fully instantiated.']


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        RESULT['status'] = 'FAILED'
        RESULT['error'] = type(exc).__name__ + ': ' + str(exc)
        RESULT['traceback'] = traceback.format_exc()
        raise
    finally:
        save_json('REPORT.json', RESULT)
