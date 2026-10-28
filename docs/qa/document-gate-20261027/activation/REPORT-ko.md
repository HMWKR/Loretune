# 전역 Stop 호환성 정리 후 상태 — 2026-10-27 04:28 UTC

**호환성 정리는 적용 완료. 새 Stop의 공식 신뢰와 native dispatch는 격리 폴더의 추가 지속 신뢰 확인에서 대기 중이다.** 아래 이전 parser 오류 기록은 보존된 역사적 경과이며, 현재 hooks 파일에는 `_disabled`가 없다.

- `~/.codex/hooks.json`에는 기존 선언 8개와 승인된 문서 Stop 1개만 있다. 그룹·명령·timeout·matcher는 그대로 보존했다. 현재 SHA256: `af8b499ddb0f192c91faa7046af7cbef0a828fdbc1434609e48d67f8c285f63a`.
- 비활성 checkpoint 정의와 메모는 `/Users/leesungmin/.codex/disabled-hook-archives/checkpoint-save-20261027.archive.json`에 보존했다. 이 파일을 hook source로 등록하지 않았고, 최상위도 hooks가 아닌 archive metadata이다. 원래 `_disabled` 객체와 일치함을 확인했다. SHA256: `a329d72382963eabe689618946ea2f8793726e5bc4eba2603097d9a12e67f2f4`.
- 정리 직전 전체 설정은 [hooks.precompat.json](hooks.precompat.json)에 보존했다. checkpoint_save.py는 활성 목록에 없으며 실행하지 않았다. 검사기 1.0.1 해시도 승인값 `33113f9e233f35f641815ef4dca2933b036466314cff6629586fa2b446a334fa` 그대로다. 이전 34/34 시험은 코드 변경이 없어 재실행하지 않았고, native 결과로 합산하지 않는다.

## 공식 CLI에서 새로 확인된 단계

격리 fixture에서 `codex --no-daemon --no-alt-screen --sandbox read-only -m gpt-6-astra`로 공식 절차를 시작했다. `/hooks`에 도달하기 전 **Folder access**가 아래 범위의 저장되는 신뢰를 요청했다:

- 대상: `/private/var/folders/t7/p6pl4snd6pd3cmz1y80_7fzw0000gn/T/document-gate-native-qcdagrhm/unconfigured`
- 의미: 그 폴더의 파일 읽기·편집·실행은 permission 설정에 따르며, 폴더 설정은 모델 요청 없이도 코드를 실행할 수 있다. 선택은 저장된다.
- 선택지: Trust and continue / Quit.

새 Stop 정의 하나의 신뢰와 별도인 지속 폴더 신뢰라 자동 동의하지 않았다. Escape로 Quit하여 CLI exit0을 확인했다. 이것은 승인 심사 거절이나 실행 결과 불명이 아니라, 추가 신뢰 확인에 동의하지 않고 종료한 상태다. trust DB 직접 편집, 다른 디렉터리로 회피, CUA 재시도, bypass는 하지 않았다.

정상/미설정/차단/재진입의 native Stop 검증은 **NOT RUN**이다. 현재 새 정의가 실제로 신뢰됐거나 자동 실행된다고 말할 수 없다. 새/기존 클라이언트의 재로드 범위도 미확인이다. 모델 프롬프트 제출0, Anthropic/fal0, 제품·DB·registry 수정0, 설치/배포0이다. CLI는 종료됐고 합성 fixture는 보존됐다.

추가 확인이 필요한 범위는 **위 무비밀 시험 폴더 한 곳의 지속 Folder trust**뿐이다. 확인되면 공식 UI에서 해당 폴더를 신뢰한 뒤 `/hooks`에서 문서 Stop 하나만 신뢰한다. 기존 8개 일괄 신뢰는 포함하지 않는다. 이 폴더를 이후 다른 용도로 재사용하지 않는 것이 적절하며 해제도 공식 프로젝트 신뢰 절차를 사용해야 한다.

## 과거 checkpoint.md 확인

Loretune 루트, aethonSaaS 루트, Desktop/atheon 루트에는 해당 파일이 없었다. `/Users/leesungmin/Desktop/aethonSaaS/atheon/checkpoint.md`는 존재하지만 제목이 ‘현재 작업 체크포인트 — 2026-09-06’인 별도 작성 문서이며 자동 writer 표식이 없고 agent-work 문서 4곳에서 참조한다. 불필요하다고 단정하지 않아 이동·삭제하지 않았다. [CHECKPOINT-CLEANUP.json](CHECKPOINT-CLEANUP.json)에 정확한 대상/참조/해시를 기록했다. 전역 동명 파일을 탐색해 일괄 삭제하지 않았다.

## 복구와 최신 증거

현재 정리본과 별도 보관본을 함께 보존한다. 정리 자체를 취소해야 한다면 최신 hash와 후속 변경을 비교해 hooks.precompat.json의 구조를 복구할 수 있지만, 그 버전에는 알려진 parser 오류가 있으므로 정상 운영 복구안으로 권하지 않는다. 새 Stop만 해제할 경우 해당 항목 하나만 제거하고 나머지를 보존한다. 비활성 checkpoint 정의는 어느 복구에서도 활성 hooks로 합치지 않는다.

[COMPAT-APPLIED.json](COMPAT-APPLIED.json), [COMPAT-NATIVE-RESULT.json](COMPAT-NATIVE-RESULT.json), [FINAL-MANIFEST.json](FINAL-MANIFEST.json)이 최신 근거다. 아래 내용은 이전 활성화 시도의 보존 기록이다.

---

# 전역 Stop 활성화 시도 — 공식 parser 차단

2026-10-27 UTC. **새 Stop 정의는 승인된 후보대로 저장됐지만, 기존 전역 파일의 형식 오류 때문에 로드되지 않는다. 신뢰 설정과 native Stop dispatch 검증은 미실행이다.** 허가 심사 거절이 아니라 공식 CLI 설정 parser 오류다.

## 실제 실행과 결과

1. 독립 재검증 보고서를 읽고 승인된 검사기·후보·기존 hooks 해시를 재확인했다. 모두 승인값과 일치했다.
2. 공식 escalation 심사 승인 후 기존 `/Users/leesungmin/.codex/hooks.json`을 `hooks.before.json`에 백업하고 새 Stop 항목 하나만 추가했다. 기존 항목과 `_disabled` 내용은 보존됐다.
3. 무비밀 임시 fixture 폴더에서 CLI 0.164.0을 `--no-daemon --no-alt-screen --sandbox read-only`로 실행하고 **공식 `/hooks` 화면**을 열었다. Codex 앱 CUA, trust DB 직접 편집, bypass 옵션은 사용하지 않았다.
4. 화면에서 다음 오류를 실제 관측했다:

```text
failed to parse hooks config /Users/leesungmin/.codex/hooks.json: unknown
field `_disabled`, expected `description` or `hooks` at line 89 column 13
```

`_disabled`는 이번 추가 전 백업에도 있던 필드다. 후보의 단순 JSON·기존 내용 보존 검사는 통과했지만 실제 Codex parser 검증을 대신하지 못했다. 이 차이는 이번 공식 UI 단계에서 처음 확인됐다. 다른 출처의 기존 플러그인 훅은 UI에 나타났지만 이 전역 파일에서 새 정의를 신뢰할 수 없었다.

5. 신뢰 작업이나 검증용 모델 프롬프트를 제출하지 않고 Esc → Ctrl-D로 종료했다. CLI process exit0을 확인했다. 화면 기본 모델은 GPT-6.1 Terra medium으로 표시됐으나 inference를 요청하지 않았으므로 Astra 실행 또는 모델 품질 검증으로 보고하지 않는다.

## 적용값과 상태

- 실제 hooks 파일: `/Users/leesungmin/.codex/hooks.json`
- 현재 파일 SHA256: `90d85ce8c0143188401509ccf4aeb16d1674ce3db1424ea63ee54bcd7c10a3d6`
- 적용 전 파일 SHA256: `1e0eee0729f46f8f35988ac7d9caf08c09fe1391fc3e1e66c5db844614f4e71d`
- 검사기 SHA256: `33113f9e233f35f641815ef4dca2933b036466314cff6629586fa2b446a334fa`
- 설정 추가: 완료. 새 정의 로드/신뢰/native dispatch: 미완료. trust 변경 시도0. 다른 훅 일괄 신뢰0.

승인된 정의는 다음 그대로다:

```json
{"type":"command","command":"/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --hook","timeout":15,"statusMessage":"문서 분류·등록·문맥 상태 검사"}
```

## 실제 검증 범위와 실행하지 않은 항목

새 CLI 클라이언트의 `/hooks`가 저장된 파일을 읽으려 시도하는 것까지 확인했다. 기존 앱/CLI 세션이 즉시 재로드하거나 동일하게 동작하는지는 확인하지 않았다. 새 Stop은 이 새 클라이언트에서도 parser 오류 때문에 활성화되지 않았다.

설정 없음/정상/미완료/재진입의 **native Stop 검증은 모두 NOT RUN**이다. 이전 34개 회귀와 수동 `--hook` fixture 결과를 여기에 대신 붙이지 않는다. 따라서 추가 턴·timeout·다른 훅 조합의 실제 lifecycle 검증도 아직 없다.

합성 fixture는 문서 3개와 선언형 정책 2개만 준비했고 제품자료·키는 넣지 않았다. 원래 5개 파일 hash는 모두 불변이다. CLI의 기존 bkit 플러그인이 격리 `unconfigured/.codex/bkit/`에 `.transaction.lock` 및 `lifecycle-observations.json` 두 파일을 생성했다. 이를 새 검사기의 쓰기 동작으로 오인하지 않는다. 내용은 보고서에 복사하지 않았고 fixture 폴더는 후속 확인용으로 보존했다. 프로세스는 종료됐다. 제품·공유 DB·registry 변경0, Anthropic/fal 호출0, 모델 프롬프트 제출0, 설치/배포/업로드0이다.

## 다음에 필요한 최소 결정

`_disabled`를 임의로 삭제하거나 이동하지 않았다. 그 필드를 없애 parser를 통과시키면 지금까지 파일 단위로 읽히지 않던 기존 SessionStart/PreToolUse/PostToolUse/UserPromptSubmit 항목도 다시 발견되며, 기존 신뢰 상태에 따라 실행될 수 있다. 새 Stop 하나의 활성화 승인만으로 그 효과를 묵인하지 않는다.

안전한 다음 단계는 기존 전역 설정의 호환성 정리 범위를 먼저 확인하는 것이다. 비활성 보관 항목은 별도 보관하고 지원되는 구조만 남기는 방법과, 기존 파일을 유지한 채 지원되는 별도 전역 설정 위치에 이 Stop 하나를 두는 방법을 비교할 수 있다. **어느 대안도 이 턴에 적용하지 않았다.** 후자는 정확한 병합/중복/원래 파일 오류의 영향까지 확인해야 하며 편의상 config·신뢰 DB를 직접 고치지 않는다.

설정이 공식 parser를 통과한 뒤 `/hooks`에서 정확히 이 새 정의만 검토·신뢰하고 격리 native 시험을 진행해야 한다. 신뢰나 sandbox/approval을 우회하지 않는다. 지속 자동 실행은 모든 지원되는 로컬 Codex 프로젝트에 영향을 줄 수 있으며, 미완료에서는 추가 Codex 턴·사용량이 생길 수 있다. 재진입/오류/미설정은 안내만 하는 보조 검사로 절대적 완료 차단은 아니다.

## 롤백

현재 추가 항목은 로드되지 않아 새 Stop 실행을 중단할 신뢰 설정이 없다. 설정 추가를 되돌릴 경우 최신 파일 hash가 위 적용값과 같은지 확인하고 새 Stop 항목 하나만 제거한다. 다른 후속 변경이 있으면 비교 후 병합한다. 전체 백업을 무조건 덮어쓰지 않는다. 검사기·수동 스킬·기존 AGENTS·registry는 그대로 사용할 수 있다.

증거: [CONFIG-APPLIED.json](CONFIG-APPLIED.json), [NATIVE-RESULT.json](NATIVE-RESULT.json), [hooks-ui-observation.txt](hooks-ui-observation.txt), [FIXTURES.json](FIXTURES.json), [FINAL-MANIFEST.json](FINAL-MANIFEST.json). UI 기록은 관측한 해당 오류의 텍스트 전사이며 화면 이미지라고 주장하지 않는다.

공식 계약: [Hooks](https://developers.openai.com/codex/hooks/)의 exact-definition 신뢰와 `/hooks` 절차, hooks.json의 description/hooks 구조를 참조했다. 지원 문서가 실제 설치 환경의 성공 결과를 대신하지 않는다.

## 기존 소스와의 차이 발견

보존 확인에서 이전 DG 수정 시점과 비교해 index.html, app.py, chat_sessions.py, chat_runtime.py, chat_protocols.py의 5개 hash가 달랐다. 이번 활성화 작업은 해당 파일을 쓰지 않았으며, 언제/누가 변경했는지는 이번 범위에서 단정하지 않는다. 따라서 이전 기준과 모두 불변이라고 보고하지 않는다. 현재 값을 PRESERVATION.json에 남겼고 되돌리거나 조사 범위를 제품 구현으로 넓히지 않았다. 나머지 비교 대상 11개는 이전 hash와 같다.
