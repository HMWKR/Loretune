"""General chat estimate_media_plan over saved fixture quotes; no model or provider calls."""
import json
import unittest

from tests import test_general_chat_media_preparation as media
from tests.test_general_chat_job_query import assert_only_turn_changed, fingerprint
from tests.test_chat_runtime import response, use


class GeneralChatEstimateTest(unittest.TestCase):
    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp()
        self.addCleanup(self.m.doCleanups)
        self.f = self.m.f
        self.store = self.f.http.store

    def plan(self):
        return self.m.project()['guided_plans'][-1]['id']

    def prepare(self):
        # The fixture quote is bound to this exact prompt; each call saves a new action.
        project = self.m.project()
        return self.m.post('media_prepare', song='A', shot='장면 1', shot_revision=project['shots']['장면 1']['revision'],
                           prompt=self.m.prompt, options={'ratio':'16:9'}, refs=[])['media_action']['action']['id']

    def edit_state(self, change):
        with self.store.connect() as c:
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(body)
            change(state['projects']['A'])
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (revision+1, json.dumps(state, ensure_ascii=False)))

    def estimate(self, cid=None):
        name, arguments = 'estimate_media_plan', {'plan_id':self.plan()}
        if cid is None:
            project = self.m.send_tool(name, arguments)
        else:
            self.store.general_chat_runtime.transport.responses = [response([use('estimate-call', name, arguments)], 'tool_use')]
            status, value = self.f.session_action(cid, 'general_chat_preview', song='A', prompt='견적 확인', maximum_micro=10000)
            self.assertEqual(status, 200, value)
            preview = value['general_chat_preview']
            status, value = self.f.session_action(cid, 'general_chat_decide', song='A', preview_id=preview['id'],
                                                  manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
            self.assertEqual(status, 200, value)
            self.assertTrue(self.store.general_chat_runtime.process_next())
            project = self.f.session_state(cid)['projects']['A']
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval', project['general_chat_turns'][-1])
        return project['production_runs'][-1]['calls'][-1]['result']

    def test_sum_of_owned_prepared_actions_is_labelled_not_whole_plan_or_billing(self):
        first, second = self.prepare(), self.prepare()
        before = fingerprint(self.store)
        result = self.estimate()
        self.assertEqual(result['status'], 'estimated')
        self.assertEqual({x['action_id'] for x in result['actions']}, {first, second})
        self.assertEqual(result['total'], {'amount':'0.02','currency':'USD'})
        self.assertIs(result['billing_confirmed'], False)
        self.assertIs(result['approval'], False)
        self.assertIn('계획 전체 견적', result['label'])
        self.assertIn('청구', result['label'])
        assert_only_turn_changed(self, before, fingerprint(self.store))
        self.m.assert_no_media_execution()

    def test_held_and_rejected_actions_are_excluded(self):
        kept, held, rejected = self.prepare(), self.prepare(), self.prepare()
        self.m.post('media_action_decide', song='A', action_id=held, decision='held')
        self.m.post('media_action_decide', song='A', action_id=rejected, decision='rejected')
        result = self.estimate()
        self.assertEqual([x['action_id'] for x in result['actions']], [kept])
        self.assertEqual(result['total'], {'amount':'0.01','currency':'USD'})
        self.m.assert_no_media_execution()

    def test_actions_owned_by_another_conversation_are_excluded(self):
        own, foreign = self.prepare(), self.prepare()
        # Synthetic ownership record: the same plan's action attributed to another conversation.
        self.edit_state(lambda p: p.setdefault('conversation_owners', {}).__setitem__(
            foreign, dict(conversation_id='other-conversation', kind='production_actions')))
        result = self.estimate()
        self.assertEqual([x['action_id'] for x in result['actions']], [own])
        self.m.assert_no_media_execution()

    def test_other_conversation_cannot_see_plan_and_gets_not_found(self):
        self.prepare()
        cid = self.m.post('conversation_create', song='A', title='other')['conversation']['id']
        result = self.estimate(cid)
        self.assertEqual(result, {'status':'not_found'})
        self.m.assert_no_media_execution()

    def test_expired_quote_makes_estimate_incomplete(self):
        identifier = self.prepare()
        with self.store.connect() as c:
            body = json.loads(c.execute('SELECT body FROM production_actions WHERE id=?', (identifier,)).fetchone()[0])
            body['options']['quote']['expires'] = 1
            c.execute('UPDATE production_actions SET body=? WHERE id=?', (json.dumps(body), identifier))
        result = self.estimate()
        self.assertEqual(result['status'], 'incomplete')
        self.assertIsNone(result['total'])
        self.assertTrue(result['actions'][0]['expired'])
        self.m.assert_no_media_execution()

    def test_missing_media_connection_is_not_connected(self):
        self.prepare()
        self.store.media_dispatch = None
        result = self.estimate()
        self.assertEqual((result['status'], result['code']), ('blocked', 'LOCAL_TOOL_NOT_CONNECTED'))
        self.m.assert_no_media_execution()


if __name__ == '__main__':
    unittest.main()
