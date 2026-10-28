"""Disabled-by-default, consent-scoped chat with separated fixture/live modes.

Each exact count and message body is approved together for a single round;
subsequent tool results require a new manifest and human decision.
"""
import hashlib
import http.client
import json
import re
import time
import uuid
from copy import deepcopy
from decimal import Decimal, ROUND_CEILING

import chat_models
import chat_protocols
import chat_runtime
import chat_sessions
import contracts
import general_chat_config
import guided
import ledger
import model_selection
import production_tools
import agent_preferences

TTL_SECONDS = 300
# D20 (user: "상한만 올리기"); 16384 is the lead's stated assumption. Transport stays 64 KiB.
MAX_INPUT = 16384
MAX_OUTPUT = 4096
MAX_ROUNDS = 4
# Per-turn continuation budget (SRV-r3). Each continuation carries every earlier round of the
# turn, so a tool result that would push the next body past BODY_CAP - CONTINUATION_MARGIN is
# replaced by a CONTEXT_BUDGET_EXHAUSTED notice. The margin leaves room for the next round's
# assistant message plus such a notice, so a model that keeps following next_query cannot lock
# the conversation as outcome_unknown.
BODY_CAP = 65536
CONTINUATION_MARGIN = 8192
CONTINUATION_LIMIT = BODY_CAP - CONTINUATION_MARGIN
CONVERSATION_CAP_MICRO = 400000
MAX_OBSERVED_TOKEN_DIGITS = 256
MAX_OBSERVED_TOKENS = 10 ** MAX_OBSERVED_TOKEN_DIGITS - 1
SAFE_JSON_INTEGER = 2 ** 53 - 1
ALLOWED_TOOLS = ('propose_media_plan', 'search_project_context',
                 'propose_timeline_changes', 'request_render',
                 'propose_motion_scene', 'request_motion_render',
                 'get_model_capabilities', 'prepare_image_action',
                 'get_generation_job', 'estimate_media_plan',
                 'prepare_video_action', 'get_agent_settings',
                 'propose_scene_3d', 'propose_preference_rule')


def initialize(c):
    c.execute('CREATE TABLE IF NOT EXISTS general_chat_previews (id TEXT PRIMARY KEY, project TEXT NOT NULL, conversation TEXT NOT NULL, body TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS general_chat_turns (id TEXT PRIMARY KEY, project TEXT NOT NULL, conversation TEXT NOT NULL, body TEXT NOT NULL)')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class FixtureTransport:
    """An in-memory response fixture. It has no endpoint, credentials or I/O."""
    mode = 'contract-fake'
    def __init__(self, responses):
        self.responses = deepcopy(responses)
        self.counted = []
        self.messages = []
    def count(self, body):
        self.counted.append(deepcopy(body))
        return 100
    def complete(self, body):
        self.messages.append(deepcopy(body))
        if not self.responses: raise ValueError('fixture response unavailable')
        value = self.responses.pop(0)
        if value == '__unknown__': raise TimeoutError('fixture timeout')
        return deepcopy(value)


class LoopbackTransport:
    """Synthetic HTTP transport; cannot send to a remote endpoint or real key."""
    def __init__(self, port):
        if type(port) is not int or not 1<=port<=65535:raise ValueError('invalid loopback port')
        self.port=port
    def __call__(self, endpoint, headers, body):
        paths={chat_runtime.anthropic.ENDPOINT:'/messages',chat_runtime.anthropic.ENDPOINT+'/count_tokens':'/count_tokens'}
        if endpoint not in paths or headers.get('x-api-key')!='synthetic-key-not-real':raise ValueError('synthetic-only transport')
        raw=json.dumps(body,ensure_ascii=False,allow_nan=False).encode('utf-8')
        if len(raw)>65536:raise ValueError('request too large')
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        try:
            connection.request('POST',paths[endpoint],body=raw,headers=headers)
            response=connection.getresponse()
            if response.status!=200:raise ValueError('fixture HTTP failure')
            payload=response.read(100001)
            if len(payload)>100000:raise ValueError('fixture response too large')
            value=json.loads(payload.decode('utf-8'))
            if not isinstance(value,dict):raise ValueError('fixture response invalid')
            return value
        finally:connection.close()


class LiveTransport:
    """Trusted server configuration, never supplied by a browser request.

    `test_only` is an isolated loopback transport. Actual delivery requires an
    explicit validated activation; Runtime still owns exact consent and claims.
    The connection ID and revision are administrator declarations, not proof
    that a provider account or billing identity has been verified.
    """
    def __init__(self, adapter, connection_id, connection_revision, *, test_only=False, activation=None):
        if type(test_only) is not bool or type(adapter) is not chat_runtime.AnthropicChatAdapter or not adapter.enabled:
            raise ValueError('명시적으로 활성화된 Anthropic 연결이 필요합니다.')
        if not isinstance(connection_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',connection_id):
            raise ValueError('연결 식별자를 확인하세요.')
        if type(connection_revision) is not int or connection_revision<1:
            raise ValueError('연결 버전을 확인하세요.')
        if test_only and (type(adapter.count_transport) is not LoopbackTransport or
                          type(adapter.message_transport) is not LoopbackTransport or
                          adapter.count_transport.port!=adapter.message_transport.port):
            raise ValueError('시험 전송은 명시된 로컬 루프백만 허용합니다.')
        if not test_only and (type(adapter.count_transport) is not chat_runtime.anthropic.BoundedCountTransport or
                              type(adapter.message_transport) is not chat_runtime.anthropic.BoundedMessagesTransport or
                              adapter.count_transport._opener is not None or adapter.message_transport._opener is not None):
            raise ValueError('실제 전송에는 고정 Anthropic 경로가 필요합니다.')
        self.adapter=adapter;self.connection_id=connection_id;self.connection_revision=connection_revision;self.test_only=test_only
        if test_only and activation is not None:raise ValueError('시험 연결에는 실제 활성화 설정을 사용할 수 없습니다.')
        self.activation=activation
        self._production_binding=(adapter,adapter.supplier,adapter.count_transport,adapter.message_transport)
        self.mode='contract-live-test' if test_only else 'anthropic-live'
    def require_activation(self,workspace=None):
        settings=self.activation
        if type(settings) is not general_chat_config.Configuration:
            raise general_chat_config.GeneralChatConfigError('명시적으로 활성화된 일반 Claude 관리자 설정이 필요합니다.')
        settings.validate()
        if (not settings.enabled or settings.connection_id!=self.connection_id or
            settings.connection_revision!=self.connection_revision or
            (workspace is not None and settings.workspace_id!=workspace)):
            raise general_chat_config.GeneralChatConfigError('일반 Claude 연결과 대상 작업공간 설정을 확인하세요.')
        return settings
    def validate(self):
        if type(self.adapter) is not chat_runtime.AnthropicChatAdapter or not self.adapter.enabled:
            raise ValueError('연결 설정이 변경됐습니다.')
        if self.test_only:
            if (self.mode!='contract-live-test' or type(self.adapter.count_transport) is not LoopbackTransport or
                type(self.adapter.message_transport) is not LoopbackTransport or
                self.adapter.count_transport.port!=self.adapter.message_transport.port):raise ValueError('시험 전송 설정이 변경됐습니다.')
        elif (self.mode!='anthropic-live' or type(self.adapter.count_transport) is not chat_runtime.anthropic.BoundedCountTransport or
              type(self.adapter.message_transport) is not chat_runtime.anthropic.BoundedMessagesTransport or
              self.adapter.count_transport._opener is not None or self.adapter.message_transport._opener is not None):
            raise ValueError('실제 전송 설정이 변경됐습니다.')
        if not self.test_only:
            self.require_activation()
            if (any(now is not pinned for now,pinned in zip(
                    (self.adapter,self.adapter.supplier,self.adapter.count_transport,self.adapter.message_transport),self._production_binding)) or
                self.adapter.count_transport.endpoint!=chat_runtime.anthropic.ENDPOINT+'/count_tokens' or
                self.adapter.message_transport.endpoint!=chat_runtime.anthropic.ENDPOINT):
                raise ValueError('실제 전송 설정이 변경됐습니다.')
    @property
    def destination(self):
        self.validate()
        return f'http://127.0.0.1:{self.adapter.count_transport.port}' if self.test_only else 'https://api.anthropic.com'
    def count(self,body):
        self.validate()
        return self.adapter.count(body)
    def complete(self,body):
        self.validate()
        return self.adapter.complete(body)


def transport_binding(store):
    runtime=getattr(store,'general_chat_runtime',None)
    transport=getattr(runtime,'transport',None)
    if isinstance(transport,LiveTransport):
        transport.validate()
        value=dict(mode=transport.mode,connection_id=transport.connection_id,
                   connection_revision=transport.connection_revision,destination=transport.destination)
        if not transport.test_only:value['activation_sha256']=transport.require_activation(store.workspace_id).digest()
        return value
    return None


def budget_scope(bound):
    mode=bound.get('transport',{}).get('mode')
    return ('project:' if mode=='anthropic-live' else 'rehearsal-live:project:' if mode=='contract-live-test' else 'rehearsal:project:')+bound['project']


def selected(p):
    result = model_selection.resolve('chat', explicit=chat_sessions.selected_chat(p))['selection']
    if not result or result['provider'] != 'anthropic': raise ValueError('선택된 Claude 모델이 필요합니다.')
    if result['state'] in {'disabled','retired','integration_blocked'}:raise ValueError('선택한 모델은 현재 사용할 수 없습니다.')
    return chat_models.contract(result['id'])


def rights_snapshot(c):
    return digest(c.execute('SELECT sha256,blocked,reason,updated FROM asset_rights ORDER BY sha256').fetchall())


def binding(c, store, p, name, *, turn=None,legacy_default=False):
    spec = selected(p)
    value=dict(workspace=store.workspace_id, project=contracts.project_id(store.workspace_id, name),
                conversation=chat_sessions.current(p), selection=spec['id'], model=spec['model'],
                model_revision=chat_sessions.resolve(p, chat_sessions.current(p))['model_revision'],
                context=model_selection.snapshot(p)['sha256'], rights=rights_snapshot(c),
                price_revision=spec['price_revision'])
    session=chat_sessions.resolve(p,chat_sessions.current(p))
    pending=session.get('pending_chat_selection') or {}
    if (turn and pending.get('after_turn')==turn['id'] and
        pending.get('execution_run')==turn['run'] and
        pending.get('execution_selection')==turn['binding']['selection'] and
        pending.get('reserved_model_revision')==session['model_revision'] and
        pending.get('execution_model_revision')==turn['binding']['model_revision'] and
        value['selection']==turn['binding']['selection'] and value['model']==turn['binding']['model']):
        value['model_revision']=turn['binding']['model_revision']
    if turn:
        if 'agent_settings' in turn['binding']:
            settings=agent_preferences.validate_snapshot(turn.get('agent_settings'))
            if settings!=turn['binding']['agent_settings']:raise ValueError('응답에 고정한 에이전트 설정이 변경됐습니다.')
            value['agent_settings']=settings
    else:
        settings=agent_preferences.profile(p,spec['id'])
        if not legacy_default or settings!=dict(selection=spec['id'],revision=0,mode='review',effort='low'):
            value['agent_settings']=settings
    transport=transport_binding(store)
    if transport:value['transport']=transport
    return value


def get_row(c, table, identifier):
    if table not in {'general_chat_previews', 'general_chat_turns'}: raise ValueError('invalid table')
    row = c.execute('SELECT body FROM '+table+' WHERE id=?', (identifier,)).fetchone()
    if not row: raise ValueError('대화 확인 항목이 없습니다.')
    return json.loads(row[0])


def put(c, table, item):
    if table not in {'general_chat_previews', 'general_chat_turns'}: raise ValueError('invalid table')
    c.execute('INSERT INTO '+table+' VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
              (item['id'], item['binding']['project'], item['binding']['conversation'], json.dumps(item, ensure_ascii=False)))


def public_preview(item):
    result={k: deepcopy(item[k]) for k in ('id','state','binding','message_body','count_body','message_sha256','count_sha256','manifest_sha256','maximum_micro','reserve_micro','expires','data_scope','destination','tool_scope','mode','turn_id')}
    result['prompt']=item['prompt']
    if 'total_maximum_micro' in item:result['total_maximum_micro']=item['total_maximum_micro']
    for key in ('message_wire_sha256','count_wire_sha256','endpoints','music_context','history_context'):
        if key in item:result[key]=deepcopy(item[key])
    return result


def manifest_digest(item):
    keys=('id','binding','message_body','count_body','message_sha256','count_sha256',
          'maximum_micro','reserve_micro','budget_revision','expires','data_scope','destination','tool_scope','mode','prompt','parent_turn_id')
    value={k:item[k] for k in keys}
    if 'total_maximum_micro' in item:value['total_maximum_micro']=item['total_maximum_micro']
    for key in ('message_wire_sha256','count_wire_sha256','endpoints','music_context','history_context','history_snapshot'):
        if key in item:value[key]=item[key]
    return digest(value)


def conversation_history(c, bound, exclude=None):
    """Only accepted general requests; prior output is unreviewed evidence."""
    approved={}
    for row in c.execute('SELECT body FROM general_chat_previews WHERE project=? AND conversation=?',
                         (bound['project'],bound['conversation'])):
        source=json.loads(row[0])
        if (source.get('state')=='consumed' and source.get('rights_confirmed') is True and
            source.get('parent_turn_id') is None and source.get('turn_id') and
            all(source.get('binding',{}).get(k)==bound[k] for k in ('workspace','project','conversation'))):
            approved[source['turn_id']]=source['prompt']
    turns=[]
    for row in c.execute('SELECT body FROM general_chat_turns WHERE project=? AND conversation=? ORDER BY rowid',
                         (bound['project'],bound['conversation'])):
        turn=json.loads(row[0])
        if turn['id']==exclude:continue
        if any(turn.get('binding',{}).get(k)!=bound[k] for k in ('workspace','project','conversation')):continue
        # Only the original consumed consent makes a persisted row a request.
        if turn['id'] in approved and approved[turn['id']]==turn.get('prompt'):turns.append(turn)
    requests=chat_runtime.request_history(bound['workspace'],bound['project'],turns,bound['conversation'])
    answers=[dict(turn_id=t['id'],text=t['answer'],review='unreviewed',canon=False)
             for t in turns if t['status']=='completed' and isinstance(t.get('answer'),str)][-8:]
    return dict(request_history=requests,public_answers=answers)


def check_history(c,item):
    # Older consent manifests are immutable: never inject history retroactively.
    if 'history_snapshot' not in item:return
    snapshot=item['history_snapshot']
    context=dict(request_count=len(snapshot['request_history']['requests']),
                 answer_count=len(snapshot['public_answers']),sha256=digest(snapshot))
    if item.get('history_context')!=context or conversation_history(c,item['binding'],item.get('turn_id'))!=snapshot:
        raise ValueError('이전 대화가 변경됐습니다. 전송 내용을 다시 확인하세요.')


class MusicContextChanged(ValueError):
    pass


class ContextBudgetExhausted(ValueError):
    def __init__(self, size):
        super().__init__('continuation body over budget');self.size=size


def wire_bytes(body):
    """Byte length of BoundedMessagesTransport.encode_body's serialization of body."""
    return len(json.dumps(body,ensure_ascii=False,allow_nan=False).encode('utf-8'))


def budget_notice(call, result, size, bytes_left):
    """Model-facing stand-in for a tool result that does not fit this turn's budget."""
    query=call['arguments'].get('query') if call['name']=='search_project_context' else None
    return dict(status='context_budget_exhausted',code='CONTEXT_BUDGET_EXHAUSTED',tool=call['name'],tool_status=result.get('status'),
                saved_ids={k:result[k] for k in ('proposal_id','preference_id','action_id','job_id','scene_id','plan_id') if isinstance(result.get(k),str)},
                result_included=False,body_bytes_with_result=size,body_limit_bytes=CONTINUATION_LIMIT,bytes_left=max(0,bytes_left),
                next_query=query,retry='new_turn',
                note='The tool ran and its result is stored, but it does not fit the request size budget of this turn, so it is not included. '
                     'Do not request more lookups in this turn. Answer with what you have; the user can continue in a new turn (pass next_query to search_project_context there).')


def check_music_context(c,p,item):
    """Check only the latest server lookup designated for this exact history.

    The marker is created from a persisted tool receipt, never user text or a
    scan for JSON-shaped messages. Older lookups remain historical context.
    """
    marker=item.get('music_context')
    if marker is None:return
    try:
        if set(marker)!={'run_id','call_id','message_index','tool_use_id','sha256'}:raise ValueError()
        turn=get_row(c,'general_chat_turns',item['parent_turn_id'])
        if marker['run_id']!=turn['run']:raise ValueError()
        run=next(x for x in p.get('production_runs',[]) if x['id']==marker['run_id'])
        call=next(x for x in run['calls'] if x['id']==marker['call_id'])
        if call['name']!='search_project_context' or call['result']['status']!='succeeded':raise ValueError()
        original=call['result']['execution_targets']['music_input']
        index=marker['message_index']
        if type(index) is not int or index<0:raise ValueError()
        message=item['message_body']['messages'][index]
        if message['role']!='user' or not isinstance(message['content'],list):raise ValueError()
        blocks=[b for b in message['content'] if isinstance(b,dict) and b.get('type')=='tool_result' and b.get('tool_use_id')==marker['tool_use_id']]
        if len(blocks)!=1:raise ValueError()
        disclosed=json.loads(blocks[0]['content'])['execution_targets']['music_input']
        if disclosed!=original or digest(original)!=marker['sha256']:raise ValueError()
    except (KeyError,TypeError,ValueError,IndexError,StopIteration) as exc:
        raise ValueError('음원 조회 결과와 전송 내용의 연결을 확인하세요.') from exc
    current=__import__('production_context').music_input(c,p,__import__('editing').current(p))
    if digest(current)!=marker['sha256']:
        raise MusicContextChanged('음원 또는 사용 구간이 변경됐습니다. 기존 이어쓰기를 거절한 뒤 다시 조회하고 새 전송 내용을 확인하세요.')


def public_turn(item):
    value = {k: deepcopy(item.get(k)) for k in ('id','conversation_id','status','mode','model','prompt','answer','error','round','preview_id','usage','observed_usage','pricing_status','usage_cost_usd','billing_confirmed','steps','journal_failure','count_status','message_status')}
    value['run_id'] = item.get('run')
    return value


def observe_usage(response):
    """Bounded, JSON-safe metadata only; never persist arbitrary response text."""
    return chat_models.observe_anthropic_usage(response,MAX_OBSERVED_TOKENS)


def unpriced_reason(observed,*,require_billing_evidence=False,usage=None):
    return chat_models.anthropic_unpriced_reason(observed,require_billing_evidence=require_billing_evidence,usage=usage)


def late_model_status(response, expected):
    """Compare to the submitted binding without storing provider model text."""
    if expected is None:return 'unknown'
    if not isinstance(response,dict) or 'model' not in response:return 'missing'
    if type(response['model']) is not str or not response['model'].strip():return 'invalid'
    return 'match' if response['model']==expected else 'mismatch'


def late_billing_sources(response):
    """Record only field locations, never provider-supplied values."""
    nested=response.get('usage') if isinstance(response,dict) else None
    sources={}
    for name in ('service_tier','speed','inference_geo','server_tool_use'):
        if not isinstance(nested,dict) or not isinstance(response,dict):sources[name]='unknown';continue
        top=name in response;inside=name in nested
        sources[name]='both' if top and inside else 'usage' if inside else 'response' if top else 'absent'
    return sources


def mark_pricing(store, turn, preview, status):
    """Update only the saved observation for this exact submitted round."""
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE');latest=get_row(c,'general_chat_turns',turn['id'])
        if (latest['preview_id']!=preview['id'] or latest['reservation']!=turn['reservation'] or
            latest['binding']!=turn['binding'] or latest['round']!=turn['round'] or
            not latest['steps'] or latest['steps'][-1].get('message_sha256')!=preview['message_sha256']):
            raise ValueError('관측 결과의 요청 연결이 변경됐습니다.')
        latest['pricing_status']=status;latest['steps'][-1]['pricing_status']=status
        put(c,'general_chat_turns',latest)
    return latest


def finish_run(project, turn, status):
    if status=='completed':chat_sessions.apply_completed_selection(project,turn)
    run=next((r for r in project.get('production_runs',[]) if r['id']==turn['run']),None)
    if run:
        run['state']=status
        if turn.get('mode')=='anthropic-live':
            run['live_model_called']=True if turn.get('provider_response_observed') else False if turn.get('message_status')=='not_sent' else None if turn.get('submitted') else False
        else:run['live_model_called']=False


def close_run(c, turn, status):
    revision,body=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
    state=json.loads(body);project=state['projects'].get(turn['name'])
    if project:
        finish_run(project,turn,status)
        c.execute('UPDATE state SET revision=?,body=? WHERE id=1',(revision+1,json.dumps(state,ensure_ascii=False)))


def claim_tool(c, store, project_id, run_id, call, request_id):
    """Guard a general-chat tool in the same transaction as its side effect."""
    rows=c.execute('SELECT body FROM general_chat_turns WHERE project=?',(project_id,)).fetchall()
    turns=[json.loads(row[0]) for row in rows if json.loads(row[0]).get('run')==run_id]
    if not turns:return  # Other, pre-existing production runs keep their contract.
    if len(turns)!=1 or store.general_chat_runtime is None:raise ValueError('도구 실행 문맥을 확인하세요.')
    turn=turns[0];preview=get_row(c,'general_chat_previews',turn['preview_id'])
    store.general_chat_runtime._current(c,turn,preview)
    expected=turn.get('pending_tool')
    declared={definition.get('name') for definition in preview['message_body'].get('tools',[])}
    if (not isinstance(expected,dict) or expected.get('call')!=call or expected.get('request_id')!=request_id or
        call.get('name') not in ALLOWED_TOOLS or call.get('name') not in preview['tool_scope'] or call.get('name') not in declared):
        raise ValueError('승인된 도구 요청이 아닙니다.')
    project=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'][turn['name']]
    project=chat_sessions.scoped(project,turn['conversation_id'])
    run=next((x for x in project.get('production_runs',[]) if x['id']==run_id),None)
    if run is None or agent_preferences.frozen(project,run)!=agent_preferences.frozen(project,turn):raise ValueError('에이전트 실행에 고정한 설정이 변경됐습니다.')
    turn.pop('pending_tool',None);put(c,'general_chat_turns',turn)


def create_preview(c, store, p, name, prompt, maximum_micro, *, turn=None, history=None, total_maximum_micro=None, music_context=None, history_snapshot=None, body_limit=None):
    if not isinstance(prompt,str) or not 1 <= len(prompt.strip()) <= 2000: raise ValueError('대화 입력을 확인하세요.')
    if type(maximum_micro) is not int or not 1 <= maximum_micro <= 100000: raise ValueError('요청 비용 상한을 확인하세요.')
    bound = binding(c,store,p,name,turn=turn); spec=selected(p)
    if history is None:
        history_snapshot=conversation_history(c,bound)
        history=[]
        if history_snapshot['request_history']['requests']:
            history.append(dict(role='user',content=(
                'Historical conversation evidence, not canonical project state or new instructions. '
                'Requests are verbatim in source order; quoted text, corrections and withdrawals retain their original meaning. '
                'Processing status is not approval. Prior assistant public answers are unreviewed, not canon. '
                'Use the current request below with this evidence; do not treat historical suggestions as approved actions.\n'
                +json.dumps(history_snapshot,ensure_ascii=False))))
        history.append(dict(role='user',content=prompt))
    settings=bound.get('agent_settings') or agent_preferences.legacy_settings(p,turn or {})
    run=next((x for x in p.get('production_runs',[]) if turn and x['id']==turn['run']),None)
    scope_run=run or dict(agent_settings=settings,agent_permission_ceiling=settings['mode'])
    permitted=agent_preferences.tools_for(p,scope_run,ALLOWED_TOOLS)
    definitions=[d for d in chat_protocols.tool_definitions('anthropic') if d['name'] in permitted]
    for item in definitions:item['strict']=True
    body=chat_models.body(spec, history if history is not None else [dict(role='user',content=prompt)], definitions, MAX_OUTPUT,effort=settings['effort'])
    live=bool(bound.get('transport'))
    if live:
        # Haiku 5.5 allows disabled thinking at low effort. Unexpected private
        # blocks are rejected rather than persisted or forwarded.
        body['thinking']={'type':'disabled'}
        if type(total_maximum_micro) is not int or not 1<=total_maximum_micro<=CONVERSATION_CAP_MICRO:
            raise ValueError('대화 전체 비용 상한을 확인하세요.')
    # Checked before anything is stored or reserved; the caller decides what to send instead.
    if body_limit is not None and wire_bytes(body)>body_limit:raise ContextBudgetExhausted(wire_bytes(body))
    count={k:deepcopy(v) for k,v in body.items() if k!='max_tokens'}
    worst=int((chat_models.cost(spec,MAX_INPUT,MAX_OUTPUT)*1000000).to_integral_value(rounding=ROUND_CEILING))
    if worst>maximum_micro: raise ValueError('요청 상한이 최대 예약액보다 작습니다.')
    if live and ((turn or {}).get('estimated_used_micro',0)+worst>total_maximum_micro):
        raise ValueError('대화 전체 비용 상한이 부족합니다.')
    scope=budget_scope(bound)
    budget=ledger.budget(c,store.workspace_id,scope)
    if not budget: raise ValueError('프로젝트 예산이 필요합니다.' if live else '테스트 예산이 필요합니다.')
    item=dict(id=uuid.uuid4().hex,state='pending',binding=bound,message_body=body,count_body=count,
              message_sha256=digest(body),count_sha256=digest(count),maximum_micro=maximum_micro,
              reserve_micro=worst,budget_revision=budget['revision'],expires=time.time()+TTL_SECONDS,
              data_scope='입력한 대화 및 이 미리보기에 표시된 도구 결과만 포함; 자산 파일은 전송하지 않음',
              destination='test-fixture-no-network',tool_scope=list(permitted),mode='contract-fake',
              turn_id=turn['id'] if turn else None,parent_turn_id=turn['id'] if turn else None,prompt=prompt)
    if history_snapshot is not None:
        item['history_snapshot']=deepcopy(history_snapshot)
        item['history_context']=dict(request_count=len(history_snapshot['request_history']['requests']),
                                     answer_count=len(history_snapshot['public_answers']),sha256=digest(history_snapshot))
        check_history(c,item)
    if music_context is not None:
        item['music_context']=deepcopy(music_context)
        check_music_context(c,p,item)
    if live:
        transport=store.general_chat_runtime.transport
        # Use the same encoder as the pinned transports before any credential read.
        count_wire=chat_runtime.anthropic.BoundedCountTransport(max_request_bytes=65536).encode_body(count)
        message_wire=chat_runtime.anthropic.BoundedMessagesTransport(max_request_bytes=65536).encode_body(body)
        item.update(mode=transport.mode,destination=transport.destination,total_maximum_micro=total_maximum_micro,
                    message_wire_sha256=hashlib.sha256(message_wire).hexdigest(),
                    count_wire_sha256=hashlib.sha256(count_wire).hexdigest(),
                    endpoints={'count':(transport.destination+'/count_tokens' if transport.test_only else chat_runtime.anthropic.ENDPOINT+'/count_tokens'),
                               'message':(transport.destination+'/messages' if transport.test_only else chat_runtime.anthropic.ENDPOINT)})
    item['manifest_sha256']=manifest_digest(item)
    put(c,'general_chat_previews',item)
    return public_preview(item)


def preview(c, store, p, name, data):
    live=bool(transport_binding(store))
    expected={'song','prompt','maximum_micro','total_maximum_micro'} if live else {'song','prompt','maximum_micro'}
    if set(data)!=expected: raise ValueError('대화 입력과 비용 상한을 확인하세요.')
    if any(json.loads(r[0])['status'] in {'queued','running','outcome_unknown','cancel_requested','awaiting_continuation_approval'}
           for r in c.execute('SELECT body FROM general_chat_turns WHERE project=? AND conversation=?',
                              (contracts.project_id(store.workspace_id,name),chat_sessions.current(p)))):
        raise ValueError('기존 대화 결과를 먼저 확인하세요.')
    if any(json.loads(r[0])['status'] in {'queued','running','outcome_unknown','cancel_requested'} and
           (json.loads(r[0]).get('conversation_id') or chat_sessions.default_id(p))==chat_sessions.current(p)
           for r in c.execute('SELECT body FROM chat_turns WHERE project=?',(contracts.project_id(store.workspace_id,name),))):
        raise ValueError('기존 대화 결과를 먼저 확인하세요.')
    if chat_sessions.resolve(p,chat_sessions.current(p)).get('pending_chat_selection'):
        raise ValueError('완료되지 않은 응답의 모델 예약이 남아 있습니다. 사용할 모델을 다시 선택하세요.')
    return create_preview(c,store,p,name,data['prompt'],data['maximum_micro'],total_maximum_micro=data.get('total_maximum_micro'))


def require_reconciled_budget(c, workspace, binding):
    # Unknown exposure cannot safely be bounded by its original reservation.
    # Only live-style chat is gated; the established fixture path is unchanged.
    if not binding.get('transport'):return
    ledger.require_bounded_exposure(c,workspace,budget_scope(binding))


def decide(c, store, p, name, data):
    if set(data)!={'song','preview_id','manifest_sha256','decision','rights_confirmed'} or data['decision'] not in {'approve','reject'} or type(data['rights_confirmed']) is not bool:
        raise ValueError('전송 승인 입력을 확인하세요.')
    item=get_row(c,'general_chat_previews',data['preview_id'])
    if item['binding']['project']!=contracts.project_id(store.workspace_id,name) or item['binding']['conversation']!=chat_sessions.current(p):
        raise ValueError('다른 작품 또는 대화의 확인 항목입니다.')
    if item['state']!='pending':raise ValueError('이미 처리된 승인입니다.')
    if data['manifest_sha256']!=item['manifest_sha256'] or manifest_digest(item)!=item['manifest_sha256']:raise ValueError('확인한 전송 내용이 변경됐습니다.')
    if data['decision']=='reject':
        item['state']='rejected';put(c,'general_chat_previews',item)
        if item['turn_id']:
            turn=get_row(c,'general_chat_turns',item['turn_id']);turn['status']='continuation_rejected';put(c,'general_chat_turns',turn);finish_run(p,turn,turn['status'])
        return dict(preview=public_preview(item),turn=None)
    if not data['rights_confirmed']:raise ValueError('전송할 내용의 사용 권한 확인이 필요합니다.')
    check_music_context(c,p,item)
    check_history(c,item)
    execution_turn=get_row(c,'general_chat_turns',item['turn_id']) if item['turn_id'] else None
    if item['expires']<=time.time() or binding(c,store,p,name,turn=execution_turn,legacy_default='agent_settings' not in item['binding'])!=item['binding']:raise ValueError('확인한 문맥이 변경됐습니다. 다시 확인하세요.')
    if digest(item['message_body'])!=item['message_sha256'] or digest(item['count_body'])!=item['count_sha256']:raise ValueError('전송 내용이 변경됐습니다.')
    if item['turn_id']:
        turn=get_row(c,'general_chat_turns',item['turn_id'])
        if turn['status']!='awaiting_continuation_approval' or turn['preview_id']!=item['id']:raise ValueError('이어쓰기 상태가 변경됐습니다.')
        if 'total_maximum_micro' in item and (turn.get('total_maximum_micro')!=item['total_maximum_micro'] or
            turn.get('estimated_used_micro',0)+item['reserve_micro']>item['total_maximum_micro']):
            raise ValueError('대화 전체 비용 상한이 부족합니다.')
    else:
        if any(json.loads(r[0])['status'] in {'queued','running','outcome_unknown','cancel_requested','awaiting_continuation_approval'}
               for r in c.execute('SELECT body FROM general_chat_turns WHERE project=? AND conversation=?',(item['binding']['project'],item['binding']['conversation']))):
            raise ValueError('기존 대화 결과를 먼저 확인하세요.')
        if any(json.loads(r[0])['status'] in {'queued','running','outcome_unknown','cancel_requested'} and
               (json.loads(r[0]).get('conversation_id') or chat_sessions.default_id(p))==chat_sessions.current(p)
               for r in c.execute('SELECT body FROM chat_turns WHERE project=?',(item['binding']['project'],))):
            raise ValueError('기존 대화 결과를 먼저 확인하세요.')
        run=production_tools.begin(p)
        p['production_runs'][-1].update(engine=item['mode'],provider_model=item['binding']['model'])
        settings=item['binding'].get('agent_settings') or agent_preferences.legacy_settings(p,{'binding':item['binding']})
        p['production_runs'][-1].update(agent_settings=deepcopy(settings),agent_permission_ceiling=settings['mode'])
        turn=dict(id=uuid.uuid4().hex,binding=deepcopy(item['binding']),conversation_id=item['binding']['conversation'],
                  name=name,run=run['id'],prompt=item['prompt'],status='queued',mode=item['mode'],model=item['binding']['model'],
                  round=0,preview_id=item['id'],answer=None,error=None,usage=None,usage_cost_usd='0',billing_confirmed=False,steps=[])
        if 'agent_settings' in item['binding']:turn['agent_settings']=deepcopy(settings)
        if 'total_maximum_micro' in item:turn.update(total_maximum_micro=item['total_maximum_micro'],estimated_used_micro=0)
        p.setdefault('conversation_owners',{})[turn['id']]=dict(conversation_id=turn['conversation_id'],kind='general_chat_turns')
    scope=budget_scope(item['binding'])
    require_reconciled_budget(c,store.workspace_id,item['binding'])
    reserved=ledger.command(c,store.workspace_id,scope,'reserve',
        dict(money={'amount':format(Decimal(item['reserve_micro'])/1000000,'.6f'),'currency':'USD'},budget_revision=item['budget_revision'],expires=item['expires'],job=turn['id']),item['id'])
    item.update(state='consumed',turn_id=turn['id'],reservation=reserved['reservation'],rights_confirmed=True)
    turn.update(status='queued',preview_id=item['id'],reservation=reserved['reservation'])
    put(c,'general_chat_previews',item);put(c,'general_chat_turns',turn)
    return dict(preview=public_preview(item),turn=public_turn(turn))


def recover(c):
    for row in c.execute('SELECT body FROM general_chat_turns').fetchall():
        turn=json.loads(row[0])
        if turn['status'] in {'running','cancel_requested'}:
            if not c.in_transaction:c.execute('BEGIN IMMEDIATE')
            turn.update(status='outcome_unknown',error='중단된 요청과 예산 예약을 확인하세요. 자동 재호출하지 않습니다.')
            turn.pop('pending_tool',None)
            scope=budget_scope(turn['binding'])
            for operation in ('chat-count','chat-message'):
                ledger.recover_attempt(c,ledger.attempt_identifier(turn['binding']['workspace'],scope,turn['reservation'],turn['id'],operation))
            reservation=c.execute('SELECT state FROM reservations WHERE id=?',(turn['reservation'],)).fetchone()
            if reservation and reservation[0]=='reserved':
                c.execute('SAVEPOINT general_chat_ledger_recover')
                try:ledger.command(c,turn['binding']['workspace'],scope,'uncertain',{'reservation':turn['reservation']},turn['id']+':restart:'+str(turn['round']))
                except Exception:
                    c.execute('ROLLBACK TO general_chat_ledger_recover');turn['journal_failure']='update_failed'
                finally:c.execute('RELEASE general_chat_ledger_recover')
            put(c,'general_chat_turns',turn);close_run(c,turn,turn['status'])


def cancel(c,store,p,name,data):
    if set(data)!={'song','turn'}:raise ValueError('대화 작업 식별자를 확인하세요.')
    turn=get_row(c,'general_chat_turns',data['turn'])
    if turn['binding']['project']!=contracts.project_id(store.workspace_id,name) or turn['conversation_id']!=chat_sessions.current(p):raise ValueError('다른 대화의 작업입니다.')
    if turn['status']=='queued':
        ledger.command(c,store.workspace_id,budget_scope(turn['binding']),'release',
                       {'reservation':turn['reservation']},turn['id']+':cancel:'+str(turn['round']))
        turn['status']='cancelled'
    elif turn['status']=='running':turn['status']='cancel_requested'
    elif turn['status']=='awaiting_continuation_approval':
        following=get_row(c,'general_chat_previews',turn['preview_id']);following['state']='rejected';put(c,'general_chat_previews',following)
        turn['status']='cancelled'
    if turn['status']=='cancelled':finish_run(p,turn,turn['status'])
    put(c,'general_chat_turns',turn)
    return public_turn(turn)


class Runtime:
    def __init__(self, store, transport):
        if type(transport) not in {FixtureTransport,LiveTransport}: raise ValueError('신뢰된 전송 설정이 필요합니다.')
        if isinstance(transport,LiveTransport) and not transport.test_only:
            transport.validate();transport.require_activation(store.workspace_id)
        self.store=store;self.transport=transport

    def capability(self, p=None):
        live=isinstance(self.transport,LiveTransport)
        value=dict(configured=True,available=True,mode=self.transport.mode if live else 'contract-fake',
                   external_transmission=live and not self.transport.test_only,
                   account_verified=False,billing_verified=False,
                   reason='서버 연결 설정됨 · 계정 접근·청구 미검증 · 각 회차의 전송 범위와 비용 상한을 확인하세요.' if live and not self.transport.test_only else '로컬 시험 전송: 실제 Claude 연결 아님')
        if p is not None:
            value['current_selection']=chat_sessions.selected_chat(p)
            value['supported_selection']='anthropic-haiku-5-5'
            try:selected(p)
            except ValueError as exc:value.update(available=False,reason=str(exc))
            pending=chat_sessions.resolve(p,chat_sessions.current(p)).get('pending_chat_selection')
            value['new_preview_available']=value['available'] and not bool(pending)
            if pending:value['new_preview_reason']='모델 예약이 남아 있습니다. 진행 중인 응답을 확인하고, 완료되지 않았다면 사용할 모델을 다시 선택하세요.'
        return value

    def _current(self,c,turn,preview):
        state=json.loads(c.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);p=state['projects'].get(turn['name'])
        if not p or p.get('archived'): raise ValueError('작품이 없습니다.')
        if (preview['state']!='consumed' or preview['turn_id']!=turn['id'] or turn['preview_id']!=preview['id'] or
            turn['reservation']!=preview.get('reservation') or turn['binding']!=preview['binding']):
            raise ValueError('승인과 실행 연결이 변경됐습니다.')
        p=chat_sessions.scoped(p,turn['conversation_id'])
        run=next((x for x in p.get('production_runs',[]) if x['id']==turn['run']),None)
        if run is None or agent_preferences.frozen(p,run)!=agent_preferences.frozen(p,turn):raise ValueError('에이전트 실행에 고정한 설정이 변경됐습니다.')
        check_music_context(c,p,preview)
        check_history(c,preview)
        if binding(c,self.store,p,turn['name'],turn=turn)!=preview['binding'] or preview['expires']<=time.time():raise ValueError('확인한 문맥이 변경됐습니다.')
        if manifest_digest(preview)!=preview['manifest_sha256'] or digest(preview['message_body'])!=preview['message_sha256'] or digest(preview['count_body'])!=preview['count_sha256']:raise ValueError('전송 내용이 변경됐습니다.')
        if preview['binding'].get('transport'):
            message=chat_runtime.anthropic.BoundedMessagesTransport(max_request_bytes=65536).encode_body(preview['message_body'])
            count=chat_runtime.anthropic.BoundedCountTransport(max_request_bytes=65536).encode_body(preview['count_body'])
            if (hashlib.sha256(message).hexdigest()!=preview.get('message_wire_sha256') or
                hashlib.sha256(count).hexdigest()!=preview.get('count_wire_sha256')):raise ValueError('전송 바이트가 변경됐습니다.')
        latest=get_row(c,'general_chat_turns',turn['id'])
        if latest['status']!='running':raise ValueError('작업이 취소됐습니다.')
        return p

    def process_next(self):
        with self.store.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            rows=c.execute('SELECT body FROM general_chat_turns ORDER BY rowid').fetchall()
            turn=next((json.loads(r[0]) for r in rows if json.loads(r[0])['status']=='queued'),None)
            if not turn:return False
            turn['status']='running';put(c,'general_chat_turns',turn)
        submitted=False;active_attempt=None;active_owner=None;active_operation=None;response_accounted=False
        try:
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');preview=get_row(c,'general_chat_previews',turn['preview_id']);self._current(c,turn,preview);require_reconciled_budget(c,self.store.workspace_id,turn['binding'])
                active_attempt,active_owner=ledger.claim_attempt(c,self.store.workspace_id,budget_scope(turn['binding']),turn['reservation'],turn['id'],'chat-count',preview.get('count_wire_sha256',preview['count_sha256']),preview['manifest_sha256'],enforce_bounded_exposure=bool(turn['binding'].get('transport')))
                active_operation='chat-count'
                turn['count_status']='attempted';put(c,'general_chat_turns',turn)
            tokens=self.transport.count(deepcopy(preview['count_body']))
            if type(tokens) is not int or not 0<=tokens<=MAX_INPUT:raise ValueError('입력 토큰 한도')
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=get_row(c,'general_chat_turns',turn['id'])
                if latest['preview_id']!=preview['id'] or latest['reservation']!=turn['reservation']:raise ValueError('토큰 계산 결과의 연결이 변경됐습니다.')
                ledger.finish_attempt(c,active_attempt,active_owner,'observed')
                latest['count_status']='response_received';put(c,'general_chat_turns',latest)
            active_attempt=None;active_owner=None;active_operation=None
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');self._current(c,turn,preview);require_reconciled_budget(c,self.store.workspace_id,turn['binding'])
                # Capture the bound model before the request, never from later
                # project selection. Unverifiable bindings stay unknown.
                try:
                    expected=selected_from_binding(preview['binding'])['model']
                    if preview['message_body'].get('model')!=expected:expected=None
                except (KeyError,TypeError,ValueError):expected=None
                active_attempt,active_owner=ledger.claim_attempt(c,self.store.workspace_id,budget_scope(turn['binding']),turn['reservation'],turn['id'],'chat-message',preview.get('message_wire_sha256',preview['message_sha256']),preview['manifest_sha256'],enforce_bounded_exposure=bool(turn['binding'].get('transport')))
                active_operation='chat-message'
                turn=get_row(c,'general_chat_turns',turn['id']);turn['submitted']=True;put(c,'general_chat_turns',turn)
                # Commit linearizes submission intent for this reservation and
                # message attempt. Later edits can overlap the approved send;
                # post-response checks still forbid applying stale tools.
            submitted=True
            response=self.transport.complete(deepcopy(preview['message_body']))
            # Persist bounded facts before price validation. Unsupported pricing,
            # cancellation, and rights changes cannot erase an observed response.
            observed=observe_usage(response)
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=get_row(c,'general_chat_turns',turn['id'])
                state=c.execute('SELECT state FROM provider_attempts WHERE id=?',(active_attempt,)).fetchone()
                if state and state[0]=='unknown':
                    late={'usage':observed,'model_status':late_model_status(response,expected),'billing_sources':late_billing_sources(response)}
                    request_id=chat_runtime.anthropic.verified_request_id(response.get('_request_id')) if isinstance(response,dict) else None
                    if request_id:late['request_id']=request_id
                    try:ledger.record_late_observation(c,active_attempt,active_owner,preview.get('message_wire_sha256',preview['message_sha256']),late)
                    except ledger.LedgerError:pass
                    return True
                if (latest['preview_id']!=preview['id'] or latest['reservation']!=turn['reservation'] or
                    latest['binding']!=turn['binding'] or latest['round']!=turn['round']):
                    raise ValueError('관측 결과의 요청 연결이 변경됐습니다.')
                ledger.finish_attempt(c,active_attempt,active_owner,'observed')
                step=dict(round=turn['round'],message_sha256=preview['message_sha256'],pricing_status='not_evaluated')
                request_id=chat_runtime.anthropic.verified_request_id(response.get('_request_id')) if isinstance(response,dict) else None
                if request_id:step['request_id']=request_id
                latest['observed_usage']=observed;latest['pricing_status']='not_evaluated';latest['provider_response_observed']=True
                if all(observed[k]['status']=='valid' and int(observed[k]['value'])<=SAFE_JSON_INTEGER for k in ('input_tokens','output_tokens')):
                    latest['usage']={k:int(observed[k]['value']) for k in ('input_tokens','output_tokens')}
                else:
                    # This field describes the latest round; never retain a
                    # previous round when the new observation is unusable.
                    latest['usage']=None
                latest['steps'].append(step);put(c,'general_chat_turns',latest);turn=latest
            active_attempt=None;active_owner=None;active_operation=None
            require_model=isinstance(self.transport,LiveTransport) and not self.transport.test_only
            reason=unpriced_reason(observed,require_billing_evidence=require_model,usage=response.get('usage') if isinstance(response,dict) else None)
            if reason:
                turn=mark_pricing(self.store,turn,preview,reason)
                raise ValueError('관측된 사용량의 가격을 확인하세요.')
            try:spec=selected_from_binding(preview['binding'])
            except ValueError:
                turn=mark_pricing(self.store,turn,preview,'pricing_contract_changed')
                raise
            if (require_model and 'model' not in response) or ('model' in response and (type(response['model']) is not str or response['model']!=spec['model'])):
                turn=mark_pricing(self.store,turn,preview,'pricing_contract_changed')
                raise ValueError('응답 모델의 가격 계약을 확인하세요.')
            usage=chat_models.usage(spec,response,require_model=require_model,require_billing_evidence=require_model)
            cost=chat_models.cost(spec,usage['input_tokens'],usage['output_tokens'])
            amount=int((cost*1000000).to_integral_value(rounding=ROUND_CEILING))
            if amount>9_000_000_000_000_000:
                turn=mark_pricing(self.store,turn,preview,'amount_out_of_range')
                raise ValueError('사용량 미확정')
            # The response was already received. Record observable usage even
            # when cancellation or rights changes now forbid tool execution.
            # Never let that later authorization check roll this record back.
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=get_row(c,'general_chat_turns',turn['id'])
                if (latest['preview_id']!=preview['id'] or latest['reservation']!=turn['reservation'] or
                    latest['binding']!=turn['binding'] or latest['round']!=turn['round']):
                    raise ValueError('관측 결과의 요청 연결이 변경됐습니다.')
                ledger_failed=False;c.execute('SAVEPOINT general_chat_observed_usage')
                try:
                    ledger.command(c,self.store.workspace_id,budget_scope(turn['binding']),'estimate' if turn['binding'].get('transport') else 'settle',
                        dict(reservation=turn['reservation'],money={'amount':format(Decimal(amount)/1000000,'.6f'),'currency':'USD'}),turn['id']+':settle:'+str(turn['round']))
                except Exception:
                    c.execute('ROLLBACK TO general_chat_observed_usage');ledger_failed=True
                finally:c.execute('RELEASE general_chat_observed_usage')
                # Large JSON numbers are not exactly representable in a browser.
                # Preserve normal numbers for compatibility and large ones as decimals.
                safe_usage={k:v if v<=SAFE_JSON_INTEGER else str(v) for k,v in usage.items()}
                turn=latest;turn['usage']=safe_usage;turn['usage_cost_usd']=str(Decimal(turn['usage_cost_usd'])+cost)
                if 'estimated_used_micro' in turn:turn['estimated_used_micro']+=amount
                turn['pricing_status']='ledger_update_failed' if ledger_failed else 'priced'
                turn['steps'][-1].update(usage=safe_usage,usage_cost_usd=str(cost),pricing_status=turn['pricing_status'])
                if ledger_failed:turn['journal_failure']='update_failed'
                put(c,'general_chat_turns',turn)
            if ledger_failed:raise ValueError('비용 기록을 확인하세요.')
            response_accounted=True
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');self._current(c,turn,preview)
            if usage['input_tokens']>MAX_INPUT or usage['output_tokens']>MAX_OUTPUT:raise ValueError('보고된 사용량이 상한을 초과했습니다.')
            # A continuation preview is persisted and displayed. Never copy
            # provider private reasoning blocks into it or the local store.
            if any(block.get('type') in {'thinking','redacted_thinking'} for block in response.get('content',[]) if isinstance(block,dict)):
                raise ValueError('비공개 추론을 포함한 응답은 이어서 전송하지 않습니다.')
            normalized=chat_protocols.normalize('anthropic',response,turn['run'])
            calls=normalized['calls']
            if len(calls)>1 or any(call['name'] not in ALLOWED_TOOLS for call in calls):raise ValueError('허용되지 않은 도구 요청')
            if not calls:
                answer=chat_models.text(spec,response)
                if not answer.strip():raise ValueError('답변이 없습니다.')
                with self.store.connect() as c:
                    c.execute('BEGIN IMMEDIATE');self._current(c,turn,preview)
                    turn.update(status='completed',answer=answer);put(c,'general_chat_turns',turn);close_run(c,turn,turn['status'])
                return True
            call=calls[0]
            request_id=turn['id']+':'+str(turn['round'])+':'+call['id']
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');self._current(c,turn,preview)
                turn['pending_tool']=dict(call=deepcopy(call),request_id=request_id);put(c,'general_chat_turns',turn)
            with self.store.connect() as c:
                revision,raw=c.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
                project=json.loads(raw)['projects'][turn['name']]
            session=chat_sessions.resolve(project,turn['conversation_id'])
            request=dict(action='production_tool',data=dict(song=turn['name'],run=turn['run'],call=call),
                         revision=revision,request_id=request_id,
                         conversation_id=turn['conversation_id'],conversation_revision=session['revision'],shared_version=chat_sessions.shared_fingerprint(project))
            result=self.store.mutate(request)['tool']
            turn.pop('pending_tool',None)
            if turn['round']+1>=MAX_ROUNDS:
                with self.store.connect() as c:
                    c.execute('BEGIN IMMEDIATE');self._current(c,turn,preview);turn.update(status='limit_reached');put(c,'general_chat_turns',turn);close_run(c,turn,turn['status'])
                return True
            tool_message=chat_protocols.result_message(normalized,call['id'],chat_runtime.compact_result(result),provider='anthropic',run_id=turn['run'])
            continuation=chat_models.continuation(spec,preview['message_body']['messages'],response,[tool_message])
            music_context=preview.get('music_context')
            if call['name']=='search_project_context' and result.get('status')=='succeeded' and 'music_input' in result.get('execution_targets',{}):
                music_context=dict(run_id=turn['run'],call_id=call['id'],message_index=len(continuation)-1,
                    tool_use_id=tool_message['content'][0]['tool_use_id'],sha256=digest(result['execution_targets']['music_input']))
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');p=self._current(c,turn,preview)
                if preview.get('total_maximum_micro') is not None and turn.get('estimated_used_micro',0)+preview['reserve_micro']>preview['total_maximum_micro']:
                    turn.update(status='limit_reached',error='대화 전체 비용 상한에 도달해 추가 전송을 중단했습니다.')
                    put(c,'general_chat_turns',turn);close_run(c,turn,turn['status']);return True
                turn['round']+=1
                try:following=create_preview(c,self.store,p,turn['name'],turn['prompt'],preview['maximum_micro'],turn=turn,history=continuation,total_maximum_micro=preview.get('total_maximum_micro'),music_context=music_context,history_snapshot=preview.get('history_snapshot'),body_limit=CONTINUATION_LIMIT)
                except ContextBudgetExhausted as full:
                    # Bytes the result text takes inside the body (JSON string), so the rest is exact.
                    text=tool_message['content'][0]['content']
                    left=CONTINUATION_LIMIT-(full.size-wire_bytes(text)+wire_bytes(''))
                    notice=budget_notice(call,result,full.size,left)
                    tool_message=chat_protocols.result_message(normalized,call['id'],notice,provider='anthropic',run_id=turn['run'])
                    continuation=chat_models.continuation(spec,preview['message_body']['messages'],response,[tool_message])
                    try:following=create_preview(c,self.store,p,turn['name'],turn['prompt'],preview['maximum_micro'],turn=turn,history=continuation,total_maximum_micro=preview.get('total_maximum_micro'),music_context=preview.get('music_context'),history_snapshot=preview.get('history_snapshot'),body_limit=BODY_CAP)
                    except ContextBudgetExhausted as over:
                        # Even the notice does not fit: nothing was created, reserved or sent for the
                        # next round, so the turn ends in a state that allows a new request.
                        turn['round']-=1
                        turn.update(status='limit_reached',context_budget=dict(code='CONTEXT_BUDGET_EXHAUSTED',body_bytes=over.size,limit_bytes=BODY_CAP,next_query=notice['next_query']),
                                    error='이어쓰기 전송 내용이 64KiB 전송 상한을 넘어 이번 대화 회차를 마쳤습니다(CONTEXT_BUDGET_EXHAUSTED). 이어쓰기 요청은 만들거나 전송하지 않았습니다. 새 요청으로 이어 가세요.')
                        put(c,'general_chat_turns',turn);close_run(c,turn,turn['status']);return True
                turn.update(status='awaiting_continuation_approval',preview_id=following['id']);put(c,'general_chat_turns',turn)
            return True
        except Exception as exc:
            # Only the exact adapter's credentials category proves that its
            # provider transport was not entered. Remote errors stay unknown.
            not_sent=(active_attempt is not None and active_operation in {'chat-count','chat-message'} and
                type(self.transport) is LiveTransport and not self.transport.test_only and
                type(self.transport.adapter) is chat_runtime.AnthropicChatAdapter and
                type(exc) is chat_runtime.anthropic.ProposalError and exc.failure.get('category')=='credentials')
            with self.store.connect() as c:
                c.execute('BEGIN IMMEDIATE');latest=get_row(c,'general_chat_turns',turn['id'])
                scope=budget_scope(turn['binding'])
                row=c.execute('SELECT state FROM reservations WHERE id=?',(turn['reservation'],)).fetchone()
                journal_failure=False
                if active_attempt is not None:
                    c.execute('SAVEPOINT general_chat_attempt_stop')
                    try:ledger.finish_attempt(c,active_attempt,active_owner,'not_sent' if not_sent else 'unknown')
                    except Exception:
                        c.execute('ROLLBACK TO general_chat_attempt_stop');journal_failure=True;not_sent=False
                    finally:c.execute('RELEASE general_chat_attempt_stop')
                if row and row[0]=='reserved':
                    c.execute('SAVEPOINT general_chat_ledger_stop')
                    try:
                        ledger.command(c,self.store.workspace_id,scope,'uncertain' if (submitted and not not_sent) or journal_failure or isinstance(exc,ledger.AttemptExists) else 'release',
                                       {'reservation':turn['reservation']},turn['id']+':stop:'+str(turn['round']))
                    except Exception:
                        c.execute('ROLLBACK TO general_chat_ledger_stop');journal_failure=True
                    finally:c.execute('RELEASE general_chat_ledger_stop')
                if not_sent:
                    latest['message_status']='not_sent'
                    if active_operation=='chat-count':latest['count_status']='not_sent'
                # Only this round's committed response accounting proves a
                # received cancellation. Pending tool execution or an unknown
                # provider/journal outcome must keep the existing unknown guard.
                received_cancel=(response_accounted and active_attempt is None and latest['status']=='cancel_requested' and
                    not latest.get('pending_tool') and not latest.get('journal_failure') and not journal_failure and
                    not isinstance(exc,ledger.AttemptExists) and
                    latest.get('pricing_status')=='priced' and row and row[0] in {'estimated','settled'} and
                    all(latest[key]==turn[key] for key in ('preview_id','reservation','binding','round')))
                latest.update(status='cancelled' if received_cancel else 'outcome_unknown' if (submitted and not not_sent) or journal_failure or isinstance(exc,ledger.AttemptExists) else 'cancelled' if latest['status']=='cancel_requested' else 'blocked_before_message',
                              error='요청을 취소했습니다. 이미 수신한 사용량과 비용 기록은 보존했습니다.' if received_cancel else '연결 키를 확인하세요. 대화 메시지는 전송하지 않았습니다. 설정을 수정한 뒤 새 전송 내용을 확인하세요.' if not_sent else str(exc) if isinstance(exc,MusicContextChanged) else '요청을 중단했습니다. 기존 결과와 비용 상태를 확인하세요. 자동 재시도하지 않습니다.')
                if journal_failure:latest['journal_failure']='update_failed'
                latest.pop('pending_tool',None)
                put(c,'general_chat_turns',latest);close_run(c,latest,latest['status'])
            return True


def selected_from_binding(bound):
    spec=chat_models.contract(bound['selection'])
    if spec['model']!=bound['model'] or spec['price_revision']!=bound['price_revision']:raise ValueError('모델 또는 가격이 변경됐습니다.')
    return spec
