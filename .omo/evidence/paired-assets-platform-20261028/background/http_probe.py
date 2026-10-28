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
 if mode=='legacy':
  post('project',name='A',era='default',story=0);r,p=create('complete');grant=r['versions'][-1]['approval']['id'];j=post('scene_render',song='A',scene_id=r['id'],scene_revision=1,grant_id=grant)['scene']['job_id'];assert http.store.process_next()
  job=next(x for x in state()['projects']['A']['scene_3d_jobs'] if x['id']==j);assert job['status']=='completed';png=(http.store.root/'assets'/Path(job['download']).name).read_bytes();(P/'legacy-approved.png').write_bytes(png)
  queued,qp=create('queued');qj=post('scene_render',song='A',scene_id=queued['id'],scene_revision=1,grant_id=queued['versions'][-1]['approval']['id'])['scene']['job_id'];draft,dp=create('rejected','rejected')
  receipt=dict(pid=os.getpid(),scene_module=str(scene_project.__file__),renderer_module=str(scene_renderer.__file__),completed=job,queued=qj,complete_record=r,rejected_proposal=dp,old_png_sha256=hashlib.sha256(png).hexdigest(),state=state())
  # Session token is not evidence; remove it from the persisted state.
  receipt['state'].pop('token',None);(P/'legacy-http.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
 else:
  old=json.loads((P/'legacy-http.json').read_text());r=record('complete');assert r['versions'][-1]['requires_review'] is True
  denied=deny('scene_render',song='A',scene_id=r['id'],scene_revision=1,grant_id=r['versions'][-1]['approval']['id'])
  review_denied=deny('scene_review',song='A',scene_proposal_id=old['complete_record']['proposals'][0]['id'],decision='approved')
  assert http.store.process_next();project=state()['projects']['A'];q=next(x for x in project['scene_3d_jobs'] if x['id']==old['queued']);assert q['status']=='failed';assert not project['shots']['queued']['takes'];assert not q['download']
  with urlopen(base+old['completed']['download']) as response:assert hashlib.sha256(response.read()).hexdigest()==old['old_png_sha256']
  proposal=post('scene_restore',song='A',scene_id=r['id'],base_revision=1,version=1)['scene'];post('scene_review',song='A',scene_proposal_id=proposal['proposal_id'],decision='approved');r=record('complete');assert not r['versions'][-1]['requires_review']
  j=post('scene_render',song='A',scene_id=r['id'],scene_revision=2,grant_id=r['versions'][-1]['approval']['id'])['scene']['job_id'];assert http.store.process_next();job=next(x for x in state()['projects']['A']['scene_3d_jobs'] if x['id']==j);assert job['status']=='completed';png=(http.store.root/'assets'/Path(job['download']).name).read_bytes();(P/'new-approved.png').write_bytes(png);assert hashlib.sha256(png).hexdigest()!=old['old_png_sha256']
  draft=record('rejected');assert draft['proposals'][-1]['requires_review'];fresh=post('scene_replace_draft',song='A',scene_id=draft['id'],scene_proposal_id=draft['proposals'][-1]['id'],base_revision=0,scene=draft['proposals'][-1]['scene'])['scene'];post('scene_review',song='A',scene_proposal_id=fresh['proposal_id'],decision='approved');assert not record('rejected')['versions'][-1]['requires_review']
  receipt=dict(pid=os.getpid(),renderer_module=str(scene_renderer.__file__),renderer_fingerprint=scene_renderer.renderer_fingerprint(),old_render_denied=denied,old_review_denied=review_denied,old_queued=q,old_png_unchanged=True,new_job=job,restored_scene=record('complete'),rejected_draft_recovered=True,distinct_process=old['pid']!=os.getpid())
  (P/'new-http.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
finally:http.shutdown();thread.join(5);http.server_close()
