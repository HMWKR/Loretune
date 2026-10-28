"""Local scene retry uses original client code against a real isolated HTTP server."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
import unittest
import uuid

import app


@unittest.skipUnless(shutil.which('node'), 'Node required for client recovery code')
class SceneRequestRecoveryTest(unittest.TestCase):
    def test_actual_http_original_id_retry_and_committed_lookup(self):
        with tempfile.TemporaryDirectory() as folder:
            http=app.server(folder,0)
            thread=Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                for action,data in [('project',dict(name='A',era='default',story=0)),('shot',dict(song='A',shot='s',description='synthetic recovery test'))]:
                    http.store.mutate(dict(action=action,data=data,revision=http.store.state()['revision'],request_id=uuid.uuid4().hex))
                root=Path(__file__).resolve().parents[1]
                result=subprocess.run(['node','tests/scene_request_recovery.cjs',f'http://127.0.0.1:{http.server_port}'],cwd=root,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr)
                evidence=json.loads(result.stdout.strip().splitlines()[-1])['evidence']
                self.assertEqual(evidence['actualPosts'],2)
                self.assertEqual(evidence['sceneCount'],1)
                self.assertEqual(evidence['proposalCount'],2)
                with http.store.connect() as db:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM requests WHERE id IN (?,?)',(evidence['first'],evidence['second'])).fetchone()[0],2)
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM scene_records').fetchone()[0],1)
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM scene_proposals').fetchone()[0],2)
            finally:
                http.shutdown();http.server_close();thread.join(5)


if __name__=='__main__':
    unittest.main()
