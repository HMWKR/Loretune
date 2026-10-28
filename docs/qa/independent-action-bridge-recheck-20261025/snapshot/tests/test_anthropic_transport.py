import io
import json
import unittest
import urllib.error
from unittest.mock import Mock, patch
import anthropic_ontology as a
from test_ontology import graph

HEADERS = {'x-api-key': 'synthetic-secret', 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}


class Response(io.BytesIO):
    def __init__(self, raw=b'{}', *, status=200, url=a.ENDPOINT, headers=None):
        super().__init__(raw)
        self.status = status
        self.url = url
        self.headers = {'Content-Type': 'application/json'} if headers is None else headers
    def geturl(self): return self.url


class TransportTests(unittest.TestCase):
    def call(self, response):
        opener = Mock(); opener.open.return_value = response
        return a.BoundedMessagesTransport(opener=opener)(a.ENDPOINT, HEADERS, {}), opener
    def test_fake_full_adapter_and_single_post(self):
        raw = json.dumps({'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': json.dumps(graph())}]}).encode()
        opener = Mock(); opener.open.return_value = Response(raw)
        result = a.AnthropicOntology(a.BoundedMessagesTransport(opener=opener), lambda name: 'synthetic-secret', enabled=True).propose({'brief-1': 'synthetic brief'})
        self.assertTrue(result['approval_required'])
        self.assertNotIn('synthetic-secret', repr(result))
        self.assertEqual(opener.open.call_count, 1)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(request.full_url, a.ENDPOINT)
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 30)
    def test_endpoint_variants_never_open(self):
        opener = Mock(); transport = a.BoundedMessagesTransport(opener=opener)
        for url in ('http://api.anthropic.com/v1/messages', a.ENDPOINT+'?x=1', a.ENDPOINT+'#fragment', 'https://evil.example/v1/messages'):
            with self.assertRaises(a.ProposalError): transport(url, HEADERS, {})
        opener.open.assert_not_called()
    def test_redirect_handler_refuses_all_targets(self):
        for target in (a.ENDPOINT, 'https://evil.example/'):
            with self.assertRaises(a.ProposalError): a._NoRedirect().redirect_request(None, None, 302, '', {}, target)
    def test_unexpected_response_origin_and_status(self):
        for response in (Response(url='https://evil.example/'), Response(status=302), Response(status=403)):
            with self.assertRaises(a.ProposalError): self.call(response)
    def test_response_size_and_truncation(self):
        for response in (Response(b'x'*100001), Response(headers={'Content-Type':'application/json','Content-Length':'100001'}), Response(b'{}', headers={'Content-Type':'application/json','Content-Length':'20'})):
            with self.assertRaises(a.ProposalError): self.call(response)
    def test_mime_encoding_and_invalid_json(self):
        for response in (Response(headers={'Content-Type':'text/html'}), Response(headers={'Content-Type':'application/json','Content-Encoding':'gzip'}), Response(b'not-json'), Response(b'[]')):
            with self.assertRaises(a.ProposalError): self.call(response)
    def test_http_failure_and_timeout_no_retry_or_secret(self):
        for failure in (urllib.error.HTTPError(a.ENDPOINT, 401, 'synthetic-secret', {}, io.BytesIO(b'synthetic-secret')), TimeoutError('synthetic-secret')):
            opener = Mock(); opener.open.side_effect = failure
            with self.assertRaises(a.ProposalError) as caught: a.BoundedMessagesTransport(opener=opener)(a.ENDPOINT, HEADERS, {})
            self.assertNotIn('synthetic-secret', str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)
    def test_read_deadline(self):
        with patch.object(a.time, 'monotonic', side_effect=[0, 31]):
            with self.assertRaises(a.ProposalError): self.call(Response())
    def test_credential_supplier_exception_redacted(self):
        transport = Mock()
        adapter = a.AnthropicOntology(transport, Mock(side_effect=RuntimeError('synthetic-secret')), enabled=True)
        with self.assertRaises(a.ProposalError) as caught: adapter.propose({'brief-1':'synthetic brief'})
        self.assertNotIn('synthetic-secret', str(caught.exception))
        transport.assert_not_called()
    def test_invalid_headers_and_request_bound_before_open(self):
        opener = Mock(); transport = a.BoundedMessagesTransport(opener=opener)
        for headers in (dict(HEADERS, authorization='synthetic-secret'), dict(HEADERS, **{'x-api-key':'bad\r\nvalue'})):
            with self.assertRaises(a.ProposalError): transport(a.ENDPOINT, headers, {})
        with self.assertRaises(a.ProposalError): transport(a.ENDPOINT, HEADERS, {'large':'x'*12001})
        opener.open.assert_not_called()
    def test_default_builder_disables_proxy_and_redirect_without_network(self):
        opener = Mock(); opener.open.return_value = Response()
        with patch.object(a.urllib.request, 'build_opener', return_value=opener) as builder:
            a.BoundedMessagesTransport()(a.ENDPOINT, HEADERS, {})
        handlers = builder.call_args.args
        self.assertEqual(handlers[0].proxies, {})
        self.assertIsInstance(handlers[1], a._NoRedirect)

if __name__ == '__main__': unittest.main()
