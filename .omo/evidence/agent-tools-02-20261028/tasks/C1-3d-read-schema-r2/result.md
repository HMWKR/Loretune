# C1-3d-read-schema 재작업 2차 결과 (S6 · S7a)

입력 자료: `PLAN-ko.md` §6·§8, 1차 결과(`tasks/C1-3d-read-schema/result.md`), critic 판정(wf_18a38ed0-25d journal 13행), codex 검수(`codex-gate/review-1.md` #8).
편집 전 사본: `before-r2/`(5파일). 전후 diff: `evidence/source.diff`(64줄), `evidence/tests.diff`(107줄). 쓰기 범위 5파일 밖은 수정하지 않았다.

## 결함별 조치

| # | 결함 | 조치 (파일:줄) | 테스트 |
|---|---|---|---|
| 1 | 오래된 revision 제안을 대기로 셈 | `scene_project.py:309-318`: `pending`은 status가 proposed·held이고 `base_revision==record['head']`인 것만 센다(`scene-studio.js:35`과 같은 조건). 나머지 proposed·held 제안은 `stale_total` 개수로만 보고한다. | `tests/test_general_chat_scene_context.py:160` A·B를 제안하고 A를 승인한다. 그러면 head=2, pending `[]`, `pending_total=0`, `stale_total=1`이 된다. B는 저장소에 'proposed'로 남아 있고, B를 승인하면 `Conflict`가 난다. |
| 2 | scenes_3d 상한 없음, 잘림 표시 없음 | `production_context.py:215` `SCENE_STATUS_LIMIT=32`. `:221-222`는 최근 32개(rowid 순 끝)만 남기고 `scenes_3d_total`·`scenes_3d_truncated`를 추가한다. `scene_project.py:318`는 장면마다 `pending_total`·`pending_truncated`를 추가한다(대기 제안 10개 상한은 유지). | `:184` 빈 목록(`[]`, 0, False)과 34개(32 반환, total 34, truncated True, 마지막 32개 id 일치). `:156` 대기 제안 12개는 `(12, True)`. |
| 3 | ontology drift 미반영 | `scene_project.py:306,312-313`: 현재 ontology snapshot revision(`ontology.snapshot`, SELECT만 함)을 읽는다. 다음 경우에 `stale_context`·`requires_review`로 표시한다. head 버전은 `approval.binding.ontology_revision`이 다를 때(render의 `require_approval` 정확 일치가 거절함), 대기 제안은 `ontology_revision`이 다를 때(`scene_review` :338이 거절함). note 문구도 같이 고쳤다(`production_context.py:224`). | `:171` ontology head만 올리고 shot context는 그대로 둔다(`public()`의 requires_review는 모두 False). status는 `('stale_context', True)`이고 승인은 `Conflict`로 거절된다. |
| 4 | base_revision 0 모순 | 스키마 `minimum=1`은 유지한다. 1차 결과의 요청 2번 중 "`'base_revision'`을 0 허용 키에 추가"는 **철회한다**(아래 절 참조). head 0 처리는 문서로 남겼다. `scene_spec.py:195`의 description을 "scene-status에서 head를 읽는다. head 0은 승인 버전이 없어 변경 제안을 받지 않는다"로 바꿨고, scene-status note(`production_context.py:224`)에도 head 0의 의미를 적었다. `validate_proposal`의 0 전용 메시지는 방어용으로 그대로 둔다(동작 변경 없음). | `tests/test_scene_spec_proposal_schema.py:31-32`: minimum 1 단언을 유지하고 description에 'scene-status'가 들어 있는지 단언한다. 기존 `test_base_revision_zero_is_explicitly_rejected`도 통과한다. |
| 5 | 도구 실행 경로 테스트 없음 | `local_creation_tools.py`는 수정하지 않았다. | `tests/test_general_chat_scene_context.py:197` `local_creation_tools.execute(store,c,studio,'A','execution_context',{'query':'scene-status'},run,call)`. 결과가 `production_context.read`와 같고, `total_changes`와 `iterdump`가 바뀌지 않으며, `pending_total=1`인지 확인한다. |

### 철회하는 요청 (트랙 A 대상, 1차 결과 requests_for_other_tracks 2번 앞부분)

- 철회: "`production_tools.validate`의 일반 int 0 허용 집합에 `'base_revision'` 추가".
- 유지: 끝에 `validate_proposal(args)`를 호출하는 요청.
- 0의 처리: 일반 int 검사의 `INVALID_TOOL_ARGUMENTS`(또는 strict 스키마의 minimum 1)로 거절된다.
- 모델이 head 0을 미리 알 수 있는 경로: scene-status의 `head:0`과 `approval_status:'none'`, 그리고 note·스키마 description.

## 의도적으로 바꾼 기존 단언 (약화 아님)

- `:86`, `:90`: 장면 dict 정확 일치 기대값에 새 필드 `pending_total=1, pending_truncated=False, stale_total=0`를 추가했다. 결함 2와 결함 1의 필드를 추가한 데 따른 것이다. 기존 키와 값의 단언은 모두 그대로다.
- `:156`: 기존 `len==10`과 `assertLess(size,4096)`은 유지한다. `(pending_total, pending_truncated)==(12, True)` 단언을 추가했다.

## 실행 명령과 결과 꼬리

```
cd /Users/leesungmin/Desktop/Loretune && SCENE_STATUS_EVIDENCE=<r2>/evidence PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest discover -s tests -p test_general_chat_scene_context.py -v
Ran 11 tests in 0.242s
OK
```

```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest discover -s tests -p test_scene_spec_proposal_schema.py -v
Ran 6 tests in 0.004s
OK
```

```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest test_general_chat_scene_context test_scene_spec_proposal_schema test_agent_work_status_context test_chat_protocols test_execution_context test_local_creation_tools test_motion_overlay test_music_input_context test_production_tools test_scene_asset_diagnostics test_scene_asset_render test_scene_asset_workflow test_scene_assets test_scene_background test_scene_cli test_scene_config test_scene_contract test_scene_request_recovery test_scene_ui test_scene_vertex_colors test_scene_workflow -q
Ran 188 tests in 67.259s
OK (skipped=18)
```

- 188은 1차의 184에 신규 4개를 더한 수다.
- skip 18건은 1차와 같은 Blender env 미주입 사유다. skip 0 조건의 전체 회귀는 main이 S0 드라이버로 실행해야 한다 [미검증: 이 워커에서 실행하지 않음].
- 실패 1회가 있었다. 신규 ontology 테스트의 기대값을 `[False,False]`로 잘못 적은 탓이다(초기 생성 제안까지 3항목이었다). 기대값을 `assertFalse(any(...))`로 고친 뒤 통과했다. 제품 코드 결함은 아니었다.

## 증거 (`evidence/`)

- `size.json`: 장면 2개, 대기 제안 10개(+2개 잘림)일 때 **2413 bytes**. 1차의 1774보다 늘었는데, note와 필드가 길어졌기 때문이다.
- `size-capped.json`: 장면 34개 중 32개 반환, 장면당 대기 제안 1개일 때 **11993 bytes**.
- `size-worst-case.json`: 대기 제안 10개짜리 장면 항목(1202 bytes)을 32번 복제한 계산값이다. 실제 34개×11제안 fixture를 실행한 값이 아니다.
  - 결과: **39482 bytes**, note 714 bytes.
- `proposal-schema-size.json`: PROPOSAL_SCHEMA 5605 bytes(기본 dumps). 1차의 5534보다 +71인데, description 문구가 길어졌기 때문이다.
- `scope.json`, `redaction.json`, `read-preservation.json`: 신규 필드가 반영된 재기록이다. redaction 단언은 모두 그대로 통과했다.

## 남은 공백

- **크기 상한은 개수만 제한하고 바이트·토큰은 제한하지 않는다.** 상한 32×10에서 최악 약 39 KB이고, 장면 32개에 대기 제안이 1개씩만 있어도 12 KB다. 입력 4096토큰 상한(codex #8, PLAN D20)과 함께 판단해야 한다. 아래 결정 항목 참조.
- 오래된 제안은 개수(`stale_total`)만 보고하고 id는 내보내지 않는다. 지시가 "separate count"였기 때문이다.
- `public()`(UI 투영)의 `requires_review`는 여전히 context만 비교하고 ontology drift를 반영하지 않는다. 지시 범위가 model-facing status였고 `app.py`와 UI 동작을 바꾸지 않으려고 손대지 않았다. Scene Studio 표시와 status가 ontology drift에서 다르게 보일 수 있다.
- critic의 선택 지적 2건은 이번 결함 목록에 없어 하지 않았다.
  - VALUE_BOUNDS를 단일 원천으로 만드는 것(경계값 일치 테스트가 drift를 감지한다).
  - configured renderer 상태에서 `capability()`를 patch 없이 실행하는 것.
- HTTP 종단(`general_chat_preview` → tool_result)은 여전히 테스트하지 않았다. 이번에는 `local_creation_tools.execute`까지만 확인했다.

## 사용자·main 결정 필요

- **D20 연동: scene-status 상한 값.**
  - 현재 값: 장면 32, 장면당 대기 제안 10. 지시 예시값을 그대로 썼다.
  - 문제: 최악 39482 bytes는 그 자체로 4096토큰 입력 상한을 넘을 가능성이 크다 [추정: bytes/4 ≈ 9.9k 토큰. 실측 count_tokens는 유료라 하지 않았다].
  - 선택지:
    - (a) 상한을 줄인다. 예: 장면 8, 대기 제안 3이면 계산상 약 3 KB 이하다 [추정].
    - (b) `motion_overlay_sources`처럼 offset 페이지 방식으로 바꾼다.
    - (c) 현재 값을 유지하고, 서버의 입력 상한 초과 거절(`chat_general.py:647`)에 맡긴다.
  - 결정한 값은 상수 1개(`SCENE_STATUS_LIMIT`)와 `[-10:]`만 바꾸면 반영된다.
- `public()`에도 ontology drift를 반영할지. 반영하면 Scene Studio의 '검토 필요' 표시가 바뀐다. 트랙 B와 `app.py` 영향이 있어 이번에는 하지 않았다.

## 가정

- 상한을 넘으면 최근에 만든 장면(rowid 순 끝)을 남긴다. 대기 제안 `[-10:]` 관례를 따른 것이다.
- head 버전의 ontology 기준은 `version['approval']['binding']['ontology_revision']`이다. 모든 head 버전은 `scene_review` 승인 경로(:339-344)로만 만들어지고 이 필드를 가진다 [검증됨: 코드 읽기]. 이 형식이 없는 예전 데이터는 범위 밖으로 가정했다.
