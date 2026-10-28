# DG01–03 독립 최종 재검증 · 1.0.1

2026-10-27 UTC. **PASS — 원래 네 반례 모두 통과하여 DG01–03을 이 고정 버전에서 닫는다.** 기존 대조군3 및 최소 인접검사2도 통과했다. primary의34회귀를 독립 재실행하거나 합산하지 않았다. 문서 등록 누락 해결·실제 Stop 활성화 완료를 뜻하지 않는다.

## 고정 범위와 독립 결과

검사기 SHA256: `33113f9e233f35f641815ef4dca2933b036466314cff6629586fa2b446a334fa`.

원본 독립 `recheck.py`에서 fixture와 기존7개 사례/기대값 블록을 그대로 복사했다. 전체 unittest 실행 부분만 제외하고 정상 PASS 및 malformed CLI 종료코드의 인접 대조군을 추가했다. 원본 감사 증거는 변경하지 않았다. 전역 검사기를 permissions 보존한 임시 사본으로 실행하고 합성 자료만 사용했다. 증거: [recheck.py](recheck.py), [results.json](results.json).

|사례|관측|판정|
|---|---|---|
|DG01a: fresh receipt지만 usage=review-required|exit1/blocked, CONTEXT_REVIEW_REQUIRED + USAGE_REVIEW_REQUIRED|PASS|
|DG01b: legacy-review-pending + registration=not-required|exit1/review-required|PASS|
|DG02: 분류된 문서가 FIFO|약0.038초, hook adapter exit0 + 명시적 incomplete JSON. timeout 없음|PASS|
|DG03: registry objects=[null]|hook adapter exit0 + incomplete JSON, stderr 공백|PASS|
|C01–03 원래 대조군|한 차례 계속 후 경고, 미설정2/생성0, unknown command 거절|3 PASS|
|C04–05 인접 대조군|정상 fresh/current는 pass0, malformed CLI는 invalid3/JSON/stderr 공백|2 PASS|

수정 원인은 실제 전역 `check.py` L51–59의 stat/NOFOLLOW/NONBLOCK/fstat, L198 및 L225의 registry/receipt 사전검증, L214 및 L229의 독립 미결정 처리에서 확인했다. 실제 hook 반환 방식(L250–260)과 처리된 invalid의 warning-only 정책은 유지됐다.

## 정확한 후보와 보존

후보 전체 파일 SHA256:
`90d85ce8c0143188401509ccf4aeb16d1674ce3db1424ea63ee54bcd7c10a3d6`

현재 실제 `~/.codex/hooks.json` SHA256:
`1e0eee0729f46f8f35988ac7d9caf08c09fe1391fc3e1e66c5db844614f4e71d`

후보의 새 Stop 항목만 제거하면 현재 hooks 객체와 정확히 같다. `_disabled`를 포함한 기존 항목을 보존한다. 전역 AGENTS도 이전 감사 hash와 같다. primary 최신 FINAL-MANIFEST의 파일 hash를 모두 대조했고 일치했다. 상세 [FINAL-MANIFEST.json](FINAL-MANIFEST.json). 해당 후보의 **native trust 정의 hash**를 CLI가 계산·표시한 것은 아니며 위 값은 후보 JSON 전체 파일 hash다.

```json
{"type":"command","command":"/opt/homebrew/bin/python3 -B /Users/leesungmin/.agents/skills/document-completion-gate/check.py --hook","timeout":15,"statusMessage":"문서 분류·등록·문맥 상태 검사"}
```

## PASS와 별도로 남는 확인

- 실제 Stop dispatch, `/hooks` 신뢰 변경, 실제 timeout/다른 훅과의 조합, 앱/CLI 각각의 native lifecycle은 **NOT RUN**이다. 함수/자식 프로세스 fixture가 native 실행 증거를 대신하지 않는다.
- 기존 독립 감사에서 확인한 [공식 Hooks 계약](https://developers.openai.com/codex/hooks/)에 따라 Stop block은 추가 prompt를 통한 계속 실행이다. 재진입·처리된 invalid·미설정은 안내만 하므로 절대적 fail-closed가 아니다. 이번에 공식 지원이나 제품 전체를 다시 광범위 검사하지 않았다.
- 문서14개의 실제 등록/승격, receipt 재생성, 미결정 분류는 이번 수정과 별개다. 실제 프로젝트 scanner도 이번에는 반복하지 않고 허용된 격리 검사로 제한했다.
- 제품, registry, 정책, 전역 설정, 원본 감사 파일은 변경하지 않았다. provider/API/비밀/공유 DB/browser/listener/install은 실행하지 않았다. native 활성화·trust는 미실행이며 거부/불명인 변경도 없다.

## 사용자에게 다음으로 확인할 정확한 범위

이번 수정을 다시 승인받을 필요는 없다. **별도의 지속 자동 실행을 시작하는 아래 동작**을 활성화 직전에 확인한다. 이 감사는 그 질문을 대신 제출하거나 동작을 실행하지 않았다.

> 위 수정본 해시와 명령으로 기존 훅을 보존하여 사용자 전역 Stop 후보를 추가하고, 공식 `/hooks`에서 새 정의를 검토·신뢰하는 데 동의하시나요? Aethon 외 Codex 작업에서도 종료 시 로컬 검사가 실행될 수 있고, 정상 미완료 결과는 한 차례 추가 Codex 턴과 사용량을 발생시킬 수 있습니다. 설정 없는 프로젝트는 안내만 하며 파일·registry를 자동 등록하지 않습니다. 이것은 절대적 종료 차단이 아닌 보조 검사입니다.

동의 범위는 후보 병합 + 그 새 Stop 정의의 신뢰다. 모든 훅 일괄 신뢰, `_disabled` 재활성화, hook trust bypass, sandbox/approval 완화, registry 등록 승인을 포함하지 않는다. 설정 추가 직전에 최신 hooks와 script hash를 재확인하고, 동시 변경이 있으면 보존한 새 diff를 제시한다. 실제 `/hooks`의 exact-definition 신뢰 검토는 그 단계에서 수행한다. 고정 경로의 script 내용이 앞으로 변경되면 별도 재검토가 필요하며 native 정의 신뢰가 외부 파일 bytes까지 고정한다고 가정하지 않는다.

이 변경은 새 계정·네트워크·OS ACL 부여는 아니지만 앞으로 로컬 명령을 자동 실행하도록 지속적으로 허용하는 **hook trust 변경**이다. 수동 실행 승인과 구분해야 한다. 해제는 새 훅만 비활성화하며 기존 훅/사용자 변경을 백업 전체로 덮지 않는다.
