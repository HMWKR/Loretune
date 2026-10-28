### K.1 CC01/P2 — 8-turn 밖 요청 제약 보존과 대화 범위

**관측과 현재 상태:** [독립 감사](../independent-claude-context-prompt-audit-20261026/REPORT-ko.md), [원 반례](../independent-claude-context-prompt-audit-20261026/offline-results.json). 첫 대화의 “이번 세션 카메라 회전 금지”가 DB에 남아도 9개 대화 뒤 다음 전송에서 빠진다. `chat_runtime.py:132,143–145`가 최근8개만 포함하고 별도 요청 제약 채널이 없다. 앱 문맥 누락 P2이며 Claude 자체의 기억 실패가 아니다. 감사 fixture4PASS/1FAIL,기존69PASS와편집4PASS는 별도 실행이다. 같은 작품의 독립 session은 미구현이며 작품 간 정보 유출과 다르다. 이번 계획 반영에서 코드 수정·테스트 재실행·외부 호출0.

|대안|장점|선택 판단|
|---|---|---|
|8개를32개 등으로 확대|매우 작은 수정|누락 시점만 늦춤. 근본 수용 기준을 충족하지 않아 제외|
|LLM이 전체 대화를 요약해 계속 덮어쓰기|입력량 감소|누락·반전·출처 소실·잘못된 제약 고정 가능. 추가 호출·품질평가 필요; 이번 최소 수정의 기준 데이터로 삼지 않음|
|서버의 대화별 사용자 요청 이력과 버전/출처 + 명시적으로 관리하는 제약|모델 기억에 의존하지 않고 재개/정정/해제를 재현 가능|**채택 제안.** 기존 chat 저장·scope·정식 ontology 읽기·proposal 검증 패턴 재사용. 별도 범용 agent/graph framework는 도입하지 않음|

**첫 구현 묶음의 경계:** 최근8개 assistant/user 왕복은 읽기 편한 recent context로 유지하되, 오래된 사용자 요청을 조용히 버리지 않는 별도 `session_request_history`를 전달한다. 모든 사용자 발화를 자동 “활성 명령”으로 확정하지 않는다. 원문·순서·출처는 보존하고, 자연어의 모호한 정정/해제는 모델 해석 품질 검증 대상으로 남긴다. 모델이 추출한 구조화 제약은 후보이며 user instruction을 IP의 승인 사실로 승격하는 경로가 아니다. 자동 요약을 필수로 만들지 않고 먼저 결정적인 CC01 누락을 닫는다.

제안 context schema v1: `workspace_id/project_id/conversation_id/context_revision`, 순서가 명시된 `requests[{turn_id,sequence,text,source_hash}]`, `constraints[{id,revision,text,source_turn_id,source_excerpt,scope,status,supersedes}]`, `canonical_revision`, `handoff_hash`. ID/해시는 모델용 내부 문맥/진단이며 일반 UI에 노출하지 않는다. 정식 ontology의 안정 ID·승인·provenance는 기존 채널을 그대로 쓴다. 세션 요청은 `canonical_approved:false`, scope는 해당 대화로 제한한다.

- 기존 `chat_turns`의 원문/행은 보존한다. 신규 대화 ID를 명시하고 query를 workspace+project+conversation으로 한정하며 순서를 안정화한다. 기존 `song,prompt` 호출은 해당 작품의 호환 default 대화로 매핑한다. 자연어 “새 대화”만으로 몰래 이력을 삭제하지 않고 명시적 새 대화 경로가 필요하다. 모델 교체는 같은 대화와 승인된 media job을 유지한다.
- 직접 사용자가 등록·정정·해제한 제약만 active 상태를 바꾸는 서버 명령으로 취급한다. 자연어에서 모델이 추출한 제약은 `proposed/uncertain` 상태이며 실행 권한이 아니다. 인용문/예시/타인의 요청을 자동 고정하지 않는다. 상태는 proposed/active/superseded/removed로 구분하며 removed는 tombstone과 provenance를 남겨 재개 때 되살아나지 않게 한다.
- 모순은 마지막 문장의 단순 lexical 매칭으로 덮지 않는다. 명시적 수정 대상과 scope가 일치하면 새 revision으로 교체하고, 애매하면 충돌 표시/확인으로 남긴다. 세션 해제는 IP 승인 사실을 삭제하지 않으며 새 대화도 IP 사실은 유지한다.
- 요청 이력+활성 제약+도구 schema가 사전 입력 한도를 넘으면 **실제 메시지 호출 전에 중단**한다. 필요한 일부 이력을 몰래 누락하거나 요약 성공으로 표시하지 않는다. 사용자에게 범위를 줄이거나 확인된 요약을 만드는 후속 선택지를 설명한다. 전체 원문이 무제한으로 매 요청 전달된다는 약속은 하지 않는다.
- 기존 pending/running/unknown 대화·작업은 바꾸지 않는다. enqueue 당시 context revision/hash와 실행 직전 상태를 비교하고 stale이면 재검토한다. 같은프로젝트 새대화가 기존유료작업을복제하거나 media approval을채팅history만으로무효화하지않는다.

**예상 파일:** `chat_runtime.py`(저장 scope/handoff/사전한도), `chat_protocols.py`(정규화 context), `production_context.py`(현재대화와정식문맥분리), `app.py`(동일Store요청검증/조회), 필요한 최소 UI context 표시와 새대화/제약 관리 hook, 관련tests. 적용 전 실제 API 의존성을 검사하며 저장소 전체 migration/rewrite는 하지 않는다. `model_selection.media_snapshot`·fal비용/승인계약·renderer는 이 묶음의 변경 대상이 아니다.

**합격 기준/회귀:** (1)원 CC01의9중립turn+Store재열기 후 금지 원문·출처가 정확히전달됨 (2)최근8turn 정상·동일revision legitimatejob변화 유지 (3)같은작품의대화A/B·작품A/B canary격리 (4)session금지와정식ontology는별도,새대화는session만분리 (5)명시적정정·부분해제·전체해제·해제후재시작에서옛제약부활0 (6)인용/예시/조건부/모순을active로거짓확정0 (7)stale context·중복update·권한가짜actor·다른대화target거부 (8)한도초과시modelMessages0·불명예약보존 (9)모델교체에canonical/진행job·source/audio/captions불변 (10)사용자승인없이제약을IPfact로적용0. 원 반례와기존69/편집4에서관련범위를먼저실행후전체회귀. 대화세션 UI는새동작을실제로제공할때만지원표시한다.

**수정 후 실제 Claude 시험:** 원 CC01의9개중립대화는offline으로준비하고수정된body에금지가포함된것을확인하므로9회유료대화는불필요하다. [독립 LIVE-PLAN](../independent-claude-context-prompt-audit-20261026/LIVE-PLAN.md)의4logicalturn에 장기제약·정정/해제·latestcanon·unknown·작품격리를배치한다. 각turn최대4Messages,입력16,384/출력8,192,실메시지총16회/사전count최대16회,stage예약$0.10; 자동재시도/fallback0. motion저작1회는별도$0.01,합계예약$0.11. 기존output2048이truncation됐던실제이력이있어독립제안의작은cap을그대로강제하지않고8192상한을선택한다. 대부분대화가더일찍완료되면남은횟수를채우지않는다.

부모가현재공식Haiku5.5가격을재확인했다: <=100k input에서$0.10/MTok input,$0.50/MTok output. [공식근거](https://platform.claude.com/docs/en/models/haiku-5-5/overview). 위한도는1response$0.0057344,16회$0.0917504이며계정가용성/실청구확인은별도다. 첫단계fail/truncation/unknown이면자동repair호출을하지않고원인보고. 실제LLM응답의금지/해제/최신설정을문맥과대조하며문자포함만으로pass하지않는다. fal은실제작성prompt를받는fake전송만사용하고승인전action준비와실submit/완료를구분한다. 실행전원장재조회/원자예약,공식인증·합성입력범위확인;현재실행보류.

**CLI/REA 상태 보존:** 독립감사의 `codex mcp list --json` metadata projection은 `rea enabled=true,stdio` 등록을확인했다. tools/list·서버연결·Remotion분석이성공했다는뜻은아니다. 기존사설소스검토거절은별개의미실행건이며새public-source조사로몰래치환해재시도하지않는다. 기존거절의provider/실host미관측·원명령미보존이라는한계를유지한다. REA의새공개소스분석에필요한최소입력과정확한수신처는해당별도조사에서확정한다.

