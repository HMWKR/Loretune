"""Fake transport only. No environment secrets, provider connection or expenditure."""
import unittest
from unittest.mock import patch
import fal_provider as fal

class FalContractTest(unittest.TestCase):
    def test_approved_reader_serializes_only_on_new_generation_request(self):
        import json
        calls=[]
        client=fal.FalKling(private_reader='synthetic-owner',transport=lambda *a:(calls.append(a) or self.receipt))
        client.submit(self.data)
        self.assertEqual(json.loads(calls[0][2]['X-Fal-Object-Lifecycle-Preference']),fal.private_lifecycle_candidate('synthetic-owner'))
        self.assertEqual(calls[0][3],self.data)
        self.assertEqual(len(calls),1)
        self.assertNotIn('Authorization',calls[0][2])
    def test_explicit_reader_candidate_is_private_and_not_live_configuration(self):
        policy=fal.private_lifecycle_candidate('synthetic-owner')
        self.assertEqual(policy,{'expiration_duration_seconds':3600,'initial_acl':{'default':'forbid','rules':[{'user':'synthetic-owner','decision':'allow'}]}})
        policy['initial_acl']['rules'].append({'user':'other','decision':'allow'})
        self.assertEqual(len(fal.private_lifecycle_candidate('synthetic-owner')['initial_acl']['rules']),1)
        calls=[]
        fal.FalKling(transport=lambda *a:(calls.append(a) or self.receipt)).submit(self.data)
        import json
        self.assertEqual(json.loads(calls[0][2]['X-Fal-Object-Lifecycle-Preference']),fal.LIFECYCLE)
        self.assertEqual(fal.LIFECYCLE['initial_acl']['rules'],[])

    def test_reader_candidate_rejects_unresolved_or_ambiguous_identity(self):
        for value in [None,'','Display Name','a@example.com','https://fal.ai/alice',' alice','alice\n','*',{'user':'alice'},['alice']]:
            with self.subTest(value=value),self.assertRaises(ValueError):fal.private_lifecycle_candidate(value)

    def setUp(self):
        self.identifier='11111111-1111-4111-8111-111111111111'
        prefix=fal.BASE+'fal-ai/kling-video/requests/'+self.identifier
        self.receipt=dict(request_id=self.identifier,status_url=prefix+'/status',response_url=prefix,cancel_url=prefix+'/cancel')
        self.data=fal.payload('A blue geometric landscape',b'\x89PNG\r\n\x1a\nfixture')
    def test_disabled_client_does_not_read_key_or_send(self):
        with patch('fal_provider.os.environ.get',side_effect=AssertionError('secret read')):
            client=fal.FalKling.from_environment()
            with self.assertRaisesRegex(fal.ProviderError,'provider_not_connected'):client.submit(self.data)
    def test_exact_model_no_audio_and_no_retry(self):
        calls=[]
        def send(*args):calls.append(args);return self.receipt
        self.assertEqual(fal.FalKling(transport=send).submit(self.data),self.receipt)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1],fal.BASE+fal.MODEL)
        self.assertEqual(calls[0][2]['X-Fal-No-Retry'],'1')
        self.assertNotIn('Authorization',calls[0][2])
        self.assertFalse(calls[0][3]['generate_audio'])
        self.assertEqual(fal.estimate()['money']['amount'],'0.70')
    def test_receipt_loss_or_host_change_is_uncertain_no_resubmit(self):
        calls=[]
        def send(*args):calls.append(args);return dict(self.receipt,status_url='https://example.com/secret')
        with self.assertRaises(fal.ProviderError) as e:fal.FalKling(transport=send).submit(self.data)
        self.assertTrue(e.exception.uncertain);self.assertEqual(len(calls),1)
    def test_completion_and_cancel_do_not_imply_approval_or_refund(self):
        client=fal.FalKling(transport=lambda *args:{'status':'COMPLETED'})
        value=client.status(self.receipt);self.assertTrue(value['result_ready']);self.assertFalse(value['approved']);self.assertFalse(value['cost_confirmed'])
        self.assertFalse(client.cancel(self.receipt)['refund_confirmed'])
        client=fal.FalKling(transport=lambda *args:{'video':{'url':'https://v3b.fal.media/test.mp4'}})
        self.assertFalse(client.result(self.receipt)['approved'])
    def test_untrusted_receipt_and_result_never_fetch_arbitrary_hosts(self):
        calls=[]
        client=fal.FalKling(transport=lambda *args:calls.append(args))
        with self.assertRaises(fal.ProviderError):client.status(dict(self.receipt,status_url='https://attacker.invalid/'))
        self.assertEqual(calls,[])
        client=fal.FalKling(transport=lambda *args:{'video':{'url':'http://127.0.0.1/private'}})
        with self.assertRaises(fal.ProviderError):client.result(self.receipt)
