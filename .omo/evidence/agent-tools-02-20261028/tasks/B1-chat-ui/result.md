# B1-chat-ui 결과 — 검토 카드 이동 개선 I1~I6 + 다음 단계 도구 라벨

작성 2026-10-28 · 작업자 B1-chat-ui · 쓰기 범위: `general-chat-ui.js`, `chat-sidebar.js`, `studio.css`, `index.html`(지정 줄만), `tests/general_chat_review_navigation.cjs`, `tests/test_general_chat_review_navigation.py`
전체 diff: `source.diff`(편집 전 사본 `before/` 대비). 편집 전에 `impeccable/reference/craft-floor.md`와 Hallmark Floor(1·2·6·7·10)를 읽음.

## 한 일 (파일별)

### general-chat-ui.js
- toolLabels에 다음 단계 도구 6개 한국어 라벨 추가(지시 문구 그대로): get_generation_job, estimate_media_plan, prepare_video_action, get_agent_settings, propose_preference_rule, propose_scene_3d.
- I1·I5: `reviewTargets`가 `{id, shot, approval, job:boolean}`을 돌려준다. 새 `reviewLabel()`이 같은 턴에서 같은 장면 대상이 2개 이상이면 순번 `1/2`를 붙이고, 결정이 끝났으면 동사를 '검토'에서 '보기'로 바꾸고 상태를 덧붙인다: `(승인됨|보류됨|거절됨|작업 생성됨)`. 예: `장면 제작안 2/2 보기 (거절됨)`. 서버 ID는 data-* 속성에만 둔다. 승인 상태가 바뀌면 다시 렌더된다(turnData에 포함).
- I5: 검토 버튼과 중단 버튼을 기존 `.general-chat-actions`로 감쌌다. 버튼이 없으면 묶음도 만들지 않는다.
- I3: `controls()`가 `[data-general-review-action]`도 다룬다. 검토 버튼은 `busy||inFlight`일 때만 비활성이다. dirty·대기 중 요청·연결 없음은 이동을 막지 않는다. 같은 장면의 미저장 초안에서도 카드를 열 수 있어야 하기 때문이다.
- I3: 턴 목록을 다시 렌더할 때 포커스가 검토·중단 버튼에 있었다면 렌더 뒤 같은 버튼(action+turn 또는 cancel turn)으로 포커스를 되돌린다. 기존 :53-56 패턴을 따랐고 `focusKey`·`restoreFocus`를 썼다.
- I2·I3: 클릭 핸들러
  - busy/inFlight이면 `진행 중인 요청이 끝난 뒤 다시 시도하세요.`를 표시한다(예전에는 아무 반응이 없었다).
  - 대상이 사라졌으면 missing 문구를 표시한다. 단 대화 범위가 바뀌었으면 표시하지 않는다.
  - 결과 코드별 문구: dirty·missing·blocked는 서로 다른 해결 행동을 안내한다. superseded와 다른 대화로 바뀐 경우는 문구를 내지 않는다. 사이드바가 없으면(undefined) blocked 문구를 낸다.
  - 성공하면 상태 문구를 비운다(예전 실패 문구 제거).
  - 실패하면 다시 렌더된 같은 버튼으로 포커스를 되돌린다.

### chat-sidebar.js — `reviewMediaAction`
- 반환값이 boolean에서 사유 코드로 바뀌었다: `'opened' | 'superseded' | 'missing' | 'dirty' | 'blocked'`.
- 사전 확인: 다른 장면 대상이면 모달을 닫거나 단계를 바꾸기 **전에** 장면 버튼이 정확히 1개이고 활성인지 확인한다. 실패하면 화면을 바꾸지 않고 'blocked'를 돌려준다.
- `setStep(3, { focus: false })`로 단계 제목 포커스를 건너뛰어, 마지막 카드 포커스 하나만 남긴다(I4).
- 마지막 단계(카드 보임·포커스)가 실패하면 `choose('chat')`으로 채팅 패널에 돌아온 뒤 'blocked'를 돌려준다. 그래서 상태 문구가 보이는 곳에 표시되고, 포커스는 핸들러가 원래 버튼으로 되돌린다(I2).
- 도착에 성공하면 카드에 `data-review-arrival`을 붙인다. 이 표시는 마우스와 키보드 모두에서 보이고, 카드가 blur되면 `{once:true}`로 제거된다(I4).

### index.html (지정 줄만)
- `setStep(step,{focus=true}={})`: 기본 동작은 그대로 두고, `focus:false`일 때만 `#flowHeading` 포커스를 생략한다. 기존 호출 7곳은 모두 숫자 1개만 넘겨 영향이 없다 [검증됨: grep].
- `mediaActionMarkup`: article에 `aria-labelledby="mediaActionTitle-<id>"`, h3에 같은 id를 줬다(I4 카드 접근 이름).

### studio.css
- `.lt-ui .media-action-card[data-review-arrival] { outline:2px solid var(--ui-focus); outline-offset:var(--ui-space-1); }`를 추가했다. 기존 토큰만 썼고 리터럴 색, 전환, 모션은 없다. 모션이 없으므로 reduced-motion 대체도 필요 없다.
- forced-colors 블록의 기존 `:focus-visible` 규칙에 같은 선택자를 추가해 `outline-color:Highlight`가 적용되게 했다.

### tests/general_chat_review_navigation.cjs (I6)
- 완료 단언: `process.on('beforeExit')`에서 `completed` 플래그가 없으면 exitCode=1로 만든다.
- 제품 esc 주입: index.html의 `esc=s=>…`를 슬라이스해 VM에 주입한다(복제본 제거). 속성 경계 입력 `a" onfocus="x' b`가 `&quot;`·`&#39;`로 이스케이프되는지 단언한다.
- 마커 누락은 `slice`·`line`이 assert로 즉시 실패한다(빈 문자열로 조용히 통과하지 않음).
- 새 케이스
  - 같은 장면 2개와 다른 장면 1개 → 이름 3개가 서로 다르고 내부 ID가 노출되지 않는다.
  - 결정이 바뀌면 꼬리말이 갱신된다.
  - `.general-chat-actions` 묶음이 생기고, 빈 묶음은 만들지 않는다.
  - 다시 렌더한 뒤 검토·중단 버튼 포커스가 복원된다.
  - controls()에서 busy/inFlight만 검토 버튼을 막는다.
  - reviewMediaAction의 사유 코드를 전부 확인한다: dirty, 같은 장면+dirty 성공, 사전 확인 blocked(모달 미닫힘·단계 미전환), superseded 2종, missing 2종, 마지막 단계 실패 시 채팅 복귀.
  - setStep에 focus:false가 전달된다.
  - 도착 표시가 붙고 blur 시 제거된다.
  - 실제 onclick 줄의 분기: busy, inFlight, 성공 시 문구 비움, dirty·missing·blocked 문구와 포커스 복귀, 사이드바 없음, superseded 침묵, 다른 대화 침묵, 대상 없음, stale scope 침묵.
  - 이동 중 run 제거: 실제 핸들러와 실제 reviewMediaAction을 결합해, 지연된 모달이 닫히기 전에 run을 지우면 missing 문구와 버튼 포커스 복귀가 일어나는지 확인한다.
- 의도적으로 바꾼 기존 단언: 반환값 `true/false`가 사유 코드 문자열로 바뀌었고, 이동 이벤트 `'step:3'`이 `'step:3:quiet'`로 바뀌었다. reviewTargets의 기대값에 approval·job이 추가됐다. 이유는 I2·I3·I4의 의도된 계약 변경이다.

### tests/test_general_chat_review_navigation.py
- `assertIn('contracts passed', result.stdout)` 추가(종료코드만 보던 공백 보완).

## 변이(mutation) 확인 — 테스트가 회귀를 잡는지
스크래치 복사본에서 한 군데씩 되돌린 뒤 VM 테스트를 실행했다. 8건 모두 rc=1로 실패했다.
```
never-resolves rc=1 did not complete
no-render-focus rc=1 AssertionError [ERR_ASSERTION]: markup was replaced
no-handler-focus rc=1 AssertionError [ERR_ASSERTION]: dirty returns focus to the originating button
setStep-focus rc=1 AssertionError [ERR_ASSERTION]: step heading focus is skipped; only the card receives focus
no-ordinal rc=1 AssertionError [ERR_ASSERTION]: Expected values to be strictly deep-equal:
no-precheck rc=1 did not complete
no-chat-return rc=1 AssertionError [ERR_ASSERTION]: final-step failure returns to the chat pane where the status is visible
weaker-product-esc rc=1 AssertionError [ERR_ASSERTION]: attribute boundary is escaped by the product esc
```

## 실행한 테스트 명령과 결과 꼬리 (원문)
1. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest tests.test_general_chat_review_navigation tests.test_general_model_schedule_ui tests.test_agent_work_status_context tests.test_chat_general_http tests.test_general_chat_media_preparation tests.test_media_creator -q` → `tests-focused.log`
```
----------------------------------------------------------------------
Ran 83 tests in 44.252s

OK
```
2. 이전 작업자의 관련 UI 6개(4모듈, 기존 puppeteer 헤드리스 테스트, 임시 포트 0): `... -m unittest tests.test_work_status_ui tests.test_chat_sidebar_ui tests.test_general_chat_ui_controls tests.test_general_chat_history_ui -v` → `tests-related-ui.log`
```
----------------------------------------------------------------------
Ran 6 tests in 8.372s

OK
```
3. index.html·UI 소스를 읽는 기존 테스트 16모듈: `... -m unittest tests.test_budget_summary_ui tests.test_central_frame_preview tests.test_caption_image_recovery tests.test_chat_display tests.test_chat_model_polling tests.test_chat_ui tests.test_desktop_layout tests.test_desktop_refinement tests.test_execution_disclosure tests.test_frontend_visual_residual tests.test_runway_image_pipeline tests.test_proposal_ui tests.test_studio_media tests.test_studio_state tests.test_timeline_motion_overlay_ui tests.test_take_rights_ui -q` → `tests-html-readers.log`
```
----------------------------------------------------------------------
Ran 56 tests in 28.845s

OK
```
4. node VM 5종 → `tests-node-vm.log`. 모두 rc=0이다. 첫 줄은 다음과 같다.
```
Exact turn/run/action references, product escaping, distinct names, focus restore, reason codes and asynchronous scoped focus contracts passed
```
skip은 0건이다(위 세 실행 모두 `OK`이고 `skipped=` 표기가 없다).

## Hallmark sloplint (정적, --render 없음)
`node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js --scope app --json > sloplint-after.json` (rc=1, 기존 FAIL 때문)
- 기준선 `{'fails': 18, 'reflex': 73, 'warns': 16, … 'files': 2}` → 이후 `{'fails': 18, 'reflex': 73, 'warns': 16, … 'files': 2}`.
- gate·grade·file·evidence 기준으로 비교한 결과 새로 생긴 항목 0건, 사라진 항목 0건이다. 줄 번호 이동은 비교에서 제외했다.
- 주의: `files: 2`이므로 sloplint는 index.html과 studio.css만 검사했고 JS 2개는 검사하지 않았다. JS 문구는 Floor 10을 손으로 확인했다(아래).

## 안 한 일 / 남은 빈칸
- 실화면 증거(aside, 375·1280, 마우스 도착 표시 캡처, 375에서 다른 장면 이동)는 지시대로 하지 않았다(main 담당). 따라서 도착 outline이 실제로 보이는지, 대비가 충분한지는 **[미확인]**이다.
- 모바일에서 장면 버튼을 클릭하면 index.html:1022 핸들러가 `choose('preview', true)`로 미리보기 탭에 포커스를 한 번 더 준다. 쓰기 범위 밖이라 그대로 두었다. 최종 포커스는 카드로 가지만 중간에 한 번 튀는 현상이 남아 있다.
- I1의 구분은 **같은 턴 안**에서만 보장된다. 서로 다른 턴의 `장면 X 제작안 검토` 버튼끼리는 이름이 같을 수 있다(턴 article 단위로 묶임).
- 모델명은 이름이나 설명에 넣지 않았다. 순번과 결정 상태만으로도 같은 턴 안에서는 유일하다. 모델명을 넣으면 좁은 폭에서 버튼이 길어진다.
- I7(증거 문구, 테스트 :37-41의 '공개 사본 변조' 단언), I8(거절 카드 버튼, 대화 복귀 경로), S5·S8(영상·3D 이동)은 범위 밖이라 하지 않았다.
- 도착 표시는 카드가 다시 렌더되면(drawMediaCreator) 포커스와 함께 사라진다. 따로 상태를 저장하지 않았다.

## 가정·추측
- Hallmark Floor 10(가운뎃점 메타 문자열 금지)에 따라, 계획서 예시 '보기 · 거절됨' 대신 `보기 (거절됨)`처럼 괄호를 썼다. 지시에서 문구를 그대로 준 toolLabels 6개는 '·'를 포함한 채 반영했다. 이는 기존 UI 관용과 같으며, sloplint는 JS를 검사하지 않아 판정이 없다. 이 충돌은 main이 판단할 사항이다.
- job이 있는 제작안의 꼬리말은 job 세부 상태 대신 `작업 생성됨` 하나로 표시했다. 세부 상태 라벨은 카드에 있다.
- 검토 버튼 비활성화는 `disabled`를 썼다. 기존 결정·중단 버튼과 같은 방식이다. busy 중에는 index.html sendRequest가 원래 모든 버튼을 끄므로, 핸들러의 busy 문구는 그 사이에 클릭된 경우를 대비한 보조 경로다.

## 기각한 가설
- "도착 강조는 `:focus` 선택자만으로 충분하다" → 기각. 카드 안의 비포커스 영역을 마우스로 눌러도 tabIndex=-1인 카드가 포커스를 받아 강조가 뜬다. 도착 시점에만 붙고 blur 때 제거되는 속성 방식을 택했다.
- "마지막 단계 실패 시 단계·샷 전환을 되돌린다" → 기각. 되돌리면 상태를 또 바꾸고 포커스도 다시 튄다. 그 대신 다음 두 가지로 대응했다.
  - 모달·단계·샷을 바꾸기 전에 할 수 있는 확인(장면 버튼)을 먼저 해서, 그 단계의 실패는 화면을 전혀 바꾸지 않게 했다.
  - 마지막 단계 실패는 채팅으로 돌아와 문구를 보여 주고 포커스를 버튼으로 되돌린다.
- "포커스 복원에 CSS 속성 선택자를 쓴다" → 기각. action ID에 따옴표가 들어오면 선택자가 깨진다. dataset을 비교하는 방식으로 대체했다.

## 절차상 기록
- 확인 중에 기존 브라우저 테스트 `tests/chat_sidebar.cjs`를 URL 인자 없이 직접 1회 실행했다. Chrome 헤드리스가 뜬 뒤 `page.goto(undefined)` 오류로 끝났고 브라우저는 스크립트의 finally에서 닫혔다. 이후 `pgrep`으로 확인했을 때 잔존 Chrome 헤드리스는 0이었다. 8765·57888에는 접근하지 않았다.

## requests_for_other_tracks
- (index.html 소유자 또는 main) `index.html:1022` 모바일 `#shotlist` 클릭 → `choose('preview', true)`의 포커스 이동 때문에 검토 카드 이동 중 포커스가 한 번 더 튄다. 프로그램에 의한 클릭(이동 경로)에서는 포커스를 생략하는 방안을 검토해 주세요.
- (트랙 D, I7) `tests/test_general_chat_review_navigation.py:37-41`의 '공개 사본 수정' 단언은 원리상 실패할 수 없다. 이 단언의 정정은 이번 작업에서 하지 않았다.
- (main, 실화면) 다음 증거를 aside로 확보해 주세요.
  - 1280·375 × 다크·라이트 각각 마우스 클릭으로 이동한 뒤 도착 outline이 보이는지
  - 같은 장면 다중 대상의 버튼 이름
  - dirty 상태에서 다른 장면으로 이동할 때의 문구와 포커스
  - 375에서 다른 장면으로 이동하는 경우
