# 독립 감사 반례 수정 및 재검증

현재 소스에서 F01–F04를 모두 다시 재현한 뒤 수정했다. 독립 감사 원본 디렉터리는 수정하지 않았다. `source-comparison.json`은 감사 스냅샷/수정 전 현재 코드 해시를 비교한다. 수정 전·후 실행은 실제 네트워크 연결을 금지한 별도 Python 프로세스와 synthetic fixture만 사용한다.

| 반례 | 수정 전 | 수정 후 실제 관측 | 관련 코드/증거 |
|---|---|---|---|
| F01 권리 철회 후 제출 | fake submit 1, accepted | fake submit 0, submission_blocked, 미전송 예약 해제 | app.py validate_generation_submission/start_generation/process_generation, generation_queue.py dispatch; test_submission_authority |
| F02 취소 timeout/완료 poll 경합 | cancel_sent/result null로 회귀 | cancelled_result 및 result 보존, 취소 응답 오류만 갱신 | generation_queue.py send_cancel; test_cancel_timeout_race_preserves_latest_result |
| F03 관계 변경 누락 | impact 빈 목록 | 관계 변경 영향 1건, 과거 관계/의존 개체 보존 | project_ontology.py bind/impact; test_relation_dependencies_are_frozen_and_unrelated_edges_do_not_stale |
| F04 소수 컷 누적 오차 | 요청3.900초→3.750초, 검증 실패 | 3.916667초, 검증 성공 | editing.py frame_timing/render_project/preflight, renderer.py render/verify_output; test_frame_timing |

## 제출 권한과 경합의 정확한 범위

등록 시 서버 승인 전체 fingerprint, 당시 adapter identity, 준비 입력 snapshot을 고정한다. prepared→submitting 전이의 SQLite BEGIN IMMEDIATE 안에서 현재 gate/만료/adapter/작품·샷/참고 승인/자산 권리/원본 파일 해시/정확한 provider payload를 재검사한다. live_enabled transport에 binding이 없으면 직접 dispatch도 차단한다. 이전 prepared job에는 binding을 임의 보충하지 않으며 새 승인 재검토가 필요하다. 브라우저 state에서 내부 submission_binding은 제외한다.

정상 대조는 submit1/예약 유지, 권리 철회·gate 교체·gate 철회·adapter 교체·파일 변경은 각각 submit0/예약 해제다. 기존 ledger의 release 결과 상태 이름은 cancelled이며 환불을 뜻하지 않는다. 제출 뒤 권리 철회에는 기존 예약을 자동 해제하지 않았고 추가 제출도 없었다.

선형화 경계는 제출 권한을 검사하고 submitting을 commit한 시점이다. 그 이후 철회는 이미 제출 시작된 작업으로 처리해야 하며 원격 전송 취소를 보장할 수 없다. SQL lock을 네트워크 응답 동안 유지하지 않는다. 이 수정은 범용 연결 rotation/grant 서비스 또는 분산 worker lease 완성을 뜻하지 않는다. 순수 queue 단위 시험의 비-live fake adapter는 기존 테스트용 경로를 유지하지만 Store worker 및 live_enabled 전송에는 검증이 강제된다.

F02는 감사와 같은 결정적 함수 interleaving이다. 현재 단일 worker UI에서 실제 도달했다고 주장하지 않는다. timeout 예외 처리에서 최신 row를 다시 읽어 완료 결과를 덮지 않도록 했다.

## 온톨로지 관계 범위

직접 바인딩한 개체에서 나가는 관계와 해당 target 개체를 snapshot에 보존한다. 관계 target/provenance 변경, 의존 개체 내용 변경을 비교하고 무관한 개체에서 나가는 관계 변경은 해당 샷에 영향을 주지 않는다. 과거 관계 snapshot 없는 연결은 확인 필요 안내를 표시하며 과거 문맥을 최신 관계로 몰래 채우지 않는다. 범용 전이적 관계 추론 전체가 검증된 것은 아니다.

## 시간 기준과 미디어

24fps에서 **전체 누적 경계**를 nearest/half-up 정수 frame으로 변환한다. 각 경계와 요청 시각의 차이는 최대1/48초이며, 컷별 반올림을 누적하지 않는다. 각 part는 정확한 frame 수로 인코딩한다. 실제 frame 계획은 snapshot과 verified manifest에 기록하고 preflight는 요청/출력 길이 및 오차 정책을 표시한다. 오디오·자막은 원래 절대 시간을 보존한다. 검증 tolerance 확대 대신 video 시간 검사를 2ms, container 차이를 1frame 이내로 제한했다.

`media/fractional-30cuts-audio-caption.mp4`: 합성 파란 화면30컷, 합성440Hz음원, 한국어자막. 요청3.900초, 실제3.916667초,640×360,24fps,48kHz,video/audio/subtitle3트랙. 추출 자막의3.880초 종료시각·Unicode 보존 확인. 실제 AI 출력이 아니다. 기존 2초 trim/reorder/click-track/한국어자막 회귀도 통과했다.

과거 acceptance_report.py의 FR-067 전체 기능 완료 표현을 특정 fixture 부분검증으로 좁혔다. 생성기를 실행해 과거 산출물을 덮어쓰지는 않았다.

## 검증과 남은 제한

- `before.log`, `counterexamples-before.json`: 현재 코드에서 네 반례 재현.
- `after.log`, `counterexamples-after.json`: 수정 뒤 네 반례 기대값 충족.
- `regression-non-http.log`: **137개 통과, 실패0**. 전체 발견154개 중 HTTP listener 필요17개 제외(`http-excluded.json`). 감사의 거절된127.0.0.1:0 bind를 다시 실행하거나 에스컬레이션하지 않았다. 따라서 전체154개 통과라고 하지 않는다.
- Python compile 및 index JavaScript syntax 통과. `final-code-hashes.json` 참조.
- 공용8765/기존8772/전용8773 서버는 이번 수정 턴에 재시작하지 않았다. 실행 중 서버는 수정 백엔드를 아직 로드하지 않았으므로 현재 앱 UI에서 새 차단/시간 정책 전체 경로 재검증은 남아 있다. index 정적 문구 변경은 파일 재읽기 시 반영된다.
- 실제 provider 호출/키조회/추가 지출0. fal 실제403의 원인 및 회수는 이 수정으로 해결했다고 주장하지 않는다. Anthropic 실호출 승인 대기와 다중 모델 미구현 범위도 유지된다.
