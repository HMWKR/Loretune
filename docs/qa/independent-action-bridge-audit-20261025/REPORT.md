# action/grant bridge 독립 감사 — 2026-10-25

**admission까지 연결된 모의 경로의 승인 해시·단일 예약·동시 예산·멱등성 대조는 통과했다. 두 가지 기능 계약 결함을 재현했다: 새 action job의 모델 인계 누락(B01), 의미적으로 잘못된 tool 요청의 오류 기록/횟수 제한 누락(B02).** 외부 제출·지출 초과·AI 권한 상승은 관측하지 않았다.

| 검사 | 결과 |
|---|---|
| 독립 bridge case16개 |14 pass /2 fail(B01/B02) |
| 선택한 비HTTP 회귀 |95개 통과, 실패0·오류0 |
| 기존 F01–F04 |4개 control 통과 |
| 기존 R01/R02 및 인접 control |16개 통과, 추가 guard12개 통과 |
| 새 action claim의 Store 자산권리 통합 |미구현 gap 확인; explicit false 단위 gate와 구별 |
| HTTP/UI/실공급자 |이번 감사에서 미실행 |

## B01 — Medium: 새 action job이 모델 전환 인계에서 누락됨

- **위치:** snapshot/chat_protocols.py:55–60, 특히58. 신규 job 구조는 snapshot/action_execution.py:79–81.
- **재현:** 실제 Store 경로로 project→guided_plan→production_run 준비. 아직 UI가 없는 사람 controller 대신 서버 함수로 immutable action/grant 작성. Store `production_tool(request_media_generation)`로 job/예약을 생성. 서버가 같은 workspace/project로 필터한 action_jobs를 `chat_protocols.handoff(project,'A',jobs)`에 전달.
- **기대:** 기존 내부 job ID와 prepared 상태가 인계에 포함되어 새 모델이 같은 job을 조회할 수 있음. 모의 mode도 유지.
- **실제:** source job은 prepared이나 handoff의 jobs=[]이다. `context.song`을 가진 구 generation_jobs만 필터하고, 신규 action_jobs body에는 해당 필드가 없기 때문.
- **영향:** 계획·설정 문맥은 전달돼도 진행 작업 정보는 사라진다. UI/live handoff가 아직 연결되지 않아 현재 실제 모델 전환 사고나 중복 생성은 관측하지 않았다. 함수/데이터 통합 반례다.
- **관련:** MS-FR-11/14, MS-AT18/22. SPEC-MS-001 §7.2.
- **최소 수정:** 서버의 workspace/project 권한 검사 후 공통 job projection(id/state/mode)을 구성해 인계. 두 job형식의 소유권을 명시적으로 지원하고 모의/실제 구분을 유지. 필터를 단순 삭제해 외부 프로젝트 job까지 통과시키는 수정은 피해야 한다.
- **검증 증거:** audit-results.json `B01-new-action-job-handoff`; audit.py의 첫 Store fixture.

## B02 — Medium: semantic invalid tool 요청이 횟수 제한과 구조화 결과를 우회

- **위치:** snapshot/production_tools.py:53–60, :73–78; app.py:345–353; action_execution.py:129–142(request_from_plan의 lookup).
- **재현:** 정상 run에서 스키마는 맞지만 존재하지 않는 action_id를 가진 request_media_generation을 서로 다른 call ID로10회 Store에 요청.
- **기대:** 존재하지 않는 action 인수를 수정 가능한 인수 오류로 반환하고 제한된 수정 횟수 후 중지. 작업 예약은 없어야 하며 오류/호출 결과가 run에 남아야 한다.
- **실제:** 각 호출은 ValueError로 거부되지만 run은 `accepting_tools`, `repair_count=0`, `calls=[]`. job0/예약0. request_generation callback 오류는 validate() 밖에서 발생해 호출 기록 append에 도달하지 않고 Store transaction이 rollback된다.
- **영향:** 잘못된 ID를 반복하는 모델 루프를 해당 run의 repair2회/tool8회 계약으로 제한하지 못한다. 현재 live loop가 없으므로 실제 비용 폭주를 주장하지 않는다. 정상 거부 자체는 안전하게 동작한다.
- **관련:** MS-FR-07, MS-AT12, SPEC-MS-001 §6.4/9.3/12.2.
- **최소 수정:** semantic errors를 명시적 code/status ToolResult로 변환하고 해당 호출·repair를 저장. 실행 side effect는 savepoint 등으로 rollback하되 오류 기록과 카운터는 보존. 승인 필요, 오래된 문맥, 일시 장애와 잘못된 ID를 같은 오류로 합치지 않는다.
- **검증 증거:** audit-results.json `B02-semantic-invalid-arguments-bounded`; audit.py의10회 Store loop.

두 발견 모두 개발 중 모의 연결의 correctness 결함이며 SaaS 보안 취약점이나 실제 공급자 피해로 분류하지 않는다.

## 확인된 긍정 계약

- **승인 target hash:** action input/model을 바꾸거나 grant money를 바꾸고 기존 hash를 유지하면 admission 거부·예약0. 현재 settings 변경도 과거 run/action 문맥으로 통과하지 못함.
- **hash의 정확한 범위:** action hash는 id/plan_id·revision/context/role/release/inputs/options/dependencies/mode/connection을 묶는다. grant hash는 action_hashes·가격버전·money·승인자·만료를 묶는다. 계획의 모든 서술 필드 자체 hash가 별도로 승인된 것은 아니므로 “전체 자유형 계획의 cryptographic binding”으로 확대하지 않는다. 공개 plan edit 경로의 변조 반례는 이번에 입증하지 않았다.
- **단일 예약/job:** 동일 action을 다른 call ID로 요청해도 같은 job ID 반환, reservations1/action_jobs1. 같은 call ID에 다른 action ID를 넣으면 Conflict.
- **동시 예산:** 1USD 예산에 다른 두 action을0.70USD씩 동시에 admit하면 하나만 허용, reserved0.70USD. queue insert 실패 rollback 등은 기존 nonHTTP 대조시험에서도 통과.
- **철회:** 새 call로 revoked grant 실행 거부. 이미 prepared인 job은 claim 시 revoked grant로 blocked되고 미전송 reservation만 cancelled/released.
- **권한/endpoint 주입:** 모델 인수의 actor/endpoint 추가는 invalid_arguments, 예약0. 모델용 tool 목록에는 grant 발급/공식 IP 확정 없음. actor='model' grant 발급 거부는 기존 action 회귀에서 통과.
- **공식 설정 분리:** 사람 grant와 모의 job admission이 canon/ontology를 승인하거나 생성하지 않음.
- **unknown:** claimed→recover→outcome_unknown 이후 reopen/claim은 같은 state를 유지, reservation uncertain. 새 작업으로 재발행하거나 예약을 해제하지 않음.
- **모의 표시:** admission receipt에 mode=rehearsal/external_calls0/실제AI미실행 안내. 공개 state는 project별 rehearsal_jobs로 분리하고 raw input을 제외. 모델 registry의 live_execution은 false. 이 코드와 API 기록에서 가짜 receipt를 live 통합 완료로 표시한 사례는 찾지 못함. UI 실제 시각 표시는 이번 범위 밖.

## G01 — 미구현 통합 gap: 실제 자산 권리와 action claim 연결

`action_execution.claim(...rights_valid=False)`가 blocked/release로 처리되는 것은 확인했다. 그러나 이 함수의 기본값은True이며, 실제 Store asset_rights 조회/controller는 연결되지 않았다.

별도 synthetic 검증에서 정상 Store로 등록한 PNG의 hash를 action input에 넣고 admission 후 Store asset_rights를 blocked=True로 바꿨다. default claim은 claimed가 됐고 external_calls0이었다. 증거 `rights_gap.py`, `rights-integration-gap.json`.

**이는 실제 외부 전송 우회 결함으로 보고하지 않는다.** 현재 새 action dispatch caller 자체가 없으며 docstring도 caller supplied rights_valid를 전제로 한다. 다만 `rights_valid=False` 단위시험을 MS-AT34의 실제 자산철회 통합 통과로 사용하면 안 된다. Live 연결 전 서버가 input hash/asset ownership/현재 rights/dependency approval/model/connection을 다시 해석하는 필수 pre-submit controller가 필요하다. 기본 True 대신 mandatory checker/false default도 누락 방지에 도움이 된다.

사람용 action/grant 생성 화면, live dispatch, live model 선택·capability/연결 검사, 실제 adapter receipt/수집/정산은 구현 중 gap으로 유지한다. absent button 자체를 새 결함으로 등록하지 않았다.

## 범위, 버전 및 증거

- 원문 인계와 milestone report를 읽고 source를 고정했다. snapshot 시각 **2026-10-25T10:18:42.800581+00:00**.
- `snapshot-manifest.json`에 source path/mtime_ns/bytes/SHA256. `source-drift.json`의 종료 비교에서 snapshot 대상 파일 변경0.
- 모든 실행은 snapshot import와 temporary synthetic DB. 네트워크 connect/bind를 harness에서 금지. 사용자DB/소스/.env/키/인증파일 읽기·수정 없음. 이번 실제 Anthropic/Kling 호출0.
- 기능 세션의 승인된 HTTP시험/서버재시작/Anthropic 실행은 **인계 정보**이며 이번 독립 실행 증거가 아니다. 기존 승인 여부를 번복하지 않았고 별도 listener를 요청하거나 실행하지 않았다.
- 기존 F/R 회귀 artifact는 `after-evidence.json`, `adjacent-results.json`, `guard-results.json`, control_*.py. 최신 whole suite가 아니라 선택된95개 nonHTTP suite만 실행했다.
- 이전 감사 디렉터리는 보존했다. 산출물은 independent-action-bridge-audit-20261025에만 작성.

재현:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-audit-20261025/audit.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-audit-20261025/rights_gap.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-action-bridge-audit-20261025/run_controls.py
```

**준비 판정:** 로컬 모의 admission 데모는 가능. 모델 전환/복구 루프 연결에는 B01/B02 수정 필요. 실제 유료/외부 제출 pilot은 G01 및 기존 provider/권한/수집/정산 미완료 때문에 보류. full SPEC-MS-001/38AT 통과가 아니다. 이번 감사에 새로운 denied/pending/uncertain tool action은 없으며 추가 권한 없이 완료했다.
