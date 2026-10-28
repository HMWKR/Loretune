# 전역 문서 완료 검사·미활성 Stop 후보 독립 검토

2026-10-27 UTC. **판정: 수동 읽기 전용 검사는 적용 가능하나 아래 3개 P2 수정 필요. native Stop 활성화·신뢰는 수정 및 사용자 범위 확인 뒤 별도 검증해야 한다. 현재 자동 강제 검사로 운영 중이라고 말할 수 없다.**

검사기 SHA256 `1123d8b91bf255c272c2763f8d4e6464cea42dea9f0af814df563c25e9a28479` 기준이다. primary FINAL-MANIFEST 8개와 GLOBAL-APPLIED 4개가 실제 파일과 모두 일치했다. 제품/registry/전역 설정/기존 보고서는 변경하지 않았다. 복사한 검사기와 합성 fixture만 실행했다. 새 기록은 이 감사 폴더뿐이며 hook 신뢰·활성화·native event·공유 DB·모델 API·설치·업로드는 실행하지 않았다. 공개 공식 Hooks 문서만 웹으로 조회했으며 프로젝트 내용은 보내지 않았다.

## 먼저 수정할 재현 가능한 항목

|ID / 심각도|재현·기대|실제 결과 / 영향|원인·최소 수정·수용 기준|
|---|---|---|---|
|DG01 / P2 — 명시적 미결정이 PASS|정상 합성 registry/context의 bytes·revision이 일치한 상태에서 context `usage=review-required`로 둔다. 별도 사례는 document `classification=legacy-review-pending`, `registration=not-required`로 두고 baseline hash를 맞춘다. 검토가 끝날 때까지 nonzero여야 한다.|두 사례 모두 `status=pass`, exit0. 분류 결정을 하지 않고 hash만 최신화하면 완료로 오인할 수 있다. 현재 Aethon의 stale receipt와 pending registration은 실제로 차단되므로 지금 결과 전체가 거짓 PASS라는 뜻은 아니다.|`check.py` L177–180은 registration 값만 pending으로 처리; L192–200은 freshness 오류가 있을 때만 review-required를 반환. 미결정 분류와 문맥 usage는 freshness와 독립적으로 nonzero 상태를 내거나 모순된 정책 조합을 거절해야 한다. **검토 상태가 남은 fresh receipt/document는 PASS 불가**, 명시적으로 current/historical 등으로 해소한 정상 대조군만 PASS.|
|DG02 / P2 — 비정규 파일 open 대기|명시 분류된 합성 `docs/current.md`를 FIFO로 교체하고 격리 자식 프로세스에서 `--hook` 호출. 일반 파일이 아니면 즉시 bounded 오류여야 한다.|1.5초 후 우리 테스트 timeout으로 해당 자식만 종료·수거. stdout 오류 JSON 없음. native Stop은 실행하지 않았다. writer 없는 FIFO의 blocking open 때문에 candidate의 15초 외부 timeout에 의존할 수 있다.|`read` L48에서 blocking `os.open`한 뒤 L50–51에서 regular-file 검사하므로 순서상 검사에 도달하지 못함. `O_NOFOLLOW` 유지하며 nonblocking open+fstat regular 검사 등으로 FIFO/device를 거절. 수용: FIFO prompt rejection, CLI invalid3 / hook 명시적 incomplete JSON, symlink 거절 유지.|
|DG03 / P2 — malformed registry가 오류 계약 이탈|합성 registry의 outer schema는 정상이나 `objects=[null]`. `--hook`은 원문을 노출하지 않는 구조화된 incomplete JSON을 반환해야 한다.|exit1, stdout 공백, stderr `AttributeError: 'NoneType' object has no attribute 'get'`. 검사가 완료되지 않았다는 정해진 사용자 안내가 사라짐. 현재 registry가 손상됐다는 발견은 아니다.|L165의 원소 타입 미검사 `.get`; L233 예외 계약에 AttributeError 없음. registry object/heads/receipt의 사용 필드 타입을 읽기 전에 명시 검증해 `Invalid`로 통일. 단순 광역 exception 삼키기보다 입력 schema 검사. null/list/scalar record는 내용 없는 오류, 정상 fixture 유지.|

실행 증거: [recheck.py](recheck.py), [results.json](results.json), [existing-fixtures.log](existing-fixtures.log). Python 3.15.0, canonical temporary directory에 source permissions를 보존해 복사했다. 기존 **24/24 PASS**를 독립 재실행했고 추가 7개 관측 중 대조군 3개 PASS, 위 4개 반례 FAIL(3개 원인)이다. 새 전체 제품 suite는 실행하지 않았다.

재현 명령(검사기/정책을 변경하지 않음):

```sh
/opt/homebrew/bin/python3 -B docs/qa/independent-document-gate-audit-20261027/recheck.py
```

## 적용 가능한 범위

- **읽기 전용 엔진:** 검사기는 표준 라이브러리만 사용하며 프로젝트 command 실행, 프로젝트 모듈 import, network client, 파일 저장 기능이 없다. 출력은 상대 경로·hash·상태이며 문서 본문은 출력하지 않는다. `--hook`은 입력 JSON을 파싱하지만 transcript 경로를 열거나 assistant 원문을 저장하지 않는다. 이번 source 검토/fixture 범위의 결론이지 OS sandbox로 강제된 권한 보증은 아니다.
- **정책과 경로:** 허용 필드·상대 경로·registry identity 검사, 상위/절대/Windows 경로 및 symlink 거절, directory FD + NOFOLLOW 접근이 있다. 중첩 Git directory/worktree `.git` file 경계는 상위 정책을 상속하지 않는다. 기존 관련 fixture 통과. 별도 git 경계가 없는 하위 폴더는 가장 가까운 정책을 상속하는 설계다.
- **비밀 제외:** `.env`, auth/credential 이름, 알려진 key/DB suffix와 제외 경로를 검사한다. 임의 이름의 문서 안에 숨은 비밀까지 분류하지 않는다. 자동 명령 실행 경로는 없어도 정책은 읽을 문서·등록부의 범위를 정하므로 신뢰해야 한다.
- **현재 프로젝트의 불완료 탐지:** primary의 `current-result.json`은 등록 누락 28 target(문서14 × kit2), 문맥14, 분류 미결정11을 구분한다. 이 감사는 해당 수를 새 제품 검증으로 세지 않는다. 새 감사 파일도 기존 정책에 자동 등록하지 않았다.
- **보존:** 실제 `~/.codex/hooks.json` bytes는 `before/global-hooks.json`과 동일하다. candidate에서 새 Stop 항목 하나를 제거하면 현재 hooks 객체와 정확히 일치한다. AGENTS는 기존 bytes를 prefix로 보존했고 suffix는 `global-agents-addition.txt`와 일치한다. `_disabled.Stop`도 그대로이며 부활하지 않았다.
- **미설정과 loop 대조군:** 미설정은 CLI2/not-configured, 파일 생성0. 정상 미완료 Stop은 최초 `decision:block`, `stop_hook_active=true`이면 경고만 반환한다. unknown command 정책은 거절한다.

## 공식 지원과 실제 미검증의 경계

로컬 `/opt/homebrew/bin/codex --version`을 직접 실행해 **0.164.0**을 확인했다. PATH alias 생성 권한 경고가 있었으나 version 명령은 exit0이며 alias를 만들기 위한 재시도는 하지 않았다. 저장된 해당 CLI의 protocol schema에는 Stop event와 hook trust 상태가 있다. protocol schema 존재와 hooks.json 전체의 실제 parser/dispatch 검증은 다르다.

[공식 Hooks 문서](https://developers.openai.com/codex/hooks/)의 현재 계약과 후보를 대조했다. `Stop`에는 matcher가 적용되지 않고, command·초 단위 timeout·statusMessage 구성 및 stdout JSON이 지원된다. `decision:block`은 완료를 거부하는 CI 장벽이 아니라 추가 사용자 prompt 형태의 계속 실행을 요청한다. 새/변경 non-managed hook은 정확한 정의를 신뢰하기 전 실행되지 않는다. user-level hook은 project-local trust와 별개이므로 전역 후보의 범위를 Aethon만으로 설명하면 안 된다.

후보의 정확한 추가 항목:

```json
{"type":"command","command":"/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --hook","timeout":15,"statusMessage":"문서 분류·등록·문맥 상태 검사"}
```

**현재 미검증:** 실제 `/hooks` 신뢰 상태 조회/변경, 후보를 로드한 native Stop dispatch, 실제 15초 timeout 뒤 UI/모델 처리, 동시 다른 훅의 결정 우선순위, 앱/CLI 각 실행 환경의 파일 권한. 이번에는 후보 JSON을 stdin으로 전달한 오프라인 함수/프로세스 fixture까지만 실행했다. 설치된 CLI가 hooks를 지원한다는 사실을 실제 이 후보의 lifecycle 검증으로 바꾸지 않는다.

### fail-open / fail-closed 판정

직접 CLI에서는 정상 불완료1, 미설정2, 처리된 invalid3이며 pass만0이다. 그러나 hook adapter는 처리된 invalid에도 exit0 + systemMessage만 반환하고 계속 실행 요청을 하지 않는다(L233–236). 이미 한 번 계속했을 때와 미설정도 warning-only다. 따라서 **의도적으로 보조 안내에 가까운 Stop**이며 절대적 fail-closed가 아니다. DG02 timeout과 DG03 비정상 exit의 실제 native 처리까지 확인하지 않았으므로 그것들이 작업을 차단한다고 주장할 수 없다. 사용자에게 이 한계를 보여주고, 강한 완료 gate가 필요하다면 별도 CI 단계 종료코드 계약으로 다뤄야 한다. 이번에 CI를 추가하지 않는다.

## 신뢰 설정의 정확한 영향과 다음 확인

이 후보는 새 계정, 외부 서비스, 토큰, listener, filesystem ACL, sandbox/approval 변경을 만들지 않는다. 하지만 `~/.codex/hooks.json`에 추가하고 `/hooks`에서 신뢰하는 것은 **향후 Stop마다 로컬 명령을 자동 실행하도록 지속적으로 허용하는 hook trust 변경**이다. 단순 MD 안내 또는 이번 한 번의 읽기 승인과 같지 않다. 현재 스크립트는 읽기 전용이지만 자동 실행 권한 자체가 읽기 전용으로 제한되는 보안 장치는 아니다.

또한 native 신뢰의 설명 대상은 hook 정의이며 외부 `check.py` 파일 내용까지 immutable하게 고정됐다는 검증은 없다. candidate는 고정 경로를 실행하며 script hash를 자체 확인하지 않는다. 따라서 활성화 직전에 **정확한 script hash·candidate diff·기존 hooks hash를 다시 검토**하고, 이후 그 파일 변경에도 재검토 기준을 두는 것이 적절하다. `--dangerously-bypass-hook-trust`나 권한 완화는 사용하면 안 된다.

부모가 사용자에게 다음으로 확인할 구체적 문안은 다음과 같다. **현재 결함을 고친 검토본이 마련된 뒤 묻는 최종 동작 확인**이며 이 감사에서 질문하거나 실행하지 않았다.

> 수정본의 확인된 해시와 위 명령으로, 기존 훅을 보존한 채 사용자 전역 Stop 훅을 추가하고 그 새 정의를 신뢰할까요? 활성화하면 Aethon 외 Codex 작업에서도 종료 시 로컬 문서 검사를 실행하며, 미완료일 때 한 차례 추가 Codex 턴과 그 사용량이 생길 수 있습니다. 미설정 프로젝트에는 안내만 하고 문서·registry를 자동 등록하지 않습니다. 오류나 두 번째 종료는 절대 차단하지 않는 보조 검사입니다.

전역 범위를 원하지 않는다면 **현재 수동 검사 유지** 또는 Aethon에 한정한 별도 후보를 먼저 검토할 수 있다. 현재 후보에 없는 프로젝트 한정을 이미 구현됐다고 설명하지 않는다. 보안 설정을 우회하는 포괄 승인은 요청하지 않는다. 확인 후에도 실제 활성화는 전용 action-time 승인/신뢰 경로를 거쳐야 하며 그 순간 최신 hooks 동시 변경을 보존해야 한다.

## 해제·롤백

현재는 미활성이므로 native 해제 작업이 필요 없다. 추후 활성화하면 해당 새 훅만 `/hooks`에서 비활성화하고, 설정에서 제거할 때 exact entry만 삭제한다. 전체 hooks 백업 덮어쓰기는 후속 사용자 변경을 잃을 수 있다. AGENTS도 marker 사이 추가 블록만 제거하고 다른 내용은 보존한다. skill을 해제할 경우 **활성 hook부터 중단**한 뒤 SKILL을 비활성화해야 하며 SKILL 이름만 바꿔도 check.py를 직접 부르는 hook은 계속될 수 있다. 프로젝트 정책 제거 시 pass가 아니라 not-configured다. 어느 rollback도 실제 registry·원본을 바꾸지 않는다.

이번 감사에서 거부된 실행이나 결과 불명인 실제 변경은 없다. 유일하게 종료한 프로세스는 DG02가 만든 격리 자식이며 subprocess timeout이 종료·수거했다. 실제 훅/신뢰 작업은 **미실행**이다. 수정·재검증 및 위 구체적 신뢰 범위 확인이 남아 있다.

마지막으로 검토한 전역 스킬의 수동 명령을 현재 프로젝트에 읽기 전용으로 실행했다. [current-gate-result.json](current-gate-result.json)은 exit1/blocked: 등록 누락28, 문맥 재검토14, 등록 검토 대기11에 새 감사 MD의 미분류1을 추가 탐지했다. 이를 통과시키려고 정책·registry를 바꾸지 않았다. [FINAL-MANIFEST.json](FINAL-MANIFEST.json)의 최종 대조에서 primary의 원래 8개 산출물과 전역 4개 파일은 모두 불변이었다.
