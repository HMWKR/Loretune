import base64
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

import app
import backup
import scene_assets
import scene_project
import scene_renderer
import scene_spec
from scene_asset_fixtures import textured_glb
from test_scene_contract import sample
import test_scene_workflow as workflow


class SceneAssetContractTest(unittest.TestCase):
    def test_v1_hash_and_compiler_stay_primitive_and_mesh_change_is_typed(self):
        value=sample()
        digest=hashlib.sha256(json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.assertEqual(scene_spec.fingerprint(value),digest)
        self.assertNotIn(b'import_scene.gltf',scene_renderer.compile_scene(value))
        ref=dict(id='a'*32,sha256='b'*64,profile=scene_assets.PROFILE)
        proposal=scene_spec.propose_changes(value,[dict(target='object',id='subject',field='asset',value=ref),dict(target='camera',id='camera',field='lens_mm',value=70)],base_revision=1,current_revision=1,allowed_fields=[('object','subject','asset'),('camera','camera','lens_mm')])
        mesh=proposal['scene']['objects'][0]
        self.assertEqual(proposal['scene']['schema_version'],2)
        self.assertEqual(mesh,dict(id='subject',kind='mesh',asset=ref,position=[0,0,0],rotation_degrees=[0,0,0],scale=[1,1,1]))
        self.assertEqual(value['objects'][0]['kind'],'cube')
        self.assertEqual(scene_spec.asset_references(proposal['scene']),[ref])
        self.assertIn(b'import_scene.gltf',scene_renderer.compile_scene(proposal['scene']))
        compiled=scene_renderer.compile_scene(proposal['scene']);compile(compiled,'trusted-scene','exec')
        with self.assertRaises(ValueError):scene_spec.validate(dict(proposal['scene'],schema_version=1))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class SceneAssetWorkflowTest(unittest.TestCase):
    # Reuse the HTTP fixture without inheriting and duplicating its tests.
    setUp=workflow.SceneWorkflowTest.setUp
    close_server=workflow.SceneWorkflowTest.close_server
    state=workflow.SceneWorkflowTest.state
    post=workflow.SceneWorkflowTest.post
    post_conversation=workflow.SceneWorkflowTest.post_conversation
    shot_id=workflow.SceneWorkflowTest.shot_id
    create_approved=workflow.SceneWorkflowTest.create_approved
    enqueue=workflow.SceneWorkflowTest.enqueue
    fake_render=workflow.SceneWorkflowTest.fake_render
    def asset(self,conversation=None,rights='직접 제작한 합성 3D 자산'):
        values=dict(song='A',filename='테스트 모델.glb',content=base64.b64encode(textured_glb()).decode(),rights=rights)
        result=self.post_conversation(conversation,'scene_asset_import',**values) if conversation else self.post('scene_asset_import',**values)
        return result['scene_asset']

    def mesh(self,asset):
        value=sample();value['schema_version']=2
        obj=value['objects'][0];obj.pop('color');obj.update(kind='mesh',asset={k:asset[k] for k in ('id','sha256','profile')})
        return value

    def approved_mesh(self):
        asset=self.asset();result=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=self.mesh(asset))['scene']
        self.post('scene_review',song='A',scene_proposal_id=result['proposal_id'],decision='approved')
        record=self.state()['projects']['A']['scenes_3d'][0]
        return asset,record['id'],record['versions'][-1]['approval']['id']

    def fake_asset_render(self,scene,config,publish_root,*,request_id,cancelled,assets):
        self.assertFalse(cancelled());self.assertEqual([{k:a[k] for k in ('id','sha256','profile')} for a in assets],scene_spec.asset_references(scene))
        for asset in assets:self.assertEqual(hashlib.sha256(Path(asset['path']).read_bytes()).hexdigest(),asset['sha256'])
        receipt=self.fake_render(scene,config,publish_root,request_id=request_id,cancelled=cancelled)
        receipt['assets']=scene_spec.asset_references(scene);return receipt

    def expect_error(self,action,code=400,**data):
        with self.assertRaises(HTTPError) as error:self.post(action,**data)
        self.assertEqual(error.exception.code,code);error.exception.close()

    def test_import_is_private_scoped_and_preserves_original_bytes(self):
        asset=self.asset();self.assertEqual(asset['sha256'],hashlib.sha256(textured_glb()).hexdigest())
        self.assertEqual(asset['metadata']['triangle_count'],12)
        self.assertEqual(self.asset()['id'],asset['id'])
        public=self.state()['projects']['A']['scene_3d_assets'];self.assertEqual(len(public),1)
        self.assertNotIn(str(self.http.store.root),json.dumps(public))
        path=self.http.store.root/'model-assets'/(asset['sha256']+'.glb');self.assertEqual(path.read_bytes(),textured_glb())
        with self.assertRaises(HTTPError) as error:urlopen(self.base+'/model-assets/'+path.name)
        self.assertEqual(error.exception.code,404);error.exception.close()
        other=self.post('conversation_create',song='A',title='다른 대화')['conversation']['id']
        self.assertEqual(self.state(other)['projects']['A']['scene_3d_assets'],[])
        with self.assertRaises(HTTPError) as error:self.post_conversation(other,'scene_create',song='A',shot_id=self.shot_id(),scene=self.mesh(asset))
        self.assertEqual(error.exception.code,400);error.exception.close()

    def test_asset_and_camera_changes_share_one_proposal_and_approval(self):
        sid,grant=self.create_approved();asset=self.asset();ref={k:asset[k] for k in ('id','sha256','profile')}
        result=self.post('scene_propose',song='A',scene_id=sid,base_revision=1,operations=[dict(target='object',id='subject',field='asset',value=ref),dict(target='camera',id='camera',field='lens_mm',value=70),dict(target='object',id='subject',field='position',value=[1,0,0])])['scene']
        record=self.state()['projects']['A']['scenes_3d'][0];self.assertEqual(record['head'],1)
        proposal=record['proposals'][-1];self.assertEqual(len(proposal['changes']),3)
        self.assertEqual(record['versions'][0]['scene']['schema_version'],1)
        self.post('scene_review',song='A',scene_proposal_id=result['proposal_id'],decision='approved')
        record=self.state()['projects']['A']['scenes_3d'][0];version=record['versions'][-1]
        self.assertEqual(version['scene']['objects'][0]['asset'],ref);self.assertEqual(version['scene']['camera']['lens_mm'],70)
        self.expect_error('scene_render',song='A',scene_id=sid,scene_revision=2,grant_id=grant)
        job=self.enqueue(sid,version['approval']['id'],2)
        with patch.object(scene_renderer,'render',side_effect=self.fake_asset_render):self.assertTrue(self.http.store.process_next())
        take=self.state()['projects']['A']['shots']['shot']['takes'][0]
        self.assertEqual(take['provenance']['source_assets'],[ref]);self.assertIsNone(self.state()['projects']['A']['shots']['shot']['selected'])
        self.assertEqual(take['rights'],'사용권 미확인');self.assertTrue(job)

    def test_original_rights_revocation_blocks_derived_png_and_new_render(self):
        asset,sid,grant=self.approved_mesh();job=self.enqueue(sid,grant)
        with patch.object(scene_renderer,'render',side_effect=self.fake_asset_render):self.http.store.process_next()
        take=self.state()['projects']['A']['shots']['shot']['takes'][0]
        with urlopen(self.base+'/assets/'+take['filename']) as response:self.assertEqual(response.status,200)
        self.post('asset_rights',sha256=asset['sha256'],blocked=True,reason='원본 사용 중지')
        self.assertTrue(self.state()['asset_rights'][take['sha256']]['blocked'])
        self.assertTrue(self.state()['projects']['A']['scene_3d_assets'][0]['blocked'])
        with self.assertRaises(HTTPError) as error:urlopen(self.base+'/assets/'+take['filename'])
        self.assertEqual(error.exception.code,403);error.exception.close()
        self.expect_error('scene_render',song='A',scene_id=sid,scene_revision=1,grant_id=grant)
        self.post('asset_rights',sha256=asset['sha256'],blocked=False,reason='다시 확인')
        with urlopen(self.base+'/assets/'+take['filename']) as response:self.assertEqual(response.status,200)

    def test_original_mesh_rights_reach_actual_music_video_export(self):
        asset,sid,grant=self.approved_mesh();self.enqueue(sid,grant)
        with patch.object(scene_renderer,'render',side_effect=self.fake_asset_render):self.http.store.process_next()
        shot=self.state()['projects']['A']['shots']['shot'];take=shot['takes'][0]
        self.post('declare_take_rights',song='A',shot='shot',take=take['id'],sha256=take['sha256'],shot_revision=shot['revision'],evidence='직접 제작한 합성 GLB와 렌더')
        shot=self.state()['projects']['A']['shots']['shot']
        self.post('select',song='A',shot='shot',take=take['id'],shot_revision=shot['revision'])
        self.post('review_take',song='A',shot='shot',take=take['id'],decision='approved',reason='합성 프레임 검토')
        audio=Path(self.tmp.name)/'synthetic-audio.wav'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','sine=frequency=440:duration=1','-y',str(audio)],check=True)
        self.post('audio',song='A',filename=audio.name,content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 제작 합성 음원')
        timeline=dict(clips=[dict(shot='shot',take=take['id'],trim=0,duration=1)],audio=1,audio_offset=0,subtitles=[dict(start=0,end=1,text='합성 GLB · 음악영상')],profile='preview')
        self.post('timeline',song='A',timeline=timeline);self.post('approve_timeline',song='A')
        job=self.post('render_job',song='A')['job'];self.assertTrue(self.http.store.process_next())
        result=next(j for j in self.state()['jobs'] if j['id']==job);self.assertEqual(result['status'],'completed',result)
        path=self.http.store.root/'exports'/(job+'.mp4')
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))
        self.assertCountEqual([s['codec_type'] for s in probe['streams']],['video','audio','subtitle'])
        with urlopen(self.base+result['download']) as response:self.assertEqual(response.status,200)
        affected=self.post('asset_rights',sha256=asset['sha256'],blocked=True,reason='원본 mesh 권리 철회')
        self.assertIn(job,affected['affected_jobs'])
        self.assertFalse(self.state()['projects']['A']['preflight']['ready'])
        with self.assertRaises(HTTPError) as error:urlopen(self.base+result['download'])
        self.assertEqual(error.exception.code,403);error.exception.close()
        self.post('asset_rights',sha256=asset['sha256'],blocked=False,reason='원본 권리 재확인')
        with urlopen(self.base+result['download']) as response:self.assertEqual(response.status,200)

    def test_private_file_change_and_unknown_rights_prevent_approval_or_render(self):
        unknown=self.asset(rights='사용권 미확인');proposal=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=self.mesh(unknown))['scene']
        self.expect_error('scene_review',song='A',scene_proposal_id=proposal['proposal_id'],decision='approved')
        claimed=self.asset();self.assertNotEqual(claimed['id'],unknown['id'])
        first=self.state()['projects']['A']['scenes_3d'][0]
        replaced=self.post('scene_replace_draft',song='A',scene_id=first['id'],scene_proposal_id=proposal['proposal_id'],base_revision=0,scene=self.mesh(claimed))['scene']
        self.post('scene_review',song='A',scene_proposal_id=replaced['proposal_id'],decision='approved')
        path=self.http.store.root/'model-assets'/(claimed['sha256']+'.glb');path.chmod(0o600);path.write_bytes(b'changed')
        record=self.state()['projects']['A']['scenes_3d'][0]
        self.expect_error('scene_render',song='A',scene_id=record['id'],scene_revision=1,grant_id=record['versions'][-1]['approval']['id'])
        self.assertEqual(self.state()['projects']['A']['scene_3d_jobs'],[])

    def test_missing_derivative_edge_is_not_treated_as_unrestricted(self):
        asset,sid,grant=self.approved_mesh();self.enqueue(sid,grant)
        with patch.object(scene_renderer,'render',side_effect=self.fake_asset_render):self.http.store.process_next()
        take=self.state()['projects']['A']['shots']['shot']['takes'][0]
        with self.http.store.connect() as c:c.execute('DELETE FROM scene_asset_dependencies WHERE derived_sha=?',(take['sha256'],))
        # Revocation still records the source decision even when a link is damaged.
        self.post('asset_rights',sha256=asset['sha256'],blocked=True,reason='원본 권리 철회와 손상 연결')
        with urlopen(self.base+'/api/state') as response:state=json.load(response)
        self.assertTrue(state['asset_rights'][asset['sha256']]['blocked'])
        self.assertTrue(state['asset_rights'][take['sha256']]['blocked'])
        with self.assertRaises(HTTPError) as error:urlopen(self.base+'/assets/'+take['filename'])
        self.assertEqual(error.exception.code,403);error.exception.close()

    def test_rights_revocation_cancels_queued_source_and_releases_reservation(self):
        asset,sid,grant=self.approved_mesh();job=self.enqueue(sid,grant)
        result=self.post('asset_rights',sha256=asset['sha256'],blocked=True,reason='원본 사용 중지')
        self.assertIn(job,result['affected_jobs']);self.assertEqual(self.state()['projects']['A']['scene_3d_jobs'][0]['status'],'cancelled')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations WHERE job=?',(job,)).fetchone()[0],0)

    def test_cancel_during_asset_render_never_attaches_take(self):
        asset,sid,grant=self.approved_mesh();job=self.enqueue(sid,grant)
        def cancel(scene,config,publish,**options):
            receipt=self.fake_asset_render(scene,config,publish,**options)
            self.post('cancel_job',song='A',job=job)
            return receipt
        with patch.object(scene_renderer,'render',side_effect=cancel):self.http.store.process_next()
        project=self.state()['projects']['A'];self.assertEqual(project['scene_3d_jobs'][0]['status'],'cancelled');self.assertEqual(project['shots']['shot']['takes'],[])

    def test_original_change_during_render_never_publishes_a_take(self):
        asset,sid,grant=self.approved_mesh();job=self.enqueue(sid,grant)
        def changed(scene,config,publish,**options):
            receipt=self.fake_asset_render(scene,config,publish,**options)
            source=self.http.store.root/'model-assets'/(asset['sha256']+'.glb');source.chmod(0o600);source.write_bytes(b'changed after claim')
            return receipt
        with patch.object(scene_renderer,'render',side_effect=changed):self.http.store.process_next()
        project=self.state()['projects']['A'];self.assertEqual(project['scene_3d_jobs'][0]['status'],'failed');self.assertEqual(project['shots']['shot']['takes'],[])
        self.assertIn('내장 텍스처',project['scene_3d_jobs'][0]['error'])
        self.assertEqual(list((self.http.store.root/'assets').glob('scene-*.png')),[])

    def test_import_rejects_unsupported_files_and_is_idempotent(self):
        bad=base64.b64encode(b'not a GLB').decode()
        for filename in ('../source.glb','source.fbx','source.glb'):
            self.expect_error('scene_asset_import',song='A',filename=filename,content=bad,rights='직접 제작')
        state=self.state();payload=dict(action='scene_asset_import',data=dict(song='A',filename='source.glb',content=base64.b64encode(textured_glb()).decode(),rights='직접 제작'),revision=state['revision'],request_id=uuid.uuid4().hex)
        raw=json.dumps(payload).encode();headers={'Content-Type':'application/json','X-Loretune-Token':state['token']}
        def send():
            with urlopen(Request(self.base+'/api/action',data=raw,headers=headers)) as response:return json.load(response)
        self.assertEqual(send(),send());self.assertEqual(len(self.state()['projects']['A']['scene_3d_assets']),1)

    def test_import_diagnostics_preserve_existing_assets_and_selected_take(self):
        from scene_asset_fixtures import glb_parts, pack_glb
        from test_scene_vertex_colors import color_glb
        from test_scene_asset_diagnostics import COMPLEXITY_ERROR, MALFORMED_ERROR
        raw=color_glb()
        asset=self.post('scene_asset_import',song='A',filename='colors.glb',content=base64.b64encode(raw).decode(),rights='직접 제작')['scene_asset']
        self.assertEqual(asset['profile'],scene_assets.COLOR_PROFILE)
        self.assertEqual((self.http.store.root/'model-assets'/(asset['sha256']+'.glb')).read_bytes(),raw)
        shot=self.state()['projects']['A']['shots']['shot']
        self.post('take',song='A',shot='shot',shot_revision=shot['revision'],filename='original.png',content=base64.b64encode(self.png).decode(),reason='기존 선택 보존 검사',rights='직접 제작')
        shot=self.state()['projects']['A']['shots']['shot']
        self.post('select',song='A',shot='shot',take=shot['takes'][0]['id'],shot_revision=shot['revision'])
        before=self.state()
        self.assertIsNotNone(before['projects']['A']['shots']['shot']['selected'])
        def files():
            return {str(p.relative_to(self.http.store.root)):hashlib.sha256(p.read_bytes()).hexdigest()
                    for folder in ('model-assets','assets') for p in (self.http.store.root/folder).rglob('*') if p.is_file()}
        before_files=files()
        document,binary=glb_parts(raw)
        for count,message in ((True,MALFORMED_ERROR),(777780,COMPLEXITY_ERROR)):
            with self.subTest(count=count):
                document['accessors'][0]['count']=count
                with self.assertRaises(HTTPError) as failure:
                    self.post('scene_asset_import',song='A',filename='rejected.glb',content=base64.b64encode(pack_glb(document,binary)).decode(),rights='직접 제작')
                with failure.exception as response:
                    self.assertEqual(response.code,400)
                    self.assertEqual(json.load(response)['error'],'입력을 확인하세요: '+message)
                after=self.state()
                self.assertEqual(after['projects'],before['projects'])
                self.assertEqual(after['revision'],before['revision'])
                self.assertEqual(files(),before_files)

    def test_backup_restore_reopens_relative_assets_and_preserves_dependency_rights(self):
        asset,sid,grant=self.approved_mesh();job=self.enqueue(sid,grant)
        with patch.object(scene_renderer,'render',side_effect=self.fake_asset_render):self.http.store.process_next()
        source=self.http.store.root;self.close_server();self.close_server=lambda:None
        with tempfile.TemporaryDirectory() as folder:
            archive=backup.create(source,Path(folder)/'backup');restored=backup.restore(archive,Path(folder)/'restored')
            reopened=app.Store(restored)
            with reopened.connect() as c:
                values=scene_project.public_assets(c,reopened,'A',__import__('chat_sessions').default_id(reopened.state()['projects']['A']))
                self.assertEqual(values[0]['id'],asset['id'])
                scene=scene_project._row(c,'scene_records',sid)['versions'][-1]['scene']
                inputs=scene_project.resolve_assets(c,reopened,__import__('contracts').project_id(reopened.workspace_id,'A'),__import__('chat_sessions').default_id(reopened.state()['projects']['A']),scene)
                self.assertTrue(inputs[0]['path'].startswith(str(restored)))
                c.execute('INSERT INTO asset_rights VALUES (?,?,?,?)',(asset['sha256'],1,'source revoked',0))
            take=reopened.state()['projects']['A']['shots']['shot']['takes'][0]
            with reopened.connect() as c:
                with self.assertRaises(ValueError):reopened.check_rights(c,[take['sha256']])
