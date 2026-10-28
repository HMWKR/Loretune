"""UI projection fixtures are synthetic saved states, never real model/render proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
import time
import unittest
import uuid

import app
import chat_sessions
import production_context

ROOT = Path(__file__).resolve().parents[1]


class WorkStatusUITest(unittest.TestCase):
    def test_actual_source_projection_contract(self):
        result = subprocess.run(['node', 'tests/work_status.cjs'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which('node') and Path('/opt/homebrew/lib/node_modules/puppeteer-core').exists() and Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome').exists(), 'installed isolated browser unavailable')
    def test_http_projection_navigation_and_live_state_change(self):
        with tempfile.TemporaryDirectory() as directory:
            server = app.server(Path(directory)/'data', 0)
            store = server.store

            def mutate(action, **data):
                return store.mutate(dict(action=action, data=data, revision=store.state()['revision'], request_id=uuid.uuid4().hex))

            for name in ['Status A', 'Status B']:
                mutate('project', name=name, era='default', story=0)
                mutate('shot', song=name, shot='status-shot', description='작업 상태 UI 합성 검증')
            private = mutate('conversation_create', song='Status A', title='별도 대화')['conversation']['id']
            p = store.state()['projects']['Status A']
            cid = chat_sessions.default_id(p)
            # A real draft record supplies the existing 3D dialog's shot binding.
            scene = dict(schema_version=1, width=96, height=96, background=[.1,.1,.1], objects=[dict(id='subject',kind='cube',position=[0,0,0],rotation_degrees=[0,0,0],scale=[1,1,1],color=[.1,.3,.8])],camera=dict(position=[5,-7,5],target=[0,0,0],lens_mm=50),lights=[dict(id='key',position=[3,-4,6],target=[0,0,0],energy_w=800,size_m=3,color=[1,1,1])])
            sid = mutate('scene_create', song='Status A', shot_id=production_context.shot_id(p,'status-shot'), scene=scene)['scene']['scene_id']
            jobs = []

            def job(name, status, **extra):
                value = dict(id=uuid.uuid4().hex,song=name,status=status,progress=25,snapshot=dict(timeline=dict(id=0,clips=[]),shots={}),error=None,download=None,fixture='UI projection only; not an executed render')
                value.update(extra); jobs.append(value); return value

            output = job('Status A','running')
            job('Status A','completed')
            job('Status A','failed',kind='local-motion',shot='status-shot',error='합성 상태 검증 오류')
            job('Status A','running',kind='local-3d-still',shot='status-shot',scene_id=sid,scene_revision=0,conversation_id=cid)
            hidden = job('Status A','failed',conversation_id=private)
            job('Status B','failed')
            provider = dict(id=uuid.uuid4().hex, context=dict(song='Status A',shot='status-shot'),state='running',receipt=None,result=None,input=None,cost_confirmed=False,fixture='UI projection only; no provider call')
            with store.connect() as connection:
                revision, raw = connection.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
                state = json.loads(raw)
                state['projects']['Status A'].setdefault('conversation_owners',{})[hidden['id']] = dict(conversation_id=private,kind='jobs')
                connection.execute('UPDATE state SET body=? WHERE id=1',(json.dumps(state,ensure_ascii=False),))
                for value in jobs:
                    connection.execute('INSERT INTO jobs VALUES (?,?)',(value['id'],json.dumps(value,ensure_ascii=False)))
                connection.execute('INSERT INTO generation_jobs VALUES (?,?,?,?)',(provider['id'],uuid.uuid4().hex,'synthetic-ui-state',json.dumps(provider)))
            thread = Thread(target=server.serve_forever,daemon=True);thread.start()
            phase = Path(directory)/'browser-phase.json'
            evidence = os.environ.get('LORETUNE_WORK_STATUS_EVIDENCE')
            command = ['node','tests/work_status.cjs',f'http://127.0.0.1:{server.server_port}',str(phase)]
            if evidence:
                Path(evidence).mkdir(parents=True,exist_ok=True);command.append(evidence)
            try:
                process = subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                deadline = time.monotonic()+60;changed=False
                while process.poll() is None and time.monotonic()<deadline:
                    if phase.exists() and not changed:
                        with store.connect() as connection:
                            value=json.loads(connection.execute('SELECT body FROM jobs WHERE id=?',(output['id'],)).fetchone()[0]);value.update(status='failed',error='합성 상태 전환 검증 오류')
                            connection.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(value,ensure_ascii=False),output['id']))
                        changed=True
                    time.sleep(.03)
                if process.poll() is None:
                    process.kill()
                stdout,stderr=process.communicate(timeout=5)
                if evidence:
                    (Path(evidence)/'invocation.json').write_text(json.dumps(dict(command=command,returncode=process.returncode,stdout=stdout,stderr=stderr,synthetic_fixture=True,actual_provider_calls=0),ensure_ascii=False,indent=2)+'\n')
                self.assertTrue(changed,'browser must request the saved fixture state transition')
                self.assertEqual(process.returncode,0,stdout+stderr)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=5)
