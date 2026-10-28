from pathlib import Path
import json,subprocess,array,math,hashlib
root=Path(__file__).resolve().parent;fixtures=root/'live-schema-corrected';data=Path(json.loads((fixtures/'fixture.json').read_text())['directory']);summary=json.loads((fixtures/'summary.json').read_text());results={}
def run(args):return subprocess.check_output(['ffmpeg','-nostdin','-v','error',*args])
for case in (1,2):
 path=root/'artifacts'/f'claude-motion-v{case}.mp4';errors=[]
 for frame in (0,12,24,36,48,60,72,84,95):
  expected=run(['-i',str(fixtures/f'case-{case}'/f'frame-{frame:02}.png'),'-f','rawvideo','-pix_fmt','rgb24','-'])
  actual=run(['-i',str(path),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
  assert len(expected)==len(actual)==1920*1080*3
  mae=sum(abs(a-b) for a,b in zip(actual,expected))/len(actual);assert mae<3
  errors.append({'frame':frame,'rgb_mean_absolute_error':mae})
 results[f'motion-{case}']={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'preview_vs_encoded':errors,'threshold':'MAE<3 RGB levels; codec loss allowed, not pixel-identical'}
path=root/'artifacts'/'claude-edited-audio-captions.mp4';colors=[]
for t,wanted in ((.5,'blue'),(2.5,'red')):
 raw=run(['-ss',str(t),'-i',str(path),'-vf','crop=2:2:100:100,scale=1:1','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']);colors.append({'seconds':t,'rgb':list(raw),'expected':wanted});assert raw[2]>240 and raw[0]<10 if wanted=='blue' else raw[0]>240 and raw[2]<10
raw=run(['-i',str(path),'-map','0:a:0','-t','0.1','-f','f32le','-ac','1','-']);values=array.array('f');values.frombytes(raw);rms=math.sqrt(sum(x*x for x in values)/len(values));assert rms>.1
subtitles=run(['-i',str(path),'-map','0:s:0','-f','srt','-']).decode();assert all(x in subtitles for x in ('시작','움직임','완성','00:00:03,000'))
results['edited-output']={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sampled_clip_order':colors,'first_100ms_audio_rms':rms,'audio_gate':'source first second silent; offset=1 output non-silent','unicode_caption_timing_preserved':True,'output':str(path),'synthetic_claude_authorship':True}
(root/'live-media-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False))
