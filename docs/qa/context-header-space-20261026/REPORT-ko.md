# 장면 문맥 헤더 공간 개선 — 구현·전후 검증

2026-10-26 07:03–07:14 UTC. [설명된 계획](../value-preserving-tokens-20261026/NEXT-SPACE-PLAN-ko.md)의 **제목+접힌 장면 설명 묶음만 완료**했다. 다른 surface·버튼·타이포·공급자 변경은 없다. 다음 위계 묶음은 시작하지 않았다.

## 결과와 이유

접힌 제목·설명 영역은 기존 `36 + 44 + 8 = 88px`에서 같은 행44px+아래8px인 **52px**가 됐다. 확보한36px가 실제 contain 영상 높이에 그대로 더해졌다. 글자를 줄이거나 미디어를 늘여 그리지 않았고, 자막·재생 transport·Take·타임라인의 위치는 유지했다.

이 선택은 영상과 편집 맥락을 함께 보는 사용자 과업에 따른 작은 배치 변경이다. 기존 [reference lock](../design-system-redesign-20261026/REFERENCE-LOCK.md)과 [방법론 적합표](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md)를 유지했다. 기존 상세 설명은 덜 자주 읽는 정보를 접는 native disclosure로 남겼다. 영상 확보를 위해 timeline 최소높이·본문 크기·caption을 줄이는 대안은 사용하지 않았다. 특정 픽셀 수가 외부 표준이거나 사용자 성공률이라는 주장은 하지 않는다.

## 실제 변경

- `index.html:229`: 기존 `.lt-shot-header`와 `.creator-scene-description`을 하나의 `.lt-scene-context`에 **이동**한다. 복제·본문 삭제·ID 변경·새 controller 없음.
- `studio.css:869–874` 부근: bounded desktop에서 두 영역을 grid 한 행으로 배치하고, 설명이 열리면 두 열 전체를 사용한다. 제목/설명의 비분리 긴 문자열을 감싼다. 기존 spacing token을 재사용한다.
- 일반 flow/mobile은 기존 세로 문맥을 유지한다. 앱200%에서는 기존 shell 규칙에 따라 flow로 전환한다. 기본44px summary, 기존 typography·palette·focus 규칙은 그대로다.
- 저장·초안·승인·재생·비교 handler와 `studio-media.js`, backend를 변경하지 않았다. [정확한 diff](implementation.patch), [수정 전 파일](before/index.html)을 보존했다.

## 같은 조건의 실제 서버 전후 측정

수정 전 `127.0.0.1:57711`, 수정 후 `127.0.0.1:58963`에서 그 시점의 실제 프로젝트 소스를 제공했다. 시작/종료 파일·HTTP SHA256을 대조했다. snapshot HTML을 document.write로 재생한 증거가 아니다. 두 주소는 검증 후 종료됐다.

같은 합성 프로젝트/장면01/Take1, 기존 승인 상태, DPR1, 앱100%, CSS viewport1920×1080 또는1280×900. 선택 Take는 원본1.000초, sequence는 편집0.500초/원본0.750초, paused/ready 상태. 비교는 Take1/2 공유0.500초이다. 각 캡처의 JSON에 frame·mode·precision·치수를 기록했다.

|뷰포트·상태|변경 전 실제 영상(px)|변경 후 실제 영상(px)|높이 증가|
|---|---:|---:|---:|
|1920 선택 · 기본|703.85×395.91|767.85×431.91|36px|
|1920 sequence · 기본|584.74×328.91|648.74×364.91|36px|
|1920 선택 · 정밀|609.75×342.98|673.75×378.98|36px|
|1920 sequence · 정밀|490.64×275.98|554.64×311.98|36px|
|1280 선택 · 기본|383.85×215.91|447.85×251.91|36px|
|1280 sequence · 기본|264.74×148.91|328.74×184.91|36px|
|1280 선택 · 정밀|394.14×221.70|458.14×257.70|36px|
|1280 sequence · 정밀|275.03×154.70|339.03×190.70|36px|

8쌍 모두 document는1920×1080/1280×900 그대로다. 제안 목표인1920 +32px,1280 +24px를 충족했다. [전후 측정](paired-measurements.json). 이미지 확대는 원본16:9의 contain 크기 변화이며 crop/stretch가 아니다. transport/dock/시간축/clip행의 위치·크기와 표제/summary의 글자 크기·line-height도 유지됨을 [기하 보존 검사](geometry-invariants.json)에 기록했다.

**설명을 펼친 상태의 영상은 증가하지 않는다.** 1920의 동일 짧은 원문 설명을 펼치면 전후 모두426.38×239.84px이다. 공간 회수는 접힌 상태에 한정한다. 긴 제목/설명은 더 많은 높이를 쓰되 전체 텍스트를 보여주는 tradeoff다.

1920 Take 비교 stage는 전후 각각471×300px, 프레임0.750/0.500초로 같았다.1280의 수정 후 stage는471×288px이며 선행 잠금 기준선과 같다. **1280 비교는 이번 세션의 새 before/after 쌍이 아니라 이전 동일 소스 기준선과의 비교**로 구분한다. 선택 Take/승인은 변하지 않았다.

픽셀 확인: [1920 전](before/1920-sequence-detail.png) → [후](after/1920-sequence-detail.png), [1280 전](before/1280-sequence-detail.png) → [후](after/1280-sequence-detail.png), [설명 펼침+focus](after/keyboard-open-1920.png), [앱200% 긴 제목](after/title-unbroken-1280-app2.png), [긴 설명](after/description-long-1920-app1.png), [통제422 오류](after/controlled-422-header-1920.png), [1280 비교](after/comparison-1280.png)를 저장 후 열어 확인했다. native 제어와 focus 상태가 다른 이미지 전체의 zero-pixel-diff는 주장하지 않는다.

## 기능·경계 검증

|검사|실제 결과와 증거 범위|
|---|---|
|전체 비HTTP 회귀|**330 통과, 실패/오류/skip0**, [로그](full-non-http.log). F07·폼 입력 version·FQ/DM·미디어 기존 회귀 포함. 중첩 시나리오를 합산하지 않음|
|정적 검사|현재 모든 inline script를 추출한 `node --check` 통과. 테스트 파일 변경 없음|
|긴 제목·설명|1920/1280 앱100%,1280 앱200%의 한글/비분리 제목·설명 **9조건 통과**. 전체 문자열 유지, scrollWidth≤clientWidth, 가로 document 넘침 없음. [기록](after/boundary-results.json)의 앞2개는 잘못 고정된900px 관찰이라 제외|
|키보드·상태|**12조건 통과**.1920/1280 Enter 열기,Space 닫기,Tab 이탈,focus-visible; precision 저장 버튼 전체40px 보임. 미저장1.1초 편집이 설명 왕복 후 유지. 통제422 후 유지,취소 버튼 전체40px 보임,취소 후1초 원본 상태 복원. [기록](after/state-keyboard-results.json)|
|저장 거절|실제 save handler를 실행하되 브라우저 메모리의 fake fetch가422를 반환. mock POST1, 실제 서버 POST0. canonical 프로젝트 불변, pending 정리. 실제 서버 장애·저장 성공 검증이 아님|
|승인·선택|기존 승인 fixture를 읽음. 새 승인 API 호출0,Take1 유지,설명/비교는 채택으로 취급하지 않음|
|새로고침|현재 served 소스 해시 일치,wrapper1개/description1개,선택Take1/편집v1/첫컷1초,dirty/pendingfalse,페이지 프로젝트와 저장 상태 동일. [최종 읽기](after/reopened-final.json)|

앱200%에서는 세로 reflow를 허용해 긴 콘텐츠에 따라 document가2640–3411px가 됐다. 표준 배율 no-page-scroll 조건을 확대 상태에 강제하지 않았다. 이는 실제 브라우저 zoom200/400% 시험이 아니다. 키보드 검사는 해당 disclosure/저장/취소의 국소 경로이며 전체 작업 여정·screenreader 검증이 아니다. focus 스타일과 target 노출을 확인했으며 모든 outline 바깥 픽셀의 clipping을 자동 판정한 것은 아니다.

## 진단 오류·한계 기록

검사 도중 제품 결함과 진단 실수를 구분했다. 원기록을 삭제하거나 pass로 덮지 않았다.

1. 최초 test ID 생성이 method를 중복 연결해330 loader error를 만들었다. **실제 테스트 본문은 미실행**이었다. 정확한 ID로 고친 뒤330개를 실행해 통과했다. [최초 로그](initial-test-discovery-error.log), [정정](harness-correction.json).
2. 최초 inline 추출은 greedy regexp 때문에 closing script tag까지 포함했다. 모든 script body를 각각 추출해 검사한 뒤 통과했다. 제품 JS 문법 결함은 아니었다.
3. Ego 새 round가 viewport를900×845로 되돌려 초기 keyboard 두 관찰은1920 근거에서 제외했다. 이후 매 viewport를 고정하고12조건에 다시 포함했다. 잘못 이름 붙인 `keyboard-description-open-1920.png`는 사용하지 않는다. 유효 파일은 `keyboard-open-1920.png`다.
4.1280 비교의 첫 대기는 default가 Take1 영상+Take3 이미지인데 video2개를 기대해 timeout했다. 현재 페이지를 읽어 원인을 확인하고 Take1/2를 명시해 검사했다. 비교 기능 실패로 집계하지 않는다.
5. reload 뒤 round-scoped telemetry가 없어 진단 조회가 실패했다. 새로고침 자체는 성공했고 이후 hash·persisted state·중복DOM을 읽어 확인했다. **reload 이후 error-monitor0은 주장하지 않는다.** 그 전 통제 시나리오/서버 요청 기록과 구분한다.

HTTP20 suite, 실제 browser zoom, native IME, cross-browser, axe/screenreader, 전체 keyboard journey, 성능/실사용자 실험, 새 export/live provider는 이번 좁은 변경에서 미실행이다. unknown-save 브라우저 시나리오를 다시 실행하지 않았으며 기존 회귀 및 이전 브라우저 근거를 유지한다. 새 품질점수·경쟁사 동등성·production 완성을 주장하지 않는다.

## 환경·보존·최종 해시

Ego Lite CLI current0.6.0.20, UAChrome154.0.0.0, 단일 공간40을 before/after에 사용했다. 업데이트 안내가 있었으나 설치하지 않았다. 첫 localhost bind와 Ego 앱 연결은 sandbox OS 제한으로 미실행됐고, 기존 승인 범위의 정식 `require_escalated` 심사를 통해 각각 실행됐다. 권한 거절 우회나 보안 설정 변경은 없었다.

승인된 동일 합성 프로젝트1개, 시험 영상2/PNG1/WAV1 총1,066,575bytes만 isolated DB/media로 복제했다. `.env`·키·고객자료 없음,worker/provider 설정 없음,실제 non-GET0. 각각 [before](before/server-start.json)/[after](after/server-start.json)에 allowlist/hash/임시 경로가 있다. 페이지에서 외부 HTTP resource는0이며 Ego 제어 경로의 외부 중계/보관은 이전 고지된 미확인 경계다.

before listener07:05:04,after listener07:13:56 UTC 정상 종료. 공간40도 종료. 원본 합성 프로젝트 fingerprint `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`와 미디어가 불변이다. [before 종료](before/server-stop.json), [after 종료](after/server-stop.json), [공간 종료](after/space-closed.json). 현재 blocker 없음. 기존 앱 서버·사용자 DB는 변경하지 않았다.

|파일|최종 SHA256|
|---|---|
|index.html|`fd8efd8a3856ba5a209dc19fe4af0d228fa66b5501d546fcadd5f95c3ce6fefa`|
|studio.css|`4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`|
|studio-media.js — 불변|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|app.py — 불변|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

소스는 위 버전으로 고정한다. 이번 구현은 설명된 공간 목표를 충족했으며 다음 surface/버튼/위계 배치는 별도 결과 검토 전 진행하지 않는다. 기존 설계 소유 문서·사용자 명세·과거 보고서는 그대로 두고 구현 인계 링크만 갱신했다.
