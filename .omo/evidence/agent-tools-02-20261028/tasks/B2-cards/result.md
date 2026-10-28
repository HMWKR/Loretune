# B2-cards 결과

시작 사본: `tasks/B2-cards/start/`(SHA256SUMS 검증 OK). 전체 diff: `tasks/B2-cards/changes.diff`(10개 파일, +464/-35).
실제 모델·공급자·유료 호출, count_tokens, .env, 8765/57888 서버, 브라우저 자동화, 파일 삭제는 쓰지 않았다.

## 항목별 변경

| 항목 | 변경(file:line) |
|---|---|
| S5 영상 미디어 action으로 가는 대화 검토 이동 | general-chat-ui.js:25 `reviewTargets`가 `prepare_video_action`을 kind `video`로 해석한다. chat-sidebar.js:146 `reviewMediaAction`이 role image와 video를 모두 허용한다. |
| S8 3D·모션 제안으로 가는 이동, dirty 3D 입력 보존 | general-chat-ui.js:25 `propose_scene_3d`는 kind `scene`, `propose_motion_scene`은 kind `motion`으로 해석한다. general-chat-ui.js:88 클릭 처리기가 kind에 따라 `reviewStudioProposal`로 보낸다. chat-sidebar.js:174 `reviewStudioProposal`이 dirty/blocked/superseded/missing을 판정하고, 장면을 조용히 전환한 뒤 런처를 연다. 이어서 `reveal(id)`을 부르고 포커스를 옮긴 다음 `data-review-arrival`을 표시한다. scene-studio.js:163과 motion-studio.js:64의 `reveal`은 저장하지 않은 입력이 있으면 `'kept'`를 반환하고 덮어쓰지 않는다. 공개 API는 scene-studio.js:166, motion-studio.js:68, chat-sidebar.js:360이다. |
| S16 D15 표시 표면 | **카드**: index.html:799 `mediaActionMarkup`과 index.html:812-829 헬퍼 `usd`, `mediaFacts`, `mediaFactsLine`, `mediaFactsDetail`. 결정 지점에는 견적 총액과 종류, 단가, 길이, 만료, 모델과 프로젝트 선택의 차이, 이유를 보인다. 출처·개정·계산식·대화 모델·권한·추론 강도·전송 조건은 `<details>` 안에 둔다. **대화 turn 요약**: general-chat-ui.js:78 `general-chat-facts`와 '제안 가격·출처 상세'. **작업 상태**: chat-sidebar.js:91 provider 그룹 행에 facts 줄을 붙인다. **재열기**: 저장된 투영을 그대로 렌더한다. 실제 서버 투영을 JSON으로 복제해도 같은 마크업이 나오는지 테스트로 확인했다. **3D 대기 변경안 origin**: scene-studio.js:84. |
| D21 에이전트 설정 요약 | chat-sidebar.js:45 `#agentSettingsCost`(lt-cost-facts). chat-sidebar.js:229 대화 모델, 사용자가 선택한 모델, 입력/출력 단가(100만 토큰당 · 문서 기준 · 청구 아님), 회차당 최대 예약, 대화 상한 안 최대 회차. chat-sidebar.js:47 상세 disclosure에는 개정, long-context, 토큰 상한, 권한, 추론 강도, 출처 링크, 정책을 둔다. |
| #41 금액 형식 하나 | index.html:812 `usd()`(소수점 끝 0 제거, 숫자가 아니면 '금액 확인 필요'). general-chat-ui.js:11 `money`가 이를 쓴다. 승인 버튼에 금액을 표시한다: 카드는 '이 조건 승인 · $X', 대화 전송 검토는 '확인한 내용 승인 · 최대 $X'(general-chat-ui.js:74). |
| #44 주 동작 하나 | studio.css:552 주 버튼 강조를 미디어 승인/실행과 대화 승인에 적용했다. studio.css:757 `.media-action-decisions` 배치, studio.css:761 편집은 텍스트 버튼이다. |
| #45 오류 요약 | index.html:161 오류일 때 '오류 · 원인'(40자 초과는 …로 자르고, 빈 값이면 '오류'). 오류가 아닌 비정형 알림은 '알림' 그대로다. |
| #46 비용은 앞에, 부차 정보는 disclosure | 카드, 대화 turn, 전송 검토 카드('비용 상한 적용 방식'), 설정 요약, 모션 소개(motion-studio.js:7 '승인 범위')에 적용했다. lt-cost-facts는 studio.css:542(기존)와 studio.css:979-980(작업 행)이다. |
| #49 비활성 사유 연결 | index.html:30 `#prepareMedia aria-describedby="mediaPreparationHint"`. |
| toolLabels ↔ ALLOWED_TOOLS 일치 | 코드는 이미 일치했다(14개). 이를 고정하는 테스트를 추가했다: tests/test_general_chat_b2_cards.py `ToolLabelTest`. node로 실제 `toolLabels` 줄을 평가해 집합이 같은지, 라벨이 비어 있지 않은지, 내부 이름이 라벨에 들어 있지 않은지 확인한다. |
| B1 이월 I1 턴 간 이름 구분 | general-chat-ui.js:56-57 `reviewLabel`이 `'요청 N · {장면} {종류} [i/n ]검토|보기 (상태)'`를 반환한다. 프롬프트가 같은 두 턴도 접근 가능한 이름이 서로 다르다. |
| 도착 표시 | studio.css:754-755 `[data-review-arrival]` 아웃라인. forced-colors는 studio.css:785이다. |

## 의도된 테스트 기대값 변경(단언 약화·삭제 없음)

- tests/general_chat_review_navigation.cjs
  - target 구조에 `kind`를 추가했다. 이유: S5/S8에서 image, video, scene, motion을 구분하려면 필요하다.
  - 라벨이 `'target 제작안 …'`에서 `'요청 N · target 이미지 제작안 …'`으로 바뀌었다. 이유: I1 턴 순번 표시, 종류 표시.
  - "턴이 달라도 이름이 같아도 된다"는 단언을 "턴이 다르면 이름이 다르다"로 바꿨다. 이유: I1 요구가 반대 방향이다. 같은 프롬프트로 두 턴을 만드는 단언도 추가했다.
  - refresh 슬라이스 VM에 제품 D15 헬퍼를 주입했다. 이유: turn 요약이 이 헬퍼를 쓴다.
- tests/studio_notice.cjs: 오류 요약 `'알림'`을 `'오류 · '+원인`으로 바꿨다. 이유: #45 의도된 변경이다. 긴 원인 잘림, 빈 원인('오류'), 비오류 알림은 '알림'이라는 단언을 추가했다.
- 구현 보정: general-chat-ui.js에서 `reviewMedia` 매핑을 `reviewTargets` 안으로 옮겼다. 이유: 테스트가 함수를 슬라이스해 쓰므로 함수 밖의 상수를 참조하면 ReferenceError가 났다. 동작은 같다.

## 새 테스트

- tests/general_chat_b2_cards.cjs. 출하된 파일에서 제품 함수를 잘라 실행한다. 검사 항목:
  - 금액 형식
  - D15 카드: agent 다른 모델 영상, local-owner, 예전 action, fixture/문서 추정, 불일치, 만료, 작업 청구 상태, 재열기 동일성
  - #44 CSS, #49
  - turn 요약과 가격 변화 재렌더
  - video, motion, scene target과 변이
  - I1
  - 전송 검토 카드 #41/#46
  - `reviewMediaAction` video
  - `reviewStudioProposal`: opened, kept, dirty(다른 장면 차단, 같은 장면 허용), blocked(런처 비활성, 포커스 실패), missing(없는 id, 낡은 참조, 장면 없음, reveal missing), superseded
  - 실제 motion·scene `reveal`의 dirty 보존
  - 클릭 처리기의 kind 분기, kept 시 포커스 유지
  - 작업 상태 facts
  - D21 설정 요약(값이 있는 경우, 없는 경우)
  - 인자로 받은 실제 서버 투영
- tests/test_general_chat_b2_cards.py
  - `ToolLabelTest`
  - `B2CardsTest`: A2a의 격리 HTTP/SQLite 픽스처로 실제 투영을 만든다(agent full_access/high 다른 모델 이미지, Store 재열기, local-owner, 예전 action, 차단된 다른 영상 모델). 이것을 cjs에 넘긴다. 미디어 실행, 예약, 전송이 0인지 단언한다.
  - 기존 두 cjs도 실행한다.
- 변이 검사(스크래치, 원본 무변경): 제품 코드에 결함 21종을 넣어 보았다. 전부 테스트가 잡았다. 처음에는 "포커스 확인 제거" 1종이 살아남아 테스트를 추가했다. 로그: `/private/tmp/claude-501/-Users-leesungmin-Desktop-Loretune/1ebfb89f-9e94-4156-8aea-2393f299eb3e/scratchpad/b2-mut1/mutation.log`

## 테스트 명령과 결과

```
cd /Users/leesungmin/Desktop/Loretune
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/B2-cards/ui-modules-after.txt)
```
목록은 기준 목록(ui-modules-nobrowser.txt)에 test_general_chat_b2_cards, test_general_chat_media_d15, test_general_chat_media_preparation, test_chat_general_http를 더한 것이다.
```
Ran 202 tests in 82.744s

OK
rc=0
```
(기준: `Ran 130 tests in 29.825s OK`, tests-before.log). 전체 로그: tasks/B2-cards/tests-after.log

`node --check`: general-chat-ui.js, chat-sidebar.js, scene-studio.js, motion-studio.js, index.html 인라인 스크립트 7개가 모두 통과했다.

## 디자인 게이트

- Hallmark sloplint
  - 명령: `node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js scene-studio.js motion-studio.js --scope app --json` → design-gate/sloplint-after-b2.json (rc=1, 기존 FAIL 때문)
  - 결과: FAIL 9 / REFLEX 1 / WARN 13. after-e1과 같다. finding 키(gate, grade, file, evidence)로 비교해 새 항목 0, 사라진 항목 0이다.
  - 주의: `files: 2`이다. JS는 sloplint 검사 대상이 아니다.
- impeccable detect(파일 모드)
  - 명령: `~/.claude/skills/impeccable/scripts/impeccable detect index.html` → design-gate/impeccable-after-b2.txt (rc=2)
  - 결과: broken-image 1, monotonous-spacing 1. after-e1과 같다(기존 항목).

## 남은 공백

- 브라우저 테스트(chat_sidebar.cjs, work_status.cjs URL 모드, central_frame_preview)는 금지 사항 때문에 실행하지 않았다. 실화면, 포커스 이동, 아웃라인, 줄바꿈 배치를 눈으로 관찰하지 않았다. [미검증]
- #46을 index.html의 정적 안내(약 18-41, 135, 259, 409, 418행)와 Scene Studio 고지 문단에는 적용하지 않았다. 이유: 범위 판단이 필요하다.
- 대화 작업의 중단 버튼은 턴 간 이름이 겹칠 수 있다. I1은 검토 버튼에만 적용했다.
- 작업 상태 facts는 작업(job)이 있는 action만, provider 그룹에만 표시한다.
- 1:1 이미지는 메가픽셀 정의가 공개되지 않아 단가가 비어 있다. 이때 카드에는 '단가 기록 없음' 계열 문구가 나온다(A2a 결정을 그대로 표시). [추정] price가 없는 경우만 테스트했고, 실제 1:1 투영은 렌더하지 않았다.
- impeccable monotonous-spacing과 broken-image는 기존 항목이고 처리하지 않았다.
- `reveal`이 'kept'를 반환해도 3D/모션 창은 열린다. 상태 문단에 안내하고 그쪽으로 포커스를 옮긴다.

## 사용자 결정이 필요한 항목

1. 순번 표시 형식 `'요청 N · …'`
   - 질문: 이 형식으로 확정할지, 다른 표기(예: 시각, 프롬프트 앞부분)를 쓸지.
   - 근거: I1은 이름 구분만 요구했다. 'N'은 현재 대화 안에서 턴의 순번이다.
2. 'kept' 동작
   - 질문: 저장하지 않은 입력이 있을 때 창을 열고 입력을 보존하는 현재 방식을 유지할지, 열지 않고 차단할지.
   - 근거: S8은 "dirty 3D 입력 보존"만 명시했다.
3. 오류 라벨 잘림 길이
   - 질문: 40자로 둘지.
   - 근거: #45가 길이를 정하지 않았다.
4. 범위 밖 #46 나머지
   - 질문: index.html 정적 안내와 Scene Studio 고지에도 같은 disclosure 패턴을 적용할지.
   - 근거: 화면 구조가 바뀌므로 승인이 필요하다.
