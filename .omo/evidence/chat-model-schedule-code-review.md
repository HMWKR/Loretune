# 대화 모델 예약 독립 코드 리뷰

판정: **WATCH / APPROVE**, 예약 기능의 현재 코드 범위에 한정. 확인된 CRITICAL/HIGH 결함은 없고 제품 전체 완료 승인이 아니다.

## 범위와 방법

- 읽은 구현: chat_sessions.py, chat_runtime.py, app.py의 세션 트랜잭션 경계, index.html의 모델 선택/예약/제출 상태.
- 읽은 기준: 원본07 §3.2, docs/design/CHAT-SESSION-PLAN.md의 CS08 충돌 기록.
- 읽고 독립 실행한 테스트: tests/test_chat_model_schedule.py, tests/test_chat_sessions.py, tests/test_chat_runtime.py.
- git status는 저장소가 아님으로 실패했다. full diff 및 별도 notepad 경로가 제공되지 않아 현행 파일을 검토했으며 수정 기원 전체는 판정하지 않는다.
- omo-agent-toolkit ulw-loop status --json은 bun/node fallback 부재로 실패했다. .omo가 없었으므로 지정된 fallback 보고서 경로를 사용했다.
- 역할 설정은 gpt-6-astra 코드 품질 리뷰이며 모델/추론 설정의 별도 런타임 계측은 없다. 제품 파일 수정과 유료 호출은 하지 않았다.

## 독립 검증 결과

실행: `python3 -m unittest tests.test_chat_model_schedule tests.test_chat_sessions tests.test_chat_runtime`

결과: **30 tests / 5.962s / OK / exit 0**. 실제 로컬 HTTP 및 임시 SQLite, 합성 공급자 어댑터를 사용한다. 실제 Claude/GPT 요청 또는 브라우저 시각 검증 결과가 아니다.

chat_sessions.py:40–70에서 예약만 갱신하고 effective selection은 유지하며 after_turn과 conversation_id가 일치할 때만 적용한다. chat_runtime.py:187 부근 _save는 BEGIN IMMEDIATE 안에서 turn 완료와 선택 적용을 함께 저장한다. cancel_requested가 먼저 기록된 경우 cancelled로 치환되어 예약을 적용하지 않는다. app.py:283–313의 세션 revision/shared fingerprint 검사는 동시 요청을 직렬화하며 타 세션 로컬 기록을 분리한다.

신규 테스트는 실행 중 예약, stale revision, 다른 세션 유지, 완료 후 재열기, unknown 유지/변경 차단, 취소 후 명시 재선택을 관찰한다. 기존 테스트는 다른 세션의 같은 global revision 쓰기 및 원자적 공동 예산 제한을 포함한다. 그러나 두 세션 모두가 모델 응답을 수행하며 동시에 예약하는 조합, 중단/재시작의 모든 지점, 실제 공급자별 사용량은 이번 신규 시험으로 입증되지 않는다.

## Skill perspective

remove-ai-slops 및 programming은 제공된 skill catalog에 없고 ~/.agents/skills, ~/.codex/skills, plugin cache 경로 검색에서도 SKILL.md를 찾지 못했다. 따라서 설치 스킬을 실행했다고 주장하지 않는다. 요청에 제공된 두 관점의 기준으로 production/test 수동 검토를 실행했다.

신규 테스트는 HTTP 입력에서 저장/충돌/재열기 결과를 검사하므로 상수 복제나 삭제 자체만 검증하는 테스트가 아니다. 신규 production 상태는 기존 세션/트랜잭션 경계에 최소한으로 추가되며 불필요한 일반화·새 파싱 계층은 확인되지 않았다. 이 검토 범위에서 두 관점의 구체적 위반은 발견하지 않았다.

## Findings

- CRITICAL: 없음.
- HIGH: 없음.
- MEDIUM: 없음.
- LOW D01: docs/design/CHAT-SESSION-PLAN.md:5의 ‘구현 미재개’와 :67 부근 CS08의 ‘active 변경 차단’은 현재 예약 구현 상태와 다르다. 문서 자체도 충돌을 명시하지만 새 코드 인수 시 최신 계획/증거와 연결해야 한다. 제품 코드 차단 결함은 아니다.

## 문서 및 인계 제한

문서 검사기를 읽고 read-only check.py를 실행했다. 시작 시 REGISTERED_SOURCE_OUTDATED 2건은 docs/qa/codex-workflow-review-20261027/REPORT-ko.md의 knowledge/specification 등록 사본이다. 기존 문맥 stale 경고도 존재한다. 등록/승격은 실행하지 않았다. 이 리뷰는 후속 실행 기록이며 권위 문서 승격 여부는 주관 담당자의 문서 게이트 절차로 결정한다.

blockers: []
