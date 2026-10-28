# 취향 제안·로컬 기획 초안 보존 — 첫 구현 묶음

> 후속 기준선 검증 완료(2026-10-26 06:36 UTC): [현재 served 화면과 브라우저12건 결과](served-baseline/REPORT-ko.md). 동일 소스의 실제 브라우저 통제 검사12/12,1920/1280 잠금 캡처8개 및 오류2개를 확인했다. 원본 쓰기·제품 추가 변경 없이 임시 서버와 검증 공간을 종료했다. 아래 테스트 수/미실행 표기는 첫 구현 당시 이력이며 최신 브라우저 범위는 연결된 보고서를 따른다.

2026-10-26. 계획 설명 체크포인트 이후 승인된 첫 묶음만 적용했다. **제품 변경은 `index.html` 한 파일**이며 CSS·미디어 JS·backend는 그대로다. 실제 모델 대화 `#modelChatForm`, 검토 의견 `#comment`, Take 검토 controller의 변경이 아니다.

## 결과와 수정 이유

대상은 `#preferenceForm`의 `preference_propose`(연출 취향 제안)와 `#chatForm`의 `chat_plan`(로컬 제작 기획 초안)이다. 이전에는 성공 응답마다 무조건 `reset()`하여 대기 중 새 입력이나 다른 작품의 입력을 지웠다.

수정은 세 조건을 모두 확인한다.

1. 제출 당시 workspace·stable project ID·작품 이름·IP와 현재 문맥이 같아야 한다. 실제 `draw()`에서 문맥 변경 epoch를 관찰하므로 A→B→A 왕복도 구별한다. 동일 문맥의 정상 refresh는 epoch를 바꾸지 않는다.
2. 폼별 `input/change/reset` revision이 같아야 한다. 텍스트를 수정했다 원문으로 되돌리거나 동일 내용의 입력 이벤트가 발생해도 새 의도로 보존한다. 다른 폼의 편집은 영향을 주지 않는다.
3. 현재 FormData가 제출 snapshot과 같아야 한다. 이벤트 없이 프로그램이 복원한 다른 값도 지우지 않는다.

이 조건을 통과한 정상·무수정 성공만 기존 초기화 동작을 유지한다. 새로운 프레임워크나 서버 mutation 경로는 만들지 않았다. 기존 `act/sendRequest`의 busy, request ID, unknown, 기존 요청 조회, 저장소 거부, 승인/가격/권리 동작은 변경하지 않았다.

## 수정 파일과 보존

- `index.html`: `proposalFormContext`, `captureProposalForm`, `resetProposalFormIfCurrent`, 두 폼의 입력 revision listener, `draw()`의 문맥 관찰 및 두 submit handler.
- `tests/frontend_proposal_drafts.cjs`: 실제 소스 핸들러/요청 controller를 실행하는 Node VM 회귀. DOM·FormData·fetch·storage·refresh는 명시적 합성 대역이다.
- `tests/test_proposal_drafts.py`: 기존 unittest discovery에 연결하는 wrapper1개.
- [최소 product diff](implementation.patch), [수정 전 원본](before/index.html), [guard 불변 비교](unchanged-guards.json), [전체 해시/검증 manifest](release-manifest.json).

기존 119개 추적 파일 중 변경은 index.html만이다. 요청 controller, F07 comment submit, 실제 모델 대화 submit은 byte-identical이다. CSS·재생 코드·provider/DB 코드는 불변이다. 실제 고객 자료·공유 QA DB·기존 미디어·이전 QA 보고서는 변경하지 않았다. 진단 로그와 이번 보고서만 새 QA 폴더에 기록했다.

## 검증 — 전후를 같은 검사로 비교

|검사|수정 전|수정 후|증거 / 한계|
|---|---|---|---|
|최초 6개 반례/대조군|4 실패, 거절2 통과|6 통과|두 폼 각각 입력 변경, 작품 전환 후 새 입력, 거절. [before](before-results.json), [after](after-results.json)|
|확장 동작38개|26 실패 /12 통과|38 통과|성공 무수정, A→B·A→B→A, 동일 내용 편집, change event, 프로그램 값 변경, workspace/project ID/IP, 확정 거절, unknown 조회만, 중복, committed refresh failure, refresh 중 새 입력, 다른 폼, 동일 문맥 refresh|
|문맥 관찰 연결1개|미구현 실패|통과|실제 draw에 연결 확인. 동작38개와 별도 정적 확인이며 총39개로 표시|
|관련 unittest14개|이번 묶음의 수정 전 전수실행 아님|14 통과|새 wrapper + FQ/VF/F07/DM·미디어 기존 회귀. [로그](focused-regression.log)|
|기존 비HTTP 전체 suite + 새 wrapper|이전329는 역사적 기준|**330 통과**, 37.147초|[전체 로그](full-non-http.log). 새 JS39개를 이 수에 더하지 않음. 최종 fixture 데이터 모양을 실제 폼에 맞춘 뒤 새 wrapper도 재검증: [최종 집중 로그](final-targeted.log)|
|문법|—|inline app JS·새 JS `node --check`, Python test AST 통과|[정적 결과](static-checks.json). 실행되지 않은 browser 결과가 아님|
|실제 HTTP20 / 브라우저|이전 별도 결과만 존재|**이번에는 NOT RUN**|새 listener/서버 재시작/브라우저 로드 없음. 새 source의 served hash/IME/native submit을 확인했다고 주장하지 않음|

수정 전 회귀 exit1은 의도된 반례 실패이고, 수정 후 exit0은 모든 기대값 통과다. 대기/중복/unknown 각 시험에서 POST1을 확인했고 payload는 제출 당시 A의 원문을 보존했다. 회수 조회는 기존 request ID만 사용했다. 실제 네트워크나 DB 호출 대신 VM 대역으로 검사했다. 전체 비HTTP suite의 DB/미디어는 기존 격리 fixture를 사용했다.

실행한 전체 검사는 기존 `run-non-http.py`가 이미 구분한 HTTP20개를 제외했다. 이 실행기의 과거 출력 문구 “already-denied”는 역사적 필터 이름이며, 이번에20개가 새로 거절됐다는 뜻이 아니다. 이번 실행·접근 blocker는 없었고 HTTP/브라우저는 범위상 미실행이다. 330+과거20을 새 단일350개 실행으로 합산하지 않는다.

## 최종 동결 해시

|파일|SHA256|
|---|---|
|index.html|13797f1b7bf9346edf7063c72347c98abd41f3ac4e47aa9a51363e1f1e602943|
|studio.css — 불변|a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0|
|studio-media.js — 불변|ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9|
|app.py — 불변|7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d|
|tests/frontend_proposal_drafts.cjs|34b741b5d2f2985cedc0331d54fea596d90c2f562f92675ad427bc51d532a990|
|tests/test_proposal_drafts.py|07198c212506b289d39c89e0b0dc065451d903b990f1f3a41d10d0fad73172d3|

동결 시각은 manifest의 UTC를 따른다. 실행 서버 revision을 뜻하지 않는다. 이번에는 서버를 시작·재시작하지 않았다.

## 다음 단계: 현재 실행 화면 기준선 확보 계획 — 아직 미실행

다음은 시각 수정 전에 필요한 측정이며 시각 소스 변경 승인을 대신하지 않는다. [PLAN-ko.md](../codex-cli-assessment-20261026/PLAN-ko.md)의 핵심은 **문제/가설 분리 → 이유·대안 설명 → 작은 단일 writer 변경 → 같은 조건 전후 검사 → 회귀·동결**이다. 입력 잠금이나 일괄 초기화 폐기 대신 문맥+revision 보호를 선택한 이유는 대기 중 작업을 허용하면서 완료된 제출만 정리하기 위해서다. 이번 첫 묶음은 끝났고 다음 token/공간 묶음은 시작하지 않았다.

### 데이터와 전송

1. 기존 `/tmp/loretune-ms-qa-20261025/studio.sqlite3`에서 **합성 `디자인 시스템 기능 QA 20261026` 프로젝트1개만 read-only로 추출**하고, 별도 임시 QA DB를 만든다. 전체 원본 DB/다른 프로젝트/작업/요청/비용 원장을 복사하지 않는다. 원본 fingerprint가 과거 `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792`와 다른 경우 조용히 재사용하지 않고 대상·범위를 확인한다.
2. 해당 프로젝트의 기존 시험음 WAV1·시험패턴 MP4 2·단색 PNG1만 사용한다. [이전 allowlist](../frontend-fq-vq-fixes-20261026/authorized-verification/final-preservation.json)의 정확한 파일명/해시/크기4개를 다시 비교한다. 합계1,066,575bytes. `.env`, 계정자료, 실제 고객 자료, 다른 /tmp 파일은 제외한다. 이전 inline fixture를 최신 소스로 가장하지 않는다.
3. 현재 `app.server(isolated_data_path, 0)`의 정상 localhost 경로로 **127.0.0.1 임시 포트**에 시험 서버를 연다. 실제 소스 HTML/CSS/JS를 제공하며 provider_adapter/chat_configuration/media_configuration는 설정하지 않는다. 모델/렌더 worker는 시작하지 않는다. 초기 recover 처리는 격리 DB에만 영향한다. 별도 새 인증키를 읽거나 저장하지 않으며 앱의 임시 로컬 접근 token은 메모리에서만 사용하고 출력하지 않는다.
4. Mac의 Ego Lite 새 검증 공간에서 이 loopback URL을 연다. 실제 응답 HTML/CSS/media JS byte hash가 위 소스와 같은지 확인한다. UI 주소와 viewport를 실제 측정한다. 이 경로는 기존 about:blank inline replay와 달리 **로컬 서버 제공 화면**이다. 전체 실제 모델/클라우드 검증이라는 뜻은 아니다.
5. 폼 지연/거절/unknown 검사는 페이지 안 controlled fetch 대역으로 수행한다. 실제 서버 POST/유료 작업은 차단하고 합성 초안만 사용한다. GET/static/media만 loopback으로 허용한다. 응답 성공 대역은 DB 저장 성공 증명이 아니며 frontend 응답 처리 시험으로 표기한다. 이후 대역을 복원한다.
6. 페이지의 외부 요청0과 read-only/대역 요청 목록을 기록한다. Ego 제어 인프라의 외부 중계·보관 여부는 여전히 미확인이며, localhost라는 이유로 모든 제어 데이터가 Mac 밖으로 나가지 않는다고 보장하지 않는다. 캡처·HTML·합성 상태·경로/해시가 제어 경로에 포함될 수 있다는 기존 고지는 유지한다.

### 승인 범위 판정

기존 사용자 승인(2026-10-26 04:56UTC)은 **동일 합성 프로젝트1개·미디어4개를 Mac Ego Lite 격리 검증에 로드하고, 127.0.0.1 임시 HTTP 시험 서버를 열어 종료**하는 구체적 범위였다. 앞선 localhost 검증 서버 사용 승인도 있다. 위 계획의 대상·목적은 그 범위 안이며 새 모델/고객 데이터/공급자 전송/업로드/설치 권한을 요구하지 않는다. 다만 실제 다음 실행의 정식 도구 심사는 아직 요청하지 않았으므로 승인심사 통과 또는 브라우저 접근 가능으로 표시하지 않는다. **기존 about:blank replay에서 실제 loopback served 화면으로 연결하는 실행 경로 차이**를 명확히 기록하고 지원되는 경로로만 시도한다. 도구가 이 차이를 승인 범위 밖 또는 실행 제한으로 판단하면 해당 작업을 멈춰 정확한 사유를 반환하며 다른 경로로 우회하지 않는다.

### 같은 과업·상태의 측정과 종료 조건

- 1920×1080 CSS viewport 주 기준,1280×900 보조. 앱100%와 앱200%를 구분하고 실제 browser zoom200/400%는 별도 미검증 항목으로 둔다.
- 기본/sequence+captions/precision 펼침, 긴 inspector·장면 목록 상태별로 같은 장면·Take·trim·재생위치·승인을 유지한다. document/client/scrollHeight와 내부 패널 scroll, 실제 contain-fit 영상 크기, 시간축 원점, 주요 조작/focus 가시성을 측정한다.
- 현재 computed background/text/border/font/spacing을 먼저 기록한다. 과거 기본718×404와 상세505×284는 서로 다른 상태의 측정이므로 새 결함이나 개선량으로 사용하지 않는다. 색상 변경·글자 축소·overflow로 강제 은폐·controls 삭제는 하지 않는다.
- 두 폼의 성공/거절/unknown/새 입력/동일 내용 재입력/문맥 왕복을 native 이벤트로 확인한다. 최초 입력과 최종 초안을 함께 남기고 서버 write0을 입증한다. 실제 한글 IME를 수행하지 못하면 not-run으로 남긴다.
- 이미지 저장 후 픽셀을 직접 확인하고 hash/time/URL/version/fixture와 연결한다. 검증 공간과 임시 서버를 종료하고 원본 DB/미디어 불변을 확인한다. 추가 디자인 점수나 고객 사용성 성공률은 만들지 않는다.

## 제한과 인계

현재 남은 것은 이 수정의 실제 브라우저/native IME 확인과 다음 시각 묶음의 최신 served baseline이다. 실행 거절이나 정책 차단이 새로 발생한 것은 아니다. 기존 Impeccable context 엔진 exit127/LSP daemon unavailable/Library prepared-upload 부재는 이번 소스 수정과 오프라인 검증을 막지 않았고 재시도하지 않았다. 이번 모델 API 호출0, 키 조회0, 설치0, 배포0, 업로드0이다.

롤백이 필요하면 [before/index.html](before/index.html)과 [좁은 diff](implementation.patch)를 대조해 이번 변경만 역적용한다. 전체 reset이나 사용자 데이터 복원/삭제는 하지 않는다. 다음 writer도 하나이며 디자인 검토자는 read-only를 유지한다.
