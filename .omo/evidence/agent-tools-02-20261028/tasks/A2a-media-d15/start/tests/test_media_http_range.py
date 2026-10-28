import tempfile,unittest
from pathlib import Path
from threading import Thread
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from app import server,media_byte_range

class MediaRangeTest(unittest.TestCase):
 def test_byte_boundaries_and_unsupported_ranges(self):
  for value,expected in [('bytes=0-0',(0,0)),('bytes=5-',(5,9)),('bytes=-3',(7,9)),('bytes=8-50',(8,9)),('bytes=-50',(0,9)),('items=1-2',None),('bytes=0-2,4-6',None),('',None)]:
   self.assertEqual(media_byte_range(value,10),expected)
  for value in ['bytes=-0','bytes=10-','bytes=9-2','bytes=x-9','bytes=','bytes=١-٢','bytes=1--2','bytes='+('9'*200)+'-']:
   with self.assertRaises(ValueError):media_byte_range(value,10)
  with self.assertRaises(ValueError):media_byte_range('bytes=0-',0)
 def test_real_http_range_body_and_rights_before_partial_response(self):
  with tempfile.TemporaryDirectory() as folder:
   app=server(folder,0);thread=Thread(target=app.serve_forever,daemon=True);thread.start()
   try:
    name='a'*64;file=Path(folder)/'assets'/(name+'.mp4');file.write_bytes(bytes(range(100)))
    base=f'http://127.0.0.1:{app.server_port}'
    def get(value=None,**headers):return urlopen(Request(base+'/assets/'+file.name,headers={**({'Range':value} if value else {}),**headers}))
    with get('bytes=12-21') as r:
     self.assertEqual(r.status,206);self.assertEqual(r.headers['Content-Range'],'bytes 12-21/100');self.assertEqual(r.headers['Content-Length'],'10');self.assertEqual(r.read(),bytes(range(12,22)))
    with get('bytes=-5') as r:self.assertEqual(r.read(),bytes(range(95,100)))
    with get() as r:self.assertEqual(r.headers['Accept-Ranges'],'bytes');self.assertEqual(len(r.read()),100)
    with get('bytes=12-21',**{'If-Range':'unknown'}) as r:self.assertEqual(r.status,200);self.assertEqual(len(r.read()),100)
    with self.assertRaises(HTTPError) as error:get('bytes=100-')
    self.assertEqual(error.exception.code,416);self.assertEqual(error.exception.headers['Content-Range'],'bytes */100');error.exception.close()
    with app.store.connect() as c:c.execute('INSERT INTO asset_rights VALUES (?,1,?,0)',(name,'synthetic revoked'))
    with self.assertRaises(HTTPError) as error:get('bytes=12-21')
    self.assertEqual(error.exception.code,403);error.exception.close()
    for static in ['studio.css','studio-media.js']:
     with urlopen(base+'/'+static) as r:self.assertEqual(r.status,200);self.assertIn('no-store',r.headers['Cache-Control'])
    with self.assertRaises(HTTPError) as error:urlopen(base+'/../studio-media.js')
    self.assertEqual(error.exception.code,404);error.exception.close()
   finally:app.shutdown();app.server_close();thread.join()
