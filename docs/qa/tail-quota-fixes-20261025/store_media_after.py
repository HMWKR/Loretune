from helpers import *
import shutil
media=ROOT/'media'
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call=fixture(folder)
 call('project',name='tail',era='default',story=0);call('shot',song='tail',shot='one',description='synthetic')
 call('take',song='tail',shot='one',shot_revision=0,filename='synthetic.png',content=base64.b64encode((media/'synthetic.png').read_bytes()).decode(),reason='audit',rights='synthetic owned')
 call('select',song='tail',shot='one',shot_revision=1,take=1)
 call('review_take',song='tail',shot='one',take=1,decision='approved',reason='audit')
 call('audio',song='tail',filename='clicks.wav',content=base64.b64encode((media/'clicks.wav').read_bytes()).decode(),rights='synthetic owned')
 timeline=dict(clips=[dict(shot='one',take=1,duration=.131,trim=0) for _ in range(30)],audio=1,audio_offset=0,profile='preview',subtitles=[dict(start=.2,end=.4,text='첫 박자'),dict(start=3.92,end=3.93,text='끝 자막')])
 call('timeline',song='tail',timeline=timeline);call('approve_timeline',song='tail')
 j=call('render_job',song='tail')['job'];st.process_next()
 job=next(jj for jj in st.state()['jobs'] if jj['id']==j)
 out=Path(folder)/'exports'/(j+'.mp4');record=json.loads(out.with_suffix('.json').read_text())
 srt=subprocess.check_output(['ffmpeg','-v','error','-i',str(out),'-map','0:s:0','-f','srt','-']).decode()
 shutil.copy2(out,media/'store-tail-preserved.mp4');shutil.copy2(out.with_suffix('.json'),media/'store-tail-preserved-manifest.json')
 value=dict(state=job['status'],manifest_captions=record['timeline']['subtitles'],actual_srt=srt,verified=job['verified'],sha256=hashlib.sha256(out.read_bytes()).hexdigest(),accepted_timeline=True)
 (ROOT/'store-media-after.json').write_text(json.dumps(value,ensure_ascii=False,indent=2))
 print(json.dumps(dict(state=job['status'],manifest_has_tail=True,output_has_tail='끝 자막' in srt,sha256=value['sha256']),ensure_ascii=False))
 assert job['status']=='completed' and '끝 자막' in srt

import struct
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(media/'store-tail-preserved.mp4'),'-map','0:a:0','-ac','1','-ar','48000','-f','s16le','-'])
samples=struct.unpack('<'+'h'*(len(raw)//2),raw)
peak=max(abs(x) for x in samples[int(3.92*48000):int(3.94*48000)])
assert peak>5000
(ROOT/'tail-audio-peak.json').write_text(json.dumps(dict(peak=peak,interval=[3.92,3.94],source_click=3.925)))
print('tail audio peak',peak)
