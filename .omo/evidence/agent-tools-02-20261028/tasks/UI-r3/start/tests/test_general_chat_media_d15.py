"""A2a: D15 media proposals, S15 provenance, D19 unit prices, D20 cap, S9/D21 settings.

Isolated HTTP/SQLite and in-process Store fixtures only. No model, provider,
count_tokens or paid call: fal transports fail the test if reached.
"""
import base64
import hashlib
import json
import os
import time
import unittest
import uuid
from copy import deepcopy

import agent_preferences
import chat_general
import chat_models
import chat_protocols
import chat_sessions
import editing
import fal_models
import guided
import ledger
import production_context
from app import Store
from fal_dispatch import CURRENT_CATALOG_PRICE, FalDispatch, NO_RECORD
from fal_model_adapter import FalModelAdapter
from fal_models import Contract
from image_adapter import SyntheticImageAdapter
from tests import test_general_chat_media_preparation as media
from tests import test_fal_multimodel as multi
from tests import test_general_chat_motion as motion
from tests.test_scene_contract import sample as scene_sample
from tests.test_chat_runtime import response as chat_response, use as chat_use

REASON = '프로젝트 기본보다 품질이 높은 모델을 제안합니다.'
PROVENANCE_KEYS = {'engine', 'chat_model', 'permission_mode', 'effort', 'run', 'call'}


def quote_for(contract, payload, amount='0.01'):
    return dict(provider='fal.ai', model=contract.MODEL, money={'amount':amount,'currency':'USD'},
                input_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), kind='fixture', price_revision='synthetic-not-real',
                source=contract.spec['source'], expires=time.time()+300)


def settings_state(store):
    """Every user-owned setting an agent tool must never change, read from the stored state.

    The browser projection omits chat_sessions, so agent settings are read from SQLite.
    """
    with store.connect() as c:
        project, = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'].values()
    sessions = {s['id']:(deepcopy(s.get('agent_settings')), deepcopy(s.get('agent_settings_history'))) for s in project.get('chat_sessions', [])}
    return deepcopy(project.get('model_settings')), sessions


class GeneralChatImageD15Test(unittest.TestCase):
    """Image path through the real general chat turn (contract-fake transport)."""
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.f = self.m.f
        self.store = self.f.http.store
        # A second image model the project did NOT select, with its own input-bound fixture quote.
        pro = Contract('fal-flux-pro-1-1')
        self.pro_quote = quote_for(pro, pro.payload(self.m.prompt, {'ratio':'16:9'}), '0.04')
        self.store.media_dispatch.adapters['fal-flux-pro-1-1'] = FalModelAdapter(
            'fal-flux-pro-1-1', quote=self.pro_quote, transport=lambda *a: self.fail('no provider submission'))

    def set_agent(self, mode, effort='low'):
        revision = self.m.project()['agent_preferences']['by_model']['anthropic-haiku-5-5']['revision']
        self.m.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=revision,
                    mode=mode, effort=effort)

    def sent_effort(self):
        with self.store.connect() as c:
            bodies = [json.loads(r[0]) for r in c.execute('SELECT body FROM general_chat_previews ORDER BY rowid')]
        return bodies[0]['message_body']['output_config']['effort']

    def test_agent_image_proposal_records_reason_provenance_and_prices_on_every_surface(self):
        for mode, effort in (('review', 'medium'), ('full_access', 'high')):
            with self.subTest(mode=mode):
                self.setUp()
                self.set_agent(mode, effort)
                before = settings_state(self.store)
                project = self.m.send_tool('prepare_image_action', self.m.arguments())
                self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
                run = project['production_runs'][-1]
                result = run['calls'][-1]['result']
                self.assertEqual(result['status'], 'proposed')
                self.assertEqual((result['actor'], result['model_reason'], result['model_reason_label']),
                                 ('agent', self.m.arguments()['model_reason'], '모델이 제시한 이유(검증 안 됨)'))
                self.assertEqual(set(result['provenance']), PROVENANCE_KEYS)
                self.assertEqual(result['provenance']['permission_mode'], mode)
                # Effort recorded = effort actually in the sent message body.
                self.assertEqual(result['provenance']['effort'], effort)
                self.assertEqual(self.sent_effort(), effort)
                self.assertEqual((result['provenance']['engine'], result['provenance']['chat_model'],
                                  result['provenance']['run'], result['provenance']['call']),
                                 ('contract-fake', 'claude-haiku-5-5', run['id'], run['calls'][-1]['id']))
                self.assertEqual((result['project_selection'], result['differs_from_project']), ('fal-flux-schnell', False))
                unit = result['price']['unit_price']
                self.assertEqual((unit['amount'], unit['unit'], unit['kind'], unit['revision']),
                                 ('0.003', 'megapixel', 'documented-estimate', fal_models.PRICE_REVISION))
                self.assertTrue(unit['source'].startswith('https://fal.ai/models/'))
                self.assertEqual(result['price']['expected_total'], {'amount':'0.003','currency':'USD'})
                # Fixture quote 0.01 vs documented 0.003: both shown, flagged, neither picked.
                self.assertEqual(result['price']['quote_total'], {'amount':'0.01','currency':'USD'})
                self.assertIs(result['price']['matches_quote'], False)
                self.assertIn('둘 다 표시', result['price']['mismatch'])
                self.assertGreater(result['quote_expires'], time.time())
                self.assertNotIn('basis', result['price'])  # recorded at preparation, not the current-catalog fallback
                card, = project['media_actions']
                reopened = Store(self.f.tmp.name).state()['projects']['A']['media_actions'][0]
                for surface in (card, reopened):
                    for key in ('actor', 'model_reason', 'model_reason_label', 'provenance', 'project_selection',
                                'differs_from_project', 'price', 'price_source', 'price_revision', 'quote_expires', 'record'):
                        self.assertEqual(surface[key], result[key], key)
                self.assertEqual(settings_state(self.store), before)
                self.m.assert_no_media_execution()

    def test_different_model_is_a_proposal_and_never_changes_project_settings(self):
        before = settings_state(self.store)
        arguments = self.m.arguments()
        arguments['model_id'] = 'fal-flux-pro-1-1'
        project = self.m.send_tool('prepare_image_action', arguments)
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual(result['status'], 'proposed')
        self.assertEqual((result['model'], result['project_selection'], result['differs_from_project']),
                         ('fal-ai/flux-pro/v1.1', 'fal-flux-schnell', True))
        self.assertEqual(result['price']['unit_price']['amount'], '0.04')
        self.assertEqual(result['price']['expected_total'], {'amount':'0.04','currency':'USD'})
        self.assertIs(result['price']['matches_quote'], True)
        self.assertEqual(settings_state(self.store), before)
        self.assertEqual(self.m.project()['model_settings']['selections']['image'], 'fal-flux-schnell')
        card, = project['media_actions']
        self.assertEqual((card['approval'], card['can_execute']), ('required', False))
        self.m.assert_no_media_execution()

    def test_missing_reason_is_a_schema_violation_like_any_missing_argument(self):
        arguments = self.m.arguments();del arguments['model_reason']
        project = self.m.send_tool('prepare_image_action', arguments)
        # A missing required key fails response validation, as for every other argument.
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertEqual(self.m.actions(), [])
        self.m.assert_no_media_execution()

    def test_empty_or_long_reason_is_a_repairable_result_and_the_turn_continues(self):
        for reason in ('', '   ', 'x'*301, '가'*301):
            with self.subTest(reason=len(reason)):
                self.setUp()
                arguments = self.m.arguments();arguments['model_reason'] = reason
                project = self.m.send_tool('prepare_image_action', arguments)
                turn = project['general_chat_turns'][-1]
                # Not outcome_unknown: the conversation is not locked and nothing was saved.
                self.assertEqual(turn['status'], 'awaiting_continuation_approval')
                result = project['production_runs'][-1]['calls'][-1]['result']
                self.assertEqual(result, dict(status='invalid_arguments', code='MODEL_REASON_1_TO_300_CHARACTERS', retryable=True))
                self.assertEqual(self.m.actions(), [])
                follow = project['general_chat_previews'][-1]
                self.assertIn('MODEL_REASON_1_TO_300_CHARACTERS', json.dumps(follow['message_body']))
                # The next round (approved by the human) repairs the reason and saves one action.
                self.f.http.store.general_chat_runtime.transport.responses = [chat_response([chat_use('media-fix', 'prepare_image_action', self.m.arguments())], 'tool_use')]
                status, value = self.f.approve(follow)
                self.assertEqual(status, 200, value)
                self.assertTrue(self.store.general_chat_runtime.process_next())
                project = self.m.project()
                self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
                self.assertEqual(project['production_runs'][-1]['calls'][-1]['result']['status'], 'proposed')
                self.assertEqual(len(self.m.actions()), 1)
                self.m.assert_no_media_execution()

    def test_reason_limit_is_visible_to_the_model_in_schema_and_description(self):
        preview = self.f.preview()
        tools = {d['name']:d for d in preview['message_body']['tools']}
        for name in ('prepare_image_action', 'prepare_video_action', 'propose_scene_3d', 'propose_preference_rule'):
            with self.subTest(tool=name):
                definition = next(d for d in chat_protocols.tool_definitions('anthropic') if d['name'] == name)
                self.assertEqual(definition['input_schema']['properties']['model_reason'], dict(type='string', minLength=1, maxLength=300))
                # Strict Anthropic wire: bounds move into the property description (chat_models.anthropic_wire_schema).
                wire = tools[name]['input_schema']['properties']['model_reason']
                self.assertEqual(wire['type'], 'string')
                self.assertIn('"maxLength": 300', wire['description']);self.assertIn('"minLength": 1', wire['description'])
                openai = next(d for d in chat_protocols.tool_definitions('openai') if d['name'] == name)
                self.assertEqual(openai['parameters']['properties']['model_reason'], dict(type='string', minLength=1, maxLength=300))
        for name in ('prepare_image_action', 'prepare_video_action'):
            self.assertIn('model_reason (1-300 chars)', tools[name]['description'])

    def test_reason_at_300_characters_is_stored_verbatim(self):
        arguments = self.m.arguments()
        arguments['model_reason'] = ' 이유<b>"'+'가'*293
        self.assertEqual(len(arguments['model_reason']), 300)
        project = self.m.send_tool('prepare_image_action', arguments)
        self.assertEqual(project['media_actions'][0]['model_reason'], arguments['model_reason'])

    def test_read_only_cannot_prepare_video_but_can_read_settings_and_prices(self):
        self.set_agent('read_only')
        preview = self.f.preview()
        self.assertNotIn('prepare_video_action', preview['tool_scope'])
        self.assertIn('get_agent_settings', preview['tool_scope'])
        self.assertIn('get_model_capabilities', preview['tool_scope'])
        project = self.m.send_tool('get_model_capabilities', {'role':'image'}, preview)
        models = project['production_runs'][-1]['calls'][-1]['result']['models']
        schnell = next(m for m in models if m['id'] == 'fal-flux-schnell')
        self.assertEqual((schnell['unit_price']['amount'], schnell['unit_price']['kind']), ('0.003', 'documented-estimate'))

    def test_human_preparation_has_null_provenance_and_owner_label(self):
        project = self.m.project()
        prepared = self.m.post('media_prepare', song='A', shot='장면 1', shot_revision=project['shots']['장면 1']['revision'],
                               prompt=self.m.prompt, options={'ratio':'16:9'}, refs=[])
        card, = self.m.project()['media_actions']
        self.assertEqual((card['actor'], card['model_reason'], card['model_reason_label']),
                         ('local-owner', None, '프로젝트에서 사용자가 선택한 모델'))
        self.assertEqual(card['provenance'], dict.fromkeys(PROVENANCE_KEYS))
        self.assertEqual(card['record'], 'recorded')
        self.assertEqual(prepared['media_action']['action']['options']['proposal']['actor'], 'local-owner')
        self.m.assert_no_media_execution()

    def test_old_action_without_fields_projects_no_record_label(self):
        self.m.post('media_prepare', song='A', shot='장면 1', shot_revision=self.m.project()['shots']['장면 1']['revision'],
                    prompt=self.m.prompt, options={'ratio':'16:9'}, refs=[])
        with self.store.connect() as c:
            identifier, body = c.execute('SELECT id,body FROM production_actions').fetchone()
            value = json.loads(body);value['options'].pop('proposal')
            c.execute('UPDATE production_actions SET body=? WHERE id=?', (json.dumps(value), identifier))
        card, = self.m.project()['media_actions']
        self.assertEqual(card['record'], NO_RECORD)
        self.assertEqual(NO_RECORD, '출처 기록 없음(변경 전 준비)')
        self.assertIsNone(card['provenance'])
        self.assertEqual(card['price']['unit_price']['amount'], '0.003')
        # The unit price of an unrecorded action is today's catalog record, labelled as such.
        self.assertEqual(card['price']['basis'], CURRENT_CATALOG_PRICE)
        self.assertEqual(CURRENT_CATALOG_PRICE, '현재 카탈로그 단가(준비 시점 기록 없음)')
        # Same label on the model-facing surfaces: estimate items and the generation job lookup.
        plan = self.m.project()['guided_plans'][-1]['id']
        item, = self.direct('estimate_media_plan', {'plan_id':plan})['actions']
        job_id = 'job-'+uuid.uuid4().hex
        job = dict(id=job_id, state='imported', mode='contract-fake', external_calls=0, cost_confirmed=False, updated=time.time(),
                   context=dict(song='A', output_kind='image', action_binding=dict(workspace=self.store.workspace_id, project=self.f.pid,
                   action_id=identifier, plan_id=plan, plan_revision=1, release_id='fal-ai/flux/schnell', grant_id='g')))
        with self.store.connect() as c:
            c.execute('INSERT INTO generation_jobs (id,request_key,digest,body) VALUES (?,?,?,?)', (job_id, 'fixture:'+job_id, 'fixture', json.dumps(job)))
        pricing = self.direct('get_generation_job', {'job_id':job_id})['job']['pricing']
        for surface in (item, pricing):
            self.assertEqual((surface['record'], surface['provenance'], surface['actor'], surface['model_reason']), (NO_RECORD, None, None, None))
            self.assertEqual(surface['price']['basis'], CURRENT_CATALOG_PRICE)
            self.assertEqual(surface['price']['unit_price'], card['price']['unit_price'])
        with self.store.connect() as c:c.execute('DELETE FROM generation_jobs WHERE id=?', (job_id,))

    def test_estimate_items_and_generation_job_carry_the_same_price_and_origin(self):
        project = self.m.send_tool('prepare_image_action', self.m.arguments())
        prepared = project['production_runs'][-1]['calls'][-1]['result']
        plan = self.m.project()['guided_plans'][-1]['id']
        item, = self.direct('estimate_media_plan', {'plan_id':plan})['actions']
        for key in ('price', 'actor', 'model_reason', 'provenance', 'differs_from_project', 'price_revision'):
            self.assertEqual(item[key], prepared[key], key)
        job_id = 'job-'+uuid.uuid4().hex
        job = dict(id=job_id, state='imported', mode='contract-fake', external_calls=0, cost_confirmed=False, quote=dict(money={'amount':'0.01','currency':'USD'}),
                   updated=time.time(), context=dict(song='A', output_kind='image', action_binding=dict(workspace=self.store.workspace_id, project=self.f.pid,
                   action_id=prepared['action_id'], plan_id=plan, plan_revision=1, release_id='fal-ai/flux/schnell', grant_id='g')))
        with self.store.connect() as c:
            c.execute('INSERT INTO generation_jobs (id,request_key,digest,body) VALUES (?,?,?,?)', (job_id, 'fixture:'+job_id, 'fixture', json.dumps(job)))
        pricing = self.direct('get_generation_job', {'job_id':job_id})['job']['pricing']
        self.assertEqual(pricing['price'], prepared['price'])
        self.assertEqual(pricing['provenance'], prepared['provenance'])
        with self.store.connect() as c:c.execute('DELETE FROM generation_jobs WHERE id=?', (job_id,))
        self.m.assert_no_media_execution()

    def direct(self, name, arguments):
        run = self.m.post('production_run', song='A')['run']['id']
        return self.m.post('production_tool', song='A', run=run, call=dict(id=uuid.uuid4().hex, name=name, arguments=arguments, complete=True))['tool']

    def test_agent_settings_tool_reports_frozen_settings_and_cannot_change_them(self):
        self.set_agent('review', 'medium')
        before = settings_state(self.store)
        project = self.m.send_tool('get_agent_settings', {})
        result = project['production_runs'][-1]['calls'][-1]['result']
        self.assertEqual(result['status'], 'succeeded')
        model = result['chat_model']
        self.assertEqual((model['id'], model['selection_reason']), ('anthropic-haiku-5-5', '사용자가 선택한 모델'))
        self.assertEqual((model['price']['input_rate'], model['price']['output_rate'], model['price']['unit']), ('.1', '.5', 'USD per 1M tokens'))
        self.assertEqual(model['price']['long_context'], dict(threshold_input_tokens=100000, input_rate='.5', output_rate='2.5'))
        self.assertEqual((model['price']['source'], model['price']['revision']),
                         (chat_models.MODELS['anthropic-haiku-5-5']['source'], 'haiku-5-5-20261027-tiered'))
        self.assertEqual(result['effort'], 'medium')
        self.assertEqual(result['permission'], dict(saved='review', frozen='review', effective='review'))
        self.assertEqual(result['reservation'], dict(max_input_tokens=16384, max_output_tokens=4096, worst_per_round_micro=3687,
                                                     conversation_cap_micro=400000, worst_case_rounds_within_cap=108))
        self.assertIs(result['agent_can_change'], False)
        self.assertEqual(settings_state(self.store), before)


class DirectToolInvariantTest(unittest.TestCase):
    """Every tool, run directly in every mode, reaches its body and leaves model and agent settings unchanged.

    The fixture holds what each tool's success path needs: an applied plan with image and
    video adapters, an approved take/start frame, an approved timeline (render grant), an
    approved 3D scene, a canon source for memory, a motion proposal approved by the owner
    and an owner-approved media grant. Arguments are built at call time from current heads.
    """
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.store = self.m.f.http.store

    def raw(self):
        with self.store.connect() as c:
            return json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']

    def tool(self, name, arguments):
        run = self.m.post('production_run', song='A')['run']['id']
        status, value = self.m.f.action('production_tool', song='A', run=run,
                                        call=dict(id=uuid.uuid4().hex, name=name, arguments=arguments, complete=True))
        self.assertEqual(status, 200, value)
        return value['tool']

    def build_fixture(self):
        shot = '장면 1'
        png = SyntheticImageAdapter().generate(dict(prompt='fixture', width=32, height=32))['bytes']
        revision = lambda: self.m.project()['shots'][shot]['revision']
        self.m.post('take', song='A', shot=shot, shot_revision=revision(), filename='start.png',
                    content=base64.b64encode(png).decode(), reason='fixture', rights='synthetic owned')
        self.take = self.m.project()['shots'][shot]['takes'][-1]
        self.m.post('select', song='A', shot=shot, take=self.take['id'], shot_revision=revision())
        self.m.post('review_take', song='A', shot=shot, take=self.take['id'], decision='approved', reason='checked')
        self.m.post('assign_reference', song='A', shot=shot, shot_revision=revision(), source_song='A', source_shot=shot,
                    source_take=self.take['id'], role='start_frame', reason='fixture')
        self.m.post('review_reference', song='A', shot=shot, shot_revision=revision(), version=1, decision='approved', reason='fixture')
        timeline = editing.current(self.raw());timeline['profile'] = 'preview'
        self.m.post('timeline', song='A', timeline=timeline);self.m.post('approve_timeline', song='A')
        self.render_grant = editing.current(self.raw())['approval']['id']
        self.m.post('model_settings', song='A', selections={'video':'fal-kling-2-5-turbo'}, model_revision=self.m.project()['model_settings']['revision'])
        kling = Contract('fal-kling-2-5-turbo')
        payload = kling.payload('blue geometry', {'duration':5,'generate_audio':False}, [png])
        self.store.media_dispatch.adapters['fal-kling-2-5-turbo'] = FalModelAdapter(
            'fal-kling-2-5-turbo', quote=quote_for(kling, payload, '0.35'), transport=lambda *a: self.fail('no provider submission'))
        self.shot = production_context.shot_id(self.m.project(), shot)
        created = self.m.post('scene_create', song='A', shot_id=self.shot, scene=scene_sample())['scene']
        self.m.post('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')
        # Canon source for propose_memory_update; the applied plan is re-bound to the new canon.
        with self.store.connect() as c:
            state = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);project = state['projects']['A']
            project['snapshot'] = [dict(id=1, text='Mira wears blue.')]
            for plan in project['guided_plans']:
                if plan['status'] == 'applied':plan['context_hash'] = guided.fingerprint(guided.context(project))
            c.execute('UPDATE state SET body=? WHERE id=1', (json.dumps(state, ensure_ascii=False),))
        self.plan = self.m.project()['guided_plans'][-1]['id']
        # Owner-approved motion version (grant) and an owner media grant for an owner-prepared image action.
        proposal = self.tool('propose_motion_scene', dict(shot_id=self.shot, base_motion_revision=0, scene=motion.GeneralChatMotionTest.motion_scene(None)))
        self.m.post('motion_review', song='A', proposal_id=proposal['proposal_id'], decision='approved')
        self.motion_grant = self.raw()['shots'][shot]['motion_versions'][-1]['approval']['id']
        prepared = self.m.post('media_prepare', song='A', shot=shot, shot_revision=revision(), prompt=self.m.prompt, options={'ratio':'16:9'}, refs=[])['media_action']
        action = prepared['action'];w = self.store.workspace_id
        self.store.media_dispatch.gates[action['id']] = dict(workspace=w, project=self.m.f.pid, action_hash=action['hash'], input_sha256=prepared['input_sha256'],
            model=action['release_id'], output_policy=action['options']['output_policy'], maximum_units=10000, maximum_calls=1, expires=time.time()+600)
        with self.store.connect() as c:
            ledger.patch_budget(c, w, 'project:'+self.m.f.pid, dict(limit={'amount':'1','currency':'USD'}, maxConcurrentJobs=1, allowAutomaticRetries=False), 0)
        self.media_action = action['id']
        self.media_grant = self.m.post('media_approve', song='A', action_id=action['id'])['media_grant']['id']
        self.job_id = 'job-'+uuid.uuid4().hex
        job = dict(id=self.job_id, state='imported', mode='contract-fake', external_calls=0, cost_confirmed=False, updated=time.time(),
                   context=dict(song='A', output_kind='image', action_binding=dict(workspace=w, project=self.m.f.pid, action_id=action['id'],
                   plan_id=self.plan, plan_revision=1, release_id='fal-ai/flux/schnell', grant_id=self.media_grant)))
        with self.store.connect() as c:
            c.execute('INSERT INTO generation_jobs (id,request_key,digest,body) VALUES (?,?,?,?)', (self.job_id, 'fixture:'+self.job_id, 'fixture', json.dumps(job)))

    def arguments(self, name, mode):
        project = self.raw();head = project['timeline_head']
        return dict(
            search_project_context={'query':'current'}, get_model_capabilities={'role':'video'},
            propose_media_plan=dict(goal='g', scenes='s', style='', constraints='', kind='visualizer'),
            estimate_media_plan={'plan_id':self.plan}, prepare_image_action=self.m.arguments(),
            prepare_video_action=dict(shot_id=self.shot, model_id='fal-kling-2-5-turbo', model_reason='r', prompt='blue geometry', duration=5,
                                      shot_revision=project['shots']['장면 1']['revision'], source_shot_id=self.shot,
                                      source_take_id=self.take['id'], source_sha256=self.take['sha256']),
            request_media_generation=dict(plan_id=self.plan, action_id=self.media_action, grant_id=self.media_grant),
            get_generation_job={'job_id':self.job_id}, get_agent_settings={},
            request_render=dict(timeline_version=head, grant_id=self.render_grant),
            request_motion_render=dict(shot_id=self.shot, motion_revision=1, grant_id=self.motion_grant),
            propose_timeline_edit=dict(description='d', timeline_version=head, changes=[dict(clip_index=0, take=self.take['id'], trim=0, duration=1)]),
            propose_motion_scene=dict(shot_id=self.shot, base_motion_revision=1, scene=motion.GeneralChatMotionTest.motion_scene(None)),
            propose_memory_update=dict(description='Mira wears blue.', kind='character', label='Mira', entity_id='', source_id='canon:1',
                                       excerpt='Mira wears blue.', ontology_revision=0),
            # Mode-specific values so each mode saves its own proposal (identical ones are deduplicated).
            propose_scene_3d=dict(shot_id=self.shot, base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=30 if mode == 'review' else 40)], model_reason='r'),
            propose_preference_rule=dict(category='camera', value='v-'+mode, evidence='e', model_reason='r'),
            # Last: in full_access this saves a new agent draft head.
            propose_timeline_changes=dict(description='d', timeline_version=head, commands=[dict(op='set_captions', cues=[dict(start=0, end=1, text='x')])]))[name]

    # Expected per-tool outcome: (status, code). read_only refuses every write tool.
    WRITABLE = dict(
        search_project_context=('succeeded', None), get_model_capabilities=('succeeded', None), propose_media_plan=('proposed', None),
        estimate_media_plan=('estimated', None), prepare_image_action=('proposed', None), prepare_video_action=('proposed', None),
        request_media_generation=('accepted', None), get_generation_job=('succeeded', None), get_agent_settings=('succeeded', None),
        request_render=('accepted', None), request_motion_render=('accepted', None), propose_timeline_edit=('proposed', None),
        propose_motion_scene=('proposed', None), propose_memory_update=('proposed', None), propose_scene_3d=('proposed', None),
        propose_preference_rule=('proposed', None), propose_timeline_changes=('proposed', None))

    def expected(self, mode, name):
        if mode == 'read_only' and name not in agent_preferences.READ_TOOLS:return ('invalid_arguments', 'AGENT_READ_ONLY')
        if mode == 'full_access' and name == 'propose_timeline_changes':return ('applied_draft', None)
        if mode == 'full_access' and name in {'request_render', 'request_motion_render', 'request_media_generation'}:return ('existing', None)  # same grant as in review
        return self.WRITABLE[name]

    def test_settings_unchanged_after_every_tool_in_every_mode(self):
        self.build_fixture()
        self.assertEqual(set(self.WRITABLE), set(__import__('production_tools').TOOLS))
        outcomes = {}
        for mode in ('read_only', 'review', 'full_access'):
            revision = self.m.project()['agent_preferences']['by_model']['anthropic-haiku-5-5']['revision']
            self.m.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=revision, mode=mode, effort='low')
            # Not vacuous: the stored agent settings are part of the compared state.
            model_settings, sessions = settings_state(self.store)
            self.assertEqual([value['anthropic-haiku-5-5']['mode'] for value, _ in sessions.values() if value], [mode])
            self.assertEqual(model_settings['selections'], {'chat':'anthropic-haiku-5-5', 'image':'fal-flux-schnell', 'video':'fal-kling-2-5-turbo'})
            for name in self.WRITABLE:
                with self.subTest(mode=mode, tool=name):
                    before = settings_state(self.store)
                    result = self.tool(name, self.arguments(name, mode))
                    outcomes['%s/%s' % (mode, name)] = (result['status'], result.get('code'))
                    self.assertEqual((result['status'], result.get('code')), self.expected(mode, name), result)
                    self.assertEqual(settings_state(self.store), before)
        self.assertEqual(len(outcomes), 3*17)
        # No provider submission: the accepted media job stays prepared and the adapters fail if reached.
        self.assertEqual(self.m.submissions, [])
        record = os.environ.get('SRV_R2_EVIDENCE')
        if record:
            with open(os.path.join(record, 'invariant-outcomes.json'), 'w', encoding='utf-8') as out:
                json.dump(outcomes, out, ensure_ascii=False, indent=1)

    def test_human_http_video_preparation_has_owner_label_null_provenance_and_rejects_injection(self):
        self.build_fixture()
        shot = '장면 1';revision = self.m.project()['shots'][shot]['revision']
        data = dict(song='A', shot=shot, shot_revision=revision, prompt='blue geometry', options={'duration':5,'generate_audio':False},
                    refs=[dict(shot=shot, take=self.take['id'], sha256=self.take['sha256'], role='start_frame')])
        for injected in (dict(actor='agent'), dict(provenance=dict(engine='x')), dict(model_reason='forged')):
            with self.subTest(injected=sorted(injected)):
                status, value = self.m.f.action('media_prepare', **data, **injected)
                self.assertEqual(status, 400, value)
        prepared = self.m.post('media_prepare', **data)['media_action']
        card = next(x for x in self.m.project()['media_actions'] if x['id'] == prepared['action']['id'])
        self.assertEqual((card['role'], card['actor'], card['model_reason'], card['model_reason_label'], card['record']),
                         ('video', 'local-owner', None, '프로젝트에서 사용자가 선택한 모델', 'recorded'))
        self.assertEqual(card['provenance'], dict.fromkeys(PROVENANCE_KEYS))
        self.assertEqual((card['project_selection'], card['differs_from_project']), ('fal-kling-2-5-turbo', False))
        self.assertEqual((card['price']['unit_price']['unit'], card['price']['quantity'], card['price']['expected_total']),
                         ('second', 5, {'amount':'0.35','currency':'USD'}))
        self.assertEqual((card['approval'], card['can_execute']), ('required', False))
        self.assertEqual(self.m.submissions, [])

    def test_read_only_cannot_prepare_video(self):
        self.m.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=0, mode='read_only', effort='low')
        shot = production_context.shot_id(self.m.project(), '장면 1')
        value = self.tool('prepare_video_action', dict(shot_id=shot, model_id='fal-kling-2-5-turbo', model_reason='r', prompt='p', duration=5,
                          shot_revision=0, source_shot_id=shot, source_take_id=1, source_sha256='a'*64))  # tool() asserts HTTP 200
        self.assertEqual((value['status'], value['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
        self.assertEqual(self.m.actions(), [])
        self.m.assert_no_media_execution()


class VideoD15Test(unittest.TestCase):
    """Video path through the direct tool endpoint with an approved start frame."""
    @classmethod
    def setUpClass(cls):
        multi.FalMultiTest.setUpClass()

    def setUp(self):
        self.t = multi.FalMultiTest('test_model_tool_prepares_action_and_quote_but_cannot_grant_or_spend')
        self.t.setUp()
        self.addCleanup(self.t.doCleanups)
        self.t.setup_model('fal-kling-2-5-turbo')
        self.take = self.t.shot()['takes'][-1]
        with open(self.take['asset'], 'rb') as handle:
            self.frame = handle.read()
        # Not the project's video model; integration_blocked in the catalog.
        blocked = Contract('fal-kling-2-6-pro')
        payload = blocked.payload('blue geometry', {'duration':5,'generate_audio':False}, [self.frame])
        self.t.pipe.adapters['fal-kling-2-6-pro'] = FalModelAdapter('fal-kling-2-6-pro', quote=quote_for(blocked, payload, '0.35'),
                                                                   transport=lambda *a: self.fail('no provider submission'))
        self.baseline = self.counts()
        self.baseline_actions = len(self.actions())

    def counts(self):
        with self.t.st.connect() as db:
            return {table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('generation_jobs', 'reservations', 'execution_grants', 'provider_action_jobs')}

    def arguments(self, **changes):
        value = dict(shot_id='장면 1', model_id='fal-kling-2-5-turbo', model_reason=REASON, prompt='blue geometry', duration=5,
                     shot_revision=self.t.shot()['revision'], source_shot_id='장면 1', source_take_id=self.take['id'], source_sha256=self.take['sha256'])
        value.update(changes)
        return value

    def tool(self, arguments, name='prepare_video_action'):
        run = self.t.call('production_run', song='synthetic')['run']['id']
        return self.t.call('production_tool', song='synthetic', run=run, call=dict(id=uuid.uuid4().hex, name=name, arguments=arguments, complete=True))['tool']

    def actions(self):
        with self.t.st.connect() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT body FROM production_actions')]

    def assert_nothing_reserved_or_sent(self):
        self.assertEqual(self.t.calls, [])
        self.assertEqual(self.counts(), self.baseline)
        self.assertEqual(self.baseline['reservations'], 0)

    def test_blocked_different_video_model_is_saved_as_proposal_only(self):
        before = settings_state(self.t.st)
        result = self.tool(self.arguments(model_id='fal-kling-2-6-pro'))
        self.assertEqual(result['status'], 'proposed')
        self.assertEqual((result['project_selection'], result['differs_from_project'], result['model_state']),
                         ('fal-kling-2-5-turbo', True, 'integration_blocked'))
        self.assertEqual(result['model_reason'], REASON)
        self.assertEqual(result['provenance']['permission_mode'], 'review')
        self.assertEqual(result['provenance']['engine'], 'local-contract-rehearsal')
        price = result['price']
        self.assertEqual((price['unit_price']['amount'], price['unit_price']['unit'], price['quantity']), ('0.07', 'second', 5))
        self.assertEqual(price['expected_total'], {'amount':'0.35','currency':'USD'})
        self.assertIs(price['matches_quote'], True)
        self.assertEqual(settings_state(self.t.st), before)
        card = next(x for x in self.t.project()['media_actions'] if x['id'] == result['action_id'])
        self.assertEqual((card['approval'], card['can_execute']), ('required', False))
        self.assert_nothing_reserved_or_sent()

    def test_full_access_agent_video_proposal_records_mode_and_stays_unexecuted(self):
        # This fixture has no chat model selected; agent settings belong to the selected chat model.
        self.t.call('model_settings', song='synthetic', selections={'chat':'anthropic-haiku-5-5'}, model_revision=self.t.project()['model_settings']['revision'])
        revision = agent_preferences.profile(self.raw_project(), 'anthropic-haiku-5-5')['revision']
        self.t.call('conversation_agent_settings', song='synthetic', selection='anthropic-haiku-5-5', settings_revision=revision, mode='full_access', effort='high')
        before = settings_state(self.t.st)
        result = self.tool(self.arguments())
        self.assertEqual(result['status'], 'proposed')
        self.assertEqual((result['actor'], result['model_reason'], result['project_selection'], result['differs_from_project']),
                         ('agent', REASON, 'fal-kling-2-5-turbo', False))
        self.assertEqual((result['provenance']['permission_mode'], result['provenance']['effort']), ('full_access', 'high'))
        self.assertEqual((result['approval'], result['external_calls']), ('required', 0))
        card = next(x for x in self.t.project()['media_actions'] if x['id'] == result['action_id'])
        self.assertEqual((card['approval'], card['can_execute'], card['provenance']['permission_mode']), ('required', False, 'full_access'))
        self.assertEqual(settings_state(self.t.st), before)
        self.assert_nothing_reserved_or_sent()

    def raw_project(self):
        with self.t.st.connect() as c:
            return json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['synthetic']

    def test_changed_quote_input_rejects_old_quote_and_accepts_only_a_new_one(self):
        for changes in (dict(duration=10), dict(prompt='blue geometry, slower')):
            with self.subTest(changes=changes):
                result = self.tool(self.arguments(**changes))
                self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'INVALID_MEDIA_INPUT'))
        self.assertEqual(len(self.actions()), self.baseline_actions)
        contract = Contract('fal-kling-2-5-turbo')
        payload = contract.payload('blue geometry', {'duration':10,'generate_audio':False}, [self.frame])
        self.t.pipe.adapters['fal-kling-2-5-turbo'].contract.quote = quote_for(contract, payload, '0.70')
        old = self.tool(self.arguments())
        self.assertEqual((old['status'], old['code']), ('invalid_arguments', 'INVALID_MEDIA_INPUT'))
        result = self.tool(self.arguments(duration=10))
        self.assertEqual(result['status'], 'proposed')
        self.assertEqual((result['price']['quantity'], result['price']['expected_total'], result['price']['matches_quote']),
                         (10, {'amount':'0.7','currency':'USD'}, True))
        self.assertEqual(len(self.actions()), self.baseline_actions+1)
        self.assert_nothing_reserved_or_sent()


class UnitPriceTest(unittest.TestCase):
    def test_unit_times_quantity_and_mismatch_are_both_visible(self):
        view = fal_models.price_view('fal-kling-2-6-pro', {'duration':10,'generate_audio':False}, {'amount':'0.70','currency':'USD'})
        self.assertEqual((view['expected_total'], view['matches_quote']), ({'amount':'0.7','currency':'USD'}, True))
        self.assertIn('0.07 USD/초 × 10초', view['formula'])
        view = fal_models.price_view('fal-flux-pro-1-1', {'ratio':'9:16'}, {'amount':'0.05','currency':'USD'})
        self.assertEqual((view['quantity'], view['expected_total'], view['quote_total'], view['matches_quote']),
                         (1, {'amount':'0.04','currency':'USD'}, {'amount':'0.05','currency':'USD'}, False))
        self.assertIn('mismatch', view)

    def test_kling_turbo_keeps_published_terms_verbatim_beside_the_per_second_value(self):
        unit = fal_models.unit_price('fal-kling-2-5-turbo')
        self.assertEqual((unit['amount'], unit['unit']), ('0.07', 'second'))
        self.assertEqual(unit['published_terms'], 'For 5s video your request will cost $0.35. For every additional second you will be charged $0.07.')
        view = fal_models.price_view('fal-kling-2-5-turbo', {'duration':5,'generate_audio':False}, {'amount':'0.35','currency':'USD'})
        # Existing projection fields keep their names; the terms travel inside unit_price.
        self.assertEqual(set(view), {'unit_price', 'quantity', 'expected_total', 'formula', 'quote_total', 'matches_quote'})
        self.assertEqual(view['unit_price']['published_terms'], unit['published_terms'])
        for seconds, total in ((5, '0.35'), (10, '0.7')):
            self.assertEqual(fal_models.price_view('fal-kling-2-5-turbo', {'duration':seconds,'generate_audio':False})['expected_total'], {'amount':total,'currency':'USD'})

    def test_square_image_is_not_priced_while_the_megapixel_definition_is_unpublished(self):
        view = fal_models.price_view('fal-flux-schnell', {'ratio':'1:1'}, {'amount':'0.003','currency':'USD'})
        self.assertIsNone(view['expected_total'])
        self.assertIsNone(view['matches_quote'])
        self.assertIn('0.006', view['reason'])
        self.assertIn('0.003', view['reason'])

    def test_every_catalog_media_model_has_a_documented_price_record(self):
        for identifier in fal_models.MODELS:
            unit = fal_models.unit_price(identifier)
            extra = {'published_terms'} if identifier == 'fal-kling-2-5-turbo' else set()
            self.assertEqual(set(unit), {'amount', 'currency', 'unit', 'source', 'fetched_at', 'revision', 'kind'} | extra)
            self.assertEqual(unit['kind'], 'documented-estimate')
            self.assertTrue(unit['source'].startswith('https://fal.ai/models/'+fal_models.MODELS[identifier]['endpoint']))
        self.assertIsNone(fal_models.unit_price('unknown'))
        self.assertEqual(fal_models.price_view('unknown', {}), dict(unit_price=None, reason='공식 단가를 찾지 못했습니다.'))


class InputCapTest(unittest.TestCase):
    def test_d20_raises_only_the_input_cap_and_reports_the_worst_round(self):
        self.assertEqual((chat_general.MAX_INPUT, chat_general.MAX_OUTPUT, chat_general.CONVERSATION_CAP_MICRO), (16384, 4096, 400000))
        self.assertEqual(agent_preferences.reservation('anthropic-haiku-5-5')['worst_per_round_micro'], 3687)
        self.assertEqual(agent_preferences.reservation('xai-grok-4-7')['worst_per_round_micro'], 57344)


if __name__ == '__main__':
    unittest.main()
