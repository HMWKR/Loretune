"""Loopback HTTP scheduling; only synthetic provider bytes and credentials."""
import json
import hashlib
import unittest
from copy import deepcopy
from tests import test_general_chat_activation as activation
import chat_general

INITIAL = 'anthropic-haiku-5-5'
NEXT = 'xai-grok-4-7'

class GeneralModelSchedulingHTTPTest(unittest.TestCase):
    setUp = activation.GeneralChatActivationHTTPTest.setUp
    close = activation.GeneralChatActivationHTTPTest.close
    request = activation.GeneralChatActivationHTTPTest.request
    state = activation.GeneralChatActivationHTTPTest.state
    project = activation.GeneralChatActivationHTTPTest.project
    action = activation.GeneralChatActivationHTTPTest.action
    post = activation.GeneralChatActivationHTTPTest.post
    budget = activation.GeneralChatActivationHTTPTest.budget
    preview = activation.GeneralChatActivationHTTPTest.preview
    approve = activation.GeneralChatActivationHTTPTest.approve
    process = activation.GeneralChatActivationHTTPTest.process
    reservation = activation.GeneralChatActivationHTTPTest.reservation

    def schedule(self, selection, revision, conversation=None):
        return self.action('conversation_model', song='A', selection=selection,
                           model_revision=revision, conversation=conversation or self.project()['active_conversation']['id'])

    def test_queued_and_tool_wait_reservations_preserve_exact_execution_then_apply(self):
        other=self.post('conversation_create', song='A', title='B')['conversation']['id']
        self.socket.replies=[activation.reply([activation.use('context','search_project_context',{'query':'현재 작품'})], 'tool_use'),activation.reply()]
        preview=self.preview()
        status,result=self.approve(preview)
        self.assertEqual(status,200,result)
        tid=result['turn']['id']
        with self.http.store.connect() as c:
            original=deepcopy(chat_general.get_row(c,'general_chat_previews',preview['id']))
        status,result=self.schedule(NEXT,0)
        self.assertEqual(status,200,result)
        self.assertEqual(self.schedule(INITIAL,0)[0],409)
        self.process()
        project=self.project()
        self.assertEqual(project['general_chat_turns'][-1]['status'],'awaiting_continuation_approval')
        self.assertEqual(project['effective_chat_selection'],INITIAL)
        self.assertTrue(project['general_chat_connection']['available'])
        self.assertFalse(project['general_chat_connection']['new_preview_available'])
        self.assertEqual(hashlib.sha256(self.socket.requests[0][1]).hexdigest(),original['count_wire_sha256'])
        self.assertEqual(hashlib.sha256(self.socket.requests[1][1]).hexdigest(),original['message_wire_sha256'])
        self.assertEqual(json.loads(self.socket.requests[1][1]),original['message_body'])
        following=project['general_chat_previews'][-1]
        self.assertEqual(self.schedule(INITIAL,1)[0],200)
        self.assertEqual(self.schedule(NEXT,2)[0],200)
        self.assertEqual(self.approve(following)[0],200)
        self.process()
        project=self.project()
        self.assertEqual(project['general_chat_turns'][-1]['status'],'completed')
        self.assertEqual(project['effective_chat_selection'],NEXT)
        self.assertNotIn('pending_chat_selection',project['active_conversation'])
        self.assertFalse(project['general_chat_connection']['available'])
        self.assertTrue(project['general_chat_connection']['configured'])
        self.assertEqual(self.action('general_chat_preview',song='A',prompt='새 요청',maximum_micro=10000,total_maximum_micro=10000)[0],400)
        self.assertEqual(len(self.socket.requests),4)
        self.assertEqual(self.request('GET','/api/state?song=A&conversation='+other)[1]['projects']['A']['effective_chat_selection'],INITIAL)
        self.assertEqual(self.schedule(INITIAL,3)[0],200)
        self.assertTrue(self.preview()['history_context']['request_count'])
        with self.http.store.connect() as c:
            saved=chat_general.get_row(c,'general_chat_previews',preview['id'])
        for key in ('binding','message_body','count_body','manifest_sha256','message_wire_sha256','count_wire_sha256'):
            self.assertEqual(saved[key],original[key])

    def test_cancelled_pending_requires_explicit_reselection(self):
        preview=self.preview(); status,result=self.approve(preview)
        self.assertEqual(status,200,result)
        tid=result['turn']['id']
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        self.post('general_chat_cancel',song='A',turn=tid)
        self.assertEqual(self.project()['effective_chat_selection'],INITIAL)
        self.assertEqual(self.action('general_chat_preview',song='A',prompt='새 요청',maximum_micro=10000,total_maximum_micro=10000)[0],400)
        self.assertEqual(self.schedule(INITIAL,1)[0],200)
        self.preview()
        self.assertEqual(self.socket.requests,[])

    def test_nondefault_conversation_completion_changes_only_its_override(self):
        other=self.post('conversation_create',song='A',title='B')['conversation']['id']
        preview=self.preview(conversation=other)
        self.assertEqual(self.approve(preview,conversation=other)[0],200)
        self.assertEqual(self.schedule(NEXT,0,conversation=other)[0],200)
        self.process()
        scoped=self.request('GET','/api/state?song=A&conversation='+other)[1]['projects']['A']
        self.assertEqual(scoped['effective_chat_selection'],NEXT)
        self.assertFalse(scoped['general_chat_connection']['available'])
        self.assertEqual(self.project()['effective_chat_selection'],INITIAL)
        self.assertTrue(self.project()['general_chat_connection']['available'])

    def test_two_active_engines_reject_reservation_without_changing_selection(self):
        preview=self.preview();self.assertEqual(self.approve(preview)[0],200)
        cid=self.project()['active_conversation']['id']
        with self.http.store.connect() as c:
            c.execute('INSERT INTO chat_turns VALUES (?,?,?)',('synthetic-legacy',self.pid,json.dumps(dict(id='synthetic-legacy',conversation_id=cid,status='queued'))))
        self.assertEqual(self.schedule(NEXT,0)[0],400)
        self.assertNotIn('pending_chat_selection',self.project()['active_conversation'])
        self.assertEqual(self.keys,[])

    def test_running_reservation_keeps_current_request_and_applies_once(self):
        preview=self.preview();self.assertEqual(self.approve(preview)[0],200)
        original_open=self.socket.open
        def reserve_during_message(request,timeout):
            if not request.full_url.endswith('count_tokens'):
                self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'running')
                self.assertEqual(self.schedule(NEXT,0)[0],200)
            return original_open(request,timeout)
        self.socket.open=reserve_during_message
        self.process()
        self.assertEqual(self.project()['effective_chat_selection'],NEXT)
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'completed')
        self.assertEqual(len(self.socket.requests),2)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())

    def test_unknown_restart_and_cancel_requested_preserve_reservation(self):
        preview=self.preview();status,result=self.approve(preview)
        tid=result['turn']['id']
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        with self.http.store.connect() as c:
            turn=chat_general.get_row(c,'general_chat_turns',tid)
            turn['status']='cancel_requested';chat_general.put(c,'general_chat_turns',turn)
        self.assertEqual(self.schedule(INITIAL,1)[0],400)
        with self.http.store.connect() as c:chat_general.recover(c)
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'outcome_unknown')
        self.assertEqual(self.project()['effective_chat_selection'],INITIAL)
        self.assertEqual(self.schedule(INITIAL,1)[0],400)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.socket.requests,[])

    def test_before_message_failure_keeps_pending_until_explicit_choice(self):
        preview=self.preview();self.assertEqual(self.approve(preview)[0],200)
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        self.key_error=RuntimeError('synthetic missing key')
        self.process()
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'blocked_before_message')
        self.assertEqual(self.project()['effective_chat_selection'],INITIAL)
        self.assertEqual(self.action('general_chat_preview',song='A',prompt='새 요청',maximum_micro=10000,total_maximum_micro=10000)[0],400)
        self.assertEqual(self.schedule(INITIAL,1)[0],200)
        self.assertEqual(self.socket.requests,[])

    def test_pending_binding_mismatch_blocks_before_any_provider_request(self):
        for field,value in (('after_turn','different'),('execution_model_revision',99),('reserved_model_revision',99),('execution_run','different'),('execution_selection',NEXT)):
            with self.subTest(field=field):
                preview=self.preview();status,result=self.approve(preview)
                tid=result['turn']['id']
                revision=self.project()['active_conversation']['model_revision']
                self.assertEqual(self.schedule(NEXT,revision)[0],200)
                with self.http.store.connect() as c:
                    row=c.execute('SELECT body FROM state WHERE id=1').fetchone()
                    state=json.loads(row[0]);session=state['projects']['A']['chat_sessions'][0]
                    session['pending_chat_selection'][field]=value
                    c.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(state),))
                self.process()
                self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'blocked_before_message')
                self.assertEqual(self.schedule(INITIAL,revision+1)[0],200)
        self.assertEqual(self.keys,[])
        self.assertEqual(self.socket.requests,[])

    def test_total_budget_limit_keeps_pending_and_requires_explicit_reselection(self):
        # The actual first tool response consumes part of the one-round budget,
        # leaving too little for another reservation. No terminal status is seeded.
        estimate=self.preview()
        self.post('general_chat_decide',song='A',preview_id=estimate['id'],manifest_sha256=estimate['manifest_sha256'],decision='reject',rights_confirmed=False)
        preview=self.post('general_chat_preview',song='A',prompt='현재 작품을 확인해줘',maximum_micro=10000,total_maximum_micro=estimate['reserve_micro'])['general_chat_preview']
        self.socket.replies=[activation.reply([activation.use('context','search_project_context',{'query':'현재 작품'})],'tool_use')]
        status,result=self.approve(preview)
        self.assertEqual(status,200,result)
        tid=result['turn']['id']
        with self.http.store.connect() as c:
            original=chat_general.get_row(c,'general_chat_previews',preview['id'])
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        reserved=self.project()['active_conversation']['pending_chat_selection']
        self.process()
        project=self.project();turn,reservation,attempts=self.reservation(tid)
        self.assertEqual(turn['status'],'limit_reached')
        self.assertGreater(turn['estimated_used_micro'],0)
        self.assertEqual(turn['total_maximum_micro'],preview['reserve_micro'])
        self.assertEqual(turn['binding'],original['binding'])
        self.assertEqual(project['effective_chat_selection'],INITIAL)
        self.assertEqual(project['active_conversation']['pending_chat_selection'],reserved)
        self.assertFalse(project['general_chat_connection']['new_preview_available'])
        self.assertEqual(project['general_chat_previews'],[])
        with self.http.store.connect() as c:
            self.assertEqual(chat_general.get_row(c,'general_chat_previews',preview['id']),original)
        self.assertEqual(len(self.socket.requests),2)
        self.assertEqual(hashlib.sha256(self.socket.requests[0][1]).hexdigest(),original['count_wire_sha256'])
        self.assertEqual(hashlib.sha256(self.socket.requests[1][1]).hexdigest(),original['message_wire_sha256'])
        budget=self.state()['budgets']
        self.assertEqual(self.action('general_chat_preview',song='A',prompt='새 요청',maximum_micro=10000,total_maximum_micro=10000)[0],400)
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.schedule(INITIAL,1)[0],200)
        self.assertNotIn('pending_chat_selection',self.project()['active_conversation'])
        self.assertTrue(self.project()['general_chat_connection']['new_preview_available'])
        self.preview()
        self.assertEqual(self.state()['budgets'],budget)
        self.assertEqual(self.reservation(tid),(turn,reservation,attempts))
        self.assertEqual(len(self.socket.requests),2)

    def test_rejected_continuation_retains_pending(self):
        self.socket.replies=[activation.reply([activation.use('context','search_project_context',{'query':'현재 작품'})],'tool_use')]
        preview=self.preview();self.assertEqual(self.approve(preview)[0],200)
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        self.process()
        following=self.project()['general_chat_previews'][-1]
        self.post('general_chat_decide',song='A',preview_id=following['id'],manifest_sha256=following['manifest_sha256'],decision='reject',rights_confirmed=False)
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'],'continuation_rejected')
        self.assertEqual(self.project()['effective_chat_selection'],INITIAL)
        self.assertIn('pending_chat_selection',self.project()['active_conversation'])
        self.assertFalse(self.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(self.socket.requests),2)

    def test_normal_selection_change_invalidates_unapproved_preview(self):
        preview=self.preview()
        self.assertEqual(self.schedule(NEXT,0)[0],200)
        self.assertEqual(self.schedule(INITIAL,1)[0],200)
        self.assertEqual(self.approve(preview)[0],400)
        self.assertEqual(self.socket.requests,[])
