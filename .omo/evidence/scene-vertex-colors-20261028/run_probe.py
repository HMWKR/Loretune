import json,os,sys,subprocess,shutil
from pathlib import Path
sys.path.insert(0,'tests');from test_scene_vertex_colors import color_glb
p=Path('.omo/evidence/scene-vertex-colors-20261028');inputs=p/'probe-input';inputs.mkdir(exist_ok=True)
for comp in (5121,5123,5126):
 maximum={5121:255,5123:65535,5126:1}[comp];v=[(.12345,.314159,.87654,1)]*24 if comp==5126 else [(int(maximum*.12345),int(maximum*.314159),int(maximum*.87654),maximum)]*24
 (inputs/f'fixture-{comp}.glb').write_bytes(color_glb(comp,normalized=None if comp==5126 else True,values=v))
for name,path in [('actual-cube','.omo/evidence/triposr-cpu-artifact-20261028/cube-resolution256-original.glb'),('actual-chair','.omo/evidence/triposr-cpu-artifact-20261028/chair-attempt-1/chair-resolution256-original.glb')]:shutil.copyfile(path,inputs/(name+'.glb'))
shutil.copyfile(p/'color_probe.py',inputs/'probe.py')
c=json.load(open('.omo/evidence/general-model-schedule-20261028/regression/preflight.json'))['native']['environment']
command=['docker','--host','unix://'+c['LORETUNE_3D_DOCKER_SOCKET'],'run','--rm','--platform=linux/amd64','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=256','--memory=2g','--cpus=2','--tmpfs','/tmp:rw,noexec,nosuid,size=128m','--mount','type=bind,src='+c['LORETUNE_3D_BLENDER']+',dst=/opt/blender,readonly','--mount','type=bind,src='+str(inputs.resolve())+',dst=/input,readonly','--entrypoint','/opt/blender/blender',c['LORETUNE_3D_IMAGE'],'--background','--factory-startup','--disable-autoexec','--python','/input/probe.py']
r=subprocess.run(command,capture_output=True,text=True,timeout=180);(p/'color-probe.log').write_text(r.stdout+r.stderr);(p/'color-probe-command.json').write_text(json.dumps(dict(command=command,exit_code=r.returncode),indent=2))
for line in r.stdout.splitlines():
 if line.startswith('COLOR_PROBE_JSON='):(p/'color-probe.json').write_text(json.dumps(json.loads(line.split('=',1)[1]),indent=2))
print('exit',r.returncode);print(r.stdout[-1000:]);sys.exit(r.returncode)
