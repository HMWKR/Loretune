# 현재 capability 확인과 작은 브라우저 측정 요청

2026-10-26 · 부모에게 전달할 요청. 기존 결과표/점수/소스는 변경하지 않았다.

## 이 세션 확인 결과

- 현재 exposed tool 목록에서 Ego/CDP/Playwright 전용 도구는 발견되지 않았다. 별도로 공개된 `mcp__cua_repl`은 존재한다.
- 이전 turn의 브라우저 변수는 현재 REPL에 없었다. 이후 공개 `cua.getBrowser({url: ...})`로 문서만 선택했고 IAB(type=iab, id=4)가 반환됐다. 페이지를 열거나 claim하거나 이동하지 않았다.
- 이 IAB의 현재 capability 목록은 **visibility, viewport** 두 개다. 공개 tab API의 evaluate는 **read-only**로 명시돼 있다. 초기 스크립트·route·CDP·Performance trace API는 공개 목록에 없다. 이전 Chrome 문서에서도 route/init-script는 확인되지 않았다.
- 이 세션에서 shell Ego 실행·숨은 API·권한 우회는 하지 않았다. 앞서 차단된 localhost GET도 재시도하지 않았다.
- 현재 source HTML `0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109`, CSS `2fbba70fa95d035aecd19a0fd9a2e7e3e00c5f6b789cf3fe0c3eed5cbef5cfab`, media `65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328` 재확인. 변경 없음.
- 디자인 검토자의 `.SF NS`/`Apple SD Gothic Neo` 관측은 그 검토자의 별도 증거이며 여기서 재검증하거나 전체 브라우저 엔진 지원으로 확장하지 않는다.

## 부모 → 디자인 검토자: 요청 1 (우선, FQ02 실제 media ended 관측)

**목표:** VM의 native-ended 반례가 실제 브라우저에서 발생하는지 작은 읽기 중심 재생 관측으로 연결한다. 시각/a11y 검토는 반복하지 않는다.

1. 현재 지원되는 공개 도구만 사용하고, 본인 소유의 이미 격리된 합성 QA 페이지를 사용한다. **음악이 없는 sequence fixture가 이미 준비돼 있을 때만** 진행한다. 없다면 공유 DB나 기존 사용자 편집을 바꾸지 말고 NOT RUN으로 반환한다. 새 서버·업로드·provider·승인·저장 요청은 필요 없다.
2. 실제 browser product/version/engine 확인 근거, viewport, DPR, 앱 scale, 실제 zoom 확인 여부, fixture ID 및 clip `trim/duration`/소스 duration을 기록한다. 1920×1080 우선. 이 재생 체크를 위해 별도의 1280 geometry 검사를 추가할 필요는 없다.
3. 공개 observer/초기 스크립트를 통해 **그 시험 페이지에서만** `loadedmetadata`, `playing`, `waiting`, `pause`, `ended`, `error`를 관측한다. app 함수·RAF·fetch·Storage를 덮어쓰지 않는다. 이벤트별 `performance.now`, `currentTime`, `duration`, `paused`, `ended`, `readyState`, media error code, sequence 위치/버튼 텍스트를 기록한다. 토큰·쿠키·프로젝트 본문은 수집하지 않는다.
4. 사용자-facing ‘편집 순서 + 음악’/‘편집 재생’ 조작으로 무음 sequence를 자연 재생한다. 마지막 컷이 종료한 뒤 약 1초 뒤 표시를 읽는다. 가능하면 같은 작업을 두 번만 관측한다. native ended를 인위적으로 dispatch하지 않는다.
5. 기대값: 최종 sequence 위치와 종료 상태가 일치하고 버튼이 ‘편집 재생’으로 돌아온다. 중간 컷 종료라면 다음 컷으로 진행해야 한다. 관측이 종료 직전 시간과 ‘일시 정지’에서 멈추면 event 로그와 한 장의 상태 캡처를 제공한다. 그 화면이 직접 재현되지 않으면 PASS 또는 NOT REPRODUCED로 기록하며 VM 결과를 은폐하지 않는다.
6. 기존 canonical fingerprint의 전후 동일 여부와 실제 mutation/provider 전달 0의 확인 근거를 함께 반환한다. 해당 증거를 지원 도구로 얻을 수 없다면 그 부분은 미확인으로 표시한다.

**선택적 frame 기록:** 공개 API에 `requestVideoFrameCallback`이 실제 존재하고 관측 허용이면 반환된 `mediaTime/presentedFrames`만 함께 수집한다. 없는 API를 추측하지 않는다. 자연 재생 관측만으로 ±1frame seek 또는 AV drift 통과를 선언하지 않는다.

## 부모 → 디자인 검토자: 요청 2 (여유가 있을 때, 작은 lab 표본)

**목표:** PER02/PER03의 전부를 완료하려는 요청이 아니라 실제 브라우저 측정 가능성과 작은 관측 표본 확보다.

- 본인 격리 페이지, 이미 존재하는 합성 두 장면에서 **1920×1080, 캐시 warm 후 장면 선택 30회**만 수행한다. Take 선택/검토/승인/저장 버튼은 누르지 않는다. 장면 rail 선택이 서버 mutation이 아님을 먼저 소스/ledger로 확인한다.
- 지원되는 PerformanceObserver entry type을 먼저 기록한다. 공개 지원이 있을 때만 longtask/event/paint 관측을 사용한다. `>50ms` task의 duration 원자료와 `>200ms` task 유무, input→첫 반영 paint의 측정 정의·30개 원표본을 반환한다. metadata/decode 완료 시간은 UI 반영 시간과 분리한다.
- 시작/15회/30회/정지 후 DOM node 수, video/audio element 수, 재생 중 media 수를 읽는다. heap API가 없으면 누락으로 남긴다. 한 번의 heap/DOM 증가를 leak으로 판정하지 않는다.
- 실제 browser/version/viewport/zoom/cache 조건, fixture의 실제 장면/Take/자막 수를 반드시 기재한다. 이 30개 표본은 기존 PER03의 90개 수용 시험을 대체하지 않으며 p95는 탐색 관측으로만 제공한다. field p75 LCP/INP/CLS 통과나 제품 점수는 산출하지 않는다.
- 주입·관측 API가 제한되거나 초기 네트워크 격리가 불분명하면 즉시 BLOCKED로 반환한다. 실제 장애 주입/Storage 거부/역순 fetch는 요청하지 않는다.

## 최소 반환 형식

`case_id`, `build/source hash`, `browser/version/engine evidence`, `viewport/DPR/app scale/zoom`, `synthetic fixture ID`, `steps`, `expected`, `observed`, `PASS/FAIL/BLOCKED/NOT RUN`, `events/samples file`, `canonical before/after fingerprint`, `mutation/provider ledger summary`, `limitations`.

FQ01/FQ03의 브라우저 fault injection은 이번 요청에 포함하지 않는다. 실제 엔진 교차 테스트도 포함하지 않는다. 지원 격리 경로가 확인되지 않는 동안 기존 VM 결과와 BLOCKED 상태를 유지한다.
