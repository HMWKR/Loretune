"""Synthetic Anthropic usage contracts; no provider or credentials are used."""
import unittest
from copy import deepcopy

import chat_general
import chat_models


class AnthropicUsageDimensionsTest(unittest.TestCase):
    def setUp(self):
        self.spec=chat_models.contract('anthropic-haiku-5-5')
        self.usage={'input_tokens':100,'output_tokens':50}

    def reason(self,usage,**top):
        response={'usage':usage,**top}
        reason=chat_general.unpriced_reason(chat_general.observe_usage(response))
        if reason:
            with self.assertRaises(ValueError):chat_models.usage(self.spec,response,require_model=False,require_billing_evidence=False)
        else:
            self.assertEqual(chat_models.usage(self.spec,response,require_model=False,require_billing_evidence=False),{'input_tokens':100,'output_tokens':50})
        return reason

    def test_standard_official_shape_and_legacy_fixture(self):
        self.assertIsNone(self.reason(deepcopy(self.usage)))
        official={**self.usage,'service_tier':'standard','speed':'standard','inference_geo':'global',
                  'server_tool_use':{'web_fetch_requests':0,'web_search_requests':0},
                  'cache_creation':{'ephemeral_1h_input_tokens':0,'ephemeral_5m_input_tokens':0},
                  'cache_creation_input_tokens':0,'cache_read_input_tokens':0,
                  'output_tokens_details':{'thinking_tokens':25}}
        self.assertIsNone(self.reason(official,service_tier='standard'))

    def test_unpriced_and_malformed_dimensions_fail_closed(self):
        cases=[({'service_tier':'priority'},'unsupported_service_tier'),({'service_tier':[]},'unsupported_service_tier'),
               ({'speed':'fast'},'unsupported_speed'),({'speed':None},'unsupported_speed'),
               ({'inference_geo':'us'},'unsupported_inference_geo'),({'inference_geo':'unknown'},'unsupported_inference_geo'),
               ({'server_tool_use':{'web_fetch_requests':0,'web_search_requests':1}},'unsupported_server_tool_usage'),
               ({'server_tool_use':{'web_fetch_requests':False,'web_search_requests':0}},'unsupported_server_tool_usage'),
               ({'server_tool_use':{'web_fetch_requests':0,'web_search_requests':0,'new':0}},'unsupported_server_tool_usage'),
               ({'cache_creation':{'ephemeral_1h_input_tokens':1,'ephemeral_5m_input_tokens':0}},'unsupported_cache_usage'),
               ({'cache_creation_input_tokens':None},'invalid_or_unrepresentable_usage'),
               ({'cache_read_input_tokens':False},'invalid_or_unrepresentable_usage'),
               ({'output_tokens_details':{'thinking_tokens':51}},'unsupported_output_tokens_details'),
               ({'new_private_billing_key':'sensitive-fixture'},'unknown_usage_dimension')]
        for extra,expected in cases:
            with self.subTest(extra=extra):
                usage={**self.usage,**extra};self.assertEqual(self.reason(usage),expected)
                self.assertNotIn('sensitive-fixture',str(chat_general.observe_usage({'usage':usage})))
        self.assertEqual(self.reason({**self.usage,'service_tier':'priority'},service_tier='standard'),'unsupported_service_tier')
        self.assertEqual(self.reason({**self.usage,'speed':'standard'},speed='fast'),'unsupported_speed')

    def test_explicit_response_model_must_match_contract(self):
        self.assertEqual(chat_models.usage(self.spec,{'model':self.spec['model'],'usage':self.usage},require_billing_evidence=False),self.usage)
        for model in ('claude-other-model',None,42):
            with self.subTest(model=model),self.assertRaises(ValueError):
                chat_models.usage(self.spec,{'model':model,'usage':self.usage})
        with self.assertRaises(ValueError):chat_models.usage(self.spec,{'usage':self.usage})
        self.assertEqual(chat_models.usage(self.spec,{'usage':self.usage},require_model=False,require_billing_evidence=False),self.usage)

    def test_actual_contract_requires_observed_standard_billing_dimensions(self):
        complete={**self.usage,'service_tier':'standard','speed':'standard','inference_geo':'global',
                  'cache_creation_input_tokens':0,'cache_read_input_tokens':0,
                  'server_tool_use':{'web_fetch_requests':0,'web_search_requests':0}}
        response={'model':self.spec['model'],'usage':complete}
        self.assertEqual(chat_models.usage(self.spec,response),self.usage)
        for name in ('service_tier','speed','inference_geo','cache_creation_input_tokens','cache_read_input_tokens','server_tool_use'):
            with self.subTest(missing=name):
                partial=dict(complete);partial.pop(name)
                with self.assertRaisesRegex(ValueError,'insufficient_billing_evidence'):
                    chat_models.usage(self.spec,{'model':self.spec['model'],'usage':partial})

    def test_actual_contract_does_not_accept_top_level_as_nested_evidence(self):
        complete={**self.usage,'service_tier':'standard','speed':'standard','inference_geo':'global',
                  'cache_creation_input_tokens':0,'cache_read_input_tokens':0,
                  'server_tool_use':{'web_fetch_requests':0,'web_search_requests':0}}
        for name in ('service_tier','speed','inference_geo','server_tool_use'):
            with self.subTest(missing=name):
                nested=dict(complete);value=nested.pop(name)
                observed=chat_general.observe_usage({'usage':nested,name:value})
                self.assertEqual(chat_general.unpriced_reason(observed,require_billing_evidence=True,usage=nested),'insufficient_billing_evidence')
                with self.assertRaisesRegex(ValueError,'insufficient_billing_evidence'):
                    chat_models.usage(self.spec,{'model':self.spec['model'],'usage':nested,name:value})

    def test_late_model_status_requires_bound_model_and_hides_original(self):
        model=self.spec['model']
        for reply,expected in [({'model':model},'match'),({'model':'private-name'},'mismatch'),
                               ({},'missing'),({'model':None},'invalid'),({'model':5},'invalid'),({'model':' '},'invalid')]:
            with self.subTest(reply=reply):self.assertEqual(chat_general.late_model_status(reply,model),expected)
        self.assertEqual(chat_general.late_model_status({'model':model},None),'unknown')

    def test_late_sources_record_field_locations_without_values(self):
        reply={'usage':{'service_tier':'standard','inference_geo':'global'},'speed':'private-speed','inference_geo':'us'}
        self.assertEqual(chat_general.late_billing_sources(reply),{'service_tier':'usage','speed':'response','inference_geo':'both','server_tool_use':'absent'})
        self.assertNotIn('private-speed',str(chat_general.late_billing_sources(reply)))
