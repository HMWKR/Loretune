"""Real HTTP and SQLite coverage for conversation-scoped model scheduling."""
import hashlib
import json
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import server
import anthropic_ontology
import chat_runtime
import contracts
import model_selection

PROMPT = 'Synthetic model scheduling test.'
INITIAL = 'anthropic-haiku-5-5'
NEXT = 'openai-gpt-6-luna'


class PausedAdapter:
    mode = 'contract-fake'

    def __init__(self, fail=False):
        self.entered = threading.Event()
        self.release = threading.Event()
        self.fail = fail
        self.calls = 0

    def count(self, body):
        return 100

    def complete(self, body):
        self.calls += 1
        self.entered.set()
        if not self.release.wait(10):
            raise RuntimeError('fixture timeout')
        if self.fail:
            raise RuntimeError('fixture failure')
        return dict(_request_id='synthetic', stop_reason='end_turn',
                    usage=dict(input_tokens=100, output_tokens=100),
                    content=[dict(type='text', text='Synthetic reply')])


class ModelSchedulingHTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.http = server(self.tmp.name, 0)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)
        self.base = f'http://127.0.0.1:{self.http.server_port}'
        self.adapter = PausedAdapter()
        state = self.get()
        self.post(dict(action='project', data=dict(name='A', era='default', story=0),
                       revision=state['revision'], request_id=uuid.uuid4().hex), state['token'])
        state = self.get()
        self.post(dict(action='model_settings', data=dict(song='A', selections={'chat': INITIAL}, model_revision=0),
                       revision=state['revision'], request_id=uuid.uuid4().hex), state['token'])
        project = self.get()['projects']['A']
        self.cid = self.get('')['projects']['A']['active_conversation']['id']
        approval = dict(model=anthropic_ontology.MODEL, workspace_id=self.http.store.workspace_id,
                        project_id=contracts.project_id(self.http.store.workspace_id, 'A'), synthetic_only=True,
                        expires=time.time()+300, context_hash=model_selection.snapshot(project)['sha256'],
                        prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],
                        price_revision='haiku-5-5-20261027-tiered', max_rounds=2)
        self.runtime = chat_runtime.ChatRuntime(self.http.store, self.adapter, approval,
                                                Path(self.tmp.name)/'synthetic-journal.sqlite')
        self.http.store.chat_runtime = self.runtime

    def shutdown(self):
        self.adapter.release.set()
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()

    def get(self, cid=None):
        query = '' if cid is None else '?' + urlencode({'song': 'A', 'conversation': cid})
        with urlopen(self.base + '/api/state' + query) as response:
            return json.load(response)

    def request(self, action, data, cid=None):
        cid = cid or self.cid
        state = self.get(cid)
        active = state['projects']['A']['active_conversation']
        return dict(action=action, data=dict(song='A', **data), revision=state['revision'],
                    request_id=uuid.uuid4().hex, conversation_id=cid,
                    conversation_revision=active['revision'], shared_version=active['shared_version']), state['token']

    def post(self, payload, token):
        request = Request(self.base+'/api/action', data=json.dumps(payload).encode(),
                          headers={'Content-Type':'application/json', 'X-Loretune-Token':token})
        try:
            with urlopen(request) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def start(self):
        req, token = self.request('chat_turn', {'prompt': PROMPT})
        status, result = self.post(req, token)
        self.assertEqual(status, 200, result)
        worker = threading.Thread(target=self.runtime.process_next)
        worker.start()
        self.addCleanup(worker.join, 10)
        self.assertTrue(self.adapter.entered.wait(10))
        return worker, result['chat_turn']['id']

    def schedule(self, model, revision):
        req, token = self.request('conversation_model', {'selection':model, 'model_revision':revision})
        return self.post(req, token)

    def test_running_turn_keeps_model_until_completion_and_reopen(self):
        req, token = self.request('conversation_create', {'title':'B'})
        status, result = self.post(req, token)
        self.assertEqual(status, 200)
        other = result['conversation']['id']
        worker, turn_id = self.start()
        stale, token = self.request('conversation_model', {'selection':NEXT, 'model_revision':0})
        status, result = self.post(stale, token)
        self.assertEqual(status, 200, result)
        during = self.get(self.cid)['projects']['A']
        self.assertEqual(during['effective_chat_selection'], INITIAL)
        self.assertEqual(during['active_conversation']['pending_chat_selection'], {'selection':NEXT,'after_turn':turn_id})
        self.assertEqual(during['chat_turns'][-1]['model'], anthropic_ontology.MODEL)
        self.assertEqual(self.get(other)['projects']['A']['effective_chat_selection'], INITIAL)
        status, _ = self.schedule(INITIAL, 0)
        self.assertEqual(status, 409)
        self.adapter.release.set()
        worker.join(10)
        self.assertFalse(worker.is_alive())
        after = self.get(self.cid)['projects']['A']
        self.assertEqual(after['chat_turns'][-1]['status'], 'completed')
        self.assertEqual(after['effective_chat_selection'], NEXT)
        self.assertNotIn('pending_chat_selection', after['active_conversation'])
        self.assertEqual(self.get(other)['projects']['A']['effective_chat_selection'], INITIAL)
        from app import Store
        self.assertEqual(Store(self.tmp.name).state({'A':self.cid})['projects']['A']['effective_chat_selection'], NEXT)
        self.assertEqual(self.adapter.calls, 1)

    def test_unknown_does_not_apply_or_allow_new_change(self):
        self.adapter.fail = True
        worker, turn_id = self.start()
        self.assertEqual(self.schedule(NEXT, 0)[0], 200)
        self.adapter.release.set()
        worker.join(10)
        self.assertFalse(worker.is_alive())
        project = self.get(self.cid)['projects']['A']
        self.assertEqual(project['chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertEqual(project['effective_chat_selection'], INITIAL)
        self.assertEqual(project['active_conversation']['pending_chat_selection']['after_turn'], turn_id)
        self.assertEqual(self.schedule(INITIAL, 1)[0], 400)
        self.assertEqual(self.adapter.calls, 1)

    def test_cancelled_turn_requires_explicit_selection_and_keeps_other_state(self):
        worker, turn_id = self.start()
        self.assertEqual(self.schedule(NEXT, 0)[0], 200)
        self.assertEqual(self.schedule(INITIAL, 1)[0], 200)
        self.assertEqual(self.schedule(NEXT, 2)[0], 200)
        cancel, token = self.request('chat_cancel', {'turn':turn_id})
        self.assertEqual(self.post(cancel, token)[0], 200)
        self.assertEqual(self.schedule(INITIAL, 3)[0], 400)
        self.adapter.release.set()
        worker.join(10)
        self.assertFalse(worker.is_alive())
        project = self.get(self.cid)['projects']['A']
        self.assertEqual(project['chat_turns'][-1]['status'], 'cancelled')
        self.assertEqual(project['effective_chat_selection'], INITIAL)
        self.assertEqual(project['active_conversation']['pending_chat_selection']['selection'], NEXT)
        retry, token = self.request('chat_turn', {'prompt':PROMPT})
        self.assertEqual(self.post(retry, token)[0], 400)
        self.assertEqual(self.schedule(NEXT, 3)[0], 200)
        project = self.get(self.cid)['projects']['A']
        self.assertEqual(project['effective_chat_selection'], NEXT)
        self.assertNotIn('pending_chat_selection', project['active_conversation'])


if __name__ == '__main__':
    unittest.main()
