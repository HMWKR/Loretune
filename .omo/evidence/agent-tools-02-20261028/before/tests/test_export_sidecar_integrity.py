"""Real HTTP checks for the files delivered alongside a rendered video."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import shutil
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest

from app import server
from tests import test_timeline_repeated_http as fixtures


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Media tools required')
class ExportSidecarIntegrityTest(unittest.TestCase):
    setUp = fixtures.RepeatedTimelineHTTPTest.setUp
    close_server = fixtures.RepeatedTimelineHTTPTest.close_server
    get_state = fixtures.RepeatedTimelineHTTPTest.get_state
    project = fixtures.RepeatedTimelineHTTPTest.project
    request = fixtures.RepeatedTimelineHTTPTest.request
    post = fixtures.RepeatedTimelineHTTPTest.post
    select = fixtures.RepeatedTimelineHTTPTest.select
    timeline = fixtures.RepeatedTimelineHTTPTest.timeline
    save_approved = fixtures.RepeatedTimelineHTTPTest.save_approved

    def get(self, path, headers=None):
        try:
            with urlopen(Request(self.base+path, headers=headers or {})) as response:
                return response.status, response.read()
        except HTTPError as error:
            with error:
                return error.code, error.read()

    def test_actual_output_files_and_legacy_recovery(self):
        timeline=self.timeline()
        timeline['subtitles']=[dict(start=0,end=1,text='달빛 moon')]
        self.post('timeline',song='A',timeline=timeline)
        self.post('approve_timeline',song='A')
        job_id=self.post('render_job',song='A')['job']
        self.assertTrue(self.http.store.process_next())
        job=next(j for j in self.get_state()['jobs'] if j['id']==job_id)
        self.assertEqual(job['status'],'completed',job.get('error'))
        root=Path(self.tmp.name)/'exports'
        paths={suffix:'/exports/'+job_id+suffix for suffix in ('.mp4','.srt','.json','.vtt')}
        original={}
        for suffix,path in paths.items():
            status,body=self.get(path);self.assertEqual(status,200,(suffix,body))
            original[suffix]=body
        self.assertIn('달빛 moon'.encode(),original['.srt'])
        self.assertEqual(json.loads(original['.json'])['sha256'],job['sha256'])
        for suffix in ('.srt','.json'):
            self.assertEqual(job['sidecar_sha256'][suffix],hashlib.sha256(original[suffix]).hexdigest())
        self.assertEqual(self.get(paths['.srt'],{'Range':'bytes=0-2'}),(206,original['.srt'][:3]))
        for suffix in ('.mp4','.srt','.json'):
            orphan='/exports/'+('f'*32)+suffix
            (root/(('f'*32)+suffix)).write_bytes(b'orphan')
            self.assertEqual(self.get(orphan)[0],404)
        with self.http.store.connect() as c:
            original_record=c.execute('SELECT body FROM jobs WHERE id=?',(job_id,)).fetchone()[0]
        broken=[]
        for label in ('missing_sha','bad_sha','missing_verified','null_snapshot','missing_shots','wrong_selected','missing_shot','bad_audio','missing_subtitles','changed_subtitles','missing_audio','changed_both_subtitles'):
            value=deepcopy(job)
            if label=='missing_sha':value.pop('sha256')
            elif label=='bad_sha':value['sha256']='a'*64
            elif label=='missing_verified':value.pop('verified')
            elif label=='null_snapshot':value['snapshot']=None
            elif label=='missing_shots':value['snapshot'].pop('shots')
            elif label=='wrong_selected':
                value['snapshot']['shots']['0']['selected']=999
                value['snapshot']['timeline']['clips'][0]['take']=999
            elif label=='missing_shot':value['snapshot']['shots'].pop('0')
            elif label=='bad_audio':value['snapshot']['audio']={'id':99,'sha256':'a'*64}
            elif label=='missing_audio':value['snapshot'].pop('audio')
            elif label=='missing_subtitles':value['snapshot'].pop('subtitles')
            elif label=='changed_both_subtitles':
                value['snapshot']['subtitles']=[]
                value['snapshot']['timeline']['subtitles']=[]
            else:value['snapshot']['subtitles']=[]
            broken.append((label,json.dumps(value)))
        broken.append(('invalid_json','{'))
        try:
            for label,record in broken:
                with self.subTest(label=label):
                    with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(record,job_id))
                    for suffix in ('.srt','.json'):self.assertEqual(self.get(paths[suffix])[0],409)
        finally:
            with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(original_record,job_id))
        modified=deepcopy(job);modified['snapshot']['shots']['0']['semantic_context']={'changed':'snapshot'}
        try:
            with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(modified),job_id))
            self.assertEqual(self.get(paths['.srt']),(200,original['.srt']))
            self.assertEqual(self.get(paths['.json'])[0],409)
        finally:
            with self.http.store.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(original_record,job_id))
        video=root/(job_id+'.mp4');saved_video=root/(job_id+'.mp4.saved')
        video.rename(saved_video)
        try:
            for suffix in ('.srt','.json'):self.assertEqual(self.get(paths[suffix])[0],409)
        finally:saved_video.rename(video)
        for suffix in ('.srt','.json'):
            path=root/(job_id+suffix);path.write_bytes(b'tampered')
            status,body=self.get(paths[suffix]);self.assertEqual(status,409,(suffix,body))
            self.assertEqual(self.get(paths[suffix],{'Range':'bytes=0-2'})[0],409)
            self.assertEqual(self.get(paths['.mp4'])[0],200)
            self.assertEqual(self.get(paths['.vtt'])[0],200)
            path.write_bytes(original[suffix])
        manifest=self.post('manifest',song='A')['download']
        self.assertEqual(self.get(manifest)[0],200)
        with self.http.store.connect() as c:
            value=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job_id,)).fetchone()[0])
            value.pop('sidecar_sha256',None)
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(value),job_id))
        # Legacy files are compared to the frozen snapshot, not promoted to trusted hashes.
        for suffix in ('.srt','.json'):
            self.assertEqual(self.get(paths[suffix]),(200,original[suffix]))
            (root/(job_id+suffix)).write_bytes(b'tampered legacy')
            self.assertEqual(self.get(paths[suffix])[0],409)
            (root/(job_id+suffix)).write_bytes(original[suffix])
        self.http.shutdown();self.http.server_close();self.thread.join()
        self.http=server(self.tmp.name,0);self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.http.server_port}'
        self.assertEqual(self.get(paths['.srt']),(200,original['.srt']))
        sha=self.project()['shots']['s']['takes'][0]['sha256']
        self.post('asset_rights',song='A',sha256=sha,blocked=True,reason='권리 확인 대기')
        for suffix in ('.mp4','.srt','.json'):self.assertEqual(self.get(paths[suffix])[0],403)
        self.assertEqual(self.get(paths['.vtt'])[0],409)
        self.assertEqual(self.get(manifest)[0],403)


if __name__=='__main__':unittest.main()
