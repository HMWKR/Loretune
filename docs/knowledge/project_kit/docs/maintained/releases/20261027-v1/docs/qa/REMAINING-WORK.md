# Aethon — 남은 요구와 완료 증거 대조

## 2026-10-27 후속 재확인

아래 문서 채택 당시의 REA 차단과 구현 미재개는 역사적 상태다. 현 세션에서 REA MCP 공개 웹 관측과 설치 Blender 바이너리 요약은 성공했으나, Blender 기능 분석·플랫폼 3D 구현과 Library 전달은 별도 미완료다. 복수 대화·직접 텍스트 모션 등 일부 기능이 재개됐다. 최신 근거와 남은 항목은 [후속 검증·누락 점검](codex-workflow-review-20261027/REPORT-ko.md), [Blender 재시도](../design/AI-MODELING-PLAN.md)를 따른다. 기존 원본 표와 과거 결과는 이 기록으로 소급 변경하지 않는다.

## 현재 남은 작업 · 2026-10-27

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** [AD01–AD07](../design/AETHONSAAS-ADOPTION-PROPOSAL.md) 전체 문서채택과 [개인 기본·협업 선택/피벗 보충](../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md)을 반영했다. 이번 문서변경을 제품완료로 계산하지 않는다. 23원요구의 현재상태는 [누락등록부 상단](OMISSION-REGISTER.md)을 따른다. 아래410분류표는 역사로 보존한다.

|종류|현재 근거|남은 행동·의존성·수용|
|---|---|---|
|마지막 검증 릴리스|[R416 manifest](chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json),20:48:43UTC.416전체/18관련은한실행과부분집합|CQ-R01 독립최종재확인은 별도. 관련표시결함을 새미구현으로 반복하지 않음|
|RW-02 / OM08 현재partial|[세션계획](../design/CHAT-SESSION-PLAN.md),baseline+before. 신규chat_sessions+5Python변경,기존실행기18인계만|재개지시후primary가diff검토·원본07모델변경UX정합→CS01–18·개인P04–P07검증. 새UI/전체실행은미완료|
|P1 / AD01·02·06|채택된입력·세션·상태설계,기존reference/context/receipt기반|개인팀가입없이완주,자료role/revision/제외동일해석,대화격리·병행예산·복구. G4미개시|
|P2 / AD04·05 개인|정확버전에서새초안,자기검토선택→변경안설계|AD01/02/06기반후P08–P10. 팀AD03불필요. 원본/승인/trim/음원/자막보존|
|P3 / AD03 선택적팀|방향채택,실제인증/역할/서버ACL/bytes경계미구현|구체공유범위/철회/권한정책결정후T01–T06. 이의존성으로개인제작을차단하지않음|
|P4 / AD04·05 팀변형|방향채택,AD03권한기반의존|다른actor새초안/비용/승인,선택댓글개정·원버전연결, T07–T09|
|AD07 / RW01·03 문서|D01–D12정합화·원본보충/38AT·상태추적 완료|이번문서공백만닫힘. 단계별구현/회귀/독립/전달증거연결은계속 필요|
|RW05 / 디자인·접근성|기존화면·후속무총점QA;90미입증,현재partial새화면없음|1920주/1280보조의영향과업matched검증. actualzoom/스크린리더·실사용자미실시보존. 모바일추가보류|
|RW06 / live·원본07운영|실제Claude제한표본과fake fal/로컬encode구별. 실제12조합·실청구·일반팀인증미검증|명세의해당조건유지. 별도허용연결/자료/가격/예산·실제증거필요, 이번실행0|
|RW07 / 도구·전달|REA실행거절·Library prepare_uploads unavailable의기존기록|차단유지. 정상지원복구확인과승인전재시도/우회없음. 이번산출물로컬만|
|OM21/22 계획전용|이질수집/자동ontology·[Blender계획](../design/AI-MODELING-PLAN.md)|AD01채택을parser/학습/worker구현허가로확대금지|

**남은 결정:** 제품재개범위, 응답중모델변경의07/CS08UX차이, 모델별자료capability·선택제외조건, 팀역할/입력공개/철회후접수작업정책, 실제공급자·비용/보존운영조건. 구체내용은 [도입설계 §15](../design/AETHONSAAS-ADOPTION-PROPOSAL.md)에 한 번만 관리한다. 개인기본/협업선택·AD전체채택·기존복수/격리/병행결정은 다시미정으로묻지않는다.

원래상태표를보존한이유는중단구현을없는것으로도완료로도표시하지않기위함이다. 아래‘미구현1/세부정책미확정/최신410’은10월26일판정이며현재판정은위와등록부상단이다. [문서검증·변경목록](adoption-docs-20261027/REPORT-ko.md).

## 2026-10-26 RECEIPT 기준 대조 — 역사적 결과 보존

2026-10-26. 문서 대조 기준: **RECEIPT 동결 19:35:59.264127 UTC**. 로컬 소스 해시 확인: **19:40:34 UTC**. 이 문서는 [누락 등록부](OMISSION-REGISTER.md)의 23개 요구를 현행 증거로 분류한 인계표다. [canonical PLAN](codex-cli-assessment-20261026/PLAN-ko.md)을 대체하지 않는다. 제품 코드·DB·서버·모델 호출·브라우저·Library를 조작하지 않았다. 후속 전달된 [최종 독립 감사](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md)까지 읽어 반영했다. 이 문서 대조가 그 검사를 재실행한 것은 아니다.

## 지금 확정할 수 있는 결과

- 제한된 네이티브 모션 저작·12프레임 수정·승인 후 로컬 렌더·복원, 모델 지시 timeline 편집은 실행 증거가 있다. 모션 후속 **실제 Claude 응답 15개 = 9개 실행 표본 + 6개 설명 품질 후속**이다. 앞선 CC01의14개와 다른 묶음이다. 마지막 서버 승인 표시 변경은 새 Claude/fal 호출0이다.
- 최신 전체 회귀는 구현팀의 **410/410 = 비HTTP390 + HTTP20**, 한 실행이다. 관련19개·receipt7개·Node 하위 시나리오는 중복이므로 더하지 않는다. 이번 문서 검토자가 회귀나 UI를 다시 실행한 결과는 아니다.
- **NM-Q01의 서버 승인 사실 표시와 Claude 자유서술 품질은 별개다.** 현재/과거 승인·미적용 제안·모델 원문을 분리한 UI는 구현팀이 검증했다. 원문에 남은 잘못된 설명은 보존돼 있으며 완전히 없어졌다고 판정하지 않는다. NM-Q02의 편집 차이 설명은 제한된 실제 표본 통과다.
- 같은 작품의 독립 대화 세션은 **미구현**이다. 세 채팅 모델의 등록·선택은 **구현됨**, 세 공급자의 일반 실사용 및12개 실제 미디어 조합은 **미검증/차단**이다. 두 사실을 혼동하지 않는다.
- 디자인 최소90 목표는 달성 증거가 없다(사용자 2026-10-25 `Sentinel_e7b62d30576c8191b6670a0ba512f34d`). [과거81 평가·보존 기록](design-system-redesign-20261026/Loretune-Design-Update-20261026-ko.md)은 `5fcc2cca…fd99b` 시점의 혼합 rubric 결과이고 현행 빌드 점수가 아니다. 이후 세부 QA는 숫자 합계를 내지 않는 기준이므로 새 점수나 동등 환산을 만들지 않는다.
- 최신 산출물의 Library 등록·전달은 **차단** 상태다. 과거 Library ID는 최신 문서/영상이 전달됐다는 증거가 아니다.

분류 합계는 **완료8 / 증거제한8 / 승인된 계획전용3 / 외부차단3 / 미구현1 = 23**이다. 항목의 크기와 범위가 달라 완료율로 계산하지 않는다. 미구현1은 **같은 작품 독립 대화 세션(OM-08)**이다. 이전 OM-19 문서 입구 잔여는 아래 후속 정합화로 닫았다. 이 숫자는 제품 전체 미구현 개수가 아니다. 완료도 아래에 적은 제한된 과업의 완료이지 모든 공급자·모든 입력의 완료가 아니다.

## 문서 정합화 후속 — 같은 RECEIPT 빌드, 제품 변경 없음

부모의 명시 요청으로 [README](../../README.md) 최신 안내를410/RECEIPT와 최종 독립 재검증으로 갱신했다. 403/393은 역사적 기록으로 보존했다. [SPEC-MS-001 38개 수용항목 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)는 원문 입력/통과조건38개와28FR, 현행 구현,68개 고유 시험 함수의 저장 `ok` 로그, 실제Claude/합성/live 한계를 연결한다. 기존 등록 coverage/원본07은 수정하거나 통과로 올리지 않았다.

**OM-19/RW-01과 OM-23의 문서 연결 하위 작업/RW-03만 닫았다.** OM-23 전체제품 수용은 여전히 증거제한이다. 세션 계획은 primary가 별도 작성 중이며 이 작업은 해당 파일/제품 소스를 변경하지 않았다. 세션 기능·디자인90·외부차단/계획전용 항목은 유지한다.

## 증거와 버전 경계

|기호|확인한 근거|판정 범위|
|---|---|---|
|R1|[RECEIPT-MANIFEST](native-motion-20261026/RECEIPT-MANIFEST.json), [서버 승인 UI 보고서](native-motion-20261026/server-receipt-ui/REPORT-ko.md)|19:35:59 최신 빌드. source28개+added_tests2개의 현재 파일 해시 **30/30 일치**를 이번 읽기로 확인. 구현팀 served4/4·410회귀·1920/1280 receipt 표본. 새 live0. 최종 독립 감사는 R2로 분리.|
|R2|[최종 독립 재검증](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md), [종료 대조](independent-native-motion-receipt-recheck-20261026/end-check.json)|R1 동결본 대상 격리10/10(기존7+독립2+승인control1), 소스/증거 해시 일치, 저장 화면3장 독립 열람. 새브라우저/API0, 전체410 재실행 아님. NM-Q01 표시 계약 닫힘, 원문 오류 잔여. 보고서를 읽어 반영했으며 본 담당의 직접 실행 아님.|
|Q1|[QUALITY-MANIFEST](native-motion-20261026/QUALITY-MANIFEST.json), [품질 판정](native-motion-20261026/quality-fix/quality-evaluation.json)|19:07:37 동결. 추가 실제6응답·403회귀. 설명 잔여를 명시. 앞선5응답과 최종1응답의 SYSTEM 버전 차이 및 마지막 응답이 서버 조회 결과 설명이라는 한계 보존.|
|M1|[FOLLOWUP-MANIFEST](native-motion-20261026/FOLLOWUP-MANIFEST.json), [모션 결과](native-motion-20261026/REPORT-ko.md), [독립 후속 검증](independent-native-motion-followup-20261026/REPORT-ko.md)|18:36:58 빌드. 실제9응답·393회귀·실제 렌더/수정/편집·Chrome UI. 독립 검토는 이 빌드의 실행/제한/출력 표본을 확인하고 당시 NM-Q01/02를 발견했다. R1 최종 독립 통과로 재표기하지 않음.|
|C1|[CC01 결과](cc01-context-fix-20261026/REPORT-ko.md), [독립 재검증](independent-cc01-fix-recheck-20261026/REPORT-ko.md)|앞선 요청 보존 반례 닫힘, 실제14응답/저작 prompt2개의 fake fal payload 전달. 모션15응답과 분리.|
|C2|[CC02 결과](cc02-preflight-fix-20261026/REPORT-ko.md), [독립 재검증](independent-cc02-recheck-20261026/REPORT-ko.md)|입력 크기 송신 전 거절과 unknown 구분. 원 반례+6 guard, 당시365회귀. 새 반례 없이 재개하지 않음.|
|E8|[이전 UI 결과](codex-cli-assessment-20261026/REPORT-ko.md), [당시 manifest](codex-cli-assessment-20261026/implementation/FINAL-MANIFEST.json)|350회귀·8 workspace 상태·두 폼12조건·3초 로컬 출력의 역사적 증거. R1 전체 화면 전수검증으로 확대하지 않음.|
|U07|[07 원본](../../07_Chat_Directed_Multimodel_Production_Spec.md), [등록 catalog](../knowledge/project_kit/docs/modules/spec-ms-001/20261025/catalog.json), [기존 coverage](../knowledge/project_kit/docs/modules/spec-ms-001/20261025/coverage.json)|원본28 FR/38 AT를 보존. 현재 등록 coverage38개는 모두 not_fully_verified이며 최신 native-motion 링크가 없다. 과거 단계의 미구현을 현행 코드 결함으로 그대로 복사하지 않음.|

R1 주요 현재 해시:

|파일|SHA256|
|---|---|
|index.html|`b8074c24e39d3bc58023af60d9a1327da5806b2b93c326818178684510998739`|
|app.py|`baa5bad0ffd913a200203ea1dab4e1f4bfd8fced6f4472bc644809c241429bc8`|
|production_context.py|`414888c9eab4e870f54addd2bd002f7e98e9f1bfbcaff9e1ca409d0c88b07fec`|
|chat_runtime.py|`d7f13645f19b770535990f7cf649b2cb06318ea6a3ff57dff6bcb496af7795f3`|
|motion-studio.js|`71e8959f23dc14863c63d619b23420b9d199165e5bd28a01901d391cfa37e40e`|
|studio.css|`4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`|
|studio-media.js|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|

전체30파일은 R1의 source/added_tests가 기준이다. R1에 기록된 등록부/보고서 해시는 **그 동결 시점**의 문서 해시다. 이 후속 문서 변경을 제품 소스 drift로 취급하거나 기존 manifest를 소급 고치지 않는다. 임시 UI 서버와 검증 탭은 R1 cleanup에서 종료됐으므로 “지금 실행 중인 화면을 확인했다”는 주장도 하지 않는다.

## 23개 요구 대조표

분류: **완료**=지정 과업에 종료 증거 있음; **증거제한**=일부 구현/시험은 있지만 요구 전체 또는 최신 독립 증거 부족; **승인된 계획전용**=명시 보류·설계 전용; **외부차단**=도구/계정/접근 경계 때문에 현재 완료 불가; **미구현**=현행 코드/문서에서 구체 부재 확인. 계획전용·차단·미검증을 사고적 누락으로 단정하지 않는다.

|ID·요구 출처|현재 분류·현재 증거|남은 행동|의존성·담당|수용 조건|
|---|---|---|---|---|
|OM-01 표시명 / 사용자 Aethon 명명·PLAN DP26-11|**완료.** E8 표시명 검사, 현재 [README](../../README.md) 및 R1 index의 Aethon. 내부 Loretune 경로/키는 호환 보존.|신규 표시에만 같은 이름 유지. 내부 전역 치환 불필요.|단일 통합 담당|보이는 이름과 저장/복구 호환을 별도 검사. 내부 문자열0을 요구하지 않음.|
|OM-02 세 역할·다중 chat 선택 / U07 FR01/03/09/11/27|**증거제한.** 등록/저장/역할 분리는 구현. [model_selection](../../model_selection.py) L7–20/32–53, [chat_models](../../chat_models.py) L7–10, [index](../../index.html) L569–578. 실제 일반 실행은 OM-03.|기존 선택 구현을 재작성하지 말고 최신 fake 계약 증거를 FR/AT에 연결. active와 registered를 구별.|통합·모델 연결 담당; live는 별도 승인/자료|chat 변경 시 image/video·기존job/승인 snapshot 보존. 선택모델과 실제 adapter/model의 일치. 미검증 모델을 자동 활성화하지 않음.|
|OM-03 일반 live·교차 공급자 / U07 FR02/10/24/25/26|**외부차단.** C1/M1/Q1은 승인된 synthetic Claude. catalog live_execution=False, 일반 runtime guard는 synthetic_only/prompt hash/expiry로 제한. OpenAI/Grok/fal 실제 전체 완주 없음.|일반 사용자 연결 UX와 계정/권한/가격·범위 계약부터 현행 요구에 맞게 확인. 실제 계정 시험을 코드 성공으로 대체하지 않음.|연결 소유자·부모; 접근/입력권리/예산·실제 연결 승인|실제 선택→request→승인→파일 수집→Take/출력→usage/청구 경계 증거. 기존403의 현재 원인은 새로 조회하지 않았음.|
|OM-04 canon/context/provenance / U07 FR11/12|**증거제한.** C1 scoped snapshot/출처/프로젝트 격리 완료, Q1/R1 승인 문맥 강화. 실제 검색 index/ranking·대규모 품질은 아님.|현재 snapshot과 계획전용 ingestion을 구별. 최신 상태/출처 시험을 추적표에 연결.|기능·증거 담당; 새 검색 범위는 별도 명세 확인|canon/사용자 요청/모델 설명/제안/실행 사실 분리. 없는 사실 unknown, 곡 예외·다른 작품 대조군.|
|OM-05 실제 Claude 저작·전달 / 사용자 실제 문맥·prompt 요구·PLAN K1|**완료—표본 범위.** C1 실제14응답/저작prompt2개→fake fal payload. M1 모션 저작9응답은 별도 추가 증거.|원 입력 재해시 제한과 raw 설명 오류 유지. 실제 영상 품질로 확대하지 않음.|증거 담당|출력/usage·도구receipt·payload·렌더를 별도 층으로 연결. thinking 제거 전hash와 공개본문hash를 혼동하지 않음.|
|OM-06 CC01 유지 / 원 요청·U07 FR11/AT18|**완료.** C1 원9턴 밖 요청 누락 반례와 독립재개/격리 검사 닫힘. 최신 전체회귀에도 관련 시험 포함(R1 보고).|원 반례 유지; 별도 세션을 CC01 완료에 포함하지 않음.|통합 담당|원문·순서·source hash가 모델 handoff에 남음. DB 존재만으로 전달 성공 판정하지 않음.|
|OM-07 CC02 한도·복구 / 비용·unknown 요구|**완료.** C2 원65529/65549byte 반례, known-not-sent 예약반환/unknown 유지. native schema 증가 후 경계fixture 조정은 M1에 이유 기록.|원 기준·후속round·다른예약 회귀 보존. R2의 기존 실행 gate 보존 범위 연결.|통합·독립 감사 담당|동일serializer/preflight, 자동재제출0, 이력삭제/상한완화로 통과시키지 않음.|
|OM-08 같은 작품 독립 대화 / 부모의 명시 점검 요구·PLAN K1|**미구현.** [chat_runtime](../../chat_runtime.py) L15/47–58/158–174: project별 turn, conversation=project-default, 입력 song/prompt만. C1와 PLAN도 독립session 미지원 명시.|RW-02의 유한 세션 계약을 먼저 설명·고정한 뒤 단일 writer 구현. 다른 작품 격리를 같은 작품 세션 분리로 오인하지 않음.|현재 사용자 의도·최신 세션 명세 확인 필요; 부모/통합 담당|같은 작품 A/B 이력·초안·pending/unknown 귀속, 재개·모델교체, 공유canon/승인 경계 시험. 기존project-default 데이터 보존.|
|OM-09 native motion / PLAN K4·사용자 직접 저작 요구|**완료—Mac 제한 기능.** M1 실제 scene→승인→4초96frame/12frame지연/새버전복원; 독립 followup 표본. Q1/R1은 승인 읽기·표시 보강.|R2에서 승인 표시/기존 실행 gate 보존 확인. rawClaude 설명 무오류·Linux/범용3D는 완료로 확장하지 않음.|raster는 macOS; 범위 확장은 별도|기존 scene/레이어·Take선택·원본 보존, 승인된 범위/미선택 후보/최종납품 구별. 새live 호출 없이 보존 증거 연결.|
|OM-10 모델 timeline 편집 / PLAN K5|**완료—E1 범위.** M1 3→1→2, 한글cue0–1/1–2/2–3, 동일audio v1 offset1, 사람 apply·3초출력·재개. Q1 서버diff/실제 설명 표본.|R2는 Q1의 기존 NM-Q02 결과를 보존함. 새로운 편집 기능/자동적용 추가하지 않음.|통합 담당; 새 기능 없음|제안/적용/출력승인 구분; 이전timeline/Take/trim/duration 보존, 서버before/after를 설명과 비교.|
|OM-11 신규 사용자 화면 / 183행 workflow·PLAN K4/K5|**증거제한.** M1 Chrome UI의 저장/검토/preview/render/restore·draft/focus, R1 현재receipt·과거원문·작품전환/reload 표본.|R2의 저장 화면3장/VM 상태 분리 확인을 연결. 전체 신규UI를 R1에서 재완주했다고 하지 않음.|추가 범위는 안전한 격리 fixture|M1 최종화면과 R1 새화면 빌드 구별. 실제브라우저·Node통제시험·실제Claude 서버시험 구별.|
|OM-12 승인·비용·권리·복구 / U07 FR05/06/13–20/24/26|**증거제한.** E8/C1/C2/M1/Q1/R1의 local/fake·승인된Claude 계약. 새 receipt가 실행권한을 만들지 않음.|live invoice/늦은공급자완료·조직권한 전체는 OM-03/23. 닫힌 guard를 반복 구현하지 않음.|통합·연결 담당|권리/모델/가격/context/expiry 재검사; unknown 재제출0; 선택≠검토≠실행허용≠납품.|
|OM-13 1920/1280 / 사용자 desktop·no-page-scroll|**증거제한.** E8 workspace8상태, M1 모션UI, R1 두viewport receipt와 작업대1080/1080 표본. R1 planning 화면은 세로scroll.|최신 영향화면에 대해서만 기존 기준 연결. planning scroll을 workspace 불합격으로 자동 확대하지 않음.|디자인 QA;1920주/1280보조|동일 과업/상태/frame/DPR/배율. 내부scroll과 확대reflow 보존; 단순overflow 숨김 금지.|
|OM-14 확대·접근성 / 사용자 상세QA|**증거제한.** E8/M1/R1에 일부keyboard/focus/draft 표본. 실제zoom200/400·screenreader·cross-engine 전수 없음.|가능한 항목과 BLOCKED/NOT RUN을 유한 matrix로 유지. 설치/우회0.|지원 도구/환경; QA 담당|app scale≠실제zoom. 자동scan≠인증, focus 제품목표≠AA전체, 미측정≠실패.|
|OM-15 모바일 / 사용자 나중에 지시|**승인된 계획전용.** [PLAN B/H](codex-cli-assessment-20261026/PLAN-ko.md) desktop 우선. 과거390은 당시 증거.|새 모바일 범위를 부모가 열기 전 보존만.|명시적 우선순위 보류|현재완료 주장에 모바일전수 포함하지 않음.|
|OM-16 디자인·스킬·90목표 / Refero/Hallmark/Impeccable·최소90 요구|**증거제한.** [reference lock](design-system-redesign-20261026/REFERENCE-LOCK.md), PLAN I의 실제read/manual/과거command 구분. 역사적81<90, 현재수치 없음.|RW-05: 합의된 순수시각QA에 최신증거 연결. 5축90/7축81/후속무총점matrix를 환산하지 않음.|디자인 담당·부모; 현재 matched visual evidence|기준 변경/점수 부풀리기0. 관찰결함·과업가설·coverage 구별; 경쟁사 동일조건 점수/고객시험 주장0.|
|OM-17 REA / 사용자 도구 활용|**외부차단.** [REA 등록/라우팅](independent-rea-routing-discovery-20261026/REPORT-ko.md), [정적 공개소스 연구](independent-remotion-public-architecture-20261026/REPORT-ko.md). 등록≠실행, inference 전 거절.|수신자/전송 범위와 정상 승인 해결 시만 재개. 이번 우회·retry0.|도구 소유자·안전 승인|handshake/tool/result 증거 없으면 정적연구로만 표시.|
|OM-18 계획·단일writer·보존 / 사용자 workflow·누락예방|**완료—이번 체크포인트.** PLAN의 대안/수용/중단조건, R1 변경목록/cleanup/보존, R2 격리10검사·소스/승인경로 보존. 전체410의 모든 assertion을 독립 재실행했다는 뜻 아님.|R2 종료를 연결. 새 finding 없이 같은 감사 반복/다른 writer·중복유료시험 시작 안 함.|단일 통합+독립 감사|원반례·동등 이상 판정·diff/source hash·테스트분모·원본보존 연결. 기존정체의 원인은 미확인으로 보존.|
|OM-19 현행 문서 입구 / workflow handoff|**완료—문서 연결.** [README](../../README.md) 최신 안내가R1/410·R2독립10으로 연결되고403/393은 역사로 구분됨. [38AT 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)와 본표/등록부도 연결.|문서 잔여 닫힘. 새 제품 완료/검증을 의미하지 않음.|이번 명시 허용으로 문서 담당이 README만 정합화; PLAN/세션계획은 primary 소유|README→PLAN→R1/R2→등록부/현행추적이 연결. 과거보고서/원요구 불변.|
|OM-20 실제 전달 / 사용자 화면·문서·산출 요청|**외부차단.** [과거 Library IDs](design-benchmark-20261025/creator-integrated-review/library-manifest.json), 등록부 OM20의 prepare_uploads unavailable. 최신 R1 업로드0.|정상 Library 기능이 복구되면 같은문서ID update·최종영상/화면등록. 지금은로컬파일임을명시.|전달 담당·지원도구; 재시도 승인/기능 가용성|등록성공ID/version과사용자전달 확인. direct전환·우회URL·중복upload 금지.|
|OM-21 이질입력·ontology진화 / 사용자PLAN ONLY·PLAN K2/K3|**승인된 계획전용.** Source/Fragment/Claim/ChangeSet/승인버전 계획 존재. 신규 parser/OCR/진화 구현 증거 없음.|계획 보존, 별도 실행 범위가 열릴 때만 구현.|명시적 계획 제한|문서완료≠기능완료; 출처/중복/충돌/철회/격리 gate 먼저.|
|OM-22 Blender·조명·카메라 / 사용자PLAN ONLY|**승인된 계획전용.** [AI-MODELING-PLAN](../design/AI-MODELING-PLAN.md) 문서 완료. SceneSpec→trustedworker/nativeUX·모호성·BM수용기준. Blender/REA실행 없음.|구현 전 version/commit/license/worker격리 확인. 이번 모델화 구현0.|명시적 계획 제한|2D모션≠Blender. 직접render≠fal기하보장; 임의Python실행 없음.|
|OM-23 원본07 전체 추적 / U07 FR01–28·AT01–38|**증거제한—전체제품. 문서 추적 연결은 완료.** 원본·두사본hash일치/28FR/38AT를 [현행 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)에 연결. 원본12live조합/조직·BYOK·자동선택은 완료 아님.|문서 연결 RW-03 닫힘. 추적표에 남긴 요구확인·미실시·외부조건을 해당 owner가 처리.|명세·통합 담당; 원본/기존coverage 소급수정 없음|38AT 전체조건과부분시험 분리. local checkpoint≠프로젝트전체완료. 취소근거없는원요구를삭제하지않음.|

## 원본07 추적에서 놓치면 안 되는 경계

19:40:34에 원본과 다음 두 사본을 바이트 해시로 확인했다. 세 파일 모두 SHA256 **`962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`**이며 catalog.source_sha256도 같다.

- [knowledge 등록 사본](../knowledge/project_kit/docs/modules/spec-ms-001/20261025/07_Chat_Directed_Multimodel_Production_Spec.md)
- [specification 등록 사본](../specification/IP_Music_Video_Platform/project_kit/docs/modules/spec-ms-001/20261025/07_Chat_Directed_Multimodel_Production_Spec.md)

원문 분실이나 두 사본 충돌은 확인되지 않았다. 처음 대조에서 확인한 **현행 구현/실행 증거와 원문의 연결 공백**은 이번 [38AT 추적표](SPEC-MS-001-ACCEPTANCE-TRACE.md)로 닫았다. 기존 등록 coverage는 그 시점의 부분검증 기록이며 새 표가 현재 근거 부록이다. [2026-10-25 독립 추적표](independent-contract-audit-20261025/ms-requirement-test-evidence.json)의 “이미지 adapter 없음/도구 미연결” 등 당시 판정을 현행 미구현으로 재사용하지 않는다. 반대로 등록 coverage의 local_subset passed를 원문의 전체 AT pass로 올리지 않는다.

|07 요구 묶음—28개 전부 연결|현재 확인과 잔여 범위|다음 추적 수용|
|---|---|---|
|FR01/03/09/11 — 선택·등록단계·고정·인계|3chat/2image/2video 등록 및 역할별 저장, frozen snapshot·현재승인projection 존재. 다중chat **선택**은 있음. 실공급자교체/작업계속은별도.|AT01/02/05/06/15/16/18/19별 config/fake/live구분. 실제모델ID·현재상태 공개, silentfallback0.|
|FR02/07/26/27 — tools·검증·감사·protocol|Claude실제왕복,3provider contract/fake,strict인수·receipt검증. 실제모든stream/시각입력/제공자연결의완료아님.|도구결과후속응답·형식거절·미지원입력·실행추적을각각기록. 정적adapter존재≠모든live형식지원.|
|FR04/05/10/22/23 — 정책·실제주체·연결·BYOK·철회|우선순위/forbidden helper·local-owner/scopedguard는존재. 일반조직/RBAC/BYOK/키교체전체는범위밖또는미검증.|일반운영요구를원본에서확인하고명시checkpoint/owner결정. 계정·비밀조회나인증인프라를이번모션작업에임의추가하지않음.|
|FR06/14/15/16/18/19/20/21 — 허용·비동기·중복·unknown·예산·대체·취소·종료|로컬/fake/Claude한정계약과회귀존재. actuallatecompletion/모든모델종료/사전허용자동대체가전부검증된것아님.|각위험시나리오에서접수·파일·비용·재실행을분리. 새유료호출이필요한표본은사전권한/예산gate.|
|FR08/13/17 — 능력·의존·원곡/샷보존|현재adapter·action/local편집의제한범위. 실제다중참조/상세능력/12샷원조건을이번3샷출력으로대체할수없음.|모델별지원입력과실제수신/원곡·다른샷불변증거를분리. 지원안되는기능을추측구현하지않음.|
|FR12 — embedding독립|선택과canon/snapshot분리계약. query는scopedsnapshot이며실제검색index의교체/재임베딩시험은없음.|원래검색요구의최신범위확인. 신규ingestion/ontology진화PLAN ONLY를넘지않음.|
|FR24 — 실제파일완료|M1 실제로컬MP4·decode·Take/출력과불명상태구분. fakefal결과≠실제외부미디어생성.|실제fal파일/원장완료는OM03. 화면성공문구만으로닫지않음.|
|FR25 — 3×2×2 실제조합|원본§14.3의12조합미완료. Claude15응답은이12조합시험이아님.|접근·권리·예산·짧은미디어범위승인후실시. 사용가능모든공급자라고표현하지않음.|
|FR28 — 평가후자동선택/대체|catalog automatic_routing=False. 현행수동선택요구와별도의원본§15.1 단계6확장.|최신명세/단계승인먼저확인. 자동선택을현재모션완료조건으로임의구현하지않음.|

**같은 작품 독립 세션은07의‘공급자 session을 canon 저장소로 쓰지 않는다’만으로 도출한 신규 기능이 아니다.** 부모의 명시 잔여 점검 요구와 PLAN K1의 미지원 기록을 근거로 별도 OM08에 둔다. 현행 `chat_runtime.prepare`의 project-wide pending/unknown gate를 세션으로 단순 분할하면 기존 비용/복구 보호가 달라질 수 있으므로, 세션 UI만 붙이는 수리로 취급하지 않는다.

## 권한과 자료가 있는 다음 행동 — 유한 인계

이 감사는 구현하지 않는다. 아래는 **이미 승인된 전체 개선/문서 정합화 범위에서 완료한 일·진행 가능한 일**과 **먼저 정해야 할 계약/외부 조건**을 분리한다. 새 feature를 추측해 backlog로 늘리지 않는다.

|ID·우선순위|구체 잔여와 원인|지금 가능한 행동 / 담당|선행조건·종료 증거|
|---|---|---|---|
|RW-01 · 완료, OM19|이전에는 README 최신 링크가403/QUALITY, PLAN이410/RECEIPT로 달랐다.|명시 권한을 받아 README 최신pointer를 R1/R2·410/10 및현재문서로 갱신.403/393문구는 날짜별 이력으로 보존.|로컬링크 확인. 제품/PLAN변경 없음. 후속날짜의문서수정은 R1 당시 handoff 문서hash를 소급 바꾸지 않음.|
|RW-02 · 제품잔여, OM08|한project에하나의project-default 이력만있음. CC01에서의도적으로제외했지만사용자전체목표상완료취소근거없음.|부모/primary가세션생성·선택·재개,canon공유,초안/turn/unknown귀속,모델선택의project대session범위에대한최소계약과대안을먼저설명. 승인된단일writer가그계약에따라구현.|**현재자료로부재는확정,세부UX/동시실행정책은미확정.** CC01/CC02불변,기존이력이기본세션으로보존,동일작품A/B누출0,unknown자동재제출0. 자동요약/새DB프레임워크는요구하지않음.|
|RW-03 · 완료—문서 연결, OM23|기존 등록coverage에는 최신CC01/CC02/M1/Q1/R1/R2 근거 연결이 없었다. 원본사본은 정상.|[38AT 현행 MD](SPEC-MS-001-ACCEPTANCE-TRACE.md)에 요구원문·FR·현재코드·시험/실제증거·한계/미실시·요구확인 연결. README/본표/등록부에서 진입 가능.|기존JSON·registration과원본불변. 38/38 행 연결을38개제품시험통과로바꾸지 않음. 일반live/운영·독립세션의 기능 잔여는 유지.|
|RW-04 · 완료, OM09–12/18|작성 중 최종 독립감사 R2를 수령했다. 격리10/10·동일hash·승인경로불변·저장화면3장 확인, 새 재현 중대결함 없음.|현재 문서와 등록부에 반영. NM-Q01 서버 사실 표시 계약 닫힘. 같은 검사를 다시 실행할 잔여 없음.|모델 원문 오류는 남음. VM/저장pixels 열람을 새 실제브라우저·전체410·실공급자 재실행으로 확대하지 않음.|
|RW-05 · 증거잔여, OM13/14/16|90목표달성미입증. 과거81과현행무총점QA는다른기준. 최신receipt 표본만으로전체시각품질을판정불가.|디자인담당이기존10그룹시각matrix·고정과업에현행증거를연결하고실제결함/가설만유한계획으로제시. 숫자평가를재개하려면같은기준/대표상태/독립검토범위를먼저설명.|1920주·1280보조·모바일보류. 새browser/API는이문서작업권한밖. 실제zoom/스크린리더제한유지. 점수상향만을위한변경·완료선언0.|
|RW-06 · 외부/범위의존, OM02/03/23|세chat선택코드는있지만일반live연결·OpenAI/Grok실제응답·fal수신/12조합은없거나미검증. 단순버튼누락으로확정할수없음.|primary가이미구현된guard/config와일반사용자진입계약의차이를읽기검토하고다음승인단위를제안. 연결활성화/비밀조회/유료실험은하지않음.|사용자권리/가격/계정접근/예산/입력범위확정후에만live. 기존3모델선택을또구현하거나새공급자추가하지않음.|
|RW-07 · 외부차단, OM17/20|REA실행전안전거절,Library prepare_uploads unavailable. 둘은제품코드결함과다름.|부모/도구담당에게정확한차단과로컬산출목록인계. 정상경로복구증거없이는재시도/대체업로드없음.|REA실행증거또는전달ID/version이실제확인될때만닫음. 예전ID재사용을최신전달로표기하지않음.|

NM-Q01 자유서술 잔여는 **알려진 모델 품질 제한**이다. R1은 사용자에게 현재 서버 사실을 먼저 보여주는 유한 완화책을 구현했다. “Claude가 어떤 경우에도 틀리지 않음”을 달성 가능한 필수수용으로 새로 추가하거나 유료재시도를 무한 반복하지 않는다. 독립 감사가 현재 표시/권한의 새 반례를 제시하면 그 반례에 한해 수리한다.

## 최종 상태 인계와 재발 방지

- **이번 직접 확인:** 문서·선별코드 읽기, R1 source/added_tests30/30해시,07원본/두사본·catalog hash 일치,23요구분류·로컬링크 점검. 새runtime/미디어/브라우저/회귀 재실행 없음.
- **구현팀 증거:**410회귀·served4/4·현재receipt표본,앞선9+6실제응답/실제모션·수정·편집·UI. **독립 증거:**C1/C2닫힘,M1후속의제한된원실행검증. **최종 독립 증거:**R2 격리10/10과 저장 화면3장, 승인 사실 표시 계약 닫힘. 원문 오류·live/zoom 제한은 유지.
- **미구현을 바로 작업으로 바꾸지 않는 gate:** 원 요구→현재코드부재→의도/범위→대안/이유→수용→단일writer→같은조건검증. OM08세부범위를추측하지않고,이미있는다중모델선택·닫힌CC01/CC02를재구현하지않는다.
- **현재완료와이력:**17:32정체/D1과당시Messages0는그시험의사실로보존. 이후성공이그당시원HTTP오류/앱대기원인을소급확정하지않음. 동일작업의종료/취소확인없는두번째writer·새유료시험금지.
- **남는경계:**실제invoice/전체live공급자,실제zoom/스크린리더/고객연구,최신디자인90,Library전달. 승인된PLAN ONLY인신규ingestion/ontology진화·Blender와모바일추가보류유지.
- **전달:**본표와갱신등록부는로컬MD다. Library새등록·전달완료주장없음. 이번 명시 허용으로 README 최신 문서 연결만 갱신했다. primary의 PLAN/CHAT-SESSION-PLAN과 기존 등록 JSON은 수정하지 않았다.

이 문서는23개 항목의 현행 대조표 하나다. 원인·이전상태·누락예방의 권위는 [OMISSION-REGISTER.md](OMISSION-REGISTER.md)에 유지하고, 다음 증거가 도착하면 해당 행과 상태전이만 갱신한다. 유한 체크포인트의 완료를 프로젝트 전체 완료로 표시하지 않는다.


### 문서 상태 전이 기록

- 최초 RECEIPT 대조: 완료7/증거제한8/계획전용3/외부차단3/미구현2. OM19는 README 최신 안내 잔여, RW03은38AT 최신 근거 연결 잔여였다.
- 후속 명시 문서 정합화: **OM19 완료**, **RW03 문서 연결 완료**. 현재 완료8/증거제한8/계획전용3/외부차단3/미구현1. OM23의 제품 전체수용은 증거제한 유지. 제품 구현/테스트 숫자를 새로 늘린 변화가 아니다.
