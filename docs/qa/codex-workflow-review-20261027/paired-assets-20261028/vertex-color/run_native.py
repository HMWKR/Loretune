import os,json,subprocess,sys,hashlib
from pathlib import Path
root=Path.cwd();e=root/'.omo/evidence/scene-vertex-colors-20261028'
p=json.load(open('.omo/evidence/general-model-schedule-20261028/regression/preflight.json'));env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','LC_ALL','LC_CTYPE','TMPDIR')};env.update(p['native']['environment']);env['PYTHONPATH']='tests:.';env['SCENE_VERTEX_EVIDENCE']=str(e/'native')
command=[p['python']['path'],'-m','unittest','test_scene_vertex_colors','test_scene_vertex_colors_native','test_scene_assets','test_scene_asset_workflow','test_scene_asset_render','test_scene_contract','test_scene_ui','-v']
with (e/'native-related.log').open('w') as f:r=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
(e/'native-related-exit.json').write_text(json.dumps(dict(command=command,exit_code=r.returncode,environment=env),indent=2));sys.exit(r.returncode)
