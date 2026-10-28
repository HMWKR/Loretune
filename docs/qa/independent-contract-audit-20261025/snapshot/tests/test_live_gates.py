import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import fal_provider as fal
from live_launcher import load_runtime,parse_key
import tests.test_generation_queue as queue_fixture

class LiveGateTest(unittest.TestCase):
    def test_token_permission_denial_never_reaches_cdn_and_blocks_resume(self):
        calls=[]
        def denied(*args):calls.append(args[1]);raise fal.ProviderError('provider_http_403')
        client=fal.FalKling(live_enabled=True,transport=denied)
        with patch('fal_provider.build_opener',side_effect=AssertionError('CDN must not be reached')):
            with self.assertRaisesRegex(fal.ProviderError,'cdn_token_http_403'):client.download('https://v3b.fal.media/fixture')
        self.assertEqual(calls,[fal.TOKEN_URL])
        case=self.fixture();j=case.admit()
        for code in ['provider_http_403','cdn_token_http_403','cdn_token_http_401']:
            with case.store.connect() as c:
                j.update(state='import_blocked',failure_code=code,result={'url':'https://v3b.fal.media/fixture'});case.queue.save(c,j)
            public=case.store.state()['generation_jobs'][0]
            self.assertTrue(public['retrieval_permission_blocked']);self.assertFalse(public['can_resume_result'])
    def test_reader_policy_hash_is_bound_before_secret_access(self):
        from live_launcher import validate_approval
        policy=fal.private_lifecycle_candidate('synthetic-owner')
        gate=dict(self.gate(),private_reader='synthetic-owner',reader_evidence='synthetic profile evidence',lifecycle_sha256=hashlib.sha256(json.dumps(policy,sort_keys=True,separators=(',',':')).encode()).hexdigest())
        validate_approval(gate)
        for change in [dict(private_reader='other'),dict(reader_evidence=''),dict(lifecycle_sha256='0'*64)]:
            with patch('live_launcher.os.open',side_effect=AssertionError('secret read')):
                with self.assertRaises(ValueError):load_runtime('/not-read',dict(gate,**change),approved=True)
    def gate(self):
        return dict(model=fal.MODEL,workspace_id='fixture',song='song',shot='shot',image_sha256='a'*64,prompt_sha256=hashlib.sha256(b'prompt').hexdigest(),privacy='private',retention_seconds=3600,duration=10,generate_audio=False,price_money={'amount':'0.70','currency':'USD'},price_checked_at=time.time(),maximum_calls=1,maximum_units=1000000,expires=time.time()+300)
    def test_disabled_launcher_cannot_read_any_file(self):
        with patch.object(Path,'read_text',side_effect=AssertionError('read')),patch.object(Path,'stat',side_effect=AssertionError('stat')):
            with self.assertRaises(PermissionError):load_runtime('/not-read.env',self.gate())
    def test_synthetic_env_is_memory_only_and_literal(self):
        before=dict(os.environ)
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/'fixture.env';file.write_text('UNRELATED=ignored\nFAL_KEY="synthetic-key-123"\n')
            with patch('fal_provider.build_opener',side_effect=AssertionError('network')):
                client=load_runtime(file,self.gate(),approved=True)
            self.assertEqual(client._key,'synthetic-key-123');self.assertEqual(dict(os.environ),before)
            self.assertEqual(set(p.name for p in Path(root).iterdir()),{'fixture.env'})
        for value in ['$(touch anything)','`secret`','abc\\nxyz','${OTHER}','abc; command','abc # secret']:
            with self.assertRaises(ValueError) as e:parse_key('FAL_KEY='+value,'FAL_KEY')
            self.assertNotIn(value,str(e.exception))
        with self.assertRaises(ValueError):parse_key('FAL_KEY=synthetic-one\nFAL_KEY=synthetic-two','FAL_KEY')
    def test_synthetic_file_boundaries(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'fixture';p.write_bytes(b'x'*65537)
            with self.assertRaises(ValueError):load_runtime(p,self.gate(),approved=True)
            p.write_bytes(b'\xff')
            with self.assertRaises(ValueError):load_runtime(p,self.gate(),approved=True)
            link=Path(root)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):load_runtime(link,self.gate(),approved=True)
    def test_submit_422_is_terminal_without_retry_or_refund(self):
        case=self.fixture();job=case.admit();calls=[]
        class Adapter:
            def submit(_,data):calls.append(1);raise fal.ProviderError('provider_http_422')
        case.queue.dispatch(job['id'],Adapter());case.store.provider_adapter=Adapter()
        self.assertFalse(case.store.process_generation());self.assertEqual(calls,[1])
        current=case.queue.get(job['id']);self.assertEqual(current['state'],'failed')
        with case.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(current['reservation'],)).fetchone()[0],'uncertain')
    def test_input_price_and_privacy_are_pinned(self):
        prep=dict(song='song',shot='shot',source={'sha256':'a'*64},prompt='prompt',estimate={'money':{'amount':'0.70','currency':'USD'}})
        fal.validate_gate(self.gate(),prep,'fixture')
        for changed in [dict(prep,prompt='changed'),dict(prep,source={'sha256':'b'*64}),dict(prep,shot='other')]:
            with self.assertRaises(ValueError):fal.validate_gate(self.gate(),changed,'fixture')
        for extra in [dict(privacy='public'),dict(price_checked_at=0),dict(price_money={'amount':'1.40','currency':'USD'})]:
            with self.assertRaises(ValueError):fal.validate_gate(dict(self.gate(),**extra),prep,'fixture')
    def test_private_acl_and_cdn_token_do_not_expose_primary_key(self):
        calls=[]
        identifier='11111111-1111-4111-8111-111111111111';prefix=fal.BASE+'fal-ai/kling-video/requests/'+identifier
        receipt=dict(request_id=identifier,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
        def transport(method,url,headers,body):
            calls.append((method,url,headers,body));return {'token':'synthetic-short-lived'} if url==fal.TOKEN_URL else receipt
        client=fal.FalKling(live_enabled=True,key='synthetic-primary-key',transport=transport)
        client.submit(fal.payload('prompt',b'\x89PNG\r\n\x1a\nfixture'))
        lifecycle=json.loads(calls[0][2]['X-Fal-Object-Lifecycle-Preference']);self.assertEqual(lifecycle['initial_acl']['default'],'forbid')
        class Response(io.BytesIO):headers={'Content-Type':'video/mp4'}
        class Opener:
            def open(_,request,timeout):
                self.assertEqual(request.get_header('Authorization'),'Bearer synthetic-short-lived')
                self.assertNotIn('synthetic-primary-key',repr(request.headers));return Response(b'\x00\x00\x00\x18ftypisom1234')
        with patch('fal_provider.build_opener',return_value=Opener()):self.assertTrue(client.download('https://v3b.fal.media/files/fixture.mp4'))
        self.assertEqual(calls[1][1],fal.TOKEN_URL)
        with self.assertRaises(fal.ProviderError):client.download('https://evil.invalid/video')
    def test_download_size_type_truncation_and_signature_boundaries(self):
        class Response(io.BytesIO):pass
        def response(raw,**headers):
            r=Response(raw);r.headers={'Content-Type':'video/mp4',**headers};return r
        raw=b'\x00\x00\x00\x18ftypisom'+b'x'*20
        with patch('fal_provider.MAX_RESULT_BYTES',len(raw)):
            self.assertEqual(fal.FalKling.read_video(response(raw)),raw)
            for r in [response(raw+b'x'),response(raw,**{'Content-Length':str(len(raw)+1)}),response(raw,**{'Content-Length':'bad'}),response(raw,**{'Content-Type':'text/html'}),response(b'not-video')]:
                with self.assertRaises(fal.ProviderError):fal.FalKling.read_video(r)
        big=b'\x00\x00\x00\x18ftypisom'+b'x'*(17*1024*1024)
        self.assertEqual(len(fal.FalKling.read_video(response(big))),len(big))
    def fixture(self):
        case=queue_fixture.GenerationQueueTest();case.setUp();self.addCleanup(case.doCleanups);return case
    def test_permanent_422_stops_polling_and_keeps_unknown_cost(self):
        case=self.fixture();job=case.admit();calls=[]
        class Adapter:
            def submit(_,data):return {'request_id':'fake'}
            def status(_,receipt):calls.append(1);raise fal.ProviderError('provider_http_422')
        case.queue.dispatch(job['id'],Adapter())
        with case.store.connect() as c:
            j=case.queue.get(job['id']);j['updated']=0;c.execute('UPDATE generation_jobs SET body=? WHERE id=?',(json.dumps(j),job['id']))
        case.store.provider_adapter=Adapter();case.store.process_generation();case.store.process_generation()
        current=case.queue.get(job['id']);self.assertEqual(current['state'],'failed');self.assertFalse(current['cost_confirmed']);self.assertEqual(len(calls),1)
        with case.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(current['reservation'],)).fetchone()[0],'uncertain')
    def test_transient_poll_stops_after_three_reads_without_resubmitting(self):
        case=self.fixture();job=case.admit();calls=[]
        class Adapter:
            def submit(_,data):calls.append('submit');return {'request_id':'fake'}
            def status(_,receipt):calls.append('read');raise fal.ProviderError('provider_http_503')
        case.queue.dispatch(job['id'],Adapter());case.store.provider_adapter=Adapter()
        for _ in range(4):
            with case.store.connect() as c:
                j=case.queue.get(job['id']);j['updated']=0;c.execute('UPDATE generation_jobs SET body=? WHERE id=?',(json.dumps(j),job['id']))
            case.store.process_generation()
        self.assertEqual(case.queue.get(job['id'])['state'],'reconciliation_required');self.assertEqual(calls.count('read'),3);self.assertEqual(calls.count('submit'),1)
    def test_http_error_never_echoes_upstream_secret(self):
        class Opener:
            def open(_,request,timeout):raise HTTPError(request.full_url,422,'synthetic-secret',{},io.BytesIO(b'synthetic-secret'))
        client=fal.FalKling(live_enabled=True,key='synthetic-primary')
        with patch('fal_provider.build_opener',return_value=Opener()),self.assertRaises(fal.ProviderError) as e:client.submit(fal.payload('p',b'\x89PNG\r\n\x1a\nfixture'))
        self.assertTrue(e.exception.terminal);self.assertNotIn('synthetic-secret',str(e.exception))

    def test_permission_block_requires_new_server_evidence_once_and_redacts_urls(self):
        import uuid
        case=self.fixture();j=case.admit()
        with case.store.connect() as c:
            j.update(state='result_ready',receipt={'request_id':'safe-request'},result={'url':'https://v3b.fal.media/secret-result'},context={'song':'fixture','shot':'fixture'})
            case.queue.save(c,j)
        class Adapter:
            def download(_,url):raise fal.ProviderError('provider_media_http_403')
        case.store.provider_adapter=Adapter()
        self.assertFalse(case.store.process_generation())
        j=case.queue.get(j['id']);self.assertEqual(j['state'],'import_blocked');self.assertEqual(j['failure_code'],'provider_media_http_403')
        public=case.store.state()['generation_jobs'][0]
        self.assertTrue(public['provider_completed']);self.assertTrue(public['retrieval_permission_blocked'])
        self.assertEqual(public['provider_request_id'],'safe-request');self.assertNotIn('secret-result',json.dumps(public))
        def resume():return case.store.mutate(dict(action='resume_generation_result',data={'song':'fixture','job':j['id'],'evidence':'client cannot grant'},request_id=uuid.uuid4().hex,revision=case.store.state()['revision']))
        with self.assertRaises(ValueError):resume()
        case.store.retrieval_approval={'id':'synthetic-resolution','job':j['id'],'expires':time.time()+30,'evidence':'synthetic authorization fix'}
        self.assertTrue(case.store.state()['generation_jobs'][0]['can_resume_result'])
        resume();case.store.process_generation()
        self.assertFalse(case.store.state()['generation_jobs'][0]['can_resume_result'])
        with self.assertRaises(ValueError):resume()
        with case.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM generation_jobs').fetchone()[0],1)
