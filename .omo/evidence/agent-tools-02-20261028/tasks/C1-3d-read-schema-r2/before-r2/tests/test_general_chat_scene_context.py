"""S6: read-only 'scene-status' context query; no grants, asset paths or scene bodies."""
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from app import Store
import chat_sessions
import model_selection
import production_context
import production_tools
import scene_project
import scene_renderer
from scene_asset_fixtures import textured_glb
from test_scene_contract import sample


def record(name,value):
    folder=os.environ.get('SCENE_STATUS_EVIDENCE')
    if folder:
        target=Path(folder);target.mkdir(parents=True,exist_ok=True)
        (target/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


class SceneStatusContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name)
        self.call('project',name='A',era='default',story=0)
        self.call('shot',song='A',shot='shot',description='synthetic 3D')
        self.call('shot',song='A',shot='second',description='synthetic 3D second')
        self.other=self.call('conversation_create',song='A',title='private sibling')['conversation']['id']

    def raw(self,name='A'):
        with self.store.connect() as c:return json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'][name]

    def project(self,cid=None):
        p=self.raw();return chat_sessions.scoped(p,cid) if cid else p

    def call(self,action,conversation=None,**data):
        with self.store.connect() as c:revision=c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        request=dict(action=action,data=data,revision=revision,request_id=uuid.uuid4().hex)
        if conversation:
            p=self.raw();request.update(conversation_id=conversation,conversation_revision=chat_sessions.resolve(p,conversation)['revision'],shared_version=chat_sessions.shared_fingerprint(p))
        return self.store.mutate(request)

    def shot_id(self,shot='shot'):return production_context.shot_id(self.raw(),shot)

    def approved(self,scene=None,conversation=None,shot='shot'):
        created=self.call('scene_create',conversation,song='A',shot_id=self.shot_id(shot),scene=scene or sample())['scene']
        self.call('scene_review',conversation,song='A',scene_proposal_id=created['proposal_id'],decision='approved')
        return created

    def mesh_asset(self):
        asset=self.call('scene_asset_import',song='A',filename='synthetic.glb',content=base64.b64encode(textured_glb()).decode(),rights='직접 제작')['scene_asset']
        value=sample();value['schema_version']=2
        obj=value['objects'][0];obj.pop('color');obj.update(kind='mesh',asset={k:asset[k] for k in ('id','sha256','profile')})
        return asset,value

    def read(self,cid=None,query='scene-status'):
        with self.store.connect() as c:return production_context.read(c,self.store,self.project(cid),'A',query)

    def full(self,cid=None):
        with self.store.connect() as c:return scene_project.public(c,self.store,self.project(cid),'A',cid or chat_sessions.default_id(self.raw()))

    def test_current_conversation_only_with_heads_approval_and_pending_proposals(self):
        mine=self.approved()
        proposal=self.call('scene_propose',song='A',scene_id=mine['scene_id'],base_revision=1,operations=[dict(target='camera',id='camera',field='lens_mm',value=35)])['scene']
        theirs=self.call('scene_create',self.other,song='A',shot_id=self.shot_id('second'),scene=sample())['scene']
        value=self.read()
        self.assertEqual(set(value),{'scene_status'});status=value['scene_status']
        self.assertEqual(status['scope'],'current-project-current-conversation')
        self.assertEqual(status['scenes_3d'],[dict(scene_id=mine['scene_id'],shot_id=self.shot_id(),head=1,approval_status='recorded',requires_review=False,
            pending_proposals=[dict(proposal_id=proposal['proposal_id'],base_revision=1,status='proposed')])])
        self.assertEqual(status['connection'],dict(available=False,external_transmission=False))
        sibling=self.read(self.other)['scene_status']['scenes_3d']
        self.assertEqual(sibling,[dict(scene_id=theirs['scene_id'],shot_id=self.shot_id('second'),head=0,approval_status='none',requires_review=False,
            pending_proposals=[dict(proposal_id=theirs['proposal_id'],base_revision=0,status='proposed')])])
        self.assertNotIn(theirs['scene_id'],json.dumps(value));self.assertNotIn(mine['scene_id'],json.dumps(sibling))
        record('scope',dict(default=status,sibling=sibling))

    def test_held_rejected_and_stale_context_are_explicit(self):
        mine=self.approved()
        held=self.call('scene_propose',song='A',scene_id=mine['scene_id'],base_revision=1,operations=[dict(target='light',id='key',field='energy_w',value=400)])['scene']
        self.call('scene_review',song='A',scene_proposal_id=held['proposal_id'],decision='held')
        rejected=self.call('scene_propose',song='A',scene_id=mine['scene_id'],base_revision=1,operations=[dict(target='light',id='key',field='size_m',value=2)])['scene']
        self.call('scene_review',song='A',scene_proposal_id=rejected['proposal_id'],decision='rejected')
        scene=self.read()['scene_status']['scenes_3d'][0]
        self.assertEqual(scene['pending_proposals'],[dict(proposal_id=held['proposal_id'],base_revision=1,status='held')])
        with self.store.connect() as c:
            saved=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);saved['projects']['A']['shots']['shot']['description']='changed context'
            c.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(saved),))
        scene=self.read()['scene_status']['scenes_3d'][0]
        self.assertEqual((scene['approval_status'],scene['requires_review']),('stale_context',True))

    def test_no_grant_ids_asset_references_paths_or_scene_bodies(self):
        asset,value=self.mesh_asset();mine=self.approved(value)
        self.call('scene_propose',song='A',scene_id=mine['scene_id'],base_revision=1,operations=[dict(target='object',id='subject',field='position',value=[1,0,0])])
        full=self.full()[0];grant=full['versions'][-1]['approval']['id']
        self.assertIn(grant,json.dumps(full));self.assertIn(asset['sha256'],json.dumps(full))
        text=json.dumps(self.read(),ensure_ascii=False)
        for secret in (grant,asset['id'],asset['sha256'],str(self.store.root),'model-assets','.glb','/assets/','/exports/','"grant_id"','"approval"','"versions"','"scene"','lens_mm','"camera"','"objects"','scene_hash','"context"','"path"'):
            self.assertNotIn(secret,text,secret)
        self.assertEqual(json.loads(text)['scene_status']['scenes_3d'][0]['approval_status'],'recorded')
        record('redaction',json.loads(text))

    def test_read_is_byte_preserving_and_never_loads_runtime_or_subprocess(self):
        self.approved()
        p=self.project();before=deepcopy(p);fingerprint=model_selection.snapshot(p)
        blocked=AssertionError('no runtime work during a context read')
        with self.store.connect() as c, patch('subprocess.run',side_effect=blocked), patch('subprocess.Popen',side_effect=blocked), \
             patch.object(scene_project,'runtime_binding',side_effect=blocked), patch.object(scene_project,'tree_manifest',side_effect=blocked), \
             patch.object(scene_renderer,'render',side_effect=blocked), patch.object(scene_renderer,'reconcile',side_effect=blocked):
            dump_before='\n'.join(c.iterdump());changes=c.total_changes;db_before=hashlib.sha256(self.store.db.read_bytes()).hexdigest()
            first=production_context.read(c,self.store,p,'A','scene-status')
            self.assertEqual(c.total_changes,changes);self.assertEqual('\n'.join(c.iterdump()),dump_before)
        self.assertEqual(hashlib.sha256(self.store.db.read_bytes()).hexdigest(),db_before)
        self.assertEqual(p,before);self.assertEqual(model_selection.snapshot(p),fingerprint)
        reopened=Store(self.tmp.name)
        with reopened.connect() as c:second=production_context.read(c,reopened,p,'A','scene-status')
        self.assertEqual(first['scene_status']['scenes_3d'],second['scene_status']['scenes_3d'])
        record('read-preservation',dict(before_db_sha256=db_before,after_db_sha256=hashlib.sha256(self.store.db.read_bytes()).hexdigest()))

    def test_connection_projects_only_availability(self):
        with patch.object(scene_project,'capability',return_value=dict(available=True,mode='configured-preflight-required',reason='PRIVATE_REASON',external_transmission=False)):
            value=self.read()['scene_status']['connection']
        self.assertEqual(value,dict(available=True,external_transmission=False))

    def test_existing_queries_unchanged_and_new_query_is_discoverable(self):
        self.approved()
        self.assertEqual(set(self.read(query='work-status')),{'work_status'})
        normal=self.read(query='current project facts')
        self.assertNotIn('scene_status',normal);self.assertIn('timeline',normal);self.assertIn('motion_overlay_sources',normal)
        self.assertEqual([x['query'] for x in normal['supported_context_queries']],['work-status','scene-status'])
        production_tools.validate('search_project_context',dict(query='scene-status'))

    def test_result_size_is_bounded_and_recorded(self):
        first=self.approved()
        for i in range(12):
            self.call('scene_propose',song='A',scene_id=first['scene_id'],base_revision=1,operations=[dict(target='camera',id='camera',field='lens_mm',value=20+i)])
        self.approved(shot='second')
        value=self.read();size=len(json.dumps(value,ensure_ascii=False).encode())
        self.assertEqual(len(value['scene_status']['scenes_3d'][0]['pending_proposals']),10)
        self.assertLess(size,4096)
        record('size',dict(bytes=size,scenes=len(value['scene_status']['scenes_3d']),value=value))


if __name__=='__main__':
    unittest.main()
