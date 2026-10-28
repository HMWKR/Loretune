"""D1 r4 citation check for docs/design/FRAME-OBSERVATION-DESIGN-ko.md (read-only).

Run from the project root:
  PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B \
    .omo/evidence/agent-tools-02-20261028/tasks/D1-r4/check_citations.py [doc-path]

Part 1 (range): every explicit `name.ext:N[-M][,K]` anchor in the doc must name an
existing file whose length covers every cited line. Source files resolve to the
before/ snapshot, as the doc header states; a leading './' means the current project file.
Part 2 (content): hand-listed anchors, including bare `:N` anchors whose file is
given by context, must contain the expected substring on the cited line.
r3: every expected substring is non-empty (asserted); './' entries check current files.
r4: no eval(); the legacy default list is parsed with ast.literal_eval (literal only).
An optional doc-path argument checks a copy (used for the negative run). Exit 1 on any failure. Writes nothing.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
EV = ROOT / '.omo/evidence/agent-tools-02-20261028'
BEFORE = EV / 'before'
DOC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'docs/design/FRAME-OBSERVATION-DESIGN-ko.md'
MD = {
    'PLAN-ko.md': EV / 'PLAN-ko.md',
    'CHAT-SESSION-PLAN.md': ROOT / 'docs/design/CHAT-SESSION-PLAN.md',
    '07_Chat_Directed_Multimodel_Production_Spec.md': ROOT / '07_Chat_Directed_Multimodel_Production_Spec.md',
}


def resolve(name):
    if name.startswith('./'):
        return ROOT / name[2:]
    base = name.rsplit('/', 1)[-1]
    if base in MD:
        return MD[base]
    return BEFORE / base


def lines(path):
    return path.read_text(encoding='utf-8').splitlines()


fails = 0
anchors = 0
doc = DOC.read_text(encoding='utf-8')
for span in re.findall(r'`([^`]*)`', doc):
    m = re.fullmatch(r'([\w./-]+\.(?:py|js|md)):([0-9,\-~]+)', span)
    if not m:
        continue
    path = resolve(m.group(1))
    if not path.exists():
        print('MISSING', span); fails += 1; continue
    n = len(lines(path))
    for part in m.group(2).rstrip('~').split(','):
        lo, _, hi = part.partition('-')
        for value in (lo, hi or lo):
            anchors += 1
            if not 1 <= int(value) <= n:
                print('OUT_OF_RANGE', span, 'len', n); fails += 1

CHECKS = [
    # (file, line, expected substring)
    ('app.py', 412, 'def motion_preview'), ('app.py', 416, "p.get('archived')"),
    ('app.py', 419, 'read_bytes()'), ('app.py', 421, 'def timeline_preview'),
    ('app.py', 423, 'timeline_preview_lock.acquire(blocking=False)'), ('app.py', 427, 'chat_sessions.scoped'),
    ('app.py', 432, "timeline['id']!=revision"), ('app.py', 438, 'check_rights'),
    ('app.py', 444, "current(latest)['id']!=revision"), ('app.py', 446, 'signature('),
    ('app.py', 447, 'check_rights'), ('app.py', 253, 'asset_rights'),
    ('app.py', 1351, '/api/motion-frame?'), ('app.py', 1358, "'image/png'"),
    ('app.py', 1359, '/api/timeline-frame?'), ('app.py', 1368, "return self.send(200,value,'image/png')"),
    ('app.py', 1021, 'def check_rights'), ('app.py', 1023, 'SELECT blocked FROM asset_rights'),
    ('renderer.py', 106, 'PROFILES'), ('renderer.py', 111, 'timeout'), ('renderer.py', 112, '16*1024*1024'),
    ('editing.py', 10, "'preview':(640,360)"),
    ('motion_renderer.py', 28, 'def frame'), ('motion_renderer.py', 31, 'len(raw)>100000'),
    ('motion_renderer.py', 33, 'timeout=10'),
    ('chat_protocols.py', 49, 'json.dumps(result'), ('chat_protocols.py', 50, '100_000'),
    ('chat_protocols.py', 51, "type='tool_result'"), ('chat_protocols.py', 55, 'def handoff'),
    ('chat_protocols.py', 57, "text=m['text']"), ('chat_protocols.py', 70, 'instructions='),
    ('chat_models.py', 8, "input_rate='.1',output_rate='.5'"), ('chat_models.py', 99, 'history+['),
    ('chat_models.py', 102, 'def cost'), ('chat_models.py', 111, '/1000000'),
    ('anthropic_ontology.py', 175, '1 <= max_request_bytes <= 65536'),
    ('anthropic_ontology.py', 176, 'request byte limit'),
    ('chat_general.py', 28, 'MAX_INPUT'), ('chat_general.py', 30, 'MAX_ROUNDS'),
    ('chat_general.py', 181, "result['provider'] != 'anthropic'"),
    ('chat_general.py', 229, 'INSERT INTO'), ('chat_general.py', 230, 'json.dumps(item'),
    ('chat_general.py', 233, 'def public_preview'), ('chat_general.py', 234, "'message_body','count_body'"),
    ('chat_general.py', 242, 'def manifest_digest'), ('chat_general.py', 243, "'message_body','count_body'"),
    ('chat_general.py', 244, 'data_scope'), ('chat_general.py', 290, 'def check_music_context'),
    ('chat_general.py', 299, "{'run_id','call_id','message_index','tool_use_id','sha256'}"),
    ('chat_general.py', 308, "item['message_body']['messages'][index]"),
    ('chat_general.py', 310, "b.get('tool_use_id')==marker['tool_use_id']"),
    ('chat_general.py', 312, "json.loads(blocks[0]['content'])"),
    ('chat_general.py', 314, 'except (KeyError,TypeError,ValueError'),
    ('chat_general.py', 315, '음원 조회 결과와 전송 내용의 연결을 확인하세요.'),
    ('chat_general.py', 316, 'music_input'), ('chat_general.py', 317, "marker['sha256']"),
    ('chat_general.py', 318, 'MusicContextChanged'),
    ('chat_general.py', 433, 'total_maximum_micro<=400000'),
    ('chat_general.py', 435, "count={k:deepcopy(v) for k,v in body.items() if k!='max_tokens'}"),
    ('chat_general.py', 436, 'chat_models.cost(spec,MAX_INPUT,MAX_OUTPUT)'),
    ('chat_general.py', 443, 'message_body=body,count_body=count'), ('chat_general.py', 444, 'count_sha256=digest(count)'),
    ('chat_general.py', 446, '자산 파일은 전송하지 않음'), ('chat_general.py', 454, 'music_context is not None'),
    ('chat_general.py', 456, 'check_music_context'), ('chat_general.py', 460, 'BoundedCountTransport(max_request_bytes=65536)'),
    ('chat_general.py', 461, 'BoundedMessagesTransport(max_request_bytes=65536)'),
    ('chat_general.py', 618, 'check_music_context'), ('chat_general.py', 619, 'check_history'),
    ('chat_general.py', 620, "preview['expires']"), ('chat_general.py', 621, "digest(preview['count_body'])"),
    ('chat_general.py', 623, 'BoundedMessagesTransport(max_request_bytes=65536)'),
    ('chat_general.py', 624, 'BoundedCountTransport(max_request_bytes=65536)'),
    ('chat_general.py', 626, '전송 바이트가 변경됐습니다'), ('chat_general.py', 642, "'chat-count'"),
    ('chat_general.py', 645, "self.transport.count(deepcopy(preview['count_body']))"),
    ('chat_general.py', 646, 'tokens<=MAX_INPUT'), ('chat_general.py', 744, 'MAX_INPUT'),
    ('chat_general.py', 751, 'len(calls)>1'), ('chat_general.py', 777, 'result_message'),
    ('chat_general.py', 778, 'chat_models.continuation'), ('chat_general.py', 779, "preview.get('music_context')"),
    ('chat_general.py', 782, "sha256=digest(result['execution_targets']['music_input'])"),
    ('chat_general.py', 789, 'history=continuation'), ('chat_general.py', 790, 'awaiting_continuation_approval'),
    ('chat_runtime.py', 175, 'list(production_tools.TOOLS)'), ('chat_runtime.py', 331, 'result_message'),
    ('chat_runtime.py', 332, 'chat_models.continuation'),
    ('general-chat-ui.js', 55, 'JSON.stringify(v.count_body'), ('general-chat-ui.js', 55, '자료 파일 자체는 전달하지 않습니다'),
    ('general-chat-ui.js', 55, 'v.data_scope'),
    ('production_context.py', 88, 'unconfirmed'), ('music.py', 16, 'def waveform'), ('music.py', 17, 'Bounded actual PCM envelope'),
    ('motion_scene.py', 9, "enum=['text','rect','circle']"), ('motion_scene.py', 31, "{'text','rect','circle'}"),
    ('production_tools.py', 10, 'TOOLS={'),
    ('CHAT-SESSION-PLAN.md', 67, '감사 당시 일반 대화 선택은 Claude만 허용'),
    ('CHAT-SESSION-PLAN.md', 29, '사용자의1차 녹화 검토'), ('CHAT-SESSION-PLAN.md', 31, '실제4096/4096토큰'),
    ('07_Chat_Directed_Multimodel_Production_Spec.md', 134, '일부 프레임만 검토했다면'),
    ('07_Chat_Directed_Multimodel_Production_Spec.md', 322, '7 4'),
    ('07_Chat_Directed_Multimodel_Production_Spec.md', 324, '외부 전송 허용 범위'),
    ('07_Chat_Directed_Multimodel_Production_Spec.md', 556, 'MS-FR-27'),
    ('07_Chat_Directed_Multimodel_Production_Spec.md', 610, 'AT38'),
    ('PLAN-ko.md', 54, 'coverage'), ('PLAN-ko.md', 81, '영상 프레임 관찰'), ('PLAN-ko.md', 115, 'S13'),
    ('PLAN-ko.md', 142, 'D9'), ('PLAN-ko.md', 143, '등록은 별도 승인'),
    # r3 additions: frame-byte path (§4-4), D20 (§4-1, §7), duplicates/cumulative (§4-3), legacy drift.
    ('PLAN-ko.md', 164, '줄 번호 일부 어긋남'), ('PLAN-ko.md', 196, 'D20 = "상한만 올리기"'), ('PLAN-ko.md', 196, '16384'),
    ('app.py', 384, 'chat_general.public_preview'), ('app.py', 384, "x['state']=='pending'"),
    ('app.py', 425, 'def project'), ('app.py', 426, 'self.connect()'),
    ('app.py', 439, "TemporaryDirectory(dir=self.root,prefix='timeline-preview-')"), ('app.py', 442, 'value=output.read_bytes()'),
    ('app.py', 496, "BEGIN IMMEDIATE"), ('app.py', 497, 'SELECT digest,result FROM requests'),
    ('app.py', 806, "a == 'production_tool'"), ('app.py', 813, 'production_tools.execute('),
    ('app.py', 1001, 'UPDATE state SET revision=?,body=?'), ('app.py', 1003, 'INSERT INTO requests VALUES'),
    ('production_tools.py', 64, "prior=next((x for x in run['calls']"), ('production_tools.py', 67, "return deepcopy(prior['result'])"),
    ('production_tools.py', 139, "run['calls'].append("),
    ('chat_general.py', 29, 'MAX_OUTPUT = 4096'), ('chat_general.py', 437, 'worst>maximum_micro'),
    ('chat_general.py', 445, 'reserve_micro=worst'), ('chat_general.py', 469, 'return public_preview(item)'),
    ('chat_general.py', 529, 'production_tools.begin(p)'), ('chat_general.py', 546, 'preview=public_preview(item)'),
    ('chat_general.py', 549, 'def recover'), ('chat_general.py', 554, 'outcome_unknown'), ('chat_general.py', 554, '자동 재호출하지 않습니다'),
    ('chat_general.py', 555, "turn.pop('pending_tool',None)"), ('chat_general.py', 322, "'steps'"),
    ('chat_general.py', 763, "turn['pending_tool']=dict(call=deepcopy(call)"), ('chat_general.py', 770, "conversation_id=turn['conversation_id']"),
    ('chat_general.py', 771, "result=self.store.mutate(request)['tool']"), ('chat_general.py', 773, "turn['round']+1>=MAX_ROUNDS"),
    ('chat_general.py', 783, 'with self.store.connect() as c:'), ('chat_general.py', 784, 'BEGIN IMMEDIATE'),
    ('chat_runtime.py', 330, "step['tool_calls'].append"), ('chat_runtime.py', 333, "self.journal.update(identifier,'completed',step)"),
    ('backup.py', 51, "source.rglob('*')"), ('backup.py', 63, 'shutil.copyfile(path, target)'),
    ('ledger.py', 135, 'INSERT INTO provider_attempts'),
    # current-file anchors ('./' in the doc): A1 r2 moved chat_runtime.py down by 3 lines.
    ('./chat_runtime.py', 17, 'LEGACY_DEFAULT_TOOLS=['), ('./chat_runtime.py', 178, 'list(LEGACY_DEFAULT_TOOLS)'),
    ('./chat_runtime.py', 334, 'chat_protocols.result_message'), ('./chat_runtime.py', 335, 'chat_models.continuation'),
    ('./chat_general.py', 29, 'MAX_INPUT = 16384'),
    # r4 additions: final-round cutoff, mid-request permission, delivery record, SQLite connect.
    ('chat_general.py', 774, 'with self.store.connect() as c:'), ('chat_general.py', 775, "status='limit_reached'"),
    ('chat_general.py', 776, 'return True'), ('chat_general.py', 764, 'with self.store.connect() as c:'),
    ('chat_general.py', 765, 'SELECT revision,body FROM state'), ('chat_general.py', 766, "json.loads(raw)['projects']"),
    ('chat_general.py', 784, 'p=self._current(c,turn,preview)'), ('chat_general.py', 424, 'agent_preferences.tools_for('),
    ('chat_general.py', 378, 'def close_run'), ('chat_general.py', 383, 'UPDATE state SET revision=?,body=?'),
    ('agent_preferences.py', 14, 'READ_TOOLS={'), ('agent_preferences.py', 61, 'def effective_mode'),
    ('agent_preferences.py', 66, 'MODES[current'), ('agent_preferences.py', 70, 'def tools_for'),
    ('agent_preferences.py', 72, "mode=='read_only'"), ('agent_preferences.py', 75, 'def authorize'),
    ('agent_preferences.py', 79, 'AGENT_READ_ONLY'), ('agent_preferences.py', 93, "project.get('production_runs'"),
    ('agent_preferences.py', 99, "run['agent_permission_ceiling']=mode"),
    ('production_tools.py', 75, 'agent_preferences.authorize(project,run'),
    ('app.py', 277, 'def connect'), ('app.py', 278, 'sqlite3.connect(self.db, timeout=30)'),
    ('app.py', 417, "prefix='motion-preview-'"),
]
assert all(expected for _, _, expected in CHECKS), 'empty expected substring is a vacuous check'
assert 'request_media_generation' not in lines(resolve('./chat_runtime.py'))[16], 'legacy default must exclude execution tool'
assert len(ast.literal_eval(lines(resolve('./chat_runtime.py'))[16].split('=', 1)[1].strip())) == 13
for name, n, expected in CHECKS:
    text = lines(resolve(name))
    ok = 1 <= n <= len(text) and expected in text[n - 1]
    if not ok:
        fails += 1
        print('FAIL', name, n, repr(expected), '|', text[n - 1][:120] if 1 <= n <= len(text) else '<out of range>')

# The doc must not keep the two corrected claims of r1.
for stale in ('바이트는 승인된 미리보기의 `message_body`에만 존재함', '`app.py:1359-1367`',
              '이번 일반 대화는 Claude만 허용한다(`CHAT-SESSION-PLAN.md:67`)', '4장은 물론 1장도 들어가지 않을 수 있다',
              # r2 statements corrected in r3
              '1456×816', 'PLAN-ko.md:161', '네트워크 금지라 원문을 다시 열지 않음', '`chat_runtime.py:175` 기본 `TOOLS`',
              '이 문제는 프레임과 별개로 먼저 풀어야 한다', '약 48,000바이트', '약 36,000바이트',
              '기본 도구는 `production_tools.TOOLS` 전체다(`chat_runtime.py:175`)', 'Haiku 5.5의 등급은 미확인',
              # r3 statements corrected in r4
              "kind:'timeline'|'motion'", 'timeline_revision|proposal_id+scene_sha256',
              '렌더가 나중에 실패한 요청도 누적에 넣는다', '이전 라운드에서 이미 요청한 같은',
              '어떤 작품, 편집, 모션의 프레임을 보낼지'):
    if stale in doc:
        fails += 1; print('STALE', stale)

current = sum(1 for name, _, _ in CHECKS if name.startswith('./'))
print('explicit anchors', anchors, 'content checks', len(CHECKS), '(before/md', len(CHECKS) - current, '+ current', str(current) + ')', 'empty-expected 0', 'fail', fails)
sys.exit(1 if fails else 0)
