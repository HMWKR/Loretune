"""Music-first model context through isolated real HTTP; no provider calls."""
import base64
import io
import json
import math
import shutil
import struct
import subprocess
import unittest
import uuid
import wave
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import chat_general
import editing
from tests import test_chat_general_http as http_fixture
from tests.test_chat_runtime import response, use


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'media inspection tools required')
class MusicInputContextTest(unittest.TestCase):
    def setUp(self):
        self.f = http_fixture.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)

    def post(self, action, *, song='A', conversation=None, **data):
        send = self.f.action if conversation is None else lambda a, **d: self.f.session_action(conversation, a, **d)
        status, result = send(action, song=song, **data)
        self.assertEqual(status, 200, result)
        return result

    def project(self):
        return self.f.state()['projects']['A']

    def context(self, *, song='A', conversation=None):
        handoff = self.post('model_handoff', song=song, conversation=conversation)['handoff']['execution_targets']
        run = self.post('production_run', song=song, conversation=conversation)['run']['id']
        lookup = self.post('production_tool', song=song, conversation=conversation, run=run,
                           call=dict(id=uuid.uuid4().hex, name='search_project_context',
                                     arguments={'query': '현재 음원과 확인한 사용 구간'}, complete=True))['tool']
        self.assertEqual(lookup['status'], 'succeeded')
        self.assertEqual(lookup['execution_targets'], handoff)
        return lookup['execution_targets']

    def upload(self, duration=3, *, song='A', conversation=None):
        data = io.BytesIO()
        with wave.open(data, 'wb') as wav:
            wav.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
            wav.writeframes(b''.join(struct.pack('<h', int(1000 * math.sin(i * math.tau * 440 / 8000)))
                                     for i in range(8000 * duration)))
        self.post('audio', song=song, conversation=conversation, filename='private-original-name.wav',
                  content=base64.b64encode(data.getvalue()).decode(), rights='직접 만든 합성 검증 음원')
        return self.f.state()['projects'][song]['audio_selected']

    def lookup_follow(self):
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('music-current', 'search_project_context', {'query': '현재 음원'})], 'tool_use'), response()]
        first = self.f.preview()
        status, result = self.f.approve(first)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        return self.project()['general_chat_previews'][-1]

    def disclosed_music(self, preview):
        blocks = [block for message in preview['message_body']['messages'] for block in message['content']
                  if isinstance(block, dict) and block.get('type') == 'tool_result']
        return json.loads(blocks[-1]['content'])['execution_targets']['music_input']

    def change_fixture(self, change):
        with self.f.http.store.connect() as c:
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            state = json.loads(body)
            change(state['projects']['A'])
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (revision + 1, json.dumps(state)))

    def save_picture_timeline(self):
        image = Path(self.f.tmp.name) / 'fixture.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=32x32',
                        '-frames:v', '1', str(image)], check=True)
        self.post('shot', shot='picture', description='선택 사진을 사용한 장면')
        self.post('take', shot='picture', shot_revision=0, filename='fixture.png',
                  content=base64.b64encode(image.read_bytes()).decode(), reason='선택 사진', rights='직접 제작')
        self.post('select', shot='picture', take=1, shot_revision=1)
        timeline = editing.current(self.project())
        self.post('timeline', timeline=timeline)

    def test_no_audio_is_explicit_without_manufactured_range_or_approval(self):
        targets = self.context()
        self.assertEqual(targets['music_input']['scope'], 'current-project-shared')
        self.assertIsNone(targets['music_input']['selected_source'])
        self.assertIsNone(targets['music_input']['timeline_source'])
        self.assertEqual(targets['music_input']['range'], {'status': 'unconfirmed'})
        self.assertTrue(targets['music_input']['requires_revalidation'])
        self.assertIsNone(targets['timeline']['grant_id'])

    def test_upload_only_discloses_inspected_duration_without_paths_or_implicit_range(self):
        self.upload()
        before = self.project()
        targets = self.context()
        music = targets['music_input']
        selected = music['selected_source']
        self.assertEqual(selected['audio_version'], 1)
        self.assertAlmostEqual(selected['duration_seconds'], 3, places=2)
        self.assertEqual(selected['metadata_status'], 'recorded')
        self.assertEqual(selected['rights_status'], 'recorded')
        self.assertFalse(selected['blocked'])
        self.assertEqual(music['timeline_source'], selected)
        self.assertEqual(music['range'], {'status': 'unconfirmed'})
        self.assertNotIn('private-original-name', json.dumps(music))
        self.assertNotIn(str(self.f.http.store.root), json.dumps(music))
        self.assertIsNone(targets['timeline']['grant_id'])
        after = self.project()
        for key in ('audio_versions', 'audio_selected', 'music_head', 'timeline_versions'):
            self.assertEqual(after.get(key), before.get(key))
        self.assertEqual(self.f.state()['jobs'], [])

    def test_confirmed_range_remains_bound_to_its_audio_when_selected_and_timeline_diverge(self):
        self.upload()
        self.post('music_structure', audio=1, start=.25, end=2.5, sections=[])
        self.save_picture_timeline()
        old = self.context()['music_input']
        self.assertEqual(old['range']['status'], 'confirmed')
        self.assertEqual(old['range']['source'], 'user')
        self.assertEqual((old['range']['start_seconds'], old['range']['end_seconds']), (.25, 2.5))
        self.assertTrue(old['range']['matches_selected_source'])
        self.assertTrue(old['range']['matches_timeline_source'])
        self.upload(duration=4)
        targets = self.context()
        music = targets['music_input']
        self.assertEqual(music['selected_source']['audio_version'], 2)
        self.assertAlmostEqual(music['selected_source']['duration_seconds'], 4, places=2)
        self.assertEqual(music['timeline_source']['audio_version'], 1)
        self.assertEqual(targets['timeline']['audio_version'], 1)
        self.assertEqual(music['range']['audio_version'], 1)
        self.assertEqual(music['range']['status'], 'confirmed')
        self.assertFalse(music['range']['matches_selected_source'])
        self.assertTrue(music['range']['matches_timeline_source'])
        self.assertIsNone(targets['timeline']['grant_id'])

    def test_bad_duration_and_extra_fields_are_not_forwarded_and_rights_are_rechecked(self):
        self.upload()
        self.save_picture_timeline()
        timeline = editing.current(self.project())
        timeline['audio'] = None
        self.post('timeline', timeline=timeline)
        private = 'https://private.invalid/secret-token'
        for invalid in (None, True, '3', -1, 0, float('inf'), float('nan'), {'secret': private}):
            with self.subTest(duration=repr(invalid)):
                def poison(p):
                    p['audio_versions'][0]['metadata'] = {'duration': invalid, 'provider_url': private, 'raw': private}
                    p['audio_versions'][0]['rights'] = private * 20
                self.change_fixture(poison)
                source = self.context()['music_input']['selected_source']
                self.assertIsNone(source['duration_seconds'])
                self.assertEqual(source['metadata_status'], 'unavailable')
                self.assertEqual(set(source), {'audio_version', 'duration_seconds', 'metadata_status', 'rights_status', 'blocked'})
                self.assertNotIn(private, json.dumps(source))
        self.change_fixture(lambda p: p['audio_versions'][0].update(metadata={'duration': 3}, rights='사용권 미확인'))
        sha = self.project()['audio_versions'][0]['sha256']
        self.post('asset_rights', sha256=sha, blocked=True, reason='fixture revoke')
        source = self.context()['music_input']['selected_source']
        self.assertEqual(source['rights_status'], 'unconfirmed')
        self.assertTrue(source['blocked'])
        self.change_fixture(lambda p: p.update(music_head=1, music_versions=[
            {'id': 1, 'audio': 1, 'start': 0, 'end': 4, 'source': 'user', 'private': private}]))
        invalid = self.context()['music_input']['range']
        self.assertEqual(invalid, {'status': 'invalid_record'})

    def test_shared_audio_is_visible_to_other_conversation_but_not_other_project(self):
        self.upload()
        original = self.context()['music_input']
        cid = self.post('conversation_create', title='같은 작품의 다음 대화')['conversation']['id']
        self.assertEqual(self.context(conversation=cid)['music_input'], original)
        status, result = self.f.action('project', name='B', era='default', story=0)
        self.assertEqual(status, 200, result)
        foreign = self.context(song='B')['music_input']
        self.assertIsNone(foreign['selected_source'])
        self.assertIsNone(foreign['timeline_source'])
        self.assertEqual(foreign['range'], {'status': 'unconfirmed'})

    def test_general_fixture_tool_result_requires_new_consent_and_carries_only_safe_music_facts(self):
        self.upload()
        expected = self.context()['music_input']
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('music-lookup', 'search_project_context', {'query': '현재 음원'})], 'tool_use'), response()]
        preview = self.f.preview()
        status, result = self.f.approve(preview)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        project = self.project()
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'awaiting_continuation_approval')
        self.assertEqual(len(transport.messages), 1)
        follow = project['general_chat_previews'][-1]
        results = [block for message in follow['message_body']['messages'] for block in message['content']
                   if isinstance(block, dict) and block.get('type') == 'tool_result']
        self.assertEqual(len(results), 1)
        payload = json.loads(results[0]['content'])
        self.assertEqual(payload['execution_targets']['music_input'], expected)
        self.assertNotIn('private-original-name', json.dumps(payload))
        self.assertIsNone(payload['context']['music'])
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages), 2)
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'], 'completed')
        self.assertEqual(self.f.state()['jobs'], [])
        self.assertEqual(transport.mode, 'contract-fake')

    def test_initial_prompt_only_preview_queries_latest_audio_after_source_change(self):
        self.upload()
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('fresh-music', 'search_project_context', {'query': '현재 음원'})], 'tool_use')]
        preview = self.f.preview()
        self.assertNotIn('music_input', json.dumps(preview['message_body']))
        self.upload(duration=4)
        status, result = self.f.approve(preview)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        follow = self.project()['general_chat_previews'][-1]
        blocks = [block for message in follow['message_body']['messages'] for block in message['content']
                  if isinstance(block, dict) and block.get('type') == 'tool_result']
        music = json.loads(blocks[0]['content'])['execution_targets']['music_input']
        self.assertEqual(music['selected_source']['audio_version'], 2)
        self.assertAlmostEqual(music['selected_source']['duration_seconds'], 4, places=2)
        self.assertEqual(music['range'], {'status': 'unconfirmed'})
        self.assertEqual(len(transport.messages), 1)

    def test_stale_follow_is_not_sent_and_explicit_new_lookup_sends_current_source(self):
        self.upload()
        self.upload(duration=4)
        follow = self.lookup_follow()
        self.assertEqual(self.disclosed_music(follow)['selected_source']['audio_version'], 2)
        self.assertIn('music_context', follow)
        transport = self.f.http.store.general_chat_runtime.transport
        self.upload(duration=5)
        with self.f.http.store.connect() as c:
            before = c.execute('SELECT count(*) FROM reservations').fetchone()[0]
        status, denied = self.f.approve(follow)
        self.assertEqual(status, 400)
        self.assertIn('다시 조회', denied['error'])
        self.assertEqual(len(transport.messages), 1)
        self.assertEqual(len(transport.counted), 1)
        with self.f.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM reservations').fetchone()[0], before)
        status, result = self.f.approve(follow, decision='reject')
        self.assertEqual(status, 200, result)
        fresh = self.lookup_follow()
        self.assertEqual(self.disclosed_music(fresh)['selected_source']['audio_version'], 3)
        status, result = self.f.approve(fresh)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(transport.messages[-1], fresh['message_body'])
        self.assertEqual(len(transport.messages), 3)
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'], 'completed')

    def test_shared_audio_change_after_approval_is_rechecked_before_count_or_message(self):
        self.upload()
        follow = self.lookup_follow()
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        cid = self.post('conversation_create', title='같은 작품의 음원 편집')['conversation']['id']
        self.upload(duration=4, conversation=cid)
        transport = self.f.http.store.general_chat_runtime.transport
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        turn = self.project()['general_chat_turns'][-1]
        self.assertEqual(turn['status'], 'blocked_before_message')
        self.assertIn('다시 조회', turn['error'])
        self.assertEqual(len(transport.messages), 1)
        self.assertEqual(len(transport.counted), 1)
        with self.f.http.store.connect() as c:
            saved = chat_general.get_row(c, 'general_chat_turns', turn['id'])
            self.assertEqual(c.execute('SELECT state FROM reservations WHERE id=?', (saved['reservation'],)).fetchone()[0], 'cancelled')

    def test_range_confirmation_stales_follow_but_foreign_project_audio_does_not(self):
        self.upload()
        follow = self.lookup_follow()
        status, result = self.f.action('project', name='B', era='default', story=0)
        self.assertEqual(status, 200, result)
        self.upload(duration=4, song='B')
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        second = self.lookup_follow()
        self.post('music_structure', audio=1, start=.25, end=2.5, sections=[])
        count = len(self.f.http.store.general_chat_runtime.transport.messages)
        status, denied = self.f.approve(second)
        self.assertEqual(status, 400)
        self.assertIn('다시 조회', denied['error'])
        self.assertEqual(len(self.f.http.store.general_chat_runtime.transport.messages), count)

    def test_audio_change_during_count_prevents_the_message_send(self):
        self.upload()
        follow = self.lookup_follow()
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        transport = self.f.http.store.general_chat_runtime.transport
        original = transport.count
        def count_then_change(body):
            tokens = original(body)
            self.upload(duration=4)
            return tokens
        with patch.object(transport, 'count', side_effect=count_then_change):
            self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.counted), 2)
        self.assertEqual(len(transport.messages), 1)
        turn = self.project()['general_chat_turns'][-1]
        self.assertEqual(turn['status'], 'blocked_before_message')
        self.assertIn('다시 조회', turn['error'])

    def after_claim_audio_change(self, *, timeout):
        self.upload()
        follow = self.lookup_follow()
        status, result = self.f.approve(follow)
        self.assertEqual(status, 200, result)
        turn_id = result['turn']['id']
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('stale-plan', 'propose_media_plan',
            dict(goal='예전 음원으로 제안', scenes='적용되면 안 되는 장면', style='', constraints='', kind='visualizer'))], 'tool_use')]
        original = transport.complete
        captured = {}
        before_calls = len(self.project()['production_runs'][-1]['calls'])
        def complete_after_change(body):
            with self.f.http.store.connect() as c:
                saved = chat_general.get_row(c, 'general_chat_turns', turn_id)
                reservation = saved['reservation']
                attempts = c.execute("SELECT id,job,state,request_hash,binding_hash FROM provider_attempts WHERE reservation=? AND operation='chat-message'", (reservation,)).fetchall()
                self.assertEqual(len(attempts), 1)
                attempt, job, state, request_hash, binding_hash = attempts[0]
                self.assertEqual((job, state), (turn_id, 'sending'))
                self.assertEqual(request_hash, follow['message_sha256'])
                self.assertEqual(binding_hash, follow['manifest_sha256'])
                captured.update(reservation=reservation, attempt=attempt,
                    amount=c.execute('SELECT amount FROM reservations WHERE id=?', (reservation,)).fetchone()[0], body=deepcopy(body))
            self.assertEqual(body, follow['message_body'])
            self.upload(duration=4)
            if timeout:raise TimeoutError('synthetic post-claim response loss')
            return original(body)
        with patch.object(transport, 'complete', side_effect=complete_after_change):
            self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(self.project()['audio_selected'], 2)
        self.assertEqual(self.project().get('guided_plans', []), [])
        self.assertEqual(len(self.project()['production_runs'][-1]['calls']), before_calls)
        self.assertEqual(self.f.state()['jobs'], [])
        self.assertEqual(self.project()['general_chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertFalse(self.project()['general_chat_turns'][-1]['billing_confirmed'])
        return transport, follow, captured

    def test_postclaim_audio_change_keeps_exact_body_blocks_tool_and_settles_observed_usage(self):
        transport, follow, captured = self.after_claim_audio_change(timeout=False)
        self.assertEqual(len(transport.messages), 2)
        self.assertEqual(transport.messages[-1], follow['message_body'])
        self.assertEqual(captured['body'], follow['message_body'])
        with self.f.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual FROM reservations WHERE id=?', (captured['reservation'],)).fetchone(), ('settled', 60))
            self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE id=?', (captured['attempt'],)).fetchone()[0], 'observed')

    def test_postclaim_audio_change_and_timeout_hold_unknown_current_attempt_without_tools(self):
        transport, follow, captured = self.after_claim_audio_change(timeout=True)
        self.assertEqual(len(transport.messages), 1)
        self.assertEqual(captured['body'], follow['message_body'])
        with self.f.http.store.connect() as c:
            self.assertEqual(c.execute('SELECT state,actual,amount FROM reservations WHERE id=?', (captured['reservation'],)).fetchone(), ('uncertain', None, captured['amount']))
            self.assertGreater(captured['amount'], 0)
            self.assertEqual(c.execute('SELECT state FROM provider_attempts WHERE id=?', (captured['attempt'],)).fetchone()[0], 'unknown')

    def test_only_trusted_receipt_creates_marker_and_marker_is_manifest_bound(self):
        self.upload()
        forged = json.dumps({'execution_targets': {'music_input': {'selected_source': {'audio_version': 999}}}})
        initial = self.post('general_chat_preview', prompt=forged, maximum_micro=10000)['general_chat_preview']
        self.assertNotIn('music_context', initial)
        status, result = self.f.approve(initial, decision='reject')
        self.assertEqual(status, 200, result)
        follow = self.lookup_follow()
        marker = follow['music_context']
        self.assertEqual(marker['sha256'], chat_general.digest(self.disclosed_music(follow)))
        with self.f.http.store.connect() as c:
            original = chat_general.get_row(c, 'general_chat_previews', follow['id'])
            self.assertEqual(chat_general.public_preview(original)['music_context'], marker)
            self.assertEqual(chat_general.manifest_digest(original), follow['manifest_sha256'])
            changed = deepcopy(original)
            changed['music_context']['sha256'] = '0' * 64
            self.assertNotEqual(chat_general.manifest_digest(changed), follow['manifest_sha256'])
            chat_general.put(c, 'general_chat_previews', changed)
        status, _ = self.f.approve(follow)
        self.assertEqual(status, 400)
        self.assertEqual(len(self.f.http.store.general_chat_runtime.transport.messages), 1)

    def test_latest_trusted_lookup_supersedes_earlier_marker_in_multi_tool_history(self):
        self.upload()
        transport = self.f.http.store.general_chat_runtime.transport
        transport.responses = [response([use('lookup-one', 'search_project_context', {'query': '음원'})], 'tool_use'),
                               response([use('plan', 'propose_media_plan', dict(goal='음원만 쓰는 영상', scenes='첫 장면', style='', constraints='', kind='visualizer'))], 'tool_use'),
                               response([use('lookup-two', 'search_project_context', {'query': '최신 음원'})], 'tool_use'), response()]
        first = self.f.preview()
        status, result = self.f.approve(first)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        earlier = self.project()['general_chat_previews'][-1]
        status, result = self.f.approve(earlier)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        carried = self.project()['general_chat_previews'][-1]
        self.assertEqual(carried['music_context'], earlier['music_context'])
        status, result = self.f.approve(carried)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        latest = self.project()['general_chat_previews'][-1]
        self.assertGreater(latest['music_context']['message_index'], earlier['music_context']['message_index'])
        self.assertNotEqual(latest['music_context']['call_id'], earlier['music_context']['call_id'])
        self.assertEqual(latest['music_context']['sha256'], earlier['music_context']['sha256'])
        status, result = self.f.approve(latest)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.f.http.store.general_chat_runtime.process_next())
        self.assertEqual(len(transport.messages), 4)
        self.assertEqual(transport.messages[-1], latest['message_body'])
