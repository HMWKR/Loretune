# 독립 의도 정렬 감사

[교정 목록](CORRECTION_LEDGER.md)의 네 항목이 최종 결과다. **Runway 역할의 해석 오류는 확인했고, 새 문서 모듈 등록은 아직 누락돼 있다. 나머지 두 시험 조건을 영구 제품 정책으로 오해했다고 볼 근거는 확인되지 않았다.** 미구현 기능을 새로운 해석 오류로 분류하지 않았다.

이 감사는 부모가 전달한 최신 사용자 설명과 대화 검증 결과를 기준으로 수행했다. 13:56 사용자 설명은 “Runway는 경쟁·벤치마크 플랫폼”이며 실제 공급자 대상으로 해석하지 않는다. 비공개 1시간 정책과 Anthropic $50는 승인된 개발 시험 범위라는 부모의 검증 결과를 전제로 한다. 원래 명세의 이름 예시보다 최신 설명이 우선한다.

## 1. Runway의 비활성 공급자 후보 승격 — 확인된 오해

14:01:27 UTC snapshot의 `model_selection.py:9–10`은 Runway gen4_image를 image 슬롯의 후보로 제공한다. 상태는 `integration_unverified`이고 active나 실제 연결이 아니다. 그래도 `validate_selection` (`:25–30`)은 이 후보의 선택·저장을 허용하며, `index.html:585`의 동적 model catalog 선택기에 노출되는 구조다.

`image_pipeline.py:8,36–41`은 Runway 전용 import, 견적, model/connection 및 출력 정책으로 실제 공급자 실행형 action을 준비한다. `action_execution.py:54`에는 runway connection이 허용돼 있다. `generation_queue.py:33–35`, `provider_billing.py:33–34`에도 Runway 분기가 존재한다. 이는 단순 디자인 레퍼런스보다 넓은 구현 범위다.

한편 원래 추가 명세 `07_Chat_Directed_Multimodel_Production_Spec.md:51`은 Runway/Luma 교차 호출을 직접 예시로 쓴다. 과거 구현에 이 문구가 있었음을 숨기지 않는다. 최신 사용자 설명은 그중 **Runway의 공급자 타깃 해석을 정정**한 것이며, MS-FR-01/02/25의 독립 슬롯과 서버 공통 도구·교차 공급자 구조까지 폐기하는 근거는 아니다.

기능 세션이 제거 중이라고 전달받았다. 이번 감사는 원본을 고치지 않았으며 제거 완료를 검증한 결과도 아니다. parent에 따르면 실제 Runway 연결/결제는 없었다. 이번에도 외부 이력을 조회하지 않았으므로 이를 독립 계정 감사로 표현하지 않는다. Luma 등 다른 경쟁 이름은 검사한 실행 registry/adapter 경로에서 실제 후보로 추가된 근거를 찾지 못했다. 문서에 등장하는 사실만으로 새 연결을 추가하지 않는다.

## 2. 단일 시험의 private+1h — 고정 범위 확인, 제품 일반화는 미확인

실제 고정 위치:

- `fal_provider.py:20`: LIFECYCLE에 expiration3600/default forbid.
- `fal_provider.py:58`: 승인 gate도 private/retention3600/duration10/no-audio 요구.
- `fal_provider.py:65–68`: 모든 FalKling 인스턴스가 이 기본 정책 또는 같은3600초의 explicit-reader 변형을 사용한다.
- `fal_provider.py:81`: 해당 모델 생성 POST에 lifecycle header 적용.
- `live_launcher.py:20–24`: private+3600초,10초 무음,1회/$1 이하, 승인 만료1시간을 강제한다.
- `app.py:673–690`: 동일한 gate hash·adapter·작품·샷·원본hash를 제출 직전에 다시 검사한다.

따라서 **현재 어댑터 구현은 모든 fal 제출에 이 좁은 시험 정책을 적용한다**. 임의 프로젝트의 일반 보관 기간 선택 기능은 없다. 반면 이것을 모든 고객의 영구 보관 정책이라고 선언하거나 자동 연결하는 코드도 확인되지 않았다. `live_launcher.py:66`은 1회 검증 런처이며, `docs/mvp-fal-kling-live-gate.md:7,17,28–30`도 마지막 smoke test/명시 상한으로 설명한다. `index.html:531`은 승인된 테스트 범위만 허용한다고 표시한다.

판정은 **현 승인 시험 구현으로는 일치, 일반 제품 정책은 아직 분리·구현되지 않음**이다. FR-087은 보관 기간/삭제 요청/자원 범위를 입력으로 관리하며 영구3600초를 요구하지 않는다(`02_requirements.md:1463–1479`). 새 고객용 기능에 이 상수를 그대로 승격하면 문제지만, 그 미래 가능성을 현재 해석 오류로 세지 않는다. 이미 승인된 시험의 제한을 임의로 완화할 이유도 없다.

## 3. 개발 Anthropic $50 — 고객·전체 공급자 상한으로 일반화되지 않음

`chat_runtime.py:69–83`의 UsageJournal은 이전 승인된 synthetic trials와 공유하는 원장이다. $50는 **같은 주입된 journal 파일**의 실제/보류액 합계에 적용되며, mode가 다른 fake/live 원장 혼용을 거부한다. 고객 계정의 요금제 상한으로 읽는 코드가 아니다.

`ChatRuntime`은 서버가 approval/journal_path를 주입한다(`:95–97`). `:115–121`에서 지정 Anthropic 모델, workspace/project, synthetic_only, 만료, 문맥 hash, 허용 prompt hash와 가격 revision을 검사한다. 이 조건을 통과하지 못하면 연결 unavailable이다(`:108–111`).

반면 제품 쪽 공급자 예산은 `ledger.py:46–68`의 workspace/scope별 금액과 revision을 사용한다. `index.html:459`는 금액 입력 기본0이며 $50를 고객 한도로 고정하지 않는다. 검사한 `app.py`, `generation_queue.py`, `media_bridge.py`, `provider_billing.py`, `ledger.py`에는 UsageJournal/$50 공통 상한이 연결돼 있지 않다.

판정은 **승인된 개발 시험 범위 유지**다. FR-044/080/081 및 MS-FR-18의 조직·고객·모든 공급자 공통 예산 전체 구현 완료를 뜻하지 않는다. 시험 원장과 제품 원장이 분리됐다는 사실을 비용 통합 완료로 바꾸지 않는다.

## 4. SPEC-MS-001의 문서 온톨로지 등록 — 확인된 미완료

추가 명세는 두 범위를 명시적으로 분리한다.

- §7.1 (`:300–304`): 고객 그룹의 공식 설정·활동기·취향·곡 예외·기준 이미지가 플랫폼 DB/자산의 canonical state라는 요구.
- §15.2 (`:667`): 이 문서를 SPEC-MS-001로 프로젝트 지식 관리에 등록하고 MS-FR/MS-AT 및 공급자 Source/재검토 연결을 남기라는 요구.

직접 JSON을 읽은 결과:

| registry | revision / updated_at | objects / heads | 신규 모듈·MS-FR·MS-AT |
|---|---|---|---|
| `docs/knowledge/project_kit/registry/knowledge.json` |3 / 2026-10-23T13:08:54+00:00|1,666 / 882|0|
| `docs/specification/IP_Music_Video_Platform/project_kit/registry/knowledge.json` |동일|동일|0|

두 파일 SHA256은 `43713eb30b990c92b08258dec4f825b5595be5763f430150d7da6c74062eada7`로 같다. `registration-evidence.json`에 경로/해시/검색 키/일치 객체 목록을 보존했다. registry_revision은 두 파일 `:119972`, updated_at은 `:119974`다. ID 부재는 한 행으로 증명하지 않고 전체 objects membership을 확인했다. 새28 MS-FR/38 MS-AT가 프로젝트 registry에 들어갔다고 볼 근거가 없다.

이것은 **명시된 문서 등록 작업의 누락**이다. 그러나 온톨로지 전체 완료를 허위 표시한 모순까지 확인되지는 않았다. `ontology.py:1–5`는 자신이 project knowledge registry나 인증 계층이 아니라고 명시한다. `project_ontology.py:9`는 runtime workspace/project scope를 사용한다. `docs/knowledge/project_kit/README.md:3,46–54`와 명세8장 `:13–23`도 문서 지식과 고객 IP runtime을 구분한다. `docs/handoff-20261025-spec-ms-001.md:14`는 전체 새 명세 완료로 보고하지 말라고 명시한다.

최소 후속 조치는 새 Document/Requirement/Test/Source 및 기존 FR 연결을 등록하고, 최신 Runway 교정을 별도 Decision/문서 버전으로 연결하는 것이다. 기존 원문을 지우거나 fixture pass를 product/live 검증으로 승격하지 않는다. KMR-001/002/005/017의 안정 ID·현재 기준·변경 영향·증거 수준과 관련된다. 이 감사에서는 registry mutation이나 CLI 승격을 실행하지 않았다.

## 확인된 비오해와 한계

추가 범용 스캔으로 확대하지 않았다. 초기 관련 파일 대조에서는 다음을 확인했다.

- local-only를 다중 사용자 production으로 표시한 근거 없음: `README.md:33,37`, `app.py:145`는 authentication=false/single-local-workspace를 명시.
- 규칙 콘티를 실제 AI로 표시한 근거 없음: `guided.py:1,37`, `index.html:540,602`의 로컬/모의/AI 아님 표시. 실제 Anthropic 경로와 구분돼 있음.
- ontology를 추출만으로 축소한 근거 없음: runtime에는 version/proposal/approval/rollback과 관계 영향 구조가 존재(`ontology.py:120–200`, `project_ontology.py:55–75`). 이것이 전체 계약 통과를 뜻하지는 않음.
- root Master_Specification.md와 보존본 docs/originals/Master_Specification.md의 현재 hash가 같고 원 개발계획 문서도 존재. 모든 연구 문서의 역사 무결성이나 최신성 전체를 검증한 것은 아님.
- Minimum90 점수는 이번 감사에서 재평가하지 않았고, 기존의 heuristic/incomplete 표시를 허위 실측으로 분류하지 않았다.

## 증거 고정·실행 범위

주 snapshot 시각 **2026-10-25T14:01:27.281742+00:00**. 문서 registry 추가 capture 시각은 개별 manifest에 기록했다. `snapshot-manifest.json`에 각 파일의 bytes/mtime_ns/SHA256을 보존했다. 종료 대조 **14:06:48 UTC**, 대상 원본 변경0/snapshot 원본 변경0이다. 판정은 이 고정본 기준이며 이후 기능 세션의 Runway 제거는 별도 확인이 필요하다.

수행한 것은 코드·문서 읽기, JSON 객체 membership 대조와 해시 비교다. 테스트 실행/앱 DB 접속/키 및 인증파일 읽기/외부 API/브라우저/서버 재시작/경쟁사 조작0. 원본 코드·문서·registry 수정0, 감사 폴더만 작성했다. 도구 승인 거부나 불명 실행 결과는 없으며 부모가 확인한 대화 이력과 이 코드 근거를 합쳐 최종 교정 범위를 정하면 된다.
