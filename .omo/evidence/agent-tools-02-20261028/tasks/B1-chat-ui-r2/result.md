# B1-chat-ui 재작업 2차 결과

작성일: 2026-10-28 · 트랙: B1-chat-ui(rework 2)
쓰기 범위: `general-chat-ui.js`, `chat-sidebar.js`, `studio.css`, `index.html`(카드 마크업·setStep·포커스·장면 클릭 경로만), `tests/general_chat_review_navigation.cjs`, `tests/test_general_chat_review_navigation.py`

입력으로 읽은 자료:
- PLAN-ko.md §6·§8
- 1차 결과 `tasks/B1-chat-ui/result.md`
- critic 판정 원문(wf_18a38ed0-25d journal 14행, id B1-chat-ui, 결함 9건)
- `codex-gate/review-1.md`(B1 관련 #9: 모바일 중간 포커스 이동)

편집 전 사본은 `before/`에 있다. 전후 diff는 `source.diff`(126줄, 10 hunk)에 있다.
`studio.css`와 `tests/test_general_chat_review_navigation.py`는 바꾸지 않았다. `diff -q` 결과 동일하다.

## 결함별 조치

### 1) I4: 375에서 장면 클릭이 미리보기 탭으로 포커스를 가져감 [수정]

**원인**: 검토 이동이 장면 버튼을 `button.click()`으로 누른다. 그러면 `index.html:1022`의 모바일 리스너가 `choose('preview', true)`를 호출해 미리보기 탭에 포커스를 준다. 그 뒤에 카드가 다시 포커스를 받는다.

**수정 1**: `chat-sidebar.js:151-152`
- 프로그램 클릭 직전에 `button.dataset.reviewNavigation = ''`를 붙인다.
- `try { button.click(); } finally { delete … }`로 클릭 직후 플래그를 지운다.
- 주석 1줄을 추가했다.

**수정 2**: `index.html:1022`
- 리스너를 `choose('preview', !('reviewNavigation' in shot.dataset))`로 바꿨다.
- 패널 전환은 그대로 한다. 카드가 보여야 하기 때문이다. 포커스 이동만 생략한다.
- 실제 사용자 클릭(마우스·키보드)에는 플래그가 없으므로 동작이 이전과 같다(`true`).

**테스트**: `tests/general_chat_review_navigation.cjs:117-123`
- index.html의 실제 리스너 줄을 `line()`으로 잘라 VM에서 실행한다.
- 실제 `reviewMediaAction`과 결합해 다음을 단언한다.
  - 검토 이동 중 호출 → `['preview', false]`
  - 이후 사용자 클릭 → `['preview', true]`
  - 데스크톱 클릭과 장면이 아닌 클릭 → 호출 없음
  - 클릭 뒤 플래그 제거

### 2) 테스트 공백 [수정]

- **성공 분기 포커스 미복원**: `cjs:145`
  - 탐색 스텁이 도착 카드에 포커스를 둔 뒤 `'opened'`를 반환한다.
  - 클릭 뒤에도 `activeElement`가 그 카드여야 한다. 이 단언으로 restoreFocus가 호출되지 않았음을 확인한다.
  - critic이 보고한 생존 변이(`always-restore-focus`)가 이제 잡힌다.
- **카드 aria-labelledby**: `cjs:82-85`
  - index.html의 `mediaActionMarkup` 함수 전체를 slice하고, 제품 `esc`를 주입해 VM에서 실행한다.
  - article의 `aria-labelledby` 값과 유일한 h3 `id`가 같은지 단언한다.
  - 따옴표가 든 id(`act"1`)로 이스케이프 일관성도 확인한다.
- **toolLabels 6개**: `cjs:86-88`
  - `const toolLabels=` 줄을 VM에서 평가해 6개 키의 한국어 문자열이 정확히 같은지 deepEqual로 비교한다.
- **도착 CSS 규칙**: `cjs:89`
  - `studio.css`의 `.lt-ui .media-action-card[data-review-arrival] {` 줄이 `outline:2px solid var(--ui-focus);`를 쓰는지 단언한다.
- **사이드바가 실제로 없는 경우**: `cjs:149`
  - `h.c.window={}`로 사이드바를 없앤다.
  - 다음 3가지를 단언한다: 호출 0회, blocked 문구, 원래 버튼으로 포커스 복귀.
  - 기존 `async()=>undefined` 케이스는 그대로 두었다.

### 3) I1: 턴 사이 이름 중복 [수정]

- `general-chat-ui.js:64`
  - 각 턴의 요청 문단 `<p class="general-chat-text">`에 `id="generalChatTurnPrompt-<turn id>"`를 붙였다.
  - 그 턴의 검토 버튼에 `aria-describedby`로 같은 id를 연결했다.
  - 턴 id는 서버의 `uuid.uuid4().hex`이다(`chat_general.py:534`). 공백이 없어 idref로 쓸 수 있고, 턴마다 유일하다.
- 주석: `general-chat-ui.js:43`
- 모델명은 넣지 않았다. 같은 모델로 보낸 두 턴은 모델명으로 구분되지 않기 때문이다.
- **테스트**: `cjs:63-71`
  - 서로 다른 턴 2개에 같은 장면 대상을 1개씩 둔다.
  - 보이는 이름은 같다(`target 제작안 검토` ×2). 이 상태를 그대로 기록했다.
  - describedby 값은 서로 다르다.
  - 각 describedby id는 마크업에 정확히 1번 존재하고, 그 문단 텍스트는 각 턴의 요청(`첫 요청`, `둘째 요청`)이다.

### 4) I3: 중간 실패 시 반쯤 전환된 화면 [수정하지 않음 — 지시대로 한계로 기록]

되돌리기 장치는 넣지 않았다. 수락한 한계는 다음과 같다.

| 실패 시점 | 실패 사유 | 남는 상태 |
|---|---|---|
| 대화창을 닫은 뒤 | dirty·missing·superseded | 닫힌 대화창은 닫힌 채로 남는다 |
| `setStep(3)`·장면 클릭 뒤 | 위와 같음 | 단계 3과 바뀐 장면이 남는다 |

- 저장 데이터·편집 초안·대화 초안은 바뀌지 않는다. 바뀌는 것은 화면 위치뿐이다.
- 실패 문구와 원래 버튼으로의 포커스 복귀는 그대로 동작한다(1차 테스트로 확인).
- 사전 확인(장면 버튼 존재·활성)은 대화창을 닫기 전에 실행된다. 따라서 그 단계에서 실패하면 화면이 전혀 바뀌지 않는다.
- 되돌리기를 하지 않은 이유: 되돌리려면 상태를 한 번 더 바꿔야 하고, 포커스도 한 번 더 이동한다. 결국 I4 문제가 다시 생긴다(1차 기각 가설과 같음).

### 5) 가운뎃점 '·' [변경 없음 — lead 결정대로 유지, 사용자 확인 필요]

- toolLabels 6개는 기존 라벨 관용에 맞춰 '·'를 유지했다. 예: `이미지 제작안 준비 · 실행 없음`
- 이는 **Hallmark Floor 10(가운뎃점 메타 문자열 금지)과 다르게 간 알려진 지점**이다.
- sloplint는 JS를 검사하지 않는다(`files: 2`). 그래서 이 문자열에 대한 기계 판정은 없다.

## 실행한 명령과 결과 꼬리(원문)

모든 Python 실행은 `/Users/leesungmin/Desktop/Loretune`에서 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B`로 했다.

### 1. 관련 테스트 5모듈 → `tests-focused.log`

명령: `-m unittest tests.test_general_chat_review_navigation tests.test_general_model_schedule_ui tests.test_agent_work_status_context tests.test_chat_general_http tests.test_general_chat_media_preparation -q`

결과: rc=0
```
----------------------------------------------------------------------
Ran 68 tests in 41.778s

OK
```

### 2. index.html을 읽는 브라우저 없는 기존 테스트 12모듈 → `tests-html-readers.log`

명령: `budget_summary_ui, caption_image_recovery, chat_display, chat_ui, desktop_layout, desktop_refinement, execution_disclosure, frontend_visual_residual, runway_image_pipeline, studio_media, studio_state, take_rights_ui -q`

결과: rc=0
```
Ran 49 tests in 5.567s

OK
```

### 3. node VM 4종 → `tests-node-vm.log`

모두 rc=0이다.
```
Exact turn/run/action references, product escaping, distinct names, focus restore, reason codes and asynchronous scoped focus contracts passed
general_chat_review_navigation rc=0
28 general chat button states and unknown/zero cost distinction passed
general_chat_controls rc=0
8 history approval scenarios and scoped history/cost copy passed
general_chat_history_ui rc=0
scoped model availability, local recovery, and general/legacy reservation UI scenarios passed
general_model_schedule_ui rc=0
```

### 4. 변이 확인 → `mutation.log`

방법: 스크래치 사본 `/private/tmp/claude-501/-Users-leesungmin-Desktop-Loretune/1ebfb89f-9e94-4156-8aea-2393f299eb3e/scratchpad/b1r2mut/`에서 한 군데씩 되돌린 뒤 VM 테스트를 실행했다.

결과: 11건 모두 rc=1로 실패했다. 즉 테스트가 모든 변이를 잡았다.
```
index-focus-always rc=1 AssertionError [ERR_ASSERTION]: programmatic review click does not focus the preview tab
no-flag rc=1 AssertionError [ERR_ASSERTION]: step heading and mobile panel focus are skipped; only the card receives focus
flag-not-removed rc=1 AssertionError [ERR_ASSERTION]: navigation flag is removed after the programmatic click
always-restore-focus rc=1 AssertionError [ERR_ASSERTION]: success keeps focus on the arrival card; the chat button is not refocused
no-aria-labelledby rc=1 AssertionError [ERR_ASSERTION]: card article carries aria-labelledby
mismatched-labelledby rc=1 AssertionError [ERR_ASSERTION]: aria-labelledby matches the card heading id
no-describedby rc=1 AssertionError [ERR_ASSERTION]: turns are separated by aria-describedby
no-prompt-id rc=1 AssertionError [ERR_ASSERTION]: describedby target exists once: generalChatTurnPrompt-turn
toolLabel-typo rc=1 AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
css-literal-color rc=1 AssertionError [ERR_ASSERTION]: arrival outline uses the focus token
no-optional-sidebar rc=1 TypeError: Cannot read properties of undefined (reading 'reviewMediaAction')
```
참고: 첫 실행에서 css 변이 문자열이 파일 안에서 유일하지 않아(4회 등장) 스크립트가 중단됐다. 선택자를 포함한 문자열로 좁혀 다시 실행했고, 두 실행의 출력이 모두 로그에 있다.

### 5. Hallmark sloplint

명령: `node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js --scope app --json > design-gate/sloplint-after-r2.json`

결과: rc=1. 원인은 기존 FAIL이다.

| | fails | reflex | warns | files | 항목 수 |
|---|---|---|---|---|---|
| 기준선 | 18 | 73 | 16 | 2 | 107 |
| 이후 | 18 | 73 | 16 | 2 | 107 |

줄·열을 제외하고 항목을 비교했다. **새로 생긴 항목 0건, 사라진 항목 0건**이다.

### 6. impeccable detect (index.html, HTML 파일 대상)

결과: before rc=2, after rc=2. 출력은 같다(`[broken-image] <img> with no src attribute`).
- 편집 전부터 있던 결함이며, 이번 변경으로 생긴 것이 아니다.
- 쓰기 범위(카드·setStep·포커스·장면 클릭 경로) 밖이라 고치지 않았다.
- 로그: `impeccable-before.txt`, `impeccable-after.txt`

## 기존 단언을 의도적으로 바꾼 곳

- `cjs:116` 성공 경로의 이벤트 기대값이 `'shot:target'`에서 `'shot:target:quiet'`로 바뀌었다.
  - 이유: 결함 1의 계약 변경이다. 이제 프로그램 장면 클릭에 포커스 생략 플래그가 반드시 실려야 한다.
  - 기존 단언은 약해지지 않았고 더 강해졌다.
- 같은 줄의 메시지 문구에 'mobile panel focus'를 추가했다.
- 다른 기존 단언은 삭제하거나 완화하지 않았다.

## 남은 공백 / 안 한 일

- **실화면 검증은 하지 않았다** — 지시상 브라우저 금지. 다음 항목은 **[미확인]**이며 main이 aside로 확인해야 한다.
  - 375에서 실제 포커스 순서(미리보기 탭을 거치지 않는지)
  - 도착 outline의 가시성·대비·잘림(1280/375 × 다크/라이트)
  - 스크린리더가 describedby를 실제로 읽는지
- **헤드리스 Chrome을 띄우는 기존 테스트는 이번에 실행하지 않았다** — 브라우저 금지. 대상:
  - `test_central_frame_preview`, `test_chat_model_polling`, `test_proposal_ui`, `test_timeline_motion_overlay_ui`
  - `tests/work_status.cjs`
  - 관련 UI 4모듈(`test_work_status_ui`, `test_chat_sidebar_ui`, `test_general_chat_ui_controls`, `test_general_chat_history_ui`)
  - 1차 때는 모두 통과했다. 이번 변경 뒤의 결과는 [미확인]이다.
- **describedby 대상이 요청 전문이다.** 요청은 최대 2000자이므로 설명이 길게 읽힐 수 있다. 발췌용 요소는 지시 범위(최소 변경) 때문에 만들지 않았다.
- **'대화 작업 중단' 버튼에는 describedby를 붙이지 않았다.** 지시 범위는 검토 버튼뿐이다. 진행 중 턴이 둘 이상이면 이 버튼 이름도 겹칠 수 있다 **[추정]**.
- I3 한계: 위 4) 참조.
- Floor 10 차이: 위 5) 참조.

## 사용자 결정이 필요한 사항

1. **가운뎃점(Floor 10) 차이를 받아들일지**
   - 근거: lead가 기존 관용을 유지하기로 결정했다. 같은 파일의 기존 라벨(`이미지 제작안 준비 · 실행 없음` 등)과 index.html 곳곳이 '·'를 쓴다.
   - 선택지:
     - (a) 유지(현재)
     - (b) 새 6개만 괄호 등으로 바꾸기 — 같은 목록 안에서 표기가 섞인다
     - (c) 전체 라벨 정리 — 범위가 커진다
2. **I3 한계를 받아들일지, 되돌리기 장치를 요청할지**
   - 근거: 위 4)의 표. 데이터는 보존되고 화면 위치만 남는다. 되돌리면 포커스가 한 번 더 튄다.
3. **(선택) 검토 버튼 설명을 요청 전문 대신 짧은 발췌로 바꿀지**
   - 근거: 요청 최대 2000자(`general-chat-ui.js` textarea `maxlength="2000"`)

## 확신도

- [검증됨] 위 테스트·변이·sloplint·detect 결과(로그 원문 있음), 플래그 경로의 VM 동작
- [미확인] 실브라우저 포커스·가시성, 스크린리더 낭독
