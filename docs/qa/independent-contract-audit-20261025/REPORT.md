# Loretune 독립 계약 감사 — 2026-10-25

**가장 먼저 수정할 항목은 F01: 큐 등록 뒤 자산 사용권을 철회해도 제출되는 경로다.** 정상 로컬 Store 입력으로 재현했으며 가짜 공급자 제출 1회가 관측됐다. 실제 외부 전송·유료 호출은 0회다. 추가로 취소/완료 경합, 온톨로지 관계 영향 누락, 컷 길이 누적오차를 재현했다. “영상 API만 해결하면 완료” 상태로 판정할 수 없다.

| 준비 수준 | 판정 | 근거 |
|---|---|---|
| Local demo | 조건부 가능 | 단일 사용자·고정 프리셋·수동 계획/승인·정상 프레임 정렬 컷의 로컬 제작 가능. 정밀 컷 길이 F04 해결 필요. 실제 멀티모델 연결 시연으로 표현 금지 |
| Limited pilot | 보류 | 유료/외부 전송 전 F01 필수 수정. 사용자별 인가·grant/action/연결 바인딩·실제 파일 회수·청구 대사·사용 범위 확정 필요. 통제된 내부 무과금 시연과 구별 |
| Full spec | 미충족 | 신규 28 MS-FR/38 MS-AT와 기존 96 FR/143 API의 전체 통과 없음. 실제 12개 교차 조합 미시험. 미구현과 결함을 아래에서 분리 |

## 1. 즉시 전달할 재현 결함

### F01 — High: 큐 등록 뒤 입력 자산 사용권 철회가 외부 제출을 막지 못함

- **관측 수준:** 정상 Store mutation→worker 경로, synthetic PNG·temporary SQLite·fake provider. DB 변조로 만든 반례가 아니다.
- **위치:** snapshot/app.py:277(권리 철회는 로컬 render jobs만 처리), :411(등록 시 gate 검사), :618–621(워커는 gate 존재/만료만 검사); snapshot/generation_queue.py:49–61(견적 만료만 재검사).
- **재현:** 합성 PNG 업로드→시작 프레임 지정/승인→생성 준비→서버 synthetic gate와 0.70 USD synthetic 예산으로 등록→같은 PNG에 `asset_rights blocked=True`→`process_generation()`.
- **기대:** 미제출 상태를 차단하고 사용권 재확인 안내. 공급자 submit 0회; 미전송 예약만 적절히 정리.
- **실제:** 권리 상태 `blocked=true`, submit 1회, job `accepted`.
- **영향:** 등록과 제출 사이 권리 변경 시 철회된 자료가 새로 전송될 수 있다. 현재 fake 시험이므로 실제 고객 자료가 전송됐다는 의미가 아니다.
- **관련 계약:** FR-016/018, MS-FR-06/23, MS-AT34, SPEC-MS-001 §12.3. MS-AT30의 binding 재검사도 인접 범위다.
- **최소 수정:** job에 입력 asset hash와 gate/grant identity·version·연결을 고정하고 worker의 prepared→submitting 전이에서 현재 권리/승인/연결과 재대조. 권리 철회 처리에 generation job 영향도 포함. 현재 남은 gate가 다른 작업용으로 교체된 경우도 만료 검사만으로 실행하지 않게 한다. 미접수/기접수 비용 처리는 구별한다.
- **재검증:** 등록 후 권리 철회, gate 교체/철회, 제출 후 철회를 각각 검증. 기준 시점과 동시성 정책을 명시해야 한다.

### F02 — Medium: 늦게 실패한 취소 응답이 완료 상태와 수집 URL을 덮어씀

- **관측 수준:** GenerationQueue 함수의 결정적 event interleaving. 현재 서버는 단일 worker이므로 이 경합의 현재 UI 도달성은 입증하지 않았다. 다중 worker/동시 poll 도입 시 문제가 되는 모듈 계약 결함이다.
- **위치:** snapshot/generation_queue.py:159–168, 특히 예외 처리의 오래된 `job` 전체 저장.
- **재현:** accepted 작업 취소→send_cancel이 cancel_sent 저장→fake cancel 처리 도중 poll이 완료를 받아 `cancelled_result`와 result URL 저장→cancel TimeoutError.
- **기대:** 이미 기록된 cancelled_result와 result URL 보존, 취소 응답 미확정 정보만 추가.
- **실제:** `cancel_sent`, `result=null`로 회귀. 완료 정보 재조회 전까지 유실되며 원격 URL 만료 시 회복이 어려울 수 있다.
- **관련 계약:** FR-051/052, MS-FR-20, MS-AT32.
- **최소 수정:** except 트랜잭션에서 latest job 재조회, 최신 상태/result를 유지하고 cancel error 필드만 변경. 상태 전이의 monotonicity/CAS 정책 적용.
- **한계:** 중복 청구가 발생했다는 증거는 없다. 기존 비용 예약은 유지됐다.

### F03 — Medium: 승인 그래프의 관계만 바꾸면 샷 영향 분석에서 누락됨

- **관측 수준:** ontology/projection module 시험. 현재 수동 UI는 character/place/style 중심이며 관계 작성 UI는 없다. 현재 사용자 화면에서 관계 편집을 수행했다는 주장이 아니다.
- **위치:** snapshot/project_ontology.py:55–66.
- **재현:** character Mira→references→asset A 그래프 승인→Mira를 shot에 bind→entity 본문은 그대로 두고 relation target만 asset B로 바꿔 새 버전 승인→impact 조회.
- **기대:** 사용한 참조 관계 변경에 대한 영향 1건 이상, 과거 사용 관계/출처 보존.
- **실제:** graph digest는 변경됐으나 `impact=[]`; semantic_context에는 revision/entities만 있고 관계가 없다.
- **관련 계약:** FR-023/024, AT-024-A 및 G1 최소 의존성 계약. MS-AT19/29는 인접 문맥/부분보존 범위이며 이 반례 자체가 그 전체 시험은 아니다.
- **최소 수정:** bind 시 실제 사용한 관계와 연결 자산의 ID/hash/version을 보존하고 그 의존 집합을 비교. 전체 graph digest만 비교해 무관한 샷까지 재검토시키지 않는다. 과거 version 조회로 export provenance도 해석 가능하게 한다.

### F04 — Medium: 허용된 소수 초 컷이 합쳐지면 타임라인 길이가 보존되지 않음

- **관측 수준:** 실제 로컬 FFmpeg/FFprobe, synthetic 정지영상 30개. 공급자/사용자 파일 없음.
- **위치:** snapshot/editing.py:55–72(0.125초 이상, millisecond 값 허용); snapshot/renderer.py:58–79(각 clip 24fps 인코딩), :12–28(길이 검증).
- **재현:** 0.130초 컷 30개, preview 24fps, 총 요청 3.900초.
- **기대:** 명시된 timebase 정책으로 승인 사양을 표현하거나 저장 전에 변환/반올림 차이를 알림.
- **실제:** 3.750초, -0.150초. verify_output에서 `출력 영상 길이·해상도 검증에 실패했습니다.` 정상 허용 입력이 렌더 실패로 이어짐.
- **관련 계약:** FR-056/067; AT-067-A. MS-AT28의 타임코드 보존 하위 계약과 관련되지만 생성 사운드 분리 시험은 아니다.
- **최소 수정:** clip boundary를 정수 frame/timebase로 정하고 전체 타임라인 기준 오차 분배 또는 명시적 quantization 검토를 제공. 오디오/자막과 export manifest에도 같은 경계를 사용. 단순히 verify tolerance만 늘리면 드리프트가 숨겨진다.
- **긍정 대조:** 기존 2초 trim/order/click-track/한국어 자막/manifest 시험은 통과. 10초1080p baseline이 임의 30컷 조합을 증명하지 않는다. 실패 출력은 검증에서 차단되므로 잘못된 결과를 납품 완료로 표시한 반례는 아니다.

모든 재현은 `reproduce.py`, 실제 값은 `counterexamples.json`. 재현 스크립트의 socket 연결은 강제로 차단되어 있다. 테스트는 결함을 관측하는 characterization이며 “제품이 통과했다”는 뜻이 아니다.

## 2. 요구사항→시험→증거와 과장 여부

신규 원문 `07_Chat_Directed_Multimodel_Production_Spec.md`는 **811줄 / 72488 bytes**, SHA256 `962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`. 제공된 첨부 크기와 일치하며 로컬에서 원문을 읽었다. Library 재수집은 필요하지 않았다. 문서 §15.2의 등록 ID는 SPEC-MS-001이다.

기존 기준은 Master_Specification.md의 기능/공통 계약, 특히 FR-016/018–024/043–053/056/067–069와 요구사항 장 원문을 대조했다. 이 감사가 원본 문서 5354줄의 모든 외부 공급자 사실을 재검증한 것은 아니다.

`ms-requirement-test-evidence.json`에는 28개 MS-FR 각각의 MS-AT 링크와 38개 MS-AT의 원문 입력/통과조건/증거/한계를 넣었다. 읽기용 표는 `ms-requirement-test-evidence.md`.

| 신규 38AT 분류 | 수 | 의미 |
|---|---:|---|
| partial | 24 | 일부 함수/로컬 경로만 존재하거나 시험됨; 전체 pass 아님 |
| not implemented | 10 | 해당 전체 실행 계약 없음. 개발 중 범위로 분류 |
| not fully verified | 1 | 코드 경계는 보이나 해당 통합 시험 없음 |
| counterexample | 3 | AT28/32/34 관련 하위 계약 반례. 상세 도달성은 F01/F02/F04 참조 |
| 전체 수용 pass 선언 | 0 | 전체 시험 자료·실행·증거 충족을 선언하지 않음 |

F03은 기존 FR-024의 독립 반례라 위 MS 3건에 중복 합산하지 않았다. 부분 통과 수와 기존 96FR/143API 수를 더해 기능 완료율로 계산하지 않는다.

기존 `mvp-flow-audit-20261025/requirement-qa-matrix.json`은 96건 중 partial 59, not implemented 37로 표시하며 원문 전체 수용 미선언을 명시한다. 이 파일에서 거짓 전체 pass 표시는 찾지 않았다. 다만 `acceptance_report.py`의 과거 FR-067 “functional_requirements_verified=True / 로컬 기능 기준 모두 met” 문구는 F04가 반증하는 허용 입력 범위까지 확대해서 읽어서는 안 된다. 특정 fixture의 검증 범위로 좁히거나 경계 결함 해결 전 partial로 되돌리는 것을 제안한다. 원본 보고서는 수정하지 않았다.

## 3. 온톨로지와 안전 계약: 확인된 범위/남은 범위

- **stable identity/역할 분리:** scope/type/source key 기반 UUID5, 역사 버전 포함 type 재할당 금지, dangling/cyclic 관계 거부, candidate와 승인 version 분리를 대조시험했다. 이름 변경 자체가 새 identity를 만들지 않는 수동 편집 경로도 통과. LLM이 기존 entity를 새 UUID로 다시 내보내는 semantic dedup은 별도 문제로 미검증이다.
- **provenance:** Anthropic fake 응답은 source_id와 원문 substring을 검사하고 잘못된 인용을 거부한다. 정확한 offset·원본 문서 버전·동일 excerpt의 여러 위치는 schema에 없으므로 완전한 source-span 추적이라 부르지 않는다. 수동 evidence는 작성자 진술이며 외부 사실 검증이 아니다.
- **scope/예외:** local project proposal의 타 작품 적용 거부, 활동기/시간 선택, IP와 song preference 예외·paused 복귀·과거 문맥 보존을 확인했다. 실제 다중 조직 RBAC는 미구현이며 single-local-workspace로 표시된다. 이것을 현재 원격 SaaS 인가 침해로 과장하지 않는다.
- **approved pinning/partial change:** ontology snapshot deep copy와 restore가 새 revision을 만드는 것은 통과. entity 변경 영향은 있으나 관계 의존성 F03이 남는다. 모든 과거 승인본을 최신 공식 설정으로 자동 덮어쓰는 현상은 관측하지 않았다.
- **conflict/transaction:** stale proposal/apply 거부, 동일 proposal 이중 적용 거부, SQL trigger failure atomicity, outer rollback 보존이 통과했다.
- **reuse lineage:** project_ontology의 외부 참고 proxy는 source song/shot/take/hash로 구별하며 동명 개체 자동 병합을 하지 않는다. full relationship/rights lineage across organization은 구현 범위 밖이다.
- **execution binding:** 현재 fal 한 경로는 admission에서 모델/10초/0.70USD/입력 gate를 검사하고 request digest mismatch를 거부한다. generic production_action/grant/connection/price revision의 불변 계약은 아직 개발 중 미구현이다. 신규 request_media_generation 도구는 blocked라 이것을 grant 우회 exploit으로 보고하지 않는다.
- **budget/idempotency:** SQLite transaction의 동시 reservation 상한, request replay, uncertain 보류, 늦은 정산/환불 구별이 대조시험에서 통과했다. 모든 프로젝트를 아우르는 조직 총한도와 chat/background 비용 합산은 미검증/미구현이다.
- **failure recovery:** receipt loss는 reconciliation_required와 예약 유지로 처리하고 reopen 뒤 재제출하지 않았다. result_ready는 URL 확보이며 imported/선택/승인/비용확정과 구별한다. cancel late completion의 정상 순서는 통과하나 F02 경합이 남는다.
- **미디어/manifest:** 정상 trim 순서·click offset·자막 텍스트/시간·manifest 타임라인을 확인했다. F04 누적 오차, generated audio를 별도 track/asset으로 보존하는 멀티모델 계약은 남는다. 현재 fal은 generate_audio=False이며 renderer는 원영상 음원을 제외한다.
- **입력/secret/redirect:** fake provider 허용 host/receipt, Anthropic exact endpoint·size·timeout·redirect 거부, 예외 secret redaction을 실행했다. 현재 실제 키·환경파일·인증파일 값은 열지 않았다. 전반 취약점 스캔/모든 로그·브라우저·백업·내보내기의 완전 비밀 누출 부재를 주장하지 않는다.

## 4. 실행 증거와 동시 개발 구분

- snapshot capture: **2026-10-25T09:32:56.821522+00:00**. 51개 파일을 허용된 QA 폴더 안에 복사했다. `snapshot-manifest.json`에 각 source path, bytes, mtime_ns, SHA256 기록.
- 독립 반례 4개: `counterexamples.json`, `reproduce.py`. synthetic temporary DB는 테스트 후 정리됨. 보고서/스냅샷과 synthetic 임시 fixture만 작성. 최초 미디어 렌더의 중간 파일은 시스템 임시 폴더에서 자동 정리됐고, 재현 harness는 이후 임시 경로도 QA 디렉터리로 고정했다. 제품 소스/사용자 데이터는 수정하지 않았다.
- 대조 회귀 **67개 통과, 실패 0, 오류 0**: `controls.log`, `run_controls.py`. ontology, project ontology의 비HTTP case, Anthropic fake/transport, generation queue, ledger, fal fake, model selection, media roundtrip, preference, settings, workflow. 기존 133 전체 suite 재실행을 주장하지 않는다.
- 초기 실행 기록 `controls-initial.log`도 보존했다. 테스트 import 경로 오류는 harness sys.path 수정으로 해결. 별도 HTTP 시험 하나는 아래 제약으로 제외했다. 제품 결함과 harness 문제를 분리했다.
- `source-drift.json` 기록 시점에 app.py와 model_selection.py가 변경됐다. app 변경은 tool job 조회의 context.song 스코프 수정이며, catalog에는 release_id/connection_id/revision_pinning 메타데이터가 추가됐다. 네 가지 발견의 해당 로직 변경은 당시 diff에 없었다. 종료 시 `source-drift-final.json`에는 production_tools.py와 tests/test_guided.py 변경도 추가 기록했다. 최신 빌드에서 반례를 다시 실행한 것은 아니므로 모든 결론은 snapshot 기준이다.
- 공급자 완료 후 fal token403으로 수집 미완료, Anthropic 실$0.01 승인 미응답은 제공된 인계 정보이며 이번 감사의 실API 관측이 아니다. 재접근·우회·실호출을 수행하지 않았다.

재현 명령(저장소 루트):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-audit-20261025/reproduce.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-audit-20261025/run_controls.py
```

## 5. 남은 제약과 권장 순서

1. 기능 담당이 F01의 제출 직전 재검증을 수정하고 동일 synthetic 반례가 submit 0회가 되는지 확인한다.
2. F04의 timebase 계약을 정하고 30컷·소수길이·오디오/자막 경계 대조를 추가한다.
3. 다중 worker/이벤트 도입 전에 F02를 수정하고, 관계 추출 연결 전에 F03의 의존성 snapshot을 보완한다.
4. SPEC-MS-001의 모델 선택 UI와 local rehearsal를 실제 공급자 연결 완료로 표시하지 않는다. 실행 가능한 action/grant/계획/계정/가격 계약을 먼저 연결한 뒤 별도 승인된 실API 평가로 12조합을 검증한다.

**블로커 기록:** optional `tests.test_project_ontology...test_http_stale_ontology_is_conflict_and_request_retry_is_idempotent`가 격리 fixture의 `127.0.0.1:0` 새 HTTP listener bind에서 `PermissionError: Operation not permitted`로 거부됐다. listener는 열리지 않았으며 공용 서버 재시작은 시도하지 않았다. 같은 bind를 재시도/에스컬레이션하지 않고 해당 시험을 제외했으며 나머지 67개와 네 반례를 완료했다. 상태는 **해당 HTTP 검증 미완료/작업 거부**, 전체 감사는 완료다. 도구의 자동 승인 심사 거절 메시지는 없었고, 관측한 것은 sandbox bind 오류다.
