"""Local render confirmation: no provider tariff or payment reservation implied."""
from hashlib import sha256
import json
import time
import uuid
from editing import PROFILES


def fingerprint(snapshot):
    inputs = dict(timeline=snapshot['timeline'], audio=snapshot['audio'],
        clips=[dict(take=next(t for t in s['takes'] if t['id']==s['selected']),
                    duration=s['duration'],trim=s['trim']) for s in snapshot['shots'].values()])
    return sha256(json.dumps(inputs,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def estimate(snapshot, now=None):
    now = time.time() if now is None else now
    timeline = snapshot['timeline']
    duration = sum(c['duration'] for c in timeline['clips'])
    return dict(id=uuid.uuid4().hex, created=now, expires=now+300,
        fingerprint=fingerprint(snapshot), timeline_version=timeline['id'],
        clips=len(timeline['clips']), duration=duration, resolution=PROFILES[timeline['profile']],
        audio_version=timeline['audio'], audio_start=timeline['audio_offset'],
        audio_end=timeline['audio_offset']+duration, subtitles=len(timeline['subtitles']),
        provider_calls=0, provider_cost=0, local_compute=None,
        scope='로컬 FFmpeg 합성만; 외부 전송 없음. AI 생성 견적·예산 예약·청구가 아닙니다.')


def validate(quote, snapshot, now=None):
    now = time.time() if now is None else now
    if now >= quote['expires']:
        raise ValueError('출력 확인이 만료됐습니다. 현재 입력으로 다시 확인하세요.')
    if quote['fingerprint'] != fingerprint(snapshot):
        raise ValueError('출력 입력이 변경됐습니다. 현재 버전과 비용 범위를 다시 확인하세요.')
