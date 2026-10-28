"""Scoped work observations; fixture job metadata is not proof of rendering."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from urllib.request import urlopen
import uuid

from app import Store
import chat_sessions
import contracts
import editing
import model_selection
import production_context
from tests import test_chat_general_http as http_fixture
from tests import test_chat_runtime as protocol_fixture


def record(name,value):
    folder=os.environ.get('WORK_STATUS_EVIDENCE')
    if folder:
        target=Path(folder);target.mkdir(parents=True,exist_ok=True)
        (target/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


class WorkStatusContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name)
        self.call('project',name='A',era='default',story=0)
        self.call('project',name='B',era='default',story=0)
        self.other=self.call('conversation_create',song='A',title='private sibling')['conversation']['id']
        self.pid=contracts.project_id(self.store.workspace_id,'A')
        self.default=chat_sessions.default_id(self.project())

    def project(self,name='A',cid=None):
        with self.store.connect() as c:p=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'][name]
        return chat_sessions.scoped(p,cid) if cid else p

    def call(self,action,**data):
        with self.store.connect() as c:revision=c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        return self.store.mutate(dict(action=action,data=data,revision=revision,request_id=uuid.uuid4().hex))

    def seed(self,table,value,*,project=None,conversation=None,workspace=None):
        raw=json.dumps(value)
        with self.store.connect() as c:
            if table=='jobs':c.execute('INSERT INTO jobs VALUES (?,?)',(value['id'],raw))
            elif table=='generation_jobs':c.execute('INSERT INTO generation_jobs VALUES (?,?,?,?)',(value['id'],value['id'],'fixture',raw))
            elif table=='action_jobs':c.execute('INSERT INTO action_jobs VALUES (?,?,?,?)',(value['id'],workspace or self.store.workspace_id,project or self.pid,raw))
            elif table=='general_chat_turns':c.execute('INSERT INTO general_chat_turns VALUES (?,?,?,?)',(value['id'],project or self.pid,conversation or self.default,raw))
            elif table=='chat_turns':c.execute('INSERT INTO chat_turns VALUES (?,?,?)',(value['id'],project or self.pid,raw))
            else:raise AssertionError(table)

    def owners(self,values):
        with self.store.connect() as c:
            saved=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            saved['projects']['A'].setdefault('conversation_owners',{}).update({k:dict(conversation_id=v,kind='fixture') for k,v in values.items()})
            c.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(saved),))

    def read(self,cid=None):
        with self.store.connect() as c:return production_context.read(c,self.store,self.project(cid=cid),'A','work-status')['work_status']

    def groups(self,cid=None):return {g['source']:g for g in self.read(cid)['sources']}

    def test_recorded_kinds_versions_modes_and_no_private_fields(self):
        self.seed('jobs',dict(id='render',song='A',status='running',revision=4,progress=37.5,snapshot=dict(timeline=dict(id=2)),error='PRIVATE_ERROR',download='/private/PRIVATE_PATH'))
        self.seed('jobs',dict(id='motion',song='A',kind='local-motion',status='completed',revision=5,progress=100,motion=dict(id=3,scene={'private':'PRIVATE_SCENE'}),sha256='a'*64,download='/assets/private.mp4',take=1))
        self.seed('jobs',dict(id='scene',song='A',kind='local-3d-still',status='completed',revision=6,progress=100,scene_revision=7,sha256='b'*64,download='/assets/private.png',environment={'key':'PRIVATE_KEY'}))
        self.seed('generation_jobs',dict(id='provider',state='imported',revision=8,mode='contract-fake',context=dict(song='A',output_kind='image',shot_revision=9,action_binding=dict(workspace=self.store.workspace_id,project=self.pid)),take=2,asset_sha256='c'*64,input={'prompt':'PRIVATE_PROMPT'},receipt={'url':'https://PRIVATE_ENDPOINT'}))
        self.seed('action_jobs',dict(id='rehearsal',state='collected',mode='rehearsal',action=dict(role='video',plan_revision=10),result=dict(sha256='d'*64,output_slot='video'),grant='PRIVATE_GRANT'))
        self.seed('general_chat_turns',dict(id='general',project=self.pid,conversation_id=self.default,status='outcome_unknown',mode='contract-live-test',prompt='PRIVATE_GENERAL_PROMPT',steps=['PRIVATE_STEP']))
        self.seed('chat_turns',dict(id='legacy',project=self.pid,status='queued',mode='contract-fake',answer='PRIVATE_ANSWER'))
        value=self.read();groups={g['source']:g for g in value['sources']};local={j['id']:j for j in groups['local_jobs']['items']}
        self.assertEqual(local['render']['input_version'],dict(kind='timeline',value=2));self.assertEqual(local['render']['progress_percent'],37.5)
        self.assertEqual(local['motion']['input_version'],dict(kind='motion',value=3));self.assertEqual(local['motion']['output_kind'],'video')
        self.assertEqual(local['scene']['input_version'],dict(kind='scene_3d',value=7));self.assertEqual(local['scene']['output_kind'],'image')
        self.assertEqual(groups['provider_jobs']['items'][0]['execution_mode'],'contract-fake');self.assertTrue(groups['provider_jobs']['items'][0]['output_registered'])
        self.assertEqual(groups['rehearsal_jobs']['items'][0]['output_sha256'],'d'*64);self.assertFalse(groups['rehearsal_jobs']['items'][0]['output_registered'])
        self.assertEqual(groups['general_chat']['items'][0]['state'],'outcome_unknown')
        self.assertIsNone(groups['legacy_chat']['items'][0]['created_at']);self.assertIsNone(groups['legacy_chat']['items'][0]['record_revision'])
        self.assertFalse(value['collaboration']['available']);self.assertNotIn('PRIVATE_',json.dumps(value))
        self.assertNotIn('grant_id',json.dumps(value));record('kinds-and-redaction',value)

    def test_scope_before_projection_rejects_siblings_foreign_binding_and_owner_conflict(self):
        for identifier,song,conversation in [('default','A',None),('sibling','A',self.other),('foreign','B',None),('conflict','A',self.default)]:
            self.seed('jobs',dict(id=identifier,song=song,status='queued',conversation_id=conversation))
        self.owners({'sibling':self.other,'conflict':self.other})
        self.seed('generation_jobs',dict(id='wrong_binding',state='accepted',context=dict(song='A',action_binding=dict(workspace='other',project=self.pid))))
        self.seed('generation_jobs',dict(id='wrong_project_binding',state='accepted',context=dict(song='A',action_binding=dict(workspace=self.store.workspace_id,project='other'))))
        self.seed('general_chat_turns',dict(id='foreign_general',status='failed',conversation_id=self.other),conversation=self.other)
        self.seed('general_chat_turns',dict(id='mismatched_general',status='failed',conversation_id=self.other))
        self.seed('action_jobs',dict(id='foreign_action',state='prepared',mode='rehearsal'),project='other')
        self.seed('chat_turns',dict(id='private_legacy',status='queued',conversation_id=self.other))
        groups=self.groups();self.assertEqual([x['id'] for x in groups['local_jobs']['items']],['default'])
        self.assertTrue(all(not groups[k]['items'] for k in ('provider_jobs','general_chat','rehearsal_jobs','legacy_chat')))
        sibling=self.groups(self.other)
        self.assertEqual([x['id'] for x in sibling['local_jobs']['items']],['sibling'])
        self.assertEqual([x['id'] for x in sibling['general_chat']['items']],['foreign_general'])
        self.assertEqual([x['id'] for x in sibling['legacy_chat']['items']],['private_legacy'])
        record('scope-filter',dict(default=groups,sibling=sibling))

    def test_per_source_limit_and_insertion_order_are_explicit(self):
        for i in range(12):
            self.seed('jobs',dict(id='local_'+str(i),song='A',status='running',created=100-i,updated=1000-i))
            self.seed('general_chat_turns',dict(id='general_'+str(i),status='completed',conversation_id=self.default))
        value=self.read();groups={g['source']:g for g in value['sources']}
        for source,prefix in [('local_jobs','local_'),('general_chat','general_')]:
            self.assertTrue(groups[source]['truncated']);self.assertEqual([j['id'] for j in groups[source]['items']],[prefix+str(i) for i in range(11,3,-1)])
            self.assertIn('not cross-source',groups[source]['ordering'])
        self.assertEqual(value['limit_per_source'],8)
        self.assertTrue(all(len(g['items'])<=8 for g in value['sources']))
        self.assertLess(len(json.dumps(value).encode()),16384)
        record('bounds-and-order',value)

    def test_unknown_or_invalid_metadata_is_not_completion_or_private_prose(self):
        self.seed('jobs',dict(id='unknown',song='A',kind='PRIVATE_UNKNOWN_KIND',status='PRIVATE_UNKNOWN_STATE',revision=True,progress=101,created=10**400,sha256='PRIVATE_HASH'))
        self.seed('generation_jobs',dict(id='unknown_provider',state='outcome_unknown',mode={'PRIVATE_MODE':'secret'},progress=True,context=dict(song='A',output_kind={'PRIVATE_OUTPUT':'secret'})))
        self.seed('generation_jobs',dict(id='recovering',state='image_recovery_running',mode='contract-fake',context=dict(song='A',output_kind='image')))
        groups=self.groups();job=groups['local_jobs']['items'][0]
        self.assertEqual(job['state'],'unrecognized_state');self.assertEqual(job['kind'],'unrecognized-local-job')
        self.assertIsNone(job['record_revision']);self.assertIsNone(job['progress_percent']);self.assertIsNone(job['created_at']);self.assertIsNone(job['output_sha256'])
        self.assertEqual(groups['provider_jobs']['items'][0]['state'],'image_recovery_running')
        other=groups['provider_jobs']['items'][1];self.assertEqual(other['state'],'outcome_unknown');self.assertEqual(other['execution_mode'],'unrecognized');self.assertEqual(other['output_kind'],'unknown')
        self.assertIsNone(other['progress_percent']);self.assertNotIn('PRIVATE_',json.dumps(groups))

    def test_read_is_byte_preserving_and_reopen_keeps_records(self):
        self.seed('jobs',dict(id='preserved',song='A',status='outcome_unknown',revision=4,progress=52,created=123))
        p=self.project();before=deepcopy(p);fingerprint=model_selection.snapshot(p)
        with self.store.connect() as c:
            dump_before='\n'.join(c.iterdump());changes=c.total_changes;db_before=hashlib.sha256(self.store.db.read_bytes()).hexdigest()
            first=production_context.read(c,self.store,p,'A','work-status')
            self.assertEqual(c.total_changes,changes);self.assertEqual('\n'.join(c.iterdump()),dump_before)
            self.assertEqual(hashlib.sha256(self.store.db.read_bytes()).hexdigest(),db_before)
        self.assertEqual(p,before);self.assertEqual(model_selection.snapshot(p),fingerprint)
        reopened=Store(self.tmp.name)
        with reopened.connect() as c:second=production_context.read(c,reopened,p,'A','work-status')
        self.assertEqual(first['work_status']['sources'],second['work_status']['sources'])
        self.assertEqual(hashlib.sha256(self.store.db.read_bytes()).hexdigest(),db_before)
        record('read-preservation',dict(before_db_sha256=db_before,after_db_sha256=hashlib.sha256(self.store.db.read_bytes()).hexdigest(),reopened=second))

    def test_normal_context_remains_available_and_discovers_reserved_query(self):
        with self.store.connect() as c:value=production_context.read(c,self.store,self.project(),'A','current project facts')
        self.assertIn('timeline',value);self.assertIn('music_input',value);self.assertIn('motion_overlay_sources',value)
        self.assertNotIn('work_status',value);self.assertEqual(value['supported_context_queries'][0]['query'],'work-status')


class WorkStatusHTTPTest(unittest.TestCase):
    def setUp(self):
        self.f=http_fixture.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store=self.f.http.store;self.pid=self.f.pid

    def seed_job(self,identifier='status_render',**changes):
        value=dict(id=identifier,song='A',revision=1,status='running',progress=31,snapshot=dict(timeline=dict(id=2)),cost=dict(provider_calls=0),download=None,error=None)
        value.update(changes)
        with self.store.connect() as c:c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(value)))
        return value

    def query(self):
        transport=self.store.general_chat_runtime.transport
        transport.responses=[protocol_fixture.response([protocol_fixture.use('status','search_project_context',dict(query='work-status'))],'tool_use'),protocol_fixture.response([dict(type='text',text='조회 시점의 저장 상태입니다. 출력 승인은 별도입니다.')])]
        code,result=self.f.action('general_chat_preview',song='A',prompt='현재 작업 현황을 확인해 주세요',maximum_micro=10000)
        self.assertEqual(code,200,result);preview=result['general_chat_preview']
        self.assertEqual(preview['message_body']['model'],'claude-haiku-5-5')
        code,accepted=self.f.approve(preview);self.assertEqual(code,200,accepted)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        p=self.f.state()['projects']['A'];self.assertEqual(p['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        following=p['general_chat_previews'][-1]
        blocks=[b for m in following['message_body']['messages'] if isinstance(m.get('content'),list) for b in m['content'] if b.get('type')=='tool_result']
        targets=json.loads(blocks[-1]['content'])['execution_targets']
        return preview,following,targets['work_status'],accepted['turn']['id']

    def test_actual_http_selected_synthetic_query_progress_change_and_explicit_continuation(self):
        self.seed_job();code,result=self.f.action('conversation_create',song='A',title='private peer');self.assertEqual(code,200,result);peer=result['conversation']['id']
        code,result=self.f.action('project',name='B',era='default',story=0);self.assertEqual(code,200,result)
        self.seed_job('private_render',conversation_id=peer,error='PRIVATE_PEER_ERROR')
        self.seed_job('foreign_render',song='B')
        with self.store.connect() as c:
            saved=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            saved['projects']['A'].setdefault('conversation_owners',{})['private_render']=dict(conversation_id=peer,kind='jobs')
            c.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(saved),))
        first,following,work,turn_id=self.query()
        groups={g['source']:g for g in work['sources']}
        self.assertEqual([j['id'] for j in groups['local_jobs']['items']],['status_render'])
        self.assertEqual(groups['local_jobs']['items'][0]['progress_percent'],31)
        self.assertTrue(any(j['id']==turn_id and j['state']=='running' for j in groups['general_chat']['items']))
        frozen=deepcopy(following['message_body'])
        with self.store.connect() as c:
            job=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',('status_render',)).fetchone()[0]);job.update(status='failed',progress=75,revision=2,error='PRIVATE_RUNTIME_ERROR')
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),job['id']))
        code,result=self.f.approve(following);self.assertEqual(code,200,result)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        self.assertEqual(self.f.state()['projects']['A']['general_chat_turns'][-1]['status'],'completed')
        transport=self.store.general_chat_runtime.transport;self.assertEqual(len(transport.messages),2);self.assertEqual(transport.messages[1],frozen)
        code,result=self.f.action('production_run',song='A');self.assertEqual(code,200,result);run=result['run']['id']
        code,result=self.f.action('production_tool',song='A',run=run,call=dict(id='fresh_status',name='search_project_context',arguments=dict(query='work-status'),complete=True));self.assertEqual(code,200,result)
        updated=result['tool']['execution_targets']['work_status'];local=next(g for g in updated['sources'] if g['source']=='local_jobs')['items'][0]
        self.assertEqual((local['state'],local['progress_percent'],local['record_revision']),('failed',75,2))
        self.assertNotIn('PRIVATE_',json.dumps(updated));self.assertFalse(self.f.state()['projects']['A']['general_chat_turns'][-1]['billing_confirmed'])
        code,result=self.f.session_action(peer,'production_run',song='A');self.assertEqual(code,200,result)
        code,result=self.f.session_action(peer,'production_tool',song='A',run=result['run']['id'],call=dict(id='peer_status',name='search_project_context',arguments=dict(query='work-status'),complete=True));self.assertEqual(code,200,result)
        peer_status=result['tool']['execution_targets']['work_status']
        self.assertEqual([j['id'] for g in peer_status['sources'] if g['source']=='local_jobs' for j in g['items']],['private_render'])
        self.assertNotIn('PRIVATE_',json.dumps(peer_status))
        record('actual-http-synthetic-query',dict(first_manifest=first,observed=work,turn_id=turn_id,continuation_preserved_after_job_change=True,updated=updated,peer_status=peer_status,actual_provider_calls=0,fixture_job_metadata=True))

    def test_canonical_change_still_blocks_status_continuation(self):
        self.seed_job();_,following,work,_=self.query()
        code,result=self.f.action('shot',song='A',shot='changed',description='new canonical target');self.assertEqual(code,200,result)
        code,_=self.f.approve(following);self.assertEqual(code,400)
        self.assertEqual(len(self.store.general_chat_runtime.transport.messages),1)
        record('canonical-change-still-blocked',dict(observed=work,continuation_http_status=code,provider_messages=1,real_provider_calls=0))

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'local media tools required')
    def test_actual_local_render_queue_worker_output_and_download_match_observation(self):
        def post(action,**data):
            code,value=self.f.action(action,**data);self.assertEqual(code,200,value);return value
        post('shot',song='A',shot='source',description='Controlled local render status input')
        post('take',song='A',shot='source',shot_revision=0,filename='source.png',content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',reason='status fixture',rights='directly authored test input')
        post('select',song='A',shot='source',take=1,shot_revision=1)
        post('review_take',song='A',shot='source',take=1,decision='approved',reason='controlled source checked')
        timeline=editing.current(self.f.state()['projects']['A']);timeline['clips'][0]['duration']=3;timeline['profile']='preview'
        post('timeline',song='A',timeline=timeline);post('approve_timeline',song='A')
        identifier=post('render_job',song='A')['job'];run=post('production_run',song='A')['run']['id']
        def query(call_id):
            result=post('production_tool',song='A',run=run,call=dict(id=call_id,name='search_project_context',arguments=dict(query='work-status'),complete=True))['tool']['execution_targets']['work_status']
            return result,next(j for g in result['sources'] if g['source']=='local_jobs' for j in g['items'] if j['id']==identifier)
        before,queued=query('before_worker');self.assertEqual((queued['state'],queued['progress_percent']),('queued',0))
        self.assertFalse(queued['output_registered']);self.assertTrue(self.store.process_next())
        after,completed=query('after_worker');self.assertEqual((completed['state'],completed['progress_percent']),('completed',100));self.assertTrue(completed['output_registered'])
        with urlopen(self.f.base+'/exports/'+identifier+'.mp4') as result:raw=result.read()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),completed['output_sha256'])
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(self.store.root/'exports'/(identifier+'.mp4'))]))
        self.assertEqual(float(probe['format']['duration']),3)
        decoded=subprocess.run(['ffmpeg','-v','error','-i',str(self.store.root/'exports'/(identifier+'.mp4')),'-f','null','-'],capture_output=True)
        self.assertEqual(decoded.returncode,0,decoded.stderr)
        folder=os.environ.get('WORK_STATUS_EVIDENCE')
        if folder:
            target=Path(folder);target.mkdir(parents=True,exist_ok=True)
            (target/'actual-local-status-output.mp4').write_bytes(raw)
        record('actual-local-render-observation',dict(job_id=identifier,before=before,after=after,download_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),probe=probe,decode_exit_code=decoded.returncode,actual_provider_calls=0,scope='Actual3s local silent PNG-source render status; not music-workflow/UI/model acceptance'))


if __name__=='__main__':unittest.main()
