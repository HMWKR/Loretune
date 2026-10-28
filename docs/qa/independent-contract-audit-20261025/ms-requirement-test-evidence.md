# SPEC-MS-001 독립 매핑

28 MS-FR / 38 MS-AT. 기존 96 FR·143 API와 별도. 아래 partial은 전체 통과가 아닙니다. 실제 실행 증거는 controls.log 및 counterexamples.json; 코드 위치만 있는 항목은 정적 검토입니다.

| 시험 | 판정 | 근거 | 남은 범위 |
|---|---|---|---|
| MS-AT01 | partial | tests/test_model_selection.py:test_role_independence_preserves_existing_media_and_context | 설정 독립성만 검증; 실제 다음 응답 모델 경로 없음 |
| MS-AT02 | not implemented | model_selection.py:CATALOG | 이미지 어댑터 없음; 자연어 모델 지정→실행 미연결 |
| MS-AT03 | not implemented | production_tools.py:execute | 계획 제안만 local; generation 요청은 LOCAL_TOOL_NOT_CONNECTED |
| MS-AT04 | not fully verified | production_tools.py:execute | 실채팅 응답→외부 무호출 통합 시험 없음 |
| MS-AT05 | partial | tests/test_model_selection.py:test_policy_precedes_execution_no_fallback_or_metadata_activation | 정적 catalog 비활성 확인; 신규 목록 ingest 없음 |
| MS-AT06 | partial | tests/test_model_selection.py:test_policy_precedes_execution_no_fallback_or_metadata_activation | 미활성 실행 차단; 종료/미지원/미확인 능력 조합 미구현 |
| MS-AT07 | partial | tests/test_model_selection.py:test_policy_precedes_execution_no_fallback_or_metadata_activation | 함수 forbidden 검사; 조직 정책 실행 통합 미구현 |
| MS-AT08 | partial | model_selection.py:resolve | 우선순위 구현, explicit만 대조시험; 조직/대화/자동선택 통합 없음 |
| MS-AT09 | not implemented | app.py:Store.state; production_tools.py:validate | 단일 local-owner, 실제 조직 주체 인가 미구현; 임의 필드 차단과 구별 |
| MS-AT10 | partial | ontology.py:apply; production_tools.py:TOOLS | 사람 승인 boolean과 allowlist; 실행 grant 발급/RBAC 없음 |
| MS-AT11 | partial | production_tools.py:execute; tests/test_anthropic_ontology.py | complete 검사와 추출 응답 거부만; 실제 도구 stream 없음 |
| MS-AT12 | partial | production_tools.py:execute | repair 2회 정적 구현; 신규 tool 회귀는 snapshot에 없음 |
| MS-AT13 | not implemented | fal_provider.py:estimate/payload | 고정10초 경로; 7초 사용/편집/끝프레임 계약 없음 |
| MS-AT14 | partial | fal_provider.py:payload | PNG size/signature 검사; 참조개수/비율 모델별 계약 없음 |
| MS-AT15 | partial | tests/test_model_selection.py:test_change_rejects_late_run_without_modifying_job_snapshot | 로컬 run superseded; 실stream/queued job 입력과 grant 불변은 미완료 |
| MS-AT16 | partial | tests/test_model_selection.py:test_wrong_role_unknown_and_stale_are_atomic | 버전 거부 검증; 실제 두 사용자 및 차이UI 없음 |
| MS-AT17 | partial | tests/test_ledger.py:test_concurrent_reservations_never_exceed_limit | 단일 예산 예약 검증; chat/background/parent-child 통합 없음 |
| MS-AT18 | not implemented | model_selection.py; production_tools.py | Claude→Grok 실응답/job handoff 없음 |
| MS-AT19 | partial | tests/test_project_ontology.py; loretune.py:new_song | 프로젝트 스코프/버전 분리; 활동기+곡예외+동명조직 전체 fixture 없음 |
| MS-AT20 | not implemented | tests/test_model_selection.py:test_role_independence_preserves_existing_media_and_context | dummy embedding 딕셔너리 유지; 실제 검색 index/재임베딩 없음 |
| MS-AT21 | not implemented | production_tools.py:execute | dependency action/output-slot 승인 및 자동 결합 없음 |
| MS-AT22 | partial | tests/test_generation_queue.py:test_lost_receipt_holds_reservation_and_never_reissues | DB reopen 보존; 브라우저 SSE replay 전체 없음 |
| MS-AT23 | partial | tests/test_generation_queue.py:test_duplicate_and_parallel_dispatch_submit_once | 기존 request-key 중복 방지; 새 tool call ID로 동일 action replay 계약 미구현 |
| MS-AT24 | partial | generation_queue.py:admit; tests/test_model_selection.py:test_store_persistence_isolation_duplicate_and_unknown_fields | digest mismatch 구현; 새 후보 action 통합 없음 |
| MS-AT25 | partial | tests/test_generation_queue.py:test_lost_receipt_holds_reservation_and_never_reissues | unknown 예약 유지+reopen 재제출 없음; receipt 없는 대사 자동 해결 없음 |
| MS-AT26 | partial | tests/test_anthropic_transport.py; tests/test_fal_provider.py | fake 예외/허용 host 검사; UI/log/export 전체 탐색 미실시 |
| MS-AT27 | partial | tests/test_anthropic_ontology.py; tests/test_fal_provider.py:test_untrusted_receipt_and_result_never_fetch_arbitrary_hosts | strict schema/host; 모든 자료 경로 통합 미실시 |
| MS-AT28 | counterexample | reproduce.py:F04; tests/test_media_roundtrip.py:test_trim_reorder_click_track_unicode_manifest | 정상2초 음원 click/subtitle 통과; 비정수 frame 누적오차 재현, 생성사운드 별도 asset 미구현 |
| MS-AT29 | partial | tests/test_generation_queue.py:test_import_adds_unselected_take_once_and_preserves_existing_approval | 기존 선택/승인 보존; 12샷 모델변경 fixture 미실시 |
| MS-AT30 | partial | fal_provider.py:validate_gate; generation_queue.py:dispatch | 등록 시 해시/가격 확인; action/grant 불변 binding과 제출 전 재검사 부족 |
| MS-AT31 | partial | tests/test_model_selection.py:test_policy_precedes_execution_no_fallback_or_metadata_activation | 자동 대체 비활성; 승인된 대체 실행 없음 |
| MS-AT32 | counterexample | reproduce.py:F02; tests/test_generation_queue.py:test_cancel_during_submit_is_not_lost_and_late_result_is_not_imported | 기본 취소 성공하나 cancel 실패와 완료poll interleaving에서 상태 회귀 |
| MS-AT33 | partial | model_selection.py:resolve; renderer.py | 모든 비활성 실행 거부; 실제 지원종료 변경→기존작품 렌더 조합 미검증 |
| MS-AT34 | counterexample | reproduce.py:F01 | 정상 Store로 자산권리 철회 후 fake submit 1회; 키/BYOK 전환은 미구현 |
| MS-AT35 | partial | tests/test_generation_queue.py:test_poll_does_not_approve_select_or_settle | URL완료와 import/selection/approval 분리; 실제 AI 설명 검출 없음 |
| MS-AT36 | not implemented | model_selection.py:CATALOG | 실12조합 0회; 이미지 0, chat integration_unverified, video integration_blocked |
| MS-AT37 | not implemented | model_selection.py:CATALOG; generation_queue.py:admit | revision_pinning/connection/action/grant/actual route/alias audit 미구현 |
| MS-AT38 | not implemented | anthropic_ontology.py; production_tools.py | Anthropic 추출 transport는 공통 chat tool adapter가 아님; OpenAI/Grok 없음 |
