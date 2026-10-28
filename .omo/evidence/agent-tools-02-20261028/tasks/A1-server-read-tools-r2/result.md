# A1-server-read-tools 재작업 2 (r2) 결과

작성 2026-10-28. 외부·유료·모델 호출 0, 네트워크 0, `.env` 미접촉, 8765/57888 서버 미기동, 브라우저 미사용, 프로젝트 파일 삭제 0.
r2 편집 전 사본: `before-r2/` (쓰기 범위 7개 모듈 + 바꾼 테스트 3개). 전체 diff: `r2.diff`.
바뀐 모듈은 `chat_runtime.py`, `fal_dispatch.py`, `chat_protocols.py` 3개다. `chat_general.py`·`agent_preferences.py`·`app.py`·`production_tools.py`는 r2에서 바꾸지 않았다(`diff -q`로 확인).

## 결함별 조치

### 1) D1 — legacy 기본 도구 목록 축소 [검증됨]
- `chat_runtime.py:16-17`: 명시 목록 `LEGACY_DEFAULT_TOOLS`(13개)를 신설했다. `production_tools.TOOLS` 14개 중 `request_media_generation`만 빼고 순서는 TOOLS 그대로 두었다.
- `chat_runtime.py:178`: `limits()` 기본값을 `list(production_tools.TOOLS)`에서 `list(LEGACY_DEFAULT_TOOLS)`로 바꿨다. 승인에 `tools`를 직접 적은 경우의 동작은 바꾸지 않았다.
- `tests/test_general_chat_tool_invariants.py:39-44`: 고정 테스트를 "포함"에서 "없음"으로 의도적으로 바꿨다. 사용자가 D1을 권장대로 승인했기 때문이다. 이제 `request_media_generation`이 없고, 나머지 도구가 TOOLS 순서 그대로 있음을 단언한다. 편집 전 코드에서는 이 테스트가 FAIL한다(`repro-d1-pin-before-r2.log`: `'request_media_generation' unexpectedly found in [...]`).
- **critic의 반증에 대한 보정(새로 발견)**: 기본값에 의존하는 테스트는 고정 테스트 하나만이 아니었다. `tests/test_chat_preflight.py`도 의존한다. 이 파일의 `final_body()`는 legacy 경로가 TOOLS 전체를 보낸다고 가정하고 기대 본문을 만든다. 그래서 D1 적용 후 4개가 FAIL했다(`after-related-tests.run1-preflight-fail.log`, 예: `b'..."get_generation_job"...' != b'..."request_media_generation"...'`).
  - `tests/test_chat_preflight.py:38-39`: 기대 본문을 런타임과 같은 방식(`limits()['tools']`로 거른 정의)으로 만들도록 고쳤다. 바이트 경계 단언(65529/65536/65537, `blocked_before_message`, 요청 0건)은 그대로 두었다. 경계 패딩은 기존 코드가 본문 크기에 맞춰 다시 계산한다. 이것도 의도된 기대 변경이고, 이유는 D1이다.
- 지정한 6개 모듈과 바꾼 테스트를 함께 돌렸다: `test_fal_multimodel`, `test_execution_context`, `test_action_tool_bridge`, `test_rehearsal_workflow`, `test_chat_runtime`, `test_production_tools`, 그리고 invariants·estimate·preflight. 결과는 91개 OK다(`d1-tests.log`).

### 2) estimate_plan — 연결 없음·오래된 입력 분리, 제외 건수 [검증됨]
- `fal_dispatch.py:72-91`
  - 항목마다 `self.adapter(a)`를 호출한다. `actions.ExecutionBlocked`가 나면 `excluded='not_connected'`로 표시하고 합계에서 뺀다.
  - `model_selection.action_context(p,a)!=a['context_hash']`이면 `excluded='stale'`로 표시하고 합계에서 뺀다. `approve()`가 쓰는 것과 같은 media snapshot 검사다(`fal_dispatch.py:86`).
  - 그 밖의 만료 quote는 `excluded='expired'`다. 만료 항목이 하나라도 있으면 `incomplete`이고 `total=None`이다. 기존 동작을 유지했다.
  - 결과에 `excluded={held,rejected,expired,not_connected,stale}` 건수를 추가했다. 보류·거절 항목은 기존처럼 목록에 넣지 않고 건수만 센다.
  - 남은 유효 항목이 없으면 `incomplete`·`total=None`이다. label은 '이 대화에서 준비된 현재 유효 작업의 견적 합계입니다(제외 건수는 excluded). 계획 전체 견적이나 청구 금액이 아닙니다.'로 바꿨다.
- 테스트(`tests/test_general_chat_estimate.py`)
  - `:109` 신규: `media_dispatch`는 있고 어댑터만 없는 경우(`adapters.clear()`). 두 항목이 모두 `not_connected`로 표시되고, `incomplete`, `total None`, `excluded.not_connected=2`, 실행 0이다. 편집 전 코드는 `'estimated' != 'incomplete'`로 FAIL한다(`repro-estimate-before-r2.log`).
  - `:120` 신규: 입력이 바뀐 경우. 준비 → 프로젝트 이미지 모델 선택 변경(`model_settings`, media-v1 입력) → 다른 모델을 명시해 다시 준비 → 대화 모델만 변경(chat) 순서로 진행한다. 결과는 예전 작업 `stale`, 새 작업 유효, 합계 0.01, `excluded.stale=1`이다. 대화 모델만 바꾼 경우에는 stale이 되지 않음도 같이 확인한다(codex #6).
  - 기존 테스트에는 단언만 추가했다(약화 0). held/rejected 테스트(`:76`)에 `excluded` 건수를, 만료 테스트에 `excluded='expired'`와 건수를 단언했다.
  - `:27` `select()` 헬퍼를 추가하고, `prepare(**extra)`가 `model`을 넘길 수 있게 했다.
- 변이 확인(`mutant-estimate.log`)
  - stale 검사 줄을 지우면 stale 테스트가 FAIL한다.
  - 어댑터 검사를 지우면 not_connected 테스트가 `'estimated' != 'incomplete'`로 FAIL한다.

### 3) prepare_video_action HTTP 테스트의 구분력 [검증됨]
- `tests/test_general_chat_tool_invariants.py:119-138`
  - 공유 visible take(id=100, 대화 출처 없음)를 대조군으로 추가했다.
  - `patch.object(pipe,'prepare',wraps=pipe.prepare)`로 호출 수를 센다.
  - unknown shot, 없는 take(98), 숨은 take(99)는 각각 `INVALID_MEDIA_INPUT`이고 `prepare` 호출 0이다. visible take 대조군은 `prepare` 호출이 1 이상이다.
  - 기존 단언(`INVALID_MEDIA_INPUT`, actions 0, 실행 0)은 유지했다.
- 변이 확인(`mutant-video-guard.log`): `fal_dispatch.prepare_tool`의 visibility 가드를 지우면 `source_take_id=98`에서 `1 != 0`, 숨은 take에서 `2 != 0`으로 FAIL한다. 이 테스트가 이제 가드를 다른 실패와 구분한다.

### 4) 토큰 예산 — 설명문 축약 [검증됨: 바이트만]
- `chat_protocols.py:7-23`: 14개 설명을 구분에 필요한 최소 문구로 줄였다. 결과에 이미 있는 필드와 겹치는 절을 뺐다.
  - get_model_capabilities: `live_execution=False`가 결과에 있다.
  - search_project_context: `search_mode`와 `note`의 '의미 검색 아님'이 결과에 있다.
  - propose_media_plan: `cost_approval=False`가 결과에 있다.
  - prepare_*: `approval='required'`, `external_calls=0`이 결과에 있다.
  - estimate: label이 결과에 있다.
  - propose_timeline_changes: `status='applied_draft'`와 `'proposed'`로 구분된다.
  - 설명 테스트 조건(160자 이하, 'server-controlled'·'Loretune'·개행 없음)은 그대로 통과한다.
- 측정: 이번 폴더의 `measure_token_budget.py`로 했다. A1 스크립트와 같고, 견적 이어쓰기 fixture만 r2 결과 형태로 바꿨다. 세 버전을 같은 fixture로 쟀다. 원본 측정값은 `measure-{wave0,wave1,r2}.json`, 요약은 `token-budget.json`이다.

| 모드 | 설명 바이트 wave0→wave1→r2 | tools 바이트 wave0→wave1→r2 | 첫 회차 본문 바이트 wave0→wave1→r2 |
|---|---|---|---|
| review·full_access | 377 → 881 → 498 | 9965 → 10880 → 10497 | 16617 → 17532 → 17149 |
| read_only | 98 → 394 → 189 | 508 → 1215 → 1010 | 7160 → 7867 → 7662 |

- wave1 대비 r2는 review에서 -383B, read_only에서 -205B다. wave0 대비 순증은 review +532B(이전 +915B), read_only +502B다.
- 견적 결과 자체는 wave1 형태 858B에서 r2 형태 1016B로 158B 늘었다(항목별 `excluded`와 건수 추가). 이어쓰기 본문은 r2에서 18564B다.
- 비율 추정(토큰 수 아님): review 첫 회차는 wave0부터 /4 기준 4096을 넘는다. 17149B/4는 약 4287, /3.2는 약 5359다. read_only 7662B는 /4 약 1916, /3.2 약 2394다. 이전에 관측한 1.97~2.31 B/tok 비율을 쓰면 약 3317~3889다. **실제 토큰 count는 하지 않았다.**

### 5) 기록만 (고치지 않음)
- **request_render / request_motion_render의 grant_id 사전 검사**: 다른 대화의 grant_id나 모르는 grant_id는 여전히 HTTP 사전 검사(`chat_sessions.py:125` `guard_refs`의 `grant_id` 분기)에서 400으로 거절된다. 두 도구는 `chat_general.ALLOWED_TOOLS`에 노출되어 있다. 따라서 모델 응답 비용을 치른 뒤 일반 대화 턴이 `outcome_unknown`으로 끝날 수 있다. `app.py:534`의 `tool_scoped`가 옮긴 것은 3개 도구뿐이다. 이 건은 wave 2 후속이다(`local_creation_tools` 핸들러가 이미 grant를 검증하므로, 키를 빼고 구조화된 결과로 돌려주는 방식이 후보다). r2 지시 범위 밖이라 손대지 않았다.
- **D14 범위**: `get_generation_job` 결과에서만 `grant_id`를 뺐다. 아래 경로에서는 설계상 grant id가 모델에 계속 보인다. `request_render`와 `request_motion_render`가 이 id를 인수로 받아야 하기 때문이다. 따라서 D14의 보호 효과는 "작업 조회 결과에 다시 싣지 않는다"는 데 한정된다.
  - `search_project_context`의 `execution_targets`: 미디어 `approval_handles[].grant_id`(`production_context.py:259`)
  - 타임라인 `grant_id`(`:249`)
  - 모션 `grant_id`(`:52`)
  - 줄 번호는 2026-10-28 현재 기준이다. 이 파일은 트랙 C가 소유하므로 번호가 바뀔 수 있다.

## 실행한 명령과 출력 꼬리 (원문)

모두 `cd /Users/leesungmin/Desktop/Loretune`에서 실행했다. 인터프리터는 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B`다.

1. D1 묶음: `PYTHONPATH=tests ... -m unittest tests.test_fal_multimodel tests.test_execution_context tests.test_action_tool_bridge tests.test_rehearsal_workflow tests.test_chat_runtime tests.test_production_tools tests.test_general_chat_tool_invariants tests.test_general_chat_estimate tests.test_chat_preflight -q` (`d1-tests.log`)
   ```
   Ran 91 tests in 16.648s

   OK
   ```
2. 관련 51개 모듈(A1의 50개 + `tests.test_chat_runtime`, 목록은 `related-modules.txt`): `PYTHONPATH=tests ... -m unittest $(cat related-modules.txt) -q`
   - 1차 실행(`after-related-tests.run1-preflight-fail.log`, preflight 고치기 전):
     ```
     Ran 503 tests in 264.336s

     FAILED (failures=4)
     ```
     FAIL 4개는 모두 `tests.test_chat_preflight`이고 원인은 위 D1 항목에 적었다.
   - 2차 실행(`after-related-tests.log`, preflight 수정 후):
     ```
     ----------------------------------------------------------------------
     Ran 503 tests in 267.267s

     OK
     ```
3. legacy 경로에 의존할 수 있는 추가 8개 모듈(grep 기준: `tool_definitions|chat_runtime|ChatRuntime|limits()|production_tools.TOOLS|request_media_generation|test_chat_runtime|anthropic_ontology|chat_adapters` 가운데 2번 목록에 없는 것, `extra-modules.txt`) (`after-extra-tests.log`)
   ```
   Ran 61 tests in 6.431s

   OK
   ```
4. 재현: r2 편집 전 모듈(`before-r2/`)을 scratchpad 모듈 묶음에 넣고 현재 테스트를 실행했다.
   - estimate: `FAILED (failures=1, errors=3)`. 어댑터 없음 케이스는 `'estimated' != 'incomplete'`, 나머지는 `KeyError: 'excluded'`다.
   - D1 고정 테스트: `FAILED (failures=1)`.
   - 영상 HTTP 테스트: 편집 전에도 OK다. 가드는 wave 1에 이미 있었으므로 예상된 결과이고, 구분력은 4의 변이 확인으로 증명했다.
5. 변이 확인: `mutant-video-guard.log` (`FAILED (failures=2)`), `mutant-estimate.log` (stale·not_connected 각각 `FAILED (failures=1)`).
6. 바이트 측정: `measure_token_budget.py <root> x`를 wave0, wave1, r2 세 가지 root로 실행했다. 세 번 모두 exit=0이다.

전체 회귀(`discover -s tests` 전체)는 실행하지 않았다. main이 통합 단계에서 실행한다.

## 남은 빈칸

- **legacy 실행 거절의 동작 증명이 없다**: D1은 기본값 축소와 정적 고정 테스트로만 확인했다. codex #1이 요구한 "유효 grant가 있어도 legacy 모델의 `request_media_generation` 호출이 거절되고 예약·제출이 0"이라는 종단 테스트는 이번 지시 범위에 없어 추가하지 않았다. 코드상으로는 `chat_runtime.py:55`(claim_tool)과 실행 루프의 `call['name'] not in limits['tools']`에서 거절된다 [추정, 종단 미검증].
- **승인에 tools를 직접 적는 경우**: 승인 dict에 `tools`를 명시하면 여전히 `request_media_generation`을 넣을 수 있다. `limits()`는 TOOLS 소속 여부만 검사한다. 저장소 코드와 테스트에서 이 도구를 명시 목록에 넣는 곳은 찾지 못했다(grep). 이것까지 막을지는 미결이다.
- 견적 `stale`은 media snapshot만 검사한다. `approve()`가 추가로 검사하는 계획 `context_hash`와 shot revision은 견적에서 검사하지 않는다(지시 범위가 media snapshot). 계획 문맥이 바뀐 작업은 견적에서 유효로 남을 수 있다 [추정].
- 실제 토큰 count, 실화면, 전체 회귀는 하지 않았다.

## 가정·추측

- [가정] 만료 quote는 기존 동작대로 전체를 `incomplete`로 만든다. 다만 연결 없음이나 stale로 이미 제외된 항목의 만료는 전체 판정에 반영하지 않는다(이미 합계 밖이기 때문).
- [가정] 견적 결과에서 보류·거절 항목은 예전처럼 `actions` 목록에서 빼고 건수만 반환한다. 연결 없음·stale·만료 항목은 목록에 남기고 `excluded` 이유를 붙인다(지시의 "mark").
- [추정] 이번에 뺀 설명 절은 결과 필드가 같은 정보를 준다고 판단했다. 모델 동작 변화는 측정하지 않았다.

## 사용자 결정이 필요한 사항

1. **D20 입력 상한**(기존 위험): review·full_access 첫 회차 본문 17149B는 /4 기준으로도 4096을 넘는다. 이 초과는 wave0 16617B 때부터 있었다(`token-budget.json`). 설명 축약으로 줄일 수 있는 양은 수백 B 수준이라 근본 해결이 아니다. 선택지는 세 가지다.
   - (a) 모드·질의별 도구 노출 분리
   - (b) 유료 count_tokens 실측을 승인한 뒤 상한 재검토
   - (c) 스키마 자체 축약
2. **승인 dict의 명시 tools에 실행 도구 허용 여부**: 위 남은 빈칸. 막으려면 `limits()`가 `request_media_generation`을 명시 목록에서도 거절해야 하는데, 이것은 승인 계약을 바꾸는 일이다.
3. **request_render / request_motion_render의 grant_id 사전 검사 이동**(wave 2): 지금은 응답 비용을 치른 뒤 `outcome_unknown`으로 끝날 수 있다.
