"""Versioned non-destructive editing and local media inspection."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import math
import shutil
import subprocess

PROFILES={'preview':(640,360),'landscape':(1920,1080),'portrait':(1080,1920)}

def frame_timing(durations):
    """24fps cumulative boundaries, half-up: bounded error, no per-cut drift."""
    from decimal import Decimal, ROUND_HALF_UP
    total=Decimal(0);previous=0;clips=[]
    for duration in durations:
        total+=Decimal(str(duration))
        end=int((total*24).to_integral_value(rounding=ROUND_HALF_UP))
        clips.append(dict(start_frame=previous,end_frame=end,frames=end-previous,start=previous/24,end=end/24))
        previous=end
    return dict(fps=24,policy='cumulative-nearest-half-up',requested_duration=float(total),duration=previous/24,clips=clips)

def seconds(value, maximum=600):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=maximum:
        raise ValueError('시간은 0~600초의 유한 숫자여야 합니다.')
    return round(value,3)

def probe(path, kind):
    exe=shutil.which('ffprobe')
    if not exe: raise ValueError('FFprobe가 없어 미디어를 검사할 수 없습니다.')
    try:
        r=subprocess.run([exe,'-v','error','-protocol_whitelist','file,pipe','-show_streams','-show_format','-of','json',str(path)],capture_output=True,timeout=20,check=True)
        d=json.loads(r.stdout)
        streams=[s for s in d['streams'] if s['codec_type']==kind]
        if not streams:raise ValueError('필요한 미디어 트랙이 없습니다.')
        stream=streams[0]
        if kind=='video' and (stream.get('width',0)<=0 or stream.get('height',0)<=0):
            raise ValueError('디코딩 가능한 영상 크기가 없습니다.')
        if kind=='audio' and (int(stream.get('sample_rate',0))<=0 or stream.get('channels',0)<=0):
            raise ValueError('디코딩 가능한 음원 정보가 없습니다.')
        decoder=shutil.which('ffmpeg')
        if not decoder:raise ValueError('미디어 검증에 FFmpeg가 필요합니다.')
        args=[decoder,'-nostdin','-v','error','-xerror','-protocol_whitelist','file,pipe','-i',str(path)]
        args+=['-map','0:v:0','-frames:v','1'] if kind=='video' else ['-map','0:a:0','-t','0.1']
        subprocess.run(args+['-f','null','-'],capture_output=True,timeout=20,check=True)
        return dict(duration=float(d.get('format',{}).get('duration',0)),codec=stream.get('codec_name'),width=stream.get('width'),height=stream.get('height'),sample_rate=stream.get('sample_rate'),channels=stream.get('channels'))
    except (subprocess.SubprocessError,KeyError,json.JSONDecodeError) as exc:
        raise ValueError('파일 내용을 읽지 못했습니다. 정상 미디어 파일을 선택하세요.') from exc

def defaults(p):
    for key,value in dict(audio_versions=[],audio_selected=None,audio_offset=0,timeline_versions=[],timeline_head=None,subtitles=[],comments=[],profile='preview').items():p.setdefault(key,deepcopy(value))

def current(p):
    defaults(p)
    if p['timeline_head'] is not None:return deepcopy(p['timeline_versions'][p['timeline_head']-1])
    return dict(id=0,clips=[dict(shot=n,take=s['selected'],duration=s.get('planned_duration',3),trim=0) for n,s in p['shots'].items()],audio=p['audio_selected'],audio_offset=p.get('music_versions',[])[-1]['start'] if p.get('music_head') else p['audio_offset'],subtitles=deepcopy(p['subtitles']),profile=p['profile'])

def validate(p, timeline):
    clips=timeline['clips']
    if not isinstance(clips,list) or not 1<=len(clips)<=30:raise ValueError('타임라인은 1~30개의 컷이어야 합니다.')
    total=0
    for clip in clips:
        if clip['shot'] not in p['shots']:raise ValueError('존재하지 않는 샷입니다.')
        if type(clip['take']) is not int or clip['take'] not in [t['id'] for t in p['shots'][clip['shot']]['takes']]:raise ValueError('각 컷의 take를 선택하세요.')
        duration=seconds(clip['duration']); trim=seconds(clip['trim'])
        if duration<0.125:raise ValueError('컷 길이는 0.125초 이상이어야 합니다.')
        take=next(t for t in p['shots'][clip['shot']]['takes'] if t['id']==clip['take'])
        media_duration=take.get('metadata',{}).get('duration',0)
        if media_duration and trim>=media_duration:raise ValueError('시작 위치가 영상 길이를 벗어납니다.')
        clip.update(duration=duration,trim=trim);total+=duration
    if total>600:raise ValueError('전체 길이는 최대 600초입니다.')
    if timeline['profile'] not in PROFILES:raise ValueError('지원하지 않는 출력 규격입니다.')
    seconds(timeline['audio_offset'])
    audio=timeline['audio']
    if audio is not None:
        versions=[a for a in p['audio_versions'] if a['id']==audio]
        if not versions or timeline['audio_offset']>=versions[0]['metadata']['duration']:raise ValueError('음원 또는 시작 위치를 확인하세요.')
    last=0
    for line in timeline['subtitles']:
        start,end=seconds(line['start']),seconds(line['end'])
        if start<last or end<=start or end>total:raise ValueError('자막은 순서대로 겹치지 않고 영상 길이 안에 있어야 합니다.')
        if not isinstance(line['text'],str) or not line['text'].strip() or len(line['text'])>500:raise ValueError('자막은 1~500자여야 합니다.')
        last=end
    return timeline

def save_timeline(p, timeline):
    defaults(p);timeline=validate(p,deepcopy(timeline));timeline['id']=len(p['timeline_versions'])+1
    timeline.pop('approval',None)
    p['timeline_versions'].append(timeline);p['timeline_head']=timeline['id'];p['revision']+=1
    return timeline

def preflight(p):
    """Explain the current stored timeline's readiness without changing it."""
    defaults(p)
    timeline = current(p)
    errors, warnings = [], []
    if not p['timeline_head']:
        errors.append('타임라인을 저장하세요.')
    if not timeline.get('approval'):
        errors.append('저장한 타임라인 승인이 필요합니다.')
    try:
        validate(p, deepcopy(timeline))
    except (ValueError, KeyError, TypeError) as exc:
        errors.append('미디어·편집 입력을 확인하세요: ' + str(exc))
    total = sum(c.get('duration', 0) for c in timeline.get('clips', []))
    timing=frame_timing(c.get('duration',0) for c in timeline.get('clips',[]))
    if any(abs(c.get('duration',0)-q['frames']/24)>0.000001 for c,q in zip(timeline.get('clips',[]),timing['clips'])):
        warnings.append(f"24fps 누적 프레임 경계로 출력합니다. 요청 {total:.3f}초 → 출력 {timing['duration']:.3f}초; 컷 경계 오차 최대 1/48초. 음원·자막의 절대 시각은 보존합니다.")
    for clip in timeline.get('clips', []):
        shot = p['shots'].get(clip.get('shot'))
        if not shot:
            continue
        if shot['selected'] != clip.get('take'):
            errors.append(clip['shot'] + ': 현재 선택과 저장된 take가 다릅니다.')
        review = next((r for r in reversed(shot.get('reviews', [])) if r['take'] == clip.get('take')), None)
        if not review or review['decision'] != 'approved':
            errors.append(clip['shot'] + ': take 검토 승인이 필요합니다.')
    if any(not c['resolved'] for c in p['comments']):
        errors.append('미해결 검토 의견이 있습니다.')
    audio = next((a for a in p['audio_versions'] if a['id'] == timeline.get('audio')), None)
    if audio is None:
        warnings.append('음원 없는 무음 출력입니다.')
    elif timeline['audio_offset'] + total > audio['metadata']['duration']:
        warnings.append('선택한 음원이 영상보다 짧아 끝부분은 무음으로 채워집니다.')
    return dict(ready=not errors, errors=errors, warnings=warnings, duration=total,
                audio_version=timeline.get('audio'), audio_start=timeline.get('audio_offset', 0),
                audio_end=timeline.get('audio_offset', 0)+total, profile=timeline.get('profile'),
                note='저장된 편집 기준 안내입니다. 실제 실행 시 자산 해시와 승인 상태를 다시 검사합니다.')

def render_project(p, timeline):
    """Resolve an immutable EDL; repeated shot occurrences are kept separately."""
    timeline=validate(p,deepcopy(timeline));result=deepcopy(p);result['shots']={}
    for i,clip in enumerate(timeline['clips']):
        shot=deepcopy(p['shots'][clip['shot']]);shot.update(selected=clip['take'],duration=clip['duration'],trim=clip['trim']);result['shots'][str(i)]=shot
    result['audio']=next((deepcopy(a) for a in p['audio_versions'] if a['id']==timeline['audio']),None)
    result['frame_timing']=frame_timing(c['duration'] for c in timeline['clips'])
    result.update(audio_offset=timeline['audio_offset'],subtitles=deepcopy(timeline['subtitles']),profile=timeline['profile'],timeline=deepcopy(timeline))
    for asset in [t for s in result['shots'].values() for t in s['takes'] if t['id']==s['selected']]+([result['audio']] if result['audio'] else []):
        if not asset.get('rights') or asset['rights']=='사용권 미확인':
            raise ValueError('영상과 음원 모두 사용권 근거를 확인한 원본을 연결하세요.')
        if sha256(Path(asset['asset']).read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('원본 미디어가 변경되었습니다.')
    return result

def srt(lines):
    def stamp(s):
        ms=round(s*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    return '\n\n'.join(f"{i+1}\n{stamp(l['start'])} --> {stamp(l['end'])}\n{l['text']}" for i,l in enumerate(lines))+'\n'
