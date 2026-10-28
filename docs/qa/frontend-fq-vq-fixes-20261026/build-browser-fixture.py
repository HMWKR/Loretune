from pathlib import Path
import sqlite3,json,base64,mimetypes,hashlib
root=Path.cwd();qa=Path('/tmp/loretune-ms-qa-20261025');out=root/'docs/qa/frontend-fq-vq-fixes-20261026'
with sqlite3.connect(f'file:{qa}/studio.sqlite3?mode=ro',uri=True) as c:
 revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
original=json.loads(body);name='디자인 시스템 기능 QA 20261026';p=original['projects'][name]
fingerprint=hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
p['model_settings']={'revision':1,'selections':{'chat':None,'image':None,'video':None}}
p.update(chat_turns=[],media_actions=[],media_connections={},chat_connection={'available':False,'mode':'disconnected','reason':'격리 화면 검증'},image_connection={'state':'unconfigured'},ontology={'revision':0,'graph':{'entities':[]}},lineage={'nodes':[],'edges':[]})
state=dict(revision=revision,workspace_id='isolated-display-fixture',projects={name:p},project_ids={name:'synthetic-project'},canon=[],preferences=[],ips=[{'id':p['ip'],'name':'합성 IP'}],model_catalog={'models':[]},jobs=[],generation_jobs=[],asset_rights={},token='synthetic-no-auth',capabilities={'provider_generation':False,'provider_mode':'disconnected'})
assets={}
for a in p['audio_versions']+[t for shot in p['shots'].values() for t in shot['takes']]:
 filename=Path(a['asset']).name;file=qa/'assets'/filename
 assert file.is_file() and file.resolve().parent==(qa/'assets').resolve()
 assets[filename]='data:'+mimetypes.guess_type(file)[0]+';base64,'+base64.b64encode(file.read_bytes()).decode()
boot='''<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; media-src data: blob:; connect-src 'none'; form-action 'none'"><script>
window.__fixtureState=STATE;window.__fixtureAssets=ASSETS;window.__fixtureErrors=[];window.__fixtureRequests=[];
window.addEventListener('error',e=>window.__fixtureErrors.push(e.message));
window.fetch=async(url,options={})=>{window.__fixtureRequests.push({url,method:options.method||'GET'});if(url==='/api/state'&&(!options.method||options.method==='GET'))return{ok:true,json:async()=>structuredClone(window.__fixtureState)};throw Error('ISOLATED_FIXTURE_BLOCKED')};
Object.defineProperty(window,'sessionStorage',{value:{values:new Map(),getItem(k){return this.values.get(k)||null},setItem(k,v){this.values.set(k,v)},removeItem(k){this.values.delete(k)}}});
navigator.sendBeacon=()=>false;
</script>'''.replace('STATE',json.dumps(state,ensure_ascii=False).replace('</','<\\/')).replace('ASSETS',json.dumps(assets))
html=(root/'index.html').read_text().replace('<head>','<head>'+boot,1)
# HTML source uses a compact opening head; insert before its first stylesheet if absent.
if 'window.__fixtureState' not in html:html=html.replace('<link rel="stylesheet"',boot+'<link rel="stylesheet"',1)
html=html.replace('<link rel="stylesheet" href="/studio.css">','<style>'+(root/'studio.css').read_text()+'</style>')
html=html.replace('<script src="/studio-media.js"></script>','<script>'+(root/'studio-media.js').read_text()+'</script>')
old="asset=a=>'/assets/'+a.asset.split('/').pop()";assert old in html
html=html.replace(old,"asset=a=>window.__fixtureAssets[a.asset.split('/').pop()]")
(out/'browser-fixture.html').write_text(html)
(out/'browser-fixture-manifest.json').write_text(json.dumps({'type':'isolated source replay, NOT served app','seams':['inline same CSS/media JS','asset URL -> local data URI','synthetic read-only state transport','in-memory storage'],'project_body_fingerprint':fingerprint,'asset_count':len(assets),'original_db_unchanged':True,'hashes':{n:hashlib.sha256((root/n).read_bytes()).hexdigest()for n in ['index.html','studio.css','studio-media.js']}},indent=2))
print('fixture assets',len(assets),'bytes',len(html))
