# 일반 채팅 UI의 실제 Claude 시험 준비 및 실행 차단

2026-10-25. 이전 221개 통과 checkpoint 이후 변경이다. 이번 실제 Claude UI 경로는 **실행 전 승인 심사 차단**이며 성공으로 계산하지 않는다.

## 완료한 코드 변경

- `chat_runtime.py`: 서버 승인에 도구 allowlist, 입력/출력 토큰 상한, 대화별 예산, 시험 단계별 누적 예산, 최대 대화 횟수, 같은 입력 재접수 제한을 묶었다. 기본값은 기존 계약을 유지한다. 모델이 허용 목록 밖 도구를 반환하면 DB 작업 전에 중단한다. 기존 $50 누적 원장과 새 단계 $0.10 제한은 같은 SQLite `BEGIN IMMEDIATE`에서 검사한다. 결과 미확정 예약은 계속 비용에 포함한다.
- `action_execution.py` + `production_tools.py`: 현재 프로젝트의 작업 조회에 mode, action/grant ID, 외부 호출 수, 결과 SHA256, 결과 승인 여부, 실제 등록된 Take 좌표를 반환한다. 로컬 파일 경로나 공급자 인증정보는 반환하지 않는다. 이전에는 상태만 반환하여 최종 답변이 Take 저장 사실을 조회할 수 없었다.
- `scripts/claude_chat_ui_trial.py`: 별도 합성 저장소와 localhost 서버를 이용하는 명시적 1개 워크플로 시험 런처. 실제 실행은 거절되어 fixture와 서버가 생성되지 않았다. 실제 어댑터는 기존 `AnthropicChatAdapter`를 사용하며 별도의 가짜 성공 구현을 만들지 않았다.
- `tests/test_chat_live_scope.py`: 네 가지 관련 회귀를 추가했다. 실제 API 사용 없음.

## 검증 결과

| 범위 | 기대값 | 실제 결과 | 증거 등급 |
|---|---|---|---|
| 서버 도구 제한 + 입력 8,192 허용 | count 5,000 허용, 승인된 도구 하나만 전송 | pass | fake transport + 실제 Store/SQLite |
| 목록 밖 모델 도구 | 계획 쓰기 전에 중단 | pass; proposal 생성 없음 | fake model response |
| 단계 예산 | 이전 turn의 unknown 예약도 포함 | pass; 다음 count/message 이전 차단 | SQLite |
| 저장 결과 조회 | 현재 프로젝트 Take ID/해시, mock 경계 노출; 경로 미노출 | pass | deterministic tool test |
| 채팅 관련 회귀 | 기존 취소/중복/비밀 canary/재시작 유지 | 30 pass | fake/contract |
| 전체 회귀 | 기존 기능/HTTP/미디어 fixture 보존 | **225 pass, 26.037s** | 로컬 HTTP, 파일, DB, fake providers |
| Python/JS 정적 검사 | 문법 오류 없음 | pass | AST / node --check |
| 실제 일반 채팅 요청 | browser → actual provider → plan → approval → local result → answer | **blocked / not run** | 실행 승인 심사 거절 |
| 최신 변경 UI 시각 검사 | 실행 코드와 같은 화면에서 확인 | not run | 이전 화면 증거와 구분 |

`full-tests.log`, `targeted-tests.log`, `checkpoint.json`이 이번 근거다. 225라는 수는 기능 완성도 또는 실제 Claude 품질 통과율이 아니다.

## 고정한 실제 시험 조건

- 목적: 합성 Song A의 승인 온톨로지와 곡 한정 예외를 실제 Claude가 조회하고, 검토 전 계획을 저장한 뒤 UI에서 승인·모의 후보 실행, 이어 같은 서버 작업 영수증을 조회한 최종 답변까지 연결.
- 데이터: 가상 Mira의 기본 파란 코트, Song A 스튜디오의 빨간 코트 예외, 알려지지 않은 나이. 실제 사용자 프로젝트/계정 자료는 전송하지 않음. 합성 2초 무음 WAV는 로컬 파일이며 API에는 음악 메타데이터만 포함. 영상·이미지 파일은 전송하지 않음.
- Claude 모델: `claude-haiku-5-5`, 공식 `https://api.anthropic.com/v1/messages`와 사전 `count_tokens`만 사용.
- 1단계 도구: `search_project_context`, `propose_media_plan`. 2단계 도구: `search_project_context`, `get_generation_job`. 권한 변경/영상 호출 도구 없음.
- 사용자 입력 최대 2건, 각 최대 4회 모델 응답, 각 요청 input cap 8,192 / output cap 4,096. 요청 전체(system/tools/messages 포함)를 먼저 count. 모델·가격·입력 해시·문맥·도구 범위를 서버에서 고정.
- 모델 응답 한 회 상한 계산: 8,192 × $0.10 / 1M + 4,096 × $0.50 / 1M = $0.0028672, 원장 예약은 올림 $0.002868. 최대 8회 예약 합계 **$0.022944**. 대화당 $0.012, 이번 단계 누적 $0.10, 전체 개발 누적 $50를 각각 검사한다. 가격 계산은 공급자 청구서 확인과 다르다.
- 자동 재시도·모델 대체·캐시·서버 도구·자동 충전 없음. 애매한 응답은 재발행하지 않음.
- 기존 `.env`의 `Anthropic_KEY`만 승인된 서버 인증 메모리에서 사용. 새 키 저장/설정 변경 없음. request 기록에는 auth headers 없음. private thinking은 로그로 저장하지 않음.
- 2단계 문맥은 사람이 검토한 실제 저장 카드가 approved이고 Take가 등록된 뒤에만 별도 고정. 첫 번째 승인 문맥을 자동 확장하지 않는다.
- 미디어는 `SyntheticImageAdapter`의 단색 PNG, 비용 $0의 로컬 모의 후보. Claude 대화가 성공해도 실제 영상 생성 성공이 아니다.

가격은 [공식 Haiku 5.5 모델 페이지](https://platform.claude.com/docs/en/models/haiku-5-5/overview)의 100k 이하 입력 $0.10/MTok, 출력 $0.50/MTok를 2026-10-25 재확인했다. [공식 토큰 계산 문서](https://platform.claude.com/docs/en/build-with-claude/token-counting)는 count가 무료·별도 rate limit 대상이며 캐시를 사용하지 않는다고 설명한다. count는 추정이며 실제 usage와 최종 청구는 별도 기록한다.

## 정확한 실행 차단

- action: `python3 -u scripts/claude_chat_ui_trial.py`로 합성 전용 localhost 시험 서버 시작. 시작 후 UI의 명시적 입력이 있어야 actual Claude 요청.
- target: Mac의 새 합성 데이터 루트/localhost, 기존 키 인증의 공식 Anthropic API.
- 상태: **denied, known not executed**. 자동 승인 심사는 “기존 credential로 프로젝트 prompt/context를 Anthropic에 전송하고 API 비용을 발생시키는 exact request와 stated budget에 대한 trusted user explicit authorization이 부족하다”고 판정했다.
- 기존 승인 대화가 전달되어 있었지만 이번 실행 심사는 위와 같이 판단했다. 동일 명령/간접 실행/다른 경로로 재시도하지 않았다.
- 확인: `attempt.json` 없음, `runtime.json` 없음, 이번 stage 원장 0행. 기존 원장 9행 그대로. 이번 신규 API count/messages 0, 신규 과금 0.
- 기존 precise usage 계산 **$0.0049575** 그대로. 마이크로달러 단위 보수적 올림 누계 $0.004960. 공급자 billing 확인은 아직 없음.

부모에게 전달할 필요한 확인 범위: **기존 `.env`의 `Anthropic_KEY`를 서버 메모리에서 공식 Anthropic count/messages 인증에만 사용하여, 위 합성 온톨로지 자료로 일반 채팅 UI 2입력/최대 8모델 응답의 1개 워크플로를 실행하며 이번 단계 $0.10 이내, 기존 개발 누적 $50 이내로 진행. 새 키·외부 미디어 호출·실제 프로젝트 전송 없음.** 키 노출 시 무단 사용과 과금 위험이 있어 브라우저/로그/파일로 키를 복사하지 않는다. 새 관련 승인 근거 없이 거절 작업은 재시도하지 않는다.

## 런타임과 남은 경계

- 기존 `127.0.0.1:8773` Python PID 54885 리스너 존재 확인. 이번에 재시작하지 않았다. 8773 백엔드는 이전 freeze이므로 이번 코드 변경이 반영됐다고 주장하지 않는다. HTML hash는 기존 `25860298244aa518ed322fdc38cb8f9875168fb6c31aa766bc21dc3e2435acd3` 그대로다.
- 새로운 전체 회귀의 로컬 HTTP는 최신 source를 임시 fixture 서버에서 검사했으나, 실제 사용자 채팅 브라우저 워크플로는 아직 미검증이다.
- 외부 미디어 boundary는 `rehearsal_workflow.handle(action_execute)`의 `SyntheticImageAdapter`와 `action_execution`의 rehearsal grant/reservation/job 경로다. canonical rights check는 claim에 연결되어 있지만 실제 provider의 제출/접수 ID/다운로드/수집을 새 action dispatcher와 연결하는 단계는 아직 없다.
- 기존 fal generation 구현은 별도 legacy 경로이며 실제 다운로드/토큰 403을 해결했다고 볼 수 없다. 이번 변경으로 이 문제를 우회하거나 재요청하지 않았다.
- 따라서 아직 “영상 API만 남음” 또는 실제 고객 운영 준비 완료라고 판정할 수 없다. 현재 blocker는 이번 actual chat UI 승인 심사, 그 다음 실제 채팅 E2E 결과 확인, 새 action↔external media bridge와 실제 fal 회수 검증이다. 다중사용자/배포/12모델 조합 수용 검증도 별도 범위다.
