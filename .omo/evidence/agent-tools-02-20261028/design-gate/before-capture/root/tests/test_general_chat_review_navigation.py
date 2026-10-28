"""Public chat result references are read-only and conversation scoped."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import unittest

import chat_general
from tests import test_general_chat_media_preparation as preparation


class GeneralChatReviewNavigationTest(unittest.TestCase):
    def setUp(self):
        self.h = preparation.GeneralChatMediaPreparationTest(
            'test_image_prepare_saves_one_card_and_http_replay_is_idempotent')
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)

    def stored(self):
        with self.h.f.http.store.connect() as c:
            return {table: c.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                    for table in ('state', 'general_chat_turns', 'general_chat_previews',
                                  'production_actions', 'execution_grants', 'generation_jobs',
                                  'provider_action_jobs', 'reservations')}

    def prepare(self):
        return self.h.send_tool('prepare_image_action', self.h.arguments())

    def test_saved_run_relation_is_read_only_and_matches_the_prepared_action(self):
        project = self.prepare()
        turn = project['general_chat_turns'][-1]
        run, = [r for r in project['production_runs'] if r['id'] == turn['run_id']]
        self.assertEqual(run['conversation_id'], turn['conversation_id'])
        call, = [x for x in run['calls'] if x['name'] == 'prepare_image_action']
        self.assertEqual(call['result']['action_id'], project['media_actions'][0]['id'])
        before = self.stored()
        for _ in range(2):
            current = self.h.project()['general_chat_turns'][-1]
            self.assertEqual(current['run_id'], run['id'])
            current['run_id'] = 'client-modified-copy'
        self.assertEqual(self.stored(), before)
        stored = json.loads(before['general_chat_turns'][-1][-1])
        self.assertEqual(stored['run'], run['id'])
        self.assertNotIn('run_id', stored)
        self.h.assert_no_media_execution()

    def test_legacy_missing_run_stays_missing_after_actual_get(self):
        turn = self.prepare()['general_chat_turns'][-1]
        with self.h.f.http.store.connect() as c:
            row = c.execute('SELECT body FROM general_chat_turns WHERE id=?', (turn['id'],)).fetchone()
            value = json.loads(row[0])
            value.pop('run')
            raw = json.dumps(value, ensure_ascii=False)
            c.execute('UPDATE general_chat_turns SET body=? WHERE id=?', (raw, turn['id']))
        before = self.stored()
        current = self.h.project()['general_chat_turns'][-1]
        self.assertIsNone(current['run_id'])
        self.assertEqual(self.stored(), before)
        self.h.assert_no_media_execution()

    def test_other_conversation_has_no_turn_run_or_prepared_action_reference(self):
        project = self.prepare()
        run_id = project['general_chat_turns'][-1]['run_id']
        cid = self.h.post('conversation_create', song='A', title='다른 대화')['conversation']['id']
        other = self.h.f.session_state(cid)['projects']['A']
        self.assertEqual(other['general_chat_turns'], [])
        self.assertEqual(other['media_actions'], [])
        self.assertNotIn(run_id, [x['id'] for x in other['production_runs']])
        self.h.assert_no_media_execution()

    def test_other_project_cannot_expose_the_prepared_turn_relation(self):
        turn = self.prepare()['general_chat_turns'][-1]
        self.h.post('project', name='B', era='default', story=0)
        other = self.h.f.state()['projects']['B']
        self.assertEqual(other['general_chat_turns'], [])
        self.assertEqual(other['media_actions'], [])
        self.assertNotIn(turn['run_id'], [x['id'] for x in other.get('production_runs', [])])
        self.h.assert_no_media_execution()

    def test_public_projection_does_not_mutate_the_stored_input(self):
        source = dict(id='turn', run='server-run', conversation_id='current', steps=[{'round': 0}])
        before = deepcopy(source)
        public = chat_general.public_turn(source)
        public['steps'][0]['round'] = 9
        self.assertEqual(source, before)
        self.assertEqual(public['run_id'], 'server-run')
        self.assertNotIn('run', public)

    def test_navigation_reference_and_async_focus_contracts(self):
        result = subprocess.run(['node', 'tests/general_chat_review_navigation.cjs'],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
