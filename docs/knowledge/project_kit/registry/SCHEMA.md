# 프로젝트 지식 레지스트리 계약 v1.0

이 문서는 `kb.py`의 실제 입력 계약입니다. JSON Schema 라이브러리를 설치하거나 외부 온톨로지 서버를 실행하지 않습니다. CLI의 명시적 검사와 fixture 시험이 아래 제약 중 구현된 범위를 검사합니다.

## 최상위

`schema_version`, `project_id`, `registry_revision`, `updated_at`, `objects`, `heads`, `audit`를 저장합니다. `registry_revision`은 감사 기록의 연속 번호와 일치합니다. 수정은 잠금 파일을 획득한 뒤 예상 revision을 비교하고, 같은 디렉터리에 임시 JSON을 저장해 교체합니다. 여러 Git 분기의 감사 배열을 그대로 이어 붙여 번호가 중복되면 검증 오류입니다.

`heads`는 `{canonical_key: record_id}`입니다. 예를 들어 `Requirement:FR-001`의 현재 기준은 `SPEC2:FR-001`입니다. `SPEC1:FR-001`은 보존할 수 있지만 기본 검색에는 들어가지 않습니다. `FR-001` 별칭은 현재 head로 해석하고, 모호하면 정확한 record ID를 요구합니다. 파일 mtime나 이름의 `final`, `latest`는 판단에 사용하지 않습니다.

## 공통 객체

| 필드 | 의미 | 구현상 주의 |
|---|---|---|
| `id` | 버전에 고유한 레코드 ID | 기존 ID의 의미를 덮어쓰지 않음 |
| `canonical_key` | 버전을 관통하는 안정 키 | 종류와 논리 ID를 포함 |
| `kind` | 아래 11개 종류 | 임의 종류는 오류 |
| `version` | 명시적 버전 문자열 | 숫자 크기나 mtime로 head 자동 선택 안 함 |
| `title`, `summary` | 사람이 읽는 식별과 요약 | 원문을 대체하는 검증 근거가 아님 |
| `status` | 편집 수명주기 | draft / review / approved / superseded / archived / rejected |
| `decision_state` | 채택 결정 | proposed / accepted / rejected / not_applicable |
| `verification_level` | 검증 종류 | unverified / source_documented / fixture_tested / product_tested / pilot_measured |
| `valid_from`, `valid_to` | 효력 구간 | ISO 날짜; valid_to는 미포함 끝점, null은 미정 |
| `review_due` | 재검토 기한 | 지난 승인 자료와 하위 소비자를 stale로 표시 |
| `tasks` | 관련 업무 | business / product / pitch / technical / validation / operations |
| `links` | 소비자→의존 대상 | type, target, target_fingerprint |
| `supersedes` | 대체한 과거 레코드 | 같은 종류·canonical_key; 순환 금지 |
| `retention` | 보존 정책 | 기본 `{policy: keep, until: null}`; 삭제 실행 기능 없음 |
| `approval` | 편집 승인 기록 | actor, at, scope=editorial_baseline, reason |
| `file`, `sha256` | 상대경로와 파일 바이트 해시 | Document에 필수. 다른 객체는 선택 |
| `aliases`, `namespace` | 원래 ID·일괄 등록 범위 | FR-001 같은 원래 ID를 보존 |

`actor`는 로컬 기록이며 인증된 전자서명이 아닙니다. `approved`가 고객 승인·제품 검증·외부 발표 허가를 뜻하지 않도록 `approval.scope`를 제한합니다. 실제 요구 채택과 검증 증거는 별도 변경으로 기록합니다.

## 11개 종류

| 종류 | 예시 | 경계 |
|---|---|---|
| Source | S-C01 공급자 가격 문서 | source citation ID, URL, 원래 확인일, 한계 |
| Claim | CLM-001 단가에 대한 주장 | 출처의 존재와 주장의 참은 다름 |
| Assumption | ASM-001 재시도 배수 | 모델링에 넣는 가정이며 관측값이 아님 |
| Decision | DEC-001 초기 제공 범위 | 이유·대안·채택 상태 |
| Requirement | FR-001, NFR-001 | 승인 문서에 있어도 미구현일 수 있음 |
| Screen | SCR-001 | 화면 상태와 역할별 흐름 |
| API | createJob | 계획 계약과 실행 endpoint 구분 |
| Test | AT-001-A, TCT-01 | 시험 정의와 실행 결과 구분 |
| Metric | MET-001 | 목표·분모·관측값 분리 |
| Experiment | EXP-001 | 설계·실행·실측 결과 분리 |
| Document | 사업계획·요구서·PPT | 고유 파일 해시와 사용한 근거 버전 |

Source는 `citation_id`가 필요합니다. `source_checked_at`이 없으면 승인해도 `SOURCE_CHECK_UNKNOWN` 경고가 나며 기본 문맥에서 제외됩니다. 카탈로그 import는 기존 확인일부터 30일을 기본 검토 기한으로 계산합니다. 가져온 날짜를 출처 확인일로 바꾸지 않습니다. 빠르게 바뀌는 가격·모델 기능은 사람이 더 짧은 기한을 정해야 합니다.

Claim/Assumption은 `claim_type=fact|assumption|target|inference`가 필요합니다. `domains=[cost, quality, latency, revenue, demand]`를 지정하면 미실측 상태가 문맥에 명시됩니다. 가정과 목표를 `product_tested`나 `pilot_measured`로 직접 바꾸는 것은 오류입니다. 별도의 실측 Claim을 만들어 실험과 연결합니다.

시험·실험의 `execution_scope`는 `not_executed`, `cli_fixture`, `product`, `pilot`처럼 구분하고 `execution_status`를 따로 둡니다. 검증 레벨이 fixture_tested/product_tested/pilot_measured라면 해당 범위의 실행 기록과 `evidence_document_id`가 필요합니다. 이 검사도 근거 파일 내용의 진실을 독립적으로 감사하지는 않습니다.

## 관계와 영향 방향

모든 영향 관계는 **소비자가 사용한 근거를 향해** 저장합니다. 변화 영향 조회는 이를 반대로 탐색합니다.

| 관계 | 출발→대상 | 영향 전파 |
|---|---|---|
| supported_by | Claim 등 → Source/실험 등 | 있음 |
| depends_on, derived_from | 소비자 → 근거 | 있음 |
| implements | Screen/API → Requirement | 있음; 구현 완료의 의미 아님 |
| verifies | Test → Requirement/API/Screen/Claim/Decision | 있음; 통과의 의미 아님 |
| measures | Metric → Requirement/Experiment/Claim | 있음 |
| tests | Experiment → Assumption/Claim/Metric/Requirement | 있음 |
| documents | Document → 기재한 객체 | 있음 |
| cites | 객체 → Source | 있음 |
| references | 단순 연관 | 영향·순환 검사에서는 제외 |

`supersedes`는 별도 배열입니다. 과거 버전을 대체했다는 사실을 근거 의존성과 혼동하지 않습니다. 의존 관계 DAG와 대체 관계 DAG를 각각 검사합니다. 단순 상호 참조가 필요하면 `references`를 사용합니다.

관계의 `target_fingerprint`는 의존 당시 대상의 의미 필드를 고정합니다. 승인 actor나 재검토 기한 같은 관리 변경은 의미 지문에서 제외하지만, 검토 기한 경과와 head 교체는 별도 검사로 전파합니다. 원본 JSON의 한 부분이 바뀌면 컨테이너 Document 해시가 바뀌므로 그 파일에 의존한 객체들이 보수적으로 stale이 됩니다. 이 초기 도구는 항목별 수정 의미를 자동 추론해 불필요한 영향 경고를 없애지 않습니다.

## 원문 위치와 import

카탈로그 객체는 `locator={document_id, json_pointer}`와 `payload_sha256`를 저장합니다. payload 해시는 그 pointer가 가리키는 실제 JSON 원문 항목의 해시이며, 정규화한 요약의 해시와 혼동하지 않습니다. 현재 importer는 requirements_catalog, screen_catalog, acceptance_tests, integration_tests, evaluation_protocol, system_and_ux_tests, source_registry, traceability_matrix, business_requirements, knowledge_management_requirements, comparison_protocol의 명시적 구조를 지원합니다. 임의 JSON을 자동 온톨로지로 해석하지 않습니다.

BUS 요구는 `subject_scope=business`, KMR 요구는 `project_knowledge_management`로 구분합니다. 제품 FR-001~096을 늘리거나 합치는 방식으로 문서 관리 요구를 끼워 넣지 않습니다. EXP-C 비교 실험도 사업 검증 계획이며 제품 생성 시험과 별개입니다. Source의 원래 `checked_at_basis`와 `inspection` 등 관측 범위도 보존하므로 캡처일을 라이브 사이트 실행일로 바꾸지 않습니다.

OpenAPI는 `.openapi.json`의 `paths`와 `operationId`를 읽습니다. YAML은 바이트 해시로 등록하지만 파싱하지 않습니다. JSON export가 없으면 수용 시험·요구서의 API 참조로 `reference_only` 노드를 만듭니다. 이 경우 전체 API 목록을 가져왔다고 보고하지 않습니다.

`import-catalogs`는 원래 `status`를 `source_declared_status`에 보존하지만 새 시험을 실행 완료로 승격하지 않습니다. 원문이 실제 실행 결과라고 주장하는 경우에도 사람 검토 후 별도 실행 증거 객체를 등록해야 합니다.

## sidecar patch

`merge`는 `{objects:[...]}` 형태의 **추가 객체**만 받습니다. `heads`, 감사 로그, 기존 레코드를 조용히 교체하지 않습니다. 기존 ID와 다른 의미가 오면 `IMMUTABLE_ID_CONFLICT`로 중지합니다. 새 관계의 target_fingerprint는 누락 시 현재 등록 대상에서 채웁니다. 없는 대상은 `BROKEN_LINK` 오류입니다.

Python에서 `import kb; kb.record(...)`로 공통 필드를 채울 수 있습니다. `examples/claims_patch.example.json`은 실제 가격을 주장하지 않는 입력 형식 예시입니다. 예시 객체가 실증 자료로 자동 포함되지 않도록 등록·승격 명령은 별도로 실행해야 합니다.
