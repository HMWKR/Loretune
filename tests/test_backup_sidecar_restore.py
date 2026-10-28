"""Verified offline restore must preserve output sidecar integrity and usability."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen
import unittest

from app import Store, server
from backup import create, restore
from tests import test_timeline_repeated_http as fixtures


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class BackupSidecarRestoreTest(unittest.TestCase):
    setUp=fixtures.RepeatedTimelineHTTPTest.setUp
    close_server=fixtures.RepeatedTimelineHTTPTest.close_server
    get_state=fixtures.RepeatedTimelineHTTPTest.get_state
    project=fixtures.RepeatedTimelineHTTPTest.project
    request=fixtures.RepeatedTimelineHTTPTest.request
    post=fixtures.RepeatedTimelineHTTPTest.post
    select=fixtures.RepeatedTimelineHTTPTest.select
    timeline=fixtures.RepeatedTimelineHTTPTest.timeline

    def get(self,path):
        try:
            with urlopen(self.base+path) as response:return response.status,response.read()
        except HTTPError as error:
            with error:return error.code,error.read()

    def start(self,root):
        self.http=server(root,0);self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.http.server_port}'

    def test_verified_restore_chain_and_legacy_with_tamper_boundaries(self):
        audio=Path(self.tmp.name)/'audio.wav'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3',str(audio)],check=True)
        self.post('audio',song='A',filename='audio.wav',content=base64.b64encode(audio.read_bytes()).decode(),rights='직접 제작')
        timeline=self.timeline();timeline['audio']=1;timeline['subtitles']=[dict(start=0,end=1,text='복원 달빛')]
        self.post('timeline',song='A',timeline=timeline);self.post('approve_timeline',song='A')
        identifier=self.post('render_job',song='A')['job'];self.assertTrue(self.http.store.process_next())
        job=next(j for j in self.get_state()['jobs'] if j['id']==identifier)
        self.assertEqual(job['status'],'completed',job.get('error'))
        paths={ext:'/exports/'+identifier+ext for ext in ('.mp4','.srt','.json')}
        originals={ext:self.get(path)[1] for ext,path in paths.items()}
        for ext,path in paths.items():self.assertEqual(self.get(path),(200,originals[ext]))
        original_root=Path(self.tmp.name).resolve()
        self.close_server()
        with tempfile.TemporaryDirectory() as outer:
            root=Path(outer).resolve()
            create(original_root,root/'backup1');restore(root/'backup1',root/'restore1')
            self.start(root/'restore1')
            for ext,path in paths.items():self.assertEqual(self.get(path),(200,originals[ext]))
            first=next(j for j in self.get_state()['jobs'] if j['id']==identifier)
            self.assertEqual(first['sidecar_sha256'],job['sidecar_sha256'])
            self.assertTrue(first['sidecar_path_origins'])
            audio_sha=first['snapshot']['audio']['sha256']
            self.post('asset_rights',song='A',sha256=audio_sha,blocked=True,reason='복원 권리 시험')
            self.assertEqual(self.get(paths['.json'])[0],403)
            self.post('asset_rights',song='A',sha256=audio_sha,blocked=False,reason='복원 권리 확인')
            with self.http.store.connect() as c:
                persisted=c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()[0]
                changed=json.loads(persisted);changed['sidecar_path_origins'][next(iter(changed['sidecar_path_origins']))]='/wrong/assets/not-the-same.png'
                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(changed),identifier))
            self.assertEqual(self.get(paths['.json'])[0],409)
            with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(persisted,identifier))
            self.close_server()
            create(root/'restore1',root/'backup2');restore(root/'backup2',root/'restore2')
            self.start(root/'restore2')
            for ext,path in paths.items():self.assertEqual(self.get(path),(200,originals[ext]))
            second=next(j for j in self.get_state()['jobs'] if j['id']==identifier)
            self.assertEqual(set(second['sidecar_path_origins'].values()),set(first['sidecar_path_origins'].values()))
            self.assertEqual(second['sidecar_sha256'],job['sidecar_sha256'])
            self.close_server()
            # A checksum-valid backup may still contain an output changed before backup;
            # its old render hash must not be replaced or granted path provenance.
            source_json=original_root/'exports'/(identifier+'.json')
            source_json.write_bytes(b'corrupt with stored render hash')
            create(original_root,root/'corrupt-hashed-backup');restore(root/'corrupt-hashed-backup',root/'corrupt-hashed-restored')
            self.start(root/'corrupt-hashed-restored')
            self.assertEqual(self.get(paths['.json'])[0],409)
            corrupt=next(j for j in self.get_state()['jobs'] if j['id']==identifier)
            self.assertNotIn('sidecar_path_origins',corrupt)
            self.assertEqual(corrupt['sidecar_sha256'],job['sidecar_sha256'])
            self.close_server();source_json.write_bytes(originals['.json'])
            # Legacy output has no trusted sidecar hash; its original JSON must
            # still exactly match the pre-restore frozen job before path tracking.
            source=Store(original_root)
            with source.connect() as c:
                legacy=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()[0])
                legacy.pop('sidecar_sha256')
                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(legacy),identifier))
            create(original_root,root/'legacy-backup');restore(root/'legacy-backup',root/'legacy-restored')
            self.start(root/'legacy-restored')
            self.assertEqual(self.get(paths['.json']),(200,originals['.json']))
            legacy_restored=next(j for j in self.get_state()['jobs'] if j['id']==identifier)
            self.assertNotIn('sidecar_sha256',legacy_restored)
            with self.http.store.connect() as c:
                persisted=c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()[0]
                missing=json.loads(persisted);missing.pop('sidecar_path_origins')
                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(missing),identifier))
            self.assertEqual(self.get(paths['.json'])[0],409)
            with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(persisted,identifier))
            self.close_server()
            # A newly backed-up corrupted legacy record is not promoted.
            (original_root/'exports'/(identifier+'.json')).write_bytes(b'corrupt')
            create(original_root,root/'corrupt-backup');restore(root/'corrupt-backup',root/'corrupt-restored')
            self.start(root/'corrupt-restored')
            self.assertEqual(self.get(paths['.json'])[0],409)
            self.assertEqual(self.get(paths['.srt']),(200,originals['.srt']))
            self.close_server()
            (root/'backup2'/'exports'/(identifier+'.json')).write_bytes(b'changed after backup')
            with self.assertRaises(ValueError):restore(root/'backup2',root/'rejected')
            self.assertFalse((root/'rejected').exists())
            # Keep the fixture's registered cleanup attached to a live server.
            self.start(root/'restore2')


if __name__=='__main__':unittest.main()
