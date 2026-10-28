# A2b-3d-pref-guards 결과 (Wave 2, 트랙 A 서버)

작성 2026-10-28. 외부·유료·모델 호출 0, count_tokens 0, `.env` 미접촉, 8765/57888 미기동(테스트 HTTP는 포트 0 임시 loopback), 브라우저 미사용, 파일 삭제 0.
편집 전 사본: `start/`(쓰기 범위 15개 모듈 + `tests/*.py`, 19:52 시작 시점 — A2a 수락본 포함). diff: `changes.diff`(start 대비, 바꾼 파일만, 신규 테스트 2개 포함).
바꾼 파일: `production_tools.py`, `chat_protocols.py`, `chat_general.py`, `local_creation_tools.py`, `scene_project.py`, `app.py` + 테스트 5개 수정·2개 신규. 바꾸지 않은 쓰기 범위 파일: `scene_spec.py`, `agent_preferences.py`, `fal_dispatch.py`, `fal_models.py`, `model_selection.py`, `media_creator.py`, `chat_runtime.py`, `chat_models.py`, `production_context.py`.

## 1. 항목별 조치

### 1) S7b `propose_scene_3d` [검증됨]
- 등록: `production_tools.py:26` TOOLS `{shot_id, base_revision, operations, model_reason}`. 검증 `:66`은 model_reason을 뺀 인수로 C1의 `scene_spec.validate_proposal`을 부른다. base_revision 0은 일반 int 규칙(최소 1)으로 거절된다(C1 r2 철회 요청 그대로).
- 실행: `production_tools.py:124` local_tool 이름 집합에 추가 → Conflict는 `STALE_VERSION`, ValueError·KeyError는 `VALIDATION_OR_HUMAN_APPROVAL_REQUIRED`(기존 처리 재사용). **AUTO_DRAFT 경로(`:127-130`, propose_timeline_changes 전용)에는 넣지 않았다.** `agent_preferences.READ_TOOLS`·`AUTO_DRAFT_COMMANDS`도 변경 없음 → read_only 차단, full_access도 자동 적용 없음.
- 스키마: `chat_protocols.py:103-105` C1의 `PROPOSAL_SCHEMA`(대상·필드별 13갈래, 전체판)에 `model_reason` 추가. 설명 `:24`. 크기 결정은 §2.
- 노출: `chat_general.py:41-42` ALLOWED_TOOLS. legacy 정적 기본 목록(`chat_runtime.LEGACY_DEFAULT_TOOLS`)에는 넣지 않았다(A2a의 get_agent_settings와 같은 처리, 범위 확대 안 함).
- 분기: `local_creation_tools.py:320-335` `propose_scene`.
  - 소유권: 현재 작품·**현재 대화**의 `scene_records`에서 shot으로 찾는다. 없거나 shot id가 모르는 값이면 `blocked/SCENE_NOT_FOUND`(구조화). 그 뒤 `scene_project.handle('scene_propose')`가 `_current`로 작품·대화를 다시 검사한다.
  - 현재 head: handle이 `base_revision!=head` 또는 head 0이면 Conflict → `STALE_VERSION`. 행 0개 추가(테스트).
  - 잠긴 필드: 저장된 잠금 데이터는 프로젝트에 없다(`locked_fields` 인자는 `scene_spec.propose_changes`에만 있고 호출부가 쓰지 않음, grep 확인). 서버 집행은 현재 head 기준 `allowed` 목록(카메라 id 고정, 기존 object/light id만, mesh의 color 금지)이고, 테스트로 mesh color·없는 object·없는 light가 거절됨을 확인했다.
  - 자산: `resolve_assets(require_rights=False)`가 현재 대화 자산·sha·profile·`check_rights`(차단)를 검사 → 차단 자산·다른 대화 자산은 제안 시점 거절. '사용권 미확인' 자산은 제안은 저장되지만 사람 승인(`scene_review`, require_rights=True)에서 거절된다(기존 사람 경로와 동일 규칙).
  - 결과(압축 영수증): `status='proposed'`, scene_id, proposal_id, base_revision, changes[{target,id,field}], `applied=False, approval_required=True, render_requested=False, external_calls=0`, actor·model_reason·model_reason_label·provenance, note.
- 출처: `local_creation_tools.py:313-318` `agent_origin` — A2a와 같은 6키 `{engine, chat_model, permission_mode(호출 시점 effective_mode), effort(동결값), run, call}` + `actor='agent'` + model_reason 원문 + 라벨 '모델이 제시한 이유(검증 안 됨)'. model_reason 길이 1..300은 A2a의 공통 검사(`production_tools.py:53`)가 그대로 적용된다.
- 저장: `scene_project.py:332` `handle(..., *, origin=None)`, `:399` 제안 body에 `origin` 저장. 사람 승인 시 `item.update`로 보존(테스트). scene-status 투영에는 origin이 나가지 않는다(테스트로 문자열 부재 확인).

### 2) S10 `propose_preference_rule` [검증됨]
- 등록 `production_tools.py:27` `{category, value, evidence, model_reason}`, category는 `preferences.CATEGORIES`(color/texture/camera/editing)만(`:67`, 스키마 enum `chat_protocols.py:106`). 권한·모델·effort 같은 설정 범주는 없다.
- 분기 `local_creation_tools.py:337-350`: 기존 `preferences.propose`를 재사용해 **status='proposed' 후보만** 저장한다. 범위는 현재 작품(song=작품명, ip=작품 IP). 활성화는 기존 사람 경로 `preference_review`뿐이다(어떤 모드에서도 자동 활성화 없음). `item['origin']`에 같은 provenance.
- 같은 범위·category에 active 규칙이 있을 때: 서버가 그 규칙 id를 `supersedes`로 묶는다. 결과에 `replaces_active=v번호`와 "승인하면 같은 속성의 활성 규칙 vN은 중지됩니다" 문구. 사람 승인 시 기존 `preferences.review` 규칙대로 이전 규칙이 paused된다(테스트). 승인 전 활성 규칙이 바뀌면 기존 review가 거절한다.
- `app.py:826` local_tool에 `preferences=preference_items` 전달(PLAN S10 "preference_items 전달 수정"). `local_creation_tools.execute`(`:373-386`)는 예외 시 SAVEPOINT와 함께 후보 목록도 원래 길이로 되돌린다.
- 화면: 기존 '연출 취향' 대화상자(`index.html:588 drawPreferences`)가 상태 '검토 대기'로 이미 보여 준다(읽기만 확인, UI 미수정). origin 표시는 B2 몫.

### 3) request_render / request_motion_render grant_id 사전 검사 이동 [검증됨]
- `app.py:535-536`: 두 도구의 `grant_id`를 production_tool 사전 가드(`chat_sessions.guard_refs`)에서 제외(A-pre 기존 패턴 확장).
- `local_creation_tools.py:356`: 도구 안에서 **같은 `chat_sessions.guard_refs`**를 다시 호출 → 실패 시 ValueError → `blocked/VALIDATION_OR_HUMAN_APPROVAL_REQUIRED`(HTTP 200, 구조화). 다른 대화 grant와 없는 grant가 같은 코드라 존재 여부를 새로 드러내지 않는다.
- 사람 HTTP 동작 불변: 이동 대상은 `action=='production_tool'`의 두 도구 이름뿐. 같은 foreign grant를 사람 액션(`motion_render`)에 넣으면 여전히 400(테스트). request_media_generation 등 다른 도구도 기존 사전 가드 그대로(기존 test_general_chat_job_query 통과).
- 효과: 일반 대화에서 다른 대화의 grant로 렌더를 요청해도 turn이 `outcome_unknown`이 아니라 `awaiting_continuation_approval`로 이어지고 job 0개.

### 4) 도구 × 권한 매트릭스 [검증됨]
- 신규 `tests/test_general_chat_tool_permission_matrix.py`: ALLOWED_TOOLS 14개 × {read_only, review, full_access} × {normal, 요청 중 read_only로 축소, 재시작(같은 SQLite에 새 Store)} = 126 호출.
  - 허용 = 모드가 read_only가 아니거나 READ_TOOLS(5개). 차단은 정확히 `invalid_arguments/AGENT_READ_ONLY`이고 관찰 상태 전후 동일. 차단 45건(쓰기 도구 9 × read_only 3시나리오 + 축소 2모드).
  - 매 호출 전후 불변: timeline_head, 3D 장면 head, 작업 수(jobs·generation_jobs·action_jobs), project 미디어 예약, 활성 선호 규칙, model_settings, 대화별 agent_settings·history.
  - 유일한 자동 적용 예외는 문서화된 full_access timeline 초안(AUTO_DRAFT): normal·restart의 full_access에서만 2건, 축소·review·read_only에서는 0건. 결과는 `applied_draft/agent-draft/output_approved=False`.
  - 각 모드의 미리보기 `tool_scope`와 message_body 선언 도구가 허용 목록과 정확히 같음.
  - 126칸 결과 분포(`evidence/permission-matrix.json`): succeeded 27, invalid_arguments 49(AGENT_READ_ONLY 45 + review·full_access의 normal·restart에서 `propose_motion_scene`의 고정 인수 `scene={}`가 무효인 4건 — 권한과 무관, 상태 불변 단언은 통과), blocked 25(가짜 grant 등 구조화 거절), not_found 9, proposed 14, applied_draft 2.
  - 추가: full_access → review 축소 후 timeline·scene·preference 세 쓰기 도구는 모두 `proposed`(초안 적용 0), 실행 ceiling='review'.
- `tests/test_general_chat_media_d15.py` 의 모든 도구 × 모드 설정 불변 테스트에 새 2개 도구 인수를 추가했다(`set(arguments)==set(TOOLS)` 유지).

### 5) C1 이월 minor [검증됨]
- legacy head 저하(degrade): `scene_project.py:285-289` `_approved_ontology`가 approval·binding·ontology_revision이 없으면 None → `stale_context`/`requires_review=True`(렌더도 require_approval에서 거절되므로 같은 의미). KeyError 없음. binding 필드 삭제·approval 전체 삭제 두 경우 테스트.
- 정확한 상한 경계 테스트: 정확히 32개 장면 → `scenes_3d_truncated=False`, 정확히 10개 대기 → `pending_truncated=False`, head 0 초안의 ontology drift → `requires_review=True`·승인 Conflict.
- 크기: **실측** 최악(장면 32 × 대기 10) scene-status 결과 **39,515 bytes**(C1의 복제 추정 39,482와 근사). bytes/4 ≈ 9,878 토큰 [추정] — MAX_INPUT 16384 단독으로는 안이지만 §2대로 이어쓰기 본문은 64KiB 전송 상한에 닿는다.
- `public()` ontology drift: `scene_project.public`(쓰기 범위 안, app.py 수정 불필요)이 버전은 승인 binding의 ontology_revision, 제안은 저장된 ontology_revision을 현재 값과 비교해 `requires_review`에 반영(`:294, :304-307`). `status()`는 이제 public의 값을 그대로 써서(`:322-323`) 직접 인덱싱이 사라졌다. **Scene Studio 화면 동작이 바뀐다**: ontology만 바뀐 경우에도 승인·렌더 버튼이 비활성되고 "실행 기준이 변경된…" 문구가 나온다. 서버가 이 상태에서 이미 Conflict로 거절하므로 화면과 서버가 일치하게 된 것이다.

## 2. 크기 측정 (UTF-8 JSON 바이트, 토큰 아님) — `measure-start.json`, `measure-after.json`, `measure-a2b.json`
측정 스크립트 `measure_token_budget.py`(A2a와 동일), `measure_a2b.py`(스키마 대안·최악 이어쓰기).

| 모드 | 도구 수 | tools 바이트 | 첫 요청 본문 |
|---|---|---|---|
| review·full_access | 12 → 14 | 11,621 → 19,889 | 18,273 → 26,541 |
| read_only | 5 → 5 | 1,339 → 1,339 | 7,991 → 7,991 |

| 항목 | 바이트 |
|---|---|
| propose_scene_3d 본문 내(strict 포함) | 7,745 |
| propose_scene_3d 정의 단독(전체판) / 대상별 축소판 | 5,841 / 2,993 |
| propose_preference_rule 본문 내 | 519 |
| review 첫 본문: 전체판 / 축소판 | 26,541 / 22,527 |
| **최악 scene-status(39,515B) 이어쓰기 본문: 전체판 / 축소판** | **66,318 / 62,304** (전송 상한 65,536) |

- 스키마 선택: **전체판 유지**. 이유: (a) MAX_INPUT 16384 기준 첫 본문 26,541B ≈ 6.6k 토큰 [추정 /4]로 여유가 크다. (b) 전체판은 field↔value 타입을 스키마가 묶어 strict 모드에서 형태 불일치 호출이 생기지 않는다. 축소판은 value를 anyOf로 풀어 불일치를 검증기만 잡고, 그 검증은 `chat_protocols.normalize` 단계라 실패 시 turn이 outcome_unknown이 된다(응답 비용은 이미 발생). (c) 64KiB 초과는 극단 scene-status(32×10)에서만 생기며 축소판도 여유가 3,232B뿐이라 대화 이력이 조금만 있어도 넘는다 — 근본 원인은 scene-status 상한(사용자 결정 대기, C1 r2)이지 스키마가 아니다. 결정 항목 §6-1.
- 64KiB 초과 시 동작 [검증됨: 코드 읽기, 실행 미검증]: live 모드 `create_preview`의 `BoundedMessagesTransport(max_request_bytes=65536).encode_body`가 전송 전에 거절한다. 직전 회차 응답 비용은 이미 정산된 뒤다. contract-fake 모드는 이 검사를 하지 않는다.

## 3. 의도된 기존 테스트 변경 (단언 삭제·약화 0)
| 파일 | 변경 | 이유 |
|---|---|---|
| tests/test_chat_protocols.py:61-62 | 도구 수 15→17, 이름 집합에 2개 추가 | S7b·S10 |
| tests/test_general_chat_media_d15.py (DirectToolInvariantTest) | 인수 표에 새 2개 도구 추가 | 모든 TOOLS 커버 단언 유지 |
| tests/test_general_chat_motion.py:263-266 | 다른 대화 motion grant 요청 turn: `outcome_unknown` → `awaiting_continuation_approval` + 도구 결과 `blocked/VALIDATION_OR_HUMAN_APPROVAL_REQUIRED` 정확 일치 단언 추가. job 0·usage·예약 정산 단언 유지 | 항목 3 |
| tests/test_timeline_grant_scope.py (3곳) | `tool(...)` HTTP 400/≠200 → `assert_tool_refused`: HTTP 200 + 정확한 blocked 결과 + jobs 행 수 불변 | 항목 3 (거절 자체는 유지, 더 엄격한 단언) |
| tests/test_general_chat_scene_context.py:179 | `public()` requires_review 전부 False → 문맥 동일 + 전부 True | 항목 5 public drift |

## 4. 실행한 명령과 출력 꼬리
모두 `cd /Users/leesungmin/Desktop/Loretune`, `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B`.

1. 신규 모듈 [검증됨]: `-m unittest tests.test_general_chat_scene_preference_tools` → `Ran 22 tests ... OK`, `tests.test_general_chat_tool_permission_matrix` → `Ran 2 tests ... OK`. 증거: `evidence/`(scene-proposal-receipt.json, preference-receipt.json, scene-status-worst-case.json, permission-matrix.json — `A2B_EVIDENCE` 환경변수로 기록).
2. `tests.test_timeline_grant_scope` (단언 갱신 후) → `Ran 6 tests in 5.690s / OK`.
3. **관련 모듈 전체**(`related-modules.txt` 78개 = A2a 목록 67 + scene·preference·timeline 관련 11): `PYTHONPATH=tests ... -m unittest $(cat related-modules.txt)` → 로그 `related-tests.log`
   ```
   Ran 715 tests in 309.256s
   OK (skipped=17)
   rc=0
   ```
   skip 사유(`related-tests.skips.txt`): Blender 신뢰 환경 미설정 14, Blender 고정 환경 1, Blender+TripoSR 산출물 1, 로컬 QA 환경 1 — 모두 환경 게이트(A2a와 동일 계열).
4. 1회차 기록(`related-tests.run1.log`, `PYTHONPATH` 없이 실행): `Ran 635, failures=3, errors=12`. errors 12개는 전부 `ModuleNotFoundError: test_scene_contract / scene_asset_fixtures`(tests 폴더 형제 import — 실행 경로 문제, 코드 회귀 아님). failures 3개는 `test_timeline_grant_scope`의 HTTP 400 기대 — 항목 3의 의도된 변경 결과라 §3대로 단언을 갱신했다. 3회 모두 2회차에서 통과.
5. **변이 검사**(작업 트리 사본 `scratchpad/a2b-mut/root`, 원본 미수정, `mutants.log`): 신규 2모듈 + scene_context 35개 테스트 기준 baseline OK → 변이 10개 **전부 FAILED** → 복원 후 OK.
   ```
   scene proposal auto-approved: FAILED (failures=6, errors=3)
   propose_scene_3d in READ_TOOLS: FAILED (failures=1, errors=1)
   in-tool grant guard removed: FAILED (failures=4)
   app preflight move reverted: FAILED (failures=3, errors=1)
   preference auto-activated: FAILED (failures=12)
   provenance permission hardcoded: FAILED (failures=2)
   public ontology drift removed: FAILED (failures=2)
   legacy degrade reverted: FAILED (errors=1)
   supersedes never set: FAILED (failures=1)
   scene proposal origin dropped: FAILED (errors=3)
   ```
6. 크기 측정: `measure_token_budget.py <root> x` (start 사본은 `PYTHONPATH=<repo>`로 미변경 모듈 보충 — 1차 시도는 `ModuleNotFoundError: chat_sessions`로 JSON이 아니었고 재실행으로 해결), `measure_a2b.py` → §2 표.

## 5. 남은 빈칸
- **UI 표시(B2)**: scene 제안·선호 후보의 origin(actor·이유·provenance) 화면 표시, toolLabels(`propose_scene_3d`, `propose_preference_rule`)는 B2 소유라 하지 않았다.
- **잠긴 필드**: 프로젝트에 장면별 잠금 저장소가 없다. 사람이 특정 필드를 잠그는 기능은 없고, 서버 집행은 head 기준 허용 목록뿐이다. 새 잠금 기능은 범위 밖(만들지 않음).
- **legacy 경로**: legacy 기본 목록에 새 2개 도구를 넣지 않았다. legacy를 tools 명시 설정으로 열면 같은 execute 경로를 탄다(별도 테스트 없음).
- **선호 범위**: 에이전트 후보는 현재 작품 범위만 만든다(IP 전체 기본 취향 후보는 만들 수 없음) [가정].
- **strict 수치 범위**: Anthropic strict 도구 모드가 `minimum/maximum`을 실제로 집행하는지는 확인하지 않았다 [미확인]. 범위 위반은 normalize의 검증기가 잡는다(실패 시 outcome_unknown).
- **전체 회귀**: `discover` 전체·skip 0 조건(S0 드라이버, Blender env)은 실행하지 않았다(main 통합 몫). 관련 모듈 실행의 skip은 아래와 같다.
- **Scene Studio 실화면**: public() 변경의 화면 효과는 코드 읽기로만 확인했다(브라우저 금지).

## 6. 사용자 결정이 필요한 사항
1. **scene-status 상한 (C1 r2 결정 미해결, 이번 측정으로 구체화)**: 실측 최악 39,515B. 전체판 스키마에서 그 결과가 담긴 이어쓰기 본문이 66,318B로 64KiB 전송 상한을 782B 넘는다(축소판 62,304B). 선택지: (a) 상한 축소(예: 장면 8·대기 3) (b) offset 페이지 (c) 유지하고 전송 전 거절에 맡김. (a)/(b)를 고르면 스키마는 전체판으로 충분하다.
2. **Scene Studio 표시 변경 수용 여부**: ontology만 바뀐 경우에도 '검토 필요'로 표시된다(서버 거절과 일치). 원치 않으면 public() 변경만 되돌리고 status()에서만 반영하는 이전 방식으로 돌릴 수 있다.
3. **선호 후보 범위**: 현재 작품 한정이 맞는지, IP 기본 취향 후보도 허용할지.
