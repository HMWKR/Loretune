"""Shared transmission claims, using isolated SQLite and loopback fixtures."""
import json
import multiprocessing
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app import Store
from generation_queue import GenerationQueue
import ledger
import chat_general
from tests import test_chat_live_contract, test_generation_queue


HASH='a'*64
AUTH='b'*64
RECEIPT='12345678-1234-1234-1234-123456789abc'


def reserve_and_claim(root, ready, results, label):
    store=Store(root)
    ready.wait(10)
    try:
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            b=ledger.budget(c,store.workspace_id,'shared')
            item=ledger.command(c,store.workspace_id,'shared','reserve',
                {'money':{'amount':'0.6','currency':'USD'},'budget_revision':b['revision'],'expires':time.time()+60,'job':label},label)
            identifier,owner=ledger.claim_attempt(c,store.workspace_id,'shared',item['reservation'],label,'generation-submit',HASH,AUTH)
        results.put(('claimed',identifier,owner))
    except ledger.LedgerError:
        results.put(('denied',))


def sending_process(root, job_id, entered, release, results):
    class Adapter:
        def submit(self, data):
            entered.set()
            release.wait(10)
            return {'request_id':RECEIPT,'ignored_secret':'must-not-be-recorded'}
    try:
        results.put(('result',GenerationQueue(Store(root)).dispatch(job_id,Adapter())['state']))
    except ledger.LedgerError:
        results.put(('fenced',))


def crash_before_claim_commit(root, job):
    store=Store(root)
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        ledger.claim_attempt(c,store.workspace_id,job['scope'],job['reservation'],job['id'],'generation-submit',HASH,AUTH)
        os._exit(0)


def crash_after_claim_commit(root, job_id):
    class Adapter:
        def submit(self, data):
            os._exit(0)
    GenerationQueue(Store(root)).dispatch(job_id,Adapter())


def crash_before_late_commit(root, attempt, owner):
    store=Store(root)
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        ledger.record_late_observation(c,attempt,owner,HASH,{'request_id':RECEIPT})
        os._exit(0)


class AttemptLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name)
        with self.store.connect() as c:
            ledger.patch_budget(c,self.store.workspace_id,'shared',{'limit':{'amount':'1','currency':'USD'},'maxConcurrentJobs':2,'allowAutomaticRetries':False},0)

    def reserve(self,job,amount='0.4'):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            return ledger.command(c,self.store.workspace_id,'shared','reserve',{'money':{'amount':amount,'currency':'USD'},'budget_revision':1,'expires':time.time()+60,'job':job},job)['reservation']

    def test_two_processes_compete_for_last_budget(self):
        ctx=multiprocessing.get_context('spawn');barrier=ctx.Barrier(2);results=ctx.Queue()
        workers=[ctx.Process(target=reserve_and_claim,args=(self.temp.name,barrier,results,n)) for n in ('one','two')]
        for p in workers:p.start()
        try:
            for p in workers:p.join(15)
            self.assertTrue(all(not p.is_alive() and p.exitcode==0 for p in workers))
            values=[results.get(timeout=3) for _ in workers]
            self.assertCountEqual([v[0] for v in values],['claimed','denied'])
            with self.store.connect() as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts').fetchone()[0],1)
                self.assertEqual(ledger.budget(c,self.store.workspace_id,'shared')['data']['reserved']['amount'],'0.6')
        finally:
            for p in workers:
                if p.is_alive():p.terminate();p.join(5)
            results.close()

    def test_duplicate_fencing_unknown_and_independent_attempts(self):
        first=self.reserve('one');second=self.reserve('two')
        def claim(res,job):
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                return ledger.claim_attempt(c,self.store.workspace_id,'shared',res,job,'generation-submit',HASH,AUTH)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(lambda pair:claim(*pair),[(first,'one'),(second,'two')]))
        self.assertNotEqual(a[0],b[0])
        with self.assertRaises(ledger.AttemptExists):claim(first,'one')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');ledger.recover_attempt(c,a[0])
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            with self.assertRaises(ledger.LedgerError):ledger.finish_attempt(c,a[0],a[1],'observed')
            ledger.finish_attempt(c,b[0],b[1],'observed')
        with self.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE id=?',(a[0],)).fetchone()[0],'unknown')
            self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE id=?',(b[0],)).fetchone()[0],'observed')
            self.assertEqual(ledger.budget(c,self.store.workspace_id,'shared')['data']['reserved']['amount'],'0.8')

    def test_claim_rejects_wrong_scope_job_and_no_transaction(self):
        reservation=self.reserve('one')
        with self.store.connect() as c:
            with self.assertRaises(ledger.LedgerError):ledger.claim_attempt(c,self.store.workspace_id,'shared',reservation,'one','generation-submit',HASH,AUTH)
            c.execute('BEGIN IMMEDIATE')
            for workspace,scope,job in [(self.store.workspace_id,'shared','two'),('foreign','shared','one'),(self.store.workspace_id,'missing','one')]:
                with self.assertRaises(ledger.LedgerError):ledger.claim_attempt(c,workspace,scope,reservation,job,'generation-submit',HASH,AUTH)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts').fetchone()[0],0)

    def test_late_evidence_is_fenced_immutable_bounded_and_idempotent(self):
        reservation=self.reserve('one')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            attempt,owner=ledger.claim_attempt(c,self.store.workspace_id,'shared',reservation,'one','generation-submit',HASH,AUTH)
            ledger.recover_attempt(c,attempt)
            for bad_owner,bad_hash,payload in [('wrong',HASH,{'request_id':RECEIPT}),(owner,AUTH,{'request_id':RECEIPT}),(owner,HASH,{'request_id':'x'*10000}),(owner,HASH,{'request_id':RECEIPT,'secret':'x'})]:
                with self.assertRaises(ledger.LedgerError):ledger.record_late_observation(c,attempt,bad_owner,bad_hash,payload)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_late_observations').fetchone()[0],0)
            ledger.record_late_observation(c,attempt,owner,HASH,{'request_id':RECEIPT})
            ledger.record_late_observation(c,attempt,owner,HASH,{'request_id':RECEIPT})
            with self.assertRaises(ledger.LedgerError):ledger.record_late_observation(c,attempt,owner,HASH,{'request_id':'00000000-0000-0000-0000-000000000000'})
            with self.assertRaises(sqlite3.IntegrityError):c.execute('DELETE FROM provider_late_observations')
            with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE provider_late_observations SET payload='{}'")
        reopened=Store(self.temp.name)
        with reopened.connect() as c:
            self.assertEqual(json.loads(c.execute('SELECT payload FROM provider_late_observations').fetchone()[0]),{'request_id':RECEIPT})
            self.assertEqual(c.execute('SELECT state FROM provider_attempts').fetchone()[0],'unknown')

    def test_late_evidence_crash_before_commit_can_be_recorded_after_restart(self):
        reservation=self.reserve('one')
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            attempt,owner=ledger.claim_attempt(c,self.store.workspace_id,'shared',reservation,'one','generation-submit',HASH,AUTH)
            ledger.recover_attempt(c,attempt)
        ctx=multiprocessing.get_context('spawn');worker=ctx.Process(target=crash_before_late_commit,args=(self.temp.name,attempt,owner));worker.start();worker.join(10)
        try:
            self.assertFalse(worker.is_alive());self.assertEqual(worker.exitcode,0)
            with self.store.connect() as c:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_late_observations').fetchone()[0],0)
                c.execute('BEGIN IMMEDIATE');ledger.record_late_observation(c,attempt,owner,HASH,{'request_id':RECEIPT})
            with self.store.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_late_observations').fetchone()[0],1)
        finally:
            if worker.is_alive():worker.terminate();worker.join(5)


class AttemptWorkflowTest(unittest.TestCase):
    def generation(self):
        fixture=test_generation_queue.GenerationQueueTest(methodName='test_unapproved_request_never_reserves')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        return fixture

    def live(self):
        fixture=test_chat_live_contract.LiveContractHTTPTest(methodName='test_exact_approved_bytes_and_estimate_is_not_confirmed')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        return fixture

    def test_generation_observed_and_repeat_after_crash_does_not_send(self):
        f=self.generation();job=f.admit();calls=[]
        class Adapter:
            def submit(_,data):calls.append(1);return {'request_id':'fixture'}
        self.assertEqual(f.queue.dispatch(job['id'],Adapter())['state'],'accepted')
        with f.store.connect() as c:
            row=c.execute('SELECT id,owner,state FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()
            self.assertEqual(row[2],'observed')
            # Reproduce a stale/partial job record without altering its claim.
            stored=f.queue.get(job['id']);stored['state']='prepared';f.queue.save(c,stored)
        result=f.queue.dispatch(job['id'],Adapter())
        self.assertEqual(result['state'],'reconciliation_required');self.assertEqual(calls,[1])
        with f.store.connect() as c:self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'uncertain')

    def test_generation_transport_loss_and_restart_fence(self):
        f=self.generation();job=f.admit();calls=[]
        class Adapter:
            def submit(_,data):calls.append(1);raise TimeoutError('private failure')
        self.assertEqual(f.queue.dispatch(job['id'],Adapter())['state'],'reconciliation_required')
        with f.store.connect() as c:
            item=c.execute('SELECT state,request_hash,binding_hash FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()
            self.assertEqual(item[0],'unknown');self.assertEqual(len(item[1]),64);self.assertEqual(len(item[2]),64)
            self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'uncertain')
        reopened=GenerationQueue(Store(f.temp.name));reopened.recover();reopened.dispatch(job['id'],Adapter())
        self.assertEqual(calls,[1])

    def test_restart_during_inflight_send_fences_late_result(self):
        f=self.generation();job=f.admit();ctx=multiprocessing.get_context('spawn')
        entered=ctx.Event();release=ctx.Event();results=ctx.Queue()
        worker=ctx.Process(target=sending_process,args=(f.temp.name,job['id'],entered,release,results));worker.start()
        try:
            self.assertTrue(entered.wait(10))
            with f.store.connect() as c:
                self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()[0],'sending')
            reopened=GenerationQueue(Store(f.temp.name));reopened.recover()
            release.set();worker.join(10)
            self.assertFalse(worker.is_alive());self.assertEqual(worker.exitcode,0)
            self.assertEqual(results.get(timeout=3),('result','reconciliation_required'))
            self.assertEqual(reopened.get(job['id'])['state'],'reconciliation_required')
            with f.store.connect() as c:
                self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()[0],'unknown')
                self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'uncertain')
                self.assertEqual(json.loads(c.execute('SELECT payload FROM provider_late_observations').fetchone()[0]),{'request_id':RECEIPT})
        finally:
            release.set()
            if worker.is_alive():worker.terminate();worker.join(5)
            results.close()

    def test_cancel_inflight_then_restart_recovers_attempt_and_late_receipt(self):
        f=self.generation();job=f.admit();ctx=multiprocessing.get_context('spawn')
        entered=ctx.Event();release=ctx.Event();results=ctx.Queue()
        worker=ctx.Process(target=sending_process,args=(f.temp.name,job['id'],entered,release,results));worker.start()
        try:
            self.assertTrue(entered.wait(10))
            with f.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');self.assertEqual(f.queue.request_cancel(job['id'],'fixture',c)['state'],'reconciliation_required')
            reopened=GenerationQueue(Store(f.temp.name));reopened.recover()
            with f.store.connect() as c:
                self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'uncertain')
                self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()[0],'unknown')
            release.set();worker.join(10)
            self.assertFalse(worker.is_alive());self.assertEqual(results.get(timeout=3),('result','reconciliation_required'))
            with f.store.connect() as c:self.assertEqual(json.loads(c.execute('SELECT payload FROM provider_late_observations').fetchone()[0]),{'request_id':RECEIPT})
            self.assertIsNone(reopened.get(job['id'])['receipt'])
        finally:
            release.set()
            if worker.is_alive():worker.terminate();worker.join(5)
            results.close()

    def test_crash_before_commit_rolls_back_and_prepared_job_can_send(self):
        f=self.generation();job=f.admit();ctx=multiprocessing.get_context('spawn')
        worker=ctx.Process(target=crash_before_claim_commit,args=(f.temp.name,job));worker.start();worker.join(10)
        try:
            self.assertFalse(worker.is_alive());self.assertEqual(worker.exitcode,0)
            with f.store.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_attempts').fetchone()[0],0)
            calls=[]
            class Adapter:
                def submit(self, data):calls.append(1);return {'request_id':'fixture'}
            self.assertEqual(f.queue.dispatch(job['id'],Adapter())['state'],'accepted');self.assertEqual(calls,[1])
        finally:
            if worker.is_alive():worker.terminate();worker.join(5)

    def test_crash_after_commit_never_automatically_resends(self):
        f=self.generation();job=f.admit();ctx=multiprocessing.get_context('spawn')
        worker=ctx.Process(target=crash_after_claim_commit,args=(f.temp.name,job['id']));worker.start();worker.join(10)
        try:
            self.assertFalse(worker.is_alive());self.assertEqual(worker.exitcode,0)
            reopened=GenerationQueue(Store(f.temp.name));reopened.recover();calls=[]
            class Adapter:
                def submit(self, data):calls.append(1);return {'request_id':'fixture'}
            self.assertEqual(reopened.dispatch(job['id'],Adapter())['state'],'reconciliation_required');self.assertEqual(calls,[])
            with f.store.connect() as c:
                self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE job=?',(job['id'],)).fetchone()[0],'unknown')
                self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'uncertain')
        finally:
            if worker.is_alive():worker.terminate();worker.join(5)

    def test_loopback_chat_exact_approved_wire_and_attempts(self):
        f=self.live();p=f.preview();self.assertEqual(f.approve(p)[0],200)
        self.assertTrue(f.http.store.general_chat_runtime.process_next())
        with f.http.store.connect() as c:
            rows=c.execute('SELECT operation,state,request_hash,binding_hash FROM provider_attempts ORDER BY rowid').fetchall()
        self.assertEqual([r[:2] for r in rows],[('chat-count','observed'),('chat-message','observed')])
        self.assertEqual([r[2] for r in rows],[p['count_wire_sha256'],p['message_wire_sha256']])
        self.assertTrue(all(r[3]==p['manifest_sha256'] for r in rows))
        self.assertNotIn('synthetic-key-not-real',json.dumps(rows))

    def test_loopback_message_timeout_preserves_unknown_and_no_retry(self):
        f=self.live();f.provider.replies=['drop'];p=f.preview();self.assertEqual(f.approve(p)[0],200)
        self.assertTrue(f.http.store.general_chat_runtime.process_next())
        with f.http.store.connect() as c:
            rows=c.execute('SELECT operation,state FROM provider_attempts ORDER BY rowid').fetchall()
            self.assertEqual(rows,[('chat-count','observed'),('chat-message','unknown')])
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
        self.assertFalse(f.http.store.general_chat_runtime.process_next());self.assertEqual(len(f.provider.requests),2)

    def test_loopback_late_chat_usage_is_recorded_without_pricing_or_tool(self):
        f=self.live();reply=test_chat_live_contract.response([test_chat_live_contract.use('plan','propose_media_plan',test_chat_live_contract.ARGS)],'tool_use')
        reply['_request_id']='req_fixture_123';reply['model']='private-model-mismatch';reply['speed']='standard';reply['private']='must-not-be-recorded';f.provider.replies=[reply]
        f.provider.message_wait=threading.Event();p=f.preview();self.assertEqual(f.approve(p)[0],200)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(f.http.store.general_chat_runtime.process_next)
            try:
                self.assertTrue(f.provider.message_started.wait(3))
                with f.http.store.connect() as c:chat_general.recover(c)
            finally:f.provider.message_wait.set()
            self.assertTrue(future.result(timeout=5))
        with f.http.store.connect() as c:
            raw=c.execute('SELECT payload FROM provider_late_observations').fetchone()[0];observation=json.loads(raw)
            self.assertEqual(observation['request_id'],'req_fixture_123')
            self.assertEqual(observation['usage']['input_tokens']['status'],'valid')
            self.assertEqual(observation['model_status'],'mismatch')
            self.assertEqual(observation['billing_sources']['speed'],'response')
            self.assertNotIn('private-model-mismatch',raw)
            self.assertNotIn('must-not-be-recorded',raw)
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
            self.assertEqual(c.execute("SELECT state FROM provider_attempts WHERE operation='chat-message'").fetchone()[0],'unknown')
            stored=json.loads(c.execute('SELECT body FROM general_chat_turns').fetchone()[0]);self.assertNotIn('pending_tool',stored)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM ledger_events WHERE kind IN ('usage_estimated','settled')").fetchone()[0],0)
        state=f.state()['projects']['A'];turn=state['general_chat_turns'][-1]
        self.assertEqual(turn['status'],'outcome_unknown');self.assertFalse(turn['billing_confirmed']);self.assertIsNone(turn['answer'])
        self.assertEqual(len(f.provider.requests),2)

    def test_late_model_uses_submitted_binding_when_contract_changes(self):
        f=self.live();p=f.preview();reply=test_chat_live_contract.response();reply['model']=p['message_body']['model']
        f.provider.replies=[reply];f.provider.message_wait=threading.Event();self.assertEqual(f.approve(p)[0],200)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(f.http.store.general_chat_runtime.process_next)
            try:
                self.assertTrue(f.provider.message_started.wait(3))
                with patch.object(chat_general,'selected_from_binding',side_effect=ValueError('contract changed')):
                    with f.http.store.connect() as c:chat_general.recover(c)
                    f.provider.message_wait.set();self.assertTrue(future.result(timeout=5))
            finally:f.provider.message_wait.set()
        with f.http.store.connect() as c:
            observation=json.loads(c.execute('SELECT payload FROM provider_late_observations').fetchone()[0])
            self.assertEqual(observation['model_status'],'match')
            self.assertEqual(c.execute('SELECT state FROM reservations').fetchone()[0],'uncertain')
            self.assertEqual(c.execute("SELECT COUNT(*) FROM ledger_events WHERE kind IN ('usage_estimated','settled')").fetchone()[0],0)


if __name__=='__main__':unittest.main()
