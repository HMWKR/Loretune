## 최종 갱신 — 14:09 KST / 05:09 UTC

이 단락이 아래 중간 체크포인트보다 우선합니다.

- **70/70 회귀 통과(11.530초), 브라우저 QA21건**, Python AST/Node구문검사 통과. 최신 summary/local-cases/automated-tests와 파일해시 기록.
- 서버 **PID88422**, exec session18027,127.0.0.1:8765. provider 비활성. 임시 fake QA서버8771(PID86363)은 종료. QAspace2/p1을 원래 명세QA1305로 복원.
- 생성 취소 UI/worker 연결 완료: 전송전 예약해제(환불 아님), 전송중 취소/접수경쟁 보호, 취소후 도착결과 자동연결 금지. fake 단위검증.
- import_blocked/취소후결과의 수동 기존결과 연결 버튼 추가. 격리 fake브라우저에서 손상출력→보류→수동재시도→새T2 연결, 작업1개/기존T1/예약0.7 유지 검증. 실제 과금 아님.
- **UI 결함 수정:** 생성 상태 polling이 렌더 jobs만보던 문제를 발견·수정. 결과take 연결도 자동새로고침하고 미저장타임라인이있으면 덮어쓰지않음. 생성 상태 한국어 표시.
- 큐 대기중 견적만료 시 외부전송없이예약해제 테스트 추가.
- 실제프로젝트 generation_jobs0, 실제provider호출0. `.env`미조회. 이전단락의 취소/수동재개 미구현 항목은 해소됨.
- 남은 외부 검증: 실제 fal키 주입 승인/변수이름, 모델10초1회/$1상한 확인, 실제수신영상/음악합성/출력QA 및 실제과금근거 대사. 로컬비용 추정치를 실청구로자동정산하지않음. actual-provider MVP는 아직완료아님.
- 후속 전체명세(조직권한/계정/나머지API/자동분석등)는 MVP핵심과분리하여추적. FR067 로컬기능기준충족만유지하며전체배포기준완료0.

# 2026-10-25 원장·Kling 준비 체크포인트

## 검증된 결과

- 전체 격리 회귀 **67/67 통과**(13.423초). `docs/qa/20261025/automated-tests.txt`, `local-cases.json`, `summary.json`. Python AST/JS `node --check` 통과. 이후 UI 상태 문구만 변경했고 정적 검사 통과.
- 브라우저 QA **20건** 기록. 새 범위: 0USD 예산 저장, 다른 클라이언트 수정→412→입력 보존·최신값 비교, 미승인 시작프레임 차단, 준비 저장/채팅·작업대 공유/재시작 보존, T1/T3 비교,390px 넘침 없음, Tab/Escape 포커스 복원.
- 스크린샷 `screenshots/take-comparison.png`, `take-comparison-mobile.png`. 실제이미지 디코딩320px 확인. 긴 해시 넘침 발견·수정.
- FR-067의 로컬 기능 기준6개 충족은 유지. **96FR 전체/143API 전체 완료를 선언하지 않음**. 원장/생성은 부분 기준이며 실제 provider 호출0.

## 변경

- `ledger.py`: 정수 마이크로 금액, 동시 예약, 예산 revision, 미확정 hold, 확정 정산/부분환급, 초과액, 취소 뒤 늦은 비용을 disputed로 기록. 영구삭제/지출 실행 없음.
- `contracts.py`,`app.py`: 원문 budget PATCH/ledger GET/cancel POST, ETag/If-Match412, operation/workspace 멱등키409, 제한 principal403. 기존 read2개+원장read1개+write2개. SSE는 현재snapshot만이며 완전 이벤트 스트림 이력 미지원. 조직 로그인/개별 grant는 미구현.
- `index.html`: 예산·원장과 충돌 비교, Kling 준비, 같은샷 take비교. 생성 준비는 전송 없는 명시 상태. 기본실행버튼 없음.
- `fal_provider.py`: Kling2.6Pro I2V 고정,10초/무음/안전검사, no-retry, 큐receipt URL검증, 결과검증, 제한 다운로드, 비밀조회는 명시runtime활성 이후에만. `.env`를 읽지 않음. 기본 비활성.
- `generation_queue.py`: 예약/요청 원자적 저장, 중복전송 방지, 전송응답 유실/재시작시 재발행 차단, receipt 재조회, 결과미디어 검증 후 새take 추가. 기존 선택/승인 유지. fake transport로만 시험.
- `app.py`: 준비→신뢰runtime gate→admit→worker→결과take 연결. 최대호출/총견적상한 검사. 비용실측 근거 없이 견적을 정산하지 않아 결과가 생겨도 원장은미확정 hold. sourcehash/승인/reference/shotrevision/견적만료 검사.
- 테스트: ledger5, fal5, generationqueue6, contract5 등 총67. 새 테스트들은 실제 외부성공을 의미하지 않음.

## 서버·데이터

- 서버 `127.0.0.1:8765`, PID **83352**, exec session72350. `python3 app.py`, provider_adapter와generation_approval 모두미설정. 재시작 직전 active renders0.
- QA브라우저 space2/p1 유지. 사용자 space0 미조작. 현재 `명세 QA1305` 작품.
- QA작품에만 예산0USD v2, 참고v2 승인, 생성준비1개(전송없음), 비교용빨간T3 추가. 선택T1/이전1080p출력 유지. 기존 손상T2는권리차단 그대로. 영구삭제 없음.
- Git 저장소가아니므로 git diff/status 사용불가. 파일해시/QA산출물로추적. `.env`/`.codex`미조회·미수정.

## MVP 남은 범위 및 실제 차단

최신 실행계획은 `docs/mvp-fal-kling-live-gate.md`. Runway제안은폐기표시.

**외부실행 차단(승인 대기, 거절아님):** 시스템·디자인 최종QA를 먼저완료해야함. 그후 fal.ai Kling `v2.6/pro/image-to-video` 무음10초1회 예상$0.70/제안상한$1/재시도0 범위를확인하고 기존키의 서버주입을승인받아야함. 키값을요청하지않고 환경변수이름만확인. 실제키유효성/잔액/모델품질/과금은미검증. 결제/충전/새키/배포 없음.

**추가 로컬 범위:** 공급자 생성 취소를UI/worker까지 연결(현cancelJob은로컬렌더), 비용확정근거와 대사동작 연결, result import_blocked 재검토/수동재개 UI, 실제runtime gate를명시승인으로안전하게설정하는 실행절차. 현재생성의 prepared→imported happy path와응답유실은fake로끝까지검증됨. LLM자동기획/음악분석/립싱크는MVP에서지원한다고표시하지않음.

실호출1회만으로부분재생성품질까지검증했다고쓰지않음. 전체MVP완료아님. 부모가요청한체크포인트이며독립적인남은로컬작업은계속가능.

## 2026-10-25 최종 로컬 준비 재감사

최신 판정/승인안은 `docs/mvp-live-readiness-reaudit.md`. 6개 로컬 게이트 수정, 자동80/80·실패0, 브라우저25건. 실제.env/키조회·외부이미지전송·모델호출0 유지. 기본서버 PID93882/session3262/8765 모델비활성; fake8771종료, QA space2/p1은8765로복귀. 수정파일 app.py, fal_provider.py, generation_queue.py, index.html, live_launcher.py(신규), tests/test_live_gates.py(신규), tests/test_editing.py, tests/test_fal_provider.py, qa_report.py 및 QA/감사문서. 원본fixture해시변경없음. 실제통합승인 전까지 키를 읽지 말 것. 전체MVP완료 아님; 실제10초 생성→private수신→검토→음원합성 검증이 남음.

## 승인 후 실제 호출 결과

사용자 승인에 따라 Kling10초무음 생성1회 실행. requestID01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d. 약5분40초후 결과준비. 익명GET403, 공식단기토큰교환성공후 인증CDN GET도403(다운로드2회후중단). 공개fallback/추가생성/권한완화없음. job import_blocked, 원장uncertain. 실제영상파일없으므로 최종음악합성미검증. 예상0.70USD/실청구미확인. 기존.env승인된읽기실시, 메모리인증만사용·키/토큰미출력미저장. 실호출프로세스종료, 기본서버는모델미연결유지. 새관련권한증거없이403재시도금지. QA공간2삭제로이번UI검증못함. 보고서 docs/qa/live-kling-20261025/user-report-ko.md 및 result.json. 자동회귀의 real_provider_runs0은그격리suite범위이며실제누적호출1과혼동하지말것.

## human 비교 및 앱 복구 게이트

human의 kling_segment.py를읽기전용대조: private ACL/만료/token없고urlretrieve결과주소직접저장. Klingv3 5/7초·Veo·Seedance의기록연결MP4와ffprobe확인. 같은키/팀인지미조회, 과거URL미보존으로공개인지서명인지단정불가. 결정적차이는명시private경로사용여부. docs/qa/live-kling-20261025/human-comparison-ko.md 및 fal-support-draft.md(미발송).

앱 app.py/index.html: provider완료와import_blocked분리,비밀없는requestID·만료주의표시.401/403의일반재시도차단.서버retrieval_approval(job/id/expires/evidence) 새근거가있을때만동일결과1회재개,사용된근거재사용차단.실제승인근거설정없음/실제회수재시도없음. tests/test_live_gates.py 새회귀포함81/81;AST/JS검사통과.실제브라우저QA는공간2삭제상태라미실행,로컬HTTP상태검증통과.기본서버PID9038/session15737/8765provider비활성.실청구는Aside Dashboard0.70관찰로보고수정,APIbilling/ledger대사별도.403근본권한원인미확정이며지원문의초안만작성,발송0.추가생성0/human수정실행0.
