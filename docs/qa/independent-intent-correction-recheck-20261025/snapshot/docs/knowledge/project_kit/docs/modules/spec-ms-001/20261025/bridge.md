# B01/B02 및 사람용 승인 경로 독립 재검증

**B01·B02의 원래 반례는 수정됐다. 다만 신규 인접 결함 B03이 남는다: 승인된 이미지 작업을 인계한 뒤 채팅 모델만 바꾸면 해당 미디어 작업의 실행이 차단된다.** B01의 “job 인계 포함” 성공과 “인계 후 작업 계속 실행”은 별도 판정이다.

## 결과 요약

| 검사 | 결과 |
|---|---|
| 기존 bridge 독립16case |16/16 통과(B01/B02 포함) |
| 오류 replay/savepoint 추가 검사 |2/2 통과 |
| 사람용 승인→실행 대조 |변경 없는 control 통과, chat-only 변경 B03 실패 |
| 선택 비HTTP 회귀 |107개 통과, 실패0/오류0 |
| F01–F04 |4개 control 통과 |
| R01/R02와 인접 경계 |16개 통과, 추가 guard12개 통과 |
| 브라우저·HTTP·실공급자 |미실행 |

각 시험 집합은 중복되는 동작을 포함하므로 합산 완료율로 계산하지 않는다. 새 승인 UI는 이번에 화면 클릭이 아니라 해당 Store command 경로를 시험했다.

## B03 — Medium: chat-only 설정 변경이 승인된 media job을 차단

**정상 Store mutation 경로, synthetic WAV/단색 이미지, temporary DB로 재현했다. 데이터베이스에 비정상 상태를 직접 삽입하지 않았다.**

재현 순서:

1. 합성2초 WAV를 업로드하고 music_structure 확정.
2. guided_plan 생성·적용, action_propose, action_decide(approved).
3. model_settings에서 chat만 `anthropic-haiku-5-5`로 변경. image/video와 action 입력/가격/승인은 그대로.
4. model_handoff: 기존 prepared job ID와 mode=rehearsal을 정확히 받음.
5. 같은 카드 revision으로 action_execute.

| 상태 | 변경 없는 control | chat-only 변경 |
|---|---|---|
| handoff |같은 prepared job 유지|같은 prepared job 유지|
| action job |collected|**blocked**|
| take |1|null|
| 예약 |settled, actual0|cancelled, actual null|
| canon |빈 상태 유지|빈 상태 유지|

**기대:** 다음 채팅 모델 선택이 이미 승인된 media action의 입력/실행 모델/가격을 바꾸거나 실행을 막지 않아야 한다. 현재 권리·grant 철회나 실제 미디어 의존 변경은 별도로 검사한다.

**실제 원인:** `rehearsal_workflow.py:59`가 현재 `model_selection.snapshot(p)` 전체 hash를 claim에 전달한다. `model_selection.py:56`의 snapshot은 chat을 포함한 model_settings/history까지 포함한다. `action_execution.py:108–115`가 기존 action context hash와 다르다고 blocked/release 처리한다.

**영향/범위:** UI가 호출하는 서버 command에서 승인된 모의 작업이 멈춘다. 외부 모델 호출·과금 손실·입력변조는 없었다. unverified chat 모델 선택도 현재 제품에서 허용된 설정이며 실제 채팅 모델을 호출한 것은 아니다.

**관련 계약:** MS-FR-09/11, MS-AT15/18, SPEC-MS-001 §3.1/7.2. 기존 `model_selection.update`의 “기존 media jobs와 snapshot은 바꾸지 않음” 의도와도 충돌한다.

**최소 수정 제안:** chat run의 freshness 문맥과 승인된 media action의 문맥을 분리한다. media input/model/price/dependency는 승인 고정본을 유지하고 claim에서 현재 grant/권리/관련 media 의존 변경만 재검사한다. 전체 freshness/권리 검사를 제거하는 방식은 피한다. chat-only 변경/미디어 선택 변경/실제 입력 변경을 별도 control로 두어 후자의 차단은 유지한다.

증거: `human_flow.py`, `human-flow-results.json`. B03 체크포인트는 최종 보고서 전에 CHECKPOINT.md에 남겼다.

## B01 재검증 — 통과

기존 실제 Store admission fixture를 그대로 사용했다. 새 구현은 `action_execution.project_jobs`가 DB 소유권으로 필터한 공통 projection을 만들고 `Store model_handoff`가 이를 기존 `chat_protocols.handoff`로 전달한다.

이제 handoff에는 정확한 내부 job ID, state=prepared, mode=rehearsal이 포함된다. 사람용 승인 흐름에서 chat 모델 변경 뒤에도 같은 job이 포함됐고, 다른 project B에는 jobs=[]였다. raw action body에는 여전히 context.song이 없지만 더 이상 raw body를 handoff 계약으로 전달하지 않는다. 서버 projection 경로로 수정된 점을 반영해 검사했으며, “raw helper도 임의 모든 job형식을 처리한다”고 주장하지 않는다.

읽고 실행한 수정 회귀: `tests/test_rehearsal_workflow.py:test_b01_handoff_preserves_new_job_after_model_switch`. 이 시험은 인계 내용까지 검사하며 이어지는 action_execute를 검사하지 않아 B03을 발견하지 못한다.

## B02 재검증 — 통과

이전과 동일하게 정상 run에서 존재하지 않는 action ID를 서로 다른 call ID로10회 요청했다.

- 첫 응답: status=invalid_arguments, code=INVALID_ACTION_REFERENCE, retryable=true.
- 두 번째 응답: 같은 code, retryable=false.
- run state=invalid_arguments, repair_count=2, calls2가 DB에 저장됨.
- 나머지8회는 RUN_NOT_ACCEPTING_TOOLS로 거부. jobs0/reservations0.
- 첫 invalid call을 동일 ID/입력으로 재전송해도 repair1/calls1만 기록됨.
- 예약 후 job 저장 시 synthetic ValueError를 주입한 별도 시험: savepoint가 reservation/job/admission을 모두 rollback하고, blocked ToolResult만 run calls에1건 저장. 승인/의존 필요는 invalid reference repair와 구별됨.

읽고 실행한 수정 회귀:

- `tests/test_rehearsal_workflow.py:test_b02_invalid_references_are_persisted_and_bounded`
- `tests/test_action_tool_bridge.py:test_foreign_plan_and_stale_revision_never_reserve`
- `tests/test_action_tool_bridge.py:test_revocation_and_scope_substitution_fail_closed`

증거: `audit-results.json`, `error-guard-results.json`, `recheck.py`, `error_guards.py`.

## 유지된 승인·예산·안전 계약

- action input/model 및 grant money hash 변경은 예약 전 거부.
- 동일 call ID·다른 action Conflict, 같은 action의 다른 call은 동일 job/예약1 반환.
- 서로 다른 두 action의 동시0.70USD 요청은1USD budget 안에서 한 개만 예약.
- revoked grant는 구조화 blocked로 반환. prepared claim에서 철회되면 미전송 예약만 release.
- claimed 복구는 outcome_unknown 및 uncertain 예약 유지, reopen/claim으로 재발행하지 않음.
- actor/endpoint 추가 인수 차단, grant가 공식 IP를 승인하지 않음.
- 사람용 흐름에서 후보 수집·결과 검토는 selected take나 canon을 자동 변경하지 않는 기존 회귀 통과.
- 기존 F/R의 철회 전 제출, cancel race, 관계 이력, fractional timebase/audio/caption, 미전송 quota 반환 control도 유지됨.

기존 G01의 범용 asset→claim 권리 integration 전체 완료를 새로 선언하지 않는다. 현재 사람용 workflow는 외부 입력 자산을 전송하지 않는 synthetic text→solid PNG이며, shot revision 검사와 결과 hash의 Store 권리 검사만 수행한다. Live provider 연결 전 권리/connection/model 정책 controller는 여전히 별도 범위다.

## 스냅샷, 한계, 재현

capture: **2026-10-25T10:42:51.959689+00:00**. `snapshot-manifest.json`에 Python/test/index.html의 mtime_ns/bytes/SHA256을 고정했다. 종료 `source-drift.json`에서 대상 변경0. 모든 import는 snapshot만 사용했다. 보고서 완성 여부와 무관하게 현재 source와 실제 시험 결과를 우선 근거로 사용했다.

이전 결과는 `before-audit-results.json`으로 복사해 보존했다. 원래 감사·제품 소스·사용자DB는 수정하지 않았다. 모든 보고서/fixture/미디어는 새 independent-action-bridge-recheck-20261025 안에 작성했다. 외부 API/유료호출/키조회/서버재시작/listener bind0. 이번 작업에 새 도구 거부나 불명 실행 결과는 없다.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-recheck-20261025/recheck.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-recheck-20261025/human_flow.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-recheck-20261025/error_guards.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-recheck-20261025/run_controls.py
```

**판정:** B01/B02 수정 수용. 승인 후 모델 전환을 포함한 local demo에는 B03이 남음. limited pilot/full spec 및 실제 UI 사용성은 완료로 선언하지 않는다.
