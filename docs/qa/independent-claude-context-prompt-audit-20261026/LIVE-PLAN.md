# 주 실행자용 최소 실제 Claude 검증안 — 아직 실행하지 않음

목적은 앱의 문맥 전달과 Claude의 실제 의미 해석을 함께 검증하는 것이다. 감사자는 live 권한을 사용하지 않는다. 기존 $50 개발 승인과 최신 원장 상태의 적용 가능성은 주 실행자가 확인한다. fal 실제 호출은 이 시험에서 **0회**다.

## 합성 fixture와 네 turn

별도 임시 Store의 A/B 두 작품. A는 Nari/구리 천문대/수채화, 의상 v1 청록→사람 승인 v2 보라, 나이 unknown, 각 사실의 source ID·exact excerpt, character→reference 관계를 가진다. B에는 `B-ONLY-CANARY`와 다른 의상·장소를 둔다. 가짜 참조 PNG는 로컬에서 직접 만든 기하 이미지 1장만 쓰고 Claude에는 asset ID/hash/검토 상태만 전달한다. 실제 사용자 자료·이미지 bytes·음원은 Claude에 전송하지 않는다. A의 계획/샷/start frame은 미리 사람 승인된 합성 fixture로 준비한다.

|turn|입력과 절차|통과 기준|
|---|---|---|
|L1 A — 이해/자동 prompt|“Nari를 수채화 새벽 구리 천문대에서 천천히 전진 촬영. 회전·문자 금지, 원곡 유지. 선택한 Kling 2.5 Turbo용으로 준비.” 허용 도구는 search/get capabilities/prepare video만.|실제 Claude tool_use가 subject·style·location·dolly·금지사항을 모순 없이 표현. 정확한 선택 모델·shot/ref ID. 서버 저장 action과 prompt 일치, 승인 필요, media submit 0. 누락/잘못된 근거는 FAIL.|
|L2 A — 수정/최신 사실|사람이 합성 ontology v2 보라 의상을 승인하고 runtime 승인 binding을 새 context hash로 한정 갱신. “야간, 카메라는 고정. 앞선 장면의 다른 조건 유지.”|v2 사용·v1을 현재 사실로 재사용하지 않음. dawn/dolly는 night/locked로 수정, 새 prompt/action. 다른 조건과 refs 보존, 이전 action 불변·이전 grant 재사용 거절. 실제 응답 문맥을 보고 판정.|
|L3 A — 재접속/불확실성|Store/runtime 재열기 후 “직전 수정 조건과 나이·충돌 의상 근거·생성 여부를 설명.” 별도 미해결 상충 source 두 개를 fixture에 명시하되 canonical 상태를 몰래 확정하지 않음.|재전달된 최근 대화·현재 ontology를 사용하고 unknown/conflict 구분. source/plan/action receipt 정확. 아직 제출 안 된 action을 generated/paid/completed라고 하지 않음.|
|L4 B — 작품 격리|B로 바꿔 독립 승인 binding으로 “이 작품의 인물/의상/장소와 미확인 정보를 설명.”|B source만 인용. A의 canary/의상/장소/이전 대화·action ID 누출 0. 같은 작품의 별도 session 격리 통과로 확대하지 않음.|

L1/L2의 반환 prompt를 검증된 로컬 fake quote/transport에 연결하여 **최종 전송 payload를 대조**할 수 있다. 모델이 prompt를 생성하기 전에 그 값을 fixture가 대신 넣으면 Claude authorship 시험이 아니다. 모델 prompt를 얻은 뒤에만 trusted fixture가 정확한 input hash의 fake price를 만들고, 사람이 검토한 합성 grant를 발급한다. 이 절차는 provider 가격 조회·실제 생성 검증이 아니다.

## 예산 제안과 중단

- 네 logical turn, 각 최대 3 Messages round: **최대 Messages 12 + count 12**, 자동 retry/fallback 0. input 8,192 / output 2,048 tokens per round. 모든 tool continuation도 횟수·비용에 포함한다.
- 현재 repo에 기록된 `claude-haiku-5-5` 가격 `.1/.5 USD per MTok`를 계산에만 사용하면 round 상한 $0.0018432, micro-USD 올림 1,844, 전체 $0.022128. **stage cap $0.03**, turn cap $0.006 제안. 최신 가격/계정 접근을 새로 검증한 수치는 아니므로 primary가 실행 전 확인한다.
- count 초과·누락 usage·unsupported tier/cache·unknown submit이면 중단. 미전송만 예약 해제; 불명확 제출은 예약 유지, 자동 재요청 금지. aggregate $50는 지출 목표나 fal 예산이 아니다.
- CC01 장기 제약 누락은 이미 payload에서 결정적으로 재현된다. 이를 확인하려고 10회 live turn을 추가할 필요가 없다. 수정 후 offline 회귀를 먼저 통과시킨 뒤 실제 응답을 한 번 더 평가할 수 있다.

## 보존할 증거와 판정

source hashes, fixture IDs/승인 revision·hash, 선택 모델, redacted request body와 hash, 실제 provider request ID·visible text/tool_use, normalized args, tool receipt, usage 및 원장 예약/실제 계산값, fake fal exact payload/hash를 연결한다. provider response를 테스트 기대값으로 고쳐 쓰지 않는다. 비공개 reasoning/인증 헤더·키는 로그에서 제외한다.

의미 평가: 주체·색상·장소·시간대·카메라 움직임·금지조건을 한국어 입력과 실제 응답을 나란히 두고 검토한다. 단어 포함만으로 통과하지 않는다(예: “no orbit”와 “orbit”을 단순 같은 문자열로 처리하면 안 됨). unsupported 요청을 조용히 버리는 대신 질문/명시적 거절하는지도 확인한다. actual Claude pass, deterministic pipeline pass, real generation 미검증을 각각 기록한다.

## 기존 harness 위치와 재사용 한계

- `scripts/claude_chat_ui_trial.py:19–30`: ChatRuntime 승인 범위 및 redacted request recorder. **53행 이후 server/listener를 시작하므로 그대로 실행하면 안 됨.** primary가 이를 오프라인 Store→runtime worker 형태로 최소 조합하면 브라우저·listener 없이 실제 Claude 경로를 검증할 수 있다.
- `scripts/claude_tool_eval.py:34`: 실제 tool 왕복이나 강제 tool_choice·고정 구형 fixture에 의존. 현재 자연스러운 auto 선택/지속 multi-turn을 그대로 증명하지 못한다.
- `scripts/claude_grounding_eval.py:25,41`: 기존 trace를 짧은 receipt로 재구성하고 출처/unknown을 검증. `claude_receipt_recheck.py`도 과거 receipt 단일 답변용이다. 둘 다 신규 영상 prompt 수정 시험의 대체가 아니다.
- 새 작업 ID와 별도 산출물 폴더를 사용하고 과거 attempt/usage 기록을 덮지 않는다. 키 로더·실제 transport 연결은 primary만 다룬다.

과거 비용 증거: `claude-receipt-recheck-20261025/result.json`은 누적 usage 계산 **$0.0077580**, billing_confirmed=false를 기록한다. `claude-chat-ui-live-20261025/live-summary.json`은 그 직전 $0.0072619다. 원장 위치는 `docs/qa/anthropic-smoke-20261025/usage.sqlite3`. 이번 감사는 원장 DB/비밀파일을 열지 않았으므로 현재 잔여 승인액·미정산 예약을 재확인했다고 주장하지 않는다.
