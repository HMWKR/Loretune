# 이번 기능 패치 검증 표

전체 명령: staging root에서 `python3 -m unittest discover -s tests -v`. **326tests/43.203초/pass**, 기존311건+이번15건. [원본 로그](full-regression-final.log). 초기 실행은 snapshot에 빠진 기존합성fixture/JS시험파일 때문에 실패했고 필요한 기존파일만 보충한 후 전체를 재실행했다. 실패를 통과 수에 합치지 않았다. Static:110Python AST와inlineJS syntax pass.

새15건은 `tests/test_media_creator.py`에 있으며 실제provider성공시험이 아니다.

| 시험 함수 | 기대/관측 | 종류 |
|---|---|---|
| test_human_hold_reject_reapprove_and_single_reservation | 보류/거절 실행불가, 재승인후 동일action job·reservation1개 | DB+fake pass |
| test_stale_model_cannot_be_reapproved_and_no_fallback | 모델변경 승인재사용거부, 대체모델없음 | DB+fake pass |
| test_unknown_repeated_human_execute_only_returns_existing_job | 불명결과 중복실행은 기존job반환, 새submit없음 | DB+fake pass |
| test_collect_double_click_workers_preserve_original_selection | 동시회수1회, 기존선택보존 | DB/파일+fake pass |
| test_403_new_permission_evidence_only_one_retry | 권한거절은 새관련근거 없으면 차단, 동일gate재사용불가 | fake pass |
| test_local_recovery_error_cannot_erase_prior_permission_denial | 다른로컬오류가 이전401/403해결조건을 삭제하지 않음 | fake pass |
| test_status_query_needs_separate_collection_approval | 기존상태확인과결과회수를 분리 | fake pass |
| test_gate_changes_and_grant_revoke_prevent_collection | enqueue이후gate/승인변경 시 download이전거부 | DB+fake pass |
| test_recovery_restart_no_resubmit_and_legacy_bypasses_blocked | 재시작/legacyAPI로 새권한우회·재생성없음 | DB+fake pass |
| test_cross_project_and_wrong_payload_cannot_gain_authority | 타프로젝트·추가authority인수거부 | DB+fake pass |
| test_model_connection_truth_and_secret_free_projection | 저장모델과연결상태표시,비밀없는응답 | projection pass |
| test_empty_selected_disabled_retired_and_unverified_remain_distinct | 실제미선택과선택미검증/종료/차단구분 | projection pass |
| test_cancel_before_submission_no_fake_network | 미전송취소는submit없음 | DB+fake pass |
| test_test_media_badge_uses_saved_provenance_not_only_reason_text | 저장contract-fake출처가testbadge결정 | 실제JS pass |
| test_actual_ui_markup_actions_model_rights_and_recovery | 실제renderer의허용버튼/상태/escape/사용권표시 | 실제JS pass |

| 실제 브라우저 과업 | 결과 | 증거/한계 |
|---|---|---|
| chat tool→계획→사람적용→image action | pass | canned tool_use/tool_result, 실제DB저장. Claude live 아님 |
| 보류→재승인→실행→다운로드중단 | pass | fake HTTP, 의도한 failure. 외부비용없음 |
| 기존결과수집→Take1등록 | pass | request보존, submit추가없음, 선택자동변경없음 |
| 사용권→시작프레임→video 준비/승인/실행 | pass | 로컬이미지bytes, selected모델, fakevideo |
| Take2수집→사람선택/검토→출력버전승인 | pass | 이전Take1보존, 생성/선택/승인별개 |
| 음악/한국어자막→로컬MP4 | pass |5.000s/1080p/24fps/AAC48kHz/mov_text 및browserWebVTT |
| provider없는서버재시작→재열기 | pass | 선택모델/Take/출력/자막보존, 실행연결미검증표시 |
|390px/1280px 화면 | 표본pass |390수평overflow없음, 실제캡처view_image확인. 디자인90미판정 |
| 다중장면전체브라우저/실제zoom/screenreader/전체keyboard | not run | 이번브라우저는1장면2Take, 자동문맥시험과구분 |
| 실제fal/실제Claude/다른provider/실청구 | not run | 이번외부호출0,기존승인예산소모없음 |

브라우저일부wait는 숨겨진모바일panel/다른성공문구/닫힌details 때문에 timeout됐다. 실제현재상태를읽고이미커밋된작업은반복하지않았다. 새생성중복없음을fake전송기록과DB로확인했다. 테스트함수개수와고객수용기준완료개수를동일시하지않는다.
