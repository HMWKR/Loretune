# Aethon 문서 완료 검사 — DG01–03 수정 및 전역 적용 결과

2026-10-27 UTC. **검사기 1.0.1의 수동 실행은 적용·검증 완료다. 자동 Stop 훅과 신뢰 설정은 아직 미적용이다.** 제품의 중단된 다중 대화 변경분과 실제 registry는 그대로 보존했다. 문서 등록 누락이 해결됐다는 보고가 아니다.

## 이번 변경과 근거

독립 감사 [REPORT-ko.md](../independent-document-gate-audit-20261027/REPORT-ko.md)의 3개 P2를 수정했다. 감사 원본은 수정하지 않았다. 수정 전 검사기/스킬/테스트/이전 보고서/manifest를 [before](fix-20261027/before/)에 보존했다.

|항목|수정 전 실제 재현|최소 수정|수정 후 근거|
|---|---|---|---|
|DG01: 미결정 상태|fresh 문맥 usage=review-required, 미결정 문서+등록 면제 각각 exit0/pass|문서 분류와 문맥 사용 미결정을 해시·revision과 독립적으로 판정|두 원래 반례 모두 nonzero. 명시적으로 current/historical 등으로 해소한 대조군만 통과|
|DG02: FIFO 대기|격리 child가 1.5초 timeout에 걸림; 종료·수거됨|open 전 regular file 확인, O_NOFOLLOW 유지, O_NONBLOCK 및 열린 FD의 fstat로 교체 race 방어|전역 수정본의 원래 hook fixture 약 0.036초에 incomplete JSON. CLI는 invalid/3. stat 후 FIFO로 바뀌는 경우도 거절|
|DG03: malformed registry|objects=[null]에서 traceback, stdout 없음|사용하는 registry record/heads/document/receipt 필드 타입을 먼저 검증하여 Invalid 계약으로 통일|원래 반례와 null/list/scalar/잘못된 필드에서 본문·오류 원문 없이 구조화 실패. 정상 비문서 record와 부가 metadata는 그대로 허용|

원래 4개 반례(원인 3개)는 수정 전 0/4 → 수정 후 4/4 통과했다. 같은 재현기의 기존 대조군 3/3도 통과했다. 독립 재현 코드를 별도 폴더에서 실행한 결과는 [before-recheck/results.json](fix-20261027/before-recheck/results.json), [after-global-recheck/results.json](fix-20261027/after-global-recheck/results.json)이다. 이는 담당 구현 세션의 재실행이며 새로운 독립 감사 완료를 뜻하지 않는다.

기존 24개와 신규 10개를 포함한 unittest **34/34 통과**: [fixture-tests.log](fix-20261027/fixture-tests.log). subprocess/하위 매개변수 사례와 위 재현을 더하여 별도의 총 시험 수로 부풀리지 않는다. 형식상 유효하지만 다른 양의 receipt revision은 invalid가 아니라 stale로 처리한다. 첫 33개 실행에서 이 대조군을 invalid로 잘못 기대한 테스트 1개가 실패했으며 기대를 분리해 새 회귀를 추가했다. 그 로그는 [fixture-initial-33.log](fix-20261027/fixture-initial-33.log)에 남겼다.

## 실제 적용 파일과 보존

- 프로젝트 source: `tools/document-gate/check.py`, `tools/document-gate/SKILL.md`, `tests/document-gate/test_gate.py`.
- 전역 실제 적용: `/Users/leesungmin/.agents/skills/document-completion-gate/check.py`, 같은 폴더 `SKILL.md`. 공식 권한 심사를 거쳐 기존 hash 일치 확인 → 별도 백업 → 같은 파일만 교체했다. 전역과 프로젝트 bytes가 일치한다.
- 이전 전역 두 파일: [before-global](fix-20261027/before-global/). 적용 기록: [GLOBAL-APPLIED.json](fix-20261027/GLOBAL-APPLIED.json).
- `~/.codex/AGENTS.md`, `~/.codex/hooks.json`, 프로젝트 `.document-gate.json`, 제품/문서/registry 보호 대상은 변경하지 않았다. [PRESERVATION.json](fix-20261027/PRESERVATION.json)에서 전후 hash를 확인할 수 있다. 원본 독립 감사도 보존했다.
- candidate command는 동일하다. `hooks.candidate.json` bytes를 불필요하게 다시 쓰지 않고, 최신 검사기 hash와 보존 비교를 [HOOK-CANDIDATE-CHECK.json](fix-20261027/HOOK-CANDIDATE-CHECK.json)에 갱신했다. 후보에서 새 Stop 항목만 제외하면 실제 기존 설정과 정확히 일치한다. `_disabled` 항목을 활성화하지 않았다.

전역 검사기 SHA-256:
`33113f9e233f35f641815ef4dca2933b036466314cff6629586fa2b446a334fa`

전역/프로젝트 SKILL SHA-256:
`d7f44446ef596c6e73c686cde290e45ba8188f93c8844a9a7b1b96daa3e3175e`

회귀 테스트 SHA-256:
`41dd555de4b6e49b005c94c46a75332313fcc19e5e1b3b012187152f87234d4f`

제품 전체 회귀를 이 비제품 작업 때문에 재실행하지 않았다. 제품 코드/공유 DB/registry/receipt 생성 변경 0, 외부 API·서버·유료 호출·키 열람·설치·배포·업로드 0이다. 검증 child 프로세스는 모두 종료·수거했다.

## 현재 프로젝트 결과는 여전히 미완료

[current-result.json](current-result.json)은 전역 1.0.1로 실행한 최신 결과다. 정책을 통과용으로 고치거나 실제 등록/승격을 하지 않았다.

- 두 registry revision9, 등록 Document 88개씩의 파일/hash 88/88씩 일치한다. 176은 두 사본 검사 횟수이며 독립 문서 수가 아니다.
- 최근 문서14개 × registry2 = **등록 대상 28개 누락**이다.
- 문맥 receipt **14개는 사용 구분 review-required가 남아 있으므로 미완료**다. 현재는 registry와도 다르다. 향후 hash가 일치해도 사용 목적의 결정을 대신하지 못한다.
- 기존 문서 **11개는 분류 미결정이면서 등록 검토 대기**다. CLASSIFICATION_REVIEW_PENDING 11건과 REGISTRATION_REVIEW_PENDING 11건은 같은 11문서의 서로 다른 두 결정이며 22개의 별도 문서가 아니다.
- 이번 독립 감사와 보존용 MD 등 정책 이후 생긴 파일도 미분류로 검출한다. 상세 경로는 최신 결과에 있다. 이를 숨기기 위해 정책/registry를 자동 갱신하지 않았다.
- 종료 **1 / blocked**. 검사기 수정 성공, 문서 관리의 완료, 제품 IP 온톨로지의 사실성은 별도이다.

## 정확한 실행 명령과 프로젝트별 적용 범위

수동 검사:

```sh
/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --root /Users/leesungmin/Desktop/Loretune
```

격리 회귀:

```sh
cd /Users/leesungmin/Desktop/Loretune
/opt/homebrew/bin/python3 -B -m unittest discover -s tests/document-gate -v
```

검토용 Stop 후보의 정확한 명령(아직 자동 연결하지 않음):

```sh
/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --hook
```

후보는 `type=command`, `timeout=15`초, `statusMessage=문서 분류·등록·문맥 상태 검사`다. 후보 전체 SHA-256은 `90d85ce8c0143188401509ccf4aeb16d1674ce3db1424ea63ee54bcd7c10a3d6`, 현재 실제 hooks 파일은 `1e0eee0729f46f8f35988ac7d9caf08c09fe1391fc3e1e66c5db844614f4e71d`다.

전역 엔진은 해당 cwd에서 가장 가까운 `.document-gate.json`만 사용한다. 중첩 Git 디렉터리/worktree 파일 경계를 넘지 않는다. 프로젝트마다 문서 분류·registry·context 기준을 선언한다. 다른 프로젝트에 Aethon 정책을 복사하거나 새 ontology/정책 파일을 생성하지 않는다. 설정이 없으면 CLI exit2/not-configured, Stop 어댑터에서는 안내만 반환한다.

임의 프로젝트 command/import/network 실행 기능은 없다. 알려진 비밀 경로와 확장자를 제외하며 경로 탈출/symlink를 거절한다. 12MiB/파일, 문서6,000개 상한과 입력 재hash 검사를 유지한다. FIFO race는 방어하지만 파일시스템 전체 snapshot이나 OS sandbox는 아니며 모든 디스크/네트워크 마운트 지연을 제한하지 않는다. 미지의 파일명에 숨은 비밀을 내용 분석으로 보장하지 않는다. POSIX/macOS에서 검증했고 Windows는 미검증이다.

## 아직 필요한 사용자 확인과 trust 동작

로컬 Codex CLI0.164.0의 hooks 지원 및 스키마, [공식 Hooks](https://developers.openai.com/codex/hooks/), [Skills](https://developers.openai.com/codex/skills/), [AGENTS](https://developers.openai.com/codex/guides/agents-md/) 지원은 이전 조사 기록을 유지한다. 이번 수정에서 Codex 모델 세션이나 native Stop 이벤트를 실행하지 않았다.

후보를 전역 hooks.json에 추가하고 신뢰하면 **Aethon 외의 Codex 작업도 Stop 시 이 로컬 명령을 자동 실행할 수 있다.** 검사기는 읽기 전용이지만 자동 실행 허용 자체가 읽기 전용 보안 장치는 아니다. native 훅의 적용/신뢰는 일반 문서나 이번 검사기 수정 승인과 구별된다.

- 최초 Stop의 정상 incomplete 결과는 `decision:block`으로 추가 점검을 요청한다. **추가 Codex 턴과 사용량/비용이 생길 수 있다.** 검사기 자체의 API 호출은 없다.
- `stop_hook_active=true` 재진입은 계속 요청 없이 미완료 안내만 반환한다. 미설정과 처리된 오류도 안내만 반환한다. 한 번의 재진입 방어이지 다른 훅과 합친 모든 반복을 절대 방지하는 장치는 아니다.
- Stop block은 CI의 절대적 완료 차단이 아니다. invalid·두 번째 Stop·timeout의 실제 UI 동작, 여러 훅의 조합, 앱/CLI 각각의 lifecycle은 미검증이다.
- 활성화 직전 정확한 script hash, 후보 diff, 최신 hooks hash를 다시 확인하고 기존 변경을 보존해야 한다. 사용자의 위 전역 범위 확인 뒤 공식 `/hooks` 절차에서 새 정의를 검토·신뢰한다. 이후 격리 native dispatch 시험이 별도로 필요하다.
- 훅 정의의 신뢰가 고정 경로의 외부 `check.py` bytes까지 pin한다는 보장은 없다. 후보는 script hash를 실행 시 자동 검증하지 않는다. 따라서 검사기 내용 변경도 재검토해야 한다. trust 우회 플래그, sandbox/approval 완화는 사용하지 않는다.

현재는 **수동 검사+전역 지침**까지만 적용됐다. 사용자 확인이나 native trust를 이번 결과로 갈음하지 않는다.

## 해제와 롤백

1. 현재 native Stop은 미활성이므로 해제할 새 Stop이 없다. 앞으로 활성화했다면 `/hooks`에서 이 새 항목만 먼저 비활성화한다. 전체 hooks 백업을 덮어써 다른 변경을 잃지 않는다.
2. 검사기 수정 롤백은 현재 두 파일 hash를 확인하고 `fix-20261027/before-global`의 대응 파일만 복원하는 방식이다. 이전 버전에는 DG01–03이 있으므로 정상판정용으로 되돌려 사용하지 말고 수정·비교용으로 보존하는 편이 안전하다.
3. 전역 지침 해제는 AGENTS의 `DOCUMENT_COMPLETION_GATE_V1_START`~`END` 블록만 제거한다. 후속 사용자 내용을 보존한다. 스킬 발견만 중단하려면 SKILL.md를 별도 보존 위치로 옮길 수 있지만, 활성 hook이 check.py를 직접 부르는 경우 그 동작은 별도로 중단해야 한다.
4. 프로젝트 정책을 해제하면 pass가 아니라 not-configured가 된다. 실제 registry·원본·제품 코드에는 영향을 주지 않는다.

이전 보고서는 [보존본](fix-20261027/before/docs/qa/document-gate-20261027/REPORT-ko.md), 최신 산출물 해시는 [FINAL-MANIFEST.json](FINAL-MANIFEST.json)에서 확인한다. 사용 스킬은 기존 `document-completion-gate`이며, 이전에 읽어 적용한 `project-knowledge-cleanup`/`skill-creator` 원칙을 유지했다. 별도 subagent, 스킬 detector 또는 새 품질 점수는 없다.
