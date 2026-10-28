"""Actual loopback requests, native composition, downloads and backup restore."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from threading import Thread
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request,urlopen
import uuid

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import app,backup,editing,motion_renderer,production_context
from tests.test_motion import scene

OUT=Path(__file__).parent
folder=Path(tempfile.mkdtemp(prefix='loretune-overlay-http-'))
data=folder/'data';http=app.server(data,0)
Thread(target=http.serve_forever,daemon=True).start()
stop,workers=app.start_workers(http.store)
origin=f'http://127.0.0.1:{http.server_port}'
trace=[]

def read(path):
    with urlopen(origin+path,timeout=45) as response:return response.status,response.read()

def state():
    return json.loads(read('/api/state')[1])

def action(action_name,**payload):
    current=state()
    if action_name!='project':payload.setdefault('song','actual overlay')
    body=dict(action=action_name,data=payload,revision=current['revision'],request_id=uuid.uuid4().hex)
    request=Request(origin+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
    started=time.monotonic()
    try:
        with urlopen(request,timeout=45) as response:code=response.status;result=json.loads(response.read())
    except HTTPError as error:
        code=error.code;result=json.loads(error.read());error.close()
    trace.append(dict(action=action_name,request_id=body['request_id'],revision=body['revision'],http_status=code,
                      elapsed=time.monotonic()-started,result=result))
    return code,result

def call(action_name,**payload):
    code,result=action(action_name,**payload)
    if code!=200:raise AssertionError((action_name,code,result))
    return result

def preview(version,clip,frame,name):
    query=urlencode(dict(song='actual overlay',timeline_revision=version,clip_index=clip,frame=frame))
    started=time.monotonic();code,raw=read('/api/timeline-frame?'+query)
    assert code==200 and raw.startswith(b'\x89PNG')
    (OUT/name).write_bytes(raw)
    trace.append(dict(action='saved-frame-preview',timeline_revision=version,clip_index=clip,frame=frame,
                      http_status=code,bytes=len(raw),elapsed=time.monotonic()-started,sha256=hashlib.sha256(raw).hexdigest()))

def wait_job(identifier):
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        job=next(x for x in state()['jobs'] if x['id']==identifier)
        if job['status'] not in {'queued','running'}:
            assert job['status']=='completed',job.get('error')
            return job
        time.sleep(.1)
    raise TimeoutError('Actual local render did not complete')

try:
    sources={}
    for filename,args in [
        ('blue.png',['-f','lavfi','-i','color=c=0x204080:s=640x360','-frames:v','1']),
        ('video.mp4',['-f','lavfi','-i','testsrc2=s=640x360:r=24:d=3','-an','-c:v','libx264','-pix_fmt','yuv420p']),
        ('music.wav',['-f','lavfi','-i','sine=frequency=440:duration=5:sample_rate=48000']),
    ]:
        path=folder/filename
        subprocess.run(['ffmpeg','-nostdin','-v','error','-y',*args,str(path)],check=True)
        sources[filename]=path
    call('project',name='actual overlay',era='default',story=0)
    call('audio',filename='music.wav',content=base64.b64encode(sources['music.wav'].read_bytes()).decode(),rights='directly authored 440Hz fixture')
    call('shot',shot='base',description='synthetic photograph/video background')
    for filename in ['blue.png','video.mp4']:
        p=state()['projects']['actual overlay']
        call('take',shot='base',shot_revision=p['shots']['base']['revision'],filename=filename,
             content=base64.b64encode(sources[filename].read_bytes()).decode(),reason='direct synthetic media',rights='directly authored fixture')
    p=state()['projects']['actual overlay']
    call('select',shot='base',take=2,shot_revision=p['shots']['base']['revision'])
    composition=scene();composition['layers']=composition['layers'][:2]
    composition['layers'][0].update(text='음악 위에\n겹치는 타이포',height=240)
    composition['layers'][0]['keyframes']=[dict(frame=0,x=160,y=160,opacity=.5,easing='linear'),dict(frame=72,x=240,y=160,opacity=.8,easing='linear')]
    proposal=call('motion_propose',shot_id=production_context.shot_id(p,'base'),base_motion_revision=0,scene=composition)['motion']['proposal_id']
    call('motion_review',proposal_id=proposal,decision='approved')
    p=state()['projects']['actual overlay'];original=p['shots']['base']['motion_versions'][0]
    timeline=dict(clips=[dict(shot='base',take=take,duration=1.5,trim=0,
                       motion_overlay=dict(shot='base',motion_revision=1,start=.25,end=1.25,offset_x=offset,offset_y=0))
                       for take,offset in [(2,0),(1,320)]],audio=1,audio_offset=0,
                       subtitles=[dict(start=.2,end=2.8,text='음원 · 영상 · 사진 · 한글 타이포')],profile='landscape')
    call('timeline',timeline=timeline)
    before_revision=state()['revision'];preview(1,0,18,'actual-before.png')
    assert state()['revision']==before_revision and not state()['jobs']
    for take in [1,2]:call('review_take',shot='base',take=take,decision='approved',reason='synthetic media checked')
    call('approve_timeline');quote=call('estimate_render')['estimate'];first=call('render_job',estimate=quote)['job'];job1=wait_job(first)
    code,raw=read(job1['download']);assert code==200 and hashlib.sha256(raw).hexdigest()==job1['sha256'];(OUT/'actual-v1.mp4').write_bytes(raw)
    timeline['clips'][0]['motion_overlay'].update(start=.5,end=1.5,offset_x=480,offset_y=120)
    call('timeline',timeline=timeline);assert action('render_job')[0]==400
    preview(2,0,18,'actual-after.png')
    call('approve_timeline');second=call('render_job')['job'];job2=wait_job(second)
    code,raw=read(job2['download']);assert code==200 and hashlib.sha256(raw).hexdigest()==job2['sha256'];(OUT/'actual-v2.mp4').write_bytes(raw)
    manifest=json.loads(read('/exports/'+second+'.json')[1]);assert len(manifest['motion_overlays'])==2
    current=state();assert current['projects']['actual overlay']['shots']['base']['motion_versions'][0]==original
    source_sha={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in sources.items()}
finally:
    stop.set();http.shutdown();http.server_close()
    for worker in workers:worker.join(3)

saved=backup.create(data,folder/'backup');restored=backup.restore(saved,folder/'restored')
reopened=app.Store(restored).state();reopened_jobs={x['id']:x for x in reopened['jobs']}
for identifier in [first,second]:
    assert hashlib.sha256((restored/'exports'/(identifier+'.mp4')).read_bytes()).hexdigest()==reopened_jobs[identifier]['sha256']
assert reopened['projects']['actual overlay']['timeline_head']==2
decoded=[]
for name in ['actual-v1.mp4','actual-v2.mp4']:
    path=OUT/name
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
    subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(path),'-f','null','-'],check=True)
    decoded.append(dict(path=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),duration=metadata['format']['duration'],streams=[s['codec_type'] for s in metadata['streams']],decoded=True))
report=dict(recorded_at=datetime.now(timezone.utc).isoformat(),origin=origin,folder=str(folder),
            fixtures='self-authored synthetic music/photo/video; no real creator media',actual_provider_calls=0,
            configured_model=None,worker_helper='app.start_workers',worker_count=len(workers),trace=trace,
            first_job=job1,second_job=job2,source_sha256=source_sha,
            source_motion_preserved=True,preview_has_no_state_or_job_side_effect=True,
            final_media=decoded,backup_and_restore=dict(backup=str(saved),restored=str(restored),
            output_hashes_match=True,timeline_head=2),limitations=['Not real model output, browser UI recording or user acceptance'])
(OUT/'http-media-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(result='PASS',artifacts=decoded,trace_events=len(trace),folder=str(folder)),ensure_ascii=False))
