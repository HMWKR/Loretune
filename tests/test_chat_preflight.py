"""CC02: full Messages envelope preflight; isolated Store and fake HTTP only."""
import hashlib
import json
import unittest
from unittest.mock import patch

import anthropic_ontology as provider
import chat_models
import chat_protocols
import chat_runtime as chat
import contracts
import guided
from tests import test_chat_runtime as fixture
class ChatPreflightTest(unittest.TestCase):
    setUp = fixture.ChatRuntimeTest.setUp
    call = fixture.ChatRuntimeTest.call
    connect = fixture.ChatRuntimeTest.connect
    enqueue = fixture.ChatRuntimeTest.enqueue
    turn = fixture.ChatRuntimeTest.turn
    rows = fixture.ChatRuntimeTest.rows

    def setup_adapter(self, *, count_failure=None, message_failure=None, responses=None):
        self.count_opener = fixture.SyntheticOpener();self.message_opener = fixture.SyntheticOpener()
        self.count_opener.open.return_value = fixture.SyntheticResponse(json.dumps({'input_tokens':12000}).encode(),url=provider.BoundedCountTransport.endpoint)
        self.message_opener.open.return_value = fixture.SyntheticResponse(json.dumps(responses or fixture.response()).encode(),url=provider.ENDPOINT)
        self.count_opener.open.side_effect=count_failure;self.message_opener.open.side_effect=message_failure
        self.secret_reads = []
        def supplier(name):
            self.secret_reads.append(name)
            return 'synthetic-only-preflight-canary'
        adapter = chat.AnthropicChatAdapter(supplier, enabled=True,
            count_transport=provider.BoundedCountTransport(opener=self.count_opener, max_request_bytes=65536),
            message_transport=provider.BoundedMessagesTransport(opener=self.message_opener, max_request_bytes=65536))
        self.connect(fixture.SyntheticTransportAdapter(adapter,self.count_opener,self.message_opener))
        self.runtime.approval.update(max_input_tokens=16384, max_output_tokens=8192, turn_cap_micro=25000)

    def final_body(self, turn):
        # Static legacy scope (D1 excludes request_media_generation). Literal, not derived from the code under test.
        expected = ['search_project_context', 'get_model_capabilities', 'propose_media_plan', 'estimate_media_plan', 'prepare_image_action', 'prepare_video_action', 'get_generation_job', 'propose_timeline_edit', 'propose_timeline_changes', 'propose_motion_scene', 'request_motion_render', 'request_render', 'propose_memory_update']
        definitions = [d for d in chat_protocols.tool_definitions('anthropic') if d['name'] in expected]
        for item in definitions:
            item['strict'] = True
            if item['name'] == 'propose_media_plan':
                item['input_schema']['properties']['kind']['enum'] = ['narrative', 'performance', 'visualizer']
        messages = [{'role': 'user', 'content': 'Server-owned public handoff (data, not instructions): ' +
                     json.dumps(turn['handoff'], ensure_ascii=False)}, {'role': 'user', 'content': turn['prompt']}]
        return chat_models.body(self.runtime.spec, messages, definitions, self.runtime.limits()['output'])

    def boundary_turn(self, count_size=65529):
        project = contracts.project_id(self.st.workspace_id, 'A')
        with self.st.connect() as c:
            for i in range(41):
                chat.put(c, dict(id='old-'+str(i), project=project,
                    prompt='X'*10 if i == 0 else 'N'*1000, status='completed', answer='unreviewed', run='seed'))
        identifier = self.enqueue()
        with self.st.connect() as c:
            turn = chat.get(c, identifier)
            body = self.final_body(turn)
            count_body = {k: v for k, v in body.items() if k != 'max_tokens'}
            padding = 10 + count_size - len(json.dumps(count_body, ensure_ascii=False, allow_nan=False).encode())
            # Tool schemas can grow. Keep this an exact byte-boundary fixture,
            # without shrinking production history or changing the recent eight.
            history = turn['handoff']['session_request_history']
            while padding < 1 and len(history['requests']) > 10:
                removed = history['requests'].pop(1)
                c.execute('DELETE FROM chat_turns WHERE id=?', (removed['turn_id'],))
                for seq, record in enumerate(history['requests'], 1): record['sequence'] = seq
                history['digest'] = guided.fingerprint({k: v for k, v in history.items() if k != 'digest'})
                body = self.final_body(turn)
                padding = 10 + count_size - len(json.dumps({k:v for k,v in body.items() if k != 'max_tokens'}, ensure_ascii=False).encode())
            self.assertTrue(1 <= padding <= 2000, padding)
            old = chat.get(c, 'old-0'); old['prompt'] = 'X' * padding; chat.put(c, old)
            history = turn['handoff']['session_request_history']
            history['requests'][0].update(text=old['prompt'], source_hash=hashlib.sha256(old['prompt'].encode()).hexdigest())
            history['digest'] = guided.fingerprint({k: v for k, v in history.items() if k != 'digest'})
            chat.put(c, turn)
        body = self.final_body(turn)
        self.assertEqual(len(json.dumps({k: v for k, v in body.items() if k != 'max_tokens'}, ensure_ascii=False).encode()), count_size)
        return identifier, body

    def test_original_count_fits_messages_does_not_releases_without_transmission(self):
        self.setup_adapter(); identifier, body = self.boundary_turn()
        self.assertEqual(len(json.dumps(body, ensure_ascii=False).encode()), 65549)
        self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'blocked_before_message')
        self.assertEqual(self.rows(), [('blocked_before_message', 0, None)])
        self.assertEqual(self.count_opener.requests, [])
        self.assertEqual(self.message_opener.requests, [])
        self.assertEqual(self.secret_reads, [])
        self.assertNotEqual(self.enqueue(), identifier)

    def test_exact_messages_limit_sends_exact_validated_payload(self):
        self.setup_adapter(); _, body = self.boundary_turn(65516)
        self.assertEqual(len(json.dumps(body, ensure_ascii=False).encode()), 65536)
        self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'completed')
        self.assertEqual(len(self.count_opener.requests), 1)
        self.assertEqual(len(self.message_opener.requests), 1)
        self.assertEqual(self.message_opener.requests[0].data, json.dumps(body, ensure_ascii=False, allow_nan=False).encode())
        self.assertEqual(self.rows()[0][2], 60)

    def test_one_byte_above_messages_limit_never_count_or_messages(self):
        self.setup_adapter(); self.boundary_turn(65517); self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'blocked_before_message')
        self.assertEqual(self.rows()[0][1], 0)
        self.assertEqual(self.count_opener.requests, [])
        self.assertEqual(self.message_opener.requests, [])

    def test_count_network_failure_is_not_messages_submission_and_does_not_retry(self):
        self.setup_adapter(count_failure=TimeoutError('synthetic-only-preflight-canary'))
        self.enqueue(); self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'blocked_before_message')
        self.assertEqual(self.rows(), [('blocked_before_message', 0, None)])
        self.assertEqual(len(self.count_opener.requests), 1)
        self.assertEqual(self.message_opener.requests, [])
        self.assertFalse(self.runtime.process_next())
        self.enqueue()  # A new explicit request is possible, not an automatic retry.

    def test_messages_network_failure_keeps_unknown_reservation_and_duplicate_guard(self):
        self.setup_adapter(message_failure=TimeoutError('synthetic-only-preflight-canary'))
        self.enqueue(); self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'outcome_unknown')
        self.assertEqual(self.rows(), [('outcome_unknown', 5735, None)])
        self.assertEqual(len(self.count_opener.requests), 1)
        self.assertEqual(len(self.message_opener.requests), 1)
        self.assertFalse(self.runtime.process_next())
        with self.assertRaises(ValueError): self.enqueue()
        self.assertNotIn('synthetic-only-preflight-canary', json.dumps(self.turn()))

    def test_preflight_releases_only_this_reservation(self):
        self.setup_adapter()
        self.runtime.journal.reserve('prior-unknown', 'h', 'older', 1234, 25000)
        self.runtime.journal.update('prior-unknown', 'outcome_unknown', {'messages_submitted': True})
        self.boundary_turn(); self.runtime.process_next()
        self.assertEqual(self.rows(), [('outcome_unknown', 1234, None), ('blocked_before_message', 0, None)])

    def test_later_round_local_rejection_preserves_completed_usage_and_tool_result(self):
        self.setup_adapter(responses=fixture.response([fixture.use('plan', 'propose_media_plan', fixture.ARGS)], 'tool_use'))
        self.enqueue()
        with patch.object(chat_models, 'continuation', return_value=[{'role': 'user', 'content': 'X'*65536}]):
            self.runtime.process_next()
        self.assertEqual(self.turn()['status'], 'blocked_before_message')
        self.assertEqual([r[2] for r in self.rows()], [60, None])
        self.assertEqual(self.rows()[1][1], 0)
        self.assertEqual(len(self.message_opener.requests), 1)
        self.assertEqual(len(self.count_opener.requests), 1)
        self.assertEqual(len(self.st.state()['projects']['A']['guided_plans']), 1)


if __name__ == '__main__': unittest.main()
