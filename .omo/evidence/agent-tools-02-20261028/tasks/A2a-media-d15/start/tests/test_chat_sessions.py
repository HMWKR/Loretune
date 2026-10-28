"""Conversation scope regression tests using an isolated local Store."""
import tempfile
import unittest
import uuid
import base64
import hashlib
import json
import shutil
import time
from threading import Thread
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from app import Store
from loretune import Conflict
from image_adapter import SyntheticImageAdapter


class ConversationScopeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.store.mutate(dict(action='project', data=dict(name='A', era='default', story=0),
                               revision=0, request_id=uuid.uuid4().hex))
        self.default = self.store.state({})['projects']['A']['active_conversation']['id']

    def request(self, action, data, conversation):
        state = self.store.state({'A': conversation})
        active = state['projects']['A']['active_conversation']
        return dict(action=action, data=dict(song='A', **data), revision=state['revision'],
                    request_id=uuid.uuid4().hex, conversation_id=conversation,
                    conversation_revision=active['revision'], shared_version=active['shared_version'])

    def create_session(self):
        request = self.request('conversation_create', {'title': '새 대화'}, self.default)
        result = self.store.mutate(request)
        self.assertEqual(self.store.mutate(request), result)
        return result['conversation']['id']

    def test_drafts_stay_in_their_session_after_reopen(self):
        other = self.create_session()
        plan = dict(goal='B의 목표', scenes='B의 장면', style='', constraints='', kind='narrative')
        self.store.mutate(self.request('guided_plan', plan, other))
        reopened = Store(self.tmp.name)
        first = reopened.state({'A': self.default})['projects']['A']
        second = reopened.state({'A': other})['projects']['A']
        self.assertEqual(first.get('guided_plans', []), [])
        self.assertEqual(second['guided_plans'][0]['goal'], 'B의 목표')
        self.assertEqual(len(second['conversations']), 2)

    def test_old_session_revision_is_rejected(self):
        other = self.create_session()
        plan = dict(goal='목표', scenes='장면', style='', constraints='', kind='narrative')
        stale = self.request('guided_plan', plan, other)
        self.store.mutate(self.request('guided_plan', plan, other))
        with self.assertRaises(Conflict):
            self.store.mutate(stale)
        self.assertEqual(len(self.store.state({'A': other})['projects']['A']['guided_plans']), 1)

    def test_different_sessions_can_write_from_same_global_revision(self):
        other = self.create_session()
        a = self.request('guided_plan', dict(goal='A', scenes='장면 A', style='', constraints='', kind='narrative'), self.default)
        b = self.request('guided_plan', dict(goal='B', scenes='장면 B', style='', constraints='', kind='narrative'), other)
        self.assertEqual(a['revision'], b['revision'])
        self.store.mutate(a)
        self.store.mutate(b)
        self.assertEqual(self.store.state({'A': self.default})['projects']['A']['guided_plans'][0]['goal'], 'A')
        self.assertEqual(self.store.state({'A': other})['projects']['A']['guided_plans'][0]['goal'], 'B')

    @unittest.skipUnless(shutil.which('ffprobe'), 'Media probe required')
    def test_http_lineage_only_includes_visible_conversation_takes(self):
        from app import server
        self.store.mutate(self.request('shot', {'shot': '장면', 'description': '합성 장면'}, self.default))

        def add_take(conversation, filename, width):
            image = SyntheticImageAdapter().generate({'prompt': 'synthetic', 'width': width, 'height': 32})['bytes']
            shot = self.store.state({'A': conversation})['projects']['A']['shots']['장면']
            request = self.request('take', {'shot': '장면', 'shot_revision': shot['revision'],
                'filename': filename, 'content': base64.b64encode(image).decode(),
                'reason': '합성 자료', 'rights': '직접 제작'}, conversation)
            self.store.mutate(request)
            return self.store.state({'A': conversation})['projects']['A']['shots']['장면']['takes'][-1]

        legacy = add_take(self.default, 'default.png', 32)
        # Simulate an existing pre-conversation take, which has no owner field.
        with self.store.connect() as db:
            body = json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            body['projects']['A']['shots']['장면']['takes'][0].pop('conversation_id')
            db.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(body),))
        other = self.create_session()
        shared = add_take(other, 'approved.png', 33)
        self.store.mutate(self.request('review_take', {'shot': '장면', 'take': shared['id'],
            'decision': 'approved', 'reason': '검토'}, other))
        private = add_take(other, 'private.png', 34)
        self.store.mutate(self.request('review_take', {'shot': '장면', 'take': private['id'],
            'decision': 'changes_requested', 'reason': '비공개 수정 의견'}, other))

        http = server(self.tmp.name, 0)
        thread = Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{http.server_port}/api/state'
            def get(conversation):
                with urlopen(base + '?' + urlencode({'song': 'A', 'conversation': conversation})) as response:
                    self.assertEqual(response.status, 200)
                    return json.load(response)['projects']['A']
            first, second = get(self.default), get(other)
            first_assets = {node['label'] for node in first['lineage']['nodes'] if node['type'] == 'asset'}
            second_assets = {node['label'] for node in second['lineage']['nodes'] if node['type'] == 'asset'}
            self.assertEqual(first_assets, {legacy['filename'], shared['filename']})
            self.assertEqual(second_assets, {legacy['filename'], shared['filename'], private['filename']})
            self.assertNotIn(private['sha256'], json.dumps(first['lineage']))
            self.assertEqual({take['id'] for take in first['shots']['장면']['takes']}, {legacy['id'], shared['id']})
            self.assertEqual({take['id'] for take in second['shots']['장면']['takes']}, {legacy['id'], shared['id'], private['id']})
            self.assertNotIn('비공개 수정 의견', json.dumps(first['shots']['장면'], ensure_ascii=False))
            self.assertIn('비공개 수정 의견', json.dumps(second['shots']['장면'], ensure_ascii=False))
            for project in (first, second):
                nodes = {node['id'] for node in project['lineage']['nodes']}
                self.assertTrue(all(edge['source'] in nodes and edge['target'] in nodes for edge in project['lineage']['edges']))
            with self.assertRaises(ValueError):
                self.store.mutate(self.request('select', {'shot': '장면', 'take': private['id'],
                    'shot_revision': first['shots']['장면']['revision']}, self.default))
            reopened = Store(self.tmp.name).state({'A': self.default})['projects']['A']
            self.assertNotIn(private['filename'], json.dumps(reopened['lineage']))
        finally:
            http.shutdown()
            http.server_close()
            thread.join()

    @unittest.skipUnless(shutil.which('ffprobe'), 'Media probe required')
    def test_http_reference_scope_and_existing_reference_history(self):
        from app import server
        self.store.mutate(self.request('shot', {'shot': '장면', 'description': '합성'}, self.default))
        other = self.create_session()
        image = SyntheticImageAdapter().generate({'prompt': 'synthetic', 'width': 34, 'height': 32})['bytes']
        self.store.mutate(self.request('take', {'shot': '장면', 'shot_revision': 0,
            'filename': 'private.png', 'content': base64.b64encode(image).decode(),
            'reason': '합성 자료', 'rights': '직접 제작'}, other))
        private = self.store.state({'A': other})['projects']['A']['shots']['장면']['takes'][0]
        reference = dict(shot='장면', role='start_frame', source_song='A', source_shot='장면',
            source_take=private['id'], reason='비공개 참고 이유')
        self.store.mutate(self.request('assign_reference', {**reference, 'shot_revision': 1}, other))
        self.store.mutate(self.request('review_reference', {'shot': '장면', 'shot_revision': 2,
            'version': 1, 'decision': 'approved', 'reason': '참고 승인'}, other))
        self.store.mutate(self.request('select', {'shot':'장면', 'take':private['id'], 'shot_revision':3}, other))
        private_prep=self.store.mutate(self.request('prepare_generation', {'shot':'장면','shot_revision':4,
            'prompt':'대화 B 비공개 영상 지시'},other))['preparation']

        http = server(self.tmp.name, 0)
        thread = Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{http.server_port}'
            def get(conversation):
                with urlopen(base + '/api/state?' + urlencode({'song': 'A', 'conversation': conversation})) as r:
                    self.assertEqual(r.status, 200)
                    return json.load(r)
            def post(request, token):
                req = Request(base + '/api/action', data=json.dumps(request).encode(),
                    headers={'Content-Type': 'application/json', 'X-Loretune-Token': token})
                try:
                    with urlopen(req) as response:
                        return response.status, json.load(response)
                except HTTPError as error:
                    with error:
                        return error.code, json.load(error)

            def context_targets(conversation):
                token=get(conversation)['token']
                status,handoff=post(self.request('model_handoff',{},conversation),token)
                self.assertEqual(status,200)
                status,result=post(self.request('production_run',{},conversation),token)
                self.assertEqual(status,200)
                call=dict(id=uuid.uuid4().hex,name='search_project_context',arguments={'query':'합성'},complete=True)
                status,result=post(self.request('production_tool',{'run':result['run']['id'],'call':call},conversation),token)
                self.assertEqual(status,200)
                return handoff['handoff'],result['tool']['execution_targets']

            first = get(self.default)
            first_project = first['projects']['A']
            own = get(other)['projects']['A']
            self.assertNotIn(private['sha256'], json.dumps(first_project))
            self.assertNotIn('비공개 참고 이유', json.dumps(first_project, ensure_ascii=False))
            self.assertNotIn('대화 B 비공개 영상 지시', json.dumps(first_project,ensure_ascii=False))
            self.assertIn(private['sha256'], json.dumps(own))
            self.assertIn('대화 B 비공개 영상 지시',json.dumps(own,ensure_ascii=False))
            self.assertEqual(own['shots']['장면']['reference_head'], 1)
            self.assertIsNone(first_project['shots']['장면']['reference_head'])
            self.assertEqual(first_project['shots']['장면']['reference_visibility']['hidden_versions'], 1)
            handoff,search=context_targets(self.default)
            for value in (handoff,search):
                self.assertNotIn(private['sha256'],json.dumps(value))
                self.assertNotIn(private['asset'],json.dumps(value))
                self.assertNotIn('비공개 참고 이유',json.dumps(value,ensure_ascii=False))
            self.assertIsNone(handoff['execution_targets']['shots'][0]['selected_take'])
            self.assertIsNone(search['shots'][0]['selected_take'])
            self.assertIsNone(handoff['context']['value']['approved_shots'][0]['selected'])
            own_handoff,own_search=context_targets(other)
            for value in (own_handoff,own_search):
                self.assertIn(private['sha256'],json.dumps(value))
                self.assertNotIn(private['asset'],json.dumps(value))
            hidden_review = self.request('review_reference', {'shot': '장면',
                'shot_revision': first_project['shots']['장면']['revision'], 'version': 1,
                'decision': 'approved', 'reason': '확인'}, self.default)
            self.assertEqual(post(hidden_review, first['token'])[0], 400)
            hidden_prepare = self.request('prepare_generation', {'shot': '장면',
                'shot_revision': first_project['shots']['장면']['revision'], 'prompt': '합성 테스트'}, self.default)
            self.assertEqual(post(hidden_prepare, first['token'])[0], 400)
            hidden_start=self.request('start_generation',{'shot':'장면','preparation':private_prep},self.default)
            start_status,start_body=post(hidden_start,first['token'])
            self.assertEqual(start_status,400)
            self.assertIn('다른 대화',start_body['error'])
            rejected = self.request('assign_reference', {**reference, 'shot_revision': first_project['shots']['장면']['revision']}, self.default)
            status, _ = post(rejected, first['token'])
            self.assertEqual(status, 400)
            rejected_reuse = self.request('reuse_take', {'shot': '장면',
                'shot_revision': first_project['shots']['장면']['revision'], 'source_song': 'A',
                'source_shot': '장면', 'source_take': private['id'], 'reason': '재사용'}, self.default)
            self.assertEqual(post(rejected_reuse, first['token'])[0], 400)
            self.assertEqual(len(self.store.state()['projects']['A']['shots']['장면']['reference_versions']), 1)

            self.store.mutate(self.request('review_take', {'shot': '장면', 'take': private['id'],
                'decision': 'approved', 'reason': '공유 승인'}, other))
            visible = get(self.default)['projects']['A']
            self.assertIn(private['sha256'], json.dumps(visible))
            self.assertNotIn('대화 B 비공개 영상 지시',json.dumps(visible,ensure_ascii=False))
            self.assertEqual(visible['shots']['장면']['reference_head'], 1)
            visible_handoff,visible_search=context_targets(self.default)
            for value in (visible_handoff,visible_search):
                self.assertIn(private['sha256'],json.dumps(value))
                self.assertNotIn(private['asset'],json.dumps(value))
            self.assertEqual(visible_handoff['execution_targets']['shots'][0]['selected_take'],private['id'])
            self.assertEqual(visible_search['shots'][0]['selected_take'],private['id'])
            import guided
            self.assertEqual(visible_handoff['context']['sha256'],guided.fingerprint(visible_handoff['context']['value']))
            allowed_review = self.request('review_reference', {'shot': '장면',
                'shot_revision': visible['shots']['장면']['revision'], 'version': 1,
                'decision': 'approved', 'reason': '확인'}, self.default)
            self.assertEqual(post(allowed_review, first['token'])[0], 200)
            visible = get(self.default)['projects']['A']
            allowed_prepare = self.request('prepare_generation', {'shot': '장면',
                'shot_revision': visible['shots']['장면']['revision'], 'prompt': '합성 테스트'}, self.default)
            self.assertEqual(post(allowed_prepare, first['token'])[0], 200)
            visible = get(self.default)['projects']['A']
            allowed = self.request('assign_reference', {**reference, 'shot_revision': visible['shots']['장면']['revision']}, self.default)
            self.assertEqual(post(allowed, first['token'])[0], 200)
            visible = get(self.default)['projects']['A']
            allowed_reuse = self.request('reuse_take', {'shot': '장면',
                'shot_revision': visible['shots']['장면']['revision'], 'source_song': 'A',
                'source_shot': '장면', 'source_take': private['id'], 'reason': '재사용'}, self.default)
            self.assertEqual(post(allowed_reuse, first['token'])[0], 200)
            reopened = Store(self.tmp.name).state({'A': self.default})['projects']['A']
            self.assertEqual(len(reopened['shots']['장면']['reference_versions']), 2)
            self.store.mutate(self.request('review_take', {'shot': '장면', 'take': private['id'],
                'decision': 'changes_requested', 'reason': '공유 검토 변경'}, other))
            hidden_again = get(self.default)['projects']['A']['shots']['장면']
            self.assertEqual(hidden_again['reference_versions'], [])
            self.assertIsNone(hidden_again['reference_head'])
            self.assertEqual(hidden_again['reference_visibility']['hidden_versions'], 2)
            self.assertEqual(len(Store(self.tmp.name).state()['projects']['A']['shots']['장면']['reference_versions']), 2)
            hidden_handoff,hidden_search=context_targets(self.default)
            self.assertIsNone(hidden_handoff['execution_targets']['shots'][0]['selected_take'])
            self.assertIsNone(hidden_search['shots'][0]['selected_take'])
            self.assertIsNone(hidden_handoff['context']['value']['approved_shots'][0]['selected'])
        finally:
            http.shutdown()
            http.server_close()
            thread.join()

    @unittest.skipUnless(shutil.which('ffprobe'), 'Media probe required')
    def test_reference_source_cannot_bypass_scope_across_projects(self):
        def call(action, **data):
            return self.store.mutate(dict(action=action, data=data, revision=self.store.state()['revision'],
                                          request_id=uuid.uuid4().hex))
        call('project', name='B', era='default', story=0)
        call('shot', song='A', shot='목적', description='합성')
        call('shot', song='B', shot='원본', description='합성')
        image = SyntheticImageAdapter().generate({'prompt': 'synthetic', 'width': 32, 'height': 32})['bytes']
        call('take', song='B', shot='원본', shot_revision=0, filename='fixture.png',
             content=base64.b64encode(image).decode(), reason='합성 자료', rights='직접 제작')
        reference = dict(song='A', shot='목적', shot_revision=0, role='style', source_song='B',
                         source_shot='원본', source_take=1, reason='참고')
        with self.assertRaisesRegex(ValueError, '미승인 Take'):
            call('assign_reference', **reference)
        self.assertFalse(self.store.state()['projects']['A']['shots']['목적'].get('reference_versions'))
        call('review_take', song='B', shot='원본', take=1, decision='approved', reason='공유 승인')
        call('assign_reference', **reference)
        state = self.store.state({'A': self.default})['projects']['A']
        self.assertEqual(state['shots']['목적']['reference_versions'][0]['roles']['style']['song'], 'B')

    @unittest.skipUnless(shutil.which('ffprobe'), 'Media probe required')
    def test_http_start_generation_rechecks_cross_project_take_approval(self):
        import ledger
        from app import server
        def call(action, **data):
            return self.store.mutate(dict(action=action, data=data, revision=self.store.state()['revision'],
                                          request_id=uuid.uuid4().hex))
        call('project', name='B', era='default', story=0)
        call('shot', song='A', shot='목적', description='합성')
        call('shot', song='B', shot='원본', description='합성')
        image = SyntheticImageAdapter().generate({'prompt': 'synthetic', 'width': 32, 'height': 32})['bytes']
        call('take', song='B', shot='원본', shot_revision=0, filename='fixture.png',
             content=base64.b64encode(image).decode(), reason='합성 자료', rights='직접 제작')
        call('review_take', song='B', shot='원본', take=1, decision='approved', reason='공유 승인')
        call('assign_reference', song='A', shot='목적', shot_revision=0, role='start_frame',
             source_song='B', source_shot='원본', source_take=1, reason='합성 참고')
        call('review_reference', song='A', shot='목적', shot_revision=1,
             version=1, decision='approved', reason='참고 승인')
        prep_id = call('prepare_generation', song='A', shot='목적', shot_revision=2,
                       prompt='합성 테스트')['preparation']
        prep = self.store.state()['projects']['A']['shots']['목적']['generation_preparations'][0]
        gate = dict(expires=time.time()+60, maximum_calls=1, maximum_units=1_000_000,
            model=prep['estimate']['model'], workspace_id=self.store.workspace_id, song='A', shot='목적',
            image_sha256=prep['source']['sha256'], prompt_sha256=hashlib.sha256(prep['prompt'].encode()).hexdigest(),
            privacy='private', retention_seconds=3600, duration=10, generate_audio=False,
            price_money=prep['estimate']['money'], price_checked_at=time.time())
        calls = []
        class FakeAdapter:
            mode = 'contract-fake'
            def submit(self, data):
                calls.append(data)
                return {'request_id': 'fake-fixture'}
        http = server(self.tmp.name, 0, provider_adapter=FakeAdapter(), generation_approval=gate)
        scope = 'project:' + http.store.state()['project_ids']['A']
        with http.store.connect() as db:
            ledger.patch_budget(db, http.store.workspace_id, scope,
                dict(limit={'amount':'1', 'currency':'USD'}, maxConcurrentJobs=1, allowAutomaticRetries=False), 0)
        thread = Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            base = f'http://127.0.0.1:{http.server_port}'
            def start():
                with urlopen(base+'/api/state?'+urlencode({'song':'A', 'conversation':self.default})) as response:
                    state=json.load(response)
                active=state['projects']['A']['active_conversation']
                payload=dict(action='start_generation', data=dict(song='A', shot='목적', preparation=prep_id),
                    revision=state['revision'], request_id=uuid.uuid4().hex, conversation_id=self.default,
                    conversation_revision=active['revision'], shared_version=active['shared_version'])
                request=Request(base+'/api/action',data=json.dumps(payload).encode(),
                    headers={'Content-Type':'application/json', 'X-Loretune-Token':state['token']})
                try:
                    with urlopen(request) as response:return response.status,json.load(response)
                except HTTPError as error:
                    with error:return error.code,json.load(error)
            call('review_take', song='B', shot='원본', take=1, decision='changes_requested', reason='공유 철회')
            status, body = start()
            self.assertEqual(status,400)
            self.assertIn('미승인 Take',body['error'])
            self.assertEqual(calls,[])
            with http.store.connect() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM generation_jobs').fetchone()[0],0)
            call('review_take', song='B', shot='원본', take=1, decision='approved', reason='공유 재승인')
            status, body = start()
            self.assertEqual(status,200)
            job_id=body['job'];self.assertTrue(job_id)
            self.assertEqual(calls,[])
            call('review_take', song='B', shot='원본', take=1, decision='changes_requested', reason='제출 직전 공유 철회')
            self.assertTrue(http.store.process_generation())
            self.assertEqual(calls,[])
            job=http.store.generation.get(job_id)
            self.assertEqual(job['state'],'submission_blocked')
            self.assertTrue(job['verified_unsubmitted'])
            with http.store.connect() as db:
                self.assertEqual(db.execute('SELECT state FROM reservations WHERE id=?',(job['reservation'],)).fetchone()[0],'cancelled')
        finally:
            http.shutdown()
            http.server_close()
            thread.join()

    @unittest.skipUnless(shutil.which('ffprobe'), 'Media probe required')
    def test_http_execution_cards_are_conversation_scoped(self):
        from app import server
        with self.store.connect() as db:
            body=json.loads(db.execute('SELECT body FROM state').fetchone()[0])
            body['projects']['A'].update(music_head=1,music_versions=[dict(id=1,audio=1,start=0,end=2)])
            db.execute('UPDATE state SET body=?',(json.dumps(body),))
        other=self.create_session()
        plan_id=self.store.mutate(self.request('guided_plan', {'goal':'합성', 'scenes':'비공개 합성 장면',
            'style':'', 'constraints':'', 'kind':'narrative'}, other))['plan']
        self.store.mutate(self.request('apply_guided_plan', {'plan':plan_id}, other))
        plan=self.store.state({'A':other})['projects']['A']['guided_plans'][0]
        card=self.store.mutate(self.request('action_propose', {'plan':plan_id,
            'scene':plan['scenes'][0]['id']}, other))['execution_card']
        http=server(self.tmp.name,0)
        thread=Thread(target=http.serve_forever,daemon=True)
        thread.start()
        try:
            base=f'http://127.0.0.1:{http.server_port}'
            def get(cid):
                with urlopen(base+'/api/state?'+urlencode({'song':'A','conversation':cid})) as response:
                    return json.load(response)
            def post(cid,action,data):
                state=get(cid);active=state['projects']['A']['active_conversation']
                payload=dict(action=action,data=dict(song='A',**data),revision=state['revision'],
                    request_id=uuid.uuid4().hex,conversation_id=cid,conversation_revision=active['revision'],
                    shared_version=active['shared_version'])
                request=Request(base+'/api/action',data=json.dumps(payload).encode(),
                    headers={'Content-Type':'application/json','X-Loretune-Token':state['token']})
                try:
                    with urlopen(request) as response:return response.status,json.load(response)
                except HTTPError as error:
                    with error:return error.code,json.load(error)
            default=get(self.default)['projects']['A']
            self.assertFalse(default.get('execution_cards'))
            self.assertNotIn(card['id'],json.dumps(default.get('rehearsal_jobs',[])))
            status,_=post(self.default,'action_decide',dict(id=card['id'],card_revision=card['revision'],decision='approved'))
            self.assertEqual(status,400)
            status,body=post(other,'action_decide',dict(id=card['id'],card_revision=card['revision'],decision='approved'))
            self.assertEqual(status,200);card=body['execution_card']
            default=get(self.default)['projects']['A']
            self.assertFalse(default.get('execution_cards'))
            self.assertNotIn(card['job'],json.dumps(default.get('rehearsal_jobs',[])))
            self.assertEqual(post(self.default,'action_execute',dict(id=card['id'],card_revision=card['revision']))[0],400)
            status,body=post(other,'action_execute',dict(id=card['id'],card_revision=card['revision']))
            self.assertEqual(status,200);card=body['execution_card']
            self.assertEqual(get(self.default)['projects']['A']['shots'][card['shot']]['takes'],[])
            self.assertEqual(post(self.default,'action_review',dict(id=card['id'],card_revision=card['revision'],decision='approved'))[0],400)
            status,body=post(other,'action_review',dict(id=card['id'],card_revision=card['revision'],decision='approved'))
            self.assertEqual(status,200);card=body['execution_card']
            default=get(self.default)['projects']['A'];self.assertFalse(default.get('execution_cards'))
            self.assertEqual(default['shots'][card['shot']]['takes'][0]['id'],card['take'])
            reopened=Store(self.tmp.name).state({'A':other})['projects']['A']
            self.assertEqual(reopened['execution_cards'][0]['result_decision'],'approved')
        finally:
            http.shutdown();http.server_close();thread.join()

    def test_http_motion_frame_requires_owning_conversation(self):
        import production_context
        from tests.test_motion import scene
        from app import server
        self.store.mutate(self.request('shot',{'shot':'모션','description':'합성'},self.default))
        other=self.create_session()
        project=self.store.state({'A':other})['projects']['A']
        proposal=self.store.mutate(self.request('motion_propose',{
            'shot_id':production_context.shot_id(project,'모션'),'base_motion_revision':0,'scene':scene()},other))['motion']['proposal_id']
        http=server(self.tmp.name,0);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            base=f'http://127.0.0.1:{http.server_port}/api/motion-frame'
            def get(cid=None):
                query={'song':'A','proposal':proposal,'frame':'0'}
                if cid is not None:query['conversation']=cid
                try:
                    with urlopen(base+'?'+urlencode(query)) as response:return response.status,response.read()
                except HTTPError as error:
                    with error:return error.code,error.read()
            self.assertEqual(get()[0],400)
            self.assertEqual(get(self.default)[0],400)
            status,body=get(other);self.assertEqual(status,200);self.assertTrue(body.startswith(b'\x89PNG\r\n\x1a\n'))
        finally:
            http.shutdown();http.server_close();thread.join()
