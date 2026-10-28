# A1-server-read-tools 결과 (S1 · A-pre · S2 · S3 · D1 · D2 · D11 · D14 · 토큰 측정)

작성 2026-10-28. 외부·유료 호출 0, 서버 8765/57888 미접촉, 파일 삭제 0. 편집 전 사본은 `before/`.

## 한 일 (파일별)

- `chat_general.py` — `ALLOWED_TOOLS`에 `get_generation_job`, `estimate_media_plan` 추가(S2·S3). 순서는 끝에 덧붙임. `request_media_generation`은 그대로 미노출.
- `agent_preferences.py` — `READ_TOOLS`에 `estimate_media_plan` 추가(D2). 읽기 전용 모드에서도 견적 합계 조회 허용.
- `production_tools.py` — `get_generation_job` 결과 키 목록에서 `grant_id` 제거(D14). 나머지 키·`registered_takes`·`result_approved` 계산은 그대로.
- `fal_dispatch.py`
  - `estimate_plan`: ① 현재 대화 소유 작업만(`chat_sessions.owns(p, action_id)`), ② 사람이 보류·거절한 작업(`media_action_reviews[...].decision in {held,rejected}`, `media_creator.guard`와 같은 기준) 제외, ③ `label` 필드 추가: `'이 대화에서 준비된 작업(보류·거절 제외)의 견적 합계입니다. 계획 전체 견적이나 청구 금액이 아닙니다.'` (S3)
  - `prepare_tool`(video): 모델이 준 `source_shot_id`/`source_take_id`를 여기서 해석 — 없는 Take 또는 현재 대화에 보이지 않는 Take(`chat_sessions.take_visible`)면 `ValueError` → 기존 분기에서 `invalid_arguments / INVALID_MEDIA_INPUT`. (A-pre, wave 2 대비. `prepare_video_action`은 ALLOWED_TOOLS에 넣지 않음)
  - import에 `chat_sessions` 추가.
- `app.py` — `mutate`의 사전 가드(A-pre). **`production_tool` 경로에서 아래 3개 도구의 해당 키만** `guard_refs`/`check_takes` 검사 사본에서 뺀다: `get_generation_job.job_id`, `estimate_media_plan.plan_id`, `prepare_video_action.source_shot_id/source_take_id`. 해당 도구는 이미 범위 안에서 해석한다(작업 목록은 `owns`로 거른 뒤 조회 → `not_found`, 계획은 대화 범위 `guided_plans`에서 조회 → `not_found`, Take는 위 fal_dispatch 검사). `run` 키, 다른 모든 도구(`request_media_generation`·`request_render` 등), 모든 사람용 HTTP 동작은 기존 검사 그대로. `append_clips` 예외 블록은 손대지 않음.
  - 구현 중 실수 1건 발견·수정: 루프 변수를 `key`로 써서 `mutate` 상단의 요청 ID 변수 `key`를 덮어써 `claim_tool`이 거절(→ outcome_unknown) — `handle`로 바꿈. 새 테스트가 이것을 잡았다.
- `chat_protocols.py` — 14개 도구 모두 `'Loretune server-controlled '+name` 대신 `DESCRIPTIONS`의 한 줄 영문 설명(D11). 영문을 고른 이유: 입력 4096 상한 대비 바이트 절약(아래 토큰 측정), 기존 모델 대상 지시문(`create_preview` 이력 머리말)이 영문. 제품명은 넣지 않음.
- `chat_runtime.py` — **변경 없음** (D1: 아래 "결정 필요" 참조).
- `tests/test_agent_preferences.py` (기존, 의도된 변경 3곳) — 읽기 전용 도구 목록 단언이 `['search_project_context','get_model_capabilities']` → `get_generation_job`, `estimate_media_plan` 포함으로 바뀜(일반 대화 `tool_scope`는 ALLOWED_TOOLS 순서, `message_body.tools`·legacy 경로는 TOOLS 순서). 이유: S2·D2로 읽기 도구가 늘어남. legacy 읽기 전용 경로에도 `estimate_media_plan`이 보이게 됨(READ_TOOLS 공유 — 읽기 도구라 의도).
- 신규 `tests/test_general_chat_tool_invariants.py` (9개)
  - 정적: ALLOWED_TOOLS에 `request_media_generation` 없음, ALLOWED ∩ ACCOUNT_DELETE = ∅, ALLOWED ∩ FILE_DELETE = ∅, (TOOLS ∪ READ_TOOLS) ∩ 삭제 이름 = ∅, 삭제 이름은 `validate`가 거절, AUTO_DRAFT 정확히 5개.
  - legacy 기본값 고정: `ChatRuntime.limits()` 기본 tools = `list(TOOLS)`이고 `request_media_generation` 포함(D1 결정 전 현 상태 고정).
  - 설명문: 14개 전부 전용 설명, 'server-controlled'·'Loretune'·개행 없음, 160자 이하.
  - 실행: 일반 대화에서 합성 `request_media_generation` tool_use → **실제 현재 결과 = `outcome_unknown`** (chat_general.py `process_next`의 `call['name'] not in ALLOWED_TOOLS` 분기, 응답 비용 정산 뒤). `production_tool` 요청 0건, run calls 0, `assert_no_media_execution`(generation_jobs·grants·provider_action_jobs·`project:%` 예약 0) 통과. `delete_account`/`delete_file`도 `outcome_unknown`·요청 0.
  - A-pre(video 키): 없는 source shot / 없는 take / 다른 대화의 숨은 take → HTTP 200 + `INVALID_MEDIA_INPUT`(편집 전에는 없는 shot·숨은 take가 HTTP 400). 숨은 take는 `prepare` 호출 전에 거절, 보이는 take는 `prepare`까지 도달(단위). 사람용 `review_take`는 숨은 take에 기존대로 400 '다른 대화의 미승인 Take…'.
- 신규 `tests/test_general_chat_job_query.py` (6개) — S2·A-pre(job_id)
  - 소유 generation job 성공 조회: `cost.billing_confirmed is False` 유지, 결과·이어쓰기 메시지 어디에도 `grant_id`/grant 값 없음, SQLite 지문(턴 기록 테이블·run·conversation_owners·chat_sessions revision 외) 불변, `project:%` 예약 수 불변.
  - `jobs` 테이블의 local render(`mode=local-render`)와 `local-3d-still` job 조회, 3D job의 승인 id 미노출.
  - 없는 id → `not_found`(기본 대화), 다른 대화에서 없는 id·기본 대화 소유 job → 둘 다 `not_found`, 턴은 `awaiting_continuation_approval`.
  - 사람 경로 불변: 다른 대화에서 `cancel_generation(job=기본 대화 job)` → 400 '다른 대화…'. 같은 id의 `production_tool get_generation_job` → 200 `not_found`. 옮기지 않은 도구(`request_media_generation`, 다른 대화의 plan_id) → 여전히 400.
  - 읽기 전용 모드 `tool_scope`에 `get_generation_job`·`estimate_media_plan` 포함, 실행 성공.
  - 예전 manifest(변경 전 생성 preview 모방, `test_general_chat_media_preparation` :129-138 패턴) → 새 도구를 얻지 못하고 `outcome_unknown`, run calls 0.
- 신규 `tests/test_general_chat_estimate.py` (6개) — S3
  - 소유 준비 작업 2개 합계 `0.02 USD`, `status=estimated`, `billing_confirmed False`, `approval False`, `label`에 '계획 전체 견적'·'청구' 포함, SQLite 지문 불변, `assert_no_media_execution`.
  - held/rejected 제외(3개 중 1개만), 다른 대화 소유로 기록된 작업 제외(소유 기록은 상태 DB에 합성 주입 — 정상 흐름에서 같은 계획에 남의 작업이 생기기 어려워 방어 검사로 시험), 다른 대화에서 계획 → `not_found`(이전엔 HTTP 400 → outcome_unknown), 만료 quote → `incomplete`·`total None`, 미디어 연결 없음(`media_dispatch=None`) → `blocked / LOCAL_TOOL_NOT_CONNECTED`.
- `token-budget.json`, `measure_token_budget.py` — 아래 토큰 측정.

## 실행한 테스트 명령과 결과 꼬리 (원문)

1) 재현(편집 전 모듈 7개를 임시 사본에 넣고 신규 테스트 실행) — `before-modules-new-tests.log`
```
cd <scratchpad>/before-root && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest tests.test_general_chat_tool_invariants tests.test_general_chat_job_query tests.test_general_chat_estimate -q
Ran 21 tests in 12.474s
FAILED (failures=14, errors=2)
exit=1
```
(통과한 5개는 원래부터 참이어야 하는 불변식: 정적 범위, AUTO_DRAFT, legacy 고정, 거절 2종, 예전 manifest, 사람 hidden-take 가드)

추가 재현(fal_dispatch만 편집 전): held/rejected·foreign 제외 2건 FAIL, `KeyError: 'label'` 1건 ERROR, 숨은 take 단위 테스트 ERROR(prepare 도달).

2) 편집 후 신규+변경 테스트 — `after-new-and-changed-tests.log`
```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest tests.test_general_chat_tool_invariants tests.test_general_chat_job_query tests.test_general_chat_estimate tests.test_agent_preferences tests.test_chat_protocols tests.test_general_chat_media_preparation -q
----------------------------------------------------------------------
Ran 56 tests in 33.128s

OK
exit=0
```

3) 바뀐 영역을 읽는 기존 테스트 50개 모듈(목록 `related-modules.txt`, grep 기준: production_tool·general_chat·estimate_plan·prepare_tool·tool_definitions·ALLOWED_TOOLS·READ_TOOLS·guard_refs·check_takes·conversation_create) — `after-related-tests.log`
```
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest <50 modules> -q
Ran 461 tests in 260.759s
OK
exit=0
```
(`PYTHONPATH=tests`는 `import test_chat_runtime`처럼 tests 폴더를 경로로 가정하는 기존 모듈 5개 때문. S0 드라이버의 `discover -s tests`와 같은 효과)

전체 회귀는 main이 실행(지시대로 미실행).

## 토큰 측정 (token-budget.json 요약)

오프라인, `json.dumps(ensure_ascii=False)` UTF-8 바이트(전송 인코더와 같은 방식). 고정 입력: haiku-5-5, effort low, 프롬프트 1개, 이력·음원 문맥 없음.

| 모드 | tools 전→후 (B) | 첫 회차 message_body 전→후 (B) | /4 | /3.2 |
|---|---|---|---|---|
| review·full_access | 9965 → 10880 (+915) | 16617 → 17532 | 4154→4383 | 5193→5479 |
| read_only | 508 → 1215 (+707) | 7160 → 7867 | 1790→1967 | 2238→2458 |

- 추가 도구 정의: `estimate_media_plan` 333B, `get_generation_job` 289B. 시스템 프롬프트 6390B.
- 이어쓰기 대표: job 결과 663B → 본문 18540B, 견적 결과 858B → 본문 18771B.
- **보정(실측 근거)**: 이전 실제 live 요청 5건의 count 토큰/바이트 비율이 1.97~2.31 B/tok(`docs/qa/claude-chat-ui-live-20261025`). 이 비율이면 review 첫 회차는 변경 전부터 약 7200~8900 tok, read_only 변경 후 약 3400~4000 tok(여유 약 100 tok).
- 결론: 요청한 /4·/3.2 기준으로도 **review/full_access 본문은 변경 전부터 4096을 넘는다**(기존 위험, 이번 변경 +915B는 일부). read_only는 /4·/3.2 기준 여유가 크지만 실측 비율로는 빠듯하다. 실제 count는 하지 않음(외부·유료 → 승인 필요).

## 안 한 일 / 남은 빈칸

- D1 legacy 경로 축소: **하지 않음**(아래 결정 필요). 현재 노출을 불변 테스트로 고정만.
- `request_media_generation`·`request_render`·`request_motion_render`의 `plan_id/action_id/grant_id` 사전 가드는 옮기지 않음(지시 범위가 job_id/plan_id/source 키, 그리고 plan_id는 견적 도구에 한정). `request_media_generation`의 다른 대화 plan_id는 여전히 HTTP 400.
- `estimate_plan`은 미디어 어댑터가 비어 있어도(`adapters` 빈 dict) 저장된 quote로 합계를 낸다. "어댑터 없음"은 `media_dispatch=None`(연결 없음) → `LOCAL_TOOL_NOT_CONNECTED`로 시험함. 어댑터 비활성 시에도 합계를 막을지 미결.
- 견적 결과에 제외된 보류·거절 작업 수는 넣지 않음(요청은 label 필드). 모델이 "몇 개 제외됐는지" 설명하려면 필드 추가가 필요 — 미결.
- 실제 count_tokens 측정, 실화면 확인, 전체 회귀: 미실행(main 또는 사용자 승인 사항).
- `chat_protocols` 설명 변경으로 새 preview의 manifest 해시가 바뀜(D11 예상). 저장된 예전 preview는 본문을 그대로 갖고 있어 유효성에는 영향 없음(테스트 통과로 확인).

## 가정·추측

- [가정] "Korean or English" 중 영문 설명을 택함(토큰 절약). 한국어로 바꾸면 바이트가 늘어난다.
- [가정] 다른 대화 소유 작업 제외 시험은 `conversation_owners`를 상태 DB에 직접 넣어 만든 합성 상황이다.
- [추정] 실측 B/tok 1.97~2.31은 legacy 경로(도구 2개, 짧은 시스템)의 값이며 도구 사용 시스템 오버헤드가 포함되어 있다. 일반 대화 본문에 그대로 적용된다는 보장은 없다.
- [검증됨] `request_media_generation` 합성 호출의 현재 종료 상태는 `outcome_unknown`(테스트로 확인).

## 기각한 가설

- "다른 대화에서 없는 job id도 기본 대화와 같이 `not_found`가 나온다" — 기각. `chat_sessions.owner`는 모르는 id를 기본 대화 소유로 보므로 기본 대화에서는 가드를 통과하지만, 다른 대화에서는 가드가 HTTP 400을 던져 턴이 `outcome_unknown`이 되었다(재현 로그). 그래서 키 제외가 필요했다.
- "숨은 take 검사는 하류(`data()`의 승인된 시작 프레임 검사)가 이미 막는다" — 통합 시험만으로는 구분되지 않아(편집 전 fal_dispatch로도 INVALID_MEDIA_INPUT) 단위 시험으로 확인: 편집 전에는 숨은 take로 `prepare`까지 도달. 하류에 의존하지 않도록 명시 검사를 둠.
- "legacy 기본 노출을 좁혀도 된다" — 근거 부족으로 보류(아래).

## 결정 필요 (D1)

legacy 경로(`chat_runtime.ChatRuntime.limits()` 기본 `tools=list(production_tools.TOOLS)`)는 모델이 **사람이 발급한 grant로** `request_media_generation`을 부르는 계약을 의도적으로 갖고 있다. 근거:
- `tests/test_fal_multimodel.py` `request()`: anthropic·openai·xai 세 형식의 `request_media_generation` 응답을 `chat_protocols.normalize` → `production_tool`로 실행해 같은 job을 받는다("Three provider envelopes use identical saved grant").
- `tests/test_execution_context.py` `test_unsubmitted_action_grant_and_stable_shot_are_discoverable_and_route_after_switch`: handoff의 `approval_handles[0].grant_id`로 `request_media_generation` → `accepted`.
- `07_Chat_Directed_Multimodel_Production_Spec.md:245`: request_media_generation = "계획 버전과 서버가 발급한 작업 ID → 허용되면 job ID".
지시대로 좁히지 않고 불변 테스트로 현재 노출을 고정했다. 좁힐지(plan D1 권장 "예전 경로도 좁힘")는 사용자 결정이 필요하다 — 좁히면 위 계약 테스트 2개가 의도적으로 바뀐다.

## requests_for_other_tracks

- 트랙 B(`general-chat-ui.js` toolLabels): 현재 파일에 이미 `get_generation_job:'생성 작업 상태 조회 · 승인 아님'`, `estimate_media_plan:'준비된 제작안 견적 합계 · 청구 아님'`이 있다. 이번 서버 동작에 맞춘 원하는 문구:
  - `get_generation_job`: `'작업 상태 조회 · 승인 아님'` (로컬 렌더·3D 정지 이미지 작업도 조회하므로 '생성'을 뺌)
  - `estimate_media_plan`: `'이 대화 준비 작업 견적 합계 · 청구 아님'`
- main(통합): 토큰 측정상 review/full_access 일반 대화 첫 회차가 변경 전부터 4096 입력 상한을 넘을 가능성이 높다. 실제 count(승인 필요) 또는 모드·질의별 노출 분리(PLAN §7) 결정 필요.
