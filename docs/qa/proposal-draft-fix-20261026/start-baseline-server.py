"""Bounded read-only localhost QA server; source files and canonical data unchanged."""
from pathlib import Path
import hashlib, json, shutil, sqlite3, sys, tempfile, time, datetime

ROOT=Path('/Users/leesungmin/Desktop/Loretune')
OUT=ROOT/'docs/qa/proposal-draft-fix-20261026/served-baseline'
OUT.mkdir(exist_ok=True)
QA=Path('/tmp/loretune-ms-qa-20261025')
NAME='디자인 시스템 기능 QA 20261026'
EXPECTED='4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792'
def digest(data):return hashlib.sha256(data).hexdigest()
def fingerprint(project):return digest(json.dumps(project,ensure_ascii=False,sort_keys=True).encode())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def original():
    with sqlite3.connect(f'file:{QA}/studio.sqlite3?mode=ro',uri=True) as c:
        revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
    return revision,json.loads(body)['projects'][NAME]
revision,project=original()
assert fingerprint(project)==EXPECTED,'Approved synthetic project changed; stop before serving'
prior=json.loads((ROOT/'docs/qa/frontend-fq-vq-fixes-20261026/authorized-verification/final-preservation.json').read_text())
allowed={Path(a['path']).name:a for a in prior['assets']}
assets=project['audio_versions']+[take for shot in project['shots'].values() for take in shot['takes']]
assert {Path(a['asset']).name for a in assets}==set(allowed) and len(allowed)==4
release=json.loads((OUT.parent/'release-manifest.json').read_text())
for name,value in release['hashes'].items():assert digest((ROOT/name).read_bytes())==value
assert not (OUT/'server-start.json').exists(),'Do not start a duplicate listener'
data=Path(tempfile.mkdtemp(prefix='loretune-served-baseline-20261026-'))
(data/'assets').mkdir()
copied=[]
for name,a in allowed.items():
    source=QA/'assets'/name
    assert source.resolve().parent==(QA/'assets').resolve()
    content=source.read_bytes();assert len(content)==a['bytes'] and digest(content)==a['sha256']
    (data/'assets'/name).write_bytes(content);copied.append({'name':name,'bytes':len(content),'sha256':digest(content)})
for asset in assets:asset['asset']=str(data/'assets'/Path(asset['asset']).name)
sys.path.insert(0,str(ROOT))
from app import Store,server
store=Store(data)
with store.connect() as c:
    c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision,json.dumps({'canon':[],'projects':{NAME:project},'preferences':[]},ensure_ascii=False)))
    c.execute('INSERT OR IGNORE INTO ips VALUES (?,?,?)',(project.get('ip','default'),'합성 QA IP','승인된 검증 fixture'))
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
http=server(data,0)
Base=http.RequestHandlerClass
requests=[]
class ReadOnlyHandler(Base):
    def log_message(self,*args):pass
    def do_GET(self):
        requests.append({'method':'GET','path':self.path})
        return super().do_GET()
    def do_POST(self):
        requests.append({'method':'POST','path':self.path,'blocked':True})
        return self.send(405,{'error':'READ_ONLY_QA_SERVER'})
    do_PATCH=do_POST
http.RequestHandlerClass=ReadOnlyHandler
http.timeout=.25
start={'time':now(),'url':f'http://127.0.0.1:{http.server_port}','bind':http.server_address,'data':str(data),'project':NAME,'original_fingerprint':EXPECTED,'assets':copied,'source_hashes':release['hashes'],'seams':['isolated one-project database','POST/PATCH blocked','no workers/provider/chat configuration'],'workers':0}
(OUT/'server-start.json').write_text(json.dumps(start,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'url':start['url'],'assets':4,'source_verified':True}),flush=True)
try:
    deadline=time.monotonic()+1800
    while not (OUT/'stop-server').exists() and time.monotonic()<deadline:http.handle_request()
finally:
    http.server_close()
    _,current=original()
    result={'time':now(),'listener_closed':http.socket.fileno()==-1,'reason':'stop marker' if (OUT/'stop-server').exists() else 'deadline','requests':requests,'non_get':sum(x['method']!='GET' for x in requests),'canonical_project_unchanged':fingerprint(current)==EXPECTED,'source_unchanged':all(digest((ROOT/k).read_bytes())==v for k,v in release['hashes'].items()),'media_unchanged':all(digest((QA/'assets'/k).read_bytes())==v['sha256'] for k,v in allowed.items())}
    (OUT/'server-stop.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='requests'}),flush=True)
