import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

import app
import scene_assets
import scene_project
import scene_renderer
from scene_asset_fixtures import glb_parts, jpeg, pack_glb, textured_glb
from test_scene_contract import sample


def two_material_glb():
    """Two cube primitive/material groups: checker PNG and an independent JPEG."""
    document,binary=glb_parts(textured_glb())
    document['accessors'][3]['count']=18
    second=deepcopy(document['accessors'][3]);second['byteOffset']=36
    document['accessors'].append(second)
    original=document['meshes'][0]['primitives'][0]
    other=deepcopy(original);other.update(indices=4,material=1)
    document['meshes'][0]['primitives'].append(other)
    offset=(len(binary)+3)//4*4;image=jpeg();binary=binary+b'\0'*(offset-len(binary))+image
    document['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(image)))
    document['images'].append(dict(bufferView=len(document['bufferViews'])-1,mimeType='image/jpeg'))
    document['textures'].append(dict(source=1))
    document['materials'].append(dict(pbrMetallicRoughness=dict(baseColorTexture=dict(index=1),metallicFactor=0,roughnessFactor=0.65)))
    document['buffers'][0]['byteLength']=len(binary)
    return pack_glb(document,binary)


@unittest.skipUnless(all(os.environ.get(k) for k in ('LORETUNE_3D_IMAGE','LORETUNE_3D_BLENDER','LORETUNE_3D_BLENDER_SHA256','LORETUNE_3D_DOCKER_SOCKET')),'trusted local Blender test environment not configured')
class SceneAssetRealRendererTest(unittest.TestCase):
    def config(self):
        renderer=scene_renderer.RendererConfig(os.environ['LORETUNE_3D_IMAGE'],Path(os.environ['LORETUNE_3D_BLENDER']),os.environ['LORETUNE_3D_BLENDER_SHA256'],180,Path(os.environ['LORETUNE_3D_DOCKER_SOCKET']))
        return dict(renderer=renderer,quota_bytes=scene_project.RESERVATION_BYTES*4,tree_sha256=scene_project.tree_manifest(renderer.blender_root))

    def test_actual_http_texture_import_render_edit_and_source_rights(self):
        with tempfile.TemporaryDirectory(prefix='scene-asset-real-') as folder:
            http=app.server(Path(folder)/'data',0,scene_configuration=self.config());thread=Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{http.server_port}'
                def state():
                    with urlopen(base+'/api/state') as response:return json.load(response)
                def post(action,**data):
                    current=state();payload=dict(action=action,data=data,revision=current['revision'],request_id=uuid.uuid4().hex)
                    request=Request(base+'/api/action',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
                    with urlopen(request) as response:return json.load(response)
                post('project',name='Asset',era='default',story=0);post('shot',song='Asset',shot='shot',description='self-authored texture cube')
                original_glb=two_material_glb();self.assertEqual(scene_assets.validate_glb(original_glb)['image_count'],2)
                asset=post('scene_asset_import',song='Asset',filename='texture.glb',content=base64.b64encode(original_glb).decode(),rights='직접 제작한 합성 fixture')['scene_asset']
                ref={k:asset[k] for k in ('id','sha256','profile')}
                scene=sample();scene['schema_version']=2;scene['width']=scene['height']=192
                obj=scene['objects'][0];obj.pop('color');obj.update(kind='mesh',asset=ref)
                import production_context
                shot_id=production_context.shot_id(state()['projects']['Asset'],'shot')
                proposed=post('scene_create',song='Asset',shot_id=shot_id,scene=scene)['scene']
                post('scene_review',song='Asset',scene_proposal_id=proposed['proposal_id'],decision='approved')
                record=state()['projects']['Asset']['scenes_3d'][0];grant=record['versions'][-1]['approval']['id']
                first=post('scene_render',song='Asset',scene_id=record['id'],scene_revision=1,grant_id=grant)['scene']['job_id']
                self.assertTrue(http.store.process_next())
                project=state()['projects']['Asset'];job=next(j for j in project['scene_3d_jobs'] if j['id']==first)
                self.assertEqual(job['status'],'completed',job)
                take=project['shots']['shot']['takes'][0]
                self.assertEqual(take['provenance']['source_assets'],[ref]);self.assertIsNone(project['shots']['shot']['selected'])
                with urlopen(base+job['download']) as response:png=response.read()
                self.assertEqual(hashlib.sha256(png).hexdigest(),job['sha256'])
                path=http.store.root/'assets'/take['filename']
                rgb=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
                pixels=list(zip(rgb[0::3],rgb[1::3],rgb[2::3]))
                self.assertGreater(sum(r>g*1.3 and r>b*1.3 and r>35 for r,g,b in pixels),20,'embedded red texture not visible')
                self.assertGreater(sum(b>r*1.3 and b>g*1.2 and b>35 for r,g,b in pixels),20,'embedded blue texture not visible')
                top=[pixels[y*192+x] for y in range(67,75) for x in range(91,101)]
                channels=[sum(p[i] for p in top)/len(top) for i in range(3)]
                self.assertGreater(channels[0],channels[1]*2,'second material JPEG not visible on the upper face')
                self.assertGreater(channels[0],channels[2]*2,'second material JPEG not visible on the upper face')
                updated=post('scene_propose',song='Asset',scene_id=record['id'],base_revision=1,operations=[dict(target='camera',id='camera',field='position',value=[7,-3,3]),dict(target='object',id='subject',field='position',value=[0.5,0,0]),dict(target='light',id='key',field='energy_w',value=500)])['scene']
                post('scene_review',song='Asset',scene_proposal_id=updated['proposal_id'],decision='approved')
                record=state()['projects']['Asset']['scenes_3d'][0]
                second=post('scene_render',song='Asset',scene_id=record['id'],scene_revision=2,grant_id=record['versions'][-1]['approval']['id'])['scene']['job_id']
                self.assertTrue(http.store.process_next())
                result=next(j for j in state()['projects']['Asset']['scene_3d_jobs'] if j['id']==second)
                self.assertEqual(result['status'],'completed',result);self.assertNotEqual(job['sha256'],result['sha256'])
                self.assertEqual((http.store.root/'model-assets'/(asset['sha256']+'.glb')).read_bytes(),original_glb)
                post('asset_rights',sha256=asset['sha256'],blocked=True,reason='source revoked after local rendering')
                with self.assertRaises(HTTPError) as error:urlopen(base+job['download'])
                self.assertEqual(error.exception.code,403);error.exception.close()
                # Marker/dimension admission is not a JPEG decoder. A header
                # without quantization/Huffman data must fail inside Blender,
                # rather than publishing a pink or missing-texture substitute.
                document,binary=glb_parts(textured_glb())
                sof=b'\x08\x00\x08\x00\x08\x01\x01\x11\x00'
                sos=b'\x01\x01\x00\x00'
                damaged=b'\xff\xd8\xff\xc0'+struct.pack('>H',len(sof)+2)+sof+b'\xff\xda'+struct.pack('>H',len(sos)+2)+sos+b'\xff\xd9'
                offset=(len(binary)+3)//4*4;binary=binary+b'\0'*(offset-len(binary))+damaged
                view=document['images'][0]['bufferView'];document['bufferViews'][view]={'buffer':0,'byteOffset':offset,'byteLength':len(damaged)}
                document['images'][0]['mimeType']='image/jpeg';document['buffers'][0]['byteLength']=len(binary)
                corrupt=pack_glb(document,binary);self.assertEqual(scene_assets.validate_glb(corrupt)['image_count'],1)
                bad_asset=post('scene_asset_import',song='Asset',filename='corrupt.glb',content=base64.b64encode(corrupt).decode(),rights='직접 제작한 손상 경계 fixture')['scene_asset']
                post('shot',song='Asset',shot='corrupt',description='must not publish broken embedded JPEG')
                bad_scene=sample();bad_scene['schema_version']=2;bad_scene['objects'][0].pop('color');bad_scene['objects'][0].update(kind='mesh',asset={k:bad_asset[k] for k in ('id','sha256','profile')})
                proposal=post('scene_create',song='Asset',shot_id=production_context.shot_id(state()['projects']['Asset'],'corrupt'),scene=bad_scene)['scene']
                post('scene_review',song='Asset',scene_proposal_id=proposal['proposal_id'],decision='approved')
                bad_record=next(r for r in state()['projects']['Asset']['scenes_3d'] if r['id']==proposal['scene_id'])
                bad_job=post('scene_render',song='Asset',scene_id=bad_record['id'],scene_revision=1,grant_id=bad_record['versions'][-1]['approval']['id'])['scene']['job_id']
                self.assertTrue(http.store.process_next())
                bad_result=next(j for j in state()['projects']['Asset']['scene_3d_jobs'] if j['id']==bad_job)
                self.assertEqual(bad_result['status'],'failed');self.assertIsNone(bad_result['download'])
                self.assertEqual(state()['projects']['Asset']['shots']['corrupt']['takes'],[])
                evidence=os.environ.get('LORETUNE_3D_ASSET_EVIDENCE')
                if evidence:
                    destination=Path(evidence);destination.mkdir(parents=True,exist_ok=True)
                    (destination/'textured-first.png').write_bytes(png)
                    with (http.store.root/'assets'/next(t['filename'] for t in state()['projects']['Asset']['shots']['shot']['takes'] if t['sha256']==result['sha256'])).open('rb') as stream:(destination/'textured-edited.png').write_bytes(stream.read())
                    (destination/'result.json').write_text(json.dumps(dict(asset=ref,first=job,edited=result,source_rights_blocked=True,real_provider_calls=0),ensure_ascii=False,indent=2)+'\n')
            finally:http.shutdown();http.server_close();thread.join(5)
