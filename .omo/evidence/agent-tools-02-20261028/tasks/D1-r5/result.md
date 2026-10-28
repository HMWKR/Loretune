# D1-r5 결과 — 프레임 관찰 설계 문서 5차 수정

- 대상: `docs/design/FRAME-OBSERVATION-DESIGN-ko.md` (58,604 → 67,344바이트, sha256 `a7a95e04bf6d77d13d91e32f654e419251a2ed0dbebf87314f2d99cdeddab933`)
- 시작 사본: `tasks/D1-r5/start/FRAME-OBSERVATION-DESIGN-ko.md.txt`(sha256 `591c7491…230ad5`, r4 결과와 같음), `tasks/D1-r5/start/check_citations.py.txt`(r4 스크립트)
- 변경 diff: `tasks/D1-r5/changes.diff` (문서 + 인용 검사 스크립트, 시작 사본 대비)
- 쓰기 범위: 설계 문서와 `tasks/D1-r5/`만 고쳤다. 문서는 등록하지 않았고, 코드·테스트 파일은 건드리지 않았다. 파일을 지우지 않았다.
- 줄 번호: 소스 인용은 문서 규약대로 `before/` 사본 기준이고, 문서 줄은 현재 파일 기준이다.

## critic 지적별 처리 (r4 verdict minor 5건, 모두 고침)

| # | 지적 | 처리 | 문서 위치 | 증거 |
|---|---|---|---|---|
| 1 | §3 :42 "위 두 함수를 그대로 호출" 문장이 v1 모션 거절과 모순 | **고침**: "v1의 도구는 `timeline_preview` 하나만 그대로 호출하고, `motion_preview`는 보완과 §9 A2 승인 뒤에만 재사용"으로 바꿈 | :43 | 인용 검사 STALE에 옛 문장 추가 → 문서에 없음(fail 0). 음성 실행에서 되살리면 STALE 검출 |
| 2 | 대화 전체 비용 검사(`chat_general.py:785-787`)가 렌더 뒤에 있어 렌더 낭비 | **고침**: 2단계 맨 앞(:773 판정 통과 뒤, 권한 재확인과 렌더 전)에 같은 식·같은 값(메모리의 `turn`, `preview`)으로 계산하고, 걸리면 렌더 없이 `:785-787`과 같은 처리(`limit_reached`, 같은 문구, `close_run`)로 끝냄. `:785-787`은 3단계에 최종 판정으로 남김. §10에 "대화 비용 상한이면 렌더 0회" 테스트(경계값 포함) 추가 | :89, :217 | 인용 검사 신규 단언 `chat_general.py:785`(식), `:786`(`limit_reached`·문구), `:787`(`close_run`·`return True`) 통과 |
| 3 | 2단계 재인가가 범위 없는 원본 프로젝트로 판정 → 기본 대화의 모드를 읽음 | **고침**: 2단계는 `chat_sessions.scoped(project, turn['conversation_id'])`로 범위를 정한 프로젝트와 그 안의 `turn['run']`으로 판정(`_current`의 `:615-616`과 같은 방식). 원본에 `_conversation_id`가 없는 이유(`chat_sessions.py:180`)와 `current`(`:34`) → `profile`(`agent_preferences.py:25-28`) 경로를 적음. §10에 두 대화 테스트(기본 read_only + 턴 대화 review/full_access → 렌더, 반대 경우 → 렌더 0회·`AGENT_READ_ONLY`) 추가 | :94, :218 | 인용 검사 신규 단언 `chat_sessions.py:34,180,185-187`, `agent_preferences.py:25,28`, `chat_general.py:615,616` 통과 |
| 4 | 3단계 뒤 권한 축소에 대한 대응 없음 | **고침(재인가 쪽을 택함)**: 본문(`message_body`)에 image 블록이 든 tool_result가 있는 미리보기에 한해 (a) 승인 때: `decide`에서 권리 확인(`:509`) 뒤·예약(`:541`) 전에 `authorize`, 실패 시 `AGENT_READ_ONLY`, 예약 0, 미리보기 `pending` 유지, reject는 계속 가능(`:504-508`이 앞에 있음). (b) 전송 직전: `:641` 트랜잭션에서 `_current` 뒤·`claim_attempt` 앞. `_current` 안에는 넣지 않음(응답 수신 뒤 `:756/:762/:775/:784`에서도 불려 마무리가 깨지므로). 실패 시 기존 예외 경로가 예약 `release`, 턴 `blocked_before_message`(`:810-814`, `:829`), 전송 0회. `decide`의 `p`가 이미 대화 범위인 근거 `app.py:523`(`enter`) → `app.py:790`. §9 A2에 이 재인가 확인 추가. §10에 (a)(b)와 프레임 없는 미리보기 회귀 (c) 테스트 추가 | :95-98, :193, :219 | 인용 검사 신규 단언 `chat_general.py:206,207,210,496,504,508,509,541,546,609,617,629,641,642,756,762,775,810,813,814,829`, `app.py:523,790` 통과 |
| 5 | `secure_delete` 기본값이 SQLite 빌드에 따라 다른데 "꺼져 있다"고 단정, 연결별 설정·삭제 뒤 백업·"65회" 오해 | **고침**: §4-4 표 SQLite 행을 실측(0/1/2)으로 다시 씀. 연결마다 새로 열리므로(`app.py:277-278`) 삭제·재작성하는 **그 연결**에서 `PRAGMA secure_delete=ON`을 켜거나 `VACUUM`을 요구(§9 A5). 백업 행과 A5에 "①·② 없이 삭제한 뒤 만든 백업에도 남음" 추가. §11에서 "65회"를 "한 벌 안의 주기 표식 적중 횟수"로 정정. §10 삭제 잔존 테스트에 연결별 PRAGMA 단언, 기본값 0인 빌드에서 실행, 앞선 연결에서만 켠 음성 대조, 삭제 뒤 백업 0벌 단언 추가 | :118, :119, :196, :216, :239 | **실측** `tasks/D1-r5/sqlite-probe/probe.log` (아래). 인용 검사 STALE에 r4 옛 문구 추가 |

## 실행한 명령과 출력 끝부분

1. 인용 검사(정상), `/Users/leesungmin/Desktop/Loretune`에서:
   ```
   PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/D1-r5/check_citations.py
   explicit anchors 324 content checks 215 (before/md 210 + current 5) empty-expected 0 fail 0
   exit 0
   ```
   r4 대비 앵커 302 → 324, 내용 단언 178 → 215(신규 37), STALE 18 → 24(r4 옛 문구 6개). r4 단언은 하나도 빼거나 약하게 하지 않았다. 로그 `check_citations.log`.
   - 단언 하나를 처음에 잘못 썼다(`chat_general.py:206`에 `'agent_settings' in turn['binding']`을 기대했으나 그 줄은 `if turn:`이고 대상은 :207). 문서 인용(`:206-210`)은 맞았고, 단언을 `:206 'if turn:'` + `:207 ...`로 고쳐 단언 수가 1 늘었다. 기대값을 약하게 한 것이 아니다.
2. 인용 검사(음성): 문서 사본(`negative/FRAME-negative.md.txt`)에 r4 문구 2개를 되살리고 앵커 하나를 `chat_sessions.py:185-1870`으로 바꿈.
   ```
   OUT_OF_RANGE chat_sessions.py:185-1870 len 266
   STALE 도구는 위 두 함수를 **그대로 호출만** 한다
   STALE 그래서 `secure_delete`는 꺼져 있고
   ... fail 3
   exit 1
   ```
   같은 로그에 r4 스크립트를 새 문서에 돌린 회귀 결과도 있다: `explicit anchors 324 content checks 178 ... fail 0`, exit 0. 로그 `check_citations-negative.log`.
3. SQLite 실측(`tasks/D1-r5/sqlite-probe/probe.py`, `sqlite-probe/` 폴더에서 인터프리터마다 `PYTHONDONTWRITEBYTECODE=1 <python> -B -I probe.py <label>`). 무작위(주기 없는) 약 40KB 표식을 행마다 `message_body`·`count_body` 2벌로 넣고, 표식 가운데 64자 창의 개수(= 남은 벌 수)를 셈. 연결은 `app.py:277-278`과 같은 `sqlite3.connect(db, timeout=30)`, 동작마다 새 연결.
   ```
   [anaconda] python 3.13.9 /opt/anaconda3/bin/python3 sqlite 3.51.0 | default secure_delete=1 compile SECURE_DELETE=['SECURE_DELETE']
   [anaconda] A default DELETE: before=2 after_delete=0 backup_copied_after_delete=0 after_vacuum=0
   [apple] python 3.9.6 /usr/bin/python3 sqlite 3.51.0 | default secure_delete=2
   [apple] A default DELETE: before=2 after_delete=2 backup_copied_after_delete=2 after_vacuum=0
   [apple] B ON on deleting connection: after_delete=0 | C ON on earlier connection only: secure_delete=2 after_delete=2
   [apple] D rewrite UPDATE: default after=2 | ON after=0
   [homebrew]/[py315] python 3.15.0 sqlite 3.54.0 | default secure_delete=0
   [py315] A default DELETE: before=2 after_delete=2 backup_copied_after_delete=2 after_vacuum=0
   [py315] B ON on deleting connection: after_delete=0 | C ON on earlier connection only: secure_delete=0 after_delete=2
   [py315] D rewrite UPDATE: default after=2 | ON after=0
   ```
   (요약. 원문은 `probe.log`, 각 실행 exit 0.) `journal_mode=delete`, `auto_vacuum=0`은 네 경우 모두 같았다. `/opt/homebrew/bin/python3`는 3.15와 같은 실행 파일이었다. `-journal` 파일은 남지 않았다(로그의 파일 목록). 실제 `data/studio.sqlite3`는 열지 않았다.
   - r4 표식 확인: `base64(b'FRAMEPROBE'*400)`은 5,336자이고 그 안에서 앞 64자가 66회 맞는다. 즉 r4의 "65회"는 한 벌 안의 적중 횟수다.
4. 문서 게이트(읽기 전용): `PYTHONDONTWRITEBYTECODE=1 python3.15 -B tools/document-gate/check.py --root .` → exit 1, `status: blocked`, findings 30. 이 문서는 `UNCLASSIFIED_DOCUMENT`(미등록, 예상대로). `.document-gate.json` mtime 실행 전후 같음(1793176405), FRAME-OBSERVATION 항목 0개. 출력 `document-gate-readonly.json`. findings 수가 r4 때(27, critic 실행 28)보다 늘어난 것은 병행 트랙의 다른 문서 때문이며 이 문서 관련 항목은 위 1건뿐이다.
5. unittest: 코드를 바꾸지 않아 실행하지 않았다. `tasks/D1-r5/` 아래 `.pyc`·`__pycache__` 없음을 확인했다.

## 남은 빈칸·한계
- §10에 추가하거나 강화한 테스트 4건(비용 상한 렌더 0회, 두 대화 권한 범위, 3단계 뒤 권한 축소 (a)(b)(c), 삭제 잔존 강화)은 설계상 요구이며, 구현하거나 실행하지 않았다.
- [추정] 승인·전송 직전 재인가의 "이미지 블록이 든 미리보기" 판별은 `message_body` 구조를 훑는 방식으로 정했다. 구현 시 블록 배열 결과(§4-2 결정 (a))의 정확한 모양에 맞춰야 한다.
- [추정] 전송 직전 재인가 실패 시 상태가 `blocked_before_message`가 된다는 것은 `before/chat_general.py:792-833` 예외 경로를 읽고 추론한 것이다(attempt 전·`submitted` False·`cancel_requested` 아님일 때). 실제 실행으로 확인하지 않았다. 사용자가 그 사이 취소를 요청했다면 `cancelled`가 된다.
- [추정] `secure_delete=ON`의 쓰기량 증가, `VACUUM`의 잠금 시간·여유 공간 영향 크기는 측정하지 않았다.
- `secure_delete=2`(FAST)의 잔존 수는 이 실측에서 2벌 중 2벌, r4 critic 실측에서 1벌로 달랐다. 페이지 배치에 따라 달라지는 것으로 보이며 [추정], 문서는 FAST를 믿을 수 없는 것으로 다룬다.
- 관찰만 하고 고치지 않은 것(지적 목록 밖): §7 표의 "대화 전체 상한 … 한 턴(4회) 안에서는 묶이지 않는다"는 상한 최댓값(400,000 micro) 기준의 문장이다. 사용자가 더 작은 상한을 두면 한 턴 안에서도 걸리며, 이번에 추가한 2단계 비용 검사가 바로 그 경우를 다룬다. 문장 자체는 최댓값 기준으로 사실이라 손대지 않았다. 필요하면 다음 라운드에서 "최댓값 기준" 단서를 붙일 수 있다.
- `frame_deliveries` 스키마 검증 여부 [미확인], 그리고 이전 라운드의 [미확인] 항목(Haiku 5.5 이미지 입력 지원, count_tokens 과금, 640×360 PNG 실제 크기, FFmpeg 출력 결정성)은 그대로다.

## 사용자 결정 항목 (구현 전 승인 대상, 이번 작업은 결정 없이 종료)
- A2: 3단계 뒤 권한 축소에 대해 "승인 때·전송 직전 재인가"를 택했다(critic이 제시한 두 선택지 중 하나). "사람 승인만 관문" 쪽을 원하면 §4-4 :95-98과 §10 :219를 바꿔야 한다.
- A5: 삭제·재작성 연결마다 `PRAGMA secure_delete=ON`(①)과 삭제 뒤 `VACUUM`(②) 중 무엇을 쓸지. 삭제 전 백업과 ①·② 없이 삭제한 뒤의 백업을 어떻게 다룰지.
- 이전 라운드에서 넘어온 항목은 그대로다: 모션 v1 제외, 바이트 처리 방식(권장안 i / 대안 ii), 64KiB 처리 방식, 전송 2회·노출 2벌 수용, 블록 배열 적용 범위 (a)/(b), D20 값 16384 확인.

## 파일
- `tasks/D1-r5/result.md`(이 파일), `changes.diff`, `check_citations.py`, `check_citations.log`, `check_citations-negative.log`, `negative/FRAME-negative.md.txt`, `sqlite-probe/probe.py`, `sqlite-probe/probe.log`, `sqlite-probe/run-*/`(모형 DB), `document-gate-readonly.json`, `document-gate-readonly.stderr`, `start/`
