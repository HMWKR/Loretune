"""Local single-user HTTP application; SQLite transactions wrap the existing Studio."""
from contextlib import contextmanager
import base64
import hashlib
import json
import mimetypes
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
import time
from threading import Thread
from copy import deepcopy
from editing import defaults, current, save_timeline, render_project, probe, seconds, srt, preflight
from renderer import render, Cancelled, verify_output
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from loretune import Studio, Conflict
from music import save_music, waveform
import guided
import model_selection
import production_tools
import action_execution
import rehearsal_workflow
import chat_protocols
import ontology
import project_ontology
from references import assign as assign_reference, review as review_reference
from estimates import estimate as render_estimate, validate as validate_estimate
import preferences
import contracts
import ledger
import fal_provider
from generation_queue import GenerationQueue

ROOT = Path(__file__).resolve().parent
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.mp4', '.mov', '.webm'}
MAX_UPLOAD = 16 * 1024 * 1024

def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('텍스트를 1~2000자로 입력하세요.')
    return value.strip()

def number(value):
    if type(value) is not int or value < 0 or value > 100000:
        raise ValueError('범위는 0~100000 정수로 입력하세요.')
    return value

class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in ['assets', 'exports']: (self.root/folder).mkdir(exist_ok=True)
        self.db = self.root/'studio.sqlite3'
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, revision INTEGER, body TEXT)')
            c.execute('INSERT OR IGNORE INTO state VALUES (1,0,?)', (json.dumps(dict(canon=[], projects={})),))
            c.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, digest TEXT, result TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, created REAL, action TEXT, revision INTEGER)')
            c.execute('CREATE TABLE IF NOT EXISTS ips (id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT NOT NULL)')
            c.execute("INSERT OR IGNORE INTO ips VALUES ('default','기본 IP','기존 로컬 작품')")
            c.execute('CREATE TABLE IF NOT EXISTS asset_rights (sha256 TEXT PRIMARY KEY, blocked INTEGER NOT NULL, reason TEXT NOT NULL, updated REAL NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS rights_history (id INTEGER PRIMARY KEY, sha256 TEXT, blocked INTEGER, reason TEXT, created REAL)')
            c.execute('CREATE TABLE IF NOT EXISTS export_assets (filename TEXT, sha256 TEXT, PRIMARY KEY(filename,sha256))')
            c.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            c.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)',('workspace_id',str(uuid.uuid4())))
            self.workspace_id=c.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0]
            ledger.initialize(c)
            ontology.initialize(c)
            action_execution.initialize(c)
        self.generation=GenerationQueue(self)
        self.provider_adapter=None
        self.generation_approval=None
        self.retrieval_approval=None

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def state(self):
        with self.connect() as c:
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
        saved=json.loads(body)
        saved.setdefault('preferences',[])
        saved['workspace_id']=self.workspace_id
        saved['model_catalog']=model_selection.catalog()
        with self.connect() as c:
            saved['budgets']=[ledger.budget(c,self.workspace_id,r[0]) for r in c.execute('SELECT scope FROM budgets WHERE workspace=?',(self.workspace_id,)).fetchall()]
        with self.connect() as c:
            saved['generation_jobs']=[]
            for r in c.execute('SELECT body FROM generation_jobs ORDER BY rowid DESC'):
                job=json.loads(r[0])
                public={k:v for k,v in job.items() if k not in {'input','receipt','result'}}
                public['context']={k:v for k,v in job['context'].items() if k!='submission_binding'}
                public['can_recheck']=job['state']=='reconciliation_required' and bool(job.get('receipt'))
                public['provider_request_id']=(job.get('receipt') or {}).get('request_id')
                public['provider_completed']=bool(job.get('result'))
                public['retrieval_permission_blocked']=job['state']=='import_blocked' and job.get('failure_code') in {'provider_media_http_401','provider_media_http_403','provider_http_401','provider_http_403','cdn_token_http_401','cdn_token_http_403'}
                approval=self.retrieval_approval or {}
                resolved=approval.get('job')==job['id'] and approval.get('expires',0)>time.time() and bool(approval.get('evidence')) and bool(approval.get('id')) and approval['id'] not in job.get('retrieval_approvals_used',[])
                public['can_resume_result']=job['state'] in {'import_blocked','cancelled_result'} and bool(job.get('result')) and (not public['retrieval_permission_blocked'] or resolved)
                public['retention_notice']='공급자 파일 만료 1시간 요청. 정확한 삭제시각 미확인; 새 생성 없이 기존 결과만 회수합니다.' if job.get('result') else None
                saved['generation_jobs'].append(public)
        saved['project_ids']={name:contracts.project_id(self.workspace_id,name) for name in saved['projects']}
        for p in saved['projects'].values():
            defaults(p)
            p['model_settings']=model_selection.settings(p)
        with self.connect() as c:
            for name,p in saved['projects'].items():
                identifier=saved['project_ids'][name];scope=project_ontology.scope(self.workspace_id,identifier)
                p['rehearsal_jobs']=[{k:j.get(k) for k in ('id','state','mode','external_calls','result_approved')}
                    for j in (json.loads(r[0]) for r in c.execute('SELECT body FROM action_jobs WHERE workspace=? AND project=? ORDER BY rowid DESC',(self.workspace_id,identifier)))]
                p['ontology']=ontology.snapshot(c,scope)
                for shot in p['shots'].values():shot['semantic_impact']=project_ontology.impact(shot,p['ontology'])
                p['ontology_proposals']=[dict(id=r[0],base_revision=r[1],graph=json.loads(r[2]),applied_revision=r[3]) for r in c.execute('SELECT id,base_revision,body,applied_revision FROM ontology_proposals WHERE scope=?',(scope,))]
                p['lineage']=project_ontology.projection(self.workspace_id,identifier,p)
        for p in saved['projects'].values(): p['preflight'] = preflight(p)
        with self.connect() as c: jobs=[json.loads(row[0]) for row in c.execute('SELECT body FROM jobs ORDER BY rowid DESC')]
        with self.connect() as c: saved['ips']=[dict(id=row[0],name=row[1],description=row[2]) for row in c.execute('SELECT id,name,description FROM ips ORDER BY rowid')]
        with self.connect() as c: saved['asset_rights']={row[0]:dict(blocked=bool(row[1]),reason=row[2]) for row in c.execute('SELECT sha256,blocked,reason FROM asset_rights')}
        for p in saved['projects'].values():
            timeline=current(p)
            assets=[t for clip in timeline['clips'] for t in p['shots'].get(clip['shot'],{}).get('takes',[]) if t['id']==clip['take']]
            assets += [a for a in p['audio_versions'] if a['id']==timeline.get('audio')]
            if any(saved['asset_rights'].get(a['sha256'],{}).get('blocked') for a in assets):
                p['preflight']['ready']=False
                p['preflight']['errors'].append('사용 중지된 원본이 포함되어 있습니다.')
        return dict(saved, revision=revision, jobs=jobs, ffmpeg=bool(shutil.which('ffmpeg')), capabilities=dict(chat_plan=True,provider_generation=bool(self.provider_adapter and self.generation_approval and self.generation_approval.get('expires',0)>time.time()),local_render=bool(shutil.which('ffmpeg')),audio=True,subtitle_track=True,burned_subtitles=False,cancel_local_job=True,authentication=False,provider_mode=getattr(self.provider_adapter,'mode','live-unverified') if self.provider_adapter else 'disconnected',scope='single-local-workspace'))

    def operations(self):
        """Actual local job outcomes; HTTP success is not render success."""
        now=time.time()
        with self.connect() as c:
            jobs=[json.loads(row[0]) for row in c.execute('SELECT body FROM jobs')]
            audit=[dict(id=r[0],at=r[1],action=r[2],revision=r[3]) for r in
                   c.execute('SELECT id,created,action,revision FROM audit ORDER BY id DESC LIMIT 50')]
            revision=c.execute('SELECT revision FROM state WHERE id=1').fetchone()[0]
        counts={status:sum(j['status']==status for j in jobs) for status in
                ['queued','running','completed','failed','cancelled','interrupted']}
        recent=[]
        for j in sorted(jobs,key=lambda j:j['created'],reverse=True)[:50]:
            recent.append(dict(id=j['id'],song=j['song'],status=j['status'],
                queue_seconds=round(max(0,j.get('started',j.get('finished',now))-j['created']),3),
                run_seconds=round(max(0,j.get('finished',now)-j['started']),3) if j.get('started') else None,
                error=j.get('error'),verified=j.get('verified'),cost=j['cost']))
        return dict(revision=revision,counts=counts,total_jobs=len(jobs),jobs=recent,audit=audit,
            provider=dict(connected=False,calls=0,cost=0,status='미연결; 실제 공급자 지연/과금은 측정하지 않음'),
            scope='로컬 렌더 운영 기록; 계정 신원 감사·외부 모니터링·알림은 미지원')

    def save_media(self, raw, extension, kind, *, max_bytes=MAX_UPLOAD, expected_duration=None):
        """Only publish verified media; invalid uploads leave no public asset."""
        if not raw or len(raw)>max_bytes:raise ValueError(f'파일은 1바이트~{max_bytes//(1024*1024)}MB여야 합니다.')
        digest=hashlib.sha256(raw).hexdigest()
        destination=self.root/'assets'/(digest+extension)
        with tempfile.TemporaryDirectory(dir=self.root,prefix='upload-') as folder:
            staging=Path(folder)/('source'+extension)
            staging.write_bytes(raw)
            metadata=probe(staging,kind)
            if expected_duration is not None:
                if abs(metadata.get('duration',0)-expected_duration)>.2:raise ValueError('생성 결과 길이가 요청한 길이와 다릅니다.')
                subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-protocol_whitelist','file,pipe','-i',str(staging),'-map','0:v:0','-f','null','-'],capture_output=True,timeout=30,check=True)
            if kind=='audio':metadata['waveform']=waveform(staging)
            if destination.exists():
                if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
                    raise ValueError('동일 해시의 기존 원본이 변경되었습니다. 복구 후 다시 연결하세요.')
            else:staging.replace(destination)
        return destination,metadata

    def mutate(self, request):
        key = text(request['request_id'])
        digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            prior = c.execute('SELECT digest,result FROM requests WHERE id=?', (key,)).fetchone()
            if prior:
                if prior[0] != digest: raise Conflict('같은 요청 번호의 내용이 다릅니다.')
                return json.loads(prior[1])
            revision, body = c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
            if number(request['revision']) != revision:
                raise Conflict('다른 화면에서 변경되었습니다. 새로고침 후 다시 시도하세요.')
            s = Studio()
            saved = json.loads(body)
            preference_items=saved.get('preferences',[])
            s.canon, s.projects = saved['canon'], saved['projects']
            for project in s.projects.values(): defaults(project)
            a, d = request['action'], request['data']
            target=s.projects.get(d.get('song')) if isinstance(d.get('song'),str) else None
            if target and target.get('archived') and a not in {'archive_project','manifest'}:
                raise ValueError('보관된 작품입니다. 먼저 보관 해제하세요.')
            result = {}
            def ip_id():
                identifier=text(d.get('ip','default'))
                if not c.execute('SELECT 1 FROM ips WHERE id=?',(identifier,)).fetchone():
                    raise ValueError('IP가 없습니다.')
                return identifier
            if a == 'archive_project':
                p=s.projects[text(d['song'])]
                if type(d['archived']) is not bool:raise ValueError('보관 상태를 확인하세요.')
                if d['archived'] and any(json.loads(row[0])['song']==d['song'] and json.loads(row[0])['status'] in {'queued','running'} for row in c.execute('SELECT body FROM jobs')):
                    raise ValueError('진행 중 렌더를 완료하거나 취소한 후 보관하세요.')
                p['archived']=d['archived']
                p.setdefault('archive_history',[]).append(dict(archived=d['archived'],reason=text(d['reason']),at=time.time(),actor='local-owner'))
            elif a == 'preference_propose':
                ip=ip_id();scope=d.get('song') or None
                if scope and (scope not in s.projects or s.projects[scope].get('ip','default')!=ip):
                    raise ValueError('선호 예외의 작품과 IP를 확인하세요.')
                previous=number(d['supersedes']) if d.get('supersedes') is not None else None
                result['preference']=preferences.propose(preference_items,ip=ip,song=scope,
                    category=text(d['category']),value=text(d['value']),evidence=text(d['evidence']),
                    reason=text(d['reason']),supersedes=previous)['id']
            elif a == 'preference_review':
                item=next((x for x in preference_items if x['id']==number(d['id'])),None)
                if item and item['song'] and s.projects[item['song']].get('archived'):
                    raise ValueError('보관된 작품의 취향 예외입니다. 먼저 보관 해제하세요.')
                result['preference']=preferences.review(preference_items,number(d['id']),text(d['decision']),text(d['reason']))['id']
            elif a == 'setting':
                s.approve_setting(text(d['text']), era=text(d['era']), valid_from=number(d['valid_from']),
                                  valid_to=None if d['valid_to'] is None else number(d['valid_to']))
                s.canon[-1]['ip']=ip_id()
            elif a == 'create_ip':
                name=text(d['name'])
                if c.execute('SELECT 1 FROM ips WHERE name=?',(name,)).fetchone():
                    raise ValueError('같은 이름의 IP가 있습니다.')
                identifier=uuid.uuid4().hex
                c.execute('INSERT INTO ips VALUES (?,?,?)',(identifier,name,text(d['description'])))
                result['ip']=identifier
            elif a == 'setting_candidate':
                ip=ip_id()
                end = None if d.get('valid_to') is None else number(d['valid_to'])
                start = number(d['valid_from'])
                if end is not None and end < start:
                    raise ValueError('적용 종료는 시작보다 앞설 수 없습니다.')
                previous = d.get('supersedes')
                if previous is not None and not any(x['revision'] == number(previous) and x.get('approved') and x.get('ip','default')==ip for x in s.canon):
                    raise ValueError('정정할 승인 설정 버전이 없습니다.')
                item = dict(text=text(d['text']), era=text(d['era']), valid_from=start, valid_to=end,
                            scope='ip', revision=len(s.canon)+1, approved=False, status='proposed',
                            evidence=text(d['evidence']), reason=text(d['reason']), supersedes=previous, ip=ip)
                s.canon.append(item)
                result['candidate'] = item['revision']
            elif a == 'review_setting':
                item = next((x for x in s.canon if x['revision'] == number(d['candidate'])), None)
                if item is None or item.get('status') != 'proposed':
                    raise ValueError('검토할 설정 후보가 없습니다.')
                decision = text(d['decision'])
                if decision not in {'approved', 'rejected'}:
                    raise ValueError('승인 또는 거절을 선택하세요.')
                old = next((x for x in s.canon if x['revision'] == item.get('supersedes')), None)
                if decision == 'approved' and old and old.get('superseded_by'):
                    raise Conflict('원본 설정에 다른 정정이 먼저 승인되었습니다. 최신 버전을 확인하세요.')
                item.update(status=decision, approved=decision=='approved', reviewed_at=time.time(), review_reason=text(d['reason']), actor='local-owner')
                if decision == 'approved' and old:
                    old['superseded_by'] = item['revision']
                result['affected_projects'] = [name for name,p in s.projects.items() if any(x['revision']==item.get('supersedes') for x in p['snapshot'])]
            elif a == 'project':
                if d.get('clone_structure') and not d.get('source_song'):
                    raise ValueError('구성을 복제할 원본 작품을 선택하세요.')
                name=text(d['name']);ip=ip_id()
                s.new_song(name, era=text(d['era']), story=number(d['story']), ip=ip)
                s.projects[name]['profile']='landscape'
                if d.get('source_song'):
                    source=s.projects[text(d['source_song'])]
                    if source.get('ip','default')!=ip:raise ValueError('계승할 작품과 같은 IP를 선택하세요.')
                    identifiers=d.get('inherit_revisions',[])
                    if not isinstance(identifiers,list) or len(identifiers)!=len(set(identifiers)):raise ValueError('계승 버전 목록을 확인하세요.')
                    available={x['revision']:x for x in source['snapshot']}
                    if any(type(i)is not int or i not in available for i in identifiers):raise ValueError('원본 작품의 정확한 설정 버전을 선택하세요.')
                    s.projects[name]['snapshot']=[deepcopy(available[i]) for i in identifiers]
                    s.projects[name]['derived_from']=dict(song=source['name'],setting_revisions=identifiers,created=time.time(),reason=text(d['inherit_reason']))
                    if type(d.get('clone_structure',False)) is not bool:raise ValueError('구성 복제 여부를 확인하세요.')
                    if d.get('clone_structure'):
                        for shot_name,shot in source['shots'].items():
                            s.plan_shot(name,shot_name,shot['description'])
                        s.projects[name]['derived_from']['structure_copied']=True
            elif a == 'asset_rights':
                sha=text(d['sha256']);reason=text(d['reason'])
                if type(d['blocked']) is not bool:raise ValueError('사용 중지 여부를 확인하세요.')
                known=[x for p in s.projects.values() for x in p['audio_versions']]+[t for p in s.projects.values() for sh in p['shots'].values() for t in sh['takes']]
                if not any(x['sha256']==sha for x in known):raise ValueError('등록된 자산이 아닙니다.')
                c.execute('INSERT INTO asset_rights VALUES (?,?,?,?) ON CONFLICT(sha256) DO UPDATE SET blocked=excluded.blocked,reason=excluded.reason,updated=excluded.updated',(sha,int(d['blocked']),reason,time.time()))
                c.execute('INSERT INTO rights_history(sha256,blocked,reason,created) VALUES (?,?,?,?)',(sha,int(d['blocked']),reason,time.time()))
                affected=[]
                if d['blocked']:
                    for identifier,body in c.execute('SELECT id,body FROM jobs').fetchall():
                        job=json.loads(body)
                        if sha in self.snapshot_hashes(job['snapshot']):
                            affected.append(identifier)
                            if job['status'] in {'queued','running'}:
                                job['cancel_requested']=True
                                if job['status']=='queued':job['status']='cancelled'
                                job['revision']=job.get('revision',1)+1
                                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),identifier))
                result['affected_jobs']=affected
            elif a == 'shot':
                s.plan_shot(text(d['song']), text(d['shot']), text(d['description']))
            elif a in {'assign_reference','review_reference'}:
                shot=s.projects[text(d['song'])]['shots'][text(d['shot'])]
                if number(d['shot_revision'])!=shot['revision']:raise Conflict('샷이 변경되었습니다. 다시 확인하세요.')
                if a=='review_reference':
                    if d.get('decision')=='approved':
                        if number(d['version'])!=shot.get('reference_head'):raise Conflict('참고 버전이 변경되었습니다.')
                        for ref in shot['reference_versions'][-1]['roles'].values():
                            self.check_rights(c,[ref['sha256']])
                            if hashlib.sha256(Path(ref['asset']).read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('참고 원본이 변경되었습니다.')
                    result['reference']=review_reference(shot,number(d['version']),text(d['decision']),text(d['reason']))
                else:
                    source_song=text(d['source_song']);source_shot=text(d['source_shot'])
                    source=next((t for t in s.projects[source_song]['shots'][source_shot]['takes'] if t['id']==number(d['source_take'])),None)
                    if source is None:raise ValueError('출처 take가 없습니다.')
                    if Path(source['asset']).suffix.lower() not in {'.png','.jpg','.jpeg'}:raise ValueError('참고 역할은 현재 이미지 원본만 지원합니다.')
                    if source.get('rights','사용권 미확인')=='사용권 미확인':raise ValueError('사용권 근거가 필요합니다.')
                    self.check_rights(c,[source['sha256']])
                    if hashlib.sha256(Path(source['asset']).read_bytes()).hexdigest()!=source['sha256']:raise ValueError('원본 해시가 변경되었습니다.')
                    ref=dict(song=source_song,shot=source_shot,take=source['id'],asset=source['asset'],sha256=source['sha256'],rights=source['rights'])
                    result['reference']=assign_reference(shot,text(d['role']),ref,text(d['reason']))
            elif a == 'music_structure':
                result['music'] = save_music(s.projects[text(d['song'])], d)
            elif a in {'ontology_propose','ontology_apply','ontology_restore','ontology_bind'}:
                name=text(d['song']);p=s.projects[name]
                scope=project_ontology.scope(self.workspace_id,contracts.project_id(self.workspace_id,name))
                if a=='ontology_bind':
                    shot=p['shots'][text(d['shot'])]
                    if shot['revision']!=number(d['shot_revision']):raise Conflict('샷이 변경됐습니다.')
                    head=ontology.snapshot(c,scope)
                    if head['revision']!=number(d['ontology_revision']):raise ontology.Conflict('승인 설정이 변경됐습니다.')
                    project_ontology.bind(shot,head,d['entities'])
                elif a=='ontology_propose':
                    result['ontology']=project_ontology.manual_proposal(c,scope,d)
                elif a=='ontology_apply':
                    result['ontology']=ontology.apply(c,scope,text(d['proposal']),number(d['ontology_revision']),'local-owner',approved=d.get('approved') is True)
                    p['ontology_snapshot']=deepcopy(result['ontology'])
                else:
                    result['ontology']=ontology.rollback(c,scope,number(d['version']),number(d['ontology_revision']),'local-owner',approved=d.get('approved') is True)
                    p['ontology_snapshot']=deepcopy(result['ontology'])
            elif a in {'action_propose','action_decide','action_execute','action_review'}:
                name=text(d['song'])
                result['execution_card']=rehearsal_workflow.handle(c,self,s,name,contracts.project_id(self.workspace_id,name),a,d)
            elif a == 'model_handoff':
                if set(d)!={'song'}:raise ValueError('인계 범위는 서버에서 결정합니다.')
                name=text(d['song']);identifier=contracts.project_id(self.workspace_id,name)
                result['handoff']=chat_protocols.handoff(s.projects[name],name,action_execution.project_jobs(c,self.workspace_id,identifier,name))
            elif a == 'production_run':
                if set(d)!={'song'}:raise ValueError('실행 문맥은 서버에서 구성합니다.')
                result['run']=production_tools.begin(s.projects[text(d['song'])])
            elif a == 'production_tool':
                if set(d)!={'song','run','call'}:raise ValueError('도구 권한과 문맥은 서버에서 구성합니다.')
                name=text(d['song'])
                project_id=contracts.project_id(self.workspace_id,name)
                jobs=action_execution.project_jobs(c,self.workspace_id,project_id,name)
                result['tool']=production_tools.execute(s.projects[name],text(d['run']),d['call'],jobs=jobs,
                    request_generation=lambda args: action_execution.request_with_savepoint(c,self.workspace_id,project_id,s.projects[name],args))
            elif a == 'model_settings':
                if set(d)-{'song','selections','model_revision'}:raise ValueError('모델 설정에 허용되지 않은 필드입니다.')
                result['model_settings']=model_selection.update(s.projects[text(d['song'])],d['selections'],d['model_revision'])
            elif a == 'guided_plan':
                p=s.projects[text(d['song'])]
                run=production_tools.begin(p)
                arguments={k:d.get(k,'narrative' if k=='kind' else '') for k in production_tools.TOOLS['propose_media_plan']}
                tool=production_tools.execute(p,run['id'],dict(id=uuid.uuid4().hex,name='propose_media_plan',arguments=arguments,complete=True))
                if tool['status']!='proposed':raise ValueError('계획 입력의 형식과 필수 항목을 확인하세요.')
                p['production_runs'][-1]['state']='completed'
                result['plan']=tool['plan']['id']
                result['run']=run['id']
            elif a == 'apply_guided_plan':
                result['shots']=guided.apply(s,text(d['song']),text(d['plan']))
            elif a == 'chat_plan':
                song = text(d['song'])
                prompt = text(d['prompt'])
                lines = [line.strip() for line in prompt.splitlines() if line.strip()]
                if len(lines) > 30:
                    raise ValueError('한 번에 최대 30개 장면을 입력하세요.')
                p = s.projects[song]
                messages = p.setdefault('conversation', [])
                plan = dict(id=uuid.uuid4().hex, prompt=prompt, scenes=lines,
                            engine='line-based-local', status='proposed', created=time.time())
                plan['music'] = deepcopy(p.get('music_versions', [])[-1]) if p.get('music_head') else None
                plan['preferences']=preferences.resolve(preference_items,p.get('ip','default'),song)
                p.setdefault('chat_plans', []).append(plan)
                messages.extend([dict(role='user', text=prompt, plan=plan['id']),
                                 dict(role='system', text=f'{len(lines)}개 장면 초안입니다. 각 줄을 그대로 장면으로 나누었습니다. AI 분석·생성은 실행하지 않았습니다. 검토 후 샷에 추가하세요.', plan=plan['id'])])
                result['plan'] = plan['id']
            elif a == 'apply_chat_plan':
                song = text(d['song'])
                p = s.projects[song]
                plan = next((item for item in p.get('chat_plans', []) if item['id'] == text(d['plan'])), None)
                if plan is None:
                    raise ValueError('제작 초안이 없습니다.')
                if plan['status'] != 'applied':
                    shots = []
                    for description in plan['scenes']:
                        index = len(p['shots']) + 1
                        while f'장면 {index}' in p['shots']:
                            index += 1
                        name = f'장면 {index}'
                        s.plan_shot(song, name, description)
                        if plan.get('music'):
                            music = plan['music']
                            duration = (music['end'] - music['start']) / len(plan['scenes'])
                            p['shots'][name].update(planned_duration=duration, music_version=music['id'], music_start=music['start'] + len(shots) * duration)
                        shots.append(name)
                    plan.update(status='applied', shots=shots)
                    p['conversation'].append(dict(role='system', text='초안을 샷 보드에 추가했습니다. 미디어 연결과 take 검토, 타임라인 승인이 필요합니다.', plan=plan['id']))
                result['shots'] = plan['shots']
            elif a in {'audio','timeline','restore_timeline','approve_timeline','comment','resolve_comment','estimate_render','render_job','cancel_job','delivery_review','review_take','reuse_take'}:
                result = self.edit(c,s,a,d)
            elif a in {'cancel_generation','resume_generation_result','resume_generation_status'}:
                row=c.execute('SELECT body FROM generation_jobs WHERE id=?',(text(d['job']),)).fetchone()
                if not row:raise ValueError('생성 작업이 없습니다.')
                job=json.loads(row[0])
                if job['context']['song']!=text(d['song']):raise ValueError('작품과 생성 작업이 다릅니다.')
                if a=='cancel_generation':self.generation.request_cancel(job['id'],text(d['reason']),c)
                elif a=='resume_generation_status':
                    if job['state']!='reconciliation_required' or not job.get('receipt'):raise ValueError('조회할 제공자 접수번호가 없습니다. 재발행하지 않습니다.')
                    job.update(state='cancel_sent' if job.get('cancel_requested') else 'accepted',last_error=None,poll_errors=0);self.generation.save(c,job)
                else:
                    if job['state'] not in {'import_blocked','cancelled_result'} or not job.get('result'):raise ValueError('다시 연결할 결과가 없습니다.')
                    if job.get('failure_code') in {'provider_media_http_401','provider_media_http_403','provider_http_401','provider_http_403','cdn_token_http_401','cdn_token_http_403'}:
                        approval=self.retrieval_approval or {}
                        if approval.get('job')!=job['id'] or approval.get('expires',0)<=time.time() or not approval.get('evidence') or not approval.get('id') or approval['id'] in job.get('retrieval_approvals_used',[]):
                            raise ValueError('접근 거절 후에는 새 권한 해결 근거를 서버에서 확인해야 합니다. 같은 다운로드를 반복하지 않습니다.')
                        job.setdefault('retrieval_approvals_used',[]).append(approval['id'])
                    job.update(state='result_ready',last_error=None);self.generation.save(c,job)
                result['job']=job['id']
            elif a == 'start_generation':
                gate=self.generation_approval
                if not self.provider_adapter or not gate or gate.get('expires',0)<=time.time():raise ValueError('시스템·디자인 QA 후 마지막 live gate 승인이 필요합니다. 외부 전송하지 않았습니다.')
                song,shot=text(d['song']),text(d['shot']);target=s.projects[song]['shots'][shot]
                prep=next((p for p in target.get('generation_preparations',[]) if p['id']==text(d['preparation'])),None)
                if not prep:raise ValueError('생성 준비 기록이 없습니다.')
                if prep.get('job'):return {'job':prep['job'],'revision':revision}
                fal_provider.validate_gate(gate,prep,self.workspace_id)
                if target['revision']!=prep['shot_revision']:raise Conflict('준비 이후 샷이 변경되었습니다. 다시 준비하세요.')
                if prep['estimate']['expires']<=time.time():raise ValueError('견적이 만료되었습니다. 다시 준비하세요.')
                ref=target['reference_versions'][prep['reference_version']-1]
                if target.get('reference_head')!=ref['id'] or ref['status']!='approved':raise ValueError('현재 시작 프레임 승인을 재검토하세요.')
                self.check_rights(c,[prep['source']['sha256']])
                raw=Path(prep['source']['asset']).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=prep['source']['sha256']:raise ValueError('시작 이미지가 변경되었습니다.')
                previous=[json.loads(r[0]) for r in c.execute('SELECT body FROM generation_jobs')]
                previous=[j for j in previous if self.generation.consumes_call_quota(c,j)]
                total=sum(ledger.units(j['quote']['money']) for j in previous)
                if len(previous)>=gate['maximum_calls'] or total+ledger.units(prep['estimate']['money'])>gate['maximum_units']:
                    raise ValueError('승인된 테스트 호출/비용 상한입니다. 추가 호출하지 않습니다.')
                scope='project:'+contracts.project_id(self.workspace_id,song)
                b=ledger.budget(c,self.workspace_id,scope)
                if not b:raise ValueError('작품 공급자 예산을 설정하세요.')
                quote=dict(prep['estimate'],budget_revision=b['revision'])
                context=dict(song=song,shot=shot,shot_revision=target['revision'],reference_version=ref['id'],rights=prep['source']['rights'],submission_binding=dict(gate_hash=guided.fingerprint(gate),adapter_identity=id(self.provider_adapter),preparation=deepcopy(prep)))
                job=self.generation.admit(scope,fal_provider.payload(prep['prompt'],raw),quote,context,key,approved=True,connection=c)
                prep['job']=job['id'];prep['status']='queued';result['job']=job['id']
            elif a == 'prepare_generation':
                song,shot=text(d['song']),text(d['shot'])
                target=s.projects[song]['shots'][shot]
                if number(d['shot_revision'])!=target['revision']:raise Conflict('샷이 변경되었습니다.')
                version=next((v for v in target.get('reference_versions',[]) if v['id']==target.get('reference_head')),None)
                if not version or version['status']!='approved' or 'start_frame' not in version['roles']:
                    raise ValueError('시작 프레임을 지정하고 현재 참고 버전을 승인하세요.')
                source=version['roles']['start_frame']
                self.check_rights(c,[source['sha256']])
                raw=Path(source['asset']).read_bytes()
                if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('시작 프레임 원본이 변경되었습니다.')
                if not source.get('rights') or source['rights']=='사용권 미확인':raise ValueError('시작 프레임 사용권을 확인하세요.')
                prompt=text(d['prompt'])
                fal_provider.payload(prompt,raw)  # validate locally; no transport or environment access
                quote=fal_provider.estimate()
                prepared=dict(id=uuid.uuid4().hex,created=time.time(),song=song,shot=shot,shot_revision=target['revision'],
                    reference_version=version['id'],source=deepcopy(source),prompt=prompt,estimate=quote,
                    status='awaiting_live_gate',external_transmission=False,provider_request_id=None)
                target.setdefault('generation_preparations',[]).append(prepared)
                result['preparation']=prepared['id']
            elif a == 'take':
                song, shot = text(d['song']), text(d['shot'])
                target = s.projects[song]['shots'][shot]
                expected = number(d['shot_revision'])
                if expected != target['revision']: raise Conflict('샷이 변경되었습니다.')
                reason = text(d['reason'])
                ext = Path(text(d['filename'])).suffix.lower()
                if ext not in EXTENSIONS: raise ValueError('PNG/JPG 또는 MP4/MOV/WebM 파일만 연결할 수 있습니다.')
                content = base64.b64decode(d['content'], validate=True)
                rights=text(d.get('rights','사용권 미확인'))
                path,metadata=self.save_media(content,ext,'video')
                s.attach_take(song, shot, path, reason=reason, expected_revision=expected)
                target['takes'][-1].update(metadata=metadata, rights=rights, filename=text(d['filename']))
                target['takes'][-1]['reference_version_at_upload']=target.get('reference_head')
            elif a == 'select':
                s.select_take(text(d['song']), text(d['shot']), number(d['take']), expected_revision=number(d['shot_revision']))
            elif a == 'render':
                raise ValueError('직접 렌더는 지원하지 않습니다. take 검토와 타임라인 승인 후 render_job을 사용하세요.')
            elif a == 'manifest':
                song = text(d['song'])
                self.check_rights(c, [t['sha256'] for sh in s.projects[song]['shots'].values() for t in sh['takes'] if t['id']==sh['selected']])
                manifest = s.export(song, s.estimate(song))
                name = uuid.uuid4().hex + '.json'
                out = self.root/'exports'/name
                out.write_text(manifest)
                for sh in s.projects[song]['shots'].values():
                    selected=next(t for t in sh['takes'] if t['id']==sh['selected'])
                    c.execute('INSERT OR IGNORE INTO export_assets VALUES (?,?)',(name,selected['sha256']))
                result['download'] = '/exports/'+name
            else:
                raise ValueError('지원하지 않는 작업입니다.')
            c.execute('INSERT INTO audit (created,action,revision) VALUES (?,?,?)',(time.time(),a,revision+1))
            c.execute('UPDATE state SET revision=?,body=? WHERE id=1', (revision+1, json.dumps(dict(canon=s.canon, projects=s.projects,preferences=preference_items))))
            result['revision'] = revision+1
            c.execute('INSERT INTO requests VALUES (?,?,?)', (key, digest, json.dumps(result)))
            return result

    @staticmethod
    def snapshot_hashes(snapshot):
        return [t['sha256'] for sh in snapshot['shots'].values() for t in sh['takes'] if t['id']==sh['selected']]+([snapshot['audio']['sha256']] if snapshot.get('audio') else [])

    @staticmethod
    def check_rights(c, hashes):
        for sha in hashes:
            row=c.execute('SELECT blocked FROM asset_rights WHERE sha256=?',(sha,)).fetchone()
            if row and row[0]:raise ValueError('사용 중지된 자산이 포함되어 있습니다. 사용권을 재검토하세요.')

    def edit(self,c,s,action,d):
        if action=='delivery_review':
            row=c.execute('SELECT body FROM jobs WHERE id=?',(text(d['job']),)).fetchone()
            if not row:raise ValueError('작업이 없습니다.')
            job=json.loads(row[0])
            if s.projects[job['song']].get('archived'):raise ValueError('보관 해제 후 납품 검토하세요.')
            if job['status']!='completed':raise ValueError('완료된 렌더만 납품 검토할 수 있습니다.')
            self.check_rights(c,self.snapshot_hashes(job['snapshot']))
            output=self.root/'exports'/(job['id']+'.mp4')
            if hashlib.sha256(output.read_bytes()).hexdigest()!=job['sha256']:raise ValueError('검토 대상 출력이 변경되었습니다.')
            decision=text(d['decision'])
            if decision not in {'approved','rejected'}:raise ValueError('승인 또는 거절을 선택하세요.')
            review=dict(decision=decision,reason=text(d['reason']),at=time.time(),actor='local-owner',sha256=job['sha256'])
            job.setdefault('delivery_reviews',[]).append(review)
            job['revision']=job.get('revision',1)+1
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),job['id']))
            return {'delivery_review':review}
        if action=='cancel_job':
            row=c.execute('SELECT body FROM jobs WHERE id=?',(text(d['job']),)).fetchone()
            if not row:raise ValueError('작업이 없습니다.')
            job=json.loads(row[0])
            if job['status'] in {'queued','running'}:
                job['cancel_requested']=True
                if job['status']=='queued':job['status']='cancelled'
                job['revision']=job.get('revision',1)+1
                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),job['id']))
            return {'job':job['id']}
        song=text(d['song']);p=s.projects[song];defaults(p)
        if action=='reuse_take':
            target=p['shots'][text(d['shot'])]
            expected=number(d['shot_revision'])
            if expected!=target['revision']:raise Conflict('대상 샷이 변경되었습니다.')
            source_song=text(d['source_song']);source_shot=text(d['source_shot']);source_take=number(d['source_take'])
            source=next((t for t in s.projects[source_song]['shots'][source_shot]['takes'] if t['id']==source_take),None)
            if not source:raise ValueError('출처 take가 없습니다.')
            self.check_rights(c,[source['sha256']])
            if not source.get('rights') or source['rights']=='사용권 미확인':raise ValueError('출처 사용권 근거를 먼저 기록하세요.')
            if hashlib.sha256(Path(source['asset']).read_bytes()).hexdigest()!=source['sha256']:raise ValueError('출처 자산이 변경되었습니다.')
            s.attach_take(song,d['shot'],source['asset'],reason=text(d['reason']),expected_revision=expected)
            target['takes'][-1].update(metadata=deepcopy(source.get('metadata',{})),rights=source['rights'],filename=source.get('filename','reused'),provenance=dict(song=source_song,shot=source_shot,take=source_take))
        elif action=='audio':
            ext=Path(text(d['filename'])).suffix.lower()
            if ext not in {'.wav','.mp3','.m4a','.flac','.ogg'}:raise ValueError('WAV/MP3/M4A/FLAC/OGG만 지원합니다.')
            raw=base64.b64decode(d['content'],validate=True)
            rights=text(d['rights'])
            path,metadata=self.save_media(raw,ext,'audio')
            item=dict(id=len(p['audio_versions'])+1,asset=str(path),sha256=hashlib.sha256(raw).hexdigest(),filename=text(d['filename']),metadata=metadata,rights=rights)
            p['audio_versions'].append(item);p['audio_selected']=item['id'];p['revision']+=1
        elif action=='timeline':
            save_timeline(p,d['timeline'])
        elif action=='restore_timeline':
            version=number(d['version'])
            if not 1<=version<=len(p['timeline_versions']):raise ValueError('버전이 없습니다.')
            save_timeline(p,p['timeline_versions'][version-1])
        elif action=='review_take':
            shot=p['shots'][text(d['shot'])]
            take=number(d['take'])
            if take not in [x['id'] for x in shot['takes']]:raise ValueError('해당 샷의 take가 아닙니다.')
            decision=text(d['decision'])
            if decision not in {'approved','changes_requested','rejected'}:raise ValueError('검토 상태를 확인하세요.')
            shot.setdefault('reviews',[]).append(dict(take=take,decision=decision,reason=text(d['reason']),actor='local-owner',at=time.time()))
            shot['revision']+=1
        elif action=='approve_timeline':
            timeline=current(p)
            if timeline['id']==0:raise ValueError('타임라인을 먼저 저장하세요.')
            self.check_rights(c,self.snapshot_hashes(render_project(p,timeline)))
            for clip in timeline['clips']:
                take=next(t for t in p['shots'][clip['shot']]['takes'] if t['id']==clip['take'])
                review=next((r for r in reversed(p['shots'][clip['shot']].get('reviews',[])) if r['take']==clip['take']),None)
                if not review or review['decision']!='approved':raise ValueError('각 타임라인 take를 먼저 승인하세요.')
                if not take.get('rights') or take['rights']=='사용권 미확인':raise ValueError('각 take를 사용권 근거와 함께 다시 연결하세요.')
            if any(not x['resolved'] for x in p['comments']):raise ValueError('미해결 검토 의견을 먼저 해결하세요.')
            p['timeline_versions'][timeline['id']-1]['approval']=dict(actor='local-owner',at=time.time(),scope='로컬 단일 사용자 승인; 조직 권한 검증 아님')
        elif action=='comment':
            p['comments'].append(dict(id=len(p['comments'])+1,at=seconds(d['at']),text=text(d['text']),timeline=p['timeline_head'],resolved=False))
        elif action=='resolve_comment':
            comment=next((x for x in p['comments'] if x['id']==number(d['id'])),None)
            if not comment:raise ValueError('검토 의견이 없습니다.')
            comment['resolved']=True
        elif action in {'estimate_render','render_job'}:
            timeline=current(p)
            if not timeline.get('approval'):raise ValueError('저장한 타임라인을 승인한 후 출력하세요.')
            for clip in timeline['clips']:
                shot=p['shots'][clip['shot']]
                review=next((r for r in reversed(shot.get('reviews',[])) if r['take']==clip['take']),None)
                if not review or review['decision']!='approved':raise ValueError('승인이 철회되거나 누락된 take가 있습니다.')
                if shot['selected']!=clip['take']:raise ValueError('현재 take 선택이 타임라인과 다릅니다. 새 편집 버전을 저장·승인하세요.')
            if any(not x['resolved'] for x in p['comments']):raise ValueError('미해결 검토 의견이 있습니다.')
            snapshot=render_project(p,timeline)
            self.check_rights(c,self.snapshot_hashes(snapshot))
            if action=='estimate_render':
                quote=render_estimate(snapshot)
                p.setdefault('render_estimates',[]).append(quote)
                return {'estimate':quote['id']}
            quote=None
            if d.get('estimate'):
                quote=next((q for q in p.get('render_estimates',[]) if q['id']==text(d['estimate'])),None)
                if quote is None:raise ValueError('출력 확인 기록이 없습니다.')
                validate_estimate(quote,snapshot)
                if quote.get('job'):return {'job':quote['job']}
            identifier=uuid.uuid4().hex
            job=dict(id=identifier,revision=1,song=song,status='queued',progress=0,created=time.time(),cancel_requested=False,snapshot=snapshot,download=None,error=None,cost=dict(provider_calls=0,provider_cost=0,local_compute='미계측',kind='render-only'))
            if quote:
                job['estimate']=deepcopy(quote)
                quote['job']=identifier
            c.execute('INSERT INTO jobs VALUES (?,?)',(identifier,json.dumps(job)))
            return {'job':identifier}
        return {}

    def validate_generation_submission(self,c,job):
        binding=job['context'].get('submission_binding')
        gate=self.generation_approval
        if not binding or not gate or gate.get('expires',0)<=time.time():raise ValueError('제출 승인이 없거나 만료됐습니다.')
        if guided.fingerprint(gate)!=binding['gate_hash'] or id(self.provider_adapter)!=binding['adapter_identity']:
            raise ValueError('큐 등록 이후 승인 또는 공급자 연결이 변경됐습니다.')
        prep=binding['preparation'];fal_provider.validate_gate(gate,prep,self.workspace_id)
        saved=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])
        project=saved['projects'].get(prep['song'])
        if not project or project.get('archived'):raise ValueError('작품을 사용할 수 없습니다.')
        shot=project['shots'].get(prep['shot'])
        if not shot or shot['revision']!=prep['shot_revision']:raise ValueError('등록 이후 샷이 변경됐습니다.')
        ref=next((r for r in shot.get('reference_versions',[]) if r['id']==prep['reference_version']),None)
        if not ref or ref['status']!='approved' or shot.get('reference_head')!=ref['id']:raise ValueError('시작 프레임 승인이 변경됐습니다.')
        self.check_rights(c,[prep['source']['sha256']])
        raw=Path(prep['source']['asset']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=prep['source']['sha256']:raise ValueError('입력 파일이 변경됐습니다.')
        if fal_provider.payload(prep['prompt'],raw)!=job['input']:raise ValueError('등록된 공급자 입력이 승인 입력과 다릅니다.')

    def process_generation(self):
        if self.provider_adapter is None:return False
        with self.connect() as c:
            jobs=[json.loads(r[0]) for r in c.execute('SELECT body FROM generation_jobs')]
        for job in jobs:
            try:
                if job['state']=='prepared':
                    self.generation.dispatch(job['id'],self.provider_adapter,pre_submit=self.validate_generation_submission);return True
                if job['state']=='cancel_pending':self.generation.send_cancel(job['id'],self.provider_adapter);return True
                if job['state'] in {'accepted','running','cancel_sent'} and time.time()-job['updated']>=5:
                    self.generation.poll(job['id'],self.provider_adapter);return True
                if job['state']=='result_ready':self.generation.import_result(job['id'],self.provider_adapter.download);return True
            except Exception as exc:
                # No repeated polling for terminal errors; unknown cost remains held.
                with self.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    latest=json.loads(c.execute('SELECT body FROM generation_jobs WHERE id=?',(job['id'],)).fetchone()[0])
                    if latest['state'] in {'result_ready','downloading'}:
                        latest['state']='import_blocked'
                        latest['failure_code']=exc.code if isinstance(exc,fal_provider.ProviderError) else 'local_media_validation_failed'
                        latest['retrieval_attempts']=latest.get('retrieval_attempts',0)+1
                    elif isinstance(exc,fal_provider.ProviderError) and exc.terminal:
                        latest['state']='failed';latest['failure_code']=exc.code
                    else:
                        latest['poll_errors']=latest.get('poll_errors',0)+1
                        if latest['poll_errors']>=3:latest['state']='reconciliation_required'
                    latest['last_error']='영구 오류로 조회를 종료했습니다. 비용 미확정·예약 유지. 입력/권한을 확인하세요.' if latest['state']=='failed' else '결과 조회/검증 보류. 기존 요청과 예약을 보존했습니다.'
                    if latest['state'] in {'failed','reconciliation_required','import_blocked'}:
                        row=c.execute('SELECT state FROM reservations WHERE id=?',(latest['reservation'],)).fetchone()
                        if row and row[0]=='reserved':ledger.command(c,self.workspace_id,latest['scope'],'uncertain',{'reservation':latest['reservation']},latest['id']+':poll-uncertain')
                    self.generation.save(c,latest)
                return False
        return False

    def recover_jobs(self):
        with self.connect() as c:
            for id,body in c.execute('SELECT id,body FROM jobs').fetchall():
                job=json.loads(body)
                if job['status']=='running':
                    job.update(status='interrupted',error='서버 재시작으로 중단됨. 기존 결과는 보존되며 자동 재실행하지 않습니다.')
                    job['revision']=job.get('revision',1)+1
                    c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),id))

    def process_next(self):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            job=next((json.loads(r[0]) for r in c.execute('SELECT body FROM jobs') if json.loads(r[0])['status']=='queued'),None)
            if not job:return False
            job.update(status='running',started=time.time())
            job['revision']=job.get('revision',1)+1
            c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(job),job['id']))
        def read():
            with self.connect() as c:return json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job['id'],)).fetchone()[0])
        def update(**values):
            with self.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=json.loads(c.execute('SELECT body FROM jobs WHERE id=?',(job['id'],)).fetchone()[0]);latest.update(values)
                latest['revision']=latest.get('revision',1)+1
                c.execute('UPDATE jobs SET body=? WHERE id=?',(json.dumps(latest),job['id']))
        out=self.root/'exports'/(job['id']+'.mp4')
        parts=self.root/'exports'/('parts-'+job['id'])
        parts.mkdir(exist_ok=True)
        staging=parts/'final.mp4'
        try:
            # Recheck content hashes immediately before rendering the frozen snapshot.
            snapshot=job['snapshot']
            with self.connect() as c:self.check_rights(c,self.snapshot_hashes(snapshot))
            for asset in [next(t for t in sh['takes'] if t['id']==sh['selected']) for sh in snapshot['shots'].values()]+([snapshot['audio']] if snapshot.get('audio') else []):
                if hashlib.sha256(Path(asset['asset']).read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('승인 후 자산이 변경되었습니다.')
            render(snapshot,staging,lambda value:update(progress=value),lambda:read()['cancel_requested'],parts)
            if read()['cancel_requested']:raise Cancelled('사용자가 취소했습니다.')
            verified=verify_output(staging,snapshot)
            if read()['cancel_requested']:raise Cancelled('사용자가 취소했습니다.')
            record=dict(job=job['id'],song=job['song'],timeline=snapshot['timeline'],sha256=hashlib.sha256(staging.read_bytes()).hexdigest(),audio=snapshot.get('audio'),cost=job['cost'],verified=verified,
                settings=snapshot.get('snapshot',[]),
                semantic_contexts=[deepcopy(sh.get('semantic_context')) for sh in snapshot['shots'].values()],
                selected_takes=[deepcopy(next(t for t in sh['takes'] if t['id']==sh['selected'])) for sh in snapshot['shots'].values()],
                reference_versions=[deepcopy(sh.get('reference_versions',[])) for sh in snapshot['shots'].values()])
            staging.replace(out)
            for suffix,body in [('.srt',srt(snapshot['subtitles'])),('.json',json.dumps(record,ensure_ascii=False,indent=2))]:
                temporary=parts/('record'+suffix)
                temporary.write_text(body)
                temporary.replace(self.root/'exports'/(job['id']+suffix))
            update(status='completed',progress=100,download='/exports/'+out.name,sha256=record['sha256'],verified=verified,finished=time.time())
        except Cancelled as exc:update(status='cancelled',error=str(exc),finished=time.time())
        except Exception as exc:update(status='failed',error=str(exc),finished=time.time())
        return True

def server(root, port, permissions=None, provider_adapter=None, generation_approval=None):
    store = Store(root)
    store.provider_adapter=provider_adapter
    store.generation_approval=generation_approval
    store.generation.recover()
    store.recover_jobs()
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def send(self, code, payload, kind='application/json', headers=None):
            data = payload if isinstance(payload,bytes) else json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            for key,value in (headers or {}).items():self.send_header(key,value)
            self.end_headers()
            self.wfile.write(data)
        def allowed(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        def do_GET(self):
            if not self.allowed(): return self.send(403, {'error':'로컬 접속만 허용됩니다.'})
            if self.path.startswith('/v1/'):
                status,payload=contracts.read(store,self.path,self.headers.get('Authorization')=='Bearer '+token,permissions)
                if status==200 and self.path.endswith('/events'):
                    last=self.headers.get('Last-Event-ID')
                    if last is not None and last!=str(payload['revision']):return self.send(409,contracts.error(409,'snapshot_refresh_required','이 로컬 구현은 현재 스냅샷만 제공합니다. 상태를 다시 조회하세요.')[1])
                    event=f"id: {payload['revision']}\nevent: snapshot\ndata: {json.dumps(payload,ensure_ascii=False)}\n\n"
                    return self.send(200,event.encode(),'text/event-stream')
                return self.send(status,payload)
            if permissions is not None:return self.send(403,{'error':'제한된 API principal은 legacy 작업실 경로를 사용할 수 없습니다.'})
            if self.path == '/': return self.send(200, (ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
            if self.path == '/api/state': return self.send(200, dict(store.state(), token=token))
            if self.path == '/api/model-catalog': return self.send(200, model_selection.catalog())
            if self.path == '/api/operations': return self.send(200, store.operations())
            if self.path.startswith('/api/requests/'):
                identifier = self.path.removeprefix('/api/requests/')
                with store.connect() as c:
                    row = c.execute('SELECT result FROM requests WHERE id=?', (identifier,)).fetchone()
                return self.send(200, dict(status='committed', result=json.loads(row[0]))) if row else self.send(404, dict(status='unknown'))
            if self.path.startswith(('/assets/', '/exports/')):
                path = store.root/self.path.lstrip('/')
                if path.parent in {store.root/'assets', store.root/'exports'} and path.is_file():
                    if path.parent==store.root/'assets':
                        try:
                            with store.connect() as c:store.check_rights(c,[path.stem])
                        except ValueError as exc:return self.send(403,{'error':str(exc)})
                    if path.parent==store.root/'exports':
                        with store.connect() as c:
                            try:store.check_rights(c,[r[0] for r in c.execute('SELECT sha256 FROM export_assets WHERE filename=?',(path.name,))])
                            except ValueError as exc:return self.send(403,{'error':str(exc)})
                            record=c.execute('SELECT body FROM jobs WHERE id=?',(path.stem,)).fetchone()
                            if record:
                                if json.loads(record[0])['status']!='completed':return self.send(409,{'error':'완료된 출력만 다운로드할 수 있습니다.'})
                                try:store.check_rights(c,store.snapshot_hashes(json.loads(record[0])['snapshot']))
                                except ValueError as exc:return self.send(403,{'error':str(exc)})
                    if path.suffix=='.mp4' and path.parent==store.root/'exports':
                        with store.connect() as c:
                            row=c.execute('SELECT body FROM jobs WHERE id=?',(path.stem,)).fetchone()
                        if row:
                            job=json.loads(row[0])
                            try:
                                with store.connect() as c:store.check_rights(c,store.snapshot_hashes(job['snapshot']))
                            except ValueError as exc:return self.send(403,{'error':str(exc)})
                            if job['status']!='completed' or hashlib.sha256(path.read_bytes()).hexdigest()!=job.get('sha256'):
                                return self.send(409,{'error':'완료되지 않았거나 검토 파일 해시가 변경되었습니다.'})
                    return self.send(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.send(404, {'error':'찾을 수 없습니다.'})
        def do_POST(self):
            if self.path.startswith('/v1/'):
                if not self.allowed():return self.send(403,contracts.error(403,'forbidden','로컬 접속만 허용됩니다.')[1])
                try:
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=100_000:raise ValueError()
                    body=json.loads(self.rfile.read(length))
                except (ValueError,TypeError):return self.send(400,contracts.error(400,'invalid_json','JSON 요청 본문을 확인하세요.')[1])
                status,payload=contracts.cancel_job(store,self.path,body,self.headers.get('Idempotency-Key'),self.headers.get('Authorization')=='Bearer '+token,permissions)
                return self.send(status,payload)
            if permissions is not None:return self.send(403,{'error':'제한된 API principal은 legacy 변경 경로를 사용할 수 없습니다.'})
            if not self.allowed() or self.headers.get('X-Loretune-Token') != token:
                return self.send(403, {'error':'접근 토큰이 만료되었습니다. 새로고침하세요.'})
            if self.path != '/api/action': return self.send(404, {'error':'찾을 수 없습니다.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length < 24*1024*1024: raise ValueError('요청 크기를 확인하세요 (파일 최대 16MB).')
                request = json.loads(self.rfile.read(length))
                self.send(200, store.mutate(request))
            except (Conflict,ontology.Conflict) as exc: self.send(409, {'error':str(exc)})
            except (ValueError, KeyError, TypeError, OSError) as exc:
                self.send(400, {'error':'입력을 확인하세요: '+str(exc)})
        def do_PATCH(self):
            if not self.allowed():return self.send(403,contracts.error(403,'forbidden','로컬 접속만 허용됩니다.')[1])
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=100_000:raise ValueError()
                body=json.loads(self.rfile.read(length))
            except (ValueError,TypeError):return self.send(400,contracts.error(400,'invalid_json','JSON 요청 본문을 확인하세요.')[1])
            status,payload=contracts.patch_budget(store,self.path,body,self.headers.get('If-Match'),self.headers.get('Authorization')=='Bearer '+token,permissions)
            return self.send(status,payload,headers={'ETag':'"'+str(payload['revision'])+'"'} if status==200 else None)
    http=ThreadingHTTPServer(('127.0.0.1', port), Handler)
    http.store=store
    http.token=token
    return http

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data', type=Path, default=ROOT/'data')
    args = parser.parse_args()
    app = server(args.data, args.port)
    print(f'Loretune: http://127.0.0.1:{app.server_port}', flush=True)
    def worker():
        while True:
            if not app.store.process_next() and not app.store.process_generation():time.sleep(.3)
    Thread(target=worker,daemon=True).start()
    app.serve_forever()
