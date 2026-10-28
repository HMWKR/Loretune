"""SRV-r2: worst-case continuation bodies stay under the 64KiB transport cap.

Real fixtures, real tool results: search_project_context and estimate_media_plan run
through the general chat turn, then chat_runtime.compact_result -> result_message ->
continuation -> body produce the follow preview. Its message body is serialized with
the pinned transport encoder (BoundedMessagesTransport.encode_body), exactly as the
live path does before any credential read. The over-cap case runs the live-mode
transport with a synthetic stdlib opener only. No model, provider, count_tokens or
paid call.
"""
import json
import os
import unittest
import uuid
from unittest.mock import patch

import anthropic_ontology as anthropic
import chat_general
import fal_dispatch
import production_context
from tests import test_chat_general_http as base
from tests import test_general_chat_activation as activation
from tests import test_general_chat_media_preparation as media
from tests.test_chat_runtime import response, use
from tests.test_scene_contract import sample

CAP = 65536
# Margin kept free for the user prompt, history and a longer note (bytes).
MARGIN = 16384
WORST_SCENES = 32  # the former single-page cap; 32 scenes x 10 pending is the A2b worst case
WORST_PENDING = 10


def wire(body):
    """Exact bytes the live transport would send (same encoder, same 64KiB check)."""
    return len(anthropic.BoundedMessagesTransport(max_request_bytes=CAP).encode_body(body))


def record(name, value):
    folder = os.environ.get('SRV_R2_EVIDENCE')
    if folder:
        with open(os.path.join(folder, name+'.json'), 'w', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False, indent=1)


def seed_scenes(store, scenes=WORST_SCENES, pending=WORST_PENDING):
    """32 approved scenes, each with 10 pending proposals, written as the HTTP handler does."""
    def call(action, **data):
        with store.connect() as c:revision = c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        return store.mutate(dict(action=action, data=data, revision=revision, request_id=uuid.uuid4().hex))
    for i in range(scenes):
        shot = 'cap-%02d' % i
        call('shot', song='A', shot=shot, description='synthetic 3D')
        with store.connect() as c:project = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']
        created = call('scene_create', song='A', shot_id=production_context.shot_id(project, shot), scene=sample())['scene']
        call('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')
        for j in range(pending):
            call('scene_propose', song='A', scene_id=created['scene_id'], base_revision=1,
                 operations=[dict(target='camera', id='camera', field='lens_mm', value=20+j)])


def tool_result(body):
    blocks = [b for m in body['messages'] if isinstance(m.get('content'), list) for b in m['content'] if b.get('type') == 'tool_result']
    return json.loads(blocks[-1]['content'])


class SceneStatusBodyCapTest(unittest.TestCase):
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store
        seed_scenes(self.store)

    def turn(self, query):
        self.store.general_chat_runtime.transport.responses = [response([use('cap-call', 'search_project_context', {'query':query})], 'tool_use')]
        preview = self.f.preview()
        status, result = self.f.approve(preview);self.assertEqual(status, 200, result)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        project = self.f.state()['projects']['A']
        return project['general_chat_turns'][-1], project['general_chat_previews'][-1], preview

    def test_worst_case_scene_status_continuation_fits_under_the_cap_with_margin(self):
        turn, follow, first = self.turn('scene-status')
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        status = tool_result(follow['message_body'])['execution_targets']['scene_status']
        limit = production_context.SCENE_STATUS_LIMIT
        self.assertEqual((len(status['scenes_3d']), status['scenes_3d_total'], status['scenes_3d_not_shown'], status['scenes_3d_truncated']),
                         (limit, WORST_SCENES, WORST_SCENES-limit, True))
        self.assertTrue(all((x['pending_total'], len(x['pending_proposals'])) == (WORST_PENDING, WORST_PENDING) for x in status['scenes_3d']))
        self.assertEqual(status['next_query'], 'scene-status offset=%d' % limit)
        size = wire(follow['message_body'])
        self.assertLess(size, CAP)
        self.assertLessEqual(size, CAP-MARGIN)
        record('scene-status-worst-case-body', dict(scenes_total=WORST_SCENES, pending_per_scene=WORST_PENDING, page_scenes=limit,
                                                    first_body_bytes=wire(first['message_body']), continuation_body_bytes=size, cap=CAP, free_bytes=CAP-size))

    def test_every_page_fits_and_pages_cover_all_scenes_once(self):
        seen = [];query = 'scene-status'
        while query:
            turn, follow, _ = self.turn(query)
            self.assertEqual(turn['status'], 'awaiting_continuation_approval')
            self.assertLessEqual(wire(follow['message_body']), CAP-MARGIN)
            status = tool_result(follow['message_body'])['execution_targets']['scene_status']
            self.assertEqual(status['scenes_3d_not_shown'], WORST_SCENES-len(status['scenes_3d']))
            seen += [x['scene_id'] for x in status['scenes_3d']]
            query = status['next_query']
            # Close this turn before the next request (an awaiting continuation blocks new previews).
            status, result = self.f.approve(follow, decision='reject');self.assertEqual(status, 200, result)
        self.assertEqual(len(seen), WORST_SCENES);self.assertEqual(len(set(seen)), WORST_SCENES)


class EstimateBodyCapTest(unittest.TestCase):
    ACTIONS = 20

    def setUp(self):
        self.m = media.GeneralChatMediaPreparationTest('test_missing_adapter_blocks_without_enabling_catalog_model')
        self.m.setUp();self.addCleanup(self.m.doCleanups)
        self.f = self.m.f;self.store = self.f.http.store
        for _ in range(self.ACTIONS):
            arguments = self.m.arguments();arguments['model_reason'] = '가'*300  # longest allowed reason (900 bytes)
            run = self.m.post('production_run', song='A')['run']['id']
            result = self.m.post('production_tool', song='A', run=run, call=dict(id=uuid.uuid4().hex, name='prepare_image_action', arguments=arguments, complete=True))['tool']
            self.assertEqual(result['status'], 'proposed')
        self.plan = self.m.project()['guided_plans'][-1]['id']

    def turn(self, name, arguments):
        self.store.general_chat_runtime.transport.responses = [response([use('estimate-call', name, arguments)], 'tool_use')]
        status, result = self.f.approve(self.f.preview());self.assertEqual(status, 200, result)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        project = self.m.project()
        return project['general_chat_turns'][-1], project['general_chat_previews'][-1]

    def test_estimate_items_are_paged_with_counts_totals_and_a_fetch_path(self):
        turn, follow = self.turn('estimate_media_plan', {'plan_id':self.plan})
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        first = tool_result(follow['message_body'])
        limit = fal_dispatch.ESTIMATE_ITEM_LIMIT
        self.assertEqual((first['status'], len(first['actions']), first['actions_total'], first['actions_not_shown']),
                         ('estimated', limit, self.ACTIONS, self.ACTIONS-limit))
        # Total covers every item, not only the listed page.
        self.assertEqual(first['total'], {'amount':'0.2', 'currency':'USD'})  # 20 x 0.01 fixture quotes
        size = wire(follow['message_body'])
        self.assertLessEqual(size, CAP-MARGIN)
        listed = [x['action_id'] for x in first['actions']];query = first['next_query']
        self.assertEqual(query, 'media-estimate plan=%s offset=%d' % (self.plan, limit))
        self.f.approve(follow, decision='reject')
        sizes = [size]
        while query:
            turn, follow = self.turn('search_project_context', {'query':query})
            self.assertEqual(turn['status'], 'awaiting_continuation_approval')
            sizes.append(wire(follow['message_body']));self.assertLessEqual(sizes[-1], CAP-MARGIN)
            page = tool_result(follow['message_body'])['media_estimate']
            self.assertEqual((page['total'], page['excluded'], page['actions_total']), (first['total'], first['excluded'], self.ACTIONS))
            self.assertNotIn('execution_targets', tool_result(follow['message_body']))
            listed += [x['action_id'] for x in page['actions']];query = page['next_query']
            self.f.approve(follow, decision='reject')
        self.assertEqual(sorted(listed), sorted(x['id'] for x in self.m.actions()))
        self.assertEqual(len(set(listed)), self.ACTIONS)
        self.m.assert_no_media_execution()
        record('estimate-worst-case-body', dict(actions=self.ACTIONS, page_items=limit, reason_chars=300, body_bytes=sizes, cap=CAP))


class OverCapLiveTransportTest(unittest.TestCase):
    """Pre-send rejection of an over-cap continuation in live mode (synthetic opener only)."""
    def setUp(self):
        self.a = activation.GeneralChatActivationHTTPTest('test_real_mode_exact_wire_bytes_and_estimate_without_verified_account_claim')
        self.a.setUp();self.addCleanup(self.a.doCleanups)
        seed_scenes(self.a.http.store)

    def run_turn(self):
        self.a.socket.replies = [activation.reply([use('cap', 'search_project_context', {'query':'scene-status'})], 'tool_use')]
        preview = self.a.preview()
        status, result = self.a.approve(preview);self.assertEqual(status, 200, result)
        self.a.process()
        return result['turn']['id']

    def test_old_single_page_cap_is_rejected_before_send_and_the_turn_state_is_recorded(self):
        rejected = [];original = anthropic.BoundedMessagesTransport.encode_body
        def spy(transport, body):
            try:return original(transport, body)
            except anthropic.ProposalError as exc:
                rejected.append((exc.failure.get('category'), len(json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8'))));raise
        with patch.object(production_context, 'SCENE_STATUS_LIMIT', WORST_SCENES), patch.object(anthropic.BoundedMessagesTransport, 'encode_body', spy):
            identifier = self.run_turn()  # the pre-SRV-r2 single 32-scene page
        category, size = rejected[0]
        self.assertEqual((len(rejected), category), (1, 'request_too_large'))
        self.assertGreater(size, CAP)
        turn, held, attempts = self.a.reservation(identifier)
        project = self.a.project()
        # Round 1 (count + message) was sent; the oversized continuation never reached the opener.
        self.assertEqual([r[0] for r in self.a.socket.requests], [anthropic.BoundedCountTransport.endpoint, anthropic.ENDPOINT])
        self.assertEqual(attempts, [('chat-count', 'observed'), ('chat-message', 'observed')])
        with self.a.http.store.connect() as c:  # the projection hides consumed previews; count stored rows
            self.assertEqual([r[0] for r in c.execute('SELECT id FROM general_chat_previews')], [turn['preview_id']])  # no continuation preview
        # The search tool ran and its result was recorded; no continuation preview was created.
        call, = [c for r in project['production_runs'] if r['id'] == turn['run'] for c in r['calls']]
        self.assertEqual((call['name'], call['result']['status']), ('search_project_context', 'succeeded'))
        # Recorded state of the turn after the pre-send rejection (see SRV-r2 result.md).
        self.assertEqual(turn['status'], 'outcome_unknown')
        self.assertEqual(turn['error'], '요청을 중단했습니다. 기존 결과와 비용 상태를 확인하세요. 자동 재시도하지 않습니다.')
        self.assertEqual(held[0], 'estimated')
        self.assertEqual(turn['pricing_status'], 'priced')
        # That status blocks new previews in this conversation.
        status, value = self.a.action('general_chat_preview', song='A', prompt='다음 요청', maximum_micro=10000, total_maximum_micro=10000)
        self.assertEqual(status, 400, value)
        record('over-cap-live-rejection', dict(rejected_body_bytes=size, rejection=category, turn_status=turn['status'], error=turn['error'], reservation=held, attempts=attempts,
                                               sent_requests=len(self.a.socket.requests), new_preview_http_status=status))

    def test_paged_result_continues_in_live_mode(self):
        identifier = self.run_turn()
        turn, held, attempts = self.a.reservation(identifier)
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        follow = self.a.project()['general_chat_previews'][-1]
        self.assertLessEqual(wire(follow['message_body']), CAP-MARGIN)
        self.assertEqual(len(self.a.socket.requests), 2)


if __name__ == '__main__':
    unittest.main()
