"""Real local HTTP and render checks for repeated shots in approved timelines."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest
import uuid

from app import server
from editing import preflight, selection_mismatches


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Media tools required')
class RepeatedTimelineHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.http=server(self.tmp.name,0)
        self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close_server)
        self.base=f'http://127.0.0.1:{self.http.server_port}'
        self.state=self.get_state()
        self.images=[]
        for name in ('red','blue'):
            dest=Path(self.tmp.name)/(name+'.png')
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i',f'color=c={name}:s=64x64','-frames:v','1',str(dest)],check=True)
            self.images.append(base64.b64encode(dest.read_bytes()).decode())
        self.post('project',name='A',era='default',story=0)
        self.post('shot',song='A',shot='s',description='합성 테스트')
        for i,content in enumerate(self.images):
            self.post('take',song='A',shot='s',shot_revision=self.project()['shots']['s']['revision'],filename=f'{i}.png',content=content,reason='합성',rights='직접 제작')
        self.select(1)
        for take in (1,2):self.post('review_take',song='A',shot='s',take=take,decision='approved',reason='합성 검토')

    def close_server(self):
        self.http.shutdown();self.http.server_close();self.thread.join()

    def get_state(self):
        with urlopen(self.base+'/api/state') as response:return json.load(response)

    def project(self):return self.get_state()['projects']['A']

    def request(self,action,**data):
        state=self.get_state();body=dict(action=action,data=data,revision=state['revision'],request_id=uuid.uuid4().hex)
        request=Request(self.base+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':state['token']})
        try:
            with urlopen(request) as response:return response.status,json.load(response)
        except HTTPError as exc:
            with exc:return exc.code,json.load(exc)

    def post(self,action,**data):
        status,body=self.request(action,**data);self.assertEqual(status,200,body);return body

    def select(self,take):
        self.post('select',song='A',shot='s',take=take,shot_revision=self.project()['shots']['s']['revision'])

    def timeline(self):
        return dict(clips=[dict(shot='s',take=1,trim=0,duration=1),dict(shot='s',take=2,trim=0,duration=1)],audio=None,audio_offset=0,subtitles=[],profile='preview')

    def save_approved(self):
        self.post('timeline',song='A',timeline=self.timeline())
        self.post('approve_timeline',song='A')

    def test_occurrences_render_and_future_changes_are_guarded(self):
        self.save_approved();project=self.project();approved=deepcopy(project['timeline_versions'][0])
        self.assertEqual(approved['approval']['selected_take_snapshot'],{'s':1})
        self.assertTrue(preflight(project)['ready'])
        job=self.post('render_job',song='A')['job'];self.assertTrue(self.http.store.process_next())
        saved=self.get_state();result=next(j for j in saved['jobs'] if j['id']==job)
        self.assertEqual(result['status'],'completed',result.get('error'))
        with urlopen(self.base+result['download']) as response:video=response.read()
        self.assertEqual(hashlib.sha256(video).hexdigest(),result['sha256'])
        path=Path(self.tmp.name)/'download.mp4';path.write_bytes(video)
        def pixel(at):
            return subprocess.check_output(['ffmpeg','-v','error','-ss',str(at),'-i',str(path),'-frames:v','1','-vf','crop=2:2:320:180,scale=1:1','-pix_fmt','rgb24','-f','rawvideo','-'])
        red,blue=pixel(.5),pixel(1.5)
        self.assertGreater(red[0],180);self.assertLess(red[2],70)
        self.assertGreater(blue[2],180);self.assertLess(blue[0],70)
        self.select(2)
        status,_=self.request('render_job',song='A');self.assertEqual(status,400)
        self.assertFalse(preflight(self.project())['ready'])
        self.select(1)
        self.post('review_take',song='A',shot='s',take=2,decision='rejected',reason='철회 테스트')
        status,_=self.request('render_job',song='A');self.assertEqual(status,400)
        self.post('review_take',song='A',shot='s',take=2,decision='approved',reason='재검토')
        sha=self.project()['shots']['s']['takes'][1]['sha256']
        self.post('asset_rights',song='A',sha256=sha,blocked=True,reason='사용 중지')
        status,_=self.request('render_job',song='A');self.assertEqual(status,400)
        self.assertEqual(self.project()['timeline_versions'][0],approved)
        self.post('restore_timeline',song='A',version=1)
        restored=self.project()['timeline_versions'][-1]
        self.assertEqual(restored['clips'],approved['clips']);self.assertNotIn('approval',restored)
        self.assertEqual(self.project()['timeline_versions'][0],approved)

    def test_legacy_approval_remains_fail_closed_and_selection_snapshot_is_validated(self):
        self.save_approved();project=self.project();timeline=deepcopy(project['timeline_versions'][0])
        self.assertEqual(selection_mismatches(project,timeline),[])
        timeline['approval'].pop('selected_take_snapshot')
        self.assertEqual(selection_mismatches(project,timeline),['s'])
        timeline['clips']=timeline['clips'][:1]
        self.assertEqual(selection_mismatches(project,timeline),[])
        timeline['approval']['selected_take_snapshot']={}
        with self.assertRaises(ValueError):selection_mismatches(project,timeline)
        def simulate_legacy_approval():
            # Recreate the persisted shape produced before selection snapshots existed.
            with self.http.store.connect() as conn:
                body=json.loads(conn.execute('SELECT body FROM state').fetchone()[0])
                project=body['projects']['A']
                project['timeline_versions'][project['timeline_head']-1]['approval'].pop('selected_take_snapshot')
                conn.execute('UPDATE state SET body=?',(json.dumps(body),))
        simulate_legacy_approval()
        status,_=self.request('render_job',song='A');self.assertEqual(status,400)
        single=self.timeline();single['clips']=single['clips'][:1]
        self.post('timeline',song='A',timeline=single);self.post('approve_timeline',song='A')
        simulate_legacy_approval()
        status,_=self.request('render_job',song='A');self.assertEqual(status,200)
        self.select(2)
        status,_=self.request('render_job',song='A');self.assertEqual(status,400)


if __name__=='__main__':unittest.main()
