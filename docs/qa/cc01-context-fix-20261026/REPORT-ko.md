# Aethon CC01 수정과 실제 Claude 문맥·영상 프롬프트 검증

2026-10-26. **CC01의 앱 문맥 누락을 수정했고, 실제 Claude가 그 문맥을 조회해 프롬프트를 작성하는 경로까지 검증했다.** 모델이 영구 기억을 갖게 된 것이 아니다. Aethon이 DB에 보존한 요청과 현재 승인 온톨로지를 매 요청에 다시 제공한다. 실제 영상 생성·다운로드의 성공을 뜻하지 않는다.

**후속 정정/연결:** 독립 재검토는 원 CC01을 닫았고, 별도 CC02(최종 Messages 본문의 로컬 크기 거절을 결과 불명으로 오분류)를 발견했다. 이 문서의358회귀/source manifest는 당시 증거로 보존한다. [CC02의 현재 수정·365회귀·소스](../cc02-preflight-fix-20261026/REPORT-ko.md)가 후속 기준이다. 실제14응답의 output hash/usage는 독립 검증됐지만, 보존된 입력 중 **6/14만 전체 본문을 독립 재해시할 수 있고 8/14는 thinking 제거로 원 wire body 재구성이 제한**된다. 이 한계를 input hash가 기록돼 있다는 사실과 구분한다. [독립 증거 검토](../independent-cc01-fix-recheck-20261026/REPORT-ko.md). CC02에는 추가 실호출이 없다.

## 변경과 원인

1. `chat_runtime.py:46`의 `request_history`가 모든 접수된 사용자 요청을 저장 순서대로 전달한다. `schema_version`, workspace/project 범위, `project-default` 대화 범위, turn ID·sequence·원문·SHA256·처리 상태, 전체 digest를 포함한다. 최근 8개 완료 대화는 별도로 유지한다. 수정·해제·인용·조건문을 원문 순서대로 보존하며 자동 활성 제약이나 승인 IP 사실로 변환하지 않는다. 새 DB 테이블/migration/세션 UI는 없다.
2. 실제 왕복 사전검사에서 조회 결과가 추가되면 13–18KB로 커져 기존 추출 전용 12KB 전송 상한에 막히는 점을 발견했다. `anthropic_ontology.py`에 제한된 byte 상한 인자를 추가하고 채팅만 65,536bytes로 설정했다. 기본 추출 경로는 12,000bytes 그대로다. count 결과의 입력 토큰·출력 상한·원자 비용 예약은 별도이며 넘으면 Messages 이전에 중단한다. 기록을 조용히 잘라내지 않는다.
3. 초기 실제 답변에서 원곡/생성음원, 온톨로지/장면/실행/최종출력 승인의 의미가 섞였다. `chat_models.py`의 모델 지침에 서버가 실제로 보장하는 구분을 명시했다. legacy `approved_shots`는 승인 증명이 아닌 장면 목록이다. 승인 handle은 원래 입력에 대한 제한된 승인 기록이며 현재 실행 가능성과 최종 출력 승인은 별도다. `generate_audio=false`는 원곡을 삭제하지 않는다. 기존 승인 검사나 데이터는 변경하지 않았다.

변경 제품 파일은 `chat_runtime.py`, `chat_models.py`, `anthropic_ontology.py` 3개다. 새 테스트 `tests/test_chat_request_history.py`, 확장 테스트 `tests/test_anthropic_transport.py`; 실행기 `scripts/cc01_context_trial.py`, `scripts/cc01_context_followup.py`는 합성 검증 전용이다. UI/app/미디어 JS/CSS/정규화 protocol은 기준선과 byte 동일하다. [diff와 기준선](baseline.json), [최종 해시](FINAL-MANIFEST.json).

## 오프라인·회귀 결과

|검사|결과와 증거|판정 범위|
|---|---|---|
|원 CC01 9턴 반례 + Store 재열기|수정 전 FAIL → 수정 후 PASS. [수정 전](before-counterexample.log), [회귀](targeted.log)|첫 요청이 DB에만 남던 누락을 모델 요청까지 보존|
|새 요청 이력 검사 7개|PASS|순서·해시·scope, quote/conditional/correction/retraction 원문, 처리상태, assistant 비승격, 타 프로젝트 제외, queued snapshot 고정, 한도 초과 Messages 0, 별도 세션 미지원 명시|
|관련 실행/도구 48개|수정 후 PASS, 의미 지침 보강 후 다시 PASS. [로그](domain-targeted.log)|후속 전체검사에 포함; 합산하지 않음|
|전송 경계 12개|PASS. [로그](transport-regression.log)|기본 12KB·채팅 64KB·상한 초과 전송 0, 고정 endpoint, TLS/redirect/proxy/timeout/secret-canary 기존 회귀|
|최종 전체 회귀|**358/358 PASS, 44.960초**, 한 실행. **338 비HTTP + 20 HTTP**. [로그](final-regression.log)|기존350 + 요청이력7 + 전송1. Node 내부 시나리오 중복 집계 없음|

첫 전체 실행의 20개 HTTP 검사는 sandbox의 `Operation not permitted`로 bind 단계에서 실행되지 않았다. 이를 통과로 세지 않았다. 기존 승인된 localhost 시험을 정식 `require_escalated` 경로로 실행한 뒤 전체358이 통과했다. 실패 로그와 재실행 로그를 모두 보존했다. 외부 제공자 없이 임시 데이터/서버를 사용하는 테스트다.

## 실제 Claude 시험: 초기 오류와 후속 수정 분리

모델은 `claude-haiku-5-5`. 실제 `count_tokens → Messages → tool_use → Store 도구 → tool_result → 최종 답변`을 사용했다. 새 합성 A/B 프로젝트만 사용했고, 처음 9개의 중립 대화는 오프라인으로 준비했다. Claude에는 소스코드·고객 자료를 전송하지 않았다. 영상 시작 프레임은 합성 32×32 PNG이고 fal 요청은 비통신 fake다.

|실행|확인된 결과|초기 한계/후속 판정|
|---|---|---|
|L1 오래된 요청 + 영상 프롬프트|최근8개 밖 `SESSION-LONG-913`의 회전 금지·전진 돌리·레터링 금지를 반영. 실제 Claude가 영어 프롬프트 작성, 승인된 teal/copper/watercolor 및 unknown age 구분. 조회→제안→답변 3응답 완료|원곡과 `generate_audio=false`를 충돌처럼 설명한 오류 발견|
|L2 명시 해제·정정 + 새 프롬프트|slow clockwise orbit로 변경, 이전 제안 보존. 인용된 “add a title”과 미승인 조건부 fast spin을 실행 지시로 적용하지 않음. 3응답 완료|같은 원곡 설명 오류가 반복됨|
|L3 재시작 + 승인 사실 정정|Store 재열기 후 canonical revision2/violet/`synthetic-A-v2`를 사용. 이전 assistant의 teal을 최신 사실로 사용하지 않음. 해제된 orbit 금지 부활 없음. 2응답 완료|기존 grant 기록을 승인 기록이 아닌 것처럼 설명하고 과거 제안 상태를 반복한 오류 발견|
|L4 다른 작품 격리|B의 saffron/underwater/`synthetic-B-v1`, 나이·카메라 unknown. A 요청·사실은 전송 payload에 없음. 2응답 완료|빈 장면 목록을 온톨로지 승인 부재로 잘못 해석|
|S1 의미 지침 보강 후 A 재조회|기존 grant=원래 입력의 제한된 승인, 현재 실행 재검사·최종 출력 승인과 구분. 원곡과 생성 오디오 비활성화가 충돌하지 않음을 설명. 2응답 완료|실제 생성 완료나 최종 승인을 주장하지 않음. 현재 조회에 없는 옵션값은 검증 못했다고 표시|
|S2 의미 지침 보강 후 B 재조회|revision1은 사람이 적용한 정식 버전이며 빈 장면 목록과 별개라고 설명. 이전 승인 부재 답변의 오류를 직접 정정. 2응답 완료|다른 작품 정보 사용·변경 없음|

초기 4개는 **프로토콜/저장 경로 완료**이며 답변 전체 무결함 통과가 아니었다. 후속2개로 발견한 의미 오류의 좁은 수정만 확인했다. 자유로운 모든 대화·모순·언어·장기 문맥의 품질을 보장하지 않는다. 원 응답은 [live](live/), 보강 후 응답은 [semantic-followup](semantic-followup/)에 별도로 보존한다.

### 실제 모델 저작 → 선택 fal 계약의 경계

L1/L2의 model tool arguments에서 저장된 action prompt와 fake fal POST 본문 prompt가 정확히 같다. 선택 모델은 `fal-kling-2-5-turbo` → `fal-ai/kling-video/v2.5-turbo/pro/image-to-video`이며 duration5, 승인된 start frame의 검증된 로컬 bytes를 사용한다. 다른 모델로 대체하지 않았다.

- action 준비까지 provider submit 0. 잘못된 grant로 실행하면 차단.
- 합성 시험의 사람 역할 controller가 정확한 action/input/가격/출력정책을 승인한 뒤 실제 queue/admission/submit 코드에 fake transport를 주입했다.
- 각 action 1회씩 fake submit, 동일 action 재요청은 같은 job으로 반환. 이전 prompt/action 보존.
- **실제 fal 네트워크·유료 영상 생성·다운로드·새 Take 등록 0회.** accepted는 완료 영상이 아니다. 기존403 결과를 재접근하지 않았다.
- 후속 조회2건은 action/grant/job/ontology version 개수를 바꾸지 않았다. [DB 경계](semantic-followup/write-boundary.json), [L1 payload 증거](live/case-1/fake-fal-evidence.json), [L2](live/case-2/fake-fal-evidence.json).

## 비용·출처·정리

[공식 Haiku 가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview)을 실행 전에 재확인했다. 100k 이하 입력 $0.10/MTok, 출력 $0.50/MTok. 이번 개별 최대 counted input은 **14,016**, 상한은16,384; 출력 상한8,192. cache/batch/fallback/retry는 사용하지 않았다.

- 실제 count14회 / Messages14회, 고유 request ID14개, 입력94,603 + 출력10,547 tokens(요청별 합계).
- 초기4개 $0.0101411 + 의미 후속2개 $0.0045927 = **이번 $0.0147338**.
- 기존 $0.0077580 포함 **누적 usage 가격 계산 $0.0224918**. 원장의 반올림·보수적 예약 포함 합계 **$0.022503**. **invoice/실청구는 미확인**이다.
- 원자 예약은 기존 누적$50 및 이번 stage$0.10 상한 아래에서 동작했다. 사용자가 허용한 이번 추가$1보다 작은 한도다. 남은 예산을 채우기 위한 호출 없음.
- 실제 request ID·input/output hash·usage는 [provider-provenance.json](provider-provenance.json). 예: L1 조회 `req_011CgR2eFSFGzm4zTLcQM65k`, L1 제안 `req_011CgR2fBRB3zxvRtCA7xHMA`, S2 최종 `req_011CgR342cjmWnpy1gHj2J3J`.
- 키는 기존 loader의 메모리 인증용으로만 사용했다. 로그/화면/새 키 파일을 만들지 않았고, 저장 JSON에 인증 header나 private thinking block이 없는지 검사했다. 원문 private reasoning을 저장하지 않았다.
- live 시험에는 listener/백그라운드worker가 없었다. 두 live 프로세스와 회귀 실행은 종료됐고 제품 서버를 새로 띄우지 않았다. 합성 데이터 디렉터리는 [fixture.json](live/fixture.json)에 기록되어 있고 원본 검증용으로 보존했다. 공유 QA/사용자 DB는 이번 시험 대상으로 열거나 수정하지 않았다.

## 남은 범위

동일 작품 안의 독립 채팅 세션/새 대화 UI는 아직 없다. 현재 범위는 `project-default` 대화다. 요청이 길어져 byte/token 상한을 넘으면 중단하며 자동 요약·무한 기억을 제공하지 않는다. 구조화 활성 제약 관리나 자연어 의미의 결정적 판정도 구현하지 않았다.

이번에는 브라우저 UI 재검증을 하지 않았다. UI 파일은 이전 고정본과 동일하다. 실제 OpenAI/Grok 교체 품질, fal 영상 결과 수집/권한403 해결, 실제 음악 포함 출력까지의 새로운 외부 생성 E2E는 이 시험으로 통과시키지 않는다. 이질 데이터 수집/온톨로지 자동 진화와 Blender 모델화는 계획만 유지한다. native motion/Remotion/편집 확장, CLI source-review와 Library 업로드를 실행하지 않았다.

현재 로컬 변경·검증에 실행 차단은 없다. 다음 진행은 위 잔여 범위를 별도 계획/권한과 실제 검증으로 다뤄야 한다. [단일 계획 K.1](../codex-cli-assessment-20261026/PLAN-ko.md), [최종 manifest](FINAL-MANIFEST.json).
