# Aethon — 전체 디자인 작업·검증 통합 계획

> **현행 기준 · 2026-10-26 워크플로 정합화. 이번 턴은 계획까지만, 제품 소스 변경 없음.** 사용자의 “현재 계획을 다 맞춘 이후에 진행 해” 지시에 따라 아래가 남은 작업의 단일 실행 계획이다. 완료된 폼 보호·값 보존 토큰·문맥 헤더는 유지한다. 아래쪽의 이전 계획과 연결된 QA 보고서는 당시 이력이며 현재 미완료 상태로 되돌리지 않는다. 다음 구현은 이 통합 계획을 부모 대화에서 설명한 뒤 기존 허용 범위에서 진행한다. 단계마다 형식적인 재승인을 요구하지 않는다.

**최신 결정:** 사용자가 “다 끝난 이후 구현까지 다 진행 해”, “추가적으로 우리 이름은 Aethon이라고 하자”라고 확정했다. 제품명은 **Aethon**이며, 계획 설명 뒤 아래 묶음의 구현·검증까지 이어간다. 이번에는 계획 체크포인트를 반환하며 제품명 소스 치환도 아직 하지 않는다. 기존 `Loretune` 폴더·내부 호환 식별자·역사적 문서는 유지하고 DP26-11에서 현행 사용자 표시만 구분해 전환한다. 새 로고·도메인·팔레트를 만들라는 요청으로 확대하지 않는다.

## A. 입력·기준선·이번 정합화에서 달라진 점

입력은 Library `libfile_3f4825539680819196c9307c0a8d1ce1`, **붙여넣은 텍스트.txt**, text/plain,17,322bytes,183행이다. 공식 Library `read`가 1–183행을 반환했고 `has_more=false`여서 전부 읽었다. 버전 ID는 null이었다. 직접 텍스트 읽기로 충분해 로컬 materialization은 하지 않았고, 과거 차단된 업로드를 재시도하지 않았다. 새 문서는 작업 절차를 보완하며 원본 제품 명세나 최신 사용자 결정을 대체하지 않는다.

기존 계획은 작은 수정의 반례·전후 비교에는 구체적이었지만 **전체 화면/상태의 범위, 열린 문제의 등급과 확신, 구조 대안, 의존성, 종료 조건**이 여러 보고서에 흩어져 있었다. 이번에는 다음을 보완한다.

1. 전체 제작 과업을 12개 화면·흐름 묶음으로 정리하고 현재 코드 확인, 현재 빌드의 실제 화면, 과거 증거, 미검증을 구분한다.
2. 문제 ID와 관찰/가설/coverage gap을 분리한다. 이미 닫힌 결함을 재개하거나 미검증을 곧바로 결함으로 세지 않는다.
3. 다음 작업을 단순 테두리 조정으로 축소하지 않는다. 입력→계획→승인→진행/복구→검토→편집→출력/재개의 알려진 목표를 점검한 후 필요한 작은 변경만 한다.
4. 역할 토큰·컴포넌트·상태·파일 범위와 검증 의존성을 고정한다. 새 명세·새 팔레트·새 프레임워크·경쟁 문서를 만들지 않는다.
5. 스킬 읽기/수동 적용/명령 실행/실행 불가를 분리하고, 실제 브라우저·VM·fixture·live 증거를 합치지 않는다.

독립 계획 검토의 PL02(분산된 과업/상태/빌드 coverage)는 C/H, PL03(넓은 공간·위계·아이콘 범주)은 D/F, PL04(작은 묶음과 전체 제품계획의 단절)는 B/C/G, PL05(분산된 종료·인계)는 H/J로 연결했다. 이들은 새 제품 결함이 아니라 계획의 구체성 문제다. 문서 불일치 PL01은 부모의 명시적 요청으로 `design-system-redesign-20261026/INDEX.md`와 `INTEGRATION-CONTRACT.md`의 현행 입구만 정정했다. 원감사의 VF01/VF02 실패는 역사적 결과로 보존하고 닫힘·최신 E1을 연결했다.

현재 코드와 최신 실제 served 검증 기준:

|파일|SHA256|
|---|---|
|`index.html`|`fd8efd8a3856ba5a209dc19fe4af0d228fa66b5501d546fcadd5f95c3ce6fefa`|
|`studio.css`|`4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`|
|`studio-media.js`|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|`app.py`|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

현재 경로의 `git status --short`는 **not a git repository**로 종료했다. clean tree라고 주장하지 않는다. root/`tests`의 소스121개 해시를 계획 편집 전후 비교했고 변경0·삭제0을 확인했다. 수정한 현행 문서3개의 로컬 링크도 누락0이었다. 이는 문서/보존 검사이며 제품 회귀 테스트를 새로 실행했다는 뜻은 아니다. root AGENTS.md/PRODUCT.md/DESIGN.md/design.md/package.json/session-handoff.md/checkpoint.md는 없었다. 홈 AGENTS와 `.codex/AGENTS.md`, README, 기존 설계/인계 문서를 읽었다. 문서 이름이 없다는 이유로 신규 제품으로 취급하지 않는다. 설치본 스킬·도구 메타데이터도 수정하지 않는다.

증거 참조:

- **E1** [최신 헤더 구현·8쌍 실제 served 화면·330 비HTTP 회귀](../context-header-space-20261026/REPORT-ko.md), [해시·종료 기록](../context-header-space-20261026/FINAL-MANIFEST.json). 현재 두1920 저장 이미지를 이번 계획에서 다시 열어 확인했다. 새 캡처는 아니다.
- **E2** [두 폼 초안 보호](../proposal-draft-fix-20261026/REPORT-ko.md), [동일 수정의 실제 브라우저12조건](../proposal-draft-fix-20261026/served-baseline/REPORT-ko.md). 이때 HTML은 이전 해시이며 현재 full regression이 보호한다.
- **E3** [값 보존 토큰·computed/숫자 폭](../value-preserving-tokens-20261026/REPORT-ko.md). 헤더 이전 빌드의 token 결과이며 현재 토큰 값은 소스 대조로 확인했다.
- **E4** [24개 기능·22개 시각 QA와 범위](../frontend-fq-vq-fixes-20261026/Loretune-프론트엔드-QA-기준과-검증결과-20261026.md), [독립 FQ 재검증](../independent-frontend-fq-recheck-20261026/REPORT-ko.md). 당시349는329비HTTP+20HTTP의 분할 실행이며 이번330과 합산하지 않는다.
- **E5** [CLI/스킬 평가](REPORT-ko.md), [코드 계약 검토](CLI-REVIEW-ko.md), [문맥 조회 관측](context-observation.json). 새 폼 결함의 당시 기록과 아직 남는 기능 경계를 구분한다.
- **E6** [현행 DS-01–14](../design-system-redesign-20261026/REQUIREMENTS-AND-ACCEPTANCE-ko.md), [token spec](../design-system-redesign-20261026/SEMANTIC-TOKEN-SPEC.md), [reference lock](../design-system-redesign-20261026/REFERENCE-LOCK.md), [방법론 적합표](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md). 설계 문서의 과거 pending/hash는 현재 실행 상태가 아니다. 명시적으로 허용된 INDEX/INTEGRATION-CONTRACT 입구의 상태만 이번에 정정했다. 수용기준·토큰·방법론과 원감사는 덮어쓰지 않고 추가 정합화가 필요하면 소유 검토자에게 전달한다.
- **E7** [원본 SPEC-MS-001](../../knowledge/project_kit/docs/modules/spec-ms-001/20261025/07_Chat_Directed_Multimodel_Production_Spec.md): §3화면,§5도구,§7문맥,§8–9미디어/승인,§13–15요구/수용/단계. 원본의 공급자 예시는 보존하되 사용자 확정인 fal 미디어/noMCP/Runway 벤치마크 역할이 실행 판단에 우선한다.

## B. 제품·사용자 과업·성공 조건

**확인된 제품:** Aethon은 로컬 음악영상 제작 작업대다. 현재 README와 실행 UI에는 이전 이름 Loretune이 남아 있으며 DP26-11에서 표시를 전환한다. Python 표준 라이브러리 HTTP/SQLite/기존 FFmpeg, 단일 HTML+CSS+미디어JS 구성이다. `app.py:873`의 서버,`:913–919`의 `/`,스타일,미디어JS,상태,모델목록과 `:985`의 `/api/action`을 사용한다. 여러 SPA 내부 패널과 dialog를 별도 URL 제품처럼 세지 않는다.

**대상 가설:** 일관된 IP 설정과 곡을 바탕으로 장면을 계획·제작·검토하려는 창작자. 실제 고객/직무/숙련도/사용빈도 조사는 없으므로 초보 경로와 숙련자 상세편집은 설계 대상이지 관찰된 사용자 집단이 아니다.

**주 과업:** 작품/IP·원곡 확인 → 선택한 채팅 모델과 정식 문맥으로 기획 → 계획/대상/모델/비용 검토 → 사람의 유효한 허용 범위 안에서 서버 도구 실행 → 파일 수집·등록 또는 기존 요청 복구 → 후보 비교·선택·검토 → 장면/음악/자막 편집 → 승인된 버전 출력 → 결과 확인·재개. 부분 수정은 필요한 샷의 새 후보이며 다른 샷·원음·기존 Take·승인본을 보존한다. 채팅과 상세 작업대는 같은 프로젝트/버전을 쓴다.

**확정 아키텍처:** Claude/OpenAI/Grok 계열 채팅 선택과 이미지/영상 선택을 독립 유지한다. 채팅 공급자 API→Aethon의 공통 제작 도구→사용자가 선택한 fal 모델 경로다. MCP·Runway/Higgsfield 직접 연결은 제품 요구가 아니다. 개발/조사 MCP 사용과는 별개다. 모델 catalog 등록/fixture/1경로의 실제 Claude 성공을 모든 조합 활성화로 바꾸지 않는다.

**이번 성공:** 알려진 제작 흐름의 핵심 상태를 빠뜨리지 않은 계획과 위험에 맞는 검증, 확인된 로컬 UX 결함의 수리, 현재 화면의 일관성, 정확한 상태·근거 표시. 1920×1080 CSS viewport/앱100%가 주 기준,1280×900이 보조다. 긴 상세는 접근 가능한 내부 scroll, 확대는 reflow를 허용한다. 모바일 추가 개선은 뒤로 미루되 기존 코드는 보존한다. `overflow:hidden`이나 축소 글자로 페이지 높이만 맞추지 않는다.

**범위 밖:** 새 공급자·모델 활성화/키 조회·설정, 유료호출, 실고객 자료 전송, 배포/다중사용자 인증 인프라,12live조합, 전체96FR/143API 완성, 신규 기능·언어·테마·모바일 전면 개편. 외부 연결과 대규모 검색 품질은 아래 별도 backlog이며 디자인 개선으로 해결됐다고 하지 않는다.

## C. 화면·흐름 coverage inventory

표의 ‘현재’는 위 해시의 코드 또는 E1 실제 served 표본을 뜻한다. ‘과거’는 연결된 QA 당시 빌드이며 현재 전수 통과가 아니다. 각 행은 기본/로딩/빈 상태/오류를 무조건 새로 만들라는 뜻이 아니라 **기존 기능에서 도달 가능한 상태**를 조사하는 범위다.

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
|DP26-04 **열린 coverage gap**|S01–12 최신빌드 상태별 evidence가 균일하지 않음, C표/E1/E4|부분스크린샷을 전체완료로 설명할 위험; historical/fixture/current 혼재|U / coverage높음|B1에서 실제경로별 검증종류와not-run 분리; 확인된 blocker만 새issue. 모든판정을 최신이라고재명명하지않음|
|DP26-05 **열린 정적차이**|`studio.css:68,72,77,118,120,192,622`에 font/white/black/spacing literal; E1소스|active인지cascade확인전 시각결함아님. 역할관리의공백 가능|P3 / 존재높음·활성영향미확인|computed inventory→active역할/의도적예외분류. 실제값유지 필요한alias만, 기존정확흰색을#F4F4F2로몰래치환금지|
|DP26-06 **가설**|현재1920 화면에 passive panel/Take/선택/버튼경계가공존, E1저장픽셀|관련그룹의동등강조가다음행동탐색을방해할수있음; 실제혼란증거없음|미정 / 낮음|S05/S07/S08과업별현재primary/보조/상태구분을검토. 구체중복·오인재현없으면변경하지않음. input/focus/selected/approval경계보존|
|DP26-06a **가설 세분화**|`.inspector`/`#ltTimelineDock` passive 외곽과 내부행동 경계, E11920 기본 화면|수동 그룹과 조작의 경계강도가 같아 보일 가능성; 불편은 미측정|미정 / 낮음|실제 active border/면을 측정하고 검토 과업의 그룹 식별을 설명. 구체적 충돌이 없으면 현재 유지. 승인 완료에 새 primary를 만들지 않음|
|DP26-06b **관찰 대기**|`#compareButton`과 Take strip의 거리, E1같은 화면|비교 시작을 찾는 이동 비용 가능성만 있으며 근접 배치가 더 낫다는 증거 없음|미정 / 낮음|현재 비교 진입과 선택의 구분·읽기순서부터 확인. 단순 거리 감소만으로 이동하지 않음. 변경한다면 기본/다중Take/긴문구/focus/선택불변 비교|
|DP26-06c **관찰 대기**|native summary marker, 재생기호, 검토 기호+텍스트의 optical alignment|실제 오정렬을 이번에 재현하지 않음. 아이콘 전체 교체 근거 없음|미정 / 낮음|이름 있는 대상의 rect/기준선/저장 픽셀에서 결함이 확인될 때만 해당 offset을 명세. native glyph 차이는 자동 결함으로 세지 않음|
|DP26-07 **열린 상태표검증**|현재모델/계획/설정copy는코드와과거표본,최신전체states미확인|미선택/선택불가,제안/실행/완료를혼동할위험의가설|U / 구조높음·사용성미확인|S03–05/S10–12를실제상태projection과대조,없는행동약속0/내부ID기본노출0/결정정보유지. 거짓표시재현시기존서비스의표현만수정|
|DP26-08 **열린 문서차이**|README상단346과옛인계,기존PLAN진행문구,설계docs과거pending, E5/E6|최신작업을누락하거나완료를오인할위험|P3 / 높음|이PLAN을단일현재계획으로;최종인계시README입구와소유문서링크갱신. 역사적숫자/원문명세보존|
|DP26-09 **미검증**|실제browserzoom/IME/forced-colors/screenreader/전체keyboard가부분범위, E1/E4|확대·입력·탐색결함이남을수있음;현재실패로단정불가|U / coverage높음|가능환경만실측,앱200%와구별. 포커스전체노출제품기준과WCAG위반판정구별. 설치/추가접근필요시분리|
|DP26-10 **미검증**|유효한성능기준선없음;이전30전환timing값은제외,E4|반응지연/메모리누수는아직가설|U / 낮음|체감/측정된재현이있을때만같은fixture로측정. staticDOM/media개수관찰을성능보장으로확대금지|
|DP26-11 **확정 제품명 변경·미구현**|사용자 Aethon 명명 결정; 현재 `index.html:1,13`, `app.py:1015`, `README.md:1,91`에 옛 사용자 표시 확인|제품 이름과 현재 화면·안내가 불일치. 결함 심각도 경쟁이 아닌 명시 요구이며 전역 치환은 저장/복구 호환성을 해칠 수 있음|요구 작업 / 높음|F의 표시·호환 목록 구분 후 현재 title/header/안내만 Aethon. 내부 namespace·경로·기존 초안/요청·import 불변을 회귀로 확인. 원명세/과거 캡처·보고서 보존|
|FG26-01 **실제 기능범위차이·별도backlog**|`production_tools.py:70–74` query와무관한scoped-snapshot, E5메모리관측|작은문맥조회는정직하게작동하나규모확장/검색효율미완성|대규모과업에서영향미정 / 높음|검색의scope/sourceID/빈결과/승인revision/예산 계약을별도계획. 새embedding/provider/검색엔진을디자인patch에끼우지않음|
|FG26-02 **코드+외부게이트 구분**|`chat_runtime.py:121`, `app.py:873`, registry는합성승인/주입제한, E5|일반프로젝트에안전한설정·전송동의·검증경로가아직제한;단순API403만남은것아님|일반live목표blocker / 높음|일반연결설정코드필요범위와계정/토큰계산/가격/live검증을별도인계. guard해제·모델silentfallback금지|
|FG26-03 **외부실검증차단**|과거falCDN403 및후속token발급403은다른단계;OpenAI/Grok/fal추가조합live미검증|완전한실생성→회수→등록및정산을현재보장할수없음|live목표blocker / 기존증거범위높음|권한/결과/비용근거확보후별도허용된시험만. 이번호출/키조회/공개fallback0|

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
|B0 **계획 정합화 완료·설명 체크포인트 반환**|입력전체읽기,현재코드/명세/스킬/증거정합화,이통합계획을부모대화에서설명할수있게반환|제품소스0변경. 부모가설명한후기존허용범위진행. 독립현재화면검토결과는DP목록에근거와함께합치고자동전면수정안으로쓰지않음|
|B0a **첫 구현: 제품 표시명**|DP11. 현재 표시·metadata·안내/관련 tests inventory를 닫고 Aethon으로 최소 치환. 내부 호환 계약과 원본·이력 유지|구현 전 baseline hash 확인. 기존 저장 키/인증 header/import/미디어 전역 불변, 표시와 재개 회귀, 1920/1280 헤더 비교. 새 로고/도메인/팔레트 없음|
|B1 **다음: 범위누락 확인**|DP04/07/09. S01–12의기존테스트/최신화면matrix완성;새캡처는미표본핵심경로에한정. 기획→모델→승인/불가→결과/복구→검토→출력경로의다음행동/상태정확성확인|현재헤더8쌍을반복촬영해진척으로세지않음. 증거로확정한finding만ID/심각도/원인/합격조건추가. 결함없으면해당구현skip|
|B2 **확인된 과업/상태 결함만 수리**|DP07및B1의P0/P1/P2재현. 모호한문구/막힌다음행동/입력보존/접근성의최소핸들러·표현patch|반례→최소수정→대조군→영향회귀. 제안/검토/승인/실행/회수각상태를서버값으로표시. 권한·비용검증을약화하지않음|
|B3 **사용자에게 보이는 위계**|DP06. 대표S07검토/승인상태와S05제작카드에서기본행동·보조행동·수동정보를관찰해필요한그룹/여백/label정리|먼저한대표상태의정확한selector·before/합격조건을설명. 값보존cleanup만무한반복하지않되근거없는테두리제거도금지. 구조변경필요시E대안검토후그범위만조정|
|B4 **시스템 정합성·선별 확대**|DP05. B2/B3에서실제쓰는color/font/spacing/radius/state mapping을공통role로정리;같은컴포넌트의관련화면에확대|activecomputed를기록. 값보존변경과의도된시각변경을별도diff/검증. 덮어쓴낡은규칙을지우려면전사용처/조건을확인;단순grep총수목표없음|
|B5 **고정 통합 검증**|선택한model상태→합성계획/허용→fake진행/회수→Take검토→정밀음악/자막→로컬출력/재개,영향받은부정경로|격리fixture/현재server로위험에맞게한대표여정. 외부media는fake명시,render는실제fileprobe. 변경영향밖의유료/12조합은제외. 같은빌드독립검토후freeze|
|B6 **인계·종료**|DP08. README입구·이PLAN상태/issue/evidence 갱신,디자인소유문서는담당자에게정확한수정요청|전후/실검사/미검증/외부gate/소스hash·cleanup. 점수없이종료조건판정. 알려진결함없이새로운장식pass를자동추가하지않음|

통합 담당은 제품 코드의 유일 writer다. 디자인/접근성/계약 검토는 기존 독립 세션의 읽기 전용 결과를 활용하며 같은 파일을 병렬 편집하지 않는다. 아직 시작하지 않은 새 CLI/서브에이전트 수를 성과로 세지 않는다. 독립평가가필요한pass는stabletarget을먼저고정하고서로의결론/검출결과를선행공유하지않는다. 이번은기존근거를정합화한계획이지새로운unanchoredcritique수행이아니다.

## H. 검증 설계·통과와 중단 조건

**같은 조건 캡처:** 현재 E1 allowlist인 합성작품1개/시험영상2·PNG1·WAV1 총1,066,575bytes,project fingerprint `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`를 기준으로 한다. 원본은읽기전용,실행은격리DB. viewport1920×1080/1280×900,DPR1,앱100%,같은장면/Take/trim/음원/자막/승인·선택,paused frame(선택1초,sequence편집0.5/원본0.75초)을 고정한다. 다른상태비교는상태명을명시한다. 앱150/200%와실제browser200/400%는별도다.

- **순수 시각 위험:** 실제served HTML/CSS/mediaJS hash,document/panel 치수,contain영상,시간축원점,대상computed색·font·크기,저장이미지픽셀확인. 현재같은8셀 영상높이431.91/364.91/378.98/311.98(1920),251.91/184.91/257.70/190.70(1280)을 비교 기준으로 보존한다. 이를새절대최소표준으로하지않으며감소가필요하면이유·대안을설명한다. nativecontrols/동적pixels를전체zero-diff로채점하지않는다.
- **흐름/비동기 위험:** 실제controller를쓰는기존NodeVM+controlledfetch로확정거절/unknown/지연성공/새입력/동일내용재편집/A→B→A/취소/더블클릭을검사. F07/DP01/FQ/DM기존guards는보존. 브라우저대역은frontend시험,DB저장성공증거아님.
- **생산/권한 위험:** plans/actions/grants/rights/price/version/receipt의기존contracttests,모델교체중job보존,unknown자동재제출0. fakeHTTP를live로부르지않는다. UI편집만으로provider/gate코드를바꾸지않는다.
- **미디어/출력 위험:** 시간·trim·순서·자막·음원과프레임양자화의기존실FFmpegfixture회귀. B5에서실제export를한다면격리데이터에만저장하고manifest/probe/재개결과를남긴다. 합성출력을생성모델성공으로표시하지않는다.
- **접근성:** 영향selector의label/name/role,Tab/Enter/Space/Escape/focus복귀/전체target노출,내부scroll끝,긴문자/앱배율/대비/forced-colors/reducedmotion을가능환경에서확인. WCAG와제품36/40/44px목표를분리한다. forced-colors·실zoom·screenreader·IME가실행불가면not-run과영향을기록하고대체측정을동일검증이라하지않는다.
- **코드·전체 회귀:** 현재330비HTTP가최신실행기준. 소스변경마다관련반례/회귀·JS구문/Python필요검사후최종고정점전체회귀1회. HTTP20은환경허용시별도실행·분모기록;과거20을더해350을실행했다고쓰지않는다. 새테스트는위험의반례를검증하며선언을그대로반복하지않는다. 이번계획에서는추가실행0.
- **실사용·성능:** 사람참가자시험없음. 과업성공률/혼란/속도개선은가설. 유효측정없는성능최적화는하지않는다. 실제사용자평가는후속계획이며이번완료를위해새고객모집/데이터전송을요구하지않는다.

**범위 완료:** 발견된in-scope재현결함이수리되고수용조건+영향회귀가통과,핵심S01–12상태coverage가성공/과거/미검증/외부차단으로빠짐없이표시,최종소스·화면·근거가같은빌드로연결되면종료한다. 새로운품질점수/90목표/경쟁사동등성/전체WCAG나제품출시완료를만들지않는다. 남는실행제약을해결된것처럼숨기지않는다.

**즉시 멈출 조건:** 기준source/fixture불일치,다른writer변경,새recipient/실고객자료/키·비용필요,정식도구거절,unknown외부작업. 해당행동만중단하고명확한사유·이미완료·미실행/불명상태를보고한다. 불필요한자동재시도/다른경로우회없음. 독립로컬문서·소스검토는가능범위계속한다.

**보존/롤백:** 배치직전수정대상snapshot/hash와diff보존. 승인·자산·비용원장/원본명세변경없음. rollback은그배치diff만대조하여역적용하고후속사용자변경과충돌하면멈춘다. reset/stash/commit/전체파일덮어쓰기/원본DB복원금지. 시작한임시서버는stop방법·포트·종료를기록하고검증공간을닫는다. 실제서버POST없는검사와격리fixture쓰기검사를구별한다.

## I. 스킬·도구 적용 장부와 한계

|도구|실제로 읽고/수행한 것|이 계획에 적용 / 실행하지 않은 것|
|---|---|---|
|Hallmark **2.0.0** `/Users/leesungmin/.agents/skills/hallmark/SKILL.md`|이번SKILL전체/redesign/app·Harnesses읽기. E5의정적sloplint는이전실제실행9FAIL/73REFLEX/15WARN|기존wiring/brand보존,appscope,control상태·역할token. 숫자는분류전후보. 이번renderlint·새lint실행없음,fullHallmark감사완료주장없음|
|Impeccable **4.7.1** `/Users/leesungmin/.codex/skills/impeccable/SKILL.md`|이번SKILL/shape/operate/audit전체,critique격리규칙부분읽기. 이전contextprobe exit127,설치경로에engine없던기록확인|Operate·과업/상태·근거계획을수동적용. detector/overlay/새context실행없음,자동다운로드안함. 다음UI편집직전craft-floor재독. fullcritique나score산출아님|
|Codex CLI|E5의read-only/ephemeral2세션과테스트는역사적실행|이번새세션없음. 새능력을상상하지않고필요하면좁은계약검토. SDK/API사용량·Library전송과별개|
|Library skill/도구|이번공식skill읽기+입력read1회성공,183행전체|입력검토만. helperupload중단은별개;재시도/직접경로전환0. 현재목록의전송도구존재를과거helper회복으로간주하지않음|
|Refero/기타개발MCP|E6 reference lock과부모가제공한독립조사재사용|이번새호출없음. 제품noMCP와개발도구를혼동하지않음. LSP의이전daemon불가를현재새거절로표시하지않고재설정안함|
|Ego Lite/실행기|E1은CLI0.6.0.20·UAChrome154·실localhost검증및종료증거|이번은저장이미지2개픽셀읽기만,새브라우저/서버0. 이후동일승인synthetic경로를정식심사로사용. 제어중계/보관미확인을localhost페이지외부요청0으로보장하지않음|

스킬 충돌 처리: 사용자·제품 기준이 우선한다. Hallmark의random theme/hero/80단어/중앙고정폭/강제clip/stamp/cleanGit요구를이편집기에기계적적용하지않는다(appscope자체도마케팅규칙을제외). Impeccable의새score/auto-variants/fonts/decorative motion이나darkmode추가를실행하지않는다. shape의인터뷰는이미확정된과업·톤·자료를다시묻는절차로사용하지않는다. 실제critique를후속수행한다면설치본의A/B격리를따르고수동동일맥락검토를공식critique성공이라고하지않는다.

## J. 현재 가능·환경 의존·외부 결정

- **지금 가능:** 계획 설명,독립결과정합,현재source/QA inventory,기존로컬테스트,동일합성범위의필요한실제화면검증과증거있는작은수정. 이번턴은계획문서만바꾸고실행하지않는다.
- **환경별 확인 필요:** 실제zoom/IME/screenreader/다중브라우저/렌더검출엔진. 미설치도구때문에새설치하거나지원되지않는명령을만들지않는다. 사용자가승인한합성프로젝트/Ego/localhost범위외전송이면먼저구체범위를분리한다.
- **디자인·CLI로 해소되지 않음:** FG26-01검색범위의별도기능설계,FG26-02일반프로젝트설정/동의/검증코드,FG26-03실제계정/가격/파일접근·청구검증. 제품모델활성화/새credentials/유료시험/배포는이번계획이허가하지않는다.
- **독립 검토:** 이미 수신된 현재스크린샷/계획 검토는 아래와 같이 반영했다. 추가 읽기 전용 검토가 있을 경우 실제 결과만 병합하며 미수신을 통과로 취급하지 않는다. 기존설계문서ownership은그대로다.
- **이번 수신된 독립 결론:** 새 제품 결함·새 점수는 없고 PL01 문서 입구 불일치와 PL02–05 계획 구체성 보완이다. selected/adopted/approved/playing을 구분하고, 차분한 승인 완료를 CTA 누락으로 판단하지 않는다. 비교 버튼 근접성은 DP26-06b 가설로 유지한다. 추가 결과가 없는 상태에서 새 디자인 pass를 발명하지 않는다.

변경 기록 — 2026-10-26: Library워크플로183행전체를대조하여 A–J통합계획 추가. 독립 PL01–05를 반영하고 명시적으로 요청된 현재 문서 입구2개만 정정했다. 최신 사용자 Aethon 명명/구현 지속 지시를 DP26-11·B0a에 추가했다. 소스/테스트121개,원본명세,역사적QA,DB·자산·키불변. 새테스트/브라우저/외부모델/설치/업로드실행0. 이전계획을아래에보존한다. 계획 설명 후 첫 구현은 B0a 표시명 변경, 이어 B1 coverage→필요한 B2–4→B5–6 검증·인계다. 단순 borderpatch로 곧장 넘어가지 않는다.

---

## 역사적 계획 — 아래 상태·시점은 당시 기록

### Loretune — 근거 확인 후 작은 묶음으로 진행하는 구현 계획

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

- **Hallmark2.0.0:** app-scope 정적 검출은 후보 목록. 이번 실제 sloplint 실행은 정적9FAIL/73REFLEX/15WARN이며 rendered 검사/독립 디자인팀의 detector 실행이 아니다. 마케팅 hero·80단어·중앙 고정컨테이너·random theme·일괄 overflow clipping/no-wrap·stamp 의무는 Loretune 요구보다 우선하지 않는다. 수치 목표로 코드를 바꾸지 않는다.
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
