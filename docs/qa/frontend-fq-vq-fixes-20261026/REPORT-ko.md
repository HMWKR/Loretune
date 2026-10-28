# FQ01–03 / VQ1–2 최소 수정 인계

> **최신 상태 — 2026-10-26 05:05 UTC:** 명시적 추가 승인 후 현재 고정 소스로 HTTP20/20과 격리 실제 브라우저 FQ/VF 검증을 완료했다. 전체349는 비HTTP329+HTTP20의 분할 통과다. 임시 리스너와 TaskSpace36 종료, 소스/공유 QA 프로젝트 불변. [승인 후 검증 보고서](authorized-verification/REPORT-ko.md)에 실제 화면·이벤트·격리·해시·한계를 기록했다. 아래 차단 상태와 준비물 설명은 **추가 승인 전 초기 고정 시점의 역사적 기록**이며 최신 결과로 소급 변경하지 않는다.

2026-10-26. 실제 앱 소스에 수정 적용. **소스/VM·비HTTP 검증과 실제 브라우저·HTTP 검증을 분리한다.** 새 공급자·결제·키·배포·서버 재시작·공유 프로젝트 쓰기는 없다. 원본 독립 감사와 그 blocked/not-run 항목은 보존했다.

## 변경과 검증

|항목|수정|현재 검증|
|---|---|---|
|FQ01 오래된 poll|요청 순번과 마지막 적용 순번, 문맥/refresh/변경 세대, workspace·작품·장면·revision·busy·dirty를 적용 직전에 확인한다. 동시 poll 최대2. 늦은 네트워크가 새 poll 시작만으로 계속 폐기되는 starvation을 피한다. 전역 revision이 같은 jobs/generation/chat/media 변경은 허용한다. refresh 대기 중 새 타임라인·자막 초안도 덮지 않는다.|원래 ASY01/02 통과. 역순·느린 중첩·ABA 전환·mutation/refresh·다른workspace·동일revision 작업 갱신·새 타임라인 초안 회귀 통과.|
|FQ02 native 종료|현재 video/controller/clip에만 유효한 ended 처리. native 종료가 RAF보다 앞서면 무음 컷 경계 또는 최종 정지로 진행. 활성 원곡 clock을 먼저 사용하며 원곡 EOF 뒤 영상 clock으로 전환. 기존50ms 소스 길이 허용 범위만 유지한다.|원래 MED02 통과. 마지막/중간 컷·trim·25ms 부족·수동pause·dispose·장면전환·seek후 늦은ended·음원clock 회귀 통과. 실제 디코더/프레임 오차는 미검증.|
|FQ03 저장소 거부|guarded pending read/clear와 안내. 읽기 불가를 pending 없음으로 처리하지 않고 새 POST를 차단한다. 이미 아는 request ID로 조회만 가능. 확정 rejected/committed를 저장소 정리 실패 때문에 unknown으로 바꾸지 않는다. reconcile의 committed 여부는 실제 응답으로만 판정. Take draft 저장소 property 접근도 기존 try 경계 안으로 지연한다.|원래 STO02 통과. 시작/read/write/remove/IDB 거부·응답유실·중복POST차단·known-ID조회·불명확 상태의 잘못된 committed 방지 통과.|
|VQ1 Take 전체 포커스 가시성|#takes focusin에서 실제 버튼 경계와 strip 경계를 비교하여 해당 strip만 가로 이동. 4px focus 여백. 선택·승인·저장 호출 없음.|보고된 좌표(1280/app200%)를 이용한 계산 회귀 통과. 실제 Tab/Shift+Tab·전체 target 가시성은 브라우저 재검증 BLOCKED. AA2.4.11 위반 판정으로 확대하지 않음.|
|VQ2 긴 장면명|`.lt-scene-copy>b`에 `overflow-wrap:anywhere`를 적용. 글자 크기/전체 이름/원래 한국어 keep-all 유지, 긴 연속 문자열에만 비상 줄바꿈. rail의 기존 내부 스크롤 사용.|전체 문자열 보존·CSS 계약 검사 통과. 실제108px 영역/동일prefix·한글·영문 시각 재검증 BLOCKED.|

소유 코드: `index.html`의 refresh/poll, pending/clear/reconcile, Take focus handler; `studio-media.js` sequence lifecycle; `studio.css` Take focus padding/장면명 wrap. 앱 backend와 정책·권한/선택·승인 엔진은 변경하지 않았다. [패치](implementation.patch), [수정 전 소스](before/), [해시](release-manifest.json).

## 수치의 분모

- 독립 원 suite 13개: **수정 전9PASS/4FAIL → 수정 후13PASS/0FAIL**. 실패4개는 ASY01/02, MED02, STO02. [전](original-before.json), [후](original-after.json), [재실행 wrapper](run-original-counterexamples.cjs).
- wrapper는 원본 감사 파일을 쓰지 않는다. 소스 경로를 현행 파일로 바꾸고, 새 global/helper를 VM에 제공하며 ENV01의 기대 SHA만 대상 버전으로 갱신했다. 반례 입력·assertion은 보존했다. 실제 전달 요청0.
- 새 비동기 집중 **18시나리오 PASS**: [결과](focused-async.json). unittest에서는 이 JS suite를1개 wrapper로 센다. 숫자를 중복 합산하지 않는다.
- 최종 현재 suite 총349개 중 **비HTTP329 PASS**, **HTTP20 BLOCKED**. [최종 로그](final-non-http-regression.log), [제외된 정확한 시험ID](blocked-http-tests.json), [필터 실행기](run-non-http.py). excluded는 pass/skip 성공으로 계산하지 않는다.
- 최초 전체 실행은347개(시각2개 추가 전), errors21. 그중20개는 bind 거부, 1개는 새 helper가 없는 기존 comment-draft VM 대역이었다. 대역을 갱신한 뒤 기존 F05/F06/F07과 전체 비HTTP 회귀가 통과했다. 최초 로그를 덮지 않았다: [전체 시도](full-regression.log).
- 정적 JS **7개 PASS**: inline6 + media module1. [정적 검사](static-check.json). 기존 media lifecycle 및 로컬 renderer/자막/오디오 회귀는 비HTTP suite에 포함된다. 브라우저 실제 재생·serve된 revision의 증거로 쓰지 않는다.
- presentation-only 기간의 전체 media 파일 동일성 테스트는 이번 lifecycle 수정으로 전제가 달라졌다. 이전 라벨/guard 계약을 남기고 기존 media behavior suite와 새 반례로 검증한다. 단순 equality 삭제를 회귀 통과로 대신하지 않았다.

## 실제 실행 차단과 상태

1. 전체 시험의 `127.0.0.1` 임시 HTTP listener 생성이 **PermissionError: Operation not permitted**로 거부됐다. 새 bind/다른 포트/권한확대 재시험 없음. 이후 정확한20개를 제외한 독립 시험만 실행했다. 기존 localhost GET 거부도 재시도하지 않았다. 서버 장애라는 뜻은 아니다.
2. Ego 시작은 sandbox의 macOS 서비스 연결 오류로 실패했다. 정식 실행 권한 심사를 거쳐 **TaskSpace35/about:blank 생성만 성공**했다.
3. 다음 단계인 **로컬 합성 QA 프로젝트1개·로컬 미디어4개와 앱 소스를 TaskSpace35의 격리 페이지로 로드**하는 명령은 자동 승인 심사에서 **“해당 목적지에 대한 민감한 데이터 공개 승인이 없습니다”**라는 이유로 거절됐다. 로드 명령은 실행되지 않았다. 다른 경로/다른 데이터 포장으로 재시도하지 않았다. 빈 TaskSpace35는 정상 종료했다.
4. 따라서 새 실제 화면·수정 후 Tab 가시성·native ended·served hash는 **BLOCKED / NOT VERIFIED**다. 이전 화면을 현행 캡처로 표기하지 않는다. 준비한 `browser-fixture.html`은 로컬 준비물이며 브라우저 실행 결과가 아니다. 그 manifest의 소스 해시는 준비 당시 버전으로, 최종 source manifest와 구별한다.

브라우저 재검증 재개에는 위 **합성 프로젝트/미디어를 검증 브라우저 목적지에 전달하는 범위의 명시적 승인**이 필요하다. 승인 시에도 정식 심사를 따르고 새 유료 호출·실제 사용자 프로젝트 전송으로 확대하지 않는다. localhost listener 시험도 기존 거절 상태를 유지하며 새 관련 허용 근거 없이는 반복하지 않는다.

## 보존·고정

공유 QA DB는 readonly SELECT만 했다. 합성 작품의 정렬 JSON SHA 전후 동일, backend source 불변: [보존 확인](preservation.json). 권리·승인·Take 선택·미디어 파일·기존 출력 수정0. F07/DM01–03의 역사적 독립 검증 보고서는 그대로 두고 이번 추가 회귀와 구분했다.

[최종 release manifest](release-manifest.json)가 현재 소스 기준이다. serve hash/실행 앱 완료판정은 하지 않는다. 새로운 디자인 점수, 전체24개 독립 frontend QA pass, WCAG/실사용자/전체제품 통과를 주장하지 않는다. 원 감사의 BLOCKED6/NOT RUN3은 후속 실제 증거가 없으므로 유지된다.
