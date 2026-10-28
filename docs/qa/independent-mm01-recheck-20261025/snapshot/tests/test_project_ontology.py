import tempfile, unittest, uuid
from app import Store
from project_ontology import projection

class ProjectOntologyTest(unittest.TestCase):
    def test_cross_project_proposal_conflict_and_identity_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            st=Store(folder)
            def call(a,**d):return st.mutate(dict(action=a,data=d,revision=st.state()['revision'],request_id=uuid.uuid4().hex))
            for n in ['A','B']:call('project',name=n,era='default',story=0)
            x=call('ontology_propose',song='A',ontology_revision=0,kind='character',label='Mira',description='blue coat',evidence='Author says blue')['ontology']
            with self.assertRaises(ValueError):call('ontology_apply',song='B',proposal=x['id'],ontology_revision=0,approved=True)
            call('ontology_apply',song='A',proposal=x['id'],ontology_revision=0,approved=True)
            first=st.state()['projects']['A']['ontology'];identifier=first['graph']['entities'][0]['id']
            y=call('ontology_propose',song='A',ontology_revision=1,entity=identifier,kind='character',label='Mira updated',description='red coat',evidence='new author statement')['ontology']
            call('ontology_apply',song='A',proposal=y['id'],ontology_revision=1,approved=True)
            second=Store(folder).state()['projects']['A']['ontology']
            self.assertEqual(len(second['graph']['entities']),1);self.assertEqual(second['graph']['entities'][0]['id'],identifier)
            call('ontology_restore',song='A',version=1,ontology_revision=2,approved=True)
            self.assertEqual(st.state()['projects']['A']['ontology']['graph'],first['graph'])
            call('archive_project',song='A',archived=True,reason='QA')
            with self.assertRaises(ValueError):call('ontology_propose',song='A',ontology_revision=3,kind='style',label='X',description='X',evidence='X')
    def test_reference_proxy_has_no_dangling_edges_or_role_conversion(self):
        p=dict(name='A',shots={'s':dict(revision=1,selected=None,takes=[],reference_versions=[dict(id=1,roles={'style':dict(song='Other',shot='s',take=1,sha256='a'*64)})])})
        graph=projection(str(uuid.uuid4()),str(uuid.uuid4()),p);ids={n['id'] for n in graph['nodes']}
        self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in graph['edges']))
        self.assertEqual(graph['edges'][-1]['role'],'style')
        self.assertEqual(graph['nodes'][-1]['origin']['song'],'Other')

    def test_bound_entities_only_become_stale_and_old_context_is_preserved(self):
        from copy import deepcopy
        from project_ontology import bind,impact
        from tests.test_ontology import graph
        g=graph();head=dict(revision=1,graph=g)
        a=dict(revision=0);b=dict(revision=0)
        bind(a,head,[g['entities'][0]['id']]);frozen=deepcopy(a)
        changed=deepcopy(head);changed['revision']=2;changed['graph']['entities'][0]['description']='changed'
        self.assertEqual(len(impact(a,changed)),1);self.assertEqual(impact(b,changed),[])
        self.assertEqual(a,frozen)
        removed=deepcopy(changed);removed['graph']['entities']=[]
        self.assertIn('제외',impact(a,removed)[0]['reason'])
        with self.assertRaises(ValueError):bind(b,head,['not-owned'])
        self.assertEqual(b,dict(revision=0))

    def test_http_stale_ontology_is_conflict_and_request_retry_is_idempotent(self):
        import json
        from threading import Thread
        from urllib.request import Request,urlopen
        from urllib.error import HTTPError
        from app import server
        with tempfile.TemporaryDirectory() as folder:
            http=server(folder,0);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{http.server_port}'
                state=json.load(urlopen(base+'/api/state'))
                def post(action,data):
                    req=dict(action=action,data=data,revision=http.store.state()['revision'],request_id=uuid.uuid4().hex)
                    request=Request(base+'/api/action',data=json.dumps(req).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':state['token']})
                    try:
                        with urlopen(request) as r:return r.status,json.load(r),request
                    except HTTPError as e:
                        with e:return e.code,json.load(e),request
                post('project',dict(name='A',era='default',story=0))
                _,x,_=post('ontology_propose',dict(song='A',ontology_revision=0,kind='character',label='Mira',description='blue',evidence='blue'))
                code,first,request=post('ontology_apply',dict(song='A',ontology_revision=0,proposal=x['ontology']['id'],approved=True));self.assertEqual(code,200)
                self.assertEqual(json.load(urlopen(request)),first)
                code,_,_=post('ontology_propose',dict(song='A',ontology_revision=0,kind='character',label='Other',description='blue',evidence='blue'));self.assertEqual(code,409)
            finally:http.shutdown();http.server_close();thread.join()

    def test_legacy_take_without_filename_remains_readable(self):
        p=dict(name='legacy',shots={'s':dict(revision=1,selected=1,takes=[dict(id=1,asset='/fixture/old.png',sha256='a'*64)])})
        graph=projection(str(uuid.uuid4()),str(uuid.uuid4()),p)
        self.assertEqual(next(n['label'] for n in graph['nodes'] if n['type']=='asset'),'old.png')

    def test_relation_dependencies_are_frozen_and_unrelated_edges_do_not_stale(self):
        from copy import deepcopy
        from project_ontology import bind,impact
        entities=[dict(id=str(uuid.uuid4()),label=n,description=n) for n in ['Mira','A','B','Other']]
        edge=dict(id='edge',source=entities[0]['id'],target=entities[1]['id'],type='references',provenance=[])
        head=dict(revision=1,graph=dict(entities=entities,relations=[edge]))
        shot={'revision':0};bind(shot,head,[entities[0]['id']]);original=deepcopy(shot)
        unrelated=deepcopy(head);unrelated['graph']['relations'].append(dict(id='other',source=entities[3]['id'],target=entities[2]['id'],type='references'))
        self.assertEqual(impact(shot,unrelated),[])
        changed=deepcopy(head);changed['graph']['entities'][1]['description']='asset hash/version changed'
        self.assertEqual(len(impact(shot,changed)),1)
        changed=deepcopy(head);changed['graph']['relations'][0]['target']=entities[2]['id']
        self.assertEqual(impact(shot,changed)[0]['id'],'relations');self.assertEqual(shot,original)
