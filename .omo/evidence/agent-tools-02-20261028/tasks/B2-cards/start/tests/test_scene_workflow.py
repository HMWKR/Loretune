import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

import app
import scene_project
import scene_renderer
from test_scene_contract import sample


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class SceneWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);install=base/'trusted-install';install.mkdir();(install/'blender').write_bytes(b'synthetic trusted binary')
        self.sock=socket.socket(socket.AF_UNIX);self.sock.bind(str(base/'docker.sock'));self.addCleanup(self.sock.close)
        renderer=scene_renderer.RendererConfig('sha256:'+'a'*64,install,hashlib.sha256(b'synthetic trusted binary').hexdigest(),docker_socket=base/'docker.sock')
        self.configuration=dict(renderer=renderer,quota_bytes=scene_project.RESERVATION_BYTES*2,tree_sha256=scene_project.tree_manifest(install))
        self.mock_configuration=patch.object(scene_renderer,'_configuration',return_value=(install,['docker'],'ffmpeg'));self.mock_configuration.start();self.addCleanup(self.mock_configuration.stop)
        self.http=app.server(base/'data',0,scene_configuration=self.configuration);self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close_server)
        self.base=f'http://127.0.0.1:{self.http.server_port}'
        png=base/'synthetic.png';subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=blue:s=96x96','-frames:v','1',str(png)],check=True)
        self.png=png.read_bytes()
        self.post('project',name='A',era='default',story=0)
        self.post('shot',song='A',shot='shot',description='synthetic 3D')

    def close_server(self):
        self.http.shutdown();self.http.server_close();self.thread.join(5)

    def state(self,conversation=None):
        suffix='?song=A&conversation='+conversation if conversation else ''
        with urlopen(self.base+'/api/state'+suffix) as r:return json.load(r)

    def post(self,action,**data):
        s=self.state();request=dict(action=action,data=data,revision=s['revision'],request_id=uuid.uuid4().hex)
        req=Request(self.base+'/api/action',data=json.dumps(request,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':s['token']})
        with urlopen(req) as r:return json.load(r)

    def post_conversation(self,cid,action,**data):
        s=self.state(cid);active=s['projects']['A']['active_conversation']
        request=dict(action=action,data=data,revision=s['revision'],request_id=uuid.uuid4().hex,conversation_id=cid,conversation_revision=active['revision'],shared_version=active['shared_version'])
        req=Request(self.base+'/api/action',data=json.dumps(request,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':s['token']})
        with urlopen(req) as r:return json.load(r)

    def shot_id(self):
        import production_context
        return production_context.shot_id(self.state()['projects']['A'],'shot')

    def create_approved(self):
        result=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=sample())['scene']
        self.post('scene_review',song='A',scene_proposal_id=result['proposal_id'],decision='approved')
        state=self.state()['projects']['A']['scenes_3d'][0]
        return state['id'],state['versions'][-1]['approval']['id']

    def enqueue(self,scene,grant,revision=1):
        return self.post('scene_render',song='A',scene_id=scene,scene_revision=revision,grant_id=grant)['scene']['job_id']

    def fake_render(self,scene,config,publish_root,*,request_id,cancelled):
        self.assertFalse(cancelled());path=Path(publish_root)/('scene-'+request_id+'.png');path.write_bytes(self.png)
        return dict(path=str(path),request_id=request_id,sha256=hashlib.sha256(self.png).hexdigest(),scene_hash=scene_project.scene_spec.fingerprint(scene),image_id=config.image_id,blender_sha256=config.blender_sha256,kind='local-3d-still',external_calls=0,assets=[],compiler_sha256=hashlib.sha256(scene_renderer.compile_scene(scene)).hexdigest())

    def test_http_create_review_render_commit_download_and_restart(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        self.assertEqual(self.enqueue(sid,grant),job)
        with patch.object(scene_renderer,'render',side_effect=self.fake_render):self.assertTrue(self.http.store.process_next())
        state=self.state();shot=state['projects']['A']['shots']['shot'];take=shot['takes'][0]
        self.assertIsNone(shot['selected']);self.assertEqual(take['rights'],'사용권 미확인');self.assertEqual(take['provenance']['kind'],'local-3d-still')
        self.assertEqual(next(x for x in state['projects']['A']['scene_3d_jobs'] if x['id']==job)['status'],'completed');self.assertEqual(state['jobs'],[])
        with urlopen(self.base+'/assets/'+take['filename']) as r:self.assertEqual(hashlib.sha256(r.read()).hexdigest(),take['sha256'])
        # A change to the private renderer file cannot mutate the committed Take.
        private=self.http.store.root/'scene-private'/('scene-'+job+'.png');private.write_bytes(b'changed private bytes')
        with urlopen(self.base+'/assets/'+take['filename']) as r:self.assertEqual(hashlib.sha256(r.read()).hexdigest(),take['sha256'])
        origin=next(n['source'] for n in state['projects']['A']['lineage']['nodes'] if n['type']=='take')
        self.assertEqual(origin,'local-3d-still')
        reopened=app.Store(self.http.store.root).state()['projects']['A'];self.assertEqual(reopened['shots']['shot']['takes'][0]['sha256'],take['sha256'])
        with self.assertRaises(HTTPError) as error:self.post('cancel_job',song='A',job=job)
        self.assertEqual(error.exception.code,400);error.exception.close()
        (self.http.store.root/'assets'/take['filename']).write_bytes(b'tampered')
        with self.assertRaises(HTTPError) as error:urlopen(self.base+'/assets/'+take['filename'])
        self.assertEqual(error.exception.code,409);error.exception.close()

    def test_cancel_during_render_leaves_no_public_or_take(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        def race(scene,config,publish_root,*,request_id,cancelled):
            self.post('cancel_job',song='A',job=job)
            return self.fake_render(scene,config,publish_root,request_id=request_id,cancelled=lambda:False)
        with patch.object(scene_renderer,'render',side_effect=race):self.http.store.process_next()
        state=self.state();self.assertEqual(state['projects']['A']['shots']['shot']['takes'],[])
        self.assertEqual(next(x for x in state['projects']['A']['scene_3d_jobs'] if x['id']==job)['status'],'cancelled')
        self.assertEqual(list((self.http.store.root/'assets').glob('scene-*.png')),[])

    def test_stale_scene_after_render_and_uncommitted_public_file_blocked(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        orphan=self.http.store.root/'assets'/('scene-'+'a'*64+'.png');orphan.write_bytes(self.png)
        with self.assertRaises(HTTPError) as error:urlopen(self.base+'/assets/'+orphan.name)
        self.assertEqual(error.exception.code,404);error.exception.close()
        def race(scene,config,publish_root,*,request_id,cancelled):
            result=self.post('scene_propose',song='A',scene_id=sid,base_revision=1,operations=[dict(target='camera',id='camera',field='lens_mm',value=60)])['scene']
            self.post('scene_review',song='A',scene_proposal_id=result['proposal_id'],decision='approved')
            return self.fake_render(scene,config,publish_root,request_id=request_id,cancelled=lambda:False)
        with patch.object(scene_renderer,'render',side_effect=race):self.http.store.process_next()
        state=self.state();self.assertEqual(state['projects']['A']['shots']['shot']['takes'],[])
        self.assertEqual(state['projects']['A']['scenes_3d'][0]['head'],2)
        self.assertEqual(next(x for x in state['projects']['A']['scene_3d_jobs'] if x['id']==job)['status'],'failed')

    def test_no_configuration_and_changed_tree_fail_closed(self):
        sid,grant=self.create_approved();self.http.store.scene_configuration=None
        with self.assertRaises(HTTPError) as error:self.enqueue(sid,grant)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.http.store.scene_configuration=self.configuration
        (self.configuration['renderer'].blender_root/'changed').write_text('synthetic drift')
        with self.assertRaises(HTTPError) as error:self.enqueue(sid,grant)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.assertEqual(self.state()['jobs'],[])

    def test_restart_running_keeps_unknown_and_no_resubmit(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        with self.http.store.connect() as c:
            value=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job,)).fetchone()[0]);value['status']='running'
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(value),job))
        reopened=app.Store(self.http.store.root);scene_project.recover(reopened);reopened.recover_jobs()
        result=next(x for x in reopened.state()['projects']['A']['scene_3d_jobs'] if x['id']==job)
        self.assertEqual(result['status'],'outcome_unknown')
        with patch.object(scene_renderer,'render',side_effect=AssertionError('must not resubmit')):self.assertFalse(reopened.process_next())

    def test_ontology_change_during_render_rejects_attachment(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        def race(scene,config,publish_root,*,request_id,cancelled):
            result=self.post('ontology_propose',song='A',ontology_revision=0,kind='character',label='합성',description='설정',evidence='시험')['ontology']
            self.post('ontology_apply',song='A',proposal=result['id'],ontology_revision=0,approved=True)
            return self.fake_render(scene,config,publish_root,request_id=request_id,cancelled=cancelled)
        with patch.object(scene_renderer,'render',side_effect=race):self.http.store.process_next()
        state=self.state();self.assertEqual(state['projects']['A']['shots']['shot']['takes'],[])
        self.assertEqual(next(j for j in state['projects']['A']['scene_3d_jobs'] if j['id']==job)['status'],'failed')

    def test_scene_and_job_are_scoped_to_their_conversation(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        other=self.post('conversation_create',song='A',title='다른 대화')['conversation']['id']
        self.assertEqual(self.state(other)['projects']['A']['scenes_3d'],[])
        with self.assertRaises(HTTPError) as error:self.post_conversation(other,'scene_render',song='A',scene_id=sid,scene_revision=1,grant_id=grant)
        self.assertEqual(error.exception.code,400);error.exception.close()
        with self.assertRaises(HTTPError) as error:self.post_conversation(other,'cancel_job',song='A',job=job)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.assertEqual(next(j for j in self.state()['projects']['A']['scene_3d_jobs'] if j['id']==job)['status'],'queued')

    def test_scene_quota_prevents_additional_queued_jobs_without_changing_approvals(self):
        sid,grant=self.create_approved();self.http.store.scene_configuration['quota_bytes']=scene_project.RESERVATION_BYTES
        self.enqueue(sid,grant)
        result=self.post('scene_propose',song='A',scene_id=sid,base_revision=1,operations=[dict(target='camera',id='camera',field='lens_mm',value=65)])['scene']
        self.post('scene_review',song='A',scene_proposal_id=result['proposal_id'],decision='approved')
        approval=self.state()['projects']['A']['scenes_3d'][0]['versions'][-1]['approval']['id']
        with self.assertRaises(HTTPError) as error:self.enqueue(sid,approval,2)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.assertEqual(len(self.state()['projects']['A']['scene_3d_jobs']),1)

    def test_attachment_failure_removes_only_new_uncommitted_asset(self):
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        preserved=self.http.store.root/'assets'/'existing.txt';preserved.write_bytes(b'keep')
        with patch.object(scene_renderer,'render',side_effect=self.fake_render),patch('loretune.Studio.attach_take',side_effect=ValueError('controlled rollback')):
            self.http.store.process_next()
        state=self.state();self.assertEqual(state['projects']['A']['shots']['shot']['takes'],[])
        self.assertEqual(next(j for j in state['projects']['A']['scene_3d_jobs'] if j['id']==job)['status'],'failed')
        self.assertEqual(list((self.http.store.root/'assets').glob('scene-*.png')),[]);self.assertEqual(preserved.read_bytes(),b'keep')

    def test_duplicate_http_request_has_one_job_and_reservation(self):
        sid,grant=self.create_approved();state=self.state()
        request=dict(action='scene_render',data=dict(song='A',scene_id=sid,scene_revision=1,grant_id=grant),revision=state['revision'],request_id=uuid.uuid4().hex)
        raw=json.dumps(request).encode();headers={'Content-Type':'application/json','X-Loretune-Token':state['token']}
        def send(_):
            with urlopen(Request(self.base+'/api/action',data=raw,headers=headers)) as response:return json.load(response)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(send,range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(len(self.state()['projects']['A']['scene_3d_jobs']),1)
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],1)

    def test_capability_is_secret_free_and_not_a_completed_preflight(self):
        connection=self.state()['projects']['A']['scene_3d_connection']
        self.assertEqual(connection['mode'],'configured-preflight-required');self.assertTrue(connection['available']);self.assertFalse(connection['external_transmission'])
        self.assertNotIn(str(self.configuration['renderer'].blender_root),json.dumps(connection));self.assertNotIn(self.configuration['tree_sha256'],json.dumps(connection))
        self.http.store.scene_configuration=None
        disabled=self.state()['projects']['A']['scene_3d_connection'];self.assertFalse(disabled['available']);self.assertEqual(disabled['mode'],'disconnected')
        self.http.store.scene_configuration={**self.configuration,'tree_sha256':'invalid'}
        self.assertFalse(self.state()['projects']['A']['scene_3d_connection']['available'])

    def test_initial_draft_can_be_replaced_without_approving_and_retry_is_idempotent(self):
        first=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=sample())['scene'];s=self.state()
        modified=sample();modified['camera']['lens_mm']=80
        payload=dict(action='scene_replace_draft',data=dict(song='A',scene_id=first['scene_id'],scene_proposal_id=first['proposal_id'],base_revision=0,scene=modified),revision=s['revision'],request_id=uuid.uuid4().hex)
        raw=json.dumps(payload).encode();headers={'Content-Type':'application/json','X-Loretune-Token':s['token']}
        def send():
            with urlopen(Request(self.base+'/api/action',data=raw,headers=headers)) as response:return json.load(response)
        revised=send();self.assertEqual(revised,send());records=self.state()['projects']['A']['scenes_3d'][0]
        self.assertEqual(records['head'],0);self.assertEqual(len(records['versions']),0);self.assertEqual([p['status'] for p in records['proposals']],['superseded','proposed'])
        with self.assertRaises(HTTPError) as error:self.post('scene_review',song='A',scene_proposal_id=first['proposal_id'],decision='approved')
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.post('scene_review',song='A',scene_proposal_id=revised['scene']['proposal_id'],decision='approved')
        self.assertEqual(self.state()['projects']['A']['scenes_3d'][0]['versions'][0]['scene']['camera']['lens_mm'],80)
        with self.assertRaises(HTTPError) as error:self.post('scene_replace_draft',song='A',scene_id=first['scene_id'],scene_proposal_id=revised['scene']['proposal_id'],base_revision=0,scene=sample())
        self.assertEqual(error.exception.code,409);error.exception.close()

    def test_initial_draft_replacement_rejects_other_conversation_and_bad_input(self):
        first=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=sample())['scene']
        other=self.post('conversation_create',song='A',title='다른 대화')['conversation']['id']
        with self.assertRaises(HTTPError) as error:self.post_conversation(other,'scene_replace_draft',song='A',scene_id=first['scene_id'],scene_proposal_id=first['proposal_id'],base_revision=0,scene=sample())
        self.assertEqual(error.exception.code,400);error.exception.close()
        bad=sample();bad['objects'][0]['path']='/tmp/unauthorized'
        with self.assertRaises(HTTPError) as error:self.post('scene_replace_draft',song='A',scene_id=first['scene_id'],scene_proposal_id=first['proposal_id'],base_revision=0,scene=bad)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.assertEqual(self.state()['projects']['A']['scenes_3d'][0]['proposals'][0]['status'],'proposed')

    def test_initial_draft_replacement_rejects_other_scene_in_same_conversation(self):
        first=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=sample())['scene']
        self.post('shot',song='A',shot='second',description='different scene')
        import production_context
        project=self.state()['projects']['A'];second_shot=production_context.shot_id(project,'second')
        second=self.post('scene_create',song='A',shot_id=second_shot,scene=sample())['scene']
        with self.assertRaises(HTTPError) as error:
            self.post('scene_replace_draft',song='A',scene_id=first['scene_id'],scene_proposal_id=second['proposal_id'],base_revision=0,scene=sample())
        self.assertEqual(error.exception.code,400);error.exception.close()
        records={r['id']:r for r in self.state()['projects']['A']['scenes_3d']}
        self.assertEqual(set(records),{first['scene_id'],second['scene_id']})
        for record in records.values():
            self.assertEqual(record['head'],0);self.assertEqual(record['versions'],[])
            self.assertEqual(len(record['proposals']),1);self.assertEqual(record['proposals'][0]['status'],'proposed')

    def test_non_default_conversation_scene_render_and_projection_are_isolated(self):
        other=self.post('conversation_create',song='A',title='별도 작업')['conversation']['id']
        import production_context
        project=self.state(other)['projects']['A'];shotid=production_context.shot_id(project,'shot')
        scene=self.post_conversation(other,'scene_create',song='A',shot_id=shotid,scene=sample())['scene']
        self.post_conversation(other,'scene_review',song='A',scene_proposal_id=scene['proposal_id'],decision='approved')
        record=self.state(other)['projects']['A']['scenes_3d'][0]
        self.assertEqual(record['shot'],'shot');self.assertEqual(record['shot_id'],shotid)
        approval=record['versions'][-1]['approval']['id']
        with self.http.store.connect() as c:
            raw=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            self.assertEqual(raw['projects']['A']['conversation_owners'][approval],dict(conversation_id=other,kind='scene_grants'))
        with self.assertRaises(HTTPError) as error:self.post('scene_render',song='A',scene_id=scene['scene_id'],scene_revision=1,grant_id=approval)
        self.assertEqual(error.exception.code,400);error.exception.close()
        job=self.post_conversation(other,'scene_render',song='A',scene_id=scene['scene_id'],scene_revision=1,grant_id=approval)['scene']['job_id']
        again=self.post_conversation(other,'scene_render',song='A',scene_id=scene['scene_id'],scene_revision=1,grant_id=approval)['scene']
        self.assertEqual(again['job_id'],job);self.assertTrue(again['existing'])
        with patch.object(scene_renderer,'render',side_effect=self.fake_render):self.assertTrue(self.http.store.process_next())
        owner=self.state(other)['projects']['A'];default=self.state()['projects']['A']
        self.assertEqual(owner['scenes_3d'][0]['head'],1)
        self.assertEqual(next(j for j in owner['scene_3d_jobs'] if j['id']==job)['status'],'completed')
        self.assertEqual(len(owner['shots']['shot']['takes']),1)
        self.assertEqual(owner['shots']['shot']['takes'][0]['conversation_id'],other)
        self.assertEqual(default['scenes_3d'],[]);self.assertEqual(default['scene_3d_jobs'],[])
        self.assertEqual(default['shots']['shot']['takes'],[])
        reopened=app.Store(self.http.store.root).state({'A':other})['projects']['A']
        self.assertEqual(reopened['scene_3d_jobs'][0]['status'],'completed')
        self.assertEqual(reopened['shots']['shot']['takes'][0]['conversation_id'],other)

    def test_non_default_queued_cancel_and_legacy_grant_backfill(self):
        other=self.post('conversation_create',song='A',title='별도 작업')['conversation']['id']
        import production_context
        project=self.state(other)['projects']['A'];shotid=production_context.shot_id(project,'shot')
        scene=self.post_conversation(other,'scene_create',song='A',shot_id=shotid,scene=sample())['scene']
        self.post_conversation(other,'scene_review',song='A',scene_proposal_id=scene['proposal_id'],decision='approved')
        grant=self.state(other)['projects']['A']['scenes_3d'][0]['versions'][-1]['approval']['id']
        # Simulate a version saved before 3D grant ownership was persisted.
        with self.http.store.connect() as c:
            revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();raw=json.loads(body)
            del raw['projects']['A']['conversation_owners'][grant]
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(raw)))
        job=self.post_conversation(other,'scene_render',song='A',scene_id=scene['scene_id'],scene_revision=1,grant_id=grant)['scene']['job_id']
        with self.http.store.connect() as c:
            raw=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            self.assertEqual(raw['projects']['A']['conversation_owners'][grant]['conversation_id'],other)
        self.post_conversation(other,'cancel_job',song='A',job=job)
        self.assertEqual(self.state(other)['projects']['A']['scene_3d_jobs'][0]['status'],'cancelled')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations WHERE job=?',(job,)).fetchone()[0],0)
        reopened=app.Store(self.http.store.root).state({'A':other})['projects']['A']
        self.assertEqual(reopened['scene_3d_jobs'][0]['status'],'cancelled')

    def test_grant_from_another_scene_in_same_conversation_is_rejected(self):
        sid,grant=self.create_approved()
        self.post('shot',song='A',shot='second',description='other scene')
        import production_context
        shotid=production_context.shot_id(self.state()['projects']['A'],'second')
        other=self.post('scene_create',song='A',shot_id=shotid,scene=sample())['scene']
        self.post('scene_review',song='A',scene_proposal_id=other['proposal_id'],decision='approved')
        with self.assertRaises(HTTPError) as error:
            self.post('scene_render',song='A',scene_id=other['scene_id'],scene_revision=1,grant_id=grant)
        self.assertEqual(error.exception.code,400);error.exception.close()
        self.assertEqual(self.state()['projects']['A']['scene_3d_jobs'],[])
        self.assertNotEqual(sid,other['scene_id'])

    def test_conflicting_existing_grant_owner_is_preserved_and_rejected(self):
        sid,grant=self.create_approved()
        with self.http.store.connect() as c:
            revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone();raw=json.loads(body)
            existing=raw['projects']['A']['conversation_owners'][grant]
            existing['kind']='existing-other-grant'
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(raw)))
        with self.assertRaises(HTTPError) as error:self.enqueue(sid,grant)
        self.assertEqual(error.exception.code,400);error.exception.close()
        with self.http.store.connect() as c:
            raw=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            self.assertEqual(raw['projects']['A']['conversation_owners'][grant]['kind'],'existing-other-grant')
            self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],0)

    def test_rejected_initial_draft_can_be_replaced_without_approval(self):
        first=self.post('scene_create',song='A',shot_id=self.shot_id(),scene=sample())['scene']
        self.post('scene_review',song='A',scene_proposal_id=first['proposal_id'],decision='rejected')
        replacement=self.post('scene_replace_draft',song='A',scene_id=first['scene_id'],scene_proposal_id=first['proposal_id'],base_revision=0,scene=sample())['scene']
        record=self.state()['projects']['A']['scenes_3d'][0]
        self.assertEqual(record['head'],0);self.assertEqual(record['versions'],[])
        self.assertEqual([p['status'] for p in record['proposals']],['superseded','proposed'])
        self.assertNotEqual(first['proposal_id'],replacement['proposal_id'])

    def test_queued_cancel_releases_reservation_and_approval_can_be_reused(self):
        sid,grant=self.create_approved();self.http.store.scene_configuration['quota_bytes']=scene_project.RESERVATION_BYTES
        first=self.enqueue(sid,grant);self.post('cancel_job',song='A',job=first)
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],0)
        second=self.enqueue(sid,grant);self.assertNotEqual(first,second)
        with patch.object(scene_renderer,'render',side_effect=self.fake_render):self.assertTrue(self.http.store.process_next())
        self.assertEqual(next(j for j in self.state()['projects']['A']['scene_3d_jobs'] if j['id']==second)['status'],'completed')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],1)

    def test_preflight_failure_releases_reservation_before_renderer_call(self):
        sid,grant=self.create_approved();self.http.store.scene_configuration['quota_bytes']=scene_project.RESERVATION_BYTES
        first=self.enqueue(sid,grant);changed=self.configuration['renderer'].blender_root/'drift';changed.write_text('changed')
        with patch.object(scene_renderer,'render',side_effect=AssertionError('must not call renderer')) as renderer:self.assertTrue(self.http.store.process_next());renderer.assert_not_called()
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],0)
        changed.unlink();second=self.enqueue(sid,grant);self.assertNotEqual(first,second)

    def test_running_cancel_and_unknown_keep_quota_across_restart(self):
        sid,grant=self.create_approved();first=self.enqueue(sid,grant)
        def cancel(scene,config,publish_root,*,request_id,cancelled):
            self.post('cancel_job',song='A',job=first)
            raise scene_renderer.RenderCancelled('synthetic')
        with patch.object(scene_renderer,'render',side_effect=cancel):self.http.store.process_next()
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],1)
        self.assertEqual(self.enqueue(sid,grant),first)
        # A second approved version can produce an unknown job; its reservation
        # remains after restart, and no automatic re-render is permitted.
        proposed=self.post('scene_propose',song='A',scene_id=sid,base_revision=1,operations=[dict(target='camera',id='camera',field='lens_mm',value=65)])['scene']
        self.post('scene_review',song='A',scene_proposal_id=proposed['proposal_id'],decision='approved')
        grant2=self.state()['projects']['A']['scenes_3d'][0]['versions'][-1]['approval']['id'];second=self.enqueue(sid,grant2,2)
        with patch.object(scene_renderer,'render',side_effect=scene_renderer.RenderOutcomeUnknown(second)):self.http.store.process_next()
        reopened=app.Store(self.http.store.root);scene_project.recover(reopened)
        with reopened.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],2)
        self.assertEqual(next(j for j in reopened.state()['projects']['A']['scene_3d_jobs'] if j['id']==second)['status'],'outcome_unknown')
        with patch.object(scene_renderer,'render',side_effect=AssertionError('must not re-render')):self.assertFalse(reopened.process_next())
        with urlopen(self.base+'/api/operations') as response:ops=json.load(response)
        self.assertEqual(ops['counts']['outcome_unknown'],1)
        self.assertEqual(ops['counts']['outcome_unknown'],sum(j['status']=='outcome_unknown' for j in self.state()['projects']['A']['scene_3d_jobs']))

    def test_semantic_binding_change_at_same_ontology_revision_invalidates_approved_scene(self):
        proposal=self.post('ontology_propose',song='A',ontology_revision=0,kind='character',label='인물',description='특성',evidence='합성')['ontology']
        self.post('ontology_apply',song='A',proposal=proposal['id'],ontology_revision=0,approved=True)
        sid,grant=self.create_approved();job=self.enqueue(sid,grant)
        entity=self.state()['projects']['A']['ontology']['graph']['entities'][0]['id']
        def bind_during_render(scene,config,publish_root,*,request_id,cancelled):
            revision=self.state()['projects']['A']['shots']['shot']['revision']
            self.post('ontology_bind',song='A',shot='shot',shot_revision=revision,ontology_revision=1,entities=[entity])
            return self.fake_render(scene,config,publish_root,request_id=request_id,cancelled=cancelled)
        with patch.object(scene_renderer,'render',side_effect=bind_during_render):self.http.store.process_next()
        state=self.state();self.assertEqual(state['projects']['A']['ontology']['revision'],1)
        self.assertEqual(state['projects']['A']['shots']['shot']['takes'],[])
        self.assertEqual(next(j for j in state['projects']['A']['scene_3d_jobs'] if j['id']==job)['status'],'failed')
        with self.http.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_reservations').fetchone()[0],1)
