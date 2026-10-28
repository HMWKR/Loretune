"""Experimental local still scenes with quarantined static assets and approvals.

Only server-provided trusted configuration can activate rendering.  The file
store and SQLite cannot form a single transaction; an unreferenced staging
file is never served and must not be treated as an approved result.
"""
from copy import deepcopy
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import time
import uuid

import chat_sessions
import contracts
import guided
import ontology
import production_context
import project_ontology
import scene_spec
import scene_assets
import scene_renderer
from loretune import Conflict

# Two copies of an 8 MiB validated image plus conservative per-job bookkeeping.
RESERVATION_BYTES = 18 * 1024 * 1024
MAX_MODEL_ASSETS = 32
MAX_MODEL_STORAGE_BYTES = 64 * 1024 * 1024
MAX_LINEAGE_NODES = 4096


def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS scene_records (id TEXT PRIMARY KEY, project TEXT NOT NULL, conversation TEXT NOT NULL, shot TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(project,conversation,shot))')
    c.execute('CREATE TABLE IF NOT EXISTS scene_proposals (id TEXT PRIMARY KEY, scene TEXT NOT NULL, conversation TEXT NOT NULL, body TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS scene_reservations (job TEXT PRIMARY KEY, bytes INTEGER NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS scene_asset_refs (filename TEXT PRIMARY KEY, sha256 TEXT NOT NULL, job TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS scene_model_assets (id TEXT PRIMARY KEY, project TEXT NOT NULL, conversation TEXT NOT NULL, sha256 TEXT NOT NULL, filename TEXT NOT NULL, rights TEXT NOT NULL, metadata TEXT NOT NULL, created REAL NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS scene_asset_dependencies (derived_sha TEXT NOT NULL, source_sha TEXT NOT NULL, PRIMARY KEY(derived_sha,source_sha))')


def _required_sources(c, sha):
    """Reconcile derivative links with the frozen render record, not just edges."""
    required=set()
    for row in c.execute('SELECT j.body FROM scene_asset_refs AS r LEFT JOIN jobs AS j ON j.id=r.job WHERE r.sha256=?',(sha,)):
        try:
            job=json.loads(row[0])
            if job.get('kind')!='local-3d-still' or job.get('status')!='completed' or job.get('sha256')!=sha:raise ValueError()
            references=scene_spec.asset_references(job['scene'])
            if job.get('assets',[])!=references or job['approval']['scene_hash']!=scene_spec.fingerprint(job['scene']):raise ValueError()
            for ref in references:
                original=c.execute('SELECT sha256,project,conversation FROM scene_model_assets WHERE id=?',(ref['id'],)).fetchone()
                if (not original or original[0]!=ref['sha256'] or original[1]!=job['approval']['binding']['project_id'] or
                    original[2]!=job['conversation_id']):raise ValueError()
                required.add(ref['sha256'])
        except (ValueError,TypeError,KeyError,IndexError):raise ValueError('3D 원본과 결과의 권리 연결을 재확인하세요.') from None
    return required


def source_hashes(c, hashes, *, verify_links=True):
    """Expand the source-rights dependency graph without trusting a shallow Take."""
    pending=[(sha,False) for sha in hashes];seen=set()
    dependencies=bool(c.execute("SELECT 1 FROM sqlite_master WHERE name='scene_asset_dependencies'").fetchone())
    while pending:
        sha,dependency=pending.pop()
        if type(sha) is not str or dependency and not re.fullmatch(r'[a-f0-9]{64}',sha):raise ValueError('자산 권리 연결을 확인하세요.')
        if sha in seen:continue
        seen.add(sha)
        if len(seen)>MAX_LINEAGE_NODES:raise ValueError('자산 권리 연결이 지원 범위를 넘었습니다.')
        if dependencies:
            actual={row[0] for row in c.execute('SELECT source_sha FROM scene_asset_dependencies WHERE derived_sha=?',(sha,))}
            try:required=_required_sources(c,sha)
            except ValueError:
                if verify_links:raise
                required=set()
            if verify_links and not required<=actual:raise ValueError('3D 원본과 결과의 권리 연결을 재확인하세요.')
            pending.extend((source,True) for source in actual|required)
    return seen


def _model_root(store):
    path=store.root/'model-assets'
    if path.is_symlink():raise ValueError('3D 자산 저장 경로를 확인하세요.')
    path.mkdir(mode=0o700,exist_ok=True)
    if not path.is_dir() or path.resolve().parent!=store.root:raise ValueError('3D 자산 저장 경로를 확인하세요.')
    return path


def _model_bytes(store, sha):
    path=_model_root(store)/(sha+'.glb')
    if path.is_symlink():raise ValueError('3D 자산 원본을 확인하세요.')
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
    try:
        fd=os.open(path,flags)
        with os.fdopen(fd,'rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size>scene_assets.MAX_BYTES:raise ValueError('3D 자산 크기 또는 형식을 확인하세요.')
            raw=stream.read(scene_assets.MAX_BYTES+1)
    except OSError:raise ValueError('3D 자산 원본을 다시 가져오세요.') from None
    if len(raw)>scene_assets.MAX_BYTES or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('3D 자산 원본이 변경되었습니다.')
    return path,raw


def public_assets(c,store,name,conversation):
    pid=contracts.project_id(store.workspace_id,name)
    values=[]
    for row in c.execute('SELECT id,sha256,filename,rights,metadata,created FROM scene_model_assets WHERE project=? AND conversation=? ORDER BY rowid',(pid,conversation)):
        identifier,sha,filename,rights,encoded,created=row
        blocked=False
        try:store.check_rights(c,[sha])
        except ValueError:blocked=True
        values.append(dict(id=identifier,sha256=sha,profile=json.loads(encoded)['profile'],filename=filename,rights=rights,metadata=json.loads(encoded),created=created,blocked=blocked))
    return values


def import_asset(c,store,p,name,data):
    _exact(data,('song','filename','content','rights'))
    pid,cid,_=_scope(c,store,p,name)
    filename,rights,content=data['filename'],data['rights'],data['content']
    if (type(filename) is not str or not 1<=len(filename)<=200 or Path(filename).name!=filename or '/' in filename or '\\' in filename or '\x00' in filename or Path(filename).suffix.lower()!='.glb'):
        raise ValueError('GLB 파일 이름을 확인하세요.')
    if type(rights) is not str or not rights.strip() or len(rights)>2000:raise ValueError('3D 자산의 사용권 근거를 입력하세요.')
    if type(content) is not str or len(content)>((scene_assets.MAX_BYTES+2)//3)*4:raise ValueError('3D 자산은 8 MiB 이하의 GLB만 지원합니다.')
    try:raw=base64.b64decode(content,validate=True)
    except (ValueError,TypeError):raise ValueError('3D 파일 데이터를 확인하세요.') from None
    metadata=scene_assets.validate_glb(raw);sha=metadata['sha256']
    rows=c.execute('SELECT id,sha256,metadata,rights FROM scene_model_assets WHERE project=? AND conversation=?',(pid,cid)).fetchall()
    existing=next((r for r in rows if r[1]==sha and r[3]==rights.strip()),None)
    if existing:
        _model_bytes(store,sha)
        return next(a for a in public_assets(c,store,name,cid) if a['id']==existing[0])
    if len(rows)>=MAX_MODEL_ASSETS:raise ValueError('이 대화의 3D 자산 개수 한도를 확인하세요.')
    if sum(json.loads(r[2])['byte_length'] for r in rows)+len(raw)>MAX_MODEL_STORAGE_BYTES:raise ValueError('이 대화의 3D 자산 저장 한도가 부족합니다.')
    folder=_model_root(store);path=folder/(sha+'.glb')
    with tempfile.NamedTemporaryFile(dir=folder,prefix='.model-upload-',delete=False) as output:
        staged=Path(output.name);output.write(raw);output.flush();os.fsync(output.fileno())
    try:
        staged.chmod(0o400)
        try:os.link(staged,path,follow_symlinks=False)
        except FileExistsError:_model_bytes(store,sha)
    finally:staged.unlink(missing_ok=True)
    identifier=uuid.uuid4().hex
    c.execute('INSERT INTO scene_model_assets VALUES (?,?,?,?,?,?,?,?)',(identifier,pid,cid,sha,filename,rights.strip(),json.dumps(metadata),time.time()))
    return next(a for a in public_assets(c,store,name,cid) if a['id']==identifier)


def resolve_assets(c,store,pid,conversation,scene,*,require_rights=True):
    """Resolve only scoped, approved-byte references; never accept client paths."""
    inputs=[]
    for ref in scene_spec.asset_references(scene):
        row=c.execute('SELECT sha256,rights,metadata FROM scene_model_assets WHERE id=? AND project=? AND conversation=?',(ref['id'],pid,conversation)).fetchone()
        if not row or row[0]!=ref['sha256'] or ref['profile'] not in scene_assets.SUPPORTED_PROFILES or ref['profile']!=json.loads(row[2])['profile']:raise ValueError('현재 작품·대화에 가져온 3D 자산을 선택하세요.')
        if require_rights and (row[1]=='사용권 미확인' or not row[1].strip()):raise ValueError('3D 자산 사용권을 확인한 뒤 구도를 승인하세요.')
        store.check_rights(c,[row[0]])
        path,raw=_model_bytes(store,row[0]);metadata=scene_assets.validate_glb(raw)
        if metadata!=json.loads(row[2]):raise ValueError('3D 자산 검증 기록이 변경되었습니다.')
        inputs.append(dict(ref,path=str(path)))
    return inputs


def tree_manifest(root):
    """Hash an explicitly trusted local installation, including symlink targets.

    This detects ordinary drift, not hostile concurrent modification by a local
    administrator. Do not use with an untrusted or remotely writable tree.
    """
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('3D 설치 경로를 확인하세요.')
    h=hashlib.sha256()
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs.sort();files.sort()
        for name in dirs+files:
            path=Path(folder)/name;rel=path.relative_to(root).as_posix();info=path.lstat()
            if stat.S_ISLNK(info.st_mode):
                target=os.readlink(path)
                try:path.resolve(strict=True).relative_to(root)
                except (ValueError,OSError):raise ValueError('설치 경로 밖 심볼릭 링크는 허용되지 않습니다.')
                h.update(b'L\0'+rel.encode()+b'\0'+os.fsencode(target)+b'\0')
            elif stat.S_ISDIR(info.st_mode):h.update(b'D\0'+rel.encode()+b'\0')
            elif stat.S_ISREG(info.st_mode):
                h.update(b'F\0'+rel.encode()+b'\0'+str(info.st_size).encode()+b'\0')
                with path.open('rb') as src:
                    for chunk in iter(lambda:src.read(1024*1024),b''):h.update(chunk)
            else:raise ValueError('지원하지 않는 설치 파일 형식입니다.')
    return h.hexdigest()


def runtime_binding(store, *, verify_tree=True):
    import scene_renderer
    config=store.scene_configuration
    if not isinstance(config,dict) or set(config)!={'renderer','quota_bytes','tree_sha256'}:
        raise ValueError('3D 로컬 렌더 환경이 설정되지 않았습니다.')
    renderer=config['renderer'];quota=config['quota_bytes'];digest=config['tree_sha256']
    if type(quota) is not int or not RESERVATION_BYTES<=quota<=2**53:
        raise ValueError('3D 저장 한도를 확인하세요.')
    if not isinstance(digest,str) or not re.fullmatch(r'[a-f0-9]{64}',digest):
        raise ValueError('신뢰된 3D 설치 검증값이 필요합니다.')
    root,_,_=scene_renderer._configuration(renderer)
    if verify_tree and tree_manifest(root)!=digest:
        raise ValueError('승인된 3D 설치 환경이 변경되었습니다.')
    return dict(image_id=renderer.image_id, blender_sha256=renderer.blender_sha256,
                tree_sha256=digest, renderer_fingerprint=scene_renderer.renderer_fingerprint(), docker_socket=str(Path(renderer.docker_socket).resolve()),
                timeout_seconds=renderer.timeout_seconds,quota_bytes=quota)


def capability(store):
    """Cheap, non-secret configuration status; each request performs full verification."""
    import scene_renderer
    config=store.scene_configuration
    unavailable=lambda reason:dict(available=False,mode='disconnected',reason=reason,external_transmission=False)
    if config is None:return unavailable('로컬 3D 렌더 환경이 설정되지 않았습니다.')
    try:
        if type(config) is not dict or set(config)!={'renderer','quota_bytes','tree_sha256'}:raise ValueError()
        renderer=config['renderer']
        if (not isinstance(renderer,scene_renderer.RendererConfig) or type(config['quota_bytes']) is not int or
            not RESERVATION_BYTES<=config['quota_bytes']<=2**53 or not isinstance(config['tree_sha256'],str) or
            not re.fullmatch(r'[a-f0-9]{64}',config['tree_sha256']) or
            not isinstance(renderer.image_id,str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',renderer.image_id) or
            not isinstance(renderer.blender_sha256,str) or not re.fullmatch(r'[a-f0-9]{64}',renderer.blender_sha256) or
            type(renderer.timeout_seconds) not in (int,float) or not 0<renderer.timeout_seconds<=scene_renderer.TIMEOUT_SECONDS):raise ValueError()
        binary=Path(renderer.blender_root).resolve(strict=True)/'blender'
        sock=Path(renderer.docker_socket).resolve(strict=True)
        if binary.is_symlink() or not binary.is_file() or not stat.S_ISSOCK(sock.stat().st_mode) or not shutil.which('docker') or not shutil.which('ffmpeg'):raise ValueError()
    except (TypeError,ValueError,OSError,RuntimeError):return unavailable('로컬 3D 환경 설정 또는 실행 도구를 확인하세요.')
    return dict(available=True,mode='configured-preflight-required',reason='요청 시 설치·권한·저장 한도를 다시 검사합니다.',external_transmission=False)


def _exact(value, fields):
    if type(value) is not dict or set(value)!=set(fields):raise ValueError('3D 요청 형식을 확인하세요.')


def _row(c, table, identifier):
    if table not in {'scene_records','scene_proposals'}:raise ValueError('unsupported record')
    row=c.execute('SELECT body FROM '+table+' WHERE id=?',(identifier,)).fetchone()
    if not row:raise ValueError('현재 대화의 3D 구도를 찾을 수 없습니다.')
    return json.loads(row[0])


def _save(c,table,item):
    if table=='scene_records':
        c.execute('INSERT INTO scene_records VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                  (item['id'],item['project_id'],item['conversation_id'],item['shot_id'],json.dumps(item,ensure_ascii=False)))
    elif table=='scene_proposals':
        c.execute('INSERT INTO scene_proposals VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                  (item['id'],item['scene_id'],item['conversation_id'],json.dumps(item,ensure_ascii=False)))
    else:raise ValueError('unsupported record')


def _scope(c,store,p,name):
    pid=contracts.project_id(store.workspace_id,name);cid=chat_sessions.current(p)
    chat_sessions.resolve(p,cid)
    revision=ontology.snapshot(c,project_ontology.scope(store.workspace_id,pid))['revision']
    return pid,cid,revision


def _current(c,store,p,name,identifier):
    pid,cid,onto=_scope(c,store,p,name);record=_row(c,'scene_records',identifier)
    if record['project_id']!=pid or record['conversation_id']!=cid:raise ValueError('다른 작품 또는 대화의 구도입니다.')
    shot=production_context.shot_key(p,record['shot_id'])
    return record,shot,onto


def _context(p,shot):
    shot_record=p['shots'][shot]
    value=dict(shot_id=production_context.shot_id(p,shot),description=shot_record['description'],canon=guided.context(p),renderer_fingerprint=scene_renderer.renderer_fingerprint())
    # Renderer or semantic-context changes require an explicit new approval.
    if 'semantic_context' in shot_record:value['semantic_context']=deepcopy(shot_record['semantic_context'])
    return guided.fingerprint(value)


def _register_grant_owner(p,conversation,identifier):
    """Bind a server-created 3D grant to its conversation in the state transaction."""
    owners=p.setdefault('conversation_owners',{})
    existing=owners.get(identifier)
    if existing and (existing.get('conversation_id')!=conversation or existing.get('kind')!='scene_grants'):
        raise ValueError('다른 대화 또는 작업에 속한 승인입니다.')
    owners[identifier]=dict(conversation_id=conversation,kind='scene_grants')


def _approved_ontology(version):
    # Legacy heads without a recorded binding degrade to "needs review" instead of failing the read.
    approval=version.get('approval') if isinstance(version.get('approval'),dict) else {}
    binding=approval.get('binding') if isinstance(approval.get('binding'),dict) else {}
    return binding.get('ontology_revision')


def public(c,store,p,name,conversation):
    pid=contracts.project_id(store.workspace_id,name)
    # Review and render also refuse an ontology revision change (scene_review, require_approval).
    onto=ontology.snapshot(c,project_ontology.scope(store.workspace_id,pid))['revision']
    records=[json.loads(row[0]) for row in c.execute('SELECT body FROM scene_records WHERE project=? AND conversation=? ORDER BY rowid',(pid,conversation))]
    for record in records:
        # A manually added shot may use a derived stable ID rather than storing
        # it in the shot record; resolve its current display name server-side.
        try:record['shot']=production_context.shot_key(p,record['shot_id'])
        except ValueError:record['shot']=None
        record['proposals']=[json.loads(row[0]) for row in c.execute('SELECT body FROM scene_proposals WHERE scene=? AND conversation=? ORDER BY rowid',(record['id'],conversation))]
        context=_context(p,record['shot']) if record['shot'] is not None else None
        for item in record['versions']:
            item['requires_review']=item.get('context')!=context or _approved_ontology(item)!=onto
        for item in record['proposals']:
            item['requires_review']=item.get('context')!=context or item.get('ontology_revision')!=onto
    return records


def status(c,store,p,name,conversation):
    """Model-facing summary of public(): no grant ids, asset references or scene bodies.

    As in Scene Studio, only proposed/held proposals on the current head are pending;
    older ones can no longer be approved and are only counted. requires_review comes
    from public(), which also flags an ontology revision change."""
    values=[]
    for record in public(c,store,p,name,conversation):
        version=next((v for v in record['versions'] if v['id']==record['head']),None)
        open_=[x for x in record['proposals'] if x['status'] in {'proposed','held'}]
        pending=[x for x in open_ if x['base_revision']==record['head']]
        stale=[version['requires_review']] if version else []
        stale+=[x['requires_review'] for x in pending]
        values.append(dict(scene_id=record['id'],shot_id=record['shot_id'],head=record['head'],
            approval_status='none' if version is None else 'stale_context' if stale[0] else 'recorded',
            requires_review=any(stale),
            pending_proposals=[dict(proposal_id=x['id'],base_revision=x['base_revision'],status=x['status']) for x in pending][-10:],
            pending_total=len(pending),pending_truncated=len(pending)>10,stale_total=len(open_)-len(pending)))
    return values


def handle(c,store,p,name,action,data,*,origin=None):
    pid,cid,onto=_scope(c,store,p,name)
    if action=='scene_create':
        _exact(data,('song','shot_id','scene'))
        shot=production_context.shot_key(p,data['shot_id']);shotid=production_context.shot_id(p,shot)
        if c.execute('SELECT 1 FROM scene_records WHERE project=? AND conversation=? AND shot=?',(pid,cid,shotid)).fetchone():
            raise ValueError('이 대화의 장면에는 이미 3D 구도가 있습니다.')
        value=scene_spec.validate(data['scene']);resolve_assets(c,store,pid,cid,value,require_rights=False);sid=uuid.uuid4().hex
        record=dict(id=sid,project_id=pid,conversation_id=cid,shot_id=shotid,head=0,versions=[])
        proposal=dict(id=uuid.uuid4().hex,scene_id=sid,conversation_id=cid,base_revision=0,scene=value,scene_hash=scene_spec.fingerprint(value),context=_context(p,shot),ontology_revision=onto,status='proposed',created=time.time())
        _save(c,'scene_records',record);_save(c,'scene_proposals',proposal)
        return dict(scene_id=sid,proposal_id=proposal['id'],status='proposed')
    if action=='scene_review':
        _exact(data,('song','scene_proposal_id','decision'))
        item=_row(c,'scene_proposals',data['scene_proposal_id']);record,shot,current_onto=_current(c,store,p,name,item['scene_id'])
        if item['conversation_id']!=cid or data['decision'] not in {'approved','held','rejected'}:raise ValueError('변경안을 다시 확인하세요.')
        if item['status']=='applied':
            if data['decision']!='approved':raise ValueError('적용된 구도는 새 변경안으로 수정하세요.')
            version=next((v for v in record['versions'] if v['id']==item['applied_revision']),None)
            if not version:raise ValueError('승인된 구도 버전을 확인하세요.')
            if version['context']!=_context(p,shot):raise Conflict('실행 기준이 변경되었습니다. 새 변경안으로 다시 승인하세요.')
            _register_grant_owner(p,cid,version['approval']['id'])
            return dict(scene_id=record['id'],revision=item['applied_revision'],status='applied')
        if item['status']=='superseded':raise ValueError('교체된 변경안입니다. 최신 변경안을 검토하세요.')
        if data['decision']=='approved':
            if record['head']!=item['base_revision'] or _context(p,shot)!=item['context'] or current_onto!=item['ontology_revision']:raise Conflict('구도 또는 작품 설정이 변경되었습니다.')
            scene=scene_spec.validate(item['scene']);resolve_assets(c,store,pid,cid,scene);revision=record['head']+1
            binding=dict(workspace_id=store.workspace_id,project_id=pid,shot_id=record['shot_id'],scene_id=record['id'],revision=revision,ontology_revision=onto)
            approval=dict(id=uuid.uuid4().hex,actor='local-owner',scope='local-3d-still',binding=binding,scene_hash=scene_spec.fingerprint(scene))
            _register_grant_owner(p,cid,approval['id'])
            version=dict(id=revision,scene=scene,scene_hash=approval['scene_hash'],approval=approval,context=item['context'],created=time.time())
            record['versions'].append(version);record['head']=revision;item.update(status='applied',applied_revision=revision)
            _save(c,'scene_records',record)
        else:item['status']=data['decision']
        _save(c,'scene_proposals',item)
        return dict(scene_id=record['id'],revision=item.get('applied_revision'),status=item['status'])
    if action=='scene_replace_draft':
        _exact(data,('song','scene_id','scene_proposal_id','base_revision','scene'))
        record,shot,current_onto=_current(c,store,p,name,data['scene_id'])
        if type(data['base_revision']) is not int or data['base_revision']!=0 or record['head']!=0:
            raise Conflict('구도가 이미 승인되었거나 변경되었습니다.')
        old=_row(c,'scene_proposals',data['scene_proposal_id'])
        if old.get('scene_id')!=record['id'] or old.get('conversation_id')!=cid or old.get('base_revision')!=0 or old.get('status') not in {'proposed','held','rejected'}:
            raise ValueError('현재 대화의 변경 가능한 첫 구도만 교체할 수 있습니다.')
        value=scene_spec.validate(data['scene']);resolve_assets(c,store,pid,cid,value,require_rights=False)
        item=dict(id=uuid.uuid4().hex,scene_id=record['id'],conversation_id=cid,base_revision=0,scene=value,scene_hash=scene_spec.fingerprint(value),context=_context(p,shot),ontology_revision=current_onto,status='proposed',created=time.time())
        old.update(status='superseded',superseded_by=item['id'])
        _save(c,'scene_proposals',old);_save(c,'scene_proposals',item)
        return dict(scene_id=record['id'],proposal_id=item['id'],status='proposed')
    if action in {'scene_propose','scene_restore'}:
        fields=('song','scene_id','base_revision','operations') if action=='scene_propose' else ('song','scene_id','base_revision','version')
        _exact(data,fields);record,shot,current_onto=_current(c,store,p,name,data['scene_id'])
        if type(data['base_revision']) is not int or data['base_revision']!=record['head'] or not record['head']:raise Conflict('현재 구도 버전을 확인하세요.')
        current=record['versions'][-1]['scene']
        if action=='scene_restore':
            if type(data['version']) is not int:raise ValueError('복원 버전을 확인하세요.')
            old=next((v for v in record['versions'] if v['id']==data['version']),None)
            if not old:raise ValueError('복원 버전이 없습니다.')
            value=scene_spec.validate(old['scene']);changes=[]
        else:
            allowed=[('camera','camera',f) for f in ('position','target','lens_mm')]
            allowed += [('object',o['id'],f) for o in current['objects'] for f in ('position','rotation_degrees','scale','asset')+(() if o['kind']=='mesh' else ('color',))]
            allowed += [('light',o['id'],f) for o in current['lights'] for f in ('position','target','energy_w','size_m','color')]
            change=scene_spec.propose_changes(current,data['operations'],base_revision=data['base_revision'],current_revision=record['head'],allowed_fields=allowed)
            value,changes=change['scene'],change['changes']
        resolve_assets(c,store,pid,cid,value,require_rights=False)
        if origin is not None:
            # An agent repeating an identical pending change reuses that proposal instead of stacking copies.
            same=next((x for x in (json.loads(r[0]) for r in c.execute('SELECT body FROM scene_proposals WHERE scene=? AND conversation=? ORDER BY rowid',(record['id'],cid)))
                       if 'origin' in x and x['status'] in {'proposed','held'} and x['base_revision']==record['head'] and x['scene_hash']==scene_spec.fingerprint(value)),None)
            if same:return dict(scene_id=record['id'],proposal_id=same['id'],status=same['status'],duplicate=True)
        item=dict(id=uuid.uuid4().hex,scene_id=record['id'],conversation_id=cid,base_revision=record['head'],scene=value,scene_hash=scene_spec.fingerprint(value),changes=changes,context=_context(p,shot),ontology_revision=current_onto,status='proposed',created=time.time())
        if origin is not None:item['origin']=deepcopy(origin)  # S7b: actor, model_reason (unverified), server provenance
        _save(c,'scene_proposals',item)
        return dict(scene_id=record['id'],proposal_id=item['id'],status='proposed')
    if action=='scene_render':
        _exact(data,('song','scene_id','scene_revision','grant_id'))
        record,shot,current_onto=_current(c,store,p,name,data['scene_id'])
        if type(data['scene_revision']) is not int or data['scene_revision']!=record['head'] or not record['head']:raise Conflict('현재 구도 버전을 확인하세요.')
        version=record['versions'][-1];approval=version['approval'];binding=dict(workspace_id=store.workspace_id,project_id=pid,shot_id=record['shot_id'],scene_id=record['id'],revision=record['head'],ontology_revision=current_onto)
        if data['grant_id']!=approval['id'] or version['context']!=_context(p,shot):raise ValueError('현재 구도의 사람 승인이 필요합니다.')
        scene_spec.require_approval(version['scene'],binding,approval)
        inputs=resolve_assets(c,store,pid,cid,version['scene'])
        _register_grant_owner(p,cid,approval['id'])
        for row in c.execute('SELECT body FROM jobs'):
            previous=json.loads(row[0])
            if previous.get('kind')=='local-3d-still' and previous.get('approval',{}).get('id')==approval['id']:
                # A queued cancellation or pre-render failure has no renderer
                # side effects and atomically released its reservation.
                if previous['status'] in {'cancelled','failed'} and not c.execute('SELECT 1 FROM scene_reservations WHERE job=?',(previous['id'],)).fetchone():continue
                return dict(scene_id=record['id'],job_id=previous['id'],state=previous['status'],existing=True)
        environment=runtime_binding(store)
        allocated=c.execute('SELECT COALESCE(SUM(bytes),0) FROM scene_reservations').fetchone()[0]
        reservation=RESERVATION_BYTES+sum(Path(a['path']).stat().st_size for a in inputs)
        if allocated+reservation>environment['quota_bytes']:raise ValueError('3D 저장 한도가 부족합니다.')
        identifier=uuid.uuid4().hex
        job=dict(id=identifier,revision=1,kind='local-3d-still',song=name,shot=shot,shot_id=record['shot_id'],conversation_id=cid,scene_id=record['id'],scene_revision=record['head'],scene=deepcopy(version['scene']),assets=scene_spec.asset_references(version['scene']),approval=deepcopy(approval),context=version['context'],environment=environment,status='queued',progress=0,created=time.time(),cancel_requested=False,snapshot=dict(shots={}),download=None,error=None,cost=dict(provider_calls=0,provider_cost=0,local_compute='미계측',kind='local-3d-still'))
        c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(job,ensure_ascii=False)))
        c.execute('INSERT INTO scene_reservations VALUES (?,?)',(identifier,reservation))
        return dict(scene_id=record['id'],job_id=identifier,state='queued',existing=False)
    raise ValueError('지원하지 않는 3D 동작입니다.')


def private_root(store):
    path=store.root/'scene-private'
    if path.is_symlink():raise ValueError('3D 비공개 저장 경로를 확인하세요.')
    path.mkdir(mode=0o700,exist_ok=True)
    if not path.is_dir() or path.resolve().parent!=store.root:raise ValueError('3D 비공개 저장 경로를 확인하세요.')
    return path


def check_job(c,store,job):
    """Recheck trusted state at claim and immediately before asset attachment."""
    revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
    saved=json.loads(body);p=saved['projects'].get(job['song'])
    if not p or p.get('archived'):raise ValueError('구도 작품을 확인하세요.')
    scoped={**p,'_conversation_id':job['conversation_id']}
    record,shot,onto=_current(c,store,scoped,job['song'],job['scene_id'])
    if (record['shot_id']!=job['shot_id'] or shot!=job['shot'] or record['head']!=job['scene_revision'] or
        _context(p,shot)!=job['context']):raise Conflict('승인 후 구도 또는 작품 문맥이 변경되었습니다.')
    version=record['versions'][-1]
    if version['scene']!=job['scene'] or version['approval']!=job['approval']:raise Conflict('승인된 구도가 변경되었습니다.')
    binding=dict(workspace_id=store.workspace_id,project_id=contracts.project_id(store.workspace_id,job['song']),shot_id=job['shot_id'],scene_id=job['scene_id'],revision=job['scene_revision'],ontology_revision=onto)
    scene_spec.require_approval(job['scene'],binding,job['approval'])
    resolve_assets(c,store,binding['project_id'],job['conversation_id'],job['scene'])
    if job.get('assets',[])!=scene_spec.asset_references(job['scene']):raise ValueError('승인된 3D 자산 연결이 변경되었습니다.')
    if runtime_binding(store)!=job['environment']:raise ValueError('승인된 3D 실행 환경이 변경되었습니다.')
    return revision,saved,p,shot


def process(store,job,read,update):
    import scene_renderer
    from editing import probe
    from loretune import Studio
    created=None;staging=None;committed=False;renderer_invoked=False
    try:
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            latest=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job['id'],)).fetchone()[0])
            if latest['status']!='running' or latest.get('cancel_requested'):raise scene_renderer.RenderCancelled('3D 렌더를 취소했습니다.')
            check_job(c,store,latest)
            inputs=resolve_assets(c,store,contracts.project_id(store.workspace_id,job['song']),job['conversation_id'],job['scene'])
        destination_root=private_root(store);renderer_config=store.scene_configuration['renderer']
        # From this point onward the renderer may have persisted a claim or
        # created files even when its call raises. Never release based on error.
        renderer_invoked=True
        options=dict(request_id=job['id'],cancelled=lambda:read().get('cancel_requested',False))
        if inputs:options['assets']=inputs
        receipt=scene_renderer.render(job['scene'],renderer_config,destination_root,**options)
        path=Path(receipt['path'])
        if (path.is_symlink() or path.resolve().parent!=private_root(store).resolve() or receipt.get('request_id')!=job['id'] or
            receipt.get('scene_hash')!=scene_spec.fingerprint(job['scene']) or receipt.get('image_id')!=job['environment']['image_id'] or
            receipt.get('blender_sha256')!=job['environment']['blender_sha256'] or receipt.get('kind')!='local-3d-still' or
            receipt.get('external_calls')!=0 or receipt.get('assets')!=scene_spec.asset_references(job['scene']) or
            receipt.get('compiler_sha256')!=hashlib.sha256(scene_renderer.compile_scene(job['scene'])).hexdigest()):
            raise ValueError('3D 결과 범위를 확인하세요.')
        scene_renderer._check_png(path,job['scene']['width'],job['scene']['height'],'ffmpeg')
        raw=path.read_bytes()
        if not raw or len(raw)>scene_renderer.MAX_IMAGE_BYTES or hashlib.sha256(raw).hexdigest()!=receipt.get('sha256'):raise ValueError('3D 결과 해시를 확인하세요.')
        metadata=probe(path,'video',expected_dimensions=(job['scene']['width'],job['scene']['height']))
        # Do not hard-link the renderer's mutable private receipt into the
        # public asset store: a later private-file write must not alter a Take.
        with tempfile.NamedTemporaryFile(dir=private_root(store),prefix='.scene-publish-',delete=False) as output:
            staging=Path(output.name);output.write(raw);output.flush();os.fsync(output.fileno())
        filename='scene-'+receipt['sha256']+'.png';destination=store.root/'assets'/filename
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            latest=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job['id'],)).fetchone()[0])
            if latest['status']!='running' or latest.get('cancel_requested'):raise scene_renderer.RenderCancelled('3D 렌더를 취소했습니다.')
            revision,saved,p,shot=check_job(c,store,latest)
            store.check_rights(c,[receipt['sha256']]+[a['sha256'] for a in scene_spec.asset_references(job['scene'])])
            try:
                os.link(staging,destination,follow_symlinks=False);created=destination
            except FileExistsError:
                if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest()!=receipt['sha256']:raise ValueError('기존 결과 파일을 확인하세요.')
            studio=Studio();studio.projects=saved['projects'];studio.canon=saved['canon'];target=p['shots'][shot]
            take=studio.attach_take(job['song'],shot,str(destination),reason='3D 구도 버전 '+str(job['scene_revision'])+' · 로컬 정지 후보',expected_revision=target['revision'])
            target['takes'][-1].update(metadata=metadata,rights='사용권 미확인',filename=filename,conversation_id=job['conversation_id'],provenance=dict(kind='local-3d-still',scene_id=job['scene_id'],scene_revision=job['scene_revision'],scene_hash=receipt['scene_hash'],job=job['id']))
            if inputs:target['takes'][-1]['provenance']['source_assets']=scene_spec.asset_references(job['scene'])
            for asset in scene_spec.asset_references(job['scene']):c.execute('INSERT OR IGNORE INTO scene_asset_dependencies VALUES (?,?)',(receipt['sha256'],asset['sha256']))
            c.execute('INSERT OR IGNORE INTO scene_asset_refs VALUES (?,?,?)',(filename,receipt['sha256'],job['id']))
            latest.update(status='completed',progress=100,take=take,download='/assets/'+filename,sha256=receipt['sha256'],verified=dict(width=job['scene']['width'],height=job['scene']['height'],kind='local-3d-still',final_output_approved=False),finished=time.time(),revision=latest.get('revision',1)+1)
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(saved,ensure_ascii=False)))
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(latest,ensure_ascii=False),job['id']))
        committed=True
    except scene_renderer.RenderCancelled:
        _finish_failure(store,job['id'],'cancelled','3D 렌더를 취소했습니다.',release=not renderer_invoked)
    except scene_renderer.RenderOutcomeUnknown:
        _finish_failure(store,job['id'],'outcome_unknown','기존 3D 작업의 접수 여부를 확인해야 합니다. 자동 재실행하지 않습니다.',release=False)
    except Exception:
        message='3D 모델·내장 텍스처 또는 권리·승인·실행 환경을 확인하세요. 기존 자산과 결과는 보존됩니다.' if job.get('assets') else '3D 결과를 연결하지 못했습니다. 승인·환경과 작업 상태를 확인하세요.'
        _finish_failure(store,job['id'],'failed',message,release=not renderer_invoked)
    finally:
        if staging is not None:staging.unlink(missing_ok=True)
        if created is not None and not committed:
            with store.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                if not c.execute('SELECT 1 FROM scene_asset_refs WHERE filename=?',(created.name,)).fetchone():created.unlink(missing_ok=True)


def _finish_failure(store,identifier,status,error,*,release):
    """Record terminal state and safe pre-invocation quota release atomically."""
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()
        if not row:raise ValueError('3D 작업이 없습니다.')
        job=json.loads(row[0])
        if job.get('kind')!='local-3d-still' or job.get('status')!='running':raise ValueError('3D 작업 상태가 변경되었습니다.')
        job.update(status=status,error=error,finished=time.time(),revision=job.get('revision',1)+1)
        c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job,ensure_ascii=False),identifier))
        if release:c.execute('DELETE FROM scene_reservations WHERE job=?',(identifier,))


def recover(store):
    """Never resubmit an interrupted 3D job; a read-only reconciliation is best effort."""
    import scene_renderer
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        rows=c.execute('SELECT id,body FROM jobs').fetchall()
        ids=[]
        for identifier,body in rows:
            job=json.loads(body)
            if job.get('kind')=='local-3d-still' and job.get('status') in {'running','outcome_unknown'}:
                if job['status']=='running':
                    job.update(status='outcome_unknown',error='서버 중단으로 3D 작업 확인이 필요합니다. 자동 재실행하지 않습니다.',revision=job.get('revision',1)+1)
                    c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job,ensure_ascii=False),identifier))
                ids.append(identifier)
    if store.scene_configuration is None:return
    for identifier in ids:
        try:
            outcome=scene_renderer.reconcile(store.scene_configuration['renderer'],private_root(store),request_id=identifier,cleanup=False)
        except Exception:
            continue
        with store.connect() as c:
            c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT body FROM jobs WHERE id=?',(identifier,)).fetchone()
            if not row:continue
            job=json.loads(row[0])
            if job['status']!='outcome_unknown':continue
            # Do not claim completion or retry based on an absent/late container.
            job['reconciliation']=dict(status=outcome.get('status','unknown'))
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job,ensure_ascii=False),identifier))
