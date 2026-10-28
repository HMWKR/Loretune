# Aethon 현재 디자인 QA와 다음 개선 계획

## 공통 AI 사이드 패널·1차 시연 QA · 2026-10-28

**이번 항목은 진행 중 설계·구현의 합격 기준이며 아직 전체 통과가 아니다.** 음악영상의 작업 완료를 우선하고, 음원 단독/사진 선택/3D 선택 경로와 기존 중성 브랜드·타입·색·토큰을 유지한다. [현행 요구·실행 기록](../qa/codex-workflow-review-20261027/REPORT-ko.md), [대화·권한 계약](CHAT-SESSION-PLAN.md)을 함께 따른다.

|문제 ID·관찰/요구|선택한 방향과 이유|합격 기준·검증 방법|
|---|---|---|
|AGENT-UI-01 · 기존 상담 위치가 stage마다 달라 공통 접근 부재|오른쪽 AI 대화/작업 설정 공간 공유, 기본 AI 열림. 별도 고정 패널을 나란히 추가하는 안보다 중앙 편집 폭을 확보. 현재 구현 중|같은 작품/대화에서 음악·계획·장면·편집출력·모션/3D modal 접근, 토글/재열기·마우스/키보드 너비 조절·재열기 선호 너비·초안/포커스 보존|
|AGENT-TOOLS-02 · 추천/편집 안내와 실제 지원 범위 차이|현재 작품·선택 대상·저장 버전과 지원 도구를 연결하고 상세는 점진 공개|실제 결과를 본 경우와 metadata만 확인한 경우 구분. 미저장 초안·저장 preview·완성 MP4를 구별하고 server diff의 원본/위치/시간 전후가 실제 프레임과 일치|
|AGENT-STATUS-03 · 작업과 작업자 현황 요구|기본에는 현재 작업·진행/완료/실패·다음 행동, 내부 ID는 상세|실제 scoped 상태 재조회와 일치. 인증/참여자/권한 데이터 없는 협업자·접속 현황을 만들지 않음|
|AGENT-REASON-04 / AGENT-PERM-05 · 모델별 설정과 위험한 조작 경계|지원 추론 강도·실효 permission과 적용 범위를 설정에서 표시|unsupported 옵션·stale 설정·실행 중 변경 반례, Full Access 계정 삭제 영구 차단·다른 삭제의 개별 허용·비용/권리/전송/출력 승인 유지|
|DEMO-01 · 화면 성공과 실제 실행 혼동 위험|같은 조건의 실제 화면 조작 녹화와 내부 API/작업/저장/다운로드 증거 연결|리허설/합성 공급자/실제 렌더/실제 모델/실청구 구분, 재생 가능한 녹화·타임코드·오류/복구·재열기. 녹화 편집·배속·생략·무음 여부 공개|

너비 조절은 [WAI APG Window Splitter](https://www.w3.org/WAI/ARIA/apg/patterns/windowsplitter/)의 focusable separator·이름·controls/value 범위·좌우키/Enter와 선택 Home/End를 참고한다. 이 패턴은 기능 예제와 task-force 검토가 미완료라는 공식 한계가 있으므로 문서 참조를 접근성 준수나 실제 조작 통과로 표현하지 않는다. 데스크톱1920×1080 대표 흐름을 먼저 확인하고1280 및 실제 레이아웃 전환점·375px, 긴 한글·긴 이름·200% 확대·로딩·실패·재시도·빈 상태·키보드/포커스를 변경 범위에 맞게 확인한다.

Hallmark2.0 [재검사](../../.omo/evidence/first-demo-20261028/hallmark-recheck/invocation.json)는 render가 실제 실행됐고 FAIL26/REFLEX75/WARN16·exit1로 미통과다. 아래 puppeteer 부재 기록은 이전 실행이다. [HTTP/file://·닫힌 control 분리 검토](../../.omo/evidence/first-demo-20261028/frontend/hallmark-render-triage.json)를 재사용하고 실제 결함·기계적 finding·취향을 구분한다. Impeccable context/detect 실행, 지침 수동 적용과 정식 격리 critique/전체 audit 합격은 별도다. 새 sidebar·추론/권한 UI의 실제 전후 비교와 전체 디자인/접근성·실무자 수용은 남아 있다.

## 현행 증분 QA · S819 · 2026-10-28

[동일 음원·장면의 전후와 실제 동작](../qa/codex-workflow-review-20261027/REPORT-ko.md)을 기준으로 UX-NOTICE-07/UX-IMPORT-06/UX-FOCUS-08/09를 수정했다. 접수는 짧게 접고 실제 진행/완료는 작업 목록에서 보여 준다. 오류·미확정·비용·권리·승인·복구는 유지한다. 기존 브랜드·토큰·기능·원본을 보존했고 새 색/글꼴/모션/의존성은 추가하지 않았다.

1920/1280/375px 편집·출력 화면, 실제 모달·키보드·입력 보존·다운로드·재생·재열기와 summary AX 속성을 점검했다. [캡처 실제 크기와 한계](../qa/codex-workflow-review-20261027/workflow-simplification-20261028/screenshot-inventory.json)는 파일명/전환 직후 치수와 구분한다. 스크린리더 발화·전체 접근성/대비/확대/실무자 평가, 정식 Hallmark/Impeccable 전체 합격은 선언하지 않는다.

다음은 UX-MUSIC-RANGE-10의 구체적인 범위 오류 안내와 기존 전체 화면·상태 목록의 미검증을 이어서 확인한다. [현재 증거·잔여](../qa/codex-workflow-review-20261027/workflow-simplification-20261028/remaining-verified.json)를 우선하며, 보고된 개선이 사용자 시간 절감으로 이어지는지는 실제 과업 평가에서 확인한다. 아래 QA 계획과 원본 참조는 보존한다.

## 현행 실동작·산출물 QA · S813 · 2026-10-28

[S813 보고서](../qa/codex-workflow-review-20261027/REPORT-ko.md)는 일반 상담 선택/예약의 S803 실제 UI와 정점 색 자산·구/신 렌더 계약의 S813을 연결한다. raw 프로파일·지문을 기본 사용자 화면에 드러내지 않고 구현 기준 변경 시 변경안 재저장/복원→재승인 경로와 옛 이미지 보존을 안내한다. 기존 토큰·브랜드·글꼴은 유지했다. 정식 Hallmark/Impeccable critique/audit·점수·전체 접근성 합격은 주장하지 않는다.

실제 UI의 원본 GLB→방향/크기/카메라 편집→Take 검토→음원/한글 자막 출력·재생·재열기를 확인했다. [1920/1280/375px 실제 렌더/넘침](../qa/codex-workflow-review-20261027/paired-assets-20261028/ui/reopened-layouts.json), Escape의 진입 버튼 포커스 복귀와 캡처 직접 검토는 해당 표본이다. 일부 전체 페이지 snapshot/요소 치수는 닫힌 details의 입력을 포함했으므로 실제 보임 여부와 구분했고, 의미 없는 대기/잘못된 작업 선택 시도도 보존했다.

다음 디자인 조사 대상은 **UX-IMPORT-06**(크기 한도 안의 복잡한 GLB 거절 시 복구 행동 불명확), **UX-NOTICE-07**(출력 완료 뒤에도 크게 열린 제출 알림)이다. 후자는 화면 관찰이며 혼란·작업 지연 효과는 사용자 연구 가설이다. [근거/다음 행동](../qa/codex-workflow-review-20261027/paired-assets-20261028/remaining-verified.json)을 따라 진단→대안→계획→구현→같은 조건 검증하며 기존 비용·권리·승인·실패·복구 정보는 결정 시점에 유지한다.

## 현재 대화·색상 QA · S789 · 2026-10-28

[최신 789개 단계](../qa/codex-workflow-review-20261027/REPORT-ko.md)에서 같은 대화의 이전 요청/최근 답변 개수를 기본에 표시하고 전문·hash는 상세로 유지했다. 결합된 현재 요청으로 초안 승인 검사를 수정하고 비용 총 상한의 적용 범위를 ‘이번 요청’으로 명확히 했다. 실제 UI 두 독립 요청·동의·초안 변경 차단·재열기, 같은 검토 상태의 1920/1280/375px 가로 넘침 0을 확인했다. 공급자 응답은 합성이며 전체 접근성/사용자 시험을 뜻하지 않는다.

NATIVE-COLOR-01은 지정 sRGB와 실제 native PNG의 채널 차이를 동일 입력으로 재현해 CGColor 생성식 한 곳을 수정했다. 한글/영문·도형·alpha의 실제 PNG 검사와 수정 후 30초 출력의 배경 표본을 확인했다. 기존 중성 UI 토큰·폰트·레이아웃을 바꾸지 않았고 옛 출력·승인은 보존한다. 정식 Hallmark/Impeccable 전체 critique·audit 통과나 새 디자인 점수는 없다. 모델 이용 가능 안내와 일반 실행 중 모델 예약의 정합성은 명시적 잔여다.

## 현재 상담 흐름 QA 보충 · S774 · 2026-10-28

[최신 구현·검증](../qa/codex-workflow-review-20261027/REPORT-ko.md)에 일반 상담의 실제 설정 모드 배치·비용 상한·전송 전 동의·키 부재 복구·금액 미확인 구분·완료 후 polling 수정을 추가했다. 실제 공급자 socket만 합성으로 대체한 로컬 UI 표본이며 실제 Claude 응답 품질이나 사용자 시험은 아니다. 1920/1280/375px 문서 가로 넘침과 입력→비용 필드 Tab 이동을 확인했다. 전체 접근성·zoom·스크린리더는 남아 있다.

Hallmark 정적 검사(index.html+studio.css)는 전후 모두 미통과이며 render는 puppeteer-core 부재로 미실행이다. 설치 지침 읽기·정적 명령 실행·수동 캡처 확인·독립 검토를 구분한다. Impeccable의 정식 격리 critique·전체 audit 통과나 가짜 점수로 표현하지 않는다. 기본 화면의 내부 진단은 줄이고 비용·권리·실패·복구와 사람 승인은 유지한다. 아래 기존 원칙·과거 관측을 삭제하거나 새 검증으로 소급하지 않는다.

## 최신 구현 반영과 선택 기능 QA — 2026-10-28

현행 기준은 [725개 단계·후속 실제 UI와 문맥 검증 기록](../qa/codex-workflow-review-20261027/REPORT-ko.md)이다. 아래 R1 소스 일치·연결 거부·모바일 제외 등은 해당 검토 시점의 기록이다. 현재 UI/소스가 그 hash와 같다는 주장이 아니다. 이전 진단의 유효한 원칙은 유지하되 이미 확인한 반례를 새 결함으로 반복하지 않는다.

선택 GLB의 실제 1920×1080/1280×900/375×840 dialog 표본은 가로 넘침이 없었고 모바일 버튼은 44px였다. 긴 파일명은 저장하지 않은 DOM 표시 시험으로 122문자가 5줄에 줄바꿈됐다. 실제 모바일 검토 탭에서 열기·Escape 닫기·보이는 진입 버튼으로 포커스 복귀를 확인했다. Tab 경계에서 브라우저 chrome으로 포커스가 이동(`document.hasFocus=false`)한 관측을 전체 포커스 순환 통과로 세지 않는다. 전체 접근성·200% 확대·스크린리더 수용은 남아 있다.

독립 수동 검토의 **OGV-02**(후보 완료 뒤에도 상단 요청 접수 안내 잔류)는 현재 구도·Take·dirty/미확정/버전 조건을 확인해 완료와 다음 행동을 표시하도록 수정했다. 계약 검사와 실제 UI의 완료→미저장 수정→입력 취소·복원으로 확인했다. **OGV-01**(재열기 때 Take/승인 출력 문맥의 명료성)은 기존 `편집 선택 · Take 1` 표시·미리보기 선택 및 `결과 검토`의 별도 출력·자막 재생을 확인해 콘텐츠 유실로 판정하지 않았다. 추가 문구가 중복을 줄이는지는 후속 과업 평가로 남긴다. Hallmark/Impeccable 설치 지침을 읽은 독립 수동 표본이며 정식 critique A/B·audit 완료나 새 점수를 뜻하지 않는다.

**확인한 후속:** 모션 입력의 글자 크기·줄바꿈·오류 위치와 명시적 NFC 정리, 타임라인 입력/포커스·반복 컷과 상태 표시, 1920/1280 및 일부 모바일 표본이 보강됐다. 독립 브라우저의 360/375px×840 타임라인에서 가로 넘침이 없었고 긴 한글108자는 줄바꿈됐다. 이 표본은 전체 모바일·zoom·스크린리더나 실제 사용자 평가를 대신하지 않는다. 새 디자인 점수는 없다.

사용자의 최신 3D 결합 요구는 [단일 아키텍처·과업 설계](../qa/AI-3D-ARCHITECTURE-RESEARCH-20261027.md)를 따른다. **Operate 화면**으로 다루고 중성 작업대·기존 타입/색/간격·선택/포커스/승인 역할을 재사용한다. `생성 후보`와 `장면`, `Take`, `출력`을 같은 승인으로 오해하지 않게 한다.

|문제/설계 항목|선택한 방향·이유|구현 후 합격 기준|
|---|---|---|
|D3-01 내부 엔진이 사용자 흐름을 나눌 위험 — 설계 가설|한 `3D 장면 만들기` 기능에서 생성·구도·빛·검토를 연결. 공급자/Blender 창 전환을 기본 과업에서 요구하지 않음|음원만/사진 추가 모두 설명→후보→수정→영상 사용을 수행. 불필요한 중복 입력·화면 전환을 과업 기록으로 확인|
|D3-02 작은 수정에 전체 재생성하는 비용/일관성 위험 — 설계 가설|위치·카메라·조명은 내부 typed 변경. 형상·texture 생성과 구별|해당 변경의 before/after가 실제 프레임과 같고 원본 자산 해시·관계없는 설정 보존. 새 외부 호출이 필요한 순간에만 자료·비용 동의|
|D3-03 상태·진단 노출 과다 위험 — 설계 가설|기본에는 대상·현재 작업·다음 행동. job ID/모델 revision·폴리곤·hash는 상세에, 비용·권리·실패·미확정·복구는 결정 시점에 표시|일반 사용자가 내부 ID 입력 없이 완주. 오류/취소/unknown에서 이유와 복구를 키보드로 찾고 초안/포커스가 보존|
|D3-04 미검증·승인 오인 위험 — 확인된 구현 잔여|과거 manifest는 현재 HTTP header만 unverified이며 화면 안내는 미구현. 사용자에게 필요한 검증 상태를 기록/다운로드 맥락에 표시하는 후속 설계|검증됨·미검증·권리중지·손상을 구별하고, 과거 자료를 자동 신뢰 승격하거나 새 승인으로 보이게 하지 않음|

방법은 기존 [matrix](../qa/design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md)의 과업 분석·인지 walkthrough·객체/버전 정체성·위험 기반 점진 공개·상태 전이/경계 회귀를 선택 적용한다. 화면 상태가 없는 단계의 시각 합격을 선언하지 않는다. 실제 구현 전 대표 흐름의 동작과 정보 순서→컴포넌트·토큰 매핑→같은 경로/폭/데이터의 전후 검증 순서로 진행한다.

## 이전 독립 진단 — 해당 소스·실행 경계 보존

## 최신 적용 범위 · 2026-10-27 후속

아래 ‘문서만 반영·구현 미재개’, 416과 새 세션 화면 부재는 당시 기록이다. 이후 부분 기능과 음원 빈 상태·오류, 복수 대화의 제한된 실제 화면 표본이 생겼다. 같은 조건의 전체 화면 전후 비교·접근성·사용자 평가는 아직 완료되지 않았다. [최신 작업 기록](../qa/codex-workflow-review-20261027/REPORT-ko.md)의 실제 화면과 실행 범위를 확인하고, 기능 후속 작업이 준비되면 사용자 과업을 기준으로 Hallmark·Impeccable의 실제 설치본을 적용해 문제·대안·계획을 먼저 제시한 뒤 구현·검증한다.

개인은 음원부터 시작하고 사진은 선택한다. 과업에 필요하지 않은 내부 진단·상세는 기본 화면에서 줄이되 비용·권리·실행 범위·오류·복구에 필요한 정보는 유지한다. 사용자 편의를 위해 중복 입력·단계를 합칠 수 있는지 검토하되 동작·승인 상태를 숨겨 성공한 것처럼 표시하지 않는다. 현재 문서 보충만으로 새 디자인 개선이나 사용성 향상이 검증된 것은 아니다.

## 현행 계획 보충 · 2026-10-27 — 문서만 반영

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** [AD01–AD07](AETHONSAAS-ADOPTION-PROPOSAL.md)의 개인 기본·선택적 팀 경로를 아래 영향 계획에 연결했다. 새 브라우저·pixels·computed 측정·품질 점수는 없다. 아래 R1 화면 관찰은 당시 증거이며 현재 부분 세션 코드의 시각 검증이 아니다.

|기존 관측|후속 증거와 현행 처리|
|---|---|
|CQ-01 승인 사실 위계, CQ-02 현재 채팅 모델 표시|[414 보고](../qa/chat-model-receipt-display-20261026/REPORT-ko.md)에서 현재 선택 모델/미선택·긴 이름과 stale 안내의 제한된 수정·served표본. 아래 관측을 새 미수정 결함으로 재계상하지 않음|
|CQ-R01 모델 polling/재열기|[독립 반례](../qa/independent-chat-model-receipt-recheck-20261026/REPORT-ko.md) → [416 수정](../qa/chat-model-receipt-display-20261026/polling/REPORT-ko.md)·[manifest](../qa/chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json). 구현팀 실제 두 탭·초안/미저장 선택 검증. 수정본의 독립최종재검증은 별도|
|현재 build|이후 [세션 partial](CHAT-SESSION-PLAN.md) 중단. index/CSS가416과 같아도 현재 backend전체가 검증된 것은 아님. 새세션 UI의 matched 실제화면 없음|

### 채택 설계의 유한 화면 계획 — 전부 계획/NOT RUN

|과업·상태|근거·이유 / 최소 설계|위험과 수용|
|---|---|---|
|개인 진입→출력·재개|최신 사용자 결정과[보충문](PRODUCT-IDENTITY-AMENDMENT-20261027.md). 팀 생성/초대/공유를 필수단계로 노출하지 않음|권리/비용/사람결정까지 숨기지 않음. P01/C01–08, 팀미사용 완주 trace|
|AD01 자료/모델·계획|원본07 역할/버전·미지원, donor S03/S04. 기존 선택기로 공통기준/이번대상/제외 이유 요약|패널 과증식 금지. 실제 effective/submitted와 요약 일치, 긴 한글/미지원 원인/키보드 접근|
|AD02 독립대화|원본07와 확정 CS. 기존 상담 영역 선택+새대화, 선택대상/모델 적용범위 인지|다른대화 늦은결과·초안/커서/scroll 유실, shared예산 혼동 방지. CS01–18/P04–07. 팀권한 UI 선행 불필요|
|AD04/05 개인 이어 만들기·의견|정확버전/선택댓글→새초안, 기존비교·검토 재사용|비교≠채택≠승인, 원본/trim/음원/자막 보존. P08–10, 미지원/누락/dirty/error 포함|
|AD03 및 팀변형|선택적 공유의 대상/입력범위/권한을 실제 계약과 일치|auth/ACL 전 기능처럼표시 금지. T01–09, hidden버튼으로서버권한 대체 금지|
|AD06 상태/오류|기존 serverreceipt, 모델·비용·권리·실패를 결정시점에 유지; raw진단은상세|unknown≠실패, 테스트미디어 배지유지, 오류인접 복구/초안보존. C03/C06|

### 시각·상호작용 검증 조건

1920×1080 CSS viewport 주·1280×900 보조, 모바일 추가 보류. 같은 작품/장면/Take/버전/frame/음원·자막/승인·선택·focus·scroll/앱배율에서 전후를 비교한다. 대표 populated 상태와 empty/dirty/loading/error/unknown/dialog/긴 한글 표본을 명시한다. 표준 desktop page-scroll 없이 preview/transport/timeline/주요검토를 보존하고 긴 panel은 내부scroll, 확대에서는 reflow를 허용한다. 실제 zoom은 app scale·viewport resize와 다르다.

각 제안은 기존 neutral tokens와 role별 type/spacing/상태를 재사용하며 새색/강한 승인완료 CTA를 강제하지 않는다. 실제 대비쌍·키보드 초기진입/복귀·선택/승인/focus 비색상단서·긴내용/overlay clipping을 [P/T/C 수용](AETHONSAAS-ADOPTION-PROPOSAL.md)과 기존10그룹 시각matrix로 연결한다. 시각가설/확정위반/checked pass/미측정을 구분하고 새점수·경쟁사순위를 만들지 않는다. Hallmark/Impeccable은 실제read/manual/static실행 범위를 [사용기록](AETHONSAAS-ADOPTION-PROPOSAL.md)에 한정한다.

## 2026-10-26 R1 화면 검토 원문 — 역사적 관측 보존

2026-10-26 UTC · **문제 발견·계획 단계, 제품 변경 없음**

## 1. 결론과 이번 검토의 경계

우선 검토할 변경은 두 가지다. **입력 옆의 현재 채팅 모델 표시**를 원본07에 맞추고, **서버 확인 상태에서 재검토가 필요한 조건을 먼저 읽히게** 한다. 새 색상 체계, 강한 승인 완료 CTA, 작업대 재배치부터 시작할 근거는 없다. 모션 편집의 미리보기와 입력 배치, 긴 대화의 오류 접근은 추가 표본을 확보한 뒤 결정할 조건부 항목이다.

현재 제품 파일은 아래 R1 동결본과 일치한다. 최신 영수증 캡처3장과 이전 Aethon 작업대·모션 캡처를 **실제로 열어 픽셀을 검토**했다. 다만 이번 독립 검증 탭에서 `http://127.0.0.1:8773/`가 `net::ERR_CONNECTION_REFUSED`로 열리지 않았다. 오류 화면의 접근성 트리에서도 연결 거부를 확인했다. 재시도·서버 시작·다른 포트 탐색 없이 검증용 탭1489480715만 닫았다. 기존 사용자/기능 검증 탭은 조작하지 않았다.

따라서 **최신 실제 화면의 저장 픽셀 검토는 완료**, **현재 실행본의 동적·키보드 재검증은 BLOCKED**다. 새 캡처·served hash·computed style을 이번에 얻었다고 주장하지 않는다. 저장된 영수증 화면은 계획 상담 화면을 스크롤한 상태이며, 최신 기본 작업대의 전체 화면을 대신하지 않는다.

- 주 기준: **1920×1080 CSS viewport**, 보조: **1280×900**. 모니터 해상도와 구분한다. 모바일은 이번 범위 제외.
- 원본07의 모델 선택 → 계획 → 범위·비용 승인 → 후보 검토 → 부분 수정 → 출력·복구 과업이 중심이다. 모션은 이미 구현된 해당 과업의 한 경로다.
- 신규 점수 없음. 과거81/100은 다른 시점의 혼합 평가이며, 이번 시각 품질·기능 정확성·검증 커버리지를 합산하지 않는다. 경쟁사 동등성이나90 달성을 주장하지 않는다.
- 제품 코드·서버·DB·공급자·세션 설계·다른 QA 문서 변경 없음. 이 문서만 작성한다. 구현 담당은 기존 단일 작성자다.

## 2. 버전과 실제로 확인한 증거

### 2.1 현재 소스 경계

[R1 RECEIPT-MANIFEST](../qa/native-motion-20261026/RECEIPT-MANIFEST.json), 동결 `2026-10-26T19:35:59.264127+00:00`. 이번 읽기에서 manifest의 `source`28개 모두 SHA-256 일치, drift0을 확인했다. 이는 소스 대조이며 새 실행시험이 아니다.

|파일|현재 SHA-256|
|---|---|
|index.html|`b8074c24e39d3bc58023af60d9a1327da5806b2b93c326818178684510998739`|
|studio.css|`4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`|
|studio-media.js|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|motion-studio.js|`71e8959f23dc14863c63d619b23420b9d199165e5bd28a01901d391cfa37e40e`|
|app.py|`baa5bad0ffd913a200203ea1dab4e1f4bfd8fced6f4472bc644809c241429bc8`|

[R1 구현 보고서](../qa/native-motion-20261026/server-receipt-ui/REPORT-ko.md)와 [최종 독립 감사](../qa/independent-native-motion-receipt-recheck-20261026/REPORT-ko.md)의410회귀/격리10검사 결과는 **기존 기능 증거**로 유지한다. 이번 디자인 검토가 직접 재실행한 테스트가 아니다. NM-Q01의 서버 승인 사실 표시 문제는 닫힌 상태이며, 모델 원문의 오류까지 사라졌다고 확대하지 않는다.

### 2.2 이미지·환경과 비교 가능성

아래 파일은 모두 이번에 `view_image`로 열었다. R1의 이미지 파일 해시는 manifest와 연결돼 있다. 로컬 이미지의1920×1080/1280×900 파일 크기는 `sips -g pixelWidth -g pixelHeight`로도 확인했다.

|ID·증거|조건·시점|이번에 가능한 판단 / 불가능한 판단|
|---|---|---|
|R1-A [현재 영수증1920](../qa/native-motion-20261026/server-receipt-ui/receipt-1920.jpg)|19:28:22경,1920×1080/DPR1/앱100%, 현재 문맥 일치, 과거 답변 재생, 원문 접힘, 과거 영수증 summary에 focus|현재·과거·원문 위계, 문구/면/테두리. **미디어 없는 합성 fixture**, 캔버스 품질 판단 불가|
|R1-B [현재 영수증1280](../qa/native-motion-20261026/server-receipt-ui/receipt-1280.jpg)|19:29:24경,1280×900/DPR1/앱100%, 스크롤 위치 다름|보조폭 줄바꿈·focus.1920과 동일 scroll/frame의 전후 비교 아님|
|R1-C [현재 불일치+과거 일치1920](../qa/native-motion-20261026/server-receipt-ui/stale-and-history-1920.jpg)|19:30:02경, 격리 fixture의 description 변경 후 현재false/과거true, 과거 disclosure 열림|정확한 문맥 불일치 문구가 일반 목록과 같은 위계인 것 확인. 실제 고객 오류 빈도·사용자 실수율은 미측정|
|M1-A [모션 검토1920](../qa/native-motion-20261026/browser-followup/motion-final-1920.jpg)|[M1 manifest](../qa/native-motion-20261026/FOLLOWUP-MANIFEST.json), 모션 dialog 중간 스크롤, 저장 프레임48, 합성 도형/텍스트|편집 필드·프레임·승인·후보 렌더의 공간 관계. **R1 이전 HTML**, motion JS/CSS는 R1과 동일. 현재 전체 페이지 판정으로 전용하지 않음|
|M1-B [모션 검토1280](../qa/native-motion-20261026/browser-followup/motion-preview-1280.jpg)|같은 M1,1280×900, 다른 프레임·스크롤|긴 모달의 밀도와 내부 스크롤. M1-A와 동일 프레임 비교/품질 평가 아님|
|E8-A [작업대1920](../qa/codex-cli-assessment-20261026/implementation/1920-sequence-detail.png), [측정](../qa/codex-cli-assessment-20261026/implementation/1920-sequence-detail.json)|07:55:34, Aethon 명칭 적용본 HTML `d82ca93a64f31e71bf0c469b1b72b7c59c6a4bbe0403b969881349d8ec82f6e2`, CSS/media JS는 R1과 동일.3장면, sequence0.5초/원본0.75초, Take1, 정밀 펼침|작업대의 이전 검증 기준선. 최신 영수증 이후 기본 작업대가 같다고 단정하지 않음|
|E8-B [작업대1280](../qa/codex-cli-assessment-20261026/implementation/1280-sequence-detail.png), [측정](../qa/codex-cli-assessment-20261026/implementation/1280-sequence-detail.json)|07:55:40,1280×900, E8-A와 같은 과업/미디어/재생위치|같은 빌드의 뷰포트 비교 가능. R1과 전후 회귀 판정 불가|
|E8-C [모델 설정1920](../qa/codex-cli-assessment-20261026/implementation/model-selected-1920.png)|같은 E8, **파일명과 달리 화면상 세 슬롯 모두 미선택**|역할별 라벨/조작 구분 확인. 선택된 긴 이름이나 실제 연결 표본으로 쓰지 않음|

R1의 Chrome extension 버전은 당시 기록에 미확인이다. E8은 UA Chrome154.0.0.0/Mac, M1은 당시 보고의 별도 환경이다. 앱100%/DPR1은 보고된 조건이며 **실제 브라우저 zoom 검증과 같지 않다**. 현재 폰트 렌더러·locale/timezone·모든 hover 상태를 다시 측정하지 않았다. 이전 잘못 이름 붙인 캡처나 수정 전 모션 오류 캡처를 최신 결함 근거로 사용하지 않는다.

### 2.3 실제 면적: 검증된 과거 측정과 현재 미측정을 구분

아래는 이번에 E8 JSON을 다시 읽은 수치이며 새로운 DOM 측정이 아니다. `#preview` 검은 contain stage와 **실제 영상 픽셀의 면적**을 혼동하지 않는다.

|동일 sequence+정밀 과업|1920×1080 E8|1280×900 E8|
|---|---:|---:|
|shell / 단계 행 높이|56 /48px|56 /48px|
|rail / inspector 폭|184 /288px|184 /288px|
|preview stage|1376×313.98px|736×192.70px|
|실제320×180 미디어 contain|554.64×311.98px|339.03×190.70px|
|transport 높이|101px|101px|
|timeline dock 하단 / document높이|1064 /1080px|884 /900px|
|장면 제목 크기/행간|20 /28px|20 /28px|
|시간눈금 크기/행간|12 /18px|12 /18px|

픽셀에서 stage 옆 여백은 크지만, 정밀 편집·Take·transport·타임라인이 함께 보이는 과업의 tradeoff다. **특정 미디어 면적 비율 미달을 자동 결함으로 삼지 않는다.** 현재 R1에서 기본/sequence/정밀·긴 장면까지 같은 표본을 재촬영하기 전에는 더 키우는 재배치를 제안하지 않는다. 기존 헤더36px 회수는 완료된 개선으로 보존하며 반복하지 않는다.

R1 영수증은 기존 [browser-checks](../qa/native-motion-20261026/server-receipt-ui/browser-checks.json)에 폭1240px·높이212.39px로 기록됐다. 스크롤된 계획 화면이며 no-page-scroll 작업대 조건을 이 화면 전체의 의무로 확대하지 않는다. 보고된 작업대 복귀1080/1080은 해당 미디어 없는 표본의 기능팀 관측이다.

## 3. 적용한 스킬과 참조의 역할

|도구·지침|실제 사용|채택 / 적용하지 않는 부분|
|---|---|---|
|Hallmark2.0.0|설치된 `/Users/leesungmin/.agents/skills/hallmark/SKILL.md`, `references/redesign.md`, `flow.md`의 App screens를 읽고 수동 적용|기존 wiring/brand 보존, 토큰 역할·focus·상태·밀도. 마케팅 hero/80단어/중앙 고정폭/random theme/일괄 테두리 삭제/강제clip 미적용. `sloplint --render` 실행·전체 Hallmark audit 인증 아님|
|Impeccable4.7.1|설치 SKILL과 `reference/operate.md` 읽기, critique 절차의 격리 요구 확인|고정 rem,400/500/600 위계, 절제된 상태색, 일반 컨트롤·입력 보존. 이번은 **수동 계획 검토**이며 공식 `/critique` A/B·detector·점수 실행 아님. 이전 context probe exit127은 [기존 기록](../qa/codex-cli-assessment-20261026/REPORT-ko.md) 그대로, 엔진 다운로드·새 설치 없음|
|Refero design|설치 cloud skill 읽기, 기존 [reference lock](../qa/design-system-redesign-20261026/REFERENCE-LOCK.md) 유지. 이번 `refero_get_screen`/`refero_get_screen_image(full)`로 아래2개 재조회·픽셀 확인|styles→screens→flows 중 **기존 style lock과 과거 flow 연구를 재사용**, 이번은 필요한 editor screens만 보완. 새 브랜드 방향/마케팅 스타일 검색은 하지 않음|

스킬은 사용자 범위보다 우선하지 않는다. 기존 미커밋 파일을 stash/reset하지 않았고, 스킬의 파일생성·실행 지침으로 서버나 데이터 변경 권한을 만들지 않았다. 자동 검사 실행 여부와 지침을 읽고 수동 적용한 사실을 분리한다.

### 3.1 경쟁사·방법론 비교표

|참조·출처|직접 확인한 부분|Aethon에 적용할 이유 / 비교 한계|
|---|---|---|
|[Descript Refero editor](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87)|이번 MCP로 이미지·메타데이터 재조회. 공통 시간축에 레이어/파형, clip 문맥 메뉴, 작은 preview와 우측 자산 영역|시간상 관계를 맞추는 과업에는 timeline 비중이 클 수 있음. 모든 editor가 preview를 최대화한다는 주장 배제. 이번 반환 이미지800×449, 원래 CSS viewport/DPR·촬영 시점 미확인. Aethon1920과 px·속도·내부 토큰 동등 비교 불가|
|[Frame.io Refero editor](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871)|이번 MCP 이미지에서 선택 asset 체크/외곽선, status 텍스트, 인접 player 확인|선택 대상과 검토 상태의 구분, preview와 대상 문맥의 인접성만 참조. Aethon의 승인 권한·과금 모델을 Frame.io와 같다고 추정하지 않음. 반환800×450, CSS viewport/실제 동작 미측정|
|[Neural Frames 공식 handbook](https://help.neuralframes.com/en/articles/12038142-handbook-the-four-stages-of-autopilot), [보존 Track 이미지](../qa/design-benchmark-20261025/structure/neural-official-track.png)|이번 공식 문서 재읽기와 저장 Track 이미지 픽셀 확인. 음악구간·파형·설정·자막·기존 영상의 묶음|시간/음원 맥락 중심의 과업 구분.3194×1494 이미지, 문서2026-04-09, 저장2026-10-25. 보라색 숫자는 문서 주석. **현재 로그인한 editor나 Aethon와 같은 상태가 아님**|
|[Runway captured home](https://refero.design/pages/bc5ff496-55ad-4478-a968-62f7e641b9db)|기존 lock의 조용한 prompt shell 참고만 유지, 이번 새 픽셀 조회 없음|timeline/승인/실행능력의 증거로 쓰지 않음. Runway는 benchmark이며 연결 공급자로 복원하지 않음|
|[NN/g Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)|이번 원문 확인: 중요한 기본 선택을 먼저, 전문·드문 정보를 요청 시 표시|현재 제한/실패는 밖에, 과거 진단은 안에 두는 근거. 승인·비용을 숨기라는 지침이 아님. 중요도에 위험을 포함하는 것은 우리 설계 판단|
|[W3C Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)|이번 공식 이해문서 확인: 일반 글자4.5:1, 큰 글자3:1, 비활성/순수장식 예외|색상 역할쌍을 수치로 확인. 실제 사람의 읽기 속도·전체 접근성·미적 완성도 지표가 아님|

Refero의 descriptions·추정 HEX·폰트명은 메타데이터이지 상대 제품의 내부 CSS를 계측한 결과가 아니다. 사진에서 추출된 오렌지/보라를 UI token으로 가져오지 않는다. 경쟁사 점수·완료율·동일1920 live 비교는 만들지 않는다.

## 4. 현재 시각·동작 상태 관찰

분류: **확인된 요구 공백**, **시각/과업 가설**, **확인한 장점**, **미측정**. 표의 관찰은 모두 출처 범위 안에서만 유효하다.

|범위|관찰·근거|판정·다음 행동|
|---|---|---|
|승인 사실 위계|R1-A/C에서 현재 영수증이 과거 원문보다 앞에 있다. 과거 조회는 “현재 승인 아님”, 원문은 “검토 전”으로 분리. 그러나 현재false 안내도 동일 흰색 목록의 한 줄이다. [index.html](../../index.html)379–401행은 상태별 시각 클래스를 만들지 않는다|정확한 사실 분리는 **유지**. 차단 사유를 먼저 찾기 어려울 수 있다는 **시각 가설 CQ-01**. 승인 기능 오류/대비 위반 재발로 분류하지 않음|
|현재 채팅 모델 인지|R1-A 입력 위는 “연결 없음”, 과거 답변에는 Claude 이름. 현재 모델 요약은 `modelDefaultsBar`이며639–648행에서 접힌 프로젝트 상태로 이동. `drawModelChat`395행은 mode/한도만 입력 주변에 표시|원본07 §3.2/L109의 현재 모델 상시표시와 **소스·표본 수준의 요구 공백 CQ-02**. 현재 과거모델과 다른 선택이 실제 혼동을 일으킨 사용성 실험은 없음|
|캔버스·조작 밀도|E8에서는 장면/preview/transport/Take/timeline/검토가 첫 화면 안에 있고 저장된 승인 상태에 과도한 실행 CTA가 없다|유지할 강점. R1의 media-rich 기본 작업대는 **미측정**, 면적 재배치 보류|
|모션 편집과 preview|M1-A/B는 긴 모달의 중간 스크롤에서 프레임과 하단 승인 렌더가 보이지만 title/레이어/첫 입력은 위로 벗어나 있다. 현재 `motion-studio.js`6·31행도 모든 keyframe 입력 뒤에 preview를 배치|**과업 가설 CQ-03**. 전체 입력 접근 불가·클리핑 결함으로 판정하지 않음. 기존 UI09 sampled keyboard 통과도 유지|
|타이포·간격·긴 한글|R1 짧은 영수증은 잘리지 않고, E8 제목20px/행간28, body14, 메타12의 역할이 보인다. 모션은 fieldset/입력이 밀집|현재 font face/긴receipt/긴모델·CJK 무공백·app150/200 재검증은 **미실시**. 일반16px 강제/한글 자간 변경 근거 없음|
|색상·surface|현재 CSS role과 저장 픽셀의 중성 surface 일치. selected는 면+선, 승인 상태는 텍스트/기호, focus는 dashed outline|아래 값 보존. “회색이라 저품질” 또는 모든선 제거는 근거 없음. 밝은 outline은 입력/선택/focus 각각 의미를 검사해야 함|
|아이콘·조작 형태|R1 native disclosure 삼각형, E8 체크/빈원, M1 native range가 task 의미를 가진다. label과 함께 사용|광학 미세차이는 있을 수 있으나 동일 크기 current closeup/hover 증거 없음. 새 icon pack·이모지 교체 작업 제안 안 함|
|오류 위치·복구|R1-C의 문맥 불일치는 default에서 보인다. 현재 chat error는 각 turn 안, motion status는 dialog 상단에 있다|긴 이력/스크롤 중 실패가 보이는지 **CQ-04 검증 항목**. 기존 저장/unknown/draft 회귀가 실패했다고 다시 세지 않음|
|키보드·focus|R1 summary의 전체 dashed focus가 저장 이미지에서 보임. 과거 보고는 Enter와 refresh 후 focus/scroll 보존, M1 Escape/opener 복귀 표본 통과|사진은 focus order/반환의 직접 실행 증거가 아니다. 이번 initial-page keyboard journey·screenreader·real zoom은 BLOCKED/NOT RUN|

### 4.1 실제 소스의 토큰과 대비

[studio.css](../../studio.css)4–65행이 semantic token authority다. 아래는 **현재 소스의 값**이며 이번 live computed style이 아니다. 역할별 선택자는252–270,670–706,751–761행을 함께 읽었다. 기본 opacity·white 선언만 보고 최종 cascade가 그대로라고 판정하지 않는다.

|역할|현재 값|
|---|---|
|canvas / panel / raised / inset / hover|`#101010` / `#1B1B1B` / `#242424` / `#141414` / `#303030`|
|strong / body / muted / disabled|`#F4F4F2` / `#DEDEDB` / `#BDBDBB` / `#A6A6A3`|
|선택 면 / 선택 marker / focus|`#2A2A28` / `#D8D8D2` / `#E4DDBE`|
|control 경계 / 장식 divider|`#858585` / `#383838`|
|error / error surface / warning|`#FFB49D` / `#28201E` / `#E6C58B`|
|primary / on-primary|strong alias / canvas alias|
|크기/weight|12·13·14·16·18·20·24px 상당 rem×앱scale;400/500/600|
|간격 / radius|4·8·12·16·24·32px 상당 rem; clip4/control6/panel8/dialog12px **token**, 사용처별 적용은 별도|
|font / motion|system-ui,-apple-system,Apple SD Gothic Neo,Noto Sans KR,sans-serif; timecode ui-monospace;120ms. 실제 glyph font는 새로 확인하지 못함|

sRGB 상대휘도 공식으로 이번에 계산했다. 각각 source의 foreground/background 역할쌍이다. screenshot compression 픽셀을 문자색이라고 추출하지 않았다.

|쌍|대비|해석|
|---|---:|---|
|strong / canvas|17.28:1|R1 본문 계열, 일반글자 임계 이상|
|body / panel|12.78:1|검토/보조 본문|
|muted / panel, muted / hover|9.15:1 /7.01:1|메타 문구를 더 밝게 만들어야 한다는 근거 없음|
|control edge / panel, edge / hover|4.67:1 /3.58:1|필수 식별 경계의3:1 검토에 사용할 수 있음. 전체 control/state 조합 인증 아님|
|focus / panel|12.62:1|선택선과 색뿐 아니라 dashed 형태도 구분|
|error / error surface|9.32:1|CQ-01에 기존 warning/error 역할 재사용 가능|
|marker / selected|10.05:1|선택 marker의 역할쌍|
|divider / panel|1.47:1|순수 그룹 장식 경계를 자동 WCAG 실패로 취급하지 않음|

forced-colors/reduced-motion 규칙은 소스에 있으나 이번 OS/browser 상태에서 직접 검증하지 못했다. 선언 존재가 준수 증명은 아니다. token을 전부 바꾸거나 하드코딩 개수를 점수로 변환하지 않는다.

## 5. 개선 제안: 대안·이유·최소 범위

### CQ-01 — 현재 승인 문맥의 판단 순서를 명확히

- **상태/심각도:** 시각·과업 가설, P2 후보. 정확한 차단 문구는 존재한다. NM-Q01 재개방 아님.
- **현재 근거:** R1-C 상단 현재false와 아래 과거true가 같은 bullet 구성·글자색. `.chat-server-receipt`, `receiptFacts`/`receiptMarkup`(`index.html`379–390). 현재 장면/버전·승인 범위·일치 여부·미적용 제안·두 경고가 연속된다.
- **사용자 영향:** “지금 이 승인으로 실행 가능한가”를 알기 위해 여러 문장을 읽어야 한다. 오류 발생률/탐색 시간은 미측정.
- **대안:** A 현행 유지(변경 위험 최소, scan 부담 유지), B 현재 판단 한 줄+근거 그룹(선택), C 영수증 전체 접기(차단사유 은폐 위험으로 제외). 모든 승인에 녹색·강한CTA를 주는 안은 권한 확대처럼 보일 수 있어 제외.
- **선택 이유/참조:** NN/g의 중요정보 우선, Impeccable Operate 상태 어휘; Frame.io의 선택과 결과 상태 분리. 서버 사실을 대체하지 않고 읽는 순서만 바꾼다.
- **계획할 최소 변경:** `.chat-server-receipt`에 current/historical 구분을 보존하고 서버 enum에서 도출한 표시상태만 부여. “현재 장면 · 모션v1” 다음에 false는 “승인 후 조건 변경 · 이 승인으로 실행 불가”, null은 “승인 조건 확인 필요”, true는 “조회 시 조건 일치 · 실행 전 재검사”처럼 정확한 한 줄을 둔다. 승인 범위/최종 출력 별개/미적용 제안 유무는 기본에서 계속 보인다. 세부 카운트·전체 원문 사실은 명시적인 상세에 보존한다. **새 실행 버튼 없음.**
- **토큰/컴포넌트:** 기존 body/heading/space2·3만 사용. false/unknown의 icon+text+기존 warning 역할을 검토, true는 중성. warning은 network job 실패 의미와 혼동하지 않게 문구로 구분. 새 palette/global CSS 수정 없음.
- **회귀 위험:** 숨겨진 승인 제한, 과거true의 현재 상태 오인, focus/scroll/초안 손실, 새 disclosure key 충돌. 서버 projection/권한/DB/service/원문은 변경 대상 아님.
- **수용기준:** true/false/null/invalid_record/없음/다른장면/과거true+현재false 각 표본에서 현재 대상·버전·판단을 기본 화면에서 확인. “실행 확정 아님/후보 승인≠출력 승인” 유지. 원문 text/hash 불변, 상세 기본 닫힘과 Enter/Space/Escape 또는 native 동작 검증. poll 전후 focus/scroll/신규입력 유지.1920/1280 app100·150·200에서 텍스트와 focus 미소실. 키보드 path 추가가 승인 액션을 호출하지 않음.

### CQ-02 — 채팅 입력 주변에 현재 모델과 적용 범위 표시

- **상태/심각도:** 원본07 §3.2/L109와 현재 소스의 확인된 표시 공백, P2. 실호출 오라우팅을 재현한 것은 아니다. [세션 계획](CHAT-SESSION-PLAN.md)의 모델 바인딩은 진행/결정 대기 범위로 존중한다.
- **현재 근거:** R1-A의 요청 입력 위 `#modelChatCapability`는 연결 상태만 표시하고, 모델명은 과거 `.guided-card` 안에 있다. 현재 기본 모델 요약은 접힌 `.lt-project-context #modelDefaultsBar`에 있다(`index.html`395·401·569–572·645–648).
- **사용자 영향:** “다음 요청에 쓰는 모델”과 “지난 답변에 쓴 모델”을 구분하기 위해 설정을 다시 열어야 한다. 선택 모델이 바뀐 장기 대화에서 더 중요하다.
- **대안:** A 모델 설정만 유지(요구 충족 안 됨), B 입력 라벨 인접 한 줄+기존 설정 진입(선택), C 세 슬롯 선택기를 입력 위에 복제(밀도·불일치 위험). 세션별 새 resolver는 이 디자인 패치에 넣지 않는다.
- **선택 이유/참조:** 직접 요구가 최우선. 위험 기반 공개: 모델·적용 범위·한도는 전송 전, 과거 비용·실제 모델은 결과에. Refero의 조용한 prompt shell은 배치 참고일 뿐 모델 의미의 근거가 아니다.
- **계획할 최소 변경:** `#modelChatForm` 앞에 “기획 모델: [서버가 선택한 모델/미선택] · 다음 요청 적용”과 현재 연결상태를 함께 표시. image/video는 기존 모델 설정 진입을 재사용. 현재 실행 중 turn의 실제 모델은 별도 고정 문구. 선택불가·미연결이면 선택값은 유지하고 이유를 표시한다. cap.mode나 과거 t.model로 현재 선택을 추정하지 않는다.
- **토큰/컴포넌트:**14px 역할 라벨/500, model명14px/500, 상태12–13px/400; 기존 color/spacing 재사용. 긴 이름은 줄바꿈, 잘린 이름을 tooltip에만 의존하지 않음.
- **회귀 위험:** 기본선택과 실제실행 모델 혼동, 세션담당과 중복 resolver, 모델 변경이 진행중 미디어/승인 변경, 입력 draft 재생성.
- **수용기준:** 현재 선택≠과거 응답 모델 표본, 미선택·unverified·blocked·긴 이름·진행중 모델 전환 표본에서 두 의미 구분. 입력과 현재 모델이1920/1280 같은 문맥에서 보임. 키보드로 기존 설정을 열고 닫으면 opener/초안 복귀. 선택 저장은 호출·비용·승인을 만들지 않음. 세션 담당이 **현재 선택/적용 시점의 제공 필드 계약을 확정한 후** 연결한다. 계약 전에는 표시만 하려고 가짜 모델명을 쓰지 않는다.

### CQ-03 — 모션 편집의 프레임과 입력을 함께 보는 배치 검증

- **상태/심각도:** 조건부 과업 가설. 현 시점 구현 승인 제안이 아니라 먼저 맞춘 baseline 필요.
- **근거/영향:** M1-A/B는 프레임을 볼 때 상단 레이어·초기 입력이 viewport 밖이다. `#motionDialog` 안에서 `#motionFields` 전체 뒤에 `#motionImage`가 온다. 입력 수정→저장안 프레임 확인을 오갈 때 위치 기억·스크롤 부담이 생길 가능성이 있다. 실제 시간/오류율은 모름.
- **대안:** A 현행 모달 내부 스크롤(보존), B desktop에서 선택 레이어 입력과 저장 프레임을 인접한2영역으로 배치, C 전체 Blender형 새 editor(범위 밖). 새 baseline에서 빈번한 왕복이 확인될 경우만 B 선택.
- **참조/최소 변경:** Frame.io의 대상+player 인접성과 Impeccable의 task-first. 기존 DOM nodes/IDs를 이동하는 범위, inputpane만 내부 scroll, 오류·현재작품/장면/모션버전은 공통 상단. saved-frame이며 dirty 즉시 미리보기가 아니라는 사실 유지. 모션 renderer·승인·합성·새 생성 기능 추가 없음.
- **위험/수용기준:** `#motionStatus`/복구 action 가려짐, preview 작아짐, Tab 순서 불일치,초안 scope/version guard 손상.3 keyframes/긴한글/최대지원레이어 fixture에서 identity·선택 입력·저장 frame·상태가1920에서 함께 보이는지 먼저 측정.1280/앱확대는 접근 가능한 세로 reflow 허용. 기존 cancel/hold/reject/restore/새 입력 보존/승인 불변 모두 유지. 기존 배치로 이미 과업이 충분하면 **변경하지 않고 종료**.

### CQ-04 — 긴 이력의 실패·복구 위치는 검증 후 결정

- **상태:** 미측정 요구. 현재 결함으로 집계하지 않음.
- **근거/영향:** `drawModelChat`는 저장 turn 순서로 카드를 만들고 오류를 각 카드 안에 둔다. `#modelChatStatus`는 최신 상태 한 줄이다. 모션 `#motionStatus`는 상단에 위치한다. 길어진 이력/모달 하단에서 실패했을 때 원인·입력보존·기존 요청 확인이 눈에 들어오는지 실제 표본이 없다.
- **대안:** A 현재 상태+local error 유지, B 필요할 때만 해당 오류로 가는 명시적 링크/인접 status, C 모든 오류를 자동 scroll/focus(새 입력 방해로 제외).
- **참조/최소 범위:** 원본07 §3.5의 실제 상태·다음 행동, Operate error state. 안전한 오류 표본에서 가려짐이 확인된 경우만 B. 전역 toast로 기존 국소 오류를 대체하지 않는다.
- **회귀 위험/수용기준:** unknown을 실패로 바꾸거나 자동 재제출, poll이 사용자 focus를 빼앗는 문제 금지.20개 저장 이력+긴 CJK 오류, queued/running/rejected/unknown/committed-refresh-failed별 현재 대상·남은 결과·비용 확인 범위·다음 행동·초안보존 확인. 모든 mutation은 격리 fake 환경에 한정. 그런 환경이 없으면 NOT RUN을 유지하고 현재 DB로 시험하지 않음.

## 6. 계획 → 구현 → 같은 조건 검증 파이프라인

1. **설명·범위 고정:** 이 문서의 CQ-01/02 최소안과 대안·위험을 부모가 사용자에게 설명한다. 세션 담당의 모델 선택 계약을 받아 CQ-02 바인딩 범위를 합친다. 원본07이나 세션 결정 질문을 임의 확정하지 않는다.
2. **baseline 확보:** 단일 작성자가 현재 소스를 정상적으로 제공한 고정 URL/hash를 전달하면, 별도 검증 탭에서R1-A/C와 같은 작품/장면/receipt조건을 재현한다. 현재 default 작업대1920/1280도 같은E8 과업으로 확인하되 다른 데이터이면 비교 불가 표시. 서버를 이 문서 담당이 시작하지 않는다.
3. **유한 구현:** CQ-01/02만 범위별 diff. 현재 핸들러·stable IDs·원문·공식 승인·모델 독립성·권리·예산·중복 실행·회복 경로 보존. CQ-03/04는 검증 없이 덧붙이지 않는다. 새 토큰이 필요해도 역할alias부터 제안하고 새 브랜드색은 만들지 않는다.
4. **같은 조건 전후:** 동일 CSS viewport/DPR/앱scale/브라우저버전/폰트/locale/timezone/선택/스크롤/열린disclosure/미디어frame·poster/원본파일hash를 기록. 캡처는 실제 served UI이며 candidate 주입을 actual로 표기하지 않는다. media ready/paused 상태를 동일하게 맞추고 오류·labels를 마스킹하지 않는다.
5. **독립 검증:** 시각 표와 기능 회귀 표 분리. 일반text4.5:1/큰text3:1,필수비문자3:1은 해당쌍만 판정. decorative선은 예외. focus가 전부 보이도록 하는 제품 목표와 WCAG2.4.11의 ‘전부 가려지지 않음’ 기준을 구분. 기존 통과 테스트는 약화하지 않는다.
6. **인계/종료:** source/served hash,수정파일,원본-후보-실통합 구분,전후측정,미실시/차단,source보존을 남긴다. 고친 항목의 수용기준이 충족되면 종료한다. 숫자90을 만들기 위한 새 장식/기능/무한benchmark는 추가하지 않는다.

### 6.1 후속 표본의 유한 체크리스트

|대상|표본·검증|현재 상태|
|---|---|---|
|현재/과거/모델 설명|current true/false/null + past true, 원문 펼침/접힘, 같은 현재 장면|R1 저장 픽셀 확인; 새 동적 검증BLOCKED|
|현재 모델|미선택/선택/blocked/unverified/긴이름/과거모델과다름|표시공백 소스 확인; 후속 계약·실제 화면 검증 대기|
|작업대|selected/sequence/precision/비교, 동일3장면1·2·4초/원본0.75초|E8 역사적 직접 픽셀 확인; 현재R1 media-rich 표본NOT RUN|
|긴 콘텐츠|긴CJK·영문무공백,긴receipt,20turn,dialog edge|이전 header 회귀 보존; 새영수증 범위NOT RUN|
|입력·상태|dirty/cancel,loading,국소error/unknown,비활성/hover/focus|코드와 기존 보고서만. 새 mutation 검사NOT RUN|
|키보드|초기페이지부터Tab→계획→입력→모델설정→닫기→원문/과거disclosure→복귀, focus 불가림|liveURLBLOCKED. 프로그램 focus로 전체여정 대체하지 않음|
|확대|앱100/150/200 각각, 실제browser200%별도|현재NOT RUN. 앱scale/DPR/viewport resize는 실제zoom의 대체 아님|
|추가 접근성|forced-colors/reduced-motion/스크린리더, 실제font fallback|현재NOT RUN. CSS 선언·정적사진만으로 통과 부여 안 함|

필수 보존 gate는 (a) 승인·비용·버전 의미, (b) 실제 media/시간축 경로, (c) 입력·키보드 접근, (d) 해당 의미의 대비다. 이번에는 새 전체 gate 통과를 선언하지 않는다. 이전 기능팀410/독립10 검사는 그 고정 범위의 근거로 남으며 이번 미측정 칸을 채우지 않는다.

## 7. 문서 완료와 남은 제한

이번 산출물은 이 계획서 하나다. 최신R1 소스와 저장 픽셀을 확인했고 현재 모델 표시 공백1건, 영수증 위계 개선 가설1건, 검증 선행 항목2건으로 범위를 정리했다. **제품 구현·새 API·유료호출·DB·서버·계정 변경·파일 업로드는0**이다. 별도 모델/세션 제품 결정, live 공급자 활성화, 모바일, Blender/ingestion 계획은 이 디자인 단계가 대신 결정하지 않는다.

현재 실행 차단은 로컬8773 연결 거부이며 권한 심사 거절이나 계정 인증 오류로 해석하지 않는다. 실제 브라우저 검증을 재개하려면 구현 담당의 정상 제공 URL과 동결 hash가 필요하다. 이 범위에서 확보하지 못한 최신 media-rich 기본 화면·키보드·확대·오류 상태를 확인하기 전에는 시각 QA 전체 완료나 출시 준비라고 보고하지 않는다.
