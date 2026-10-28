# 운영 장애 시나리오 코드 검증 · 2026-10-25

판정: 로컬 수신·복구 결함을 수정하고 전체91개 테스트를 통과했다. **실제 fal private CDN 403은 해결됐다고 판정하지 않는다. 배포 준비 완료도 아니다.** 실제 키 조회·모델 호출·실제 CDN 재시도·ACL 변경은 이번 검증에서0회다.

## 발견 및 수정

- `generation_queue.py:106`: 동시 작업자가 같은 결과를2회 다운로드하던 결함. SQLite BEGIN IMMEDIATE로 downloading/claim을 먼저 저장하고 파일 및 DB 반영 전에 소유권을 다시 검사한다. 재시작은 기존 request를 보존한 import_blocked로 복원한다(`recover:78`).
- `app.py:136`: 길이 검증 전에 파일을 공개 assets에 옮기던 결함. staging에서 요청길이10초±0.2초와 FFmpeg 전체 영상 decode를 확인한 뒤 원자 rename한다. worker는 다운로드/검증 실패를 로컬 수신 차단으로 구분한다(`app.py:582`).
- `fal_provider.py:149`: CDN401은 단기 인증 토큰을 한 번만 갱신한다. 403은 권한 차단으로 유지하고 재시도·공개 fallback하지 않는다. 잘린 HTTP body도 비민감 오류로 처리한다. HTTP 오류 응답을 닫는다.
- `index.html:88`: provider 성공을 앱 완료로 표시하지 않고 수신/검증 중 상태를 구분한다. 실제 브라우저에서 과거 비용까지0으로 읽힐 수 있던 채팅 문구도 로컬 초안에만 한정했다(`index.html:9`).

수정 전 유효한7개 새 테스트에서 실패2개와 오류1개를 재현했다(`baseline.txt`). 수정 후 신규10개 통과(`targeted-after.txt`), 최종 전체91개 통과(`full-regression.txt`). 최초 최종 실행은 샌드박스의 localhost bind 제한으로16개 error였으며 제품 실패로 은폐하지 않았다(`sandbox-bind-failure.txt`). 승인된 loopback 실행 범위로 다시 실행해 통과했다. Python AST 및 JavaScript node --check도 통과했다. 최종 QA 원문 기준 매핑은 ../20261025/local-cases.json에 기록한다. 테스트 관련성 매핑은 FR 전체 완료를 의미하지 않는다.

## 시나리오별 결과

모든 자동 시나리오는 임시 디렉터리·SQLite·synthetic 인증값·loopback HTTP fixture만 사용한다. 아래 evidence의 테스트 코드에 입력과 단계 및 assert가 있으며 full-regression.txt에 실제 결과가 있다. timeout은 실제 장시간 대기가 아닌 주입된 transport exception이다.

| ID | 기대 및 실제 확인 범위 | 상태 | 증거 |
|---|---|---|---|
| P01 | HTTP 정상 다운로드; Key는 token endpoint에만, Bearer는 CDN에만 | pass | test_http_success_credentials_separated |
| P02 | 401 한 번 token 갱신, 반복401 최대2회 GET;403 갱신·우회 없음 | pass | test_http_401_refreshes_once_but_never_403 / test_repeated401_and_timeout_are_bounded |
| P03 | 403/404/410/429/500/503/302 오류 분류; 자동 재시도·redirect 없음 | pass | test_http_faults_never_retry_permission_or_transient_automatically |
| P04 | 잘린 body·MIME·크기·MP4 signature 거절 | pass | test_http_truncated_or_wrong_type_rejected / test_live_gates.test_download_size_type_truncation_and_signature_boundaries |
| P05 | HTTP/타호스트/userinfo/비표준포트는 소켓 전 거절 | pass | test_disallowed_origins_never_open_socket |
| P06 | 동시 수신2회 중 실제 download1회; 새 프로세스에서 기존job import_blocked 복원 | pass | test_concurrent_result_claim_downloads_once_and_restart_does_not_reissue |
| P07 | 1초 영상을10초 결과로 등록 금지; 검증 실패 시 assets 없음 | pass | test_wrong_duration_is_not_published |
| P08 | 파일 원자 이동 실패 후 staging/asset 없음 | pass | test_atomic_publish_failure_cleans_staging |
| P09 | DB commit fault 후 Take/imported 없음; 같은request 복구 후 Take1회 추가 | pass | test_db_rollback_never_marks_imported_and_same_request_recovers |
| P10 | timeout 오류 비밀값 삭제·반복 없음 (transport fault injection) | pass | test_repeated401_and_timeout_are_bounded |
| P11 | 중복 enqueue/응답 유실: reservation 유지·새 생성 금지 | pass | test_generation_queue.test_duplicate_and_parallel_dispatch_submit_once / test_lost_receipt_holds_reservation_and_never_reissues |
| P12 | 승인·선택 보존, 중복결과 Take1회, 취소 도착 결과 자동import 금지 | pass | test_generation_queue.test_import_adds_unselected_take_once_and_preserves_existing_approval / test_cancel_during_submit_is_not_lost_and_late_result_is_not_imported |
| P13 | 권한 없는 legacy 쓰기/타workspace job/잘못된 프로젝트 회수 거절 | pass | test_contracts.test_scoped_principal_cannot_bypass_write_grant_via_legacy / test_job_contract_auth_foreign_workspace_and_state_revision / test_live_gates.test_permission_block_requires_new_server_evidence_once_and_redacts_urls |
| P14 | 원장 예약/미확정/정산/환급 멱등성; 초과 확인 시 새 예약 중지 | pass | tests/test_ledger.py |
| P15 | 실제 UI: provider 완료와 로컬 차단 구분, requestID·만료 안내,403 재시도 버튼 없음; 채팅/작업대 동일 작품 | pass | ui-final.txt / ui-final.png |
| P16 | 실제 private CDN 결과 수신→최종 음악/자막영상 | blocked | live403 원인 미확정; 추가 실제 요청 없음 |
| P17 | 다중 서버 lease/SSO·실사용자 tenant auth/원격TLS/실클라우드 부하 | not implemented | 현재 localhost 단일 사용자 MVP 범위 |
| P18 | 전원 차단 fsync 내구성·장시간/메모리 부하 | not run | 원자 rename과 DB rollback만 검증; cross-resource atomic 아님 |

## 실제 화면 및 서버

IAB 별도 검증 탭에서 Kling 승인 실검증 20261025 작품을 읽기 전용으로 확인했다. 채팅/작업대 전환 후 같은 작품·샷·requestID를 유지한다. 기존 Take1은 입력 이미지이며 새 AI 영상이 아니다. provider 완료/로컬 차단/비용 미확정, 정확한 파일 삭제시각 미확인 안내가 있고 권한 해결 근거 없는 재시도 버튼은 없다. 채팅의 비용0 오해 문구를 수정한 뒤 reload로 확인했다. 새 생성·실제 다운로드·사용자 자료 수정은 하지 않았다. 서버 PID11039,127.0.0.1:8765, provider disabled로 유지한다. 새 UI 증거는 ui-final.txt/png. 이번 검증은 모바일 전체 재검증이나 기존25건 UI QA의 재수행을 의미하지 않는다.

## 403 원인과 정상 해결 조건

공식 private-to-owner 정책 default forbid/rules[] 자체는 올바른 지원 경로다. human의 ACL 미지정 흐름과 별도 경로이며 공개 fallback은 근본 해결이 아니다. 기존 실제 요청은 provider 완료, token 교환 성공 뒤 CDN403으로 파일 body 이전에 차단됐다. Asset/Take 저장까지 진행되지 않았다. Dashboard 관찰 비용은USD0.70이나 자동 원장 대사는 아직 미완료다.

[ACL GET](https://fal.ai/docs/platform-apis/v1/storage/files/acl/get)은 assets:read를 요구하므로 생성 성공만으로 해당 권한을 입증할 수 없다. [팀 문서](https://fal.ai/docs/documentation/setting-up/teams)상 개인/팀 귀속도 다르다. [공식 ACL 계약](https://fal.ai/docs/documentation/model-apis/file-access-controls)과 [toolkit](https://github.com/fal-ai/fal/blob/main/projects/fal/src/fal/toolkit/file/providers/fal.py)은 caller token/requestID 전달을 설명하지만 Kling 배포가 실제로 어떤 소유자로 업로드했는지는 미확인이다. Sign API는 권한 우회책이 아니다. 계정 설정 API도 존재하므로 지원문의만 유일한 해결이라고 단정하지 않는다.

다음 정상 확인은 key의 비밀값이 아니라 승인된 계정/팀 식별과 요청·출력 asset 소유자 및 assets:read 권한의 일치 여부다. provider 측 전달/귀속 문제라면 requestID와 비민감 증거로 지원 확인이 필요하다. 지원문의 초안은 ../live-kling-20261025/fal-support-draft.md이며 발송하지 않았다. 새로운 관련 권한 근거 없이는 거절된 요청을 반복하지 않는다. 만료 결과는 복구 가능하다고 보장하지 않는다.

## 배포 전 남은 사항

현재 단일 localhost 사용자 신뢰 경계다. API principal 격리 테스트는 실제 로그인/조직 인증 완료를 의미하지 않는다. 다중 서버에서 startup recovery가 다른 worker의 claim을 회수하지 않도록 lease와 소유자 heartbeat를 추가해야 하며, 원격 배포 전에 인증·TLS·tenant별 파일 접근·권한 감사가 필요하다.

파일 rename과 SQLite commit은 하나의 원자 트랜잭션이 아니다. commit 실패 시 검증된 미참조 해시 파일은 남을 수 있으나 Take/완료 상태는 rollback된다. 같은request 복구가 파일을 재사용하는 것을 검증했으며 기존 사용자 파일을 삭제하는 정리는 하지 않았다. fsync/전원 차단, 고아 파일 정책, 동시128MiB 수신 메모리/부하, 다중호스트 테스트는 남아 있다. 이 항목을 해소하지 않은 상태를 production-ready라 부르지 않는다.
