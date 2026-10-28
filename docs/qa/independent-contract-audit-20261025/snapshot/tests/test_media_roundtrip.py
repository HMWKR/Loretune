"""Actual FFmpeg trim/order/audio/subtitle roundtrip; no provider/network."""
import base64,json,math,shutil,struct,subprocess,tempfile,unittest,uuid,wave
from pathlib import Path
from app import Store

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class MediaRoundtripTest(unittest.TestCase):
    def test_trim_reorder_click_track_unicode_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);video=root/'color-clock.mp4';audio=root/'click.wav'
            args=['ffmpeg','-v','error']
            for color in ['red','green','blue']:args+=['-f','lavfi','-i',f'color={color}:s=128x72:r=24:d=1']
            subprocess.run(args+['-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]','-map','[v]','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
            rate=48000
            with wave.open(str(audio),'wb') as w:
                w.setparams((1,2,rate,0,'NONE','not compressed'))
                w.writeframes(b''.join(struct.pack('<h',int(20000*math.sin(2*math.pi*1000*i/rate)) if any(t<=i/rate<t+.025 for t in [.5,1.5,2.5]) else 0) for i in range(rate*3)))
            store=Store(root/'store')
            def call(action,**data):
                data.setdefault('song','QA');return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
            call('project',name='QA',era='default',story=0)
            for shot in ['blue','red']:
                call('shot',shot=shot,description=shot)
                call('take',shot=shot,shot_revision=0,filename=video.name,content=base64.b64encode(video.read_bytes()).decode(),reason='generated local color clock fixture',rights='synthetic QA')
                call('select',shot=shot,take=1,shot_revision=1)
                call('review_take',shot=shot,take=1,decision='approved',reason='fixture')
            call('audio',filename=audio.name,content=base64.b64encode(audio.read_bytes()).decode(),rights='synthetic QA')
            timeline=dict(clips=[dict(shot='blue',take=1,duration=1,trim=2),dict(shot='red',take=1,duration=1,trim=0)],audio=1,audio_offset=.25,profile='preview',subtitles=[dict(start=.1,end=.9,text='파랑 · Mira'),dict(start=1.1,end=1.9,text='빨강 · Theo')])
            call('timeline',timeline=timeline);call('approve_timeline');job=call('render_job')['job'];store.process_next()
            j=next(x for x in store.state()['jobs'] if x['id']==job);self.assertEqual(j['status'],'completed',j.get('error'))
            path=root/'store'/'exports'/(job+'.mp4')
            meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
            self.assertLessEqual(abs(float(meta['format']['duration'])-2),1/24)
            for t,channel in [(.5,2),(1.5,0)]:
                pixel=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=1:1','-f','rawvideo','-pix_fmt','rgb24','-'])
                self.assertGreater(pixel[channel],180);self.assertLess(sum(pixel)-pixel[channel],60)
            pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar',str(rate),'-f','s16le','-'])
            samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
            for expected in [.25,1.25]:
                start=int((expected-.05)*rate);window=samples[start:int((expected+.1)*rate)]
                first=next(i for i,x in enumerate(window) if abs(x)>5000)
                self.assertLessEqual(abs((start+first)/rate-expected),1/24)
            subtitle=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:s:0','-f','srt','-']).decode()
            self.assertIn('파랑 · Mira',subtitle);self.assertIn('빨강 · Theo',subtitle);self.assertIn('00:00:00,100',subtitle)
            manifest=json.loads(path.with_suffix('.json').read_text());self.assertEqual(manifest['timeline']['clips'][0]['shot'],'blue')
