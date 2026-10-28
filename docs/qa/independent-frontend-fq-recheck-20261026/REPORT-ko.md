# FQ01–FQ03 독립 오프라인 재검증

**FQ01–FQ03은 요청된 Node VM/단위검증 범위에서 수정 확인됐다. 원래 반례 4개는 이전 snapshot에서 4 FAIL → 수정 snapshot에서 4 PASS다. 추가 독립 guard 15개와 집중 회귀 unittest 14개도 통과했다. 새 재현 가능 결함은 발견하지 않았다.** 기존 F07·DM01–03을 새 결함으로 재분류하지 않는다. VF01/VF02는 소스상 수정만 확인했으며 실제 시각 통과로 판정하지 않는다.

2026-10-26. 구현팀의 보고된 전체 시험 수를 독립 통과 수로 사용하지 않았다. 종합점수·전체 frontend 통과·실사용자 테스트·서버 배포판 검증을 주장하지 않는다.

## 원래 반례 전후

|이슈 / 원래 시험|동일 재현 절차와 기대|이전 실제|수정 후 실제|재검증 상태 / 수정 소스|
|---|---|---|---|---|
|FQ01 / ASY01 · 기존 P2|두 poll을 시작하고 revision 3 응답 뒤 revision 2 응답을 완료. 최종 revision 3 유지.|3→2로 회귀, draw `[3,2]`|3 유지, draw `[3]`|PASS · [index.html:566](after/snapshot/index.html#L566), 적용 직전 guard 571행|
|FQ01 / ASY02 · 기존 P2|idle에서 시작한 poll을 busy/dirty·작품 전환·revision 3 반영 뒤 완료. 현재 상태 유지.|revision 2로 덮고 draw 실행|revision 3 유지, draw 없음|PASS · index.html 566–585행|
|FQ02 / MED02 · 기존 P2|3초 무음 컷에서 마지막 RAF보다 native EOF를 먼저 발생. 정확 길이 및 25ms 부족 두 경우 모두 끝으로 이동하고 정지.|2.95초 / 2.925초에서 `일시 정지`, RAF 1개 지속|두 경우 모두 3초, `편집 재생`, RAF 0개. 프로젝트/편집 fingerprint 동일.|PASS · [studio-media.js:101](after/snapshot/studio-media.js#L101), tick 116행|
|FQ03 / STO02 · 기존 P2|sessionStorage.getItem이 SecurityError를 던진 상태에서 시작 recovery 표시 및 act 실행. 예외를 처리하고 POST 차단.|시작/제출 모두 예외 전파|둘 다 예외 없이 처리, fake 요청 0개|PASS · [index.html:265](after/snapshot/index.html#L265), act 284–293행|

원자료: [before 결과](before/vm-results.json), [after 결과](after/vm-results.json), [이전 실행 로그](before-original.log), [수정 후 실행 로그](after-original.log). 원래 반례의 입력·assertion은 보존했다. 새 global/helper 주입과 snapshot 경로·기대 hash, 네 반례만 선택하는 변경은 [before diff](before-harness-adaptation.diff), [after diff](after-harness-adaptation.diff)에 남겼다. 원래 JSON의 `source` 문자열은 역사적 행 번호로 보존돼 있으므로 현행 위치는 위 표를 기준으로 한다.

## 인접 guard

[독립 실행기](adjacent-controls.cjs)의 15개 case가 모두 PASS다. [상세 관찰값](adjacent-results.json)에 Node 버전, fixture, 기대를 확인하는 assertion 및 실제 값이 있다. viewport/zoom/browser는 VM에 해당하지 않아 null이다.

|독립 case|기대와 실제 확인|
|---|---|
|P-jobs / P-generation / P-chat / P-media|각 데이터만 따로 바꾼 동일 revision 7 응답이 적용됨. 변경을 한 응답에 몰아 다른 경로로 우연히 통과하지 않도록 분리. 선택·승인·timeline head·model snapshot fingerprint 유지.|
|P-guards|shot 변경, 다른 workspace, epoch 변경, busy, dirty를 각각 적용한 뒤 늦은 응답을 완료. 모두 state/draw 불변, in-flight 수 정상 회수.|
|P-bound|동시 읽기 최대 2. 두 번째 요청이 진행 중이어도 첫 응답으로 20% 진행 가능. 이후 80% 반영, 더 늦은 이전 순번의 동일 revision 20%는 폐기.|
|M-late|**`ended=true`를 명시한** 옛 callback이 수동 pause, 다른 clip, dispose, controller 교체 후 시간·버튼·RAF·canonical state를 변경하지 않음. 구현팀의 일부 late-event 시험이 ended 기본값으로 단락될 가능성을 보완한 검증이다.|
|M-trim|첫 컷 trim 2초·길이 3초 native 종료 → timeline 3초에서 다음 컷 source 1초. 두 번째 종료 → timeline 6초, 정지. 승인·Take 선택 불변.|
|M-short|기존 허용 범위 안인 25ms 부족은 종료. 51ms 부족은 오류 표시·정지, 가짜 완료 위치로 전진하지 않음. 50ms는 기존 구현 정책이며 프레임 정밀도 표준 판정이 아니다.|
|M-audio|원곡 offset 1초, audio 3.4초이면 timeline 2.4초. video EOF가 먼저 와도 원곡 clock 유지. 수동 pause 뒤 callback/RAF 불변. audio EOF 후 video 종료 처리 가능.|
|S-empty|정상 empty와 denied read의 recovery UI/failed flag가 다름. denied에서는 recovery 표시·조회 버튼 비활성·새 요청 0.|
|S-known|이전에 읽은 ID 또는 pendingRequest의 ID를 각각 보존. 저장소 읽기 거부 중 새 POST 없음, 해당 ID의 GET 조회만 1회. unknown 뒤에도 ID 유지.|
|S-settled|확정 200/400 응답 뒤 removeItem 실패가 committed/rejected를 unknown으로 바꾸지 않음. 다음 act와 불필요 재조회 차단. 저장소 복구 뒤 settled ID 정리 및 recovery 해제.|
|S-unknown|조회 transport 실패 및 저장소 read 실패가 함께 발생해도 unknown_checked 유지. draft clear 0회, ID 보존.|
|S-draft|sessionStorage 메서드가 아닌 **property getter 자체**가 거부되어도 실제 lazy wrapper로 Take 초안을 메모리에 보존. 다른 작품 key에 누출되지 않음. 탭 종료/재시작 후 지속 보존은 증명하지 않는다.|

추가 source 위치: refresh stale/draft guard [index.html:55](after/snapshot/index.html#L55), epoch 갱신 254–255·291·322행, lazy draft storage 96행, outcome 구분 268–312행, ended detach 77행, audio align 82행.

## 기존 F07·DM 및 집중 회귀

[실행기](run-focused.py)는 명시한 6개 module만 로드했다. **14 unittest PASS, 실패/오류/skip 0**. [로그](focused-regression.log), [결과와 내부 Node stdout](focused-regression-results.json).

- F07 comment draft: 16개 기존 내부 case. 지연 응답 중 새 입력, 작품/shot 전환, 지운 뒤 같은 값 재작성, 실패 응답, 반복 저장 회귀 유지.
- DM media lifecycle: 기존 12개 내부 case. stale media handler, 비교 진입 정지, metadata 전 seek, play Promise 거절 및 현행 오류 처리 유지.
- Take 초안 9개, 비교 기본값 5개, 저장 outcome/recovery 13개 내부 확인을 재실행했다.
- 순수 media/static 단위검증 8개와 구현팀 신규 frontend async 18개 시나리오를 재실행했다. 신규 18개는 unittest wrapper **1개**다.

내부 시나리오 수와 14 unittest, 원래 반례 4개, 추가 guard 15개는 중첩 범위가 있으므로 합산한 총 coverage 수를 만들지 않는다. 구현팀의 전체 329개 비HTTP 통과는 이번 독립 실행 범위가 아니다.

## VF01/VF02: 소스 확인만

부모의 VF01/VF02는 구현 보고서의 VQ1/VQ2와 대응한다. [읽은 소스 증거](source-only-observations.json).

- VF01: `revealTakeFocus`는 strip/button 좌표와 4px 여유로 해당 strip의 scrollLeft만 조정한다([index.html:103](after/snapshot/index.html#L103)). `focusin` 연결은 321행이며 선택/승인/저장 호출이 없다. 클릭 선택 handler는 별도로 유지. [studio.css:366](after/snapshot/studio.css#L366)에 padding 4px 존재. **실제 Tab/Shift+Tab의 전체 target 가시성은 BLOCKED/미검증.**
- VF02: [studio.css:565](after/snapshot/studio.css#L565)의 장면명 `overflow-wrap:anywhere` 확인. 표시 문자열이나 승인·선택 로직을 변경하지 않음. **실제 긴 한글/영문·동일 prefix 이름의 줄바꿈과 1280×900/1920×1080 화면은 BLOCKED/미검증.**

## 고정 버전·재현·보존

현재 snapshot:

|파일|SHA-256|
|---|---|
|index.html|`07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3`|
|studio-media.js|`ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`|
|studio.css|`a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0`|
|app.py|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

[시작 manifest](snapshot-manifest.json)에 before/after의 bytes·mtime·hash를 기록했다. [종료 확인](final-source-check.json)에서 현행 4개 소스와 frozen snapshot 및 시작 해시가 모두 동일하다. 원본 과거 보고서/결과를 변경하지 않았다. 쓰기는 이 QA 폴더와 테스트가 만든 일회성 임시 fixture에 한정했다. 공유 DB는 열거나 쓰지 않았다.

프로젝트 루트에서 재현:

```sh
node docs/qa/independent-frontend-fq-recheck-20261026/before/original-replay.cjs
node docs/qa/independent-frontend-fq-recheck-20261026/after/original-replay.cjs
node docs/qa/independent-frontend-fq-recheck-20261026/adjacent-controls.cjs
python3 -B docs/qa/independent-frontend-fq-recheck-20261026/run-focused.py
```

before의 exit 1은 원래 네 결함 재현으로 기대된 결과다. after/adjacent/focused는 exit 0. 모든 app fetch는 VM 내부 fake 응답이다. [원 반례 ledger](after/request-ledger.json), [추가 guard ledger](adjacent-request-ledger.json)의 forwarded는 0. 추가 guard와 집중 회귀는 [offline guard](offline-node-guard.cjs)로 Node net/http/fetch를 차단했고 Python runner도 socket bind/connect를 차단했다. API/실제 브라우저/포트/공유 데이터/provider 호출·키 접근·의존성 설치는 0회다.

## 남은 검증 경계

오프라인 수정 확인 범위는 닫는다. 실제 decoder의 native ended 순서, decoded-frame seek 정확도, AV drift, 실제 Storage 보안 정책·reload, served hash, 실제 focus 가시성과 장면명 overflow는 이번 결과로 통과 처리하지 않는다. DOM 및 media 객체는 fake이며 실제 재생이 아니다. 새로운 최소 수정 제안은 없다.

**차단 상태:** 실제 브라우저 로드/HTTP/listener는 이번 위임에서 명시적으로 금지되어 시도하지 않았다. 구현 보고서에 따르면 이전 `TaskSpace35` 격리 페이지로 앱 소스·합성 QA 프로젝트 1개·로컬 미디어 4개를 로드하는 작업은 자동 승인 심사가 “해당 목적지에 대한 민감한 데이터 공개 승인이 없습니다”라는 이유로 거절했고, 로드는 실행되지 않았다. 이번 검증은 다른 경로로 재시도하지 않았다. 이 과거 거절은 앱 결함이나 이번 오프라인 실행 실패가 아니며, 브라우저 재검증만 미완료 상태로 남긴다.
