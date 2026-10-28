"""A2b item 4: every general-chat tool x {read_only, review, full_access} x {normal, reduced mid-request, restart}.

Loopback HTTP fixture plus a second Store on the same SQLite file for the restart
case. No model, provider, count_tokens or paid call. Asserts the permission
outcome, the exposed manifest scope, and that nothing is applied automatically
except the documented FullAccess timeline draft (AUTO_DRAFT_COMMANDS).
"""
import json
import os
import unittest
import uuid

import agent_preferences
import app
import chat_general
import editing
import production_context
from tests import test_chat_general_http as base
from tests.test_scene_contract import sample

MODES = ('read_only', 'review', 'full_access')


def allowed(mode, name):
    return mode != 'read_only' or name in agent_preferences.READ_TOOLS


class ToolPermissionMatrixTest(unittest.TestCase):
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store
        self.post('shot', song='A', shot='s', description='synthetic media')
        self.post('take', song='A', shot='s', shot_revision=0, filename='base.png',
                  content='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
                  reason='own fixture', rights='directly authored fixture')
        self.post('select', song='A', shot='s', take=1, shot_revision=1)
        self.post('review_take', song='A', shot='s', take=1, decision='approved', reason='checked')
        value = editing.current(self.f.state()['projects']['A']);value['profile'] = 'preview'
        self.post('timeline', song='A', timeline=value);self.post('approve_timeline', song='A')
        self.shot = production_context.shot_id(self.raw()['projects']['A'], 's')
        created = self.post('scene_create', song='A', shot_id=self.shot, scene=sample())['scene']
        self.post('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')

    def post(self, action, **data):
        status, result = self.f.action(action, **data)
        self.assertEqual(status, 200, result);return result

    def raw(self):
        with self.store.connect() as c:return json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])

    def set_mode(self, mode):
        current = agent_preferences.profile(self.raw()['projects']['A'], 'anthropic-haiku-5-5')
        if current['mode'] != mode:
            self.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=current['revision'], mode=mode, effort='low')

    def arguments(self, name):
        p = self.raw()['projects']['A'];head = p['timeline_head']
        return dict(
            search_project_context={'query':'current'}, get_model_capabilities={'role':'image'},
            propose_media_plan=dict(goal='g', scenes='s', style='', constraints='', kind='narrative'),
            estimate_media_plan={'plan_id':'missing-plan'},
            prepare_image_action=dict(shot_id=self.shot, model_id='fal-flux-schnell', model_reason='r', prompt='p', ratio='16:9', shot_revision=p['shots']['s']['revision']),
            prepare_video_action=dict(shot_id=self.shot, model_id='fal-kling-2-5-turbo', model_reason='r', prompt='p', duration=5,
                                      shot_revision=p['shots']['s']['revision'], source_shot_id=self.shot, source_take_id=1, source_sha256='a'*64),
            get_generation_job={'job_id':'missing'}, get_agent_settings={},
            propose_timeline_changes=dict(description='matrix', timeline_version=head, commands=[dict(op='set_captions', cues=[dict(start=0, end=1, text='matrix')])]),
            propose_motion_scene=dict(shot_id=self.shot, base_motion_revision=0, scene={}),
            request_motion_render=dict(shot_id=self.shot, motion_revision=1, grant_id='g'),
            request_render=dict(timeline_version=head, grant_id='g'),
            propose_scene_3d=dict(shot_id=self.shot, base_revision=1, operations=[dict(target='camera', id='camera', field='lens_mm', value=35)], model_reason='r'),
            propose_preference_rule=dict(category='camera', value='v', evidence='e', model_reason='r'))[name]

    def observed(self):
        """Everything an agent tool must not apply on its own."""
        state = self.raw();p = state['projects']['A']
        with self.store.connect() as c:
            scenes = [json.loads(r[0])['head'] for r in c.execute('SELECT body FROM scene_records ORDER BY rowid')]
            jobs = sum(c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('jobs', 'generation_jobs', 'action_jobs'))
            reservations = c.execute("SELECT count(*) FROM reservations r JOIN budgets b ON b.id=r.budget WHERE b.scope LIKE 'project:%'").fetchone()[0]
        sessions = [(s.get('agent_settings'), s.get('agent_settings_history')) for s in p.get('chat_sessions', [])]
        return dict(timeline_head=p['timeline_head'], scenes=scenes, jobs=jobs, media_reservations=reservations,
                    active_preferences=[x['id'] for x in state.get('preferences', []) if x['status'] == 'active'],
                    model_settings=p.get('model_settings'), agent_settings=sessions)

    def call(self, name, run, store=None):
        store = store or self.store
        with store.connect() as c:revision = c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        call = dict(id=uuid.uuid4().hex, name=name, arguments=self.arguments(name), complete=True)
        return store.mutate(dict(action='production_tool', data=dict(song='A', run=run, call=call), revision=revision, request_id=uuid.uuid4().hex))['tool']

    def check(self, mode, scenario, name, run, effective, store=None):
        before = self.observed()
        result = self.call(name, run, store)
        after = self.observed()
        if allowed(effective, name):
            self.assertNotEqual(result.get('code'), 'AGENT_READ_ONLY', result)
        else:
            self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'AGENT_READ_ONLY'))
            self.assertEqual(after, before)
        if name == 'propose_timeline_changes' and effective == 'full_access':
            # The one documented automatic draft (AUTO_DRAFT_COMMANDS); output approval stays human.
            self.assertEqual((result['status'], result['application_actor'], result['output_approved']), ('applied_draft', 'agent-draft', False))
            self.assertEqual(after['timeline_head'], before['timeline_head']+1)
            before['timeline_head'] = after['timeline_head']
        if name in {'propose_scene_3d', 'propose_preference_rule'} and allowed(effective, name):
            self.assertEqual((result['status'], result['applied']), ('proposed', False))
        self.assertEqual(after, before, (mode, scenario, name, result))
        return result

    def test_every_tool_in_every_mode_and_scenario(self):
        self.assertEqual(len(chat_general.ALLOWED_TOOLS), 14)
        outcomes = {}
        for mode in MODES:
            self.set_mode(mode)
            preview = self.f.preview()
            expected = [n for n in chat_general.ALLOWED_TOOLS if allowed(mode, n)]
            self.assertEqual(preview['tool_scope'], expected)
            self.assertEqual({d['name'] for d in preview['message_body']['tools']}, set(expected))
            for name in chat_general.ALLOWED_TOOLS:
                with self.subTest(mode=mode, scenario='normal', tool=name):
                    outcomes[(mode, 'normal', name)] = self.check(mode, 'normal', name, self.post('production_run', song='A')['run']['id'], mode)['status']
            runs = {name:self.post('production_run', song='A')['run']['id'] for name in chat_general.ALLOWED_TOOLS}
            self.set_mode('read_only')  # lowered while the runs are still accepting tools
            for name in chat_general.ALLOWED_TOOLS:
                with self.subTest(mode=mode, scenario='reduced', tool=name):
                    outcomes[(mode, 'reduced', name)] = self.check(mode, 'reduced', name, runs[name], 'read_only')['status']
            self.set_mode(mode)
            runs = {name:self.post('production_run', song='A')['run']['id'] for name in chat_general.ALLOWED_TOOLS}
            reopened = app.Store(self.f.tmp.name)
            for name in chat_general.ALLOWED_TOOLS:
                with self.subTest(mode=mode, scenario='restart', tool=name):
                    outcomes[(mode, 'restart', name)] = self.check(mode, 'restart', name, runs[name], mode, reopened)['status']
        self.assertEqual(len(outcomes), 14*3*3)
        blocked = [k for k in outcomes if not allowed('read_only' if k[1] == 'reduced' else k[0], k[2])]
        # 9 write tools: blocked in read_only (3 scenarios) and after the mid-request reduction in review/full_access.
        self.assertEqual(len(blocked), 9*3+9*2)
        self.assertEqual({outcomes[k] for k in blocked}, {'invalid_arguments'})
        evidence = {'%s/%s/%s' % k:v for k, v in sorted(outcomes.items())}
        self.assertEqual(sum(1 for v in evidence.values() if v == 'applied_draft'), 2)  # full_access normal + restart only; never reduced, review or read_only
        folder = os.environ.get('A2B_EVIDENCE')
        if folder:
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, 'permission-matrix.json'), 'w', encoding='utf-8') as out:
                json.dump(dict(tools=list(chat_general.ALLOWED_TOOLS), read_tools=sorted(agent_preferences.READ_TOOLS), outcomes=evidence), out, ensure_ascii=False, indent=1)

    def test_full_access_lowered_to_review_mid_request_never_drafts(self):
        self.set_mode('full_access')
        runs = {name:self.post('production_run', song='A')['run']['id'] for name in ('propose_timeline_changes', 'propose_scene_3d', 'propose_preference_rule')}
        self.set_mode('review')
        for name, run in runs.items():
            with self.subTest(tool=name):
                result = self.check('full_access', 'reduced-to-review', name, run, 'review')
                self.assertEqual(result['status'], 'proposed')
        ceilings = {r['id']:r['agent_permission_ceiling'] for r in self.raw()['projects']['A']['production_runs'] if r['id'] in runs.values()}
        self.assertEqual(set(ceilings.values()), {'review'})


if __name__ == '__main__':
    unittest.main()
