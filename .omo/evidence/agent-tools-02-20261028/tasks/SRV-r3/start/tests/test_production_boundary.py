"""Real loopback HTTP + filesystem/SQLite; synthetic credentials only."""
import sys,io,json,tempfile,threading,unittest,subprocess,uuid,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,build_opener
from urllib.parse import urlsplit
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
import fal_provider as fal
import tests.test_generation_queue as fixture

class ProductionBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.responses=[];self.calls=[];outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):self.do_GET()
            def do_GET(self):
                outer.calls.append(dict(path=self.path,authorization=self.headers.get('Authorization'),body=self.rfile.read(int(self.headers.get('Content-Length',0)))))
                status,headers,body=outer.responses.pop(0)
                self.send_response(status)
                for k,v in headers.items():self.send_header(k,v)
                self.send_header('Connection','close');self.end_headers()
                try:self.wfile.write(body)
                except BrokenPipeError:pass
        self.http=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.http.server_close);self.addCleanup(self.http.shutdown)
        origin='http://127.0.0.1:'+str(self.http.server_port)
        real=build_opener(fal.NoRedirect())
        class Route:
            def open(_,req,timeout):
                p=urlsplit(req.full_url)
                assert p.hostname in {'rest.fal.ai','v3b.fal.media'}
                mapped=Request(origin+p.path,headers=dict(req.headers),data=req.data,method=req.get_method())
                return real.open(mapped,timeout=timeout)
        self.route=Route();self.client=fal.FalKling(live_enabled=True,key='synthetic-primary')
        self.video=b'\0\0\0\x18ftypisom'+b'x'*20
    def token(self):return (200,{'Content-Type':'application/json'},b'{"token":"synthetic-cdn-token"}')
    def get(self):
        with patch('fal_provider.build_opener',return_value=self.route):return self.client.download('https://v3b.fal.media/files/b/test/result.mp4')
    def test_http_success_credentials_separated(self):
        self.responses=[self.token(),(200,{'Content-Type':'video/mp4'},self.video)]
        self.assertEqual(self.get(),self.video)
        self.assertEqual(self.calls[0]['authorization'],'Key synthetic-primary');self.assertEqual(self.calls[1]['authorization'],'Bearer synthetic-cdn-token')
    def test_http_faults_never_retry_permission_or_transient_automatically(self):
        for code in [403,404,410,429,500,503,302]:
            with self.subTest(code=code):
                self.calls=[];self.responses=[self.token(),(code,{'Location':'http://127.0.0.1:1/must-not-follow'},b'synthetic-secret-error')]
                with self.assertRaises(fal.ProviderError) as e:self.get()
                self.assertEqual(e.exception.code,'provider_media_http_'+str(code));self.assertNotIn('synthetic-secret',str(e.exception));self.assertEqual(len(self.calls),2)
    def test_http_401_refreshes_once_but_never_403(self):
        self.responses=[self.token(),(401,{},b'expired'),self.token(),(200,{'Content-Type':'video/mp4'},self.video)]
        self.assertEqual(self.get(),self.video);self.assertEqual(len(self.calls),4)
    def test_http_truncated_or_wrong_type_rejected(self):
        for headers,body in [({'Content-Type':'video/mp4','Content-Length':'200'},self.video),({'Content-Type':'text/html'},b'<html>')]:
            with self.subTest(headers=headers):
                self.responses=[self.token(),(200,headers,body)]
                with self.assertRaises(fal.ProviderError):self.get()
    def test_disallowed_origins_never_open_socket(self):
        for url in ['http://v3b.fal.media/a','https://v3b.fal.media.evil/a','https://u:p@v3b.fal.media/a','https://v3b.fal.media:444/a','https://127.0.0.1/a']:
            with patch('fal_provider.build_opener',side_effect=AssertionError('socket')):
                with self.assertRaises(fal.ProviderError):self.client.download(url)
    def test_concurrent_result_claim_downloads_once_and_restart_does_not_reissue(self):
        case=fixture.GenerationQueueTest();case.setUp();self.addCleanup(case.doCleanups)
        j=case.admit();entered=threading.Event();release=threading.Event();calls=[]
        with case.store.connect() as c:j.update(state='result_ready',result={'url':'fake'});case.queue.save(c,j)
        def download(url):calls.append(1);entered.set();release.wait(2);raise fal.ProviderError('provider_media_http_403')
        with ThreadPoolExecutor(2) as pool:
            first=pool.submit(case.queue.import_result,j['id'],download);self.assertTrue(entered.wait(2))
            second=pool.submit(case.queue.import_result,j['id'],download)
            time.sleep(.05);release.set()
            for future in [first,second]:
                try:future.result()
                except fal.ProviderError:pass
        self.assertEqual(len(calls),1)
        child=subprocess.run([sys.executable,'-c',"from app import Store; import sys; s=Store(sys.argv[1]); s.generation.recover(); print(s.state()['generation_jobs'][0]['state'])",case.temp.name],capture_output=True,text=True,check=True)
        self.assertEqual(child.stdout.strip(),'import_blocked');self.assertEqual(case.queue.get(j['id'])['state'],'import_blocked')
    def test_wrong_duration_is_not_published(self):
        case=fixture.GenerationQueueTest();case.setUp();self.addCleanup(case.doCleanups)
        v=Path(case.temp.name)/'wrong.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=s=64x64:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(v)],check=True)
        j=case.admit()
        with case.store.connect() as c:j.update(state='result_ready',result={'url':'fake'});case.queue.save(c,j)
        with self.assertRaises(ValueError):case.queue.import_result(j['id'],lambda url:v.read_bytes())
        self.assertEqual(list((Path(case.temp.name)/'assets').iterdir()),[])

    def test_repeated401_and_timeout_are_bounded(self):
        self.responses=[self.token(),(401,{},b'expired'),self.token(),(401,{},b'expired')]
        with self.assertRaisesRegex(fal.ProviderError,'provider_media_http_401'):self.get()
        self.assertEqual(len(self.calls),4)
        class TimeoutOpener:
            def open(_,request,timeout):raise TimeoutError('synthetic-secret')
        client=fal.FalKling(live_enabled=True,key='synthetic',transport=lambda *args:{'token':'synthetic-token'})
        with patch('fal_provider.build_opener',return_value=TimeoutOpener()),self.assertRaises(fal.ProviderError) as err:client.download('https://v3b.fal.media/result')
        self.assertEqual(err.exception.code,'provider_media_download_failed');self.assertNotIn('synthetic-secret',str(err.exception))
    def test_atomic_publish_failure_cleans_staging(self):
        from app import Store
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);v=Path(root)/'valid.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=s=64x64:d=10','-c:v','libx264','-pix_fmt','yuv420p',str(v)],check=True)
            with patch.object(Path,'replace',side_effect=OSError('disk fault')):
                with self.assertRaises(OSError):store.save_media(v.read_bytes(),'.mp4','video',expected_duration=10)
            self.assertEqual(list((Path(root)/'assets').iterdir()),[]);self.assertEqual(list(Path(root).glob('upload-*')),[])
    def test_db_rollback_never_marks_imported_and_same_request_recovers(self):
        import sqlite3,ledger
        import tests.test_editing as editing_fixture
        case=editing_fixture.EditingTest();case.setUp();self.addCleanup(case.doCleanups);store=case.store
        with store.connect() as c:ledger.patch_budget(c,store.workspace_id,'fixture',dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
        v=store.root/'result.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=green:s=64x64:d=10','-c:v','libx264','-pix_fmt','yuv420p',str(v)],check=True)
        q=store.generation;j=q.admit('fixture',fal.payload('x',b'\x89PNG\r\n\x1a\nfixture'),dict(fal.estimate(),budget_revision=1),dict(song='song',shot='a',shot_revision=2,reference_version=1,rights='synthetic'),'one',approved=True)
        with store.connect() as c:j.update(state='result_ready',result={'url':'fake'},receipt={'request_id':'same-request'});q.save(c,j)
        original=q.save
        def fault(c,job):
            if job['state']=='imported':raise sqlite3.OperationalError('commit fault')
            return original(c,job)
        with patch.object(q,'save',side_effect=fault):
            with self.assertRaises(sqlite3.OperationalError):q.import_result(j['id'],lambda url:v.read_bytes())
        self.assertEqual(q.get(j['id'])['state'],'downloading');self.assertEqual(len(store.state()['projects']['song']['shots']['a']['takes']),1)
        q.recover()
        with store.connect() as c:current=q.get(j['id']);current['state']='result_ready';q.save(c,current)
        result=q.import_result(j['id'],lambda url:v.read_bytes())
        self.assertEqual(result['state'],'imported');self.assertEqual(result['receipt']['request_id'],'same-request')
        self.assertEqual(len(store.state()['projects']['song']['shots']['a']['takes']),2)
        with store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM generation_jobs').fetchone()[0],1)
