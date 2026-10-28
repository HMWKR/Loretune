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
        # Cursor page (SRV-r3): the next page ends before the oldest scene shown here.
        self.assertEqual(status['next_query'], 'scene-status before=%s' % status['scenes_3d'][0]['scene_id'])
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

    def test_old_single_page_result_is_withheld_with_a_budget_notice_and_the_turn_continues(self):
        # SRV-r2 recorded this case as outcome_unknown (pre-send rejection). SRV-r3: the result that would
        # overflow is replaced by CONTEXT_BUDGET_EXHAUSTED before any continuation is built or sent.
        rejected = [];original = anthropic.BoundedMessagesTransport.encode_body
        def spy(transport, body):
            try:return original(transport, body)
            except anthropic.ProposalError as exc:
                rejected.append(exc.failure.get('category'));raise
        with patch.object(production_context, 'SCENE_STATUS_LIMIT', WORST_SCENES), patch.object(anthropic.BoundedMessagesTransport, 'encode_body', spy):
            identifier = self.run_turn()  # the pre-SRV-r2 single 32-scene page
        self.assertEqual(rejected, [])
        turn, held, attempts = self.a.reservation(identifier)
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        self.assertEqual([r[0] for r in self.a.socket.requests], [anthropic.BoundedCountTransport.endpoint, anthropic.ENDPOINT])
        self.assertEqual(attempts, [('chat-count', 'observed'), ('chat-message', 'observed')])
        self.assertEqual(held[0], 'estimated')
        project = self.a.project()
        call, = [c for r in project['production_runs'] if r['id'] == turn['run'] for c in r['calls']]
        self.assertEqual((call['name'], call['result']['status'], call['result']['execution_targets']['scene_status']['scenes_3d_total']),
                         ('search_project_context', 'succeeded', WORST_SCENES))  # the full result is stored
        follow = project['general_chat_previews'][-1]
        size = wire(follow['message_body'])
        notice = tool_result(follow['message_body'])
        self.assertEqual((notice['code'], notice['tool'], notice['tool_status'], notice['result_included'], notice['next_query'], notice['retry']),
                         ('CONTEXT_BUDGET_EXHAUSTED', 'search_project_context', 'succeeded', False, 'scene-status', 'new_turn'))
        self.assertGreater(notice['body_bytes_with_result'], CAP)
        self.assertEqual(notice['body_limit_bytes'], chat_general.CONTINUATION_LIMIT)
        self.assertLessEqual(size, chat_general.CONTINUATION_LIMIT)
        record('over-cap-live-rejection', dict(withheld_body_bytes=notice['body_bytes_with_result'], notice_body_bytes=size, bytes_left=notice['bytes_left'],
                                               turn_status=turn['status'], reservation=held, attempts=attempts, sent_requests=len(self.a.socket.requests)))

    def test_over_cap_continuation_ends_the_turn_recoverably_with_zero_provider_writes(self):
        # Round 2: a long answer text plus another lookup. Even the budget notice cannot fit, so
        # nothing is created, reserved or sent for round 3 and a new request is allowed.
        self.a.socket.replies = [activation.reply([use('q0', 'search_project_context', {'query':'scene-status'})], 'tool_use')]
        preview = self.a.preview()
        status, result = self.a.approve(preview);self.assertEqual(status, 200, result)
        identifier = result['turn']['id'];self.a.process()
        for round_ in (1, 2):
            turn, _, _ = self.a.reservation(identifier)
            self.assertEqual(turn['status'], 'awaiting_continuation_approval')
            follow = self.a.project()['general_chat_previews'][-1]
            query = tool_result(follow['message_body'])['execution_targets']['scene_status']['next_query']
            blocks = ([dict(type='text', text='가'*4700)] if round_ == 2 else [])+[use('q%d' % round_, 'search_project_context', {'query':query})]
            self.a.socket.replies = [activation.reply(blocks, 'tool_use')]
            status, result = self.a.approve(follow);self.assertEqual(status, 200, result)
            self.a.process()
        turn, held, attempts = self.a.reservation(identifier)
        self.assertEqual(turn['status'], 'limit_reached')
        self.assertIn('CONTEXT_BUDGET_EXHAUSTED', turn['error'])
        self.assertEqual(turn['context_budget']['code'], 'CONTEXT_BUDGET_EXHAUSTED')
        self.assertGreater(turn['context_budget']['body_bytes'], CAP)
        self.assertEqual(turn['round'], 2)
        # Zero provider writes for the rejected round: 3 rounds x (count + message) only.
        self.assertEqual([r[0] for r in self.a.socket.requests], [anthropic.BoundedCountTransport.endpoint, anthropic.ENDPOINT]*3)
        with self.a.http.store.connect() as c:
            previews = c.execute('SELECT body FROM general_chat_previews').fetchall()
            states = [r[0] for r in c.execute('SELECT state FROM reservations')]
        self.assertEqual(len(previews), 3)  # first + 2 continuations; none for the rejected round
        # Nothing is held: each sent round is estimated from its received response, no reservation exists for the
        # rejected one (ledger 'release' applies only to 'reserved', and none is left).
        self.assertEqual(states, ['estimated']*3)
        self.assertEqual(held[0], 'estimated')
        status, value = self.a.action('general_chat_preview', song='A', prompt='다음 요청', maximum_micro=10000, total_maximum_micro=10000)
        self.assertEqual(status, 200, value)
        self.assertEqual(len(self.a.socket.requests), 6)  # a preview sends nothing
        record('over-cap-recoverable-end', dict(turn_status=turn['status'], error=turn['error'], context_budget=turn['context_budget'],
                                                reservations=states, sent_requests=len(self.a.socket.requests), new_preview_http_status=status))

    def test_paged_result_continues_in_live_mode(self):
        identifier = self.run_turn()
        turn, held, attempts = self.a.reservation(identifier)
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        follow = self.a.project()['general_chat_previews'][-1]
        self.assertLessEqual(wire(follow['message_body']), CAP-MARGIN)
        self.assertEqual(len(self.a.socket.requests), 2)



def next_query(value):
    """First non-null next_query in a tool result, as a model following the result would pick it."""
    if isinstance(value, dict):
        if value.get('next_query'):return value['next_query']
        value = list(value.values())
    if isinstance(value, list):
        for item in value:
            found = next_query(item)
            if found:return found
    return None


def follow_in_one_turn(test, first_call, project, process):
    """Scripted model: one lookup, then it follows next_query in the SAME turn through MAX_ROUNDS.

    Every continuation preview is approved as a user would. Returns per-round (status, body bytes, result)."""
    transport = test.store.general_chat_runtime.transport
    name, arguments = first_call
    transport.responses = [response([use('r0', name, arguments)], 'tool_use')]
    status, value = test.f.approve(test.f.preview());test.assertEqual(status, 200, value)
    process()
    rounds = []
    for round_ in range(1, chat_general.MAX_ROUNDS+1):
        latest = project()
        turn = latest['general_chat_turns'][-1]
        test.assertNotEqual(turn['status'], 'outcome_unknown', turn.get('error'))
        if turn['status'] != 'awaiting_continuation_approval':
            rounds.append((turn['status'], None, None));break
        follow = latest['general_chat_previews'][-1]
        result = tool_result(follow['message_body'])
        rounds.append((turn['status'], wire(follow['message_body']), result))  # wire() raises over 65,536
        query = next_query(result)
        transport.responses = [response([use('r%d' % round_, 'search_project_context', {'query':query})], 'tool_use') if query else response()]
        status, value = test.f.approve(follow);test.assertEqual(status, 200, value)
        process()
    return rounds


class InTurnPagingBudgetTest(unittest.TestCase):
    """SRV-r3 serious: following next_query inside one turn must never pass the 64KiB cap or lock the turn."""
    def check(self, rounds, label):
        sizes = [size for _, size, _ in rounds if size is not None]
        codes = [result.get('code') for _, _, result in rounds if result is not None]
        self.assertTrue(all(size < CAP for size in sizes), sizes)
        self.assertEqual(rounds[-1][0], 'limit_reached')  # MAX_ROUNDS, the existing per-turn round limit
        self.assertEqual(len(sizes), chat_general.MAX_ROUNDS-1)
        self.assertIn('CONTEXT_BUDGET_EXHAUSTED', codes)
        # Every notice keeps the query for a new turn and is itself under the margin limit.
        for _, size, result in rounds:
            if result is not None and result.get('code') == 'CONTEXT_BUDGET_EXHAUSTED':
                self.assertEqual((result['result_included'], result['retry']), (False, 'new_turn'))
                self.assertTrue(result['next_query'])
                self.assertGreater(result['body_bytes_with_result'], chat_general.CONTINUATION_LIMIT)
                self.assertLessEqual(size, chat_general.CONTINUATION_LIMIT+chat_general.CONTINUATION_MARGIN)
        record('in-turn-'+label, dict(body_bytes=sizes, codes=codes, final=rounds[-1][0], cap=CAP, limit=chat_general.CONTINUATION_LIMIT))
        return [result for _, _, result in rounds if result is not None and result.get('code') == 'CONTEXT_BUDGET_EXHAUSTED']

    def scene_fixture(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store;seed_scenes(self.store)
        return lambda:self.f.state()['projects']['A'], lambda:self.assertTrue(self.store.general_chat_runtime.process_next())

    def test_estimate_pages_followed_in_one_turn(self):
        m = EstimateBodyCapTest('test_estimate_items_are_paged_with_counts_totals_and_a_fetch_path');m.setUp();self.addCleanup(m.doCleanups)
        self.f, self.store = m.f, m.store
        process = lambda:self.assertTrue(self.store.general_chat_runtime.process_next())
        notices = self.check(follow_in_one_turn(self, ('estimate_media_plan', {'plan_id':m.plan}), m.m.project, process), 'estimate')
        # The withheld page is reachable in a new turn and fits there.
        status, value = self.f.action('general_chat_preview', song='A', prompt='다음 요청', maximum_micro=10000)
        self.assertEqual(status, 200, value)
        self.f.approve(value['general_chat_preview'], decision='reject')
        turn, follow = m.turn('search_project_context', {'query':notices[0]['next_query']})
        self.assertEqual(turn['status'], 'awaiting_continuation_approval')
        self.assertLessEqual(wire(follow['message_body']), chat_general.CONTINUATION_LIMIT)
        self.assertEqual(len(tool_result(follow['message_body'])['media_estimate']['actions']), fal_dispatch.ESTIMATE_ITEM_LIMIT)

    def test_scene_status_pages_followed_in_one_turn(self):
        project, process = self.scene_fixture()
        self.check(follow_in_one_turn(self, ('search_project_context', {'query':'scene-status'}), project, process), 'scene-status')

    def test_plain_query_then_scene_status_in_one_turn(self):
        project, process = self.scene_fixture()
        transport = self.store.general_chat_runtime.transport;queries = iter(['scene-status'])
        # Round 1 asks scene-status (critic probe_plain); later rounds follow next_query.
        original = next_query
        def pick(value):return next(queries, None) or original(value)
        with patch(__name__+'.next_query', pick):
            rounds = follow_in_one_turn(self, ('search_project_context', {'query':'project overview'}), project, process)
        self.assertEqual(rounds[0][2]['execution_targets']['list_pages']['shots']['total'], len(project()['shots']))
        self.assertIn('scene_status', rounds[1][2].get('execution_targets', {}))
        self.check(rounds, 'plain-then-scene-status')

    def test_live_mode_three_reads_then_rounds_never_lock_the_conversation(self):
        # critic probe_live: plain query, scene-status, then its next_query, in live mode (synthetic opener).
        a = activation.GeneralChatActivationHTTPTest('test_real_mode_exact_wire_bytes_and_estimate_without_verified_account_claim')
        a.setUp();self.addCleanup(a.doCleanups);seed_scenes(a.http.store)
        a.socket.replies = [activation.reply([use('q0', 'search_project_context', {'query':'project overview'})], 'tool_use')]
        status, result = a.approve(a.preview());self.assertEqual(status, 200, result)
        identifier = result['turn']['id'];a.process();sizes = [];statuses = []
        for round_ in range(1, chat_general.MAX_ROUNDS+1):
            turn, held, _ = a.reservation(identifier);statuses.append(turn['status'])
            self.assertNotEqual(turn['status'], 'outcome_unknown', turn.get('error'))
            if turn['status'] != 'awaiting_continuation_approval':break
            follow = a.project()['general_chat_previews'][-1];sizes.append(wire(follow['message_body']))
            query = 'scene-status' if round_ == 1 else next_query(tool_result(follow['message_body']))
            a.socket.replies = [activation.reply([use('q%d' % round_, 'search_project_context', {'query':query})], 'tool_use')]
            status, result = a.approve(follow);self.assertEqual(status, 200, result)
            a.process()
        self.assertEqual(statuses[-1], 'limit_reached')
        self.assertTrue(all(size < CAP for size in sizes), sizes)
        self.assertEqual(len(a.socket.requests), 2*chat_general.MAX_ROUNDS)
        status, value = a.action('general_chat_preview', song='A', prompt='다음 요청', maximum_micro=10000, total_maximum_micro=10000)
        self.assertEqual(status, 200, value)
        record('in-turn-live', dict(body_bytes=sizes, statuses=statuses, sent_requests=len(a.socket.requests), new_preview_http_status=status))


class StablePagesTest(unittest.TestCase):
    """Records saved between two page reads neither repeat nor skip an item (critic minor)."""
    def test_scene_saved_between_pages_does_not_shift_the_cursor(self):
        f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        f.setUp();self.addCleanup(f.doCleanups);store = f.http.store
        seed_scenes(store, scenes=10, pending=0)
        def page(query):
            with store.connect() as c:
                p = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']
                return production_context.read(c, store, p, 'A', query=query)['scene_status']
        first = page('scene-status');original = [x['scene_id'] for x in first['scenes_3d']]
        seed_scenes_extra(store, 'late')  # a newer scene saved between the two reads
        second = page(first['next_query'])
        self.assertTrue(second['cursor_found'])
        self.assertEqual(second['scenes_3d_total'], 11)
        self.assertEqual(len(second['scenes_3d']), 2)
        seen = [x['scene_id'] for x in second['scenes_3d']]+original
        self.assertEqual(len(seen), 10);self.assertEqual(len(set(seen)), 10)
        self.assertIsNone(second['next_query'])
        newest = page('scene-status')['scenes_3d']
        self.assertNotIn(newest[-1]['scene_id'], seen)  # the late scene joins the newest page only
        gone = page('scene-status before='+'0'*32)
        self.assertEqual((gone['scenes_3d'], gone['cursor_found'], gone['next_query']), ([], False, None))

    def test_action_prepared_between_estimate_pages_lands_on_a_later_page(self):
        m = EstimateBodyCapTest('test_estimate_items_are_paged_with_counts_totals_and_a_fetch_path');m.setUp();self.addCleanup(m.doCleanups)
        turn, follow = m.turn('estimate_media_plan', {'plan_id':m.plan})
        page = tool_result(follow['message_body']);listed = [x['action_id'] for x in page['actions']];query = page['next_query']
        m.f.approve(follow, decision='reject')
        arguments = m.m.arguments();arguments['model_reason'] = 'late'
        run = m.m.post('production_run', song='A')['run']['id']
        late = m.m.post('production_tool', song='A', run=run, call=dict(id=uuid.uuid4().hex, name='prepare_image_action', arguments=arguments, complete=True))['tool']['action_id']
        while query:
            turn, follow = m.turn('search_project_context', {'query':query})
            page = tool_result(follow['message_body'])['media_estimate']
            self.assertEqual(page['actions_total'], m.ACTIONS+1)
            listed += [x['action_id'] for x in page['actions']];query = page['next_query']
            m.f.approve(follow, decision='reject')
        self.assertEqual(len(listed), m.ACTIONS+1);self.assertEqual(len(set(listed)), m.ACTIONS+1)
        self.assertEqual(listed[-1], late)


class BoundedContextListsTest(unittest.TestCase):
    """General search_project_context lists (shots, actions, plans) carry counts and next_query (contract)."""
    def test_shot_and_plan_lists_are_paged_and_cover_every_item_once(self):
        f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        f.setUp();self.addCleanup(f.doCleanups);store = f.http.store
        seed_scenes(store, scenes=20, pending=0)
        for i in range(12):  # saved plan proposals, as the propose_media_plan tool saves them
            status, value = f.action('production_run', song='A');self.assertEqual(status, 200, value)
            status, value = f.action('production_tool', song='A', run=value['run']['id'], call=dict(id=uuid.uuid4().hex, name='propose_media_plan',
                                     arguments=dict(goal='plan %d' % i, scenes='s', style='', constraints='', kind='visualizer'), complete=True))
            self.assertEqual((status, value['tool']['status']), (200, 'proposed'), value)
        project = f.state()['projects']['A'];limit = production_context.CONTEXT_LIST_LIMIT
        def turn(query):
            store.general_chat_runtime.transport.responses = [response([use('lists', 'search_project_context', {'query':query})], 'tool_use')]
            status, result = f.approve(f.preview());self.assertEqual(status, 200, result)
            self.assertTrue(store.general_chat_runtime.process_next())
            follow = f.state()['projects']['A']['general_chat_previews'][-1]
            self.assertLessEqual(wire(follow['message_body']), chat_general.CONTINUATION_LIMIT)
            f.approve(follow, decision='reject')
            return tool_result(follow['message_body'])['execution_targets']
        first = turn('project overview')
        for kind, key, total in (('shots', 'shot_id', len(project['shots'])), ('plans', 'plan_id', len(project.get('guided_plans', [])))):
            with self.subTest(kind=kind):
                meta = first['list_pages'][kind]
                self.assertGreater(total, limit)
                self.assertEqual((len(first[kind]), meta['total'], meta['not_shown'], meta['truncated'], meta['next_query']),
                                 (limit, total, total-limit, True, 'context-%s offset=%d' % (kind, limit)))
                seen = [x[key] for x in first[kind]];query = meta['next_query']
                while query:
                    page = turn(query)
                    self.assertEqual(set(page), {kind, 'list_pages', 'note'})  # only that list, not the whole context again
                    seen += [x[key] for x in page[kind]];query = page['list_pages'][kind]['next_query']
                self.assertEqual(len(seen), total);self.assertEqual(len(set(seen)), total)
        self.assertEqual(first['list_pages']['actions'], dict(total=0, offset=0, limit=limit, not_shown=0, truncated=False, next_query=None))

    def test_action_list_is_paged(self):
        m = EstimateBodyCapTest('test_estimate_items_are_paged_with_counts_totals_and_a_fetch_path');m.setUp();self.addCleanup(m.doCleanups)
        turn, follow = m.turn('search_project_context', {'query':'project overview'})
        targets = tool_result(follow['message_body'])['execution_targets'];meta = targets['list_pages']['actions']
        limit = production_context.CONTEXT_LIST_LIMIT
        self.assertEqual((len(targets['actions']), meta['total'], meta['not_shown'], meta['next_query']), (limit, m.ACTIONS, m.ACTIONS-limit, 'context-actions offset=%d' % limit))
        m.f.approve(follow, decision='reject')
        seen = [x['action_id'] for x in targets['actions']];query = meta['next_query']
        while query:
            turn, follow = m.turn('search_project_context', {'query':query})
            page = tool_result(follow['message_body'])['execution_targets']
            seen += [x['action_id'] for x in page['actions']];query = page['list_pages']['actions']['next_query']
            m.f.approve(follow, decision='reject')
        self.assertEqual(seen, [x['id'] for x in m.m.actions()])  # rowid order, each once


def seed_scenes_extra(store, shot):
    def call(action, **data):
        with store.connect() as c:revision = c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        return store.mutate(dict(action=action, data=data, revision=revision, request_id=uuid.uuid4().hex))
    call('shot', song='A', shot=shot, description='synthetic 3D')
    with store.connect() as c:project = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects']['A']
    created = call('scene_create', song='A', shot_id=production_context.shot_id(project, shot), scene=sample())['scene']
    call('scene_review', song='A', scene_proposal_id=created['proposal_id'], decision='approved')

if __name__ == '__main__':
    unittest.main()
