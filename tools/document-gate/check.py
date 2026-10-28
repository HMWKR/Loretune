#!/usr/bin/env python3
"""Read-only document completion gate. Stdlib; no project code or commands run.

Exit 0 checked, 1 incomplete, 2 not configured, 3 invalid configuration/I/O.
JSON stdout is the evidence. Callers may save it explicitly, never automatically.
"""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

POLICY = '.document-gate.json'
VERSION = '1.0.1'
MAX_BYTES = 12 * 1024 * 1024
MAX_FILES = 6000
SKIP_DIRS = {'.git','.codex','.agents','.aws','.ssh','.venv','venv','node_modules',
             '__pycache__','.pytest_cache','data','dist','build','vendor'}
SECRET = re.compile(r'(^\.env(?:\.|$)|^\.?(?:secrets?|credentials?|passwords?|auth)(?:[._-]|$)|^(?:access|refresh|api)[_-]?tokens?(?:[._-]|$)|^tokens?\.(?:json|txt|ya?ml)$|^id_(rsa|ed25519)$)', re.I)
SECRET_SUFFIXES = {'.pem','.key','.p12','.pfx','.sqlite','.sqlite3','.db'}
CLASSIFICATIONS = {'current','original','historical','evidence','tooling','legacy-review-pending'}

class Invalid(ValueError):pass

def digest(data):return hashlib.sha256(data).hexdigest()

def secret(path):
 return any(SECRET.search(x) or x in {'.aws','.ssh','secrets','credentials'} for x in PurePosixPath(path).parts) or Path(path).suffix.lower() in SECRET_SUFFIXES

def relative(value,allow_secret=False):
 if not isinstance(value,str) or not value or '\\' in value or ':' in value or '\x00' in value:raise Invalid('invalid relative path')
 p=PurePosixPath(value)
 if p.is_absolute() or any(x in {'','..','.'} for x in value.split('/')):raise Invalid('path escape rejected')
 if secret(value) and not allow_secret:raise Invalid('secret path excluded')
 return value

def read(root, value):
 """Walk with directory FDs and NOFOLLOW; never follow project symlinks."""
 parts=relative(value).split('/');fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  for component in parts[:-1]:
   nxt=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
   os.close(fd);fd=nxt
   try:os.stat('.git',dir_fd=fd,follow_symlinks=False)
   except FileNotFoundError:pass
   else:raise Invalid('nested repository excluded')
  before=os.stat(parts[-1],dir_fd=fd,follow_symlinks=False)
  if stat.S_ISLNK(before.st_mode):raise OSError(errno.ELOOP,'symlink file rejected')
  if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:raise Invalid('unsupported or oversized file')
  # Precheck avoids opening devices. NONBLOCK also prevents a FIFO swapped in
  # after stat from waiting for a writer; fstat still validates the opened FD.
  source=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  try:
   meta=os.fstat(source)
   if not stat.S_ISREG(meta.st_mode) or meta.st_size>MAX_BYTES:raise Invalid('unsupported or oversized file')
   chunks=[];size=0
   while True:
    chunk=os.read(source,65536)
    if not chunk:break
    size+=len(chunk)
    if size>MAX_BYTES:raise Invalid('file grew beyond limit')
    chunks.append(chunk)
   end=os.fstat(source)
   if (meta.st_size,meta.st_mtime_ns)!=(end.st_size,end.st_mtime_ns):raise Invalid('file changed during check')
   return b''.join(chunks)
  finally:os.close(source)
 finally:os.close(fd)

def load(root,value):
 try:return json.loads(read(root,value))
 except (json.JSONDecodeError,UnicodeDecodeError) as exc:raise Invalid('invalid JSON') from exc

def find_root(start):
 raw=Path(os.path.abspath(start))
 if any(p.is_symlink() for p in [raw,*raw.parents]):raise Invalid('symlink project root rejected')
 if not raw.is_dir():raise Invalid('project directory missing')
 p=raw
 while True:
  if (p/POLICY).exists() or (p/POLICY).is_symlink():return p
  if (p/'.git').exists() or p==p.parent:return None
  p=p.parent

def exact(obj,required,optional=()):
 if not isinstance(obj,dict) or set(obj)-set(required)-set(optional) or set(required)-set(obj):raise Invalid('unknown or missing policy fields; commands are unsupported')

def text_field(obj,key):
 value=obj.get(key)
 if not isinstance(value,str) or not value.strip():raise Invalid('invalid registry or receipt text field')
 return value

def hash_field(obj,key):
 if not re.fullmatch(r'[a-f0-9]{64}',text_field(obj,key)):raise Invalid('invalid registry or receipt hash')

def validate_heads(heads):
 if not isinstance(heads,dict) or any(not isinstance(k,str) or not k.strip() or not isinstance(v,str) or not v.strip() for k,v in heads.items()):raise Invalid('invalid registry or receipt heads')

def validate_registry(r):
 """Validate fields used below; never interpret unrelated record payloads."""
 if not isinstance(r,dict):raise Invalid('invalid registry object')
 text_field(r,'project_id')
 if not isinstance(r.get('objects'),list) or type(r.get('registry_revision')) is not int or r['registry_revision']<0:raise Invalid('unsupported registry schema')
 validate_heads(r.get('heads'))
 for item in r['objects']:
  if not isinstance(item,dict):raise Invalid('invalid registry record')
  if text_field(item,'kind')=='Document':
   text_field(item,'id');text_field(item,'canonical_key')
   relative(text_field(item,'file'));hash_field(item,'sha256')

def validate_receipt(r):
 if not isinstance(r,dict):raise Invalid('invalid receipt object')
 if type(r.get('registry_revision')) is not int or r['registry_revision']<0:raise Invalid('invalid receipt revision')
 relative(text_field(r,'context_file'))
 hash_field(r,'context_sha256');hash_field(r,'registry_sha256')
 validate_heads(r.get('heads',{}))

def validate_policy(p):
 exact(p,{'schema_version','project_id','scan','registries','documents','contexts'})
 if p['schema_version']!=1 or not isinstance(p['project_id'],str) or not p['project_id']:raise Invalid('unsupported policy identity')
 exact(p['scan'],{'roots','extensions'}, {'exclude'})
 if not isinstance(p['scan']['roots'],list) or not p['scan']['roots']:raise Invalid('scan roots required')
 for x in p['scan']['roots']:
  if x!='.':relative(x)
 for x in p['scan'].get('exclude',[]):relative(x,allow_secret=True)
 if not isinstance(p['scan']['extensions'],list) or not set(p['scan']['extensions'])<={'.md','.txt','.pdf','.docx','.yaml','.yml'}:raise Invalid('unsupported document extensions')
 if not isinstance(p['registries'],list) or not isinstance(p['documents'],list) or not isinstance(p['contexts'],list):raise Invalid('policy lists required')
 names=set()
 for r in p['registries']:
  exact(r,{'name','base','path','project_id'})
  if not isinstance(r['name'],str) or r['name'] in names:raise Invalid('duplicate registry')
  names.add(r['name']);relative(r['base']);relative(r['path'])
  if not r['path'].startswith(r['base']+'/'):raise Invalid('registry outside declared base')
 paths=set()
 for d in p['documents']:
  exact(d,{'path','classification','registration','reason'}, {'baseline_sha256','registrations'})
  relative(d['path'])
  if any(d['path']==x or d['path'].startswith(x+'/') for x in p['scan'].get('exclude',[])):raise Invalid('classified document conflicts with exclusion')
  if d['path'] in paths:raise Invalid('duplicate document')
  paths.add(d['path'])
  if d['classification'] not in CLASSIFICATIONS or d['registration'] not in {'required','not-required','review-pending'} or not isinstance(d['reason'],str) or not d['reason'].strip():raise Invalid('classification and rationale required')
  if d['registration']=='required':
   if not d.get('registrations'):raise Invalid('registration targets required')
   seen=set()
   for ref in d['registrations']:
    exact(ref,{'registry','file','require_head'})
    if ref['registry'] not in names or ref['registry'] in seen or type(ref['require_head']) is not bool:raise Invalid('invalid registry target')
    seen.add(ref['registry']);relative(ref['file'])
  if d['classification'] in {'original','historical','legacy-review-pending'} and not re.fullmatch(r'[a-f0-9]{64}',d.get('baseline_sha256','')):raise Invalid('preserved/review-pending file needs a baseline')
 for c in p['contexts']:
  exact(c,{'registry','receipt','usage','reason'})
  if c['registry'] not in names or c['usage'] not in {'current','historical','review-required'} or not c['reason']:raise Invalid('context classification required')
  relative(c['receipt'])

def inventory(root,p):
 found=set();excluded=[]
 def omitted(rel):return any(rel==x or rel.startswith(x+'/') for x in p['scan'].get('exclude',[]))
 for scope in p['scan']['roots']:
  path=root/scope
  if path.is_symlink():raise Invalid('symlink scan root')
  if omitted(scope):continue
  if path.is_file():
   if not secret(scope) and path.suffix.lower() in p['scan']['extensions']:found.add(scope)
   continue
  if not path.is_dir():raise Invalid('scan root missing')
  for folder,dirs,files in os.walk(path,followlinks=False):
   current=Path(folder)
   if current!=root and (current/'.git').exists():
    excluded.append({'path':current.relative_to(root).as_posix(),'reason':'nested-repository'});dirs[:]=[];continue
   kept=[]
   for name in sorted(dirs):
    child=current/name;rel=child.relative_to(root).as_posix()
    if name in SKIP_DIRS or secret(rel) or child.is_symlink() or omitted(rel):continue
    kept.append(name)
   dirs[:]=kept
   for name in sorted(files):
    child=current/name;rel=child.relative_to(root).as_posix()
    if child.suffix.lower() not in p['scan']['extensions'] or secret(rel) or omitted(rel):continue
    if child.is_symlink():
     excluded.append({'path':rel,'reason':'symlink'});continue
    found.add(rel)
    if len(found)>MAX_FILES:raise Invalid('document count exceeds bound')
 return found,excluded

def check(start):
 root=find_root(start)
 if root is None:return dict(status='not-configured',schema_version=1,engine=VERSION,reason='No project document policy. Do not create a registry automatically.'),2
 policy_bytes=read(root,POLICY);p=json.loads(policy_bytes);validate_policy(p)
 findings=[];warnings=[];inputs={POLICY:digest(policy_bytes)};stats={'registered_documents_checked':0,'documents_classified':len(p['documents']),'receipts_checked':0}
 def issue(code,path,**detail):findings.append(dict(code=code,path=path,**detail))
 def hashed(path):
  if any(path==x or path.startswith(x+'/') for x in p['scan'].get('exclude',[])):raise Invalid('excluded file referenced by policy or registry')
  raw=read(root,path);sha=digest(raw);inputs[path]=sha;return raw,sha
 registries={}
 for spec in p['registries']:
  raw,sha=hashed(spec['path']);r=json.loads(raw);validate_registry(r)
  if r.get('project_id')!=spec['project_id']:raise Invalid('registry project identity mismatch')
  docs=[d for d in r['objects'] if d.get('kind')=='Document']
  registries[spec['name']]=(spec,r,docs,sha)
  for d in docs:
   path=spec['base']+'/'+relative(d['file'])
   try:_,actual=hashed(path)
   except FileNotFoundError:issue('REGISTERED_FILE_MISSING',path,registry=spec['name']);continue
   stats['registered_documents_checked']+=1
   if actual!=d.get('sha256'):issue('REGISTERED_HASH_CHANGED',path,registry=spec['name'],record=d.get('id'))
 for d in p['documents']:
  path=d['path']
  try:_,actual=hashed(path)
  except FileNotFoundError:issue('CLASSIFIED_FILE_MISSING',path);continue
  if d.get('baseline_sha256') and actual!=d['baseline_sha256']:
   issue('CLASSIFICATION_REVIEW_REQUIRED' if d['classification']=='legacy-review-pending' else 'PRESERVED_SOURCE_CHANGED',path)
  if d['classification']=='legacy-review-pending':warnings.append(dict(code='CLASSIFICATION_REVIEW_PENDING',path=path))
  if d['registration']=='review-pending':warnings.append(dict(code='REGISTRATION_REVIEW_PENDING',path=path))
  if d['registration']!='required':continue
  for target in d['registrations']:
   spec,r,docs,sha=registries[target['registry']]
   hits=[x for x in docs if x.get('file')==target['file'] and (not target['require_head'] or r['heads'].get(x.get('canonical_key'))==x.get('id'))]
   if not hits:issue('REGISTRATION_MISSING',path,registry=spec['name'],target_file=target['file']);continue
   if len(hits)!=1:issue('REGISTRATION_AMBIGUOUS',path,registry=spec['name']);continue
   if hits[0].get('sha256')!=actual:issue('REGISTERED_SOURCE_OUTDATED',path,registry=spec['name'])
 for ctx in p['contexts']:
  spec,r,docs,sha=registries[ctx['registry']]
  raw,_=hashed(ctx['receipt']);receipt=json.loads(raw);validate_receipt(receipt);stats['receipts_checked']+=1
  file=spec['base']+'/'+relative(receipt['context_file'])
  _,context_sha=hashed(file)
  reasons=[]
  if ctx['usage']=='review-required':reasons.append('USAGE_REVIEW_REQUIRED')
  if context_sha!=receipt.get('context_sha256'):reasons.append('CONTEXT_BYTES_CHANGED')
  if sha!=receipt.get('registry_sha256') or r['registry_revision']!=receipt.get('registry_revision'):reasons.append('REGISTRY_CHANGED')
  if any(r['heads'].get(k)!=v for k,v in receipt.get('heads',{}).items()):reasons.append('HEAD_CHANGED')
  # Exact registry bytes bind selected record fingerprints too; no local import
  # or execution of kb.py from an untrusted project's policy is needed.
  if reasons:
   item=dict(code='CONTEXT_REVIEW_REQUIRED' if ctx['usage']=='review-required' else 'CONTEXT_STALE',path=ctx['receipt'],reasons=reasons)
   (warnings if ctx['usage']=='historical' else findings).append(item)
 found,excluded=inventory(root,p);known={d['path'] for d in p['documents']}
 for path in sorted(found-known):issue('UNCLASSIFIED_DOCUMENT',path)
 # Detect ordinary concurrent edits; this is a verified snapshot, not a lock.
 for path,expected in list(inputs.items()):
  if digest(read(root,path))!=expected:raise Invalid('input changed during validation; rerun after edits settle')
 status='blocked' if findings else 'review-required' if warnings else 'pass'
 result=dict(schema_version=1,engine=VERSION,status=status,root=str(root),project_id=p['project_id'],
  policy_sha256=digest(policy_bytes),stats=stats,findings=findings,warnings=warnings,excluded=excluded,
  inputs=inputs,verification_scope='classification, membership, bytes and receipt freshness; not semantic truth, product ontology or implementation acceptance')
 result['evidence_sha256']=digest(json.dumps(result,sort_keys=True,separators=(',',':')).encode())
 return result,1 if findings or warnings else 0

def hook(payload):
 # No transcript/tool input/assistant text is read or retained.
 if not isinstance(payload,dict) or payload.get('hook_event_name')!='Stop' or not isinstance(payload.get('cwd'),str):raise Invalid('invalid Stop input')
 result,code=check(payload['cwd'])
 if code==2:return {'systemMessage':'Document gate: not-configured. No registry or project files were created.'}
 if not code:return {'systemMessage':'Document gate passed for the configured scope; evidence '+result['evidence_sha256']}
 summary='Document gate: '+result['status']+'. Run the read-only checker, report gaps and request any required registration approval. Do not auto-register or promote documents.'
 # Only one continuation per turn. Returning a warning afterward avoids an
 # infinite cost loop. Native Stop is not an unbypassable CI completion gate.
 if payload.get('stop_hook_active'):return {'systemMessage':summary+' Continued once already; report incomplete status honestly.'}
 return {'decision':'block','reason':summary}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',default=os.getcwd());parser.add_argument('--hook',action='store_true');args=parser.parse_args()
 try:
  if args.hook:
   raw=sys.stdin.buffer.read(65537)
   if len(raw)>65536:raise Invalid('hook payload too large')
   result=hook(json.loads(raw));code=0
  else:result,code=check(args.root)
 except (Invalid,OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
  # Never echo file contents or arbitrary exception text from a project.
  result={'status':'invalid','error':'Policy, path, identity, input stability or JSON validation failed. No project mutation occurred.'};code=3
  if args.hook:result={'systemMessage':'Document gate could not validate this project. Report the gate as incomplete; do not claim pass.'};code=0
 print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2));return code

if __name__=='__main__':raise SystemExit(main())
