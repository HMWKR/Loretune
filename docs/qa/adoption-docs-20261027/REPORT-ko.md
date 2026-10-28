# AD01–AD07 문서 채택·정합화 결과

2026-10-27 UTC · **도입 방향 확정, 문서 반영 완료, 구현 미재개.**

## 승인과 핵심 결정

사용자 `Sentinel_dd01ccfa2ffc819197e6d67fa402ecfc`와 `Sentinel_c6a68879bed8819182c6ccce6dafb174`는 제안 AD01–AD07 전부를 문서에 반영하고 **일단 문서만 작성**하도록 승인했다. 최신 결정은 개인 제작 기본·팀 협업 선택이다. 개인의 기획→생성→검토·편집→출력·재개에 팀 생성/초대/공유/타인 팀 승인이 필요 없어야 한다. 비용·권리·실행 범위·사람의 결정·비파괴 버전·복구는 개인도 유지한다.

AD03 팀 기능 및 AD04/05의 팀 변형은 인증·서버 권한·입력/파일 접근·철회·동시성 기반 이후 단계다. 개인 AD04/05는 팀 기반을 선행 조건으로 삼지 않는다. 상세 단일 기준은 [채택 설계](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md)이며, 신규 수용기준 개인10·팀9·공통8은 **설계/NOT RUN**이다. 이는 새 제품시험 통과 수가 아니다.

## 현재 버전과 이번 작업의 범위

- 마지막 전체 검증은 [416회귀 polling manifest](../chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json), 동결2026-10-26 20:48:43.131965 UTC다. HTML `4e96344612858c553cb47ec6c7561524016d384c77b61aa655eb2b9a72851e91`, CSS `348e0f0fbe4bdc617ff0d94b7e7a11d4bfd3862df2020312412bc264fa65361b`. 구현팀의 관련18은 전체에 포함되고, CQ-R01 수정본 독립 최종 재검증은 별도다.
- 현재는 [세션 baseline](../chat-conversations-20261027/BASELINE.json) 이후 `chat_sessions.py` 신규, `app.py/chat_runtime.py/chat_protocols.py/production_tools.py/production_context.py` 부분 변경 상태다. 기존 실행기18개 통과 인계만 있고 새 세션/UI·전체 회귀는 미완료다. 이전416 결과를 현재 partial에 적용하지 않았다.
- 문서 작업 시작2026-10-27 00:41:32.966531 UTC에 [BEFORE.json](BEFORE.json)으로 제품·테스트·원본151파일 SHA와 대상 문서를 고정했다. 기존 문서13개는 [before](before/)에 보존했다. 디자인 INDEX는 추가하기 직전에 사본/해시를 기록했다.
- 제품·테스트 코드·DB·서버·API·설치·배포·업로드는 변경하거나 실행하지 않았다. 외부 연구·aethonSaaS 원천 변경·엔진 재실행도 없다. 이번 검사는 문서의 링크·구조·해시 비교이며 제품시험이 아니다.

## 작성·수정 목록 — 12묶음

기존 유지 문서13개 수정, 새 정체성 보충문1개 작성. QA 보고/전후 manifest·보존사본은 검증 산출물이며 별도의 제품 명세가 아니다.

|묶음|문서|핵심 반영|
|---|---|---|
|D01|[README](../../../README.md)|개인 기본/팀 선택,416 vs partial, 현재 entry와 구현 보류|
|D02|[단일 PLAN](../codex-cli-assessment-20261026/PLAN-ko.md)|문서 단계만 완료, AD 단계·재개 조건·G0–G7, 역사 상태 보존|
|D03|[세션 계획](../../design/CHAT-SESSION-PLAN.md)|부분 구현/검증 한계, 개인 대화, 기존 확정 병행 정책,07 적용시점 차이|
|D04|[누락 등록부](../OMISSION-REGISTER.md)|23요구 유지·현재 전이·원인 한계·AD 연결·재발 방지|
|D05|[남은 작업](../REMAINING-WORK.md)|채택 backlog와 개인/팀 단계, 구현·외부·증거 잔여|
|D06|[38AT 추적](../SPEC-MS-001-ACCEPTANCE-TRACE.md)|414/416 좁은 근거, AD/CS/P/T/C 대응, 원문조건 불변|
|D07|[현재 디자인 QA 계획](../../design/CURRENT-DESIGN-QA-PLAN.md)|기존CQ의 후속 상태·AD 영향화면/유한수용, 새점수 없음|
|D08|[reference lock](../design-system-redesign-20261026/REFERENCE-LOCK.md), [token spec](../design-system-redesign-20261026/SEMANTIC-TOKEN-SPEC.md), [방법론](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md), [기존 색인](../design-system-redesign-20261026/INDEX.md)|donor는 계약 참고, neutral 역할/값 보존, 실제 스킬 사용 구분, 현재/역사·전달 경계|
|D09|[새 정체성 보충문](../../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md) §1–3|기존Aethon→피벗Loretune→현재Aethon, 개인기본/협업선택. 역사 사업MD/Master/DOCX 원본 불변|
|D10|같은 보충문 §4 및38AT|원본07와 두 등록사본 불변, no-MCP/fal·독립모델·권리/비용/승인 보존|
|D11|[모델화 계획](../../design/AI-MODELING-PLAN.md) 및 PLAN 범위|Blender/이질수집/자동ontology는 PLAN ONLY 유지|
|D12|[AD 도입 설계](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md)|7항목 채택, 개인/팀 의존성·수용·제외·단계·잔여 결정의 단일 기준|

원본 사업계획의 ‘별개의 신규 사업’ 문구와 협업/승인 조율 가설은 역사 자료로 보존했다. 이전 설명의 ‘팀 협업 OS’를 원문 인용이나 모든 사용자의 필수 경로로 취급하지 않는다. 실제 사업계획 §1.2에는 개인 VTuber도 포함돼 있음을 확인했다. 보충문은 최신 사용자 해석과 기능 경로만 명시하며 시장 수치·고객 성과·요금·법적 소유관계는 새로 확정하지 않았다. 원본07의 조직/운영 수용조건도 개인 기본 결정을 이유로 삭제하지 않았다.

## 문서 검증

최종 링크/해시·구조 대조는 [VERIFICATION.json](VERIFICATION.json), 변경 문서의 SHA는 [AFTER.json](AFTER.json)에 기록했다. 외부 서비스나 제품 기능 검증은 포함하지 않는다.

<!-- VERIFIED-RESULTS -->
- **보호 대상151파일 전후 SHA-256 일치**, 변경/누락0. 제품/테스트144파일과 원본7파일의 확인 범위다. 원본07·두 등록사본 SHA는 모두 `962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`로 유지됐다. 원본 사업MD/Master/DOCX도 불변이다.
- **로컬 Markdown 링크 680개 확인, 누락0.** 외부 URL의 네트워크 접속·가용성이나 before 보존사본 내부의 상대링크 재작성은 하지 않았다.
- **원본38AT의 제목/입력/통과조건114행 전후 동일**, 현재 등록부 OM01–23 모두 유지. 신규 개인10·팀9·공통8 수용은 NOT RUN 설계이며 기존 AT를 대체하지 않는다.
- 현재 상태 문구·AD 단계·원본/보충문 권위·개인/팀 의존성·skills 실행 경계·계획전용/제외를 문서상 대조했다. 상충할 수 있는07§3.2/CS08모델 변경 UX는 미해결 계약 차이로 남겼다.
- **유지 문서13개 + 새 보충문1개**만 제품 관련 문서 변경이다. 기존 문서13개의 정확한 사본과 사전 hash를 보존했다. 앱·테스트 실행0,새pixels/점수0,외부API/업로드0. 검증 시각 `2026-10-27T00:58:21.913720+00:00`.
<!-- /VERIFIED-RESULTS -->

## 남은 단계와 결정

구현 재개 지시가 있을 때 P1 입력/대화/상태와 기존 partial 검토→P2 개인 이어 만들기/의견→P3 선택적 팀 권한→P4 팀 변형, 각 단계에 AD07·독립 QA를 적용한다. 지금 G4 구현은 미개시다.

응답 중 모델 변경의 원본07 ‘완료 후 적용’과 CS08 ‘변경 거절’ 차이는 재개 전 설명·정합화해야 한다. 팀 역할/입력 공개 범위/철회 후 접수 작업·결과 접근, 실제 모델별 자료 capability·운영 비용/보존 정책도 해당 단계 전에 결정한다. 확정된 개인/팀·AD채택·복수대화/격리/병행을 다시 미정으로 돌리지 않는다.

실공급자 전체 조합·실청구·새 세션 UI/회귀·실제 zoom/스크린리더/고객연구·디자인90·최신 Library 전달의 기존 한계는 유지된다. 과거 실제 Claude15응답과 fake 미디어/로컬 렌더 증거는 당시 범위로 보존하며, 모델 원문 설명 오류 전체 해소를 주장하지 않는다. **산출물은 로컬 문서다. Library 등록·사용자 파일 전달은 이번 작업에서 수행하지 않았다.**
