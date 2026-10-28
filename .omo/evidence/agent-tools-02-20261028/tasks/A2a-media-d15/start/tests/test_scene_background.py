"""World background rendering and loaded renderer approval boundary."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import scene_renderer
from test_scene_contract import sample
import test_scene_workflow as workflow


class BackgroundContractTest(unittest.TestCase):
    def test_background_is_assigned_to_active_shader(self):
        compiled=scene_renderer.compile_scene(sample()).decode()
        self.assertIn("nodes['Background'].inputs['Color'].default_value",compiled)
        self.assertNotIn('use_nodes = False',compiled)

    def test_fingerprint_uses_loaded_code_not_current_disk(self):
        source=Path(scene_renderer.__file__).read_text()
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'loaded_renderer.py';file.write_text(source)
            def load():
                spec=importlib.util.spec_from_file_location('background_loaded_renderer',file)
                module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
            try:
                first=load();before=first.renderer_fingerprint();compiled=first.compile_scene(sample())
                file.write_text(source.replace('scene.cycles.samples = 4','scene.cycles.samples = 17'))
                self.assertEqual(first.renderer_fingerprint(),before)
                self.assertEqual(first.compile_scene(sample()),compiled)
                second=load();self.assertNotEqual(second.renderer_fingerprint(),before)
                self.assertNotEqual(second.compile_scene(sample()),compiled)
            finally:sys.modules.pop('background_loaded_renderer',None)


class BackgroundApprovalHTTPTest(unittest.TestCase):
    setUp=workflow.SceneWorkflowTest.setUp
    close_server=workflow.SceneWorkflowTest.close_server
    state=workflow.SceneWorkflowTest.state
    post=workflow.SceneWorkflowTest.post
    shot_id=workflow.SceneWorkflowTest.shot_id
    create_approved=workflow.SceneWorkflowTest.create_approved
    enqueue=workflow.SceneWorkflowTest.enqueue
    fake_render=workflow.SceneWorkflowTest.fake_render

    def test_previous_renderer_approval_and_queued_job_require_explicit_reapproval(self):
        with patch.object(scene_renderer,'_RENDERER_FINGERPRINT','0'*64):
            sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        record=self.state()['projects']['A']['scenes_3d'][0]
        self.assertTrue(record['versions'][-1]['requires_review'])
        with self.assertRaises(HTTPError) as e:self.enqueue(sid,grant)
        self.assertEqual(e.exception.code,400);e.exception.close()
        with patch.object(scene_renderer,'render',side_effect=AssertionError('stale renderer must not run')):self.assertTrue(self.http.store.process_next())
        self.assertEqual(self.state()['projects']['A']['shots']['shot']['takes'],[])
        proposed=self.post('scene_restore',song='A',scene_id=sid,base_revision=1,version=1)['scene']
        self.post('scene_review',song='A',scene_proposal_id=proposed['proposal_id'],decision='approved')
        record=self.state()['projects']['A']['scenes_3d'][0];self.assertFalse(record['versions'][-1]['requires_review'])
        self.enqueue(sid,record['versions'][-1]['approval']['id'],revision=2)
        with patch.object(scene_renderer,'render',side_effect=self.fake_render):self.assertTrue(self.http.store.process_next())
        self.assertEqual(len(self.state()['projects']['A']['shots']['shot']['takes']),1)


@unittest.skipUnless(all(os.environ.get(k) for k in ('LORETUNE_3D_IMAGE','LORETUNE_3D_BLENDER','LORETUNE_3D_BLENDER_SHA256','LORETUNE_3D_DOCKER_SOCKET')),'pinned local Blender environment required')
class BackgroundNativeTest(unittest.TestCase):
    def test_background_changes_actual_pixels_without_color_management_override(self):
        import scene_project
        import uuid
        config=scene_renderer.RendererConfig(os.environ['LORETUNE_3D_IMAGE'],Path(os.environ['LORETUNE_3D_BLENDER']),os.environ['LORETUNE_3D_BLENDER_SHA256'],180,Path(os.environ['LORETUNE_3D_DOCKER_SOCKET']))
        if os.environ.get('LORETUNE_3D_TREE_SHA256'):
            self.assertEqual(scene_project.tree_manifest(config.blender_root),os.environ['LORETUNE_3D_TREE_SHA256'])
        with tempfile.TemporaryDirectory(prefix='scene-background-native-') as folder:
            publish=Path(folder);rows=[]
            for color in ([0,0,0],[1,1,1],[.1,.3,.8]):
                scene=sample();scene.update(width=192,height=192,background=color)
                compiled=scene_renderer.compile_scene(scene)
                for setting in (b'view_transform',b'exposure',b'gamma'):self.assertNotIn(setting,compiled)
                receipt=scene_renderer.render(scene,config,publish,request_id=uuid.uuid4().hex)
                rgb=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',receipt['path'],'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
                rows.append(dict(color=color,corner=list(rgb[:3]),pixel_sha256=hashlib.sha256(rgb).hexdigest()))
            self.assertEqual(rows[0]['corner'],[0,0,0]);self.assertTrue(all(v>150 for v in rows[1]['corner']))
            self.assertGreater(rows[2]['corner'][2],rows[2]['corner'][0]+30)
            self.assertEqual(len({r['pixel_sha256'] for r in rows}),3)
            print('BACKGROUND_NATIVE_OBSERVATIONS='+json.dumps(rows))
