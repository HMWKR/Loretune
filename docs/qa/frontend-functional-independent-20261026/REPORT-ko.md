# 프런트엔드 기능 QA — 독립 실행 결과

**현재 고정본에서 P2 결함 3건을 controlled VM으로 재현했다.** 늦은 poll 응답의 상태 퇴행, native 영상 종료 후 sequence 정지 누락, 브라우저 저장소 읽기 거부의 미처리 예외다. 실제 사용자 브라우저에서 재현했다는 뜻은 아니며, 서버·사용자 DB·권한을 변경한 증거도 없다. P0/P1은 이번 범위에서 확인하지 않았다.

실행 전 고정한 24개 case의 결과는 **PASS 11 / FAIL 4 / BLOCKED 6 / NOT RUN 3**이다. 실패 4개 중 ASY01/02는 같은 결함 FQ01이다. 별도로 실행한 기존 집중 unittest **21개는 모두 통과**했다. 이 두 숫자를 더해 하나의 테스트 수로 부르지 않는다. 기존 F07·DM01–03은 회귀 control로 유지되며 새 종합 점수는 만들지 않았다.

## 재현 결함

### FQ01 · P2 · 늦은 poll이 더 최신 상태를 덮음

- **코드:** [snapshot/index.html:564](snapshot/index.html:564). 1.5초 interval의 시작에서만 `busy`를 확인한다. `await fetch/json` 뒤 요청 순서·현재 revision·workspace/context·busy 재검사가 없고, 채팅 변화 시 `state=fresh`를 적용한다.
- **기준:** ASY01/ASY02. “이전 응답이 최신 화면 상태를 뒤로 돌리지 않음”은 Loretune 수용 기준이다. 격리·사용자 관측 중심 방법은 [Playwright best practices](https://playwright.dev/docs/best-practices)를 참고했다.
- **재현:** 같은 원본 poll callback을 VM에 로드한다. 첫 요청을 지연시킨 채 다음 poll을 시작한다. 두 번째 요청에 revision 3을 반환한 후 첫 번째에 revision 2를 반환한다.
- **기대 / 실제:** 최신 revision 3 유지 / `state.revision`과 채팅 렌더가 **3 → 2**. 별도 시나리오에서 idle에 시작한 요청이 대기하는 동안 현재 상태를 revision 3, `busy=true`, `dirty=true`, 작품 B로 전환해도 늦은 revision 2가 적용됐다.
- **영향:** 채팅·제작 상태 및 해당 snapshot의 화면 문맥이 오래된 상태로 돌아갈 수 있다. 서버의 승인 검증 우회나 저장된 프로젝트 파괴를 입증한 것은 아니다.
- **최소 수정 제안:** poll의 중첩을 제어하고 요청 세대/대상 문맥과 snapshot revision을 검증한다. 적용 직전에 busy/context를 다시 확인하며, backend revision이 모든 작업 상태 갱신을 포괄하는지도 함께 확인한다. revision 비교 하나만으로 다른 비동기 도메인의 최신성을 보장한다고 가정하지 않는다.
- **반대 조건 확인:** 시작부터 busy이면 요청 0건, 단일 fresh 응답이면 revision 2 정상 적용. [원 재현](vm-results.json), [정상 control](finding-controls.json).
- **재검증 상태:** 미수정. 실제 브라우저의 지연 네트워크 재현은 BLOCKED.

### FQ02 · P2 · native ended가 RAF보다 먼저 도착하면 무음 sequence가 끝나지 않음

- **코드:** [snapshot/studio-media.js:100](snapshot/studio-media.js:100), [tick:107](snapshot/studio-media.js:107). `video.paused ? at : …` 때문에 native 종료로 paused가 true가 된 이후에는 마지막 clock 값을 고수한다. 종료 이벤트 처리도 설치하지 않는다.
- **기준:** MED02. “실제 종료를 재생 중으로 표시하지 않고 다음 컷 또는 최종 정지로 진행”은 Loretune 기준이다. 종료 시 paused를 true로 바꾸는 전이는 [HTML media playback 규정](https://html.spec.whatwg.org/multipage/media.html#ended-playback)에 근거한 fixture다.
- **재현:** 외부 음악이 없는 3초 컷을 재생한다. RAF가 2.95초를 관측한 뒤 영상이 `currentTime=3`, `ended=true`, `paused=true`가 되고 다음 RAF를 3초와 8초에 실행한다.
- **기대 / 실제:** 마지막 컷이면 끝 시간과 정지 상태, 중간 컷이면 다음 컷 / **2.95초·‘일시 정지’ 버튼·RAF 1개**가 남는다. 두 컷 fixture에서도 첫 컷에 머물렀다. 소스가 2.975초인 현재 허용 오차 조건에서도 2.925초에 머물렀다.
- **영향:** 무음 sequence 또는 해당 시점에 원곡 clock을 사용하지 않는 재생에서 끝나지 않는 표시/다음 컷 정체가 생길 수 있다. 출력 렌더 오류나 실제 AV drift를 주장하지 않는다. canonical project와 편집 hash는 그대로였다.
- **최소 수정 제안:** 현재 controller/clip 세대에만 유효한 ended 처리를 두고 source 종료 위치를 타임라인 종료/다음 컷과 조정한다. 부족한 소스 길이를 허용하는 정책도 명시적으로 처리한다. 기존 dispose/late-event guard를 보존하며 stalled를 무조건 재생시켜 숨기지 않는다.
- **반대 조건 확인:** paused가 false인 동안 RAF가 정확한 3초를 먼저 관측하면 time 3, RAF 0으로 정상 정지했다. 현재 play Promise 거부와 waiting→playing 복구도 통과했다. [원 재현](vm-results.json), [종료 순서 control](finding-controls.json).
- **검증 한계:** native media event를 모델링한 원본 함수 실행이다. 실제 브라우저 디코드/프레임 정밀도를 측정하지 않았다. 기존 DM01–03과 다른 종료 순서이며 해당 결함을 재개방하지 않는다.

### FQ03 · P2 · 저장소 읽기 거부가 초기화·제출 경로의 미처리 예외가 됨

- **코드:** [snapshot/index.html:264](snapshot/index.html:264), [act guard:286](snapshot/index.html:286), [초기화:312](snapshot/index.html:312). `pendingId()`의 `sessionStorage.getItem()`에 방어가 없고 초기화에서도 바로 호출한다.
- **기준:** STO02. Web Storage 접근이 정책에 의해 거부될 수 있다는 [MDN 설명](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)을 참고했다. 구체적인 복구 안내·fail-closed 정책은 Loretune 제안이다.
- **재현:** 분리 VM의 Storage 대역에서 `getItem()`만 `SecurityError`를 던지도록 한다. 원본 `pendingId()`와 초기 recovery 표시 식, 원본 `act()`를 실행한다.
- **기대 / 실제:** 읽기 불가를 인지하는 안내와 안전한 제출 차단 / 초기화 식 및 act guard 양쪽이 `SecurityError`로 종료. 요청은 0건이다. 전체 화면에서 어떤 부분까지 보이는지는 실제 브라우저 미검증이다.
- **영향:** 저장소 이용이 차단된 환경에서 정상적인 복구 안내에 도달하지 못할 수 있다. 저장소 보안 정책을 우회해야 한다는 뜻은 아니다.
- **최소 수정 제안:** guarded storage adapter로 사용 불가 상태를 별도 관리하고, 기존 pending 여부를 읽지 못했을 때 “pending 없음”으로 취급하지 않는 안내를 제공한다. 초기 DOM 연결과 clear/reconcile 경로도 같은 정책을 사용한다.
- **반대 조건 확인:** 빈 정상 Storage는 초기화 성공. Take draft store는 malformed JSON·예전 shape를 무시하고 write-denied 시 메모리 초안을 보존했다. IndexedDB open 실패와 transaction abort도 제출 0건·busy 해제·안내로 처리했다.
- **근거:** [vm-results STO02](vm-results.json), [control](finding-controls.json). VM 결과의 단순 `source` 문자열에 있는 `264,284,310`은 위치 메모 오차이며 위 실제 행 **264,286,312**가 정확하다. 실행 코드는 해당 원본 함수를 사용했다.

## 실행 범위와 결과표

[실행 전 기준 JSON](criteria-before-execution.json)은 각 case의 출처, 기준 종류, fixture, 절차, 기대값을 기록한다. 기준 SHA256 `dac358193ab300990850fbd2a602afd74beba48e631085533bbc2507a1827ccb`는 실행 후에도 동일하다. [전체 결과 JSON](results.json)에 관측값, 상태, 환경, 증거, severity와 retest 상태를 붙였다.

| 영역 / case | 결과 | 확인한 범위 |
|---|---|---|
| ENV01 격리 | PASS | 고정 HTML hash; synthetic transport 허용/차단; 실제 전달 0 |
| FUN02 긴 한국어/중복 | PASS | 10,000자 payload 보존, 미입력 제출 0, pending 중 1회만 제출, 새 초안 유지 |
| FUN03 모델 슬롯 | PASS | chat/image/video를 독립 payload로 보존. 빈 image를 null로 보내며 첫 모델 자동 대체 없음 |
| STA01 기존 초안/context | PASS | F05/F06/F07, Take review, 비교 기본값의 현재 snapshot 회귀 |
| STA02 출력 revision | PASS | timeline 2와 과거 출력 1 구별, 이전 편집·테스트 미디어 표시, 원본 변경 없음 |
| ASY01/02 순서/문맥 | FAIL | FQ01의 두 반례 |
| ASY03 unknown 저장/취소 | PASS | 응답 불명은 취소 완료로 단정하지 않음. 같은 요청 GET, 추가 POST 차단 |
| MED01 기존 media 수명 | PASS | DM01–03과 late Promise/metadata/오류 control. 실제 decode와 구분 |
| MED02 active media 오류/종료 | FAIL | play rejection와 stall 복구 통과, native-ended 순서 FQ02 실패 |
| TIM01 공통 시간축 | PASS | 30×0.131초, trim 0.5초, 컷 경계 및 반개방 자막 구간. decoded frame 보장 아님 |
| STO01 저장소 형태/초안 | PASS | reload를 모사한 store 재생성, 작품 분리, bad JSON/old shape, in-memory fallback |
| STO02 접근 거부 | FAIL | FQ03 |
| STO03 요청 복구 저장 | PASS | 실제 requestCache 함수의 synthetic open 실패/transaction abort: POST 0; cache 대기 중 중복 1회 |
| PER01 반복 수명 | PASS | 60장면·180Take·120자막·각 1,000자 이상 label, controller 30+30회 교체; 활성 RAF 1, 정지 후 0 |
| FUN01/MED03/TIM02/PER02/PER03 | BLOCKED | native validation/IME, browser media 오류·디코드·정밀도, 실제 성능 trace 지원 경로 부족 |
| XBR01 | BLOCKED | engine 캐시/설치만 확인. Chromium/Firefox/WebKit/Safari 실행 coverage 없음 |
| DES01/DES02/VIS01 | NOT RUN | geometry·키보드/a11y·실제 zoom·시각 검토는 디자인 담당 소유 |

실제 사용자 role/name 기반 조작과 자동 대기는 [Playwright actionability](https://playwright.dev/docs/actionability)와 [Testing Library 원칙](https://testing-library.com/docs/guiding-principles/)에 따라 브라우저층에 요구했다. 이번 VM 실행은 그 브라우저층을 대체하지 않는다. hidden/disabled 조작 강제 실행은 하지 않았다.

## 성능·미디어 증거의 한계

- PER01은 **원본 JS의 controller 수명** 관측이다. 60개의 현재 실행 표본에서 활성 미디어 최대 1, callback 보유 요소 최대 2, RAF 최대 1/stop 후 0. fixture가 생성 요소를 의도적으로 배열에 보유하므로 heap 증가나 실제 DOM leak 판정을 하지 않았다.
- Node의 함수 실행 표본 p95는 [vm-results](vm-results.json)에 있지만 browser input-to-paint가 아니다. 캐시 장면 전환 p95≤200ms 목표를 통과 처리하지 않았다. 실제 main-thread task, LCP/INP/CLS는 미측정이다. [공식 CWV 기준](https://web.dev/articles/vitals)의 p75 LCP≤2.5s, INP≤200ms, CLS≤0.1은 현장 지표이며 이 로컬 시험으로 확정할 수 없다. [long task 정의](https://web.dev/articles/optimize-long-tasks)는 50ms이고 조사 대상으로 제안한 200ms와 구별했다.
- 로컬 합성 H.264 320×180/24fps/3초/72프레임, PCM 48kHz/3초, 한국어 SRT와 의도적 corrupt MP4를 준비했다. [fixture metadata](media-fixture-readiness.json)의 FFprobe 성공/실패는 **시험 데이터 준비 증거**다. 앱에서 재생·오류 처리가 성공한 증거가 아니다.
- ±1 decoded frame의 static seek, 100ms exploratory AV drift는 미측정이다. `timeupdate`나 VM currentTime을 프레임 정밀도로 보고하지 않았다. [requestVideoFrameCallback](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback) 근거에 맞는 실제 frame 증거가 필요하다.
- immutable model/input/price/rights/grant의 서버 계약 전체는 이번 프런트엔드 검증에서 재실행하지 않았다. model form payload·review 문맥·출력 revision에 한정했다. 기존 별도 backend 감사 결과와 혼합하지 않는다.

## 고정본, 재현 명령과 접근 경계

| 파일 | SHA256 |
|---|---|
| index.html | `0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109` |
| studio.css | `2fbba70fa95d035aecd19a0fd9a2e7e3e00c5f6b789cf3fe0c3eed5cbef5cfab` |
| studio-media.js | `65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328` |
| app.py | `7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d` |

snapshot 사본만 실행했다. [manifest](snapshot-manifest.json), [종료 hash](finish.json): source drift 0. [request ledger](request-ledger.json)는 신규 VM suite의 요청 9개, 실제 전달 0을 기록한다. 기존 집중 fixture의 내부 대역 호출을 같은 ledger로 포착했다고 주장하지 않는다. 초기 결과와 fixture stress 보강 전 기록도 `initial-*`로 보존했다.

프로젝트 루트에서:

```sh
node docs/qa/frontend-functional-independent-20261026/suite.cjs
node docs/qa/frontend-functional-independent-20261026/finding-controls.cjs
python3 -B docs/qa/frontend-functional-independent-20261026/run-focused.py
```

첫 명령은 **현재 4개 실패 case 때문에 exit 1이 정상적인 재현 결과**다. 집중 unittest의 21개에는 내부 JS scenario wrapper가 포함되며 wrapper 내부 개수를 다시 더하지 않는다. [실행 로그](focused-tests.log).

**환경 blocker:** 터미널에서 `http://127.0.0.1:8773/`, `/studio.css`, `/studio-media.js`를 읽는 정적 GET이 `Operation not permitted`로 차단됐다. 같은 batch에서 각 대상 1회씩 요청했으며 종료 후 재시도·다른 포트·다른 경로 우회는 하지 않았다. 완료한 작업은 로컬 원본/기존 manifest 확인과 snapshot 실행이며, 현재 served-byte 독립 확인은 BLOCKED다. 이는 서버 장애 판정이 아니다.

현재 CUA의 공개 API에는 read-only evaluate, DOM·screenshot·locator·keyboard·viewport 기능은 있으나 본 작업에 필요한 route/init script/격리 browser context 기능이 확인되지 않았다. 과거 Ego 스크립트를 현재 지원의 증거로 대신하지 않았다. browser fault injection, actual decoded-frame accuracy, cross-engine 및 live trace는 BLOCKED로 남겼다. 의존성 설치·설정 변경·서버 재시작·키 조회·실제 provider·DB 작업 0. 사용자 탭을 claim하거나 새로고침하지 않았다.

환경 도구 목록과 디자인 담당 분담은 [환경 보고서](../independent-frontend-qa-environment-20261026/ENVIRONMENT.md)에 있다. 이 한정 실행은 완료했으며 **세 P2의 수정·독립 retest가 남는다.** 전체 frontend 수용, WCAG 전체 준수, 실제 브라우저 성능, 제품 출시 준비의 통과 판정은 아니다.
