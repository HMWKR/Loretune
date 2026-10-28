"""Run old archived modules and new modules in separate processes against one evidence store."""
import sys,os,importlib.util,json,hashlib,uuid,subprocess
from pathlib import Path
from threading import Thread
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path.cwd();P=ROOT/'.omo/evidence/paired-assets-platform-20261028/background'
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
mode=sys.argv[1]
if mode=='legacy':
 for name in ('scene_renderer','scene_project'):
  spec=importlib.util.spec_from_file_location(name,P/'implementation-before'/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
import app,scene_renderer,scene_project,production_context
from test_scene_contract import sample
c=json.load(open(ROOT/'.omo/evidence/general-model-schedule-20261028/regression/preflight.json'))['native']['environment']
config=scene_renderer.RendererConfig(c['LORETUNE_3D_IMAGE'],Path(c['LORETUNE_3D_BLENDER']),c['LORETUNE_3D_BLENDER_SHA256'],180,Path(c['LORETUNE_3D_DOCKER_SOCKET']))
assert scene_project.tree_manifest(config.blender_root)==c['LORETUNE_3D_TREE_SHA256']
store=P/'http-store'
if mode=='legacy':assert not store.exists()
http=app.server(store,0,scene_configuration=dict(renderer=config,quota_bytes=scene_project.RESERVATION_BYTES*8,tree_sha256=c['LORETUNE_3D_TREE_SHA256']));thread=Thread(target=http.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{http.server_port}'
def state():
 with urlopen(base+'/api/state') as r:return json.load(r)
def post(action,**data):
 s=state();request=Request(base+'/api/action',data=json.dumps(dict(action=action,data=data,revision=s['revision'],request_id=uuid.uuid4().hex)).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':s['token']})
 with urlopen(request) as r:return json.load(r)
def deny(action,**data):
 try:post(action,**data);raise AssertionError('old approval accepted')
 except HTTPError as e:
  body=e.read().decode();assert e.code in (400,409);return dict(status=e.code,body=body)
def record(shot):return next(r for r in state()['projects']['A']['scenes_3d'] if r['shot']==shot)
def create(shot,decision='approved'):
 post('shot',song='A',shot=shot,description='background runtime migration evidence')
 scene=sample();scene.update(width=192,height=192,background=[1,1,1]);shotid=production_context.shot_id(state()['projects']['A'],shot)
 proposal=post('scene_create',song='A',shot_id=shotid,scene=scene)['scene'];post('scene_review',song='A',scene_proposal_id=proposal['proposal_id'],decision=decision);return record(shot),proposal
try:
 before=state()['projects']['A'];r=record('complete');take_count=len(before['shots']['complete']['takes'])
 restored=post('scene_restore',song='A',scene_id=r['id'],base_revision=r['head'],version=r['head'])['scene'];post('scene_review',song='A',scene_proposal_id=restored['proposal_id'],decision='approved');r=record('complete')
 j=post('scene_render',song='A',scene_id=r['id'],scene_revision=r['head'],grant_id=r['versions'][-1]['approval']['id'])['scene']['job_id']
 actual=scene_renderer.render;fingerprint=scene_renderer._RENDERER_FINGERPRINT;captured={}
 def race(*args,**kwargs):
  receipt=actual(*args,**kwargs);captured.update(receipt);scene_renderer._RENDERER_FINGERPRINT='f'*64;return receipt
 scene_renderer.render=race
 try:assert http.store.process_next()
 finally:scene_renderer.render=actual;scene_renderer._RENDERER_FINGERPRINT=fingerprint
 after=state()['projects']['A'];job=next(x for x in after['scene_3d_jobs'] if x['id']==j)
 assert captured and Path(captured['path']).is_file();assert job['status']=='failed';assert job['download'] is None;assert len(after['shots']['complete']['takes'])==take_count
 (P/'publication-race.json').write_text(json.dumps(dict(controlled_test='Fingerprint changed after actual native render returns, before publication; this is an injected race, not proof of code reload',receipt=captured,failed_job=job,takes_before=take_count,takes_after=len(after['shots']['complete']['takes']),private_png_preserved=True),ensure_ascii=False,indent=2))
finally:http.shutdown();thread.join(5);http.server_close()
