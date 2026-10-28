# 보강된 계획 영수증 — 실제 Claude 재검증 완료

2026-10-25. 이전 일반 채팅 실제 시험에서 Claude는 작업·Take·해시는 맞게 답했지만, 서버 영수증에 계획 연결이 없어 계획 ID를 확인할 수 없다고 답했다. 이후 `action_execution.project_jobs`와 `production_tools.get_generation_job`에 **plan_id / plan_revision / release_id / 등록된 Take**를 보강했다. 그 변경이 이번 재검증 이유다. 이전 모델 답변을 고쳐 쓰지 않았다.

이번에는 같은 승인된 합성 DB를 읽기 전용으로 열고, 실제 이전 tool_use에 대응하는 최신 서버 tool_result를 구성했다. 실제 Claude Messages **1회**로 이 영수증·canonical source를 다시 해석시켰다. 전체 UI 여정을 유료로 반복하지 않았으며 새 계획·Take·media job을 만들지 않았다. `scripts/claude_receipt_recheck.py`가 실행 코드다.

## 결과

- 모델: `claude-haiku-5-5`
- request: `req_011CgNwE8NqJaPBNNGrJGinB`
- 사전 count 1회: 2,921 tokens. 입력 상한8,192 / 출력 상한4,096.
- 실제 Messages 1회: 입력2,921 / 출력408 / `end_turn`.
- 단일 예약 $0.002868, 이번 단계 상한 $0.05, 누적 개발 승인 $50. 자동 retry0 / fallback0.
- 이번 usage×가격 계산 **$0.0004961**, 기존$0.0072619 포함 **$0.0077580**. 공급자 청구서 확인 아님.
- 기존 `Anthropic_KEY`는 승인된 공식 API 서버 인증 메모리에서만 사용. 새 credential 저장·생성0, 실제 사용자 자료 전송0, 외부 미디어 생성0.

| 검사 | 실제 결과 |
|---|---|
| 계획 ID / 버전 | 595787d6ebc649448d47843c8dbb4a3f / 1 일치 |
| 작업 / release / Take / hash | 실제 DB 영수증과 모두 일치 |
| 검토 상태 / 외부 생성 수 | 미승인 / 0 유지, mock을 AI 영상이라고 하지 않음 |
| 전역 파란 코트 / 곡 한정 빨간 코트 / 나이 | 범위를 구분하고 전역 변경 false, 없는 나이는 unknown |
| provenance | source_id와 원문 excerpt가 정확히 일치 |

5개 검증 항목 pass. 구조화 응답 유효성만을 근거로 내용 정확성을 선언하지 않고 서버 영수증·source와 필드별 대조했다. 한 합성 사례의 성공이며 전체 ontology 품질이나 사용자 조사 결과는 아니다.

입력 SHA256 `5cdee9f781cbe71f872e183965d5e727232c111d82528b6cab8572c42c6460cb`.
출력 SHA256 `f85e4ca616441bed7a5e952c2305f113a7c5d14ca0ad49e9c6c5d1ad100a1c54`.

근거: `request.json`, `actual-receipt.json`, `answer.json`, `result.json`. 원장 `../anthropic-smoke-20261025/usage.sqlite3`의 `claude-receipt-recheck-20261025-001`. 실제 토큰·인증 헤더는 산출물에 없다.

당일 확인된 공식 가격: [Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview), 100k 이하 입력$0.10/MTok·출력$0.50/MTok. [count_tokens 설명](https://platform.claude.com/docs/en/build-with-claude/token-counting). 이번 검증 후 실제 Claude 추가 호출0.
