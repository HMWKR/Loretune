# 값 보존 토큰 묶음 — 구현·실제 서버 검증

2026-10-26 06:46–06:56 UTC. **설명된 세 선언만 적용 완료. 레이아웃 변경은 하지 않았다.** 다음 사용자에게 보이는 변경은 [별도 공간·위계 계획](NEXT-SPACE-PLAN-ko.md)이며 아직 구현하지 않았다.

## 적용 범위

|위치|이전 → 현재|실제 값|
|---|---|---|
|`index.html:45`, `audioWave()` SVG 배경|`#101010` → 기존 `var(--ui-canvas)`|`rgb(16, 16, 16)` 동일|
|같은 polyline|`#ddd` → `var(--ui-waveform-stroke)`; `studio.css:30`에 역할 정의|정확히 `#DDDDDD`, `rgb(221, 221, 221)` 동일|
|`studio.css:299`, `.lt-ui .lt-timecode`|literal → `var(--ui-font-timecode)`; `:58`에 역할 정의|`ui-monospace, monospace`, `tabular-nums` 동일|

폰트 설치, 새 색상, 간격·크기·DOM·handler·파형 좌표 변경은 없다. `before/` 원본과 [implementation.patch](implementation.patch)를 보존했다. 최종 파일이 위 치환만 적용한 예상 파일과 정확히 같음을 검사했다. 이 정리는 현재 화면을 개선했다는 주장이 아니라 이후 역할 기반 변경의 범위를 분명히 하는 작업이다.

## 실행한 검증

- 기존 **비HTTP 330개 통과**, 실패·오류·skip 0. [전체 로그](full-non-http.log). 기존 회귀를 다시 실행했으며 중첩 시나리오나 아래 브라우저 측정을 합산하지 않는다. 별도 HTTP 20개 suite는 이번에 재실행하지 않았다.
- 현재 inline JavaScript `node --check` 통과. 테스트 파일은 변경하지 않았다.
- 실제 `app.server()` GET 경로로 현재 HTML/CSS/media JS를 제공하고 시작·종료 시 HTTP 응답 SHA256과 파일 SHA256을 대조했다. `document.write` replay가 아니다. [시작](served-source.json), [종료](browser-final.json).
- 1920×1080 주 기준과 1280×900 보조 기준에서 선택 Take/sequence × 정밀 접힘/펼침의 **8상태**를 측정했다. 추가로 실제 파형을 펼친 상태와 Take 비교 상태에서 대상 역할을 확인했다.
- 각 상태의 현재 computed 값·rect·실제 텍스트 Range 폭·파형 points를 기록한 뒤, 페이지 메모리에만 이전 literal을 대입하여 비교하고 원상 복원했다. 대상 값은 모두 같았다. 이는 두 제품 빌드를 새로 실행한 비교가 아니라 **현재 제공 화면 내 이전 선언 참조 실험**이다. [요약](browser-summary.json), [보이는 파형](waveform-visible-parity.json), [보이는 비교](comparison-visible-parity.json).
- 시간 표시의 실제 DOM 폭: `00:00.000`, `11:11.111`, `88:88.888` 각각 **65.0234375px**; `00:00.500 / 00:07.000`은 **151.71875px**. sequence/compare 모두 현재 token과 이전 literal이 같았다. 12px/400, line-height18px, tabular-nums 유지. [유효한 숫자 폭 결과](verified-numeral-widths.json).

측정 정정: 초기 각 상태 JSON의 `numeralWidths`는 빈 computed font shorthand를 Canvas에 적용한 진단 오류 때문에 숫자 폭 증거로 사용하지 않는다. 해당 원기록은 보존하고 위 실제 DOM span 측정으로 대체했다. 다른 computed 색·font-family·rect·Range 폭·points 측정에는 해당 오류가 없다.

## 치수와 촬영 조건

|상태|1920×1080 실제 contain 영상|1280×900 실제 contain 영상|
|---|---:|---:|
|선택 Take · 기본|703.85×395.91px|383.85×215.91px|
|sequence · 기본|584.74×328.91px|264.74×148.91px|
|선택 Take · 정밀 펼침|609.75×342.98px|394.14×221.70px|
|sequence · 정밀 펼침|490.64×275.98px|275.03×154.70px|

모두 document 크기가 CSS viewport와 같았다. 선행 잠금 기준선과 직접 대응하는 기본·sequence+정밀의 **4상태**에서 영상 크기·프레임 시각·preview/stage/dock/transport/media-pane 위치와 치수가 정확히 같았다. [전후 geometry 비교](baseline-geometry-comparison.json). 나머지 4셀은 이번 공간 분석용 측정이며 선행 4셀과 합쳐 8쌍의 전후 비교라고 하지 않는다.

Ego Lite, CLI가 보고한 current version **0.6.0.20**, UA `Chrome/154.0.0.0`, DPR1, 앱 글자배율100%, visualViewport.scale1. 브라우저 앱 전체 버전은 별도 검증하지 않았다. 버전 업그레이드 안내가 있었으나 설치하지 않았다. CSS viewport emulation이며 실제 브라우저 zoom 시험이 아니다.

같은 합성 장면01/Take1, 원본 320×180 영상: 선택 모드는 원본1.000초, sequence는 편집0.500초/원본0.750초. 비교는 공유경과0.500초, 왼쪽0.750/오른쪽0.500초. paused/ready 상태를 기록했다. 이미지별 시각과 metrics는 같은 이름 JSON에 있다.

대표 저장 이미지: [1920 기본](1920-selected-basic.png), [1920 sequence+정밀](1920-sequence-detail.png), [1280 sequence+정밀](1280-sequence-detail.png), [Take 비교](comparison-1920.png), [보이는 실제 파형](waveform-visible-1920.png). 해당 저장 픽셀을 열어 확인했다. 다른 상태 이미지도 같은 디렉터리에 보존했다.

**전체 픽셀 동일성은 주장하지 않는다.** native 영상 제어 오버레이·과거 spinner, 기본 화면의 타임라인 playhead 초기 위치는 동적 차이다. 기존과 이번의 기본 영상 프레임은 같지만 모든 UI 상태가 pixel golden 조건인 것은 아니다. 이미지 전역 zero-diff 판정 대신 대상 computed 값/실측 기하/숫자 폭의 일치를 증거로 사용했다. 숨겨진 요소만으로 판정하지 않도록 파형과 비교 시간을 각각 보이는 상태에서도 검증했다.

## 자료·보존·정리

승인된 합성 프로젝트1개와 시험 영상2·PNG1·WAV1, 총1,066,575bytes만 isolated DB/media로 사용했다. 프로젝트 fingerprint `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`. [allowlist와 해시](server-start.json). 키·실고객 자료·외부 provider 설정·worker는 없다. POST/PATCH를 차단한 검증용 경계를 사용했으며 실제 non-GET 요청0이다. 페이지에서 외부 resource/차단 시도/처리되지 않은 JS 오류 모두0. Ego 제어 경로의 외부 중계·보관 여부는 이전에 고지된 미확인 경계이며, 페이지 resource0을 그 경로 전체의 보장으로 확대하지 않는다.

공간39는 **06:52:01 UTC 종료**, 임시 `127.0.0.1:63949` listener는 **06:55:10 UTC 정상 종료(exit0)**. 서버 중단 전 canonical 합성 프로젝트·미디어·소스 불변 확인. 기존 앱 서버를 변경하지 않았다. isolated 복제본 위치는 server-start.json에 있으며 재현용으로 보존했다. [브라우저 종료](space-closed.json), [서버 종료](server-stop.json), [최종 확인](final-verification.json). Library 업로드·외부 공유는 시도하지 않았다.

|파일|최종 SHA256|
|---|---|
|index.html|`fd8205bb4c4bb43a098b56f686e41ca42c630b6f9e5d3241b9ccc75f48ce619a`|
|studio.css|`6f4992769b8d7ecc5019e5927c308b7bd9c77956d4d9c6dcd6d4f3e937bada3a`|
|studio-media.js — 불변|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|app.py — 불변|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

Hallmark의 작업 중심·기존 방향 보존과 Impeccable의 역할 token 추출·값 보존 기준을 이 작은 diff에 수동 적용했다. 별도 detector/render lint의 실행 결과라고 하지 않는다. Impeccable context-engine은 사용할 수 없어 설치/우회하지 않았고 기존 reference lock과 측정 근거를 사용했다. 전체 시각 점수·경쟁사 동등성은 산출하지 않았다.

현재 blocker 없음. 이번 배치에서 실제 zoom200/400%, 앱200%, native IME, 모든 키보드 경로, screenreader/axe, cross-browser, live provider·과금은 새로 검증하지 않았다. 이전 두 폼 브라우저12/12는 [선행 결과](../proposal-draft-fix-20261026/served-baseline/REPORT-ko.md)로 유지하며 이번 token 검증으로 다시 계산하지 않는다. 원본 명세·과거 QA는 보존했다.

변경 이력: HTML/CSS의 위 세 선언, 검증 스크립트·JSON·이미지·보고서만 이번 묶음에 추가/수정. 다음 공간 개선은 계획 설명 후 별도 작은 diff로 진행한다.
