# F07 독립 최종 재검증

**F07을 검사 범위 안에서 수정 완료로 닫는다.** 원래 delayed-fetch 반례와 요청한 프로젝트·샷 전환/입력 재작성/실패/반복 저장에서 새 초안 손실은 재현되지 않았다. 추가 correctness blocker는 발견하지 않았다.

| 검사 | 결과 | 증거 |
|---|---:|---|
| 이전 독립 fixture: F05/F06 및 원래 F07 | **12/12 통과** | `original_repro.js`, `ui-results.json`, `original-repro.log` |
| 새 독립 인접 경합 | **16/16 통과** | `adjacent_recheck.js`, `adjacent-results.json`, `adjacent.log` |
| 기존 제품 UI unittest | **2/2 통과** | `existing-ui-tests.log` |
| 위 unittest 안의 기능 세션 초안 fixture | 16/16 통과 | `snapshot/docs/qa/f07-comment-draft-20261025/ui-results.json` |
| HTML script 문법 | node --check 통과 | `static-result.json` |

위 집합은 겹치는 동작을 포함하므로 합산 완성률로 계산하지 않는다. 기능 세션의 **전체226개 통과는 보고받은 baseline**이며, 이번에 전체226개를 재실행한 것은 아니다. 기존 unittest는 `test_comment_draft.py`와 관련 disclosure/cancel 회귀 `test_chat_ui.py`만 실행했다.

## 원래 F07 전후

실제 HTML의 `comment.onsubmit`, `act`, `sendRequest`, pending helpers, input listener, draft 복원 함수를 Node VM에서 실행했다. 통신은 지연된 fake fetch이며 브라우저나 서버는 사용하지 않았다. 이전 독립 fixture의 시나리오는 그대로 유지했고 새 코드가 참조하는 기존 앱 전역 `shotName`만 VM에 추가했다.

1. `1.25 / first submitted draft`를 제출하고 응답을 보류.
2. 대기 중 `2.5 / second unsent draft while save pending` 입력.
3. 첫 요청을 성공으로 완료.

| 관측 | 수정 전 | 수정 후 |
|---|---|---|
| 전송 payload | 첫 의견 | 첫 의견 |
| 대기 중 쓴 두 번째 의견 | 입력 빈 값, 저장소 삭제 | **입력과 저장소 모두 보존** |
| 기존 제출본만 성공하고 추가 편집 없음 | 정상 정리 | 정상 정리 유지 |

수정 전 결과·fixture·manifest는 `before/`에 보존했다. 새 결과의 마지막 `F06-adjacent-pending-save-must-preserve-new-edit`는 pass다.

## 인접16개 결과

- 입력 삭제 후 다른 문구로 재작성, 삭제 후 같은 원래 문구로 재작성, 삭제한 빈 초안 자체 유지: 3개 통과.
- A 저장 중 B의 기존 초안으로 전환, B에 새 초안 작성, A로 돌아와 새 초안 작성, A로 돌아왔지만 새 편집 없음: 4개 통과. B 초안을 유지하며 변경 없는 A 제출본만 정리한다.
- 샷 전환 후 새 입력, 샷만 전환했을 때 다른 문맥의 폼 reset 방지, 샷을 돌아온 뒤 같은 원래 값으로 재작성: 3개 통과.
- 서버 실패 응답, 응답 유실, 저장 성공 후 화면 갱신 실패에서 후속 초안 유지: 3개 통과. 응답 유실의 pending request도 유지한다.
- workspace 전환 뒤 새 초안 유지: 1개 통과.
- 저장 대기 중 중복 저장 시도, 첫 저장 후 두 번째 저장 대기 중 세 번째 초안 작성, 마지막 변경 없는 저장만 정리: 1개 통과.
- 실패한 저장을 다시 시도하고 그 응답 대기 중 또 입력한 초안 유지: 1개 통과.

샷 전환만 있고 새 편집이 없는 사례는 **폼을 다른 문맥에서 reset하지 않는지** 검사했다. 초안 저장 key는 workspace/project 기준이므로 샷별 독립 초안 저장 기능까지 구현됐다고 주장하지 않는다.

## 수정 원인 확인

`snapshot/index.html:198`의 `commentDraftRevisions`와 `:201`의 input listener가 key별 편집 revision을 증가시킨다. `:254` submit handler는 제출 당시 key/shot/revision/폼 직렬화 값을 고정한다.

성공 처리에서는 revision이 같고 저장값도 제출본과 같을 때만 sessionStorage를 제거한다. 폼 reset은 추가로 현재 key·shot·폼 값까지 일치해야 한다. 따라서 문구를 바꿨다가 같은 값으로 되돌리는 편집도 단순 문자열 비교로 오인하지 않는다. 기존 F05의 미확정 계획 disabled 조건과 F06의 reload복원/실패 시 보존/정상 성공 정리도 유지된다.

이 결과는 F06/F07 입력 보존 계약의 scoped verification이다. 관련 기존 FR-060/FR-062 전체 수용시험이나 새38 MS-AT 완료로 확대하지 않는다.

## 버전·제약·재현

- Capture: **2026-10-25 12:12:52.653320 UTC**.
- 검사 HTML SHA256: **7426e52fdb37487dbf7dba35344146a8d13408795aff9aa363334a860f6d5fa3**.
- `snapshot-manifest.json`: HTML/보고서/테스트/fixture의 bytes·mtime_ns·hash.
- `source-drift.json`: 종료 대조 시 대상 원본 변경0, snapshot 원본 파일 변경0.
- `REPORT-ko.md`와 소스/시험을 읽고 확인했다. 해당 보고서의 실제 브라우저 결과는 별도 제공 증거이며 이번 독립 브라우저 시험으로 계산하지 않는다.
- 제품 소스 수정0, 사용자DB 접근0, 브라우저 조작0, 실제 API/키 조회0. 이번에는 DB 자체가 필요 없는 합성 JS fixture만 사용했다. 승인 거부·보류·불명 도구 실행은 없다.

```sh
node docs/qa/independent-f07-final-recheck-20261025/original_repro.js
node docs/qa/independent-f07-final-recheck-20261025/adjacent_recheck.js
```

**판정:** F07 수정 수용. 요청한 좁은 회귀 범위에서 완료이며 일반 채팅·미디어·배포에 관한 새 범용 감사로 확대하지 않았다.
