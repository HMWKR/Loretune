# 실제 Claude 온톨로지 조회·계획 저장·근거 답변 검증

2026-10-25. 합성 인물 Mira/Theo와 rooftop/studio 및 의상 충돌 텍스트만 사용했다. 실제 프로젝트 자료·음원·이미지는 전송하지 않았다. Claude는 서버의 canonical 데이터로부터 제안하며 ontology 자체나 승인 주체가 아니다.

## 결과 판정

**대표 한 경로는 실제 Claude → 서버 문맥 도구 → 도구 결과 → 계획 저장 도구 → 실제 DB 계획 → 최종 근거 답변까지 확인했다.** 앱의 일반 채팅창에 지속 실행 transport가 통합됐다는 뜻은 아니다. 별도 bounded 합성 평가 런처에서 기존 Store/controller를 사용한 검증이다. 실제 이미지/영상 공급자는 호출하지 않았다.

실제 답변은 기본 코트 `blue`, Song A studio 코트 `red`, 나이 `unknown`, 기본 설정 변경 `false`, 저장 계획 `46d0aa5d81584c85874dee1b295d77dc`/`proposed`, approved/generated/paid 모두 `false`였다. 두 승인 사실과 원문 불확실성의 정확한 출처를 인용했다. `answer.json`과 `offline-review.json` 참조.

## 실제 실행 순서와 실패도 포함한 기록

| 단계 | 관측 | 판정 |
|---|---|---|
| 최초 ontology 2,048 출력 cap | max_tokens, $0.0011523 | 미완결. 적용 0 |
| ontology follow-on 001 | end_turn이나 로컬 contract 거절, $0.0013493 | 최초 후보가 보존되지 않아 정확한 실패 필드 미확인 |
| ontology follow-on 002 | schema·exact spans 통과, 인물2/장소2, $0.0011427 | 합성 검증 DB에서만 승인/재시작 검사. 관계0, typed clothing claim·교차 호출 ID 품질은 미검증 |
| 첫 tool 평가 | 조회 성공, 계획 인수 검증 거절, $0.0003674 합계 | 잘못된 계획은 저장하지 않음. 그 응답 인수가 미보존되어 정확한 필드 미확인 |
| 진단 tool 평가 | 실제 조회→tool_result→실제 계획 도구 저장, $0.0005009 합계 | 계획1, 외부 프로젝트 계획0, 동일 tool call 반복에 계획 추가0 |
| 최종 답변 최초 준비 | count_tokens가 4,096 상한 초과 | Messages POST 0. 응답불명이 아닌 `blocked_before_message`; 예약 해제. 기존 도구 응답에 전체 문맥이 중복되어 커짐 |
| 간결한 계획 receipt로 답변 1회 | 입력3,294/출력231, end_turn, $0.0004449 | 실제 완료 답변. 추가 도구 실행/계획 저장/영상 생성 없음 |

처음 답변 평가기는 “blue”를 “blue coat”와 다르게 처리하고 근거를 정확히 두 개만 허용했다. 요청 schema에는 그런 제한이 없고 추가 `brief-2` 인용은 실제 전달한 ontology provenance의 exact span이다. 최초 `semantic_failed` 결과를 지우지 않았다. 검증기는 명시적인 색상 동의 표현만 허용하고, 두 승인 사실을 반드시 인용하며, 추가 인용도 입력에 있는 정확한 span만 허용하도록 수정했다. 별도 `offline-review.json`의 7개 검사는 모두 통과했다. 재평가를 위해 API를 다시 호출하지 않았다. 사실이 틀린 응답을 자동 repair하지 않는다.

## 요청·비용 증거

모델은 `claude-haiku-5-5`, 공식 입력 $0.10/MTok / 출력 $0.50/MTok(p<=100k) 기준이다. 이 문서 시점 실제 Messages 8회, token count 9회. 비용 계산 누적 **$0.0049575**. 계정 billing 실청구는 **미확인**이다. micro-USD 원장은 보수적 올림으로 $0.004960을 기록한다. $50는 전체 승인 상한이며 사용 목표가 아니다.

| 요청 | request ID | usage 계산 USD |
|---|---|---:|
| ontology smoke | req_011CgNn1N4CFqz2GQs6XFV8b | 0.0011523 |
| ontology 001 | req_011CgNnJnAFY48aPMNgGnsju | 0.0013493 |
| ontology 002 | req_011CgNnq6PSep9gS4pGoQk8p | 0.0011427 |
| first tools/read | req_011CgNoGiJPqGqzUde26B171 | 0.0001099 |
| first tools/invalid plan | req_011CgNoGsLr5bGTy9pTw8toA | 0.0002575 |
| diagnostic/read | req_011CgNoQxXcca8QVS6X6bcJK | 0.0001120 |
| diagnostic/plan | req_011CgNoRbEEtH8ZoYvqb9bby | 0.0003889 |
| concise final answer | req_011CgNp3zRkXojFjzqBCWFhs | 0.0004449 |

최종 입력 hash `9f4e59766ebcec43982b0489ca202e97f706e869906a82eb87e0eb1962ff5e1a`, text 응답 hash `9fa080dfe38ddb0de87732e11bac32a18c2d33610e12eed6e96153653a0a482f`. JSON 재직렬화 파일의 hash는 이 text hash와 다르며 offline-review에 별도로 기록했다.

원장: `../anthropic-smoke-20261025/usage.sqlite3`. 동일 ID를 재실행하지 않으며 요청 직전 원자적 예산 예약을 수행했다. 키는 기존 파일에서 서버 프로세스 메모리로 읽어 공식 API 인증에만 사용했고 새 키 저장/로그/화면 노출/충전/다른 모델 fallback은 하지 않았다. count_tokens는 [공식 문서상 무료](https://platform.claude.com/docs/en/build-with-claude/token-counting)이지만 실제 Messages usage와 billing 확인을 혼동하지 않는다.

## 수용 기준별 증거 경계

| 사용자 요구 | 실제 Claude | 서버/로컬 검증 | 남은 것 |
|---|---|---|---|
| 승인 사실 근거 답변, 없는 정보 | 기본/예외/unknown 및 실제 ID 답변 확인 | exact source span·receipt 검증 | 다양한 사실/한국어 장기 대화 품질 |
| 일회 예외와 global 구분 | red studio exception, global_changed=false | 입력 canon 보존 | 별도 typed claim 모델의 범위 제약 |
| 다른 프로젝트 접근 차단 | foreign gold 데이터가 답변/계획에 없음 | 다른 scope/run/action 거절 테스트 | 실제 Claude의 악성 cross-project tool 시도는 미실행 |
| 설정 변경 영향 샷만 수정 | 미실행 | 기존 ontology relation impact 회귀 통과 | live 제안과 영향샷 UI 통합 |
| hold/reject/approve 후 실행 | Claude는 계획만 저장, 승인하지 않음 | 별도 실제 브라우저 사람 승인→모의 PNG→Take→출력 | 같은 실제 Claude 계획에서 영상 provider까지 연결 |
| stale proposal 거절 | live 출력 합성 DB로 stale 검증 | optimistic revision/rollback 테스트 | live multi-turn stale 설명 |
| source 없는 hallucination 거절 | 이번 답변 출처 모두 실제 존재 | 위조 source/권한/ID 변조 negative fixtures 거절 | 다른 환각 유형을 충분히 평가하지 않음 |
| 중복 도구 멱등성 | 실제 받은 call을 서버에서 재전달 | 동일 결과, 계획1 유지 | 실제 모델이 반복하는 긴 대화 |
| 권한·예산 증액 차단 | 그런 요청 live 미실행 | 모델 grant 생성/actor/가격 인수 거절, 동시 cap 테스트 | UI 실사용자 권한/조직 검증 |
| 모델 교체 job 보존 | 다른 provider live 미실행 | B01 회귀, private reasoning 제외 | 실제 계정/provider handoff |
| 실패/unknown 정직 설명 | 미실행 | reserved/unknown/미전송과 파일 회수 상태 분리 | 실제 Claude의 오류 설명 평가 |

## 다음 단계

현재 stage는 완료하고 자동 추가 호출하지 않는다. 앱 소스는 디자인 QA를 위해 고정한 상태다. 다음 구현은 간결한 서버 receipt와 canonical ID를 일반 채팅 transport에 통합하고, 실제 사용자 승인 UI·asset 권리 재검사·새 action provider bridge를 연결하는 것이다. 소스 고정 해제 후 별도 합성 사례로 권한 거절·stale·unknown 답변을 검증해야 한다. 영상 API만 해결하면 모든 MVP가 끝난다고 판정하지 않는다.

공식 근거: [모델·가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview), [도구 정의·간결한 tool result](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools), [구조화 출력](https://platform.claude.com/docs/en/build-with-claude/structured-outputs). 이 자료는 구현 계약 근거이며 이번 앱의 전체 품질 증거가 아니다.
