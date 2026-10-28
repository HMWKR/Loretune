# Aethon · 일반 대화 제작 도구 연결 + 검토 카드 이동 개선 + 디자인 개선 — 작업 보고 (2026-10-28)

상태: **사용자 지시로 중단.** 마지막 재작업(Wave 2d)은 시작 직후 중지했다(인용: "아니야 재작업은 하지 말고"). 이 문서는 중단 시점의 사실만 적는다. 확신도 표기: [검증됨] 파일·실행 결과로 확인 / [추정] / [미확인].

## 1. 요약

| 영역 | 상태 | 근거 |
|---|---|---|
| 서버 — 일반 대화 읽기·준비 도구(A1·C1, Wave 1) | 재작업 후 critic PASS | `tasks/A1-server-read-tools-r2/acceptance.json`, `tasks/C1-3d-read-schema-r2/acceptance.json` |
| 대화 UI(B1, Wave 1) | 재작업 후 critic PASS | `tasks/B1-chat-ui-r2/acceptance.json` |
| 서버 — D15 영상 준비·단가·이유(A2a), 3D·취향 도구(A2b) → SRV-r2 → SRV-r3 | **마지막 판정 FAIL(serious 1)** | `tasks/SRV-r3/verdict-wave2c.json` |
| 화면 — 디자인 확정 52건(E1)·카드 표시(B2) → UI-r2 → UI-r3 | 마지막 판정 PASS, minor 6 남음 | `tasks/UI-r3/verdict-wave2c.json` |
| 설계문서 — 프레임 관찰(D1, 코드 아님) → r3 → r4 → r5 | 마지막 판정 PASS, minor 4 남음 | `tasks/D1-r5/verdict-wave2c.json`, `docs/design/FRAME-OBSERVATION-DESIGN-ko.md` |
| S14 통합 검증(실화면 ego lite·전체 회귀·codex 최종 검수) | **미실행** | — |

## 2. 한 일

### 2-1. 기준선과 보존 [검증됨]
- 편집 전 사본 `before/`(240파일, `before-inventory.json`).
- S0 전체 회귀 `regression-s0/receipt.json`: passed, 931개, skip 0, Warning 0.
- 디자인 '전' 캡처 24장 `design-gate/before-capture/`(Aside, 8상태×1920/1280/375, 다크). ego lite로 같은 조건 재촬영은 S14와 함께 미실행.

### 2-2. 사용자 결정 반영(PLAN §6, §8-4)
- D15: 영상 준비 때 모델이 프로젝트 선택과 다른 model_id를 주면 *제안*으로 허용. 권한 모드(read_only/review/full_access)를 따르고 실행은 항상 사람 승인. 선택 모델·단가·출처·이유(`model_reason`)를 권한과 무관하게 표시.
- D19: fal 공개 가격 페이지 값을 출처·조회 시각(2026-10-28T09:28:18Z)·'문서 기준 추정' 라벨로 기록. flux schnell $0.003/MP, flux pro 1.1 $0.04/MP, kling 2.6 pro $0.07/s, kling 2.5 turbo는 원문("For 5s video your request will cost $0.35. For every additional second you will be charged $0.07.")을 함께 저장.
- D20: `MAX_INPUT` 16384로 상향. 회차·대화당 최대 예약액 변화는 A2a 결과에 계산.
- D21: 대화 모델의 토큰 단가·선택 이유·effort·permission을 에이전트 설정 요약에 표시.
- 디자인: 확정 52건 전부(기각 10건 제외) 수정 지시.

### 2-3. 서버 변경 요지(현재 코드에 반영됨)
- 영상·이미지 준비에 `model_reason`(1~300자, 스키마·설명으로 모델에 노출, 위반 시 고칠 수 있는 `invalid_arguments` 결과), actor·provenance{engine, chat_model, permission_mode, effort, run, call} 기록.
- 설정 불변 테스트를 17도구×3모드 51칸으로 실제화, 변이 테스트 8/8·매트릭스 3/3 검출(`tasks/SRV-r3/mutants.log`).
- 이어쓰기 본문 크기: 결과 쪽 나누기(scene-status 커서, estimate·목록 쪽), 회차 단위 예산(57,344B = 65,536 − 8KiB). 상한 초과는 더 이상 `outcome_unknown`으로 잠그지 않고 회복 가능한 `limit_reached`로 끝냄(제공자 쓰기 0, 예약 해제 — 테스트 확인).
- 취향 후보 대기 상한 10(`PREFERENCE_CANDIDATE_LIMIT`), 같은 인수 중복 재사용(저장된 출처·상태 반환), OpenAI strict 스키마는 min/maxLength를 설명으로 옮김.
- 마지막 서버 실행: 154모듈 `Ran 1038 tests / OK (skipped=19) / rc=0`, Warning 0(`tasks/SRV-r3/full-tests.log`). 공식 회귀 드라이버 실행이 아니고 `test_contract_counterexamples`를 뺀 목록이며 skip 19가 있어 S14 합격 기준(skip 0)과 다르다.

### 2-4. 화면 변경 요지(현재 코드에 반영됨)
- 375 헤더 작품 선택 칸 잘림 수정(CSS 덮어쓰기 해소), 알림 문구 과다(#46) 대부분 정리, 작업 상태 줄·대화 요약에 단가·가격 종류·출처·개정·만료·출처 기록 표시(S16), 금액 형식 통일(`usd()`), 재생 헤드 표시 정확도(#3), 버튼 괄호 면책 정리(#7), 토글 라벨(#8).
- 디자인 게이트: Hallmark lint fails 18→9, reflex 73→1, warns 16→13(`design-gate/sloplint-before.json` → `sloplint-after-r3.json`). Impeccable detect index.html은 전후 모두 anti-pattern 1건·advisory 12건(`impeccable-start-e1.txt`, `impeccable-after-r3.txt`).
- UI 테스트: 210개 OK(`tasks/UI-r3/verdict-wave2c.json`의 재실행 기록).
- **렌더 관찰은 하지 않았다**(워커는 브라우저 금지, S14 미실행). 화면 결과는 [미확인].

## 3. 안 한 일·남은 결함 (모두 결함으로 유지, 강등 없음)

### 3-1. 서버 — SRV-r3 critic
- **serious**: 목록(shots·actions·plans)을 개수(8개)로만 잘라 shot당 take가 많으면(측정: 8 shot × 25 take) 새 회차 첫 쪽도 예산을 넘는다. 이때 안내의 `next_query`가 실패한 조회어를 그대로 되풀이해 진전이 없다(`chat_general.py:36`). 잠김은 없지만 모델의 주 조회 도구가 그 작품에서 빈 결과만 낸다. 재현 probe: `/private/tmp/claude-501/-Users-leesungmin-Desktop-Loretune/1ebfb89f-9e94-4156-8aea-2393f299eb3e/scratchpad/srvr2/probe_r3_bigplain.py`(스크래치 경로라 세션 뒤 사라질 수 있음).
- minor: estimate 등 비검색 도구 안내의 next_query=null인데 문구는 넘기라고 함 / 예전 `scene-status offset=N` 형식이 오류 없이 일반 조회로 처리됨 / 목록 쪽 offset 방식이라 쪽 사이 변경 시 밀림 / `timeline.clips`·`server_receipts`·`context`·`sources` 상한 없음 / 새 회차 첫 요청은 contract-fake에서 크기 검사 없음(live는 400) / xAI strict 정의에 min/maxLength 남음 / result.md의 .pyc 날짜 서술 오류.
- 원인 분석(lead, codex 의견 미확보): 결과를 만드는 쪽은 개수로, 보내는 쪽은 바이트로 제한해 단위가 어긋나고, 초과 안내에 진전하는 커서가 없다. 제안 설계는 `task-contract-wave2d.json`(실행 안 됨).

### 3-2. 화면 — UI-r3 critic minor 6
경고 토큰이 종료 상태·contract-live-test에도 붙음 / seek oninput 순서 수정의 회귀 테스트 없음 / `usd()`가 지수 표기('1E-7')를 못 받아 '금액 금액' 중복 문구 / `timeline()`의 재생 헤드 clamp 누락(기존 결함) / 연결 해제 뒤 과거 live turn에 승인 분리 문장이 안 보임 / `index.html:806` 문구·' · ' 연결 facts 줄 남음, 렌더 미관찰.

### 3-3. 설계문서 — D1-r5 critic minor 4
전송 시점 재인가가 `:654` 트랜잭션에 없음 / step-2 조기 종료의 트랜잭션 명시 부족 / 승인 시점 run 조회 방법 미기술 / 인용 검사기가 문서의 실제 앵커와 내용 검사를 묶지 않음.

### 3-4. 미실행
- S14: ego lite 실화면 1920·1280·375 다크 전후 비교, 합성 모델 종단·권한 3종·정상/실패/경계, axe, 8765·57888·Ego Space 전후 확인, `run_regression.py` 공식 전체 회귀(skip 0·Warning 0), 문서 checker.
- codex read-only 최종 검수(1회차 `codex-gate/review-1.md`는 Wave 1 때 것).
- S17 일부: I7 문구 정정, METHODOLOGY 절. 문서 등록·분류·승격은 하지 않음(별도 승인 대상).
- loretune-b2 아이콘 반영(피어 세션 보류 중) 시작 알림.

### 3-5. 사용자 결정 대기
- 회차 예산 여유 8KiB, 목록 쪽 크기 8, 취향 후보 상한 10(사람이 만든 후보 포함)의 기본값 유지 여부.
- `locked_fields` 재검사(새 잠금 저장소 필요) — 범위 밖, 결함 유지.
- 프로젝트 `__pycache__`에 작업 중 쓰인 .pyc(22:16:50, 22:55:17, 22:59:20) 삭제 여부. 원인은 `tests/test_general_chat_activation.py`의 하위 프로세스가 `-B` 없이 `app.py`를 실행한 것으로 추정, SRV-r3에서 수정.
- 1:1 이미지 메가픽셀 정의(유료 실측 필요), 16384 토큰 상한 적합성(count_tokens 유료, 미승인).

## 4. 실행 기록과 오류

| 실행 | 결과 |
|---|---|
| 읽기 전용 조사 워크플로 3개, Wave 1·W1b, 디자인 감사, 누락 점검 | `workflow-health.md` 표: 오류·빈 결과 0 |
| Wave 2 `wf_c133a2b4-507` | 10/10 완료, 오류 0. B2의 grep 1건 25분 지연(원인 [미확인]) |
| Wave 2b `wf_c196e942-beb` | 6/6 완료, 오류 0 |
| Wave 2c `wf_05ff58cd-abd` | 6/6 완료, 오류 0 |
| Wave 2d `wf_0a9d7999-977` | 사용자 지시로 즉시 중지, 변경 0 |
| codex MCP | Wave 1 검수 성공(gpt-6-astra). 2c 뒤 근본원인 의견: 1차 `model_not_found`(기본 모델 미지원), 2차 429 사용량 제한으로 실패 |
| ego lite | 0.6.0.20 실행 중, 업그레이드 설치됨(0.6.1.13)·재시작 대기(사용자 몫) |

외부·유료 모델 호출 0, count_tokens 0, `.env` 읽기 0, 서버 8765·57888 조작 0 [검증됨: 워크플로 계약·critic 점검 범위].

## 5. 문서 정리 (2026-10-28, 사용자 지시)
- 사용자 지시: "과거에 있던 핸드오프 문서는 없애줘" → 답변 "지워도 되는 핸드오프 즉, 작업을 다 완료한 핸드오프는 지워도돼", 새 인계 위치 "루트에도 둠", docs 인계 처리 "완료 8개 보관 폴더로 이동".
- 루트 `session-handoff.md`를 이 작업의 인계로 교체했다. 이전 원문(검토 카드 이동, 완료·수락)은 `.omo/evidence/agent-tools-02-20261028/before/session-handoff.md`에 바이트 그대로 있다(SHA-256 c8de806a…, 교체 전 해시 일치 확인).
- 완료·대체된 인계 8개를 `docs/`에서 `docs/archive/handoff/`로 옮겼다(이동 전후 SHA-256 일치): frontend-fq-vq, action-bridge, production-code-qa, session-transfer, research-first-pause, detailed-qa, criteria-api, spec-ms-001. 삭제한 파일은 없다.
- 미완료라 남긴 인계 3개: `docs/handoff-20261025-explicit-reader-live.md`(실제 Kling CDN 403 미해결), `docs/handoff-20261025-ledger-kling.md`(실제 공급자 검증 대기), `docs/handoff-20261025-guided-ontology-qa.md`(완료 선언 금지 항목).
- 갱신한 문서: README.md 맨 위 절, docs/qa/REMAINING-WORK.md 맨 위 절, 이 폴더의 PLAN-ko.md(§8-8, §8-9), REPORT-ko.md, HANDOFF-ko.md, next-work-plan.json.
- 문서 게이트(읽기 전용 실행, `.omo/evidence/agent-tools-02-20261028/doc-gate-end.txt`): blocked 유지(시작 때도 blocked). 이번 정리로 생긴 항목은 CLASSIFIED_FILE_MISSING 8(옮긴 파일의 예전 경로), UNCLASSIFIED_DOCUMENT 8(보관 폴더의 새 경로), PRESERVED_SOURCE_CHANGED 1(`session-handoff.md` 교체)이다. 이 밖에 이 작업의 증거 md(result.md 등)와 `docs/design/FRAME-OBSERVATION-DESIGN-ko.md`가 미분류로 잡힌다. 시작 때 있던 REGISTERED_SOURCE_OUTDATED 22건은 사라졌다. 누가 등록을 갱신했는지는 [미확인]이다(이 세션은 `.document-gate.json`을 수정하지 않음). 게이트 등록·분류 갱신은 별도 승인 대상이라 하지 않았다.
- 옮긴 8개 파일의 예전 경로를 참조하는 링크·manifest(파일당 약 115~120개 파일, 대부분 증거 해시 기록)는 고치지 않았다. 과거 증거의 원문이라 수정하지 않는다.

## 6. 파일 위치
- 계획·결정: `PLAN-ko.md`(§6, §8), 계약 `task-contract*.json`.
- 작업별: `tasks/<ID>/{result.md, changes.diff, start/, verdict-*.json}`.
- 디자인: `design-audit/verified-findings.json`, `design-gate/`.
- 다음 순서: `next-work-plan.json`, 인계: `HANDOFF-ko.md`.
