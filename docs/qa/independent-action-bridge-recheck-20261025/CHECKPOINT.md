# 재검증 체크포인트

B01/B02 원래 반례 수정 확인. 새 action project_jobs projection을 통해 model_handoff에 id/state/mode가 포함되고, 타 프로젝트는 제외됨. 잘못된 action ID는 structured invalid_arguments2회(retryable true→false), repair_count2/calls2, 이후 RUN_NOT_ACCEPTING_TOOLS, job/예약0.

**B03 Medium 신규 인접 반례:** 정상 Store의 합성 WAV 업로드→music_structure→guided_plan 적용→action_propose→사람 승인→채팅 model_settings만 변경→model_handoff는 같은 prepared job 유지→action_execute를 호출하면 card/job blocked, take null, reservation cancelled. 모델설정 변경 없는 동일 대조군은 collected/take1/settled0 성공. human_flow.py/human-flow-results.json.

원인: rehearsal_workflow.action_execute가 현재 전체 model_selection.snapshot hash로 claim. 승인 snapshot에는 chat settings/history까지 포함되므로 chat-only 변경이 이미 승인된 media context를 무효화. MS-FR09/11, MS-AT15/18: 다음 채팅 선택은 기존 media job을 유지해야 함. 실제 공급자 호출/금전피해는 없음. 해당 문제는 B01의 인계 누락과 달리 인계 후 실행단계 결함.

최소 제안: chat-run context와 승인된 media action context를 분리. 승인 시 media input/model/price/dependency 고정본은 유지하고, claim은 현재 grant/권리/실제 media 의존 변경을 재검사. 전체 freshness 검사를 제거하지 말 것.

새 snapshot/readonly/tempDB만 사용. 독립 bridge16case 통과, 선택 nonHTTP107개 통과. 완료: F/R control 통과, error replay/savepoint2개 통과. REPORT.md 작성. B03만 새 인접 미해결 결함으로 유지.
