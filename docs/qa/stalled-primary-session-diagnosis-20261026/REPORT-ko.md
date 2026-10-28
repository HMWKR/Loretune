# 멈춘 기본 구현 세션 — 공식 도구 진단

관측: 2026-10-26 17:32 UTC. 대상: **Loretune 전체 기능 완성**, thread `01a170bf-5655-71b3-b6ec-6b2bcfe1a023`, turn `01a178d1-95fc-71a4-ac10-f4188a3ce231`.

**확인 결과:** 공식 상태는 계속 `inProgress`이지만 반환된 마지막 도구 호출은 `completed`다. 저장된 motion trial은 15:51:35에 이미 `blocked_before_message`로 중단됐다. 두 상태의 차이는 확인했으나, 작업 세션이 계속 진행 중으로 남은 원인과 화면상의 대기 상태는 확인하지 못했다. 승인 창이 있다고 추정하지 않는다.

## 직접 시도와 결과

|대상/동작|실행 결과|해석과 한계|
|---|---|---|
|공식 `read_thread`, 대상 thread, 최신 turn 1개|성공. active / inProgress / error=null, items 102|최신 반환 항목 중 미종결 status 없음. 숨은 작업이나 원격 실행 부재를 증명하지 않음|
|공식 `wait_threads`, 동일 대상, timeoutMs=0|성공. 같은 turn·assistant message·completed tool 확인|즉시 상태 조회. timedOut=true는 기다리지 않은 조회 결과이며 도구 장애 판정 아님|
|`cua.getApp("Codex")`|**안전 제한으로 거부**|“Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.” 화면/접근성 트리를 받지 못함|
|`cua.listBrowsers()`|성공. Chrome extension 2항목, in-app browser, MCP Apps 노출|연결 목록만 확인. 탭 내용·화면 열람, 탐색, 재로드 없음. Codex 앱 제한을 브라우저로 우회하지 않음|
|`codex --version` 및 help 4종|성공. CLI 0.164.0|resume/agents/doctor의 공식 용도만 확인. inference, resume, agents TUI, doctor 실행 없음|

Codex CUA 거부 후 재시도하지 않았다. 전체 화면 캡처, AppleScript, 접근성 우회, 브라우저의 Codex 내부 경로, 다른 CLI 모델을 통한 대리 화면 읽기를 사용하지 않았다. 화면을 보지 못했으므로 보이지 않는 오류·승인 창·중단 버튼에 대한 판단은 **미검증**이다.

CLI 도움말은 `resume`을 기존 interactive session을 이어 실행하는 명령으로 설명한다. 이것이 현재 원격 host `durable`의 inProgress 턴을 안전하게 복구하거나 중복 실행을 막는 동작인지는 확인되지 않았다. 따라서 실행하지 않았다. 도움말 호출의 PATH aliases 경고는 이 진단 명령에서 발생한 로컬 경고이며 기본 구현 턴이 멈춘 원인으로 연결할 증거가 없다.

## 저장된 시험과 작업 상태 구분

- 공식 최신 assistant message: 합성 rehearsal 완료, 실제 Claude 시험 실행 전이라는 내용. 최신 tool marker `exec-7f5a8619-0f69-4f03-83ce-42a752202b99`는 completed.
- 로컬 [trial summary](../native-motion-20261026/live/summary.json), mtime **15:51:35.121286Z**: `stopped / AssertionError / provider turn not completed: blocked_before_message`.
- [transport](../native-motion-20261026/live/case-1/transport.json), mtime **15:51:35.120992Z**: count_calls=1, messages=0, request_bytes=[7336]. count_calls는 recorder 진입 횟수이며 HTTP 송신/공급자 수신을 입증하지 않는다.
- [turn](../native-motion-20261026/live/case-1/turn.json), mtime **15:51:35.120627Z**: blocked_before_message, 마지막 step count_started, request_id=null, tool_calls=[].
- [cleanup](../native-motion-20261026/live/cleanup.json), mtime **15:51:35.127838Z**: listeners=0, subprocesses_remaining=0, real_fal_calls=0. 당시 harness의 기록이며 현재 Mac 프로세스 상태를 독립 관찰한 증거는 아니다.
- count 단계의 원래 HTTP/transport/응답 오류 정보는 저장되지 않아 구체 원인은 여전히 미확인이다. 위 기록만으로 공급자 거절·credential 오류·승인 대기 중 하나로 단정할 수 없다.
- 현재 스레드 조회가 로컬 artifact보다 앞선 기록에서 끝나는 이유도 미확인이다. 메타데이터가 지연됐을 가능성과 실제 턴 실행 정체를 구분할 자료가 부족하다.

## 안전한 다음 조치와 책임 경계

1. 부모/작업 제어 담당은 **해당 thread와 turn만** 대상으로 공식 실행 제어에서 pending approval/active call 상태를 확인해야 한다. 이번에 노출된 전용 앱 도구에는 명시적 turn-resume/turn-cancel이 없었다. 숨은 RPC나 저장 DB를 사용하지 않았다.
2. 취소가 필요할 경우 대상은 위 turn 하나다. 마지막 반환 command는 완료됐으나 실제 원격 턴의 실행 여부는 불확실하다. **이번 취소·종료·재개 동작은 0회**다. 취소 성공을 먼저 확인하지 않고 다른 canonical writer나 새 유료 시험을 시작하면 안 된다.
3. canonical writer가 정상 복귀한 뒤 [격리 진단 패치](../isolated-count-diagnostics-20261026/REPORT-ko.md)를 base hash 대조 후 검토할 수 있다. 패치는 미적용이며 과거 오류를 소급 복구하지 않는다. 통합 자체를 provider 재시도 승인으로 간주하지 않는다.
4. 세션 복구와 trial count 실패는 별도 문제로 기록한다. 화면 접근 제한을 해결하지 못했다는 이유로 사용자의 잘못된 설정이나 보이지 않는 승인 창을 원인으로 제시하지 않는다.

## 등록부 연결

[OMISSION-REGISTER](../OMISSION-REGISTER.md)의 **OM-09/10/11**에 연결할 독립 진단이다. 등록부와 canonical PLAN은 이번에 변경하지 않았다. 권장 문구:

> 17:32 UTC 공식 조회: 기본 구현 turn은 inProgress, 반환된 마지막 tool은 completed. trial은 15:51:35 blocked_before_message/messages=0로 저장됨. CUA Codex 앱 접근은 안전 제한으로 거부되어 화면·대기 원인은 미확인. 재개·취소·유료 재시도 0회. [진단](stalled-primary-session-diagnosis-20261026/REPORT-ko.md).

## 증거와 무변경 범위

`evidence.json`은 공식 조회의 필요한 상태·마지막 항목과 도구 결과를 보존한다. `file-manifest.json`은 읽은 trial artifacts, 등록부 및 기존 진단 patch base 파일의 hash/mtime를 담는다. 키·credentials·.env·live DB는 열지 않았다. 코드·서버·계정·브라우저 설정·사용자 작업 변경 없음. 진단 보고서 3개 파일만 새 QA 폴더에 작성했다.

