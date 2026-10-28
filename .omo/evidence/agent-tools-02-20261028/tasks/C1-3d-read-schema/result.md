# C1-3d-read-schema 결과 (S6 · S7a)

## 한 일 (파일별)

- `scene_project.py` [검증됨]: `status(c,store,p,name,conversation)` 추가 (`public()` 재사용 후 필터).
  - 장면마다 `{scene_id, shot_id, head, approval_status, requires_review, pending_proposals[{proposal_id, base_revision, status}]}`만 반환한다.
  - grant id, 자산 id·sha·경로, 장면 본문, scene_hash, context, provenance는 넣지 않는다.
  - `shot_id`는 `scene_records.shot_id`(= `production_context.shot_id`, 다른 투영과 같은 공개 stable id)를 쓴다.
  - `approval_status`: head 버전 없음 → `none`, head 버전의 `requires_review`(문맥 변경) → `stale_context`, 그 외 → `recorded`.
  - 장면 단위 `requires_review` = head 버전 또는 대기 제안 중 하나라도 저장 후 문맥이 바뀐 경우(기존 `public()` 필드 의미를 장면 단위로 모은 것).
  - `pending_proposals` = status `proposed`·`held`만, 최근 10개 상한(`motion_context`의 `[-10:]` 관례).
- `production_context.py` [검증됨]:
  - `scene_status()`를 추가하고, `read()`에 `query=='scene-status'` 조기 반환 분기를 넣었다(`work-status`와 같은 방식).
  - 결과 형태: `{scene_status:{scope:'current-project-current-conversation', observed_revision, scenes_3d, connection:{available, external_transmission:False}, note}}`.
  - `connection.available`은 기존 `scene_project.capability(store)`에서 bool만 가져온다. 이 경로는 `scene_config.load`·docker·subprocess를 부르지 않고, stat과 `shutil.which`만 쓴다.
  - `supported_context_queries`에 `scene-status` 항목을 뒤에 추가했다(`[0]`은 `work-status`로 유지).
  - `scene_project`는 순환 import를 피하려고 함수 안에서 지연 import한다(`motion_context`와 같은 관례).
- `scene_spec.py` [검증됨]:
  - 모듈 상수 `CHANGE_FIELDS`(대상별 변경 가능 필드)와 `VALUE_BOUNDS`(`validate()` 범위의 사본)를 추가했다.
  - `propose_changes`의 지역 `valid_fields`는 `CHANGE_FIELDS`를 참조하도록 바꿨다. 동작은 같다(멤버십 검사만 한다).
  - `PROPOSAL_SCHEMA`(JSON schema, 닫힌 객체)를 추가했다.
    - 필드: `shot_id` str 1..200, `base_revision` integer 1..2^31-1, `operations` 1..16.
    - `operations`는 (target, field)별 anyOf 13갈래이고, 각 갈래가 value 타입·범위를 고정한다. asset은 `{id, sha256, profile enum}`이다.
  - `validate_proposal(args)`를 추가했다.
    - 키 정확 일치, shot_id, revision 타입과 범위를 검사한다.
    - **`base_revision==0`이면 별도 메시지 `'no approved scene version; the first draft is reviewed in Scene Studio'`로 거절**한다.
    - 그 밖에 1..16개, 연산 키 정확 일치, target·field enum, camera id는 `'camera'`, object·light id 패턴, (target,id,field) 중복, value 범위와 asset 형식을 검사한다.
    - 분리된 사본을 반환한다. 대상 존재 여부·잠금·리비전은 호스트(`propose_changes`)가 계속 판정한다.
- `tests/test_general_chat_scene_context.py` (신규, 7개):
  - 현재 대화만 보이는지(다른 대화 장면 불가시)
  - held·rejected 필터와 stale_context
  - grant id, 자산 id·sha, store 경로, `model-assets`, `.glb`, `/assets/`, 장면 본문 키 문자열 검색(전체 `public()`에는 해당 값이 있다는 대조 포함)
  - DB `iterdump`·`total_changes`·파일 sha와 project·snapshot 불변, subprocess·runtime_binding·tree_manifest·render·reconcile 호출 시 실패하도록 patch
  - connection은 available만 투영
  - work-status와 기본 질의 불변, `production_tools.validate` 통과
  - 결과 크기 상한과 기록
- `tests/test_scene_spec_proposal_schema.py` (신규, 6개):
  - 스키마가 닫혀 있고 add·delete 단어가 없는지
  - 13개 필드 전부 유효하고 `propose_changes`와 연결되는지
  - 필드별 경계값에서 `validate_proposal`과 `propose_changes`의 판정이 일치하는지(범위 사본 drift 감지)
  - base 0의 명시적 거절과 -1·bool·float·str·2^31·None
  - 잘못된 형태 29종
  - add·delete·kind·id 변경과 objects 대상 시도 8종, 존재하지 않는 id는 적용 시점에 `scene target not found`

## 재현 → 수정 → 통과

편집 전 사본(`before/`)을 PYTHONPATH 앞에 두고 신규 테스트를 실행하면 실패한다(원문 꼬리).

```
Ran 7 tests in 0.105s
FAILED (failures=3, errors=4)
```

```
Ran 6 tests in 0.012s
FAILED (errors=42)
```

## 실행한 테스트 명령과 결과 꼬리

```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest discover -s tests -p test_general_chat_scene_context.py -q
----------------------------------------------------------------------
Ran 7 tests in 0.109s

OK
```

```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest discover -s tests -p test_scene_spec_proposal_schema.py -q
----------------------------------------------------------------------
Ran 6 tests in 0.004s

OK
```

관련 기존 모듈 회귀는 다음과 같다(native Blender 모듈 `test_scene_vertex_colors_native`는 제외).

```
cd /Users/leesungmin/Desktop/Loretune && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest test_general_chat_scene_context test_scene_spec_proposal_schema test_agent_work_status_context test_chat_protocols test_execution_context test_local_creation_tools test_motion_overlay test_music_input_context test_production_tools test_scene_asset_diagnostics test_scene_asset_render test_scene_asset_workflow test_scene_assets test_scene_background test_scene_cli test_scene_config test_scene_contract test_scene_request_recovery test_scene_ui test_scene_vertex_colors test_scene_workflow -q
----------------------------------------------------------------------
Ran 184 tests in 65.345s

OK (skipped=18)
```

skip 18건은 모두 `'trusted local Blender test environment not configured'`, `'pinned local Blender environment required'`, `'trusted local (Blender) QA environment not configured'`이다. S0 드라이버가 주입하는 native 3D env 없이 실행했기 때문이며, 이번 변경과 무관하다 [검증됨: -v 출력의 skip 사유]. 전체 회귀(skip 0 조건)는 main이 S0 드라이버로 실행한다.

## 증거 (`tasks/C1-3d-read-schema/evidence/`)

- `scope.json`, `redaction.json`, `read-preservation.json`, `size.json`, `proposal-schema-size.json`: 신규 테스트가 `SCENE_STATUS_EVIDENCE` 환경변수로 기록한 것.
- **scene-status 결과 크기**: 장면 2개 + 대기 제안 10개(상한 적용)에서 **1774 bytes**(`size.json`). 테스트 상한은 4096 bytes.
- **PROPOSAL_SCHEMA 크기**: indent 없는 기본 dumps 5534 bytes, compact(`,` `:`) **4979 bytes**, 13갈래. 참고로 현재 `chat_protocols.tool_definitions('anthropic')` 전체는 compact 10194 bytes이다.
  - 대안 측정: 대상별 3갈래 + value anyOf(number|vector|asset)로 느슨하게 만들면 2362 bytes이다. 대신 field↔value 결속이 스키마에서 빠지고 검증기만 집행한다. 4096 토큰 상한 판단은 wave 2·main 몫이다.
- `existing-queries-vs-before.json`: 같은 fixture에서 `before/production_context.py`와 비교한 결과.
  - `work_status_equal: true`(시각 필드 2개 제외)
  - `default_read_equal_except_queries: true`
  - queries `["work-status"]` → `["work-status","scene-status"]`
- `source.diff`: 내 쓰기 범위 3개 파일의 `before/` 대비 diff.

## provenance 수용성 점검 (`scene-studio.js` 읽기만, 수정 안 함)

결론: `scene_proposals` body에 `provenance:{run, call, model, mode}`를 추가해도 Scene Studio는 깨지지 않는다 [검증됨: grep·읽기].

- `scene-studio.js`가 제안에서 읽는 것은 `id`, `status`, `base_revision`, `scene`, `requires_review`뿐이다(:35-37, :63, :76, :82, :140, :152). 키를 열거하거나 전체 객체를 비교하지 않는다. `Object.keys`·`entries`는 :132의 편집 경로에만 있고 제안 객체와는 무관하다.
- `index.html:891`은 `JSON.stringify(p.scenes_3d)`를 변경 감지에만 쓴다. 필드가 하나 늘어도 안전하다.
- `chat-sidebar.js:73`은 `scene.shot`·`shot_id`만 읽는다.
- 주의사항:
  - (1) `app.py:387`의 `public()`이 제안 body를 그대로 화면 상태로 내보낸다. 그래서 provenance(run·call id, 모델명, mode)가 UI 상태에 노출된다. 비밀은 아니다.
  - (2) `scene_review`는 `item.update`로 provenance를 보존한다.
  - (3) `scene_replace_draft`(head 0 전용)는 provenance 없이 새 항목을 만든다. 도구는 head 0을 다루지 않으므로 해당 없다.
  - (4) 이번 `status()` 투영은 provenance를 내보내지 않는다.
  - (5) 기존 테스트 중 제안 키 집합 전체를 단언하는 것은 없다 [추정: `assertEqual(set(` grep 기준].

## 안 한 일 / 남은 빈칸

- S7b(도구 연결, provenance 저장, Scene Studio 표시)는 지시대로 하지 않았다. `scene_project.handle`에 provenance 인자도 추가하지 않았다(S7b 몫).
- `test_scene_vertex_colors_native`와 Blender env가 필요한 skip 18건은 이 워커에서 검증하지 않았다(main 전체 회귀 대상).
- HTTP 경유(실제 `general_chat_preview` → `search_project_context(query='scene-status')` → tool_result) 종단 테스트는 추가하지 않았다. `production_tools.validate` 통과와 `local_creation_tools._execute`가 query를 그대로 넘기는 것(:316)은 확인했다.

## 가정·추측

- `approval_status`는 지시된 3값만 쓴다. 손상된 approval 레코드(`motion_context`의 `invalid_record` 같은 경우)는 별도 값으로 구분하지 않는다. 서버만 쓰는 레코드라 손상 시나리오는 범위 밖으로 가정했다.
- 장면 단위 `requires_review`의 의미는 위에 적은 대로(head 버전 또는 대기 제안의 문맥 변경)로 정했고, note에도 적었다.
- `pending_proposals`에는 base_revision이 현재 head보다 낮은(=stale) proposed·held 제안도 포함된다. 모델이 base_revision을 비교해 알 수 있다.
- `VALUE_BOUNDS`는 `validate()` 범위를 옮겨 적은 사본이다. drift는 경계값 일치 테스트가 잡는다. 최종 권위는 여전히 적용 시점의 `propose_changes`→`validate`이다.
- `PROPOSAL_SCHEMA`에서 id·sha 패턴(`pattern`)은 쓰지 않고 길이 제한만 둔다. 기존 스키마들이 `pattern`을 쓰지 않아 strict 호환성을 맞춘 것이고, 패턴은 검증기가 집행한다.

## 기각한 가설

- "`capability()`가 docker나 subprocess를 부른다": 아니다. `Path.resolve`·`stat`·`shutil.which`뿐이다. patch 테스트에서 subprocess.run·Popen 호출 0으로 확인했다.
- "`production_context`에서 `scene_project`를 최상위 import해도 된다": `scene_project`가 `production_context`를 최상위 import하므로 순환이 생긴다. 지연 import로 해결했다.
- "scene-status는 `production_tools.validate`에서 막힌다": `overlay_page_offset`은 `motion-overlay-sources` 접두만 검사하므로 통과한다. 테스트로 확인했다.

## requests_for_other_tracks (S7b·wave 2 배선, 정확한 기대안)

1. `production_tools.TOOLS`(트랙 A): `'propose_scene_3d': {'shot_id':str,'base_revision':int,'operations':list}`
2. `production_tools.validate`(트랙 A):
   - 일반 int 검사의 0 허용 집합에 `'base_revision'`을 추가한다. 그래야 0이 일반 `INVALID_TOOL_ARGUMENTS`가 아니라 명시 메시지로 거절된다.
   - 끝에 `if name=='propose_scene_3d':__import__('scene_spec').validate_proposal(args)`를 추가한다.
3. `chat_protocols.tool_definitions`(트랙 A): `if name=='propose_scene_3d':schema=deepcopy(__import__('scene_spec').PROPOSAL_SCHEMA)`
   - `test_chat_protocols` 도구 개수 단언은 의도된 diff다.
   - 크기 4979 bytes compact이므로 4096 토큰 여유 측정 후 결정한다(대안 2362 bytes).
4. `production_tools.execute`(트랙 A): local_tool 분기 이름 집합에 `'propose_scene_3d'`를 추가한다. Conflict는 `STALE_VERSION`, ValueError·KeyError는 `VALIDATION_OR_HUMAN_APPROVAL_REQUIRED`로 기존 처리를 그대로 쓴다. AUTO_DRAFT 확장은 금지다.
5. `local_creation_tools._execute`(트랙 A): `if tool=='propose_scene_3d':return propose_scene(store,c,p,name,args,run,call)`
   - 동작:
     - `shot=production_context.shot_key(p,args['shot_id'])`
     - `SELECT id FROM scene_records WHERE project=? AND conversation=chat_sessions.current(p) AND shot=production_context.shot_id(p,shot)`
     - 결과가 없으면 `dict(status='blocked',code='SCENE_NOT_FOUND',retryable=False)`
     - 있으면 `scene_project.handle(c,store,p,name,'scene_propose',dict(song=name,scene_id=row,base_revision=args['base_revision'],operations=args['operations']),provenance=dict(run=run['id'],call=call['id'],model=run.get('provider_model'),mode=run['engine']))`
   - 결과는 압축 영수증이다: `status='proposed'`, `scene_id`, `proposal_id`, `base_revision`, `changes=[{target,id,field}]`, `applied=False`, `approval_required=True`, `render_requested=False`, `external_calls=0`.
   - scene_proposals는 SQLite 행이라 `execute()`의 SAVEPOINT가 롤백한다. `keys` 튜플은 바꿀 필요가 없다.
6. `scene_project.handle`(트랙 C / S7b): `scene_propose` 분기에 선택 인자 `provenance=None`을 추가하고 `if provenance:item['provenance']=dict(provenance)`를 넣는다(위 점검 결과상 UI 안전).
   - 승인 시 차단·미확인 자산 교체가 거절되는지 테스트한다(`resolve_assets(require_rights=True)`가 `scene_review`에서 이미 집행).
7. `agent_preferences`(트랙 A): `propose_scene_3d`는 READ_TOOLS에 넣지 않는다(read_only에서 차단). AUTO_DRAFT_COMMANDS에도 넣지 않는다.
8. `chat_general.ALLOWED_TOOLS`(트랙 A): `'propose_scene_3d'`를 추가한다. `scene-status`는 기존 `search_project_context`로 이미 도달하므로 별도 노출이 필요 없다.
9. UI(트랙 B / S8):
   - `toolLabels['propose_scene_3d']='3D 구도 변경안'`
   - reviewTargets에서 Scene Studio 이동, dirty 3D 입력 보존
   - Scene Studio 제안 카드에 provenance(모델·mode) 표시는 S7b
