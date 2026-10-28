import base64
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app import Store, Conflict

class WorkerCycleTest(unittest.TestCase):
    def test_failed_chat_does_not_stop_other_queues_or_log_private_error(self):
        from app import worker_cycle
        class Chat:
            def process_next(self):
                raise OSError('secret provider details')
        class Queues:
            chat_runtime = Chat()
            def __init__(self): self.calls = []
            def process_next(self): self.calls.append('render'); return True
            def process_generation(self): self.calls.append('generation'); return False
        store = Queues()
        with self.assertLogs('app', level='ERROR') as logs:
            self.assertEqual(worker_cycle(store), (True, True))
            self.assertEqual(worker_cycle(store), (True, True))
        self.assertEqual(store.calls, ['render', 'generation', 'render', 'generation'])
        self.assertNotIn('secret provider details', ' '.join(logs.output))

    def test_failed_render_still_processes_generation_and_chat(self):
        from app import worker_cycle
        class Chat:
            def process_next(self): calls.append('chat'); return True
        class Queues:
            chat_runtime = Chat()
            def process_next(self): raise OSError('failure')
            def process_generation(self): calls.append('generation'); return False
        calls = []
        with self.assertLogs('app', level='ERROR'):
            self.assertEqual(worker_cycle(Queues()), (True, True))
        self.assertEqual(calls, ['generation', 'chat'])

class PersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name)
    def request(self,action,data):
        return dict(action=action,data=data,revision=self.store.state()['revision'],request_id=uuid.uuid4().hex)
    def call(self,action,data):return self.store.mutate(self.request(action,data))
    def test_restart_duplicate_and_conflict(self):
        req=self.request('project',dict(name='곡',era='default',story=0))
        first=self.store.mutate(req)
        self.assertEqual(first,Store(self.tmp.name).mutate(req))
        self.assertIn('곡',Store(self.tmp.name).state()['projects'])
        req['request_id']=uuid.uuid4().hex
        with self.assertRaises(Conflict): self.store.mutate(req)
    def test_concurrent_writers(self):
        requests=[self.request('project',dict(name=n,era='default',story=0)) for n in ['a','b']]
        def run(r):
            try: self.store.mutate(r); return 'ok'
            except Conflict:return 'conflict'
        with ThreadPoolExecutor() as pool:self.assertCountEqual(list(pool.map(run,requests)),['ok','conflict'])
        self.assertEqual(len(self.store.state()['projects']),1)
    def test_invalid_rolls_back(self):
        with self.assertRaises(ValueError):self.call('project',dict(name=' ',era='default',story=-1))
        self.assertEqual(self.store.state()['revision'],0)
    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg unavailable')
    def test_real_render_and_immutable_takes(self):
        import subprocess
        img=Path(self.tmp.name)/'fixture.png'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64','-frames:v','1',str(img)],check=True)
        self.call('setting',dict(text='달빛',era='default',valid_from=0,valid_to=2))
        self.call('project',dict(name='곡',era='default',story=1))
        self.call('shot',dict(song='곡',shot='a',description='달'))
        data=dict(song='곡',shot='a',shot_revision=0,filename='fixture.png',content=base64.b64encode(img.read_bytes()).decode(),reason='처음',rights='직접 제작')
        self.call('take',data)
        first=self.store.state()['projects']['곡']['shots']['a']['takes'][0]
        data.update(shot_revision=1,reason='부분 수정')
        self.call('take',data)
        self.assertEqual(first,self.store.state()['projects']['곡']['shots']['a']['takes'][0])
        self.call('select',dict(song='곡',shot='a',take=2,shot_revision=2))
        with self.assertRaises(ValueError):self.call('render',dict(song='곡'))
        with self.assertRaises(ValueError):self.call('render_job',dict(song='곡'))
        from editing import current
        self.call('review_take',dict(song='곡',shot='a',take=2,decision='approved',reason='QA'))
        self.call('timeline',dict(song='곡',timeline=current(self.store.state()['projects']['곡'])))
        self.call('approve_timeline',dict(song='곡'))
        identifier=self.call('render_job',dict(song='곡'))['job']
        from app import worker_cycle
        class FailingChat:
            def process_next(self): raise OSError('controlled chat journal failure')
        self.store.chat_runtime = FailingChat()
        with self.assertLogs('app', level='ERROR'):
            self.assertEqual(worker_cycle(self.store), (True, True))
        self.store.chat_runtime = None
        path=self.store.root/'exports'/(identifier+'.mp4')
        probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(path)])
        self.assertAlmostEqual(float(json.loads(probe)['format']['duration']),3,places=1)
        self.call('project',dict(name='다음',era='default',story=2))
        self.assertEqual(len(Store(self.tmp.name).state()['projects']['다음']['snapshot']),1)

class HttpTest(unittest.TestCase):
    def test_http_validation_and_local_boundary(self):
        from app import server
        from threading import Thread
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        with tempfile.TemporaryDirectory() as folder:
            app=server(folder,0); thread=Thread(target=app.serve_forever,daemon=True);thread.start()
            try:
                url=f'http://127.0.0.1:{app.server_port}'
                state=json.load(urlopen(url+'/api/state'))
                ops=json.load(urlopen(url+'/api/operations'))
                self.assertEqual(ops['total_jobs'],0)
                self.assertNotIn('token',ops)
                (Path(folder)/'exports'/'record.json').write_text('{"song":"한국어 QA"}')
                with self.assertRaises(HTTPError) as error:urlopen(url+'/exports/record.json')
                self.assertEqual(error.exception.code,404);error.exception.close()
                def post(body,token=state['token']):
                    return urlopen(Request(url+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':token}))
                req=dict(action='project',data=dict(name='HTTP',era='default',story=0),revision=0,request_id='http-1')
                self.assertEqual(json.load(post(req))['revision'],1)
                self.assertEqual(json.load(post(req))['revision'],1)
                recovered=json.load(urlopen(url+'/api/requests/http-1'))
                self.assertEqual(recovered,dict(status='committed',result=dict(revision=1)))
                with self.assertRaises(HTTPError) as error:urlopen(url+'/api/requests/unknown')
                self.assertEqual(error.exception.code,404);error.exception.close()
                req['request_id']='http-2'
                with self.assertRaises(HTTPError) as error:post(req)
                self.assertEqual(error.exception.code,409); error.exception.close()
                with self.assertRaises(HTTPError) as error:post({},'invalid')
                self.assertEqual(error.exception.code,403); error.exception.close()
                with self.assertRaises(HTTPError) as error:post({})
                self.assertEqual(error.exception.code,400); error.exception.close()
                with self.assertRaises(HTTPError) as error:urlopen(url+'/../.env')
                self.assertEqual(error.exception.code,404); error.exception.close()
            finally:app.shutdown();app.server_close();thread.join()

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
    def test_registered_manifest_http_preserves_content_and_rights(self):
        import subprocess
        from app import server
        from threading import Thread
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        with tempfile.TemporaryDirectory() as folder:
            app=server(folder,0);thread=Thread(target=app.serve_forever,daemon=True);thread.start()
            try:
                url=f'http://127.0.0.1:{app.server_port}'
                def state():
                    with urlopen(url+'/api/state') as response:return json.load(response)
                def post(action,**data):
                    current=state();body=dict(action=action,data=data,revision=current['revision'],request_id=uuid.uuid4().hex)
                    request=Request(url+'/api/action',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':current['token']})
                    with urlopen(request) as response:return json.load(response)
                image=Path(folder)/'fixture.png'
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64','-frames:v','1',str(image)],check=True)
                post('project',name='한국어 QA',era='default',story=0)
                post('shot',song='한국어 QA',shot='a',description='달빛')
                post('take',song='한국어 QA',shot='a',shot_revision=0,filename='fixture.png',content=base64.b64encode(image.read_bytes()).decode(),reason='합성',rights='직접 제작')
                post('select',song='한국어 QA',shot='a',take=1,shot_revision=1)
                download=post('manifest',song='한국어 QA')['download']
                with urlopen(url+download) as response:
                    self.assertEqual(response.status,200)
                    self.assertEqual(response.headers['Content-Type'],'application/json')
                    manifest=json.load(response)
                self.assertEqual(manifest['format'],'loretune-manifest-v1')
                self.assertEqual(manifest['project']['name'],'한국어 QA')
                self.assertEqual(manifest['project']['shots']['a']['description'],'달빛')
                sha=state()['projects']['한국어 QA']['shots']['a']['takes'][0]['sha256']
                post('asset_rights',song='한국어 QA',sha256=sha,blocked=True,reason='권리 확인 대기')
                with self.assertRaises(HTTPError) as error:urlopen(url+download)
                self.assertEqual(error.exception.code,403);error.exception.close()
            finally:app.shutdown();app.server_close();thread.join()
