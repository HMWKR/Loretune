# A2a-media-d15 결과 (Wave 2, 트랙 A 서버)

작성 2026-10-28. 외부·유료·모델 호출 0, count_tokens 0, `.env` 미접촉, 8765/57888 미기동, 브라우저 미사용, 파일 삭제 0.
허용된 외부 조회는 fal.ai 공개 모델 페이지 WebFetch/WebSearch뿐이다(D19).
편집 전 사본은 `start/`에 있다(쓰기 범위 12개 모듈 + `tests/*.py`, 작업 시작 시점). `fal_models.py`·`media_creator.py`는 시작 시점에 `before/`와 같았다.
diff: `changes.diff`(start 대비, 바꾼 파일만). 바꾸지 않은 쓰기 범위 파일: `model_selection.py`, `chat_runtime.py`, `chat_models.py`, `production_context.py`.

## 1. 항목별 조치

### 1) S4 — `prepare_video_action` 일반 대화 노출 [검증됨]
- `chat_general.py:41`: `ALLOWED_TOOLS`에 `prepare_video_action`을 추가했다. 도구 스키마는 이미 있었고(`production_tools.py:16`), `model_reason`만 추가했다(2번 항목).
- D15: 프로젝트 선택과 다른 `model_id`는 거절하지 않고 *제안*으로 저장한다(`fal_dispatch.py:45-50`). 프로젝트 모델 설정은 바꾸지 않는다.
- 권한: read_only는 준비 불가(기존 `agent_preferences.authorize`, READ_TOOLS 밖). review·full_access는 준비 가능. 승인·실행은 기존 사람 경로 그대로다.
- 결과에 `model_state`(카탈로그 상태, 예: `integration_blocked`)를 넣었다(`fal_dispatch.py:76`). 차단 상태 모델의 제안도 승인·실행 가능으로 표시되지 않는다(카드 `approval='required'`, `can_execute=False`).
- 증명(`tests/test_general_chat_media_d15.py`)
  - `VideoD15Test.test_blocked_different_video_model_is_saved_as_proposal_only`: 프로젝트 영상 모델은 kling 2.5 turbo이고, 모델은 차단 상태인 kling 2.6 pro를 제안한다. 결과는 `proposed`, `differs_from_project=True`, `model_state='integration_blocked'`다. 설정은 그대로이고 예약 0, 전송 0, grant·job 증가 0이다.
  - `GeneralChatImageD15Test.test_different_model_is_a_proposal_and_never_changes_project_settings`: 이미지에서 flux-pro를 제안해도 `model_settings`와 `agent_settings`가 전후 동일하다. `assert_no_media_execution`(project 예약 0, grant·job 0, 제출 0)도 통과한다.
  - `DirectToolInvariantTest.test_read_only_cannot_prepare_video`: `AGENT_READ_ONLY`, action 0. 이미지 쪽 read_only 거절은 기존 테스트에 있다.

### 2) S15 — model_reason · actor · provenance · 프로젝트 선택 비교 [검증됨]
- **스키마**: `production_tools.py:15-16`에서 두 준비 도구에 필수 `model_reason:str`을 추가했다. `production_tools.py:53`에서 길이를 1..300자로 제한한다. 빈 문자열·공백만 있는 값은 기존 공통 검사에서 거절된다.
- **저장**: `fal_dispatch.proposal_record`(`fal_dispatch.py:180`)가 action `options.proposal`에 다음을 동결한다. action hash에 포함된다.
  - `actor`, `model_reason`(원문 그대로), `provenance`, `project_selection`, `differs_from_project`, `unit_price`
  - agent는 이유가 필수이고 provenance 6키가 정확해야 한다. local-owner는 이유가 없고 provenance 값은 모두 null이다.
- **provenance**는 서버가 만든다(`production_tools.py:108-111`). 모델 인수로는 바꿀 수 없다(스키마 키 고정).
  - `engine`=run.engine
  - `chat_model`=run.provider_model
  - `permission_mode`=호출 시점 `effective_mode`
  - `effort`=run에 동결된 agent_settings.effort
  - `run`, `call`
- **effort 일치**: 일반 대화 run의 agent_settings는 turn binding에서 복사된다(`chat_general.decide`). 이 값으로 `output_config.effort`가 만들어진다. 테스트는 review/medium과 full_access/high 두 경우에서 기록 effort와 저장된 preview `message_body.output_config.effort`가 같음을 단언한다.
- **사람 HTTP 경로**: `media_prepare`는 바꾸지 않았다. 기본값 `actor='local-owner'`로 기록된다. 라벨은 '프로젝트에서 사용자가 선택한 모델'이고, 사용자가 다른 모델을 지정한 경우에는 '사용자가 준비 시 지정한 모델'이다.
- **표시 라벨**: agent의 이유는 `model_reason_label='모델이 제시한 이유(검증 안 됨)'`로 표시한다.
- **예전 action**: proposal이 없으면 `record='출처 기록 없음(변경 전 준비)'`로 표시하고 출처 필드는 null이다. 단가는 현재 카탈로그로 계산해 보여 준다(`fal_dispatch.py:193-203`).

### 3) D19 — fal 공개 단가 [검증됨: 공개 페이지 / 일부 미확정]
조회 시각 2026-10-28T09:28:18Z(UTC), revision `fal-public-model-pages-20261028`, kind `documented-estimate`(`fal_models.py:17-34`). 페이지 원문:

| 모델 | 원문 | 기록 | 출처 |
|---|---|---|---|
| fal-flux-schnell | "Your request will cost $0.003 per megapixel." / "Images are billed by rounding up to the nearest megapixel." | 0.003 USD / megapixel | https://fal.ai/models/fal-ai/flux/schnell |
| fal-flux-pro-1-1 | "Your request will cost $0.04 per megapixel." / 같은 올림 규칙 | 0.04 USD / megapixel | https://fal.ai/models/fal-ai/flux-pro/v1.1 |
| fal-kling-2-6-pro | "Videos generated without audio cost $0.07 per second." (audio는 항상 false) | 0.07 USD / second | https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video |
| fal-kling-2-5-turbo | "For 5s video your request will cost $0.35. For every additional second you will be charged $0.07." | 0.07 USD / second(허용 길이 5·10초에서 동일) | https://fal.ai/models/fal-ai/kling-video/v2.5-turbo/pro/image-to-video |

- **장당 금액 계산**(`fal_models.price_view`, `fal_models.py:40-60`): 식은 `올림(w×h px ÷ 1MP) × 단가`다.
  - 16:9·9:16(1024×576=589,824px)은 1MP 정의가 10^6이든 2^20이든 1MP로 같다. schnell 0.003, pro 0.04다.
  - 1:1(1024×1024=1,048,576px)은 정의에 따라 1MP 또는 2MP다. fal 공개 페이지·pricing 페이지에는 메가픽셀 정의가 없다(WebFetch로 확인). 그래서 `expected_total=None`으로 두고, 두 후보(0.003/0.006, 0.04/0.08)를 이유와 함께 표시한다. 값을 만들어 내지 않았다.
  - 검색 요약에는 flux/dev 페이지에 "1024×1024 = 1MP"라는 예가 있다고 나왔다. 그러나 실제 페이지 WebFetch에서는 그 문장을 찾지 못해 근거로 쓰지 않았다 [미확인].
- **견적과 단가×수량 비교**: 견적 총액 ≠ 단가×수량이면 `matches_quote=False`와 `mismatch` 문구를 붙이고 둘 다 보여 준다. 자동으로 고르지 않는다. 테스트 fixture 견적(0.01)은 문서 단가와 달라서 실제로 mismatch로 표시된다.
- **노출 위치**(모두 같은 `proposal_view`): prepare 결과, `estimate_media_plan` 항목, `get_generation_job.job.pricing`(`app.py:820-822`에서 job의 action을 조회), `media_actions` 카드(`media_creator.py:69`), `fal_dispatch.public_actions`, `get_model_capabilities`의 모델별 `unit_price`(미디어)·`token_price`(대화, `production_tools.py:28-31`). read_only에서도 조회할 수 있다.
- **테스트**
  - quote 입력 변경(5→10초, 프롬프트 변경)이면 예전 quote를 거절하고(INVALID_MEDIA_INPUT, action 0), 새 10초 quote만 수락한다. 이때 예전 5초 입력은 거절된다.
  - 단가×수량 일치·불일치, 1:1 미확정, 카탈로그 4개 모델 모두 기록이 있음을 확인한다(`UnitPriceTest`, `VideoD15Test.test_changed_quote_input_...`).

### 4) D20 — MAX_INPUT 4096 → 16384 [검증됨: 계산 / 추정: 바이트]
- `chat_general.py:28-29`: `MAX_INPUT = 16384`. 사용자 결정은 "상한만 올리기"이고, 16384는 lead의 가정이다.
- `chat_general.py:32`: `CONVERSATION_CAP_MICRO = 400000`. 이 리터럴을 상수로 바꿨을 뿐 값은 같다(`:437`). 64KiB 전송 상한(65536)은 바꾸지 않았다.
- **최악 회차 예약 `chat_models.cost(spec, MAX_INPUT, MAX_OUTPUT)`, 올림 micro-USD**:

| 대화 모델 | 변경 전(4096/4096) | 400000 안 회차 | 변경 후(16384/4096) | 400000 안 회차 |
|---|---|---|---|---|
| anthropic-haiku-5-5 | 2458 | 162 | 3687 | 108 |
| openai-gpt-6-luna | 2458 | 162 | 3687 | 108 |
| xai-grok-4-7 | 32768 | 12 | 57344 | 6 |

  - 일반 대화 경로는 Claude(haiku)만 지원한다. 16384는 long-context 문턱(100000) 미만이라 표준 단가가 적용된다.
  - `agent_preferences.reservation()`(`agent_preferences.py:113`)으로 설정 요약(`public().capabilities.models[*].reservation`)과 `get_agent_settings`에 노출했다.
- **64KiB와의 관계** [추정, 토큰 실측 없음]
  - review 첫 본문(도구 정의 포함)은 18273B이므로 이력에 남는 바이트는 약 47KB다.
  - 이전 관측 비율 1.97~2.31 B/token(한국어 위주)이면 16384토큰은 약 32~38KB다. 이 경우 64KiB 안에 들어가고 토큰 상한이 먼저 걸린다.
  - 영어·ASCII 위주(~4 B/token)면 64KiB가 약 16K 토큰에 해당한다. 도구 정의까지 합치면 **바이트 상한(65536)이 16384토큰보다 먼저 걸릴 수 있다.** 이때 실제 구속 한도는 `BoundedMessagesTransport(max_request_bytes=65536)`이고, 초과하면 전송 전에 거절된다(기존 `test_chat_preflight` 경계 테스트 65529/65536/65537 유지).
- **의도된 테스트 기대 변경**(이유: D20, 최악 예약 2458→3687)
  - `tests/test_chat_live_contract.py:207`: `total=2458`→`3687`. "정확히 1회차분 상한" 의미는 유지한다.
  - `tests/test_general_chat_activation.py:362`: 예산 `0.003`→`0.004`. "1회차만 예약 가능, 2회차 불가" 의미는 유지한다.
  - legacy 경로(`chat_runtime`, 자체 4096 기본값)의 2458 단언들은 변경 대상이 아니라 그대로다.

### 5) D21 + S9 — `get_agent_settings` [검증됨]
- `production_tools.py:19` 스키마는 `{}`(0 허용 키)다. `:92`가 분기다. `agent_preferences.py:15` READ_TOOLS에 넣었고(read_only 포함), `chat_general.py:41` ALLOWED_TOOLS와 `chat_protocols.py:17` 설명에도 추가했다.
- legacy 기본 목록에는 넣지 않았다. legacy는 자체 한도로 예약하므로, 이 도구의 예약 수치가 legacy와 맞지 않기 때문이다.
- 결과(`agent_preferences.settings_summary`, `:122`):
  - `chat_model`: id·model·provider, `selection_reason='사용자가 선택한 모델'`, 그리고 `price`. price에는 input/output rate, unit `USD per 1M tokens`, long-context 문턱과 단가, source, revision이 들어간다.
  - `effort`(동결값)
  - `permission`: `saved`(현재 저장값), `frozen`(이 응답에 고정된 값), `effective`
  - `reservation`: max_input/output, worst_per_round_micro, conversation_cap_micro, worst_case_rounds_within_cap
  - `agent_can_change=False`
- 불변 테스트 `DirectToolInvariantTest.test_settings_unchanged_after_every_tool_in_every_mode`: TOOLS 15개 전부를 read_only/review/full_access에서 각각 직접 실행한다. 매번 `model_settings`와 대화별 `agent_settings`·`agent_settings_history`가 전후 동일함을 단언한다.
- 변이 확인(`mutants.log`): get_agent_settings가 model_settings revision을 올리게 하면 이 테스트가 FAIL한다(failures=3).

### 6) 이월 항목 [검증됨]
- `tests/test_chat_preflight.py:38-40`: 기대 본문을 `limits()`가 아니라 **정적 리터럴 13개 목록**으로 거르도록 바꿨다(자기참조 제거).
- 같은 이유로 `tests/test_general_chat_tool_invariants.py:39-44`의 legacy 단언도 `TOOLS` 파생에서 정적 목록으로 바꿨다. TOOLS에 `get_agent_settings`가 추가되어 파생식은 더 이상 legacy 목록과 같지 않다.
- 설명 절 복원(`chat_protocols.py:9-10`): 'scoped snapshot, not semantic search.', 'not proof of a live connection.'. prepare 두 도구에는 'model_reason is shown unverified.'를 추가했다.

### 의도된 기존 테스트 변경 전체 (단언 약화·삭제 0)
| 파일 | 변경 | 이유 |
|---|---|---|
| tests/test_general_chat_media_preparation.py:65 | `arguments()`에 model_reason | S15 필수 인수 |
| tests/test_general_chat_tool_invariants.py:39-44, :110 | legacy 정적 목록 / 영상 인수에 model_reason | 이월 6 / S15 |
| tests/test_execution_context.py:21, tests/test_fal_multimodel.py:106 | 준비 인수에 model_reason | S15 |
| tests/test_chat_protocols.py:62-63 | 도구 수 14→15, 이름 집합에 get_agent_settings | S9 |
| tests/test_agent_preferences.py:126-127, :178 | read_only tool_scope·message tools에 get_agent_settings | S9(read_only 허용 읽기 도구) |
| tests/test_chat_preflight.py:38-40 | 정적 기대 목록 | 이월 6 |
| tests/test_chat_live_contract.py:207, tests/test_general_chat_activation.py:362 | 3687 / 0.004 | D20 |

## 2. 도구 정의 바이트 (모드별, 전후) — `measure-start.json` → `measure-after.json`
측정 스크립트는 `measure_token_budget.py`(A1 r2와 동일)이고, 단위는 UTF-8 JSON 바이트다. 토큰 수가 아니다.

| 모드 | 도구 수 | tools 바이트 | 첫 요청 본문 바이트 | 설명 바이트 |
|---|---|---|---|---|
| review·full_access | 10 → 12 | 10497 → 11621 (+1124) | 17149 → 18273 | 498 → 791 |
| read_only | 4 → 5 | 1010 → 1339 (+329) | 7662 → 7991 | 189 → 350 |

도구별 증가:

| 도구 | 바이트 | 원인 |
|---|---|---|
| search_project_context | 256→294 | 설명 절 복원 |
| get_model_capabilities | 233→287 | 설명 절 복원 |
| prepare_image_action | 431→517 | model_reason + 설명 |
| prepare_video_action | 신규 707 | |
| get_agent_settings | 신규 235 | |

대표 결과 크기(`result-sizes.json`):

| 결과 | 바이트 |
|---|---|
| prepare_image_action | 1715 |
| estimate 1항목 | 1841 |
| get_agent_settings | 869 |
| get_model_capabilities video / image | 1481 / 1300 |

이전 예산 판정: review 첫 본문 18273B는 /4 추정으로 약 4568토큰이다. 4096에서는 넘쳤지만 16384 안에는 든다 [추정].

## 3. D15 표시 표면 매트릭스 (서버 투영 기준)
| 표면 | 단가·종류·출처·revision·만료 | 이유·라벨 | provenance | 프로젝트 선택·차이 | 예전 action |
|---|---|---|---|---|---|
| prepare 결과(도구) | 표시 | 표시 | 표시 | 표시 | 해당 없음(새 action) |
| estimate_media_plan 항목 | 표시 | 표시 | 표시 | 표시 | '출처 기록 없음' |
| get_generation_job `job.pricing` | 표시(fal action job) | 표시 | 표시 | 표시 | '출처 기록 없음'; 로컬 렌더·rehearsal job은 `null`(fal action 아님, 의도적) |
| media_actions 카드(`/api/state`) | 표시 | 표시 | 표시 | 표시 | '출처 기록 없음' (테스트) |
| 재열기(Store 재생성) | 표시(동일 단언) | 표시 | 표시 | 표시 | — |
| fal_dispatch.public_actions | 표시 | 표시 | 표시 | 표시 | '출처 기록 없음' |
| get_model_capabilities | 모델별 단가(동결 아님, 현재 카탈로그) | 해당 없음 | 해당 없음 | 해당 없음 | — |
| get_agent_settings / 설정 요약 | 대화 모델 토큰 단가·예약 | '사용자가 선택한 모델' | effort·permission | — | — |
| **화면 렌더링(index.html 카드)** | **미구현 — B2(S16) 소유** | | | | |

권한 × 경로 테스트 커버리지:

| 경로 | read_only | review | full_access |
|---|---|---|---|
| 이미지·대화 | 거절(기존) | 기록 | 기록 |
| 이미지·사람 | — | 기록 | — |
| 영상·도구 | 거절 | 기록 | **미검증** |
| 영상·사람 | — | **미검증** | — |

## 4. 실행한 명령과 출력 꼬리
모두 `cd /Users/leesungmin/Desktop/Loretune`에서 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B`로 실행했다.

1. 신규 모듈: `PYTHONPATH=tests ... -m unittest tests.test_general_chat_media_d15`
   ```
   Ran 17 tests in 14.656s
   OK
   ```
2. 대상 8개 모듈(media_preparation, tool_invariants, estimate, preflight, chat_protocols, execution_context, fal_multimodel, job_query):
   ```
   Ran 62 tests in 26.054s
   OK
   ```
3. 관련 67개 모듈(`related-modules.txt` = A1 r2의 related 51 + extra 8 + 변경 심볼 grep + 신규):
   - 1차(`related-tests.run1.log`): `Ran 638 tests in 300.108s / FAILED (failures=4)`. 4개 모두 위 표의 의도된 기대값(D20 2건, S9 2건)이다.
   - 2차(`related-tests.log`): `Ran 638 tests in 298.728s / FAILED (failures=3)`.
     - test_agent_preferences 1건: 기대 목록 수정이 첫 시도에서 적용되지 않았다. 고친 뒤 모듈 단독 `Ran 18 tests ... OK`.
     - `test_general_chat_review_navigation.test_navigation_reference_and_async_focus_contracts`와 `test_scene_ui.SceneUIContractTest.test_drafts_approval_capability_and_pending_requests`: Node VM 오류 `TypeError: el(...).addEventListener is not a function`(general-chat-ui.js)와 scene-studio.js 오류. 두 JS 파일은 이 작업의 쓰기 범위 밖이고, 이 작업 도중 수정 시각이 바뀌었다(general-chat-ui.js 18:42, scene-studio.js 18:44, E1 병행 트랙 [추정]). 1차 실행(18:36 시작)에서는 두 테스트가 통과했다. 이 작업의 결함이 아니라 병행 편집 영향으로 판단한다 [추정 — 원인 파일 diff는 확인하지 않음].
   - 최종 실행(`related-tests.final.log`, 모든 수정 후): `Ran 638 tests in 300.836s / OK` (rc=0). 2차에서 실패한 UI 2건도 이번에는 통과했다. 병행 편집이 진행 중이던 시점의 일시 상태였던 것으로 보인다 [추정].
4. 변이 확인(`mutants.log`)

| 변이 | 결과(실행 1개) |
|---|---|
| 불변 테스트 기준선 | failures=0 |
| get_agent_settings가 설정 변경 | failures=3 |
| provenance 기준선 | failures=0 |
| differs 항상 False | failures=1 |
| 단가 불일치 숨김 | failures=2 |

## 5. 남은 빈칸
- **UI 표시(S16)**: 카드·대화 요약에 이 필드를 실제로 그리는 일은 B2 소유라 하지 않았다. 서버 투영까지만 했다.
- **미검증 조합**: 영상 full_access, 영상 사람 준비 경로의 D15 기록은 테스트하지 않았다(코드 경로는 이미지와 공유).
- **요청 중 권한 축소**: provenance permission_mode는 호출 시점 effective_mode를 쓴다(축소를 즉시 반영하는 기존 min 로직). 다만 이 시나리오의 전용 테스트는 없다.
- **견적 결과 크기**: `estimate_media_plan` 항목당 약 1.4KB가 늘었고 항목 수에는 상한이 없다. 준비 action이 많으면 이어쓰기 본문이 64KiB 쪽으로 커진다.
- **1:1 이미지 장당 단가**: fal 공개 문서에 메가픽셀 정의가 없어 미확정이다.
- **kling 2.5 turbo 단가**: "5초 $0.35 + 초당 $0.07"을 초당 0.07로 표현했다. 이는 이 앱이 허용하는 5·10초에서만 동일하다.
- **D20 실측**: 실제 토큰 수(count_tokens)는 측정하지 않았다(금지). 16384는 가정값이다.
- **legacy**: codex #1(legacy 실행 거절 종단 증명)은 이 작업 항목이 아니라 하지 않았다. legacy 기본 목록에 get_agent_settings를 넣지 않았다.
- **전체 회귀**: `discover` 전체는 실행하지 않았다(main 통합 단계 몫).

## 6. 사용자 결정이 필요한 사항
1. **1:1 이미지 메가픽셀 정의**: 10^6과 2^20 중 어느 것인지 fal 공개 문서로 확정되지 않는다. 그동안 1:1 이미지의 문서 기준 장당 금액은 '미확정(두 후보 표시)'로 둔다. 확정하려면 fal 문의나 유료 실측이 필요하다(별도 승인).
2. **MAX_INPUT 16384 확정**: 회차 최악 예약이 2458→3687 micro-USD(+50%)로 늘고, 400000 상한 안 최악 회차는 162→108이다. 영어 위주 이력에서는 64KiB 바이트 상한이 먼저 구속할 수 있다. 값 조정 여부를 정해야 한다.
3. **estimate 결과 크기 상한**: 준비된 항목이 많을 때 페이지 처리나 항목 수 상한을 둘지 정해야 한다.
