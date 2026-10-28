"""Local rendering from an immutable timeline snapshot; no provider calls."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import json
from editing import PROFILES, caption_text, frame_timing
from caption_preview import webvtt

class Cancelled(Exception): pass

def verify_output(path, project):
    exe=shutil.which('ffprobe')
    if not exe:raise ValueError('출력 검증에 FFprobe가 필요합니다.')
    result=subprocess.run([exe,'-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,timeout=20,check=True)
    data=json.loads(result.stdout)
    streams=data['streams'];types=[x['codec_type'] for x in streams]
    video=next((x for x in streams if x['codec_type']=='video'),None)
    width,height=PROFILES[project.get('profile','preview')]
    duration=float(data['format']['duration'])
    timing=frame_timing(x.get('duration',3) for x in project['shots'].values())
    expected=timing['duration']
    if not video or (video['width'],video['height'])!=(width,height) or abs(duration-expected)>1/24:
        raise ValueError('출력 영상 길이·해상도 검증에 실패했습니다.')
    if abs(float(video.get('duration',duration))-expected)>0.002:raise ValueError('출력 프레임 시간 경계가 명세와 다릅니다.')
    if video.get('r_frame_rate')!='24/1':raise ValueError('출력 프레임률이 24fps가 아닙니다.')
    if bool(project.get('audio'))!=('audio' in types) or bool(project.get('subtitles'))!=('subtitle' in types):
        raise ValueError('출력 음원·자막 트랙 검증에 실패했습니다.')
    audio=next((x for x in streams if x['codec_type']=='audio'),None)
    if audio and audio.get('sample_rate')!='48000':raise ValueError('출력 음원 샘플레이트가 48kHz가 아닙니다.')
    if audio and float(audio.get('duration',0))+0.002<timing['requested_duration']:
        raise ValueError('승인한 음원 사용 구간의 말미가 출력에서 잘렸습니다.')
    if project.get('subtitles'):
        # mov_text samples start with a two-byte big-endian text length; reject
        # unexpected style boxes because this editor exports plain captions.
        # https://ffmpeg.org/doxygen/trunk/movtextdec_8c_source.html
        packets=json.loads(subprocess.run([exe,'-v','error','-select_streams','s:0','-show_packets','-show_entries','packet=pts_time,duration_time,pos,size','-of','json',str(path)],capture_output=True,timeout=20,check=True).stdout)['packets']
        actual=[]
        with Path(path).open('rb') as source:
            for packet in packets:
                source.seek(int(packet['pos']));payload=source.read(int(packet['size']))
                if len(payload)<2:raise ValueError('출력 자막 패킷이 불완전합니다.')
                length=int.from_bytes(payload[:2],'big')
                if len(payload)!=length+2:raise ValueError('출력 자막에 예상하지 않은 서식 또는 잘린 데이터가 있습니다.')
                if not length:continue
                start=float(packet['pts_time']);cue_duration=float(packet['duration_time'])
                actual.append((round(start*1000),round((start+cue_duration)*1000),payload[2:].decode('utf-8')))
        expected=[(round(line['start']*1000),round(line['end']*1000),caption_text(line['text'])) for line in project['subtitles']]
        if actual!=expected:raise ValueError('출력 자막 내용·시각이 승인된 자막과 다릅니다.')

    return dict(duration=duration,width=width,height=height,frame_rate=video['r_frame_rate'],
                audio_sample_rate=audio.get('sample_rate') if audio else None,frame_timing=timing,streams=types,verified_at=time.time())

def run(args,cancelled):
    with tempfile.TemporaryFile() as errors:
        p=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=errors)
        start=time.monotonic()
        while p.poll() is None:
            if cancelled() or time.monotonic()-start>180:
                p.terminate()
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:p.kill();p.wait()
                if cancelled():raise Cancelled('사용자가 취소했습니다.')
                raise ValueError('렌더 제한 시간 초과. 더 짧은 구간 또는 낮은 해상도를 사용하세요.')
            time.sleep(.05)
        if p.returncode:raise ValueError('미디어 디코딩 또는 인코딩 실패. 파일 형식과 시작 위치를 확인하세요.')

def render(project,output,progress=lambda n:None,cancelled=lambda:False,parts_dir=None):
    exe=shutil.which('ffmpeg')
    if not exe:raise ValueError('FFmpeg가 설치되어 있지 않습니다.')
    if not 1<=len(project['shots'])<=30:raise ValueError('1~30개 샷이 필요합니다.')
    width,height=PROFILES[project.get('profile','preview')]
    with tempfile.TemporaryDirectory() as folder:
        work=Path(parts_dir) if parts_dir else Path(folder)
        work.mkdir(parents=True,exist_ok=True);parts=[]
        timing=frame_timing(s.get('duration',3) for s in project['shots'].values());total=timing['duration']
        for i,shot in enumerate(project['shots'].values()):
            if cancelled():raise Cancelled('사용자가 취소했습니다.')
            take=next(t for t in shot['takes'] if t['id']==shot['selected']);asset=Path(take['asset']);part=work/f'{i}.mp4'
            frames=timing['clips'][i]['frames'];duration=frames/24;trim=shot.get('trim',0)
            args=[exe,'-nostdin','-y','-v','error','-protocol_whitelist','file,pipe']
            if asset.suffix.lower() in {'.jpg','.jpeg','.png'}:args+=['-loop','1']
            else:args+=['-ss',str(trim)]
            args+=['-i',str(asset),'-frames:v',str(frames),'-an','-vf',f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,tpad=stop_mode=clone:stop_duration={duration}','-r','24','-c:v','libx264','-preset','fast','-pix_fmt','yuv420p',str(part)]
            run(args,cancelled);parts.append(part);progress(round((i+1)/len(project['shots'])*80))
        listing=Path(folder)/'list.txt';listing.write_text('\n'.join("file '"+str(p)+"'" for p in parts))
        args=[exe,'-nostdin','-y','-v','error','-f','concat','-safe','0','-protocol_whitelist','file,pipe','-i',str(listing)]
        audio=project.get('audio');lines=project.get('subtitles',[]);index=1
        if audio:
            args+=['-protocol_whitelist','file,pipe','-ss',str(project.get('audio_offset',0)),'-i',audio['asset']];audio_index=index;index+=1
        if lines:
            subtitle=Path(folder)/'captions.vtt';subtitle.write_bytes(webvtt(lines,preserve_leading_spaces=True));args+=['-i',str(subtitle)];subtitle_index=index
        args+=['-map','0:v:0','-c:v','copy']
        if audio:args+=['-map',f'{audio_index}:a:0','-c:a','aac','-ar','48000','-af','apad']
        if lines:args+=['-map',f'{subtitle_index}:s:0','-c:s','mov_text','-metadata:s:s:0','language=kor','-disposition:s:0','default']
        args+=['-t',str(total),'-movflags','+faststart',str(output)]
        run(args,cancelled);progress(100)
