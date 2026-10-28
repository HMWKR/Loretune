"""Encode only actual captured JPEGs at their elapsed timestamps, sampled24fps."""
from pathlib import Path
import bisect
import hashlib
import json
import math
import subprocess
import sys

folder=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve()
if output.exists():raise SystemExit('Refusing to overwrite an earlier recording')
record_path=folder/'recording.json'; record=json.loads(record_path.read_text())
frames=record['frames']; fps=24
if not frames or record.get('captureError'):raise SystemExit('No valid capture')
viewport=record['viewport']
if any(f.get('pixelWidth')!=viewport['width'] or f.get('pixelHeight')!=viewport['height'] for f in frames):raise SystemExit('Capture dimensions changed')
start=record['startedAt']/1000; elapsed=record['elapsedSeconds']
timestamps=[min(elapsed,max(0,f['capturedTimestamp']-start)) for f in frames]
if any(a>b for a,b in zip(timestamps,timestamps[1:])):raise SystemExit('Capture time moved backwards')
for f in frames:
 if hashlib.sha256((folder/f['filename']).read_bytes()).hexdigest()!=f['sha256']:raise SystemExit('Capture bytes changed')
count=math.ceil(elapsed*fps)
indices=[max(0,bisect.bisect_right(timestamps,i/fps)-1) for i in range(count)]
encoding=folder/('encoding-'+output.stem);encoding.mkdir(exist_ok=False)
schedule=[dict(output_frame=i,output_time=i/fps,capture_frame=j,capture_time=timestamps[j],sha256=frames[j]['sha256']) for i,j in enumerate(indices)]
(encoding/'sampling-schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
command=['ffmpeg','-nostdin','-v','error','-f','image2pipe','-framerate',str(fps),'-c:v','mjpeg','-i','pipe:0','-frames:v',str(count),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
with (encoding/'encode.stderr.log').open('xb') as stderr:
 process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=stderr,stdout=subprocess.DEVNULL)
 try:
  previous=None;data=None
  for index in indices:
   if index!=previous:data=(folder/frames[index]['filename']).read_bytes();previous=index
   process.stdin.write(data)
  process.stdin.close();process.stdin=None
  code=process.wait(timeout=180)
 except BaseException:
  process.kill();process.wait();raise
if code:raise SystemExit('Capture encoding failed')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
decoded=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(output),'-f','null','-'],capture_output=True,timeout=180)
(encoding/'decode.stderr.log').write_bytes(decoded.stderr)
duration=float(probe['format']['duration']);video=next(s for s in probe['streams'] if s['codec_type']=='video')
if video['width']!=viewport['width'] or video['height']!=viewport['height']:raise SystemExit('Encoded dimensions changed')
if decoded.returncode or int(video['nb_frames'])!=count or abs(duration-elapsed)>1/fps+.002:raise SystemExit('Actual capture duration/frame count/decode failed')
result=dict(command=command,encode_exit_code=code,decode_exit_code=decoded.returncode,output=str(output),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),probe=probe,recorded_elapsed_seconds=elapsed,output_duration=duration,actual_capture_frames=len(frames),encoded_frames=count,frame_sampling='Latest actual captured JPEG at each24fps elapsed-clock sample; initial pre-capture interval holds first actual JPEG; no painted/reconstructed frames',initial_capture_latency=timestamps[0],sampling_schedule_sha256=hashlib.sha256((encoding/'sampling-schedule.json').read_bytes()).hexdigest(),capture_record_sha256=hashlib.sha256(record_path.read_bytes()).hexdigest(),edited=False,sped_up=False,omitted_intervals=[],audio=record['audio'],playback_and_content_review='Pending browser playback; real middle capture JPEG already viewed')
(encoding/'encode-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('output','output_duration','actual_capture_frames','encoded_frames','decode_exit_code')}))
