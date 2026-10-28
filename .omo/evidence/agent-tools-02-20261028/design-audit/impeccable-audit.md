# Aethon 기술 품질 감사 (impeccable audit · Operate 모드)

- 대상: 안정 스냅샷 `.omo/evidence/agent-tools-02-20261028/before/` — `index.html`(1119줄), `studio.css`(1037줄), `chat-sidebar.js`, `general-chat-ui.js`, `scene-studio.js`, `motion-studio.js`, `studio-media.js`. 경로는 프로젝트 루트 기준이고 줄 번호는 스냅샷 기준이다.
- 방식: 읽기 전용 정적 감사. 서버·브라우저·렌더 모드는 쓰지 않았다. 따라서 **렌더 결과(실제 375px 화면, 포커스 이동, 스크린리더 낭독)는 보지 않았다.** 렌더가 필요한 항목에는 [추정]을 붙였다.
- 도구 실행 기록
  - `impeccable context --target index.html`: 정상 실행. PRODUCT.md·DESIGN.md가 없고 기존 시각 구현이 디자인 기준(SCOPED_EXISTING_ALLOWED)이라고 판정했다. 감사는 이 판정대로 기존 구현을 기준으로 진행했다.
  - `impeccable detect --json --no-config <index.html+studio.css 사본 폴더>`: 정적 파일 모드. 종료코드 2, 결과 15건. 원본 결과는 `design-audit/impeccable-detect-static.json`에 있다. 분류는 아래 §6에 적었다.
  - 대비 계산: `studio.css:4-64` 토큰 값으로 WCAG 상대휘도 공식을 직접 계산했다(§5).
  - HTML 파서 검증: `html5lib`로 `index.html:40`의 잘못된 option 구문을 파싱해 실제 옵션 수를 확인했다.

## 1. 감사 점수

| # | 영역 | 점수 | 핵심 발견 |
|---|---|---|---|
| 1 | 접근성 | 3 | ≤359px에서 Label-in-Name 위반(A), 시간 비례 컷 버튼이 24px보다 작아짐 |
| 2 | 성능 | 2 | 숨겨진 탭에서도 1.5초마다 전체 상태를 폴링, 원본 파일을 썸네일로 사용하고 lazy 로딩 없음 |
| 3 | 테마·토큰 | 3 | 토큰 체계는 좋음. general-chat 블록·인라인 스타일에 토큰 이탈 |
| 4 | 반응형 | 3 | 모바일 44px 타깃은 대체로 충족. 글자 크기 150·200%에서 넘칠 위험, 모바일 첫 화면이 사이드바로 덮임 |
| 5 | 구현 일관성 | 2 | 잘못된 마크업 때문에 기능이 사라짐, `!important` 58개, reduced-motion 블록 5개 중복, CSS 세대 3겹 |
| **합계** | | **13/20** | **Acceptable** — 다룰 일이 상당히 남음 |

### 구현 일관성 판정 — 조건부 FAIL

토큰(`studio.css:4-64`)과 상태 어휘(aria-pressed, aria-current=step, tab 패턴)는 제품 고유의 일관된 체계다. 그러나 다음 두 가지 때문에 조건부 FAIL로 판정했다.

- 정적 마크업 오류로 기능 하나가 사라졌다(H1).
- 레거시 CSS(`studio.css:66-279`)에 `.lt-ui` 계층(280~)과 후속 패치(791~, 857~, 933~)가 겹겹이 덮여 있다. 같은 속성이 3~5곳에서 재정의된다.

## 2. 요약

- 건수: **High 3 / Medium 15 / Low 10** (High와 Medium의 정의는 작업 지시를 따랐다)
- 우선 조치
  1. H1 연출 취향 "이 IP의 기본 취향" 옵션이 마크업 오류로 사라짐(기능 결함)
  2. H2 ≤359px 단계 버튼 "4 출력"이 접근 가능한 이름 "4 편집·출력"에 포함되지 않음(WCAG 2.5.3 A)
  3. H3 시간 비례 컷 버튼 `min-width:0`, 간격 0 → 24px 미만(WCAG 2.5.8 AA, 예외 미성립 [추정])
  4. M1 모든 모달이 열리면 첫 포커스가 작업과 무관한 "AI 대화 열기"에 감
  5. M8 숨겨진 탭에서도 1.5초 폴링

## 3. 상세 발견 (심각도순)

### High

#### H1. 연출 취향 적용 범위 옵션이 마크업 오류로 사라짐
- 위치: `index.html:40` — `<option value="song">현재 작품의 예외</option value="ip">이 IP의 기본 취향</option>`
- 무엇이 문제인가: 두 번째 `<option>`의 여는 태그가 없다. 그 자리에 속성이 붙은 닫는 태그 `</option value="ip">`가 있다.
- 사용자 영향: 적용 범위 select에는 "현재 작품의 예외" 한 개만 보인다. `index.html:599`의 제출 로직은 `f.get('scope')==='song'?song():null`로 IP 단위 취향을 지원하지만, UI에서 그 값을 고를 수 없다. IP 기본 취향 기능 전체에 도달할 수 없다.
- 증거 [검증됨]: html5lib 파싱 결과 `[('song','A')]` — 옵션은 1개이고 두 번째 텍스트는 select 안의 떠도는 텍스트 노드가 된다.
- 수정: `</option><option value="ip">이 IP의 기본 취향</option>`로 고친다.
- 분류: 구현 일관성 · 명령 `/impeccable harden`

#### H2. ≤359px 단계 버튼에서 보이는 이름이 접근 가능한 이름에 없음
- 위치: `index.html:1061-1066`(shortStages, `button.setAttribute('aria-label',label)`), `studio.css:589-594`(≤359px에서 `.lt-stage-short`만 표시)
- 무엇이 문제인가: ≤359px에서는 "4 출력"이 보인다. 그런데 접근 가능한 이름은 `aria-label="4 편집·출력"`이다. "4 출력"은 이 이름의 부분 문자열이 아니다.
- 사용자 영향: 음성 제어 사용자가 화면에 보이는 "4 출력"을 말해도 버튼이 반응하지 않는다. 나머지 1~3단계는 짧은 이름이 긴 이름의 앞부분이라 통과한다.
- 기준: WCAG 2.5.3 Label in Name(A) 위반
- 증거 [검증됨]: 코드 대조 — `shortStages={'1':'1 음악','2':'2 계획','3':'3 장면','4':'4 출력'}`, 원래 라벨은 `index.html:17`의 "4 편집·출력"
- 수정: 짧은 라벨을 긴 이름의 앞부분으로 바꾼다(`'4':'4 편집'`). 또는 aria-label을 제거하고, 전체 라벨 span에 기존 `.sr-only`(`studio.css:798`)를 적용해 숨김 텍스트로 둔다.
- 분류: 접근성 · 명령 `/impeccable clarify`

#### H3. 시간 비례 타임라인 컷 버튼이 24×24px보다 작아질 수 있음
- 위치: `studio-media.js:62`(`style="width:${c.duration/total*100}%"`), `studio.css:816-817`(`#track.time-clips { gap:0; overflow:hidden }`, 버튼 `min-width:0`)
- 무엇이 문제인가: 너비가 전체 길이에 비례하고 최소값이 없다. 예를 들어 3분 편집에서 0.5초 컷은 트랙 폭 약 700px 기준으로 2px 남짓이 된다. 버튼 사이 간격이 0이라 SC 2.5.8의 간격 예외도 성립하지 않는다.
- 사용자 영향: 터치·저정밀 포인터 사용자가 짧은 컷을 누를 수 없거나 옆 컷을 잘못 누른다.
- 예외 판정 [추정]: "동등한 다른 컨트롤"이 있는지 검토했다. `#sequenceSeek` 슬라이더로도 위치를 옮길 수 있지만, 컷 시작점으로 정확히 이동하는 동등 기능은 아니다. 그래서 예외가 성립하지 않는다고 판단했다. 렌더 실측은 하지 않았다.
- 기준: WCAG 2.5.8 Target Size Minimum(AA)
- 수정: `.lt-ui #track.time-clips button`에 `min-width:24px`을 주고, 컨테이너의 `overflow:hidden`을 `overflow-x:auto`로 바꾼다. 비례 표현은 유지되고 짧은 컷만 최소 폭을 갖는다. 기존 `scroll-padding`·`--ui-space-*` 토큰을 재사용한다.
- 분류: 반응형·접근성 · 명령 `/impeccable adapt`

### Medium

#### M1. 모든 모달의 첫 포커스와 시각 최상단이 "AI 대화 열기" 버튼
- 위치: `chat-sidebar.js:257-258`(`main.prepend(launcher)`), `studio.css:1008`(`.agent-dialog-launcher { display:block; margin:0 0 var(--ui-space-3) auto }`)
- 무엇이 문제인가: `prepareDialog`가 모든 `<dialog>`의 맨 앞에 런처를 넣는다. 대상에는 렌더 확인(`#renderConfirm`), 보관, 사용권 대화상자도 포함된다. 네이티브 `showModal()`은 첫 포커스 가능 요소에 초기 포커스를 준다.
- 사용자 영향: 키보드·스크린리더 사용자는 모달을 열 때마다 작업과 무관한 버튼에서 시작하고, 제목보다 런처를 먼저 듣는다. 시각적으로도 제목 줄 위에 버튼이 따로 떠 있어 위계가 흐트러진다.
- 수정: 런처를 각 대화상자의 기존 `.row`(h2 + 닫기) 안, 닫기 버튼 앞에 넣는다. 확인 대화상자의 기본 포커스는 기존 버튼(`#dismissRender` 등)에 `autofocus`로 지정한다.
- 기준 관련: 2.4.3 Focus Order(위반 경계)
- 명령 `/impeccable layout`

#### M2. 작업 설정(검토) 패널에서 Esc를 누르면 오른쪽 패널 전체가 닫힘
- 위치: `chat-sidebar.js:285`(sidebar keydown Escape → `closeAgent()`)
- 무엇이 문제인가: 대화 패널은 열린 `<details>`부터 닫도록 처리한다(`chat-sidebar.js:286`). 그러나 설정 패널(인스펙터 이동본)에는 같은 처리가 없다. 검토 이유 textarea에 입력하던 중 Esc를 누르면 패널 전체가 사라지고 포커스가 토글로 이동한다.
- 사용자 영향: 작업 맥락을 잃고 다시 찾아 들어가야 한다. 초안은 저장소에 남는다.
- 수정: 286행 로직을 settings pane에도 적용한다. 또는 `event.target`이 `input, textarea, select`이면 무시한다.
- 명령 `/impeccable harden`

#### M3. ≤900px 첫 진입 시 작업 영역이 숨겨지고 AI 사이드바가 화면을 차지함 [추정]
- 위치: `chat-sidebar.js:46`(`let opened = true`), `chat-sidebar.js:215`(`work.hidden = narrow.matches && opened && !activeDialog`), `studio.css:1026-1029`
- 무엇이 문제인가: 첫 진입에 음악 입력·빈 상태 안내("첫 작품을 만들어 보세요")가 들어 있는 `.agent-work`가 숨겨진다. 모델이 연결되지 않은 상태에서도 AI 대화 화면이 첫 화면이 된다.
- 사용자 영향: 모바일 신규 사용자가 첫 작업을 시작할 위치를 찾기 어렵다.
- 증거: 코드 경로만 확인했다. 렌더는 보지 않았다.
- 수정: 초기값을 `opened = !narrow.matches`로 바꾼다.
- 명령 `/impeccable onboard`

#### M4. 오류 필드가 프로그래밍적으로 표시되지 않음
- 위치: `studio.css:291`(`[aria-invalid="true"]` 스타일만 있음), HTML·JS 전체에서 `aria-invalid` 설정 0회 [검증됨]
- 무엇이 문제인가: 서버 검증 오류(음악 구간, 예산, 사용권 등)는 전역 `#notice`나 `.dialog-status` 문장으로만 알린다. 어느 입력이 틀렸는지 필드 단위로 연결되지 않는다.
- 사용자 영향: 스크린리더 사용자는 오류가 난 필드를 찾아야 한다. 오류 스타일은 준비만 돼 있고 쓰이지 않는다.
- 수정: 기존 검증 경로(`scene-studio.js:99`의 `invalid.focus()` 위치, `creatorError` 결과)에서 해당 입력에 `aria-invalid="true"`와, `.dialog-status` id를 가리키는 `aria-describedby`를 설정한다.
- 기준: 3.3.1 보강
- 명령 `/impeccable harden`

#### M5. 오류 메시지 요소에 role=status를 메시지 삽입 시점에 붙임
- 위치: `studio-media.js:28` — `const err=(el,text)=>{el.textContent=text;el.setAttribute('role','status');}`
- 무엇이 문제인가: 라이브 영역은 내용이 바뀌기 전에 이미 존재해야 낭독된다. 텍스트를 넣는 순간 역할을 붙이면 첫 오류가 낭독되지 않을 수 있다.
- 기준: 4.1.3 Status Messages
- 수정: 해당 요소를 만들 때 `role="status"`를 부여하고, `err`는 텍스트만 바꾸게 한다.
- 명령 `/impeccable harden`

#### M6. 한국어 어절 줄바꿈이 버튼에만 적용됨
- 위치: `studio.css:185`, `studio.css:293`(`p, li, h1, h2, label`은 `overflow-wrap:anywhere`만 있음), `studio.css:187`(버튼만 `word-break:keep-all`)
- 무엇이 문제인가: 제목(`#shotTitle`), 안내문, 라벨, summary, `dd`가 음절 단위로 끊긴다. 예: "렌더 대기열에 추/가". 버튼과 일부 요소(`studio.css:623, 647, 656, 684, 744, 752`)만 어절 단위라 화면 안에서도 줄바꿈 방식이 섞여 있다.
- 수정: `.lt-ui :where(p,li,h1,h2,h3,label,summary,dd,small) { word-break:keep-all; }`를 추가한다. 긴 URL·해시 대비로 기존 `overflow-wrap:anywhere`는 유지한다.
- 명령 `/impeccable typeset`

#### M7. 앱 내 글자 크기 150·200%에서 고정 폭 컨트롤이 넘침 [추정]
- 위치
  - `studio.css:483`(`#compareButton { max-width:112px }`)과 `studio.css:631`(`min-width:144px; white-space:nowrap`)이 충돌 → 폭이 144px로 고정되고 줄바꿈이 없다.
  - `studio.css:658`(`#creatorReviewEditor>.row { grid-template-columns:1fr 80px }`) — "미저장 검토 초안 지우기"(keep-all)가 80px 열에 들어간다.
  - `studio.css:380-381`(>900px에서 `.flow-nav` nowrap, 넘침 처리 없음)
- 사용자 영향: 저시력 사용자가 앱의 "글자 크기" 설정(`index.html:14`, `index.html:703`)을 켜면 버튼 글자가 테두리 밖으로 넘치거나 단계 바가 가로로 넘친다.
- 수정
  - 483행 `max-width`를 제거하고 631행 `nowrap`을 해제한다.
  - 열 정의를 `minmax(80px,auto)`로 바꾼다.
  - `.flow-nav`에 `overflow-x:auto`를 모든 폭에 적용한다(≤900px의 468행 규칙을 승격).
- 명령 `/impeccable adapt`

#### M8. 숨겨진 탭에서도 1.5초마다 전체 상태를 폴링
- 위치: `index.html:874-875` — `setInterval(async()=>{ if(busy||!state||pollReadsInFlight>=2)return; …},1500)`
- 무엇이 문제인가: `document.hidden` 검사가 없다. 같은 저장소의 `chat-sidebar.js:298`에는 검사가 있다.
- 사용자 영향: 백그라운드 탭에서도 계속 네트워크 요청과 JSON 비교·재렌더가 일어나 배터리와 CPU를 쓴다.
- 수정: 시작 조건에 `document.hidden`을 추가하고, `visibilitychange`에서 즉시 1회 갱신한다.
- 명령 `/impeccable optimize`

#### M9. 원본 미디어 파일을 썸네일로 쓰고 지연 로딩이 없음
- 위치
  - `index.html:114`(샷 목록 `<img class="thumb" src="${asset(t)}">`, 48×40 표시)
  - `index.html:115`(take 스트립)
  - `index.html:425`(자산함: 범위 "이 로컬 작업실 전체"면 모든 take 이미지)
  - `index.html:554`(`#assetSearch.oninput=drawLibrary` — 키 입력마다 innerHTML 전체 재생성)
- 무엇이 문제인가: 업로드 상한이 16MB인 원본을 썸네일에 그대로 쓰고, `loading="lazy"`, `decoding="async"`, `width/height`가 없다.
- 사용자 영향: 자산이 많아지면 대화상자를 열거나 검색할 때 끊긴다. 이미지 크기 미지정으로 레이아웃 이동(CLS)도 생길 수 있다.
- 수정: 기존 마크업에 `loading="lazy" decoding="async" width height`를 추가하고, 검색 입력은 150ms 디바운스한다. 새 프레임워크는 필요 없다.
- 명령 `/impeccable optimize`

#### M10. general-chat 블록이 토큰을 쓰지 않음
- 위치: `studio.css:945-955` — `border:1px solid var(--border, #d5d5d5)`(`--border` 미정의), `border-radius:.65rem`, `gap:.35rem .8rem`, `margin-block:.8rem`, `padding:1rem`
- 무엇이 문제인가: 사이드바 호스트 밖에서 렌더되면 어두운 화면에 밝은 회색 테두리(#d5d5d5, 패널 대비 11.7:1)가 그려진다. `general-chat-ui.js:21`의 비사이드바 경로가 이 경우다. 반경과 간격도 토큰 스케일(`--ui-radius-*`, `--ui-space-*`) 밖이다.
- 수정: `var(--ui-line)`, `var(--ui-radius-panel)`, `--ui-space-1/2/3/4`로 치환한다. `studio.css:988`의 사이드바 재정의는 그대로 둔다.
- 명령 `/impeccable polish`

#### M11. CSS 재정의가 겹겹이 쌓임 (구현 일관성, 체계적)
- 증거 [검증됨]
  - `!important` 58개
  - `prefers-reduced-motion:reduce` 블록 5개 중복(`studio.css:277, 494, 586, 788, 844`)
  - 버튼 규칙 3세대(`studio.css:72` → `282` → `502`)
  - `#chatPanel` 인라인 스타일(`index.html:19`, `max-width:900px; padding:24px`)을 `!important` 3곳(`studio.css:335, 444, 492`)이 다시 덮음
  - 인라인 스타일: `index.html:36`(compareDialog), `motion-studio.js:6-7, 44`
- 사용자 영향: 직접 영향은 없다. 다만 다음 수정이 의도치 않은 화면에 새고, 상태 스타일이 일관되지 않을 위험이 커진다.
- 수정: 레이아웃 변경 없이 중복 블록을 하나로 합치고, 인라인 스타일을 기존 클래스·토큰으로 옮긴다.
- 명령 `/impeccable distill`

#### M12. 선택 가능한 카드형 버튼의 경계가 거의 보이지 않음 [추정]
- 위치
  - `studio.css:720`(`#takes button { border-color:var(--ui-line); background:var(--ui-panel) }`)
  - `studio.css:381`(flow-nav 버튼 `background:transparent; border-color:transparent`)
  - `studio.css:717`(`.shot` 투명)
- 계산: `--ui-line` #383838 테두리는 canvas 대비 1.62:1, panel 대비 1.47:1이다. 버튼 배경 panel과 canvas의 차이는 약 1.1:1이다.
- 사용자 영향: 텍스트가 있어 WCAG 1.4.11 위반으로 단정하지는 않는다. 다만 저시력 사용자에게는 무엇을 누를 수 있는지 잘 보이지 않는다.
- 수정: 비선택 테두리를 이미 쓰는 `--ui-control`(#858585, panel 대비 4.67:1)로 통일한다.
- 명령 `/impeccable polish`

#### M13. 일반 div·span의 aria-label이 보조기술에서 무시됨
- 위치
  - `index.html:19`(`#memoryProposals`), `index.html:23`(`#timelineProposals`), `index.html:24`(`#executionCards`), `index.html:31`(`#mediaActionCards`)
  - `general-chat-ui.js:7`(`#generalChatReviews`, `#generalChatTurns`)
  - `studio-media.js:156`(`#sequenceCaption`)
  - `index.html:110`(`studioBadge` span)
- 무엇이 문제인가: ARIA 1.2는 generic 역할의 이름 지정을 금지한다. 붙여 둔 이름이 낭독되지 않는다.
- 수정: 영역이면 `role="region"`이나 `role="group"`을 추가하거나 기존 `section`으로 바꾼다. 배지 span은 aria-label을 지우고, 보이는 텍스트(이미 있음)를 그대로 쓴다.
- 명령 `/impeccable harden`

#### M14. 일반 대화 결과를 다시 그릴 때 포커스를 잃음
- 위치: `general-chat-ui.js:58`(`#generalChatTurns` innerHTML 전체 교체)
- 무엇이 문제인가: 같은 파일의 검토 카드(`general-chat-ui.js:53-56`)는 포커스를 복원하지만 결과 카드에는 그 처리가 없다. 상태 폴링으로 다시 그려지면 "대화 작업 중단"이나 "… 제작안 검토" 버튼에 있던 포커스가 body로 사라진다.
- 기준: 2.4.3 Focus Order
- 수정: 56행 복원 패턴(`data-general-cancel`, `data-general-review-action` 키로 다시 focus)을 그대로 재사용한다.
- 명령 `/impeccable harden`

#### M15. 음원 파일 입력의 라벨이 용도가 아니라 형식 목록임
- 위치: `index.html:21` — `<label>WAV / MP3 / M4A / FLAC / OGG<input name="file" type="file" …>`
- 무엇이 문제인가: 접근 가능한 이름이 "WAV / MP3 / M4A / FLAC / OGG"다. 무엇을 올리는 칸인지 말하지 않는다. 다른 파일 입력은 "새 take · 기존 이미지/영상", "GLB 파일"처럼 용도를 말한다.
- 기준: 2.4.6 Headings and Labels(AA)
- 수정: `음원 파일 (WAV·MP3·M4A·FLAC·OGG)`
- 명령 `/impeccable clarify`

### Low

- **L1. 다크 테마만 있음** — `studio.css:4`(`color-scheme:dark`), `prefers-color-scheme` 분기 0개 [검증됨]. 제작 도구라는 사용 맥락에서는 타당한 선택일 수 있다. 결함 여부는 사용자 결정이 필요하다. 라이트가 필요해지면 `:root` 토큰만 재정의하는 구조라 비용이 낮다.
- **L2. 포커스 링 형태 혼재** — 실선 2px·offset 3(`studio.css:159, 289`)과 점선 2px·offset 2(`studio.css:792-793`)가 섞여 있다. 하나로 통일한다(대비는 둘 다 충분 — 집중색 canvas 대비 13.9:1).
- **L3. 하드코딩 색 잔존** — `studio.css:72, 77, 146, 148`(`color:white`), `studio.css:220`(skip-link white/black). 대부분 `.lt-ui` 규칙이 덮지만 `dialog`(148)와 `.job a`(146)는 실제로 적용된다. `--ui-strong`, `--ui-canvas`로 바꾼다.
- **L4. 측면 강조 테두리(디텍터 side-tab)** — `studio.css:529`(`#track span border-left:3px`), `studio.css:732`(`.production-review-error border-left:2px var(--ui-error)`). craft-floor는 1px 초과 측면 색 테두리를 금지한다. 1px 또는 전체 테두리로 바꾼다.
- **L5. 트랙 클립 장면명이 말줄임되고 전체 이름은 title로만 제공** — `studio.css:616`, `index.html:116`(`title`이 포커스 불가 span에 있음). 키보드·터치 사용자는 전체 이름을 볼 수 없다. 두 줄 줄바꿈을 허용하거나 기존 `#creatorMobileContext`처럼 선택 시 전체 이름을 보여 준다.
- **L6. 모바일 알림 summary 높이 24px** — `studio.css:697`. AA(24px)는 통과하지만 하네스 목표 44px에 못 미친다. 같은 파일 572행의 44px 값과 충돌한다.
- **L7. 자산함 카드 버튼 이름이 모두 "선택 샷에 연결"** — `index.html:425`. 버튼 목록으로 탐색하면 구분되지 않는다. `aria-label`에 파일명을 포함한다. 같은 곳의 영문 배지 "VIDEO"는 "영상"으로 통일한다.
- **L8. 인스펙터 섹션 h2를 disclosure summary로 바꾸며 제목 계층이 사라짐** — `index.html:980-982`. 헤딩 탐색이 줄어든다. 인스펙터 `aside`가 `aside.agent-sidebar` 안으로 들어가 랜드마크도 중첩된다(`chat-sidebar.js:45`).
- **L9. 앱 글자 크기를 따르지 않는 고정 값** — `studio.css:654`(`.creator-diagnostic pre { font:12px/1.55 … }`), `studio.css:936, 938`(`font-weight:600` 리터럴). `--ui-meta`, `--ui-weight-heading`으로 바꾼다.
- **L10. 단일 선택 목록에 aria-pressed 사용** — `index.html:114-115`(샷·take 버튼). 하나만 선택되는 목록에는 토글 의미(`aria-pressed`)보다 `aria-current="true"`가 정확하다.

## 4. 체계적 패턴

1. **CSS 3세대 누적**: 레거시(66-279) → `.lt-ui`(280-) → 날짜별 패치(791-, 857-, 892-, 912-, 933-, 957-). 같은 선택자가 여러 번 재정의된다. 예: `#flowNext` 6곳, `.lt-notice-detail>summary` 5곳.
2. **DOM 재배치 스크립트 3겹**: `loretuneWorkspaceStructure`(`index.html:909-`), `loretuneCraftUI`(`index.html:1053-`), `chat-sidebar.js`. 앞 스크립트가 만든 구조를 뒤 스크립트가 다시 옮긴다. 포커스 순서·랜드마크 문제(M1, L8)의 근원이다.
3. **오류 전달이 문장 중심**: 필드 연결(aria-invalid·describedby)이 없다(M4).

## 5. 대비 계산 (토큰 쌍, WCAG 2.x)

| 전경 \ 배경 | canvas #101010 | panel #1B1B1B | raised #242424 | hover #303030 | pressed #3D3D3D |
|---|---|---|---|---|---|
| strong #F4F4F2 | 17.28 | 15.64 | 14.10 | 11.98 | 9.86 |
| body #DEDEDB | 14.11 | 12.78 | 11.51 | 9.79 | 8.06 |
| muted #BDBDBB | 10.11 | 9.15 | 8.25 | 7.01 | 5.77 |
| error #FFB49D | 11.12 | 10.06 | 9.07 | 7.71 | 6.35 |
| warning #E6C58B | 11.53 | 10.44 | 9.41 | 8.00 | 6.58 |
| focus #E4DDBE (비텍스트) | 13.94 | 12.62 | 11.37 | 9.67 | 7.96 |
| control #858585 (입력 테두리·비활성 글자) | 5.16 | 4.67 | 4.21 | 3.58 | 2.94 |
| line #383838 (구분선·카드 테두리) | 1.62 | 1.47 | 1.32 | 1.13 | 1.08 |
| disabled-edge #555555 | 2.55 | 2.31 | 2.08 | 1.77 | 1.46 |

- 텍스트 대비 위반 쌍은 없다(최저 muted/pressed 5.77). primary 버튼 글자(canvas on strong)는 17.28이다.
- 입력 테두리(control)는 표면 대비 3:1 이상이라 1.4.11을 통과한다. `--ui-line`은 3:1 미만이므로 컨트롤 경계로 쓰면 안 된다(M12).
- 비활성 컨트롤(`--ui-control` 글자, `--ui-disabled-edge`)은 1.4.3·1.4.11의 비활성 예외 대상이다.
- 계산은 토큰 값 기준이다. 실제 렌더에서 겹침·투명도로 생기는 대비는 측정하지 않았다 [미확인].

## 6. 디텍터 결과 분류 (`impeccable detect`, 정적 15건)

| 규칙 | 건수 | 분류 | 근거 |
|---|---|---|---|
| side-tab (`studio.css:529, 732`) | 2 | 실제 결함 → L4 | 측면 2~3px 테두리 |
| broken-image | 1 | 오탐 | `index.html:23` `#timelineFrameImage`는 `hidden` 상태로 시작하고 프레임 확인 시 src가 채워진다 |
| gpt-thin-border-wide-shadow | 12 | 오탐 | `studio.css:559`의 `box-shadow:0 24px 80px`는 모달 `<dialog>` 전용이다. 정적 분석은 12개 대화상자를 "한 줄의 카드"로 보지만 실제로는 한 번에 하나만 열린다 |

디텍터 무시 설정은 추가하지 않았다(읽기 전용 범위).

## 7. 잘 된 점

- **토큰 권위 일원화**: `studio.css:4-64`. 텍스트 대비가 모두 AA를 크게 넘는다.
- **강제 색상 모드 대응**: `forced-colors:active` 블록(`studio.css:363, 595, 783`)이 Highlight·CanvasText로 대응한다.
- **reduced-motion 커버리지 완전**: `@keyframes`가 0개이고, 전환은 배경·테두리 색 120ms(`studio.css:361`, `no-preference` 조건)뿐이다. 따라서 전정 장애 유발 모션이 없고, reduce 전역 차단이 잃는 피드백도 없다. 재생 헤드의 rAF 이동은 사용자가 시작한 재생이다.
- **네이티브 dialog와 상태 영역**: `showModal`을 사용하고, 모든 대화상자에 `aria-label`과 `.dialog-status` live 영역을 주입한다(`index.html:702`). 모션·3D 대화상자는 닫을 때 런처로 포커스를 되돌린다(`motion-studio.js:48`, `scene-studio.js:130`).
- **ARIA 패턴 정석 구현**: 탭(roving tabindex, 화살표·Home·End — `index.html:1016-1019`, `chat-sidebar.js:237-240`), 크기 조절 구분선(`role=separator`, aria-value*, 키보드·pointercancel·lostpointercapture 처리 — `chat-sidebar.js:241-254`), 단계 `aria-current="step"`.
- **스킵 링크와 포커스 가림 방지**: 스킵 링크(`index.html:13`)와 sticky 헤더 아래 포커스 가림 방지(`scroll-margin-block` — `studio.css:888, 993`).
- **모바일 터치 타깃**: ≤900px에서 주요 컨트롤 44px(`studio.css:579`), ≤520px에서 컷 편집이 가로 스크롤 없이 재배치(`studio.css:919-929`).
- **dialog 여백**: dialog 폭이 `min(640px, calc(100vw - 32px))`로 16px 여백을 보장한다.

## 8. 권장 명령 순서

1. **[High] `/impeccable harden`** — H1 option 마크업 수정, M2·M4·M5·M13·M14
2. **[High] `/impeccable clarify`** — H2 단계 짧은 라벨, M15 음원 파일 라벨
3. **[High] `/impeccable adapt`** — H3 컷 버튼 최소 폭, M7 글자 크기 150·200% 넘침
4. **[Medium] `/impeccable layout`** — M1 대화상자 런처 위치·초기 포커스
5. **[Medium] `/impeccable onboard`** — M3 모바일 첫 화면
6. **[Medium] `/impeccable optimize`** — M8 숨김 탭 폴링, M9 썸네일 지연 로딩·디바운스
7. **[Medium] `/impeccable typeset`** — M6 한국어 keep-all
8. **[Medium] `/impeccable distill`** — M11 CSS 중복 정리
9. **[Medium] `/impeccable polish`** — M10, M12, L2~L7, L9 마무리

> 하나씩, 한꺼번에, 원하는 순서로 진행할 수 있다. 수정 후 `/impeccable audit`를 다시 돌리면 점수 변화를 볼 수 있다.

## 9. 미검증·한계

- 렌더하지 않았다. 375px 실제 넘침, 실제 포커스 이동, 스크린리더 낭독은 관찰하지 않았다. M3, M7, M12, H3의 예외 판정은 코드 추론이다 [추정]. 확정하려면 aside repl 렌더 검증(run-qa.sh 375·1280)이 필요하다.
- 스냅샷 밖 서버 코드(.py)는 UI 감사 범위에서 제외했다.
- axe 자동 스캔은 실행하지 않았다(브라우저 금지 조건).
