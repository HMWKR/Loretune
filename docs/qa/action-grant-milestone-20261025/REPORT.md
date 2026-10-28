# 불변 실행 계약과 모델 인계: 무과금 구현 체크포인트

> 최신 결과는 [fixed-checkpoint-ko.md](fixed-checkpoint-ko.md)를 우선한다. 아래는 단계별 과거 기록이다.

2026-10-25. SPEC-MS-001 전체 완료가 아닌 로컬 계약 구현이다. 실제 모델 연결 및 38개 MS-AT 전체 통과를 의미하지 않는다.

## 구현

- `action_execution.py`: 프로젝트에 귀속된 불변 action, action hash와 가격 버전을 묶은 grant, 만료·철회·문맥 재검사, action당 단일 admission, 동일 트랜잭션의 예산 예약/작업 기록, 승인된 동일 프로젝트 dependency 및 결과 slot/hash 검증. 복구 시 실행 여부 불명은 outcome_unknown으로 유지한다. caller가 BEGIN IMMEDIATE 트랜잭션을 소유한다.
- 예산은 rehearsal 전용 scope로 실제 공급자 원장과 분리했다. local-owner 승인 제어기는 모델 tool에 노출하지 않았다. 이 계약 엔진을 실제 공급자 dispatch와 HTTP/UI에 연결하는 작업은 아직 남았다.
- `chat_protocols.py`: Anthropic tool_use/tool_result, OpenAI 및 xAI Responses function_call/function_call_output의 완결된 응답을 공통 도구 계약으로 변환한다. 중복 JSON 키, 잘못된 인수, 불완전 응답, 다른 run/provider의 tool receipt를 거절한다. 모델 변경 시 서버 문맥과 공개 대화·작업 상태만 전달하며 private reasoning과 pending provider ID를 넘기지 않는다. 실제 네트워크 transport·stream 조립·계정 통합은 미검증이다.
- `image_adapter.py`: 이미지 저장/검증/승인 dependency 계약을 검사하는 합성 단색 PNG 어댑터. 실제 AI 이미지 생성기가 아니며 외부 호출은 없다.
- `index.html`: 모델 설정을 상시 긴 폼에서 요약 바+대화상자로 변경했다. 기존 3개 역할 선택과 저장 기능을 보존했다. 모델 선택기가 있다고 연결 완료로 표시하지 않는다. 새 화면의 실제 기하·키보드 회귀는 아직 미검증이다.

## 증거와 한계

`tests/test_action_execution.py` 8개는 동시 admission, 예산 cap, queue 기록 실패의 트랜잭션 롤백, grant 철회, unknown 복구, 프로젝트/slot 오염, 결과 멱등성 및 실제 합성 PNG 저장을 검사한다. `tests/test_chat_protocols.py` 6개는 세 공급자 envelope가 동일 Store 도구 경로에 도달하는 것과 인계/인수 경계를 검사한다. `tests/test_image_adapter.py` 2개는 합성 파일 경계와 명시적 fake 표시를 검사한다.

최신 전체 허용 회귀는 `../tail-quota-fixes-20261025/regression-non-http.log`의 156개 통과다. 이 디렉터리의 이전 152개 로그는 이전 체크포인트다. HTTP 17개 제외와 서버의 이전 backend 리비전 한계는 R01/R02 보고서를 따른다. 실제 인증/다중사용자 운영, 12개 live 모델 조합, 신규 provider 연동, Anthropic smoke test는 완료하지 않았다.

프로토콜의 1차 근거: [Anthropic tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling), [xAI function calling](https://docs.x.ai/developers/tools/function-calling). 문서와 fake 계약 검증은 실제 계정 성공의 증거가 아니다.

## 후속 연결 및 승인 후 전체 회귀

`production_tools.execute`에 서버가 주입하는 생성 요청 controller를 추가했다. `app.py`는 현재 workspace/project에서만 `action_execution.request_from_plan`을 호출한다. 모델 인수는 plan/action/grant ID뿐이다. 저장 계획의 버전·문맥, action 귀속, 기존 사람 승인, 고정 rehearsal 가격 버전을 검사한 뒤 같은 트랜잭션에서 admission과 예약을 기록한다. 동일 action의 반복 tool 호출은 같은 job receipt를 반환한다. 외부 모델 호출은 없다. 신규 grant를 모델이 만들거나 전달한 가격을 신뢰하지 않는다.

현재 프로젝트의 모의 작업 상태만 공개 state에 포함하며 입력 payload·다른 프로젝트 작업은 제외한다. 채팅 진행 요약에 “모의 계약 (AI 생성 아님)”과 접수/처리/차단/미확정 상태를 표시하는 소스를 연결했다. 실제 공급자 dispatch와 사람용 action/grant 생성 화면은 아직 미완료다.

`tests/test_action_tool_bridge.py` 4개는 멱등 영수증·단일 예약, 다른 계획/오래된 버전 차단, 승인 철회/다른 프로젝트 차단, 공개 state의 프로젝트 격리·입력 비노출을 검사한다. 최신 비HTTP 160개 통과 후, 사용자 localhost 시험 승인에 따라 정식 require_escalated로 전체 회귀를 실행해 **177개, 23.948초, 모두 통과**했다. `bridge-regression-non-http.log`, `full-http-regression.log` 참조. JavaScript 구문 검사도 통과했다.

이 전체 HTTP 시험 성공은 기존 8773 장기 실행 서버의 최신화와 다르다. lsof에서 127.0.0.1:8773 listener PID33482를 확인했으나, 이어 수행한 `ps -p 33482 -o pid=,command=`는 `operation not permitted`로 거절됐다. 해당 명령은 반복하지 않았고 서버를 종료/재시작하지 않았다. 최신 UI 실제 캡처·디자인 재검증은 아직 남았다.

Anthropic 1회 시험은 새 승인 수신 후 공식 Haiku 5.5 모델·가격 및 token counting 문서를 다시 확인했다. 아직 키 조회·count_tokens·Messages 요청은 실행하지 않았다. 현재 런처는 Kling 전용이며, 정확한 혼합 대소문자 변수 `Anthropic_KEY`를 처리하는 안전한 일회성 런처·count_tokens 경로와 중복 실행 방지 기록을 먼저 완성해야 한다. 기존 승인을 다시 요구할 이유는 없으며 이것은 구현 준비 잔여 사항이다.
