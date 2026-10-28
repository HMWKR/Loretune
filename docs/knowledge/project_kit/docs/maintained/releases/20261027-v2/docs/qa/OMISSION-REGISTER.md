# Aethon 요구사항 누락·완료 근거 등록부

## 최신 상태 해석 · 2026-10-27 후속

아래 23개 표의 ‘구현 미재개’, OM-08의 새 UI 미구현 및 OM-17의 REA 차단은 해당 시점 기록이다. 이후 복수 대화와 다음 모델 예약이 부분 구현되고, REA의 공개 웹·Blender 바이너리 요약이 제한적으로 수행됐다. 이것이 전체 CS 수용, Blender 3D 구현이나 과거 차단 작업 전체의 성공을 뜻하지는 않는다. 추가된 음원·자막·미리보기 수정과 [435개 회귀](codex-workflow-review-20261027/regression-435-20261027.log)는 [작업 기록](codex-workflow-review-20261027/REPORT-ko.md)과 연결한다. 최신 잔여는 [남은 작업](REMAINING-WORK.md)에서 관리하며 아래 이력의 완료 분류·합계를 소급 변경하지 않는다.

누락 점검 시 최신 사용자 지시인 AI 외 자체 플랫폼, 음원 우선/사진 선택, 실제 제작→편집→출력→재개, 원인 조사 후 재시도, 그리고 실무 준비 이후 AI 영상 모델 시험을 함께 대조한다. 확인된 실패, 구현, 시험 표본과 외부/운영·실사용자 미검증을 분리한다.

## 2026-10-27 후속 상태

아래 OM-17의 REA 실행 차단은 당시 기록이다. 현 세션의 REA MCP 공개 웹 관측과 설치 Blender Mach-O 요약은 성공했으며 각각 제한된 관측이다. Blender 기능·플랫폼 통합과 과거 차단된 모든 REA 작업의 완료를 뜻하지 않는다. 복수 대화 등 이후 구현과 남은 항목은 [후속 검증·누락 점검](codex-workflow-review-20261027/REPORT-ko.md), Blender 관측은 [계획의 현재 보충](../design/AI-MODELING-PLAN.md)을 따른다.

## 당시 등록부 · 2026-10-27 문서 채택 시점

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** 최신 사용자 승인 `Sentinel_dd01ccfa2ffc819197e6d67fa402ecfc` / `Sentinel_c6a68879bed8819182c6ccce6dafb174`를 반영했다. [단일 도입 설계 AD01–AD07](../design/AETHONSAAS-ADOPTION-PROPOSAL.md), [정체성·개인 기본/팀 선택 보충문](../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md), [현재 잔여](REMAINING-WORK.md), [문서 변경 검증](adoption-docs-20261027/REPORT-ko.md).

23개 원요구를 유지한다. AD01–07은 아래 OM에 연결된 채택 설계이며 기능 완료 항목을 늘리기 위한 새 집계가 아니다. 아래 현재표가 이전410시점 분류/‘결정 대기’보다 우선하며, 과거 표·원인·완료 근거는 삭제하지 않는다. 항목별 크기가 달라 완료율을 만들지 않는다.

|ID|현재 분류(기능 완료의 범위 제한 유지)|완료 범위 또는 정확한 잔여|
|---|---|---|
|OM-01|완료—표시/문서|기존 표시명 증거 유지. 새 정체성 보충문으로 피벗 이후 기준·개인 기본·팀 선택 연결. 원본/내부 식별자 보존.|
|OM-02|증거제한|세 역할·3chat 선택 구현. 전체 실제 공급자 실행은 미검증/차단.|
|OM-03|외부차단|일반 live 설정·계정·권리·가격·fal 결과 수신/12조합 경계.|
|OM-04|증거제한|scoped snapshot/provenance 완료; 검색 index·확장 품질 아님.|
|OM-05|완료|C1 실제 Claude prompt 표본과 fake fal 전달. 실제영상 품질 아님.|
|OM-06|완료|CC01 원 반례/독립재검증 보존, 새 반례 없음.|
|OM-07|완료|CC02 byte/known-not-sent/unknown 반례 닫힘.|
|OM-08|부분 구현 중단·증거제한|복수대화/격리/공유canon/병행 결정 확정. 신규chat_sessions 및5파일 partial 보존. 새UI/CS/전체회귀 미완료, 구현 미재개.|
|OM-09|완료|Mac 제한 모션·12프레임 수정·렌더·복원. M1/Q1/R1/R2의 범위.|
|OM-10|완료|E1 모델 timeline 제안·사람 적용·음원/자막 출력. 임의 새 편집기능 아님.|
|OM-11|증거제한|M1/R1/R2 역사 표본 및R414/R416 좁은 표시·polling 근거. 새 세션UI·현재전수브라우저/접근성 증거 아님.|
|OM-12|증거제한|로컬/fake/승인된 Claude 계약 완료; 모든 live/조직/실청구는 아님.|
|OM-13|증거제한|R414/R416 포함 각1920/1280 표본만. 현재partial의matched 화면 없음; 모바일추가 보류.|
|OM-14|증거제한|실제zoom/스크린리더/전엔진·모든키보드 미검증 보존.|
|OM-15|승인된 계획전용|모바일 추가 작업 명시 보류.|
|OM-16|증거제한|참조/스킬 적용 기록 있음. 최소90 달성 증거 없음; 과거81≠현행 점수.|
|OM-17|외부차단|REA 등록·정적 공개 연구와 inference 실행 거절을 구별.|
|OM-18|완료—기존 체크포인트|R1/R2의 유한 독립검사 인계 유지. 새partial/AD 구현검증 완료 아님. 이번 문서범위 단일작성·원본보존 검사.|
|OM-19|완료—이번 문서 정합화|D01–D12 현재입구·416/partial·AD전체채택·개인/팀 수용 연결. 제품완료/Library전달과 별개.|
|OM-20|외부차단|최신 Library 등록/전달 ID 없음. 로컬 산출물·과거 ID를 최신 전달로 바꾸지 않음.|
|OM-21|승인된 계획전용|이질 입력/ontology 진화의 구현 승인은 별도.|
|OM-22|승인된 계획전용|AI-MODELING-PLAN 문서 완료, Blender 제품 구현/실행 없음.|
|OM-23|증거제한|원본07 보존/등록 정상. [38AT 현행 추적](SPEC-MS-001-ACCEPTANCE-TRACE.md)의 문서 연결 완료; 전체제품 수용·live/운영조건 잔여 유지.|

### 문서 채택 당시 상태전이·원인·예방

|ID/출처|관측한 공백·원인|현재 조치·담당/수용 증거|재발 방지 gate|
|---|---|---|---|
|OM-01 / 피벗·최신 개인기본 결정|역사사업문구 ‘별개의 신규 사업’ 및 협업 중심설명과 현재결정의 시간 차이. 원문작성자의 심리적 원인 미확인|문서 담당이 dated보충문 작성·입구 연결. 원본사업MD/DOCX/Master 그대로. 사업성과/시장수치 변경0|현재명칭/사업기준/개인완주/선택협업을 checkpoint마다 확인; 내부키 일괄치환 금지|
|OM-08 / 세션확정+문서만 지시|CC01에서 별도세션을 제외했던 역사 후 부분구현 시작·사용자정지. 사고적누락/완료로 단정하지 않음|[세션 계획](../design/CHAT-SESSION-PLAN.md)과before baseline, 현재hash 연결. 신규1+변경5; 기존실행기18 인계만, 새UI/CS미검증. primary 단독 재개 지시 대기|416검증본≠partial, CS01–18·개인P04–P07·공통예산/unknown 회귀. 원본07§3.2/CS08변경UX차이 해소 전 통과 금지|
|OM-19 / 요구별문서·누락예방 요청|서로 다른checkpoint 문서의 latest/partial 반영 범위 불일치 확인. 개인의 망각/실수 여부는 알 수 없음|D01–D12 현재/역사 구분·상호링크로 이번문서공백 닫힘. [전후기록](adoption-docs-20261027/REPORT-ko.md)|README→PLAN→마지막검증/현재partial→추적표/등록부의 동일버전경계. 문서채택/구현/시험/전달 각각별도|
|OM-23 / 원본07전체조건|문서38행연결은 기능38개전체통과 아님; 조직/실제12조합/운영조건 제한 유지|AD/P/T/C와38AT 교차표 추가, 원문/등록사본 불변. 소유:명세·구현 담당|개인기본을 원문조직조건 삭제로 사용 금지. 해당범위 미실시/차단을 유지|
|OM-16/20 / 디자인90·실제전달|현재90증거 없음, Library prepare_uploads unavailable 기록. 이번 지원상태 재조회 안 함|기존상태 유지. 이번은 로컬MD만; 새pixels/점수/업로드0|문서수정이품질점수/고객연구/등록ID를 대신하지 않음|

### 채택 항목의 요구 연결

|AD|연결 원요구|현재 문서상 결과 / 남은 구현|
|---|---|---|
|AD01|OM04/05/12/23|자료역할·정확버전·제외·미지원 계약 및P02/03. resolver/UX 확장은 미재개|
|AD02|OM06/07/08/18/23|개인 독립대화·공유승인기준·격리/P04–P07. partial중단·CC01/02닫힘보존|
|AD03|OM12/23|선택적 팀권한 T01–T06 채택. 실제auth/ACL 의존, 미구현|
|AD04/05|OM10/12/23|개인 P08–P10 먼저 가능. 팀 T07/08은AD03이후. 원본·승인·cost 불변|
|AD06|OM02/03/11/12/23|기존영수증/원장/복구 보강 설계. 실제제출/미디어/비용 증거는 별도|
|AD07|OM16/18/19/20/23|이번문서연결 적용. 새제품·실제사용자연구/외부전달 미실시|

### 이번 체크포인트

- [x] 원요구·최신사용자결정·AD전부채택·제외·개인/팀 경로를 연결했다.
- [x] 마지막416검증/현재partial/새시험미완료를 구별하고원본·코드전후hash를 검증했다.
- [x] D01–D12 문서상태·링크·원본보충관계를 대조했다. 과거시험/manifest/183행workflow 근거보존.
- [x] 비용/권한/동시성/복구/접근성 계획과 실제skill read/manual/engine범위를 연결했다.
- [ ] 제품구현재개·새세션UI/전체회귀·실공급자/디자인90/접근성완료·Library전달은 이번에 수행하지 않았다.

최신 제품 증거는 [R416](chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json), 현재partial은 [세션BASELINE](chat-conversations-20261027/BASELINE.json)과 [이번BEFORE](adoption-docs-20261027/BEFORE.json)로 구분한다. 아래날짜별문구의 ‘현재’는 당시시점이다.

## 역사적 등록·실행·상태전이 기록 — 원문 보존

## CQ-R01 표시 정합성 후속 — 2026-10-26

기능팀은 독립 재검증이 발견한 **모션 없는 작품의 모델 선택 polling 누락(P2)**을 수정했다. `model_settings`/catalog 변경 감지를 추가하고, 열린 설정창의 미저장 선택은 보존하며 재열기 때 최신 저장값을 읽는다. 원 반례4PASS/2FAIL→6PASS, 최종전체416/416·관련18/18 및 실제 두 탭 GPT→Grok/미선택·초안/포커스/작품 격리 확인. 이 수정본의 독립 재검증은 아직 별도다. [구현·검증](chat-model-receipt-display-20261026/polling/REPORT-ko.md), [최종 manifest](chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json), [수정 전 독립 발견](independent-chat-model-receipt-recheck-20261026/REPORT-ko.md). OM-02/11/13의 좁은 표시 근거만 추가하며23개 분류·독립 세션 결정 대기·live/접근성 제한은 바꾸지 않는다. 기존410/414와 아래 당시 “현재” 문구는 해당 빌드의 역사적 증거다. 외부 API·공유DB·키·유료호출·설치·배포0, 임시 서버/탭 종료.

## 23개 요구 최종 대조 — 2026-10-26 RECEIPT 동결본

**현재 기준은 19:35:59 RECEIPT와 최종 독립 감사다.** [남은 작업·요구출처·의존성·수용조건](REMAINING-WORK.md)에 23개 전체를 대조했다. 제품 소스/추가 테스트30개는19:40:34 읽기 확인에서 manifest와 모두 일치했다. 07 원본·두 등록 사본과 catalog source hash도 일치한다. 아래 이전 시각의 진행 중/차단/WIP 문장은 역사적 기록이며 현재 실행 대기가 아니다.

- [구현팀 최종 보고서](native-motion-20261026/server-receipt-ui/REPORT-ko.md) / [RECEIPT-MANIFEST](native-motion-20261026/RECEIPT-MANIFEST.json): 전체410/410, 현재 승인·과거 조회·모델 원문 분리, 최신 served 표본. 모션 후속 실제 Claude15응답은9+6이며 마지막 표시 변경의 새 호출은0이다.
- [최종 독립 재검증](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md): 격리10/10, 현재 stale/과거true/원문·버전·타작품/장면·악성원문·구grant 거절·조회불변, 소스/기존 승인경로 보존. 저장 화면3장 독립 열람이며 새 브라우저/API 실행은0이다. 전체410을 재실행한 것이 아니다.
- **NM-Q01 서버 승인 사실 표시 계약은 닫힘. Claude 원문 오류 자체는 남음.** NM-Q02의 기존 서버diff·실제 설명 표본 결과는 유지한다. 모션·편집 기능과 일반 언어 정확성/실제 fal 완주를 분리한다.
- 현재 분류는 **완료8 / 증거제한8 / 승인된 계획전용3 / 외부차단3 / 미구현1**다. 완료율이나 제품 점수가 아니다. 미구현1은 독립 대화 세션 기능이다. README 최신 안내와38AT 추적 문서 연결은 후속 명시 요청으로 닫았다. 제품 전체 미구현 기능 수를 뜻하지 않는다.

|ID|현재 분류|완료 범위 또는 정확한 잔여|
|---|---|---|
|OM-01|완료|Aethon 표시, 내부 호환 식별자 보존. E8/현재 소스.|
|OM-02|증거제한|세 역할·3chat 선택 구현. 전체 실제 공급자 실행은 미검증/차단.|
|OM-03|외부차단|일반 live 설정·계정·권리·가격·fal 결과 수신/12조합 경계.|
|OM-04|증거제한|scoped snapshot/provenance 완료; 검색 index·확장 품질 아님.|
|OM-05|완료|C1 실제 Claude prompt 표본과 fake fal 전달. 실제영상 품질 아님.|
|OM-06|완료|CC01 원 반례/독립재검증 보존, 새 반례 없음.|
|OM-07|완료|CC02 byte/known-not-sent/unknown 반례 닫힘.|
|OM-08|미구현|같은 작품 독립 session_id/UI 없음. 먼저 세션/공유canon/unknown 귀속 계약 필요.|
|OM-09|완료|Mac 제한 모션·12프레임 수정·렌더·복원. M1/Q1/R1/R2의 범위.|
|OM-10|완료|E1 모델 timeline 제안·사람 적용·음원/자막 출력. 임의 새 편집기능 아님.|
|OM-11|증거제한|M1 새 모션 UI·R1 receipt 표본, R2 저장화면 열람. 전체 접근성/현재 전수브라우저 아님.|
|OM-12|증거제한|로컬/fake/승인된 Claude 계약 완료; 모든 live/조직/실청구는 아님.|
|OM-13|증거제한|1920/1280의 해당 빌드 표본; planning scroll과 workspace shell 구별.|
|OM-14|증거제한|실제zoom/스크린리더/전엔진·모든키보드 미검증 보존.|
|OM-15|승인된 계획전용|모바일 추가 작업 명시 보류.|
|OM-16|증거제한|참조/스킬 적용 기록 있음. 최소90 달성 증거 없음; 과거81≠현행 점수.|
|OM-17|외부차단|REA 등록·정적 공개 연구와 inference 실행 거절을 구별.|
|OM-18|완료|현재 유한 체크포인트의 계획/단일writer/보존/최종 독립10검사 인계. 범용 전수보증 아님.|
|OM-19|완료|README 최신 안내를410/RECEIPT·최종독립10으로 갱신,403/393은 역사 보존. 현재 추적/잔여/등록부 연결.|
|OM-20|외부차단|최신 Library 등록/전달 ID 없음. 로컬 산출물·과거 ID를 최신 전달로 바꾸지 않음.|
|OM-21|승인된 계획전용|이질 입력/ontology 진화의 구현 승인은 별도.|
|OM-22|승인된 계획전용|AI-MODELING-PLAN 문서 완료, Blender 제품 구현/실행 없음.|
|OM-23|증거제한|원본07 보존/등록 정상. [38AT 현행 추적](SPEC-MS-001-ACCEPTANCE-TRACE.md)의 문서 연결 완료; 전체제품 수용·live/운영조건 잔여 유지.|

**RW-01 최신 README 안내와 RW-03 원본07의38AT 최신 추적 문서 연결은 완료했다.** 부모의 후속 명시 권한으로 README와 새 [수용항목 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)를 작성하고 등록부/잔여표에 연결했다. 원본07·등록 JSON·primary PLAN은 그대로다. 제품 잔여 **RW-02 독립 세션**의 계획은 primary가 별도 작성 중이며 해당 파일/제품 코드는 변경하지 않았다. 디자인90/접근성 증거 과업, Library/REA 외부차단, ingestion/Blender/mobile 범위 제한은 유지한다.

이 표와 [REMAINING-WORK](REMAINING-WORK.md)가 현재 대조 결과다. 원래의 원인·전이·실패 근거는 아래 그대로 보존하며, 과거에 “현재”라고 쓴 문장은 해당 시각을 뜻한다.

## 문서 정합화 후속 — OM-19/RW-01 및 RW-03 닫힘

[README](../../README.md)는 최신410/RECEIPT 및 [최종독립보고서](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md)로 연결했다.403/393은 역사적 기준으로 남겼다. [38AT 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)는 원문 입력·기대문구38개/28FR, 현행 코드,68개 고유 시험함수와410로그의 `ok` 행, 실제Claude/합성/실공급자 한계를 연결한다. **38개 행의 문서 정합화이지38개 제품시험 통과가 아니다.** 최신원본해시/로컬링크를 확인하며 기존 catalog/coverage와 원요구서를 변경하지 않는다.

원인 구분: OM19는 후속build를 README 입구에 아직 반영하지 않은 사실, RW03은 최신실행근거가 이전등록추적에 연결되지 않은 사실이다. 사람의 의도나 “잊음”은 확정하지 않는다. 예방 gate는 새checkpoint마다 README→manifest/독립검토→현재AT추적→잔여표를 연결하고, 문서완료와 기능완료를 따로 기록하는 것이다.

## 이전 체크포인트 기록 — 당시 사실 보존

> **2026-10-26 19:34 현재:** NM-Q01 승인 사실의 deterministic 표시를 구현·검증했다. 과거/현재·모델 원문을 분리하며 자유서술 정확성 해결로 확대하지 않는다. 410/410, served1920/1280 표본 완료, 추가Claude/fal0. OM-09/10/11의 기존 저작·출력·편집 근거는 보존하고 해당 승인 설명의 사용자 표시 보강을 연결한다. [현재 보고서](native-motion-20261026/server-receipt-ui/REPORT-ko.md), [manifest](native-motion-20261026/RECEIPT-MANIFEST.json).

> **2026-10-26 19:05 품질 후속:** NM-Q01/NM-Q02의 저장 승인 문맥과 서버 timeline diff를 수정했다. 최종403/403, 추가Claude6응답·누적usage$0.0381186/실청구미확인. NM-Q02 설명 표본 통과, NM-Q01 핵심 구분 개선 확인이나 ontology를 실행 설명 근거로 섞는 문장은 잔여다. [현재 보고서](native-motion-20261026/REPORT-ko.md), [최종 manifest](native-motion-20261026/QUALITY-MANIFEST.json). 아래 이전 시각의 안내는 이력이며 해당 시점의 증거를 보존한다.


> **2026-10-26 후속 갱신:** OM-09/10/11은 실제 Claude9응답과 현재 served UI 결과로 아래 갱신했다. 전체393/393, 누적 usage가격$0.0320001/실청구미확인. [현재 보고서](native-motion-20261026/REPORT-ko.md), [고정 manifest](native-motion-20261026/FOLLOWUP-MANIFEST.json). 아래17:32 진단/우선순위 문장은 당시 이력이며 현재 실행 대기로 해석하지 않는다. 다른 OM 항목의 범위/판정은 이번 갱신에서 변경하지 않았다.


작성: 2026-10-26. 소스 관측 기준은16:03:48 UTC이며, 실행 상태는 후속 독립 진단의 **17:32 UTC 공식 조회**를 반영했다. **모션 실제 Claude 시험은15:51:35에 blocked_before_message로 중단됐고 Messages는0회다. 기본 구현 turn은17:32에도 inProgress/error=null이지만 원인·앱 화면은 미확인이다.** 로컬 구현 근거는 보존하며 기능 완료·동결 릴리스로 판정하지 않는다.

이 파일을 요구사항 누락과 체크포인트의 단일 등록부로 유지한다. 실행 계획의 권위는 [canonical PLAN](codex-cli-assessment-20261026/PLAN-ko.md)에 있고, 본 문서는 그 요구와 증거를 연결한다. 제품 소스 및 PLAN 작성자는 통합 담당 한 명이다. 최초 감사의 쓰기는 이 파일 하나였으며, 후속 명시 요청으로 OM-22의 [독립 모델화 계획](../design/AI-MODELING-PLAN.md) 작성과 해당 행 갱신만 추가했다. 별도 중복 감사 보고서를 만들지 않는다.

## 이전 17:32 우선순위 기록 — 현재 상태는 위 체크포인트 참조

1. **OM-09/10/11 — 실행 차단과 미확인 작업 상태:** [17:32 독립 진단](stalled-primary-session-diagnosis-20261026/REPORT-ko.md)을 연결했다. 저장 trial은15:51:35 송신 전 차단/Messages0, 공식 turn은inProgress/error=null/마지막 tool completed다. Codex 앱 CUA 접근은 안전 제한으로 거부되어 화면·대기 원인은 미확인. 이 차이를 기능 완료나 전체 구현 실패로 바꾸지 않으며, 실행 종료/취소 성공 확인 없이 두 번째 writer·새 유료 시험을 시작하지 않는다.
2. **OM-08/23 — 전체 완료 범위의 공백:** 같은 작품의 독립 대화 세션은 CC01에 포함되지 않는다. 07 전체 요구와 현재 로컬 체크포인트 범위를 구분하고, 제외된 요구를 폐기된 것으로 취급하지 않는다.
3. **OM-19 — 현행 상태 안내:** PLAN 상단/README의 완료 빌드, 진행 중 소스, 역사적 구역 뒤에 붙은 K.4/K.5를 구분하는 현행 상태표가 필요하다. 완료 보고서 원문은 소급 수정하지 않는다.
4. **OM-22 — 문서 공백 닫힘:** [Blender 모델화·조명·카메라 독립 계획](../design/AI-MODELING-PLAN.md)을 작성했다. 사용자 흐름/대안/SceneSpec/모호성/수용 gate를 연결했으며 **제품 구현은 계속 PLAN ONLY**다.
5. **OM-03/14/17/20 — 외부·환경·전달 제한:** 일반 live 공급자, 실제 zoom/보조기술, REA 실행, Library 전달은 로컬 시험 성공으로 닫을 수 없다. 설치/호출/우회는 이번 감사 범위 밖이다.

## 상태와 원인 표기 규칙

- 허용 상태: **완료(completed)** / **진행 중(in progress)** / **미검증(unverified)** / **차단(blocked)** / **명시적 계획만(explicitly plan-only)**.
- 완료는 각 항목에 적힌 범위와 빌드에만 적용한다. 제품 전체 완료나 현재 변경 중 소스의 전수 통과를 뜻하지 않는다.
- 유형은 별도다: 확인된 수리 누락, 문서/계획 공백, 의도적 범위 제한, 진행 중, 외부 차단, 검증 공백. 미검증은 실패가 아니다.
- 원인은 파일/동작으로 확인된 사실만 확정한다. “잊었다”, “서둘렀다” 같은 사람의 의도는 추정하지 않는다. 사고적 누락인지 판단할 근거가 없으면 **원인 미확인**으로 남긴다.
- 각 상태 변경은 아래 전이 이력에 이전/다음 상태, 증거 빌드, 실제 수행 주체를 추가한다. 완료 근거와 원 반례를 삭제하지 않는다.

## 권위·증거와 빌드 경계

- U1: 부모가 전달한 사용자 요구 — 전체 작업의 누락과 작업방식을 확인하고, 누락 원인과 예방을 MD에 기록. 기록 메시지 `Sentinel_368045f4798c8191b2813e2a64b06a92`.
- U2: 183행 워크플로 `libfile_3f4825539680819196c9307c0a8d1ce1`. [PLAN A, L13–23](codex-cli-assessment-20261026/PLAN-ko.md)은 공식 read 1–183/has_more=false를 기록한다. 이번 감사는 그 기록과 부모 전달 요구를 대조했으며 첨부 원문을 새로 조회하지 않았다.
- U3: [07 원본](../../07_Chat_Directed_Multimodel_Production_Spec.md). SHA256 `962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`. 모델/도구/권리/승인 요구의 원본을 수정하지 않는다.
- E8: [Aethon UI 보고서](codex-cli-assessment-20261026/REPORT-ko.md), [manifest](codex-cli-assessment-20261026/implementation/FINAL-MANIFEST.json). HTML `d82ca93a64f31e71bf0c469b1b72b7c59c6a4bbe0403b969881349d8ec82f6e2`; CSS `4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`; media JS `ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`. 350회귀/served8상태/폼12조건/3초 로컬 출력은 **그 빌드의 구현팀 증거**다.
- C1: [CC01 수정·실Claude 보고서](cc01-context-fix-20261026/REPORT-ko.md), [manifest](cc01-context-fix-20261026/FINAL-MANIFEST.json), [독립 재검증](independent-cc01-fix-recheck-20261026/REPORT-ko.md).
- C2: [CC02 보고서](cc02-preflight-fix-20261026/REPORT-ko.md), [manifest](cc02-preflight-fix-20261026/FINAL-MANIFEST.json), [독립 재검증](independent-cc02-recheck-20261026/REPORT-ko.md). runtime `50ec18343dc4619aa2df8a5ffda7008a0a96c6bef71917c805c482700a51c54a`, transport `e7021df88da62058a746b370f6eca26aa26f45012a3ae7a2195c3cea2be6d0f0`. 365회귀와 독립 원 반례+6 guard는 분모가 다르며 합산하지 않는다.
- WIP: 16:03:48 UTC 로컬 읽기. HTML `eccf0e11ffaddbb60e4c38727a54ea3228eb246808b0c1203d87b9de967121e9`; app `26615dc7dacd66244b2e3dac2735722046fa7879657ed582c32c2d4cfc1a3580`; motion_scene `aec910b146d0e04d53c2e5560d312adf16c5985875c66afbb937928acc8529a3`; Swift helper `a2f41e73a434d57e455729ccf8aad3cc6986c4f9caf1d0fcef7030633835896e`; local_creation_tools `e72f5245712161a12567298f95ee78b8c3f3289edda2f086315491e0857b16e6`. CSS/media JS와 C2 runtime/transport는 위 값과 같았다. **WIP 해시는 served 검증이나 final freeze가 아니며 변경될 수 있다.**
- D1: [정체 상태 진단](stalled-primary-session-diagnosis-20261026/REPORT-ko.md), [공식 상태·도구 결과](stalled-primary-session-diagnosis-20261026/evidence.json), [파일 해시/mtime](stalled-primary-session-diagnosis-20261026/file-manifest.json). 대상 thread `01a170bf-5655-71b3-b6ec-6b2bcfe1a023`, turn `01a178d1-95fc-71a4-ac10-f4188a3ce231`. 등록부 갱신 시 summary/transport/turn/cleanup의 파일 SHA가 D1 manifest와 일치함을 읽기로 확인했다. D1의 공식 조회/화면 접근 시도는 진단 담당의 작업이며, 이 문서 담당이 재실행한 것이 아니다. 새로운 소스/served 검증도 아니다.

## 요구사항 → 증거 체크리스트

### OM-01 — Aethon 표시명과 호환 식별자
- **요구/출처·상태:** 사용자 명명, PLAN DP26-11/F. **완료**, 의도적 호환성 보존.
- **근거/빌드:** E8 branding-check와 manifest; 현행 `index.html:1,13`, `README.md:1–3`도 Aethon. 기존 Loretune 폴더·모듈·HTTP header·저장 키는 PLAN L139에 보존 목록이 있다.
- **공백·원인·영향:** 남은 내부 Loretune 문자열은 표시명 누락으로 판정하지 않는다. 전역 치환은 기존 초안·요청 복구를 깨뜨릴 수 있다.
- **조치/담당:** 통합 담당은 새 사용자 표시만 Aethon으로 유지. 경로/DB/인증 namespace 변경 없음.
- **수용/예방 gate:** visible name 검사와 기존 저장/복구 호환 검사를 각각 통과. grep 결과 0을 완료 조건으로 삼지 않는다.

### OM-02 — 독립 chat/image/video 선택과 실제 모델 ID
- **요구/출처·상태:** 07 MS-FR-01/03/09/11/27; PLAN B/S04. **완료 — 등록·선택·계약/fixture 범위만**.
- **근거/빌드:** `model_selection.py:7–20,32–53`, `chat_models.py:7–10`, `fal_models.py:10–14`; E8 모델 dialog 및 기존 protocol 회귀. 역할을 독립 변경하고 미검증 선택값을 지우거나 silent fallback하지 않는다.
- **공백·원인·영향:** 일반 실행 활성화는 별도다. 등록된 chat은 `anthropic-haiku-5-5`, `openai-gpt-6-luna`, `xai-grok-4-7`; image는 FLUX schnell/pro1.1, video는 Kling2.6pro/2.5turbo. 이것은 현행 로컬 catalog이며 공급자의 전체 지원 목록이나 live 인증 결과가 아니다.
- **조치/담당:** 기능 담당은 역할별 선택/고정 snapshot 회귀를 유지하고 실제 연결은 OM-03으로 분리.
- **수용/예방 gate:** 모델마다 registered / contract-tested / live-verified / active를 분리하고 제품 no-MCP 및 fal 경로를 보존. Runway는 벤치마크만.

### OM-03 — 일반 프로젝트 live 연결과 교차 공급자 완주
- **요구/출처·상태:** 07 MS-FR-02/10/24/25/26; PLAN FG26-02/03. **차단**, 외부 권한 및 아직 검증되지 않은 일반 연결 경계.
- **근거/빌드:** PLAN L104–105/227, `model_selection.catalog().live_execution=False`; C1은 실제 Claude+fake fal. 과거 fal 파일수신/CDN403과 후속 token403은 서로 다른 단계다.
- **공백·원인·영향:** OpenAI/Grok 실제 응답, 일반 프로젝트의 안전한 설정·전송 동의, fal 실제 결과 회수·등록·청구까지 한 과업 완주가 입증되지 않았다. “키만 넣으면 완료”라고 할 수 없다. 현재 외부 거절 사유의 실시간 재조회는 하지 않았다.
- **조치/담당:** 통합 담당/연결 소유자가 설정 코드·계정·입력권리·가격·허용 범위를 각각 확인한 뒤 명시된 live 시험만 수행. 이번 감사 호출0.
- **수용/예방 gate:** 선택 모델→실제 request→승인 scope→수신 파일→등록→검증 출력→usage/청구 구분을 한 build에 연결. fake 응답과 UI 버튼 존재로 닫지 않는다.

### OM-04 — 정식 설정·곡 예외·문맥·출처
- **요구/출처·상태:** 07 MS-FR-11/12, 원본 L302–318; PLAN S10/K.1. **완료 — 현재 scoped snapshot/provenance 계약 표본**.
- **근거/빌드:** C1 독립 보고서 L34–40: 현재 canon revision, stable entity/relation, provenance, 이전 version, A/B project 격리 확인. 모델 답변/요청 이력은 승인 사실로 자동 승격하지 않는다.
- **공백·원인·영향:** `production_tools.py`의 query는 검색 ranking/index가 아니라 scoped snapshot이다(PLAN FG26-01). 대규모 검색/자동 충돌해결까지 완료 아님. 원인은 현재 구현 범위를 제한한 설계이며 우발적 누락 여부는 미확인.
- **조치/담당:** 기능 담당은 source/scope/revision 계약 유지. 검색 확장은 별도 설계로 남기고 새 ingestion은 OM-21의 PLAN ONLY 준수.
- **수용/예방 gate:** canon/claim/assistant/request를 분리한 사실 질문·없는 사실·정정·곡 예외·다른 작품 대조군 유지. fixture pass를 의미 정확성 전체로 확대하지 않는다.

### OM-05 — 실제 Claude 프롬프트 저작과 전달 증거
- **요구/출처·상태:** PLAN K.1, 사용자의 실제 모델 문맥/프롬프트 확인. **완료 — 저장된 Claude 표본과 fake fal 전달 범위**.
- **근거/빌드:** C1 독립 보고서 L42–51: Messages14개 output/usage 연결, 실제 작성 prompt2개가 저장 action→선택 Kling2.5turbo fake payload와 동일. 14개는 이력이며 진행 중 motion 호출 수가 포함되지 않는다.
- **공백·원인·영향:** 원 입력 전체 재해시는6/14만 가능;8개는 thinking redaction 전 hash와 공개 저장본문의 차이. 이는 확인된 recorder 정책이며 변조 증거가 아니다. 원곡/approval 의미 오류는 후속2질문에서만 재확인했으므로 전체 언어품질 통과 아님.
- **조치/담당:** 증거 담당은 추후 recorder에 공개본문 hash/byte/redaction 종류를 별도 기록하는 작은 개선안을 검토. private reasoning 저장을 요구하지 않는다.
- **수용/예방 gate:** original recorded hash와 sanitized artifact hash를 혼동하지 않고, authored text/검증/payload/실영상 품질을 별도 판정한다.

### OM-06 — CC01 기존 요청 문맥 보존
- **요구/출처·상태:** 사용자의 이어가기·원 요청 유지, 07 MS-FR-11/AT18; PLAN K.1. **완료**, 확인된 결함 수리.
- **근거/빌드:** C1 원9턴 밖 요청 누락 반례→독립 PASS. project별 모든 접수 요청을 rowid 순서의 immutable `session_request_history`로 보존하며 최근8개 대화와 분리.
- **공백·원인·영향:** 원인은 과거 최근8개 완료 대화만 보낸 구현. 현재 bounded context이며 무한 기억/자동 요약은 아니다. 새 반례 없이 재개하지 않는다.
- **조치/담당:** 기능 담당은 기존 원 반례·Store reopen·취소 상태·assistant 비승격·project 격리를 회귀 유지.
- **수용/예방 gate:** 모델 input까지 원 요청/순서/해시가 남는지 검사. DB에만 존재함을 모델 전달 성공으로 대체하지 않음. 독립 세션은 OM-08로 분리.

### OM-07 — CC02 입력 크기 거절·unknown 복구
- **요구/출처·상태:** bounded input, 비용·복구 무결성; PLAN K.1 CC02. **완료**, 확인된 결함 수리.
- **근거/빌드:** C2 독립 원 반례+6 guard PASS. 동일65,529/65,549byte 입력에서 count0/Messages0, blocked_before_message, 예약0, 후속 명시 요청 접수 가능. runtime/transport 해시는 감사 시에도 C2와 같았다.
- **공백·원인·영향:** 원인은 count와 최종 Messages의 envelope 차이를 송신 전 동일 serializer로 검사하지 않은 것. 실제 timeout은 여전히 unknown/예약 유지. 이력 삭제나 상한 완화로 해결한 것이 아니다.
- **조치/담당:** 원 반례·정확 상한·1byte 초과·다른 예약·후속 round 비용 보존을 유지. 새 한계 UI의 사용자 이해 전체는 별도 coverage다.
- **수용/예방 gate:** preflight와 실제 POST가 동일 직렬화를 사용; known-not-sent와 unknown-after-send를 구분. 과거 unknown 원장을 일괄 해제하지 않음.

### OM-08 — 같은 작품의 독립 대화 세션
- **요구/출처·상태:** 부모의 이번 점검 요구 및 PLAN K.1 L217/227의 별도 잔여. **미검증**, 알려진 미지원 범위/다음 계획 공백.
- **근거/빌드:** 현재 history scope는 workspace/project/`project-default`; C1 독립 L40은 별도 session ID/UI가 없음을 확인. 07 자체는 공급자 세션을 canon 저장소로 쓰지 말라고 요구하며, 그것만으로 다중 독립 세션 구현을 요구했다고 확대하지 않는다.
- **공백·원인·영향:** CC01에서 새 session UI/DB migration을 의도적으로 제외했다. 다만 후속 세션 요구의 실행 범위·수용기준·종료 조건은 아직 연결되지 않았다. 다른 프로젝트 격리가 같은 프로젝트의 세션 격리를 증명하지 않는다.
- **조치/담당:** 부모/기능 담당이 독립 세션의 생성·선택·이력·canon 공유 범위를 별도 계획에 명시. 이번 감사가 임의 구현/자동 세션 분리를 정하지 않음.
- **수용/예방 gate:** 동일 project의 A/B 대화와 모델 교체, 재개, pending/unknown 귀속 대조군. CC01 완료 표에 이 기능을 섞지 않는다.

### OM-09 — native motion 저작·렌더·수정·복원
- **현행 상태:** 기존 실제 Claude 모션 저작·12프레임 수정·로컬 렌더·복원 실행 증거는 유지한다. NM-Q01 후속은 현재 작품/샷/버전에 바인딩된 저장 승인 주체·범위·scene hash를 읽기 문맥에 제공하고 새 미승인 제안과 구분했다. 승인 생성·실행 로직 변경은 없다.
- **추가 검증:** 무승인/타작품/오래된 context·revision·scene/가짜·이전 grant/AI 승인 인수 주입은 회귀로 차단했다. 전체403/403, 새10개는 포함 수치다. [수정 전 두 반례](native-motion-20261026/quality-fix/before-counterexamples.log), [최종 검증](native-motion-20261026/quality-fix/final-full-regression.log).
- **실제 답변 판정:** 기존v1 승인 범위와 새 제안 미승인은 실제Claude가 구분했다. 모션 적용과 타임라인 채택의 혼동은 마지막1응답에서 명확해졌으나, ontology/snapshot 공백을 현재 context 일치 불명의 근거로 드는 문장은 남는다. **핵심 개선 확인·설명 근거 일부 잔여**, 전체 문장 품질 통과로 닫지 않는다. 마지막 시험은 서버가 실제 조회한 영수증의 설명이며 새 model-selected tool loop는 아니다. [판정](native-motion-20261026/quality-fix/quality-evaluation.json).
- **원장·제한:** 앞선9응답과 별도 stage에 추가6응답/$0.0061185, 누적$0.0381186. 보수원장$0.038135/열린예약0, 실청구미확인. 응답상한6 사용 후 종료, fal0/새영상렌더0/자동retry0. [출처](native-motion-20261026/quality-fix/live-provenance.json). 원래 source/MP4/스크린샷/backup 증거는 보존했다.

<details>
<summary>이전17:32 진단 시점의 상태·조치 이력</summary>

- **요구/출처·상태:** 사용자 Claude 직접 저작 요구, PLAN K.4. **차단 — 실제 Claude 시험**. 기존 로컬 구현·합성 시험은 보존하며 전체 기능 실패 또는 완료로 판정하지 않는다.
- **근거/빌드:** WIP 소스와 [m1-tests.log](native-motion-20261026/m1-tests.log)6개 PASS는 기존 근거다. D1이 읽은 [trial summary](native-motion-20261026/live/summary.json)는15:51:35 UTC `stopped/AssertionError/blocked_before_message`; [transport](native-motion-20261026/live/case-1/transport.json)는count_calls=1/messages=0/request_bytes=[7336], [turn](native-motion-20261026/live/case-1/turn.json)은count_started/request_id=null/tool_calls=[]다. count_calls는 recorder 진입 횟수이지 HTTP 송신·공급자 수신 증거가 아니다.
- **공백·원인·영향:** 실제 Messages가 없으므로 이번 trial의 Claude 저작·편집·출력 완주 근거가 없다. **송신 전 차단이라는 결과는 확인됐으나 count 단계 원 HTTP/transport/응답 오류가 저장되지 않아 구체 원인은 미확인**이다. 자격증명 오류·공급자 거절·승인 대기로 단정하지 않는다. 별도로17:32 공식 turn은inProgress/error=null, 반환된 마지막 tool은completed다. 세션 정체/메타데이터 지연의 원인도 미확인.
- **조치/담당:** 부모/작업 제어 담당이 D1의 정확한thread/turn만 공식 지원 제어로 확인한다. 실제 종료/취소 성공 전 두 번째 canonical writer나 유료 재시험을 시작하지 않는다. 단일 writer 정상 복귀 후 [격리 count 진단 제안](isolated-count-diagnostics-20261026/REPORT-ko.md)을 base hash와 대조해 검토할 수 있으나, 미적용 patch가 과거 원인을 복구하거나 새 provider 재시도를 허가하지 않는다.
- **수용/예방 gate:** 실행 시도별 마지막 stage·송신 여부·request ID·원인 범주·정리 상태를 비민감 증거로 기록한다. trial/turn/tool 상태를 따로 비교하고 error=null 또는 마지막tool completed만으로 정상 종료를 선언하지 않는다. 이후 실제 모델 저작과 fixture,frame0…95/한글/12frame수정/이전버전·승인 보존을 연결해야 한다. 재개·취소·유료 재시도·거부된 CUA 접근 재시도는 이번 갱신에서0회다.

</details>

### OM-10 — 모델 지시 타임라인 편집
- **현행 상태:** 기존 실제 Claude 컷/자막/음원 편집 및 출력 표본을 유지한다. NM-Q02에서 legacy `changes`의 clip 속성 범위를 명시하고 실제 base/candidate의 occurrence 순서·clip 속성·caption·audio version/offset diff를 서버가 계산해 저장/반환한다.
- **검증:** 실제Claude 추가3응답 tool roundtrip에서0,1,2→2,0,1, 자막교체, 원음offset0→1와 버전1 유지, Take/trim/duration 불변을 정확히 설명했다. saved proposal과applied/output-approved를 구분했다. [실제 답변](native-motion-20261026/quality-fix/live/case-2/turn.json). **NM-Q02 이번 표본 통과**이며 모든모델/모든편집 품질 보장은 아니다.
- **경계:** 순서만/자막만/오디오만/clip+순서/no-op/동명occurrence/중복영수증/보류·거절·stale는 결정적 회귀로 확인했다. 설명문을diff로복사하지 않고 원본timeline/승인/새렌더job을 바꾸지 않는다. [최종403검사](native-motion-20261026/quality-fix/final-full-regression.log).

<details>
<summary>이전17:32 진단 시점의 상태·조치 이력</summary>

- **요구/출처·상태:** PLAN K.5, 기존 직접 편집과 모델 도구 구분. **진행 중 — 단일 writer 상태 확인 및 실제 모델 검증 대기**.
- **근거/빌드:** WIP `local_creation_tools.py:150`의 `propose_timeline_changes`; [e1-tests.log](native-motion-20261026/e1-tests.log)4개 PASS 기록. 기존 Take/trim/duration에 reorder/captions/audio-offset을 더하는 중이다.
- **공백·원인·영향:** 실제 Claude 명령→정확한 diff→사람 apply→출력·복원·재개가 최종 확정되지 않음. D1의case-1 송신 전 차단을 이 편집 기능 자체의 결함으로 전이하지 않는다.17:32 같은 구현turn이inProgress인 원인은 미확인이다. 직접 UI 또는 backend4 PASS는 실제 모델·화면 완주 증거가 아니다.
- **조치/담당:** OM-09의 공식 실행 상태 확인을 먼저 따르고, 단일 기능 담당이 정상 복귀한 후 E1의3→1→2/cue/원음 시작1초를 검증. caption은 절대 timeline 시각, audio offset은 원곡 시작 지점이라는 의미를 유지. 다른 writer의 동시 편집/새 유료 시도로 이어가지 않는다.
- **수용/예방 gate:** occurrence index/base version, hold/reject/stale/foreign/중복, 승인 무효화, 이전 출력 불변, decoded 순서·cue·오디오 측정을 같은 빌드로 연결. 시험case별 not-started/blocked/completed를 구분하고 선행case 중단을 뒤case의 실패·성공으로 추정하지 않는다.

</details>

### OM-11 — 새 모션/편집의 실제 사용자 화면
- **현행 상태:** 앞선 실제Chrome149.0.7827.55, 격리synthetic DB/media,1920×1080주/1280×900보조/DPR1의 UI 증거를 유지한다. 이번 품질 수정은 Python문맥·영수증·SYSTEM만이며 **HTML/CSS/JS byte불변**, 새브라우저/캡처는0이다.
- **근거:** [앞선 UI 수용표](native-motion-20261026/browser-followup/acceptance.json), [1920화면](native-motion-20261026/browser-followup/motion-final-1920.jpg), [1280화면](native-motion-20261026/browser-followup/motion-preview-1280.jpg), [현재 source 비교](native-motion-20261026/QUALITY-MANIFEST.json). 새 실제Claude답변은 서버시험 실행기에서 검증했으며 새브라우저UI답변검증이라고하지않는다.
- **한계·정리:** 이전 unknown/refresh-failure는Node통제시험,screenreader/실제zoom/다른브라우저/mobile미실행 그대로다. 기존Codex앱거절재시도0. 이번live/회귀process종료,canonicalDB변경0,HTTPsuite임시서버정리. 이전미디어·스크린샷·backuphash불변.

<details>
<summary>이전17:32 진단 시점의 상태·조치 이력</summary>

- **요구/출처·상태:** U2의 실제 rendered 결과·사용자 과업 검증, PLAN K.4 L454/K.5. **미검증**, 진행 중 빌드의 검증 대기.
- **근거/빌드:** WIP HTML은 E8과 다르며 `AethonMotion.refresh` 연결이 생겼다. E8 screenshot은 이전 HTML의 증거다. 이번에는 브라우저를 열지 않았다.
- **공백·원인·영향:** 새 proposal/레이어 수정/frame preview/허용·실패·restore/keyboard가 사용자 화면에서 완료됐는지 미확인. D1에서 `cua.getApp("Codex")`는 **“Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.”**로 거부됐고 화면/접근성 트리를 받지 못했다. 이는 Codex 앱의 대기 화면을 확인하지 못했다는 뜻이며 Aethon 웹 UI 자체의 결함·접근 차단 증거가 아니다. 승인 창이나 숨은 오류가 있다고 추정하지 않는다.
- **조치/담당:** 거부된 앱 접근은 재시도/우회하지 않는다. 공식 작업 상태가 정리되고 기능 담당 freeze가 제공된 후 화면 검토 담당이 허용된 별도 검증 경로에서1920 주/1280 보조의 영향 상태만 확인. 계획된 컨트롤이 없으면 backend와 별도 항목으로 남김.
- **수용/예방 gate:** 지원되는 상태 metadata와 실제 본 화면을 구분하고, 새 화면 증거 없이 오래된 캡처를 최신으로 재표기하지 않는다. served/source hash, fixture/frame, 실제 승인 범위와mock, dirty/error입력, focus/복귀·재개를 각각 기록. code test와 UI proof에 각각 체크 필요.

</details>

### OM-12 — 승인·비용·권리·중복·복구 계약
- **요구/출처·상태:** 07 MS-FR-05/06/13–20/24/26. **완료 — 로컬/fake 계약 및 C1/C2 표본 범위**.
- **근거/빌드:** E8 격리 UI 계획→허용→후보→Take 검토/선택→timeline 승인→3초1080p음악/자막→납품 검토/reload. C1 wrong grant/duplicate same job, C2 known/unknown 예약 유지 독립 확인.
- **공백·원인·영향:** live invoice, 모든 늦은 공급자 완료, 조직 권한 전체는 입증되지 않음(OM-03/23). scoped approval≠final-output approval, 선택≠검토 승인을 유지해야 한다.
- **조치/담당:** 새 motion/tool도 기존 서버 guard와 immutable snapshot을 재사용. 권한·가격·권리검사를 디자인 때문에 숨기거나 약화하지 않음.
- **수용/예방 gate:** 변경 입력/base revision/rights/가격/expiry에 오래된 grant 차단; unknown 재제출0; 이전 결과/원곡 보존. 현재 승인 완료 화면에 불필요한 강한 CTA를 요구하지 않는다.

### OM-13 — 1920 작업대와1280 회귀
- **요구/출처·상태:** 사용자1920 우선/no-page-scroll 요구; PLAN B/H. **완료 — E8 대표8상태 범위**.
- **근거/빌드:** E8 selected/sequence×기본/정밀×두viewport, document1080/900. 헤더 배치 개선 및 native controls/타임라인 보존. E8은320×180 합성 패턴을 사용하며 창작 품질 점수 아님.
- **공백·원인·영향:** 현재 WIP UI는 OM-11 대상. CSS 같음만으로 새 DOM의 geometry를 증명하지 않는다.
- **조치/담당:** 새로운 영향 영역만 matched capture. 기존 header/token/draft를 다시 설계하지 않음.
- **수용/예방 gate:**1920×1080 CSS viewport primary/1280×900 secondary, 확대 예외 reflow·내부 scroll 허용, font/DPR/frame/selection/열린details 기록. overflow로 감춘 것을 통과로 세지 않음.

### OM-14 — 실제 확대·접근성·키보드 coverage
- **요구/출처·상태:** 사용자 상세 frontend QA, U2, PLAN DP26-09. **미검증 — 남은 환경/상태 범위**.
- **근거/빌드:** E8 native description Enter, comparison Escape focus,1280/app200% Take3 노출 표본 PASS. 실제 browser200/400%, native IME, screenreader, axe, cross-engine, forced-colors 전체·모든 keyboard 경로는 E8에서 not-run.
- **공백·원인·영향:** 지원 도구/환경과 실행 범위 제한. 실제 실패를 재현한 것이 아니다. 과거 닫힌 VF01/02를 다시 열지 않는다.
- **조치/담당:** QA 담당이 현재 허용 도구에서 가능한 항목만 실행하거나 정확한 BLOCKED/NOT RUN 사유를 유지. 임의 설치/외부 script 주입 금지.
- **수용/예방 gate:** app scale/viewport/DPR와 실제 zoom 분리; AA최소 focus 기준과 제품 전체가시 목표 분리; 자동 scan을 WCAG 인증으로 부르지 않음.

### OM-15 — 모바일 추가 개선
- **요구/출처·상태:** 사용자 명시 “모바일은 나중에”, PLAN B/H. **명시적 계획만**, 의도적 순서 보류.
- **근거/빌드:** PLAN L58/74의1920 주·1280 보조, 모바일 새 작업 보류; 과거390 evidence는 당시 빌드 기록이다.
- **공백·원인·영향:** 이번 최신 모바일 전수 QA가 없다는 것은 누락 결함이 아니다. 현재 변경에서 기존 mobile 기능을 무심코 손상하면 별도 회귀다.
- **조치/담당:** 기존 responsive 계약 보존. 새 모바일 설계/전수검증은 부모가 후속 범위를 열 때 계획.
- **수용/예방 gate:** 모바일 deferred를 final report에 표시하고 generic workflow의 모바일 문구로 현재 우선순위를 덮어쓰지 않는다.

### OM-16 — 디자인 참조·스킬 적용과 점수 정직성
- **요구/출처·상태:** 사용자 Refero/Hallmark/Impeccable 요청, U2. **완료 — 설치 확인·문서/수동 적용·기록된 과거 명령 범위**.
- **근거/빌드:** [reference lock](design-system-redesign-20261026/REFERENCE-LOCK.md), PLAN I. Hallmark2.0.0 개인 `.agents` 파일, Impeccable4.7.1 개인 `.codex` 파일을 이전 독립 턴에서 실제 읽음. Hallmark sloplint 정적 실행은 구현팀 역사적 기록; Impeccable context probe exit127 후 수동 fallback. 이번 새 command0.
- **공백·원인·영향:** full rendered Hallmark/Impeccable critique/detector 실행이나 경쟁사 동일조건 점수는 없다. 참조캡처/공식tutorial과 직접 editor 접근을 구분한다. 81은 역사적 혼합 rubric이며 이번 점수 아님.
- **조치/담당:** 디자인 담당은 사용한 지침→실제 판단을 연결하고 마케팅 hero/강제clip/새팔레트/자동점수는 제외.
- **수용/예방 gate:** read/manual/command/result/blocked를 따로 기록. 설치됨=실행됨=통과라는 등식 금지; 가설인 비교버튼/경계/아이콘을 무조건 수정하지 않음.

### OM-17 — REA 사용과 공개 소스 분석
- **요구/출처·상태:** 사용자 REA/Codex 활용 확인. **차단 — REA 실행**, 등록/정적 연구는 완료 기록.
- **근거/빌드:** [라우팅 확인](independent-rea-routing-discovery-20261026/REPORT-ko.md) L5–14: rea enabled/stdio, 설치6.7.0. [공개 Remotion 조사](independent-remotion-public-architecture-20261026/REPORT-ko.md) L5–13: v4.0.538/commit5217b0c…69896,17공개파일 해시 확인; REA 실행은 프로세스 생성 전 자동심사 거절.
- **공백·원인·영향:** 실효 provider/base endpoint·수신자를 확정하지 못한 것이 기록된 거절 이유. handshake/tool call/Evidence ID 없음. GitHub 정적 해석을 REA 실행 결과로 표시하면 부정확하다.
- **조치/담당:** 도구 소유자/부모가 허용된 범위에서 실제 수신자·전송 승인을 해결할 때만 지원 경로 재개. 이번 재시도/직접CLI우회0.
- **수용/예방 gate:** registered/reachable/executed/result를 분리. source_paths는 전체 inventory 범위 제한이 아님. 새 계정/설치나 private-source 전송을 자동 추가하지 않는다.

### OM-18 — 계획 우선·단일 writer·보존·시험 무결성
- **요구/출처·상태:** U1/U2, PLAN A–J/K.4/K.5. **진행 중 — 현재 체크포인트 인계까지**.
- **근거/빌드:** PLAN은 관찰/가설/대안/수용/stop/rollback을 포함; E8/C1/C2에 snapshot·반례·대조군·종료 기록. CC02 원 독립 반례는 같은 크기로 재실행됐다. 현 디렉터리는 git repository가 아니라 해시 보존을 사용했다는 기록이 있다.
- **공백·원인·영향:** 현재 WIP 전체 diff/시험 assertion/원본 보존/최종 독립검토를 아직 감사하지 않았다. 로그 PASS만으로 “테스트를 약화하지 않았다” 전체 증명은 안 된다. 위반을 재현한 것은 아니다.
- **조치/담당:** 단일 writer가 freeze 시 baseline→final 변경목록·대상 tests diff·현재 전체 suite·독립 재검증을 연결. 현재 감사는 제품을 쓰지 않음.
- **수용/예방 gate:** source mismatch/다른 writer/unknown 작업/도구거절에서 해당 행동 중단; reset·덮어쓰기 금지. 원 assertion 변경은 이유와 동등/더 강한 판정 증거 필요. 테스트·JS내부사례 분모 합산 금지.

### OM-19 — 현행 문서 입구와 진행 상태
- **요구/출처·상태:** U2/U1, PLAN DP26-08. **미검증 — 확인된 문서 연결 공백 포함**.
- **근거/빌드:** README L5는E8/350, PLAN상단L9는C2/365를 연결한다. PLAN L305의‘역사적 계획’ 이후 L414/L458에 **현행** K.4/K.5가 붙어 있다. 문서에는‘구현 없음’ 당시 문구, 현재 소스에는 모션 구현이 존재. 부모가 진행 중임을 별도로 전달했다.
- **공백·원인·영향:** 기록된 사실은 후속 계획이 역사적 구역 뒤에 추가됐고 활성 상태표가 아직 갱신되지 않았다는 것. 사람이 왜 그랬는지는 미확인. 읽는 사람이 진행 중을 미착수 또는 완료로 오해할 수 있다.
- **조치/담당:** primary가 다음 자연스러운 checkpoint에서 상단에 E8/C2/WIP/final 구분, 현재 K4/K5 링크, 이 등록부 링크를 추가. 원 보고서의 당시 결과는 보존. 이 감사는 PLAN/README를 수정하지 않는다.
- **수용/예방 gate:** README→canonical PLAN→현행 manifest→본 등록부가 연결되고 latest/pending 문구와 source 기준이 일치. 새 phase를 history heading 아래 넣을 때 명시적으로 구역을 닫는다.

### OM-20 — 산출물 등록·실제 전달
- **요구/출처·상태:** 사용자 현재 화면/상세문서 요청, U2 handoff. **차단 — 최신 Library 전달**.
- **근거/빌드:** [역사적 Library manifest](design-benchmark-20261025/creator-integrated-review/library-manifest.json)는 확인된 이전 screenshot IDs를 보존한다. 이전 요약/방법론 identity는 부모가 `libfile_602cae4d172481919c1100482a16f9f1` / `libfile_ed743f25319881918ecddf58fa431d2d`로 전달했다. 이것들은 최신 E8/WIP 파일 등록 증거가 아니다. PLAN I와 E8 REPORT L85는 신규 upload/retry0.
- **공백·원인·영향:** Library helper의 prepare_uploads 사용 불가가 앞선 기록의 정확한 blocker. 새 지원 상태는 이번에 재조회하지 않았다. 현재 E8 이미지/출력/보고서와 본 등록부는 **로컬 파일**, 최신 Library 완료 ID 없음. 부모가 채팅으로 설명했는지와 파일 전달 여부를 구분한다.
- **조치/담당:** 전달 담당은 정상 지원 절차가 복구/승인될 때 기존 문서 identity를 보존해 갱신. 시작된 helper를 direct upload로 바꾸거나 미확인 중복 업로드 금지.
- **수용/예방 gate:** 로컬 생성→등록 확인→version/ID→사용자 전달을 각각 기록. 경로만으로 전달 완료라고 쓰지 않고 private download URL도 제공하지 않는다.

### OM-21 — 이질 입력 수집·온톨로지 자동 진화
- **요구/출처·상태:** 최신 사용자 범위, PLAN K.2/K.3. **명시적 계획만**.
- **근거/빌드:** PLAN L233–299: Source/Fragment/Claim/Entity/ChangeSet,형식별근거·권한·충돌·철회·원자 적용·단계별 형식 계획과 공식 연구 출처. 실제 새 수집 기능 완료 보고서 없음.
- **공백·원인·영향:** 사용자 명시적 계획 제한이므로 미구현은 사고적 누락이 아니다. 계획이 있다는 사실을 parser/OCR/embedding/ontology evolution 지원으로 표현하면 안 됨.
- **조치/담당:** 연구/설계 담당은 채택·제외와 사전 수용 사례를 계획으로 유지. 부모가 구현 범위를 별도로 열기 전 schema migration·설치·실자료수집·canonical 적용0.
- **수용/예방 gate:** PLAN ONLY 태그와 non-goals 유지; 새 사실/출처/추론/승인 구분. 향후 구현 전 source→claim→approved version 추적과 중복/충돌/철회/다른project 대조군을 먼저 고정.

### OM-22 — Blender 모델링·조명·카메라 UX 계획
- **요구/출처·상태:** 부모가 전달한 사용자 PLAN ONLY 요구. **완료 — 문서 상세화 한정. 제품 기능은 명시적 계획만**.
- **근거/빌드:** 2026-10-26 [AI-MODELING-PLAN.md](../design/AI-MODELING-PLAN.md) 작성. 선택형 진입, native Aethon UX, light/camera 조작, SceneSpec·ontology 연결, 명확한 입력과 모호한 의도의 구분, 대안/이유, version·worker·출력 경계, BM-G0/BM-01–10 수용 시나리오를 포함한다. 제품 빌드/실행 결과는 없음.
- **공백·원인·영향:** 최초에는 canonical 문서의 범위표시만 있고 세부 계획 연결이 없었다. 분실/작성누락의 사람 원인은 미확인이라는 기록을 유지한다. 동등 로컬 문서를 먼저 검색한 뒤 하나의 독립 계획으로 보완했다. 2D motion과 Blender 모델화의 완료 상태를 섞지 않는다.
- **조치/담당:** 독립 설계 담당의 문서 작성은 완료. 부모/primary는 canonical PLAN에 이 파일을 연결하고 후속 구현 범위를 설명한다. 이번에는 primary PLAN·제품 코드·Blender 설치/실행을 변경하지 않았다.
- **수용/예방 gate:** 문서의 요구/대안/흐름/schema/모호성/수용/미결정/소유/출처를 확인하고 로컬 링크를 검증한다. commit·Blender build·license·격리 capability를 구현 전 고정해야 한다. 계획 작성 완료를 제품/REA/렌더/live 성공으로 처리하지 않는다.

### OM-23 — 07 전체 요구와 로컬 체크포인트의 종료 범위
- **요구/출처·상태:** U1의 전체 누락 확인,07 MS-FR-01–28/AT01–38. **미검증 — 의도된 단계 범위 밖 요구의 전체 완료 여부**.
- **근거/빌드:** PLAN B L60/J는 전체96FR/143API·12live조합·다중사용자 인프라를 이번 디자인 pass 밖으로 둔다. 07의조직정책/역할, BYOK청구주체,키회전/철회,교차공급자,평가집합자동선택까지 이 pass로 완료됐다는 증거는 없다. README도 local-owner가 조직 인증을 대신하지 않는다고 명시한다.
- **공백·원인·영향:** 현재 checkpoint를 작게 제한한 것은 확인되지만 사용자 전체목표에서 그 요구가 취소됐다는 근거는 없다. 미해결 요구를 범위 밖이라는 말만으로 최종 삭제하면 실제 누락이 된다.
- **조치/담당:** 부모/기능 담당이 기존 요구 추적표에 각07 요구의 완료/미검증/차단/계획 범위·owner·다음 checkpoint를 연결. 이번 native motion에 인증/새provider를 끼워넣지 않음.
- **수용/예방 gate:** ‘이번 묶음 종료’와 ‘프로젝트 전체 완료’를 다른 상태로 표시. 승인된 전체 요구에 terminal 증거가 없으면 전체 완료 선언 금지; 임의 새 품질점수/기능 확장도 금지.

## 최초 WIP 릴리스·체크포인트 확인표 — 역사적 미완료 표

아래는 **최초 WIP 시점의 완료 조건**이며 체크되지 않은 항목은 실패가 아니라 pending/unverified다. 기존 E8/C1/C2 결과를 지우지 않는다.

- [x] 원 사용자 요구·07·183행 workflow 검토 기록과 현재 canonical PLAN을 연결했다.
- [x] CC01/CC02의 원 반례와 독립 닫힘 근거를 보존했다. 새 반례 없이 다시 열지 않는다.
- [x] Aethon 표시와 Loretune 내부 호환 식별자를 구분했다.
- [x] 실제 Claude 저작, fake fal transport, 실제 로컬 encode, live provider 파일수신을 다른 증거층으로 분리했다.
- [x] D1의trial/turn/tool 상태·시각·원인 미확인·CUA 거부를 각각 연결했다. count recorder 진입을 실제 전송으로 계산하지 않았다.
- [ ] 공식 제어로 대상thread/turn의 현재 실행·종료/취소 상태가 확인됐다. 이 확인 전 두 번째 writer·새 유료 시험·중복 재개를 시작하지 않는다.
- [ ] WIP 최종 source/test hash와 source→served hash가 고정됐다. 현재 파일 해시 관측은 final이 아니다.
- [ ] 모션 M0/M1/M2 및 편집 E1 요구별 성공·미완료·차단이 실제 응답/프레임/파일로 연결됐다.
- [ ] backend test와 별도로 신규 visible UI·dirty/error·focus·승인·restore의 완료를 확인했다.
- [ ] 같은 과업/fixture/frame/폰트/DPR/앱배율의1920 전후,1280 보조 증거가 있다. 실제 zoom 미실행을 구별했다.
- [ ] 변경된 tests의 기대값 약화 여부, 원 반례·대조군·영향회귀·전체suite 분모와 독립 검토 범위를 확인했다.
- [ ] 사용자 원본/기존 source 변경/DB·미디어·권리·비용 계약의 보존과 필요한 cleanup이 기록됐다.
- [ ] canonical PLAN/README에 현재 진행·완료·역사적 상태 및 이 등록부 링크가 반영됐다.
- [ ] 최신 산출물의 로컬생성/Library등록/사용자전달 상태가 실제 ID·version으로 구분됐다. Library blocked이면 그대로 남긴다.
- [x] 신규 ingestion/ontology진화·Blender는 PLAN ONLY,모바일 추가작업은 deferred로 보존했다.
- [ ] 남은 전체 요구는 소유자·다음 행동·수용증거가 연결됐다. 제한된 checkpoint 통과를 프로젝트 전체 완료로 표시하지 않는다.

## 상태 전이·다음 갱신

|시점|항목|이전 → 현재|근거/실행 주체|
|---|---|---|---|
|2026-10-26, 기존 완료 이력 등록|OM-01/13|표시명/로컬 UI 검증 → E8 범위 완료|통합팀 E8; 이번에는 보고서/manifest 읽기|
|2026-10-26, 기존 완료 이력 등록|OM-06|CC01 반례 → 완료|C1 수정 및 독립 원 반례 PASS; 이번 재실행0|
|2026-10-26 15:28 보고서 기준|OM-07|CC02 반례 → 완료|C2 독립 원 반례+6guard; 이번 재실행0|
|2026-10-26 16:03:48 관측|OM-09/10|PLAN의 미착수 표기 → 진행 중|부모의 실제 진행 통보+WIP 소스/개별 로그. 최종성공 아님|
|2026-10-26, 본 등록부|OM-19/22|문서 상태/계획 연결 미추적 → 공백 등록|현행 PLAN 구역/링크·로컬 문서 검색. 사람의 원인은 미확인|
|2026-10-26, 본 등록부|OM-20|이전 전달과 새 로컬 산출물 혼재 → 전달 차단 분리|역사적 Library IDs, 현재 upload0 기록. 새 호출/재시도0|
|2026-10-26, 문서 후속 요청|OM-22|계획 상세화 공백 → **문서 완료 / 제품 PLAN ONLY**|독립 설계 담당의 [단일 모델화 계획](../design/AI-MODELING-PLAN.md). 기존 동등 문서 검색·문서 링크/항목 검사만. 제품/PLAN 수정·설치·Blender/REA 실행·업로드0|
|2026-10-26 17:32 공식 진단 반영|OM-09|진행 중의 live 시험 → **차단:15:51:35 blocked_before_message/Messages0**|D1 보고서·evidence·trial artifacts hash 대조. count 원인과inProgress 지속 원인은 미확인;새실행0|
|2026-10-26 17:32 공식 진단 반영|OM-10/11|진행 중/미검증 유지 + 단일writer 상태 확인 선행|공식turn inProgress/error=null/마지막tool completed. Codex CUA 안전 제한 거부로 화면 미확인;편집기 결함으로 전이하지 않음|

다음 갱신은 지원되는 공식 제어에서 대상thread/turn의 상태가 확정되거나, primary의 native motion/model-edit 최종 보고서와 manifest를 받은 시점이다. 실행 복구와 trial count 원인은 별도 항목으로 확인하며, 오래된tool completed·error=null만으로 재개/중복 실행을 허용하지 않는다. 본 등록부 owner는 새 증거를 확인한 후 해당 행과 전이 이력만 갱신한다. 새로운 보고서/점수체계/무제한 QA 반복을 추가하지 않는다. 원인을 확인하지 못한 항목을 임의 사유로 닫지 않는다.

최초 감사는 읽기 전용 문서·선별 소스·저장 로그 확인과 본 MD 작성만 수행했다. 후속 OM-22 요청에서는 위에 연결한 독립 계획 문서와 이 등록부의 해당 상태만 추가했다. 두 작업 모두 브라우저/서버/provider/REA/CLI inference/업로드/설치/비밀파일/공유DB 접근0, 제품·primary PLAN 변경0이다. 실제 사용자시험·현재 UI 성능·교차브라우저·실청구·현재 live 시험 완료는 확인하지 않았다.

17:32 진단 반영 작업도 이 등록부만 수정했다. D1 보고서/evidence/manifest 및 지정trial artifacts를 읽었으며, 공식thread 조회·CUA 접근·재시도·취소·재개·provider 호출·소스 patch 적용은 수행하지 않았다. 원래 다른20개 OM 항목 본문은 보존 검사를 거쳤다.


## 최종 문서 대조 전이와 남은 gate — 2026-10-26

|항목|이전 → 현행|근거·수행 주체|
|---|---|---|
|OM-09/10/11|17:32 차단·18:36 실행/UI·19:07 설명 품질 후속 → 19:35 표시 계약 및 최종 독립 검사 반영|M1/Q1/R1은 primary 실행, R2는 독립 감사10검사/저장pixels. 본 담당은 문서/해시 대조만.|
|NM-Q01/OM-18|최종 독립 감사 대기 → 서버 사실 표시 계약 닫힘/유한 체크포인트 인계 완료|R2 10/10, source/승인 경로 보존. 원문 설명 오류·실제zoom 등 범위 제한 유지.|
|OM-08|미검증으로 묶였던 미지원 → 미구현 명시|현재 chat_runtime project-default/입력 song,prompt와 PLAN K1. 독립 세션 세부계약은 먼저 확인.|
|OM-19|과거 PLAN/WIP 입구 혼선 → PLAN 갱신 확인, README 최신pointer 잔여로 축소|PLAN은410/RECEIPT, README L5는403/QUALITY. 이 등록부의 현재/역사 구분은 이번 문서에서 정리.|
|OM-23|전체 요구 추적 미확인 → 원본/두사본hash일치, 최신coverage 연결 잔여 확인|원본 SHA962f1526…c93378,28FR/38AT. 현행 증거를 과거 not-implemented 문구와 혼동하지 않음.|
|OM-16/20/21/22|기존 한계 유지|디자인90 미입증/현재수치 없음, Library blocked, 신규 ingestion/Blender 계획 전용.|

- [x] 원본07·23개 요구·현재 PLAN·최종 manifest를 연결하고 현재 상태/역사적 시험을 구별했다.
- [x] R1 소스28개+추가test2개의 실제 파일 해시30/30 일치를 확인했다. 410은 구현팀 결과,10은 독립 감사 결과로 분리했다.
- [x] 실제 Claude15(9+6), fake fal, 실제 로컬 렌더, 서버 사실 표시, raw 설명 한계를 분리했다. CC01의14응답은 별도 이력이다.
- [x] 최종 독립 감사와 원본/DB·승인경로 불변, 격리 실행·cleanup을 연결했다. 거부된 Codex 화면 접근을 재시도하지 않았다.
- [x] 23개 요구마다 남은 행동/의존성/수용조건을 REMAINING-WORK에 연결했다. 완료7을 전체 완료율로 계산하지 않는다.
- [x] README 최신 안내와 [07의38AT 현행 MD 추적](SPEC-MS-001-ACCEPTANCE-TRACE.md)에 최종 증거를 연결했다(RW-01/03). 등록 JSON/원본은 그대로이며 과거 결과를 소급 성공으로 덮어쓰지 않았다.
- [ ] 독립 세션 범위·대안·회귀계약을 먼저 고정한 뒤 단일 writer가 구현한다(RW-02).
- [ ] 현행 디자인90 및 확대/보조기술 범위에 검증되지 않은 성공을 부여하지 않는다(RW-05).
- [ ] 일반 live/실제 수신·12조합·실청구, REA, Library는 지원/승인/실제 결과가 있을 때만 닫는다(RW-06/07).
- [x] 모바일 추가 작업 보류, ingestion/ontology진화·Blender PLAN ONLY를 유지한다.

재발 방지: 요구→현행코드/증거→잔여의 원인→대안/계획→수용→단일 구현→같은조건 검증→전달 gate를 지킨다. 작업 정체 시 마지막 파일/시험/공식 상태의 시각과 알려진 송신 여부를 먼저 기록하며, 종료/취소 확인 없이 두 번째 writer·중복 유료 시험·blind retry를 시작하지 않는다. 과거 D1의 원인 미확인은 이후 성공으로 소급 확정하지 않는다.

이번 갱신은 본 등록부와 REMAINING-WORK 두 Markdown만 작성했다. 제품·canonical PLAN/README·등록 모듈·DB·서버 변경0, API/브라우저/업로드/설치/비밀 열람0이다. 최신 사용자 산출물의 Library 전달은 여전히 blocked이며 로컬 경로만으로 전달 완료라고 하지 않는다.


### 문서 연결 잔여 종료 기록 — 2026-10-26 후속 명시 승인

|항목|이전 → 현행|완료 근거/남은 범위|
|---|---|---|
|OM-19/RW-01|최신pointer 미반영 → **문서 완료**|README 최신410/RECEIPT/R2독립10, 과거403/393 분리, 현재추적/등록부/잔여표 링크 검증.|
|OM-23/RW-03|38AT 최신증거 미연결 → **문서 하위작업 완료**|SPEC-MS-001-ACCEPTANCE-TRACE.md의38원문행/28FR·현행구현·시험로그·live한계. **OM23 전체제품수용은 증거제한 유지**.|
|OM-08/16/03/17/20|상태 유지|독립 세션은 제품 미구현/별도계획 작성 중; 디자인90 미입증; 일반live/REA/Library 차단을 문서 작성으로 닫지 않음.|

수정 파일은 README.md, docs/qa/SPEC-MS-001-ACCEPTANCE-TRACE.md(신규), REMAINING-WORK.md, 본 등록부다. 원래23개 상세 본문·실패/성공 이력과 원요구서는 보존했다. primary의 CHAT-SESSION-PLAN.md/제품코드/DB/서버/API/Library는 조작하지 않았다. 링크/해시 검사는 문서 검증이며 제품 테스트 재실행이 아니다.
