"""Timeline execution grant scoping over local HTTP; no provider calls."""
import base64
import json
import subprocess
import threading
import unittest
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app import Store, server
from tests import test_editing


class TimelineGrantScopeTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_editing.EditingTest(); self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        f.call('audio', filename='song.wav', content=base64.b64encode(f.wav.read_bytes()).decode(), rights='fixture rights')
        timeline = f.timeline(); timeline['audio'] = 1
        timeline['subtitles'] = [dict(start=0, end=1, text='합성 가사')]
        for clip in timeline['clips']: clip['duration'] = 1
        f.call('timeline', timeline=timeline)
        for clip in timeline['clips']:
            f.call('review_take', shot=clip['shot'], take=clip['take'], decision='approved', reason='fixture')
        self.http = server(f.temp.name, 0)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.close)
        self.base = 'http://127.0.0.1:' + str(self.http.server_port)

    def close(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()

    def state(self, cid=None):
        query = '?' + urlencode({'song':'song', 'conversation':cid}) if cid else ''
        with urlopen(self.base + '/api/state' + query) as response: return json.load(response)

    def action(self, name, cid=None, **data):
        current = self.state(cid)
        body = dict(action=name, data=dict(song='song', **data), revision=current['revision'], request_id=uuid.uuid4().hex)
        if cid:
            active = current['projects']['song']['active_conversation']
            body.update(conversation_id=cid, conversation_revision=active['revision'], shared_version=active['shared_version'])
        request = Request(self.base + '/api/action', data=json.dumps(body).encode(), headers={'Content-Type':'application/json', 'X-Loretune-Token':current['token']})
        try:
            with urlopen(request) as response: return response.status, json.load(response)
        except HTTPError as response:
            with response: return response.code, json.load(response)

    def create_conversation(self, title):
        status, result = self.action('conversation_create', title=title)
        self.assertEqual(status, 200, result)
        return result['conversation']['id']

    def approve(self, cid=None):
        status, result = self.action('approve_timeline', cid)
        self.assertEqual(status, 200, result)
        return self.state(cid)['projects']['song']['timeline_versions'][0]['approval']['id']

    def tool(self, grant, cid=None, call_id='render', version=1):
        status, result = self.action('production_run', cid)
        self.assertEqual(status, 200, result)
        call = dict(id=call_id, name='request_render', arguments={'timeline_version':version,'grant_id':grant}, complete=True)
        return self.action('production_tool', cid, run=result['run']['id'], call=call)

    def remove_owner_and_provenance(self, grant):
        with self.http.store.connect() as c:
            rev, raw = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            data = json.loads(raw); project = data['projects']['song']
            project['conversation_owners'].pop(grant, None)
            project['timeline_versions'][0]['approval'].pop('conversation_id', None)
            prior = dict(project['timeline_versions'][0]['approval'])
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (rev+1, json.dumps(data)))
        return prior

    def test_nondefault_owner_context_http_render_and_restart(self):
        cid = self.create_conversation('승인 대화'); other = self.create_conversation('다른 대화')
        grant = self.approve(cid)
        with self.http.store.connect() as c:
            data = json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
            self.assertEqual(data['projects']['song']['conversation_owners'][grant]['conversation_id'],cid)
        self.assertIsNone(self.state(other)['projects']['song']['timeline_versions'][0]['approval']['id'])
        status, handoff = self.action('model_handoff', other)
        self.assertEqual(status,200,handoff);self.assertNotIn(grant,json.dumps(handoff))
        self.assertEqual(self.tool(grant,other)[0],400)
        status,result = self.tool(grant,cid)
        self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'accepted')
        job = result['tool']['job_id']
        status,result = self.tool(grant,cid,call_id='same-job')
        self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'existing');self.assertEqual(result['tool']['job_id'],job)
        self.assertTrue(self.http.store.process_next())
        j = next(x for x in self.state(cid)['jobs'] if x['id']==job)
        self.assertEqual(j['status'],'completed',j.get('error'));self.assertFalse(j.get('delivery_reviews'))
        output = self.http.store.root/'exports'/(job+'.mp4')
        info = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))
        self.assertEqual({x['codec_type'] for x in info['streams']},{'video','audio','subtitle'})
        reopened = Store(self.fixture.temp.name).state({'song':cid})
        self.assertEqual(next(x for x in reopened['jobs'] if x['id']==job)['status'],'completed')
        self.assertEqual(reopened['projects']['song']['timeline_versions'][0]['approval']['id'],grant)

    def test_unknown_legacy_owner_requires_new_approval_and_preserves_history(self):
        cid=self.create_conversation('원래 대화');other=self.create_conversation('다른 대화')
        grant=self.approve(cid);old=self.remove_owner_and_provenance(grant)
        for context in (None,cid,other):
            self.assertIsNone(self.state(context)['projects']['song']['timeline_versions'][0]['approval']['id'])
            status,handoff=self.action('model_handoff',context)
            self.assertEqual(status,200,handoff);self.assertNotIn(grant,json.dumps(handoff))
            self.assertNotEqual(self.tool(grant,context)[0],200)
        replacement=self.approve(cid);self.assertNotEqual(replacement,grant)
        with self.http.store.connect() as c:
            rows=c.execute('SELECT timeline,approval FROM timeline_approval_history').fetchall()
        self.assertEqual(len(rows),1);self.assertEqual(rows[0][0],1);self.assertEqual(json.loads(rows[0][1]),old)
        self.assertIsNone(self.state(other)['projects']['song']['timeline_versions'][0]['approval']['id'])
        status,result=self.tool(replacement,cid);self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'accepted')
        status,result=self.tool(grant,cid)
        self.assertTrue(status!=200 or result['tool']['status']=='blocked')
        self.assertEqual(len(self.state(cid)['jobs']),1)

    def test_unambiguous_default_legacy_and_explicit_provenance(self):
        grant=self.approve();self.remove_owner_and_provenance(grant)
        self.assertEqual(self.state()['projects']['song']['timeline_versions'][0]['approval']['id'],grant)
        status,result=self.tool(grant);self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'accepted')
        cid=self.create_conversation('새 대화')
        self.assertIsNone(self.state(cid)['projects']['song']['timeline_versions'][0]['approval']['id'])
        self.assertIsNone(self.state()['projects']['song']['timeline_versions'][0]['approval']['id'])

    def test_reapproval_preserves_older_snapshot_and_prevents_reuse(self):
        cid=self.create_conversation('제작 대화');first=self.approve(cid)
        status,result=self.tool(first,cid);self.assertEqual(status,200,result);old_job=result['tool']['job_id']
        second=self.approve(cid);self.assertNotEqual(first,second)
        with self.http.store.connect() as c:
            data=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(old_job,)).fetchone()[0])
            history=json.loads(c.execute('SELECT approval FROM timeline_approval_history').fetchone()[0])
        self.assertEqual(data['snapshot']['timeline']['approval']['id'],first);self.assertEqual(history['id'],first)
        status,result=self.tool(first,cid);self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'blocked')
        status,result=self.tool(second,cid);self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'accepted')
        self.assertEqual(len(self.state(cid)['jobs']),2)

    def test_stale_and_cancelled_requests_do_not_start_a_new_job(self):
        cid=self.create_conversation('작업 대화');grant=self.approve(cid)
        status,result=self.tool(grant,cid);self.assertEqual(status,200,result);job=result['tool']['job_id']
        status,result=self.action('cancel_job',cid,job=job);self.assertEqual(status,200,result)
        status,result=self.tool(grant,cid,call_id='after-cancel')
        self.assertEqual(status,200,result);self.assertEqual(result['tool']['status'],'existing');self.assertEqual(result['tool']['state'],'cancelled')
        self.assertEqual(len(self.state(cid)['jobs']),1)
        current=self.state(cid)['projects']['song']['timeline_versions'][0]
        status,result=self.action('timeline',cid,timeline=current);self.assertEqual(status,200,result)
        status,result=self.tool(grant,cid,call_id='stale')
        self.assertEqual(status,200,result);self.assertEqual(result['tool']['code'],'STALE_VERSION')
        self.assertEqual(len(self.state(cid)['jobs']),1)

    def test_manual_render_uses_existing_shared_approval_without_grant_handle(self):
        owner=self.create_conversation('승인한 대화');other=self.create_conversation('수동 작업 대화')
        grant=self.approve(owner)
        self.assertIsNone(self.state(other)['projects']['song']['timeline_versions'][0]['approval']['id'])
        status,quote=self.action('estimate_render',other);self.assertEqual(status,200,quote)
        status,result=self.action('render_job',other,estimate=quote['estimate']);self.assertEqual(status,200,result)
        self.assertEqual(len(self.state(other)['jobs']),1)
        self.assertEqual(self.tool(grant,other)[0],400)

if __name__=='__main__':unittest.main()
