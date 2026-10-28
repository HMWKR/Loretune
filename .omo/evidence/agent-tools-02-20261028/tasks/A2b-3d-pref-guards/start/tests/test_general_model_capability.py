"""Selected-model capability is observed through the real state/action HTTP API."""
import unittest
from unittest.mock import patch
import model_selection
from tests import test_general_model_schedule as schedule_tests

class GeneralModelCapabilityHTTPTest(unittest.TestCase):
    setUp=schedule_tests.GeneralModelSchedulingHTTPTest.setUp
    close=schedule_tests.GeneralModelSchedulingHTTPTest.close
    request=schedule_tests.GeneralModelSchedulingHTTPTest.request
    state=schedule_tests.GeneralModelSchedulingHTTPTest.state
    project=schedule_tests.GeneralModelSchedulingHTTPTest.project
    action=schedule_tests.GeneralModelSchedulingHTTPTest.action
    post=schedule_tests.GeneralModelSchedulingHTTPTest.post
    budget=schedule_tests.GeneralModelSchedulingHTTPTest.budget
    schedule=schedule_tests.GeneralModelSchedulingHTTPTest.schedule

    def test_current_selection_scope_and_no_credential_acquisition(self):
        other=self.post('conversation_create',song='A',title='B')['conversation']['id']
        for revision,selection in enumerate((None,'openai-gpt-6-luna','xai-grok-4-7','anthropic-haiku-5-5')):
            self.assertEqual(self.schedule(selection,revision)[0],200)
            cap=self.project()['general_chat_connection']
            self.assertTrue(cap['configured'])
            self.assertEqual(cap['available'],selection=='anthropic-haiku-5-5')
            self.assertFalse(cap['account_verified'])
            self.assertFalse(cap['billing_verified'])
            self.assertEqual(cap['current_selection'],selection)
            if not cap['available']:
                self.assertEqual(self.action('general_chat_preview',song='A',prompt='예시',maximum_micro=10000,total_maximum_micro=10000)[0],400)
            scoped=self.request('GET','/api/state?song=A&conversation='+other)[1]['projects']['A']
            self.assertTrue(scoped['general_chat_connection']['available'])
        self.assertEqual(self.keys,[])
        self.assertEqual(self.socket.requests,[])

    def test_retired_and_disabled_catalog_models_fail_closed_without_key(self):
        for state in ('disabled','retired','integration_blocked'):
            catalog=tuple(dict(x,state=state) if x['id']=='anthropic-haiku-5-5' else x for x in model_selection.CATALOG)
            with patch.object(model_selection,'CATALOG',catalog):
                self.assertFalse(self.project()['general_chat_connection']['available'])
                self.assertEqual(self.action('general_chat_preview',song='A',prompt='예시',maximum_micro=10000,total_maximum_micro=10000)[0],400)
        self.assertEqual(self.keys,[])
