# 현재 서버 화면 기준선 · 두 폼 브라우저 확인

검증 시각: 2026-10-26 06:19–06:36 UTC. **제품 소스 수정 0, 실제 저장 0, 외부 공급자 호출 0.** 이 문서는 구현 결과가 아니라 다음 시각 변경 전 기준선과 작은 후속 변경안을 설명한다.

## 결과 먼저

- 현재 `index.html`, `studio.css`, `studio-media.js`를 실제 localhost HTTP로 제공해 시작·종료 시 응답 SHA256이 파일 SHA256과 일치했다. `document.write` replay가 아니다.
- 연출 취향 `#preferenceForm`, 기존 자유 입력 로컬 초안 `#chatForm`에서 6조건씩 **12건 통과**. `#modelChatForm` 실제 모델 대화는 이번 검사의 대상이 아니다.
- 1920×1080을 주 기준, 1280×900을 보조 기준으로 기본/승인, 순서 재생+정밀 편집, 미저장, 비교 화면을 저장하고 픽셀을 열어 확인했다. 거절/미확정 오류 캡처는 1920에서 수행했다.
- 정상 잠금 상태에서 document 높이는 각각1080/900px. 정밀 편집의 저장 버튼은 내부 스크롤을 통해 전체40px 높이가 보였다. 전체 키보드 여정이나 모든 내용의 무스크롤 보장을 뜻하지 않는다.
- 최종 미저장 상태 false, pending request 없음, 처리되지 않은 JS 오류0. 합성 프로젝트·소스·미디어 불변, 서버 non-GET 요청0. 공간37과 임시 listener 모두 종료했다.

## 실행 환경·자료·권한 범위

Ego Lite 설치 브라우저, CLI가 보고한 current version **0.6.0.20**, UA `Chrome/154.0.0.0`. 브라우저 앱 전체 버전은 이번에 별도 확인하지 않았다. 업그레이드 안내가 있었지만 설치/업그레이드는 하지 않았다.

실제 접속 주소는 `http://127.0.0.1:64306`였다. 06:36:21 UTC에 종료돼 현재 접속용 주소가 아니다. 기존 승인 합성 프로젝트 `디자인 시스템 기능 QA 20261026` 하나와 시험 영상2, PNG1, WAV1(총1,066,575bytes)만 별도 임시 DB/asset 디렉터리에 복제했다. 원본 DB는 read-only로 해당 프로젝트를 읽었고 사용자 데이터·`.env`·자격증명은 복제하지 않았다. 정식 `app.server()`의 GET handler를 사용하되 검증용 handler는 POST/PATCH를405로 차단하며 worker/provider/chat 연결은 설정하지 않았다.

원본 프로젝트 fingerprint: `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`.

파일 allowlist/해시/크기는 [server-start.json](server-start.json), 요청과 종료 증거는 [server-stop.json](server-stop.json), 브라우저 최종 확인은 [browser-final.json](browser-final.json), 공간 종료는 [space-closed.json](space-closed.json)에 있다. 원본과 별도로 만든 합성 복제본은 재현을 위해 `server-start.json`의 data 경로에 보존했다. 개인정보·비밀키는 없다.

Ego 제어 경로의 외부 중계/보관 여부는 이전에 고지된 미확인 경계 그대로다. 앱 페이지에서 관측한 외부 HTTP resource는0이지만 이것으로 Ego 제어 경로 전체의 전송/보관을 보장하지 않는다. 새 수신자·파일 업로드·Library 업로드는 사용하지 않았다.

|파일|현재 파일 및 HTTP 응답 SHA256|
|---|---|
|index.html|13797f1b7bf9346edf7063c72347c98abd41f3ac4e47aa9a51363e1f1e602943|
|studio.css|a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0|
|studio-media.js|ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9|
|app.py(파일)|7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d|

## 브라우저 폼 검증

실제 DOM 폼의 fill/click과 현재 submit/request controller를 실행했다. `/api/action` 응답만 페이지 메모리에서 지연/성공/422/응답 유실로 통제했다. `/api/state`는 실제 격리 서버 GET이었다. 테스트에서 성공 응답을 주었다고 실제 계획/취향 DB 저장이 일어난 것은 아니다.

|조건|취향 제안|로컬 자유 입력 초안|실제 확인|
|---|---|---|---|
|제출 후 수정 없는 성공|PASS|PASS|해당 폼 정상 초기화|
|대기 중 새 문장 작성 후 성공|PASS|PASS|새 문장 보존|
|편집 후 제출 당시와 같은 내용으로 복귀|PASS|PASS|입력 버전이 달라 초기화하지 않음|
|문맥 identity 변경 후 복귀|PASS|PASS|이전 요청이 현재 초안을 지우지 않음|
|확정422 거절|PASS|PASS|입력 보존, pending 정리|
|응답 미확정·재제출·기존 요청 확인|PASS|PASS|입력/pending 보존, 추가 POST 없음, 기존 요청 GET 결과로 복구|

문맥 검사는 **페이지 메모리의 workspace identity를 잠시 변경하고 복원하는 통제 실험**이다. 실제 다른 프로젝트를 생성하거나 사용자 프로젝트를 전환한 시험이 아니다. 실제 UI 이동의 전체 여정은 이번 범위에서 미실행이다. 입력은 native IME 조합이 아니라 자동 fill로 넣었다.

모의 POST12회와 모의 기존 요청 조회2회만 사용했다. 미확정 재제출 시 POST가 늘지 않았으며 모든 실제 서버 요청은 GET이었다. 각 결과/시각은 [browser-form-results.json](browser-form-results.json). 성공·거절·unknown의 데이터 보존은 PASS이나 서버 영속 저장/전체 제품 완성도 판정으로 확대하지 않는다. 기존 비HTTP330 통과는 앞선 구현 묶음 결과이며 이번12와 합산해 새 전체 테스트 수로 만들지 않는다.

통제 오류 이미지: [거절](controlled-preference-rejection-1920.png), [미확정](controlled-preference-unknown-1920.png). 화면에는 합성 입력이 유지된다. 미확정은 연결 문제라고 단정하지 않고 기존 요청 확인/재실행 금지를 표시한다. 취향 dialog의 실제 복구 버튼은 dialog 밖에 있어 닫고 접근했다. 일반 거절 안내는 상세 오류 펼침을 요구한다. 이를 새 수정 완료라고 표시하지 않으며 다음 위계 논의의 관찰 사항으로 남긴다.

## 비교 가능한 현재 화면

`locked-*`가 최종 비교 기준선이다. 같은 장면01/Take1, 앱 글자배율100%, DPR1, CSS viewport emulation, visualViewport.scale1, 알림/작품 설정 접힘을 고정했다. 기본은 선택한 Take 원본1.000초, sequence는 편집0.500초=원본trim0.250+0.500초, 비교는 공유경과0.500초(왼쪽0.750/오른쪽0.500)다. 시간/모드/dirty를 캡처 앞뒤로 검사했다. **실제 브라우저200/400% 확대를 한 것은 아니다.**

|뷰포트·상태|실제 contain 영상 영역|document 높이|이미지|
|---|---:|---|
|1920 기본·기존 승인|703.85×395.91px|1080px|[기본](locked-basic-approved-1920.png)|
|1920 sequence+정밀 편집|490.64×275.98px|1080px|[상세](locked-sequence-detailed-1920.png)|
|1920 미저장1.1초 첫 컷|490.64×275.98px|1080px|[초안](locked-dirty-1920.png)|
|1920 Take1/2 비교|비율별 contain, 각 stage471×300px|배경1080px|[비교](locked-comparison-1920.png)|
|1280 기본·기존 승인|383.85×215.91px|900px|[기본](locked-basic-approved-1280.png)|
|1280 sequence+정밀 편집|275.03×154.70px|900px|[상세](locked-sequence-detailed-1280.png)|
|1280 미저장1.1초 첫 컷|275.03×154.70px|900px|[초안](locked-dirty-1280.png)|
|1280 Take1/2 비교|비율별 contain, 각 stage471×288px|배경900px|[비교](locked-comparison-1280.png)|

각 이미지 옆 JSON에 시간·선택·프레임·레이아웃·computed 값이 있다. 비교 후 Take 선택/승인/프로젝트 JSON은 그대로였다. 기존 승인 상태를 관찰한 것이며 이번에 승인 API를 실행하지 않았다. 미저장 편집은 취소했고 원본은 유지했다.

정밀 입력 내부 패널은 clientHeight180px/scrollHeight730px였다. `#saveTimeline`에 DOM focus를 주었을 때 내부 scrollTop550.5px로 이동해 버튼40px 전체가 노출됐고 document 높이가 늘지 않았다. [1920](precision-focus-1920.json) / [1280](precision-focus-1280.json). Tab-only 모든34대상 검증으로 확대하지 않는다.

**촬영 한계:** 1280 기본 이미지에는 native video control의 일시적 spinner가 남아 있다. 당시 readyState/paused/currentTime은 검사했지만 이 이미지를 모든 픽셀이 안정된 golden image라고 사용하지 않는다. geometry 기준은 유효하며 다음 pixel comparison에서는 native 제어 오버레이 안정 조건을 추가해야 한다. 초기 `observed-900x845-not-1920`은 뷰포트가 달라 제외했다. 초기 `sequence-detailed-1280` 등 비locked 파일은 알림/재생 모드 조건이 달라 최종 기준선으로 쓰지 않는다. 이전파일은 증거 보존을 위해 삭제하지 않았다.

## 실제 확인한 토큰 후보와 해석

현재1920 computed 값: 본문14px/400, 장면명13px/500, 보조12px/400, 주요 버튼14px/500, 타임라인 상태13px/400. 전체 semibold라거나 글자 축소가 필요하다는 근거는 없다. 캔버스#101010, 패널#1B1B1B, 기본문자#F4F4F2, 보조#BDBDBB 등 기존 역할을 유지한다.

|선언·위치|관측한 현재값|판정|
|---|---|---|
|`audioWave()`, index.html:45 SVG inline 배경|rgb(16,16,16), literal#101010|`--ui-canvas`와 정확히 같아 alias 재사용 가능|
|같은 polyline stroke|rgb(221,221,221), literal#ddd|기존#DEDEDB/#D8D8D2와 다름. 비슷한 token으로 임의 교체 금지|
|studio.css:297 `.lt-ui .lt-timecode`|ui-monospace, monospace|시간 표시 역할 font token화 후보; 새 폰트 설치 불필요|
|studio.css:190 skip link|#FFF/#000, padding10px|유효한 대비쌍. #F4F4F2/#101010으로 자동 치환하면 값 보존 아님|
|studio.css:118 dialog|실제 computed#FFF|일부 input의#F4F4F2와 구분. literal 검색만으로 모두 같은색이라고 판단하면 안 됨|
|clip input/비교 버튼/precision summary spacing|6px,6px10px 및 viewport별6px/10px|반응형 적용 차이 존재. 일괄4/8단위 반올림은 값 보존 아님|

`locked-*.json`의 computed가 명시된 뷰포트의 기준이다. [active-declarations-verified.json](active-declarations-verified.json)은 실제 CSSOM selector와 선언의 연결을 확인한 보조자료다. 이 마지막 round는 viewport를 다시 고정하지 않아 **반응형 spacing의1920 판정 자료로 쓰지 않는다**. 최초 후보파일의 matchingRules가 비어 있던 것은 modern nested CSSRule 순회 진단 코드 문제였으며 마지막 순회에서 보완했다. 제품 CSS 결함이 아니다.

## 다음 묶음 제안 — 아직 적용하지 않음

먼저 값 보존 정리를 작은 두 항목으로 제한하는 것이 적절하다. 현재 공간 크기 차이는 재생/정밀 모드의 기능량 차이도 포함하므로 글자나 필수 조작을 일괄 압축하는 근거가 되지 않는다.

1. `audioWave()`의 배경만 기존 `--ui-canvas`를 참조. 선은 정확한#DDDDDD를 보존하는 `--ui-waveform-stroke` 역할 token을 만들고 실제 파형 데이터·좌표·높이는 유지한다.
2. `.lt-timecode`의 정확한 `ui-monospace,monospace`를 `--ui-font-timecode`로 추출. 대상은 sequence/비교의 현재 시간 표시다. 다른 diagnostic font shorthand와 spacing은 이 묶음에서 제외한다.

대안: literal 유지가 가장 적은 변화지만 의미와 재사용 기준이 분산된다. 비슷한 기존 색으로 통합하면 실제 렌더값이 바뀌므로 제외한다. 전체 CSS 일괄 정리도 반응형 override를 함께 바꿀 위험이 있어 제외한다. 선택안은 **2파일의 두 역할만 정리하며 외형 변화가 없어야 한다**.

통과 조건:

- 수정 전 파일 snapshot/hash와 작은 diff 보존, 단일 writer. 기존 palette·font·spacing·DOM·handler·미디어 lifecycle·승인 계약 불변.
- 두 뷰포트에서 같은 fixture/시각/재생모드/정밀패널 상태의 background/stroke/font-family/line-height/치수 computed 값 일치. 타임코드 숫자폭 보존.
- 정적 검사, 파형/미디어·초안 보호 관련 회귀, 최종 전체 suite를 해당 권한 환경에서 실행하고 HTTP를 별도 표기. 12브라우저 검사를 새 전체 테스트로 합산하지 않음.
- 실제 served 해시 확인. 재촬영 시 스피너·native controls·포커스 상태를 별도 고정하고 앱 UI 영역 pixel diff를 확인. 불일치를 무시하거나 페이지 clipping으로 숨기지 않음.
- 값 변화/회귀가 있으면 이 작은 묶음 diff만 되돌림. checkout 전체 reset/DB 복구는 하지 않음.

**그다음 별도 공간 묶음의 후보:** 정밀 편집이 열린1920 timeline dock은약359px이며 실제 입력은 내부 스크롤을 요구한다. 중간 미디어는 기본704×396에서 sequence+상세491×276으로 작아진다. 현재 CSS의 열린 dock `minmax(340px,38%)`, 내부 precision 최소180px와 재생 transport가 높이를 나눠 쓴다. 이는 관측한 공간 배분 차이이며 새 기능 결함/사용자 실패로 판정하지 않는다. 다음 계획에서 선택Take/sequence × 정밀접힘/펼침의2×2를 분리 측정한 뒤, 읽기용 타임라인과 상세 입력의 배분을 최소 조정하는 대안을 비교한다. 텍스트축소·caption제거·overflow강제은폐·패널 전면재구축은 제외한다.1920 핵심 조작/공유 시간축/내부 focus 접근을 유지하지 못하면 적용하지 않는다. **이번 턴에는 이 공간 수정도 하지 않았다.**

## 범위·미검증·정리

현재 단계에 실행/권한 blocker는 없다. 실브라우저 확대200/400%, 앱200% 신규 재검증, native IME, screenreader/axe, cross-browser, 실제 다른 프로젝트 UI 전환, 전체 키보드 여정, 새 렌더/공급자/실청구는 이번 범위에서 NOT RUN이다. 선행 보고서의 독립 검증과 혼동하지 않는다. 새 품질점수나 경쟁사 동등성 평가는 없다.

도구 역할: Ego skill의 단일 TaskSpace/현재 화면/종료 절차를 적용했다. 앞선 Hallmark/Impeccable 검토의 입력 보존·작업 중심·값 보존 원칙을 이 기준선에 연결했다. 이번에 해당 detector/엔진/CLI 평가를 다시 실행했다고 주장하지 않는다. 기준과 이유는 [기존 PLAN](../../codex-cli-assessment-20261026/PLAN-ko.md), [reference lock](../../design-system-redesign-20261026/REFERENCE-LOCK.md), [방법론 적합표](../../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md)를 따른다.

변경 기록: 이 기준선의 진단 스크립트·이미지·측정 JSON·보고서만 추가했다. 원본 QA/명세/제품 파일은 변경하지 않았다. 공간37은06:36:13경 종료, 임시listener는06:36:21종료(exit0/socket closed). 기존 서버 재시작이나 추가 listener는 남기지 않았다. Library 연결 차단은 별도이며 이번에 업로드를 시도하지 않았다.
