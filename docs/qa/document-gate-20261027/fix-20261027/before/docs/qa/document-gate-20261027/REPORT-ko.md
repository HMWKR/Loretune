# Aethon 문서 완료 검사 · 전역 적용 결과

2026-10-27 UTC. 제품 세션 구현은 중단 상태로 보존했다. 이번 범위는 문서 관리 검사와 사용자 요청의 비보안 전역 지침이다. 제품 코드, 실제 registry, 생성 문맥, 공유 DB, API 키/인증, 공급자, Git hooksPath, native hook trust를 변경하지 않았다.

## 결과와 실제 적용 범위

- **전역 적용 완료:** `~/.agents/skills/document-completion-gate/{SKILL.md,check.py}` 및 `~/.codex/AGENTS.md`의 `DOCUMENT_COMPLETION_GATE_V1` 블록. 기존 AGENTS 전체 bytes + 추가 블록만 이어 붙였음을 검사했다. 파일 hash는 `GLOBAL-APPLIED.json`.
- **프로젝트 설정 완료:** 루트 `.document-gate.json`. 전역 공통 엔진은 프로젝트별 선언형 JSON만 읽는다. 새 정책/registry를 다른 프로젝트에 자동 생성하지 않는다. 임의 shell command·로컬 코드 import·네트워크·파일 쓰기 기능이 없다.
- **자동 native Stop 훅은 미적용/신뢰 대기:** `hooks.candidate.json`은 기존 훅 객체를 보존한 검토용 합성본이다. 현재 `~/.codex/hooks.json` bytes는 그대로다. 새/변경 native 훅은 exact definition hash 신뢰 검토 전에는 실행되지 않는다. 신뢰/보안 설정을 우회하지 않았다. 실제 lifecycle dispatch 시험도 하지 않았다.
- **기계적 검사:** 선언 범위 미완료는 CLI exit 1, 정책/경로 실패는 3, 정책 없음은 2, 통과만 0. CI가 이 종료코드를 의존하도록 연결하면 해당 검사 단계는 실패할 수 있으나, 이번에는 CI/Git 훅을 설치하지 않았다. 이 폴더는 Git 저장소가 아니다.
- **지침 수준:** AGENTS/스킬은 모델에게 실행을 요구하는 지원 지침이며 자동 실행의 절대 보장은 아니다. 새 세션에서 발견되는 공식 위치에 저장했지만 별도 모델 호출로 자동 선택 여부를 검증하지 않았다.

## 왜 이 구조인가

실수는 파일·링크 검사와 registry 편입을 같은 완료로 취급한 데 있었다. 공통 엔진은 ① 문서 발견 ② 명시 분류 ③ 필요한 등록의 실제 membership ④ 원본/등록 사본 hash ⑤ context receipt와 registry/head/출력 hash ⑥ 해당 결과의 evidence digest를 연결한다. 자동 등록/승격/내용 추론은 하지 않는다.

Aethon 규칙을 다른 프로젝트에 강요하지 않는다. 가장 가까운 정책을 사용하되 중첩 Git/worktree는 별도 경계다. 정책이 없는 프로젝트는 `not-configured`와 설정 안내만 반환한다. 읽기 전용이라 상태 파일을 프로젝트 간 공유하지 않는다. 정책에는 실제 project ID, registry별 base/path/identity, 문서별 classification/registration/rationale, 필요한 등록 대상, context 사용 구분, scan/exclude를 선언한다. 임의 command 키는 거절한다.

원본/역사 문서는 baseline hash로 보존하고 자동 canonical 승격하지 않는다. 이번 목록에 있던 미결정 문서는 `legacy-review-pending`으로 남긴다. 수정되면 재분류 필요가 발생하고, 기존 pending 자체도 pass로 표현하지 않는다. 새 MD가 생기면 명시 분류 전 `UNCLASSIFIED_DOCUMENT`로 차단한다. 정책을 통과용으로 완화하는 행위는 의미 검증으로 인정하지 않는다.

## 공식 지원 확인

1. 로컬 `/opt/homebrew/bin/codex --version`: **codex-cli 0.164.0**. `--help`, `debug --help`, `app-server --help`, `app-server generate-json-schema --help`, `features list`를 실행했다. `hooks stable true`와 hook trust 우회 옵션의 존재를 확인했으나 우회 옵션은 사용하지 않았다. PATH alias 생성 경고가 있었지만 도움말/스키마 명령은 exit 0이었다.
2. `codex app-server generate-json-schema --out docs/qa/document-gate-20261027/schema`는 프로토콜 파일만 생성했다. 서버 listener나 모델 세션을 실행하지 않았다. `HookEventName`에 stop/postToolUse 등, `HookTrustStatus`에 managed/untrusted/trusted/modified가 있다. 이것은 hook 구성 JSON 전체를 검증한 결과와 다르다.
3. [공식 Hooks](https://developers.openai.com/codex/hooks/)에서 hooks.json 위치, 새 훅 신뢰 검토, Stop 입력/출력 계약을 확인했다. Stop의 block은 추가 점검 prompt를 만드는 동작이다. 검증기 테스트는 이를 한 번만 요청하고 stop_hook_active에서는 미완료 안내로 끝내 무한 반복을 피한다. 이는 최종 완료의 절대적 차단이 아니다.
4. [공식 Skills](https://developers.openai.com/codex/skills/)와 [AGENTS 지침](https://developers.openai.com/codex/guides/agents-md/)의 USER 위치/시작 시점 발견 규칙을 확인했다. 웹은 공식 주소만 근거로 사용했고 검색 결과의 제3자 문서나 이슈 제안을 계약으로 사용하지 않았다.

사용 스킬: `project-knowledge-cleanup`의 원본/현행/증거 분리와 완료 근거 원칙, `skill-creator`의 최소 범위·권한 비확대·점진적 안내 원칙을 직접 읽어 적용했다. 별도 스킬 detector/lint나 서브에이전트 실행을 주장하지 않는다.

## 프로젝트 실제 검사 결과

`current-result.json`이 재실행 가능한 전체 기계 결과다.

- 문서 분류 **476개**: 현재14, 역사396, 원본53, 기존 재검토11, 도구2. 이번 Aethon 정책의 자동 발견 범위는 MD다. 엔진은 명시 설정된 txt/pdf/docx/yaml도 hash할 수 있지만 이번에 그 전체를 분류·내용 검사했다고 하지 않는다. JSON은 지정 registry/receipt로만 검사한다.
- 두 registry는 각각 revision9, Document **88개씩**. 기존 등록 파일의 존재·hash **88/88씩 일치**. 합계176 검사는 두 사본에 대한 횟수이며 독립 문서176개가 아니다. 그래프 의미/인용의 사실성/kb.py 전체 validate를 실행한 것은 아니다.
- 최근 유지 문서13+보충문1은 두 registry에 각각 없음: **14문서 / 28 registry-target 누락**. 선언된 `docs/maintained/<원본 경로>`는 등록 시 검토할 snapshot 대상 경로이며 아직 파일 생성·등록·head 승격하지 않았다. 실제 수정 단계에서는 담당자가 native kb 절차와 현재 revision으로 dry run/검토해야 한다.
- 기존 생성 문맥 receipt **7개씩, 총14개**가 현재 registry와 달라 `CONTEXT_REVIEW_REQUIRED`. 무조건 덮어써 재생성하지 않는다. 과거 증거로 둘지 현행 입력으로 새 파일을 만들지 확인해야 한다.
- 기존 미결정11개: 두 키트의 AGENTS/README/OPERATIONS/SCHEMA 각4개, DOCUMENT-INVENTORY, ONTOLOGY-COVERAGE-AUDIT, adoption-docs 보고서. 의미·권위 검토를 하지 않고 자동 등록하지 않았다.
- 종료코드 **1 / blocked**. 이 요청의 검사기 구현 성공과 프로젝트 문서 등록 완료를 구별한다. 제품 runtime IP ontology, 다중 대화 구현, 실제 고객·공급자 검증은 이번 결과가 아니다.

## 검증과 보존

`fixture-tests.log`: **24/24 통과**. 정상/누락등록/등록hash/원본-source drift/오래된 receipt/context 변조/신규 미분류/역사 예외/미결정/미설정/다른 project ID/비밀 경로/경로 탈출/심볼릭 링크/중첩 저장소/worktree/임의 명령 금지/기존 훅 보존/Stop 1회 계속/잘못된 입력/내용 미출력/동시 변경/추가 제외/루트 신규 문서 검출을 시험했다. 세부 메서드는 테스트 파일에 있다.

첫 fixture 실행은 macOS 임시 경로 /var의 symlink 때문에 실패했다. 실제 canonical 임시 루트에서 다시 시험했으며 symlink 거절 조건은 약화하지 않았다. `fixture-initial.log`에 실패도 보존했다. 정책 초기 적용에서는 semantic TOKEN 문서를 비밀 파일로 과잉 분류해 검사가 invalid였다. 자격증명 파일명 규칙을 좁히고 디자인 토큰 문서/실제 token 파일 구분 회귀를 추가했다. 그 이후 결과가24/24다.

검사기는 파일 내용을 출력하지 않고 hash/상대 경로/코드만 보고한다. 알려진 비밀 경로·확장자는 읽기 전에 제외한다. 이름만으로 임의 문서에 숨은 비밀을 모두 탐지한다고 보장하지 않으며 프로젝트별 exclude에 추가해야 한다. 경로는 NOFOLLOW directory FD로 열고 상위/절대/Windows 경로와 중첩 repo를 거절한다. 12MiB/파일,6,000 문서 상한. 입력을 마지막에 재hash해 일반 동시 변경을 거절하지만 filesystem 전체 atomic snapshot/인증 보안 경계는 아니다. 현재 POSIX/macOS 구현이며 Windows는 미검증이다.

`PRESERVATION.json`: 제품 코드·중단 세션 변경분·현재 주요 문서·두 registry 등14개 보호 대상 hash 불변. 전역 기존 hooks 원문과 Git core.hooksPath도 변경하지 않았다. 별도 제품 전체 회귀는 이 비제품 검사 작업 때문에 재실행하지 않았다. 실제 API0/DB0/서버0/설치0/업로드0/배포0. 로컬 스킬을 직접 작성한 것이며 외부 패키지를 설치하지 않았다.

## native 훅 연결에 필요한 다음 확인

후보 동작: 모든 Codex Stop 이벤트에서 현재 cwd에 맞는 정책을 찾아 이 읽기 전용 검사기를 실행한다. 파일내용/transcript/모델답변을 저장하거나 네트워크 전송하지 않는다. 설정 없는 프로젝트는 안내만 하고 생성하지 않는다. 알려진 누락은 한 차례 재점검을 요청하고 이후 미완료 상태를 알린다. 기존 다른 훅을 막거나 교체하지 않는다. Stop의 자동 계속은 추가 Codex 턴을 유발할 수 있으므로 사용자가 그 동작까지 검토해야 한다. 검사기 자체는 네트워크를 사용하지 않는다.

실제 적용 전 `hooks.candidate.json`과 현재 전역 hooks를 다시 대조해 동시 변경을 보존해야 한다. 이후 새 Stop 항목의 정확한 command를 `/hooks`에서 검토·신뢰해야 한다. **이 단계는 현재 미적용이며 자동 검사가 가동 중이라고 말하면 안 된다.** 승인 후에도 실제 native event 전달은 격리 환경에서 별도 확인해야 한다. `--dangerously-bypass-hook-trust`, sandbox/approval 변경은 사용하지 않는다.

## 해제·복구

1. 검사 실행만 중단하려면 직접 명령을 호출하지 않는다. 현재 활성화된 native hook은 없다.
2. 전역 안내 해제는 AGENTS에서 `DOCUMENT_COMPLETION_GATE_V1_START`~`END` 블록만 제거한다. 기존 전체 파일을 백업으로 덮어 후속 사용자 변경을 잃지 않는다. 적용 전 파일은 `before/global-AGENTS.md`에 보존됐다.
3. 스킬 발견을 중단하려면 해당 새 폴더의 `SKILL.md`를 별도 보존 위치로 옮기거나 `SKILL.md.disabled`로 바꾼다. 원래 다른 스킬/훅은 건드리지 않는다. 적용 hash와 다르면 먼저 변경을 검토한다.
4. 프로젝트 정책을 해제하려면 `.document-gate.json`을 별도 보존하고 제거한다. 그 이후 상태는 pass가 아니라 not-configured다. 실제 registry와 원본은 바뀌지 않는다.
5. 추후 native hook을 활성화한 경우 `/hooks`에서 해당 문서 검사 훅만 비활성화하고 다른 훅을 보존한다.

## 정확한 실행 명령

```sh
/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --root /Users/leesungmin/Desktop/Loretune
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/document-gate -v
```

전역 엔진 SHA-256: `1123d8b91bf255c272c2763f8d4e6464cea42dea9f0af814df563c25e9a28479`.
최종 산출물 해시는 `FINAL-MANIFEST.json`에 둔다. 보고서 자기 hash를 본문에 넣는 순환을 만들지 않는다.
