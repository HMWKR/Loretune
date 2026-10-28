from pathlib import Path
import json,subprocess,array,math
out=Path(__file__).resolve().parent;qa=out.parent/'native-motion-20261026'
def run(args):return subprocess.check_output(['ffmpeg','-nostdin','-v','error',*args])
def decoded(name,frame):return run(['-i',str(qa/'artifacts'/name),'-vf',f'select=eq(n\\,{frame})','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
def dot(raw):
 xs=[];ys=[]
 for y in range(740,900):
  for x in range(1920):
   i=(y*1920+x)*3;r,g,b=raw[i:i+3]
   if abs(r-247)+abs(g-164)+abs(b-79)<45:xs.append(x);ys.append(y)
 return {'pixels':len(xs),'bounds':[min(xs),min(ys),max(xs),max(ys)] if xs else None}
records=[]
for case,frame in [(1,12),(2,24)]:
 raw=decoded(f'claude-motion-v{case}.mp4',frame)
 expected=run(['-i',str(qa/'live-schema-corrected'/f'case-{case}'/f'frame-{frame:02}.png'),'-f','rawvideo','-pix_fmt','rgb24','-'])
 assert len(raw)==len(expected)==1920*1080*3
 mae=sum(abs(a-b) for a,b in zip(raw,expected))/len(raw)
 assert mae<3
 records.append({'case':case,'frame':frame,'rgb_mae':mae,'dot':dot(raw)})
assert records[0]['dot']['pixels']>2000 and records[1]['dot']['pixels']>2000
assert all(abs(a-b)<=2 for a,b in zip(records[0]['dot']['bounds'],records[1]['dot']['bounds']))
before=dot(decoded('claude-motion-v2.mp4',0));assert before['pixels']==0
path=qa/'artifacts/claude-edited-audio-captions.mp4'
captions=run(['-i',str(path),'-map','0:s:0','-f','srt','-']).decode()
for i,t in enumerate(['시작','움직임','완성']):assert t in captions and f'00:00:0{i},000 --> 00:00:0{i+1},000' in captions
raw=run(['-i',str(path),'-map','0:a:0','-t','0.1','-f','f32le','-ac','1','-']);v=array.array('f');v.frombytes(raw);rms=math.sqrt(sum(x*x for x in v)/len(v));assert rms>.1
colors=[]
for seconds,channel in [(0.5,2),(2.5,0)]:
 rgb=run(['-ss',str(seconds),'-i',str(path),'-vf','crop=2:2:100:100,scale=1:1','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']);assert rgb[channel]>240;colors.append({'seconds':seconds,'rgb':list(rgb)})
result={'status':'PASS','decoded_samples':records,'delayed_dot_frame_0':before,'trial_tolerances':{'rgb_mae':'<3 codec RGB levels, implementation proposal','dot_bounds':'within 2 decoded pixels, this audit sample only'},'caption_text_and_exact_times':captions,'first_100ms_audio_rms':rms,'colors':colors,'limits':'Sampled decoded content; not continuous AV drift, complete visual quality or full audio preservation measurement. No render/model call.'}
(out/'media-samples.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
