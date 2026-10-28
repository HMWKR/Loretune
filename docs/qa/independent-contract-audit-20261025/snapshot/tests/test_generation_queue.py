import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from app import Store
from generation_queue import GenerationQueue
import fal_provider as fal
import ledger

class GenerationQueueTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.queue=GenerationQueue(self.store)
        with self.store.connect() as c:ledger.patch_budget(c,self.store.workspace_id,'fixture',dict(limit={'amount':'1','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False),0)
        self.quote=dict(fal.estimate(),budget_revision=1)
        self.data=fal.payload('abstract landscape',b'\x89PNG\r\n\x1a\nfixture')
    def admit(self,key='one',approved=True):return self.queue.admit('fixture',self.data,self.quote,{'shot':'fixture','revision':1},key,approved=approved)
    def test_unapproved_request_never_reserves(self):
        with self.assertRaises(ValueError):self.admit(approved=False)
        with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0],0)
    def test_duplicate_and_parallel_dispatch_submit_once(self):
        job=self.admit();self.assertEqual(job,self.admit())
        calls=[]
        class Adapter:
            def submit(_,data):calls.append(data);return {'request_id':'fixture'}
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:self.queue.dispatch(job['id'],Adapter()),range(2)))
        self.assertEqual(len(calls),1)
        self.assertEqual(self.queue.get(job['id'])['state'],'accepted')
        with self.assertRaises(ledger.LedgerError):self.admit('second')
    def test_lost_receipt_holds_reservation_and_never_reissues(self):
        job=self.admit();calls=[]
        class Adapter:
            def submit(_,data):calls.append(1);raise TimeoutError()
        result=self.queue.dispatch(job['id'],Adapter());self.assertEqual(result['state'],'reconciliation_required')
        restored=GenerationQueue(Store(self.temp.name));restored.recover();restored.dispatch(job['id'],Adapter())
        self.assertEqual(len(calls),1)
        with self.store.connect() as c:self.assertEqual(ledger.budget(c,self.store.workspace_id,'fixture')['data']['reserved']['amount'],'0.7')
    def test_crash_before_receipt_and_result_are_distinct(self):
        job=self.admit()
        with self.store.connect() as c:job['state']='submitting';self.queue.save(c,job)
        self.queue.recover();self.assertEqual(self.queue.get(job['id'])['state'],'reconciliation_required')
    def test_poll_does_not_approve_select_or_settle(self):
        job=self.admit()
        class Adapter:
            def submit(_,data):return {'request_id':'fixture'}
            def status(_,receipt):return {'state':'COMPLETED','result_ready':True}
            def result(_,receipt):return {'url':'https://fal.media/fixture.mp4'}
        self.queue.dispatch(job['id'],Adapter());result=self.queue.poll(job['id'],Adapter())
        self.assertEqual(result['state'],'result_ready');self.assertFalse(result['approved']);self.assertFalse(result['cost_confirmed'])
        self.assertEqual(self.store.state()['projects'],{})

    def test_import_adds_unselected_take_once_and_preserves_existing_approval(self):
        import base64
        import subprocess
        from pathlib import Path
        image=Path(self.temp.name)/'first.png';video=Path(self.temp.name)/'result.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64','-frames:v','1',str(image)],check=True)
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=64x64:d=10','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
        import uuid
        def action(a,**d):return self.store.mutate(dict(action=a,data=d,revision=self.store.state()['revision'],request_id=uuid.uuid4().hex))
        action('project',name='song',era='default',story=0);action('shot',song='song',shot='shot',description='blue')
        action('take',song='song',shot='shot',shot_revision=0,filename='first.png',content=base64.b64encode(image.read_bytes()).decode(),reason='original',rights='synthetic test')
        action('select',song='song',shot='shot',shot_revision=1,take=1)
        action('review_take',song='song',shot='shot',take=1,decision='approved',reason='QA')
        before=self.store.state()['projects']['song']['shots']['shot']
        job=self.queue.admit('fixture',self.data,self.quote,dict(song='song',shot='shot',shot_revision=before['revision'],reference_version=1,rights='synthetic test'),'import',approved=True)
        with self.store.connect() as c:
            job.update(state='result_ready',receipt={'request_id':'fixture'},result={'url':'https://fal.media/fixture.mp4'});self.queue.save(c,job)
        result=self.queue.import_result(job['id'],lambda url:video.read_bytes())
        replay=self.queue.import_result(job['id'],lambda url:self.fail('duplicate download'))
        self.assertEqual(result,replay)
        after=Store(self.temp.name).state()['projects']['song']['shots']['shot']
        self.assertEqual(len(after['takes']),2);self.assertEqual(after['selected'],1);self.assertEqual(after['reviews'],before['reviews'])
        self.assertEqual(after['takes'][0],before['takes'][0]);self.assertFalse(result['cost_confirmed'])

    def test_cancel_before_submit_releases_without_refund_or_network(self):
        job=self.admit()
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');result=self.queue.request_cancel(job['id'],'stop',c)
        self.assertEqual(result['state'],'cancelled')
        class Adapter:
            def submit(_,data):raise AssertionError('must not send')
        self.queue.dispatch(job['id'],Adapter())
        with self.store.connect() as c:
            self.assertEqual(ledger.budget(c,self.store.workspace_id,'fixture')['data']['reserved']['amount'],'0')
            self.assertEqual(c.execute("SELECT count(*) FROM ledger_events WHERE kind='refunded'").fetchone()[0],0)
    def test_cancel_during_submit_is_not_lost_and_late_result_is_not_imported(self):
        job=self.admit();queue=self.queue;store=self.store;cancels=[]
        class Adapter:
            def submit(_,data):
                with store.connect() as c:
                    c.execute('BEGIN IMMEDIATE');queue.request_cancel(job['id'],'stop during submission',c)
                return {'request_id':'fake'}
            def cancel(_,receipt):cancels.append(1)
            def status(_,receipt):return {'state':'COMPLETED','result_ready':True}
            def result(_,receipt):return {'url':'https://fal.media/late.mp4'}
        result=queue.dispatch(job['id'],Adapter());self.assertEqual(result['state'],'cancel_pending');self.assertTrue(result['cancel_requested'])
        queue.send_cancel(job['id'],Adapter());queue.send_cancel(job['id'],Adapter());self.assertEqual(len(cancels),1)
        result=queue.poll(job['id'],Adapter());self.assertEqual(result['state'],'cancelled_result')
        with self.assertRaises(ValueError):queue.import_result(job['id'],lambda url:self.fail('late result download'))
        with store.connect() as c:self.assertEqual(ledger.budget(c,store.workspace_id,'fixture')['data']['reserved']['amount'],'0.7')

    def test_quote_expiring_in_queue_does_not_send(self):
        job=self.admit()
        with self.store.connect() as c:job['quote']['expires']=0;self.queue.save(c,job)
        class Adapter:
            def submit(_,data):raise AssertionError('expired request sent')
        self.assertEqual(self.queue.dispatch(job['id'],Adapter())['state'],'expired')
        with self.store.connect() as c:self.assertEqual(ledger.budget(c,self.store.workspace_id,'fixture')['data']['reserved']['amount'],'0')
