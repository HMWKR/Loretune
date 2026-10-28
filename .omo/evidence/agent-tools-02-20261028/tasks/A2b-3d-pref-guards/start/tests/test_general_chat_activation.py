"""Real platform HTTP + production branch; provider sockets are synthetic only."""
import base64
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
import hashlib
import http.client
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
import wave
from unittest.mock import Mock, patch

import anthropic_ontology as anthropic
import chat_general
import chat_models
import chat_runtime
import contracts
import editing
import general_chat_config as config
import guided
import ledger
from app import Store, server
from tests.test_chat_runtime import response, use


FAKE_KEY = 'synthetic-key-not-real'


def settings(workspace, enabled=True):
    spec = chat_models.contract('anthropic-haiku-5-5')
    return dict(version=1, enabled=enabled, workspace_id=workspace,
                connection_id='synthetic-account-declaration', connection_revision=1,
                model=spec['model'], price_revision=spec['price_revision'])


def reply(blocks=None, stop='end_turn'):
    value = response(blocks, stop)
    value['model'] = 'claude-haiku-5-5'
    value['usage'].update(cache_creation_input_tokens=0, cache_read_input_tokens=0,
                          service_tier='standard', speed='standard', inference_geo='global',
                          server_tool_use=dict(web_fetch_requests=0, web_search_requests=0))
    return value


class SyntheticResponse(io.BytesIO):
    def __init__(self, body, url, number):
        raw = json.dumps(body).encode()
        super().__init__(raw)
        self.status = 200
        self.url = url
        self.headers = {'Content-Type': 'application/json', 'Content-Length': str(len(raw)),
                        'request-id': 'req_synthetic_' + str(number)}

    def geturl(self):
        return self.url


class ProviderSocket:
    """Only replaces stdlib's opener in the tests, never a production instance."""
    def __init__(self):
        self.requests = []
        self.replies = [reply()]

    def open(self, request, timeout):
        if request.full_url not in {anthropic.ENDPOINT, anthropic.BoundedCountTransport.endpoint}:
            raise AssertionError('unexpected provider URL')
        if request.get_header('X-api-key') != FAKE_KEY:
            raise AssertionError('synthetic key required')
        self.requests.append((request.full_url, request.data, timeout))
        body = {'input_tokens': 100} if request.full_url.endswith('count_tokens') else self.replies.pop(0)
        if isinstance(body, Exception):
            raise body
        return SyntheticResponse(body, request.full_url, len(self.requests))


class GeneralChatConfigTest(unittest.TestCase):
    def test_closed_schema_and_disabled_factory_never_acquire_credentials(self):
        value = settings(str(uuid.uuid4()), False)
        supplier = Mock(side_effect=AssertionError('must stay lazy'))
        self.assertIsNone(config.build(config.parse(value), supplier))
        supplier.assert_not_called()
        for change in ({'enabled': 1}, {'version': True}, {'connection_revision': 0},
                       {'connection_revision': True}, {'workspace_id': 'other'},
                       {'model': 'other'}, {'price_revision': 'old'}, {'connection_id': 'bad value'},
                       {'endpoint': 'https://private.invalid'}, {'api_key': FAKE_KEY}, {'test_only': True}):
            with self.subTest(change=change):
                with self.assertRaises(config.GeneralChatConfigError) as caught:
                    config.parse(dict(value, **change))
                self.assertNotIn(FAKE_KEY, str(caught.exception))
        supplier.assert_not_called()

    def test_json_loader_rejects_duplicates_nonfinite_symlink_and_writable_config(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'connection.json'
            path.write_text(json.dumps(settings(str(uuid.uuid4()), False)))
            self.assertFalse(config.load(path).enabled)
            for raw in ('{"version":1,"version":1}', '{"enabled":NaN}', '[]', 'x' * (config.MAX_CONFIG_BYTES + 1)):
                path.write_text(raw)
                with self.assertRaises(config.GeneralChatConfigError):
                    config.load(path)
            path.write_text(json.dumps(settings(str(uuid.uuid4()), False)))
            link = Path(folder) / 'link.json'
            link.symlink_to(path)
            with self.assertRaises(config.GeneralChatConfigError):
                config.load(link)
            path.chmod(0o666)
            with self.assertRaises(config.GeneralChatConfigError):
                config.load(path)

    def test_activation_retains_actual_type_endpoint_and_supplier_identity_guards(self):
        supplier = Mock(return_value=FAKE_KEY)
        transport = config.build(settings(str(uuid.uuid4())), supplier)
        self.assertIsNone(transport.adapter.count_transport._opener)
        self.assertIsNone(transport.adapter.message_transport._opener)
        with self.assertRaises(ValueError):
            chat_general.LiveTransport(transport.adapter, 'fixture', 1, test_only=True)
        transport.adapter.message_transport.endpoint = 'https://private.invalid'
        with self.assertRaises(ValueError):
            transport.complete({})
        transport.adapter.message_transport.endpoint = anthropic.ENDPOINT
        transport.adapter.message_transport._opener = Mock()
        with self.assertRaises(ValueError):
            transport.count({})
        transport.adapter.message_transport._opener = None
        transport.adapter.supplier = Mock(return_value=FAKE_KEY)
        with self.assertRaises(ValueError):
            transport.count({})
        supplier.assert_not_called()

    def test_unconfigured_or_disabled_transport_and_dual_legacy_fail_before_store(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'must-not-be-created'
            supplier = Mock(return_value=FAKE_KEY)
            value = settings(str(uuid.uuid4()))
            with self.assertRaises(ValueError):
                server(path, 0, general_chat_configuration=value, general_chat_credential_supplier=supplier,
                       chat_configuration={})
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):
                server(path, 0, general_chat_configuration=value, general_chat_fixture=[])
            unconfigured = chat_general.LiveTransport(chat_runtime.AnthropicChatAdapter(supplier, enabled=True), 'manual', 1)
            with self.assertRaises(ValueError):
                server(path, 0, general_chat_live=unconfigured)
            self.assertFalse(path.exists())
            supplier.assert_not_called()

    def test_cli_invalid_configuration_exits_before_data_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            path.write_text(json.dumps({'api_key': FAKE_KEY}))
            data = Path(folder) / 'untouched'
            result = subprocess.run([sys.executable, 'app.py', '--data', str(data), '--port', '0',
                                     '--general-chat-config', str(path)], capture_output=True, text=True,
                                    timeout=10, env={'PATH': '/usr/bin:/bin'})
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(FAKE_KEY, result.stderr)
            self.assertFalse(data.exists())

    def test_default_disabled_and_wrong_workspace_never_touch_supplier_or_transport(self):
        supplier = Mock(side_effect=AssertionError('must stay lazy'))
        with tempfile.TemporaryDirectory() as folder:
            initial = Store(folder)
            for value in (None, settings(initial.workspace_id, False)):
                http = server(folder, 0, **({} if value is None else {
                    'general_chat_configuration': value, 'general_chat_credential_supplier': supplier}))
                try:
                    self.assertIsNone(http.store.general_chat_runtime)
                finally:
                    http.server_close()
            with self.assertRaises(ValueError):
                server(folder, 0, general_chat_configuration=settings(str(uuid.uuid4())),
                       general_chat_credential_supplier=supplier)
        supplier.assert_not_called()


class GeneralChatActivationHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        initial = Store(self.tmp.name)
        self.configuration = settings(initial.workspace_id)
        self.keys = []
        self.key_value = FAKE_KEY
        self.key_error = None
        def supplier(name):
            self.keys.append(name)
            if self.key_error is not None:
                raise self.key_error
            return self.key_value
        self.socket = ProviderSocket()
        self.opener_patch = patch.object(anthropic.urllib.request, 'build_opener', return_value=self.socket)
        self.builder = self.opener_patch.start()
        self.addCleanup(self.opener_patch.stop)
        self.http = server(self.tmp.name, 0, general_chat_configuration=self.configuration,
                           general_chat_credential_supplier=supplier)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.post('project', name='A', era='default', story=0)
        self.post('model_settings', song='A', selections={'chat': 'anthropic-haiku-5-5'}, model_revision=0)
        self.pid = contracts.project_id(initial.workspace_id, 'A')
        self.budget('1')

    def close(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=10)
        try:
            connection.request(method, path, body=None if body is None else json.dumps(body).encode(),
                               headers=headers or {})
            result = connection.getresponse()
            raw = result.read()
            return result.status, json.loads(raw) if 'application/json' in result.getheader('Content-Type', '') else raw
        finally:
            connection.close()

    def state(self):
        status, result = self.request('GET', '/api/state')
        self.assertEqual(status, 200, result)
        return result

    def project(self):
        return self.state()['projects']['A']

    def action(self, action, *, conversation=None, **data):
        state = self.state()
        body = dict(action=action, data=data, revision=state['revision'], request_id=uuid.uuid4().hex)
        if conversation is not None:
            status, scoped = self.request('GET', '/api/state?song=A&conversation=' + conversation)
            self.assertEqual(status, 200, scoped)
            session = scoped['projects']['A']['active_conversation']
            body.update(conversation_id=conversation, conversation_revision=session['revision'], shared_version=session['shared_version'])
        return self.request('POST', '/api/action', body, {'Content-Type': 'application/json', 'X-Loretune-Token': state['token']})

    def post(self, action, **data):
        status, result = self.action(action, **data)
        self.assertEqual(status, 200, result)
        return result

    def budget(self, amount):
        state = self.state()
        current = next((x for x in state['budgets'] if x['data']['scope'] == 'project:' + self.pid), None)
        body = dict(period='project', projectId=self.pid, limit={'amount': amount, 'currency': 'USD'},
                    maxConcurrentJobs=4, allowAutomaticRetries=False)
        status, result = self.request('PATCH', '/v1/workspaces/' + state['workspace_id'] + '/billing/budgets', body,
            {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state['token'],
             'If-Match': '"' + str(current['revision'] if current else 0) + '"'})
        self.assertEqual(status, 200, result)

    def preview(self, *, conversation=None):
        return self.post('general_chat_preview', song='A', prompt='현재 음원으로 내부 편집을 도와줘',
                         maximum_micro=10000, total_maximum_micro=10000, conversation=conversation)['general_chat_preview']

    def approve(self, preview, *, conversation=None):
        return self.action('general_chat_decide', song='A', preview_id=preview['id'],
                           manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True,
                           conversation=conversation)

    def process(self):
        self.assertTrue(self.http.store.general_chat_runtime.process_next())

    def reservation(self, turn_id):
        with self.http.store.connect() as c:
            turn = chat_general.get_row(c, 'general_chat_turns', turn_id)
            row = c.execute('SELECT state,actual FROM reservations WHERE id=?', (turn['reservation'],)).fetchone()
            attempts = c.execute('SELECT operation,state FROM provider_attempts WHERE reservation=? ORDER BY operation', (turn['reservation'],)).fetchall()
        return turn, row, attempts

    def test_real_mode_exact_wire_bytes_and_estimate_without_verified_account_claim(self):
        capability = self.project()['general_chat_connection']
        self.assertEqual(capability['mode'], 'anthropic-live')
        self.assertTrue(capability['external_transmission'])
        self.assertFalse(capability['account_verified'])
        self.assertFalse(capability['billing_verified'])
        preview = self.preview()
        self.assertEqual((self.keys, self.socket.requests), ([], []))
        self.assertEqual(preview['destination'], 'https://api.anthropic.com')
        self.assertEqual(preview['binding']['transport']['activation_sha256'], config.parse(self.configuration).digest())
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        self.process()
        turn, held, attempts = self.reservation(result['turn']['id'])
        self.assertEqual(turn['status'], 'completed')
        self.assertEqual(held, ('estimated', 60))
        self.assertEqual(attempts, [('chat-count', 'observed'), ('chat-message', 'observed')])
        self.assertEqual(self.keys, ['Anthropic_KEY', 'Anthropic_KEY'])
        self.assertEqual([r[0] for r in self.socket.requests], [anthropic.BoundedCountTransport.endpoint, anthropic.ENDPOINT])
        self.assertEqual(hashlib.sha256(self.socket.requests[0][1]).hexdigest(), preview['count_wire_sha256'])
        self.assertEqual(hashlib.sha256(self.socket.requests[1][1]).hexdigest(), preview['message_wire_sha256'])
        self.assertNotIn(FAKE_KEY, json.dumps(self.state()))
        self.receipt = {'mode': capability['mode'], 'provider_network': 'synthetic stdlib opener only',
                        'wire_hashes': [hashlib.sha256(x[1]).hexdigest() for x in self.socket.requests],
                        'reservation': held, 'attempts': attempts, 'billing_confirmed': turn['billing_confirmed']}

    def test_connection_revision_change_rejects_approved_manifest_without_key_access(self):
        preview = self.preview()
        transport = self.http.store.general_chat_runtime.transport
        transport.activation = replace(transport.activation, connection_revision=2)
        transport.connection_revision = 2
        status, _ = self.approve(preview)
        self.assertEqual(status, 400)
        self.assertEqual((self.keys, self.socket.requests), ([], []))

    def test_browser_cannot_supply_activation_and_two_round_caps_are_mandatory(self):
        for data in (dict(enabled=True), dict(total_maximum_micro=None)):
            body = dict(song='A', prompt='도와줘', maximum_micro=10000, total_maximum_micro=10000)
            body.update(data)
            status, _ = self.action('general_chat_preview', **body)
            self.assertEqual(status, 400)
        self.assertEqual((self.keys, self.socket.requests), ([], []))

    def test_cancel_after_count_never_calls_message_transport(self):
        preview = self.preview()
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        identifier = result['turn']['id']
        original = self.socket.open
        def cancel_after_count(request, timeout):
            value = original(request, timeout)
            if request.full_url.endswith('count_tokens'):
                self.post('general_chat_cancel', song='A', turn=identifier)
            return value
        with patch.object(self.socket, 'open', side_effect=cancel_after_count):
            self.process()
        turn, held, attempts = self.reservation(identifier)
        self.assertEqual(turn['status'], 'cancelled')
        self.assertEqual(held, ('cancelled', None))
        self.assertEqual(attempts, [('chat-count', 'observed')])
        self.assertEqual(len(self.socket.requests), 1)

    def test_production_tool_follow_rejects_changed_music_before_new_key_or_reservation(self):
        self.upload_audio()
        self.socket.replies = [reply([use('music', 'search_project_context', {'query': '음원'})], 'tool_use')]
        first = self.preview()
        status, result = self.approve(first)
        self.assertEqual(status, 200, result)
        self.process()
        follow = self.project()['general_chat_previews'][-1]
        self.assertIn('music_context', follow)
        self.upload_audio()
        keys = len(self.keys)
        status, _ = self.approve(follow)
        self.assertEqual(status, 400)
        self.assertEqual(len(self.keys), keys)
        self.assertEqual(len(self.socket.requests), 2)
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 1)

    def test_shared_production_budget_cannot_reserve_twice_from_different_conversations(self):
        self.budget('0.004')  # one worst round (3687 micro after D20) fits, two do not
        first = self.preview()
        cid = self.post('conversation_create', song='A', title='동일 예산 대화')['conversation']['id']
        second = self.preview(conversation=cid)
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(self.approve, first), pool.submit(self.approve, second, conversation=cid)]
            results = [f.result() for f in futures]
        self.assertEqual(sum(code == 200 for code, _ in results), 1)
        for index, (code, _) in enumerate(results):
            if code == 409:
                code, _ = self.approve(first if index == 0 else second, conversation=None if index == 0 else cid)
            if code != 200:
                self.assertEqual(code, 400)
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT scope FROM budgets').fetchone()[0], 'project:' + self.pid)
        self.assertEqual((self.keys, self.socket.requests), ([], []))

    def prepare_media_action(self):
        from fal_dispatch import FalDispatch
        from fal_model_adapter import FalModelAdapter
        from fal_models import Contract
        self.upload_audio()
        self.post('music_structure', song='A', audio=1, start=0, end=3, sections=[])
        plan = self.post('guided_plan', song='A', goal='합성 이미지 예산 확인', scenes='푸른 도형', kind='visualizer')['plan']
        self.post('apply_guided_plan', song='A', plan=plan)
        self.post('model_settings', song='A', selections={'image': 'fal-flux-schnell'},
                  model_revision=self.project()['model_settings']['revision'])
        contract = Contract('fal-flux-schnell')
        payload = contract.payload('blue geometry', {'ratio': '16:9'}, [])
        quote = dict(provider='fal.ai', model=contract.MODEL, money={'amount': '0.01', 'currency': 'USD'},
                     input_sha256=guided.fingerprint(payload), kind='fixture', price_revision='synthetic-not-real',
                     source=contract.spec['source'], expires=time.time()+300)
        adapter = FalModelAdapter('fal-flux-schnell', quote=quote,
                                  transport=Mock(side_effect=AssertionError('no media provider call')))
        pipeline = FalDispatch(self.http.store, [adapter])
        self.http.store.media_dispatch = pipeline
        prepared = self.post('media_prepare', song='A', shot='장면 1', shot_revision=0,
                             prompt='blue geometry', options={'ratio': '16:9'}, refs=[])['media_action']
        action = prepared['action']
        pipeline.gates[action['id']] = dict(workspace=self.http.store.workspace_id, project=self.pid,
            action_hash=action['hash'], input_sha256=prepared['input_sha256'], model=contract.MODEL,
            output_policy=action['options']['output_policy'], maximum_units=10000, maximum_calls=1,
            expires=time.time()+200)
        self.budget('0.01')
        grant = self.post('media_approve', song='A', action_id=action['id'])['media_grant']
        return dict(plan_id=plan, action_id=action['id'], grant_id=grant['id'])

    def test_actual_media_controller_reservation_blocks_general_approval_in_same_budget(self):
        args = self.prepare_media_action()
        preview = self.preview()
        media = self.post('media_action_decide', song='A', action_id=args['action_id'], decision='execute')
        status, failure = self.approve(preview)
        self.assertEqual(status, 400)
        self.assertIn('예산', failure['error'])
        with self.http.store.connect() as c:
            row = c.execute('SELECT b.scope,r.job FROM reservations r JOIN budgets b ON b.id=r.budget').fetchall()
        self.assertEqual(row, [('project:' + self.pid, media['job'])])
        self.assertEqual((self.keys, self.socket.requests), ([], []))
        self.receipt = {'crossflow': 'actual media controller admission -> general-chat approval',
                        'budget_scope': 'project:' + self.pid, 'chat_status': status,
                        'reservations': len(row), 'external_provider_calls': 0}

    def test_general_reservation_blocks_actual_media_controller_in_same_budget(self):
        args = self.prepare_media_action()
        preview = self.preview()
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        status, failure = self.action('media_action_decide', song='A', action_id=args['action_id'], decision='execute')
        self.assertEqual(status, 400)
        self.assertIn('예산', failure['error'])
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT count(*) FROM generation_jobs').fetchone()[0], 0)
        self.assertEqual((self.keys, self.socket.requests), ([], []))

    def test_minimal_usage_keeps_unknown_cost_and_blocks_same_budget_in_other_conversation(self):
        for index, upstream in enumerate((response(), dict(reply(), model='wrong-model'))):
            cid = self.post('conversation_create', song='A', title='격리 과금 확인 ' + str(index))['conversation']['id']
            if index:
                # A separate project budget is not used to evade uncertainty;
                # the first unsafe result must prevent this later admission.
                preview = self.preview(conversation=cid)
                status, _ = self.approve(preview, conversation=cid)
                self.assertEqual(status, 400)
                break
            self.socket.replies = [upstream]
            preview = self.preview(conversation=cid)
            status, result = self.approve(preview, conversation=cid)
            self.assertEqual(status, 200, result)
            self.process()
            turn, held, attempts = self.reservation(result['turn']['id'])
            self.assertEqual(turn['status'], 'outcome_unknown')
            self.assertEqual(held, ('uncertain', None))
            self.assertEqual(len(self.socket.requests), 2)
            self.assertEqual(turn['pricing_status'], 'insufficient_billing_evidence')

    def test_model_mismatch_preserves_observation_and_never_executes_tools(self):
        self.socket.replies = [dict(reply([use('forbidden', 'propose_media_plan', dict(goal='x', scenes='x', style='', constraints='', kind='visualizer'))], 'tool_use'), model='wrong-model')]
        preview = self.preview()
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        self.process()
        turn, held, _ = self.reservation(result['turn']['id'])
        self.assertEqual(turn['status'], 'outcome_unknown')
        self.assertEqual(held, ('uncertain', None))
        self.assertEqual(turn['pricing_status'], 'pricing_contract_changed')
        self.assertEqual(self.project().get('guided_plans', []), [])

    def test_timeout_retains_claim_and_unknown_reservation_without_retry(self):
        self.socket.replies = [TimeoutError(FAKE_KEY)]
        preview = self.preview()
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        self.process()
        turn, held, attempts = self.reservation(result['turn']['id'])
        self.assertEqual(turn['status'], 'outcome_unknown')
        self.assertEqual(held, ('uncertain', None))
        self.assertIn(('chat-message', 'unknown'), attempts)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.socket.requests), 2)
        self.assertNotIn(FAKE_KEY, json.dumps(self.state()))

    def test_missing_credential_acquisition_stays_lazy_and_does_not_open_provider(self):
        self.key_value = None
        preview = self.preview()
        self.assertEqual(self.keys, [])
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        self.assertEqual(self.keys, [])
        self.process()
        turn, held, attempts = self.reservation(result['turn']['id'])
        self.assertEqual(self.keys, ['Anthropic_KEY'])
        self.assertEqual(self.socket.requests, [])
        self.receipt = {'boundary': 'credential missing before provider transport', 'mode': 'anthropic-live',
                        'provider_network_requests': 0, 'reservation': held, 'attempts': attempts, 'turn_status': turn['status']}
        self.assertEqual((turn['status'], held, attempts), ('blocked_before_message', ('cancelled', None), [('chat-count', 'not_sent')]))
        self.assertEqual(turn['message_status'], 'not_sent')
        self.assertFalse(self.project()['production_runs'][-1]['live_model_called'])
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.key_value = FAKE_KEY
        fresh = self.preview()
        self.assertEqual(self.socket.requests, [])
        status, accepted = self.approve(fresh)
        self.assertEqual(status, 200, accepted)
        self.process()
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'], 'completed')
        self.assertEqual(len(self.socket.requests), 2)

    def test_missing_message_credential_after_successful_count(self):
        preview = self.preview()
        status, result = self.approve(preview)
        self.assertEqual(status, 200, result)
        original = self.socket.open
        def count_then_remove(request, timeout):
            response = original(request, timeout)
            if request.full_url.endswith('count_tokens'):
                self.key_value = None
            return response
        with patch.object(self.socket, 'open', side_effect=count_then_remove):
            self.process()
        turn, held, attempts = self.reservation(result['turn']['id'])
        self.assertEqual(len(self.socket.requests), 1)
        self.receipt = {'boundary': 'message credential missing after observed count', 'mode': 'anthropic-live',
                        'provider_network_requests': 1, 'reservation': held, 'attempts': attempts,
                        'turn_status': turn['status'], 'live_model_called': self.project()['production_runs'][-1]['live_model_called']}
        self.assertEqual((turn['status'], held, attempts), ('blocked_before_message', ('cancelled', None), [('chat-count', 'observed'), ('chat-message', 'not_sent')]))
        self.assertFalse(self.project()['production_runs'][-1]['live_model_called'])

    def test_empty_and_failing_credential_suppliers_never_open_transport_or_leak_error(self):
        for value, failure in (('', None), (None, RuntimeError(FAKE_KEY))):
            self.key_value = value
            self.key_error = failure
            before_keys = len(self.keys)
            preview = self.preview()
            self.assertEqual(len(self.keys), before_keys)
            status, result = self.approve(preview)
            self.assertEqual(status, 200, result)
            self.process()
            turn, held, attempts = self.reservation(result['turn']['id'])
            self.assertEqual((turn['status'], held), ('blocked_before_message', ('cancelled', None)))
            self.assertEqual(attempts, [('chat-count', 'not_sent')])
            self.assertEqual(self.socket.requests, [])
            self.assertFalse(self.project()['production_runs'][-1]['live_model_called'])
            self.assertNotIn(FAKE_KEY, json.dumps(self.state()))

    def test_later_round_message_credentials_failure_preserves_earlier_observed_usage(self):
        self.socket.replies = [reply([use('context', 'search_project_context', {'query': '현재 작품'})], 'tool_use')]
        first = self.preview()
        status, result = self.approve(first)
        self.assertEqual(status, 200, result)
        self.process()
        first_private, first_held, _ = self.reservation(result['turn']['id'])
        self.assertEqual(first_held, ('estimated', 60))
        first_reservation = first_private['reservation']
        follow = self.project()['general_chat_previews'][-1]
        self.assertIn('music_context', follow)
        status, result = self.approve(follow)
        self.assertEqual(status, 200, result)
        original = self.socket.open
        def lose_key(request, timeout):
            value = original(request, timeout)
            if request.full_url.endswith('count_tokens'):
                self.key_value = None
            return value
        with patch.object(self.socket, 'open', side_effect=lose_key):
            self.process()
        turn, held, attempts = self.reservation(result['turn']['id'])
        self.assertTrue(turn['submitted'])
        self.assertEqual(held, ('cancelled', None))
        self.assertEqual(attempts, [('chat-count', 'observed'), ('chat-message', 'not_sent')])
        self.assertTrue(self.project()['production_runs'][-1]['live_model_called'])
        self.assertEqual(len(self.socket.requests), 3)
        with self.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual FROM reservations WHERE id=?', (first_reservation,)).fetchone(), ('estimated', 60))
        self.receipt = {'boundary': 'later-round credential failure', 'reservation': held,
                        'current_attempts': attempts, 'prior_reservation': ['estimated', 60],
                        'live_model_called_preserves_prior_observation': True, 'automatic_retry': False}

    def upload_audio(self):
        content = io.BytesIO()
        with wave.open(content, 'wb') as wav:
            wav.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
            wav.writeframes(b'\x00\x00' * 24000)
        self.post('audio', song='A', filename='synthetic.wav',
                  content=base64.b64encode(content.getvalue()).decode(), rights='직접 제작한 합성 음원')

    def run_dialogue(self, replies):
        self.socket.replies = replies
        preview = self.preview()
        while True:
            status, result = self.approve(preview)
            self.assertEqual(status, 200, result)
            self.process()
            project = self.project()
            if project['general_chat_turns'][-1]['status'] == 'completed':
                return project['general_chat_turns'][-1]
            self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
            preview = project['general_chat_previews'][-1]

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'local media tools required')
    def test_production_branch_music_edit_human_approval_render_and_verified_receipt(self):
        self.upload_audio()
        image = Path(self.tmp.name) / 'synthetic.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=64x64',
                        '-frames:v', '1', str(image)], check=True)
        self.post('shot', song='A', shot='s', description='선택 사진 장면')
        self.post('take', song='A', shot='s', shot_revision=0, filename='synthetic.png',
                  content=base64.b64encode(image.read_bytes()).decode(), rights='직접 제작', reason='선택 사진')
        self.post('select', song='A', shot='s', shot_revision=1, take=1)
        self.post('review_take', song='A', shot='s', take=1, decision='approved', reason='합성 자료 확인')
        timeline = editing.current(self.project())
        timeline['clips'][0]['duration'] = 1
        self.post('timeline', song='A', timeline=timeline)
        self.post('approve_timeline', song='A')
        commands = [dict(op='set_audio_offset', audio_version=1, source_offset_seconds=.25),
                    dict(op='set_captions', cues=[dict(start=0, end=1, text='새로운 리듬 BEAT')])]
        self.run_dialogue([reply([use('read', 'search_project_context', {'query': '음원과 편집 버전'})], 'tool_use'),
                           reply([use('edit', 'propose_timeline_changes', dict(description='음원 시작과 자막 수정', timeline_version=1, commands=commands))], 'tool_use'),
                           reply()])
        self.assertEqual(self.project()['timeline_head'], 1)
        self.assertEqual(self.state()['jobs'], [])
        proposal = self.project()['timeline_edit_proposals'][-1]
        self.post('review_timeline_proposal', song='A', proposal_id=proposal['id'], timeline_version=1, decision='approved')
        self.assertNotIn('approval', editing.current(self.project()))
        self.post('approve_timeline', song='A')
        current = editing.current(self.project())
        args = dict(timeline_version=current['id'], grant_id=current['approval']['id'])
        self.run_dialogue([reply([use('read-again', 'search_project_context', {'query': '승인 편집'})], 'tool_use'),
                           reply([use('render', 'request_render', args)], 'tool_use'), reply()])
        self.assertTrue(self.http.store.process_next())
        job = self.state()['jobs'][-1]
        self.assertEqual(job['status'], 'completed', job.get('error'))
        self.run_dialogue([reply([use('receipt', 'request_render', args)], 'tool_use'), reply()])
        bodies = [json.loads(raw) for url, raw, _ in self.socket.requests if url == anthropic.ENDPOINT]
        receipts = [json.loads(block['content']) for body in bodies for message in body['messages']
                    if isinstance(message.get('content'), list) for block in message['content']
                    if block.get('type') == 'tool_result']
        self.assertTrue(any(x.get('finished_verified') and not x['output_approved'] for x in receipts))
        status, downloaded = self.request('GET', '/exports/' + job['id'] + '.mp4')
        self.assertEqual(status, 200)
        self.assertEqual(hashlib.sha256(downloaded).hexdigest(), job['sha256'])
        path = self.http.store.root / 'exports' / (job['id'] + '.mp4')
        metadata = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
        self.assertEqual({s['codec_type'] for s in metadata['streams']}, {'video', 'audio', 'subtitle'})
        captions = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:s:0', '-f', 'srt', '-']).decode()
        self.assertIn('새로운 리듬 BEAT', captions)
        self.receipt = {'workflow': 'real platform HTTP -> production adapter branch -> synthetic provider socket -> human edit approval -> real local MP4 -> receipt',
                        'actual_AI_requests': 0, 'runtime_mode': 'anthropic-live', 'mp4_sha256': job['sha256'],
                        'stream_types': sorted(s['codec_type'] for s in metadata['streams']),
                        'approved_audio_version': current['audio'], 'audio_offset': current['audio_offset'],
                        'output_approved': False, 'provider_socket_requests': len(self.socket.requests)}
