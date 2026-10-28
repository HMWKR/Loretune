"""Explicit local synthetic Claude protocol for a separately approved UI recording.

No product source patches, real model, credentials, activation or remote sockets.
The fixture constructs typed arguments from actual search tool results; it does
not demonstrate model understanding. Existing workspaces require an explicit
post-recording/stopped-server flag. Importing this module never opens a Store.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
import argparse
import io
import json
import os
import signal
import socket
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

PROMPT = '현재 작업을 확인하고 사진 위 타이포 위치와 마지막 자막을 바꿔줘'
LAST_CAPTION = '음악의 여운을 이어서'
MAX_WIRE_BYTES = 65536
MAX_RESPONSE_BYTES = 100000
EXPECTED_MODEL = 'claude-haiku-5-5'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tree_hashes(folder):
    values = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlink data requires independent review')
        if path.is_file():
            values[str(path.relative_to(folder))] = dict(sha256=file_hash(path), bytes=path.stat().st_size)
    return values


class Receipt:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=False)
        self.lock = Lock()

    def append(self, name, value):
        with self.lock:
            with (self.folder / name).open('a') as stream:
                stream.write(json.dumps(dict(at=now(), **value), ensure_ascii=False) + '\n')

    def save(self, name, value):
        with self.lock:
            (self.folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class SyntheticClaude:
    """Four responses, constructed only from this fixture's actual tool results."""
    def __init__(self, receipt, expected_timeline=3, expected_motion=2):
        self.receipt = receipt
        self.expected_timeline = expected_timeline
        self.expected_motion = expected_motion
        self.prefix = 'ui-fixture-' + os.urandom(6).hex() + '-'
        self.seen = {}
        self.lock = Lock()

    def response(self, content, *, tool=False):
        return dict(_request_id=self.prefix + 'synthetic-request',
                    stop_reason='tool_use' if tool else 'end_turn', content=content,
                    usage=dict(input_tokens=100, output_tokens=100))

    def say(self, text):
        return self.response([dict(type='text', text='합성 시험 응답입니다. ' + text)])

    def use(self, suffix, name, args):
        declared = dict(type='tool_use', id=self.prefix + suffix, name=name, input=args)
        return self.response([declared], tool=True)

    def results(self, body):
        found = {}
        for message in body.get('messages', []):
            for block in message.get('content', []) if isinstance(message.get('content'), list) else []:
                if block.get('type') != 'tool_result':
                    continue
                identifier = block.get('tool_use_id', '')
                if not identifier.startswith(self.prefix):
                    continue
                value = block.get('content')
                if not isinstance(value, str) or block.get('is_error'):
                    raise ValueError('Fixture tool result was not a successful JSON receipt')
                found[identifier[len(self.prefix):]] = json.loads(value)
        return found

    def commands(self, result):
        if result.get('status') != 'succeeded':
            raise ValueError('Current context lookup did not succeed')
        targets = result['execution_targets']
        timeline = targets['timeline']
        if timeline['version'] != self.expected_timeline or not timeline['clips'] or not timeline['captions']:
            raise ValueError('Expected saved timeline with last caption is unavailable')
        clip = timeline['clips'][0]
        previous = clip.get('motion_overlay')
        if not previous:
            raise ValueError('Expected existing first-clip overlay is unavailable')
        source = next((x for x in targets['motion_overlay_sources']['items']
                       if x['source_shot_id'] == previous['source_shot_id']
                       and x['motion_revision'] == self.expected_motion
                       and x.get('approval_status') == 'recorded_immutable_source'), None)
        if source is None:
            raise ValueError('Exact approved immutable source revision is unavailable in this page')
        x = previous['offset_x'] + (240 if previous['offset_x'] <= 1680 else -240)
        y = previous['offset_y'] + (120 if previous['offset_y'] <= 960 else -120)
        start = .25 if previous['start'] != .25 else .5
        end = min(start + 2, clip['duration'], start + source['duration_seconds'])
        if end <= start:
            raise ValueError('First clip has no supported overlay interval')
        captions = [{key: cue[key] for key in ('start', 'end', 'text')} for cue in timeline['captions']]
        if captions[-1]['text'] == LAST_CAPTION:
            raise ValueError('Fixture would not visibly change the last caption')
        captions[-1]['text'] = LAST_CAPTION
        commands = [dict(op='set_motion_overlay', clip_index=0,
                         source_shot_id=source['source_shot_id'], motion_revision=source['motion_revision'],
                         start=start, end=end, offset_x=x, offset_y=y),
                    dict(op='set_captions', cues=captions)]
        self.receipt.append('fixture-decisions.jsonl', dict(
            decision='typed commands derived from actual context tool result; not AI understanding',
            base_timeline=timeline['version'], source_motion=source['motion_revision'],
            source_shot_id=source['source_shot_id'], commands_sha256=digest(commands),
            overlay_before=previous, overlay_after=commands[0],
            last_caption_before_sha256=sha256(timeline['captions'][-1]['text'].encode()).hexdigest(),
            last_caption_after_sha256=sha256(LAST_CAPTION.encode()).hexdigest()))
        return dict(description='명시적 합성 fixture: 사진 위 타이포 위치·표시 구간과 마지막 자막 변경',
                    timeline_version=timeline['version'], commands=commands)

    def complete(self, body):
        body_sha = digest(body)
        with self.lock:
            if body_sha in self.seen:
                return deepcopy(self.seen[body_sha])
            if len(self.seen) >= 4:
                raise ValueError('Only four distinct synthetic response requests are allowed')
            if (body.get('model') != EXPECTED_MODEL or body.get('thinking') != {'type': 'disabled'}
                    or body.get('output_config', {}).get('effort') != 'high'):
                raise ValueError('Expected selected Haiku high/disabled frozen request')
            results = self.results(body)
            if 'edit' in results:
                result = results['edit']
                applied = (result.get('status') == 'applied_draft' and result.get('agent_draft_created') is True
                           and result.get('application_actor') == 'agent-draft'
                           and result.get('timeline_version') == self.expected_timeline + 1
                           and result.get('output_approved') is False)
                value = self.say('도구 결과에서 타이포 위치·표시 구간과 마지막 자막이 새 초안에 저장된 것을 확인했습니다. 최종 출력 승인은 별도입니다. 편집 화면에서 미리보기를 확인해 주세요.'
                                 if applied else '편집의 실제 저장 완료를 확인하지 못했습니다. 현재 초안과 차단 사유를 확인해 주세요. 성공이나 출력 승인을 주장하지 않겠습니다.')
                self.receipt.append('fixture-decisions.jsonl', dict(decision='conditional final answer',
                    applied_draft_confirmed=applied, actual_tool_status=result.get('status'),
                    timeline_version=result.get('timeline_version'), output_approved=result.get('output_approved')))
            elif 'context' in results:
                try:
                    value = self.use('edit', 'propose_timeline_changes', self.commands(results['context']))
                except (ValueError, KeyError, TypeError) as error:
                    self.receipt.append('fixture-decisions.jsonl', dict(decision='safe stop before edit', error_type=type(error).__name__))
                    value = self.say('이 시연에서 요구한 저장 타임라인·승인 모션·마지막 자막 조건을 확인하지 못해 편집을 실행하지 않았습니다. 시작 조건을 확인해 주세요.')
            elif 'status' in results:
                status = results['status']
                if status.get('status') != 'succeeded' or status.get('execution_targets', {}).get('work_status', {}).get('scope') != 'current-project-current-conversation':
                    value = self.say('현재 대화의 작업 상태 조회를 확인하지 못해 편집을 진행하지 않았습니다.')
                else:
                    value = self.use('context', 'search_project_context', {'query': 'current timeline overlay and approved immutable motion sources'})
            else:
                prompt = next((message.get('content') for message in reversed(body.get('messages', []))
                               if message.get('role') == 'user' and isinstance(message.get('content'), str)), None)
                value = self.use('status', 'search_project_context', {'query': 'work-status'}) if prompt == PROMPT else self.say('지정한 합성 시연 요청만 지원하는 fixture입니다. 실제 모델 응답이나 범용 AI 동작이 아닙니다.')
            self.seen[body_sha] = deepcopy(value)
            return value


def fixture_server(fixture, receipt):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            code = 200
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if self.path not in {'/count_tokens', '/messages'} or not 0 < length <= MAX_WIRE_BYTES:
                    raise ValueError('Bounded synthetic endpoint required')
                if self.headers.get('x-api-key') != 'synthetic-key-not-real':
                    raise ValueError('Only the constant synthetic credential is accepted')
                raw = self.rfile.read(length)
                body = json.loads(raw)
                value = {'input_tokens': 100} if self.path == '/count_tokens' else fixture.complete(body)
                receipt.append('synthetic-wire.jsonl', dict(endpoint=self.path, bytes=len(raw),
                    wire_sha256=sha256(raw).hexdigest(), model=body.get('model'),
                    effort=body.get('output_config', {}).get('effort'), thinking=body.get('thinking'),
                    declared_tools=[tool.get('name') for tool in body.get('tools', [])],
                    input_tokens=100, output_tokens=100 if self.path == '/messages' else 0,
                    usage_origin='synthetic fixture; not counted real tokens or billing', actual_external_calls=0))
            except Exception as error:
                code = 400
                receipt.append('synthetic-wire.jsonl', dict(endpoint=self.path, http_status=code, error_type=type(error).__name__))
                value = {'error': 'synthetic fixture contract rejected'}
            output = json.dumps(value, ensure_ascii=False).encode()
            if len(output) > MAX_RESPONSE_BYTES:
                code = 400
                output = b'{"error":"fixture response limit"}'
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(output)))
            self.end_headers()
            self.wfile.write(output)
    return ThreadingHTTPServer(('127.0.0.1', 0), Handler)


def inspect_existing(data, song, expected_timeline):
    database = data / 'studio.sqlite3'
    if not database.is_file():
        raise ValueError('An existing completed demonstration workspace is required')
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        revision, raw = db.execute('SELECT revision,body FROM state WHERE id=1').fetchone()
        state = json.loads(raw)
        project = state['projects'].get(song)
        if project is None or project.get('timeline_head') != expected_timeline:
            raise ValueError('Expected project/timeline must match before server startup')
        for table, active in [('jobs', {'queued', 'running', 'cancel_requested'}),
                              ('general_chat_turns', {'queued', 'running', 'cancel_requested', 'outcome_unknown', 'awaiting_continuation_approval'}),
                              ('chat_turns', {'queued', 'running', 'cancel_requested', 'outcome_unknown'})]:
            if any(json.loads(row[0]).get('status') in active for row in db.execute('SELECT body FROM ' + table)):
                raise ValueError('Unfinished workspace jobs/turns require review before this harness')
        workspace = db.execute("SELECT value FROM metadata WHERE key='workspace_id'").fetchone()[0]
        return dict(workspace_id=workspace, revision=revision, timeline_head=project['timeline_head'],
                    project_sha256=digest(project), timeline_versions_sha256=digest(project['timeline_versions']),
                    timeline_versions_count=len(project['timeline_versions']),
                    original_shots_sha256=digest(project['shots']), original_audio_versions_sha256=digest(project.get('audio_versions', [])),
                    outputs=[dict(id=json.loads(row[0])['id'], sha256=json.loads(row[0]).get('sha256'))
                             for row in db.execute('SELECT body FROM jobs') if json.loads(row[0]).get('status') == 'completed'])


def sanitized_environment():
    # Read only these explicitly named noncredential values; never load an env file.
    safe = {key: os.environ[key] for key in ('PATH', 'HOME', 'TMPDIR', 'LANG', 'LC_ALL') if key in os.environ}
    os.environ.clear()
    os.environ.update(safe)
    return sorted(safe)


def run(args):
    if not args.authorize_existing_data_after_main_stop or not args.seed_rehearsal_budget:
        raise ValueError('Both explicit stopped-workspace and synthetic-budget setup flags are required')
    data = Path(args.data).resolve()
    evidence = Path(args.evidence).resolve()
    if evidence == data or evidence.is_relative_to(data):
        raise ValueError('Evidence must stay outside the preserved workspace')
    # This check runs only on an explicit future invocation; preparation does not touch the main server.
    with socket.socket() as check:
        check.settimeout(.25)
        if check.connect_ex(('127.0.0.1', args.port)) == 0:
            raise ValueError('The original server must be stopped before reopening this workspace')
    receipt = Receipt(evidence)
    before = tree_hashes(data)
    initial = inspect_existing(data, args.song, args.expected_timeline)
    if initial['workspace_id'] != args.expected_workspace_id:
        raise ValueError('The explicitly expected workspace ID does not match this data')
    receipt.save('data-before.json', dict(recorded_at=now(), **initial, files=before))
    source_files = ['app.py', 'chat_general.py', 'chat_runtime.py', 'chat_models.py', 'agent_preferences.py',
                    'production_tools.py', 'production_context.py', 'local_creation_tools.py', 'editing.py',
                    'renderer.py', 'motion_renderer.py', 'motion_scene.py', 'index.html', 'general-chat-ui.js', 'chat-sidebar.js']
    source_before = {name: file_hash(ROOT / name) for name in source_files}
    receipt.save('source-current.json', source_before)
    allowed_env = sanitized_environment()
    external_attempts = []
    def deny_external(event, values):
        address = values[1] if event == 'socket.connect' else values[0] if event == 'socket.getaddrinfo' else None
        host = address[0] if isinstance(address, tuple) else address
        if event in {'socket.connect', 'socket.getaddrinfo'} and host not in {'127.0.0.1', '::1', None}:
            external_attempts.append(dict(event=event, denied=True))
            receipt.append('network-denials.jsonl', dict(event=event, denied=True))
            raise PermissionError('This synthetic recording forbids external network calls')
    sys.addaudithook(deny_external)
    import app
    import chat_general
    import chat_runtime
    import contracts
    import ledger
    fixture = SyntheticClaude(receipt, args.expected_timeline, args.expected_motion)
    provider = fixture_server(fixture, receipt)
    Thread(target=provider.serve_forever, daemon=True).start()
    fake_supplier_calls = []
    def synthetic_credential(name):
        if name != 'Anthropic_KEY':
            raise ValueError('Unexpected synthetic credential label')
        fake_supplier_calls.append('constant synthetic credential returned; no lookup')
        return 'synthetic-key-not-real'
    adapter = chat_runtime.AnthropicChatAdapter(synthetic_credential, enabled=True,
        count_transport=chat_general.LoopbackTransport(provider.server_port),
        message_transport=chat_general.LoopbackTransport(provider.server_port))
    transport = chat_general.LiveTransport(adapter, 'ui-synthetic-local-only', 1, test_only=True)
    http = app.server(data, args.port, general_chat_live=transport)
    pid = contracts.project_id(http.store.workspace_id, args.song)
    scope = 'rehearsal-live:project:' + pid
    with http.store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        old_budget = ledger.budget(db, http.store.workspace_id, scope)
        new_budget = ledger.patch_budget(db, http.store.workspace_id, scope,
            dict(limit={'amount': '0.04', 'currency': 'USD'}, maxConcurrentJobs=4, allowAutomaticRetries=False),
            old_budget['revision'] if old_budget else 0)
    receipt.save('fixture-budget.json', dict(scope=scope, before=old_budget, after=new_budget,
        authorization='Parent explicitly authorized this one USD0.04 synthetic scope at future harness invocation only',
        distinction='Existing budget UI supports project scope, not rehearsal-live. This is disclosed fixture setup; not proof of test-budget UI or real spend consent.'))
    original = http.RequestHandlerClass
    state_signature = [None]
    class Handler(original):
        def log_message(self, *_):
            pass

        def do_POST(self):
            if self.path != '/api/action':
                return super().do_POST()
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length < 24 * 1024 * 1024:
                return super().do_POST()
            raw = self.rfile.read(length)
            value = json.loads(raw)
            self.receipt_meta = dict(action=value.get('action'), request_id=value.get('request_id'),
                                     revision=value.get('revision'), conversation_id=value.get('conversation_id'),
                                     request_sha256=sha256(raw).hexdigest(), data_fields=sorted(value.get('data', {})))
            previous = self.rfile
            self.rfile = io.BytesIO(raw)
            try:
                return super().do_POST()
            finally:
                self.rfile = previous

        def send(self, status, value, *arguments, **keywords):
            if self.path == '/api/action' and getattr(self, 'receipt_meta', None):
                meta = dict(self.receipt_meta, http_status=status)
                if isinstance(value, dict):
                    meta['response_fields'] = sorted(value)
                    preview = value.get('general_chat_preview')
                    if preview:
                        meta['preview'] = {key: preview.get(key) for key in ('id', 'manifest_sha256', 'message_wire_sha256', 'count_wire_sha256', 'mode', 'maximum_micro', 'total_maximum_micro')}
                receipt.append('ui-actions.jsonl', meta)
            if self.path.startswith('/api/state') and status == 200 and isinstance(value, dict):
                project = value.get('projects', {}).get(args.song, {})
                prefs = project.get('agent_preferences', {})
                summary = dict(timeline_head=project.get('timeline_head'),
                               desired_settings=prefs.get('current'), active_response=prefs.get('active_response'),
                               turns=[{key: turn.get(key) for key in ('id', 'status', 'mode', 'billing_confirmed')}
                                      for turn in project.get('general_chat_turns', [])[-2:]])
                signature = digest(summary)
                if signature != state_signature[0]:
                    state_signature[0] = signature
                    receipt.append('ui-observed-state.jsonl', summary)
            return super().send(status, value, *arguments, **keywords)
    http.RequestHandlerClass = Handler
    stop, workers = app.start_workers(http.store)
    assert len(workers) == 4 and sum('general-chat' in thread.name for thread in workers) == 2
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    Thread(target=http.serve_forever, daemon=True).start()
    start = dict(recorded_at=now(), pid=os.getpid(), url=f'http://127.0.0.1:{http.server_port}/',
                 data=str(data), workspace_id=http.store.workspace_id, project_id=pid,
                 mode='contract-live-test', real_provider_calls=0, real_credentials_read=0, billing_calls=0,
                 env_whitelist=allowed_env, env_files_loaded=False, activation_loaded=False,
                 fixture_provider=f'http://127.0.0.1:{provider.server_port}', workers=[thread.name for thread in workers],
                 expected_timeline=args.expected_timeline, expected_motion=args.expected_motion,
                 expected_new_draft=args.expected_timeline + 1, prompt=PROMPT,
                 fixture_interpretation='Deterministic response builder reads actual tool receipts; not real Claude or semantic model validation',
                 next_steps='UI select Haiku high/review; save FullAccess; submit exact prompt with per-round0.01/total0.04; approve each exact manifest; inspect draft; separately approve final output and render',
                 fixture_budget='fixture-budget.json', source_freeze='source-current.json', data_before='data-before.json')
    receipt.save('start.json', start)
    print(json.dumps(start, ensure_ascii=False), flush=True)
    try:
        stop.wait()
    finally:
        stop.set()
        http.shutdown()
        http.server_close()
        for worker in workers:
            worker.join(5)
        provider.shutdown()
        provider.server_close()
        after = tree_hashes(data)
        with sqlite3.connect((data / 'studio.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
            project = json.loads(db.execute('SELECT body FROM state WHERE id=1').fetchone()[0])['projects'][args.song]
        structured = dict(original_timeline_versions_preserved=digest(project['timeline_versions'][:initial['timeline_versions_count']]) == initial['timeline_versions_sha256'],
                          original_shots_and_motion_sources_preserved=digest(project['shots']) == initial['original_shots_sha256'],
                          original_audio_versions_preserved=digest(project.get('audio_versions', [])) == initial['original_audio_versions_sha256'],
                          final_timeline_head=project.get('timeline_head'))
        preserved = {name: data_record == after.get(name) for name, data_record in before.items()
                     if name.startswith(('assets/', 'exports/'))}
        receipt.save('data-after.json', dict(recorded_at=now(), files=after,
                     original_assets_and_outputs_preserved=preserved, structured_preservation=structured))
        receipt.save('stop.json', dict(recorded_at=now(), external_attempts=external_attempts,
                     real_credentials_read=0, constant_synthetic_credential_returns=len(fake_supplier_calls),
                     real_provider_calls=0, billing_calls=0, distinct_synthetic_messages=len(fixture.seen),
                     worker_threads_still_alive=[thread.name for thread in workers if thread.is_alive()],
                     source_changed_during_run=[name for name, expected in source_before.items() if file_hash(ROOT / name) != expected]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    start = sub.add_parser('serve', help='Future root-authorized post-main invocation only')
    start.add_argument('--data', required=True)
    start.add_argument('--evidence', required=True)
    start.add_argument('--song', required=True)
    start.add_argument('--expected-workspace-id', required=True)
    start.add_argument('--port', type=int, required=True)
    start.add_argument('--expected-timeline', type=int, default=3)
    start.add_argument('--expected-motion', type=int, default=2)
    start.add_argument('--authorize-existing-data-after-main-stop', action='store_true')
    start.add_argument('--seed-rehearsal-budget', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('A fixed loopback app port is required')
    run(args)


if __name__ == '__main__':
    main()
