# Aethon — 전체 디자인 작업·검증 통합 계획

## 2026-10-27 후속 구현 이후 현재 기준

아래 ‘구현 미재개’, 416회귀와 문서만 작업한 범위는 **당시 이력**이다. 현재는 일부 기능 구현이 재개됐고 음원·자막·미리보기·대화 모델 예약의 제한된 검증과 [435개 회귀 기록](../codex-workflow-review-20261027/regression-435-20261027.log)이 있다. 동일 조건의 전체 디자인 QA, 일반 사용자 Claude 연결 및 실무 업무 완주는 미완료다. 결과와 잔여는 [최신 작업 기록](../codex-workflow-review-20261027/REPORT-ko.md)과 [남은 작업](../REMAINING-WORK.md)을 따른다.

최신 사용자 지시에 따라 AI 모델 연결을 제외한 제작·편집·저장·출력·복구는 다른 플랫폼 서비스에 필수 의존하지 않는 자체 기능을 목표로 한다. 음원부터 시작하고 사진은 선택이며, 실제 AI 영상 모델 시험은 실무 워크플로 준비 이후로 보류한다. 조사 도구의 REA나 오픈소스 사용은 제품의 외부 서비스 의존과 구분한다. 기능 작업 후 실제 설치본의 Hallmark·Impeccable을 사용해 근거 기반 진단→계획 제시→구현→동일 조건 검증을 수행하며, 과거 스킬 검사의 수행 범위를 확대하지 않는다.

## 현재 실행 경계 · 2026-10-27 문서 채택

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** 사용자 `Sentinel_dd01ccfa2ffc819197e6d67fa402ecfc` 및 `Sentinel_c6a68879bed8819182c6ccce6dafb174`가 AD01–AD07과 문서 반영을 승인하면서 구현은 하지 말라고 제한했다. 원본183행 workflow의 근거→진단→이유/대안→계획→구현→검증→인계 순서를 유지하며, 이번에는 G3 문서 승인과 문서 정합화까지만 완료했다. G4 구현은 시작하지 않는다.

|현재 기준|근거·판정|
|---|---|
|제품 정체성|[보충문](../../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md): Aethon IP 음악영상 제작 제품; AethonSaaS와 별개. 피벗 이후 사업 기준, 개인 제작 기본·팀 선택. 과거 사업/시장 수치 무변경|
|채택된 설계|[AD01–AD07 단일 설계](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md) §7/§16. P1개인 입력·세션·상태→P2개인 이어 만들기/의견→P3선택적 팀 권한→P4팀 변형. AD07은 단계별 적용|
|마지막 전체 검증|[416 polling manifest](../chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json). 원래18관련시험은 부분집합이며 합산하지 않음. 독립 최종 CQ-R01 재검증 별도|
|현재 소스|[세션 계획](../../design/CHAT-SESSION-PLAN.md), [baseline](../chat-conversations-20261027/BASELINE.json): 이후 부분 구현 중단. 기존 실행기18개 인계만 있고 새세션/UI/전체회귀 미완료.416을 현재 partial에 적용 금지|
|문서 검증|[12묶음 반영·전후 보존](../adoption-docs-20261027/REPORT-ko.md). 원본07/사업/DOCX·제품/테스트 불변. 실제 기능시험0|

### 재개 전후 작업 방식

1. 재개 지시가 있을 때 **기존 partial diff와 before 사본을 먼저 검토**한다. 자동 rollback, 새 세션 엔진 중복 작성, 두 source writer를 허용하지 않는다.
2. AD의 근거·원문 수용→문제/가설·영향→실제 대안→선택 이유→영향 token/component/state/interaction→유한 수용·회귀를 연결한다. 확정된 복수 대화/병행/공유 canon 결정을 다시 질문하지 않는다.
3. 개인 과업은 팀 가입 없이 검증한다. 팀 역할·공개/철회·동시성은 선택적 팀 단계의 진입 gate이며 개인 단계 전체의 선행 조건이 아니다. 사람 실행승인·비용/권리·비파괴 버전은 양쪽 모두 유지한다.
4. 코드·합성 fake·실제 Claude·실제 decode/encode·실제 외부 미디어·사용자 관찰을 따로 판정한다. 같은 source/fixture/frame·1920×1080주/1280×900보조·앱배율의 전후와 키보드·오류·긴 콘텐츠를 검증한다. 모바일 추가는 보류, 실제zoom/스크린리더 미실시는 성공 아님.
5. Refero는 기존 research-first reference lock, Hallmark/Impeccable은 유용한 수동 craft/상태 기준을 보조한다. 기존 static sloplint 실행과 Impeccable엔진 미실행, REA등록/차단, Library읽기/업로드차단을 구분한다. [실제 적용 기록·G0–G7](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md). 새 스킬 실행/설치 없음.
6. 유한 묶음의 고정hash에서 독립 재검증→현재 entry/추적표/등록부/전달 증거를 연결한다. 닫힌반례는 새근거 없이 재개하지 않고 테스트 기준·분모를 조작하지 않는다. 전체목표미완료와 묶음종료를 구별한다.

Blender·이질 자료 입력·자동 온톨로지 진화는 K.2/K.3 및 [별도 모델화 계획](../../design/AI-MODELING-PLAN.md)의 PLAN ONLY다. AD01 채택이 수집/OCR/자동학습을 실행할 권한은 아니다. 원본07의 no-MCP/fal·독립모델·권리/비용/승인 유지. 응답 중 모델변경 UX와 원본07§3.2 차이는 세션계획에서 명시 조정하며 원문을 몰래 바꾸지 않는다.

## 기존 실행계획·체크포인트 이력 — 당시 상태 보존

**현재 체크포인트 — 2026-10-26 19:34 UTC:** NM-Q01 deterministic 서버 영수증을 기존 chat/state/search 경로에 통합했다. 현재 승인 사실과 과거 조회, 모델 원문을 구별하며 새 권한/API는 없다. 410/410, served1920/1280·초안·포커스·재열기 통과; 새 유료 호출0. 모델 자유서술의 잔여 오류는 원문에 보존하며 해결했다고 주장하지 않는다. [실행·검증 상세](../native-motion-20261026/server-receipt-ui/REPORT-ko.md), [고정 manifest](../native-motion-20261026/RECEIPT-MANIFEST.json). 이 이전의 계획/수치는 역사적 기록이다. 신규 ingestion/자동온톨로지/Blender 계획 전용 범위 유지.

> **최신 품질 체크포인트 · 2026-10-26 19:05 UTC.** NM-Q01/NM-Q02 후속에서 저장된 모션 승인 actor/scope/version과 새 제안을 구분하고, 서버 계산 timeline diff를 추가했다. 최종403/403(383비HTTP+20HTTP), 신규10/10·관련27/27은 전체에 포함한다. 실제 추가6응답/$0.0061185, 누적$0.0381186/실청구미확인. 편집 before/after 설명은 표본 통과했고 기존 승인·새 제안의 구분도 개선됐지만, 실행 가능성에 불필요한 ontology 근거를 섞는 문장은 남는다. [현재 결과](../native-motion-20261026/REPORT-ko.md), [현재 소스·판정 manifest](../native-motion-20261026/QUALITY-MANIFEST.json). HTML/CSS/JS와 승인 실행 서비스는 불변이며 신규 브라우저 시험은 없다. 앞선9응답/393개/UI 증거는 아래 시점별 기록으로 보존한다. 추가 응답 상한6을 사용했으므로 이번 시험은 종료했고 자동재시도하지 않는다.

> **최신 기능 체크포인트 · 2026-10-26 후속 검증 종료.** K.4/K.5 실제 Claude 9응답의 3개 실행 표본, 4초 모션/12프레임 수정/3초 음악·자막 출력, 격리 Chrome UI 검증을 완료했다. 최종393/393(373비HTTP+20HTTP), HTML `25bfab1a…e768b`, motion JS `71e8959f…7e40e`. [현재 결과·잔여 한계](../native-motion-20261026/REPORT-ko.md), [현재 source/served manifest](../native-motion-20261026/FOLLOWUP-MANIFEST.json). 승인 상태 및 편집 차이를 설명하는 모델 답변은 일부 미흡해 별도 품질 gate로 남는다. 누적 usage 가격 $0.0320001, 실청구 미확인. 아래350/358/365/379와 당시 차단 상태는 각 시점의 이력이며 현재 상태를 덮지 않는다. 새 ingestion/온톨로지 진화·Blender는 계속 계획 전용이다.

> **현행 기준 · 2026-10-26 08:20 UTC 검증 종료.** 계획 설명 이후 B0a 표시명 전환과 B1/B5/B6 로컬 검증·인계를 완료했다. 새 시각 결함이 재현되지 않아 B2–4의 가설 기반 변경은 생략했다. [현재 결과](REPORT-ko.md), [정확한 소스·증거·종료 manifest](implementation/FINAL-MANIFEST.json)를 기준으로 삼는다. 아래 계획의 과거 증거는 현재 전수 통과로 바꾸지 않는다.

**최신 결정과 상태:** Aethon 표시명이 UI/실행 안내/README에 적용됐다. 기존 Loretune 폴더·모듈·저장/인증 식별자와 원본 명세·과거 증거를 보존했다. 전체350개 회귀(330비HTTP+20HTTP, 한 실행), 현재 served8상태, 두 폼 통제응답12조건, 격리 UI의 합성 후보→3초1080p 음악/한글자막 출력→reload를 검증했다. 임시 서버2개/렌더worker/검증공간42는 종료했다. 신규 유료/실제 모델 호출은0이다.

**2026-10-26 CC01 후속 완료:** K.1의 제한된 문맥 보존 수정과 실제 Claude 합성 조회·프롬프트 시험을 실행했다. 최종358회귀(338비HTTP+20HTTP), 실제 Messages14회, 이번 usage가격$0.0147338/누적$0.0224918,실청구미확인이다. [최신 기능 보고서](../cc01-context-fix-20261026/REPORT-ko.md), [고정 source manifest](../cc01-context-fix-20261026/FINAL-MANIFEST.json). 위350/UI8상태 증거는 앞선 UI 릴리스의 역사적 결과이며 UI source는 byte 동일하다. 모션그래픽·모델 편집 확장·새 ingestion/온톨로지진화·Blender 모델화는 별도 계획/검증 범위다.

**2026-10-26 CC02 후속 완료:** 독립 감사의 최종 Messages byte 사전검사 결함을 수정했다. 전체365/365(345비HTTP+20HTTP), 새7조건은 수정 전3실패→수정 후7통과이며 새 실제 API 호출0. [현재 수정 보고서](../cc02-preflight-fix-20261026/REPORT-ko.md), [현재 source manifest](../cc02-preflight-fix-20261026/FINAL-MANIFEST.json). 이전 live14응답 output/usage는 검증됐지만 원 입력 전체 재해시는6/14만 가능하고8/14는 thinking redaction 제한을 유지한다. K.4/K.5는 당시 다음 실행 제안이었으며, 현재 구현·검증 상태는 바로 아래 후속 기록을 따른다.

**2026-10-26 K.4/K.5 후속:** M0 한글·도형1frame, M1 제한모션→승인→96frameMP4→미선택Take/복원, E1순서·자막·원음offset제안→사람승인→실제출력의 로컬 구현과fixture 검증을 마쳤다. 전체379/379(359비HTTP+20HTTP), 현재 [결과·잔여gate](../native-motion-20261026/REPORT-ko.md), [source manifest](../native-motion-20261026/FINAL-MANIFEST.json). 실제Claude시험은 count 경로 실패로 Messages0/예약0/추가usage0에서중단했다. 새UI브라우저검증도Ego조회중단으로미완료다. 모의scene를실제Claude저작이라고하지않는다. 공유데이터/유료fal/ingestion/Blender변경0. 아래E8/CC01/CC02의과거화면·테스트는해당빌드의증거로보존한다.

## A. 입력·기준선·이번 정합화에서 달라진 점

입력은 Library `libfile_3f4825539680819196c9307c0a8d1ce1`, **붙여넣은 텍스트.txt**, text/plain,17,322bytes,183행이다. 공식 Library `read`가 1–183행을 반환했고 `has_more=false`여서 전부 읽었다. 버전 ID는 null이었다. 직접 텍스트 읽기로 충분해 로컬 materialization은 하지 않았고, 과거 차단된 업로드를 재시도하지 않았다. 새 문서는 작업 절차를 보완하며 원본 제품 명세나 최신 사용자 결정을 대체하지 않는다.

기존 계획은 작은 수정의 반례·전후 비교에는 구체적이었지만 **전체 화면/상태의 범위, 열린 문제의 등급과 확신, 구조 대안, 의존성, 종료 조건**이 여러 보고서에 흩어져 있었다. 이번에는 다음을 보완한다.

1. 전체 제작 과업을 12개 화면·흐름 묶음으로 정리하고 현재 코드 확인, 현재 빌드의 실제 화면, 과거 증거, 미검증을 구분한다.
2. 문제 ID와 관찰/가설/coverage gap을 분리한다. 이미 닫힌 결함을 재개하거나 미검증을 곧바로 결함으로 세지 않는다.
3. 다음 작업을 단순 테두리 조정으로 축소하지 않는다. 입력→계획→승인→진행/복구→검토→편집→출력/재개의 알려진 목표를 점검한 후 필요한 작은 변경만 한다.
4. 역할 토큰·컴포넌트·상태·파일 범위와 검증 의존성을 고정한다. 새 명세·새 팔레트·새 프레임워크·경쟁 문서를 만들지 않는다.
5. 스킬 읽기/수동 적용/명령 실행/실행 불가를 분리하고, 실제 브라우저·VM·fixture·live 증거를 합치지 않는다.

독립 계획 검토의 PL02(분산된 과업/상태/빌드 coverage)는 C/H, PL03(넓은 공간·위계·아이콘 범주)은 D/F, PL04(작은 묶음과 전체 제품계획의 단절)는 B/C/G, PL05(분산된 종료·인계)는 H/J로 연결했다. 이들은 새 제품 결함이 아니라 계획의 구체성 문제다. 문서 불일치 PL01은 부모의 명시적 요청으로 `design-system-redesign-20261026/INDEX.md`와 `INTEGRATION-CONTRACT.md`의 현행 입구만 정정했다. 원감사의 VF01/VF02 실패는 역사적 결과로 보존하고 닫힘·최신 E1을 연결했다.

현재 코드와 최신 실제 served 검증 기준(E8):

|파일|SHA256|
|---|---|
|`index.html`|`d82ca93a64f31e71bf0c469b1b72b7c59c6a4bbe0403b969881349d8ec82f6e2`|
|`studio.css`|`4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`|
|`studio-media.js`|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|`app.py`|`830cc77c8004c4b673e7cda4653782646ca14092f46d7647a8750717fbd96780`|

현재 경로의 `git status --short`는 **not a git repository**로 종료했다. clean tree라고 주장하지 않는다. root/`tests`의 소스121개 해시를 계획 편집 전후 비교했고 변경0·삭제0을 확인했다. 수정한 현행 문서3개의 로컬 링크도 누락0이었다. 이는 문서/보존 검사이며 제품 회귀 테스트를 새로 실행했다는 뜻은 아니다. root AGENTS.md/PRODUCT.md/DESIGN.md/design.md/package.json/session-handoff.md/checkpoint.md는 없었다. 홈 AGENTS와 `.codex/AGENTS.md`, README, 기존 설계/인계 문서를 읽었다. 문서 이름이 없다는 이유로 신규 제품으로 취급하지 않는다. 설치본 스킬·도구 메타데이터도 수정하지 않는다.

증거 참조:

- **E8 현재 구현·검증** [결과와12개 coverage](REPORT-ko.md), [manifest](implementation/FINAL-MANIFEST.json), [현재350회귀](implementation/full-regression.log), [실제 로컬 출력](implementation/workflow/output-verification.json). B0a 이후 source/served 확인과 종료까지 연결한다. E1–7은 이전 빌드/계획 근거다.

- **E1** [최신 헤더 구현·8쌍 실제 served 화면·330 비HTTP 회귀](../context-header-space-20261026/REPORT-ko.md), [해시·종료 기록](../context-header-space-20261026/FINAL-MANIFEST.json). 현재 두1920 저장 이미지를 이번 계획에서 다시 열어 확인했다. 새 캡처는 아니다.
- **E2** [두 폼 초안 보호](../proposal-draft-fix-20261026/REPORT-ko.md), [동일 수정의 실제 브라우저12조건](../proposal-draft-fix-20261026/served-baseline/REPORT-ko.md). 이때 HTML은 이전 해시이며 현재 full regression이 보호한다.
- **E3** [값 보존 토큰·computed/숫자 폭](../value-preserving-tokens-20261026/REPORT-ko.md). 헤더 이전 빌드의 token 결과이며 현재 토큰 값은 소스 대조로 확인했다.
- **E4** [24개 기능·22개 시각 QA와 범위](../frontend-fq-vq-fixes-20261026/Loretune-프론트엔드-QA-기준과-검증결과-20261026.md), [독립 FQ 재검증](../independent-frontend-fq-recheck-20261026/REPORT-ko.md). 당시349는329비HTTP+20HTTP의 분할 실행이며 이번330과 합산하지 않는다.
- **E5** [CLI/스킬 평가](REPORT-ko.md), [코드 계약 검토](CLI-REVIEW-ko.md), [문맥 조회 관측](context-observation.json). 새 폼 결함의 당시 기록과 아직 남는 기능 경계를 구분한다.
- **E6** [현행 DS-01–14](../design-system-redesign-20261026/REQUIREMENTS-AND-ACCEPTANCE-ko.md), [token spec](../design-system-redesign-20261026/SEMANTIC-TOKEN-SPEC.md), [reference lock](../design-system-redesign-20261026/REFERENCE-LOCK.md), [방법론 적합표](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md). 설계 문서의 과거 pending/hash는 현재 실행 상태가 아니다. 명시적으로 허용된 INDEX/INTEGRATION-CONTRACT 입구의 상태만 이번에 정정했다. 수용기준·토큰·방법론과 원감사는 덮어쓰지 않고 추가 정합화가 필요하면 소유 검토자에게 전달한다.
- **E7** [원본 SPEC-MS-001](../../knowledge/project_kit/docs/modules/spec-ms-001/20261025/07_Chat_Directed_Multimodel_Production_Spec.md): §3화면,§5도구,§7문맥,§8–9미디어/승인,§13–15요구/수용/단계. 원본의 공급자 예시는 보존하되 사용자 확정인 fal 미디어/noMCP/Runway 벤치마크 역할이 실행 판단에 우선한다.

## B. 제품·사용자 과업·성공 조건

**확인된 제품:** Aethon은 로컬 음악영상 제작 작업대다. 현재 README와 실행 UI의 제품 표시명은 Aethon이다. 내부 호환 식별자는 보존했다. Python 표준 라이브러리 HTTP/SQLite/기존 FFmpeg, 단일 HTML+CSS+미디어JS 구성이다. `app.py:873`의 서버,`:913–919`의 `/`,스타일,미디어JS,상태,모델목록과 `:985`의 `/api/action`을 사용한다. 여러 SPA 내부 패널과 dialog를 별도 URL 제품처럼 세지 않는다.

**대상 가설:** 일관된 IP 설정과 곡을 바탕으로 장면을 계획·제작·검토하려는 창작자. 실제 고객/직무/숙련도/사용빈도 조사는 없으므로 초보 경로와 숙련자 상세편집은 설계 대상이지 관찰된 사용자 집단이 아니다.

**주 과업:** 작품/IP·원곡 확인 → 선택한 채팅 모델과 정식 문맥으로 기획 → 계획/대상/모델/비용 검토 → 사람의 유효한 허용 범위 안에서 서버 도구 실행 → 파일 수집·등록 또는 기존 요청 복구 → 후보 비교·선택·검토 → 장면/음악/자막 편집 → 승인된 버전 출력 → 결과 확인·재개. 부분 수정은 필요한 샷의 새 후보이며 다른 샷·원음·기존 Take·승인본을 보존한다. 채팅과 상세 작업대는 같은 프로젝트/버전을 쓴다.

**확정 아키텍처:** Claude/OpenAI/Grok 계열 채팅 선택과 이미지/영상 선택을 독립 유지한다. 채팅 공급자 API→Aethon의 공통 제작 도구→사용자가 선택한 fal 모델 경로다. MCP·Runway/Higgsfield 직접 연결은 제품 요구가 아니다. 개발/조사 MCP 사용과는 별개다. 모델 catalog 등록/fixture/1경로의 실제 Claude 성공을 모든 조합 활성화로 바꾸지 않는다.

**이번 성공:** 알려진 제작 흐름의 핵심 상태를 빠뜨리지 않은 계획과 위험에 맞는 검증, 확인된 로컬 UX 결함의 수리, 현재 화면의 일관성, 정확한 상태·근거 표시. 1920×1080 CSS viewport/앱100%가 주 기준,1280×900이 보조다. 긴 상세는 접근 가능한 내부 scroll, 확대는 reflow를 허용한다. 모바일 추가 개선은 뒤로 미루되 기존 코드는 보존한다. `overflow:hidden`이나 축소 글자로 페이지 높이만 맞추지 않는다.

**범위 밖:** 새 공급자·모델 활성화/키 조회·설정, 유료호출, 실고객 자료 전송, 배포/다중사용자 인증 인프라,12live조합, 전체96FR/143API 완성, 신규 기능·언어·테마·모바일 전면 개편. 외부 연결과 대규모 검색 품질은 아래 별도 backlog이며 디자인 개선으로 해결됐다고 하지 않는다.

## C. 화면·흐름 coverage inventory

아래 표는 계획 당시 검사 목록이며 E8 결과표가 이번 실제 확인 범위를 갱신한다. 표의 E1 ‘현재’는 해당 당시 빌드다. 최신 실제 상태별 결과는 REPORT의 S01–12 표를 우선한다. ‘과거’는 연결된 QA 당시 빌드이며 현재 전수 통과가 아니다. 각 행은 기본/로딩/빈 상태/오류를 무조건 새로 만들라는 뜻이 아니라 **기존 기능에서 도달 가능한 상태**를 조사하는 범위다.

|ID·화면/목적|현재 코드 접점|보유 증거 / 아직 확인할 상태|완료 판정·연결|
|---|---|---|---|
|S01 작품/IP 선택·재개: 작업 대상을 안다|`#songs`, `#projectDialog`, `#settingDialog`, `#ipForm`; `index.html:32–33`|E1 현재 populated 읽기/재개. 신규/빈 작품·보관/복원 전체는 과거/fixture|현재 대상 유지, 전환 전후 초안 귀속, 빈 경우 실제 다음 행동. DS05/11|
|S02 음악 입력·구간 확정: 원곡과 계획 길이를 정한다|`#audioUpload`, `#musicStructure`, `audioWave`; `index.html:21,45`; `music.py`|E3 실제 PCM표시; 입력/형식·구간은 기존 tests. 새 화면 오류·빈 음원 표본 부족|원곡/구간/분석 종류를 정직 표시, 미확정 계획은 승인 차단, 파일 실패시 입력 유지. DS06/11|
|S03 기획·채팅: 요청에서 검토 가능한 계획을 얻는다|`#guidedBrief`, `#chatForm`, `#modelChatForm`, `#chatPlans`; `index.html:19,359,386`|E2 로컬 기획폼 브라우저12조건; actual modelChat는 별도 과거 합성live, 최신 전체 렌더 미점검|규칙 초안/모의/실제 경계, 원문/출처/제안 상태, 모델·취소·unknown. MS-FR01/02/07/26|
|S04 모델 설정: 선택·사용 가능성·변경 범위를 안다|`#modelSettingsPanel`, `#modelSlots`, `drawModelSettings`; `index.html:18,554`; `model_selection.py`|selected-but-unavailable 과거 수정/회귀. 최신 empty/retired/긴 이름/dialog 전체는 재표본 필요|선택을 지우지 않고 불가 이유와 다음 응답/새 작업 적용을 알림. Escape/focus 복귀. MS-FR03/09/11/21|
|S05 계획·견적·제작 허용: 무엇을 얼마에 실행할지 안다|`#guidedPlans`, `#mediaPrepareForm`, `.media-action-card`; `index.html:25,drawExecutionCards/drawMediaCreator`|공통 도구·승인·권리·예산 fake/contracts와 과거 UI. 현재 모든 상태 캡처 아님|수량/대상/모델/견적/상한/권리/영향을 결정시점에 제공. hold/reject/approve 구분, 유효 허용 재사용·stale 재검사. MS-FR05/06/13/18|
|S06 장면 탐색·재생: 편집 대상과 재생 대상을 구별|`#shotlist`, `#preview`, `#sequenceTransport`, `.lt-scene-context`; `studio-media.js`|E1 최신8상태+긴문구. DM/FQ가 과거 독립 재현 및 현재330에 포함|contain/실제 poster, 시간좌표·음원·자막, selected/sequence/ended/error를 일관 표시. DS05/06/12/13/14|
|S07 Take 비교·검토: 대안을 보고 별도로 판단|`#takes`, `#compareDialog`, `#creatorReviewEditor`, `#takeDecision`, `#reviewReason`|E1 비교1920쌍/1280후, 과거 F07/다중맥락; 현재 모든 결정 상태는 미표본|비교≠채택≠승인, 서로 다른 기본Take, 초안/문맥/지연성공 보존, 승인결과의 보조수정. DS08/09/10|
|S08 정밀 편집: 순서/trim/곡/자막·버전을 통제|`#ltTimelineDock`, `#track`, `.lt-timeline-controls`, `draft`; `editing.py`, `caption_preview.py`|E1 save/cancel접근·dirty/통제422, 실제1:2:4시간축은 과거. 최신 새 render는 없음|같은 시간축·길이·원본범위, 초안보존, 버전/stale, 승인 무효화 범위와 독립 내부scroll. DS06/10/14|
|S09 자산·사용권·재사용: 사용 가능한 원본을 가져온다|`#libraryDialog`, `#rightsDialog`, `#upload`; `action_assets.py`, `references.py`|과거권리/격리fixture와 UI, 최신 검색없음/미연결/금지상태 표본 부족|source/version/권리 전달·승인 미상속, 검색결과없음의 구체 다음 행동. DS11/13; MS-FR08/13|
|S10 정식 설정·취향·변경제안: 기억과 예외를 관리|`#ontologyDialog`, `#candidateForm`, `#preferencesDialog`, `#memoryProposals`; `project_ontology.py`|E2 취향폼12조건, ontology과거실Claude/합성단위; 최신전체dialog 미표본|곡 예외/global 구분, 출처/불확실성/충돌, 제안≠적용, 사람 승인·stale·rollback. MS-FR11/12|
|S11 작업/복구/비용: 중단된 작업을 중복 없이 이어간다|`.creator-recovery-card`, `#budgetDialog`, `#operationsDialog`, `sendRequest`; queue/ledger/recovery modules|E4 unknown/403/계약회귀, E1확정422. 현재 모든job상태는 미표본|provider-completed≠collected≠registered, unknown조회만, 취소≠환급, 회수≠자동채택, 예상/사용량/실청구 분리. MS-FR14–16/18/20/24|
|S12 출력·검증·재개: 승인버전 결과를 확인한다|`#renderConfirm`, `.render-section`, output/job cards; `renderer.py`|과거 합성1080p/음원/한글자막·재시작, 현재330미디어회귀. 현재새브라우저출력 미실행|요청≠파일검증≠납품승인, 음악/자막revision·길이/순서/파일 확인, 이전결과 보존·재개. DS11; MS-FR17/24/26|

공통 상태 검증축: default/hover/focus/pressed/selected/disabled, loading/empty/no-results/full, dirty/saving/saved/rejected/unknown/committed-but-refresh-failed, stale/permission-blocked/unverified/retired, dialog open/close/escape/focus return. 지원하지 않는 상태에 가짜 버튼·스켈레톤·성공 화면을 추가하지 않는다.

## D. 추적 가능한 문제·가설·기능 경계

심각도는 사용자 영향에 관한 판단, 확신은 증거 강도다. P0과업 차단·데이터/비용위험, P1중대 마찰, P2우회 가능한 불편, P3유지보수/표현 보정. 실제 빈도/사용자 수는 모두 미측정이다. U는 미검증이며 심각도를 부여하지 않는다. 아래 새 DP26 ID는 기존 DS/FR/감사ID를 대체하지 않는다.

|ID·상태|관찰 / 증거·빌드|과업 영향·원인/가설|심각도 / 확신|결정·합격 기준|
|---|---|---|---|---|
|DP26-01 **완료**|취향/로컬기획 두 폼의 성공 후 신규입력 유실, E2|무조건reset이 제출문맥/입력revision을 무시|당시P2 / 높음|문맥+revision+snapshot 보호, 원6사례4실패→6통과,확장38+연결1,브라우저12. 실제modelChat 결함으로 확대 금지|
|DP26-02 **완료**|파형배경/정확#DDD/timecodefont가 역할토큰 밖, E3|값 자체오류 아님, 미래변경 추적비용|P3 / 소스높음·사용자영향미측정|세 선언만 token화; 값·points·숫자폭 동일. 전체DS01완료 주장 금지|
|DP26-03 **완료**|접힌 제목/설명88px, E1 같은8상태|별도행이 미디어세로예산36px 사용|P2 / 높음|52px통합,+36px실영상,기본/비교/글자/자막/축보존. 펼침에는 증가없음이라는절충 명시|
|DP26-04 **핵심 표본 완료·전체 coverage 잔여**|S01–12 최신빌드 상태별 evidence가 균일하지 않음, C표/E1/E4|부분스크린샷을 전체완료로 설명할 위험; historical/fixture/current 혼재|U / coverage높음|B1에서 실제경로별 검증종류와not-run 분리; 확인된 blocker만 새issue. 모든판정을 최신이라고재명명하지않음|
|DP26-05 **computed 표본 분류·추가 정리 보류**|`studio.css:68,72,77,118,120,192,622`에 font/white/black/spacing literal; E1소스|active인지cascade확인전 시각결함아님. 역할관리의공백 가능|P3 / 존재높음·활성영향미확인|computed inventory→active역할/의도적예외분류. 실제값유지 필요한alias만, 기존정확흰색을#F4F4F2로몰래치환금지|
|DP26-06 **가설**|현재1920 화면에 passive panel/Take/선택/버튼경계가공존, E1저장픽셀|관련그룹의동등강조가다음행동탐색을방해할수있음; 실제혼란증거없음|미정 / 낮음|S05/S07/S08과업별현재primary/보조/상태구분을검토. 구체중복·오인재현없으면변경하지않음. input/focus/selected/approval경계보존|
|DP26-06a **가설 세분화**|`.inspector`/`#ltTimelineDock` passive 외곽과 내부행동 경계, E11920 기본 화면|수동 그룹과 조작의 경계강도가 같아 보일 가능성; 불편은 미측정|미정 / 낮음|실제 active border/면을 측정하고 검토 과업의 그룹 식별을 설명. 구체적 충돌이 없으면 현재 유지. 승인 완료에 새 primary를 만들지 않음|
|DP26-06b **관찰 대기**|`#compareButton`과 Take strip의 거리, E1같은 화면|비교 시작을 찾는 이동 비용 가능성만 있으며 근접 배치가 더 낫다는 증거 없음|미정 / 낮음|현재 비교 진입과 선택의 구분·읽기순서부터 확인. 단순 거리 감소만으로 이동하지 않음. 변경한다면 기본/다중Take/긴문구/focus/선택불변 비교|
|DP26-06c **관찰 대기**|native summary marker, 재생기호, 검토 기호+텍스트의 optical alignment|실제 오정렬을 이번에 재현하지 않음. 아이콘 전체 교체 근거 없음|미정 / 낮음|이름 있는 대상의 rect/기준선/저장 픽셀에서 결함이 확인될 때만 해당 offset을 명세. native glyph 차이는 자동 결함으로 세지 않음|
|DP26-07 **대표 상태 검증·미실행 분리**|현재모델/계획/설정copy는코드와과거표본,최신전체states미확인|미선택/선택불가,제안/실행/완료를혼동할위험의가설|U / 구조높음·사용성미확인|S03–05/S10–12를실제상태projection과대조,없는행동약속0/내부ID기본노출0/결정정보유지. 거짓표시재현시기존서비스의표현만수정|
|DP26-08 **완료**|README상단346과옛인계,기존PLAN진행문구,설계docs과거pending, E5/E6|최신작업을누락하거나완료를오인할위험|P3 / 높음|이PLAN을단일현재계획으로;최종인계시README입구와소유문서링크갱신. 역사적숫자/원문명세보존|
|DP26-09 **미검증**|실제browserzoom/IME/forced-colors/screenreader/전체keyboard가부분범위, E1/E4|확대·입력·탐색결함이남을수있음;현재실패로단정불가|U / coverage높음|가능환경만실측,앱200%와구별. 포커스전체노출제품기준과WCAG위반판정구별. 설치/추가접근필요시분리|
|DP26-10 **미검증**|유효한성능기준선없음;이전30전환timing값은제외,E4|반응지연/메모리누수는아직가설|U / 낮음|체감/측정된재현이있을때만같은fixture로측정. staticDOM/media개수관찰을성능보장으로확대금지|
|DP26-11 **완료**|사용자 Aethon 명명 결정; 현재 `index.html:1,13`, `app.py:1015`, `README.md:1,91`에 옛 사용자 표시 확인|제품 이름과 현재 화면·안내가 불일치. 결함 심각도 경쟁이 아닌 명시 요구이며 전역 치환은 저장/복구 호환성을 해칠 수 있음|요구 작업 / 높음|F의 표시·호환 목록 구분 후 현재 title/header/안내만 Aethon. 내부 namespace·경로·기존 초안/요청·import 불변을 회귀로 확인. 원명세/과거 캡처·보고서 보존|
|FG26-01 **실제 기능범위차이·별도backlog**|`production_tools.py:70–74` query와무관한scoped-snapshot, E5메모리관측|작은문맥조회는정직하게작동하나규모확장/검색효율미완성|대규모과업에서영향미정 / 높음|검색의scope/sourceID/빈결과/승인revision/예산 계약을별도계획. 새embedding/provider/검색엔진을디자인patch에끼우지않음|
|FG26-02 **코드+외부게이트 구분**|`chat_runtime.py:121`, `app.py:873`, registry는합성승인/주입제한, E5|일반프로젝트에안전한설정·전송동의·검증경로가아직제한;단순API403만남은것아님|일반live목표blocker / 높음|일반연결설정코드필요범위와계정/토큰계산/가격/live검증을별도인계. guard해제·모델silentfallback금지|
|FG26-03 **외부실검증차단**|과거falCDN403 및후속token발급403은다른단계;OpenAI/Grok/fal추가조합live미검증|완전한실생성→회수→등록및정산을현재보장할수없음|live목표blocker / 기존증거범위높음|권한/결과/비용근거확보후별도허용된시험만. 이번호출/키조회/공개fallback0|

**E8 실행 판정:** DP04/07은 아래 REPORT의 각 상태별 current/fixture/historical/not-run 구분을 완료했으며 전수검증 완료가 아니다. DP05는 body/button/input/timecode/pre/skip-link의 실제 computed와 의도된 예외를 확인했고 추가 alias 변경 필요를 재현하지 않았다. DP06/06a–c는 구체적 시각 결함이 관측되지 않아 보류하며 임의 수정하지 않았다. DP08/11은 완료. DP09/10과 FG01–03의 미검증/기능 경계는 남는다.

F07·DM01–03·FQ01–03·VF01/02·B/MM계열의 기존 닫힌 반례는 해당 원감사와 현재 regression으로 보존한다. 이번에 재현하지 않은 것을 새 finding이나 다시 미해결로 세지 않는다. 실제token/상태/비교/원본보존이 잘 작동하는 이유도 같은 결정기록에 남긴다.

## E. 중요한 선택의 대안과 채택 이유

|판단|실질 대안|선택·이유·비용/위험|
|---|---|---|
|작업 공간|①현재bounded rail/media/inspector/timeline 유지+국소 위계 ②정밀편집을 별도drawer/modal로 이동 ③세로문서형/마법사로 재구축|**①유지**. E1에서+36px확보와조작접근을확인했다.②는panel상태·focus·초안전환비용,③은사용자의한화면목표와상충. 추가구조는현재과업실패가재현될때만가벼운prototype으로비교|
|계획→실행의정보|①기존결과옆맥락카드+상세공개 ②모든기술/권한을상시노출 ③모든것을채팅안으로숨김|**①**. 대상/모델/비용/승인/오류를결정시점에유지하며진단은접는다.②는밀도,③은직접편집·검증정보접근손실. 기존유효승인을불필요하게반복하지않음|
|시각체계|①현재중성role정리 ②전체중복CSS일괄재작성 ③새팔레트/테마|**①**. 실제역할과cascade근거로만수정.②는조건별값/상태퇴행범위,③은브랜드교체근거없음. token수감소자체가목표아님|
|입력/복구|①제출문맥+입력revision/기존request조회 ②요청중전체잠금 ③성공후전부reset/unknown재제출|완료된**①보존**.②는대기중편집막음,③은새의도유실/중복비용위험. 새공용프레임워크불필요|

작은 오류 수정에는 억지 대안을 늘리지 않는다. 본질적인 구조 변경이 필요하면 대상 문제ID·기존과업 실패·와이어/작동prototype·대안의 focus/저장 영향부터 설명하고 그 부분만 범위를 조정한다.

## F. 상세 설계와 파일 경계

시각 기준은 E6 한 벌을 링크하며 PRODUCT.md/DESIGN.md를 새로 만들어 경쟁 기준을 두지 않는다. 외부 참조는 Descript의공통시간축,Frame.io의자산/플레이어인접,Runway의조용한prompt shell만 차용한다. 내부editor직접관찰/Refero캡처/공식설명을구분한 기존REFERENCE-LOCK을 따른다. 경쟁사동일HEX·수치·동기비교를추정하지않는다.

|역할/컴포넌트|고정 또는 조사 범위|불변 계약 / 예상 파일|
|---|---|---|
|색·표면·경계|`--ui-canvas #101010`,panel#1B1B1B,raised#242424,hover#303030;strong#F4F4F2,body#DEDEDB,muted#BDBDBB;line#383838/control#858585;selected#2A2A28/marker#D8D8D2;focus#E4DDBE;error#FFB49D|장식divider와필수control경계구분. 승인중립+기호/말,색만사용금지. 새색없음. `studio.css`의실제active선언부터|
|타입·숫자|현행meta/item/body/section/context/title/display=12/13/14/16/18/20/24px×앱배율,400/500/600,기존line-height역할;한국어systemfont,tabular timecode|일괄semibold/새폰트/글자축소금지. 앱배율중복계산금지. label과metadata역할정리때만해당selector변경|
|간격·형태·layer·motion|4/8/12/16/24/32px역할,clip4/control6/panel8/dialog12px;기존shadow/backdrop,120ms/easing|표준정답이아닌현행값. 광학예외실측후명시;passive그룹은조건부만. focus즉시표시,reducedmotion과의도적미디어재생구분|
|장면/비교/검토|`.lt-scene-context`,rail/Take state,comparison contain,review result/editor|현재헤더+36px보존,편집선택/재생장면/승인분리,F07보존. `index.html`,`studio.css`;mediaJS는원칙읽기전용|
|기획·모델·승인|S03–05선택상태·plan/proposal/receipt/action projection|모델명/불가이유/범위/가격은유지,rawID/trace는details,없는버튼금지. `index.html`표현층,기존server source of truth불변|
|저장·상태복구|두폼revisionguard,reviewdraft,unknown/pending/committed-refresh-failure|새mutation경로없음;기존request를조회하고새초안보존. `index.html`필요부분+관련`tests`;DB/원장수정금지|
|시간편집·출력|공통x축/비례clip/실파형/playhead,caption/audio/trim/version|실제데이터/시간도메인보존;정밀입력은내부scroll. `studio-media.js`,renderer/Store는근거있는기능결함없으면변경하지않음|
|제품 표시명|현재 페이지 title/header, 실행 안내·README 및 앞으로의 사용자용 문서 Aethon 전환|`index.html:1,13`, `app.py:1015`, `README.md:1,91`와 관련 표시 assertions. 아래 호환 식별자와 과거 증거는 변경하지 않음|

컴포넌트별 행동/데이터 상태는 C의 공통축과 조합해 기록한다. 메뉴/dialog는 native동작·열림/닫힘/포커스복귀,긴한글/비분리문자/파일명/숫자·단위를 포함한다. 현재언어·단일dark방향을 유지하며 lightmode,drag,undo과금환급 등 없는 기능을 추가하지 않는다.

**DP26-11 이름 전환의 경계:** 위 네 파일과 `tests`의 정적 검색으로 사용자 표시와 내부 식별자를 먼저 구분했다. `LoretuneMedia` 전역과 script IDs, `loretune.py` import/패키지 이름, `X-Loretune-Token`, IndexedDB `loretune-recovery`, sessionStorage `loretune-pending`, 검토·의견·채팅·brief·receipt 저장 키와 테스트 fixture 환경변수는 호환 계약이므로 유지한다. `/Users/leesungmin/Desktop/Loretune`, 기존 URL·도메인·provider 설정, DB키/파일·asset명도 유지한다. 원본 사용자 명세·historical reports/screenshots는 치환하지 않는다. 현재 문서에는 필요할 때 ‘Aethon(기존 프로젝트 경로: Loretune)’으로 설명한다. 미확인 metadata는 구현 직전 해당 배포/설정 파일의 존재와 의존성을 확인하고, 없는 manifest를 새로 만들지 않는다. 합격 조건은 title/header/현행 안내의 Aethon 일치, 기존 저장 초안·pending request의 읽기/복구와 media 전역·HTTP 계약 유지, 같은 조건에서 헤더 줄바꿈/높이·키보드 진입 퇴행 없음이다. 전역 검색 결과0은 목표가 아니다.

## G. 실행 순서·의존성·한 번의 변경 범위

|단계|문제 연결·실제 작업|진입/산출·다음 단계 조건|
|---|---|---|
|B0 **계획 정합화·설명 완료**|입력전체읽기,현재코드/명세/스킬/증거정합화,이통합계획을부모대화에서설명할수있게반환|제품소스0변경. 부모가설명한후기존허용범위진행. 독립현재화면검토결과는DP목록에근거와함께합치고자동전면수정안으로쓰지않음|
|B0a **완료: 제품 표시명**|DP11. 현재 표시·metadata·안내/관련 tests inventory를 닫고 Aethon으로 최소 치환. 내부 호환 계약과 원본·이력 유지|구현 전 baseline hash 확인. 기존 저장 키/인증 header/import/미디어 전역 불변, 표시와 재개 회귀, 1920/1280 헤더 비교. 새 로고/도메인/팔레트 없음|
|B1 **대표 상태 표본 완료**|DP04/07/09. S01–12의기존테스트/최신화면matrix완성;새캡처는미표본핵심경로에한정. 기획→모델→승인/불가→결과/복구→검토→출력경로의다음행동/상태정확성확인|현재헤더8쌍을반복촬영해진척으로세지않음. 증거로확정한finding만ID/심각도/원인/합격조건추가. 결함없으면해당구현skip|
|B2 **신규 재현 결함 없음·변경 생략**|DP07및B1의P0/P1/P2재현. 모호한문구/막힌다음행동/입력보존/접근성의최소핸들러·표현patch|반례→최소수정→대조군→영향회귀. 제안/검토/승인/실행/회수각상태를서버값으로표시. 권한·비용검증을약화하지않음|
|B3 **관측·현재 유지**|DP06. 대표S07검토/승인상태와S05제작카드에서기본행동·보조행동·수동정보를관찰해필요한그룹/여백/label정리|먼저한대표상태의정확한selector·before/합격조건을설명. 값보존cleanup만무한반복하지않되근거없는테두리제거도금지. 구조변경필요시E대안검토후그범위만조정|
|B4 **computed 표본 확인·추가 변경 생략**|DP05. B2/B3에서실제쓰는color/font/spacing/radius/state mapping을공통role로정리;같은컴포넌트의관련화면에확대|activecomputed를기록. 값보존변경과의도된시각변경을별도diff/검증. 덮어쓴낡은규칙을지우려면전사용처/조건을확인;단순grep총수목표없음|
|B5 **격리 로컬 대표 여정 완료**|선택한model상태→합성계획/허용→fake진행/회수→Take검토→정밀음악/자막→로컬출력/재개,영향받은부정경로|격리fixture/현재server로위험에맞게한대표여정. 외부media는fake명시,render는실제fileprobe. 변경영향밖의유료/12조합은제외. 같은빌드독립검토후freeze|
|B6 **완료·후속 감사에 소스 고정**|DP08. README입구·이PLAN상태/issue/evidence 갱신,디자인소유문서는담당자에게정확한수정요청|전후/실검사/미검증/외부gate/소스hash·cleanup. 점수없이종료조건판정. 알려진결함없이새로운장식pass를자동추가하지않음|

통합 담당은 제품 코드의 유일 writer다. 디자인/접근성/계약 검토는 기존 독립 세션의 읽기 전용 결과를 활용하며 같은 파일을 병렬 편집하지 않는다. 아직 시작하지 않은 새 CLI/서브에이전트 수를 성과로 세지 않는다. 독립평가가필요한pass는stabletarget을먼저고정하고서로의결론/검출결과를선행공유하지않는다. 이번은기존근거를정합화한계획이지새로운unanchoredcritique수행이아니다.

## H. 검증 설계·통과와 중단 조건

**같은 조건 캡처:** 현재 E1 allowlist인 합성작품1개/시험영상2·PNG1·WAV1 총1,066,575bytes,project fingerprint `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`를 기준으로 한다. 원본은읽기전용,실행은격리DB. viewport1920×1080/1280×900,DPR1,앱100%,같은장면/Take/trim/음원/자막/승인·선택,paused frame(선택1초,sequence편집0.5/원본0.75초)을 고정한다. 다른상태비교는상태명을명시한다. 앱150/200%와실제browser200/400%는별도다.

- **순수 시각 위험:** 실제served HTML/CSS/mediaJS hash,document/panel 치수,contain영상,시간축원점,대상computed색·font·크기,저장이미지픽셀확인. 현재같은8셀 영상높이431.91/364.91/378.98/311.98(1920),251.91/184.91/257.70/190.70(1280)을 비교 기준으로 보존한다. 이를새절대최소표준으로하지않으며감소가필요하면이유·대안을설명한다. nativecontrols/동적pixels를전체zero-diff로채점하지않는다.
- **흐름/비동기 위험:** 실제controller를쓰는기존NodeVM+controlledfetch로확정거절/unknown/지연성공/새입력/동일내용재편집/A→B→A/취소/더블클릭을검사. F07/DP01/FQ/DM기존guards는보존. 브라우저대역은frontend시험,DB저장성공증거아님.
- **생산/권한 위험:** plans/actions/grants/rights/price/version/receipt의기존contracttests,모델교체중job보존,unknown자동재제출0. fakeHTTP를live로부르지않는다. UI편집만으로provider/gate코드를바꾸지않는다.
- **미디어/출력 위험:** 시간·trim·순서·자막·음원과프레임양자화의기존실FFmpegfixture회귀. B5에서실제export를한다면격리데이터에만저장하고manifest/probe/재개결과를남긴다. 합성출력을생성모델성공으로표시하지않는다.
- **접근성:** 영향selector의label/name/role,Tab/Enter/Space/Escape/focus복귀/전체target노출,내부scroll끝,긴문자/앱배율/대비/forced-colors/reducedmotion을가능환경에서확인. WCAG와제품36/40/44px목표를분리한다. forced-colors·실zoom·screenreader·IME가실행불가면not-run과영향을기록하고대체측정을동일검증이라하지않는다.
- **코드·전체 회귀:** 현재350개(330비HTTP+20HTTP 한 실행)가최신실행기준. 소스변경마다관련반례/회귀·JS구문/Python필요검사후최종고정점전체회귀1회. HTTP20은환경허용시별도실행·분모기록;과거20을더해350을실행했다고쓰지않는다. 새테스트는위험의반례를검증하며선언을그대로반복하지않는다. 이번검증결과와정확한분모는E8참조.
- **실사용·성능:** 사람참가자시험없음. 과업성공률/혼란/속도개선은가설. 유효측정없는성능최적화는하지않는다. 실제사용자평가는후속계획이며이번완료를위해새고객모집/데이터전송을요구하지않는다.

**범위 완료:** 발견된in-scope재현결함이수리되고수용조건+영향회귀가통과,핵심S01–12상태coverage가성공/과거/미검증/외부차단으로빠짐없이표시,최종소스·화면·근거가같은빌드로연결되면종료한다. 새로운품질점수/90목표/경쟁사동등성/전체WCAG나제품출시완료를만들지않는다. 남는실행제약을해결된것처럼숨기지않는다.

**즉시 멈출 조건:** 기준source/fixture불일치,다른writer변경,새recipient/실고객자료/키·비용필요,정식도구거절,unknown외부작업. 해당행동만중단하고명확한사유·이미완료·미실행/불명상태를보고한다. 불필요한자동재시도/다른경로우회없음. 독립로컬문서·소스검토는가능범위계속한다.

**보존/롤백:** 배치직전수정대상snapshot/hash와diff보존. 승인·자산·비용원장/원본명세변경없음. rollback은그배치diff만대조하여역적용하고후속사용자변경과충돌하면멈춘다. reset/stash/commit/전체파일덮어쓰기/원본DB복원금지. 시작한임시서버는stop방법·포트·종료를기록하고검증공간을닫는다. 실제서버POST없는검사와격리fixture쓰기검사를구별한다.

## I. 스킬·도구 적용 장부와 한계

|도구|실제로 읽고/수행한 것|이 계획에 적용 / 실행하지 않은 것|
|---|---|---|
|Hallmark **2.0.0** `/Users/leesungmin/.agents/skills/hallmark/SKILL.md`|이번SKILL전체/redesign/app·Harnesses읽기. E5의정적sloplint는이전실제실행9FAIL/73REFLEX/15WARN|기존wiring/brand보존,appscope,control상태·역할token. 숫자는분류전후보. 이번renderlint·새lint실행없음,fullHallmark감사완료주장없음|
|Impeccable **4.7.1** `/Users/leesungmin/.codex/skills/impeccable/SKILL.md`|이번SKILL/shape/operate/audit전체,critique격리규칙부분읽기. 이전contextprobe exit127,설치경로에engine없던기록확인|Operate·과업/상태·근거계획을수동적용. detector/overlay/새context실행없음,자동다운로드안함. 이번표시명편집전craft-floor재독완료. fullcritique나score산출아님|
|Codex CLI|E5의read-only/ephemeral2세션과테스트는역사적실행|이번새read-only/ephemeral Astra 검토는 실행 전 자동승인심사 거절. 소스/계획의 외부모델 전송 승인 근거 부족이 이유이며 재시도0. 역사적2세션과 구분; SDK/API·Library와 별개|
|Library skill/도구|이번공식skill읽기+입력read1회성공,183행전체|입력검토만. helperupload중단은별개;재시도/직접경로전환0. 현재목록의전송도구존재를과거helper회복으로간주하지않음|
|Refero/기타개발MCP|E6 reference lock과부모가제공한독립조사재사용|이번새호출없음. 제품noMCP와개발도구를혼동하지않음. LSP의이전daemon불가를현재새거절로표시하지않고재설정안함|
|Ego Lite/실행기|E1은CLI0.6.0.20·UAChrome154·실localhost검증및종료증거|이번동일승인synthetic경로로 실제served8상태/폼12조건/로컬출력·재개를확인. 공간42와두임시서버종료. 제어중계/보관미확인을localhost페이지외부요청0으로보장하지않음|

스킬 충돌 처리: 사용자·제품 기준이 우선한다. Hallmark의random theme/hero/80단어/중앙고정폭/강제clip/stamp/cleanGit요구를이편집기에기계적적용하지않는다(appscope자체도마케팅규칙을제외). Impeccable의새score/auto-variants/fonts/decorative motion이나darkmode추가를실행하지않는다. shape의인터뷰는이미확정된과업·톤·자료를다시묻는절차로사용하지않는다. 실제critique를후속수행한다면설치본의A/B격리를따르고수동동일맥락검토를공식critique성공이라고하지않는다.

## J. 현재 가능·환경 의존·외부 결정

- **지금 가능:** 계획 설명,독립결과정합,현재source/QA inventory,기존로컬테스트,동일합성범위의필요한실제화면검증과증거있는작은수정. 승인된로컬검증을완료했고현재소스는후속독립감사를위해고정한다.
- **환경별 확인 필요:** 실제zoom/IME/screenreader/다중브라우저/렌더검출엔진. 미설치도구때문에새설치하거나지원되지않는명령을만들지않는다. 사용자가승인한합성프로젝트/Ego/localhost범위외전송이면먼저구체범위를분리한다.
- **디자인·CLI로 해소되지 않음:** FG26-01검색범위의별도기능설계,FG26-02일반프로젝트설정/동의/검증코드,FG26-03실제계정/가격/파일접근·청구검증. 제품모델활성화/새credentials/유료시험/배포는이번계획이허가하지않는다.
- **독립 검토:** 이미 수신된 현재스크린샷/계획 검토는 아래와 같이 반영했다. 추가 읽기 전용 검토가 있을 경우 실제 결과만 병합하며 미수신을 통과로 취급하지 않는다. 기존설계문서ownership은그대로다.
- **이번 수신된 독립 결론:** 새 제품 결함·새 점수는 없고 PL01 문서 입구 불일치와 PL02–05 계획 구체성 보완이다. selected/adopted/approved/playing을 구분하고, 차분한 승인 완료를 CTA 누락으로 판단하지 않는다. 비교 버튼 근접성은 DP26-06b 가설로 유지한다. 추가 결과가 없는 상태에서 새 디자인 pass를 발명하지 않는다.

변경 기록 — 2026-10-26: Library워크플로183행전체를대조하여 A–J통합계획 추가. 독립 PL01–05를 반영하고 명시적으로 요청된 현재 문서 입구2개만 정정했다. 최신 사용자 Aethon 명명/구현 지속 지시를 DP26-11·B0a에 추가했다. 소스/테스트121개,원본명세,역사적QA,DB·자산·키불변. 새테스트/브라우저/외부모델/설치/업로드실행0. 이전계획을아래에보존한다. 계획 설명 후 첫 구현은 B0a 표시명 변경, 이어 B1 coverage→필요한 B2–4→B5–6 검증·인계다. 단순 borderpatch로 곧장 넘어가지 않는다.

---

## K. 후속 사용자 요구 — CC01 구현·실검증과 계획 전용 범위 구분

1. **Claude 문맥·영상 프롬프트:** `chat_runtime.prepare/process_next`, `production_context`, `chat_protocols.handoff`, `fal_dispatch.prepare_tool/data`를 연결해 실제 제공 문맥·최근 대화·정식 설정/곡 예외·version/provenance·선택 모델·도구 prompt를 추적한다. 서버가 저장 문맥을 API에 다시 전달하는 기능이며 영구 모델 기억이 아니다. 기존 `chat_turns`가 project 단위인 점과 최근8개 조회의 순서/session 경계는 독립 감사 대상이다. 합성 대화의 재개/다른 작품 격리/없는 사실/설정 수정→모델 tool_use→정규화 fal payload를 먼저 무과금 fixture로 검증한다. 실제 Claude 시험은 목적/입력hash/count/output상한·원자 예약을 고정한 뒤 기존 승인 범위와 자동심사를 따르며 fal 제출은 fake로 고정한다.
2. **Claude 직접 모션그래픽:** 기존 `renderer.py:58`은 이미지·영상의 trim/contain/concat, 원곡 offset/AAC, 선택형 자막을 출력한다. 객체/layer/keyframe/텍스트 animation 계약은 없다. Claude가 구도·시간·움직임을 직접 작성한 작은 선언형 scene/keyframe과 검증된 로컬 렌더러를 사용하는 안을 우선 검토한다. hand-authored fixture를 Claude 저작으로 부르지 않는다. 임의 모델 생성 code를 unrestricted 실행하거나 새 프레임워크를 설치하지 않는다. 실제 작성 응답·타임라인·중간 프레임·최종 파일이 있어야 해당 E2E 통과다. Remotion/REA는 설치·연결 capability를 확인하기 전 있다고 가정하지 않으며, 사용자 확인대로 CLI에서 노출될 가능성과 부모 도구목록은 구분한다.
3. **모델 지시 편집:** 기존 `propose_timeline_edit`/`local_creation_tools.propose_timeline`은 현재 clip의 Take·trim·duration만 제안한다. `review_timeline`은 사람 승인 후 기존 Store.timeline 경로로 새 버전을 저장하며 `request_render`는 유효한 사람 출력허용과 기존 job을 재사용한다. **컷 순서·자막·음원 offset 변경은 현재 모델 도구 인수에 없고 직접 편집기에는 있다.** 새 mutation layer 대신 기존 proposal의 typed changes를 필요한 범위만 확장하는 안을 감사 후 설명한다. 원본·과거승인 불변, 예외/권리/범위 확인, stale 거절, 중복 idempotency, preview→검토→apply→재승인, 기존 버전복원을 회귀로 검증한다. 영상모델 변경이나 유료 생성은 이 편집 기능의 전제 아님.

08:20:57 UTC Anthropic 원장 readback은 usage가격 $0.0077580, 요청별 micro올림 합계 $0.007764, 미확정양수예약0이다. 청구서 확인이 아니며 다음 실제 호출 전 새 조회/원자 예약이 필요하다. 이번 호출0. 새 CLI 소스검토는 자동심사에서 실행 전 거절됐으므로 REA 확인을 이유로 그 작업을 우회하지 않는다. 도구 노출·schema·연결 확인은 허용된 별도 범위에서 실제 관측 결과만 기록한다.

**Remotion 최신 방향:** 외부 서비스 링크만 추가하는 것이 아니라 구조/개념을 분석해 Aethon 안에서 모델 요청→편집 가능한 motion/timeline→preview→export를 제공하는 목표다. Remotion은 MIT/무제한 재판매 가능으로 가정하지 않는다. 검토자가 전달한 [현재 LICENSE](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md), [v4 조건](https://www.remotion.pro/terms-4-0), [v5 예정 조건](https://www.remotion.dev/docs/terms), [FAQ](https://www.remotion.dev/docs/license/faq), [가격/자격](https://www.remotion.dev/docs/license/pricing)는 다음 단계에서 실제 후보 버전과 대조해야 한다. 적법한 dependency 사용과 독립 작성 렌더러 대안을 구분하며 제3자 notices 제거·소유권 재표시·일괄 소스복제·설치·라이선스 수락/구매는 이 계획으로 허용하지 않는다. 이번 단계는 해당 원문 재조사나 법적 적합성 판정이 아니다.

### K.1 CC01/P2 — 제한된 수정·실제 Claude 검증 완료

**관측:** 첫 요청이 DB에 남아도 9턴 뒤 API 입력에서 빠졌다. [독립 원 반례](../independent-claude-context-prompt-audit-20261026/REPORT-ko.md)는 불변 보존한다. 이 문제는 앱 문맥 누락이며 모델의 영구 기억 문제로 해석하지 않는다. [수정/실검증 보고서](../cc01-context-fix-20261026/REPORT-ko.md)가 현재 결과다. 더 넓었던 직전 K.1 초안은 [보존 사본](../cc01-context-fix-20261026/before/PLAN-K1.md)에 남기며 아래의 실제 구현 범위로 대체한다.

**선택한 알고리즘과 실제 schema:** 기존 `chat_turns`에서 현재 project의 모든 접수 요청을 `ORDER BY rowid`로 읽는다. `session_request_history={schema_version:1, scope:{workspace_id,project_id,conversation:'project-default'}, requests:[{turn_id,sequence,text,source_hash,status}], digest}`를 불변 handoff에 추가한다. 최근8개 완료 user/assistant 대화는 별도 유지한다. assistant 답변은 이 사용자 요청 원장에 넣지 않는다. source_hash는 원문의 UTF-8 SHA256, digest는 기존 canonical JSON fingerprint다. queued 이후 원본행 변경이 과거 handoff를 바꾸지 않는다.

**정정·해제·조건 처리:** 자연어 원문과 순서를 보존하고 이전 요청을 물리적으로 삭제/자동 비활성화하지 않는다. 명시적 정정/해제의 target/scope를 해석하도록 모델에 지시하되, 인용·조건문을 무조건 실행 명령으로 만들지 않는다. 모호하면 확인하도록 한다. 모든 발화를 canonical ontology로 승격하거나 `constraints[]`를 자동 확정하지 않는다. 승인 사실은 현재 ontology 버전/출처와 기존 approval 서비스가 소유한다. 실제 Claude의 release/quote/conditional/restart 표본은 확인했으나 모든 의미 해석을 보장하지 않는다.

**범위/격리:** workspace/project 한정이며 독립 `session_id`는 지원하지 않는다. 새 session UI/DB migration/제약관리 API를 추가하지 않았다. 모델 교체·같은 작품의 새 독립 대화 기능을 이 수정의 완료 항목으로 부풀리지 않는다. 새 대화 세션 설계는 별도 결정이다.

**대안:** 최근 N을 단순 확대하면 경계에서 다시 누락되므로 제외. 자동 LLM 요약/active constraint 추출은 손실·추가과금·승인사실 혼동 때문에 이번 수리에서 제외. 새 graph/session framework는 범위 초과. 원문 보존+명시적 한도가 작은 수정으로 원 반례와 재개를 재현 가능하게 한다.

**실제 파일/안전 경계:** `chat_runtime.py`(요청 원장/채팅 transport), `chat_models.py`(원문·상태·승인/오디오 의미), `anthropic_ontology.py`(검증된 최대byte 설정) 3제품파일. UI/app/protocol/media/approval/renderer는 변경하지 않았다. 기본 추출12KB는 유지하고 채팅만64KB. token count/원자 예약/실행직전 검사는 그대로이며 한도 초과는 Messages 전에 중단한다. 조용한 이력 삭제/fallback/retry0.

**완료 수용 증거:** 원9턴 반례 FAIL→PASS; 새 요청이력7개/전송1개 추가; 최종358/358(338비HTTP+20HTTP) 한 실행. 최초sandbox HTTP20미실행 로그와 정식권한 전체통과 로그를 모두 보존. last8 정상·Store재개·원문순서·project격리·cancelled처리상태·assistant비승격·queued고정·count초과Messages0·별도session미지원 검증. 관련48/transport12는 전체에 포함되므로 합산하지 않는다.

**실제 Claude:** 새 합성 A/B만 사용. 4logicalcase(9턴밖 금지/명시해제/최신canonical과재개/다른작품격리)에서10Messages를 완료했다. 실제 모델이 작성한 프롬프트2개는 승인검사 후 선택Kling2.5Turbo의 정확한 fakefalpayload까지 연결했다. 원곡/승인종류 설명오류를 기록하고 지침보강 후 조회전용2case/4Messages로 좁게 재검증했다. 총14Messages/count14,최대입력14,016(상한16,384),출력상한8,192. [공식 가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview)재확인,이번$0.0147338·누적$0.0224918 usage계산,보수원장$0.022503,invoice미확인. stage$0.10/사용자이번$1/누적$50 아래이며추가호출중단. 실제fal0,모션저작0. 모델언어이해 전체품질이나실제영상E2E통과아님.

**정리/남은 것:** live에는listener/worker0,실행종료,공유DB수정0. 합성fixture와원응답/도구receipt/hash/원장을보존. UI는이전고정본과동일하여이번browser재시험없음. 길어진요청은한도에서명확히중단하므로무한기억/자동요약기능아님. 독립session·일반모순해결·OpenAI/Grok실품질·fal403/수집은미완료또는별도livegate다. 신규이질데이터수집·ontology진화·Blender모델화는계획만유지한다.

**CLI/REA 상태:** 등록 metadata의 `rea enabled=true/stdio`와 실제 tools/schema/분석 성공을 구분한다. 이전 거절된 private source-review, Library 쓰기, 새 source 전달은 재시도하지 않았다. 이번 실제시험은 승인된 로컬 실행기와 공식 Anthropic 인증 경로만 사용했다.

**CC02/P2 — 후속 경계 수정 완료:** count 본문65,529bytes와 최종 Messages65,549bytes 차이 때문에 후자만 로컬 거절되던 반례다. transport의 동일 UTF-8 직렬화/크기 검사를 `encode_body`로 추출하고, Anthropic adapter의 순수 preflight를 매 round의 count 이전에 실행한다. 알려진 미전송은 `blocked_before_message`/해당 예약0/새 명시 요청 가능, 실제 Messages timeout은 `outcome_unknown`/예약 유지/새 enqueue 차단 그대로다. count timeout은 Messages 미시도와 구분하고 자동 retry0. 과거 unknown 원장을 일괄 해제하지 않는다. 제품 변경은 `chat_runtime.py`와 `anthropic_ontology.py`, 새 테스트는 `tests/test_chat_preflight.py`7개다. 정확한상한·1byte초과·원반례·count실패·Messages불명·다른예약보존·후속round거절시기존usage/도구결과보존을 검증했다. [전후 재현/회귀](../cc02-preflight-fix-20261026/REPORT-ko.md). 이 수정은 더 큰 본문을 허용하거나 이력을 자르지 않는다.

### K.2 새 정보에 따른 온톨로지 자동 정리·진화 — CC01 이후의 별도 묶음

사용자 최신 요구는 새 정보가 들어올 때 시스템이 규칙에 따라 분류·개체/관계 추출·중복/충돌 검사·버전 변경안을 스스로 만드는 것이다. 자동으로 모든 말을 정식 사실로 확정하거나 스키마를 마음대로 확장한다는 뜻으로 구현하지 않는다. **CC01을 첫 구현 묶음으로 유지**하고 이 연구/확장이 첫 수정의 시작을 지연하지 않도록 분리한다. 현재는 계획만 갱신하며 주요 코드 변경은 설명 이후다.

**재사용할 실제 코드:** `ontology.py`의 TYPES/RELATIONS·안정ID·관계 endpoint/중복ID/파생cycle 검증·scope별proposal/version/apply/rollback, `anthropic_ontology.py`의schema구조화 추출·exact source span·unknown/conflict 요구, `project_ontology.py`의실제객체계보/샷bind/관계포함impact, `local_creation_tools.propose_memory`의현재작품출처·revision·후보작성. 승인권한/원자적Store경로는보존한다. 현재모델변경제안은character/place/style개체위주이며자동identity-resolution·주장별scope/철회·schema진화전체를이미지원한다고하지않는다.

**방법론의 역할과 연구 대기점:** 제작 과업의 competency questions로 필요한 개념/관계를 먼저 정한다(“이 샷에서 누가 어떤 예외 의상을 입는가?”,“이 사실의 수정이 어느 승인 샷/출력에 영향을 주는가?”). 기존 typed schema를 executable constraint로 사용해 shape validation 원칙을 적용하되 SHACL/OWL엔진 도입을 전제하지 않는다. 기존 provenance 패턴(PROV의entity/activity/agent/derivation 참고), scoped claims와 incremental/versioned change-set, 인간 검토 중심 entity resolution을 조합하는 안이다. 새 방법론의 공식1차근거·영상제작적합성은담당연구자의결과를받아확정한다. 아직 연구완료·표준준수라고기록하지않으며그래프DB나새검색/모델공급자를추가하지않는다.

**유한 파이프라인:** 허용된입력등록→불변sourceID/hash/version/출처종류→①대화요청②shared/IP사실후보③곡/샷한시예외④추론⑤인용/불확실/권한밖으로분류→기존ID와연결후보/개체·관계추출→schema/source/type/scope/time검증→정확중복no-op/동일성후보/상충주장보존→의존대상impact→버전변경안→검토/허용된적용→새canonicalrevision/재현manifest. 파일시스템전체자동수집이나실제프로젝트자료의Anthropic자동전송은현재승인범위가아니다. 합성시험을먼저사용한다.

|정보 종류|자동 처리 가능 범위|확정/적용 경계|
|---|---|---|
|세션 지시·금지·일회요청|K.1의대화scope/request provenance에보존·분류|IP사실로승격금지. 명시정정/해제와후보추론구분|
|새 IP 사실·관계|출처확인·추출·형식검증·변경안·영향목록 작성|기존사람검토/승인서비스로적용. 저장된유효허용범위를재사용할수있는경우에도scope/version재검사|
|곡/샷 한정 예외|명시scope/유효범위를별도claim으로연결|global값교체금지. 적용끝/철회가원래공식값을삭제하지않음|
|추론·모호한 동일성·충돌|inferred/unknown·복수source·merge후보 유지|modelconfidence가truth/권한아님. 라벨이같다는이유만으로합치지않음|
|정확한 중복 입력|같은scope/sourcehash/ruleversion의입력은기존결과반환|다른source의같은주장은추가근거이므로출처를버리지않음|
|철회/정정|기존claim에supersedes/retracts와source를연결·영향분석|과거승인/출력스냅샷보존. 삭제/tombstone도새버전,몰래과거덮어쓰기금지|
|새 개체유형·관계·제약 제안|지원불가사유와schema-change후보 기록|LLM이스키마/validator/권한코드를직접수정하지않음. rule version변경은별도설계·migration/회귀검토|

**최소 계약:** 기존entity graph를당장전면재작성하지않고필요한claim/change-set에 `source_id/source_version/source_hash/exact_span`, `entity_id/relation_id`, `scope{project,conversation?,song?,shot?}`, `assertion_kind`, `status`, `supersedes/retracts`, `base_ontology_revision`, `rule_version`, `model/prompt_version`, `input_hash`를명시한다. 결측scope를global로추정하지않는다. provenance는모델의설명문이아니라서버가검증하는원입력좌표다. 권리/승인/job와실제asset계보는읽기전용투영이며모델서술로변조할수없다.

**규칙 기준 초안:** identity는label이아닌stableID/명시source연결을우선;동명이인/다른작품은분리. 새정보가자동으로옛승인보다옳다고보지않음. 명시적저자정정과동일scope/target이있을때교체안을만들며그외는병존충돌. 시간범위/샷한정예외는globalfact와함께유효성판정. unsupported/dangling/type/cycle/exactspan위반은적용차단. 무해한추출/중복판정과공유사실적용권한을분리. 모든결과는사용자결정에필요한요약/영향을보여주고hash/내부graph는진단에둔다.

**구현 순서:** O1 기존schema/validator와과업질문의규칙표·합성fixture를고정 → O2 source/checksum/version과분류·중복·충돌변경안 최소계약 → O3 기존proposal/apply/rollback·shotimpact와연결 → O4 작은실Claude품질시험. CC01회귀를먼저닫으며순서/자막/음원편집도구확장과같은파일을동시쓰기하지않는다. 자기평가prompt만추가해서자동진화완료라고하지않는다.

**합격 기준:** 동일입력재수신변경0/중복과금0;같은이름다른인물·작품분리;같은개체새의상은새인물로복제안함;reference의style/identity역할보존;두상충source와unknown유지;일회예외의scope종료후global불변;정정/철회에과거version·출력재현불변;근거없는entity/edge/권한승격거부;stale동시제안원자거부;한샷변경의실의존샷만impact;관계변경도impact;ruleversion변경후재처리idempotency;도구실패/모델truncation/토큰한도에서canonical변경0. 자동검증과실제Claude의의미분류/동일성품질을별도판정한다. 이미passing인validator회귀를새실제품질통과로합산하지않는다.

기존$0.11시험안/전체$50원장을이확장에따라자동증액하지않는다. 연구후대표합성case를앞선4turn안에겹쳐측정할수있는지먼저판단하고,추가실시험이필요하면목적·횟수·입출력상한·예약을별도로제시한다. 이번외부호출/키조회/새설치/DB변경0.

### K.3 정형·반정형·비정형 입력 — 사용자 명시 PLAN ONLY

최신지시에따라 K.2 자동진화와이절의신규수집/온톨로지화는**계획만**진행한다. DB/schema migration, ingestion도구설치, 실제자료수집/외부전송, canonical자동적용은하지않는다. 완료된UI/회귀를되돌리지않으며CC01의제한된수정/시험완료는K.1에별도기록한다. 연구담당자의공식방법론/멀티모달설계를받아아래안의채택·제외근거를보완하며이미연구완료라고쓰지않는다.

**데이터층 구분:** ①원본 저장(source object/version/hash/권한·수신시각) ②추출물(text/table/record/transcript/frame와추출기version) ③근거(source의row/column/page/bbox/offset/timecode) ④주장(claim,scope,유효시점,asserted/inferred/unknown,충돌) ⑤개체·관계(stableID,type,identity후보) ⑥검증·변경안·검토·승인version ⑦검색projection/embedding. 벡터chunk는⑦의찾기도구이며정식ontology나truth가아니다. 원본/추출/claim/canon을같은테이블blob으로취급하지않고기존단순Store와파일저장에필요한경계부터설계한다.

|입력|추출·매핑 계획|근거·불확실성·중단 경계|
|---|---|---|
|정형 CSV/XLSX/선택 DB records|사용자선택표/열/관계키의schema확인→타입/단위/date/null검증→행별claim→기존개체매핑|source version+sheet/table+row key+column. 열명만으로global사실확정금지,단위/동명이인/키충돌은제안. DB연결·계정권한은별도범위|
|반정형 JSON/XML/YAML/API response|명시허용schema/parser→path·record boundary→nested관계/유효시점매핑|JSONpointer/XPath등원위치와원문hash. 중복key/schema drift/unknown필드기록;코드·태그·원격include실행안함|
|비정형 문서/메모/대화/PDF|텍스트추출→필요시OCR후검토→문장/단락claim·개체/관계후보|page/span/bbox. OCR누락/표오독을모델확신으로감추지않음. 인용문/가정/사용자명령/정식설정후보를구분|
|이미지/영상/음원|원본메타·권리→허용된frame/time window나transcript→시각/음성관측claim|frame/timecode/channel+추출모델version. 보이는의상은관측이고인물정체성/세계관사실은별도근거필요. 자동외부업로드·임의얼굴동일인추정·전곡전사승인으로확대금지|

모든입력은공통source/claim계약으로연결하되추출방법·근거좌표·오류종류는형식별로유지한다. 매핑template은schema fingerprint와rule version에고정하고유사파일명이같은문서/개체라는근거로쓰지않는다. 중복내용다른출처는근거를모으고,같은출처의정정/삭제는claim철회와영향분석으로추적한다. 처리실패시원본은보존하고partial extraction/unknown을표시하며없는사실을채우지않는다.

**방법론 후보의 구체 역할:** competency questions와제작도메인패턴으로필요한개념결정;schema mapping/형식별validation으로입력정규화;source-centric claim/provenance와incremental change-set으로상충·시점·철회관리;stableID/entity-resolution후보로교차형식연결;인간검토와semantic/structural test 분리. 특정GraphDB/OWL/벡터DB/새LLM을이단계의전제로선택하지않는다. 실제사용자형식/크기/권한·반복수집필요를확인한뒤1–2형식의최소MVP범위를정하는후속계획이필요하며“모든형식지원완료”를약속하지않는다.

**사전 수용 사례:** 같은인물이CSV/문서/이미지에나타나도근거없이자동병합하지않기;곡한정의상이IP기본값을덮지않기;OCR불확실값unknown유지;동일파일재수신멱등;새source버전철회/재처리;중복claim다중근거보존;정형외래키와문서관계충돌표시;단위/date오독차단;추출기/rule변경재현;다른project/권한없는source격리;새사실후보가승인전렌더설정을바꾸지않기. raw bytes→근거좌표→claim→entity/relation→approved version→affected shot/export를왕복추적할수있어야한다.

#### K.3 연구 근거와 단계 확정 — 구현하지 않음

부모가 전달하고 사용자에게 설명한 연구를 적용한다. 이번 통합 세션이 아래 문서를 새로 조사하거나 관련 엔진을 실행한 것은 아니다.

- [Stanford Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101-noy-mcguinness.html): competency questions로 영상 제작에서 답해야 할 질문·개념·관계의 범위를 고정한다.
- [R2RML](https://www.w3.org/TR/r2rml/) / [RML과 R2RML](https://rml.io/docs/rml/rmlvsr2rml/): 원본 필드/경로를 개념·관계에 매핑하는 접근을 참고한다. RDF 엔진 도입이나 해당 표준 구현 완료를 뜻하지 않는다.
- [SHACL](https://www.w3.org/TR/shacl/): 타입·관계·수량·필수값의 결정적 제약검사 원칙을 참고한다. 현재 Python validator를 SHACL 준수 구현이라고 부르지 않는다.
- [PROV-DM](https://www.w3.org/TR/prov-dm/): 원본·추출·모델 제안·인간 검토·변환의 출처와 활동/행위자를 구분한다. CSVW의 typed columns, JSON Pointer와 Web Annotation의 원위치/영역/시각 anchor 개념은 형식별 근거 설계에 적용할 연구 항목이다.

**수정된 공통 흐름:** 원본 불변 버전(보존기한·삭제 정책 포함) → 형식 parser → evidence fragment → candidate claim → entity resolution/scope → 결정적 validation → 위험별 자동 처리/승인 → 원자적 새 version. 불변은 기존 버전을 조용히 덮지 않는다는 뜻이지 삭제 불가·무기한 보존을 뜻하지 않는다. 삭제/철회 시 원본 접근, 파생 추출/검색 index와 주장 유효성의 전파 정책을 별도로 설계한다.

논리 역할은 Source, Fragment, Entity, Claim, ClaimEvidence, Mapping/SchemaVersion, ChangeSet, RequestConstraint로 구분한다. 이는 책임 모델이며 테이블8개나 새 graph DB를 지금 생성한다는 결정이 아니다. RequestConstraint는 canonical fact와 분리한다. source authority·extraction confidence·approval·conflict는 서로 다른 축이며 하나의점수로합치지않는다. embedding 유사도만으로개체를병합하지않는다. 새개체instance추가와새type/relation/schema변경도별도심사다.

**도입 순서 제안:** 1차CSV/JSON/text/text-PDF/DOCX → 2차OCR/image/audio → 이후video시간index. 각형식은supported/partial/unsupported와크기·처리시간·토큰/비용상한을명시한다. 이는구현계획이며현재지원선언이아니다. 새parser/설치/실자료전송을자동승인하지않는다.

**우선순위 예시:** Mina의갈색눈은global사실,scene3의파란렌즈는명시적장면예외로동시에보존한다. 장면예외가hard constraint를자동무효화하지않고충돌은검토한다. 생성이미지에나온색상은관측근거후보이며기존style canon을자동수정하지않는다. provenance/철회/stale revision/project격리검사는모든형식에공통이다. 정확중복no-op등의무해한자동처리와공유승인사실의적용권한을구분한다.

CC01의최소수정·검증이선행이며이추가연구가대기조건이되지않는다. 신규ingestion/ontology진화는PLAN ONLY,실제Claude/fal호출은이번추가에서0이다.

변경 기록 — 2026-10-26 구현 인계: DP11 표시명,350회귀,served8상태,폼12조건,격리 제작·출력/재개·백업/종료 증거를 E8로 추가. 원본/공유데이터와 호환 식별자 보존. 다음 사용자의 세 검증 요구는 K에 계획만 기록했고 독립 감사/부모 설명 전 대규모 구현이나 유료 호출을 시작하지 않았다.

---

## 역사적 계획 — 아래 상태·시점은 당시 기록

### Aethon — 근거 확인 후 작은 묶음으로 진행하는 구현 계획

> 장면 문맥 헤더 묶음 완료 — 2026-10-26 07:14 UTC: 제목+접힌 설명의 높이88→52px,같은8상태 영상높이+36px,전체비HTTP330통과. [실제 서버 전후·키보드/긴 제목/초안 검증 및 한계](../context-header-space-20261026/REPORT-ko.md). 다음 surface/위계 변경은 시작하지 않았으며 아래 이전 계획은 이력으로 보존한다.

> 값 보존 묶음 완료 — 2026-10-26 06:56 UTC: 설명된 파형 배경/선색·timecode font 역할만 적용했다. [구현·330회귀·실제 서버 값/치수 검증](../value-preserving-tokens-20261026/REPORT-ko.md), [다음 공간·위계 계획—미구현](../value-preserving-tokens-20261026/NEXT-SPACE-PLAN-ko.md). 아래 이전 계획/기준선은 당시 이력으로 보존한다. 레이아웃 변경은 아직 하지 않았다.

> 기준선 게이트 완료 — 2026-10-26 06:36 UTC: 첫 수정 이후 현재 소스를 실제 localhost로 제공해 해시를 검증했다. [서버 화면·브라우저 결과와 다음 묶음 제안](../proposal-draft-fix-20261026/served-baseline/REPORT-ko.md): 통제된 두 폼12/12,1920/1280 잠금 화면8개,서버 쓰기0,원본·소스·미디어 불변,공간/임시listener 종료. **시각 소스는 아직 수정하지 않았다.** 아래 구현 전 계획과 이전 진행 문구는 당시 이력이다.

> 진행 이력 — 2026-10-26: 부모 대화에서 계획과 이유를 설명한 뒤 첫 폼 초안 보호 묶음만 적용했다. [구현·검증 인계](../proposal-draft-fix-20261026/REPORT-ko.md): 원6사례 4실패→6통과, 확장 동작38+연결확인1 통과, 비HTTP330통과. 시각 소스 수정·브라우저 기준선 획득은 아직 시작하지 않았다. 아래 내용은 구현 전 수립한 계획을 보존한 것이다.

상태: **설명·순서 체크포인트. 제품 소스 변경 전.** 사용자 최신 요청에 따라 부모 대화에 이 계획과 이유를 먼저 전달한다. 이미 승인된 범위를 매번 재승인받는 절차가 아니라, 문제 확인에서 구현으로 바로 뛰어넘지 않기 위한 순서다. 독립 디자인 검토는 읽기 전용, 제품 코드는 기존 통합 담당 한 명만 수정한다.

## 1. 기준선과 증거

- [baseline.json](baseline.json)의 root source/tests 119개 SHA256을 고정했다. 최신 [preservation-check.json](preservation-check.json)에서 변경 0을 확인한다. Git reset, 사용자 변경 되돌림, 공유 DB 수정은 하지 않는다.
- HTML `07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3`, CSS `a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0`, 미디어 JS `ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`.
- CLI1의 순수 계약 9개, 실행기의 프런트엔드 unittest 3개는 통과했다. CLI2의 FQ01/FQ03 13개는 위 검사의 일부와 중복되므로 합산하지 않는다. 과거 349개(329 비HTTP+20 HTTP 분할실행)를 이번 전수 검사로 표시하지 않는다.
- 최신 소스와 맞는 기존 화면 증거는 격리 replay다. 과거 served 화면과 혼동하지 않는다. 이번에는 새 서버·브라우저·빌드를 실행하지 않았으므로 최신 served-page 검증은 아직 없다.
- [보고서](REPORT-ko.md), [CLI 검토1](CLI-REVIEW-ko.md), [CLI 검토2](HARDEN-CLI-ko.md), [반례 코드](draft-reset-reproduction.cjs), [반례 결과](draft-reset-results.json)를 함께 읽는다.

## 2. 문제, 가설, 제약을 분리

|항목|판정과 근거|사용자 과업 영향 / 원인|이번 범위|
|---|---|---|---|
|폼 응답 후 새 초안 유실|**확정 P2, Node VM**. `index.html:356` 취향 제안, `:375` 로컬 기획 초안. 성공 응답 4경우 유실, 거절 응답 2경우 보존|응답 대기 중 새로 쓴 문장 또는 다른 작품 입력이 지워짐. 성공 후 무조건 `reset()`하며 제출 문맥/입력 버전을 확인하지 않음|첫 구현 묶음. 실제 모델 대화 폼 `#modelChatForm`의 버그라고 확대하지 않음|
|파형색 literal|**소스상 확인된 token 기준 이탈**. `index.html:45` 배경 `#101010`, 선 `#ddd`|현재색/실제 파형 데이터가 잘못됐다는 뜻은 아님. 색상 역할 변경 시 일관성 추적이 어려움|계산된 색을 기록한 뒤 값 보존 token화 후보|
|상세 입력이 미리보기 공간을 과점유|**재측정 필요 가설**. 이전 기본 718×404 / 상세 505×284는 다른 상태의 과거 측정|미디어 판단과 상세 입력 사이 작업 공간 배분 문제일 수 있음|현재 served 소스, 같은 과업/상태로 먼저 확인. 새 결함으로 미리 단정하지 않음|
|수동 컨테이너 경계/글자/아이콘 밀도|**선별 검토 후보**. 기존400/500/600,20/14/12 역할 존재|중요 조작과 수동 정보의 시각적 구분에 영향할 수 있으나 전체 semibold/전체 박스 과다로 단정 불가|확인된 광학/위계 문제만. 일괄 약화·새 아이콘 패키지 금지|
|문맥 검색이 query로 좁혀지지 않음|**구현 범위 차이**. `production_tools.py:70`은 scoped snapshot을 정직하게 반환|큰 프로젝트 검색/토큰 효율은 아직 완성 아님. 범위 밖 데이터 유출을 재현한 것은 아님|후속 별도 계약 계획. 이번 UI 수정에 검색 엔진/임베딩 추가하지 않음|
|일반 프로젝트의 실제 다중모델 실행|**설정·코드·live gate 분리 필요**. 라우터/codec은 존재, runtime은 승인된 synthetic 범위|현재 fixture/특정 합성 시험을 모든 사용자·모델에 일반화할 수 없음|이번 작업에서 guard 해제/실제 연결/키 조회 없음|
|최신 문서入口|**문서 정합성 차이**. README 상단346 vs 최신349 분할실행|오래된 인계를 기준으로 이미 있는 도구를 다시 만들 위험|유지 문서 링크만 갱신 후보. 과거 QA/명세 원문은 보존|

## 3. 첫 구현 묶음 — 두 폼의 새 초안 보존

**목표:** 현재 요청 결과는 처리하되, 그 결과가 이후 작성된 입력이나 다른 작품의 문맥을 지우지 못하게 한다.

|대안|장점|문제 / 선택|
|---|---|---|
|요청 중 모든 입력·작품 이동 잠금|구현 단순|대기 시간을 사용자의 편집 정지로 바꿈. 기존 흐름을 과도하게 제한하므로 제외|
|성공해도 절대 초기화하지 않기|유실 방지|같은 내용이 계속 남아 제출 완료와 다음 입력의 구분이 약해짐. 정상 초기화 동작도 바뀌므로 제외|
|현재 값과 제출값만 비교|작은 변경|A→B→A 문맥 왕복, 수정했다 원래 값으로 돌아온 경우의 입력 이력 구별 부족|
|**제출 문맥+입력 revision/snapshot 보호**|작성과 이동을 허용하고 응답의 적용 범위를 제한|선택. 현재 request/draft controller 패턴을 재사용하고 별도 저장 시스템을 만들지 않음|

예상 수정 범위는 `index.html`의 두 폼 핸들러와 작은 입력 버전/문맥 추적, 관련 `tests/` 회귀다. 정확한 helper 공용화 여부는 기존 controller와 충돌 여부를 확인해 최소 범위로 결정한다. `act/sendRequest`의 request ID, unknown 차단, 기존 요청 조회, 승인/가격/DB 계약을 바꾸지 않는다. 미디어 재생 코드는 손대지 않는다.

통과 조건:

1. 원 반례 6개에서, 새 입력은 성공·거절 모두 보존하고 POST는 각각1회다.
2. 제출 후 수정이 없고 동일 문맥이면 정상 성공 시 기존 초기화 동작을 유지한다.
3. 작품 A→B 및 A→B→A, 입력 수정 후 원문 복귀에도 그 이후 작성 이력을 보존한다. 다른 폼/문맥의 초안을 지우지 않는다.
4. 응답 unknown/네트워크 대역 오류/확정 거절은 초안 보존. unknown 재제출은 기존 guard로 차단하고 기존 request 조회만 가능하다.
5. double click/중복 이벤트에서 추가 POST 없음. F07 검토 초안과 FQ01–03/DM01–03 기존 회귀 유지.
6. 이후 허용된 실제 브라우저에서 controlled delayed response로 두 폼 확인. native 한글 IME는 VM 성공으로 대체하지 않는다.

첫 묶음은 시각 리브랜딩과 무관하므로 최신 화면 세팅이 없더라도 소스·VM 검증을 시작할 수 있다. 다만 **이 계획 반환 전에는 수정하지 않는다**. 실제 브라우저가 불가하면 코드/VM 완료와 브라우저 미검증을 분리한다.

## 4. 고정 디자인 방향과 후속 작은 묶음

기존 [REFERENCE-LOCK](../design-system-redesign-20261026/REFERENCE-LOCK.md), [SEMANTIC-TOKEN-SPEC](../design-system-redesign-20261026/SEMANTIC-TOKEN-SPEC.md), [방법론 적합표](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md)를 단일 설계 근거로 사용한다. 새 경쟁사 스타일/브랜드색을 만들지 않는다. Runway는 참조이며 공급자 요구가 아니다. 제품의 선택형 chat→서버 승인 도구→fal 미디어와 noMCP 원칙은 유지한다.

|순서|작은 묶음 / 소유|진행 근거 / 완료 조건|
|---|---|---|
|0|계획 설명, 기준선·문제 합의 / 통합 담당+부모|현재 문서 전달. 확정 문제와 가설 구분, 원본 변경0|
|1|초안 유실 수정 / 통합 담당 단독 writer|위 6개 수용 조건, 관련 회귀·정적 검사. 결과를 먼저 보고|
|2|최신 실행 화면과 active computed token 목록 / 통합 담당, 디자인 검토는 read-only|정확한 served hash·CSS viewport·앱배율·상태·fixture를 고정. 비교 가능한 before 캡처 없으면 시각 변경의 개선 주장을 보류|
|3|값 보존 token 정리 / 통합 담당|파형 literal부터. background/stroke/line-height/font/spacing computed 값이 전후 같아야 함. 해당 역할 token이 이미 있으면 재사용; `#ddd`를 비슷한 기존값으로 임의 치환하지 않음. 대규모 CSS 합치기 금지|
|4|입증된 작업 공간·위계 미세 조정 / 통합 담당|미리보기와 상세폼 공간, passive surface, 자주 쓰는 조작과 metadata, 실제 아이콘 정렬만. before에서 문제가 없으면 해당 변경은 생략. 글자 축소·필수 버튼 숨김·새 구조 추가 금지|
|5|회귀·독립 읽기 검토·유지 문서 갱신 / 통합 담당+검토자|새 코드/화면의 실제 결과와 한계를 명시. 원본 연구/이전 점수/감사 수정 금지. 새 점수를 만들지 않음|

시각 범위의 역할 기준: canvas/panel/raised/hover와 text/body/muted, input-border/selected/focus/approval/error를 혼동하지 않는다. passive 경계는 줄일 수 있어도 입력·선택·키보드 focus·승인의 필수 경계는 유지한다. 주요 조작/상태/금액/모델은 계속 보이고 내부 ID·hash는 진단에 둔다. typography의 현행 weight400/500/600을 출발점으로 삼고 모든 글자에 같은 weight를 강제하지 않는다.

## 5. 비교 조건과 사용자 과업 검증

주 기준은 **브라우저 CSS viewport 1920×1080**, 기본 앱 글자배율이다. 모니터 해상도와 구별한다. 1280×900은 보조 회귀, 모바일은 기존 기능 보존만 하고 이번 심층 개선 범위에서 제외한다.

- 같은 합성 프로젝트/장면/Take/trim/자막/음악/승인 상태, 같은 선택/재생 위치로 before/after를 남긴다. 입력이 길고 장면/목록이 많은 상태와 precision 펼침 상태를 포함한다.
- 기본1920에서 document 높이/가로폭, 각 패널 scrollHeight/clientHeight, 실제 영상의 contain-fit 크기, 공유 시간축 원점, 주요 버튼과 내부 스크롤의 접근성을 기록한다. 타임라인과 모든 필수 조작을 유지한다.
- `overflow:hidden`으로 미접근 내용을 감추거나 글자를 작게 만드는 방법은 허용하지 않는다. 제한된 내부 스크롤은 키보드 focus 대상을 드러내야 한다. 앱200%/작은 창에서는 접근 가능한 reflow/스크롤을 허용한다.
- 1280 앱200% Take focus와 긴 이름은 이미 닫힌 이슈다. 새 결함으로 다시 점수화하지 않고 회귀로만 확인한다. 실제 browser200/400%와 앱배율은 별도 항목이다.
- 실제 수행할 과업: 장면 탐색→Take 비교/선택→검토 입력/취소→모델 선택창→미확정/실패 복구→타임라인/자막/음악→로컬 fixture 출력 및 재개. 변경과 무관한 유료 생성이나 사용자 원본은 사용하지 않는다. 모든 단계 전수 반복보다 변경 영향에 맞는 경로를 우선한다.
- 오류 화면은 controlled response임을 표시한다. 확정 실패와 unknown은 구분하고, 연결 장애를 근거 없이 원인으로 쓰지 않는다. 초안 보존과 기존 request 조회, duplicate 방지를 확인한다.
- 실제 고객 시험, cross-browser, screenreader, axe, 실제 zoom, provider, 성능 계측이 수행되지 않으면 그대로 not-run이다. 스크린샷/VM/토큰 산술만으로 대체하지 않는다.

## 6. 도구/스킬의 구체적인 역할

- **Hallmark2.0.0:** app-scope 정적 검출은 후보 목록. 이번 실제 sloplint 실행은 정적9FAIL/73REFLEX/15WARN이며 rendered 검사/독립 디자인팀의 detector 실행이 아니다. 마케팅 hero·80단어·중앙 고정컨테이너·random theme·일괄 overflow clipping/no-wrap·stamp 의무는 Aethon 요구보다 우선하지 않는다. 수치 목표로 코드를 바꾸지 않는다.
- **Impeccable4.7.1:** Operate/harden/audit의 입력 보존·작업 중심·상태 구분을 적용했다. 로컬 엔진 context probe exit127이므로 자동 다운로드하지 않고 문서/소스를 읽는 fallback 사용. 실제 UI 편집 전 해당 craft 지침을 다시 범위에 맞게 확인한다. 새 폰트/장식모션/variant/점수는 만들지 않는다.
- **Codex CLI 두 세션:** 공식 read-only/ephemeral로 요구·계약 검토와 async hardening을 분리. 제품 writer로 쓰지 않았다. 추가 세션 수를 늘리는 것 자체를 진척으로 세지 않는다.
- **LSP MCP:** status에서 daemon unreachable. 설치/설정 변경 없이 AST/기존 테스트로 가능한 부분 완료. 자동 재시도하지 않는다. Refero는 독립 디자인팀이 기존 참조를 검토하므로 중복 조사하지 않는다.

## 7. 회귀·보존·롤백

각 작은 변경 직전 대상 파일 해시/내용을 별도 QA snapshot으로 보존하고 diff를 검토한다. 다른 작성자 변경이 있으면 덮어쓰지 않고 해당 묶음을 멈춰 충돌을 조정한다. 공유 DB/기존 자산/비용 원장에는 손대지 않는다. 롤백은 이 묶음의 파일 단위 변경만 역적용하며 전체 checkout reset/사용자 데이터 삭제는 금지다.

검사는 반례→최소 수정→같은 반례+대조군→영향 회귀→정적 검사 순서다. 제품 변경이 실제 적용된 최종 checkpoint에서 기존 전체 suite는 당시 허용된 로컬 환경으로 수행하되 HTTP listener가 허용되지 않으면 분리해서 blocked로 기록한다. 이번 평가의 9+3과 중복13/내부18를 더해 새 전수 통과 수를 만들지 않는다. 정상 렌더/미디어 생명주기·승인·비용 상태를 변경하지 않았다면 관련 control로 퇴행을 확인하며 새 모델 호출은 하지 않는다.

## 8. 가능한 일과 blocker

**지금 가능:** 이 계획과 반례 검토, 동결된 소스/계약 읽기, 오프라인 회귀. 계획 설명 후 첫 폼 보호 묶음, 값 보존 token 정리안은 외부 API가 필요 없다.

**환경 확인 필요:** 현재-source served 화면·실제 IME/zoom/보조기술/다중엔진. 이전 허가를 임의 확장하거나 거절된 경로로 우회하지 않는다. 새 실행이 차단되면 대상·이유·미실행 여부를 보고하고 독립 오프라인 작업은 계속한다.

**CLI로 해제 불가:** fal 인증/결과권한/실청구, 다른 제공자 계정·live 검증, 일반 사용자 데이터 외부 전송 정책, unavailable Library prepared-upload capability. 시작된 Library helper를 direct upload로 전환하지 않는다. 이번 계획은 키 조회·유료 호출·설치·배포·업로드를 포함하지 않는다.

변경 기록: 2026-10-26 — 최신 사용자 순서 지시와 독립 디자인 검토를 반영한 첫 계획. 제품 source 변경0, 실제 공급자 호출0. 구현 결과가 아니며, 적용/검증 완료 때 별도 이력으로 추가한다.


### K.4 Native motion — 제한된 실제 Claude 저작·수정·로컬 UI 검증 완료, 답변 품질 일부 잔여

> 아래는 구현 전 설명한 선택·수용 계획을 보존한 내용이다. 현행 결과는 상단 후속 기록과 native-motion 보고서가 우선한다.

**목표:** Claude가 한국어 문구/도형/구도/키프레임을 실제 작성하고, Aethon이 검증된 데이터를 자체 로컬 렌더러로 표시·출력한다. Claude가 MP4를 직접 인코딩한다거나 fal이 만든 영상을 모션그래픽이라고 부르지 않는다. 첫 수직 기능은 **4초, 1920×1080, 24fps,96frames, 한글 텍스트+사각형+원**이다. 새 프레임워크/외부 서비스/임의 모델 코드 실행/Remotion 소스 복사는 없다. CC02 수정 후 소스는 다시 고정하고 이 계획 설명 전 모션 구현을 시작하지 않는다.

**현재 실행 환경 확인:** FFmpeg/ffprobe9.0.2,libx264/AAC,drawbox/overlay 존재. drawtext·Pillow/numpy/cairo/skia/Canvas 경로는 현재 Python/프로젝트에 없다. `/usr/bin/swift`6.3.2와 현재 macOS SDK의 CoreText/CoreGraphics/ImageIO/Foundation, `/System/Library/Fonts/AppleSDGothicNeo.ttc`를 확인했다. SDK의 CTLineDraw/CTLineGetImageBounds, rect/ellipse,bitmap/image-output 선언도 직접 확인했다. **컴파일·한글 glyph·프레임 렌더 성공은 아직 미검증**이다. 환경 증거는 [capability readback](implementation/motion-capability-plan-readback.json). Apple 웹 개요는 JS 필요/markdown content-type 미지원으로 본문을 읽지 못했으므로 그 도구 성공을 주장하지 않는다.

**대안과 결정:**

|대안|장점/부담|결정|
|---|---|---|
|기존 FFmpeg filter만 사용|현재 설치 그대로지만 drawtext가 없고 키프레임/text 레이아웃 서비스가 없음|한글 필수 기준을 충족하지 못해 단독안 제외|
|Remotion/React/Chromium dependency|범용 구성·player 생태계가 있지만 현재 미설치, 운영·보안·license 결정 필요|이번 작은 기능의 우회 설치나 fallback으로 사용하지 않음|
|독립 frame evaluator + 설치된 Swift/CoreText/CoreGraphics + FFmpeg|표현 범위는 작고 Mac 전용이지만 모델 데이터만 받고 동일 frame 재현 가능|**우선안. M0 capability gate를 먼저 통과해야 구현 진행.** 실패하면 정확한 dependency/권한 gap을 반환하고 설치하지 않음|

[고정 Remotion 공개 조사](../independent-remotion-public-architecture-20261026/REPORT-ko.md)는 v4.0.538/commit5217b0c…69896의 정적 검토다. frame clock,composition parameters,sequence local time,deterministic render/stitch 책임 분리라는 개념만 참조한다. REA 실행은 거절됐으며 이 계획에서 재시도하지 않는다. Remotion의 코드·license를 Aethon 소유라고 재표시하지 않는다.

**최소 schema v1(제품 제안 한도, 표준이 아님):**
- server가 project/shot stable ID, proposal ID,parent/base revision,source run/call/request ID,scene hash와승인scope를보유. 모델인수는 `shot_id`, `base_motion_revision`, `scene`만 받으며actor/approved/permission/path/endpoint는없다.
- scene: schema_version1,canvas1920×1080,fps24,frame_count72–96(첫시험96),opaque background HEX,layers1–8. layer ID는중복불가,종류text/rect/circle,그리기순서는배열순서로고정.
- 좌표는canvas좌상단 기준. 레이어 표시구간 `[in_frame,out_frame)`;frame은정수. 위치x/y·opacity만animate하며 keyframes≤8/layer,frame엄격증가,값은유한/범위검사. easing은linear/easeInOutCubic 두개,구간밖은clamp. rotation/3D/spring/expression/nesting/externalassets는첫범위밖.
- text는NFC한글/일반문자 최대80자·2줄,서버allowlistfont1개/규정된size. glyph부재·너비넘침은오류로반환하며몰래폰트교체/글자축소하지않는다. circle/rect의크기·색·좌표도한도검사한다. unknownfield,URL,script,NaN/Infinity,과도한canvas/frame/layers는렌더전에거절.
- font는모델의파일경로가아닌 `system-ko-regular` 같은논리ID. 현재OSfont경로/face/hash를서버manifest에고정한다. font는배포물에복사하지않고,다른Mac/OS버전의bit재현은별도gate다.

**데이터·도구·승인·복원:**
1. `propose_motion_scene(shot_id,base_motion_revision,scene)` → 기존production run/normalized tool envelope/Store transaction/idempotency를사용해검토전proposal저장. 기존project JSON에motion proposals/immutableversions/head를작게추가하며새graphDB나별도범용jobengine없음. 정식ontology는변경하지않음.
2. 같은화면에서레이어문구/위치/시간을수정하면같은proposal service로새human-edit출처를남긴다. 모델수정도새버전전체diff를보여주며원본/이전버전을덮지않는다. “원만12frame늦춤” 시험은다른레이어/색/문구변경0을반드시검사한다. 모델의declaredscope를권한으로신뢰하지않는다.
3. 사람검토 hold/reject/approve;승인시currentproject/shot/base revision/canonical context/fontmanifest 재검사. 적용과local candidate render허용범위를명시적으로묶어중복승인클릭을줄일수있되최종출력승인으로확대하지않는다.
4. `request_motion_render(shot_id,motion_revision,grant_id)`는기존jobs에local-motion kind를추가해receipt반환. 기존queued/running/cancel/interrupted/failed/atomicpublish를재사용한다. 같은승인+scene/font/profile hash는기존job반환;취소/실패/불명결과를몰래새job으로재실행하지않는다.
5. 완료된MP4는검증후기존asset/Take등록서비스로새미채택후보를붙인다. 모델출처와scene revision/job/hash를provenance에보존. 기존Take선택/검토·타임라인승인·음악/자막최종render/delivery approval은그대로다. candidate를최종export로잘못분류하지않도록job projection을구분한다.
6. restore는이전scene를새revision으로복원하며이전파일/출력을남긴다. 복원·수정은이전허용을새입력에자동재사용하지않는다. 기존timeline restore도같은방식으로유지.

**프리뷰/인코딩:** 모델코드가아닌직접작성한trusted Swift helper가동일 scene+fontmanifest+frame으로그림을평가한다. 미리보기slider의정확한PNG frame과96frame export가같은평가기능을사용한다. CSS animation을녹화하지않는다. 초기에는정확한프레임still과완료MP4를기존player로보여주며편집중60fps실시간성을약속하지않는다. 전체render는bounded RGBA frame stream→기존FFmpeg/libx264/yuv420p. 임시결과는검증후원자저장,취소시helper/encoder둘다종료·미완성Take0. shell=False,모델인수에실행명령/네트워크/파일경로0,읽을font는serverallowlist만,1render동시성/180초상한을초기안으로측정한다. 네트워크없는helper코드와OS sandbox를동일한보장으로부르지않는다.

**파일 경계:** 새 `motion_scene.py`(schema/evaluator input/version/proposal), `native/motion_frame_renderer.swift`(신뢰된 rasterizer) 후보. 기존 `local_creation_tools.py`, `production_tools.py`, `chat_protocols.py`, `production_context.py`에공통tool/context계약; `app.py`의Store/actions/jobworker/candidate등록과 `renderer.py`의공통인코딩/검증을최소확장. `index.html`에는proposal/layer fields/frame preview/restore/status만추가. 기존media lifecycle JS와provider/fal경로는불필요하게수정하지않는다. 현재approved_shots명칭/기존승인hash를무조건rename하거나실행권한을넓히지않는다.

**순서/수용 기준:**
- **M0 무과금 capability spike:** scratch에서trustedhelper를빌드해“새로운 리듬”+rect/circle 1frame을그린다. glyph누락/실제fontface/bbox/alpha/색·PNG크기를검사. 실행권한/컴파일/font실패시중단하고정확한gap보고. 자동설치없음. 이단계가통과하기전Claude과금0.
- **M1 fixture제품경로:** schema악성/경계·stale/foreign·hold/reject·동일요청·apply/restore/reopen·cancel/restart·디스크/검증실패·원본보존·font변화로승인무효를검사. preview frame과lossless원본frame동일,MP4 decoded는손실압축허용오차를명시한다.
- **M2 실제Claude저작+수정:** 합성brief→실제 tool_use→scene→검토/승인→96frame render→미채택Take→기존음악/자막포함최종output/reopen. 이어“원의진입만12frame늦춰;문구/색/다른레이어유지” 요청. Claude원응답/usage/requestID와scene diff를보존;손수작성한JSON을대체성공으로쓰지않음.
- frame0/12/24/36/48/60/72/84/95의실제decodedframe을검사. 위치·bounds·opacity·한글glyph·지연12frame·unchangedlayers/원본hash·96frames/24fps/1920×1080/4초·최종frame검사. imagehash변화만으로내용준수판정하지않음. 최종음악/자막version은기존manifest와일치해야함.
- 영향tests+전체회귀,1920주화면(1280보조)proposal→preview→approve→candidate→output→reopen을별도syntheticDB로검증. 현재frozenUI를새capture라고재사용하지않음. 실제LLM품질과deterministicvalidator/renderer판정을분리한다.

**소액 실제 시험 계획:** 첫motion create+수정2logicalturn×최대3Messages=6responses. Haiku5.5 입력16,384/출력8,192상한의worst$0.0344064;stage$0.05. 실행전공식가격/계정·원장재확인,공식Anthropic기존메모리인증·합성자료만. 자동retry/fallback0,unknown은예약보존. 현재누적usage$0.0224918/보수원장$0.022503(invoice미확인). 이번단계의추가실Claudehardcap$1와기존총$50를넘지않는다. 이번계획작성의실호출0,설치0,렌더0이다.

### K.5 모델 지시 편집 최소 확장 — 실제 Claude 제안·사람 승인·출력 표본 검증 완료

[기존 EDITING-ADDENDUM](../independent-claude-context-prompt-audit-20261026/EDITING-ADDENDUM.md)대로현행모델도구는Take/trim/duration만제안한다. 직접편집기의순서·자막·오디오offset을모델이이미지원한다고하지않는다.

**E1 범위:** 기존 `propose_timeline_edit`의legacy형식을유지하고별도versioned `propose_timeline_changes` typed commands를같은proposal/apply서비스로정규화한다. (a) `reorder_clips(order)`는현재base timeline의clip occurrence index전체순열만;추가/삭제없음 (b) `set_captions(cues)`는전체교체가명시된순서/비겹침/길이내Unicode cues,누락명령은기존자막보존 (c) `set_audio_offset(audio_version,source_offset_seconds)`는현재선택한같은audio version의원음시작지점만;새음원/볼륨mix/음수delay/외부전송없음. 기존set_clip과조합가능하되최대30commands,동일target중복/상충/알수없는필드는거절한다.

**의미 고정:** clip target은timeline_version+occurrence index이므로같은shot반복사용도명확히구분한다. 컷reorder가자막을자동따라움직인다고가정하지않고,자막은기존절대timeline시각을유지한다. 재배열후필요한자막변경은별도명시proposal로보여준다. audio_offset은원음에서잘라시작하는시간이며타임라인에서새로지연시키는기능이아니다.

**재사용/파일:** `local_creation_tools.py`에서후보timeline을구성→`editing.validate`→기존review_timeline→Store.timeline/save_timeline. `production_tools.py`/`chat_protocols.py`에는엄격schema,`production_context.py`에는현재clip/version/audio/caption targets,UI에는간결한before/afterdiff. 승인/hold/reject,source/rights/hash,stale/context,idempotency를재사용한다. 새버전은기존출력승인을지우고 `request_render`는해당새버전의유효한human grant만쓴다. undo는기존restore_timeline의새버전복원,원본파일삭제0.

**E1 수용:** 색/프레임번호3컷+click-track+한글cue 합성fixture에서실제Claude가“3→1→2순서,지정cue수정,원음시작1초”를공통도구로제안;사람검토후적용→같은renderer출력. 예상diff외변경0,원본/이전출력hash불변,순서/프레임수·cue Unicode/시각·audio offset검증(샘플측정방법명시,기본허용1frame). hold/reject시미변경,stale/다른project/가짜grant차단,동일toolcall/승인/렌더중복방지,복원/restart도검사. 세chat protocol은fake계약으로확인하고실품질은Claude만표기한다.

E1 실제시험은1logicalturn×최대3Messages,worst$0.0172032,stage$0.025제안. M2+E1 합계9Messages,worst$0.0516096,분리stage합계$0.075이며동일이번hardcap$1/누적$50아래. 필요이상횟수를채우지않고실패원인/미완료를보고한다. motionM0실패시독립E1fixture검증은가능하지만sourcefreeze해제후에만진행한다. 이질데이터ingestion/온톨로지자동진화·Blender는계속PLAN ONLY.
