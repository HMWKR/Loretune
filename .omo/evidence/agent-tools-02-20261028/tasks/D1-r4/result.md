# D1-r4 결과 — 프레임 관찰 설계 문서 4차 수정

- 대상: `docs/design/FRAME-OBSERVATION-DESIGN-ko.md` (49,262 → 58,604바이트, sha256 `591c7491767ef8c1ac7b882b356ae49bb796b73b36ab1f146de577a428230ad5`)
- 시작 사본: `tasks/D1-r4/start/FRAME-OBSERVATION-DESIGN-ko.md.txt`(sha256 `1552a674…09192`, r3 수락본과 같음), `tasks/D1-r4/start/check_citations.py.txt`(r3 스크립트)
- 변경 diff: `tasks/D1-r4/changes.diff` (문서 + 인용 검사 스크립트)
- 쓰기 범위: 설계 문서와 `tasks/D1-r4/`만. 문서 등록 안 함. 코드·테스트 파일 변경 없음.
- 줄 번호: 소스 인용은 문서 규약대로 `before/` 사본 기준, 문서 줄은 현재 파일 기준.

## critic 지적별 처리 (r3 verdict minor 6건)

| # | 지적 | 처리 | 위치 | 증거 |
|---|---|---|---|---|
| 1 | 모션 대상이 3단계 바이트 경로에 없음 | **고침**: v1을 저장된 편집 프레임으로 한정하고 `kind:'motion'`은 1단계에서 `TARGET_KIND_UNSUPPORTED`로 거절(렌더 0회). 나중에 모션을 넣을 때 필요한 것(같은 3단계 경로, 변경안 id·scene sha256 고정과 재대조, 출력 바이트 상한, 권리 검사, 같은 테스트)을 §3에 적고 §9 A2 승인 항목으로 옮김. §6 예시에서 `'motion'` 제거 | 문서 :17(§1), :44(§3), :87(§4-4 1단계), :144(§6), :188(A2), :209(§10 테스트) | 인용 검사 STALE 항목 `kind:'timeline'\|'motion'`, `timeline_revision\|proposal_id+scene_sha256`이 문서에 없음(fail 0). 음성 실행에서 되살리면 STALE 2건 검출 |
| 2 | 렌더 단계와 마지막 라운드 판정(:773)의 순서 미정 | **고침**: 2단계는 `chat_general.py:773` 판정을 통과한 뒤 `:777` 앞에서만 실행. 마지막 라운드 프레임 호출은 영수증만 남고 렌더 0회. 그 영수증의 누적 영향은 턴이 끝나 없음을 명시 | 문서 :88(§4-4 2단계), :208(§10 "마지막 라운드 렌더 0회") | 인용 검사 신규 단언 `chat_general.py:773-776`(판정·`limit_reached`·`return True`) 통과 |
| 3 | 중복 판정과 실패 누적이 경계에서 충돌 | **고침**: 중복은 **실제로 전달된** 프레임(3단계가 run의 `frame_deliveries`에 바이트 없이 기록)만 기준. busy 등 실패 프레임은 같은 턴에서 재요청 가능. 누적은 1단계 통과 영수증 기준이며 1단계 거절(중복·초과·인수 오류·권한·모션)은 0장, 2·3단계 실패는 포함 → busy 뒤 재요청은 허용되지만 누적 2장. `frame_deliveries` 기록은 같은 트랜잭션이 state를 쓰는 기존 `close_run` 방식(`chat_general.py:378-383`)을 따름 | 문서 :70(§4-3), :89(3단계), :205·:206·:207(§10 "1단계 거절은 누적 0장", "이전 라운드 재요청", "busy 뒤 재요청") | 인용 검사 신규 단언 `chat_general.py:378`, `:383` 통과 |
| 4 | 요청 도중 권한 축소 미설계, 읽기 도구 분류 없음 | **고침**: 2단계 렌더 전(현재 state 읽기, `chat_general.py:764-766` 방식)과 3단계 트랜잭션 안(`:784` `_current`)에서 `authorize` 재호출. 실패 시 이미지 없는 `status:'blocked'`, `code:'AGENT_READ_ONLY'`. 프레임 도구는 `READ_TOOLS`(`agent_preferences.py:14`)에 넣지 않음 → `read_only`에서 거절·도구 정의 제외(`:70-72`, `chat_general.py:424`). 근거는 `effective_mode`가 현재 프로필 모드를 포함(`agent_preferences.py:61-67`)하고 `update`가 진행 중 run 상한을 낮춤(`:93-99`) | 문서 :87-89, :91-94(§4-4 "요청 도중 권한 축소"), :188(A2), :210(§10 테스트) | 인용 검사 신규 단언 `agent_preferences.py:14,61,66,70,72,75,79,93,99`, `production_tools.py:75`, `chat_general.py:424,764-766,784` 통과 |
| 5 | A5 보관 목록에 SQLite 삭제 잔존·이전 백업 없음 | **고침**: §4-4 표에 "SQLite 파일의 빈 페이지", "SQLite 롤백 journal" 행 추가, 백업 행에 "삭제 전 백업에는 남음" 추가. §9 A5에 `PRAGMA secure_delete=ON` 또는 `VACUUM` 필수와 이전 백업 처리 추가. §11에 실측 기록, §10에 삭제 잔존 테스트 추가 | 문서 :113-115(§4-4 표), :191(A5), :211(§10), :231(§11) | **실측** `tasks/D1-r4/sqlite-probe/probe.log` (아래) |
| 6 | 인용 검사의 `eval()` | **고침**: r4 스크립트 `tasks/D1-r4/check_citations.py:175`에서 `ast.literal_eval`로 교체하고 전체 재실행. r3 폴더의 원본 스크립트는 쓰기 범위 밖이라 그대로 둠 | `tasks/D1-r4/check_citations.py:16`(`import ast`), `:175` | 재실행 fail 0. `ast.literal_eval("__import__('os').getcwd()")`는 `ValueError`(코드 실행 안 됨) — `check_citations-negative.log` |

## 실행한 명령과 출력 끝부분 (모두 `/Users/leesungmin/Desktop/Loretune`에서)

1. 인용 검사(정상):
   ```
   PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B .omo/evidence/agent-tools-02-20261028/tasks/D1-r4/check_citations.py
   explicit anchors 302 content checks 178 (before/md 173 + current 5) empty-expected 0 fail 0
   exit 0
   ```
   r3 대비: 앵커 274 → 302, 내용 단언 155 → 178(신규 23), STALE 문구 13 → 18(r3 문구 5개 추가). 기존 단언은 하나도 빼거나 약하게 하지 않았다. 로그 `check_citations.log`.
2. 인용 검사(음성): 문서 사본에 r3 모션 대상 문구를 되살리고 앵커 하나를 `agent_preferences.py:93-999`로 바꿈.
   ```
   OUT_OF_RANGE agent_preferences.py:93-999 len 141
   STALE kind:'timeline'|'motion'
   STALE timeline_revision|proposal_id+scene_sha256
   ... fail 3
   exit 1
   ValueError: malformed node or string on line 1: Call(...)
   literal list ok: 2
   ```
   로그 `check_citations-negative.log`.
3. SQLite 삭제 잔존 실측(`tasks/D1-r4/sqlite-probe/probe.py`, `run/` 폴더에서 실행, `python3.15 -B -I`):
   ```
   default.sqlite3: sqlite 3.54.0 journal_mode=delete secure_delete=0 auto_vacuum=0 | marker hits before_delete=65 rows_after_delete=0 file_hits_after_delete=65 after_vacuum(False)=65
   vacuum.sqlite3:  ... file_hits_after_delete=65 after_vacuum(True)=0
   secure.sqlite3:  ... secure_delete=1 ... file_hits_after_delete=0
   ```
   연결은 `app.py:277-278`과 같은 `sqlite3.connect(db, timeout=30)`, PRAGMA 없음. 미리보기 행 모양(`general_chat_previews` 4열, JSON 본문 안 base64)의 축소 모형이며 실제 `studio.sqlite3`는 건드리지 않았다. 실행 뒤 폴더에 `-journal` 파일 없음(로그 끝 목록).
4. 문서 게이트(읽기 전용): `tools/document-gate/check.py --root .` → exit 1, `status: blocked`, findings 27. 이 문서는 `UNCLASSIFIED_DOCUMENT`(미등록, 예상대로). `.document-gate.json` mtime 실행 전후 동일(1793176405). 출력 `document-gate-readonly.json`.
5. unittest: 코드 변경이 없어 실행하지 않음.

## 남은 빈칸·한계
- 문서의 새 테스트(§10 추가 6건)는 **설계상 요구**이며 구현·실행되지 않았다. 이번 범위는 설계 문서다.
- [추정] `secure_delete`의 쓰기량 증가, `VACUUM`의 잠금 시간과 여유 공간 영향의 크기는 측정하지 않았다. 지워진 `-journal` 파일 블록이 파일시스템에 남는지도 확인하지 않았다.
- 현재 프로젝트의 `READ_TOOLS`는 병행 트랙 변경으로 `./agent_preferences.py:15`에 5개(`estimate_media_plan`, `get_agent_settings` 추가)다. 문서는 before 기준 `agent_preferences.py:14`를 인용한다. 프레임 도구를 넣지 않는다는 결정은 두 판 모두에 성립한다.
- `frame_deliveries`는 새 run 필드 제안이다. run 스키마를 검증하는 코드가 이 필드를 막는지는 구현 때 확인해야 한다 [미확인].
- r3 폴더의 `check_citations.py`(eval 포함)는 쓰기 범위 밖이라 그대로 있다. 앞으로는 `tasks/D1-r4/check_citations.py`를 쓴다.
- 이전 라운드의 [미확인] 항목(Haiku 5.5 이미지 입력 지원, count_tokens 과금, 640×360 PNG 실제 크기, FFmpeg 출력 결정성)은 그대로다.

## 사용자 결정 항목 (구현 전, 이번 작업은 결정 없이 종료)
- A2: 모션 변경안 프레임을 v1에서 빼는 것, 프레임 도구를 읽기 도구로 보지 않아 `read_only`에서 거절하는 분류.
- A5: 프레임이 든 행 삭제 시 `secure_delete=ON`과 `VACUUM` 중 무엇을 쓸지, 삭제 전에 만든 백업을 어떻게 다룰지.
- 이전 라운드에서 넘어온 항목은 그대로: 바이트 처리 방식(권장안 i / 대안 ii), 64KiB 처리 방식, 전송 2회·노출 2벌 수용, 블록 배열 적용 범위 (a)/(b), D20 값 16384 확인.
