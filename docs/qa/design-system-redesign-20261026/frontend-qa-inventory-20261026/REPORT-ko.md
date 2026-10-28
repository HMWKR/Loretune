# 프런트엔드 시각·CSS·키보드 QA — 2026-10-26

**새 시각 문제 2건을 확인했다.** 1280×900·앱 글자 200%에서 Take 3 키보드 포커스가 일부 잘리고(VF01, P2), 긴 공백 없는 장면명이 1920 rail에서 잘린다(VF02, P3). P0/P1은 이번 표본에서 확인하지 않았다. 앱 코드·서버·공유 DB는 변경하지 않았다. 관측을 끝내고 전용 TaskSpace 34를 종료했으므로 기능팀은 수정 동결을 해제할 수 있다.

실행 전에 고정한 22개 케이스는 **15 PASS / 2 FAIL / 2 BLOCKED / 3 NOT RUN**이다. PASS는 기재한 상태와 절차에 한정된다. 오류 표시 fixture가 통과했다고 실제 서버 오류 복구가 통과한 것은 아니다. 새 종합 디자인 점수는 산출하지 않았다. 이전 81/100은 다른 혼합 rubric의 역사적 결과다.

- [실행 전 기준](SCENARIOS-LOCKED-ko.md), [원본 JSON](SCENARIOS-LOCKED.json), [10개 시각 영역](VISUAL-GROUPS-LOCKED.md)
- [케이스별 결과·출처·기대/실제·환경·severity·retest JSON](RESULTS.json), [동일 CSV](RESULTS.csv)
- [환경](environment.json), [종료 불변성](evidence/end.json), [기존 화면 34개 provenance](SCREENSHOT-INVENTORY.csv)

## 확인된 문제와 수정 담당에게 전달할 기준

### VF01 — 확대 시 Take 3 포커스가 목록에 일부 가려짐 · P2

- **재현:** 합성 작품 `디자인 시스템 기능 QA 20261026` → 장면 01 → 1280×900 CSS viewport → 정상 설정 UI로 앱 글자 크기 200% → Take 1에서 Tab 두 번으로 Take 3. Take 선택/승인/저장은 실행하지 않았다.
- **기대:** 포커스를 받은 대상의 이름·상태·윤곽을 함께 볼 수 있어야 한다. 이는 Loretune의 더 강한 제품 기준이다. [WCAG 2.4.11 AA](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)는 “완전히 가려지지 않음”이므로 이 표본을 그 조항의 실패라고 부르지 않는다.
- **실제:** 버튼 x=681.32, 폭157.60px. 목록의 오른쪽 clip 경계749.28px로 약67.96px, **43.1%만 가시**. `#takes` clientWidth529/scrollWidth619, scrollLeft0. 중앙 hit-test도 버튼을 가리키지 않는다. 스크린샷 후 다시 읽고 같은 경로로 한 번 재현해도 동일했다.
- **사용자 영향:** 키보드로 후보에 도달했지만 어느 Take와 상태에 초점이 있는지 시각적으로 판독하기 어렵다. 접근성 트리에는 이름이 남아 있으므로 “키보드 완전 불능”으로 과장하지 않는다.
- **관련 구현:** `studio.css:103`, `:232–233`, `:365–367`, `:572–579`의 가로 Take 목록·flex 배분. 정확한 scroll 동작 원인은 기능팀에서 확인해야 한다. 확대 시 비교 버튼을 별도 행에 배치하거나 Take 목록의 포커스 이동을 전체 대상이 보이도록 처리하는 방향을 검토한다. 글자를 줄이거나 overflow로 숨기는 해결은 제외한다.
- **재검증:** 1280 앱150/200, 1920 앱100/200에서 첫/중간/끝 Take의 Tab·Shift+Tab·pointer 접근, 비교 버튼 접근, 선택/승인 불변성을 확인. 실제 브라우저 zoom은 별도다.
- **근거:** [재현 화면](evidence/scale2-take3-recheck-1280.png), [측정](evidence/scale2-take3-recheck.json), [최초 화면](evidence/scale2-take3-keyboard-1280.png). 미수정.

### VF02 — 공백 없는 긴 장면명 잘림 · P3

- **재현:** 1920×1080·앱100%, 실제 첫 장면 카드의 구조/클래스는 그대로 두고 제목 텍스트만 `01 긴 한국어 장면 제목과 EnglishNoSpacesABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`로 일시 교체. 이후 원래 노드를 복원했다. 실제 저장된 장면명을 바꾸지 않았다.
- **실제:** `.lt-scene-copy>b`의 clientWidth108px, scrollWidth417px. computed `word-break:keep-all`, `overflow-wrap:normal`; 카드에 title 속성은 없다. 연속 문자열이 rail 우측에 잘려 끝부분이 보이지 않는다.
- **사용자 영향:** 같은 앞부분을 가진 긴 식별자의 구분이 어려워진다. 한국어는 줄바꿈되고, 실제 선택 시 중앙 제목이나 접근성 이름으로 전체 문자열을 볼 가능성은 별도다. 이 표시 fixture만으로 저장 경로·모든 WCAG 조항의 실패를 주장하지 않는다.
- **관련 구현:** `studio.css:157`의 button keep-all, `:564–566`의 title 스타일에 긴 연속 문자열 대책이 없다. 이미 정상인 `#creatorSavedReason`/`.lt-model-name`의 `overflow-wrap:anywhere`와 역할을 비교할 수 있다. 자연스러운 한국어 줄바꿈을 유지하면서 연속 문자열에는 emergency wrap을 적용하거나, 명시적 축약과 전체명 접근 경로를 제공한다.
- **재검증:** 한글/영문/공백 없는 이름과 동일 prefix 두 장면, hover/keyboard/선택 제목, 1920 및1280. 실제 저장을 요구하는 회귀는 기능팀의 격리 fixture에서 수행한다.
- **근거:** [단일 제목만 변경한 화면](evidence/long-unbroken-title-1920.png), [측정](evidence/long-title-metrics.json). 미수정.

처음 긴 목록 fixture는 카드 내부 구조를 단순화해 부적절한 모양을 만들었다. 해당 `long-content-start-1920` 등 원파일은 지우지 않았지만 **텍스트 품질 판단에서 제외**했다. 실제 클래스 구조를 보존한 `long-content-structure-preserved-1920`과 단일 제목 재현으로 교정했다. 잘못된 fixture 결과를 앱 결함으로 계산하지 않았다.

## 고정 버전·환경·안전 경계

| 항목 | 확인값 |
|---|---|
| HTML | `0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109` |
| CSS | `2fbba70fa95d035aecd19a0fd9a2e7e3e00c5f6b789cf3fe0c3eed5cbef5cfab` |
| media JS | `65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328` |
| 앱 backend 소스 | `7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d` |
| 합성 작품 지문 | `8ac30524626fcd58457cb62a2616710426e7ec33c1958f3d271bc3dca42a740d` — 시작/끝 동일 |
| 화면 | 1920×1080 주,1280×900 보조 **CSS viewport**; DPR1. OS 모니터 해상도로 표현하지 않음 |
| 브라우저 | Ego Lite CLI0.6.0.20, UA `Chrome/154.0.0.0`, MacIntel. 정확한 engine/product build와 실제 macOS 버전은 미확인 |
| 언어/시간 | ko-KR / Asia/Seoul. 로그 시각 UTC, 로컬 파일mtime은 환경 시간대와 다를 수 있음 |
| 확대 | 앱100/150/200 측정. `visualViewport.scale=1` 및 DPR1은 실제 브라우저100%의 증명이 아님 |
| 종료 | 앱scale1, 장면01, selected preview, 열린dialog0, 재생중media0, 임시DOM0, emulation복원, TaskSpace34 종료 |

실제 `page.fetch`의 동일 origin GET으로 시작/끝 제공 HTML/CSS/JS를 확인했다. 이는 이미 승인된 본인의 전용 브라우저 경로이며, 다른 감사 세션에서 거절된 터미널 localhost GET을 재시도하거나 우회한 것이 아니다.

가드의 fetch/XHR/form 방어를 호출 안에서 확인했고 저장·승인·실행 버튼은 누르지 않았다. 로그에는 GET만 남고 blocked 목록은 비어 있다. **브라우저 가드는 backend provider 격리 증명이 아니다.** 실제 서비스의 유료 provider 장애 주입은 수행하지 않았다. 소스·작품 지문 불변과 수행한 UI 동작을 근거로 변경 없음 범위를 판단했다.

## 실제 지원 API와 한계

- 사용: Ego `taskSpace(34)`, `page.snapshot`, `click`, `selectOption`, `fill`, `focus`, `keyboard.press/insertText`, `hover`, `evaluate`, `fetch`, `screenshot`, `waitForFunction`, `task.finish`.
- 공개 CDP 사용: `Emulation.setDeviceMetricsOverride`, `Emulation.setEmulatedMedia`, `Accessibility.getFullAXTree/getPartialAXTree`, `DOM.enable/getDocument/querySelector`, `CSS.enable/getPlatformFontsForNode`, `Runtime.evaluate`.
- `Page.addScriptToEvaluateOnNewDocument`는 identifier1을 반환했으나, 후속 호출에서 guard가 없는 상태도 관찰했다. 지속 격리를 가정하지 않고 이후 각 호출 안에서 확인했다. 이 API 성공을 Playwright `route`나 완전한 mock transport 지원으로 확대하지 않는다.
- `Browser.getVersion`은 “wasn't found”. 정확한 버전을 UA로 대체해 확정하지 않았다.
- `ControlOrMeta+Equal`/reset0 후 실제 배율 변화 없음 → browser200/400 **BLOCKED**. CSS transform·DPR·viewport·앱scale로 대체하지 않았다.
- double-requestAnimationFrame Promise 대기는 해결되지 않아 중단했다. 앱 결함으로 세지 않았고, paint 측정의 근거로 사용하지 않았다.
- `window.axe` 없음; 조사한 프로젝트/QA 도구 범위에 사용 가능한 bundle 없음 → axe **BLOCKED**. 설치나 외부 script 주입 없음.
- screen reader, 다른 engine/실제 Safari, 실제 Windows high contrast, 실제 고객 사용성 시험은 수행하지 않았다. Ego 업데이트 알림은 있었지만 업그레이드하지 않았다.

## 10개 순수 시각 영역 — 기능 정확성과 별도

| 영역 | 분류·관측 | 판단과 범위 |
|---|---|---|
|1. geometry/enlargement|checked pass + VF01 confirmed product violation|앱100% 문서1920×1080/1280×900. 확대 reflow는 허용.1280 앱200% Take 끝 포커스 잘림은 별도 실패.|
|2. 공간 배분·밀도|checked pass / visual-task hypothesis|기본1920 preview stage1376×405.91, 정밀 sequence1376×285.98. 실제 landscape는 높이에 맞춰 contain. rail184, inspector288. 주요 작업 진입점이 한 화면에 있으나1280 정밀 영상은 약289×163이라 세부 프레임 판독 부담 가능. 임의 최소미디어면적 위반으로 판정하지 않음.|
|3. 그룹·간격·정렬|checked pass|panel 간16px, Take 간8px와 역할별 여백. 비교identity/media/facts 열이 정렬됨. 긴 메모는 inspector 내부 scroll. 전문 폼은 중첩scroll이 있어 학습 부담 가설은 남지만 접근불능으로 보이지 않음.|
|4. 타입·폰트·CJK|checked pass + VF02 confirmed fixture limitation|제목20/600/28px, 본문14/400/23.8px, metadata12/400/17.4px, Take12/500/15.6px. 실제 CJK Apple SD Gothic Neo Regular/Semibold, Latin SF NS, timecode Menlo. 긴 memo/모델명은 wrap, 긴 rail 연속 문자열만 잘림. 사용자 text-spacing override는 NOT RUN.|
|5. 색상·상태쌍|checked pass, sampled|canvas#101010/panel#1B1B1B/raised#242424/selected#2A2A28. 주요 글자#F4F4F2,본문#DEDEDB,metadata#BDBDBB.20개 대비표본 통과. 장식divider#383838을 필수경계로 오판하지 않음.|
|6. focus/선택/playhead|checked pass + VF01|선택면+세로표식+현재선택 문구, 승인 체크+텍스트, dashed focus, 1px playhead+상단marker를 구분. 확대Take3 제외 표본의 포커스 가시. forced-color error+focus는 미실행.|
|7. 아이콘·컨트롤 형태|checked pass / missing evidence|체크/원/공개 화살표는 텍스트와 함께 사용. 핵심control36–40px, 패널8px/컨트롤6px radius 역할 확인. 모든 native media control의 OS별 광학 일관성은 미검증; 혼합 native controls 자체를 실패로 세지 않음.|
|8. 미디어·시간축|checked pass, visual only|두 비교stage471×300;16:9/9:16 원본 contain, 크롭/왜곡 없음.1/2/4초 폭의 비례와 공통축, 파형·playhead 표시. 단색/저해상도 합성미디어의 작품 품질은 평가하지 않음.1:1/투명/오류poster·decoded-sync 미검증.|
|9. 표면·overlay·CSS|checked pass / missing evidence|모델/비교 dialog가 viewport안에 있고 Escape복귀 확인. 본문tone/경계와 modal backdrop 구분. 실제computed값으로 판단했으며 selector중복 자체를 결함으로 부르지 않음. 모든 tooltip/edge popover 상태는 미검증.|
|10. 증거 신뢰성|checked pass, limited|같은 paused-ready 상태 두 PNG가 바이트 동일. 이전34개 역사자료와 새34개 파일을 구분. 잘못된 DOMfixture·측정콜백은 명시적으로 제외. screenshot동일함은 미감/모든동적상태 통과가 아님.|

색상·타입·간격의 px/HEX는 현재 제품의 측정값이지 경쟁사의 내부 token이나 보편적 정답이 아니다. 경쟁사 점수는 만들지 않았다. 기존 reference lock의 Descript는 시간정렬, Frame.io는 asset/player 인접성, Runway는 조용한 workspace/prompt 맥락에 한정하며, 서로 다른 시점/viewport 캡처를 동일조건 라이브비교로 부르지 않는다.

## 주요 대비와 비색상 단서

| 실제 역할쌍 | 대비 | 판단 |
|---|---:|---|
|제목#F4F4F2 / canvas#101010|17.28:1|표본 PASS|
|검토본문#DEDEDB / panel#1B1B1B|12.78:1|표본 PASS|
|metadata#BDBDBB / canvas#101010|10.11:1|표본 PASS|
|dirty action#101010 / #F4F4F2|17.28:1|표본 PASS|
|오류#FFB49D / #28201E|9.32:1|표시 fixture만 PASS|
|필수control경계#858585 / raised#242424|4.21:1|비문자 표본 PASS|
|focus#E4DDBE / panel#1B1B1B|12.62:1|비문자 표본 PASS|
|playhead#D8D8D2 / raised#242424|10.85:1|비문자 표본 PASS|

전체 계산: [contrast.csv](evidence/contrast.csv), [computed역할·상태](evidence/computed-roles-states.json). 투명 배경은 실제 조상 opaque layer까지 따라갔다. playhead는 텍스트가 없으므로 상속된 text color로 만든 잘못된 대비 후보를 제외했다. Disabled 버튼은 별도 시각 구분을 확인했으며 일반텍스트 최소대비 조항을 그대로 적용하지 않았다.

기준은 [일반 텍스트 대비](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [비문자 대비](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)다. [text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)은 사용자 변경 후 내용/기능 보존 시험이며 기본행간을 강제하는 디자인 법칙으로 쓰지 않는다. 위 결과는 전체 WCAG 인증이 아니다.

## 시나리오·키보드 coverage

- 초기 BODY부터52개 관측/8개 과업 target의 keyboard-only 경로. 비교 Escape, 검토 취소, 모델 Escape 복귀 확인. 저장·유료승인 실행은 제외했다.
- 정밀편집35 Tab target씩.1280 전부 가시.1920 첫 즉시측정의 profile만 위치변경 중 가림 후보가 있었으나 같은 경로 재검토와 저장픽셀에서958–999px의 전체가시 확인. 원로그를 유지하고 지속 결함으로 등록하지 않았다.
- AX 트리의 nonignored relevant controls: initial14/dirty33/dialog6, 이 표본에서 빈 이름 없음. 이는 screenreader 발화시험이 아니다.
- 긴60카드/40문단은 DOM 표시 fixture다. 문서1080px, rail내부scroll7744px/inspector5230px, 끝focus가시. 실제60장면 데이터·성능 시험이라고 부르지 않는다.
- pending/rejected inspector, queued/running/partial/failed, loading/poster-failure, 투명/정방형 미디어, 사용자textspacing, forced-colors의 오류+focus, 실제zoom/스크린리더/다른engine은 미검증 또는blocked로 남는다.

실행 설계는 [Playwright 사용자 중심 격리](https://playwright.dev/docs/best-practices), [actionability](https://playwright.dev/docs/actionability), [Testing Library 원칙](https://testing-library.com/docs/guiding-principles/), [snapshot의 동일환경 조건](https://playwright.dev/docs/test-snapshots)을 참고했다. 실제 도구는 Ego이며 Playwright를 실행했다고 주장하지 않는다. 전체 사용자 journey와 targeted programmatic focus segment를 결과표에서 구분했다.

## 기능팀 요청에 대한 추가 관측

**FQ02 natural-ended: NOT RUN.** 기존 허용 QA 작품의 저장된 timeline을 확인했으나 모두 audio1이었다. 준비된 무음 sequence가 없으므로 새 fixture/공유 편집 변경 없이 중단했다. 기능 감사팀의 VM 재현을 닫거나 반박하지 않는다.

**30회 warm 장면 전환:** 정상 rail 클릭만 수행. DOM1169/video3/audio1/playing0이 시작·15·30·종료에서 동일했다. 약5초 관측 중 longtask entry0,200ms 초과 entry0이다. heap표본도 기록했지만 이 작은 표본으로 leak 또는 field CWV를 판정하지 않는다.

**시간 측정은 폐기:** click capture에서 예약한 microtask가 앱 bubbling handler보다 먼저 실행돼30개 모두 이전 장면 제목을 기록했다. 따라서0–0.1ms를 DOM-ready/input-to-paint로 쓰지 않았고 p95도 산출하지 않았다. 실제paint 측정은 BLOCKED다. 이 30개는 기능팀의90표본 수용시험을 대체하지 않는다. [원자료](evidence/cached-selection-lab30.json), [한계 포함 handoff](MEDIA-PERFORMANCE-HANDOFF-RESULT.json).

## 다음 조치

1. 기능팀은 FQ01–03과 별개로 VF01의 확대 시 Take 가시성을 수정하고 위 조건에서 재검증한다.
2. VF02는 긴 연속 제목의 표현 전략을 정한 뒤 실제 클래스 구조·한글·동일prefix 회귀로 확인한다.
3. 오류·실행상태 전체시험은 독립 backend/fixture가 갖춰진 뒤 수행한다. 미검증을 실패나 성공으로 대신하지 않는다.
4. 기존 방법론/참고/81점 이력은 보존한다. 이번 결과는 숫자보다 **확인된 계약 위반, 시각 과업 가설, coverage 부족**을 구분하기 위한 별도 프런트엔드 QA다.

실제 화면 파일은 모두 로컬 QA 폴더에 저장했다. Library 전달 결과는 별도 DELIVERY.json에 기록한다. 로컬 파일 저장만으로 Library 전달 완료를 뜻하지 않는다. 본 보고서의 상대 경로는 프로젝트 내 근거 위치다.
