import os,sys,json,hashlib,subprocess,uuid
from pathlib import Path
sys.path[:0]=['.','tests']
import scene_renderer,scene_project
from test_scene_contract import sample
p=Path('.omo/evidence/paired-assets-platform-20261028/background/fixed-renders').resolve();p.mkdir(exist_ok=True)
c=json.load(open('.omo/evidence/general-model-schedule-20261028/regression/preflight.json'))['native']['environment']
config=scene_renderer.RendererConfig(c['LORETUNE_3D_IMAGE'],Path(c['LORETUNE_3D_BLENDER']),c['LORETUNE_3D_BLENDER_SHA256'],180,Path(c['LORETUNE_3D_DOCKER_SOCKET']))
assert scene_project.tree_manifest(config.blender_root)==c['LORETUNE_3D_TREE_SHA256']
sources={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ('scene_renderer.py','scene_project.py','scene_assets.py','scene_spec.py','scene-studio.js')};(p/'source-before.json').write_text(json.dumps(sources,indent=2))
cmd=['docker','--host','unix://'+c['LORETUNE_3D_DOCKER_SOCKET'],'run','--rm','--pull=never','--platform=linux/amd64','--network=none','--read-only','--user=65534:65534','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=64','--memory=1536m','--cpus=1','--tmpfs','/tmp:rw,noexec,nosuid,size=64m,mode=1777','--mount','type=bind,src='+str(config.blender_root)+',dst=/opt/blender,readonly','--mount','type=bind,src='+str(p)+',dst=/input,readonly','--entrypoint','/opt/blender/blender',config.image_id,'--background','--factory-startup','--disable-autoexec','--threads','1','--python-exit-code','3','--python','/input/probe.py']
r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);(p/'factory.log').write_text(r.stdout+r.stderr);assert r.returncode==0
factory=json.loads(next(line.split('=',1)[1] for line in r.stdout.splitlines() if line.startswith('WORLD_PROBE_JSON=')));(p/'factory.json').write_text(json.dumps(factory,indent=2))
rows=[]
for name,color in [('black',[0,0,0]),('white',[1,1,1]),('blue',[0.1,0.3,0.8])]:
 s=sample();s.update(width=192,height=192,background=color);(p/(name+'-scene.json')).write_text(json.dumps(s,indent=2));(p/(name+'-compiled.py')).write_bytes(scene_renderer.compile_scene(s))
 receipt=scene_renderer.render(s,config,p,request_id=uuid.uuid4().hex)
 rgb=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',receipt['path'],'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']);corners=[list(rgb[(y*192+x)*3:(y*192+x)*3+3]) for x,y in [(0,0),(191,0),(0,191),(191,191)]]
 rows.append(dict(name=name,background=color,corners=corners,rgb_sha256=hashlib.sha256(rgb).hexdigest(),receipt=receipt));(p/'renders.json').write_text(json.dumps(rows,indent=2))
 assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==sha for f,sha in sources.items())
(p/'execution.json').write_text(json.dumps(dict(factory_command=cmd,environment=c,source_after=sources,unchanged=True),indent=2))
print(json.dumps([dict(name=x['name'],corners=x['corners'],rgb_sha256=x['rgb_sha256']) for x in rows]))
