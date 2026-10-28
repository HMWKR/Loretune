# Hallmark 정적 감사 — sloplint 기준선 트리아지 (Aethon 제작 스튜디오)

- 날짜: 2026-10-28 · 모드: **읽기 전용 `audit`**(Hallmark `references/redesign.md` "audit <target> stops here": 프로젝트 파일 변경 없음)
- 대상: 안정 스냅샷 `.omo/evidence/agent-tools-02-20261028/before/` (경로·줄번호는 스냅샷 기준, 프로젝트 루트 상대로 표기)
- 기준선: `.omo/evidence/agent-tools-02-20261028/design-gate/sloplint-before.json` (18 FAIL / 73 REFLEX / 16 WARN, `--scope app`, render off)
- 범위 밖(지시대로 미실행): 서버·브라우저·render 계층(`--render`/`--url`). 그래서 **R·R/J 계층 게이트(대비 실측·줄바꿈·가로 넘침 실측·화면 판정)는 이 문서에서 판정하지 않았다** — 해당 항목은 [미확인]으로 표기.

## 0. 요약 (4줄 판독, redesign.md §Before 3 형식)

1. **무엇을 위한 화면인가**: 음악 → 계획 → 장면 제작·검토 → 편집·출력을 한 작업대에서 처리하는 앱 화면(scope app). 랜딩 게이트는 해당 없음.
2. **잘 된 것(유지)**: `:root` 토큰 체계(`studio.css:4-65`)와 `.lt-ui` 계층이 대부분의 화면을 토큰으로 덮는다. 초점 링은 `--ui-focus`가 배경 대비 11.4~13.9:1. 모든 축소 모션 대체(`prefers-reduced-motion`)·강제 색 모드(`forced-colors`)가 있고, 분할바는 키보드(ARIA separator + 화살표)로도 조작된다.
3. **생성 티(게이트별)**: 간격 토큰 우회(24b ×72, 20px·rem 원시값), 같은 상태에 대한 규칙 여러 벌(비활성 4벌, 축소 모션 5벌), 버튼·제목·aria-label 안의 ` · ` 이어붙이기(63).
4. **실제로 고장/위험한 것**: 분할바 너비 조절이 끌기 전용(WCAG 2.5.7, High), 재생 헤드를 `left`로 매 프레임 이동(10a), 모바일 첫 화면에서 작업 영역이 AI 패널에 가려짐(이전 HTTP 트리아지 HHTTP-16과 일치), 그리고 **sloplint가 `.js` 파일을 전혀 읽지 않아**(요약 `files: 2`) 동적 UI 대부분이 기준선 밖이다.

## 1. 재현성·커버리지 확인 [검증됨]

| 확인 | 결과 |
|---|---|
| 스냅샷에 같은 명령 재실행 (`node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js --scope app --json`, cwd=before/) | 18/73/16, findings 107건 **기준선과 완전 동일**(집합 차 0). 산출: `design-audit/sloplint-snapshot-rerun.json` |
| sloplint가 읽는 확장자 | `sloplint.mjs:29,42` — `.html .css .jsx .tsx .vue .svelte .astro`만. **`.js` 무시** → 요약 `"files": 2`(index.html·studio.css). `general-chat-ui.js`·`chat-sidebar.js`는 인자로 넘겼지만 검사 0건. `scene-studio.js`·`motion-studio.js`·`studio-media.js`도 대상 아님 |
| scope app이 건너뛰는 게이트 | `references/flow.md` §App screens: "1, 6, 8, 9, 32, 42, 44, 46b, 58, 59, 66, 68, 77 to 79 and 81 to 83, and F8, F15 and F20" |

→ **결론**: 기준선의 0건이 JS 생성 DOM의 무결함을 뜻하지 않는다. §5에 JS 정적 수동 점검 결과를 따로 적었다.

## 2. FAIL 18건 — 전수 트리아지

등급: 사용자 기준(High=WCAG AA 위반·기능 고장 / Medium=시각 결함·모호한 문구 / Low=미세·잠재). 판정: **결함**(고칠 것) / **오탐**(근거와 함께 기각 제안 — 기각 확정은 소유자 몫) / **절차**(Hallmark 기록 형식).

| # | 게이트 | 위치 | 판정 | 무엇이 문제인가 / 근거 | 사용자 영향 | 수정(기존 토큰·컴포넌트 재사용) | 등급 |
|---|---|---|---|---|---|---|---|
| F-1 | 7a | studio.css:72 `button,.download{color:white}` | 결함(사문화) | `.lt-ui :where(button,.download)`(282, 같은 특이도·뒤쪽)가 `--ui-strong`으로 덮음. body가 `class="lt-ui lt-system"`(index.html:12)라 실제 화면엔 안 나옴 | 없음(유지보수 혼선) | `color:var(--ui-strong)`로 바꾸거나 레거시 줄에서 color 삭제 | Low |
| F-2 | 7a | studio.css:77 `input,select,textarea{color:white}` | 결함(사문화) | 290 `.lt-ui :where(input…){color:var(--ui-strong)}`(0,1,0)가 덮음 | 없음 | 동일 | Low |
| F-3 | 7a | studio.css:146 `.job a{color:white}` | 결함(실효) | 덮는 `.lt-ui` 규칙 없음 → 작업 카드 링크만 순백 #FFF, 나머지 본문은 `--ui-strong #F4F4F2` | 미세한 색 불일치(대비는 충분) | `color:var(--ui-strong)` | Low |
| F-4 | 7a | studio.css:148 `dialog{color:white}` | 결함(실효) | `.lt-ui dialog`(318·559)는 color를 정하지 않아 모든 대화상자 본문이 #FFF로 남음 | 대화상자와 본 화면 글자색 미세 불일치 | `color:var(--ui-strong)` | Low |
| F-5 | 7a | studio.css:220 `.skip-link{background:white}` | 결함(실효) | 토큰 밖 절대색. 대비 자체는 21:1로 안전 | 일관성 | `background:var(--ui-strong)` | Low |
| F-6 | 7a | studio.css:220 `.skip-link{color:black}` | 결함(실효) | 동일 | 일관성 | `color:var(--ui-canvas)` (기존 `--ui-on-primary`와 같은 쌍) | Low |
| F-7 | 20 | studio.css:1 | 절차 | Hallmark 스탬프 부재. 1행은 프로젝트 자체 주석. **사용자 기능과 무관**; Hallmark가 만든/폴리시한 파일에만 요구되는 기록 형식(gates.md §4 20) | 없음 | Hallmark polish를 채택할 때만 스탬프(+`shape: app screen`, 아래 기각·면제 줄) 추가. 채택 전엔 추가하지 않음 | Low(절차) |
| F-8 | 34 | studio.css:1 (html/body `overflow-x` 없음) | 결함(보호장치 부재) | html·body에 `overflow-x:clip` 없음. 가로 스크롤이 생겨도 막을 장치 없음. 실제 넘침 여부는 render 필요 [미확인]. 이전 HTTP 트리아지(구 소스)는 320px 열린 상태에서 `body_horizontal_overflow: 0` 관측 | 넘침 발생 시 WCAG 1.4.10 위반(High)로 승격 | `html,body{overflow-x:clip}` 추가(`clip`은 스크롤 컨테이너를 만들지 않아 sticky 유지). 단 추가 전 375·320 실측으로 잘리는 내용이 없는지 확인 | Low(잠정) |
| F-9 | 34 | studio.css:318 `.lt-ui dialog{width:min(640px,calc(100vw - 32px))}` | 결함(약함) | `100vw`는 스크롤바 폭 포함. 다만 dialog는 top layer·fixed 배치라 문서 가로 스크롤을 만들지 않고 32px 여백이 스크롤바(약 15~17px)를 흡수 [추정] | 실영향 낮음 | 같은 파일 934행이 이미 쓰는 레시피로 통일: `calc(100% - 2rem)` | Low |
| F-10 | 34 | studio.css:640 `.lt-notice-detail[open]{width:min(500px,calc(100vw - 24px))}` | 결함(약함) | absolute 팝오버. 900px 이하에선 696행이 static으로 바꿔 무력화. 901px 이상에선 500px가 항상 들어감 | 실영향 낮음 | `min(500px, calc(100% - var(--ui-space-6)))` 또는 `max-width:calc(100vw - …)` 대신 컨테이너 기준 | Low |
| F-11 | 34 | studio.css:1010 `dialog.agent-dialog…{width:min(1320px,calc(100vw - 32px))!important}` | 결함(약함) | F-9와 동일 + `!important` | 실영향 낮음 | `calc(100% - 2rem)`, `!important` 제거 가능 여부 확인 | Low |
| F-12 | 39a | studio.css:75 `button:disabled{opacity:.45;cursor:wait}` | 결함(사문화) | 286·505의 `.lt-ui` 규칙이 opacity:1·not-allowed로 덮음. 남아 있는 `cursor:wait`는 의미도 틀림(대기 아님) | 없음(레거시 혼선) | 75행 삭제 또는 286과 동일 값으로 | Low |
| F-13 | 39a | studio.css:728 `#reviewTake:not(:disabled){opacity:1!important}` | **오탐** | `:not(:disabled)` = 활성 상태 선택자. 비활성은 730행에서 색·`cursor:not-allowed`·네이티브 disabled 3채널 모두 충족 | 없음 | 기각 제안: `dismissed 39a · 728은 활성 상태, 730이 비활성 3채널` | — |
| F-14 | 48 | studio.css:946 `var(--border, #d5d5d5)` | 결함(잠재) | `--border` 토큰이 어디에도 정의되지 않음(grep 0건) → 폴백 #D5D5D5(밝은 회색). 정상 동작에선 chat-sidebar.js:294가 패널을 `.agent-chat-pane` 안에 넣어 988행이 `--ui-line`으로 덮지만, 사이드바 스크립트가 실패하면 어두운 화면에 밝은 테두리가 드러남. 945-955 블록 전체가 rem 원시값·`font-weight:600` | 평상시 없음 / 장애 시 시각 결함 | `border:1px solid var(--ui-line); border-radius:var(--ui-radius-control); padding:var(--ui-space-4)`; dl gap `var(--ui-space-1) var(--ui-space-3)`; dt `font-weight:var(--ui-weight-heading)` | Low |
| F-15 | 50 | studio.css:658 `#creatorReviewEditor>.row{grid-template-columns:1fr 80px}` | 결함(약함)·이미지 근거는 오탐 | 이 행에는 이미지가 없음(라벨·select·버튼). 다만 bare `1fr`는 긴 select 옵션 문자열에서 최소 콘텐츠 폭 때문에 넘칠 수 있음 [추정] | 좁은 인스펙터에서 넘침 가능 | `minmax(0,1fr) 80px` | Low |
| F-16 | 56 | studio.css:962 `.agent-sidebar{position:sticky;top:0}` (+963 헤더) | **오탐** | 헤더는 사이드바 자신의 `overflow:auto` 안에서 붙고, 사이드바는 바깥 스크롤러에서 붙음 → 서로 다른 스크롤 컨테이너. 경계 셸(1023)에선 relative. 이전 HTTP 실측 HHTTP-15도 "교차 면적 0" | 없음 | 기각 제안 | — |
| F-17 | 63 | index.html:23 `<small>24fps · 원곡 48kHz · 클립 오디오 음소거 · 짧은 원곡은 무음으로 채움<br>…` | 결함 | 성격이 다른 출력 규격 4개를 ` · `로 한 줄에 이어붙임. 이후 문장과 한 `<small>`에 섞임 | 출력 조건(무음 채움 등)을 놓치기 쉬움 → 문구 모호 | 기존 `.general-chat-card dl` 패턴처럼 `<dl>`(프레임률/원곡 샘플레이트/클립 오디오/짧은 원곡) 또는 줄바꿈 목록. 크기는 `--ui-meta` 유지 | Medium |
| F-18 | 76 | index.html:23 `<img id="timelineFrameImage" alt="…" hidden>` | **오탐** | 소스 없는 img는 `hidden`이고, index.html:418에서 PNG 미리 로드(`pending.onload`) 성공 후에만 `img.src=url; img.hidden=false`. 깨진 이미지가 보이는 경로 없음 | 없음 | 기각 제안 | — |

## 3. WARN 16건 — 전수 트리아지

| # | 게이트 | 위치 | 판정 | 근거 | 수정 | 등급 |
|---|---|---|---|---|---|---|
| W-1 | 3 | studio.css:529 `#track span{border-left:3px solid var(--ui-control)}` | 결함(잔재) | 현재 트랙은 studio-media.js:62가 `<button>`으로 다시 그림(`time-clips`) → 이 규칙은 버튼 안 `span`(검토 배지 등)에 새어 618·711·716이 `border-left-width`/`border:0`로 되막는 중. 현재 클립 표시는 724 `inset 2px var(--ui-marker)`와 신호가 둘 | 529의 `border-left` 삭제(선택 표시는 724 하나로) | Low |
| W-2 | 25 | studio.css:446 `#chatPanel>p{max-width:76ch;font-size:var(--ui-meta)}` | 결함 | 측정폭 1ch 초과 + 안내 문단을 12px(meta)로 | `max-width:65ch; font-size:var(--ui-item)` | Low |
| W-3 | 40 | studio.css:505 비활성 컨트롤 `color:var(--ui-control)!important` | 결함(일관성) | `--ui-control #858585` on `--ui-raised #242424` = **4.21:1**(계산 [검증됨]). 비활성 컨트롤은 WCAG 1.4.3 예외라 WCAG 위반은 아님. 하지만 비활성 전용 토큰 `--ui-disabled #A6A6A3`(6.36:1)이 있는데 505가 덮어씀. 비활성 규칙이 286/421/505/730 네 벌이고 글자색이 `--ui-disabled`/`--ui-control`/`--ui-muted`로 제각각. 이전 HTTP 실행의 FAIL 40(HHTTP-01, 4.21:1, "에이전트 설정 저장 · 호출 없음")과 **같은 원인** | 505를 `color:var(--ui-disabled)!important`로, 730의 `--ui-muted`도 `--ui-disabled`로; 286·421은 505로 흡수 | Medium |
| W-4 | 41 | studio.css:314 `.guided-card,.job,.timeline` | **오탐** | 다크 전용(`color-scheme:dark`) 화면이고 글자색은 `.lt-ui{color:var(--ui-strong)}`(497) 상속 → `--ui-panel` 위 15.64:1 | 기각 제안 | — |
| W-5 | 41 | studio.css:474 `.lt-panel-nav button[aria-selected=true]` | **오탐** | 글자색은 502 `--ui-strong` → `--ui-selected` 위 13.06:1 | 기각 제안 | — |
| W-6 | 41 | studio.css:544 `.lt-execution-card` | **오탐** | 상속 `--ui-strong` → `--ui-inset` 위 16.73:1 | 기각 제안 | — |
| W-7 | F3 | studio.css:80 | Finish 답변 | 앱 제목은 짧지만 한글 제목 2줄 이상 시 균형 줄바꿈이 도움 | `.lt-ui :where(h1,h2){text-wrap:balance; word-break:keep-all}` (선택) | Low |
| W-8 | F4 | index.html:19 "새 대화 만들기"·"대화 모델 선택 저장" | **오탐** | 두 버튼은 서로 다른 접힌 `<details>` 안의 제출 버튼이고 `class="primary"`도 아님. 문구도 "hero"를 전제(앱엔 hero 없음 — flow.md "no hero or fold") | 기각 제안. 단 진짜 F4는 §5 X-9 참고 | — |
| W-9 | F6 | studio.css:322 `.lt-status` | Finish 답변 | 표시 크기 아님(meta 12px). "N건" 같이 바뀌는 숫자가 들어가면 폭 흔들림 | `font-variant-numeric:tabular-nums`(327 `.lt-timecode`와 같은 방식) | Low |
| W-10 | F6 | studio.css:546 `.lt-state-chip` | Finish 답변 | 동일 | 동일 | Low |
| W-11 | F6 | studio.css:603 `.lt-review-state` | Finish 답변 | 숫자 거의 없음 → 적용 불필요 | 답변 기록만 | — |
| W-12 | F6 | studio.css:715 `.review-state-symbol` | **오탐** | 기호(✓ ○ × ↺) 전용, 숫자 아님 | 기각 제안 | — |
| W-13 | F6 | studio.css:981 `.agent-work-status` | Finish 답변 | "진행 2건 · 확인 필요 1건"처럼 1.5초 주기로 갱신(chat-sidebar.js:298) | `tabular-nums` | Low |
| W-14 | F7 | studio.css:85 컨테이너 레시피 7개 선택자 | 답변(앱에선 의도) | 앱 지침은 오히려 "one container recipe"를 요구(flow.md §App screens, Density) | 답변 기록만 | — |
| W-15 | F23 | index.html:1 meta description 없음 | 답변 | 로컬 작업 도구라 검색 노출 무관. `lang="ko"`·`<title>` 있음 | (선택) 1줄 추가 | Low |
| W-16 | F24 | studio.css:640 테두리 + `box-shadow:0 12px 36px` | Finish 답변 | 다크 바탕에서 넓은 그림자는 거의 안 보이고 테두리와 겹침 | 그림자를 `0 8px 24px var(--ui-shadow)`로 줄이거나 테두리만 | Low |

## 4. REFLEX 73건 — 게이트별 묶음

### 4-1. 랜딩 전용 게이트가 섞였는가 → **0건**

`--scope app`이 랜딩 게이트(1, 6, 8, 9, 32, 42, 44, 46b, 58, 59, 66, 68, 77~79, 81~83, F8, F15, F20)를 이미 건너뛰었다(flow.md §App screens 원문 위 표 참조). 남은 REFLEX는 **24b(72건)와 38iii(1건)뿐이고 둘 다 앱에도 적용되는 게이트**다. 다만 개별 문구에 랜딩 전제가 섞인 경우는 따로 기록:

- **W-8(F4)** 증거 문구의 "in the hero" — 앱엔 hero 없음("no hero or fold").
- **7a 수정 문구** "Tint the base toward the anchor hue" — 이 앱은 의도적 무채색 팔레트(anchor hue 없음, 22 게이트도 발화 안 함). 앱에서 맞는 수정은 "색조 입히기"가 아니라 **기존 토큰(`--ui-strong`/`--ui-canvas`)으로 치환**이다.
- **F23**(meta description)은 검색 노출용이라 로컬 도구엔 실익 없음.

### 4-2. 24b 간격 척도 이탈 — 72건 (실결함, 누적 승격 Medium)

- 근거: gates.md 24b "Off-scale spacing. Guard: three at most, each an optical nudge". 스캐일 토큰은 `--ui-space-1/2/3/4/6/8 = 4/8/12/16/24/32px`(studio.css:31-36).
- 개별은 1~2px 차이(Low)지만 72건 누적 → rigor §2 "누적 시 Medium 승격".
- 분포: 6px 27 · 10px 25 · 14px 7 · 3px 7 · 7px 5 · 5px 3 · 9px 2 · 2px 1 (값 기준, 한 줄에 여러 값 가능).
- 층별: **레거시 기반층(1~279행) 25건** — 이 중 72·77행은 `.lt-ui` 층(282·501)이 덮어 실효 없음, 79(`label` margin 10/5)·109·113·145 등은 아직 실효. **`.lt-ui` 층(280행~) 47건**은 모두 실효.
- 같은 요소에 대한 정의가 여러 벌: 예) `.timeline` 패딩 113(14px)·314(space-4)·487(10px)·527(14px)·860(space-3) **다섯 벌**, 툴바·플로우 내비 수직 패딩 92·243·244·302·308·344·380.

| 값 | 위치 예 | 권장 치환(기존 토큰만) |
|---|---|---|
| 2~3px | 112·142·523·546·610·650·748 | `--ui-space-1`(4px). 시각 미세조정이 꼭 필요하면 3개 이내로 남기고 기록 |
| 5~7px | 79·111·233·240·302·308·321·322·344·381·382·383·401·405·408·463·515·517·536·564·565·614·643·651·652·655·746 | 칩·뱃지 내부 = `--ui-space-1`, 바·툴바 수직 = `--ui-space-2`(8px) |
| 9~10px | 72·77·109·145·152·190·220·243·244·252·369·373·406·469·487·490·499·501·521·543·549·664·732·776 | `--ui-space-2`(8px). 입력·버튼 높이는 패딩이 아니라 기존 `min-height:40px`/`--ui-control-min`이 보장하도록 |
| 14px | 109·113·274·527·544·583·737 | `--ui-space-3`(12) 또는 `--ui-space-4`(16) — 카드 패딩은 314행처럼 `--ui-space-4`로 통일 |

24b가 잡지 못한 같은 계열: **20px 원시값 11곳**(99·105·113·242·255·367·379·383×2·387·444 — 4px 척도엔 맞지만 토큰에 20px 단계가 없음)과 rem 원시값 블록(945-955). 기존 단계로 맞추려면 `--ui-space-6`(24) 또는 `--ui-space-4`(16), 20px 거터를 꼭 유지해야 하면 그때만 `--ui-space-5:1.25rem` 1개 추가(소유자 결정).

### 4-3. 38iii — 1건 (오탐)

- studio.css:112 `.badge` — index.html:21 `<h2>샷 보드 <span id="shotCount" class="badge">0</span></h2>`. "강조 단어"가 아니라 **개수 표시 칩**(사실을 담은 값). gates.md §5 38iii의 대상(한 단어를 색·굵기로 띄움)과 다름.
- 처리: 면제(waive) 제안 — `waive 38iii · 샷 보드 제목 옆 0~N 개수 칩, 강조어가 아니라 목록 개수` (스탬프 채택 시).

## 5. 기준선 밖(정적 수동 점검) — sloplint가 못 본 결함

| # | 위치 | 무엇이 문제 | 왜 중요한가 | 수정(기존 것 재사용) | 등급 |
|---|---|---|---|---|---|
| X-1 | chat-sidebar.js:248-254 (`pointerdown/move/up`), 241-247(키보드) | 작업 공간/AI 패널 너비 조절이 **포인터 끌기 전용**. 키보드 대안은 있으나 WCAG 2.5.7(AA)은 "끌기 없는 단일 포인터 대안"을 요구(키보드는 대체 불가) | 운동 장애·트랙패드 사용자가 너비를 못 바꿈 | 사이드바 헤더(963 `.agent-sidebar-header`)에 기존 버튼 스타일로 "좁게/넓게" 2개 추가 → 이미 있는 `width(current ± 48, true)` 호출(키보드 Shift 단계와 동일) | **High** |
| X-2 | studio-media.js:72 `#timePlayhead.style.left=…%` (122 `tick`→`seek`→`updatePlayhead`, 매 rAF) | 재생 중 **`left`를 매 프레임 변경** = Floor 10a("Never animate … left"). 매 프레임 레이아웃 재계산 | 영상 디코딩과 겹쳐 재생 헤드 끊김·CPU 부하 | 821 `#timePlayhead`를 축 전체 폭 래퍼로 두고 `transform:translateX(calc(var(--playhead,0) * 100%))`(래퍼 폭 = 축 폭), JS는 `style.setProperty('--playhead', t/total)`만. 축소 모션 블록은 이미 있음 | Medium |
| X-3 | chat-sidebar.js:46 `let opened = true`, 215 `work.hidden = narrow.matches && opened && !activeDialog` | 900px 이하 첫 진입 시 AI 패널이 열려 **작업 영역(음악 입력 등) 전체가 숨겨짐**. 이전 HTTP 트리아지 HHTTP-16(F25: 1440에서 보이던 62단어가 375에서 숨음)과 같은 원인, 스냅샷에도 그대로 [검증됨: 코드] | 모바일 첫 사용자가 1단계(음악 입력)를 못 찾음 — 과업 영향 | 초기값을 `opened = !narrow.matches`로(데스크톱 동작 불변) | Medium |
| X-4 | studio.css:1004 `.agent-resizer::after{background:var(--ui-line)}` | 분할바의 평상시 시각 표시가 `--ui-line` on `--ui-canvas` = **1.62:1**(계산). 포커스·호버 때만 `--ui-control`(5.16:1) | 분할바를 컨트롤로 알아볼 근거가 약함 — WCAG 1.4.11(3:1) 위반 가능 [추정: 판정 해석 필요, 확정 시 High] | 평상시도 `var(--ui-control)` 또는 `--ui-disabled-edge`가 아닌 3:1 이상 토큰 | Medium |
| X-5 | studio.css:503 `button:hover{border-color:var(--ui-disabled-edge)}` | 호버 테두리를 "비활성" 토큰(#555)으로 → 평상시 `--ui-control`(on raised 4.21:1)보다 **호버 때 더 흐려짐**(on hover 1.77:1) | 호버가 "비활성처럼" 보이는 역신호 | `border-color:var(--ui-control)` 유지 또는 `--ui-marker` | Medium |
| X-6 | chat-sidebar.js:218 `toggle.textContent = opened ? 'AI 대화 · 열림' : 'AI 대화 열기'` | 열린 상태 라벨이 **상태(열림)**만 말하고, 누르면 닫힘(235). `aria-expanded`와 중복 낭독 | 버튼이 무엇을 할지 모호 — 문구 모호 | 열림 시 "AI 대화 닫기", 닫힘 시 "AI 대화 열기"(상태는 `aria-expanded`가 전달) | Medium |
| X-7 | ` · ` 이어붙이기(63) — index.html 215곳, general-chat-ui.js 12, chat-sidebar.js 19, scene-studio.js 9, motion-studio.js 13, studio-media.js 17 (띄어 쓴 ` · ` 기준 집계) | 버튼 라벨에 행동+면책을 이어붙임: chat-sidebar.js:37 "에이전트 설정 저장 · 호출 없음", general-chat-ui.js:7 "전송 내용 준비 · 전송 없음", index.html:19 "계획 미리보기 · 외부 전송 없음"; 제목: "타임라인 · 비파괴 편집", "실행 승인 · 모의 검증"; aria-label: studio-media.js:62 "…· 선택하면…" | 라벨이 길어져 줄바꿈(이전 HTTP 49a 13건의 배경), 낭독 시 구분자 소리 [추정] | 버튼은 동사만 남기고 면책은 바로 아래 기존 `.muted`/`small` 도움말 + `aria-describedby`로. **붙여 쓴 열거(`설정·자산·운영`, 134곳)는 표준 한글 가운뎃점이라 결함 아님** | Medium |
| X-8 | studio.css:654 `.creator-diagnostic pre{font:12px/1.55 ui-monospace,monospace}` | 토큰 밖 글꼴 리터럴(48, sloplint가 `font:` 단축형을 놓침). 936·938·949 `font-weight:600` 리터럴 | 일관성 | `font:var(--ui-meta)/1.55 var(--ui-font-timecode)`, `font-weight:var(--ui-weight-heading)` | Low |
| X-9 | studio.css:411 + index.html:14 (`#review.primary`, `#render.primary`) | `.lt-output-actions`에서 저장·승인·렌더 3개가 활성일 때 모두 채운 기본 버튼 → 나란히 2~3개(F4 실체) [추정: 동시 활성 여부는 상태 의존, render 미확인] | 다음 행동 우선순위 흐림 | 단계상 다음 행동 1개만 `.primary`, 나머지는 414·415의 raised 스타일 | Low |
| X-10 | studio.css:289 vs 792 | 초점 링 두 벌: 일반 `2px solid, offset 3px` / 컨트롤 `2px dashed, offset 2px` | 일관성(대비는 둘 다 충분) | 한 레시피로 | Low |
| X-11 | index.html:110 `<span class="lt-review-state" aria-label="Take N 검토: …">` · general-chat-ui.js:7 `<div id="generalChatReviews" aria-label>`·`#generalChatTurns` · index.html:19 `#memoryProposals` | 역할 없는 span/div에 aria-label(ARIA 1.2에서 generic 이름 금지 → 보조기기가 무시할 수 있음) | "Take N" 식별 정보가 낭독에서 빠질 수 있음 | span은 보이는 텍스트에 Take 번호 포함 또는 `role="img"`가 아닌 `sr-only`(798) 텍스트; div는 `<section>`+제목 또는 `role="region"` | Low |
| X-12 | studio.css:697 `.lt-notice-detail[open]>summary{min-height:24px;padding:0}` (≤900px) | 572의 44px를 열린 상태에서 24px로 낮춤 | WCAG 2.5.8(24px)은 경계 통과, 하네스 목표 44px 미달(위반 아님) | `min-height:44px` 유지 | Low |
| X-13 | index.html:19 `#chatPanel style="max-width:900px;margin:auto;padding:24px"` ↔ studio.css:230·335·444·492 `!important` 4곳 | 인라인 스타일을 CSS가 `!important`로 되덮는 구조. 같은 계열: index.html:36 `style="width:min(1000px,95vw)"`, motion-studio.js:6 `min(900px,95vw)` | 유지보수 위험 | 인라인 제거 → 335/444 규칙만 남기고 `!important` 제거, 대화상자 폭은 934 레시피로 | Low |
| X-14 | studio.css:277·494·586·788·844 | `prefers-reduced-motion` 블록 5벌(788은 `!important` 없음) | 중복(기능은 충족) | 1벌로 통합 | Low |

## 6. "Hallmark HTTP FAIL15/WARN1" 기록과의 대조

- 출처 [검증됨]: `docs/qa/REMAINING-WORK.md:43`("원래 FAIL15/WARN1은 문맥 해석으로 0PASS가 되지 않는다"), `docs/qa/codex-workflow-review-20261027/REPORT-ko.md:65`, 원 영수증 `.omo/evidence/first-demo-20261028/hallmark-agent-http-only/stdout.json`, 해석 `…/triage/report.json`.
- **두 실행은 같은 것을 잰 것이 아니다**:

| 항목 | 이전 HTTP 실행 | 이번 기준선 |
|---|---|---|
| 계층 | render 전용(`--url`, `files: 0`, `render: ran`, `--genre modern-minimal`) | 정적 전용(`render: off`, `files: 2`) |
| 소스 | 2026-10-28 02:51Z 실행 서버. sha256: index.html `45e3f364…`, studio.css `cf1ec74f…`, chat-sidebar.js `e15b31d3…`, general-chat-ui.js `f92daed3…` | 스냅샷 sha256: index.html `be666645…`, studio.css `8e9b9acf…`, chat-sidebar.js `1709be3c…`, general-chat-ui.js `696ad613…` (**4개 다름**; motion-studio.js·scene-studio.js만 동일) |
| 결과 | FAIL 15 = 40×1 · 49a×13 · 56×1 / WARN 1 = F25 | FAIL 18 / REFLEX 73 / WARN 16 |

- 겹치는 원인 3개:
  1. **40 대비 4.21:1** — HTTP FAIL(HHTTP-01, 비활성 "에이전트 설정 저장 · 호출 없음") = 이번 W-3(studio.css:505). 같은 원인(`--ui-control` on `--ui-raised`), 정적 계층은 WARN·render 계층은 FAIL로 등급만 다름. W-3 수정으로 두 기록이 함께 닫힘(재측정 필요).
  2. **56 sticky** — HTTP(`agent-dialog-heading`+`agent-resizer`)와 이번 F-16(962 사이드바+헤더)은 같은 계열의 오탐(서로 다른 스크롤 컨테이너·교차 면적 0).
  3. **F25 모바일 숨김** — HTTP WARN = 이번 X-3. 이전 트리아지는 "의도된 절충"으로 해석했으나 발견 가능성 문제를 잔여로 남김 → 이번엔 수정안(`opened = !narrow.matches`) 제시.
- 이번 정적 계층이 볼 수 없는 것: **49a 13건(320·1024px 버튼 줄바꿈)**. 이전 트리아지는 "닫힌 disclosure 안의 미표시 기하"라 실화면 재현 안 됨이라고 해석. 현재 소스는 해시가 달라 그 해석을 그대로 승계할 수 없음 [미확인] → render 재실행 필요. X-7(버튼 라벨에 면책 이어붙이기)이 길이 원인 중 하나.
- 합산 금지: 15+18 같은 합계는 의미 없음. 정직한 현재 상태는 **"정적 계층 18/73/16(이 문서로 실결함·오탐 분류) + render 계층은 구 소스 기준 15/0/1이며 현재 소스 미측정"**. 어느 쪽도 0 PASS가 아니고, 이 문서도 기각·면제를 확정하지 않는다(제안만).

## 7. 우선순위 (가장 가벼운 깊이 = polish로 해결 가능)

Hallmark 깊이 판정: 아래는 모두 **polish**(요소·토큰 단위 제자리 수정)로 해결되고 레이아웃 재구성은 필요 없다.

1. High: X-1(분할바 단일 포인터 대안).
2. Medium: W-3(비활성 색 토큰 통일 — HTTP FAIL 40도 함께), X-2(재생 헤드 transform), X-3(모바일 첫 화면), X-5(호버 테두리), X-6·X-7·F-17(문구), X-4(분할바 표시 대비 — 해석 확정 시 High), 4-2(간격 토큰 일괄 치환).
3. Low: F-1~F-6(7a 토큰 치환), F-9~F-11·F-15, W-1·W-2, X-8~X-14, F6 tabular-nums.
4. 오탐 기각 제안(소유자 확정 필요): F-13, F-16, F-18, W-4~W-6, W-8, W-12, 38iii.
5. 절차: F-7 스탬프와 기각·면제 기록은 Hallmark polish를 채택할 때만(`shape: app screen` + `dismissed …` 줄).

## 8. 정직 보고

- **한 일**: 기준선 107건 전수 분류(FAIL 18·WARN 16 개별, REFLEX 73 게이트별), 스냅샷 재실행으로 기준선 동일성 확인, sloplint `.js` 미검사 확인, JS 6개 파일 정적 수동 점검(14건 추가), 이전 HTTP 기록과 해시·계층 대조, 토큰 대비 계산.
- **안 한 일**: render 계층·브라우저 실측(지시상 금지) → 가로 넘침(F-8~F-11), 버튼 줄바꿈(49a), 분할바·출력 버튼 실상태(X-4·X-9)는 [미확인]. 화면낭독기 실사용 미확인. 프로젝트 파일 수정 없음.
- **가정·추측**: F-9 스크롤바 흡수, F-15 넘침 가능성, X-4 WCAG 1.4.11 해당 여부, X-7 낭독 방식은 [추정].
- **산출물**: 이 문서, `design-audit/sloplint-snapshot-rerun.json`(+빈 `.stderr`).
