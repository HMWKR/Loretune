# B03·권리 연결·F05/F06 독립 재검증

**B03과 새 자산 권리 claim 연결은 고정한 스냅샷에서 통과했다. 신규 F07 한 건은 재현됐다: 의견 저장을 기다리는 동안 쓴 새 초안이 이전 요청의 성공 처리로 삭제된다.** F05/F06의 원래 사례는 통과했다. 실제 브라우저·HTTP·외부 공급자는 이번 감사에서 실행하지 않았다.

검사 대상은 **2026-10-25 11:47:52.431523 UTC** 스냅샷이다. 기능 세션 `final-runtime.json`의 11개 대상 SHA256과 모두 일치한다. 아래 수치는 서로 중복되는 계약을 포함하므로 합산 완성률로 계산하지 않는다.

| 검사 | 독립 실행 결과 | 증거 |
|---|---:|---|
| B03 이전 정상 Store 재현 및 무변경 대조 | 2/2 통과 | `human_flow.py`, `human-flow-results.json` |
| 신규 media-v1/권리/자산/의존 결과 경계 | 26/26 통과 | `next_contracts.py`, `next-contract-results.json` |
| 기존 B01/B02·hash·예산·중복·unknown bridge | 16/16 통과 | `recheck.py`, `audit-results.json` |
| replay·transaction rollback | 2/2 통과 | `error_guards.py`, `error-guard-results.json` |
| F05/F06 코드 실행 및 인접 비동기 사례 | 11 통과, **1 실패(F07)** | `ui_controls.js`, `ui-results.json` |
| 선택한 비HTTP 회귀 | 134/134 통과, 오류0 | `run_controls.py`, `controls.log` |
| F01–F04 원래 반례 | 4/4 통과 | `control_recheck_original.py`, `after-evidence.json` |
| R01/R02·관계 이력·시간 경계 인접 사례 | 16/16 통과 | `control_adjacent.py`, `adjacent-results.json` |
| quota/자막/오디오 거부 대조 검사 | 12/12 통과 | `control_guards.py`, `guard-results.json` |
| 문법 검사 | Python AST70개, JS node --check 통과 | `environment-static.json` |

## F07 — Medium: 저장 중 추가 작성한 의견 초안 삭제

현재 제품 소스의 JavaScript를 그대로 추출해 **Node VM + 합성 DOM + 지연된 fake fetch**로 재현했다. 사용자의 브라우저나 서버는 조작하지 않았다. 호출한 함수는 실제 `comment.onsubmit`, `act`, `sendRequest`, `pendingId`, `clearPending`, 초안 input listener 및 복원 함수다. 동작을 새로 구현한 모형으로 대체하지 않았다.

재현:

1. project A에 `at=1.25`, `text=first submitted draft`를 입력하고 저장한다.
2. fake fetch 응답을 보류한다. 실제 `sendRequest`는 버튼만 disable하며 의견 입력칸은 편집 가능하다.
3. 같은 입력칸에 `at=2.5`, `text=second unsent draft while save pending`을 입력한다. 원래 input listener가 이를 같은 sessionStorage key에 저장한다.
4. 첫 요청을 성공으로 완료한다. 화면 갱신은 같은 프로젝트 초안 복원을 호출한다.
5. 첫 요청의 submit handler가 해당 key를 무조건 제거하고 `form.reset()`한다.

| 항목 | 기대 | 실제 |
|---|---|---|
| 서버로 보낸 payload | 첫 의견만 전송 | 첫 의견만 전송 |
| 아직 보내지 않은 두 번째 의견 | 입력 및 저장소에 보존 | **입력 빈 문자열, 저장소 빈 배열** |
| 새로고침 복원 | 두 번째 초안 복원 | 복원할 저장 항목 없음 |

**영향:** 응답 지연 중 편집한 검토 의견을 잃는다. 이미 저장된 첫 의견의 서버 데이터 손실이나 미디어 승인 우회는 아니다. 실제 브라우저에서 발생 빈도/사용성까지 검증한 결과는 아니다.

**원인/파일행:** `snapshot/index.html:201`은 모든 새 input을 저장한다. `:214`는 버튼만 잠근다. `:254`의 `$('#comment').onsubmit`은 제출한 초안과 현재 초안을 비교하지 않고 성공 시 removeItem/reset한다. `:200`은 같은 scope에서 복원을 생략하므로 이 손실을 막지 못한다. 원본 HTML은 종료 시점에도 같은 hash였다.

**최소 수정 제안:** 제출 시 scope와 초안 값 또는 draft revision을 고정한다. 성공 후 저장소 내용이 그 제출본일 때만 제거하고, 현재 scope 및 form 값도 제출본과 일치할 때만 reset한다. 이후 입력은 그대로 둔다. 프로젝트 전환 중 응답, 성공 중 새 입력, 실패 중 새 입력을 각각 회귀로 두면 된다. 제품 소스 수정은 하지 않았다.

**요구사항 연결:** 직접 대상은 이번 F06의 ‘초안 보존/성공한 제출본만 정리’ 계약이다. 기존 FR-060의 미저장 상태 구분·손실 방지 원칙과 FR-062 검토 의견 기능에 관련된다. 새 MS-AT에는 이 의견 초안 경합을 직접 명시한 번호가 없으며 MS-AT 전체 실패로 확대하지 않는다. 기존 AT-060-A/B 전체 동시 편집 시험을 대체하는 증거도 아니다.

단독 재현: `node docs/qa/independent-next-functional-recheck-20261025/ui_controls.js`. 결과 파일의 마지막 case `F06-adjacent-pending-save-must-preserve-new-edit`가 fail이다. JS 실행 자체는 정상 완료하며 검사 상태는 JSON으로 구분한다. 초기 발견은 `CHECKPOINT.md`에 먼저 기록했다.

## B03 — 수정 수용

이전 감사의 `human_flow.py`를 변경하지 않고 새 snapshot으로 실행했다. 합성 WAV 업로드 → 음악 구간 확정 → 계획 적용 → action 준비/사람 승인 → chat 모델만 변경 → handoff → 기존 card 실행 경로다. 임의 DB 상태 주입이 없는 정상 Store mutation 재현이다.

| 상태 | 이전 B03 | 새 B03 |
|---|---|---|
| job handoff | 같은 prepared job | 같은 prepared job |
| 실행 결과 | blocked, take=null | **collected, take=1** |
| 예약 | cancelled, actual=null | settled, actual=0 |
| 다른 프로젝트 handoff | 없음 | 없음 |
| 공식 canon | 빈 상태 유지 | 빈 상태 유지 |

이전 보고서/재현 결과/manifest는 `before/`에 별도로 보존했다. 무변경 대조도 새 snapshot에서 collected였다.

소스 근거: `model_selection.py:61–74`의 `media-v1`이 chat 선택/history를 제외하고 image/video 선택 및 canonical 음악·설정·샷 문맥을 유지한다. `rehearsal_workflow.py:21–26`에서 새 action에 이 계약을 저장하며 `:61`에서 Store claim으로 연결한다. `action_execution.py:49–51`의 hash에 context_kind도 포함된다. 기존 full-v1 승인본은 재작성하지 않으며 이전 strict control이 계속 통과한다.

독립 추가 검사에서 chat-only 변경은 media hash 불변/claimed였다. video 기본값 변경과 selected take 변경은 hash가 바뀌어 blocked였다. 저장된 job의 input/model/options/context_kind 및 grant 금액 변조도 blocked였다. 후자는 합성 DB의 무결성 검증용 변조 대조이며 사용자가 정상 UI로 해당 DB 필드를 직접 변경할 수 있다는 주장과 구별한다.

관련: MS-FR-09/11, MS-AT15/18의 **로컬 승인·인계·불변성 부분**. Claude→Grok 실제 모델 전환이나 외부 영상 완료까지 통과했다는 뜻은 아니다.

## 자산 권리 claim 연결 — 검사한 범위 수용

`app.py:537–545`는 현재 프로젝트를 기준으로 `action_assets.validate`를 수행한 뒤 claim한다. `action_assets.py:13–34`는 exact reference schema, Take/해시/역할 소유, 권리 근거, canonical revoke, 자산 경로·symlink·열린 fd·파일 해시를 검사한다. `action_execution.py:104–117`이 미전송 prepared job에 대해서만 실패 예약을 반환한다.

독립26개 사례는 다음을 확인했다.

- 정상 자산/채팅 변경: claimed, 예약 reserved. fake provider도 이 claim 시험에서는 호출하지 않았다.
- **실제 project B에만 등록한 서로 다른 PNG**를 A와 같은 shot 이름·take 번호로 참조: blocked. 단지 존재하지 않는 shot 이름을 넣은 시험에 그치지 않는다.
- 이미 예약한 뒤 권리 철회, missing rights, ref에 rights_valid=true 삽입: blocked/cancelled.
- 등록 해시 불일치, 원본 bytes 교체, 원본 삭제, symlink 대체: blocked/cancelled.
- 가격 revision 변경, grant 철회, frozen action/grant 변경: blocked/cancelled.
- B의 소유권으로 A job을 claim: 거부, A의 prepared/reserved 그대로 유지.
- 선행 결과: 정상 승인/등록 결과만 claimed; 승인 철회·결과 교체·외부 프로젝트 hash·권리 철회는 blocked.
- 이미 claimed 후 recover한 unknown에 권리를 철회해도 outcome_unknown/uncertain을 유지한다. 불명 비용을 미전송으로 간주해 풀지 않는다.

관련: MS-FR-05/06/09/13/18/23, MS-AT09/21/30/34의 **synthetic Store claim 부분**. 외부 submit 직전 전송 bytes의 고정과 provider receipt까지 묶은 실제 dispatcher 계약은 아직 이 모듈에 없다. claim 이후 외부 네트워크 제출을 원자적으로 검증했다는 주장은 하지 않는다. 과거 G01의 ‘로컬 등록 자산→canonical 권리→claim’ 연결 부족은 이 범위에서 해소됐다.

## F05/F06 및 일반 채팅의 검사 한계

F05는 실제 drawGuided가 음악 미확정 버튼에 disabled/data-plan-blocked를 출력함을 확인했다. sendRequest의 성공/서버 오류/transport 오류/refresh 오류 및 act의 cache 오류 후에도 해당 버튼은 disabled이고 일반 버튼은 복원됐다.

F06의 기존 문제는 통과했다: 1.25초/한국어 의견 새 VM 로드 복원, 프로젝트·workspace 분리, 실패 시 유지, 정상 성공 시 정리. 다만 위 F07 경합이 추가로 남는다.

134개 선택 회귀에는 신규 `test_next_functional` 8개, `test_chat_runtime` 18개, `test_chat_ui` 1개가 포함된다. 채팅 취소/unknown/restart/동시 worker/예산/오류 sanitization은 **기존 테스트의 fake transport 재실행**으로 확인했다. 이 18개를 독립 작성한 18개 새 반례로 표현하지 않는다. `AnthropicChatAdapter`에 가짜 transport를 주입한 테스트가 내부 mode=anthropic-live를 기록하는 경우도 실제 API 호출 성공 증거가 아니다. 사용한 secret canary도 테스트 문자열이며 실제 키는 읽지 않았다.

새 일반 채팅의 실제 API/가격/실청구/답변 의미 정확성은 기능 세션의 별도 시험 범위다. 이번 감사는 해당 연결을 호출하거나 현재 서버 상태를 조회하지 않았다. F05/F06 브라우저 실행과 모바일·키보드·스크린리더도 여기서는 미검증이다.

## 이전 F/R 회귀 및 증거 해석

- F01: 정상 Store 큐 등록 후 권리 철회 → fake submit0, submission_blocked.
- F02: 완료 poll 뒤 cancel timeout → cancelled_result와 결과 유지.
- F03: 관계 변경이 영향 대상으로 잡히고 과거 relation snapshot 유지. 인접 relation 변경/삭제/복원/provenance 검사도 통과.
- F04: 30×0.130초 요청3.900초 → 출력3.916667초. frame quantization 범위 내이며 누적30컷 손실 없음.
- R01: 30×0.131초 요청3.930초 → 출력3.958333초. 끝 자막3.920–3.930 및 3.925초 click peak20054 보존. 내부 경계와 마지막 ceil을 500 sequence/7663 boundary로 검사했다. 잘못된 자막 내용·시간 및 짧은 오디오 출력은 거부됐다.
- R02: 확정 미전송·미청구 reservation release만 quota 반환. unknown/접수됨/late-bill은 quota를 유지하고 새로운 중복 제출을 막는다.

미디어는 전부 이번 감사 폴더 안에서 만든 synthetic fixture다. 실제 고객 자료나 공급자 영상 품질 검사가 아니다.

## 버전 고정과 진행 중 변경

`snapshot-manifest.json`은74개 source/test/HTML/보고 문서의 bytes·mtime_ns·SHA256을 보존한다. `environment-static.json`은 Python3.15.0/Node26.11.1/FFmpeg9.0.2 및 문법 검사 결과를 기록한다.

11:54:41 UTC 종료 대조에서 **snapshot 변경0**이었다. 다만 기능 개발이 계속되어 원본3개가 변경됐다.

| 파일 | 검사한 SHA256 앞12자리 | 이후 원본 앞12자리 |
|---|---|---|
| action_execution.py | c35709d92e38 | 570b674b2e1a |
| chat_runtime.py | 786c161cd628 | 7128a1e617e4 |
| production_tools.py | d63909e74964 | 68688033fd02 |

`source-drift.json`에 전체 hash, `later-source-drift.patch`에 관측 diff를 보존했다. 후속 diff는 job projection/조회 정보 확대, 채팅 stage·token·tool·turn limits 관련이다. **이번 통과 결과를 이 후속 세 파일에 그대로 적용하지 않는다.** 이 보고서는 부모가 지정한 11:40 통합본과 일치한 11:47:52 snapshot의 판정이다. `index.html`은 변경되지 않아 F07은 종료 대조 시점 원본에도 같은 코드가 남는다.

모든 import와 실행은 snapshot에서 했고 temp DB는 감사 폴더 안에서 생성·정리했다. Python socket connect/create_connection/bind는 harness에서 거부하도록 했다. 실제 외부 호출0, 키/.env/인증파일 조회0, 사용자DB 접근0, listener/재시작/브라우저 조작0. 제품 소스 수정0. 이번 감사에서 도구 승인 거부·pending·불명 실행 결과는 발생하지 않았다.

## Readiness

| 범위 | 판정 |
|---|---|
| Local demo | 고정 snapshot의 B03/모의 미디어 승인·권리·인계 경로 수용. 검토 의견 입력 보존에는 F07이 남아 조건부. |
| Limited pilot | 완료 선언 불가. F07 수정 및 실제 브라우저 회귀, 실제 provider dispatcher/결과 수집/허용 범위에 맞는 live 증거가 별도 필요. |
| Full spec | 미충족/미검증. 96FR·143API와 새28MS-FR·38MS-AT는 별도이며 이번 fake/local 결과로 전체 pass를 선언하지 않는다. |

기능 세션의221개 통합 통과는 그 보고서의 baseline이다. 이번 독립134개 비HTTP 통과 및 계약별 결과를 그 전체 재실행으로 혼동하지 않는다.
