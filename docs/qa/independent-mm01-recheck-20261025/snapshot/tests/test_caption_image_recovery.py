import hashlib,json,subprocess,tempfile,time,unittest,uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from app import Store
from caption_preview import webvtt
import action_execution,contracts,guided,image_recovery
from tests import image_fixture as rw
from fal_provider import ProviderError
from tests import test_image_pipeline as fixtures
from tests import test_editing as editing_fixture

class CaptionPreviewTest(unittest.TestCase):
 def test_unicode_markup_blank_lines_and_export_rounding(self):
  result=webvtt([dict(start=.1306,end=1.9996,text='한글 <b>& -->\n\n끝')]).decode()
  self.assertIn('00:00:00.131 --> 00:00:02.000',result);self.assertIn('한글 &lt;b&gt;&amp; --&gt;\n\u00a0\n끝',result)
  self.assertEqual(webvtt([]),b'WEBVTT\n\n\n')
 def test_actual_render_caption_version_survives_edit_restart_and_rights_gate(self):
  case=editing_fixture.EditingTest();case.setUp();self.addCleanup(case.doCleanups)
  timeline=case.timeline();timeline['subtitles']=[dict(start=0,end=1,text='승인 자막 v1 한글')]
  for clip in timeline['clips']:clip['duration']=.5
  case.save_approve(timeline);jid=case.call('render_job')['job'];case.store.process_next()
  old=case.store.caption_preview(jid);self.assertIn('승인 자막 v1',old.decode())
  timeline['subtitles'][0]['text']='아직 승인하지 않은 v2';case.call('timeline',timeline=timeline)
  self.assertEqual(case.store.caption_preview(jid),old);self.assertEqual(Store(case.temp.name).caption_preview(jid),old)
  out=case.store.root/'exports'/(jid+'.mp4');embedded=subprocess.check_output(['ffmpeg','-v','error','-i',str(out),'-map','0:s:0','-f','srt','-']).decode()
  self.assertIn('승인 자막 v1 한글',embedded)
  sha=case.p()['shots']['a']['takes'][0]['sha256'];case.call('asset_rights',sha256=sha,blocked=True,reason='fixture revoke')
  with self.assertRaises(ValueError):case.store.caption_preview(jid)
 def test_missing_unapproved_incomplete_and_changed_media_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(folder);jid=uuid.uuid4().hex;out=store.root/'exports'/(jid+'.mp4');out.write_bytes(b'synthetic-no-provider')
   job=dict(id=jid,status='completed',sha256=hashlib.sha256(out.read_bytes()).hexdigest(),snapshot=dict(shots={},timeline=dict(id=1,approval={'actor':'fixture'}),subtitles=[]))
   def save():
    with store.connect() as c:c.execute('INSERT OR REPLACE INTO jobs VALUES (?,?)',(jid,json.dumps(job)))
   save();self.assertEqual(store.caption_preview(jid),webvtt([]))
   with self.assertRaises(ValueError):store.caption_preview('../escape')
   with self.assertRaises(KeyError):store.caption_preview('a'*32)
   job['status']='running';save()
   with self.assertRaises(ValueError):store.caption_preview(jid)
   job['status']='completed';job['snapshot']['timeline'].pop('approval');save()
   with self.assertRaises(ValueError):store.caption_preview(jid)
   job['snapshot']['timeline']['approval']={"actor":"fixture"};save();out.write_bytes(b'changed')
   with self.assertRaises(ValueError):store.caption_preview(jid)

class ImageRecoveryTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixtures.ImagePipelineTest.setUpClass()
 def setUp(self):
  self.f=fixtures.ImagePipelineTest();self.f.setUp();self.addCleanup(self.f.doCleanups);self.store=self.f.store;self.pipe=self.f.pipeline
 def blocked(self,code='download_interrupted'):
  j=self.f.start();self.store.process_generation();j=self.store.generation.poll(j['id'],self.f.adapter)
  j.update(state='import_blocked',failure_code=code)
  with self.store.connect() as c:self.store.generation.save(c,j)
  return j
 def approval(self,j,operation='collect',**extras):
  self.pipe.recovery_approval=dict(id=uuid.uuid4().hex,evidence='synthetic local verification',workspace=self.store.workspace_id,project=self.pipe.gate['project'],connection_id=rw.CONNECTION,job=j['id'],request_id=j['receipt']['request_id'],operation=operation,result_sha256=guided.fingerprint(j.get('result')),expires=time.time()+30,**extras)
 def enqueue(self,j,op='collect'):
  return self.f.call('recover_image_job',song='synthetic',job=j['id'],operation=op)
 def test_readiness_flags_never_enable_fake_or_read_environment(self):
  self.store.image_pipeline=None;self.assertEqual(image_recovery.capability(self.store,'synthetic')['state'],'unconfigured');self.assertIn('미선택',image_recovery.capability(self.store,'synthetic')['policy'])
  self.store.image_pipeline=self.pipe;self.assertEqual(image_recovery.capability(self.store,'synthetic')['state'],'unverified')
  v=dict(workspace=self.store.workspace_id,connection_id=rw.CONNECTION,model=rw.MODEL,output_policy=rw.OUTPUT_POLICY,account_verified=True,configuration_verified=True,integration_verified=True,evidence_id='synthetic-proof-only',expires=time.time()+60)
  self.pipe.verification=dict(v,blocked=True);self.assertEqual(image_recovery.capability(self.store,'synthetic')['state'],'blocked')
  self.pipe.verification=v;self.pipe.gate=dict(workspace=self.store.workspace_id,project=contracts.project_id(self.store.workspace_id,'synthetic'),expires=time.time()+30,live_approved=True)
  self.assertFalse(image_recovery.capability(self.store,'synthetic')['available'])
  self.assertEqual(image_recovery.capability(self.store,'synthetic')['state'],'unverified')
  self.pipe.verification['expires']=0;self.assertEqual(image_recovery.capability(self.store,'synthetic')['state'],'unverified')
 def test_manual_collect_is_same_receipt_take_once_and_preserves_selection(self):
  j=self.blocked();self.approval(j);before=self.f.shot()['selected'];self.enqueue(j)
  pending=image_recovery.describe(self.store,self.store.generation.get(j['id']));self.assertFalse(pending['can_collect']);self.assertFalse(pending['can_status']);self.assertIn('처리 중',pending['reason'])
  with patch.object(self.f.adapter,'download',return_value=self.f.png) as download:
   with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:self.store.process_generation(),range(2)))
   self.assertEqual(download.call_count,1)
  latest=self.store.generation.get(j['id']);self.assertEqual(latest['state'],'imported');self.assertEqual(latest['receipt'],j['receipt']);self.assertEqual(self.f.shot()['selected'],before)
  self.assertEqual(len(self.f.shot()['takes']),1);self.assertEqual(sum(c[0]=='POST' for c in self.f.calls),1)
  status=image_recovery.describe(self.store,latest);self.assertIn('등록이 완료',status['reason']);self.assertFalse(status['can_collect']);self.assertFalse(status['can_status'])
  with self.assertRaises(ValueError):self.enqueue(latest)
 def test_403_needs_new_matching_permission_evidence_and_one_use(self):
  j=self.blocked('download_http_403');self.approval(j)
  with self.assertRaisesRegex(ValueError,'접근 거절'):self.enqueue(j)
  self.approval(j,resolves_permission=True,resolved_failure='download_http_403');self.enqueue(j)
  with patch.object(self.f.adapter,'download',side_effect=ProviderError('download_http_403')) as download:
   self.store.process_generation();self.store.process_generation();self.assertEqual(download.call_count,1)
  latest=self.store.generation.get(j['id']);self.assertEqual(latest['state'],'import_blocked');self.assertFalse(image_recovery.describe(self.store,latest)['can_collect'])
 def test_existing_status_query_does_not_implicitly_collect_or_submit(self):
  j=self.blocked('download_http_410');self.approval(j,'status');self.enqueue(j,'status')
  with patch.object(self.f.adapter,'download',side_effect=AssertionError('no download')):
   self.store.process_generation();self.assertFalse(self.store.process_generation())
  latest=self.store.generation.get(j['id']);self.assertEqual(latest['state'],'import_blocked');self.assertEqual(latest['failure_code'],'collection_requires_approval');self.assertEqual(sum(c[0]=='POST' for c in self.f.calls),1)
 def test_pending_status_stops_after_one_read_and_keeps_unknown_cost(self):
  j=self.blocked();self.approval(j,'status');self.enqueue(j,'status');self.f.adapter._transport=lambda *a:dict(id=self.f.rid,status='RUNNING')
  with patch.object(self.f.adapter,'status',wraps=self.f.adapter.status) as status:
   self.store.process_generation();self.store.process_generation();self.assertEqual(status.call_count,1)
  self.assertEqual(self.store.generation.get(j['id'])['state'],'reconciliation_required')
 def test_gate_payload_scope_expiry_and_revocation_block_before_io(self):
  j=self.blocked()
  for field,value in [('request_id','other'),('project','other'),('workspace','other'),('expires',0),('result_sha256','wrong')]:
   self.approval(j);self.pipe.recovery_approval[field]=value
   with self.assertRaises(ValueError):self.enqueue(j)
  self.approval(j);self.enqueue(j)
  with self.store.connect() as c:action_execution.revoke(c,self.store.workspace_id,self.pipe.gate['project'],j['context']['action_binding']['grant_id'],1)
  with patch.object(self.f.adapter,'download',side_effect=AssertionError('no download')):self.store.process_generation()
  self.assertEqual(self.store.generation.get(j['id'])['state'],'import_blocked');self.assertEqual(self.f.shot()['takes'],[])
 def test_restart_running_recovery_never_reissues(self):
  j=self.blocked();j['state']='image_recovery_running'
  with self.store.connect() as c:self.store.generation.save(c,j)
  self.store.generation.recover();self.assertEqual(self.store.generation.get(j['id'])['state'],'reconciliation_required');self.assertFalse(self.store.process_generation())
 def test_unknown_receipt_and_cross_project_never_generate(self):
  j=self.blocked();self.approval(j);j['receipt']=None
  with self.store.connect() as c:self.store.generation.save(c,j)
  with self.assertRaises(ValueError):self.enqueue(j)
  self.f.call('project',name='foreign',era='default',story=0)
  with self.assertRaises(ValueError):self.f.call('recover_image_job',song='foreign',job=j['id'],operation='collect')
  self.assertEqual(sum(c[0]=='POST' for c in self.f.calls),1)

class CaptionRecoveryUITest(unittest.TestCase):
 def test_actual_renderer_binds_approved_export_and_disables_unconfigured(self):
  code=r'''const fs=require('fs'),vm=require('vm'),assert=require('assert');const html=fs.readFileSync('index.html','utf8'),nodes={};
const state={jobs:[{id:'abc',song:'mine',status:'completed',download:'/exports/abc.mp4',snapshot:{timeline:{id:1},subtitles:[{text:'old'}]}}]};
const ctx={state,song:()=>'mine',esc:x=>String(x).replaceAll('<','&lt;'),message:()=>{},creatorOutputTest:()=>false,creatorDiagnostic:()=>'',creatorError:()=>({message:'결과 연결 확인 필요'}),$:k=>k.endsWith(' track')?null:(nodes[k]||=( {dataset:{},innerHTML:''}))};vm.createContext(ctx);
for(const name of ['showRenderPreview','imageConnectionMarkup','imageRecoveryMarkup'])vm.runInContext(html.split('\n').find(l=>l.startsWith('function '+name+'(')),ctx);
ctx.showRenderPreview('/exports/abc.mp4');assert(nodes['#downloadPreview'].innerHTML.includes('/exports/abc.vtt'));assert(nodes['#downloadPreview'].innerHTML.includes('승인 자막 v1'));const frozen=nodes['#downloadPreview'].innerHTML;ctx.showRenderPreview('https://foreign.invalid');assert.equal(nodes['#downloadPreview'].innerHTML,frozen);
for(const state of ['unconfigured','unverified','blocked','available']){const out=ctx.imageConnectionMarkup({state,checks:{},available:state==='available'});assert(!out.includes('<button'));assert(!out.includes('data-activate'));assert(out.includes(state==='available'?'입력과 예상 비용':'기존 이미지를 연결'))}
assert(ctx.imageRecoveryMarkup({id:'j',state:'import_blocked',image_recovery:{can_collect:true}}).includes('data-image-recovery="collect"'));assert(!ctx.imageRecoveryMarkup({id:'j',state:'import_blocked',image_recovery:{}}).includes('<button'));assert(html.includes("b.hasAttribute('data-runtime-blocked')"));console.log('pass');'''
  result=subprocess.run(['node','-e',code],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,check=True);self.assertIn('pass',result.stdout)

class CaptionHTTPTest(unittest.TestCase):
 def test_local_vtt_mime_and_incomplete_unknown_host_denials(self):
  from app import server
  from threading import Thread
  from urllib.request import urlopen,Request
  from urllib.error import HTTPError
  with tempfile.TemporaryDirectory() as folder:
   http=server(folder,0);thread=Thread(target=http.serve_forever,daemon=True);thread.start()
   try:
    st=http.store;jid=uuid.uuid4().hex;output=st.root/'exports'/(jid+'.mp4');output.write_bytes(b'synthetic HTTP fixture')
    j=dict(id=jid,status='completed',sha256=hashlib.sha256(output.read_bytes()).hexdigest(),snapshot=dict(shots={},timeline=dict(id=1,approval={'actor':'fixture'}),subtitles=[dict(start=0,end=1,text='HTTP 한글')]))
    with st.connect() as c:c.execute('INSERT INTO jobs VALUES (?,?)',(jid,json.dumps(j)))
    url=f'http://127.0.0.1:{http.server_port}/exports/{jid}.vtt'
    with urlopen(url) as r:self.assertEqual(r.headers['Content-Type'],'text/vtt; charset=utf-8');self.assertIn('HTTP 한글',r.read().decode())
    with self.assertRaises(HTTPError) as error:urlopen(Request(url,headers={'Host':'foreign.invalid'}))
    self.assertEqual(error.exception.code,403)
    with self.assertRaises(HTTPError) as error:urlopen(url.replace(jid,'b'*32))
    self.assertEqual(error.exception.code,404)
    j['status']='running'
    with st.connect() as c:c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(j),jid))
    with self.assertRaises(HTTPError) as error:urlopen(url)
    self.assertEqual(error.exception.code,409)
   finally:http.shutdown();http.server_close();thread.join()
 def test_restricted_principal_cannot_read_legacy_captions(self):
  from app import server
  from threading import Thread
  from urllib.request import urlopen
  from urllib.error import HTTPError
  with tempfile.TemporaryDirectory() as folder:
   http=server(folder,0,permissions=set());thread=Thread(target=http.serve_forever,daemon=True);thread.start()
   try:
    with self.assertRaises(HTTPError) as error:urlopen(f'http://127.0.0.1:{http.server_port}/exports/'+('a'*32)+'.vtt')
    self.assertEqual(error.exception.code,403)
   finally:http.shutdown();http.server_close();thread.join()
