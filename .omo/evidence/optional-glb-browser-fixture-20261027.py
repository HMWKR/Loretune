"""Isolated synthetic browser fixture; never used by normal app startup."""
from pathlib import Path
import base64,hashlib,io,json,math,socket,struct,sys,tempfile,time,uuid,wave
from threading import Thread
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import app,scene_project,scene_renderer
from test_scene_asset_render import two_material_glb

folder=Path(tempfile.mkdtemp(prefix='loretune-optional-glb-ui-'))
binary=Path('/private/tmp/loretune-blender-x64.jEi6qO/unpacked/blender-5.2.2-linux-x64')
renderer=scene_renderer.RendererConfig('sha256:3d80954520e9890c49c488e3b739fc3aec09d1a87b91fcbdffd3fe481cb8ca51',binary,hashlib.sha256((binary/'blender').read_bytes()).hexdigest(),180,Path('/Users/leesungmin/.docker/run/docker.sock'))
http=app.server(folder/'data',0,scene_configuration=dict(renderer=renderer,quota_bytes=scene_project.RESERVATION_BYTES*5,tree_sha256=scene_project.tree_manifest(binary)))
store=http.store
def call(action,**data):return store.mutate(dict(action=action,data=data,revision=store.state()['revision'],request_id=uuid.uuid4().hex))
call('project',name='음원 중심 검증',era='default',story=0)
audio=io.BytesIO()
with wave.open(audio,'wb') as output:
    output.setnchannels(1);output.setsampwidth(2);output.setframerate(48000)
    output.writeframes(b''.join(struct.pack('<h',round(6500*math.sin(2*math.pi*440*i/48000))) for i in range(144000)))
call('audio',song='음원 중심 검증',filename='자체 제작 합성 음원.wav',content=base64.b64encode(audio.getvalue()).decode(),rights='직접 제작한 합성 음원')
call('shot',song='음원 중심 검증',shot='선택 장면',description='음원 흐름의 선택형 합성 자산')
(folder/'합성 자산.glb').write_bytes(two_material_glb())
(folder/'지원하지 않는 자산.glb').write_bytes(b'not-a-valid-glb')
Original=http.RequestHandlerClass
http.drop_next=None;http.fixture_posts=[]
class Handler(Original):
    def do_GET(self):
        if self.path.startswith('/__fixture/drop?'):
            mode=self.path.split('?',1)[1]
            if mode not in ('before','after'):return self.send(400,dict(error='invalid fixture mode'))
            http.drop_next=mode;return self.send(200,dict(mode=mode))
        if self.path=='/__fixture/stats':return self.send(200,dict(posts=http.fixture_posts,drop=http.drop_next))
        return super().do_GET()
    def do_POST(self):
        if self.path!='/api/action':return super().do_POST()
        raw=self.rfile.read(int(self.headers.get('Content-Length','0')));value=json.loads(raw)
        http.fixture_posts.append(dict(id=value.get('request_id'),action=value.get('action'),sha256=hashlib.sha256(raw).hexdigest(),mode=http.drop_next))
        self.drop_response=http.drop_next=='after';mode=http.drop_next;http.drop_next=None
        if mode=='before':return self.drop()
        original=self.rfile;self.rfile=io.BytesIO(raw)
        try:return super().do_POST()
        finally:self.rfile=original
    def drop(self):
        self.close_connection=True
        try:self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:pass
        self.connection.close()
    def send(self,status,value,*args,**kwargs):
        if getattr(self,'drop_response',False) and self.path=='/api/action' and status==200:
            self.drop_response=False;return self.drop()
        return super().send(status,value,*args,**kwargs)
http.RequestHandlerClass=Handler
Thread(target=http.serve_forever,daemon=True).start()
def work():
    while True:
        ran,failed=app.worker_cycle(store)
        if failed or not ran:time.sleep(.1)
Thread(target=work,daemon=True).start()
print(json.dumps(dict(url=f'http://127.0.0.1:{http.server_port}',root=str(folder),data=str(store.root),asset=str(folder/'합성 자산.glb'),invalid_asset=str(folder/'지원하지 않는 자산.glb')),ensure_ascii=False),flush=True)
try:
    while True:time.sleep(60)
finally:http.shutdown();http.server_close()
