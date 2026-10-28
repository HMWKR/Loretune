# 공급자 action 연결 및 구조 디자인 통합 — 고정 체크포인트

2026-10-25. **보강한 영수증의 실제 Claude 재검증, 새 action/grant→기존 fal 큐 연결, 구조 디자인 통합 및 로컬 제작 완주를 완료했다.** 이 문서는 이전 체크포인트의 남은 항목을 갱신한다. 새 유료 영상 호출0, 기존 fal403 재접근0, credential/ACL 변경0.

실제 Claude 결과는 [별도 보고서](../claude-receipt-recheck-20261025/REPORT-ko.md): Messages1회 추가, usage 계산$0.0004961, 누적$0.0077580. 실청구는 미확인. 이후 영상 검증은 실제 어댑터 코드에 **모의 HTTP/CDN과 합성 MP4**를 사용했다.

## 코드 연결

`media_bridge.py`를 추가하고 `app.py`, `action_execution.py`, `generation_queue.py`, `production_tools.py`, `fal_provider.py`, `index.html`을 변경했다. 불필요한 새 worker나 두 번째 공급자 원장을 만들지 않았다.

1. 승인·적용된 guided plan의 샷에서 Kling 준비 → plan ID/version, shot/reference/input hash, 고정 모델·옵션·견적 버전을 가진 immutable provider action.
2. 기존 서버 live gate와 사람의 start_generation 조작 → grant → **기존 GenerationQueue의 예약1건과 job1건**. 작업/action 매핑도 같은 SQLite transaction에서 저장된다. 매핑 중 실패하면 grant/job/reservation을 함께 롤백한다.
3. submit 직전 현재 권리, 파일 hash, 승인 프레임, 샷 문맥, grant/hash/만료/가격/모델을 재검사. 채팅 모델만 바꾸면 미디어 action을 무효화하지 않는다. 실제 미디어 선택·권리·가격이 바뀌면 차단한다.
4. 기존 FalKling submit/status/result/token download/cancel 코드를 사용한다. private lifecycle·기존 허용 host·redirect 거부·크기/MP4 검증·401/403 구분은 유지한다.
5. 검증된 파일의 원자적 저장 후 Take에 action/plan/version/job/request 출처를 연결한다. 선택·승인·실청구 확정은 자동으로 하지 않는다.
6. 채팅 도구는 사람이 이미 접수한 작업을 같은 ID로 조회한다. AI가 grant나 전송 권한을 만들거나 별도 예약·재생성을 실행할 수 없다. 새 provider action이 미접수이면 명확히 blocked다.
7. receipt에 공급자 완료/수신 상태, 로컬 결과 hash, 예약 상태, 견적, 미확정 실제비용을 별도로 노출한다. 토큰/서명 URL/원본 입력은 반환하지 않는다.

현재 actual video adapter는 **Kling2.6 Pro I2V10초·무음**에 한정된다. `model_catalog`를 active로 바꾸지 않았고 정상 서버의 provider는 비활성이다. 연결이 코드에 있다는 것과 실제 제공자 권한이 해결됐다는 것은 다르다. fake transport는 `contract-fake`로 표시한다. 수동 작성된 legacy 샷의 기존 승인 경로도 보존한다.

## 계약 QA

`tests/test_provider_action_bridge.py`: 9개 test methods, 하위 fault 사례 포함. 외부 network0/secret read0. 실제 FalKling class, 실제 SQLite/파일시스템/FFmpeg, 합성10초 MP4. `targeted.log` 및 전체 로그.

| 시나리오 | 실제 관측 / 기대 충족 |
|---|---|
| 미연결·AI 임의 요청 | grant/admission/reservation 생성0, provider 비활성 유지 |
| submit→poll→result→token→download→Take | 올바른 endpoint/private1h/재시도0; Take lineage 일치; 이전 Take 보존 |
| 중복 요청·동시 worker | 동일 job 재사용, submit1회, 예약1건, action_jobs에 모의 job 복제0 |
| 채팅 모델 handoff·타 프로젝트 | 기존 영상 job 조회 유지, 다른 project scope 조회0 |
| grant/rights/media model/price 변경 | 전송 전에 submission_blocked, 미전송 예약 반환, transport0 |
| mapping 저장 예외 | grant/job/reservation/map 모두 rollback |
| submit 응답 유실·복구 | reconciliation_required/uncertain 유지, 새 제출0 |
| token403 / 잘린 MP4 | provider_completed와 import_blocked 구분, Take 추가0, 403 재개 거부 |
| 취소 전/후 | 제출 전 반환; 제출 후 PUT cancel·late result 보존, 실제 비용·환급 미확정 |

첫 전체235tests/28.333s pass. 아래 UI 회귀에서 표시 결함3개를 수정한 후 **최종235tests/28.310s pass** (`full-regression-final.log`). Python AST와 HTML의 JS2블록 node --check pass. F07·B03·기존 F/R 회귀를 포함한다. 테스트 수는 FR/MS-AT 전체 완료율이 아니다.

## 구조 디자인 통합

전담 원본 `../design-benchmark-20261025/structure/REPORT.md`, `TOKENS-AND-STATES.md`, `comparison.html` 및 patch를 검토했다. baseline HTML **7426e52fdb37487dbf7dba35344146a8d13408795aff9aa363334a860f6d5fa3** 일치를 확인하고 적용했다. 원본 디자인·독립 감사 산출물은 수정하지 않았다.

상단 통합, 장면 rail / media / 검토 inspector, 미디어 아래 timeline, 모바일 작업영역 탭을 통합했다. 기존 F07 draft revision guard, 도구·승인 handler와 원래 IDs를 보존했다. 준비 카드에 실제 plan/action/grant 연결 상태를 추가했다.

실제 통합 회귀에서 발견·수정:
- 출력 검토 뒤 step3로 돌아가면 output video와 현재 Take가 함께 노출되어 미디어가 중복됐다. 안내형 step4에서만 output preview를 보이도록 수정.
- 작품 전환 시 직전 작품 output preview가 남을 수 있었다. 표시한 출력의 project를 기록하고 다른 작품에서는 컨테이너를 비운다. 저장된 출력은 보존한다.
- 모바일 검토 패널에서 '렌더 결과 검토'를 누르면 영상은 생성되지만 숨겨진 미리보기 패널로 이동하지 않았다. 해당 버튼은 미리보기 탭을 선택·포커스한다.

후속 브라우저에서 모두 재검증했다. 초기 childElementCount 기반 진단은 CUA read-only DOM scope에서 지원되지 않는 속성이어서 false로 평가됐다. outerHTML/children 배열과 실제 DOM으로 빈 컨테이너를 확인했다. 이를 실제 결함 실패로 집계하지 않는다.

## 통합 화면의 실제 로컬 여정

합성 작품 `구조 통합 최종 QA 20261025`, 격리 저장소 `/tmp/loretune-ms-qa-20261025`.

| 단계 | 실제 결과 |
|---|---|
| 새 작품 저장 | UI 생성, 기존6개 프로젝트 보존 |
| 음원 연결·확정 | 직접 생성한2초440Hz WAV 업로드, 원본 보존, 실제파형,0–2초 확정 |
| 계획 저장·검토 | 입력 문구 보존, plan v1; 비용 승인과 별개로 샷 추가 |
| 실행 승인 | $0 모의임을 명시한 카드, approval 후 prepared; 실행 별도 |
| 후보 실행·검토·선택 | 로컬 단색 PNG/Take1; 후보검토 후 선택; 실제 AI 아님 |
| 음악·자막 편집 | 2초,1920×1080,음원v1,한국어 자막0–2초, timelinev1 저장·승인 |
| export | 고정 입력 확인 dialog 후 local render; completed, video/audio/subtitle3트랙 |
| 결과 재생·재개 | browser readyState4/2초/1920×1080/error없음; 새로고침 후 저장버전·승인·자막·완료파일 복원 |
| 작품 전환 | 다른 작품에서 이전 preview 비움, 원 작품 재선택 후 저장된 출력 재열기 가능 |
| responsive·keyboard | 1280/390/320 가로넘침0, mobile Arrow/Home 탭 이동, model dialog Escape와 opener focus 복귀 |

새로고침하면 제작 단계는1로 돌아가지만 저장 데이터는 복원된다. 작업 단계의 위치까지 자동 복원한다고 주장하지 않는다.

Render ID `b6cd2217ff114a23822809db63ac4880`, plan `20e1f8366c804ebda57ba220c0bff1bf`, action `a3d4e21409ae4521b07560bd9a2f3c4f`. 실제 출력 [MP4](ui/integrated-output.mp4), [SRT](ui/integrated-output.srt), [manifest](ui/integrated-output.json), [측정](ui/output-verification.json).

MP4 hash `542040801770d77ecd6d11653b010e6779c94b9265298155e10b947ae2819645`. duration2.0s/24fps/1920×1080/48kHz. decoded AAC와 원본440Hz 음원의 상관0.999792, 실제 SRT Unicode 및 끝2초 확인. 오디오는 파일 디코딩으로 검증했으며 사람의 청취 시험을 수행했다고 주장하지 않는다. 사각형 영상의 검정 여백은 contain 정책이며 누락/검정 프레임으로 오인하지 않는다.

[완료 desktop](ui/integrated-output-1280.png), [390px](ui/integrated-scenes-390.png), [320px](ui/integrated-scenes-320.png). 실제 desktop1280×900에서 workspace top141px, 결과 video bottom605px, timeline controls top694px. 정밀편집을 펼친 전체 timeline은1329px까지 이어진다. 후보의 previewbottom542px를 이번 완료 화면의 측정치로 전용하지 않는다.

## 고정 런타임

- **http://127.0.0.1:8773**, exec82301, revision59. 기존 서버88376은 Ctrl-C 종료130 확인 후 정상 승인 경로로 재시작했다.
- 최종 HTML/source/served **be3ff1634a396e378d320cb32020f94a9332e643d2128b5c92209af312ababf5**.
- 백엔드는 이번 bridge 버전으로 로드. 후속 HTML 표시 수정은 매 GET 파일을 읽는 서버에 즉시 반영 후 reload·served hash 확인.
- source freeze. `fixed-runtime.json`에 모든 제품 파일 hash. 이후 docs/증거만 추가한다.
- real provider/key 연결0. 실제 Claude 시험 readback65338은 이전 백엔드 checkpoint이며 이번 새 bridge/UI 통합 수용 서버는8773이다.

## 남은 필수 통합·운영 경계

**좁은 단일 사용자 경로**(업로드 PNG + 승인 계획 + pinned Kling10초 + 로컬 음악/자막 출력)의 큐·worker·저장 연결은 더 이상 별개 미구현 경로가 아니다. 실제 adapter fake-contract로 연결됐다. 그러나 **전체 MVP에서 영상 API만 남았다고 단정하지 않는다.**

1. **외부 gate:** fal 실제결과 정상 인증다운로드→저장→등록. 과거 CDN403과 최신 token 발급403은 다른 단계. 원인 미확정; 이번 bridge가 이를 해결한 것은 아니다. 새 호출/거절 재시도 없음. 실제 성공 검증과 비용 확인이 필요하다.
2. **미구현 코드/선택 범위:** 실제 이미지 생성 어댑터/모델 없음. SyntheticImageAdapter는 모의이며, 이미지 업로드 경로가 현재 대안이다. 다양한 image/video 모델의 typed options·cancel/cost·capability 검증과 MS명세12live조합은 미완료·미승인. 임의 모델 활성화 안 함.
3. **실제 통합 미검증:** 일반 사용자 자료의 Anthropic consent/configuration/품질. 현재 실제 증거는 승인된 synthetic workspace 및 고정 server gate다. 이 성공으로 모든 프로젝트의 자동 외부 전송을 활성화하지 않았다.
4. **비용 운영 코드:** 예약/불명/정산/환급은 구현·fixture검증됐으나 실제 billing webhook/reader 자동대사는 연결되지 않았다. result success만으로 견적을 실제청구로 정산하지 않는다.
5. **출시 운영:** local-single-user이며 로그인/조직별 실제 tenant 인증·클라우드배포·장시간/다중worker 운영부하 검증은 미완료. scope fixture test와 실제 다중사용자 보안은 구분한다.
6. **QA 미검증:** 실제 browser200/400%zoom, screenreader, keyboard-only전체여정, 실제 고객사용성. 이번 mobile viewport 및 일부 keyboard 확인을 AA전체준수로 확장하지 않는다.

96FR/143API는 전체제품, SPEC-MS-001은 확장명세다. 이번 증거는 plan/action/grant/명시적 승인/중복비용방지/출력수신분리/모델handoff/로컬출력 기준을 보강한다. 모든 FR나 MS-AT가 pass라는 선언은 하지 않는다. 다음 독립 디자인 감사는 이 고정 버전을 대상으로 할 수 있다.
