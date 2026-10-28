"""HTTP contract for a selected chat model's proposed plan; no provider calls."""
import base64
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import uuid
import wave
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import anthropic_ontology
import chat_runtime
import contracts
import model_selection
from app import Store, server
from editing import current
from tests.test_chat_runtime import ARGS, PROMPT, Fake, response, use


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg and FFprobe required')
class ChatToolHTTPFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.http = server(self.tmp.name, 0)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)
        self.base = f'http://127.0.0.1:{self.http.server_port}'
        self.action('project', name='A', era='default', story=0)
        self.action('project', name='B', era='default', story=0)
        self.action('model_settings', song='A', selections={'chat':'anthropic-haiku-5-5'}, model_revision=0)
        sound = io.BytesIO()
        with wave.open(sound, 'wb') as audio:
            audio.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
            audio.writeframes(b'\0\0' * 16000)
        self.action('audio', song='A', filename='synthetic.wav',
                    content=base64.b64encode(sound.getvalue()).decode(), rights='synthetic owned')
        self.action('music_structure', song='A', audio=1, start=0, end=2, sections=[])
        project = self.state()['projects']['A']
        self.cid = project['active_conversation']['id']
        self.adapter = Fake([response([use('plan', 'propose_media_plan', ARGS)], 'tool_use'), response()])
        approval = dict(model=anthropic_ontology.MODEL, workspace_id=self.http.store.workspace_id,
                        project_id=contracts.project_id(self.http.store.workspace_id, 'A'),
                        synthetic_only=True, expires=time.time()+300,
                        context_hash=model_selection.snapshot(project)['sha256'],
                        prompt_hashes=[hashlib.sha256(PROMPT.encode()).hexdigest()],
                        price_revision='haiku-5-5-20261027-tiered', max_rounds=3)
        self.runtime = chat_runtime.ChatRuntime(self.http.store, self.adapter, approval,
                                                Path(self.tmp.name)/'synthetic-usage.sqlite3')
        self.http.store.chat_runtime = self.runtime

    def shutdown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()

    def state(self, song=None, conversation=None):
        query = '?' + urlencode({'song':song, 'conversation':conversation}) if conversation else ''
        with urlopen(self.base+'/api/state'+query) as result:
            return json.load(result)

    def action(self, action, **data):
        state = self.state()
        payload = dict(action=action, data=data, revision=state['revision'], request_id=uuid.uuid4().hex)
        request = Request(self.base+'/api/action', data=json.dumps(payload).encode(),
                          headers={'Content-Type':'application/json', 'X-Loretune-Token':state['token']})
        try:
            with urlopen(request) as result:
                return result.status, json.load(result)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_over_limit_response_records_usage_without_executing_tool_or_next_round(self):
        upstream = response([use('plan', 'propose_media_plan', ARGS)], 'tool_use')
        upstream['usage'] = {'input_tokens': 100, 'output_tokens': 100000}
        self.adapter.responses = [upstream, response()]
        status, reply = self.action('chat_turn', song='A', prompt=PROMPT)
        self.assertEqual(status, 200, reply)
        self.assertTrue(self.runtime.process_next())
        project = self.state('A', self.cid)['projects']['A']
        turn = project['chat_turns'][-1]
        self.assertEqual(turn['status'], 'response_validation_failed')
        self.assertEqual(turn['steps'][0]['failure']['category'], 'usage_limit_exceeded')
        self.assertEqual(turn['steps'][0]['usage']['output_tokens'], 100000)
        self.assertEqual(turn['usage_cost_usd'], '0.05001')
        self.assertFalse(turn['billing_confirmed'])
        self.assertFalse(project.get('guided_plans'))
        self.assertEqual(len(self.adapter.messages), 1)
        self.assertFalse(self.runtime.process_next())
        import sqlite3
        with closing(sqlite3.connect(self.runtime.journal.path)) as conn:
            row = conn.execute('SELECT state, actual_micro, metadata FROM trials').fetchone()
        self.assertEqual(row[0:2], ('response_validation_failed', 50010))
        self.assertEqual(json.loads(row[2])['failure']['category'], 'usage_limit_exceeded')

    def test_unsettled_response_blocks_repeat_over_http_and_keeps_reservation(self):
        upstream = response([use('plan', 'propose_media_plan', ARGS)], 'tool_use')
        upstream.pop('usage')
        self.adapter.responses = [upstream]
        status, reply = self.action('chat_turn', song='A', prompt=PROMPT)
        self.assertEqual(status, 200, reply)
        self.assertTrue(self.runtime.process_next())
        turn = self.state('A', self.cid)['projects']['A']['chat_turns'][-1]
        self.assertEqual(turn['status'], 'outcome_unknown')
        self.assertEqual(turn['steps'][0]['failure']['category'], 'usage_unsettled')
        self.assertFalse(turn['billing_confirmed'])
        status, reply = self.action('chat_turn', song='A', prompt=PROMPT)
        self.assertEqual(status, 400, reply)
        self.assertEqual(len(self.adapter.messages), 1)
        self.assertFalse(self.runtime.process_next())
        import sqlite3
        with closing(sqlite3.connect(self.runtime.journal.path)) as conn:
            row = conn.execute('SELECT state, held_micro, actual_micro FROM trials').fetchone()
        self.assertEqual(row, ('outcome_unknown', 2458, None))

    def test_selected_fake_chat_plan_is_saved_then_applied_by_human_and_reopened(self):
        status, reply = self.action('chat_turn', song='A', prompt='unapproved input')
        self.assertEqual(status, 400, reply)
        self.assertEqual(self.adapter.counts, [])
        status, reply = self.action('chat_turn', song='B', prompt=PROMPT)
        self.assertEqual(status, 400, reply)
        self.assertEqual(self.adapter.counts, [])

        status, reply = self.action('chat_turn', song='A', prompt=PROMPT)
        self.assertEqual(status, 200, reply)
        turn_id = reply['chat_turn']['id']
        self.assertTrue(self.runtime.process_next())
        self.assertFalse(self.runtime.process_next())
        project = self.state('A', self.cid)['projects']['A']
        self.assertEqual(project['chat_turns'][-1]['id'], turn_id)
        self.assertEqual(project['chat_turns'][-1]['status'], 'completed')
        self.assertEqual(project['effective_chat_selection'], 'anthropic-haiku-5-5')
        self.assertEqual(len(self.adapter.messages), 2)
        self.assertEqual(len(project['guided_plans']), 1)
        plan = project['guided_plans'][0]
        self.assertEqual(plan['status'], 'proposed')
        self.assertEqual(plan['source']['mode'], 'contract-fake')
        self.assertFalse(project['shots'])
        self.assertFalse(self.state()['generation_jobs'])

        status, reply = self.action('apply_guided_plan', song='A', plan=plan['id'])
        self.assertEqual(status, 200, reply)
        reopened = Store(self.tmp.name).state({'A':self.cid})['projects']['A']
        saved = reopened['guided_plans'][0]
        self.assertEqual(saved['status'], 'applied')
        self.assertEqual(saved['approval']['actor'], 'local-owner')
        self.assertFalse(saved['approval']['cost_approval'])
        self.assertEqual(reopened['shots'][saved['shots'][0]]['description'], ARGS['scenes'])
        self.assertEqual(reopened['music_versions'][-1]['audio'], 1)
        self.assertEqual(len(Store(self.tmp.name).state()['projects']['B']['shots']), 0)

    def test_fake_chat_edit_requires_human_review_and_outputs_approved_version(self):
        image = Path(self.tmp.name)/'synthetic.png'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=64x64',
                        '-frames:v','1',str(image)],check=True)
        for name in ('first','second'):
            self.assertEqual(self.action('shot', song='A', shot=name, description=name)[0], 200)
            self.assertEqual(self.action('take', song='A', shot=name, shot_revision=0,
                                         filename='synthetic.png', content=base64.b64encode(image.read_bytes()).decode(),
                                         reason='synthetic fixture', rights='synthetic owned')[0], 200)
            self.assertEqual(self.action('select', song='A', shot=name, take=1, shot_revision=1)[0], 200)
            self.assertEqual(self.action('review_take', song='A', shot=name, take=1,
                                         decision='approved', reason='synthetic fixture reviewed')[0], 200)
        timeline = current(self.state()['projects']['A'])
        for clip in timeline['clips']:
            clip['duration'] = 1
        timeline.update(audio=1, audio_offset=0, subtitles=[], profile='preview')
        self.assertEqual(self.action('timeline', song='A', timeline=timeline)[0], 200)
        self.assertEqual(self.action('approve_timeline', song='A')[0], 200)
        project = self.state()['projects']['A']
        original = project['timeline_versions'][0]
        args = dict(description='한글 자막과 컷 순서 변경 검토', timeline_version=1,
                    commands=[dict(op='reorder_clips', order=[1,0]),
                              dict(op='set_captions', cues=[dict(start=0,end=1,text='새 한글 자막')]),
                              dict(op='set_audio_offset', audio_version=1, source_offset_seconds=.25)])
        self.adapter = Fake([response([use('edit','propose_timeline_changes',args)],'tool_use'),response()])
        approval = dict(self.runtime.approval, context_hash=model_selection.snapshot(project)['sha256'])
        self.runtime = chat_runtime.ChatRuntime(self.http.store,self.adapter,approval,
                                                Path(self.tmp.name)/'edit-usage.sqlite3')
        self.http.store.chat_runtime = self.runtime
        self.assertEqual(self.action('chat_turn', song='A', prompt=PROMPT)[0], 200)
        self.assertTrue(self.runtime.process_next())
        proposed = self.state('A',self.cid)['projects']['A']
        self.assertEqual(proposed['chat_turns'][-1]['status'],'completed')
        self.assertEqual(proposed['timeline_versions'][0],original)
        self.assertEqual(proposed['timeline_head'],1)
        proposal = proposed['timeline_edit_proposals'][0]
        self.assertEqual(proposal['status'],'proposed')
        self.assertFalse(proposal.get('output_approved',False))
        status,reply=self.action('review_timeline_proposal',song='A',proposal_id=proposal['id'],
                                 timeline_version=1,decision='approved')
        self.assertEqual(status,200,reply)
        changed=self.state()['projects']['A']
        self.assertEqual(changed['timeline_versions'][0],original)
        edited=changed['timeline_versions'][-1]
        self.assertEqual([x['shot'] for x in edited['clips']],['second','first'])
        self.assertEqual(edited['audio_offset'],.25)
        self.assertEqual(edited['subtitles'][0]['text'],'새 한글 자막')
        self.assertNotIn('approval',edited)
        self.assertEqual(self.action('approve_timeline',song='A')[0],200)
        status,reply=self.action('render_job',song='A')
        self.assertEqual(status,200,reply)
        self.assertTrue(self.http.store.process_next())
        reopened=Store(self.tmp.name).state({'A':self.cid})
        job=next(j for j in reopened['jobs'] if j['id']==reply['job'])
        self.assertEqual(job['status'],'completed',job.get('error'))
        self.assertEqual(job['snapshot']['timeline']['id'],2)
        self.assertEqual(job['verified']['streams'],['video','audio','subtitle'])
        with urlopen(self.base+job['download']) as result:
            downloaded=result.read()
        self.assertEqual(hashlib.sha256(downloaded).hexdigest(),job['sha256'])
        output=Path(self.tmp.name)/'exports'/(job['id']+'.mp4')
        streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))['streams']
        self.assertCountEqual([stream['codec_type'] for stream in streams],['video','audio','subtitle'])
        captions=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-map','0:s:0','-f','srt','-']).decode()
        self.assertIn('새 한글 자막',captions)
        self.assertEqual(reopened['projects']['A']['timeline_versions'][0],original)


if __name__ == '__main__':
    unittest.main()
