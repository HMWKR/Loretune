"""Mac raster backend for platform-neutral motion scenes; trusted code only."""
from pathlib import Path
import hashlib,json,os,platform,shutil,subprocess,tempfile,time
from copy import deepcopy
import motion_scene,guided
from renderer import Cancelled

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'native/motion_frame_renderer.swift'
FONT=Path('/System/Library/Fonts/AppleSDGothicNeo.ttc')

def font_manifest():
 if platform.system()!='Darwin' or not FONT.is_file() or not Path('/usr/bin/swiftc').is_file() or not shutil.which('ffmpeg'):raise ValueError('이 모션 렌더러는 현재 Mac/CoreText 환경에서만 지원됩니다.')
 return dict(backend='aethon-coretext-v1',font='AppleSDGothicNeo-Regular',font_sha256=hashlib.sha256(FONT.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),os=platform.mac_ver()[0],color_space='sRGB')

def helper(root):
 manifest=font_manifest();folder=Path(root)/'motion-runtime'/guided.fingerprint(manifest);folder.mkdir(parents=True,exist_ok=True)
 binary=folder/'frame-renderer';record=folder/'binary.json'
 if binary.exists() and record.exists():
  if hashlib.sha256(binary.read_bytes()).hexdigest()!=json.loads(record.read_text())['sha256']:raise ValueError('로컬 렌더러 파일 검증 실패')
  return binary
 staging=folder/('build-'+str(os.getpid()))
 result=subprocess.run(['/usr/bin/swiftc','-module-cache-path','/tmp/aethon-motion-module-cache',str(SOURCE),'-o',str(staging)],capture_output=True,timeout=90)
 if result.returncode:raise ValueError('설치된 Swift로 모션 렌더러를 컴파일하지 못했습니다.')
 staging.replace(binary);record.write_text(json.dumps(dict(sha256=hashlib.sha256(binary.read_bytes()).hexdigest())))
 return binary

def frame(scene,index,destination,root,*,validate_only=False):
 payload=motion_scene.frame_state(scene,index,all_layers=validate_only)
 raw=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
 if len(raw)>100000:raise ValueError('frame data too large')
 result=subprocess.run([str(helper(root)),'validate' if validate_only else 'png',str(destination)],input=raw,capture_output=True,timeout=10)
 if result.returncode:raise ValueError('한글 glyph·텍스트 상자·모션 프레임을 확인하세요. 자동 폰트 대체 없음')
 return json.loads(result.stdout)

def validate_text(scene,root):return frame(scene,0,'unused',root,validate_only=True)

def render(scene,destination,root,progress,cancelled,parts):
 motion_scene.validate(scene);validate_text(scene,root);deadline=time.monotonic()+180;size=0
 for i in range(scene['frame_count']):
  if cancelled():raise Cancelled('모션 렌더를 취소했습니다.')
  if time.monotonic()>deadline:raise ValueError('모션 렌더 시간 한도 초과')
  png=parts/f'frame-{i:03d}.png';frame(scene,i,png,root);size+=png.stat().st_size
  if size>128*1024*1024:raise ValueError('모션 임시 출력 크기 한도 초과')
  progress(round((i+1)/scene['frame_count']*80))
 cmd=[shutil.which('ffmpeg'),'-nostdin','-v','error','-y','-framerate','24','-i',str(parts/'frame-%03d.png'),'-frames:v',str(scene['frame_count']),'-an','-c:v','libx264','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(destination)]
 with (parts/'encoder.log').open('wb') as errors:
  process=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=errors)
  try:
   while process.poll() is None:
    if cancelled():raise Cancelled('모션 렌더를 취소했습니다.')
    if time.monotonic()>deadline:raise ValueError('모션 렌더 시간 한도 초과')
    time.sleep(.05)
   if process.returncode:raise ValueError('모션 인코딩 실패')
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(2)
    except subprocess.TimeoutExpired:process.kill();process.wait()
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(destination)],timeout=20))
 streams=data['streams'];video=streams[0]
 if len(streams)!=1 or video.get('codec_type')!='video' or (video['width'],video['height'])!=(1920,1080) or video['r_frame_rate']!='24/1' or int(video['nb_read_frames'])!=scene['frame_count'] or abs(float(data['format']['duration'])-scene['frame_count']/24)>1/24:raise ValueError('모션 출력 프레임 검증 실패')
 progress(95);return dict(width=1920,height=1080,fps=24,frames=scene['frame_count'],duration=scene['frame_count']/24,kind='local-motion-candidate',final_output_approved=False)

def process(store,job,read,update):
 # Reuses the jobs claim/cancel/restart lifecycle. Candidate publication is separate from delivery.
 from loretune import Studio
 parts=store.root/'exports'/('parts-'+job['id']);parts.mkdir(exist_ok=True)
 published_new=None;committed=False
 try:
  if font_manifest()!=job['motion']['font']:raise ValueError('승인 후 폰트·렌더러가 변경됐습니다.')
  if guided.fingerprint(job['motion']['scene'])!=job['motion']['scene_hash'] or job['motion']['approval']['scene_hash']!=job['motion']['scene_hash']:raise ValueError('모션 승인 내용이 변경됐습니다.')
  with store.connect() as c:
   p=json.loads(c.execute('SELECT body FROM state').fetchone()[0])['projects'][job['song']]
   if p.get('archived') or motion_scene.context(p,job['shot'])!=job['motion']['context']:raise ValueError('승인 모션 문맥이 변경됐습니다.')
  staging=parts/'motion.mp4';scene=job['motion']['scene']
  verified=render(scene,staging,store.root,lambda n:update(progress=n),lambda:read()['cancel_requested'],parts)
  if read()['cancel_requested']:raise Cancelled('모션 렌더를 취소했습니다.')
  # Existing content-addressed verified asset service; incomplete files never become Takes.
  with store.connect() as c:
   c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job['id'],)).fetchone()[0])
   if latest['cancel_requested']:raise Cancelled('모션 렌더를 취소했습니다.')
   revision,body=c.execute('SELECT revision,body FROM state').fetchone();saved=json.loads(body);p=saved['projects'][job['song']]
   if p.get('archived') or production_shot_id(p,job['shot'])!=job['shot_id'] or motion_scene.context(p,job['shot'])!=job['motion']['context']:raise ValueError('등록 대상 모션 문맥이 변경됐습니다.')
   raw=staging.read_bytes();destination=store.root/'assets'/(hashlib.sha256(raw).hexdigest()+'.mp4');existed=destination.exists()
   asset,metadata=store.save_media(raw,'.mp4','video',expected_duration=scene['frame_count']/24,expected_dimensions=(1920,1080))
   if not existed:published_new=asset
   studio=Studio();studio.projects=saved['projects'];studio.canon=saved['canon'];shot=p['shots'][job['shot']]
   take=studio.attach_take(job['song'],job['shot'],str(asset),reason='모션 버전 '+str(job['motion']['id'])+' · 로컬 렌더 후보',expected_revision=shot['revision'])
   shot['takes'][-1].update(metadata=metadata,rights='사용권 미확인',filename='motion-v'+str(job['motion']['id'])+'.mp4',provenance=dict(kind='local-motion',motion_revision=job['motion']['id'],scene_hash=job['motion']['scene_hash'],font=job['motion']['font'],source=job['motion']['source'],job=job['id']))
   latest.update(status='completed',progress=100,take=take,download='/assets/'+asset.name,sha256=shot['takes'][-1]['sha256'],verified=verified,finished=time.time(),revision=latest.get('revision',1)+1)
   c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(saved)))
   c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(latest),job['id']))
  committed=True
 except Cancelled as exc:update(status='cancelled',error=str(exc),finished=time.time())
 except Exception as exc:update(status='failed',error=str(exc),finished=time.time())
 finally:
  if published_new is not None and not committed:
   # Remove only our newly published, unreferenced file; never a prior asset.
   with store.connect() as c:
    c.execute('BEGIN IMMEDIATE');body=c.execute('SELECT body FROM state').fetchone()[0]
    jobs=''.join(row[0] for row in c.execute('SELECT body FROM jobs'))
    if str(published_new) not in body and published_new.name not in jobs:published_new.unlink(missing_ok=True)
  shutil.rmtree(parts,ignore_errors=True)

def production_shot_id(p,name):return __import__('production_context').shot_id(p,name)
