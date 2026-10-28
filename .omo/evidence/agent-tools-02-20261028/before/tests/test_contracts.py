"""Real HTTP schema/auth-boundary tests on synthetic local fixtures; no provider."""
import json
from pathlib import Path
import tempfile
import time
from threading import Thread
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
from app import server
from contracts import project_id


class ContractTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.http=server(self.temp.name,0)
        self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
        self.base=f'http://127.0.0.1:{self.http.server_port}'
        self.state=json.load(urlopen(self.base+'/api/state'))
        self.workspace=self.state['workspace_id']
        self.schemas=json.loads((Path(__file__).resolve().parents[1]/'docs/knowledge/project_kit/sources/current_spec/output/technical_contracts.openapi.json').read_text())['components']['schemas']
    def close(self):self.http.shutdown();self.http.server_close();self.thread.join()
    def get(self,path,token=True):
        headers={'Authorization':'Bearer '+self.state['token']} if token else {}
        try:
            with urlopen(Request(self.base+path,headers=headers)) as r:return r.status,json.load(r)
        except HTTPError as r:
            with r:return r.code,json.load(r)
    def schema(self,value,name):
        spec=self.schemas[name]
        self.assertTrue(set(spec['required'])<=set(value))
        self.assertTrue(set(value)<=set(spec['properties']))
        for key,item in value.items():
            field=spec['properties'][key]
            if 'enum' in field:self.assertIn(item,field['enum'])
            if item is None:
                self.assertTrue('null' in field.get('type',[]) or any(x.get('type')=='null' for x in field.get('oneOf',[])));continue
            if field.get('format')=='uuid':self.assertEqual(str(uuid.UUID(item)),item)
            if field.get('type')=='integer':self.assertIs(type(item),int)
        if name=='ResourceList':
            for item in value['items']:self.schema(item,'Resource')
    def write(self,path,method,body,extra=None):
        headers={'Authorization':'Bearer '+self.state['token'],'Content-Type':'application/json',**(extra or {})}
        try:
            with urlopen(Request(self.base+path,method=method,data=json.dumps(body).encode(),headers=headers)) as r:return r.status,json.load(r),dict(r.headers)
        except HTTPError as r:
            with r:return r.code,json.load(r),dict(r.headers)
    def test_budget_patch_schema_etag_and_stale_write(self):
        path=f'/v1/workspaces/{self.workspace}/billing/budgets'
        body=dict(period='month',limit={'amount':'10.123456','currency':'USD'},maxConcurrentJobs=2,allowAutomaticRetries=False)
        code,value,headers=self.write(path,'PATCH',body,{'If-Match':'"0"'})
        self.assertEqual(code,200);self.schema(value,'Resource');self.assertEqual(headers['ETag'],'"1"')
        code,value,_=self.write(path,'PATCH',body,{'If-Match':'"0"'});self.assertEqual(code,412);self.schema(value,'Error')
        code,value,_=self.write(path,'PATCH',dict(body,unknown=True),{'If-Match':'"1"'});self.assertEqual(code,400)
        code,value,_=self.write(path,'PATCH',dict(body,limit={'amount':'0.0000001','currency':'USD'}),{'If-Match':'"1"'});self.assertEqual(code,422)
        code,value=self.get(f'/v1/workspaces/{self.workspace}/billing/ledger');self.assertEqual(code,200);self.schema(value,'ResourceList');self.assertEqual(len(value['items']),1)
    def test_cancel_job_is_durable_idempotent_and_has_real_status_links(self):
        identifier=uuid.uuid4().hex
        job=dict(id=identifier,song='fixture',status='queued',progress=0,revision=1,created=time.time(),cost={},snapshot={},cancel_requested=False)
        with self.http.store.connect() as c:c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(job)))
        path=f'/v1/workspaces/{self.workspace}/jobs/{uuid.UUID(identifier)}/cancel'
        headers={'Idempotency-Key':'cancel-fixture-0001'}
        code,first,_=self.write(path,'POST',{'reason':'QA'},headers);self.assertEqual(code,202);self.schema(first,'JobAccepted')
        code,second,_=self.write(path,'POST',{'reason':'QA'},headers);self.assertEqual(code,202);self.assertEqual(first,second)
        code,value,_=self.write(path,'POST',{'reason':'different'},headers);self.assertEqual(code,409);self.schema(value,'Error')
        code,value=self.get(first['statusUrl']);self.assertEqual(code,200);self.assertEqual(value['state'],'cancelled');self.assertEqual(value['revision'],2)
        with urlopen(Request(self.base+first['eventsUrl'],headers={'Authorization':'Bearer '+self.state['token']})) as r:
            self.assertEqual(r.headers['Content-Type'],'text/event-stream');self.assertIn('event: snapshot',r.read().decode())
    def test_scoped_principal_cannot_bypass_write_grant_via_legacy(self):
        with tempfile.TemporaryDirectory() as root:
            restricted=server(root,0,permissions={'billing.read'});thread=Thread(target=restricted.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{restricted.server_port}'
                path=f'/v1/workspaces/{restricted.store.workspace_id}/billing/budgets'
                body=dict(period='month',limit={'amount':'10','currency':'USD'},maxConcurrentJobs=1,allowAutomaticRetries=False)
                req=Request(base+path,method='PATCH',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+restricted.token,'If-Match':'"0"'})
                with self.assertRaises(HTTPError) as e:urlopen(req)
                self.assertEqual(e.exception.code,403);e.exception.close()
                for path in ['/api/state','/']:
                    with self.assertRaises(HTTPError) as e:urlopen(base+path)
                    self.assertEqual(e.exception.code,403);e.exception.close()
                with restricted.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM budgets').fetchone()[0],0)
            finally:restricted.shutdown();restricted.server_close();thread.join()
    def test_job_contract_auth_foreign_workspace_and_state_revision(self):
        identifier=uuid.uuid4().hex
        job=dict(id=identifier,song='fixture',status='running',progress=40,revision=1,
                 created=time.time(),started=time.time(),cost={},snapshot={},cancel_requested=False)
        with self.http.store.connect() as c:c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(job)))
        path=f'/v1/workspaces/{self.workspace}/jobs/{uuid.UUID(identifier)}'
        code,value=self.get(path);self.assertEqual(code,200);self.schema(value,'Job')
        self.assertEqual(value['progress'],.4);self.assertEqual(value['costStatus'],'pending')
        self.http.store.mutate(dict(action='cancel_job',data={'job':identifier},revision=0,request_id='contract-cancel-fixture'))
        code,value=self.get(path);self.assertEqual(value['revision'],2);self.assertEqual(value['state'],'cancel_requested')
        code,value=self.get(path,False);self.assertEqual(code,401);self.schema(value,'Error')
        code,value=self.get(path.replace(self.workspace,str(uuid.uuid4())));self.assertEqual(code,404);self.schema(value,'Error')
        self.assertNotIn('fixture',json.dumps(value))
        code,value=self.get(path.replace(str(uuid.UUID(identifier)),'invalid'));self.assertEqual(code,400);self.schema(value,'Error')
    def test_versions_pagination_exact_resource_envelope(self):
        self.http.store.mutate(dict(action='project',data=dict(name='fixture',era='default',story=0),revision=0,request_id='contract-project-fixture'))
        with self.http.store.connect() as c:
            body=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            p=body['projects']['fixture'];p['timeline_versions']=[dict(id=i,clips=[],audio=None,audio_offset=0,subtitles=[],profile='preview') for i in [1,2]]
            c.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(body),))
        path=f'/v1/workspaces/{self.workspace}/projects/{project_id(self.workspace,"fixture")}/versions'
        code,first=self.get(path+'?limit=1');self.assertEqual(code,200);self.schema(first,'ResourceList');self.assertEqual(first['nextCursor'],'1')
        code,second=self.get(path+'?limit=1&cursor=1');self.assertEqual(code,200);self.schema(second,'ResourceList')
        self.assertIsNone(second['nextCursor']);self.assertNotEqual(first['items'][0]['id'],second['items'][0]['id'])
        for query in ['?limit=0','?limit=201','?cursor=999','?limit=1&limit=2']:
            code,error=self.get(path+query);self.assertEqual(code,400);self.schema(error,'Error')
