"""Loopback HTTP and SQLite checks for late evidence review; no provider calls."""
import json
import sqlite3
import tempfile
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import server
from contracts import project_id
import ledger
import chat_general


class LateObservationsHTTPTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.http=self.start()
        self.workspace=self.http.store.workspace_id
        for i,name in enumerate(('first','second')):
            self.http.store.mutate(dict(action='project',data=dict(name=name,era='default',story=0),revision=i,request_id='late-project-'+name))
            scope='project:'+project_id(self.workspace,name)
            with self.http.store.connect() as c:
                ledger.patch_budget(c,self.workspace,scope,{'limit':{'amount':'10','currency':'USD'},'maxConcurrentJobs':10,'allowAutomaticRetries':False},0)
        self.project=project_id(self.workspace,'first');self.other=project_id(self.workspace,'second')
        # All transmissions have started before any response becomes unknown.
        # The pending fourth attempt delivers its late evidence during paging.
        self.attempts=[self.claim('first',i) for i in range(3)]
        self.pending=self.claim('first',10,'chat-message')
        self.other_attempt=self.claim('second',9)
        for attempt in self.attempts+[self.other_attempt]:self.observe(attempt)

    def start(self,permissions=None):
        http=server(self.temp.name,0,permissions=permissions)
        thread=Thread(target=http.serve_forever,daemon=True);thread.start()
        def close():http.shutdown();http.server_close();thread.join()
        self.addCleanup(close)
        return http

    def claim(self,name,index,operation=None):
        scope='project:'+project_id(self.workspace,name);job='late-job-'+str(index)
        with self.http.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            reservation=ledger.command(c,self.workspace,scope,'reserve',{'money':{'amount':'0.1','currency':'USD'},'budget_revision':1,'expires':time.time()+60,'job':job},'reserve-'+job)['reservation']
            operation=operation or ('generation-submit' if index!=1 else 'chat-message')
            attempt,owner=ledger.claim_attempt(c,self.workspace,scope,reservation,job,operation,'a'*64,'b'*64)
        return attempt,reservation,owner,scope,job,operation

    def observe(self,claimed):
        attempt,reservation,owner,scope,job,operation=claimed
        with self.http.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            ledger.recover_attempt(c,attempt)
            ledger.command(c,self.workspace,scope,'uncertain',{'reservation':reservation},'uncertain-'+job)
            if operation=='generation-submit':payload={'request_id':'12345678-1234-1234-1234-123456789abc'}
            else:payload={'request_id':'req_fixture_private','usage':{k:{'status':'valid','value':'12'} for k in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens')}};payload['usage']['service_tier']={'status':'valid','value':'default'}
            ledger.record_late_observation(c,attempt,owner,'a'*64,payload)

    def request(self,http,path,method='GET',body=None,authenticated=True,key=None):
        headers={}
        if authenticated:headers['Authorization']='Bearer '+http.token
        if key:headers['Idempotency-Key']=key
        if body is not None:headers['Content-Type']='application/json'
        data=json.dumps(body).encode() if body is not None else None
        req=Request(f'http://127.0.0.1:{http.server_port}'+path,headers=headers,method=method,data=data)
        try:
            with urlopen(req) as response:return response.status,json.load(response)
        except HTTPError as response:
            with response:return response.code,json.load(response)

    def path(self,project=None,identifier=None,review=False,workspace=None,**query):
        value=f'/v1/workspaces/{workspace or self.workspace}/billing/late-observations'
        if identifier is not None:value+='/'+str(identifier)
        if review:value+='/reviews'
        return value+'?'+urlencode(dict(projectId=project or self.project,**query))

    def test_permissions_scoping_and_minimized_payload(self):
        path=self.path()
        self.assertEqual(self.request(self.http,path,authenticated=False)[0],401)
        read=self.start({'billing.read'});manage=self.start({'billing.manage'});none=self.start(set())
        self.assertEqual(self.request(none,path)[0],403)
        self.assertEqual(self.request(manage,path)[0],403)
        code,value=self.request(read,path);self.assertEqual(code,200);self.assertEqual(len(value['items']),3)
        item=value['items'][1];self.assertEqual(item['kind'],'chat_usage')
        code,detail=self.request(read,self.path(identifier=item['id']));self.assertEqual(code,200)
        self.assertEqual(detail['evidence']['usageStatuses']['input_tokens'],'valid')
        for sensitive in ('req_fixture_private','12345678-1234-1234-1234-123456789abc','a'*64,'b'*64,self.attempts[1][0],self.attempts[1][2]):
            self.assertNotIn(sensitive,json.dumps([value,detail]))
        self.assertNotIn('evidenceDigest',item)
        self.assertEqual(self.request(read,self.path(workspace=str(uuid.uuid4())))[0],404)
        self.assertEqual(self.request(read,self.path(project=str(uuid.uuid4())))[0],404)
        self.assertEqual(self.request(read,self.path(project=self.other,identifier=item['id']))[0],404)
        body={'decision':'reviewed_pending_billing','revision':0,'evidenceDigest':detail['evidenceDigest']}
        self.assertEqual(self.request(read,self.path(identifier=item['id'],review=True),'POST',body,key='permission-key')[0],403)
        self.assertEqual(self.request(manage,self.path(project=self.other,identifier=item['id'],review=True),'POST',body,key='permission-key')[0],404)
        self.assertEqual(self.request(manage,self.path(identifier=item['id'],review=True),'POST',body,authenticated=False,key='permission-key')[0],401)
        self.assertEqual(self.request(manage,self.path(identifier=item['id'],review=True),'POST',body,key='permission-key')[0],200)

    def test_extended_chat_evidence_remains_bounded_and_uncertain(self):
        attempt,reservation,owner,scope,job,operation=self.pending
        response={'speed':'standard','usage':{'input_tokens':100,'output_tokens':20,'service_tier':'standard',
            'inference_geo':'us','server_tool_use':{'web_search_requests':1,'web_fetch_requests':0},
            'private-new-field':'sensitive-fixture'}}
        observed=chat_general.observe_usage(response);sources=chat_general.late_billing_sources(response)
        with self.http.store.connect() as c:
            c.execute('BEGIN IMMEDIATE');ledger.recover_attempt(c,attempt)
            ledger.command(c,self.workspace,scope,'uncertain',{'reservation':reservation},'uncertain-extended')
            with self.assertRaises(ledger.LedgerError):
                ledger.record_late_observation(c,attempt,owner,'a'*64,{'usage':observed,'model_status':'private-model-name'})
            ledger.record_late_observation(c,attempt,owner,'a'*64,{'usage':observed,'model_status':'mismatch','billing_sources':sources})
            with self.assertRaises(ledger.LedgerError):
                ledger.record_late_observation(c,attempt,owner,'a'*64,{'usage':observed,'model_status':'match'})
            state,actual=c.execute('SELECT state,actual FROM reservations WHERE id=?',(reservation,)).fetchone()
            stored=c.execute('SELECT payload FROM provider_late_observations WHERE attempt=?',(attempt,)).fetchone()[0]
        self.assertEqual((state,actual),('uncertain',None))
        self.assertNotIn('sensitive-fixture',stored);self.assertNotIn('private-new-field',stored)
        code,page=self.request(self.http,self.path());self.assertEqual(code,200)
        code,detail=self.request(self.http,self.path(identifier=page['items'][-1]['id']));self.assertEqual(code,200)
        self.assertEqual(detail['evidence']['usageStatuses']['server_tool_use'],'unsupported')
        self.assertEqual(detail['evidence']['modelStatus'],'mismatch')
        self.assertEqual(detail['evidence']['usageSources']['speed'],'response')
        self.assertEqual(detail['evidence']['usageStatuses']['speed'],'unconfirmed')

    def test_keyset_pagination_and_invalid_inputs(self):
        path=self.path(limit=1);code,first=self.request(self.http,path);self.assertEqual(code,200)
        with self.http.store.connect() as c:c.execute('VACUUM')
        self.observe(self.pending)
        ids=[first['items'][0]['id']];cursor=first['nextCursor']
        while cursor:
            code,page=self.request(self.http,self.path(limit=1,cursor=cursor));self.assertEqual(code,200)
            ids.extend(item['id'] for item in page['items']);cursor=page['nextCursor']
        self.assertEqual(len(ids),4);self.assertEqual(ids,sorted(set(ids)))
        for query in ('limit=0','limit=101','limit=1&limit=2','cursor=-1','cursor=9223372036854775808'):
            self.assertEqual(self.request(self.http,self.path()+'&'+query)[0],400)
        self.assertEqual(self.request(self.http,self.path(identifier=999999))[0],404)

    def test_review_idempotency_stale_restart_and_hold(self):
        _,page=self.request(self.http,self.path());identifier=page['items'][0]['id']
        _,detail=self.request(self.http,self.path(identifier=identifier))
        path=self.path(identifier=identifier,review=True)
        body={'decision':'reviewed_pending_billing','revision':0,'evidenceDigest':detail['evidenceDigest']}
        self.assertEqual(self.request(self.http,path,'POST',body,key='review-key-0001')[0],200)
        self.assertEqual(self.request(self.http,path,'POST',body,key='review-key-0001'),(200,{'id':identifier,'reviewState':'reviewed_pending_billing','revision':1}))
        self.assertEqual(self.request(self.http,path,'POST',dict(body,decision='conflicting_evidence'),key='review-key-0001')[0],409)
        self.assertEqual(self.request(self.http,path,'POST',body,key='review-key-0002')[0],412)
        self.assertEqual(self.request(self.http,path,'POST',dict(body,revision=1,evidenceDigest='0'*64),key='review-key-0003')[0],412)
        self.assertEqual(self.request(self.http,path,'POST',dict(body,revision=1,decision='conflicting_evidence'),key='review-key-0004')[0],200)
        self.assertEqual(self.request(self.http,path,'POST',dict(body,revision=2,amount='0'),key='review-key-0005')[0],400)
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE id=?',(self.attempts[0][0],)).fetchone()[0],'unknown')
            self.assertEqual(c.execute('SELECT state,actual,refunded FROM reservations WHERE id=?',(self.attempts[0][1],)).fetchone(),('uncertain',None,0))
            self.assertEqual(c.execute("SELECT COUNT(*) FROM ledger_events WHERE kind IN ('settled','refund')").fetchone()[0],0)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_late_reviews').fetchone()[0],2)
            with self.assertRaises(sqlite3.IntegrityError):c.execute('DELETE FROM provider_late_reviews')
        reopened=self.start()
        code,detail=self.request(reopened,self.path(identifier=identifier));self.assertEqual(code,200)
        self.assertEqual((detail['revision'],detail['reviewState']),(2,'conflicting_evidence'))
        self.assertEqual(self.request(reopened,path,'POST',body,key='review-key-0001')[0],200)

    def test_concurrent_review_and_database_scope_join(self):
        _,page=self.request(self.http,self.path());identifier=page['items'][0]['id']
        _,detail=self.request(self.http,self.path(identifier=identifier))
        path=self.path(identifier=identifier,review=True)
        body={'decision':'reviewed_pending_billing','revision':0,'evidenceDigest':detail['evidenceDigest']}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda key:self.request(self.http,path,'POST',body,key=key)[0],('race-review-1','race-review-2')))
        self.assertCountEqual(results,[200,412])
        with self.http.store.connect() as c:
            # Simulate an inconsistent attempt whose workspace disagrees with its budget.
            c.execute('UPDATE provider_attempts SET workspace=? WHERE id=?',(self.workspace,self.other_attempt[0]))
            foreign_budget=str(uuid.uuid4())
            c.execute('UPDATE budgets SET workspace=? WHERE id=(SELECT budget FROM provider_attempts WHERE id=?)',(foreign_budget,self.other_attempt[0]))
        _,foreign=self.request(self.http,self.path(project=self.other))
        self.assertEqual(foreign['items'],[])
        self.assertEqual(self.request(self.http,self.path(project=self.other,identifier=4))[0],404)

    def test_existing_observations_get_stable_ids_on_schema_upgrade(self):
        with self.http.store.connect() as c:
            c.execute('DROP TABLE provider_late_evidence_ids')
            ledger.initialize(c)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM provider_late_evidence_ids').fetchone()[0],4)
            original=c.execute('SELECT id,attempt FROM provider_late_evidence_ids ORDER BY id').fetchall()
            ledger.initialize(c)
            self.assertEqual(c.execute('SELECT id,attempt FROM provider_late_evidence_ids ORDER BY id').fetchall(),original)
        _,page=self.request(self.http,self.path())
        self.assertEqual(len(page['items']),3)


if __name__=='__main__':unittest.main()
