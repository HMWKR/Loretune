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
OUT = BASE / 'corrected'
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
          'attempt': 4, 'status': 'RUNNING', 'actual_provider_calls': 0,
          'prior_attempt': '../attempt3/REPORT.json',
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
    prior = json.loads((BASE/'attempt3/REPORT.json').read_text())
    folder = Path(prior['owned_temporary_root'])
    assert folder.name.startswith('loretune-native-music-benchmark-')
    RESULT['owned_temporary_root'] = str(folder)
    RESULT['scope'] = 'New approvals/candidates and third30s MP4 after exact sRGB fix. Same edited timeline order/audio/image/captions; existing native takes and outputs remain immutable.'
    RESULT['source_before']['native/motion_frame_renderer.swift'] = hashlib.sha256((ROOT/'native/motion_frame_renderer.swift').read_bytes()).hexdigest()
    RESULT['source_before']['tests/test_native_motion_color.py'] = hashlib.sha256((ROOT/'tests/test_native_motion_color.py').read_bytes()).hexdigest()
    name='음원 중심 30초 벤치마크'
    api=HTTP(folder/'data')
    try:
        RESULT['url']=api.base
        old_project=api.project();old_timelines=deepcopy(old_project['timeline_versions'])
        old_runtime=[str(p.relative_to(folder/'data')) for p in (folder/'data/motion-runtime').rglob('frame-renderer')]
        check('resume edited version2',old_project['timeline_head']==2,dict(version=old_project['timeline_head']))
        old_hashes={t['asset']:digest(Path(t['asset']).read_bytes()) for sh in old_project['shots'].values() for t in sh['takes']}
        for label,identifier in prior['job_ids'].items():
            job=next(j for j in api.state()['jobs'] if j['id']==identifier)
            code,raw,_=api.fetch(job['download'])
            check('old output preserved before correction '+label,code==200 and digest(raw)==prior[label]['.mp4']['sha256'],dict(status=code,sha256=digest(raw)))
        first_old=old_project['shots']['장면01']['motion_versions'][0]
        blocked=api.post('motion_render',expected=400,song=name,shot_id=production_context.shot_id(old_project,'장면01'),motion_revision=1,grant_id=first_old['approval']['id'])
        check('old motion approval rejects changed source', '렌더러' in blocked['error'],blocked)
        new_takes={}
        for number in [1,2]:
            shot='장면%02d'%number;project=api.project();version=project['shots'][shot]['motion_versions'][-1]
            sid=production_context.shot_id(project,shot)
            proposal=api.action('motion_propose',shot_id=sid,base_motion_revision=version['id'],scene=deepcopy(version['scene']))['motion']
            api.action('motion_review',proposal_id=proposal['proposal_id'],decision='approved')
            version=api.project()['shots'][shot]['motion_versions'][-1]
            jobid=api.action('motion_render',shot_id=sid,motion_revision=version['id'],grant_id=version['approval']['id'])['motion']['job_id']
            job=api.process_job(jobid);take=api.project()['shots'][shot]['takes'][-1]
            check('new source pinned '+shot,version['font']['source_sha256']==RESULT['source_before']['native/motion_frame_renderer.swift'] and take['provenance']['font']['source_sha256']==version['font']['source_sha256'],dict(font=version['font'],job=jobid))
            api.action('declare_take_rights',shot=shot,take=take['id'],sha256=take['sha256'],shot_revision=api.project()['shots'][shot]['revision'],evidence='직접 제작 모션의 새sRGB 렌더 후보 확인')
            api.action('select',shot=shot,take=take['id'],shot_revision=api.project()['shots'][shot]['revision'])
            api.action('review_take',shot=shot,take=take['id'],decision='approved',reason='동일구도 새색상후보 별도검토')
            new_takes[shot]=take['id']
            color=command(['ffmpeg','-v','error','-ss','1','-i',take['asset'],'-frames:v','1','-vf','crop=2:2:20:20,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
            expected=[26,42,74] if number==1 else [74,42,26]
            check('corrected native candidate YUV color '+shot,max(abs(a-b) for a,b in zip(color,expected))<=4,dict(actual=list(color),declared=expected,tolerance=4))
        for number in range(3,12):
            shot='장면%02d'%number;source='장면01' if number%2 else '장면02'
            api.action('reuse_take',shot=shot,shot_revision=api.project()['shots'][shot]['revision'],source_song=name,source_shot=source,source_take=new_takes[source],reason='새색상후보를새take로재사용')
            take=api.project()['shots'][shot]['takes'][-1]
            api.action('select',shot=shot,take=take['id'],shot_revision=api.project()['shots'][shot]['revision'])
            api.action('review_take',shot=shot,take=take['id'],decision='approved',reason='새후보별도검토')
            new_takes[shot]=take['id']
        timeline={k:deepcopy(old_timelines[-1][k]) for k in ['clips','audio','audio_offset','profile','subtitles']}
        for clip in timeline['clips']:
            if clip['shot'] in new_takes:clip['take']=new_takes[clip['shot']]
        api.action('timeline',timeline=timeline);api.action('approve_timeline')
        jobid=api.action('render_job')['job'];job=api.process_job(jobid)
        RESULT['corrected']=api.download_job(job,'corrected')
        colors,cues,pcm=inspect_video('corrected')
        after_pcm=command(['ffmpeg','-v','error','-i',str(BASE/'attempt3/after.mp4'),'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-']).stdout
        check('same edited audio PCM',digest(pcm)==digest(after_pcm),dict(sha256=digest(pcm)))
        check('same edited captions', (OUT/'corrected.srt').read_bytes()==(BASE/'attempt3/after.srt').read_bytes(),dict(cues=cues))
        expected=[[16,192,128]]+[[26,42,74] if i%2==0 else [74,42,26] for i in list(reversed(range(12)))[1:]]
        check('all12 corrected source colors',all(max(abs(a-b) for a,b in zip(c,e))<=4 for c,e in zip(colors,expected)),dict(actual=colors,expected=expected,tolerance=4))
        all_frames=command(['ffmpeg','-v','error','-i',str(OUT/'corrected.mp4'),'-map','0:v:0','-vf','crop=2:2:20:20,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-']).stdout
        check('exact720frames and60frame cut boundaries',len(all_frames)==2160 and all(max(abs(a-b) for a,b in zip(all_frames[i*3:i*3+3],expected[i//60]))<=4 for i in range(720)),dict(decoded_frames=len(all_frames)//3,frames_per_cut=60))
        check('old two timelines immutable',api.project()['timeline_versions'][:2]==old_timelines,dict(original_versions=2))
        check('old source bytes immutable',all(digest(Path(n).read_bytes())==h for n,h in old_hashes.items()),dict(original_assets=len(old_hashes)))
        for label,identifier in prior['job_ids'].items():
            old=next(j for j in api.state()['jobs'] if j['id']==identifier);code,raw,_=api.fetch(old['download'])
            check('old output preserved after correction '+label,code==200 and digest(raw)==prior[label]['.mp4']['sha256'],dict(status=code,sha256=digest(raw)))
        new_runtime=[str(p.relative_to(folder/'data')) for p in (folder/'data/motion-runtime').rglob('frame-renderer')]
        check('source-hashed compiled cache adds new binary',len(new_runtime)==len(old_runtime)+1 and set(old_runtime).issubset(new_runtime),dict(before=old_runtime,after=new_runtime))
        save_json('state-corrected.json',{k:v for k,v in api.state().items() if k!='token'})
    finally:api.close()
    # Controlled historical-code snapshot: create an ordinary approved queued job using the
    # byte-identical old Swift copy, then restore current source before reopening/claiming it.
    import motion_renderer
    from unittest.mock import patch
    with patch.object(motion_renderer,'SOURCE',BASE/'color-probe/before.swift'):
        upgrade=HTTP(folder/'upgrade-guard')
        try:
            upgrade.post('project',name=name,era='default',story=0);upgrade.action('shot',shot='queued',description='oldsourcequeuedguard')
            scene=sample_scene();sid=production_context.shot_id(upgrade.project(),'queued')
            proposal=upgrade.action('motion_propose',shot_id=sid,base_motion_revision=0,scene=scene)['motion']
            upgrade.action('motion_review',proposal_id=proposal['proposal_id'],decision='approved')
            version=upgrade.project()['shots']['queued']['motion_versions'][0]
            old_jobid=upgrade.action('motion_render',shot_id=sid,motion_revision=1,grant_id=version['approval']['id'])['motion']['job_id']
            check('historical-source job remains queued before upgrade',next(j for j in upgrade.state()['jobs'] if j['id']==old_jobid)['status']=='queued',dict(source_sha256=version['font']['source_sha256']))
        finally:upgrade.close()
    upgraded=HTTP(folder/'upgrade-guard')
    try:
        worked=upgraded.http.store.process_next();oldjob=next(j for j in upgraded.state()['jobs'] if j['id']==old_jobid)
        check('queued old source refuses publication after upgrade',worked and oldjob['status']=='failed' and '렌더러' in oldjob['error'] and upgraded.project()['shots']['queued']['takes']==[],dict(job=oldjob['id'],status=oldjob['status'],error=oldjob['error'],takes=0))
        save_json('queued-upgrade-job.json',oldjob)
    finally:upgraded.close()
    RESULT['source_after']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in RESULT['source_before']}
    RESULT['changed_sources']=[n for n,h in RESULT['source_before'].items() if RESULT['source_after'][n]!=h]
    RESULT['status']='REPORTED'
    RESULT['limits']=['Actual native/HTTP outputs and controlled historical-source upgrade fixture; no user/browser/model test.', 'Existing 30s output pair remains historical and unmodified; corrected output uses fresh approvals/takes/timeline.', 'One local timing sample, not production throughput.']


if __name__=='__main__':
    try:main()
    except Exception as exc:
        RESULT['status']='FAILED';RESULT['error']=type(exc).__name__+': '+str(exc);RESULT['traceback']=traceback.format_exc();raise
    finally:save_json('REPORT.json',RESULT)
