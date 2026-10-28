# B03·자산 권리·채팅 도구 실행 통합 결과

2026-10-25 11:40 UTC 기준. **원본 통합 완료**, 최종 전체 회귀 **221/221 통과(25.556초)**. 테스트 수는 기능 완성률이나 38 MS-AT 전체 통과율이 아니다. 이번 단계의 실제 외부 Anthropic/Kling 호출·키 조회·추가 비용은 **0**이다.

## 현재 실행 기준

- `http://127.0.0.1:8773`, 소유 exec session **7905**, 기존 격리 QA 데이터 `/tmp/loretune-ms-qa-20261025` 유지.
- API state revision **45**, 기존 5개 QA 작품 보존 + 이번 검증 작품 1개. 진행 중 render/chat 작업이 없는 상태에서 소유 프로세스를 정상 종료·재시작했다.
- `final-runtime.json`이 최종 기준이다. HTML 응답/source SHA256: `25860298244aa518ed322fdc38cb8f9875168fb6c31aa766bc21dc3e2435acd3`.
- 원본 최초 baseline은 `baseline.json`, 원본 수정 전 코드는 `before-integration/`, 적용 가능한 전체 diff는 `functional.patch`, 현재 11개 파일의 before/after 해시는 `patch-manifest.json`에 있다. `patch-files/`와 staging도 최종 통합 코드와 동기화했다.
- 원본 `.env`, `.codex`, 실제 사용자 DB/미디어와 실제 API 비용 원장은 읽거나 복사·변경하지 않았다. baseline에 포함된 비대상 코드/문서 해시는 불변 확인.
- 임시 합성 채팅 서버 52901은 검증 후 종료했다. 데이터는 `contract-ui-runtime.json`의 경로에 보존했다. 이 파일의 mode는 시험 당시 설정이며, 최종 재시작 복원 검사는 provider 연결 없이 수행했다.

## 변경과 근거

| 항목 | 원인 / 변경 | 실제 증거와 범위 |
|---|---|---|
| B03 채팅 변경 후 승인 미디어 실행 차단 | 전체 모델 설정 revision/history가 media 승인 문맥에 포함됐다. 새 action은 `media-v1` 문맥으로 chat 선택/history를 제외하며 image/video 선택·음악·canonical ontology·shot revision은 유지한다. `context_kind` 자체도 action/grant hash에 포함한다. | 기존 반례 재현 `b03-before.log`; `test_b03_chat_only_switch_preserves_execution_not_only_handoff`; 실제 UI에서 승인 후 chat만 미선택으로 바꿔 Take1/collected 확인. |
| 기존 승인 호환 | 기존 `full-v1` action 해시나 grant를 조용히 다시 쓰지 않는다. 기존 엄격 문맥은 유지하며 새 준비/승인으로 신규 계약을 이용한다. | source `model_selection.action_context`, `action_execution.propose` |
| 자산 권리 claim 연결 | `Store.claim_action`에서 현재 프로젝트의 등록 Take/해시/역할·권리 근거·canonical revoke를 조회한다. 모델이 전달한 승인 bool을 신뢰하지 않는다. 의존 결과도 현재 프로젝트의 등록 자산이어야 한다. | `action_assets.validate`, `test_canonical_asset_control_and_rights_revoke`, foreign reference/file tamper/price regression. 실제 외부 provider submit은 이번 경로에 연결되지 않았다. |
| 원본 파일 경계 | store assets 하위 경로/해시명, `O_NOFOLLOW`, 열린 fd의 regular-file/크기/해시를 검사한다. | 정상 fixture claim, 변조 파일 차단 테스트. claim과 미래 외부 네트워크 제출이 하나의 원자적 트랜잭션이라고 주장하지 않는다. |
| 일반 채팅 화면→tool loop | 새 `chat_runtime.py`가 기존 `AnthropicChatAdapter` bounded transports, `chat_protocols`, `Store.production_tool`을 사용한다. queued→count→Messages→tool_result→최종 답변을 DB에 기록한다. 기존 로컬 계획·사람 승인·후보 흐름을 재사용한다. | 실제 전송 대신 계약/fake 및 bounded adapter에 가짜 HTTP transport를 주입한 테스트. UI synthetic fixture에서 context lookup→plan 저장→final reply 확인. **이 UI에서 실제 Claude 호출은 아직 안 했다.** |
| 승인 범위 | 서버에서만 주입하는 workspace/project/context/prompt hash, 만료, 모델, 가격 버전과 최대 회차를 검증한다. 임의 브라우저 prompt·다른 프로젝트·변경된 문맥은 외부 전송 전 차단한다. `.env` 자동 읽기 없음. | `test_unapproved_prompt_foreign_project_and_model_authority_rejected`, stale-after-count, disabled-connection |
| 비용·불명 상태 | 회차별 최대 입력4096/출력4096, reservation2458 microUSD, 최대4회·turn $0.01·누적 $50. 예전 unknown 예약도 포함하고 실제 usage 계산치는 별도로 저장한다. 실제/fake 원장 혼용은 차단한다. | concurrent cumulative cap, prior unknown, fake/live journal 분리, timeout unknown 유지. 공식 가격 재검증·실청구 확인은 이번에 수행하지 않았으며 다음 실제 시험 전 필요하다. |
| 도구 멱등성 | 병렬 tool_use의 결과를 하나의 다음 user/tool_result 메시지로 전달한다. 같은 tool ID 재등장 시 canonical run의 기존 영수증을 재사용해 계획을 중복 생성하지 않는다. | `test_parallel_tool_results_one_message_and_duplicate_tool_idempotence`; plan1 유지 |
| 취소·재시작 | 미전송 취소는 모델 호출0. 호출 이후 취소는 사용량/기존 결과를 유지하고 새 도구 적용을 막는다. 시작된 turn의 프로세스 중단은 unknown으로 보존하며 자동 재호출하지 않는다. | queued cancellation, after-message cancellation, restart unknown, competing workers; UI 재시작 후 완료 답변/계획/Take 보존 |
| 출처 표시 | model-authored / contract-fake 계획과 서버의 균등 시간 배분을 구분한다. 답변은 검토 전이며 미디어 완료/사람 승인이 아니다. chat/video 연결 배지도 분리했다. | UI mode/status/answer_review, plan.source(run/call/model), tool trace |
| F05 | `sendRequest`의 blanket enable이 음악 미확정 계획 승인 조건을 덮었다. 저장 성공·오류 복귀에서 `data-plan-blocked`를 보존하고 새 chat 전송 조건도 재계산한다. | 실제 8773 UI: 음악0·구간미확정 계획 저장 후 승인버튼 disabled; 재시작/새로고침 후 동일 |
| F06 | 검토 의견 초안이 새로고침에 유실됐다. workspace/project별 sessionStorage 저장·복원, 성공 저장 때만 초안 제거. | 실제 1.25초/한국어 의견 초안 복원, DB 저장 후 입력 초기화. 원래 디자이너 패치를 필요한 위치에 통합했다. |
| 추가 UI 결함 | 새 tool trace 컨테이너가 모든 클릭에 다시 그려 disclosure를 즉시 닫았다. 취소 버튼 클릭에만 실행 처리하고 상태 갱신 시 열린 근거를 보존한다. | `test_disclosure_click_does_not_rerender_but_cancel_is_dispatched_once`; 클릭/Enter 펼침 실제 확인 |

## 자동 검증 이력

- 기존 baseline 194 tests.
- staging 첫 전체218: 217 통과, `test_store_export_preserves_last_caption_and_audio_click` 1 error. 이유는 staging 복사에서 합성 PNG/클릭 WAV fixture 누락이었다. 실패 기록 `staging-full-tests.log` 보존.
- synthetic fixture 120byte PNG/384044byte WAV만 보완하고 해시/출처를 `synthetic-fixtures.json`에 기록했다. 실제 사용자 자산은 복사하지 않았다. 해당 미디어 검사 단독 통과.
- staging 전체218/218 통과26.700s → 원본 통합 전체218/218 통과25.562s.
- 추가 budget isolation/concurrency 및 UI disclosure 수정 후 **최종221/221 통과25.556s**, `integrated-final-tests.log`.
- 새 focused tests: B03/권리8, chat18, disclosure1. 기존194 회귀와 합계221.
- `node --check`/Python compile/비대상 baseline 보존 검사 통과, `static-final.json`.
- 전체 회귀에는 실제 FFmpeg 합성 fixture의 trim/reorder·음원·한국어 자막·짧은30컷 끝부분 보존 검사와 기존 권리/원장/HTTP 경계가 포함된다. 실제 모델 생성 품질 검사로 세지 않는다.
- 기존 테스트 일부는 Python3.15의 sqlite ResourceWarning을 출력한다. 실패는0이며 이번 chat tests의 직접 연결은 closing으로 정리했다. 배포 준비 완료를 의미하지 않는다.

## 실제 UI 검증

| 시나리오 | 결과 / 증거 |
|---|---|
| F05 구간 미확정 계획 저장 후 승인 불가 | pass, `F05-model-disconnected.png` |
| 모델 연결 없음 상태에서 전송 불가·로컬 계획 사용 가능 | pass, 같은 screenshot + 최신8773 |
| F06 초안 새로고침 복구·성공 저장 후 초기화 | pass, `F06-comment-saved.png` |
| 모의 연결 표시→합성 요청 접수→서버 context 조회→계획 저장→final answer | pass **contract-fake**, `ui-contract-evidence.json`, `chat-tool-receipt-final.png` |
| 도구 근거와 실제 계획 ID 표시·동일 프로젝트에서 계획 검토 | pass, 계획 `8787664a35944a489ba0eae810e3cf58` |
| 사람 계획 승인→모의 작업 승인→chat만 변경→Take 생성 | pass, job `cbae3313ea1447758926495b379ab3ea`, Take1, `B03-candidate-after-chat-switch.png` |
| 실행 성공과 Take 선택/승인 분리 | pass, 새 Take는 선택 대기이며 기존 선택 자동 교체 없음 |
| 최종 코드 재시작 후 turn/계획/Take 복원 | pass, provider adapter 없이 저장 결과 표시 유지 |
| 키보드 Enter로 근거 disclosure 펼치기 | pass, focus/expanded 실제 확인. 전체 키보드 여정 또는 screenreader 통과로 확대하지 않음 |
| 320/390/1280 CSS px | 가로 overflow0, `responsive.json`, `chat-mobile-320.png`. 실제200/400% zoom 대체 증거 아님 |

UI synthetic turn의 모의 비용 표시는 $0.00021이며 **실제 지출이 아니다**. 실제 총 Anthropic 사용량에는 합산하지 않는다. 이번 추가 실제 비용0. 이전 검증된 실사용 계산치 $0.0049575와 실청구 미확인 상태는 그대로이며 이번에는 실제 원장/키를 조회하지 않았다.

## 남은 범위와 다음 검증

1. 새 일반 채팅 UI→실제 Anthropic API→도구→최종 답변의 소규모 합성 end-to-end는 **not run**. 기존 대표 live script의 성공과 이번 UI/fake 성공은 서로 다른 증거다. 서버 scoped configuration이 필요하며 현재8773은 미연결이다. 다음 실제 시험 전 모델/가격·정확한 합성 입력·context 해시·잔여 원장과 상한을 확인해야 한다. 기존 $50 승인을 재확인 요구로 바꾸지 않으며 범위가 같으면 그 안에서 진행 가능하다.
2. 승인 gate가 고정한 문맥이 바뀌면 실제 연결도 fail-closed된다. 사람의 작업 진행을 임의 승인 범위 확대로 해석하지 않으며 재바인딩은 서버 controller 단계로 남는다. 일반 고객 자료를 자동 전송할 수 있는 production 설정은 없다.
3. 새로운 action controller는 아직 rehearsal media만 실행한다. canonical asset 권리 claim 연결은 구현됐지만 실제 외부 image/video dispatcher와 연결·live 검증이 끝난 것은 아니다. provider 제출 직전 재검사와 정확한 input bytes/receipt 고정은 실제 adapter 통합에서 검증해야 한다.
4. 기존 fal private 결과 수신/단기 토큰403 문제는 그대로 외부 통합 차단이다. 이번에 기존 파일 접근 재시도·추가 생성·ACL/key 변경 없음.
5. 답변의 의미 정확성을 일반적으로 보장하는 grounded-answer validator/품질 평가, 실제 고객 formative test, screenreader 전체 여정과 실제200/400% zoom은 미완료다. 현재 답변을 `unreviewed`로 표시한다.
6. 다중 사용자 인증·클라우드 배포·tenant 운영 격리·12개 모델 조합 live 수용시험은 이 로컬 통합의 범위가 아니다. 기존96FR/143API/38MS-AT 전체 완료나 '영상 API만 남음'으로 판정하지 않는다.

## 실행 제약 기록

처음 비승격 sandbox에서 localhost GET 연결이 `Operation not permitted`로 미실행됐다. 이미 확보한 사용자의 localhost 시험/재시작 승인 범위에서 정식 `require_escalated` 요청이 허용되어 같은 상태 조회·HTTP 시험·서버 재시작이 완료됐다. 우회 경로·방화벽·공개 바인딩 변경은 없으며, 현재 남은 로컬 실행 거절은 없다. 불확실한 작업을 중복 실행하지 않았다.
