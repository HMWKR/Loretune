import os,json,subprocess,sys,hashlib
from pathlib import Path
p=Path('.omo/evidence/paired-assets-platform-20261028/background')
c=json.load(open('.omo/evidence/general-model-schedule-20261028/regression/preflight.json'))
env={k:v for k,v in os.environ.items() if k in ('HOME','PATH','LANG','LC_ALL','LC_CTYPE','TMPDIR')};env.update(c['native']['environment']);env['PYTHONPATH']='tests:.'
cmd=[c['python']['path'],'-m','unittest','test_scene_background','test_scene_workflow','test_scene_asset_workflow','test_scene_contract','test_scene_ui','test_scene_config','-v']
files=['scene_renderer.py','scene_project.py','scene-studio.js','tests/test_scene_background.py'];before={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files};(p/'source-freeze.json').write_text(json.dumps(before,indent=2))
with (p/'related.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}
(p/'related-exit.json').write_text(json.dumps(dict(command=cmd,exit_code=r.returncode,before=before,after=after,source_unchanged=before==after),indent=2));sys.exit(r.returncode)
