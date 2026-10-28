"""Non-destructive approved-motion composition and the real saved-frame API."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid

import app
import editing
import motion_renderer
import production_context
from tests.test_motion import scene


class MotionOverlayTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=app.Store(self.tmp.name)
        self.call('project',name='song',era='default',story=0)
        self.call('shot',shot='base',description='directly authored fixture')
        self.call('take',shot='base',shot_revision=0,filename='base.png',
                  content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
                  reason='synthetic image',rights='directly authored')
        self.call('select',shot='base',shot_revision=1,take=1)
        self.original_scene=scene();self.original_scene['layers']=self.original_scene['layers'][:1]
        self.approve_motion(self.original_scene)

    def call(self,action,**data):
        if action!='project':data.setdefault('song','song')
        return self.store.mutate(dict(action=action,data=data,revision=self.store.state()['revision'],request_id=uuid.uuid4().hex))

    def project(self):return self.store.state()['projects']['song']

    def approve_motion(self,value):
        p=self.project()
        proposal=self.call('motion_propose',shot_id=production_context.shot_id(p,'base'),
                           base_motion_revision=p['shots']['base'].get('motion_head',0),scene=value)['motion']['proposal_id']
        # Unit setup isolates source approval; real CoreText composition is
        # exercised explicitly by the actual-media integration case below.
        with patch.object(motion_renderer,'validate_text',return_value={}):
            self.call('motion_review',proposal_id=proposal,decision='approved')

    def timeline(self):
        value=editing.current(self.project());value['profile']='preview'
        value['clips'][0]['duration']=3
        value['clips'][0]['motion_overlay']=dict(shot='base',motion_revision=1,start=.5,end=2.5,offset_x=0,offset_y=0)
        return value

    def test_null_normalizes_to_absence_without_changing_legacy_clip(self):
        value=self.timeline();value['clips'][0]['motion_overlay']=None
        saved=editing.validate(self.project(),value)
        self.assertNotIn('motion_overlay',saved['clips'][0])
        snapshot=editing.render_project(self.project(),saved)
        self.assertNotIn('motion_overlay',snapshot['shots']['0'])

    def test_invalid_source_time_offsets_and_untrusted_fields_roll_back(self):
        base=self.timeline();before=self.project()
        for change in [dict(shot='foreign'),dict(motion_revision=2),dict(motion_revision=True),
                       dict(start=-1),dict(start=2.5),dict(end=3.1),dict(end=6),
                       dict(offset_x=float('nan')),dict(offset_x=1921),dict(offset_y=-1081),
                       dict(offset_y=True),dict(path='/tmp/unsafe'),dict(scene=self.original_scene)]:
            value=deepcopy(base);value['clips'][0]['motion_overlay'].update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):self.call('timeline',timeline=value)
        self.assertEqual(self.project(),before)
        self.assertEqual(self.store.state()['jobs'],[])

    def test_original_duration_and_approval_hash_are_enforced(self):
        value=self.timeline();value['clips'][0]['duration']=5;value['clips'][0]['motion_overlay'].update(start=0,end=5)
        with self.assertRaises(ValueError):self.call('timeline',timeline=value)
        p=self.project();version=p['shots']['base']['motion_versions'][0]
        for mutate in [lambda v:v['scene']['layers'][0].update(text='tampered'),
                       lambda v:v['approval'].update(scene_hash='0'*64),
                       lambda v:v['approval'].update(actor='model'),lambda v:v.update(approval=None)]:
            changed=deepcopy(p);mutate(changed['shots']['base']['motion_versions'][0])
            with self.assertRaises(ValueError):editing.validate(changed,self.timeline())
        self.assertEqual(self.project()['shots']['base']['motion_versions'][0],version)

    def test_immutable_source_survives_new_head_context_and_conversation(self):
        first=deepcopy(self.project()['shots']['base']['motion_versions'][0])
        changed=deepcopy(self.original_scene);changed['layers'][0]['text']='new head'
        self.approve_motion(changed)
        p=self.project();p['shots']['base']['description']='new description'
        p['music_versions']=[dict(id=1,start=1,end=2,audio=1)];p['music_head']=1
        p['_conversation_id']='another-conversation'
        resolved=editing.render_project(p,self.timeline())
        self.assertEqual(resolved['shots']['0']['motion_overlay']['motion'],first)
        self.assertEqual(self.project()['shots']['base']['motion_versions'][0],first)

    def test_font_change_rejected_at_approval_and_render_resolution(self):
        self.call('timeline',timeline=self.timeline())
        with patch.object(motion_renderer,'font_manifest',return_value={'changed':True}):
            with self.assertRaisesRegex(ValueError,'폰트'):self.call('approve_timeline')
            with self.assertRaisesRegex(ValueError,'폰트'):editing.render_project(self.project(),self.timeline())
        self.assertNotIn('approval',editing.current(self.project()))

    def test_editing_placement_requires_fresh_approval_and_preserves_old_snapshot(self):
        self.call('timeline',timeline=self.timeline())
        self.call('review_take',shot='base',take=1,decision='approved',reason='checked')
        self.call('approve_timeline');original=deepcopy(editing.current(self.project()))
        changed=self.timeline();changed['clips'][0]['motion_overlay'].update(start=1,end=2,offset_x=320)
        self.call('timeline',timeline=changed)
        self.assertNotIn('approval',editing.current(self.project()))
        self.assertEqual(self.project()['timeline_versions'][0],original)
        with self.assertRaises(ValueError):self.call('render_job')
        self.assertEqual(app.Store(self.tmp.name).state()['projects']['song']['timeline_versions'][0],original)

    def test_preview_busy_stale_bad_frame_and_blocked_rights_do_not_create_jobs(self):
        self.call('timeline',timeline=self.timeline())
        self.store.timeline_preview_lock.acquire()
        try:
            with self.assertRaises(app.Conflict):self.store.timeline_preview('song',1,0,0)
        finally:self.store.timeline_preview_lock.release()
        with self.assertRaises(app.Conflict):self.store.timeline_preview('song',2,0,0)
        for frame in [-1,72,True]:
            with self.assertRaises(ValueError):self.store.timeline_preview('song',1,0,frame)
        sha=self.project()['shots']['base']['takes'][0]['sha256']
        self.call('asset_rights',sha256=sha,blocked=True,reason='fixture rights stop')
        with self.assertRaisesRegex(ValueError,'사용 중지'):self.store.timeline_preview('song',1,0,24)
        self.assertEqual(self.store.state()['jobs'],[])

    def test_snapshot_sidecar_rejects_missing_or_different_composition(self):
        self.call('timeline',timeline=self.timeline())
        self.call('review_take',shot='base',take=1,decision='approved',reason='checked')
        self.call('approve_timeline');identifier=self.call('render_job')['job']
        job=next(x for x in self.store.state()['jobs'] if x['id']==identifier)
        job.update(sha256='0'*64,verified={},status='completed')
        self.assertTrue(app.sidecar_snapshot_hashes(job,identifier))
        broken=deepcopy(job);broken['snapshot']['shots']['0'].pop('motion_overlay')
        with self.assertRaises(ValueError):app.sidecar_snapshot_hashes(broken,identifier)
        broken=deepcopy(job);broken['snapshot']['shots']['0']['motion_overlay']['offset_x']=20
        with self.assertRaises(ValueError):app.sidecar_snapshot_hashes(broken,identifier)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'media tools required')
    def test_actual_video_overlay_position_and_clip_clock(self):
        video=Path(self.tmp.name)/'base.mp4'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=c=0x204080:s=640x360:r=24:d=3',
                        '-an','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
        self.call('take',shot='base',shot_revision=self.project()['shots']['base']['revision'],filename='base.mp4',
                  content=base64.b64encode(video.read_bytes()).decode(),reason='synthetic video',rights='directly authored')
        self.call('select',shot='base',take=2,shot_revision=self.project()['shots']['base']['revision'])
        s=deepcopy(self.original_scene);shape=deepcopy(scene()['layers'][1])
        shape.update(width=240,height=100,color='#FFFFFF');shape['keyframes'][0].update(x=300,y=600,opacity=.5)
        s['layers'].append(shape);self.approve_motion(s)
        value=self.timeline();value['clips'][0]['take']=2
        value['clips'][0]['motion_overlay'].update(motion_revision=2,start=1,end=2,offset_x=320)
        self.call('timeline',timeline=value)
        frames=[]
        for frame in (18,30,54):
            raw=self.store.timeline_preview('song',1,0,frame)
            frames.append(subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i','pipe:0','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],input=raw))
        def at(raw,x,y):return tuple(raw[(y*640+x)*3:(y*640+x)*3+3])
        self.assertEqual(at(frames[0],240,216),at(frames[2],240,216))
        self.assertEqual(at(frames[0],133,216),at(frames[1],133,216),'source location must move')
        self.assertTrue(all(b>a+30 for a,b in zip(at(frames[0],240,216),at(frames[1],240,216))))
        self.assertEqual(hashlib.sha256(video.read_bytes()).hexdigest(),self.project()['shots']['base']['takes'][1]['sha256'])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'media tools required')
    def test_actual_http_preview_transparency_timing_positions_render_and_reopen(self):
        png=Path(self.tmp.name)/'blue.png'
        subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=c=0x204080:s=64x36',
                        '-frames:v','1',str(png)],check=True)
        self.call('take',shot='base',shot_revision=self.project()['shots']['base']['revision'],filename='blue.png',
                  content=base64.b64encode(png.read_bytes()).decode(),reason='synthetic blue',rights='directly authored')
        self.call('select',shot='base',take=2,shot_revision=self.project()['shots']['base']['revision'])
        s=deepcopy(self.original_scene)
        s['layers'][0].update(text='겹치는 한글',color='#FFFFFF')
        s['layers'][0]['keyframes'][0]['opacity']=.5
        shape=deepcopy(scene()['layers'][1]);shape.update(width=240,height=100,in_frame=6,out_frame=36,color='#FFFFFF')
        shape['keyframes'][0].update(x=300,y=600,opacity=.5);s['layers'].append(shape)
        self.approve_motion(s)
        motion_renderer.validate_text(s,self.store.root)
        value=self.timeline();value['clips'][0].update(take=2);value['clips'][0]['motion_overlay']['motion_revision']=2
        self.call('timeline',timeline=value)
        http=app.server(self.tmp.name,0);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
        self.addCleanup(http.server_close);self.addCleanup(http.shutdown)
        origin=f'http://127.0.0.1:{http.server_port}'
        def preview(frame):
            query=urlencode(dict(song='song',timeline_revision=1,clip_index=0,frame=frame))
            with urlopen(origin+'/api/timeline-frame?'+query,timeout=40) as response:
                self.assertEqual(response.status,200);self.assertEqual(response.headers['Content-Type'],'image/png')
                return response.read()
        def pixels(raw):
            return subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i','pipe:0','-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],input=raw)
        def at(raw,x,y):return tuple(raw[(y*640+x)*3:(y*640+x)*3+3])
        before=self.store.state()['revision']
        early=pixels(preview(14));inside_png=preview(24);inside=pixels(inside_png);late=pixels(preview(51))
        self.assertEqual(self.store.state()['revision'],before);self.assertEqual(self.store.state()['jobs'],[])
        self.assertEqual(at(early,133,216),at(late,133,216))
        underlying=at(early,133,216);blended=at(inside,133,216)
        self.assertTrue(all(abs(actual-(base+255)/2)<6 for actual,base in zip(blended,underlying)),(underlying,blended))
        self.assertEqual(at(early,20,20),at(inside,20,20),'transparent canvas must preserve base')
        self.call('review_take',shot='base',take=2,decision='approved',reason='actual image checked')
        self.call('approve_timeline');identifier=self.call('render_job')['job'];self.assertTrue(self.store.process_next())
        result=next(x for x in self.store.state()['jobs'] if x['id']==identifier)
        self.assertEqual(result['status'],'completed',result.get('error'))
        output=self.store.root/'exports'/(identifier+'.mp4')
        decoded=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(output),'-vf',"select='eq(n,24)'",'-frames:v','1','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
        self.assertLess(sum(abs(a-b) for a,b in zip(decoded,inside))/len(inside),3)
        record=json.loads((self.store.root/'exports'/(identifier+'.json')).read_text())
        self.assertEqual(record['motion_overlays'][0]['motion_revision'],2)
        self.assertEqual(record['motion_overlays'][0]['motion']['scene'],s)
        self.assertEqual(app.Store(self.tmp.name).state()['jobs'][0]['sha256'],hashlib.sha256(output.read_bytes()).hexdigest())
        changed=deepcopy(value);changed['clips'][0]['motion_overlay'].update(offset_x=320,start=1,end=2)
        self.call('timeline',timeline=changed)
        with self.assertRaises(HTTPError) as stale:preview(24)
        self.assertEqual(stale.exception.code,409)
        stale.exception.close()


if __name__=='__main__':unittest.main()
