"""Synthetic local QA only. Idempotent: never overwrites an existing project."""
import sys,base64,json,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from app import Store
out=Path(__file__).parent/'fixture';out.mkdir(exist_ok=True)
name='디자인 시스템 기능 QA 20261026';store=Store('/tmp/loretune-ms-qa-20261025')
if name in store.state()['projects']:raise SystemExit('fixture already exists; no changes made')
for file,size in [('landscape.mp4','320x180'),('portrait.mp4','180x320')]:
 subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'testsrc2=size={size}:rate=24:duration=5','-c:v','libx264','-pix_fmt','yuv420p',str(out/file)],check=True)
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=8','-af','volume=0.1','-ar','48000',str(out/'tone.wav')],check=True)
subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=320x180','-frames:v','1',str(out/'still.png')],check=True)
def call(action,**data):
 data.setdefault('song',name);return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
def shotrev(n):return store.state()['projects'][name]['shots'][n]['revision']
call('project',name=name,era='default',story=0)
shots=['01 빛의 시작','02 움직임과 만남','03 여운을 남기는 마지막 장면']
for n in shots:
 call('shot',shot=n,description='시간축·트림·한국어 검토용 합성 미디어. 외부 AI 생성 아님.')
 for f in ['landscape.mp4','portrait.mp4','still.png']:
  call('take',shot=n,shot_revision=shotrev(n),filename=f,content=base64.b64encode((out/f).read_bytes()).decode(),reason='synthetic local QA fixture',rights='직접 만든 합성 테스트 패턴')
 call('select',shot=n,take=1,shot_revision=shotrev(n))
 call('review_take',shot=n,take=1,decision='approved',reason='합성 테스트. 실제 인물·모델 생성 결과 아님.')
call('audio',filename='tone.wav',content=base64.b64encode((out/'tone.wav').read_bytes()).decode(),rights='직접 만든 합성 음원')
timeline=dict(clips=[dict(shot=n,take=1,duration=d,trim=.25) for n,d in zip(shots,[1,2,4])],audio=1,audio_offset=.5,profile='landscape',subtitles=[dict(start=.1,end=.9,text='첫 장면 · 시작'),dict(start=1.1,end=2.8,text='두 번째 장면 · 함께'),dict(start=3.1,end=6.95,text='마지막 장면 · 끝까지 보존')])
call('timeline',timeline=timeline)
(out/'identity.json').write_text(json.dumps(dict(project=name,shots=shots,source='local FFmpeg synthetic',provider_calls=0,timeline=timeline),ensure_ascii=False,indent=2))
print(json.dumps(dict(project=name,shots=len(shots),takes=9,duration=7,external_calls=0),ensure_ascii=False))
