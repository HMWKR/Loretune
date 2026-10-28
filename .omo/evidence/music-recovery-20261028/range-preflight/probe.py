"""Isolated real HTTP selection/output comparison. No configured providers."""
import base64
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from threading import Thread
from urllib.request import Request, urlopen
import uuid
import wave

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from app import server

phase = sys.argv[1]
out = Path(__file__).parent / phase
out.mkdir(exist_ok=True)
events = []
def save(name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
save('source-hashes.json', {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                          for p in ('editing.py', 'music.py', 'renderer.py', 'app.py')})
with tempfile.TemporaryDirectory(prefix='loretune-range-preflight-') as temp:
    folder = Path(temp)
    wav = folder / 'range.wav'
    with wave.open(str(wav), 'wb') as stream:
        stream.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b''.join(struct.pack('<h', round(8000 * math.sin(math.tau * (220 + 100 * (i // 48000)) * i / 48000))) for i in range(480000)))
    png = folder / 'image.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64', '-frames:v', '1', str(png)], check=True)
    http = server(folder / 'data', 0)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{http.server_port}'
    def state():
        with urlopen(base + '/api/state') as r: return json.load(r)
    def project(): return state()['projects']['range']
    def post(action, **data):
        data.setdefault('song', 'range')
        s = state()
        req = Request(base + '/api/action', data=json.dumps(dict(action=action, data=data, revision=s['revision'], request_id=uuid.uuid4().hex)).encode(), headers={'Content-Type': 'application/json', 'X-Loretune-Token': s['token']})
        with urlopen(req) as r:
            result = json.load(r)
            events.append(dict(action=action, status=r.status, response=result))
            return result
    try:
        post('project', name='range', era='default', story=0)
        post('audio', filename=wav.name, content=base64.b64encode(wav.read_bytes()).decode(), rights='직접 만든 합성 검증 음원')
        post('music_structure', audio=1, start=3, end=4, sections=[])
        post('shot', shot='s', description='합성 검증 장면')
        post('take', shot='s', shot_revision=0, filename=png.name, content=base64.b64encode(png.read_bytes()).decode(), reason='합성 검증', rights='직접 제작')
        post('select', shot='s', shot_revision=1, take=1)
        post('review_take', shot='s', take=1, decision='approved', reason='합성 검토 완료')
        timeline = dict(clips=[dict(shot='s', take=1, duration=3, trim=0)], audio=1, audio_offset=3, subtitles=[], profile='preview')
        post('timeline', timeline=timeline)
        post('approve_timeline')
        before = project()
        save('project-before-estimate.json', before)
        assert before['preflight']['ready'] and not before['preflight']['errors']
        assert before['preflight']['audio_start'] == 3 and before['preflight']['audio_end'] == 6
        mismatch = [w for w in before['preflight']['warnings'] if '현재 음악 선택' in w]
        assert bool(mismatch) == (phase != 'before'), before['preflight']
        post('estimate_render')
        quote = project()['render_estimates'][-1]
        save('estimate.json', quote)
        job = post('render_job', estimate=quote['id'])['job']
        assert http.store.process_next()
        result = next(j for j in state()['jobs'] if j['id'] == job)
        assert result['status'] == 'completed', result
        with urlopen(base + result['download']) as r:
            video = r.read()
            events.append(dict(action='download', status=r.status, bytes=len(video)))
        output = out / 'output.mp4'
        output.write_bytes(video)
        assert hashlib.sha256(video).hexdigest() == result['sha256']
        metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)]))
        save('ffprobe.json', metadata)
        assert abs(float(metadata['format']['duration']) - 3) < .05
        pcm = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', '0.1', '-i', str(output), '-map', '0:a:0', '-t', '0.2', '-ac', '1', '-ar', '48000', '-f', 's16le', '-'])
        (out / 'output-start.pcm').write_bytes(pcm)
        samples = struct.unpack('<' + 'h' * (len(pcm) // 2), pcm)
        hz = sum(a <= 0 < b for a, b in zip(samples, samples[1:])) / (len(samples) / 48000)
        assert abs(hz - 520) < 15, hz
        after = project()
        for key in ('timeline_versions', 'timeline_head', 'music_versions', 'music_head', 'audio_versions', 'audio_selected', 'shots'):
            assert before[key] == after[key], key
        assert http.store.operations()['provider']['calls'] == 0
        save('result.json', dict(status='PASS', phase=phase, source_duration=10, selected_range=[3,4], output_range=[3,6], preflight=before['preflight'], output_duration=float(metadata['format']['duration']), measured_start_frequency_hz=hz, expected_start_frequency_hz=520, provider_calls=0, immutable_fields=['timeline_versions','timeline_head','music_versions','music_head','audio_versions','audio_selected','shots'], output_sha256=result['sha256']))
        save('project-after-render.json', after)
        if phase == 'after-matrix':
            matrix = []
            for name, start, end, offset, duration, expected in [
                ('same', 3, 6, 3, 3, False),
                ('output-longer', 3, 4, 3, 3, True),
                ('output-shorter', 3, 9, 3, 3, True),
                ('offset-earlier', 3, 6, 2, 3, True),
                ('offset-later', 3, 6, 4, 3, True),
                ('fraction-equal', .1, .3, .1, .2, False),
                ('millisecond-difference', .1, .301, .1, .2, True),
                ('source-tail', 8, 9, 8, 3, True),
            ]:
                post('music_structure', audio=1, start=start, end=end, sections=[])
                timeline.update(audio_offset=offset)
                timeline['clips'][0]['duration'] = duration
                post('timeline', timeline=timeline)
                post('approve_timeline')
                before_read = project()
                observed = project()
                assert before_read == observed
                preflight = observed['preflight']
                assert preflight['ready'] and not preflight['errors']
                assert bool([w for w in preflight['warnings'] if w.startswith('현재 음악 선택')]) == expected, preflight
                if name == 'source-tail': assert any('무음으로 채워' in w for w in preflight['warnings'])
                matrix.append(dict(scenario=name, selected=[start,end], output=[offset,offset+duration], preflight=preflight, reread_immutable=True))
            post('audio', filename=wav.name, content=base64.b64encode(wav.read_bytes()).decode(), rights='직접 만든 합성 검증 음원')
            post('music_structure', audio=2, start=3, end=4, sections=[])
            observed = project()['preflight']
            assert observed['ready'] and not any(w.startswith('현재 음악 선택') for w in observed['warnings'])
            matrix.append(dict(scenario='different-audio-version', preflight=observed))
            post('comment', at=1, text='검토 필요')
            observed = project()['preflight']
            assert not observed['ready'] and '미해결 검토 의견이 있습니다.' in observed['errors']
            matrix.append(dict(scenario='existing-comment-block', preflight=observed))
            save('http-boundary-matrix.json', matrix)
    finally:
        save('http-events.json', events)
        http.shutdown(); http.server_close(); thread.join()
print(json.dumps(json.loads((out / 'result.json').read_text()), ensure_ascii=False))
