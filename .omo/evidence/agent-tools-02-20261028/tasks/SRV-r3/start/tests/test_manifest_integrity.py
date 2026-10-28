"""Actual HTTP and offline restore boundaries for standalone manifests."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import unittest
import uuid

from app import server
from backup import create, restore
from tests import test_timeline_repeated_http as fixtures


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Media tools required')
class ManifestIntegrityTest(unittest.TestCase):
    setUp=fixtures.RepeatedTimelineHTTPTest.setUp
    close_server=fixtures.RepeatedTimelineHTTPTest.close_server
    get_state=fixtures.RepeatedTimelineHTTPTest.get_state
    project=fixtures.RepeatedTimelineHTTPTest.project
    request=fixtures.RepeatedTimelineHTTPTest.request
    post=fixtures.RepeatedTimelineHTTPTest.post
    select=fixtures.RepeatedTimelineHTTPTest.select

    def get(self,path,headers=None):
        try:
            with urlopen(Request(self.base+path,headers=headers or {})) as response:
                return response.status,dict(response.headers),response.read()
        except HTTPError as error:
            with error:return error.code,dict(error.headers),error.read()

    def test_manifest_hash_legacy_rights_duplicate_and_restored_http(self):
        self.post('shot',song='A',shot='second',description='다른 장면')
        self.post('take',song='A',shot='second',shot_revision=0,filename='blue.png',content=self.images[1],reason='합성',rights='직접 제작')
        self.post('select',song='A',shot='second',take=1,shot_revision=1)
        state=self.get_state();payload=dict(action='manifest',data=dict(song='A'),revision=state['revision'],request_id=uuid.uuid4().hex)
        def send():
            request=Request(self.base+'/api/action',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Loretune-Token':state['token']})
            with urlopen(request) as response:return json.load(response)
        first=send();self.assertEqual(send(),first)
        path=first['download'];name=Path(path).name;file=Path(self.tmp.name)/'exports'/name
        raw=file.read_bytes();status,headers,body=self.get(path)
        self.assertEqual((status,body),(200,raw));self.assertEqual(headers['X-Loretune-Integrity'],'verified')
        self.assertEqual(json.loads(body)['project']['name'],'A')
        with self.http.store.connect() as c:
            saved=c.execute('SELECT sha256,asset_hashes FROM export_manifests WHERE filename=?',(name,)).fetchone()
            assets=[row[0] for row in c.execute('SELECT sha256 FROM export_assets WHERE filename=?',(name,))]
        self.assertEqual(len(assets),2)
        self.assertEqual(saved[0],hashlib.sha256(raw).hexdigest());self.assertEqual(set(json.loads(saved[1])),set(assets))
        status,headers,body=self.get(path,{'Range':'bytes=0-7'})
        self.assertEqual((status,body),(206,raw[:8]));self.assertEqual(headers['X-Loretune-Integrity'],'verified')
        status,headers,_=self.get(path,{'Range':'bytes=999999-'})
        self.assertEqual(status,416);self.assertEqual(headers['X-Loretune-Integrity'],'verified')
        saved_file=file.with_suffix('.saved');file.rename(saved_file);file.symlink_to(saved_file)
        try:self.assertEqual(self.get(path)[0],409)
        finally:file.unlink();saved_file.rename(file)
        file.write_bytes(b'changed')
        self.assertEqual(self.get(path)[0],409);self.assertEqual(self.get(path,{'Range':'bytes=0-1'})[0],409)
        file.write_bytes(raw)
        with self.http.store.connect() as c:c.execute('UPDATE export_manifests SET sha256=? WHERE filename=?',('broken',name))
        self.assertEqual(self.get(path)[0],409)
        with self.http.store.connect() as c:c.execute('UPDATE export_manifests SET sha256=? WHERE filename=?',(saved[0],name))
        with self.http.store.connect() as c:c.execute('UPDATE export_manifests SET asset_hashes=? WHERE filename=?',('not json',name))
        self.assertEqual(self.get(path)[0],409)
        with self.http.store.connect() as c:c.execute('UPDATE export_manifests SET asset_hashes=? WHERE filename=?',(saved[1],name))
        with self.http.store.connect() as c:c.execute('DELETE FROM export_assets WHERE filename=? AND sha256=?',(name,assets[0]))
        self.assertEqual(self.get(path)[0],409)
        with self.http.store.connect() as c:c.execute('INSERT INTO export_assets VALUES (?,?)',(name,assets[0]))
        self.post('asset_rights',song='A',sha256=assets[0],blocked=True,reason='사용 중지')
        self.assertEqual(self.get(path)[0],403)
        self.post('asset_rights',song='A',sha256=assets[0],blocked=False,reason='사용 허가 확인')
        with self.http.store.connect() as c:c.execute('DELETE FROM export_manifests WHERE filename=?',(name,))
        status,headers,body=self.get(path);self.assertEqual((status,body),(200,raw));self.assertEqual(headers['X-Loretune-Integrity'],'unverified')
        # Without a saved hash, matching selected assets does not authenticate
        # the rest of the legacy document; report it as unverified.
        edited=json.loads(raw);edited['project']['name']='수정된 이름'
        altered=json.dumps(edited,ensure_ascii=False).encode('utf-8');file.write_bytes(altered)
        status,headers,body=self.get(path);self.assertEqual((status,body),(200,altered));self.assertEqual(headers['X-Loretune-Integrity'],'unverified')
        file.write_bytes(b'invalid json');self.assertEqual(self.get(path)[0],409)
        bad=json.loads(raw);bad['project']['shots']['s']['selected']=999
        file.write_bytes(json.dumps(bad).encode());self.assertEqual(self.get(path)[0],409)
        file.write_bytes(raw)
        with self.http.store.connect() as c:c.execute('DELETE FROM export_assets WHERE filename=? AND sha256=?',(name,assets[0]))
        self.post('asset_rights',song='A',sha256=assets[0],blocked=True,reason='누락된 권리 확인')
        self.assertEqual(self.get(path)[0],409)
        self.post('asset_rights',song='A',sha256=assets[0],blocked=False,reason='권리 재확인')
        with self.http.store.connect() as c:c.execute('INSERT INTO export_assets VALUES (?,?)',(name,assets[0]))
        file.write_bytes(raw)
        with self.http.store.connect() as c:
            self.assertIsNone(c.execute('SELECT 1 FROM export_manifests WHERE filename=?',(name,)).fetchone())
            c.execute('INSERT INTO export_manifests VALUES (?,?,?)',(name,*saved))
        self.close_server()
        with tempfile.TemporaryDirectory() as outer:
            root=Path(outer);create(self.tmp.name,root/'backup');restore(root/'backup',root/'restore')
            self.http=server(root/'restore',0);self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
            self.base=f'http://127.0.0.1:{self.http.server_port}'
            status,headers,body=self.get(path);self.assertEqual((status,body),(200,raw));self.assertEqual(headers['X-Loretune-Integrity'],'verified')
            (root/'restore'/'exports'/name).write_bytes(b'altered after restore')
            self.assertEqual(self.get(path)[0],409)
            self.close_server()
        self.http=server(self.tmp.name,0);self.thread=Thread(target=self.http.serve_forever,daemon=True);self.thread.start()


if __name__=='__main__':unittest.main()
