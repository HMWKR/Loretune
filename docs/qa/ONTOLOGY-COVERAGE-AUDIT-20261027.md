# Aethon 온톨로지·개발 문서 연결 범위 독립 감사

2026-10-27 UTC · 읽기 전용 소스/등록부/보존 시험 증거 감사

**“우리 프로젝트에 맞는 온톨로지 기반과 일부 문서 등록은 구현돼 있다. 모든 최신 MD가 온톨로지 처리를 거쳐 연결됐고, 모든 새 입력이 자동 반영되는 상태는 아니다.”** 이것이 현재 근거로 답할 수 있는 범위다. 제품의 승인된 IP 설정, 개발 문서의 지식 등록부, Claude에 전달하는 문맥은 서로 연결 목적과 권한이 다른 계층이다.

이번에는 코드·기존 보고서·등록 JSON 및 등록 문서의 파일 해시만 읽었다. 제품 코드, 기존 문서, registry, 공유 DB는 변경하지 않았다. DB·비밀파일·키 접근, API 호출, 브라우저/서버/CLI inference 실행, 새 제품 시험은 0이다. 아래 ‘실행 검증’은 **보존된 과거 증거**이며 이번 신규 실행 결과가 아니다. 이 감사 MD만 새로 작성했다.

## 1. 질문별 판정

|범주|설계|구현·연결|보존된 실행 근거|현재 판정과 한계|
|---|---|---|---|---|
|제품 도메인 온톨로지|Master, 제품 공통 계약, 원본07에 있음|작품/인물/장소/스타일/곡/샷/자산/Take/승인/출력 등의 타입, 관계와 버전 모델 있음|로컬 계약·격리 DB 시험과 일부 실제 Claude 합성 시험|**프로젝트 맞춤 기반 있음. 전체 제품 명세 완료 아님.** 모든 활동기·분기·시점·조직 권한 요구의 완성으로 확대할 수 없음|
|Canonical 저장·사람 승인·조회·복원|명시됨|SQLite head/version/proposal, revision 검사, 적용·복원, UI 조회/승인, 장면 버전 고정·영향 표시 연결|`test_ontology.py`, `test_project_ontology.py` 및 과거 독립 감사·Claude 합성 승인/재열기 기록|**구현·제한 검증 있음.** 이번에는 실제 사용자 DB 내용을 읽어 채워진 상태를 확인하지 않음. local-owner가 실제 다중사용자 ACL을 대신하지 않음|
|Claude 세션 문맥·도구 실행|원본07 §7.1–7.2, CC01, 새 대화 계획|앱이 저장 요청/현재 승인 문맥을 매번 구성하고 조회·변경 제안 도구로 연결. 모델 답변은 자동 승인되지 않음|CC01 실제 Claude 14응답, 합성 A/B 격리·정정·재열기·프롬프트 작성; 독립 증거 검토 존재|**기존 단일 작품 대화 경로 제한 검증 있음.** 모델 자체 영구 기억이나 모든 문서 기억이 아님. 현재 복수 대화 부분 코드는 검증 미완료|
|개발 MD·요구·시험의 지식 등록|Master 8장, KMR-001–020, 원본07 §15.2|별도 `project_kit` CLI와 JSON registry 2개. 파일 등록·정형 catalog import·관계·head·문맥 receipt 있음|각 registry revision9, SPEC-MS-001 및 28 MS-FR/38 MS-AT 실제 등록. 역사적 CLI fixture 기록 있음. 이번 등록 파일 해시 대조 이상 0|**선정한 동결 문서의 수동 등록/카탈로그 온톨로지화 있음. 모든 최신 MD 처리 근거 없음.** 일반 MD 전체 의미 자동 추출·자동 감시·제품 canonical 자동 반영 경로 아님|
|새 정보·정형/반정형/비정형 입력|PLAN K.2/K.3에 상세 설계|현재는 수동 설정 제안, 제한된 모델 제안, 제공된 텍스트 map 추출 adapter, 정해진 개발 catalog importer|작은 합성 텍스트 추출/근거 일치 시험|**부분 경로만 구현. 신규 통합 ingestion·자동 진화는 명시적 PLAN ONLY.** CSV/XLSX/PDF/OCR/음성/영상 전체 처리 완료 아님|
|모든 MD가 최신이며 처리됐는가|문서 버전·해시·영향 추적 원칙 있음|현재 주요 계획·보충문이 작성되고 서로 링크됨. 하지만 두 registry의 최신 등록 시각은 10/25|현재 문서 11개를 표본 대조: 원본07만 동일 바이트 등록 확인, 나머지 10개는 동일 바이트 등록 없음|**전체 완료 주장 불가.** 파일별 ingestion/등록/소비 receipt를 모두 갖춘 전수 추적표 없음. 새 문서 작성 완료와 registry 최신 반영 완료는 다름|

## 2. 어떤 온톨로지인지 먼저 구분

1. **제품 IP/제작 온톨로지:** 작품에 적용할 공식 설정, 출처, 승인 버전, 장면·Take·자산 계보를 다룬다. [Master](../../Master_Specification.md) L19, L642, L2141; [제품 계약](../specification/IP_Music_Video_Platform/chapters/03_product_contracts.md) L9–23, L31–38; [07](../../07_Chat_Directed_Multimodel_Production_Spec.md) L300–324.
2. **개발 프로젝트 지식 온톨로지:** Source/Claim/Assumption/Decision/Requirement/Screen/API/Test/Metric/Experiment/Document를 연결한다. [개발 온톨로지 8장](../specification/IP_Music_Video_Platform/chapters/08_project_ontology_and_cli.md) L3–38. 고객 IP 데이터나 승인 상태를 저장하는 기능이 아니며, KMR-001–020은 제품 FR-001–096과 별도다. 원본07 L667의 SPEC-MS-001 등록 요구도 이 계층이다.
3. **Claude 문맥:** 위 제품 상태와 현재 작업 이력을 선택해 매 요청에 전달한 스냅샷이다. 문맥을 읽었다고 사실 승인·실행 권한이 생기지 않는다. `search_project_context`는 현재 작품 스냅샷 조회이며 의미/임베딩 검색이 아니라고 코드에 명시돼 있다.

여기서 검사한 두 kit는 **현재 Loretune 저장소 안의 개발 명세 kit**다. 별도 `aethonSaaS` 저장소를 읽거나 그 지식 등록을 현재 제품 구현으로 계산하지 않았다. [제품 정체성 보충문](../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md) L19–28, L44–54와 [도입 제안](../design/AETHONSAAS-ADOPTION-PROPOSAL.md) L158, L191은 과거 제품의 선택적 참고와 현재 런타임의 경계를 명시한다. 원본 문서는 보존하고 최신 보충 결정을 함께 읽어야 하며 원본 파일 날짜만으로 최신성을 판정하면 안 된다.

## 3. 제품 코드에서 실제 연결된 경로

|경로|정확한 근거|확인한 범위|
|---|---|---|
|구조·식별·출처|[ontology.py](../../ontology.py) L12–22, L34–38, L50–117|12개 타입·9개 관계, label과 독립된 ID 생성, 타입/끝점/중복/순환 검사, `source_id + excerpt`, asserted/inferred/unknown 구분|
|저장·적용·복원|`ontology.py` L120–206|head/version/proposal 분리. expected revision, scope, 명시 승인, 과거 ID 타입 보존, savepoint rollback, 과거 버전을 새 승인 버전으로 복원|
|작품·샷 연결|[project_ontology.py](../../project_ontology.py) L9–36, L39–90|workspace/project scope와 제작 계보 projection. 수동/모델 제안은 character/place/style. 승인 개체·관계·의존 개체를 샷에 deep-copy 고정하고 변경 영향 비교|
|앱·사용자 승인|[app.py](../../app.py) L161–167, L439–455; [index.html](../../index.html) L427–436|상태 조회에 ontology/proposals/lineage 포함. 설정 제안→사람 승인→현재 버전, 장면 연결, 복원 UI/서비스 호출 연결|
|Claude 읽기·제안|[production_tools.py](../../production_tools.py) L77–81, L99–104; [local_creation_tools.py](../../local_creation_tools.py) L124–140|현재 작품 문맥과 출처 반환. memory 제안은 현재 ontology revision 및 실제 제공된 출처의 excerpt 일치를 검사하고 제안 저장만 수행|
|앱의 기억 재구성|[chat_runtime.py](../../chat_runtime.py) L49–61, L162–203; [chat_protocols.py](../../chat_protocols.py) L55–61; [guided.py](../../guided.py) L9–11|수락된 사용자 요청의 순서·원문·hash·처리상태, 현재 승인 문맥, 작업 handle, 최근 공개 답변을 handoff로 저장·전달. assistant 원문은 unreviewed|
|텍스트 추출 adapter|[anthropic_ontology.py](../../anthropic_ontology.py) L71–117, L127–153|호출자가 전달한 1–20개 텍스트 source map, 12KB 입력 경계, 구조 및 exact excerpt 검사, 충돌 시 불확실성 요구, approval-required 제안. 기본 비활성·명시 transport 경로|

제약을 좁혀 해석해야 한다. 현재 graph의 개체 필드는 `id/type/label/description/provenance/uncertainty`이고 관계 필드도 제한돼 있다. prose에 적힌 곡 예외를 이해한 표본과, 모든 예외·활동기·사실 유효시점·분기·철회를 정형 claim으로 판정하는 범용 엔진은 다르다. 수동 근거는 로컬 사용자 진술의 hash이며 외부 사실 검증이 아니라고 코드가 명시한다. exact excerpt 일치도 의미적 진실이나 올바른 범위까지 보장하지 않는다.

또한 `ontology.py` L1–5는 이 모듈을 인증 계층이 아닌 로컬 도메인 모델로 명시한다. 실제 조직·사용자 권한 및 모든 원본 FR의 통과로 확대하지 않는다.

## 4. MD가 처리되는 현재 경로와 끊긴 연결

### 현재 존재하는 개발 문서 경로

`선정된 파일/폴더 → kb.py ingest → Document(경로·SHA256·버전) → guarded merge/promote → registry head → context + receipt`

정해진 JSON/OpenAPI 카탈로그는 `import-catalogs → Requirement/Test/API 등 노드 + derived_from + JSON pointer + payload hash` 경로를 추가한다. [kb.py](../knowledge/project_kit/kb.py) L587–612, L630–720, L773–924. 문맥 생성/검증은 L497–585에 구현돼 있다.

- 일반 MD의 `ingest`는 **문서 스냅샷 등록**이다. MD 안의 모든 주장·요구·관계를 자동 추출하지 않는다. `make_documents` L603–606도 내용 주장의 근거 상태는 별개라고 적는다.
- catalog import는 지원하는 정해진 파일 형식에 대한 매핑이다. 임의 JSON/YAML/XML이나 모든 MD를 같은 의미 모델로 자동 변환한다는 뜻이 아니다.
- `kb.py`의 context/receipt가 있어도 새 문서 편집 때마다 자동 등록하거나 Claude 제품 세션에 자동 주입되는 것은 아니다. 검사한 제품 경로에 이 kit를 읽어 IP canonical을 만드는 연결은 없다. [config](../knowledge/project_kit/registry/config.json) L12–16은 `editorial_baseline`, `network_calls:false`, `product_runtime_ontology:false`다.
- [8장](../specification/IP_Music_Video_Platform/chapters/08_project_ontology_and_cli.md) L38, L123, L127–133도 바이너리 전체 추출/산출물 자동 완성을 부정하고, 새 버전 등록·승격 및 선언된 관계를 통한 영향 검토를 요구한다.
- 코드가 존재하고 담당자가 원문을 읽었다는 사실만으로 **모든 개발자가 매 작업마다 최신 context receipt를 소비했다**고 말할 수 없다. 전수 소비 이력은 이번 근거에 없다.

### 현재 등록부 실측 — 파일 읽기/해시 검사

|대상|revision / 갱신 시각 UTC|전체 객체 / 현재 head|Document 전체 / 현재 / 현재 MD|MS 현재 head|
|---|---|---|---|---|
|`docs/knowledge/project_kit/registry/knowledge.json`|9 / 2026-10-25 14:26:20|1772 / 982|88 / 55 / 23|28 FR / 38 AT|
|`docs/specification/IP_Music_Video_Platform/project_kit/registry/knowledge.json`|9 / 2026-10-25 14:26:23|1772 / 982|88 / 55 / 23|28 FR / 38 AT|

각 kit의 Document 88개가 가리키는 파일과 SHA256을 대조했고 **누락·hash 불일치 0**이었다. 두 사본이므로 이를 고유 문서 176개나 고유 현재 MD 46개로 합산하지 않는다. 이는 등록된 스냅샷의 무결성 검사이며 전체 relation/schema 검증이나 전체 제품 시험 실행이 아니다.

두 kit의 SPEC-MS-001은 원본07과 hash가 일치한다. 현재 38개 MS-AT head는 모두 전체 수준에서 `verification_level=unverified`, `execution_status=not_run`이며 local/live subset 근거가 별도다. `status=approved`의 승인 범위는 `editorial_baseline`이다. **등록됐다는 이유로 시험이 통과됐다고 기록하지 않은 점은 올바르다.** 반대로 이 10/25 등록부만으로 10/26 이후 실제 검사 결과가 모두 최신 반영됐다고 말할 수 없다.

### 최신 파일의 동일 바이트 등록 여부

두 kit의 모든 Document 기록(현재와 이력)을 현재 파일 SHA256과 대조했다. 아래는 전수 MD 목록이 아닌 **전체 최신 등록 주장에 대한 좁은 표본**이다.

|현재 파일|동일 바이트의 Document 기록|
|---|---|
|`07_Chat_Directed_Multimodel_Production_Spec.md`|있음 — `MS20261025:SPEC-MS-001`|
|`Master_Specification.md`|없음. 다만 분할 chapter/catalog 등록이 있으므로 설계 내용 전체가 미등록이라는 뜻은 아님|
|`README.md`|없음|
|`docs/qa/REMAINING-WORK.md`|없음|
|`docs/qa/OMISSION-REGISTER.md`|없음|
|`docs/qa/SPEC-MS-001-ACCEPTANCE-TRACE.md`|없음|
|`docs/qa/codex-cli-assessment-20261026/PLAN-ko.md`|없음|
|`docs/design/CHAT-SESSION-PLAN.md`|없음|
|`docs/design/CURRENT-DESIGN-QA-PLAN.md`|없음|
|`docs/design/AETHONSAAS-ADOPTION-PROPOSAL.md`|없음|
|`docs/design/PRODUCT-IDENTITY-AMENDMENT-20261027.md`|없음|

이것은 **최신 스냅샷 등록·추적의 미연결**이지 문서를 아무도 읽지 않았다거나 문서 결정이 채택되지 않았다는 판정이 아니다. 특히 최근 ‘문서 반영 완료’는 문서 작성/링크 정합화 상태이며 제품 구현 또는 registry 전수 등록 완료와 다르다. 동일 바이트 등록이 없는 파일을 포함하는 현재 전수 처리 원장은 발견하지 못했으므로 “모든 MD 처리 완료”라고 답할 근거가 없다.

## 5. 새 정보와 입력 형식별 경계

|입력/변경|현재 가능한 범위|계획 또는 미검증 범위|
|---|---|---|
|사용자의 새 설정·정정|수동 제안/모델 제안→출처/버전 검사→사람 적용. 이전 버전 및 샷의 고정 문맥 보존|새 사실의 범용 자동 분류·entity resolution·정형 claim 철회·자동 schema 진화|
|대화의 정정·해제·인용·가정|원문/순서/상태를 별도로 전달. 실제 Claude의 제한된 표본 확인|모든 표현의 의미 정확성 및 현재 복수 대화 partial 구현의 전체 수용|
|개발 catalog JSON/OpenAPI|지원하는 catalog를 Requirement/Test/API 등으로 결정적 매핑|임의 고객 CSV/XLSX/DB/XML/YAML의 일반 수집·통합 처리|
|직접 제공한 텍스트 map|Anthropic 추출 후보와 exact excerpt 검사. 기존 합성 시험 존재|일반 MD 업로드→추출→source version→review→canonical의 완결 제품 경로와 전수 운영|
|PDF/DOCX/OCR/이미지/음원/영상|일부 원본·미디어 저장/제작 기능 존재. 그것만으로 의미 추출 완료는 아님|형식별 parser/OCR/transcript/frame→좌표 근거→claim→승인 버전의 공통 ingestion|

정확한 계획 근거는 [PLAN K.2/K.3](codex-cli-assessment-20261026/PLAN-ko.md) L266–332와 [OM-21](OMISSION-REGISTER.md) L328 이후다. K.3 L298은 신규 수집·온톨로지화를 **PLAN ONLY**로 명시한다. L300–313은 row/column/page/bbox/offset/timecode, source version/hash, 충돌·unknown·철회·재처리를 앞으로 구현할 계약으로 정의한다. 이 설계가 존재한다는 이유로 구현 완료로 표시하지 않는다.

## 6. 실제 이전 검증에서 말할 수 있는 것

|보존 근거|실제로 기록된 관측|이 근거가 증명하지 않는 것|
|---|---|---|
|[Claude grounding 보고](claude-grounding-20261025/REPORT-ko.md) L3–27, `answer.json`, `offline-review.json`|합성 인물/장소/의상 텍스트. 초기 cap/contract 실패 보존. 후속 추출은 인물2·장소2, exact excerpt·합성 DB 승인/재열기. 실제 도구 조회→계획 저장→답변 표본|관계 추출은 0개. typed clothing claim·교차 호출 ID 품질 미검증. 실제 프로젝트 MD 전송/처리 시험 아님|
|[CC01 보고](cc01-context-fix-20261026/REPORT-ko.md) L3–10, L27–60 및 [provider provenance](cc01-context-fix-20261026/provider-provenance.json)|실제 Claude 14응답. 최근8개 밖의 요청, 정정/해제, 재열기 후 최신 승인 사실, 다른 작품 canary 격리, 모델이 작성한 2개 프롬프트→fake fal payload 연결. 초기 의미 오류와 후속 수정도 남김|모델의 영구 기억, 모든 MD ingestion, 다른 모든 모델/사용자/형식 품질, 실제 fal 생성 성공이 아님|
|[CC01 독립 검토](independent-cc01-fix-recheck-20261026/REPORT-ko.md), [CC02 후속 검토](independent-cc02-recheck-20261026/REPORT-ko.md)|원 CC01 반례 폐쇄. 14응답 output hash 대조, 입력 전체 본문 재해시 6/14 가능. 발견했던 CC02 경계 후속 수정 검증|8/14는 thinking 제거로 원 wire 입력 재구성 한계. 전체 무제한 기억·토큰 수용을 보장하지 않음|
|[프로젝트 kit 시험 기록](../knowledge/project_kit/tests/LOCAL_TOOL_TEST_REPORT.json), [통합 기록](../knowledge/project_kit/tests/FINAL_INTEGRATION_REPORT.json)|2026-10-23 CLI fixture 16개와 별도 산술 fixture 10개 등 당시 문서 도구 검사|당시 revision3 기록을 현재 revision9 전체 신규 검증 또는 제품/고객 시험으로 계산하지 않음|
|[서버 승인 영수증 독립 검토](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md)|모델 원문과 서버의 현재 승인 사실/과거 영수증을 구분하는 표시 개선|모델 자유문장 자체의 모든 사실 오류가 해결됐다는 뜻이 아님|

현재 기준의 최신 비용·호출 원장을 새로 대사하는 감사는 아니다. 위 실제 응답 수는 각각의 과거 시험 범위이며 누적 합산해 새 성능 점수나 전수 수용으로 만들지 않았다. 계정 실청구 확인도 하지 않았다.

## 7. 현재 부분 코드와 완료 선언의 제한

[README](../../README.md) L8–9와 [CHAT-SESSION-PLAN](../design/CHAT-SESSION-PLAN.md) L5–19는 마지막 전체 검증을 **2026-10-26 20:48:43 UTC, 416회귀 manifest**로 한정한다. 이후 신규 `chat_sessions.py`와 5개 Python 파일(`app.py`, `chat_runtime.py`, `chat_protocols.py`, `production_tools.py`, `production_context.py`) 부분 변경을 실제 hash로 확인했다. `index.html`/`model_selection.py`는 세션 baseline과 같다.

따라서 과거 Claude 시험이나 416개 결과를 **현재 작업 트리 전체 PASS**로 표시하지 않는다. 새 독립 대화 CS01–18/UI/전체 검증은 미완료다. 이번 감사는 그 부분 구현을 재개하거나 되돌리지 않았다. 기존 CQ-R01의 독립 폐쇄 근거는 [해당 보고](independent-cq-r01-final-recheck-20261026/REPORT-ko.md)에 있으나, 이 역시 새 세션 구현의 검증은 아니다.

## 8. 빠진 연결과 최소 다음 단계 — 이번에는 실행하지 않음

1. **개발 MD의 최신 등록 범위 확정:** 두 kit 중 운영 기준과 배포 사본의 관계를 명시하고, 현재 읽어야 할 MD를 allowlist로 확정한다. 파일별 `path/hash/version/canonical_key/head/supersedes/요구·시험 링크/등록 receipt/소비 receipt/제외 이유`를 남긴다. 현재 채택된 정체성·AD·세션·수용 추적 문서부터 기존 CLI의 검토 가능한 새 버전 등록 경로로 연결한다. 원본·역사 자료를 덮어쓰지 않는다.
2. **문서 등록과 의미 변환을 분리해 수용:** Document 해시만 존재하면 ‘등록’, Requirement/Decision/Claim의 원위치·관계까지 확인하면 ‘구조화’, 최신 receipt를 실제 작업 문맥에 사용한 증거가 있으면 ‘소비’로 기록한다. 모든 MD라는 완료 조건에는 전수 분모와 각 파일의 상태/실패/제외 근거가 필요하다. 시험 등록은 시험 통과가 아니다.
3. **제품 자료 ingestion은 별도 범위:** 모든 개발 사업/요구 MD를 고객 IP canonical으로 자동 복사하지 않는다. 제품에서 쓸 특정 텍스트 형식을 선택한 뒤 `원본 버전→근거→후보→검토→사람 승인→샷/실행 고정 버전`을 먼저 완결한다. 파일 변경·정정·삭제·충돌·타 작품 격리의 추적을 수용 조건에 둔다. K.2/K.3의 PLAN ONLY는 후속 구현 권한 전까지 유지한다.
4. **새 세션 완료는 별도 판정:** 구현 재개 시 기존 canonical과 세션별 요청/미승인 제안의 경계를 현재 CS 기준으로 검증하고 실제 build hash에 결과를 연결한다. 과거 실제 Claude 시험은 회귀 근거로 재사용하되 새 세션의 실행 검증을 대신하지 않는다.

현재 감사에 도구 거부·대기 중 행동은 없다. 미완료 항목은 위 연결·수용 근거의 공백이며, 이번에 허용되지 않은 구현/API/실데이터 접근을 시도하지 않은 결과다. 전체 플랫폼 완료·모든 MD 자동 처리·전체 온톨로지 품질 PASS로 확대하지 않는다.

## 부록 A. 등록된 현재 MD 23개

두 kit에서 동일한 상대 경로 집합을 확인했다. 각 경로는 해당 kit root 아래이며, 아래 목록이 저장소 전체 MD 목록은 아니다.

```text
sources/current_spec/chapters/00_overview.md
sources/current_spec/chapters/01_business.md
sources/current_spec/chapters/02_requirements.md
sources/current_spec/chapters/03_product_contracts.md
sources/current_spec/chapters/04_technical.md
sources/current_spec/chapters/05_ux_flows.md
sources/current_spec/chapters/06_validation.md
sources/current_spec/chapters/07_workflow_and_pitch.md
sources/current_spec/chapters/08_project_ontology_and_cli.md
sources/current_spec/chapters/09_cost_and_comparison.md
sources/current_spec/output/API_Contract_Index.md
sources/current_spec/output/Acceptance_Scenarios.md
sources/current_spec/output/Traceability_Matrix.md
sources/current_spec/planning/PITCH_BRIEF.md
sources/current_spec/research/price_comparison_notes.md
docs/modules/spec-ms-001/20261025/07_Chat_Directed_Multimodel_Production_Spec.md
docs/modules/spec-ms-001/20261025/runway-role-decision.md
docs/modules/spec-ms-001/20261025/claude.md
docs/modules/spec-ms-001/20261025/receipt.md
docs/modules/spec-ms-001/20261025/intent.md
docs/modules/spec-ms-001/20261025/contract.md
docs/modules/spec-ms-001/20261025/bridge.md
docs/modules/spec-ms-001/20261025/rights.md
```

## 부록 B. 읽기 시점과 고정 hash

- 핵심 16개 파일 첫 hash 확인: `2026-10-27T01:09:34.104590+00:00`; 최종 재확인: `2026-10-27T01:15:52.236926+00:00`. 사이 변경 0.
- registry 2개 SHA256은 아래와 같다. 현재 MD 경로 집합 및 표본 11개 등록 여부는 두 kit에서 일치했다.
- 세션 baseline 대비 제품 파일 5개 변경 및 신규 `chat_sessions.py`를 확인했다. 문서 변경은 제품 코드 검증에 합산하지 않았다.
- 이 목록의 mtime은 파일 시각이며 기능 완료나 검증 시각을 뜻하지 않는다. 이번에는 코드/registry CLI를 import 또는 실행하지 않았다.

|파일|SHA256|mtime UTC|
|---|---|---|
|`ontology.py`|`14439e06ddc6e233b4f61371d1353142818c36b4a295a71b7e8da1fac0fee685`|2026-10-25T08:53:52.328972+00:00|
|`project_ontology.py`|`9521a386b983b92d994b5eee4200e6f69b2ef2e64bddbd3225f7c2b0b5842db8`|2026-10-25T15:32:34.015715+00:00|
|`anthropic_ontology.py`|`2f97cd79e6c9b15a6f8d49814647791fd5a13ae0faef36aca788ff1b86e6802f`|2026-10-26T18:18:49.096331+00:00|
|`app.py`|`ab8e4edb1c616512116fe637d083b0cc0126cb44b57d45b250c93a2526d765a6`|2026-10-27T00:04:50.700778+00:00|
|`chat_runtime.py`|`f1efe0e9f5c3762545dc4560853bdf162fd8e3a2d6ae0654899a622d036e9d80`|2026-10-27T00:05:28.342335+00:00|
|`chat_protocols.py`|`da1a03240e2e3bb19bdacd3bd4cbf27ae8f0f35ed19ab61f6e495222571eda82`|2026-10-27T00:05:28.343482+00:00|
|`production_tools.py`|`a51e953be8ba07ad796abcbd9b0835be1391625deadaa55fb1aebc9d69a14e89`|2026-10-27T00:05:28.342836+00:00|
|`production_context.py`|`b6b5e2d824336138ea1dd7fd506e7019675fbe69cdc7816e40601a06735d323d`|2026-10-27T00:05:28.343204+00:00|
|`local_creation_tools.py`|`263154a41540f15b1b1aa9feaa50627c6c4584c96bfb7f38a1411db43134f7d8`|2026-10-26T18:52:53.539083+00:00|
|`guided.py`|`c21a2f573c2287819e3154adca5a610405411367dfd467953f75829739b99ebd`|2026-10-25T09:08:03.278976+00:00|
|`chat_sessions.py`|`443433bc5129db8082b52257ff6ca0c2aa570a4de8da1892d3ba4edf13a16c4b`|2026-10-27T00:04:50.986719+00:00|
|`chat_models.py`|`29a54c95d2fc87645b13f6f13127e9bb5a7f5db33d63328493bf2a293eedef2b`|2026-10-26T19:02:09.301006+00:00|
|`index.html`|`4e96344612858c553cb47ec6c7561524016d384c77b61aa655eb2b9a72851e91`|2026-10-26T20:45:03.465792+00:00|
|`model_selection.py`|`97d8c826626afc93ad65216722f9aa850415a699897ce7b72c50e6f5b1e51925`|2026-10-25T15:32:34.015373+00:00|
|`Master_Specification.md`|`9ebc6156cea07f13a96974221902eb250ead2098af0999c140345d3f01677913`|2026-10-25T08:53:12.288305+00:00|
|`07_Chat_Directed_Multimodel_Production_Spec.md`|`962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`|2026-10-25T09:22:04.636698+00:00|
|`docs/knowledge/project_kit/registry/knowledge.json`|`29d8471202c3ce28ad7ae902904a3ecc3f7245122611e1b5ea52ea217952225e`|2026-10-25T14:26:20.925107+00:00|
|`docs/specification/IP_Music_Video_Platform/project_kit/registry/knowledge.json`|`d207e2f15d0fd3626f68e72faaee449a3516a36acf241943b3aa435e37f038cd`|2026-10-25T14:26:23.224867+00:00|
|`docs/knowledge/project_kit/kb.py`|`841d7d361eff1af11c2116c5e0531399958e76a8dad97e56a3571ba1a03625e2`|2026-10-25T01:24:54.686980+00:00|
|`README.md`|`a3fa7ccafd59c55f4e4e0427ff4b170bd5c247ee7e2db33c0099f87e470c5bbe`|2026-10-27T00:49:22.657868+00:00|
|`docs/qa/REMAINING-WORK.md`|`c2f2a650b18ae201b3dbdc4139e659677cbb6edb934b6132520815d322ca6f6c`|2026-10-27T00:51:18.791456+00:00|
|`docs/qa/OMISSION-REGISTER.md`|`8e5f38a59f99335701890a4b034324df540c12be7f02959dc72101b78bd4b26f`|2026-10-27T00:51:18.790684+00:00|
|`docs/qa/SPEC-MS-001-ACCEPTANCE-TRACE.md`|`3677c60081eba1baf417294fb942a280fb9eb53a6418f52355c0686794bfe63c`|2026-10-27T00:49:22.660497+00:00|
|`docs/qa/codex-cli-assessment-20261026/PLAN-ko.md`|`916c922376e4be00445cd3ad1011e697be559b6d589fc5469d077f5ea781f61a`|2026-10-27T00:49:22.658923+00:00|
|`docs/design/CHAT-SESSION-PLAN.md`|`357868870856b3cc4b675dd4b60cc0921b7643b7a6e1af9cd61d441228e093aa`|2026-10-27T00:49:22.659756+00:00|
|`docs/design/CURRENT-DESIGN-QA-PLAN.md`|`1c94aa6494a4e26f28fe61ca3b3ed8857877e0ca9c42db13de2e22114dbf9b3a`|2026-10-27T00:54:18.013274+00:00|
|`docs/design/AETHONSAAS-ADOPTION-PROPOSAL.md`|`7845b413370440a37164ab8a0af4625012b63eeb742e2cfb6b359b46754ee050`|2026-10-27T00:57:26.585665+00:00|
|`docs/design/PRODUCT-IDENTITY-AMENDMENT-20261027.md`|`d6f80bb6fd35aed08dae0eb9b37b3c1ed3e57cce151611431cfc02c36bb5ea53`|2026-10-27T00:57:26.586095+00:00|
|`docs/qa/cc01-context-fix-20261026/provider-provenance.json`|`cf09df2c73ece4e241ca0878eb9a383fb451bc6a0448489132d4c1d2d703c638`|2026-10-26T14:54:15.299388+00:00|
