import copy
import json
import unittest
import uuid
from unittest.mock import Mock
import anthropic_ontology as a
from tests.test_ontology import graph


class AnthropicTests(unittest.TestCase):
    def response(self, value=None):
        return {'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': json.dumps(value or graph())}]}
    def test_disabled_never_reads_credential_or_sends(self):
        supplier, transport = Mock(), Mock()
        adapter = a.AnthropicOntology(transport, supplier)
        with self.assertRaises(a.ProposalError): adapter.propose({'brief-1': 'synthetic brief'})
        supplier.assert_not_called(); transport.assert_not_called()
    def test_fake_request_contract_and_proposal_only(self):
        transport, supplier = Mock(return_value=self.response()), Mock(return_value='synthetic-test-key')
        result = a.AnthropicOntology(transport, supplier, enabled=True).propose({'brief-1': 'synthetic brief'})
        supplier.assert_called_once_with('Anthropic_KEY')
        endpoint, headers, body = transport.call_args.args
        self.assertEqual(endpoint, a.ENDPOINT)
        self.assertEqual(body['model'], 'claude-haiku-5-5')
        self.assertEqual(body['output_config']['format']['type'], 'json_schema')
        self.assertTrue(result['approval_required'])
        self.assertNotIn('synthetic-test-key', repr(result))
        self.assertEqual(transport.call_count, 1)
    def test_incomplete_refusal_and_false_source(self):
        for stop in ('max_tokens', 'refusal', 'tool_use'):
            response = self.response(); response['stop_reason'] = stop
            with self.assertRaises(a.ProposalError): a.parse_response(response, {'brief-1': 'synthetic brief'})
        with self.assertRaises(a.ProposalError): a.parse_response(self.response(), {'brief-1': 'different text'})
    def test_transport_exception_redaction_no_retry(self):
        transport = Mock(side_effect=RuntimeError('synthetic-secret-token'))
        adapter = a.AnthropicOntology(transport, lambda name: 'synthetic-secret-token', enabled=True)
        with self.assertRaises(a.ProposalError) as caught: adapter.propose({'brief-1': 'synthetic brief'})
        self.assertNotIn('synthetic-secret-token', str(caught.exception))
        self.assertEqual(transport.call_count, 1)
    def test_conflicting_assertions_rejected(self):
        value = graph(); other = copy.deepcopy(value['entities'][0]); other['id'] = str(uuid.uuid4()); other['description'] = 'conflicting coat'
        value['entities'].append(other)
        with self.assertRaises(a.ProposalError): a.parse_response(self.response(value), {'brief-1': 'synthetic brief'})
        other['uncertainty']['status'] = 'unknown'; value['entities'][0]['uncertainty']['status'] = 'unknown'
        self.assertEqual(len(a.parse_response(self.response(value), {'brief-1': 'synthetic brief'})['entities']), 3)
    def test_duplicate_json_keys_rejected(self):
        response = self.response(); response['content'][0]['text'] = '{"entities":[],"entities":[],"relations":[]}'
        with self.assertRaises(a.ProposalError): a.parse_response(response, {})
    def test_thinking_block_not_persisted(self):
        response = self.response(); response['content'].insert(0, {'type': 'thinking', 'thinking': 'not stored', 'signature': 'opaque'})
        value = a.parse_response(response, {'brief-1': 'synthetic brief'})
        self.assertNotIn('opaque', repr(value))
    def test_input_boundary_before_credential_access(self):
        supplier = Mock()
        adapter = a.AnthropicOntology(Mock(), supplier, enabled=True)
        with self.assertRaises(a.ProposalError): adapter.propose({'brief': 'x' * 15000})
        supplier.assert_not_called()

if __name__ == '__main__': unittest.main()
