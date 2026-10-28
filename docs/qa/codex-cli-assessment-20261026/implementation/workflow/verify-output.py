from pathlib import Path
import json,hashlib,subprocess,array,math
base=Path(__file__).resolve().parent;r=json.loads((base/'render-result.json').read_text());j=r['job'];assert j['status']=='completed';out=base/'verified-output';f=out/'synthetic-local.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(f)]))
srt=subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-map','0:s:0','-f','srt','-']).decode();assert 'Aethon 합성 제작 검증' in srt and '단색 시험 후보 · 실제 AI 생성 아님' in srt
raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-map','0:a:0','-ac','1','-ar','48000','-f','f32le','-']);got=array.array('f',raw)
original=j['snapshot']['audio']['asset'];raw=subprocess.check_output(['ffmpeg','-v','error','-ss','0.5','-t','3','-i',original,'-ac','1','-ar','48000','-f','f32le','-']);expected=array.array('f',raw);n=min(len(got),len(expected));a=got[:n];b=expected[:n];correlation=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b));assert correlation>.98
for label,pos in [('pattern-frame','0.25'),('synthetic-candidate-frame','1.75')]:
 file=out/(label+'.png')
 if not file.exists():subprocess.run(['ffmpeg','-v','error','-ss',pos,'-i',str(f),'-frames:v','1',str(file)],check=True)
vid=next(s for s in probe['streams'] if s['codec_type']=='video');assert (vid['width'],vid['height'],vid['nb_read_frames'])==(1920,1080,'72');assert abs(float(probe['format']['duration'])-3)<1/24
record={'job':j['id'],'timeline':j['snapshot']['timeline']['id'],'provider_calls':0,'origin':'synthetic imported patterns + locally generated solid image; no model generation','duration':probe['format']['duration'],'resolution':[vid['width'],vid['height']],'fps':vid['r_frame_rate'],'frames':vid['nb_read_frames'],'streams':[s['codec_type'] for s in probe['streams']],'audio_correlation':correlation,'audio_rms':math.sqrt(sum(x*x for x in a)/n),'audio_compared_samples':n,'source_audio_offset':.5,'captions':j['snapshot']['subtitles'],'files':{x.name:{'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in out.iterdir()}}
(base/'output-verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in record.items() if k not in ['files','captions']})
