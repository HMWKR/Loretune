"""General chat -> existing image action, isolated HTTP/SQLite; no model calls."""
import base64
from copy import deepcopy
import hashlib
import io
import json
import time
import unittest
import wave
from unittest.mock import patch

import chat_general
import guided
import production_context
from app import Store
from fal_dispatch import FalDispatch
from fal_model_adapter import FalModelAdapter
from fal_models import CONNECTION, Contract
from tests import test_chat_general_http as base
from tests.test_chat_runtime import response, use


class GeneralChatMediaPreparationTest(unittest.TestCase):
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.post('model_settings', song='A', selections={'image':'fal-flux-schnell'},
                  model_revision=self.project()['model_settings']['revision'])
        audio = io.BytesIO()
        with wave.open(audio, 'wb') as stream:
            stream.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
            stream.writeframes(b'\0\0' * 40000)
        self.post('audio', song='A', filename='owned-fixture.wav',
                  content=base64.b64encode(audio.getvalue()).decode(), rights='self-authored fixture')
        self.post('music_structure', song='A', audio=1, start=0, end=5, sections=[])
        plan = self.post('guided_plan', song='A', goal='음원에서 시작', scenes='푸른 음악 무대', kind='visualizer')['plan']
        self.post('apply_guided_plan', song='A', plan=plan)
        self.model = Contract('fal-flux-schnell')
        self.prompt = '음원의 리듬을 담은 푸른 음악 무대'
        payload = self.model.payload(self.prompt, {'ratio':'16:9'})
        quote = dict(provider='fal.ai', model=self.model.MODEL,
                     money={'amount':'0.01','currency':'USD'},
                     input_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
                     kind='fixture', price_revision='synthetic-not-real', source=self.model.spec['source'],
                     expires=time.time()+300)
        self.submissions = []
        def forbid_submission(*args):
            self.submissions.append(args)
            raise AssertionError('preparation must not submit to a provider')
        adapter = FalModelAdapter('fal-flux-schnell', quote=quote, transport=forbid_submission)
        self.f.http.store.media_dispatch = FalDispatch(self.f.http.store, [adapter])

    def post(self, action, **data):
        status, result = self.f.action(action, **data)
        self.assertEqual(status, 200, result)
        return result

    def project(self):
        return self.f.state()['projects']['A']

    def arguments(self):
        project = self.project()
        return dict(shot_id=production_context.shot_id(project, '장면 1'), model_id='fal-flux-schnell',
                    model_reason='프로젝트 이미지 모델과 같은 저비용 모델', prompt=self.prompt, ratio='16:9', shot_revision=project['shots']['장면 1']['revision'])

    def send_tool(self, name, arguments, preview=None):
        self.f.http.store.general_chat_runtime.transport.responses = [response([use('media-call', name, arguments)], 'tool_use')]
        first = preview or self.f.preview()
        status, result = self.f.approve(first)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        return self.project()

    def actions(self):
        with self.f.http.store.connect() as c:
            return [value for row in c.execute('SELECT body FROM production_actions')
                    if (value := json.loads(row[0]))['connection_id'] == CONNECTION]

    def assert_no_media_execution(self):
        self.assertEqual(self.submissions, [])
        self.assertEqual(self.f.state()['generation_jobs'], [])
        self.assertEqual(self.f.state()['jobs'], [])
        with self.f.http.store.connect() as c:
            for table in ('execution_grants', 'provider_action_jobs', 'generation_jobs'):
                self.assertEqual(c.execute('SELECT count(*) FROM '+table).fetchone()[0], 0, table)
            self.assertEqual(c.execute("SELECT count(*) FROM reservations r JOIN budgets b ON b.id=r.budget WHERE b.scope LIKE 'project:%'").fetchone()[0], 0)

    def test_image_prepare_saves_one_card_and_http_replay_is_idempotent(self):
        requests = []
        original = self.f.http.store.mutate
        def record(request):
            if request['action'] == 'production_tool':
                requests.append(deepcopy(request))
            return original(request)
        with patch.object(self.f.http.store, 'mutate', side_effect=record):
            project = self.send_tool('prepare_image_action', self.arguments())
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
        card, = project['media_actions']
        self.assertEqual((card['model'], card['prompt'], card['options']),
                         (self.model.MODEL, self.prompt, {'ratio':'16:9'}))
        self.assertEqual(card['approval'], 'required')
        self.assertFalse(card['can_execute'])
        self.assertFalse(card['can_approve'])
        self.assertEqual(card['estimate'], {'amount':'0.01','currency':'USD'})
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual((result['external_calls'], result['approval'], result['action_id']),
                         (0, 'required', card['id']))
        stored, = self.actions()
        status, replay = self.f.send(requests[0])
        self.assertEqual(status, 200, replay)
        self.assertEqual(self.actions(), [stored])
        self.assertEqual(Store(self.f.tmp.name).state()['projects']['A']['media_actions'][0]['id'], card['id'])
        self.assert_no_media_execution()

    def test_capability_catalog_is_read_only_and_not_live_execution_proof(self):
        self.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=0,
                  mode='read_only', effort='low')
        preview = self.f.preview()
        self.assertIn('get_model_capabilities', preview['tool_scope'])
        self.assertNotIn('prepare_image_action', preview['tool_scope'])
        project = self.send_tool('get_model_capabilities', {'role':'image'}, preview)
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual(result['status'], 'succeeded')
        self.assertTrue(result['models'])
        self.assertFalse(result['live_execution'])
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_old_manifest_cannot_gain_new_preparation_tool(self):
        old_scope = tuple(name for name in chat_general.ALLOWED_TOOLS
                          if name not in {'get_model_capabilities','prepare_image_action'})
        with patch.object(chat_general, 'ALLOWED_TOOLS', old_scope):
            old = self.f.preview()
        self.assertNotIn('prepare_image_action', old['tool_scope'])
        project = self.send_tool('prepare_image_action', self.arguments(), old)
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_read_only_cannot_prepare_even_if_model_returns_unlisted_tool(self):
        self.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=0,
                  mode='read_only', effort='low')
        project = self.send_tool('prepare_image_action', self.arguments())
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_stale_shot_revision_does_not_persist_action(self):
        arguments = self.arguments()
        arguments['shot_revision'] += 1
        project = self.send_tool('prepare_image_action', arguments)
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual(result['code'], 'INVALID_MEDIA_INPUT')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_changed_music_blocks_old_applied_plan_with_current_chat_context(self):
        old_plan = deepcopy(self.project()['guided_plans'][-1])
        self.post('music_structure', song='A', audio=1, start=0, end=4, sections=[])
        project = self.project()
        self.assertEqual(project['guided_plans'][-1], old_plan)
        self.assertEqual(old_plan['status'], 'applied')
        self.assertNotEqual(old_plan['context_hash'], guided.fingerprint(guided.context(project)))
        arguments = self.arguments()
        self.assertEqual(arguments['shot_revision'], project['shots']['장면 1']['revision'])
        current = self.send_tool('prepare_image_action', arguments)
        self.assertEqual(current['production_runs'][-1]['calls'][-1]['result']['code'], 'INVALID_MEDIA_INPUT')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_missing_adapter_blocks_without_enabling_catalog_model(self):
        self.f.http.store.media_dispatch.adapters.clear()
        project = self.send_tool('prepare_image_action', self.arguments())
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual(result['code'], 'MODEL_CONNECTION_OR_PRICE_REQUIRED')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_foreign_project_shot_is_not_a_current_execution_target(self):
        self.post('project', name='B', era='default', story=0)
        self.post('shot', song='B', shot='private', description='other project')
        arguments = self.arguments()
        arguments['shot_id'] = production_context.shot_id(self.f.state()['projects']['B'], 'private')
        project = self.send_tool('prepare_image_action', arguments)
        self.assertEqual(project['production_runs'][-1]['calls'][-1]['result']['code'], 'INVALID_MEDIA_INPUT')
        self.assertEqual(self.actions(), [])
        self.assert_no_media_execution()

    def test_other_conversation_cannot_review_private_prepared_action(self):
        project = self.send_tool('prepare_image_action', self.arguments())
        card, = project['media_actions']
        cid = self.post('conversation_create', song='A', title='other')['conversation']['id']
        self.assertEqual(self.f.session_state(cid)['projects']['A']['media_actions'], [])
        status, _ = self.f.session_action(cid, 'media_action_decide', song='A', action_id=card['id'], decision='rejected')
        self.assertEqual(status, 400)
        self.assertEqual(self.project()['media_actions'][0]['approval'], 'required')
        self.assert_no_media_execution()

    def test_hold_and_reject_persist_without_grant_or_automatic_execution(self):
        project = self.send_tool('prepare_image_action', self.arguments())
        card, = project['media_actions']
        for decision in ('held', 'rejected'):
            self.post('media_action_decide', song='A', action_id=card['id'], decision=decision)
            current, = self.project()['media_actions']
            self.assertEqual(current['approval'], decision)
            self.assertFalse(current['can_execute'])
        self.assertEqual(len(self.actions()), 1)
        self.assert_no_media_execution()


if __name__ == '__main__':
    unittest.main()
