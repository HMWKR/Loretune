# SRV-r2 결과 (A2a-media-d15 · A2b-3d-pref-guards 재작업)

- 범위: 서버 `.py`와 `tests/*.py`. 시작 시점 사본은 `start/`에 있고, `changes.diff`는 그 사본과 비교한 12개 파일입니다(신규 1개 포함).
- 같은 시간에 다른 작업자가 `tests/test_budget_summary_ui.py`를 고치고 `tests/test_ui_r2_contracts.py`를 새로 만들었습니다(UI-r2로 보임). 두 파일은 diff에서 뺐고 손대지 않았습니다.
- 실제 모델·제공자 호출, 유료 호출, count_tokens, `.env` 읽기, 8765·57888 포트 서버, 브라우저는 쓰지 않았습니다.
- 테스트 서버는 기존 fixture처럼 포트 0(임의 루프백)으로만 띄웠습니다.

## 1. 이슈별 처리

### A2a serious 1 — 설정 불변 테스트가 사실상 빈 검사였던 문제 → 고침 [검증됨]
- **원인 두 가지**:
  - 도구 대부분이 인수 검증 단계에서 거절돼 본문까지 가지 않았습니다.
  - `settings_state()`가 브라우저 투영(`/api/state`)을 읽었습니다. 이 투영에는 `chat_sessions`가 없어서 에이전트 설정 비교가 항상 `{}`였습니다.
  - 두 번째 원인은 이번에 새로 확인한 결함입니다.
- **수정**:
  - `tests/test_general_chat_media_d15.py:39` `settings_state(store)`가 이제 SQLite에 저장된 상태를 읽습니다(`model_settings` + `chat_sessions[].agent_settings/agent_settings_history`).
  - `:407`에 새로 넣은 단언은 모드마다 저장된 에이전트 설정이 비어 있지 않고 현재 모드와 같은지 확인합니다.
- `DirectToolInvariantTest.build_fixture`(`:320`)가 마련하는 것:
  - 적용된 계획과 이미지·영상 어댑터, 승인된 테이크·시작 프레임, 승인된 타임라인(렌더 grant), 승인된 3D 장면
  - memory용 canon 출처(적용 계획의 context_hash를 새 canon에 다시 묶음)
  - 사람이 승인한 모션 버전과 미디어 grant, 생성 작업 한 행
- 인수는 호출 시점의 head로 만들고, 도구×모드마다 기대 (status, code)를 단언합니다(`expected()`).
  - 결과는 `evidence/invariant-outcomes.json`에 있습니다.
  - review: 17개 도구 모두 성공 경로입니다(succeeded/proposed/estimated/accepted).
  - full_access: `propose_timeline_changes`는 `applied_draft`입니다. `request_render`·`request_motion_render`·`request_media_generation`는 review에서 받은 같은 grant를 다시 쓰므로 `existing`이고, 이 경우 본문의 기존 접수 조회 분기까지 실행됩니다.
  - read_only: 쓰기 도구 12개는 `AGENT_READ_ONLY`, 읽기 도구 5개는 성공입니다.
- **변이 테스트**: `mutants.py` → `mutants.log`. 변이는 프로세스 안에서 `unittest.mock`으로 적용했고 소스 파일은 수정하지 않았습니다.
  - 변이 없는 대조군은 PASS입니다.
  - 쓰기 도구가 설정을 바꾸는 변이 7개는 모두 KILLED입니다(`propose_timeline_changes`→model/agent, `propose_memory_update`→agent/model, `propose_motion_scene`→model, `request_render`→agent, `prepare_video_action`→model).
  - `propose_motion_scene` 변이는 fixture 구성 중 HTTP 단계에서 먼저 실패했습니다. 설정 비교 단언이 잡은 것은 아닙니다.
- **문구 정정**: A2a result.md §5의 "15개 도구 전부를 세 권한에서 실행해도 설정이 그대로"는 실제로는 본문에 도달하지 않은 실행이었습니다. 올바른 문구는 다음과 같습니다(A2a result.md는 쓰기 범위 밖이라 여기에만 적습니다).
  > 17개 도구 × 3개 모드 51칸을 실행했습니다. review·full_access에서는 모든 도구가 성공 또는 재조회(existing) 경로를 거쳤고 read_only의 쓰기 도구는 권한에서 거절됐습니다. 저장된 model_settings와 대화별 agent_settings가 바뀌지 않음을 51칸 모두에서 비교했고, 쓰기 도구에 설정 변경을 넣은 변이 7개는 모두 실패로 잡혔습니다.

### A2a serious 2 — model_reason 1~300자 제한이 모델에게 보이지 않던 문제와 대화 잠김 → 고침 [검증됨]
- **모델에게 노출**:
  - `chat_protocols.py:7` `MODEL_REASON_SCHEMA=dict(type='string',minLength=1,maxLength=300)`를 이미지·영상 준비, `propose_scene_3d`, `propose_preference_rule` 4개 도구에 적용했습니다(`:100`, `:108`).
  - 두 준비 도구의 설명에는 `model_reason (1-300 chars)`를 넣었습니다(`:14-15`).
  - Anthropic strict 전송에서는 기존 `chat_models.anthropic_wire_schema`가 길이 제한을 설명문으로 옮깁니다(`Server-enforced constraints: {"maxLength": 300, "minLength": 1}`).
  - OpenAI 정의에는 min/maxLength가 그대로 남습니다. 이 저장소는 이미 `local_creation_tools.COMMAND_SCHEMA`에서 같은 방식을 씁니다.
- **바이트**(`evidence/tool-bytes.json`, `measure_tools.py`로 start/와 현재 코드를 비교):

  | 대상 | 전 → 후 |
  |---|---|
  | review·full_access 도구 정의 | 19,889 → 20,265B (+376) |
  | read_only | 1,339 → 1,339B |
  | OpenAI 전체 | 17,985 → 18,149B (+164) |

- **고칠 수 있는 결과로 돌림**: 기존 경로를 찾았습니다.
  - `production_tools.execute`는 `validate()` 실패를 `status='invalid_arguments', retryable` 도구 결과로 돌려줍니다(`repair_count`, 최대 2회).
  - 문제는 `chat_protocols.normalize`가 같은 `validate()`를 응답 단계에서 먼저 불러, 실패하면 turn 전체를 `outcome_unknown`으로 만드는 것이었습니다.
  - 수정: `production_tools.py:55`의 `validate()`는 model_reason의 타입(str)만 봅니다. 빈 값·공백·301자 이상 검사는 `check_model_reason`(`:73`)으로 옮겨 `execute`의 같은 try 블록 안(`:97`)에서 합니다.
  - 결과는 `invalid_arguments / MODEL_REASON_1_TO_300_CHARACTERS / retryable=True`입니다.
  - 키가 아예 없는 경우는 다른 필수 인수와 같게 응답 검증 실패(`outcome_unknown`)로 남겼습니다. 원래 설계를 유지한 것입니다.
- **증명 테스트**:
  - `test_empty_or_long_reason_is_a_repairable_result_and_the_turn_continues`(`d15:149`): '', '   ', 'x'*301, '가'*301 네 경우 모두 확인했습니다.
    - turn은 `awaiting_continuation_approval`이고 action은 0건입니다.
    - 이어쓰기 미리보기에 코드가 들어 있습니다.
    - 사람이 이어쓰기를 승인한 다음 회차에서 고친 인수로 `proposed`가 되고 action 1건이 생깁니다. 다음 미리보기와 대화가 계속됩니다.
  - `test_reason_limit_is_visible_to_the_model_in_schema_and_description`(`:174`): 4개 도구의 원본 스키마, 전송 스키마 설명, OpenAI 정의, 준비 도구 설명을 확인합니다.
  - `test_missing_reason_is_a_schema_violation_like_any_missing_argument`(`:141`)

### A2b serious — 이어쓰기 본문 실측 오류와 64KiB 초과 → 고침 [검증됨]
- **재측정**: critic의 `probe_size.py`를 수정 전 코드로 다시 돌렸습니다.

  | 항목 | 값 |
  |---|---|
  | scene-status만 | 39,515B |
  | 도구 결과 | 39,768B |
  | tool_result 문자열 | 43,961B |
  | 이어쓰기 본문 | **70,579B** (상한 초과) |
  | 축소판 | 66,565B |

  - A2b 보고의 66,318B와 '축소판 여유 3KB'는 틀린 값입니다.
- **수정**:
  - scene-status를 페이지로 나눴습니다(`production_context.py:224-243`).
    - `SCENE_STATUS_LIMIT=8`, 최신 장면부터 셉니다.
    - 쿼리 `scene-status offset=N`을 받고, `offset`, `limit`, `next_query`, `scenes_3d_not_shown`, `scenes_3d_total`, `scenes_3d_truncated`를 돌려줍니다.
    - 잘못된 offset 형식은 새 거절 경로를 만들지 않고 기존 일반 조회로 처리됩니다.
  - estimate_media_plan 항목을 페이지로 나눴습니다(`fal_dispatch.py:77-103`, `ESTIMATE_ITEM_LIMIT=6` `:184`).
    - `total`과 `excluded`는 언제나 전체 항목 기준입니다.
    - `actions_total`, `actions_not_shown`, `offset`, `limit`, `next_query='media-estimate plan=<id> offset=N'`를 돌려줍니다.
    - 다음 쪽은 `search_project_context`에 그 query를 넘겨 받습니다(`production_tools.py:110-113`, `production_context.estimate_page`, `app.py:828` offset 전달). 도구 스키마는 바꾸지 않았습니다.
  - 생략은 숨기지 않습니다. 장면당 대기 제안은 기존대로 최근 10건이고, `pending_total`·`pending_truncated`가 생략을 알려 줍니다. note에 "더 오래된 대기 제안은 Scene Studio에서 검토"를 적었습니다.
- **실측**:
  - fixture 구성: 장면 32개 × 대기 10개, 실제 general chat turn → search_project_context → compact_result → result_message → continuation → body.
  - 크기는 고정 전송 인코더 `BoundedMessagesTransport.encode_body`로 쟀습니다.

  | 경우 | 이어쓰기 본문 | 상한 대비 |
  |---|---|---|
  | scene-status (`evidence/scene-status-worst-case-body.json`) | **39,292B** | 여유 26,244B (첫 요청 26,917B) |
  | estimate 20건 × 300자 이유 (`evidence/estimate-worst-case-body.json`) | 42,629 / 44,089 / 44,343 / 34,757B | 4쪽 모두 상한 안 |

  - estimate는 처음 8건/쪽에서 49KB가 나와 여유가 작았습니다. 그래서 6건으로 낮췄습니다.
- **테스트**: `tests/test_general_chat_body_cap.py`(신규)
  - `test_worst_case_scene_status_continuation_fits_under_the_cap_with_margin`(`:82`): 본문 < 65,536이고 여유 16KiB 이상(≤ 49,152B)인지 확인합니다.
  - `test_every_page_fits_and_pages_cover_all_scenes_once`(`:97`): 4쪽 모두 상한 안이고 32개 장면이 정확히 한 번씩 나오는지 확인합니다.
  - `test_estimate_items_are_paged_with_counts_totals_and_a_fetch_path`(`:133`): 4쪽 모두 상한 안이고, 합계가 쪽마다 같고, 20건을 중복 없이 모두 보는지 확인합니다.
- **전송 직전 거절 실행 검증**: `OverCapLiveTransportTest`(`:163`)
  - 실제 live 경로 전송 계층을 쓰고 공급자 소켓은 합성 stdlib opener만 썼습니다.
  - 수정 전 단일 32장면 페이지(패치)를 쓰면:
    - 이어쓰기 본문 **71,145B**가 `request_too_large`로 거절됩니다.
    - 전송은 1회차의 count와 message 2건뿐이고, 이어쓰기 미리보기는 만들어지지 않습니다.
    - 도구 실행은 기록되고, 예약은 `estimated`, 가격 상태는 `priced`입니다.
    - **turn 상태는 `outcome_unknown`**이고, 이후 새 미리보기 요청은 HTTP 400입니다(`evidence/over-cap-live-rejection.json`).
  - 페이지를 나눈 현재 코드에서는 같은 경로가 `awaiting_continuation_approval`로 이어집니다(`test_paged_result_continues_in_live_mode`).

### A2a/A2b minor

| 항목 | 처리 | 근거(테스트) |
|---|---|---|
| full_access에서 영상 준비 | 고침 | `VideoD15Test.test_full_access_agent_video_proposal_records_mode_and_stays_unexecuted`(`d15:526`): full_access·high 출처, 승인 필요, 예약·전송 0. 이 fixture는 대화 모델이 선택돼 있지 않아 먼저 haiku를 선택합니다 |
| 사람이 HTTP로 준비하는 영상 경로 | 고침 | `test_human_http_video_preparation_has_owner_label_null_provenance_and_rejects_injection`(`d15:433`): 실제 HTTP `media_prepare`(영상·시작 프레임). local-owner, 출처 값 전부 null, '프로젝트에서 사용자가 선택한 모델', 초당 단가×5초=0.35. actor/provenance/model_reason 주입은 400 |
| '출처 기록 없음' 표시를 견적 항목·작업 조회에도 | 고침 | `test_old_action_without_fields_projects_no_record_label`(`d15:220`): 카드(public_actions), estimate 항목, get_generation_job.pricing 셋 모두 `NO_RECORD`, 출처 값 None, 같은 unit_price |
| 기록 없는 예전 작업에 현재 단가를 붙이던 문제 | 고침 | `fal_dispatch.py:209`에서 `price.basis='현재 카탈로그 단가(준비 시점 기록 없음)'`. 기록된 작업에는 이 키가 없음을 `d15:113`이 단언 |
| ResourceWarning 파일 핸들 누수 | 고침 | `d15` VideoD15Test.setUp에서 `with open(...)`. 전체 실행 로그에 `Warning` 0건 |
| kling 2.5 turbo 공개 가격 문구 | 고침 | `fal_models.py:33-35`: `published_terms`에 페이지 원문 "For 5s video your request will cost $0.35. For every additional second you will be charged $0.07."를 초당 0.07 옆에 둠. 투영 필드 이름은 그대로 두고 `unit_price` 안에 실음(`test_kling_turbo_keeps_published_terms_verbatim_beside_the_per_second_value`, `d15:576`) |
| 매트릭스 observed()에 누락 항목 | 고침 | `test_general_chat_tool_permission_matrix.py:87-89`에 scene_proposals 행 수, preferences 전체 길이, timeline_edit_proposals·motion_proposals 길이 추가. 허용된 쓰기 도구의 정상 증가분은 `:110-116`에서 명시적으로 더함 |
| observed() 검사가 실제로 잡는지 | 확인 | `mutants.log`: 거절됐는데도 저장하는 변이 3개(scene/preference/timeline)가 새 observed()에서 KILLED, 이전 observed()(start/ 사본)에서는 SURVIVED |
| 실제 대화 turn 도중 권한 축소 | 고침 | `test_permission_lowered_to_read_only_mid_request_in_a_real_turn_saves_nothing`(`scene_pref:445`): review·full_access × {propose_scene_3d, propose_preference_rule, propose_timeline_changes}. 승인 뒤 read_only로 낮추면 `AGENT_READ_ONLY`, 제안·후보·타임라인 0건, turn은 계속됨 |
| 같은 인수로 반복된 제안·후보 | 고침(중복 제거) | `scene_project.py:398-402`(에이전트 출처, 대기 상태, 같은 base, 같은 scene_hash면 기존 제안 재사용), `local_creation_tools.py:346-353`(같은 category/value/evidence/reason/supersedes의 에이전트 대기 후보 재사용). 결과에 `duplicate`와 안내문. 테스트 `scene_pref:139`, `:366`(값이 다르면 새로 만들고, 거절된 뒤에는 다시 만듦) |
| docs/qa/contract-fixes-20261025/counterexamples-after.json 쓰기 | 기록만 | 이 파일은 `tests/test_contract_counterexamples.py:9`가 서브프로세스로 실행하는 `docs/qa/contract-fixes-20261025/verify-fixes.py:93`(`write_text`)이 씁니다. 이번 작업은 그 모듈을 실행 목록에서 뺐고(`full-modules.txt` 154개), 파일 수정 시각은 그대로 `Oct 28 19:52:52 2026`입니다. 19:52:52 변경의 주체는 여전히 [미확인]입니다 |
| locked_fields 재검사 미구현 (A2b minor) | 고치지 않음 | 지시된 minor 목록에 없고, 필드 잠금 저장소를 새로 만드는 일이라 사용자 결정 사항으로 남깁니다(§4) |

## 2. 의도적으로 바꾼 기존 기대값 (단언 삭제·약화 없음)

| 파일 | 바뀐 점 | 이유 |
|---|---|---|
| `test_general_chat_media_d15.py` | `test_missing_empty_or_long_reason_is_rejected_before_any_action`을 둘로 나눔. 키 없음은 `outcome_unknown` 그대로, ''·공백·301자는 `awaiting_continuation_approval` + `MODEL_REASON_1_TO_300_CHARACTERS` + 다음 회차 복구 | A2a serious 2. 예전 기대값 자체가 대화 잠김을 고정하고 있었음 |
| 같은 파일 `settings_state` | 투영 대신 저장 상태를 읽음 | 예전 함수는 agent settings를 비교하지 못했음 |
| 같은 파일 `test_read_only_cannot_prepare_video` | HTTP 200 단언을 `tool()` 안으로 옮김 | `tool()`이 결과 dict를 돌려주도록 바뀜. 단언은 남아 있음 |
| 같은 파일 `test_every_catalog_media_model_has_a_documented_price_record` | kling 2.5 turbo만 키 집합에 `published_terms` 추가 | kling minor |
| `test_general_chat_scene_preference_tools.py` `test_candidate_only_in_every_writable_mode_with_origin` | 모드마다 다른 value를 쓰고 `duplicate=False` 단언 추가 | 같은 인수를 쓰면 이제 중복 제거로 기존 후보를 재사용하기 때문. 후보 2건 단언은 그대로 |
| 같은 파일 `test_read_only_invalid_category_and_long_reason_store_nothing` | 301자 코드 `INVALID_TOOL_ARGUMENTS` → `MODEL_REASON_1_TO_300_CHARACTERS` | 원인이 드러나는 코드로 바꿈. 상태 `invalid_arguments`와 저장 0건 단언은 그대로 |
| `test_general_chat_tool_permission_matrix.py` | observed()에 항목 4개 추가, 허용된 쓰기의 정상 증가분 반영 | 매트릭스 minor |

## 3. 테스트 명령과 결과

모두 `cd /Users/leesungmin/Desktop/Loretune` 뒤 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests /opt/homebrew/opt/python@3.15/bin/python3.15 -B`로 실행했습니다.

- 전체(카운터예시 기록 모듈 제외 154개 모듈):
  - 명령: `-m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/SRV-r2/full-modules.txt)`
  - 로그: `full-tests.log`
  - 결과 끝부분:
    ```
    Ran 1025 tests in 427.269s
    OK (skipped=19)
    rc=0
    ```
  - `grep -c Warning full-tests.log` → `0`
- 변경 모듈 단독: `-m unittest tests.test_general_chat_media_d15` → `Ran 22 tests ... OK`. `tests.test_general_chat_body_cap` → `Ran 5 tests ... OK`.
- 변이 테스트: `.omo/evidence/agent-tools-02-20261028/tasks/SRV-r2/mutants.py`와 `mutants_old_observed.py` → `mutants.log`
  - 설정 불변 테스트: 대조군 PASS, 7/7 KILLED
  - 매트릭스: 대조군 PASS, 3/3 KILLED. 이전 observed()에서는 SURVIVED
- 바이트 측정: `measure_tools.py <start|.>` → `evidence/tool-bytes.json`
- 근거 파일 재생성: `SRV_R2_EVIDENCE=<SRV-r2>/evidence`를 주고 위 두 모듈을 실행하면 `evidence/*.json`이 다시 만들어집니다.

## 4. 남은 빈칸과 사용자 결정 사항

1. **[결정 필요] 이어쓰기 본문이 상한을 넘으면 대화가 `outcome_unknown`으로 잠김**(실행 검증함). 이번 작업은 lead 결정대로 결과를 상한 안에 들도록 묶었고, 이 상태 의미는 바꾸지 않았습니다. 아직 이 경로에 닿을 수 있는 경우:
   - 여러 회차에 걸쳐 쌓이는 이어쓰기 기록(최대 4회차)
   - 일반 `search_project_context`의 shots, actions, plans 목록(상한 없음)
   - 아직 실제로 보내지 않은 이어쓰기를 `blocked_before_message` 같은 회복 가능한 상태로 둘지 정해야 합니다. 원장(`uncertain`/`release`) 의미와 얽혀 있어 정하지 않았습니다.
2. **[추정] 토큰 수**: 본문 39~44KB가 `MAX_INPUT=16384` 토큰 안에 드는지는 count_tokens 없이 확인할 수 없습니다(금지 조건). JSON·한글 비율로 대략 1만~1.4만 토큰으로 추정합니다.
3. **장면당 대기 제안 11번째 이후**: 수와 생략 여부는 표시하지만 모델이 그 목록을 더 받아 오는 경로는 없습니다. 검토는 사람이 Scene Studio에서 합니다. 모델용 페이지가 필요한지 정해 주세요.
4. **중복 제거 범위**: 지금은 인수가 완전히 같을 때만입니다. 같은 활성 규칙을 대체하려는 값이 다른 후보 여러 건(critic probe의 a·b)은 여전히 따로 쌓입니다. 이 경우 첫 후보를 승인하면 둘째 승인은 거절됩니다. 대기 후보 개수 상한이 필요한지 정해 주세요.
5. **locked_fields 재검사**(A2b minor): 필드 잠금 저장소를 새로 만들지, 범위에서 뺄지 정해 주세요.
6. **A2a·A2b result.md의 틀린 문구**(설정 불변 범위, 66,318B·축소판 여유 3KB)는 쓰기 범위 밖이라 고치지 않았습니다. 바른 값은 이 문서 §1에 있습니다.
7. `request_media_generation`의 성공 경로 fixture는 사람이 `media_prepare`한 이미지 action에 시험용 live gate와 `project:` 예산을 붙여 만든 것입니다. 작업은 `prepared`까지만 가고 제공자 전송은 없습니다(`submissions == []`).
8. full_access에서 같은 grant로 다시 요청하면 `existing`(재조회)입니다. 두 번째 모드에서 새 렌더·생성 접수는 하지 않았습니다.

## 5. 산출물
- `changes.diff`, `start/`, `mutants.py`, `mutants_old_observed.py`, `mutants.log`, `measure_tools.py`
- `related-modules.txt`(A2a·A2b 관련 모듈 + 신규 모듈), `full-modules.txt`, `full-tests.log`
- `evidence/`: `invariant-outcomes.json`, `scene-status-worst-case-body.json`, `estimate-worst-case-body.json`, `over-cap-live-rejection.json`, `tool-bytes.json`
