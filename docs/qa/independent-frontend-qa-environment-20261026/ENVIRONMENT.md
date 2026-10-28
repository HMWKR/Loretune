# 실행환경·분담 사전 확인

현재 HTML0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109 일치. CSS2fbba70f…, media65e2468e…; 로컬 snapshot/mtime/hash 고정. 최신 구현 보고346tests와 AST346methods/62files는 구분하며 이번inventory에서 제품test0개 실행.

- Node26.11.1, Python3.15.0, FFmpeg/ffprobe9.0.2 사용 가능. unittest/NodeVM은 별도 snapshot에서 실행 가능.
- CUAinventory: Chrome extension 연결, 설치Chrome149.0.7827.55. 현재브라우저 UA/engine을새탭에서 검증하지 않았고 기존탭도claim하지 않음. CUA 공개문서: read-only evaluate, DOM/screenshot/locators/keyboard/logs, viewport capability. route/addInitScript/CDP/session 격리 API는공개목록에없음.
- IAB는목록에있지만엔진/버전미확인. Ego/Aside CLI설치, Ego가이드2.1.0문서조회만수행. 과거Ego0.6.0.20보고의evaluate/CDP/fetch대역은과거관측이며현재연결/엔진증명이아님. 이 세션 UI작업은CUA만사용하므로별도CLI로우회실행하지않음.
- Playwright caches:chromium1208/1228/1234,headless shells;firefox1532/1538;webkit2311/2336. 실행안함. Safari26.5와safaridriver설치, WebDriver허용/연결/테스트미검증. 캐시=설치증거이지coverage아님. WebKit=Safari로세지않음.
- 프로젝트node_modules없음. require.resolve 기준playwright,playwright-core,@playwright/test,puppeteer,axe-core,@axe-core/playwright,lighthouse,jsdom,happy-dom 미해결. PATHlighthouse/playwright없음. Python3.15의pytest/playwright/selenium/PIL없음;별도PATHpytest는존재하나필요없어실행안함. 추가설치0.
- workspace dependencies조회는local thread만지원한다는오류. 이미있는runtime으로계속가능하며설치우회없음.
- 기존브라우저fetch오류fixture는특정POST/GET대역만막고나머지는원래fetch로전달.새독립시험에는그대로재실행하지않음. 기존local_ui_fixture.py는공유/tmp데이터와8773listener를사용하므로실행금지. fal_creator_fixture_server.py도listener를여므로실행금지.
- 실제앱저장:sessionStorage초안/pending과IndexedDB loretune-recovery. 새탭만으로IndexedDB격리가보장되지않으므로현재사용자origin에서storage.clear/오류주입금지.

## 차단

정적GET http://127.0.0.1:8773/ 및 /studio.css,/studio-media.js가터미널에서URLError:Operation not permitted. 같은batch에3정적대상을각1회요청했으나모두차단,반복/우회없음. 로컬sourcehash와기존release-manifest읽기는완료;실제servedhash새검증은BLOCKED. 서버장애로해석하지않음. 키/DB/API실행/서버재시작없음.

## 역할 분담

본검증자:실제source함수VM,strictfake transport/requestledger,고정snapshot,초안/중복/비동기/시간축/저장복구/30회resourcecontrol. 실제브라우저성능·디코드는지원경로가확인되기전BLOCKED.
디자인검토자:본인에게지원되고승인된격리브라우저에서1920×1080/1280×900 geometry,Tab/accessible labels,zoom,scrollreachability,스크린샷. 사용자작업탭과동일data를변경하지않음. 기능mutation시나리오는demonstrablyfakebackend와request차단을확인하기전실행하지않음.
공유최소자료:3sourcehash,syntheticfixture ID,viewport/zoom,case ID/status,requestledger허용/차단건수,canonical fingerprint,증거경로. 계정·토큰·userstate공유없음.

사전기준은 ../frontend-functional-independent-20261026/criteria-before-execution.json 에고정. 현재작업은종합점수나기존81점수정이아님.
