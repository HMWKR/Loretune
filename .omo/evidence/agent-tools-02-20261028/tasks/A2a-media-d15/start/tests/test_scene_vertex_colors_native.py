"""Actual immutable TripoSR artifacts through the existing isolated native workflow.

Optional local artifacts are not bundled test fixtures or commercial-quality proof.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen
import uuid

import app
import production_context
import scene_project
import scene_renderer
from test_scene_contract import sample

SOURCES=(('.omo/evidence/triposr-cpu-artifact-20261028/cube-resolution256-original.glb','307b92e8cb61be726d6de12d9059dc54254be956d13bae3f66700b60dccd1cfe'),('.omo/evidence/triposr-cpu-artifact-20261028/chair-attempt-1/chair-resolution256-original.glb','2f589816941840ed59a0b5f8661d7d40e6a76edf1c07cdaaf371431772ecb4b3'))
READY=all(os.environ.get(k) for k in ('LORETUNE_3D_IMAGE','LORETUNE_3D_BLENDER','LORETUNE_3D_BLENDER_SHA256','LORETUNE_3D_DOCKER_SOCKET')) and all(Path(p).is_file() for p,_ in SOURCES)

@unittest.skipUnless(READY,'pinned local Blender and actual TripoSR artifacts required')
class VertexColorNativeTest(unittest.TestCase):
    def test_actual_assets_import_approve_render_edit_take_and_revoke(self):
        renderer=scene_renderer.RendererConfig(os.environ['LORETUNE_3D_IMAGE'],Path(os.environ['LORETUNE_3D_BLENDER']),os.environ['LORETUNE_3D_BLENDER_SHA256'],180,Path(os.environ['LORETUNE_3D_DOCKER_SOCKET']))
        tree=scene_project.tree_manifest(renderer.blender_root)
        if os.environ.get('LORETUNE_3D_TREE_SHA256'):self.assertEqual(tree,os.environ['LORETUNE_3D_TREE_SHA256'])
        with tempfile.TemporaryDirectory(prefix='vertex-color-native-') as folder:
            evidence=Path(os.environ.get('SCENE_VERTEX_EVIDENCE',str(Path(folder)/'evidence')))
            evidence.mkdir(parents=True,exist_ok=True)
            self.assertFalse(any(evidence.iterdir()),'native evidence output must be empty; preserve prior observations')
            receipts=[]
            http=app.server(Path(folder)/'data',0,scene_configuration=dict(renderer=renderer,quota_bytes=scene_project.RESERVATION_BYTES*8,tree_sha256=tree))
            thread=Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{http.server_port}'
                def state():
                    with urlopen(base+'/api/state') as r:return json.load(r)
                def post(action,**data):
                    current=state();payload=dict(action=action,data=data,revision=current['revision'],request_id=uuid.uuid4().hex)
                    request=Request(base+'/api/action',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
                    try:
                        with urlopen(request) as r:return json.load(r)
                    except HTTPError as error:
                        body=error.read().decode();print('HTTP_FAILURE',action,error.code,body);raise
                for index,(source,sha) in enumerate(SOURCES):
                    name='Color'+str(index);raw=Path(source).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
                    post('project',name=name,era='default',story=0);post('shot',song=name,shot='shot',description='self-authored input actual model output')
                    asset=post('scene_asset_import',song=name,filename=Path(source).name,content=base64.b64encode(raw).decode(),rights='직접 제작한 입력의 로컬 모델 실험 결과')['scene_asset']
                    self.assertEqual(asset['profile'],'gltf2-static-pbr-color-v2');ref={k:asset[k] for k in ('id','sha256','profile')}
                    scene=sample();scene.update(schema_version=2,width=192,height=192)
                    scene['objects'][0].pop('color');scene['objects'][0].update(kind='mesh',asset=ref,scale=[3,3,3])
                    shot_id=production_context.shot_id(state()['projects'][name],'shot')
                    proposed=post('scene_create',song=name,shot_id=shot_id,scene=scene)['scene']
                    post('scene_review',song=name,scene_proposal_id=proposed['proposal_id'],decision='approved')
                    jobs=[];grants=[]
                    for revision in (1,2):
                        if revision==2:
                            proposal=post('scene_propose',song=name,scene_id=record['id'],base_revision=1,operations=[dict(target='camera',id='camera',field='position',value=[7,-3,3]),dict(target='light',id='key',field='energy_w',value=500)])['scene']
                            post('scene_review',song=name,scene_proposal_id=proposal['proposal_id'],decision='approved')
                            with self.assertRaises(HTTPError) as stale:post('scene_render',song=name,scene_id=record['id'],scene_revision=1,grant_id=grants[0])
                            self.assertIn(stale.exception.code,(400,409));stale.exception.close()
                        record=state()['projects'][name]['scenes_3d'][0];grant=record['versions'][-1]['approval']['id'];grants.append(grant)
                        result=post('scene_render',song=name,scene_id=record['id'],scene_revision=revision,grant_id=grant)['scene']
                        self.assertTrue(http.store.process_next());project=state()['projects'][name]
                        job=next(j for j in project['scene_3d_jobs'] if j['id']==result['job_id']);self.assertEqual(job['status'],'completed',job)
                        with urlopen(base+job['download']) as response:png=response.read()
                        self.assertEqual(hashlib.sha256(png).hexdigest(),job['sha256']);(evidence/f'{index}-revision-{revision}.png').write_bytes(png)
                        self.assertEqual(project['shots']['shot']['takes'][-1]['provenance']['source_assets'],[ref]);jobs.append(job)
                    self.assertNotEqual(jobs[0]['sha256'],jobs[1]['sha256'])
                    self.assertEqual((http.store.root/'model-assets'/(sha+'.glb')).read_bytes(),raw)
                    post('asset_rights',sha256=sha,blocked=True,reason='source revocation verification')
                    for job in jobs:
                        with self.assertRaises(HTTPError) as denied:urlopen(base+job['download'])
                        self.assertEqual(denied.exception.code,403);denied.exception.close()
                    receipts.append(dict(source=source,sha256=sha,asset=asset,scene=record,jobs=jobs,original_bytes_unchanged=True,stale_approval_rejected=True,revoked_downloads=403))
                    (evidence/'receipt.json').write_text(json.dumps(dict(tree_sha256=tree,scenarios=receipts),ensure_ascii=False,indent=2))
            finally:http.shutdown();thread.join(5);http.server_close()
