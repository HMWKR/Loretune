"""A2a: D15 media proposals, S15 provenance, D19 unit prices, D20 cap, S9/D21 settings.

Isolated HTTP/SQLite and in-process Store fixtures only. No model, provider,
count_tokens or paid call: fal transports fail the test if reached.
"""
import hashlib
import json
import time
import unittest
import uuid
from copy import deepcopy

import agent_preferences
import chat_general
import chat_models
import chat_sessions
import fal_models
import production_context
from app import Store
from fal_dispatch import FalDispatch, NO_RECORD
from fal_model_adapter import FalModelAdapter
from fal_models import Contract
from tests import test_general_chat_media_preparation as media
from tests import test_fal_multimodel as multi

REASON = '프로젝트 기본보다 품질이 높은 모델을 제안합니다.'
PROVENANCE_KEYS = {'engine', 'chat_model', 'permission_mode', 'effort', 'run', 'call'}


def quote_for(contract, payload, amount='0.01'):
    return dict(provider='fal.ai', model=contract.MODEL, money={'amount':amount,'currency':'USD'},
                input_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), kind='fixture', price_revision='synthetic-not-real',
                source=contract.spec['source'], expires=time.time()+300)


def settings_state(project):
    """Every user-owned setting an agent tool must never change."""
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
                before = settings_state(self.m.project())
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
                card, = project['media_actions']
                reopened = Store(self.f.tmp.name).state()['projects']['A']['media_actions'][0]
                for surface in (card, reopened):
                    for key in ('actor', 'model_reason', 'model_reason_label', 'provenance', 'project_selection',
                                'differs_from_project', 'price', 'price_source', 'price_revision', 'quote_expires', 'record'):
                        self.assertEqual(surface[key], result[key], key)
                self.assertEqual(settings_state(self.m.project()), before)
                self.m.assert_no_media_execution()

    def test_different_model_is_a_proposal_and_never_changes_project_settings(self):
        before = settings_state(self.m.project())
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
        self.assertEqual(settings_state(self.m.project()), before)
        self.assertEqual(self.m.project()['model_settings']['selections']['image'], 'fal-flux-schnell')
        card, = project['media_actions']
        self.assertEqual((card['approval'], card['can_execute']), ('required', False))
        self.m.assert_no_media_execution()

    def test_missing_empty_or_long_reason_is_rejected_before_any_action(self):
        for reason in ('', '   ', 'x'*301, None):
            with self.subTest(reason=None if reason is None else len(reason)):
                self.setUp()
                arguments = self.m.arguments()
                if reason is None:del arguments['model_reason']
                else:arguments['model_reason'] = reason
                project = self.m.send_tool('prepare_image_action', arguments)
                # The schema validator refuses the model response before any tool request.
                self.assertEqual(project['general_chat_turns'][-1]['status'], 'outcome_unknown')
                self.assertEqual(self.m.actions(), [])
                self.m.assert_no_media_execution()

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
        before = settings_state(self.m.project())
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
        self.assertEqual(settings_state(self.m.project()), before)


class DirectToolInvariantTest(unittest.TestCase):
    """Every tool, run directly, leaves model_settings and agent_settings unchanged."""
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)

    def tool(self, name, arguments):
        run = self.m.post('production_run', song='A')['run']['id']
        status, value = self.m.f.action('production_tool', song='A', run=run,
                                        call=dict(id=uuid.uuid4().hex, name=name, arguments=arguments, complete=True))
        return status, value

    def test_settings_unchanged_after_every_tool_in_every_mode(self):
        project = self.m.project()
        shot = production_context.shot_id(project, '장면 1')
        plan = project['guided_plans'][-1]['id']
        arguments = dict(
            search_project_context={'query':'scene'}, get_model_capabilities={'role':'video'},
            propose_media_plan=dict(goal='g', scenes='s', style='', constraints='', kind='visualizer'),
            estimate_media_plan={'plan_id':plan}, prepare_image_action=self.m.arguments(),
            prepare_video_action=dict(shot_id=shot, model_id='fal-kling-2-5-turbo', model_reason='r', prompt='p', duration=5,
                                      shot_revision=0, source_shot_id=shot, source_take_id=1, source_sha256='a'*64),
            request_media_generation=dict(plan_id=plan, action_id='a', grant_id='g'), get_generation_job={'job_id':'missing'},
            get_agent_settings={}, propose_timeline_edit=dict(description='d', timeline_version=0, changes=[]),
            propose_timeline_changes=dict(description='d', timeline_version=0, commands=[]),
            propose_motion_scene=dict(shot_id=shot, base_motion_revision=0, scene={}),
            request_motion_render=dict(shot_id=shot, motion_revision=1, grant_id='g'),
            request_render=dict(timeline_version=1, grant_id='g'),
            propose_memory_update=dict(description='d', kind='fact', label='l', entity_id='', source_id='s', excerpt='e', ontology_revision=0),
            # A2b: the two new tools join the every-tool invariant (S7b, S10).
            propose_scene_3d=dict(shot_id=shot, base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=35)], model_reason='r'),
            propose_preference_rule=dict(category='camera', value='v', evidence='e', model_reason='r'))
        self.assertEqual(set(arguments), set(__import__('production_tools').TOOLS))
        for mode in ('read_only', 'review', 'full_access'):
            revision = self.m.project()['agent_preferences']['by_model']['anthropic-haiku-5-5']['revision']
            self.m.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=revision, mode=mode, effort='low')
            for name, value in arguments.items():
                with self.subTest(mode=mode, tool=name):
                    before = settings_state(self.m.project())
                    self.tool(name, value)
                    self.assertEqual(settings_state(self.m.project()), before)
        self.m.assert_no_media_execution()

    def test_read_only_cannot_prepare_video(self):
        self.m.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=0, mode='read_only', effort='low')
        shot = production_context.shot_id(self.m.project(), '장면 1')
        status, value = self.tool('prepare_video_action', dict(shot_id=shot, model_id='fal-kling-2-5-turbo', model_reason='r', prompt='p', duration=5,
                                  shot_revision=0, source_shot_id=shot, source_take_id=1, source_sha256='a'*64))
        self.assertEqual(status, 200, value)
        self.assertEqual((value['tool']['status'], value['tool']['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
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
        self.frame = open(self.take['asset'], 'rb').read()
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
        before = settings_state(self.t.project())
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
        self.assertEqual(settings_state(self.t.project()), before)
        card = next(x for x in self.t.project()['media_actions'] if x['id'] == result['action_id'])
        self.assertEqual((card['approval'], card['can_execute']), ('required', False))
        self.assert_nothing_reserved_or_sent()

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

    def test_square_image_is_not_priced_while_the_megapixel_definition_is_unpublished(self):
        view = fal_models.price_view('fal-flux-schnell', {'ratio':'1:1'}, {'amount':'0.003','currency':'USD'})
        self.assertIsNone(view['expected_total'])
        self.assertIsNone(view['matches_quote'])
        self.assertIn('0.006', view['reason'])
        self.assertIn('0.003', view['reason'])

    def test_every_catalog_media_model_has_a_documented_price_record(self):
        for identifier in fal_models.MODELS:
            unit = fal_models.unit_price(identifier)
            self.assertEqual(set(unit), {'amount', 'currency', 'unit', 'source', 'fetched_at', 'revision', 'kind'})
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
