# UI-r2 결과 (E1-design · B2-cards 재작업)

- 시작 사본: `tasks/UI-r2/start/` (쓰기 대상 7개 파일과 `tests/*.cjs`). `tests/test_budget_summary_ui.py`는 시작 시점에 복사하지 않았다. 그래서 내가 한 두 군데 치환을 되돌려 `start/tests-py-reconstructed/`에 원본을 다시 만들었다. 이 재구성은 [추정]이고, 치환 문자열이 각각 1회씩만 일치하는 것은 확인했다.
- 전체 diff: `tasks/UI-r2/changes.diff` (15개 파일).
- 쓰기 대상 밖의 파일은 수정하지 않았다.
- 쓰지 않은 것: 실제 모델·공급자·유료 호출, count_tokens, .env, 8765/57888 서버, 브라우저 자동화, 파일 삭제.

## 1. critic 지적별 처리

### E1 serious — 375px 헤더 작품 select: 고침
- 수정: studio.css:674 `.lt-ui .lt-studio-shell #songs`의 `flex:1`을 `flex:1 1 12rem`으로 바꿨다. 이 규칙이 뒤에 있어 :458을 덮어쓰고 있었다. 이제 두 규칙의 값이 같다.
- 증명: `tests/ui_r2_contracts.cjs` 'E1' 블록.
  - studio.css를 375×812 조건으로 cascade 계산한다. media 조건, 명시도, 순서, !important를 모두 반영한다.
  - 확인하는 승자 값: #songs `flex:1 1 12rem`(.lt-ui .lt-studio-shell #songs), `width:auto`, `min-width:0`, `max-width:none`, 셸 `flex-wrap:wrap`.
  - 변이 검사: start/studio.css로 바꾸면 `winning flex ... keeps a 12rem basis`에서 실패한다.
- 계산 근거 [추정, 렌더 미관찰]:
  - 셸 내용 폭은 375 − 2×0.75rem = 351px다.
  - 줄바꿈되는 flex 줄에는 기준 크기(basis)가 남은 폭에 들어가는 항목만 놓인다. 그래서 select는 192px(12rem)보다 줄어들지 않는다.
  - 브랜드 옆에 들어가지 않으면 다음 줄로 넘어가 351px까지 늘어난다.
  - 실제 화면은 lead가 S14에서 확인한다.

### B2 serious 1 (#46) — 지목된 위치 전부에 cost-facts 1줄 + provenance-detail 패턴: 고침
| 위치 | 변경 (file:line) |
|---|---|
| 모델 기본값 대화상자 | index.html:18. 안내 1줄을 남기고, Anthropic 미연결 문장은 `<details class="lt-provenance-detail">`로 옮겼다. 저장 버튼은 #7로 정리했다. |
| 채팅 초안 진행 | index.html:19. `.lt-cost-facts` "외부 전송·공급자 호출이 없습니다."를 두고, 비용 확인 위치와 로컬 연산비는 disclosure로 옮겼다. |
| Kling 준비 버튼 | index.html:31. #7 처리: 동사 라벨과 `#prepareGenerationHelp`. |
| 참고 승인 | index.html:31. 승인 범위와 전송 사실을 `.lt-cost-facts` 한 줄로 합쳤다. 결정 지점이라 둘 다 화면에 남겼다. |
| 렌더 작업 | index.html:31. 비용 줄은 `.lt-cost-facts`, 자막 형식은 disclosure. |
| 온톨로지 | index.html:32. 전송·승인 사실을 `.lt-cost-facts`로 분리했다. 런타임은 첫 `<p>`만 덮어쓰므로(index.html:310) 이 줄은 이제 화면에 남는다. |
| 세계관 설정 | index.html:33. 승인 적용 범위는 facts 줄, 권한 범위는 disclosure. |
| 자산함 | index.html:34. 사용권·승인 사실은 facts 줄, 연결 방식은 disclosure. |
| 사용권 · 보관 | index.html:35, :39. 결정 지점의 사실 1줄에 facts 스타일만 적용했다. |
| 예산 | index.html:37. 승인 아님은 facts 줄, 공급자·로컬 비용은 disclosure. 런타임 문구(index.html:314)도 이 facts 줄에 들어간다. |
| 운영 상태 | index.html:38. 공급자·연산비는 facts 줄, "요청 저장과 렌더 성공은 따로 기록"은 disclosure. |
| 연출 취향 | index.html:40. 사용권 사실은 facts 줄, 사용 범위 두 문단은 disclosure. |
| 출력 확인 | index.html:41. 비용 줄에 facts 스타일을 적용했다(런타임 문구는 그대로). |
| 135 / 259 | 사용 표시 `<small>` 뒤에 붙어 있던 " · 출력 승인과 별도"를 떼어 냈다. 대신 `<p class="lt-cost-facts">Take 검토는 출력 승인과 별도입니다.</p>`를 둔다(studio.css:617). |
| 409 | 프레임 선택 안내에서 반복 문장을 지웠다. |
| 418 | **유지.** 아래 미수정 항목 참고. |
| scene-studio.js | :10 소개 1줄과 '지원 범위와 입력 보관' disclosure. :19 에셋 패널의 중복 승인 문장 제거. :21 `.lt-cost-facts#sceneStudioApprovalScope`(저장/승인 결정 지점, :23 승인 버튼이 aria-describedby로 연결). :142 승인 직후 status의 중복 제거(:88 요약 줄이 같은 내용을 표시). |
| motion-studio.js:59 | 프레임 status에서 "영상 출력은 별도입니다." 제거. 승인 범위는 승인 버튼 옆에 있다(아래 minor). |

- 증명: `ui_r2_contracts.cjs` '#46' 블록.
  - 대화상자 10개 각각: facts 줄이 있다. disclosure 밖에서 '별도/별개/미계측/전송 없음'을 반복하는 일반 `<p>`는 0개다.
  - 135/259의 facts 줄 2개, 409 제거, scene 대화상자 disclosure 밖 '별도|별개'가 1회인지 확인한다.
  - 정적 index.html의 해당 일반 `<p>` 수를 실측하면 **0**이다.

### B2 serious 2 (S16) — 작업 상태 행과 대화 turn의 단가·종류·출처·개정·만료·출처 기록: 고침
- index.html:829 `mediaFactsDetail(f,withUnit)`: `withUnit`이면 맨 앞에 `단가 $X/초 · 문서 기준 추정`(f.unit, 종류 라벨 포함)을 붙인다. 카드 쪽은 비용 줄에 이미 단가가 있으므로 넘기지 않는다(중복 방지).
- general-chat-ui.js:78: turn disclosure가 `mediaFactsDetail(mediaFacts(x),true)`를 쓴다.
- chat-sidebar.js:94-104 작업 상태 provider 행:
  - facts 줄은 그대로 둔다(기존 테스트가 정확한 문자열을 고정).
  - 그 아래 `<details class="lt-provenance-detail"><summary>가격·출처 상세</summary>`를 붙인다.
  - 내용은 action별 라벨, 단가와 종류, 단가 출처 링크·개정·조회 시각, 견적 출처·개정·만료, 계산식, 제안 출처(대화 모델·권한·추론 강도)다.
  - 모든 값은 esc 또는 mediaFactsDetail의 link()를 거친다.
- 증명:
  - '#S16 work status': 실제 `workGroups` + `renderWorkStatus`를 실행해 detail 텍스트에 9개 사실과 `<a href=… rel="noopener noreferrer">`가 있는지 단언한다.
  - 'S16 turn detail': withUnit 출력이 단가로 시작하는지, 카드 detail에는 단가가 반복되지 않는지 확인한다.
  - 변이 검사: start/general-chat-ui.js와 start/chat-sidebar.js에서 각각 실패한다.

### minor
| 지적 | 처리 | 증명 |
|---|---|---|
| #23 visibilitychange 즉시 갱신 | **고침.** index.html:904 폴링 본문을 이름 있는 `pollState`로 만들고 `setInterval(pollState,1500)`로 등록했다. :937에 별도 리스너 `visibilitychange`(보이게 되면 `pollState()` 1회)를 두었다. 숨김 skip은 본문에 그대로 있다. | `ui_r2_contracts.cjs` '#23': 실제 슬라이스 실행 결과 숨김 상태에서 fetch 0회, 다시 보이면 1회. interval과 listener가 같은 함수인지도 확인한다. 기존 두 테스트(chat_model_polling, frontend_async)는 그대로 통과한다(슬라이스 표지만 변경, 아래 6절). |
| #3 시간 텍스트·seek 쓰기 | **고침.** studio-media.js:72 `updatePlayhead(t,total,playing)`: 재생 중에는 0.1초 단위로 내림한 값으로 표시하고, 값이 바뀔 때만 `#sequenceSeek.value`와 `#sequenceTime`에 쓴다. :88에서 seek가 `playing`을 넘긴다. 정지 상태와 사용자 seek는 ms 정밀도를 유지한다. | '#3' 실측(가짜 노드 setter로 횟수 계산): 1초 동안 61프레임에서 텍스트 쓰기 **11회**, seek 쓰기 **11회**. start 사본은 텍스트 쓰기 **61회**(변이 실패 메시지). 같은 값 재호출 시 0회, 정지 3.929초는 `00:03.929` 그대로. |
| #7 ' · ' 면책 버튼 | **고침.** 기본 선택 저장(index.html:18, `#modelSettingsSaveHelp`), `3D 장면 만들기`(scene-studio.js:3-7, `#sceneStudioButtonHelp`를 버튼 뒤에 두고 aria-describedby 연결), `문자 조합 정리`(motion-studio.js:33, 기존 도움말 `<p>`에 `#motionNormalizeHelp`와 `.muted`를 주고 연결, '한글 포함'은 도움말로 이동). 추가로 Kling `(전송 없음)`(index.html:31)도 처리했다. | '#7': 쓰기 대상 6개 파일에서 ' · '가 붙은 버튼 라벨이 0개다. 금액을 보여 주는 승인 버튼 2종(#41 의도)은 예외. 각 aria-describedby 대상 id와 .muted가 실제로 있는지도 확인한다. |
| #8 토글 라벨과 aria-expanded | **고침.** chat-sidebar.js:279 `toggleState`: chat 탭이 열려 있으면 'AI 대화 닫기'/expanded=true. 설정 탭이 열려 있으면 'AI 대화 보기'이고 aria-expanded를 **제거**한다(누르면 탭만 바뀌므로 disclosure가 아니다). 닫혀 있으면 'AI 대화 열기'/false. :286에서 적용한다. | '#8' 4개 상태 단언. |
| monotonous-spacing | **고침(토큰화, ignore 없음).** studio.css:31에 `--ui-space-half:.125rem`, :38에 `--ui-space-10:2.5rem`를 추가했다. 2px 11곳은 half, 4px는 `--ui-space-1`, 40px는 `--ui-space-10`. 처음 쓴 `calc(var(--ui-space-8)+var(--ui-space-2))`는 detector가 패딩 0으로 읽어 `cramped-padding`(#preview .empty)이 새로 나와서 단일 토큰으로 바꿨다. | impeccable-after-r2b.txt: monotonous-spacing 없음, cramped-padding 없음. '#spacing' 단언: padding/margin/gap의 px 리터럴 0개(.sr-only `margin:-1px`만 예외). 16px 루트 기준 계산값은 같다. |
| 승인·전송 사실을 결정 지점으로 | **고침.** motion-studio.js:7 'disclosure 승인 범위'를 지우고 `#motionApprovalScope`를 승인 툴바 바로 앞에 보이게 두었다(motionApprove aria-describedby). chat-sidebar.js:43 `preferenceScopeNote`("편집 권한과 관계없이 최종 출력·비용·전송·사용권 승인은 별도입니다. 계정 삭제는 금지합니다.")를 폼 안 권한 select 뒤에 두고 aria-describedby로 연결했다. disclosure에는 편집 방식만 남겼다. general-chat-ui.js:74 "자료 파일 자체는 전달하지 않습니다."를 disclosure 밖으로 빼서 승인 버튼 aria-describedby에 연결했다. 미디어 카드(index.html:805)의 "표시된 지시와 …만 전송합니다."도 disclosure 밖으로 뺐다(summary는 '가격·출처·출력 조건'). | 'approval/transfer facts' 블록 4개 표면. |
| #41 금액 형식 | **고침.** Kling 준비 카드(index.html:571 `usd()`), 예산 요약(index.html:592 한도·사용 가능·확인 사용액·진행 중·추정액·초과 전부 `usd()`, 'X USD' 표기 제거). 같은 성격인 기존 모델 대화 사용량 줄(index.html:631)도 `usd()`로 바꿨다. | '#41': 실제 `drawGeneration`을 실행하면 `예상 비용 $0.7`(이전 `$0.70`). index.html 안 `$${esc(` 직접 조립은 0개다. test_budget_summary_ui: `한도 $10 · 사용 가능 $9.9`, `확인된 사용액 $0`, `사용량 기준 추정액 $0.1`, ' USD' 없음. chat_receipts.cjs: `모의 사용량 계산 $0`. |
| currentReviewTarget kind+id | **고침.** general-chat-ui.js:78 버튼에 `data-general-review-kind`. :48 `currentReviewTarget(turn,id,scope,kind)`가 `target.kind===kind&&target.id===id`로 찾는다. 클릭과 valid() 모두 kind를 넘긴다. | general_chat_review_navigation.cjs: 같은 id에 kind 'video' → null 단언 추가. |
| facts 목록과 provider 그룹 수 일치 | **고침.** chat-sidebar.js:87 provider 그룹 레코드에 `jobIds`를 둔다. :94 facts는 그 집합에 job이 있는 action만 쓴다. 준비 기록(action)이 없는 작업은 `agent-work-note` "준비 기록이 없는 작업 N건은 가격 정보를 표시하지 않습니다."로 센다(studio.css:982,985). | 'S16 work status': 그룹 2건 = facts 1 + 미표시 1. 다른 대화 action의 job은 그룹과 facts 양쪽에서 빠진다. 미표시가 없으면 note가 없고, 가격 action이 없으면 disclosure가 없다. |
| 브라우저 렌더 미검증(E1 · B2) | **미수정.** 이번 과업은 브라우저 자동화를 금지한다. lead S14 대상. | — |

## 2. 고치지 않았거나 일부만 유지한 것(이유)
- **index.html:418 "출력 승인은 별도입니다."**: tests/central_frame_preview.cjs:13과 tests/timeline_motion_overlay.cjs:52가 이 문장을 단언한다. 단언을 약화하지 않으려고 유지했다. 로드된 프레임 라벨에만 남기고 409 안내에서는 지웠다.
- **scene-studio.js:88 요약, :154 복구 status의 "구성 승인은 별도"**: 요약은 후보 생성 버튼 옆 결정 지점이다. :154는 tests/scene_ui_contract.cjs:83 `/구성 승인은 별도/` 단언 때문에 유지했다. 지웠다가 테스트 실패를 보고 되돌렸다.
- **'· 별도 실행 이력'(chat-sidebar.js:50 summary), general-chat-ui.js:68/:78 도움말·turn별 "…출력 승인은 별도입니다."**: critic 지목 위치가 아니어서 이번에는 손대지 않았다. 결함 후보로 아래에 등재한다.

## 3. 새로 발견한 결함(미수정, 등재)
1. index.html:571 `drawGeneration`의 작업 버튼 라벨에 괄호 면책이 남아 있다. '기존 접수 상태 다시 조회 (새 생성 없음)', '기존 결과 검토용 연결 재시도 (새 생성 없음)'. #7과 같은 유형이지만 ' · '가 아니라 괄호다. Medium(문구, 접근 가능한 이름).
2. studio-media.js:146 비교 재생 tick이 `#compareSeek.value`와 `#compareTime`을 매 프레임 쓴다. #3과 같은 유형이지만 critic이 지목한 updatePlayhead 밖이다. Medium(성능).
3. general-chat-ui.js:78 turn마다 "모델 답변과 변경안의 적용·출력 승인은 별도입니다."가 반복되고, :68 도움말과도 겹친다. #46 유형. Medium.
4. studio-media.js `#sequenceStatus` 초기 문구 "선택·승인은 별도입니다." 반복. #46 유형. Low.
5. impeccable `broken-image`(src 없는 `<img hidden>`): 시작 사본부터 있던 항목이다. 처리하지 않았다.

## 4. 테스트
명령(/Users/leesungmin/Desktop/Loretune):
```
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/UI-r2/ui-modules-after.txt)
```
- 목록: B2 ui-modules-after(브라우저 실행 테스트 제외)에 test_ui_r2_contracts, test_save_feedback, test_comment_draft를 더했다.
- 수정 전(ui-modules.txt, tests-before.log): `Ran 202 tests in 84.875s / OK / rc=0`
- 수정 후(tests-after.log): `Ran 210 tests in 88.498s / OK / rc=0`
- `node tests/ui_r2_contracts.cjs` 출력 11줄(PASS 전부):
  - `E1 375 #songs cascade: flex 1 1 12rem from ".lt-ui .lt-studio-shell #songs", shell flex-wrap wrap`
  - `#3 playhead: 61 playing frames -> text 11 writes, seek 11 writes`
  - `#41 Kling card renders 예상 비용 $0.7`
  - `#46 index.html static notes: plain p with 별도/별개/미계측/전송 없음 outside disclosures 0`
  - `S16 work status: facts 1 + unpriced note 1 = group count 2; ...`
  - `spacing px literals: 0` 외 5줄
- 변이 검사(스크래치 복사본, 원본 무변경): 7개 파일을 하나씩 start 사본으로 되돌리면 모두 실패했다. 7/7 검출. 예: start/studio-media.js → "61 frames over 1 s write the time text 61 times", start/studio.css → "winning flex … 12rem basis".
- `node --check`: JS 5개와 index.html 인라인 스크립트 7개 모두 통과.
- 실행하지 않은 것: 브라우저 테스트(chat_sidebar.cjs, work_status.cjs URL 모드, central_frame_preview). 금지 사항 때문이다. [미검증]

## 5. 디자인 게이트
- Hallmark sloplint(`node ~/.claude/skills/hallmark/scripts/sloplint.mjs index.html studio.css general-chat-ui.js chat-sidebar.js scene-studio.js motion-studio.js --scope app --json`) → design-gate/sloplint-after-r2b.json (rc=1, 기존 FAIL 때문).
  - 결과: FAIL 9 / REFLEX 1 / WARN 13.
  - finding 키(gate, grade, file, evidence)로 after-b2와 비교: 새 항목 0, 사라진 항목 0. after-e1 대비 새 FAIL 0.
  - FAIL 게이트: 20, 34×4, 39a, 50, 56, 76 (기존).
- impeccable detect(파일 모드, `impeccable detect index.html`) → design-gate/impeccable-after-r2b.txt (rc=2).
  - anti-pattern: broken-image 1건만 남음(기존). monotonous-spacing이 **사라졌다**.
  - advisory 12건은 그대로다.

## 6. 의도된 테스트 변경(단언 약화·삭제 없음)
- tests/chat_model_polling.cjs, tests/frontend_async_regressions.cjs: 슬라이스 표지를 `setInterval(async()=>{…},1500);`에서 `const pollState=async()=>{…};setInterval(pollState,1500);`로 바꿨다. 이유: #23 즉시 갱신에 같은 폴링 함수를 써야 한다. refresh()를 쓰면 편집기 DOM 전체를 다시 그리고 draft를 초기화한다. 단언은 그대로다.
- tests/general_chat_review_navigation.cjs, tests/general_chat_b2_cards.cjs: 버튼 픽스처에 `data-general-review-kind`/`generalReviewKind`를 넣었다. `current(...)` 호출에 kind 인자를 추가했다. kind 불일치 시 null 단언을 **추가**했다.
- tests/test_budget_summary_ui.py: VM에 제품 `usd()`를 주입했다. 기대값 변경(#41 의도):
  - '확인된 사용액 0' → '$0'
  - '사용량 기준 추정액 0.1 USD' → '$0.1'
  - 한도·사용 가능 표기와 ' USD' 부재 단언 추가
- tests/chat_receipts.cjs: VM에 `usd()`를 주입하고 `모의 사용량 계산 $0` 단언을 추가했다.
- 새 파일: tests/ui_r2_contracts.cjs, tests/test_ui_r2_contracts.py.

## 7. 남은 공백
- 렌더 미관찰 [미확인]:
  - 375 헤더의 실제 폭
  - takeReviewStatus facts 줄 배치
  - 작업 상태 행 disclosure와 note 줄바꿈
  - 새 .muted 도움말 위치(3D 버튼 아래, 저장 버튼 아래, Kling 버튼 아래)
  - 온톨로지 facts 줄이 런타임에 새로 보이는 것
  - lead S14 대상.
- #3: 렌더 비용이 실제로 줄었는지는 trace로 측정하지 않았다. 측정한 것은 DOM 쓰기 횟수뿐이다.
- S16: 실제 서버 투영(1:1 이미지, 단가 없음)으로 작업 상태 disclosure를 렌더하지는 않았다. 픽스처 투영만 썼다.
- 동시 작업: 다른 워커(SRV-r2, D1-r4)는 내 쓰기 대상 밖이다. changes.diff에는 내 변경만 있는 것으로 보인다(파일별 변경 줄 수 확인). [추정]

## 8. 사용자 결정이 필요한 항목
1. 설정 탭이 열린 상태의 토글: 'AI 대화 보기'로 하고 aria-expanded를 빼는 현재 방식을 확정할지, 대신 누르면 패널을 닫는 동작으로 통일할지.
2. 재생 중 시간 표시 0.1초 단위: 이 단위로 둘지, 1초 단위로 더 줄일지. 정지·seek는 ms 그대로다.
3. 온톨로지 대화상자: 이전에는 런타임이 지우던 전송·승인 사실 1줄이 이제 보인다. 유지할지.
4. 418 프레임 라벨, scene :154 status의 "…승인은 별도" 문장: 테스트가 고정하고 있어 남겼다. 지우려면 테스트 기대값 변경 승인이 필요하다.
5. 3절에서 새로 발견한 결함 5건을 다음 라운드에서 고칠지.
