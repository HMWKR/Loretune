"""Isolated stdlib fixtures; no product Store, subprocess providers or network."""
import contextlib,copy,hashlib,importlib.util,io,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch

ENGINE=Path(__file__).resolve().parents[2]/'tools/document-gate/check.py'
spec=importlib.util.spec_from_file_location('document_gate',ENGINE)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class GateTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name).resolve();self.write('docs/current.md','current')
  self.write('kit/docs/current.md','current');self.write('kit/generated/context.md','context')
  self.registry=dict(project_id='fixture-registry',registry_revision=2,objects=[dict(id='D2',kind='Document',canonical_key='Document:current',file='docs/current.md',sha256=gate.digest(b'current'))],heads={'Document:current':'D2'})
  self.registry_save()
  self.policy=dict(schema_version=1,project_id='fixture',scan=dict(roots=['docs'],extensions=['.md']),
    registries=[dict(name='kit',base='kit',path='kit/registry.json',project_id='fixture-registry')],
    documents=[dict(path='docs/current.md',classification='current',registration='required',reason='maintained criterion',registrations=[dict(registry='kit',file='docs/current.md',require_head=True)])],
    contexts=[dict(registry='kit',receipt='kit/generated/context.receipt.json',usage='current',reason='current input')])
  self.save()
 def write(self,path,text):
  p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 def registry_save(self):
  self.write('kit/registry.json',json.dumps(self.registry))
  self.write('kit/generated/context.receipt.json',json.dumps(dict(registry_revision=self.registry['registry_revision'],registry_sha256=gate.digest((self.root/'kit/registry.json').read_bytes()),context_file='generated/context.md',context_sha256=gate.digest(b'context'),heads=self.registry['heads'])))
 def save(self):self.write(gate.POLICY,json.dumps(self.policy))
 def result(self):return gate.check(self.root)
 def codes(self):return {x['code'] for x in self.result()[0]['findings']}
 def test_normal_pass_and_read_only(self):
  before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
  r,code=self.result();self.assertEqual(code,0);self.assertEqual(r['status'],'pass');self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
 def test_required_missing_registration(self):
  self.registry['objects']=[];self.registry['heads']={};self.registry_save()
  self.assertIn('REGISTRATION_MISSING',self.codes())
 def test_modified_registered_hash(self):
  self.write('kit/docs/current.md','changed');self.assertIn('REGISTERED_HASH_CHANGED',self.codes())
 def test_source_drift_even_registered_copy_unchanged(self):
  self.write('docs/current.md','new source');self.assertIn('REGISTERED_SOURCE_OUTDATED',self.codes())
 def test_stale_receipt_and_changed_context(self):
  self.registry['registry_revision']=3;self.write('kit/registry.json',json.dumps(self.registry));self.write('kit/generated/context.md','edited')
  self.assertIn('CONTEXT_STALE',self.codes())
 def test_new_unclassified_document(self):
  self.write('docs/new-plan.md','new');self.assertIn('UNCLASSIFIED_DOCUMENT',self.codes())
 def test_historical_document_needs_no_registration(self):
  self.write('docs/old.md','historical')
  self.policy['documents'].append(dict(path='docs/old.md',classification='historical',registration='not-required',reason='past release evidence only',baseline_sha256=gate.digest(b'historical')));self.save()
  self.assertEqual(self.result()[1],0)
  self.write('docs/old.md','rewritten');self.assertIn('PRESERVED_SOURCE_CHANGED',self.codes())
 def test_legacy_pending_is_not_false_pass(self):
  d=self.policy['documents'][0];d.update(classification='legacy-review-pending',registration='review-pending',baseline_sha256=gate.digest(b'current'));self.save()
  self.assertEqual(self.result()[0]['status'],'review-required');self.assertEqual(self.result()[1],1)
 def test_other_project_not_configured(self):
  with tempfile.TemporaryDirectory() as p:
   r,code=gate.check(Path(p).resolve());self.assertEqual(code,2);self.assertEqual(r['status'],'not-configured');self.assertEqual(list(Path(p).iterdir()),[])
 def test_registry_project_mismatch(self):
  self.registry['project_id']='other';self.registry_save()
  with self.assertRaises(gate.Invalid):self.result()
 def test_secret_excluded_without_open(self):
  self.write('docs/.env.md','DO_NOT_READ_CANARY');self.write('docs/auth.json.md','DO_NOT_READ_CANARY');self.write('docs/credentials/private.md','DO_NOT_READ_CANARY')
  original=gate.read
  def spy(root,path):
   self.assertNotIn('.env',path);self.assertNotIn('auth.json',path);self.assertNotIn('credentials',path);return original(root,path)
  gate.read=spy
  try:self.assertEqual(self.result()[1],0)
  finally:gate.read=original
 def test_semantic_design_token_document_is_not_a_secret(self):
  self.assertFalse(gate.secret('docs/SEMANTIC-TOKEN-SPEC.md'))
  self.assertTrue(gate.secret('docs/api-token.txt'))
 def test_explicit_secret_path_rejected(self):
  self.policy['documents'][0]['path']='docs/.env';self.save()
  with self.assertRaises(gate.Invalid):self.result()
 def test_escape_absolute_and_windows_paths(self):
  for path in ['../other.md','/tmp/other.md','docs/../../other.md','C:/auth.json','docs\\other.md']:
   with self.subTest(path=path),self.assertRaises(gate.Invalid):gate.read(self.root,path)
 def test_symlink_document_and_parent_rejected(self):
  self.write('outside.md','outside');(self.root/'docs/link.md').symlink_to(self.root/'outside.md')
  with self.assertRaises(OSError):gate.read(self.root,'docs/link.md')
  (self.root/'alias').symlink_to(self.root/'kit',target_is_directory=True)
  with self.assertRaises(OSError):gate.read(self.root,'alias/registry.json')
  with self.assertRaises(gate.Invalid):gate.check(self.root/'alias')
 def test_nested_repo_and_worktree_do_not_inherit(self):
  for name,worktree in [('nested',False),('worktree',True)]:
   base=self.root/'docs'/name;base.mkdir()
   if worktree:(base/'.git').write_text('gitdir: /DO/NOT/READ')
   else:(base/'.git').mkdir()
   (base/'private.md').write_text('not ours')
   self.assertEqual(gate.check(base)[1],2)
   with self.assertRaises(gate.Invalid):gate.read(self.root,f'docs/{name}/private.md')
  self.assertEqual(self.result()[1],0)
 def test_no_project_command_execution(self):
  self.policy['command']='touch SHOULD_NOT_EXIST';self.save()
  with self.assertRaises(gate.Invalid):self.result()
  self.assertFalse((self.root/'SHOULD_NOT_EXIST').exists())
 def test_custom_private_exclusion_and_reference_rejected(self):
  self.write('docs/private/note.md','PRIVATE_CANARY')
  self.policy['scan']['exclude']=['docs/private'];self.save()
  self.assertEqual(self.result()[1],0)
  self.registry['objects'][0]['file']='../docs/private/note.md';self.registry_save()
  with self.assertRaises(gate.Invalid):self.result()
 def test_root_document_scan_detects_new_file(self):
  self.policy['scan']['roots']=['.'];self.save();self.write('new-root.md','new')
  self.assertIn('UNCLASSIFIED_DOCUMENT',self.codes())
 def test_existing_hooks_preserved(self):
  p=self.root/'.codex/hooks.json';p.parent.mkdir();p.write_text('{"hooks":{"Stop":[{"hooks":[{"command":"existing"}]}]}}')
  before=p.read_bytes();self.result();self.assertEqual(before,p.read_bytes())
 def test_stop_blocks_once_then_reports_without_loop(self):
  self.write('docs/new.md','new');payload=dict(hook_event_name='Stop',cwd=str(self.root),stop_hook_active=False,transcript_path='/DO/NOT/READ',last_assistant_message='DO NOT READ')
  self.assertEqual(gate.hook(payload)['decision'],'block')
  payload['stop_hook_active']=True;self.assertNotIn('decision',gate.hook(payload))
 def test_invalid_stop_input_is_safe_and_not_pass(self):
  proc=subprocess.run([sys.executable,str(ENGINE),'--hook'],input='{broken',text=True,capture_output=True)
  self.assertEqual(proc.returncode,0);self.assertIn('incomplete',json.loads(proc.stdout)['systemMessage'])
 def test_cli_exit_codes_and_no_content_echo(self):
  self.write('docs/new.md','PRIVATE_CANARY')
  proc=subprocess.run([sys.executable,str(ENGINE),'--root',str(self.root)],capture_output=True,text=True)
  self.assertEqual(proc.returncode,1);self.assertNotIn('PRIVATE_CANARY',proc.stdout+proc.stderr)
 def test_input_changed_during_check_is_not_pass(self):
  original=gate.inventory
  def mutate(root,p):
   result=original(root,p);self.write('docs/current.md','concurrent edit');return result
  gate.inventory=mutate
  try:
   with self.assertRaises(gate.Invalid):self.result()
  finally:gate.inventory=original

 def test_fresh_context_pending_usage_cannot_pass(self):
  self.policy['contexts'][0]['usage']='review-required';self.save()
  result,code=self.result();self.assertEqual(code,1)
  self.assertIn('CONTEXT_REVIEW_REQUIRED',{x['code'] for x in result['findings']})
  self.assertEqual(result['findings'][0]['reasons'],['USAGE_REVIEW_REQUIRED'])
  for resolved in ['current','historical']:
   self.policy['contexts'][0]['usage']=resolved;self.save()
   self.assertEqual(self.result()[1],0)

 def test_pending_classification_cannot_pass_with_exempt_or_valid_registration(self):
  d=self.policy['documents'][0]
  d.update(classification='legacy-review-pending',baseline_sha256=gate.digest(b'current'))
  for registration in ['not-required','required']:
   with self.subTest(registration=registration):
    d['registration']=registration;self.save();result,code=self.result()
    self.assertEqual(code,1);self.assertEqual(result['status'],'review-required')
    self.assertIn('CLASSIFICATION_REVIEW_PENDING',{x['code'] for x in result['warnings']})
  d['classification']='current';self.save();self.assertEqual(self.result()[1],0)

 def assert_invalid_contract(self):
  for mode in ['cli','hook']:
   with self.subTest(mode=mode):
    args=['--root',str(self.root)] if mode=='cli' else ['--hook']
    payload=json.dumps(dict(hook_event_name='Stop',cwd=str(self.root),stop_hook_active=False))
    proc=subprocess.run([sys.executable,'-B',str(ENGINE),*args],input=payload,text=True,capture_output=True,timeout=3)
    self.assertEqual(proc.returncode,3 if mode=='cli' else 0)
    self.assertEqual(proc.stderr,'');self.assertNotIn('PRIVATE_CANARY',proc.stdout)
    result=json.loads(proc.stdout)
    if mode=='cli':self.assertEqual(result['status'],'invalid')
    else:self.assertIn('incomplete',result['systemMessage']);self.assertNotIn('decision',result)

 def test_fifo_rejected_without_waiting_for_writer_cli_and_hook(self):
  for name in ['docs/current.md','kit/registry.json','kit/generated/context.receipt.json',gate.POLICY]:
   with self.subTest(path=name):
    p=self.root/name;original=p.read_bytes();p.unlink();os.mkfifo(p,0o600)
    try:self.assert_invalid_contract()
    finally:p.unlink();p.write_bytes(original)

 def test_fifo_swapped_after_stat_is_rejected_without_blocking(self):
  # Isolated child timeout protects the test runner if NONBLOCK regresses.
  script="""
import importlib.util,os,pathlib,sys
spec=importlib.util.spec_from_file_location('g',sys.argv[1]);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
root=pathlib.Path(sys.argv[2]);original=g.os.open
def swapped(path,flags,*args,**kwargs):
 if path=='current.md':
  (root/'docs/current.md').unlink();os.mkfifo(root/'docs/current.md',0o600)
 return original(path,flags,*args,**kwargs)
g.os.open=swapped
try:g.read(root,'docs/current.md')
except g.Invalid:print('rejected')
else:raise AssertionError('nonregular file accepted')
"""
  proc=subprocess.run([sys.executable,'-B','-c',script,str(ENGINE),str(self.root)],capture_output=True,text=True,timeout=3)
  self.assertEqual(proc.returncode,0,proc.stderr);self.assertEqual(proc.stdout.strip(),'rejected')

 def test_nonregular_file_rejected_before_open_and_limits_preserved(self):
  p=self.root/'docs/device.md';os.mkfifo(p,0o600)
  with patch.object(gate.os,'open',wraps=gate.os.open) as opened:
   with self.assertRaises(gate.Invalid):gate.read(self.root,'docs/device.md')
   self.assertNotIn('device.md',[call.args[0] for call in opened.call_args_list])
  with patch.object(gate,'MAX_BYTES',3):
   with self.assertRaises(gate.Invalid):gate.read(self.root,'docs/current.md')
  with self.assertRaises(gate.Invalid):gate.read(self.root,'docs')

 def test_malformed_registry_shapes_are_structured_and_redacted(self):
  malformed=[None,[],17,'PRIVATE_CANARY']
  malformed += [dict(self.registry,objects=[item]) for item in [None,[],17,'PRIVATE_CANARY',{},dict(kind=None),dict(kind=[])]]
  malformed += [dict(self.registry,heads=h) for h in [None,[],{'Document:current':None},{'Document:current':[]}]]
  malformed += [dict(self.registry,registry_revision=True),dict(self.registry,registry_revision=-1)]
  for value in malformed:
   with self.subTest(shape=type(value).__name__):
    self.write('kit/registry.json',json.dumps(value));self.assert_invalid_contract()

 def test_malformed_document_fields_are_structured_and_redacted(self):
  for field in ['id','canonical_key','file','sha256']:
   for bad in [None,[],{},17,'']:
    with self.subTest(field=field,type=type(bad).__name__):
     doc=dict(self.registry['objects'][0]);doc[field]=bad
     self.write('kit/registry.json',json.dumps(dict(self.registry,objects=[doc])));self.assert_invalid_contract()
  doc=dict(self.registry['objects'][0],sha256='PRIVATE_CANARY')
  self.write('kit/registry.json',json.dumps(dict(self.registry,objects=[doc])));self.assert_invalid_contract()

 def test_malformed_receipt_fields_are_structured_and_redacted(self):
  name='kit/generated/context.receipt.json';receipt=json.loads((self.root/name).read_text())
  malformed=[None,[],17,'PRIVATE_CANARY',{}]
  malformed += [dict(receipt,**{key:bad}) for key in ['context_file','context_sha256','registry_sha256','heads'] for bad in [None,[],17]]
  malformed += [dict(receipt,registry_revision=bad) for bad in [None,[],-1,True]]
  malformed += [dict(receipt,heads={'Document:current':None})]
  for value in malformed:
   with self.subTest(shape=type(value).__name__):
    self.write(name,json.dumps(value));self.assert_invalid_contract()

 def test_valid_other_records_and_receipt_metadata_are_not_reinterpreted(self):
  self.registry['objects'].append(dict(kind='Requirement',id='R1',custom={'not_a_document':None}))
  self.registry_save()
  name='kit/generated/context.receipt.json';receipt=json.loads((self.root/name).read_text())
  receipt['extra_metadata']={'ignored':'PRIVATE_CANARY'};self.write(name,json.dumps(receipt))
  result,code=self.result();self.assertEqual(code,0);self.assertNotIn('PRIVATE_CANARY',json.dumps(result))

 def test_valid_but_different_receipt_revision_is_stale_not_invalid(self):
  name='kit/generated/context.receipt.json';receipt=json.loads((self.root/name).read_text())
  receipt['registry_revision']=17;self.write(name,json.dumps(receipt))
  result,code=self.result();self.assertEqual(code,1)
  self.assertIn('CONTEXT_STALE',{x['code'] for x in result['findings']})
  self.assertEqual(gate.hook(dict(hook_event_name='Stop',cwd=str(self.root),stop_hook_active=False))['decision'],'block')

if __name__=='__main__':unittest.main()
