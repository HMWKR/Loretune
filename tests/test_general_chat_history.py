"""Independent general turns retain scoped request evidence over real local HTTP."""
import json
from copy import deepcopy
import chat_general
import unittest
from tests import test_general_chat_activation as fixture
reply=fixture.reply


class GeneralChatHistoryTest(unittest.TestCase):
    setUp=fixture.GeneralChatActivationHTTPTest.setUp
    close=fixture.GeneralChatActivationHTTPTest.close
    request=fixture.GeneralChatActivationHTTPTest.request
    state=fixture.GeneralChatActivationHTTPTest.state
    project=fixture.GeneralChatActivationHTTPTest.project
    action=fixture.GeneralChatActivationHTTPTest.action
    post=fixture.GeneralChatActivationHTTPTest.post
    budget=fixture.GeneralChatActivationHTTPTest.budget
    preview=fixture.GeneralChatActivationHTTPTest.preview
    approve=fixture.GeneralChatActivationHTTPTest.approve
    process=fixture.GeneralChatActivationHTTPTest.process
    reservation=fixture.GeneralChatActivationHTTPTest.reservation

    def seed(self, prompts, **changes):
        source=self.preview();bound=source['binding']
        with self.http.store.connect() as c:
            for i,prompt in enumerate(prompts):
                item=dict(id='seed-'+str(i),binding=deepcopy(bound),prompt=prompt,
                          status='completed',answer='Public answer '+str(i),**changes)
                chat_general.put(c,'general_chat_turns',item)
                approved=deepcopy(chat_general.get_row(c,'general_chat_previews',source['id']))
                approved.update(id='accepted-'+str(i),state='consumed',rights_confirmed=True,
                                turn_id=item['id'],prompt=prompt)
                chat_general.put(c,'general_chat_previews',approved)

    def snapshot(self, preview):
        with self.http.store.connect() as c:
            return chat_general.get_row(c,'general_chat_previews',preview['id'])['history_snapshot']
    def test_independent_turn_retains_previous_request(self):
        first = self.preview()
        status, accepted = self.approve(first)
        self.assertEqual(status, 200, accepted)
        self.process()
        second = self.preview()
        self.assertEqual(second['history_context']['request_count'], 1)
        self.assertEqual(second['history_context']['answer_count'], 1)
        self.assertIn(first['prompt'], second['message_body']['messages'][0]['content'])
        self.socket.replies = [reply()]
        self.assertEqual(self.approve(second)[0], 200)
        self.process()
        sent = json.loads(self.socket.requests[-1][1])
        self.assertEqual(sent, second['message_body'])

    def test_all_requests_recent_eight_answers_and_verbatim_corrections(self):
        prompts=['Never orbit.', 'Quotation: "orbit" is a bad example.',
                 'Correction: only scene 1.', 'Withdraw scene 1 prohibition.']+['Request '+str(i) for i in range(6)]
        self.seed(prompts)
        preview=self.preview();snapshot=self.snapshot(preview)
        records=snapshot['request_history']['requests']
        self.assertEqual([r['text'] for r in records],prompts)
        self.assertEqual([r['sequence'] for r in records],list(range(1,11)))
        self.assertEqual([a['text'] for a in snapshot['public_answers']],['Public answer '+str(i) for i in range(2,10)])
        self.assertTrue(all(a['review']=='unreviewed' and not a['canon'] for a in snapshot['public_answers']))
        self.assertEqual(preview['history_context'],dict(request_count=10,answer_count=8,sha256=chat_general.digest(snapshot)))
        self.assertEqual(preview['count_body']['messages'],preview['message_body']['messages'])
        self.assertNotIn('active_constraints',json.dumps(snapshot))

    def test_scope_and_unapproved_preview_exclusion(self):
        empty=self.preview()
        self.preview() # another pending preview is not accepted request history
        self.seed(['Accepted'])
        with self.http.store.connect() as c:
            base=chat_general.get_row(c,'general_chat_turns','seed-0')
            for key in ('workspace','project','conversation'):
                other=deepcopy(base);other['id']='other-'+key;other['binding'][key]='other';other['prompt']='LEAK-'+key
                chat_general.put(c,'general_chat_turns',other)
            draft=deepcopy(base);draft.update(id='draft',prompt='DRAFT-LEAK');chat_general.put(c,'general_chat_turns',draft)
            c.execute('INSERT INTO chat_turns (id,project,body) VALUES (?,?,?)',('legacy',self.pid,json.dumps(dict(id='legacy',status='completed',prompt='LEGACY-LEAK'))))
        current=self.preview();records=self.snapshot(current)['request_history']['requests']
        self.assertEqual([r['text'] for r in records],['Accepted'])
        self.assertEqual(empty['history_context']['request_count'],0)
        self.assertNotIn('LEAK',json.dumps(current))

    def test_second_pending_preview_rejected_after_completed_turn(self):
        first=self.preview();stale=self.preview()
        self.assertEqual(self.approve(first)[0],200);self.process()
        status,result=self.approve(stale)
        self.assertEqual(status,400,result)
        self.assertIn('이전 대화',json.dumps(result,ensure_ascii=False))

    def test_history_mutation_after_count_stops_message(self):
        self.seed(['Approved prior request'])
        preview=self.preview();status,result=self.approve(preview);self.assertEqual(status,200,result)
        original=self.socket.open
        def mutate(request,timeout):
            response=original(request,timeout)
            if request.full_url.endswith('count_tokens'):
                with self.http.store.connect() as c:
                    old=chat_general.get_row(c,'general_chat_turns','seed-0');old['prompt']='changed'
                    chat_general.put(c,'general_chat_turns',old)
            return response
        self.socket.open=mutate
        self.process()
        self.assertEqual(len(self.socket.requests),1)
        turn,_,_=self.reservation(result['turn']['id'])
        self.assertNotEqual(turn['status'],'completed')

    def test_manifest_history_and_message_tamper_rejected(self):
        for field in ('history_snapshot','history_context','message_body'):
            preview=self.preview()
            with self.http.store.connect() as c:
                saved=chat_general.get_row(c,'general_chat_previews',preview['id'])
                saved[field]['tamper']=True
                chat_general.put(c,'general_chat_previews',saved)
            self.assertEqual(self.approve(preview)[0],400)
        self.assertEqual((self.keys,self.socket.requests),([],[]))

    def test_oversized_history_rejected_before_credentials_and_network(self):
        self.seed(['가'*1900 for _ in range(15)])
        status,result=self.action('general_chat_preview',song='A',prompt='Continue',maximum_micro=10000,total_maximum_micro=10000)
        self.assertEqual(status,400,result)
        self.assertEqual((self.keys,self.socket.requests),([],[]))

    def test_continuation_inherits_snapshot_and_lookup_marker(self):
        self.seed(['Keep the camera still'])
        self.socket.replies=[reply([fixture.use('lookup','search_project_context',{'query':'music'})],'tool_use'),reply()]
        preview=self.preview();status,result=self.approve(preview);self.assertEqual(status,200,result)
        self.process()
        turn,_,_=self.reservation(result['turn']['id'])
        self.assertEqual(turn['status'],'awaiting_continuation_approval')
        with self.http.store.connect() as c:
            following=chat_general.get_row(c,'general_chat_previews',turn['preview_id'])
        self.assertEqual(following['history_snapshot'],self.snapshot(preview))
        self.assertEqual(following['history_context'],preview['history_context'])
        self.assertGreaterEqual(following['music_context']['message_index'],3)
        self.assertEqual(self.approve(following)[0],200)
        self.process()
        turn,_,_=self.reservation(result['turn']['id']);self.assertEqual(turn['status'],'completed')

    def test_old_preview_keeps_exact_body_without_retroactive_injection(self):
        preview=self.preview()
        with self.http.store.connect() as c:
            old=chat_general.get_row(c,'general_chat_previews',preview['id'])
            old.pop('history_snapshot');old.pop('history_context')
            old['manifest_sha256']=chat_general.manifest_digest(old)
            chat_general.put(c,'general_chat_previews',old)
        self.seed(['New historical content'])
        self.assertEqual(self.approve(old)[0],200)
        self.process()
        self.assertEqual(json.loads(self.socket.requests[-1][1]),preview['message_body'])
        self.assertNotIn('New historical content',self.socket.requests[-1][1].decode())

    def test_cancelled_accepted_request_preserved_without_answer(self):
        first=self.preview();status,result=self.approve(first);self.assertEqual(status,200,result)
        self.post('general_chat_cancel',song='A',turn=result['turn']['id'])
        current=self.preview();snapshot=self.snapshot(current)
        self.assertEqual(current['history_context']['request_count'],1)
        self.assertEqual(current['history_context']['answer_count'],0)
        self.assertEqual(snapshot['request_history']['requests'][0]['status'],'cancelled')

    def test_changed_history_after_approval_prevents_count_and_credentials(self):
        self.seed(['Prior request'])
        preview=self.preview();status,result=self.approve(preview);self.assertEqual(status,200,result)
        with self.http.store.connect() as c:
            previous=chat_general.get_row(c,'general_chat_turns','seed-0')
            previous['answer']='Changed public answer';chat_general.put(c,'general_chat_turns',previous)
        self.process()
        self.assertEqual((self.keys,self.socket.requests),([],[]))
        turn,_,_=self.reservation(result['turn']['id']);self.assertEqual(turn['status'],'blocked_before_message')

    def test_changed_history_after_message_prevents_tool_effect(self):
        self.seed(['Prior request'])
        self.socket.replies=[reply([fixture.use('lookup','search_project_context',{'query':'music'})],'tool_use')]
        preview=self.preview();status,result=self.approve(preview);self.assertEqual(status,200,result)
        original=self.socket.open
        def mutate(request,timeout):
            response=original(request,timeout)
            if not request.full_url.endswith('count_tokens'):
                with self.http.store.connect() as c:
                    previous=chat_general.get_row(c,'general_chat_turns','seed-0')
                    previous['answer']='Changed public answer';chat_general.put(c,'general_chat_turns',previous)
            return response
        self.socket.open=mutate
        self.process()
        turn,_,_=self.reservation(result['turn']['id'])
        self.assertNotEqual(turn['status'],'completed')
        run=next(r for r in self.project()['production_runs'] if r['id']==turn['run'])
        self.assertEqual(run.get('calls',[]),[])
