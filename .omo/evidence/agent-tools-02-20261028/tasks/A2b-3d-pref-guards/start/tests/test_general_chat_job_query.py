"""General chat get_generation_job over isolated HTTP/SQLite; no model or provider calls."""
import hashlib
import json
import time
import unittest
import uuid
from unittest.mock import patch

import chat_general
from tests import test_chat_general_http as base
from tests.test_chat_runtime import response, use

# A read turn may only change its own conversation bookkeeping: the turn, its
# previews, the chat-budget ledger rows, the request receipt and the run.
TURN_TABLES = {'audit', 'general_chat_previews', 'general_chat_turns', 'ledger_events', 'ledger_requests',
               'provider_attempts', 'requests', 'reservations', 'state'}
TURN_PROJECT_KEYS = {'production_runs', 'conversation_owners', 'chat_sessions'}


def fingerprint(store):
    with store.connect() as c:
        tables = {}
        for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            rows = sorted(repr(row) for row in c.execute('SELECT * FROM "'+table+'"'))
            tables[table] = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
        state = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        media_reservations = c.execute("SELECT count(*) FROM reservations r JOIN budgets b ON b.id=r.budget "
                                       "WHERE b.scope LIKE 'project:%'").fetchone()[0]
    for project in state['projects'].values():
        for key in TURN_PROJECT_KEYS:project.pop(key, None)
    return dict(tables=tables, state=state, media_reservations=media_reservations)


def assert_only_turn_changed(test, before, after):
    changed = {k for k in set(before['tables']) | set(after['tables']) if before['tables'].get(k) != after['tables'].get(k)}
    test.assertTrue(changed <= TURN_TABLES, changed)
    test.assertEqual(before['state'], after['state'])
    test.assertEqual(after['media_reservations'], before['media_reservations'])


class GeneralChatJobQueryTest(unittest.TestCase):
    def setUp(self):
        self.f = base.GeneralChatHTTPTest('test_preview_approval_tool_and_continuation_require_distinct_consent')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.store = self.f.http.store

    def post(self, action, **data):
        status, result = self.f.action(action, **data)
        self.assertEqual(status, 200, result)
        return result

    def project(self, cid=None):
        return (self.f.session_state(cid) if cid else self.f.state())['projects']['A']

    def insert_generation_job(self, identifier, grant='grant-secret-canary'):
        job = dict(id=identifier, state='imported', mode='contract-fake', external_calls=1, cost_confirmed=False,
                   asset_sha256='c'*64, quote=dict(money={'amount':'0.01','currency':'USD'}), updated=time.time(),
                   context=dict(song='A', output_kind='video',
                                action_binding=dict(workspace=self.store.workspace_id, project=self.f.pid,
                                                    action_id='action-'+identifier, plan_id='plan-'+identifier,
                                                    plan_revision=1, release_id='synthetic/model', grant_id=grant)))
        with self.store.connect() as c:
            c.execute('INSERT INTO generation_jobs (id,request_key,digest,body) VALUES (?,?,?,?)',
                      (identifier, 'fixture:'+identifier, 'fixture', json.dumps(job)))
        return job

    def insert_local_job(self, identifier, **extra):
        job = dict(id=identifier, revision=2, song='A', status='completed', progress=100, created=time.time(),
                   cancel_requested=False, snapshot=dict(shots={}), download='/exports/'+identifier+'.mp4', error=None,
                   sha256='d'*64, take=None, cost=dict(provider_calls=0, provider_cost=0, local_compute='미계측', kind='render-only'))
        job.update(extra)
        with self.store.connect() as c:
            c.execute('INSERT INTO jobs VALUES (?,?)', (identifier, json.dumps(job)))
        return job

    def send_tool(self, name, arguments, cid=None, preview=None):
        self.store.general_chat_runtime.transport.responses = [response([use('job-call', name, arguments)], 'tool_use')]
        if preview is None and cid is None:
            preview = self.f.preview()
        elif preview is None:
            status, result = self.f.session_action(cid, 'general_chat_preview', song='A', prompt='작업 상태 확인', maximum_micro=10000)
            self.assertEqual(status, 200, result)
            preview = result['general_chat_preview']
        if cid is None:
            status, result = self.f.approve(preview)
        else:
            status, result = self.f.session_action(cid, 'general_chat_decide', song='A', preview_id=preview['id'],
                                                   manifest_sha256=preview['manifest_sha256'], decision='approve', rights_confirmed=True)
        self.assertEqual(status, 200, result)
        self.assertTrue(self.store.general_chat_runtime.process_next())
        return self.project(cid)

    def tool_result(self, project):
        turn = project['general_chat_turns'][-1]
        self.assertEqual(turn['status'], 'awaiting_continuation_approval', turn)
        follow = project['general_chat_previews'][-1]
        blocks = [b for m in follow['message_body']['messages'] if isinstance(m.get('content'), list)
                  for b in m['content'] if b.get('type') == 'tool_result']
        return json.loads(blocks[-1]['content']), follow

    def reject(self, follow, cid=None):
        if cid is None:
            status, result = self.f.approve(follow, decision='reject')
        else:
            status, result = self.f.session_action(cid, 'general_chat_decide', song='A', preview_id=follow['id'],
                                                   manifest_sha256=follow['manifest_sha256'], decision='reject', rights_confirmed=False)
        self.assertEqual(status, 200, result)

    def test_owned_generation_job_is_read_without_grant_and_billing_stays_unconfirmed(self):
        self.insert_generation_job('job-owned')
        before = fingerprint(self.store)
        result, follow = self.tool_result(self.send_tool('get_generation_job', {'job_id':'job-owned'}))
        self.assertEqual(result['status'], 'succeeded')
        job = result['job']
        self.assertEqual((job['id'], job['state'], job['mode']), ('job-owned', 'imported', 'contract-fake'))
        self.assertIs(job['cost']['billing_confirmed'], False)
        self.assertNotIn('grant_id', job)
        self.assertNotIn('grant-secret-canary', json.dumps(result))
        self.assertNotIn('grant-secret-canary', json.dumps(follow['message_body']))
        assert_only_turn_changed(self, before, fingerprint(self.store))

    def test_local_render_and_3d_still_jobs_are_read_from_their_table(self):
        self.insert_local_job('render-job')
        self.insert_local_job('still-job', kind='local-3d-still', conversation_id=self.project()['active_conversation']['id'],
                              approval=dict(id='scene-grant-canary', actor='local-owner'),
                              cost=dict(provider_calls=0, provider_cost=0, local_compute='미계측', kind='local-3d-still'))
        before = fingerprint(self.store)
        expected = {'render-job':'local-render', 'still-job':'local-3d-still'}
        for identifier, mode in expected.items():
            with self.subTest(job=identifier):
                result, follow = self.tool_result(self.send_tool('get_generation_job', {'job_id':identifier}))
                self.assertEqual(result['status'], 'succeeded')
                self.assertEqual((result['job']['id'], result['job']['state'], result['job']['mode']), (identifier, 'completed', mode))
                self.assertEqual(result['job']['result']['sha256'], 'd'*64)
                self.assertEqual((result['job']['external_calls'], result['job']['result_approved']), (0, False))
                self.assertNotIn('grant_id', result['job'])
                self.assertNotIn('scene-grant-canary', json.dumps(follow['message_body']))
                self.reject(follow)
        assert_only_turn_changed(self, before, fingerprint(self.store))

    def test_unknown_and_foreign_job_are_not_found_in_any_conversation(self):
        self.insert_generation_job('job-default')
        result, follow = self.tool_result(self.send_tool('get_generation_job', {'job_id':'missing-job'}))
        self.assertEqual(result, {'status':'not_found'})
        self.reject(follow)
        cid = self.post('conversation_create', song='A', title='other')['conversation']['id']
        before = fingerprint(self.store)
        for identifier in ('missing-job', 'job-default'):
            with self.subTest(job=identifier):
                result, follow = self.tool_result(self.send_tool('get_generation_job', {'job_id':identifier}, cid=cid))
                self.assertEqual(result, {'status':'not_found'})
                self.reject(follow, cid)
        assert_only_turn_changed(self, before, fingerprint(self.store))

    def test_human_endpoint_keeps_foreign_job_guard_while_tool_returns_not_found(self):
        self.insert_generation_job('job-default')
        cid = self.post('conversation_create', song='A', title='other')['conversation']['id']
        status, result = self.f.session_action(cid, 'cancel_generation', song='A', job='job-default')
        self.assertEqual(status, 400, result)
        self.assertIn('다른 대화', json.dumps(result, ensure_ascii=False))
        status, value = self.f.session_action(cid, 'production_run', song='A')
        self.assertEqual(status, 200, value)
        run = value['run']['id']
        status, value = self.f.session_action(cid, 'production_tool', song='A', run=run,
            call=dict(id=uuid.uuid4().hex, name='get_generation_job', arguments={'job_id':'job-default'}, complete=True))
        self.assertEqual(status, 200, value)
        self.assertEqual(value['tool'], {'status':'not_found'})
        # Tools outside the moved set keep the preflight guard unchanged.
        plan = self.post('guided_plan', song='A', goal='g', scenes='s', kind='narrative')['plan']
        status, value = self.f.session_action(cid, 'production_tool', song='A', run=run,
            call=dict(id=uuid.uuid4().hex, name='request_media_generation',
                      arguments=dict(plan_id=plan, action_id='a', grant_id='g'), complete=True))
        self.assertEqual(status, 400, value)

    def test_read_only_scope_includes_job_and_estimate_reads(self):
        self.post('conversation_agent_settings', song='A', selection='anthropic-haiku-5-5', settings_revision=0,
                  mode='read_only', effort='low')
        self.insert_generation_job('job-owned')
        preview = self.f.preview()
        self.assertIn('get_generation_job', preview['tool_scope'])
        self.assertIn('estimate_media_plan', preview['tool_scope'])
        self.assertNotIn('prepare_image_action', preview['tool_scope'])
        result, _ = self.tool_result(self.send_tool('get_generation_job', {'job_id':'job-owned'}, preview=preview))
        self.assertEqual(result['status'], 'succeeded')

    def test_old_manifest_cannot_gain_job_query(self):
        self.insert_generation_job('job-owned')
        old_scope = tuple(x for x in chat_general.ALLOWED_TOOLS if x not in {'get_generation_job', 'estimate_media_plan'})
        with patch.object(chat_general, 'ALLOWED_TOOLS', old_scope):
            old = self.f.preview()
        self.assertNotIn('get_generation_job', old['tool_scope'])
        self.assertNotIn('get_generation_job', {d['name'] for d in old['message_body']['tools']})
        project = self.send_tool('get_generation_job', {'job_id':'job-owned'}, preview=old)
        self.assertEqual(project['general_chat_turns'][-1]['status'], 'outcome_unknown')
        self.assertEqual(project['production_runs'][-1]['calls'], [])


if __name__ == '__main__':
    unittest.main()
