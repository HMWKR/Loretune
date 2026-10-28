"""Strict exposure checks with local loopback chat and synthetic generation.

The shared rehearsal scope is deliberately injected into the generation
queue; this does not claim that today's production HTTP routes share it.
"""
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

import ledger
from app import Store
from generation_queue import GenerationQueue
from tests import test_budget_crossflow


class BudgetDispatchGuardTest(unittest.TestCase):
    def setUp(self):
        self.cross=test_budget_crossflow.CrossFlowBudgetTest('test_competing_admissions_have_only_one_winner')
        self.cross.setUp();self.addCleanup(self.cross.doCleanups)
        self.f=self.cross.fixture;self.store=self.cross.store;self.scope=self.cross.scope
        self.cross.budget('2')

    def state(self,job):
        with self.store.connect() as c:
            return c.execute('SELECT state,actual FROM reservations WHERE id=?',(job['reservation'],)).fetchone()

    def test_chat_unknown_blocks_reserved_and_new_generation_until_reconciled(self):
        queued=self.cross.generation('queued-before-unknown')
        self.f.provider.replies=['drop']
        self.assertEqual(self.f.approve(self.f.preview())[0],200)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.f.provider.requests),2)
        calls=[]
        class Adapter:
            def submit(self,data):calls.append(data);return {'request_id':'fixture'}
        blocked=self.store.generation.dispatch(queued['id'],Adapter())
        self.assertEqual((blocked['state'],blocked['verified_unsubmitted'],blocked['failure_code']),
                         ('submission_blocked',True,'budget_exposure_changed'))
        self.assertEqual(calls,[]);self.assertEqual(self.state(queued),('cancelled',None))
        visible=next(j for j in self.f.state()['generation_jobs'] if j['id']==queued['id'])
        self.assertEqual((visible['state'],visible['failure_code'],visible['verified_unsubmitted']),
                         ('submission_blocked','budget_exposure_changed',True))
        with self.assertRaises(ledger.BudgetExposureBlocked):self.cross.generation('new-during-unknown')
        with self.store.connect() as c:
            row=c.execute("SELECT id,state FROM reservations WHERE job!=?",(queued['id'],)).fetchone()
            self.assertEqual(row[1],'uncertain')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts WHERE job=?',(queued['id'],)).fetchone()[0],0)
            c.execute('BEGIN IMMEDIATE')
            ledger.command(c,self.store.workspace_id,self.scope,'settle',{'reservation':row[0],'money':{'amount':'0.001','currency':'USD'}},'chat-reconciled-fixture')
        # Reconciliation alone does not requeue the blocked request.
        reopened=GenerationQueue(Store(self.f.tmp.name))
        self.assertEqual(reopened.dispatch(queued['id'],Adapter())['state'],'submission_blocked');self.assertEqual(calls,[])
        fresh=self.cross.generation('new-after-reconciliation')
        self.assertEqual(self.store.generation.dispatch(fresh['id'],Adapter())['state'],'accepted');self.assertEqual(len(calls),1)

    def test_known_overrun_blocks_queued_generation_without_rewriting_cost(self):
        first=self.cross.generation('overrun-first');second=self.cross.generation('overrun-second')
        calls=[]
        class Adapter:
            def submit(self,data):calls.append(1);return {'request_id':'fixture'}
        self.assertEqual(self.store.generation.dispatch(first['id'],Adapter())['state'],'accepted')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            ledger.command(c,self.store.workspace_id,self.scope,'settle',{'reservation':first['reservation'],'money':{'amount':'1.4','currency':'USD'}},'observed-overrun')
        result=self.store.generation.dispatch(second['id'],Adapter())
        self.assertEqual((result['state'],result['failure_code']),('submission_blocked','budget_exposure_changed'))
        self.assertEqual(len(calls),1);self.assertEqual(self.state(first),('disputed',1400000));self.assertEqual(self.state(second),('cancelled',None))

    def test_known_overrun_blocks_queued_chat_before_count_and_new_approval(self):
        p=self.f.preview();self.assertEqual(self.f.approve(p)[0],200)
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');b=ledger.budget(c,self.store.workspace_id,self.scope)
            r=ledger.command(c,self.store.workspace_id,self.scope,'reserve',{'money':{'amount':'0.7','currency':'USD'},'budget_revision':b['revision'],'expires':time.time()+60,'job':'earlier-work'},'earlier-work')
            ledger.command(c,self.store.workspace_id,self.scope,'settle',{'reservation':r['reservation'],'money':{'amount':'2','currency':'USD'}},'overrun-observed')
        self.assertTrue(self.store.general_chat_runtime.process_next());self.assertEqual(self.f.provider.requests,[])
        turn=self.f.state()['projects']['A']['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'blocked_before_message')
        self.assertEqual(self.f.approve(self.f.preview())[0],400)
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual FROM reservations WHERE id=?',(r['reservation'],)).fetchone(),('disputed',2000000))
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts').fetchone()[0],0)

    def test_low_level_claim_is_guarded_by_default_and_other_budget_is_independent(self):
        first=self.cross.generation('unknown');calls=[]
        class Timeout:
            def submit(self,data):calls.append(1);raise TimeoutError()
        self.assertEqual(self.store.generation.dispatch(first['id'],Timeout())['state'],'reconciliation_required')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');b=ledger.budget(c,self.store.workspace_id,self.scope)
            reserved=ledger.command(c,self.store.workspace_id,self.scope,'reserve',{'money':{'amount':'0.1','currency':'USD'},'budget_revision':b['revision'],'expires':time.time()+60,'job':'low-level'},'low-level')
            with self.assertRaises(ledger.BudgetExposureBlocked):
                ledger.claim_attempt(c,self.store.workspace_id,self.scope,reserved['reservation'],'low-level','chat-message','a'*64,'b'*64)
            other='project:independent';ledger.patch_budget(c,self.store.workspace_id,other,{'limit':{'amount':'1','currency':'USD'},'maxConcurrentJobs':1,'allowAutomaticRetries':False},0)
        quote=dict(first['quote'],budget_revision=1)
        independent=self.store.generation.admit(other,first['input'],quote,{'shot':'fixture','revision':1,'execution_mode':'contract-fake'},'other-budget',approved=True)
        class Adapter:
            def submit(self,data):calls.append(2);return {'request_id':'fixture'}
        self.assertEqual(self.store.generation.dispatch(independent['id'],Adapter())['state'],'accepted')
        self.assertEqual(calls,[1,2]);self.assertEqual(self.state(first),('uncertain',None))

    def test_already_sent_job_is_not_cancelled_by_later_unknown(self):
        first=self.cross.generation('already-sending');second=self.cross.generation('later-unknown')
        started=threading.Event();finish=threading.Event();calls=[]
        class Slow:
            def submit(self,data):
                calls.append('sent');started.set()
                if not finish.wait(5):raise TimeoutError()
                return {'request_id':'fixture'}
        class Timeout:
            def submit(self,data):calls.append('unknown');raise TimeoutError()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(self.store.generation.dispatch,first['id'],Slow())
            try:
                self.assertTrue(started.wait(3))
                self.assertEqual(self.store.generation.dispatch(second['id'],Timeout())['state'],'reconciliation_required')
            finally:finish.set()
            self.assertEqual(future.result(timeout=5)['state'],'accepted')
        self.assertEqual(calls,['sent','unknown']);self.assertEqual(self.state(first),('reserved',None));self.assertEqual(self.state(second),('uncertain',None))

    def test_existing_claim_remains_unknown_instead_of_unsubmitted_on_budget_block(self):
        # Simulate a persisted claim paired with stale prepared job state. A
        # different unknown cost must never cause the claimed hold to release.
        first=self.cross.generation('old-claim');other=self.cross.generation('other-unknown')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            ledger.claim_attempt(c,self.store.workspace_id,self.scope,first['reservation'],first['id'],'generation-submit','a'*64,'b'*64)
        class Timeout:
            def submit(self,data):raise TimeoutError()
        self.store.generation.dispatch(other['id'],Timeout())
        calls=[]
        class Adapter:
            def submit(self,data):calls.append(1);return {'request_id':'fixture'}
        result=self.store.generation.dispatch(first['id'],Adapter())
        self.assertEqual(result['state'],'reconciliation_required')
        self.assertNotEqual(result.get('verified_unsubmitted'),True)
        self.assertEqual(self.state(first),('uncertain',None));self.assertEqual(calls,[])


if __name__=='__main__':unittest.main()
