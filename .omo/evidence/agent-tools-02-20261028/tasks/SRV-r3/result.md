# SRV-r3 결과 (SRV-r2 재작업: 한 turn 안 next_query 64KiB 초과 + minor 전부)

- 범위: 서버 `.py`와 `tests/*.py`. 시작 사본은 `start/`(서버 16개 + tests 전체)에 있습니다. `changes.diff`는 그 사본과 비교한 12개 파일입니다(서버 7, 테스트 5).
- 같은 시간에 다른 작업자(UI-r3로 보임)가 `tests/test_chat_receipts.py`(22:48)와 `tests/test_ui_r2_contracts.py`(22:47)를 고쳤습니다. 두 파일은 손대지 않았고 diff에도 넣지 않았습니다.
- 실제 모델·제공자·유료 호출, count_tokens, `.env`, 8765·57888 서버, 브라우저 자동화, 파일 삭제는 하지 않았습니다. 테스트 서버는 기존 fixture처럼 포트 0 루프백만 썼습니다. live 경로는 기존 합성 opener(`ProviderSocket`)만 썼습니다.

## 1. 이슈별 처리

### SERIOUS — 한 turn 안에서 next_query를 따라가면 64KiB를 넘어 outcome_unknown으로 잠김 → 고침 [검증됨]
- **재현**: critic probe 3개를 수정 전 코드로 다시 돌렸습니다.
  - estimate: 42,613 → 58,734 → **74,857B(상한 초과)**
  - scene-status: 39,280 → 51,653 → 64,028B
  - live: 세 번째 조회 뒤 `outcome_unknown`이 되고, 새 미리보기는 400
  - 결과가 critic 보고와 같았습니다.
- **수정: 예산을 쪽이 아니라 turn 단위로 잽니다.** `chat_general.py`
  - `:38` `BODY_CAP=65536`, `CONTINUATION_MARGIN=8192`, `CONTINUATION_LIMIT=57,344`
  - `:470` `create_preview(..., body_limit=)`: 이어쓰기 본문을 저장·예약하기 **전에** 잽니다. 측정은 `encode_body`와 같은 직렬화를 씁니다(`wire_bytes`, `:308`).
  - `:826` 도구 결과를 넣은 이어쓰기가 57,344B를 넘으면, 그 결과 대신 `budget_notice`(`:313`)를 모델에게 보냅니다.
    - 담는 값: `status=context_budget_exhausted`, `code=CONTEXT_BUDGET_EXHAUSTED`, `tool`, `tool_status`, `saved_ids`, `result_included=false`, `body_bytes_with_result`(실측), `body_limit_bytes`, `bytes_left`, `next_query`(같은 조회어, 새 turn용), `retry='new_turn'`, 안내문
    - `bytes_left`는 결과 문자열이 본문 안에서 차지하는 JSON 바이트를 빼서 계산한 정확한 값입니다.
    - 도구는 이미 실행됐고 전체 결과는 run 기록에 그대로 남습니다.
  - margin 8KiB는 다음 회차의 assistant 메시지와 안내문이 들어갈 자리입니다. 모델이 안내를 무시하고 계속 조회해도 매 회차가 같은 방식으로 막힙니다.
- **증명 테스트**: `tests/test_general_chat_body_cap.py`
  - `InTurnPagingBudgetTest`(`:295`): 한 turn 안에서 next_query를 MAX_ROUNDS(4)까지 따라갑니다. 매 회차 사람이 이어쓰기를 승인합니다.

    | 테스트 | 이어쓰기 본문 B | 결과 |
    |---|---|---|
    | estimate 쪽(`:320`) | 42,607 / 43,573(안내) / 44,539(안내) | 끝 `limit_reached` |
    | scene-status 쪽(`:334`) | 39,405 / 51,965 / 52,912(안내) | 끝 `limit_reached` |
    | 일반 조회 + scene-status(`:338`) | 37,592 / 50,080 / 51,027(안내) | 끝 `limit_reached` |
    | live, critic probe_live 순서(`:350`) | 37,598 / 50,086 / 51,033 | 전송 8건, 다음 새 미리보기 200 |

    - 모든 테스트가 확인하는 것: turn이 한 번도 `outcome_unknown`이 아님, 모든 본문이 encode_body 기준 65,536B 미만(`wire()`는 초과하면 예외), `CONTEXT_BUDGET_EXHAUSTED` 발생
    - estimate는 추가로 확인합니다: 안내의 next_query를 새 turn에서 넘기면 그 쪽(6건)을 57,344B 안에서 받습니다.
  - 근거 파일: `evidence/in-turn-*.json`
- **수정 전 코드로 돌린 결과**: `old_code_check.py` → `old_code_check.log`. 서버 모듈만 start/ 사본으로 바꿔 같은 테스트를 돌리면 InTurn 4건이 실패·오류입니다(본문 초과 시 `wire()` 예외 포함).

### 계약 항목 1 — 전송 직전 상한 초과 거절을 회복 가능하게 → 고침 [검증됨]
- 안내문으로 바꿔도 상한을 넘는 경우를 처리합니다(`chat_general.py:834`).
  - 다음 회차 미리보기를 만들지 않습니다. 예약도, 전송도 하지 않습니다.
  - turn은 `limit_reached`로 끝납니다. 이 상태는 새 요청을 막지 않는 기존 상태입니다.
  - `context_budget{code, body_bytes, limit_bytes, next_query}`와 오류 문구(`CONTEXT_BUDGET_EXHAUSTED` 포함)를 남깁니다.
  - `round`는 마지막으로 보낸 회차로 되돌립니다.
- 테스트 `test_over_cap_continuation_ends_the_turn_recoverably_with_zero_provider_writes`(`body_cap:209`, live 합성 소켓):
  - 시나리오: 2회차 응답이 긴 답변 글(한글 4,700자) + 조회입니다. 안내문을 넣은 본문도 67,045B입니다.
  - **공급자 쓰기**: 3회차분 0건. 소켓 요청은 정확히 (count, message)×3입니다.
  - 미리보기 행 3개(첫 요청 + 이어쓰기 2)이고, 거절된 회차의 행은 없습니다.
  - 예약 3건이 모두 `estimated`이고 `reserved`·`uncertain`은 0건입니다.
  - 새 `general_chat_preview`는 HTTP 200이고, 미리보기는 아무것도 보내지 않습니다(요청 수 6 유지).
  - 근거: `evidence/over-cap-recoverable-end.json`
- **"예약 해제"에 대한 근거**:
  - 원장의 `release`는 `reserved` 상태에서만 됩니다(`ledger.py:302-303`, "미확정·정산된 예약은 취소만으로 해제할 수 없습니다").
  - 거절된 회차의 예약은 사람이 이어쓰기를 승인할 때(`decide`) 생깁니다. 그래서 이 시점에는 예약 자체가 없습니다.
  - 직전 회차의 예약은 받은 응답의 사용량으로 이미 `estimated`입니다. 이를 해제하면 실제 사용 기록을 지우게 되므로 건드리지 않았습니다.
  - 결과적으로 남은 hold는 0입니다. 새 원장 경로는 만들지 않았습니다.
- 바뀐 기존 기대값: SRV-r2의 `test_old_single_page_cap_is_rejected_before_send_and_the_turn_state_is_recorded`
  - 이 테스트는 `outcome_unknown`과 새 미리보기 400을 **고정**하고 있었습니다.
  - 지금은 32장면 한 쪽(71,259B)이 안내문으로 바뀌어 turn이 `awaiting_continuation_approval`로 이어집니다. 인코더 거절은 0건이고 본문은 27,793B입니다.
  - 테스트 이름을 `test_old_single_page_result_is_withheld_with_a_budget_notice_and_the_turn_continues`(`:178`)로 바꿨습니다(§2).

### 계약 항목 2 — 일반 search_project_context 목록(shots·actions·plans) 상한 → 고침 [검증됨]
- `production_context.py:224-236`, `:313-321`
  - `CONTEXT_LIST_LIMIT=8`. `read(..., bounded=True)`는 search_project_context 경로(`local_creation_tools.py:375`)만 씁니다.
  - 목록이 잘리면 `list_pages.{shots,actions,plans}={total, offset, limit, not_shown, truncated, next_query}`를 붙입니다.
  - 다음 쪽 조회는 `context-shots|context-actions|context-plans offset=N`이고, 그 목록과 `list_pages`, `note`만 돌려줍니다.
- **잘린 목록이 없으면 `list_pages`를 붙이지 않습니다.**
  - 그래서 잘리지 않은 결과는 handoff(무제한 read)와 같습니다. 기존 단언 15개(`test_music_input_context`, `test_execution_context`의 `lookup == handoff`)는 그대로 둡니다.
  - 처음에는 항상 붙였는데, 그 15개 단언이 깨져서 이렇게 바꿨습니다. 단언은 고치지 않았습니다.
  - legacy handoff(`chat_runtime.py:225`, `app.py:811`)는 무제한 그대로입니다.
- actions 조회에 `ORDER BY rowid`를 넣어 쪽 순서를 고정했습니다(`:297`).
- 실측(32장면 fixture): 일반 조회 본문 45,618 → **37,592B**. shots가 10,272 → 2,568B로 줄었습니다(critic probe_plain 재실행).
- 테스트 `BoundedContextListsTest`(`body_cap:416`):
  - shots 20+개와 plans 12개는 쪽마다 57,344B 안에 들고, 모든 항목을 중복 없이 한 번씩 봅니다.
  - 쪽 결과의 키는 정확히 {목록, list_pages, note}입니다.
  - actions 20건은 rowid 순서로 한 번씩 나옵니다.

### 계약 항목 3 — 값이 다른 대기 선호 후보의 개수 상한 → 고침 [검증됨]
- `local_creation_tools.py:340` `PREFERENCE_PENDING_LIMIT=10`(되돌리기 쉬운 기본값)
  - (ip, 작품, category)별로 `proposed` 후보가 10건이면 거절합니다: `status=blocked, code=PREFERENCE_CANDIDATE_LIMIT, retryable=False, open_candidates, limit` + 안내(`:361`)
  - 같은 인수의 반복은 먼저 기존 후보 재사용으로 처리합니다.
  - 사람이 만든 후보도 개수에 들어갑니다.
- 테스트 `test_open_candidates_per_category_are_capped_with_a_structured_refusal`(`scene_pref:401`)이 확인하는 것:
  - 10건까지 저장되고 11번째는 거절되며, 저장 상태는 바뀌지 않습니다.
  - 같은 인수는 여전히 duplicate로 재사용됩니다.
  - 다른 category는 영향이 없습니다.
  - 사람이 1건을 거절하면 다시 저장할 수 있습니다.

### 계약 항목 4 — 장면당 11번째 이후 대기 제안 → 바꾸지 않음(lead 결정)
- 모델이 더 받아 오는 경로는 만들지 않았습니다. 모델은 승인하지 않고, 검토는 사람이 Scene Studio에서 합니다.
- `pending_total`, `pending_truncated`, note 문구로 생략 사실은 그대로 알립니다. 근거 테스트: `test_exactly_ten_pending_is_not_truncated`, `scene-status-worst-case` 테스트(장면당 10건, `pending_total=10`).

### MINOR 1 — OpenAI strict 정의의 minLength/maxLength → 고침 [검증됨]
- `chat_models.py:77` `openai_wire_schema`: minLength·maxLength만 설명문 `Server-enforced constraints: {...}`로 옮깁니다. 하위 스키마까지 재귀로 처리하고 원본은 바꾸지 않습니다.
- `chat_protocols.py:111`: `tool_definitions('openai')`에 적용했습니다. 기존 `COMMAND_SCHEMA`의 길이 제한도 같이 옮겨집니다.
- 근거: OpenAI structured-outputs 문서의 문자열 지원 키는 pattern·format뿐입니다(critic WebFetch 인용, 이번에 다시 조회하지는 않음).
- 테스트:
  - `test_general_chat_media_d15.py:185`: OpenAI 정의에 min/maxLength가 **없고** 설명에 `"maxLength": 300`·`"minLength": 1`이 있음
  - `test_strict_wire_schema.py:35`: OpenAI 전 도구에 두 키가 없음, strict 유지, 원본 TOOLS 불변, 변환 결과를 정확히 비교
  - 두 테스트 모두 수정 전 코드에서 실패합니다.
- 바이트(SRV-r2 `measure_tools.py`, -B):

  | 대상 | 전 → 후 |
  |---|---|
  | OpenAI 전체 정의 | 18,149 → **19,138B (+989)** |
  | Anthropic review·full_access | 20,265 → 20,265B |
  | read_only | 1,339 → 1,339B |

- xAI 정의(같은 function 형식, strict=True)는 계약 범위 밖이라 그대로입니다(§4).

### MINOR 2 — 중복 결과의 출처·상태 오표시 → 고침 [검증됨]
- 장면 제안:
  - `scene_project.py:402`: 재사용할 때 저장된 `origin`을 돌려줍니다.
  - `local_creation_tools.py:333`: 결과의 `status`를 저장된 값(proposed/held)으로 내고, 출처도 저장된 origin으로 냅니다.
- 선호 후보: `:357`에서 저장된 `same['origin']`을 냅니다.
- 테스트:
  - `test_duplicate_reports_the_stored_proposal_origin_and_held_status`(`scene_pref:157`): review·medium으로 만든 제안을 사람이 보류하고, full_access·high에서 같은 인수로 다시 부릅니다. `status='held'`이고, 출처는 첫 호출의 run·call·review·medium이며, 저장된 origin과 같습니다.
  - `test_duplicate_candidate_reports_the_stored_origin`(`:391`)
  - 둘 다 수정 전 코드에서 실패합니다.

### MINOR 3 — 쪽 안정성 → 고침 [검증됨]
- estimate:
  - `fal_dispatch.py:81`에 `ORDER BY rowid`를 넣었습니다.
  - `test_action_prepared_between_estimate_pages_lands_on_a_later_page`(`body_cap:398`): 쪽 사이에 작업 1건을 준비하면 21건이 중복 없이 나오고, 새 작업은 마지막에 옵니다.
  - **이 테스트는 수정 전 코드에서도 통과합니다.** SQLite의 순서 없는 스캔이 이 fixture에서 우연히 rowid 순이었기 때문입니다. ORDER BY는 그 순서를 보장으로 바꾼 것이고, 관측 가능한 차이를 증명한 것은 아닙니다.
- scene-status:
  - offset 대신 커서를 씁니다: `scene-status before=<scene_id>`(`production_context.py:242`).
  - 쪽 사이에 장면이 추가돼도 뒤쪽 쪽은 밀리지 않고, 새 장면은 최신 쪽에만 나옵니다.
  - 커서 장면이 없으면 빈 쪽, `cursor_found=false`, `next_query=null`을 돌려주고, note에 "scene-status로 다시 시작"을 적었습니다.
  - `test_scene_saved_between_pages_does_not_shift_the_cursor`(`:376`). 수정 전 코드에서 실패합니다.
- **한계**: estimate는 여전히 offset입니다. 쪽 사이에 사람이 작업을 보류·거절하면 목록이 줄어 밀릴 수 있습니다(합계·제외 건수는 매 쪽 전체 기준). §4에 적었습니다.

### MINOR 4 — 설정 불변 변이: 모션 변이를 per-tool 루프에서만, 개수 재현 → 고침 [검증됨]
- `mutants.py`(SRV-r3):
  - 모든 설정 쓰기 변이를 `build_fixture`가 끝난 뒤(per-tool 루프)에만 켭니다.
  - 각 경우를 한 프로세스에서 3회 돌려, 관측한 실패 수 집합을 기록합니다.
  - 스크립트 첫 줄에서 `sys.dont_write_bytecode=True`로 바이트코드를 쓰지 않게 했습니다.
- 결과 `mutants.log`:
  - 대조군 PASS
  - 설정 변이 8/8 KILLED. `propose_motion_scene → model_settings`·`→ agent_settings` 둘 다 **`self.assertEqual(settings_state(self.store), before)`**에서 잡힙니다.
  - 매트릭스 3/3 KILLED
- **재현성**: 새 프로세스에서 다시 돌린 `mutants-run2.log`가 `mutants.log`와 완전히 같습니다(diff 없음).
  - `propose_memory_update → model_settings`는 6회 모두 failures=2입니다.
  - SRV-r2 로그의 4는 재현되지 않았습니다. 원인은 [미확인]입니다.

### MINOR 5 — 바이트코드 쓰기 → 원인 찾고 막음 (삭제 안 함)
- **원인 [추정, 시각 근거 있음]**: `tests/test_general_chat_activation.py:161`의 CLI 하위 프로세스입니다.
  - `env={'PATH': ...}`로 환경을 비우고 -B 없이 `app.py`를 실행합니다. 그래서 상위의 `PYTHONDONTWRITEBYTECODE`가 전달되지 않습니다.
  - 이 프로세스는 내 실행에서도 소스가 바뀐 모듈의 .pyc를 썼습니다.

    | 시각 | 쓰인 .pyc | 그 시점 내 작업 |
    |---|---|---|
    | 22:55:17 | chat_general·chat_models·chat_protocols·scene_project | activation 포함 관련 모듈 실행 |
    | 22:59:20 | production_context | 같은 실행 |

  - SRV-r2의 22:16:50 쓰기도 같은 원인으로 봅니다(그때 바뀐 모듈과 정확히 일치).
- **수정**: 그 하위 프로세스에 `-B`와 `PYTHONDONTWRITEBYTECODE=1`을 줬습니다(`test_general_chat_activation.py:162`). 단언은 그대로이고 모듈 22개 테스트가 OK입니다.
  - 다른 python 하위 프로세스(`test_media_tail`, `test_scene_contract`, `test_scene_cli`, `test_production_boundary`)는 env를 물려받거나 -B를 이미 줍니다.
  - `test_contract_counterexamples`는 실행 목록에서 뺐습니다.
- **삭제하지 않음**: .pyc 5개(22:55·22:59)와 SRV-r2 때 것은 지우지 않았습니다(사용자 허용 필요).
- **[미확인]**: `__pycache__/image_recovery·image_pipeline·provider_billing·runway_provider·generation_queue` .pyc와 `tests/__pycache__`의 일부 파일은 23:19~23:29 시각으로 찍혀 있습니다.
  - 이 시각은 내 마지막 명령 시각(23:13)보다 뒤라 미래 시각입니다.
  - 내 전체 실행은 23:08:19에 끝났습니다.
  - 쓴 주체는 확인하지 못했습니다.

### MINOR 6 — critic이 남긴 미해결 목록
- 이어쓰기 상한 잠김: 위 SERIOUS·계약 1로 고침
- 일반 목록: 계약 2로 고침
- 장면당 11번째 이후: 계약 4(그대로, 이유 있음)
- 값이 다른 후보: 계약 3으로 고침
- locked_fields: **고치지 않음**. lead 결정에 따라 범위 밖이며 사용자 결정 결함입니다(§5).

## 2. 의도적으로 바꾼 기존 기대값 (단언 삭제·약화 없음)

| 파일:위치 | 바뀐 점 | 이유 |
|---|---|---|
| `test_general_chat_body_cap.py` 예전 `test_old_single_page_cap_is_rejected_before_send...` → `:178` 새 이름 | `outcome_unknown`·새 미리보기 400 단언 → 인코더 거절 0, `awaiting_continuation_approval`, 안내문 필드, 본문 ≤ 57,344, 전체 결과는 run에 저장됨 | 예전 기대값이 lead가 금지한 잠김을 고정하고 있었음 |
| 같은 파일 `:91` worst-case next_query | `'scene-status offset=8'` → `'scene-status before=<이 쪽에서 가장 오래된 scene_id>'` | 쪽 안정성 minor(커서) |
| `test_general_chat_media_d15.py:185` | OpenAI 정의에 min/maxLength가 **있다** → **없고** 설명문에 있다 | OpenAI strict minor(지시에 명시된 수정) |
| `test_general_chat_activation.py:162` | 하위 프로세스에 `-B`·`PYTHONDONTWRITEBYTECODE=1` 추가(단언 변화 없음) | 바이트코드 쓰기 minor |

`supported_context_queries`의 scene-status 설명 문구는 "offset=N" → "its next_query"로 바꿨습니다. 쿼리 목록(`['work-status','scene-status']`) 단언은 그대로 통과합니다.

## 3. 테스트 명령과 결과
모두 `cd /Users/leesungmin/Desktop/Loretune`, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests /opt/homebrew/opt/python@3.15/bin/python3.15 -B`로 실행했습니다.

- **전체**: SRV-r2와 같은 154개 모듈(`full-modules.txt`, `test_contract_counterexamples` 제외)
  - 명령: `-m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/SRV-r3/full-modules.txt)`
  - 로그: `full-tests.log`
  - 결과 끝부분:
    ```
    Ran 1038 tests in 439.479s
    OK (skipped=19)
    rc=0
    ```
  - `grep -c Warning full-tests.log` → `0`
  - 이 전체 실행 뒤에 `test_general_chat_activation.py`의 하위 프로세스 인자(§1 MINOR 5) 한 줄만 바꿨습니다. 그 모듈은 다시 돌려 `Ran 22 tests ... OK`입니다.
- **변경 모듈**:

  | 모듈 | 결과 |
  |---|---|
  | `tests.test_general_chat_body_cap` | `Ran 14 tests ... OK` |
  | `tests.test_general_chat_scene_preference_tools` | `Ran 28 tests ... OK` |
  | `tests.test_strict_wire_schema tests.test_general_chat_media_d15 tests.test_chat_protocols` | `Ran 34 tests ... OK` |
  | 관련 16개 모듈 묶음 | `Ran 182 tests ... OK` |

- **변이**: `.omo/.../SRV-r3/mutants.py` → `mutants.log`, `mutants-run2.log`(동일)
- **수정 전 코드에서 새 테스트가 실패하는지**:
  - 명령: `.omo/.../SRV-r3/old_code_check.py <start/*.py 사본 폴더>` → `old_code_check.log`
  - 10개 항목 모두 실패·오류입니다. 단 StablePagesTest의 estimate 1건은 수정 전에도 통과합니다(§1 MINOR 3).
  - 사본 폴더는 scratchpad에 있습니다. `start/tests/`가 현재 tests 패키지를 가리지 않도록 서버 .py만 복사했습니다.
- **critic probe 재실행**(수정 후):
  - `probe_plain`: 37,592 → 50,080B
  - `probe_live`: 3회차까지 `awaiting_continuation_approval`
  - `probe_inturn` estimate: 42,607 / 43,573 / 44,539B, 끝 `limit_reached`
  - `probe_inturn` scene 쪽은 안내문을 받으면 `execution_targets` 키가 없어 probe 코드가 KeyError로 멈춥니다. 같은 경로는 `InTurnPagingBudgetTest`가 끝까지 확인합니다.
- **근거 재생성**: `SRV_R2_EVIDENCE=<SRV-r3>/evidence`를 주고 body_cap을 실행하면 `evidence/*.json`이 다시 만들어집니다.

## 4. 남은 빈칸
1. **margin 8KiB의 근거**: 다음 회차 응답(도구 호출 ~200B + 글)과 안내문(~1KB)이 들어갈 자리입니다.
   - 한 회차에 긴 글(약 7KB 이상)과 조회를 같이 내면 안내문도 못 들어갑니다. 그때는 위 회복 가능한 `limit_reached`로 끝납니다. 이 경우도 테스트로 확인했습니다.
   - margin 값은 조정할 수 있습니다.
2. **새 turn의 첫 요청**이 상한을 넘는 경우는 이번 변경 대상이 아닙니다.
   - live에서는 미리보기 생성 시 encode_body가 거절해 400이 되고, 저장되는 것은 없습니다(기존 동작).
   - contract-fake에서는 첫 요청 크기를 검사하지 않습니다.
3. **아직 상한 없이 남은 일반 조회 항목**: `timeline.clips`, `server_receipts`, `context`(run 스냅샷), `sources`
   - 계약은 shots·actions·plans만 지정했습니다.
   - 커져도 이제는 turn 예산 안내로 막히고 잠기지 않습니다.
4. **estimate 쪽**: offset 방식이라 쪽 사이의 보류·거절 결정으로 밀릴 수 있습니다(§1 MINOR 3).
5. **xAI 정의**에도 min/maxLength가 그대로 남아 있습니다. xAI strict의 지원 여부는 [미확인]이고 계약 밖입니다.
6. **[추정] 토큰 수**: count_tokens가 금지라 본문 37~53KB가 `MAX_INPUT=16384` 토큰 안에 드는지는 실측하지 못했습니다.
7. **.pyc**: 22:55·22:59의 5개(내 실행)와 SRV-r2의 22:16:50 것이 남아 있습니다. 23:19~23:29 시각 파일의 주체는 [미확인]입니다.

## 5. 사용자 결정 사항
- **locked_fields 재검사**: 새 잠금 저장소가 필요해 범위 밖입니다(lead 결정). 결함으로 남아 있습니다.
- **선호 후보 상한 10건과 범위**: (ip·작품·속성별, 사람이 만든 후보 포함). 이 값과 범위를 그대로 둘지 정해 주세요.
- **이어쓰기 margin 8KiB와 목록 쪽 크기 8**: 기본값 그대로 둘지 정해 주세요.
- **stray .pyc 삭제 여부**

## 6. 산출물
- `changes.diff`(12개 파일), `start/`
- `mutants.py`, `mutants.log`, `mutants-run2.log`
- `old_code_check.py`, `old_code_check.log`
- `full-modules.txt`, `full-tests.log`
- `evidence/`: `in-turn-estimate.json`, `in-turn-scene-status.json`, `in-turn-plain-then-scene-status.json`, `in-turn-live.json`, `over-cap-recoverable-end.json`, `over-cap-live-rejection.json`(안내문 대체 기록), `scene-status-worst-case-body.json`, `estimate-worst-case-body.json`
