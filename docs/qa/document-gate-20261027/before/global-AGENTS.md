# Codex 글로벌 지침 (CE v2.0 최적화)

> 모든 프로젝트 공통. 프로젝트별 지침은 각 `AGENTS.md`를 우선한다.
> 개인 스킬 위치: `~/.agents/skills`
> Codex 설정 위치: `~/.codex`

## CE 원칙

- **적정 고도**: 너무 추상적이지도, 너무 구체적이지도 않은 수준으로 지시를 유지한다.
- **토큰 위치**: 중요한 지시는 문서 상단과 마지막 요약 위치에 둔다.
- **신호 대 잡음비**: 행동 변화에 기여하지 않는 중복과 장식 문구를 제거한다.
- **4대 실패 모드 방지**: Poisoning, Distraction, Confusion, Clash를 항상 점검한다.
- **Progressive Disclosure**: 상세 절차는 `~/.agents/skills/_core/`와 `~/.codex/rules/`로 분리한다.

## 언어

- 기본 출력은 한국어로 한다.
- 기술문서 스타일을 유지하되, 필요한 설명만 명확하고 간결하게 쓴다.

## Codex Question Gate Fallback

- Codex 스킬이 Question Gate에 도달했는데 `request_user_input` 도구가 현재 모드에서 unavailable이면, 이 환경에서는 사용자가 텍스트 fallback을 전역 허용한 것으로 본다.
- 이미 전역/세션 fallback 허용이 존재하므로 fallback permission을 다시 요청하지 말고 곧장 blocking `Text fallback Question Gate`를 연다.
- fallback gate에서도 추천 경로는 `(Recommended)`로 표시하고, 사용자의 응답 전에는 다음 단계, 파일 쓰기, 외부 서비스 호출, destructive action, production change, real sub-agent execution을 진행하지 않는다.
- `request_user_input`이 available인 모드에서는 반드시 도구를 우선 사용한다.

## Claude-to-Codex Runtime Porting

- Claude-origin skill/command를 가져올 때 `AskUserQuestion`, `"맞나요?"`, `Confirmation Loop`는 Codex Question Gate로 변환한다.
- Claude에서 자연어 확인이 잘 동작했더라도 Codex Default mode에서는 `request_user_input`이 unavailable일 수 있으므로 task/thread/session/global fallback 허용 규칙을 같이 적용한다.
- Browser Use namespace가 직접 노출되지 않으면 Computer Use나 scripted browser automation을 browser-capable fallback으로 본다.
- Claude의 `Task`/`Agent`/`Agent Teams` 표현은 그 자체로 Codex `spawn_agent` 실행 허가가 아니다. 실제 spawn은 사용자가 sub-agent, 병렬, 위임, Agent Teams 실행을 명시하고 Q4 gate 또는 해당 실행 승인 조건이 충족된 경우에만 한다.

## Expert Methodology Research Hook

- 전문가, AI 전문가, 부서, Worker/Evaluator, Agent Teams를 매핑할 때는 역할명을 먼저 확정하지 않는다. 각 후보 전문가/부서가 실제 현업에서 쓰는 방법론, 표준, 프레임워크를 먼저 조사하고 분석한다.
- 조사 우선순위는 프로젝트 내부 문서와 공식/1차 문서, 표준 문서, 권위 있는 핸드북/논문/벤더 문서, 필요한 경우 웹 검색 순서다. 출처가 불명확하면 `[추정]`으로 표시하고 확정 방법론처럼 쓰지 않는다.
- Agent Execution Plan과 sub-agent 프롬프트에는 `Methodology sources`, `Applied methodology`, `Non-goals/limits`, `Verification standard`를 포함한다.
- 전문가 매핑 후에는 "이 전문가가 어떤 실제 방법론으로 사고하고 검증하는가?"가 답해지기 전까지 실행 프롬프트, 부서 설계, spawn 계획으로 넘어가지 않는다.

## 세션 연속성

- 멀티세션 작업은 `checkpoint.md` 또는 `session-handoff.md`를 먼저 확인한다.
- 3단계 이상 작업은 진행 상태를 명시적으로 관리하고, 완료 시 임시 handoff를 정리한다.
- 프로젝트 checkpoint를 자동으로 덮어쓰지 않는다. 연결된 lifecycle 훅은 Codex 소유 경로에 handoff snapshot을 저장하도록 구성하며, 실제 훅 전달·저장은 별도 검증한다. 작업별 인계 문서는 현재 상태로 명시적으로 갱신한다.

## 코드 작성

- 기존 구조와 스타일을 우선한다.
- 파일/심볼/라인을 언급하기 전 실제 파일을 확인한다.
- Magic Number를 피하고, 입력 검증과 호환성 영향을 함께 본다.
- 새 추상화는 중복 감소나 복잡도 축소가 명확할 때만 추가한다.

## 서브에이전트

- 위임이 승인된 복합 작업은 현재 목록의 `harness-orchestration:orchestrate`를 읽고 작업 계약·세션별 도구 능력·분야별 검증·결과 수락 절차를 적용한다. 스킬 존재만으로 실제 spawn을 승인하지 않는다.
- 위임 전에 worker의 소유 범위와 런타임이 요구하는 증거 경로를 맞춘다. 완료 보고, driver 수락, 종료 훅 결과는 별도로 기록한다.
- 소스 코드 대량 탐색은 가능한 경우 `explorer` 또는 Codex custom agent에 위임한다.
- 직접 읽기 허용: `AGENTS.md`, `session-handoff.md`, `package.json`, 설정 파일, 짧은 문서.
- 위임 결과는 사실 요약으로 받고, 구현 판단은 현재 작업 맥락에서 통합한다.

<!-- ARCHITECT_AGENT_EXECUTION_START -->

## Architect Agent Execution

- `architect`가 생성한 `AGENTS.md`, `.codex/agents/*`, `.codex/rules/*`, `session-handoff.md`는 설명용 조직도가 아니라 실제 실행 조직 신호다.
- architect 신호가 2개 이상이면 Architect Agent Execution Mode로 보고, 사용자가 에이전트/병렬/위임/harness-loop/Agent Teams/worker/evaluator 실행을 명시한 경우 실제 `spawn_agent` 실행 계획을 세운다.
- 명시 의도가 없으면 logical mapping으로 대체하지 말고 "실제 sub-agent 병렬 실행으로 진행할까요, 아니면 Lead 단독으로 진행할까요?"라고 묻는다.
- 실행 전 Agent Execution Plan에 `Agent`, `Role`, `Methodology sources`, `Applied methodology`, `Model`, `Reasoning`, `Scope`, `Write set`, `Verification`, `Dependency`를 적고 Worker write set은 겹치지 않게 한다.
- 실제 Worker/Evaluator는 현재 런타임에서 지원되는 모델·reasoning을 사용한다. 모델 미지정 시 세션 설정을 상속하고, 사용자가 모델을 지정했는데 지원되지 않으면 조용히 대체하지 않고 사유를 보고한다.
- 상세 절차는 `~/.codex/rules/architect-agent-execution.md`, `~/.agents/skills/harness-loop/SKILL.md`, `~/.agents/skills/architect/SKILL.md`를 따른다.

<!-- ARCHITECT_AGENT_EXECUTION_END -->

<!-- SUPABASE_PROJECT_MCP_START -->

## Project-scoped Supabase MCP

- Supabase MCP는 전역 `supabase` 하나로 여러 프로젝트를 섞어 쓰지 않는다.
- Supabase가 필요한 프로젝트는 `project_ref`가 포함된 별도 MCP server entry를 사용한다. 서버명은 `supabase-<project-slug>[-<env>]` 형식이다.
- 첫 연결은 기본 `read_only=true`와 `features=database,docs`로 시작한다. write access는 schema/migration/storage/auth 영향과 rollback 계획을 확인한 뒤 별도로 승인받는다.
- Supabase 작업 전 프로젝트명, 환경(dev/staging/prod), `project_ref`, feature scope, 기존 MCP 등록 여부를 확인한다.
- Supabase command/MCP 호출 전에는 현재 cwd의 `.codex/supabase-active-target.json`이 가리키는 active target을 확인한다.
- read-only mode에서는 조회만 허용하고, write-risk 작업은 write mode와 write-access MCP 설정이 둘 다 명시된 경우에만 진행한다.
- 상세 절차는 `~/.codex/rules/supabase-project-mcp.md`와 repo의 `docs/supabase-project-mcp-policy.md`를 따른다.

<!-- SUPABASE_PROJECT_MCP_END -->










## 문제 해결

1. 목표를 한 문장으로 재정의한다.
2. 현재 상태와 실패 조건을 실제 파일/로그로 확인한다.
3. 원인을 좁히고, 대안 2개 이상을 비교한다.
4. 승인된 범위 안에서 구현하고 검증한다.
5. 남은 리스크와 후속 작업을 짧게 기록한다.

## 리뷰/테스트/보안

- 리뷰: 정확성, 예외처리, 가독성, 중복, 보안, 성능, 확장성 순서로 본다.
- 테스트: 정상/예외/경계값과 Mock 필요성을 판단한다.
- 보안: 파괴적 명령, 민감정보, 외부 서비스 호출은 사전 확인한다.

## 커밋 메시지

필수 섹션:

```text
## What
## Why
## Impact
Co-Authored-By:
```

## 참조

- 공통 프로토콜: `~/.agents/skills/_core/protocols.md`
- 전문가 역할: `~/.agents/skills/_core/roles.md`
- 안전 규칙: `~/.codex/rules/safety.md`
- 환각 방지: `~/.codex/rules/anti-hallucination.md`

<!-- CANTOS_SECTION_START -->

## Cantos Project (auto-synced concise — DO NOT EDIT)

> Generated by `cantos/_system/scripts/sync-cantos-section-to-codex-agents-md.mjs`
> Source-of-Truth: `cantos/.claude/agents/*.md` + `cantos/.claude/rules/dual-harness.md`
> 본 절 직접 수정 금지. cantos 변경 시 sync 스크립트 재실행으로만 갱신.

### Runtime Rules

- Cantos root: `/Users/leesungmin/Desktop/cantos`.
- Engine-agnostic: supported engines call the same Cantos MCP and write to the same Cantos store without hierarchy.
- Workflow: map request keyword → read `cantos/.claude/agents/<name>.md` or `~/.codex/agents/cantos-<name>.md` → perform the persona directly, not by implicit spawn → record insights in `cantos/docs/domain-knowledge/<name>-insights.md`.
- MCP tools: `mcp__cantos__create_adr`, `create_ddr`, `register_project`, `capture_visual`, `list_projects`; path validation must keep writes inside Cantos.
- Agent matrix: do not inline it here. Read `cantos/.claude/rules/agent-matrix.md` or the mirrored `~/.codex/agents/cantos-*.md` only when a Cantos task needs it.
- Iron Law: preserve immutability, insight isolation, provenance metadata, cross-project portability, and visual verification.
- Core rules: `dual-harness.md`, `agent-matrix.md`, `insight-isolation.md`, `immutability.md`, `narrative-rules.md`, `living-addendum.md`, `visual-verification.md`.

<!-- CANTOS_SECTION_END -->

## Codex 독립 하네스 실행

- 작업별 절차 선택·실패 복구·효과 비교는 `~/.codex/rules/harness-execution-policy.md`를 따른다. 작은 작업은 기본 흐름으로 수행하고 복합 작업에서도 여러 계획·반복 절차를 자동 중첩하지 않는다.

- 사용자 지시와 현재 런타임 규칙을 우선한다. 원본 Claude 설정·공유 스킬·공유 의존성은 이식본의 갱신 대상으로 사용하지 않는다.
- 추가 기능은 `codex-harness` 마켓플레이스의 `harness-*` 패키지로 격리한다. 기존 Codex MCP·플러그인·스킬을 보존한다.
- 명시 호출은 현재 목록의 정확한 스킬 이름을 우선한다. Claude의 `/command`는 대응표의 Codex 스킬로 해석하고, 동명 스킬을 경로 확인 없이 대체하지 않는다.
- 자연어 라우터는 관련 후보만 제안한다. 수동 전용 스킬은 자동 실행하지 않고, 목표 생성·실제 서브에이전트·외부 변경은 각각 현재 승인 범위를 확인한다.
- 모델명은 세션에서 상속한다. Claude의 Opus/Sonnet/Fable 처방을 GPT 모델의 능력이라고 간주하지 않는다. 사용 가능한 도구와 실제 검증 결과로 실행 경로를 결정한다.
- 복잡한 작업은 확인 가능한 체크리스트로 진행하고, 완료 전에 실제 실행·측정 증거를 확보한다. 반복 실패는 원인과 가설을 바꿔 조사한다.
- 이미지 제작은 현재 이미지 생성 도구, 코드 영상은 Remotion, 웹 모션은 웹 런타임 도구로 수행한다. Codex MCP 자기 호출이나 Claude 실행을 기본 경로로 만들지 않는다.
- 브라우저 작업 전 `~/.codex/rules/browser-tooling-policy.md`를 읽는다. 사용자 지정 → 프로젝트 규칙 → 충분한 전용 MCP → 작업 성격 순으로 선택한다. Aside는 탐색·맥락 기반 조사·별도 리뷰 위임, ego-lite는 Codex 직접 조작·문제 재현·수정 후 검증에 우선 사용한다. 각 스킬의 기본 브라우저 권고보다 이 선택 규칙을 우선하며 기존 Codex 도구는 보존한다.
- 디자인·리디자인·UI 패턴 조사에는 `~/.codex/rules/design-reference-policy.md`를 읽고 설치된 `refero-design` 스킬과 현재 Refero 도구를 연결한다. 사용자 시안·기존 디자인 시스템을 우선하며, 작은 수정은 기존 근거를 재사용한다. 참고 조사와 실제 화면 검증은 구분한다.
- bkit·Superpowers·Fablize는 기능 절차를 제공한다. 완료 판정은 실제 검증 증거에 따르고, 여러 Stop 훅이 서로 무한 재시도를 유발하지 않게 한다.
- REA로 배포 번들·앱 패키지·바이너리·웹 실행/네트워크 증거를 조사할 때 `~/.codex/rules/rea-analysis-policy.md`와 설치된 `reverse-engineer-anything` 스킬을 읽는다. 일반 소스 분석에는 기존 코드 도구를 사용한다. 대상 우선 선택, 요약 우선 조회, Evidence 재사용, 관측·추론·미확인 분리를 따른다. REA의 병렬 작업 권고는 실제 위임 승인을 대신하지 않는다.
- 에이전트 역할 문서를 읽었다는 사실은 실제 spawn이나 도구 접근 제한의 증거가 아니다. 검증자 읽기 전용 제한은 실제 런타임 설정으로 확인한다.
- 지식 vault와 메모리는 저장 요청·승인 범위 내에서만 변경한다. 프로젝트 등록, 외부 발송, 결제·배포를 스킬의 예시만으로 실행하지 않는다.
- 등록·활성화·인증·호출 성공·산출물 검증을 각각 기록한다. 누락된 도구, 미지원 이벤트, 인증 실패를 정상 완료로 표시하지 않는다.
