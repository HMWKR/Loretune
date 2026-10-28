"""User-authored music structure; never presented as inferred analysis."""
import math
import time
import subprocess
import shutil
from array import array
import sys


def finite(value, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise ValueError('시간은 유한한 0 이상의 숫자여야 합니다.')
    return round(value, 3)


def waveform(path):
    """Bounded actual PCM envelope, not beats or structural/semantic inference."""
    executable = shutil.which('ffmpeg')
    if not executable:
        return dict(status='unavailable', reason='FFmpeg 미설치')
    try:
        result=subprocess.run([executable,'-v','error','-protocol_whitelist','file,pipe','-i',str(path),
                               '-t','600','-vn','-ac','1','-ar','8000','-f','s16le','pipe:1'],
                              capture_output=True,check=True,timeout=20)
        samples=array('h');samples.frombytes(result.stdout)
        if sys.byteorder != 'little':samples.byteswap()
        if not samples:return dict(status='unavailable',reason='오디오 샘플 없음')
        bins=128
        step=max(1,math.ceil(len(samples)/bins))
        peaks=[round(max(abs(v) for v in samples[i:i+step])/32768,4) for i in range(0,len(samples),step)]
        rms=(sum(v*v for v in samples)/len(samples))**.5/32768
        return dict(status='measured',source='decoded-pcm-8khz-mono',duration=len(samples)/8000,
                    peaks=peaks,rms=round(rms,5),quiet=rms<.001,
                    note='최대 첫 600초의 간이 진폭 표시. 비트·BPM·구간 분석이 아닙니다.')
    except (subprocess.SubprocessError,ValueError):
        return dict(status='unavailable',reason='간이 파형 분석 실패; 원본 재생과 수동 입력을 사용하세요.')


def save_music(project, data):
    audio = next((a for a in project['audio_versions'] if a['id'] == data['audio']), None)
    if not audio:
        raise ValueError('음원 버전을 먼저 연결하세요.')
    start, end = finite(data['start']), finite(data['end'])
    if not start < end <= audio['metadata']['duration']:
        raise ValueError('선택 구간은 원곡 길이 안에서 시작 < 끝이어야 합니다.')
    sections = data.get('sections', [])
    if not isinstance(sections, list) or len(sections) > 100:
        raise ValueError('음악 구간은 최대 100개입니다.')
    checked = []
    previous_end = start
    for section in sections:
        a, b = finite(section['start']), finite(section['end'])
        label = section['label']
        if not isinstance(label, str) or not label.strip() or len(label) > 100:
            raise ValueError('구간 이름은 1~100자입니다.')
        if not previous_end <= a < b <= end:
            raise ValueError('구간은 선택 범위 안에서 시간순으로 겹치지 않아야 합니다.')
        checked.append(dict(start=a, end=b, label=label.strip(), source='user'))
        previous_end = b
    versions = project.setdefault('music_versions', [])
    version = dict(id=len(versions)+1, audio=audio['id'], start=start, end=end,
                   sections=checked, source='user', engine=None, created=time.time())
    versions.append(version)
    project['music_head'] = version['id']
    return version
