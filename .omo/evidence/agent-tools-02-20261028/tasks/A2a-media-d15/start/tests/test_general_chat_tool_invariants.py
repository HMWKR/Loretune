"""Tool exposure invariants for general and legacy chat; no model or provider calls."""
import json
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import agent_preferences
import chat_general
import chat_protocols
import chat_sessions
import chat_runtime
import production_context
import production_tools
from tests import test_general_chat_media_preparation as media

DELETE_TOOLS = agent_preferences.ACCOUNT_DELETE_TOOLS | agent_preferences.FILE_DELETE_TOOLS


class StaticToolScopeTest(unittest.TestCase):
    def test_general_scope_excludes_generation_and_every_delete_name(self):
        allowed = set(chat_general.ALLOWED_TOOLS)
        self.assertEqual(len(allowed), len(chat_general.ALLOWED_TOOLS))
        self.assertNotIn('request_media_generation', allowed)
        self.assertEqual(allowed & agent_preferences.ACCOUNT_DELETE_TOOLS, set())
        self.assertEqual(allowed & agent_preferences.FILE_DELETE_TOOLS, set())
        self.assertEqual((set(production_tools.TOOLS) | agent_preferences.READ_TOOLS) & DELETE_TOOLS, set())
        self.assertTrue(allowed <= set(production_tools.TOOLS))
        self.assertTrue(agent_preferences.READ_TOOLS <= set(production_tools.TOOLS))
        self.assertNotIn('request_media_generation', agent_preferences.READ_TOOLS)
        for name in sorted(DELETE_TOOLS):
            with self.subTest(name=name), self.assertRaises(ValueError):
                production_tools.validate(name, {})

    def test_full_access_auto_draft_is_exactly_five_timeline_commands(self):
        self.assertEqual(agent_preferences.AUTO_DRAFT_COMMANDS,
                         {'set_clip', 'reorder_clips', 'set_captions', 'set_audio_offset', 'set_motion_overlay'})

    def test_legacy_runtime_default_scope_excludes_media_generation(self):
        # D1 (user approved): the legacy default is an explicit list without
        # request_media_generation; every other tool stays, in TOOLS order.
        value = chat_runtime.ChatRuntime.limits(SimpleNamespace(approval={}))
        self.assertNotIn('request_media_generation', value['tools'])
        self.assertEqual(value['tools'], [t for t in production_tools.TOOLS if t != 'request_media_generation'])

    def test_every_tool_has_a_short_specific_description(self):
        self.assertEqual(set(chat_protocols.DESCRIPTIONS), set(production_tools.TOOLS))
        for provider in chat_protocols.PROVIDERS:
            for definition in chat_protocols.tool_definitions(provider):
                text = definition['description']
                with self.subTest(provider=provider, name=definition['name']):
                    self.assertEqual(text, chat_protocols.DESCRIPTIONS[definition['name']])
                    self.assertNotIn('server-controlled', text)
                    self.assertNotIn('Loretune', text)
                    self.assertNotIn('\n', text)
                    self.assertLessEqual(len(text), 160)


class GeneralChatToolRefusalTest(unittest.TestCase):
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.store = self.m.f.http.store

    def refused(self, name, arguments):
        requests = []
        original = self.store.mutate
        def record(request):
            if request['action'] == 'production_tool':requests.append(request)
            return original(request)
        with patch.object(self.store, 'mutate', side_effect=record):
            project = self.m.send_tool(name, arguments)
        self.assertEqual(requests, [])
        self.assertEqual(project['production_runs'][-1]['calls'], [])
        self.m.assert_no_media_execution()
        return project['general_chat_turns'][-1]

    def test_generation_request_ends_turn_unknown_before_any_tool_request(self):
        plan = self.m.project()['guided_plans'][-1]['id']
        turn = self.refused('request_media_generation', dict(plan_id=plan, action_id='synthetic-action', grant_id='synthetic-grant'))
        self.assertEqual(turn['status'], 'outcome_unknown')

    def test_delete_tool_names_end_turn_unknown_before_any_tool_request(self):
        for name in ('delete_account', 'delete_file'):
            with self.subTest(name=name):
                self.setUp()
                self.assertEqual(self.refused(name, {})['status'], 'outcome_unknown')


class PreparedVideoReferenceTest(unittest.TestCase):
    """prepare_video_action handles become structured results, never an HTTP preflight error."""
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.f = self.m.f
        self.store = self.f.http.store

    def hidden_take(self):
        with self.store.connect() as c:
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(body)
            state['projects']['A']['shots']['장면 1']['takes'].append(dict(id=99, sha256='e'*64, asset='/missing', conversation_id='other-conversation'))
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (revision+1, json.dumps(state, ensure_ascii=False)))

    def tool(self, **changes):
        project = self.m.project()
        arguments = dict(shot_id=production_context.shot_id(project, '장면 1'), model_id='fal-flux-schnell', prompt='p',
                         duration=5, shot_revision=project['shots']['장면 1']['revision'],
                         source_shot_id=production_context.shot_id(project, '장면 1'), source_take_id=99, source_sha256='e'*64)
        arguments.update(changes)
        run = self.m.post('production_run', song='A')['run']['id']
        status, value = self.f.action('production_tool', song='A', run=run,
                                      call=dict(id=uuid.uuid4().hex, name='prepare_video_action', arguments=arguments, complete=True))
        self.assertEqual(status, 200, value)
        return value['tool']

    def test_unknown_missing_and_hidden_source_are_invalid_media_input(self):
        self.hidden_take()
        with self.store.connect() as c:
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(body)
            # Visible control take: no conversation origin, so it is shared and reaches prepare.
            state['projects']['A']['shots']['장면 1']['takes'].append(dict(id=100, sha256='f'*64, asset='/missing'))
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (revision+1, json.dumps(state, ensure_ascii=False)))
        pipe = self.store.media_dispatch
        with patch.object(pipe, 'prepare', wraps=pipe.prepare) as prepare:
            for changes in (dict(source_shot_id='unknown-shot'), dict(source_take_id=98), {}):
                with self.subTest(changes=changes):
                    result = self.tool(**changes)
                    self.assertEqual((result['status'], result['code']), ('invalid_arguments', 'INVALID_MEDIA_INPUT'))
                    self.assertEqual(prepare.call_count, 0)
            # Positive control: the same arguments with a visible take do reach prepare.
            self.tool(source_take_id=100, source_sha256='f'*64)
            self.assertGreaterEqual(prepare.call_count, 1)
        self.assertEqual(self.m.actions(), [])
        self.m.assert_no_media_execution()

    def test_hidden_source_take_is_rejected_before_preparation(self):
        self.hidden_take()
        with self.store.connect() as c:
            raw = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']
        raw['shots']['장면 1']['takes'].append(dict(id=100, sha256='f'*64, asset='/missing'))
        project = chat_sessions.scoped(raw)
        shot = production_context.shot_id(project, '장면 1')
        arguments = dict(shot_id=shot, model_id='m', prompt='p', duration=5, shot_revision=0,
                         source_shot_id=shot, source_take_id=99, source_sha256='e'*64)
        class Reached(Exception):pass
        pipe = self.store.media_dispatch
        with patch.object(pipe, 'prepare', side_effect=Reached):
            with self.assertRaisesRegex(ValueError, 'source take unavailable'):
                pipe.prepare_tool(None, project, 'A', 'prepare_video_action', arguments)
            arguments['source_take_id'] = 100
            with self.assertRaises(Reached):
                pipe.prepare_tool(None, project, 'A', 'prepare_video_action', arguments)

    def test_human_endpoint_keeps_hidden_take_guard(self):
        self.hidden_take()
        status, value = self.f.action('review_take', song='A', shot='장면 1', take=99, decision='approved', note='')
        self.assertEqual(status, 400, value)
        self.assertIn('다른 대화의 미승인 Take', json.dumps(value, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
