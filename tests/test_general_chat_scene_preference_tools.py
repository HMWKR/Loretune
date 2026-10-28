"""A2b: S7b propose_scene_3d, S10 propose_preference_rule, render grant prechecks, scene-status limits.

Isolated temporary Store/SQLite and loopback HTTP fixtures only. No model,
provider, count_tokens or paid call; the general chat transport is a fixture.
"""
import base64
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid

import agent_preferences
import app
import chat_general
import chat_protocols
import chat_sessions
import contracts
import editing
from loretune import Conflict
import ontology
import preferences as preference_rules
import production_context
import production_tools
import project_ontology
import scene_project
from tests import test_chat_general_http as base
from tests.scene_asset_fixtures import textured_glb
from tests.test_chat_runtime import response, use
from tests.test_scene_contract import sample

REASON = '카메라를 낮춰 인물을 강조하려는 제안입니다.'
PROVENANCE_KEYS = {'engine', 'chat_model', 'permission_mode', 'effort', 'run', 'call'}  # same keys as the D15/S15 media record
LENS = [dict(target='camera', id='camera', field='lens_mm', value=35)]


def evidence(name, value):
    folder = os.environ.get('A2B_EVIDENCE')
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
        (Path(folder)/(name+'.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


class StoreFixture:
    """Direct Store transactions, as the HTTP handler performs them."""
    def __init__(self, test):
        self.tmp = tempfile.TemporaryDirectory(); test.addCleanup(self.tmp.cleanup)
        self.store = app.Store(self.tmp.name)
        self.call('project', name='A', era='default', story=0)
        self.call('model_settings', song='A', selections={'chat':'anthropic-haiku-5-5'}, model_revision=0)
        self.call('shot', song='A', shot='shot', description='synthetic 3D')
        self.call('shot', song='A', shot='second', description='synthetic 3D second')

    def raw(self):
        with self.store.connect() as c:return json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])

    def call(self, action, conversation=None, store=None, **data):
        store = store or self.store
        with store.connect() as c:revision = c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        request = dict(action=action, data=data, revision=revision, request_id=uuid.uuid4().hex)
        if conversation:
            p = self.raw()['projects']['A']
            request.update(conversation_id=conversation, conversation_revision=chat_sessions.resolve(p, conversation)['revision'],
                           shared_version=chat_sessions.shared_fingerprint(p))
        return store.mutate(request)

    def shot_id(self, shot='shot'):return production_context.shot_id(self.raw()['projects']['A'], shot)

    def approved(self, scene=None, conversation=None, shot='shot'):
        created = self.call('scene_create', conversation, song='A', shot_id=self.shot_id(shot), scene=scene or sample())['scene']
        self.call('scene_review', conversation, song='A', scene_proposal_id=created['proposal_id'], decision='approved')
        return created

    def settings(self, mode, effort='low', conversation=None):
        p = chat_sessions.scoped(self.raw()['projects']['A'], conversation) if conversation else self.raw()['projects']['A']
        revision = agent_preferences.profile(p, 'anthropic-haiku-5-5')['revision']
        current = agent_preferences.profile(p, 'anthropic-haiku-5-5')
        if (current['mode'], current['effort']) == (mode, effort):return
        self.call('conversation_agent_settings', conversation, song='A', selection='anthropic-haiku-5-5', settings_revision=revision, mode=mode, effort=effort)

    def run(self, conversation=None):return self.call('production_run', conversation, song='A')['run']['id']

    def tool(self, name, arguments, run=None, conversation=None, call_id=None, store=None):
        run = run or self.run(conversation)
        call = dict(id=call_id or uuid.uuid4().hex, name=name, arguments=arguments, complete=True)
        return self.call('production_tool', conversation, store=store, song='A', run=run, call=call)['tool'], run, call

    def records(self, conversation=None):
        with self.store.connect() as c:
            return scene_project.public(c, self.store, self.raw()['projects']['A'], 'A', conversation or chat_sessions.default_id(self.raw()['projects']['A']))

    def proposal_rows(self):
        with self.store.connect() as c:return c.execute('SELECT count(*) FROM scene_proposals').fetchone()[0]

    def status(self, conversation=None):
        p = self.raw()['projects']['A']
        if conversation:p = chat_sessions.scoped(p, conversation)
        with self.store.connect() as c:return production_context.read(c, self.store, p, 'A', 'scene-status')['scene_status']

    def asset(self, rights='직접 제작', conversation=None):
        return self.call('scene_asset_import', conversation, song='A', filename='synthetic.glb',
                         content=base64.b64encode(textured_glb()).decode(), rights=rights)['scene_asset']


def scene_args(shot_id, base=1, operations=None, reason=REASON):
    return dict(shot_id=shot_id, base_revision=base, operations=operations or LENS, model_reason=reason)


def swap(asset):
    return [dict(target='object', id='subject', field='asset', value={k:asset[k] for k in ('id', 'sha256', 'profile')})]


class ProposeScene3DTest(unittest.TestCase):
    def setUp(self):
        self.s = StoreFixture(self)

    def test_review_saves_a_proposal_with_server_origin_and_never_applies(self):
        mine = self.s.approved()
        self.s.settings('review', 'medium')
        result, run, call = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual(result['status'], 'proposed', result)
        self.assertEqual((result['scene_id'], result['base_revision'], result['changes']), (mine['scene_id'], 1, [dict(target='camera', id='camera', field='lens_mm')]))
        self.assertEqual((result['applied'], result['approval_required'], result['render_requested'], result['external_calls']), (False, True, False, 0))
        self.assertEqual((result['actor'], result['model_reason'], result['model_reason_label']), ('agent', REASON, '모델이 제시한 이유(검증 안 됨)'))
        self.assertEqual(set(result['provenance']), PROVENANCE_KEYS)
        self.assertEqual(result['provenance'], dict(engine='local-contract-rehearsal', chat_model=None, permission_mode='review', effort='medium', run=run, call=call['id']))
        record = self.s.records()[0]
        self.assertEqual(record['head'], 1)
        saved = next(x for x in record['proposals'] if x['id'] == result['proposal_id'])
        self.assertEqual((saved['status'], saved['base_revision']), ('proposed', 1))
        self.assertEqual(saved['origin'], {k:result[k] for k in ('actor', 'model_reason', 'model_reason_label', 'provenance')})
        self.assertEqual(saved['scene']['camera']['lens_mm'], 35)
        status = self.s.status()['scenes_3d'][0]
        self.assertEqual(status['pending_proposals'], [dict(proposal_id=result['proposal_id'], base_revision=1, status='proposed')])
        with self.s.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM jobs').fetchone()[0], 0)
        evidence('scene-proposal-receipt', result)

    def test_identical_agent_proposal_reuses_the_pending_one(self):
        mine = self.s.approved();self.s.settings('review')
        first, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        rows = self.s.proposal_rows()
        again, _, call = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual((again['status'], again['proposal_id'], again['duplicate'], again['applied']), ('proposed', first['proposal_id'], True, False))
        self.assertIn('이미 있어 새로 저장하지 않았습니다', again['note'])
        self.assertEqual(self.s.proposal_rows(), rows)
        # Different values are a different proposal; a rejected one no longer absorbs repeats.
        other, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), operations=[dict(target='camera', id='camera', field='lens_mm', value=50)]))
        self.assertEqual((other['duplicate'], self.s.proposal_rows()), (False, rows+1))
        self.s.call('scene_review', song='A', scene_proposal_id=first['proposal_id'], decision='rejected')
        fresh, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual((fresh['duplicate'], self.s.proposal_rows()), (False, rows+2))
        self.assertNotEqual(fresh['proposal_id'], first['proposal_id'])
        self.assertEqual(self.s.status()['scenes_3d'][0]['pending_total'], 2)
        self.assertEqual(mine['scene_id'], fresh['scene_id'])

    def test_duplicate_reports_the_stored_proposal_origin_and_held_status(self):
        # SRV-r3 minor: a reused proposal reports what is stored, not the repeating call's origin or 'proposed'.
        self.s.approved();self.s.settings('review', 'medium')
        first, first_run, first_call = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.s.call('scene_review', song='A', scene_proposal_id=first['proposal_id'], decision='held')
        self.s.settings('full_access', 'high')
        again, run, call = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual((again['duplicate'], again['proposal_id'], again['status']), (True, first['proposal_id'], 'held'))
        self.assertEqual(again['provenance'], dict(engine='local-contract-rehearsal', chat_model=None, permission_mode='review', effort='medium', run=first_run, call=first_call['id']))
        self.assertNotEqual((again['provenance']['run'], again['provenance']['call']), (run, call['id']))
        saved = next(x for x in self.s.records()[0]['proposals'] if x['id'] == first['proposal_id'])
        self.assertEqual(saved['origin'], {k:again[k] for k in ('actor', 'model_reason', 'model_reason_label', 'provenance')})

    def test_full_access_never_auto_applies_and_human_approval_keeps_origin(self):
        self.s.approved();self.s.settings('full_access', 'high')
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual((result['status'], result['applied'], result['provenance']['permission_mode']), ('proposed', False, 'full_access'))
        self.assertEqual(self.s.records()[0]['head'], 1)
        self.s.call('scene_review', song='A', scene_proposal_id=result['proposal_id'], decision='approved')
        record = self.s.records()[0];saved = next(x for x in record['proposals'] if x['id'] == result['proposal_id'])
        self.assertEqual((record['head'], saved['status'], saved['origin']['actor']), (2, 'applied', 'agent'))
        self.assertEqual(record['versions'][-1]['approval']['actor'], 'local-owner')

    def test_stale_head_and_head_zero_are_rejected_without_rows(self):
        mine = self.s.approved()
        newer = self.s.call('scene_propose', song='A', scene_id=mine['scene_id'], base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=40)])['scene']
        self.s.call('scene_review', song='A', scene_proposal_id=newer['proposal_id'], decision='approved')
        rows = self.s.proposal_rows()
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), base=1))
        self.assertEqual(result, dict(status='blocked', code='STALE_VERSION', retryable=False))
        self.assertEqual(self.s.proposal_rows(), rows)
        draft = self.s.call('scene_create', song='A', shot_id=self.s.shot_id('second'), scene=sample())['scene']
        rows = self.s.proposal_rows()
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id('second'), base=1))
        self.assertEqual(result, dict(status='blocked', code='STALE_VERSION', retryable=False))
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id('second'), base=0))
        self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'INVALID_TOOL_ARGUMENTS'))
        self.assertEqual(self.s.proposal_rows(), rows)
        self.assertEqual([x['status'] for x in self.s.records()[1]['proposals']], ['proposed'])
        self.assertEqual(self.s.records()[1]['proposals'][0]['id'], draft['proposal_id'])

    def test_other_conversation_scene_or_unknown_shot_is_not_found(self):
        other = self.s.call('conversation_create', song='A', title='sibling')['conversation']['id']
        self.s.approved(conversation=other)
        rows = self.s.proposal_rows()
        for shot_id in (self.s.shot_id(), 'missing-shot-id'):
            with self.subTest(shot_id=shot_id):
                result, _, _ = self.s.tool('propose_scene_3d', scene_args(shot_id))
                self.assertEqual((result['status'], result['code'], result['retryable']), ('blocked', 'SCENE_NOT_FOUND', False))
        self.assertEqual(self.s.proposal_rows(), rows)
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()), conversation=other)
        self.assertEqual(result['status'], 'proposed')

    def test_out_of_scope_fields_and_unknown_targets_are_refused(self):
        asset = self.s.asset();value = sample();value['schema_version'] = 2
        obj = value['objects'][0];obj.pop('color');obj.update(kind='mesh', asset={k:asset[k] for k in ('id', 'sha256', 'profile')})
        self.s.approved(value)
        rows = self.s.proposal_rows()
        for operations in ([dict(target='object', id='subject', field='color', value=[1, 0, 0])],
                           [dict(target='object', id='ghost', field='position', value=[1, 0, 0])],
                           [dict(target='light', id='ghost', field='energy_w', value=10)]):
            with self.subTest(operations=operations):
                result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), operations=operations))
                self.assertEqual(result, dict(status='blocked', code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED', retryable=False))
        self.assertEqual(self.s.proposal_rows(), rows)

    def test_blocked_asset_is_refused_at_proposal(self):
        self.s.approved();asset = self.s.asset()
        self.s.call('asset_rights', sha256=asset['sha256'], blocked=True, reason='synthetic block')
        rows = self.s.proposal_rows()
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), operations=swap(asset)))
        self.assertEqual(result, dict(status='blocked', code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED', retryable=False))
        self.assertEqual(self.s.proposal_rows(), rows)

    def test_other_conversation_asset_is_refused(self):
        self.s.approved()
        other = self.s.call('conversation_create', song='A', title='sibling')['conversation']['id']
        asset = self.s.asset(conversation=other)
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), operations=swap(asset)))
        self.assertEqual(result, dict(status='blocked', code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED', retryable=False))

    def test_unconfirmed_rights_asset_is_saved_but_human_approval_refuses_it(self):
        self.s.approved();asset = self.s.asset(rights='사용권 미확인')
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id(), operations=swap(asset)))
        self.assertEqual(result['status'], 'proposed')
        with self.assertRaises(ValueError):
            self.s.call('scene_review', song='A', scene_proposal_id=result['proposal_id'], decision='approved')
        self.assertEqual(self.s.records()[0]['head'], 1)

    def test_read_only_is_refused_and_replayed_call_creates_one_proposal(self):
        self.s.approved();self.s.settings('read_only')
        rows = self.s.proposal_rows()
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
        self.assertEqual(self.s.proposal_rows(), rows)
        self.s.settings('review')
        run = self.s.run();call_id = uuid.uuid4().hex
        first, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()), run=run, call_id=call_id)
        second, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()), run=run, call_id=call_id)
        self.assertEqual(first, second)
        self.assertEqual(self.s.proposal_rows(), rows+1)

    def test_restart_keeps_origin_and_scene_status_stays_redacted(self):
        self.s.approved()
        result, _, _ = self.s.tool('propose_scene_3d', scene_args(self.s.shot_id()))
        reopened = app.Store(self.s.tmp.name)
        with reopened.connect() as c:
            records = scene_project.public(c, reopened, self.s.raw()['projects']['A'], 'A', chat_sessions.default_id(self.s.raw()['projects']['A']))
        saved = next(x for x in records[0]['proposals'] if x['id'] == result['proposal_id'])
        self.assertEqual(saved['origin']['provenance'], result['provenance'])
        text = json.dumps(self.s.status(), ensure_ascii=False)
        for secret in (REASON, '"origin"', '"provenance"', result['provenance']['run']):
            self.assertNotIn(secret, text)


class SceneStatusCarriedTest(unittest.TestCase):
    """Carried C1 minors: legacy degrade, exact caps, worst-case size vs MAX_INPUT."""
    def setUp(self):
        self.s = StoreFixture(self)

    def test_legacy_head_without_ontology_binding_degrades_instead_of_failing(self):
        mine = self.s.approved()
        with self.s.store.connect() as c:
            body = json.loads(c.execute('SELECT body FROM scene_records WHERE id=?', (mine['scene_id'],)).fetchone()[0])
            del body['versions'][0]['approval']['binding']['ontology_revision']
            c.execute('UPDATE scene_records SET body=? WHERE id=?', (json.dumps(body), mine['scene_id']))
        scene = self.s.status()['scenes_3d'][0]
        self.assertEqual((scene['head'], scene['approval_status'], scene['requires_review']), (1, 'stale_context', True))
        with self.s.store.connect() as c:
            body['versions'][0].pop('approval')
            c.execute('UPDATE scene_records SET body=? WHERE id=?', (json.dumps(body), mine['scene_id']))
        self.assertEqual(self.s.status()['scenes_3d'][0]['approval_status'], 'stale_context')

    def test_head_zero_draft_flags_ontology_drift(self):
        draft = self.s.call('scene_create', song='A', shot_id=self.s.shot_id(), scene=sample())['scene']
        scope = project_ontology.scope(self.s.store.workspace_id, contracts.project_id(self.s.store.workspace_id, 'A'))
        with self.s.store.connect() as c:
            item = ontology.propose(c, scope, dict(entities=[], relations=[]), 0, 'test');ontology.apply(c, scope, item['id'], 0, 'test', approved=True)
        scene = self.s.status()['scenes_3d'][0]
        self.assertEqual((scene['head'], scene['approval_status'], scene['requires_review'], scene['pending_total']), (0, 'none', True, 1))
        self.assertTrue(self.s.records()[0]['proposals'][0]['requires_review'])
        with self.assertRaises(Conflict):
            self.s.call('scene_review', song='A', scene_proposal_id=draft['proposal_id'], decision='approved')

    def test_exactly_ten_pending_is_not_truncated(self):
        mine = self.s.approved()
        for i in range(10):
            self.s.call('scene_propose', song='A', scene_id=mine['scene_id'], base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=20+i)])
        scene = self.s.status()['scenes_3d'][0]
        self.assertEqual((len(scene['pending_proposals']), scene['pending_total'], scene['pending_truncated']), (10, 10, False))

    def test_exactly_the_scene_limit_is_not_truncated_and_worst_case_size_is_recorded(self):
        limit = production_context.SCENE_STATUS_LIMIT
        for i in range(limit):
            shot = 'cap-%02d' % i
            self.s.call('shot', song='A', shot=shot, description='synthetic 3D')
            created = self.s.approved(shot=shot)
            for j in range(10):
                self.s.call('scene_propose', song='A', scene_id=created['scene_id'], base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=20+j)])
        status = self.s.status()
        self.assertEqual((len(status['scenes_3d']), status['scenes_3d_total'], status['scenes_3d_truncated']), (limit, limit, False))
        self.assertTrue(all((x['pending_total'], x['pending_truncated']) == (10, False) for x in status['scenes_3d']))
        size = len(json.dumps(dict(scene_status=status), ensure_ascii=False).encode())
        # Measured (not extrapolated) worst case at both caps; bytes, not tokens.
        evidence('scene-status-worst-case', dict(bytes=size, scenes=limit, pending_per_scene=10, max_input_tokens=chat_general.MAX_INPUT,
                                                 transport_bytes=65536, bytes_over_4=size//4))
        self.assertLess(size, 65536)


class ProposePreferenceRuleTest(unittest.TestCase):
    def setUp(self):
        self.s = StoreFixture(self)

    def args(self, category='camera', value='낮은 앵글을 선호', evidence_text='사용자 대화: "낮게 찍어줘"'):
        return dict(category=category, value=value, evidence=evidence_text, model_reason=REASON)

    def settings_state(self):
        p = self.s.raw()['projects']['A']
        return p.get('model_settings'), [(x.get('agent_settings'), x.get('agent_settings_history')) for x in p.get('chat_sessions', [])]

    def test_candidate_only_in_every_writable_mode_with_origin(self):
        for mode in ('review', 'full_access'):
            with self.subTest(mode=mode):
                self.s.settings(mode)
                before = self.settings_state()
                # A value per mode: identical arguments would reuse the first candidate (SRV-r2 dedupe).
                result, run, call = self.s.tool('propose_preference_rule', self.args(value='낮은 앵글을 선호 ('+mode+')'))
                self.assertEqual((result['status'], result['applied'], result['active'], result['approval_required'], result['duplicate']), ('proposed', False, False, True, False))
                self.assertEqual((result['scope'], result['replaces_active'], result['actor']), ('current-project', None, 'agent'))
                self.assertEqual(result['provenance'], dict(engine='local-contract-rehearsal', chat_model=None, permission_mode=mode, effort='low', run=run, call=call['id']))
                saved = next(x for x in self.s.raw()['preferences'] if x['id'] == result['preference_id'])
                self.assertEqual((saved['status'], saved['song'], saved['ip'], saved['reason']), ('proposed', 'A', 'default', REASON))
                self.assertEqual(saved['origin']['provenance'], result['provenance'])
                self.assertEqual(self.settings_state(), before)
        self.assertEqual([x['status'] for x in self.s.raw()['preferences']], ['proposed', 'proposed'])
        self.assertEqual(preference_rules.resolve(self.s.raw()['preferences'], 'default', 'A'), [])
        self.assertEqual(len(self.s.store.state()['preferences']), 2)
        evidence('preference-receipt', result)

    def test_active_rule_in_same_category_is_superseded_only_on_human_approval(self):
        first = self.s.call('preference_propose', ip='default', song='A', category='camera', value='수평 구도', evidence='e', reason='r', supersedes=None)['preference']
        self.s.call('preference_review', id=first, decision='active', reason='owner')
        result, _, _ = self.s.tool('propose_preference_rule', self.args())
        self.assertEqual(result['replaces_active'], first)
        self.assertIn('v%d' % first, result['note'])
        self.assertEqual([x['status'] for x in self.s.raw()['preferences']], ['active', 'proposed'])
        other, _, _ = self.s.tool('propose_preference_rule', self.args(category='color'))
        self.assertIsNone(other['replaces_active'])
        self.s.call('preference_review', id=result['preference_id'], decision='active', reason='owner approved')
        self.assertEqual([x['status'] for x in self.s.raw()['preferences']], ['paused', 'active', 'proposed'])

    def test_read_only_invalid_category_and_long_reason_store_nothing(self):
        self.s.settings('read_only')
        result, _, _ = self.s.tool('propose_preference_rule', self.args())
        self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
        self.s.settings('review')
        result, _, _ = self.s.tool('propose_preference_rule', self.args(category='permission'))
        self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'INVALID_TOOL_ARGUMENTS'))
        result, _, _ = self.s.tool('propose_preference_rule', dict(self.args(), model_reason='x'*301))
        self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'MODEL_REASON_1_TO_300_CHARACTERS'))
        self.assertEqual(self.s.raw()['preferences'], [])

    def test_identical_agent_candidate_reuses_the_pending_one(self):
        first, _, _ = self.s.tool('propose_preference_rule', self.args())
        again, _, _ = self.s.tool('propose_preference_rule', self.args())
        self.assertEqual((again['status'], again['preference_id'], again['duplicate'], again['active']), ('proposed', first['preference_id'], True, False))
        self.assertEqual(len(self.s.raw()['preferences']), 1)
        # A different value or evidence is a new candidate; after review the same arguments propose again.
        other, _, _ = self.s.tool('propose_preference_rule', self.args(value='높은 앵글을 선호'))
        self.assertEqual((other['duplicate'], len(self.s.raw()['preferences'])), (False, 2))
        self.s.call('preference_review', id=first['preference_id'], decision='rejected', reason='owner')
        fresh, _, _ = self.s.tool('propose_preference_rule', self.args())
        self.assertEqual((fresh['duplicate'], len(self.s.raw()['preferences'])), (False, 3))

    def test_duplicate_candidate_reports_the_stored_origin(self):
        self.s.settings('review', 'medium')
        first, first_run, first_call = self.s.tool('propose_preference_rule', self.args())
        self.s.settings('full_access', 'high')
        again, _, _ = self.s.tool('propose_preference_rule', self.args())
        self.assertEqual((again['duplicate'], again['preference_id']), (True, first['preference_id']))
        self.assertEqual(again['provenance'], dict(engine='local-contract-rehearsal', chat_model=None, permission_mode='review', effort='medium', run=first_run, call=first_call['id']))
        saved, = self.s.raw()['preferences']
        self.assertEqual(saved['origin'], {k:again[k] for k in ('actor', 'model_reason', 'model_reason_label', 'provenance')})

    def test_open_candidates_per_category_are_capped_with_a_structured_refusal(self):
        limit = __import__('local_creation_tools').PREFERENCE_PENDING_LIMIT
        self.assertEqual(limit, 10)
        for i in range(limit):
            result, _, _ = self.s.tool('propose_preference_rule', self.args(value='앵글 %d' % i))
            self.assertEqual((result['status'], result['duplicate']), ('proposed', False))
        before = self.s.raw()['preferences']
        refused, _, _ = self.s.tool('propose_preference_rule', self.args(value='앵글 넘침'))
        self.assertEqual(refused, dict(status='blocked', code='PREFERENCE_CANDIDATE_LIMIT', retryable=False, category='camera', open_candidates=limit, limit=limit, note=refused['note']))
        self.assertIn('연출 취향', refused['note'])
        self.assertEqual(self.s.raw()['preferences'], before)
        # An identical repeat still reuses its candidate; another category is unaffected.
        again, _, _ = self.s.tool('propose_preference_rule', self.args(value='앵글 0'))
        self.assertEqual((again['status'], again['duplicate']), ('proposed', True))
        other, _, _ = self.s.tool('propose_preference_rule', self.args(category='color'))
        self.assertEqual((other['status'], other['duplicate']), ('proposed', False))
        # A human review frees a slot.
        self.s.call('preference_review', id=before[0]['id'], decision='rejected', reason='owner')
        fresh, _, _ = self.s.tool('propose_preference_rule', self.args(value='앵글 넘침'))
        self.assertEqual(fresh['status'], 'proposed')
        self.assertEqual(sum(x['status'] == 'proposed' and x['category'] == 'camera' for x in self.s.raw()['preferences']), limit)

    def test_restart_keeps_the_pending_candidate(self):
        result, _, _ = self.s.tool('propose_preference_rule', self.args())
        reopened = app.Store(self.s.tmp.name).state()['preferences']
        self.assertEqual([(x['id'], x['status'], x['origin']['actor']) for x in reopened], [(result['preference_id'], 'proposed', 'agent')])


class GeneralChatToolsTest(unittest.TestCase):
    """Through the real general chat turn with the contract-fake transport."""
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store

    def post(self, action, cid=None, **data):
        status, result = self.f.session_action(cid, action, **data) if cid else self.f.action(action, **data)
        self.assertEqual(status, 200, result);return result

    def project(self, cid=None):return (self.f.session_state(cid) if cid else self.f.state())['projects']['A']

    def send(self, name, arguments, cid=None):
        self.store.general_chat_runtime.transport.responses = [response([use('a2b-call', name, arguments)], 'tool_use')]
        preview = self.post('general_chat_preview', cid, song='A', prompt='합성 도구 시험', maximum_micro=10000)['general_chat_preview']
        self.assertIn(name, preview['tool_scope'])
        self.post('general_chat_decide', cid, song='A', preview_id=preview['id'], manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        project = self.project(cid);turn = project['general_chat_turns'][-1]
        follow = project['general_chat_previews'][-1]
        blocks = [b for m in follow['message_body']['messages'] if isinstance(m.get('content'), list) for b in m['content'] if b.get('type') == 'tool_result']
        return turn, (json.loads(blocks[-1]['content']) if blocks else None), preview

    def seed_timeline(self):
        self.post('shot', song='A', shot='s', description='synthetic media')
        self.post('take', song='A', shot='s', shot_revision=0, filename='base.png',
                  content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
                  reason='own fixture', rights='directly authored fixture')
        self.post('select', song='A', shot='s', take=1, shot_revision=1)
        self.post('review_take', song='A', shot='s', take=1, decision='approved', reason='checked')
        value = editing.current(self.project());value['profile'] = 'preview'
        self.post('timeline', song='A', timeline=value);self.post('approve_timeline', song='A')
        project = self.project()
        return project['timeline_head'], project['timeline_versions'][project['timeline_head']-1]['approval']['id']

    def test_scene_proposal_through_general_chat_uses_the_strict_schema(self):
        self.post('shot', song='A', shot='s', description='synthetic 3D')
        shot_id = production_context.shot_id(self.project(), 's')
        created = self.post('scene_create', song='A', shot_id=shot_id, scene=sample())['scene']
        self.post('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')
        turn, result, preview = self.send('propose_scene_3d', scene_args(shot_id))
        definition = next(d for d in preview['message_body']['tools'] if d['name'] == 'propose_scene_3d')
        self.assertTrue(definition['strict'])
        self.assertEqual(definition['input_schema']['required'], ['shot_id', 'base_revision', 'operations', 'model_reason'])
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        self.assertEqual((result['status'], result['applied'], result['provenance']['engine'], result['provenance']['permission_mode']),
                         ('proposed', False, 'contract-fake', 'review'))
        self.assertEqual(result['provenance']['call'], self.project()['production_runs'][-1]['calls'][-1]['id'])

    def test_preference_candidate_through_general_chat(self):
        turn, result, _ = self.send('propose_preference_rule', dict(category='editing', value='빠른 컷', evidence='대화 근거', model_reason=REASON))
        self.assertEqual((turn['status'], result['status'], result['active']), ('awaiting_continuation_approval', 'proposed', False))
        self.assertEqual([x['status'] for x in self.f.state()['preferences']], ['proposed'])

    def set_mode(self, mode):
        with self.store.connect() as c:p = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']
        current = agent_preferences.profile(p, 'anthropic-haiku-5-5')
        if current['mode'] != mode:
            self.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=current['revision'], mode=mode, effort='low')

    def test_permission_lowered_to_read_only_mid_request_in_a_real_turn_saves_nothing(self):
        version, _ = self.seed_timeline()  # creates shot 's' with an approved timeline
        shot_id = production_context.shot_id(self.project(), 's')
        created = self.post('scene_create', song='A', shot_id=shot_id, scene=sample())['scene']
        self.post('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')
        cases = dict(propose_scene_3d=scene_args(shot_id), propose_preference_rule=dict(category='camera', value='v', evidence='e', model_reason=REASON))
        cases['propose_timeline_changes'] = dict(description='d', timeline_version=version, commands=[dict(op='set_captions', cues=[dict(start=0, end=1, text='x')])])
        for start in ('review', 'full_access'):
            for name, arguments in cases.items():
                with self.subTest(start=start, tool=name):
                    self.set_mode(start)
                    with self.store.connect() as c:rows = c.execute('SELECT count(*) FROM scene_proposals').fetchone()[0]
                    head, proposals = self.project()['timeline_head'], len(self.project().get('timeline_edit_proposals', []))
                    self.store.general_chat_runtime.transport.responses = [response([use('mid-'+uuid.uuid4().hex[:6], name, arguments)], 'tool_use')]
                    preview = self.post('general_chat_preview', song='A', prompt='합성 도구 시험', maximum_micro=10000)['general_chat_preview']
                    self.assertIn(name, preview['tool_scope'])
                    self.post('general_chat_decide', song='A', preview_id=preview['id'], manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
                    self.set_mode('read_only')  # lowered after approval, before the response is processed
                    self.assertTrue(self.store.general_chat_runtime.process_next())
                    project = self.project();turn = project['general_chat_turns'][-1]
                    result = project['production_runs'][-1]['calls'][-1]['result']
                    self.assertEqual(turn['status'], 'awaiting_continuation_approval')
                    self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
                    with self.store.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM scene_proposals').fetchone()[0], rows)
                    self.assertEqual(self.f.state()['preferences'], [])
                    self.assertEqual((project['timeline_head'], len(project.get('timeline_edit_proposals', []))), (head, proposals))
                    follow = project['general_chat_previews'][-1]
                    self.post('general_chat_decide', song='A', preview_id=follow['id'], manifest_sha256=follow['manifest_sha256'], decision='reject', rights_confirmed=True)

    def test_foreign_or_unknown_render_grant_is_a_structured_result_not_outcome_unknown(self):
        version, grant = self.seed_timeline()
        other = self.post('conversation_create', song='A', title='other')['conversation']['id']
        jobs = len(self.f.state()['jobs'])
        for identifier in (grant, 'unknown-grant'):
            with self.subTest(grant=identifier):
                turn, result, _ = self.send('request_render', dict(timeline_version=version, grant_id=identifier), cid=other)
                self.assertEqual(turn['status'], 'awaiting_continuation_approval', turn)
                self.assertEqual(result, dict(status='blocked', code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED', retryable=False))
                follow = self.project(other)['general_chat_previews'][-1]
                self.post('general_chat_decide', other, song='A', preview_id=follow['id'], manifest_sha256=follow['manifest_sha256'], decision='reject', rights_confirmed=False)
        self.assertEqual(len(self.f.state()['jobs']), jobs)
        # Human actions keep the HTTP preflight: the same foreign grant is still a 400.
        status, value = self.f.session_action(other, 'motion_render', song='A', shot_id=production_context.shot_id(self.project(), 's'), motion_revision=1, grant_id=grant)
        self.assertEqual(status, 400, value)
        self.assertIn('현재 대화에서 확인한 출력 승인만', json.dumps(value, ensure_ascii=False))

    def test_foreign_motion_grant_through_direct_tool_is_structured(self):
        version, grant = self.seed_timeline()
        other = self.post('conversation_create', song='A', title='other')['conversation']['id']
        run = self.post('production_run', other, song='A')['run']['id']
        for name, arguments in (('request_render', dict(timeline_version=version, grant_id=grant)),
                                ('request_motion_render', dict(shot_id=production_context.shot_id(self.project(), 's'), motion_revision=1, grant_id=grant))):
            with self.subTest(tool=name):
                status, value = self.f.session_action(other, 'production_tool', song='A', run=run,
                                                      call=dict(id=uuid.uuid4().hex, name=name, arguments=arguments, complete=True))
                self.assertEqual(status, 200, value)
                self.assertEqual(value['tool'], dict(status='blocked', code='VALIDATION_OR_HUMAN_APPROVAL_REQUIRED', retryable=False))


if __name__ == '__main__':
    unittest.main()
