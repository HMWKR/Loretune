# UI-r3 결과 (UI-r2 critic minor 재작업)

- 시작 사본: `tasks/UI-r3/start/` (쓰기 대상 7개 파일, `tests/*.cjs`, `tests/test_*.py`). 이번에는 손대기 전에 복사했다.
- 전체 diff: `tasks/UI-r3/changes.diff`. 내가 고친 14개 파일만 담았다(소스 5개, 테스트 9개). chat-sidebar.js와 motion-studio.js는 바꾸지 않았다.
- start에 복사된 `test_*.py` 가운데 test_general_chat_body_cap.py, test_general_chat_media_d15.py, test_general_chat_scene_preference_tools.py, test_strict_wire_schema.py는 지금 start와 다르다. 이 파일들은 내가 편집하지 않았고, 동시에 진행 중인 다른 워커(SRV-r3)가 바꾼 것으로 보인다 [추정]. 그래서 diff에서 뺐다.
- 하지 않은 것: 실제 모델·공급자·유료 호출, count_tokens, .env, 8765/57888 서버, 브라우저 자동화, 파일 삭제.
- 읽은 기준 문서: impeccable `reference/craft-floor.md`, Hallmark SKILL.md의 Floor 절.

## 1. critic 지적별 처리

### 지적 1 — #3 일시 정지·재생 끝 표시와 위치 복원: 고침
- studio-media.js:81 `pause()`
  - 재생 중이었으면 `updatePlayhead(at,total,false)`를 한 번 부른다(`wasPlaying` 확인).
  - 재생 끝은 두 경로 모두 `pause()`를 거친다. tick의 `if(at>=total){pause();return;}`와 onended의 `seek(cut.end);if(at>=total)pause();`다. 그래서 끝난 뒤에는 정확한 총 길이가 표시된다.
  - 이미 정지한 상태에서 다시 부르면 아무것도 쓰지 않는다.
- studio-media.js:57-60 `timeline()`: 다시 그리기 전에 `sequence.time`(실제 위치 `at`)을 읽고(`const prior=sequence?.time`), 그 값으로 위치를 복원한다. 0.1초 단위로 내림한 `#sequenceSeek.value`는 쓰지 않는다. 시퀀스가 없을 때만 예전처럼 seek 값을 쓴다.
- 함께 고친 회귀 위험: studio-media.js:161과 165의 oninput.
  - 문제: 이제 pause가 정확한 위치를 seek 입력에 다시 쓴다. 그런데 기존 핸들러는 pause를 부른 뒤에 `e.target.value`를 읽는다. 그대로 두면 사용자가 끌어 놓은 값 대신 이전 위치를 읽는다.
  - 수정: 값을 먼저 읽고(`const t=e.target.value`) pause를 부른다.
- 증명: tests/ui_r2_contracts.cjs의 UI-r3 #3 블록. 실제 `createSequence`를 기존 `media_async_harness.cjs`로 실행한다.
  - 일시 정지: 재생 중 `seek(4.567)`의 표시는 `00:04.500 / 00:06.033`이다. `pause()` 뒤에는 `00:04.567 / 00:06.033`이고 seek 값은 `4.567`이다. 다시 pause를 불러도 쓰기는 0회다.
  - 재생 끝: 마지막 프레임 tick 뒤 표시는 `00:06.033 / 00:06.033`이다(이전 동작에서는 `00:06.000`). seek 값은 6.033이고 버튼은 '편집 재생'으로 돌아온다.
  - 다시 그리기: 재생 중 4.567(표시 4.5)에서 `timeline()`을 부르면 표시가 `00:04.567 / 00:06.033`, seek 값이 `4.567`이다.
  - 변이 검사(스크래치 사본):
    - start/studio-media.js → "pause shows the exact position"에서 실패.
    - pause 쓰기만 지운 변이 → 같은 단언에서 실패.

### 지적 2 — index.html:418, scene-studio.js:154 고지 잔여: 고침 (계약 결정대로 테스트 기대값도 같은 과업에서 변경)
- index.html:418 프레임 라벨: '…초의 실제 합성 프레임입니다.'로 끝낸다. "출력 승인은 별도입니다."는 지웠다.
- scene-studio.js:154 복구 status: '기존 변경안 저장을 확인했습니다. 입력은 그대로입니다.'
- 같은 유형이라 함께 정리한 것(UI-r2 result 3절 4번): studio-media.js:158 `#sequenceStatus`의 초기 문구를 '선택한 원본 Take를 확인합니다.'로 줄였다.
- 바꾼 테스트 기대값(단언을 약화하지 않았고, 정확한 문장 단언으로 바꿨다):
  - tests/timeline_motion_overlay.cjs:52: `/0\.500초의 실제 합성 프레임입니다\.$/` 일치와 '출력 승인은 별도' 불일치.
  - tests/central_frame_preview.cjs:13: `/실제 합성 프레임입니다\.$/` 일치와 '출력 승인은 별도' 불일치. 브라우저 테스트라 실행하지 않았다(`node --check`만 통과) [미검증].
  - tests/scene_ui_contract.cjs:83: status 전체 문장이 같은지 확인한다(`assert.equal`).
  - tests/ui_r2_contracts.cjs '#46': 418 "유지" 단언을 "제거" 단언으로 바꿨다. scene·sequenceStatus 제거 단언을 추가했다.

### 지적 3 — `.lt-cost-facts`를 비용·전송 사실에만 쓰고, 실제 경고에 경고 토큰을 쓰고, 고지 수 테스트를 넓히고, 온톨로지 덮어쓰기를 확인: 고침
- 비용이 아닌 범위 안내는 `.lt-cost-facts`에서 `.muted`로 옮겼다.
  - index.html:33 세계관 설정('새 승인 설정은 이후 작품에만 적용합니다.')
  - :34 자산함
  - :35 사용 중지
  - :39 보관
  - :40 연출 취향
  - :135/:259 'Take 검토는 출력 승인과 별도입니다.'(studio.css:619 선택자도 `>.muted`로 바꿨다)
  - scene-studio.js:21 `#sceneStudioApprovalScope`
- 경고 토큰
  - studio.css:546에 `.lt-ui .lt-cost-facts.lt-cost-warning { color:var(--ui-warning); }`를 추가했다. `--ui-warning`은 기존 토큰(#E6C58B)이다.
  - 적용 기준: 이 결정을 누르면 돈이 예약·사용되거나 자료가 전송되는 줄에만 붙인다.
    - index.html:805 미디어 카드 비용 줄. 단 contract-fake 모의 카드는 제외한다.
    - general-chat-ui.js:74 전송 검토 카드의 '최대 예약' 줄. 단 contract-fake는 제외한다.
  - '전송 없음·호출비 0'처럼 없음을 알리는 사실은 중립 facts로 둔다.
- 온톨로지 대화상자(index.html:32, 런타임 :310)
  - 확인 결과: 런타임은 `#ontologyDialog>p:not(.dialog-status)`, 즉 첫 `<p>`만 소개문으로 덮어쓴다. before/와 UI-r2 start에서는 전송·적용 문장이 그 첫 `<p>` 안에 있었다. 그래서 실제 화면에는 소개문만 보였다.
  - 판단: UI-r2가 이 문장을 분리하면서 의도치 않게 화면에 새로 노출됐다.
  - 수정: 이 줄을 `<details class="lt-provenance-detail"><summary>전송·적용 범위</summary>`로 옮겼다. 이제 기본 화면은 예전처럼 소개문만 보이고, 원문은 펼치면 볼 수 있다. 되돌리기 쉽다(아래 5절 1번).
- 고지 수 테스트 확대(ui_r2_contracts '#46')
  - 정규식이 '전송 없이', '전송은/이 없', '전송하지 않', '호출은/이 없', '호출하지 않'까지 잡는다.
  - 대화상자 10개만이 아니라 정적 페이지 전체에서 details 밖 일반 `<p>`가 0개인지 단언한다.
  - class 속성이 어느 위치에 있어도 muted나 facts면 제외한다.
  - 정적·리터럴 facts 줄 9개가 모두 비용이나 전송 어휘를 담는지 단언한다.
  - 대화상자별로 facts / muted / disclosure 종류를 단언한다.
- 넓힌 검사가 잡아 고친 것
  - index.html:19 채팅 소개 문단의 "직접 계획은 외부 전송 없이 저장됩니다."를 지웠다. 바로 아래 `#guidedBriefHelp`와 같은 사실이고, 런타임(:304)이 이 문단을 덮어쓴다.
  - index.html:24 '테스트 미디어는 … 외부 전송은 없습니다.'는 결정 지점의 전송 사실이므로 `.lt-cost-facts`로 바꿨다.
- 실측
  - `grep -c lt-cost-facts index.html`: start 15 → 8.
  - critic 방식(script·style·details 제거 후 키워드 별도|별개|미계측|전송|호출|승인이 아닙|청구|미연결)으로 센 정적 고지 문장: 14 → 12.
  - 측정 스크립트: scratchpad `density.py`.
- 증명
  - ui_r2_contracts '#46' 출력: `widened notice words outside disclosures 0; facts lines 9 all cost/transmission`
  - 'approval/transfer facts … warning token on real spend decisions'
  - general_chat_b2_cards.cjs:38(카드 warning), :111(live 검토 카드 warning, contract-fake는 중립)
  - 변이: start/index.html, start/studio.css, start/scene-studio.js가 각각 실패한다.

### 지적 4 — #41 요청당 한도 금액 형식: 고침
- index.html:625: `' · 요청당 한도 '+usd(cap.maximum_usd)`.
- 넓힌 테스트가 같은 유형 1건을 더 잡았다. general-chat-ui.js:17 `'사용량 기준 금액 $'+turn.usage_cost_usd`를 `usd(...)`로 바꿨다.
- 테스트 확대: ui_r2_contracts '#41'은 이제 쓰기 대상 6개 스크립트 전체에서 `$'+`, `$"+`, `` $`+ `` 이어 붙이기를 찾는다. 0개여야 하고, usd() 정의 자체만 예외다. 기존 `$${esc(` 검사는 그대로 둔다.
- 실측(실제 객체)
  - tests/test_chat_receipts.py가 실제 `ChatRuntime.capability()` 사전을 만든다. guard는 우회하고 adapter 호출은 없다. turn_cap_micro 1/3687/10000/100000으로 만들어 JSON으로 직렬화한 뒤 chat_receipts.cjs의 실제 `drawModelChat`에 넣는다.
  - maximum_usd 원문: "0.000001", "0.003687", "0.01", "0.1"
  - 화면: `요청당 한도 $0.000001 | $0.003687 | $0.01 | $0.1`
  - critic이 [추정]한 '1E-6' 표기는 허용 범위(1~100000)에서 나오지 않았다. 나오더라도 usd()가 '금액 확인 필요'로 막는다.
- general_chat_controls.cjs: VM에 제품 `usd()`를 넣었다. `사용량 기준 금액 $0.003687` 단언을 추가했다.

### 지적 5 — 괄호 면책 버튼, 비교 재생 매 프레임 쓰기, turn마다 반복되는 승인 문장: 고침
- index.html:571 생성 작업 버튼
  - 라벨에서 괄호 면책을 뺐다: '기존 접수 상태 다시 조회', '기존 결과 검토용 연결 재시도'.
  - 작업마다 `<p class="muted" id="generationNoNew-{id}">기존 요청만 확인하며 새로 생성하지 않습니다.</p>` 한 줄을 두고, 두 버튼을 aria-describedby로 연결한다.
  - 버튼이 없으면 도움말 줄도 만들지 않는다.
- 비교 재생(studio-media.js:72-74, :141-148)
  - 시퀀스와 같은 `writeTime(seekId,timeId,t,total,playing)`을 쓴다. 재생 중에는 0.1초 단위로, 값이 바뀔 때만 쓴다.
  - seek, 일시 정지, 재생 끝은 정확한 값을 쓴다. `updatePlayhead`는 이제 이 함수를 부르는 얇은 래퍼다.
- general-chat-ui.js:78
  - anthropic-live turn에서 반복하던 '모델 답변과 변경안의 적용·출력 승인은 별도입니다.'를 지웠다.
  - 이 사실은 `#generalChatHelp`(:68) 한 줄에만 남는다. 테스트는 이 파일에 "출력 승인은 별도입니다"가 1회인지 단언한다.
  - contract-fake turn의 '시험 응답이며 …'는 응답의 정체를 알리는 문장이라 남겼다.
- 증명
  - ui_r2_contracts '#7': 6개 파일에서 괄호 면책 버튼 0개.
  - '#41': 실제 `drawGeneration`으로 렌더해 라벨, aria-describedby, 작업당 muted 1줄, 버튼이 없을 때 도움말 없음을 확인한다.
  - 'compare playback': 실제 `comparison()`과 harness로 측정했다.
    - 1초 61프레임에서 텍스트 쓰기 9회, seek 쓰기 9회.
    - 일시 정지 `00:01.235 / 00:02.987`, 재생 끝 `00:02.987 / 00:02.987`.
  - 변이: compare tick만 되돌리면 "61 compare frames write the time text 60 times"에서 실패한다.

### 지적 6 — 렌더 미관찰: 이번 과업 범위 밖 (lead S14)
- 브라우저를 금지했으므로 렌더하지 않았다. 아래 7절 목록을 S14에서 확인해야 한다.

## 2. 테스트 명령과 결과 (/Users/leesungmin/Desktop/Loretune)
```
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/UI-r3/ui-modules.txt)
```
- 목록 `ui-modules.txt`는 UI-r2 `ui-modules-after.txt`와 같다(브라우저 테스트 제외).
- 결과(tests-after.log 끝):
  ```
  Ran 210 tests in 86.113s
  OK
  ```
- 첫 실행은 210개 중 1개가 실패했다(test_general_chat_ui_controls: `ReferenceError: usd is not defined`). 원인은 내 general-chat-ui.js:17 변경이고, 테스트 VM에 usd가 없었다. VM에 제품 usd()를 넣고 단언 1개를 추가해 고쳤다.
- 수정 전 기준선: 이번 과업에서는 따로 돌리지 않았다. UI-r2 critic의 재실행 결과(`Ran 210 tests / OK`)를 기준으로 삼는다.
- `node tests/ui_r2_contracts.cjs`: PASS 15줄. 래퍼의 기대 개수를 11에서 15로 바꿨다(새 블록 4개).
  ```
  PASS #3 pause: playing 00:04.500 -> paused 00:04.567 / 00:06.033
  PASS #3 end of playback: 00:06.033 / 00:06.033
  PASS #3 redraw restore: 4.567 -> 4.567
  PASS #7 dot-joined and parenthetical disclaimer buttons: 0 left
  PASS #46 index.html static notes: plain p with widened notice words outside disclosures 0; facts lines 9 all cost/transmission
  PASS approval/transfer facts outside disclosures: motion, agent settings, chat review, media card; warning token on real spend decisions
  PASS compare playback: 61 frames -> text 9 writes, seek 9 writes; pause/end exact
  ```
- `test_chat_receipts`: `Ran 7 tests / OK`. node 쪽에 4개 cap 값 deepEqual이 있다.
- 변이 검사: 스크래치 사본에서 파일 하나씩 start로 되돌려 `ui_r2_contracts.cjs`를 실행했다.
  - 실패로 잡힘(5/5): index.html, studio.css, general-chat-ui.js, studio-media.js, scene-studio.js.
  - chat-sidebar.js, motion-studio.js: 바꾸지 않았으므로 rc=0이 정상이다.
- 문법 검사(`node --check`): JS 5개, index.html 인라인 스크립트 7개, central_frame_preview.cjs 모두 통과.

## 3. 디자인 게이트
- Hallmark sloplint
  - 명령: `node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js scene-studio.js motion-studio.js --scope app --json`
  - 결과 파일: `design-gate/sloplint-after-r3.json`(rc=1, 기존 FAIL 때문).
  - FAIL 9 / REFLEX 1 / WARN 13. finding 키(gate·grade·file·evidence)가 sloplint-after-r2b.json과 같다: 새 항목 0, 사라진 항목 0. **새 FAIL 0.**
- impeccable detect(파일 모드)
  - 명령: `~/.claude/skills/impeccable/scripts/impeccable detect index.html`
  - 결과 파일: `design-gate/impeccable-after-r3.txt`(rc=2).
  - 본문이 impeccable-after-r2b.txt와 같다. 다른 곳은 r2b 파일 끝에 붙은 'rc=2' 줄 위치뿐이다.
  - broken-image 1건(기존, src 없는 `<img hidden>`)과 advisory 12건.

## 4. 의도된 테스트 기대값 변경 (단언 삭제·약화 없음)
- ui_r2_contracts.cjs
  - '#46'
    - 대화상자 5개의 범위 안내를 facts에서 muted로, 온톨로지를 disclosure로 바꾼 데 맞춰 기대 종류를 바꿨다.
    - 135/259 줄 단언을 `<p class="muted">`로 바꿨다.
    - 418 단언을 "유지"에서 "제거"로 바꿨다.
    - scene `#sceneStudioApprovalScope` class를 muted로 바꿨다.
    - 이유: 계약의 lead 결정 2개, 즉 고지 제거와 비용이 아닌 안내를 muted로 옮기는 것.
  - `NOTICE` 정규식을 넓혔다. 제외 조건도 class가 첫 속성일 때만에서 class 속성 어디서나로 바꿨다. muted 도움말이 id 뒤에 class를 둔 경우 오탐이었다.
- general_chat_b2_cards.cjs:38: 미디어 카드 비용 줄 기대 class를 `lt-cost-facts lt-cost-warning`으로 바꿨다(provider-unverified 카드는 실제 지출 결정이다). live 검토 카드 warning 단언을 추가했다.
- timeline_motion_overlay.cjs:52, central_frame_preview.cjs:13, scene_ui_contract.cjs:83: '…승인은 별도' 일치 단언을 정확한 새 문장 단언과 반복 부재 단언으로 바꿨다.
- test_ui_r2_contracts.py: PASS 개수 11 → 15.
- 추가만 한 것
  - chat_receipts.cjs와 test_chat_receipts.py: cap 줄 단언, 실제 capability() 입력
  - general_chat_controls.cjs: usd 주입과 금액 단언

## 5. 사용자 결정이 필요한 항목
1. 온톨로지 대화상자의 '외부로 전송하지 않습니다. 설정을 승인해도 기존 영상과 출력은 바뀌지 않습니다.'
   - 지금: 접힌 상세('전송·적용 범위')에 있다. UI-r2 이전처럼 기본 화면에는 런타임 소개문만 보인다.
   - 다시 기본 화면에 보이게 하려면 muted 한 줄로 되돌리면 된다.
2. 경고 토큰 적용 범위
   - 지금: 결정 지점 두 곳에만 쓴다(미디어 카드 비용, 전송 검토 예약).
   - 경고 토큰을 쓰지 않은 곳:
     - 대화 turn의 제안 가격 목록
     - 에이전트 설정의 대화 모델 단가 줄(`#agentSettingsCost`)
     - 작업 상태의 진행 중 비용 줄
   - 이 세 곳은 실제 금액이지만 버튼을 누르는 결정 지점이 아니어서 중립 facts로 뒀다. 넓힐지 결정이 필요하다.
3. 참고 승인 줄(index.html:31): 승인 범위와 전송 사실이 섞여 있다. 전송 사실이 있어 facts로 유지했다. 범위 부분만 muted로 나눌지 결정이 필요하다.

## 6. 남은 공백·결함 (rigor §2: 등재 유지)
1. index.html:806 미디어 작업 imported 상태 문구 '파일 검증과 Take 연결 완료 · 선택·검토 승인은 별도입니다.'
   - #46 유형의 반복이다. critic 지목 밖이라 고치지 않았다. Low.
   - `·`로 이어 붙인 메타 문자열이기도 하다(Hallmark Floor 10). 기존 문구다.
2. index.html:41 '외부 공급자 호출비 0 · 로컬 연산비 미계측. …' 등 기존 facts 줄의 `·` 연결(Hallmark Floor 10). 이번 과업 지목 밖이다. Low.
3. 고지 문장 밀도: critic 방식으로 14 → 12. 렌더 밀도 판정은 S14가 한다.
4. #3과 비교 재생: DOM 쓰기 횟수만 쟀다. 실제 렌더 비용은 trace로 재지 않았다.
5. central_frame_preview.cjs는 브라우저 테스트라 실행하지 않았다 [미검증].
6. 프로젝트 `__pycache__`의 .pyc 5개(22:16:50): 이번 과업 시작(파일 시각 기준) 전에 있던 것이다. 이번 과업에서 새로 생긴 .pyc는 없다. 모든 실행에 -B와 PYTHONDONTWRITEBYTECODE=1을 줬다.

## 7. 렌더 확인 대상 (lead S14) [미확인]
- 경고 토큰 줄(#E6C58B)의 대비와 무게: 미디어 카드, live 전송 검토 카드.
- muted로 옮긴 대화상자 안내 5개와 Take 검토 줄의 위치·크기.
- 온톨로지 대화상자: 소개문과 접힌 '전송·적용 범위'.
- 생성 작업 행: 동사 버튼 2개와 muted 도움말 1줄의 배치.
- 일시 정지·재생 끝·비교 재생 시간 표시가 정확한 값으로 끝나는지.
