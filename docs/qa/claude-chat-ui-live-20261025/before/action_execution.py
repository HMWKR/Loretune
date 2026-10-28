"""Immutable action/grant/ledger rehearsal. No provider transports or credentials.
All writes require the caller's BEGIN IMMEDIATE transaction. Live execution absent.
"""
import json,time,uuid
from copy import deepcopy
import ledger
from guided import fingerprint
from loretune import Conflict

class ExecutionBlocked(ValueError):
 pass

def project_jobs(c,w,p,name):
 """Database ownership projection shared by tool lookup and model handoff."""
 result=[]
 for row in c.execute('SELECT body FROM generation_jobs'):
  j=json.loads(row[0])
  if j.get('context',{}).get('song')==name:
   result.append(dict(id=j['id'],state=j['state'],mode=j.get('mode','provider-unverified'),context={'song':name}))
 for row in c.execute('SELECT body FROM action_jobs WHERE workspace=? AND project=?',(w,p)):
  j=json.loads(row[0]);result.append(dict(id=j['id'],state=j['state'],mode=j['mode'],context={'song':name}))
 return result


def initialize(c):
 for table in ['production_actions','execution_grants','action_jobs']:
  c.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, workspace TEXT NOT NULL, project TEXT NOT NULL, body TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS action_admissions (workspace TEXT, project TEXT, action TEXT, job TEXT, PRIMARY KEY(workspace,project,action))')


def get(c,table,workspace,project,identifier):
 if table not in {'production_actions','execution_grants','action_jobs'}:raise ValueError('invalid table')
 row=c.execute(f'SELECT body FROM {table} WHERE id=? AND workspace=? AND project=?',(identifier,workspace,project)).fetchone()
 if not row:raise ValueError('현재 작품의 객체가 아닙니다.')
 return json.loads(row[0])


def put(c,table,w,p,value):
 c.execute(f'INSERT INTO {table} VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(value['id'],w,p,json.dumps(value)))


def propose(c,w,p,*,plan_id,plan_revision,context_hash,role,release_id,inputs,options,dependencies=(),context_kind='full-v1'):
 if role not in {'image','video'} or type(plan_revision) is not int or plan_revision<1:raise ValueError('작업 역할·계획 버전 오류')
 if not all(isinstance(x,str) and x for x in [plan_id,context_hash,release_id]):raise ValueError('고정 식별자가 필요합니다.')
 if not isinstance(inputs,dict) or not isinstance(options,dict):raise ValueError('구조화 입력이 필요합니다.')
 if not isinstance(dependencies,(list,tuple)) or len(dependencies)!=len(set(dependencies)):raise ValueError('의존 작업 목록 오류')
 for dependency in dependencies:get(c,'production_actions',w,p,dependency)
 if context_kind not in {'full-v1','media-v1'}:raise ValueError('승인 문맥 종류 오류')
 value=dict(id=uuid.uuid4().hex,plan_id=plan_id,plan_revision=plan_revision,context_hash=context_hash,context_kind=context_kind,role=role,release_id=release_id,
            inputs=deepcopy(inputs),options=deepcopy(options),dependencies=list(dependencies),mode='rehearsal',connection_id=None)
 value['hash']=fingerprint(value);put(c,'production_actions',w,p,value);return value


def grant(c,w,p,action_ids,*,actor,approved,expires,price_revision,money_by_action):
 # Called by the local human controller, not by any model tool.
 if actor!='local-owner' or approved is not True:raise ValueError('사람의 명시적 승인이 필요합니다.')
 if not action_ids or len(set(action_ids))!=len(action_ids) or set(action_ids)!=set(money_by_action):raise ValueError('승인 작업과 견적 범위가 다릅니다.')
 if type(expires) not in (int,float) or not time.time()<expires<=time.time()+3600:raise ValueError('승인 만료 오류')
 actions=[get(c,'production_actions',w,p,x) for x in action_ids]
 for money in money_by_action.values():ledger.units(money)
 value=dict(id=uuid.uuid4().hex,revision=1,state='active',actor=actor,expires=expires,price_revision=price_revision,
            action_hashes={x['id']:x['hash'] for x in actions},money=deepcopy(money_by_action),mode='rehearsal',external_transmission=False)
 value['hash']=fingerprint(value);put(c,'execution_grants',w,p,value);return value


def revoke(c,w,p,identifier,expected_revision):
 g=get(c,'execution_grants',w,p,identifier)
 if g['revision']!=expected_revision:raise Conflict('승인 버전 충돌')
 g.update(state='revoked',revision=g['revision']+1);put(c,'execution_grants',w,p,g);return g


def validate(action,g,context_hash,price_revision):
 if fingerprint({k:v for k,v in g.items() if k!='hash'})!=g['hash']:raise ValueError('승인 내용 변조')
 if g['state']!='active' or g['expires']<=time.time():raise ValueError('승인 철회 또는 만료')
 if g['action_hashes'].get(action['id'])!=action['hash'] or fingerprint({k:v for k,v in action.items() if k!='hash'})!=action['hash']:raise ValueError('승인 작업 변조')
 if action['context_hash']!=context_hash or g['price_revision']!=price_revision:raise ValueError('문맥 또는 가격 버전 변경')


def admit(c,w,p,identifier,grant_id,*,context_hash,price_revision):
 action=get(c,'production_actions',w,p,identifier);g=get(c,'execution_grants',w,p,grant_id)
 validate(action,g,context_hash,price_revision)
 prior=c.execute('SELECT job FROM action_admissions WHERE workspace=? AND project=? AND action=?',(w,p,identifier)).fetchone()
 if prior:return get(c,'action_jobs',w,p,prior[0])
 # No parent reservation: each executable action reserves exactly once.
 dependencies=[]
 for dep in action['dependencies']:
  row=c.execute('SELECT job FROM action_admissions WHERE workspace=? AND project=? AND action=?',(w,p,dep)).fetchone()
  if not row:raise ValueError('선행 작업이 없습니다.')
  j=get(c,'action_jobs',w,p,row[0])
  if j['state']!='collected' or not j.get('result'):raise ValueError('선행 결과 수집·승인이 필요합니다.')
  if j.get('result_approved') is not True:raise ValueError('선행 결과 승인 필요')
  dependencies.append(dict(action=dep,job=j['id'],result=deepcopy(j['result'])))
 scope='rehearsal:project:'+p;b=ledger.budget(c,w,scope)
 if not b:raise ValueError('모의 원장 예산이 없습니다. 실제 공급자 원장과 분리됩니다.')
 identifier_job=uuid.uuid4().hex
 reserve=ledger.command(c,w,scope,'reserve',dict(money=g['money'][identifier],budget_revision=b['revision'],expires=g['expires'],job=identifier_job),identifier_job)
 job=dict(id=identifier_job,action=deepcopy(action),grant=g['id'],grant_hash=g['hash'],state='prepared',reservation=reserve['reservation'],scope=scope,
          dependencies=dependencies,result=None,result_approved=False,mode='rehearsal',external_calls=0)
 put(c,'action_jobs',w,p,job)
 c.execute('INSERT INTO action_admissions VALUES (?,?,?,?)',(w,p,identifier,identifier_job))
 return job


def claim(c,w,p,identifier,*,context_hash,price_revision,rights_valid=True):
 j=get(c,'action_jobs',w,p,identifier)
 if j['state']!='prepared':return j
 g=get(c,'execution_grants',w,p,j['grant'])
 try:
  validate(j['action'],g,context_hash,price_revision)
  if not rights_valid or g['hash']!=j['grant_hash']:raise ValueError('권리 또는 승인 변경')
  for dependency in j['dependencies']:
   parent=get(c,'action_jobs',w,p,dependency['job'])
   if parent['state']!='collected' or not parent['result_approved'] or parent['result']!=dependency['result']:raise ValueError('선행 승인 결과 변경')
 except ValueError:
  ledger.command(c,w,j['scope'],'release',{'reservation':j['reservation']},j['id']+':blocked')
  j['state']='blocked';put(c,'action_jobs',w,p,j);return j
 j['state']='claimed';put(c,'action_jobs',w,p,j);return j


def record_result(c,w,p,identifier,*,asset_hash,output_slot):
 j=get(c,'action_jobs',w,p,identifier)
 if j['state']=='collected':
  if j['result']!=dict(sha256=asset_hash,output_slot=output_slot):raise Conflict('같은 작업의 다른 결과')
  return j
 if j['state']!='claimed' or output_slot!=j['action']['role']:raise ValueError('작업 상태·출력 슬롯 오류')
 if not isinstance(asset_hash,str) or len(asset_hash)!=64 or any(x not in '0123456789abcdef' for x in asset_hash):raise ValueError('검증된 파일 해시 필요')
 j.update(state='collected',result=dict(sha256=asset_hash,output_slot=output_slot))
 put(c,'action_jobs',w,p,j);return j


def approve_result(c,w,p,identifier,*,actor):
 j=get(c,'action_jobs',w,p,identifier)
 if actor!='local-owner' or j['state']!='collected':raise ValueError('수집된 결과에 대한 사람 검토 필요')
 j['result_approved']=True;put(c,'action_jobs',w,p,j);return j


def recover(c,w,p):
 for row in c.execute('SELECT body FROM action_jobs WHERE workspace=? AND project=?',(w,p)).fetchall():
  j=json.loads(row[0])
  if j['state']=='claimed':
   j['state']='outcome_unknown';ledger.command(c,w,j['scope'],'uncertain',{'reservation':j['reservation']},j['id']+':unknown');put(c,'action_jobs',w,p,j)


def request_from_plan(c,w,p,project,args):
 """Server-scoped bridge; accepts only previously saved human-approved rehearsal actions."""
 import guided
 import model_selection
 if set(args)!={'plan_id','action_id','grant_id'}:raise ValueError('생성 요청 식별자만 허용됩니다.')
 if project.get('archived'):raise ValueError('보관된 작품에서는 실행할 수 없습니다.')
 plan=next((x for x in project.get('guided_plans',[]) if x['id']==args['plan_id']),None)
 if plan is None:raise ValueError('현재 작품의 저장된 계획이 아닙니다.')
 if plan['context_hash']!=guided.fingerprint(guided.context(project)):raise Conflict('계획 문맥이 변경됐습니다.')
 action=get(c,'production_actions',w,p,args['action_id'])
 if action['plan_id']!=plan['id'] or action['plan_revision']!=plan['version']:raise Conflict('작업과 계획 버전이 다릅니다.')
 if action['mode']!='rehearsal' or action['connection_id'] is not None:raise ValueError('실제 공급자 실행은 연결되지 않았습니다.')
 # A model cannot choose a new price version or mint a grant through this bridge.
 get(c,'execution_grants',w,p,args['grant_id'])
 try:job=admit(c,w,p,action['id'],args['grant_id'],context_hash=model_selection.action_context(project,action),price_revision='rehearsal-v1')
 except Conflict:raise
 except ValueError:raise ExecutionBlocked('승인·예산·의존 결과를 다시 검토하세요.') from None
 return dict(status='accepted',job_id=job['id'],state=job['state'],mode='rehearsal',external_calls=0,
             note='로컬 모의 실행 계약만 접수했습니다. 실제 AI 생성·외부 전송은 실행하지 않았습니다.')

def request_with_savepoint(c,w,p,project,args):
 c.execute('SAVEPOINT production_tool_action')
 try:
  result=request_from_plan(c,w,p,project,args)
 except Exception:
  c.execute('ROLLBACK TO production_tool_action');c.execute('RELEASE production_tool_action');raise
 c.execute('RELEASE production_tool_action');return result
