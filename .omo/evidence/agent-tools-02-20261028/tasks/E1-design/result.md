# E1-design 결과

- 범위: verified-findings.json `confirmed` 52건 중 E1 배정분 + 375px 헤더 작품 select
- 시작 사본: `tasks/E1-design/start/` (SHA256SUMS 7/7 OK, 편집 후 재확인 [검증됨])
- 시작 사본 대비 diff: `tasks/E1-design/changes.diff` (7파일, 80 hunk)
- 편집 파일: index.html, studio.css, chat-sidebar.js, general-chat-ui.js, studio-media.js, scene-studio.js, motion-studio.js
- 테스트 파일은 수정하지 않았다. 단언 약화·삭제 없음.
- 렌더 관찰은 하지 않았다. 과업이 브라우저 자동화를 금지하므로 모든 시각·배치 결과는 [미확인]이다.

## 1. 항목별 처리

줄 번호는 편집 후 현재 파일 기준이다.

### High
| # | 처리 | 위치 |
|---|---|---|
| 1 | 끌기 없이 너비를 바꾸는 '좁게/넓게' 버튼 그룹(role=group)을 추가했다. 키보드 Shift 단계와 같은 ±48px를 쓰고, 최소·최대에 닿으면 비활성화한다. 핸들과 함께 숨겨지고, 대화가 모달로 옮겨지면 함께 옮겨진다. 288px 넘침을 막으려고 헤더에 flex-wrap을 줬다. | chat-sidebar.js:25-26, 206, 230, 249, 284-285 / studio.css:946, 1027-1029 |
| 14 (=38) | `</option value="ip">` 마크업 오류를 고쳐 'IP 기본 취향' 옵션을 복구했다. | index.html:40 |
| 15 | 짧은 라벨 '4 출력'을 '4 편집'으로 바꿨다. 이제 긴 이름 '4 편집·출력'의 앞부분과 같다. | index.html:1057 |
| 16 | 시간 비례 막대는 그대로 둔다. 축 정렬을 깨지 않기 위해서다(critic 반박 반영). 대신 같은 기능을 하는 컨트롤을 뒀다. 각 컷 행의 번호(#)를 버튼으로 바꿨고, 누르면 해당 트랙 컷을 클릭한 것과 똑같이 그 위치를 미리 본다. 버튼은 28px 열 + min-width 26px이다(WCAG 2.5.8 동등 컨트롤 예외). | index.html:424, 561 |

### Medium
| # | 처리 | 위치 |
|---|---|---|
| 2 | 비활성 글자색을 --ui-disabled 하나로 통일했다(505, 730). 286과 421은 505로 흡수했다(286은 box-shadow만 남김). 레거시 75의 opacity 비활성은 색으로 바꿨다. | studio.css:75, 285, 498, 719 |
| 4 (=19) | 첫 상태를 `opened = !narrow.matches`로 바꿨다. 좁은 화면으로 처음 들어오면 작업 영역이 먼저 보인다. | chat-sidebar.js:49 |
| 5 | 호버 테두리를 --ui-control로 바꿨다. | studio.css:496 |
| 6 | 분할바 평상시 색을 --ui-control로, hover와 focus 색을 --ui-marker로 바꿨다. | studio.css:987-988 |
| 7 | 버튼 이름에서 면책 문구를 빼고, 그 문구는 aria-describedby 도움말로 옮겼다. 해당 버튼: '에이전트 설정 저장', '전송 내용 준비', '계획 미리보기'. 24fps 규격 나열은 `<dl>`로 바꿨다. 트랙 컷 이름의 가운뎃점은 쉼표로 바꿨다. | chat-sidebar.js:39-40 / general-chat-ui.js:7 / index.html:19, 23 / studio.css:1033-1034 / studio-media.js:62 |
| 8 | 토글 이름이 동작을 말하도록 바꿨다. chat 탭이 열려 있으면 'AI 대화 닫기', 그 밖에는 'AI 대화 열기'다. | chat-sidebar.js:229 |
| 9 | sloplint 24b 72건과 원시 20px 9곳을 --ui-space-* 토큰으로 바꿨다. 매핑: 2-3px→space-1, 5-7px→space-1(칩)/space-2, 9-10px→space-2, 14px→space-3/4, 20px→space-6(gap은 space-4). 178행 20px은 격자 열 폭이라 제외했다. | studio.css 전반 (24b 72→0) |
| 17 | 대화 런처를 제목 행의 닫기 버튼 앞으로 옮겼다. 제목 행이 없으면 첫 h2 뒤에 둔다. autofocus가 없는 대화상자는 기존 닫기 버튼(renderConfirm은 #dismissRender)이 처음 포커스를 받는다. | chat-sidebar.js:271-274 / studio.css:1026 |
| 18 | 검토 패널에서 Esc를 누르면 열린 details를 먼저 닫는다. 입력 필드에서 누른 Esc는 패널을 닫지 않는다. | chat-sidebar.js:302 |
| 20 | 장면 검증 실패 경로 3곳에서 aria-invalid와 aria-describedby=sceneStudioStatus를 설정하고, 다시 입력하면 해제한다. 오류 테두리 CSS가 select에도 적용되게 했다. | scene-studio.js:99-100, 131-132 / studio.css:290 |
| 21 | `.lt-ui :where(p,li,h1,h2,h3,label,summary,dt,dd,small,legend){word-break:keep-all;overflow-wrap:anywhere}`를 추가했다. | studio.css:1022 |
| 22 | #compareButton의 max-width와 nowrap을 제거했다. 단계 바에 flex-wrap을, flow-nav에 overflow-x:auto를 줬다. 80px 열은 critic 근거가 반박돼 수정하지 않았다. | studio.css:378-379, 621 |
| 23 | 숨겨진 탭에서는 폴링을 건너뛴다(`globalThis.document?.hidden`). 제안된 'visibilitychange 즉시 1회 갱신'은 넣지 않았다. 이유: 테스트 2개(chat_model_polling, frontend_async_regressions)가 `setInterval(async()=>{`부터 `},1500);`까지 문자열로 잘라 실행하므로, 콜백에 이름을 붙이거나 밖으로 빼면 그 테스트가 깨진다. 탭으로 돌아오면 다음 tick(최대 1.5초 안)에 갱신된다. | index.html:880 |
| 24 | 썸네일과 자산함 img에 loading=lazy, decoding=async를 붙였다. 자산 검색은 150ms 디바운스한다. width/height 속성과 서버 썸네일 생성은 하지 않았다(원본 크기를 알 수 없고 서버는 범위 밖). | index.html:114-115, 425, 554 |
| 25 | 축소 모션 블록 5개를 1개(276)로 합쳤다. #chatPanel·compareDialog·motionDialog 인라인 스타일을 CSS로 옮겼다. #chatPanel의 !important 4개를 제거했다. 전체 !important는 58→45개다. | studio.css:276, 334, 488, 1024-1025 / index.html:19, 36 / motion-studio.js:6 |
| 26 | take 비선택 테두리를 --ui-control로 바꿨다. 선택과 구분되도록 선택(.active, aria-current) 테두리는 --ui-marker로 강화했다(critic 지적 반영). | studio.css:709, 711, 518 |
| 27 | 이름을 가진 div 6곳에 role=group을 붙였다(index.html의 #memoryProposals, #timelineProposals, #executionCards, #mediaActionCards, general-chat-ui.js의 2곳, #sequenceCaption). 검토 배지는 aria-label을 지우고 sr-only로 'Take N 검토:'를 넣었다. | index.html:19, 23, 24, 31, 110 / general-chat-ui.js:7 / studio-media.js:156 |
| 28 | 이미 고쳐져 있어 변경하지 않았다. 턴을 다시 그릴 때 focusKey/restoreFocus로 review와cancel 버튼의 포커스를 복원한다. | general-chat-ui.js:20-21, 64 [검증됨] |
| 29 | 라벨을 '음원 파일 (WAV·MP3·M4A·FLAC·OGG)'로 바꿨다. | index.html:21 |
| 39 | message()에 raw 인자를 추가했다. 클라이언트가 만든 검증 문구 25곳은 원문 그대로 표시한다(node로 creatorError가 바꿔 쓰는 문구만 골랐다). 넓은 정규식 확장은 하지 않았다. 실제 연결 오류인 '서버 연결을 확인하세요.'는 제외했다. | index.html:55-56 외 26개 호출 |
| 40 | #flowNext를 프로젝트 상태 disclosure 안으로 옮기던 코드와 관련 CSS 규칙(642)을 제거했다. 마지막 단계 버튼은 '렌더 작업 확인'이며, 누르면 검토 탭을 열고 #jobs로 포커스를 옮긴다. | index.html:295, 862, 865, 877 |
| 42 | 검토 결정의 첫 옵션을 빈 '검토 결정 선택'으로 했다. 사유 기본값 4개(참고, 납품, 계승, 취향)를 제거했다. reasonGates()가 사유와 결정이 입력되기 전까지 버튼을 비활성화한다(data-runtime-blocked 패턴). 계승 작품을 골랐는데 사유가 비어 있으면 details를 열고 포커스와 안내를 준다. | index.html:31-32, 40, 437, 558, 589-591 |
| 43 | 탭과 랜드마크 이름을 '검토'로 통일했다. 제작안 카드로 이동하는 데 성공하면 '대화로 돌아가기' 버튼이 나타난다(공개 API 래퍼에서 처리). | chat-sidebar.js:16-17, 19, 48, 248, 310 |
| 47 | 바꾼 라벨: 'FullAccess'→'전체 편집', 추론 강도 원시값→한국어(옵션 value는 그대로), 컷 '시작(초)'→'원본 시작(초)', 일반 대화 제목→'시험용 일반 대화 전송 검토'. 정적 HTML 버튼 문구 10개를 런타임 라벨과 같게 맞췄다. | chat-sidebar.js:41, 167-176 / index.html:14, 23-24, 31, 424 / general-chat-ui.js:4, 52 |
| 48 | 비용 상한 오류가 허용 범위(0.000001~0.1, 총 상한은 회차 상한 이상 0.4 이하)를 알려 준다. 권리 확인 체크 전에는 승인 버튼이 비활성이고 옆에 이유를 표시한다. | general-chat-ui.js:48, 61, 67, 72 |
| 50 | 컷 행과 자막 행의 모든 컨트롤 이름에 '샷 N번 컷', '자막 N'을 넣었다. | index.html:424 |
| 51 | 단계별 완료 표시를 추가했다. 기준: 음원 / 계획 적용 또는 장면 존재 / 모든 장면 Take 선택 / 출력 완료. 시각 표시는 '완료'(aria-hidden), 이름은 '… 완료'로 하고 data-done을 단다. 359px 이하에서는 표시 텍스트를 숨긴다. 마지막 단계는 #40과 같이 렌더 작업으로 연결된다. | index.html:863-864 / studio.css:1031, 1035-1037 |

### Low
| # | 처리 | 위치 |
|---|---|---|
| 3 | 재생 헤드는 `transform:translateX(Ncqw)`로 움직인다(#timeAxis에 container-type:inline-size, playhead에 left:0). 시간·자막·상태 텍스트는 값이 바뀔 때만 쓴다. CSS 변수 대신 style.transform을 쓴 이유: 테스트 하네스의 style 스텁에 setProperty가 없다. | studio-media.js:72, 89, 93 / studio.css:794, 807 |
| 10 (=31) | white/black을 --ui-strong/--ui-canvas로 바꿨다. | studio.css:72, 77, 146, 148, 198 |
| 11, 36 | general-chat-card 블록을 토큰화했다(#d5d5d5 폴백 제거). 진단 pre는 --ui-meta/--ui-font-timecode, scene 대화상자의 600은 --ui-weight-heading으로 바꿨다. | studio.css:928-938, 326, 917-921 |
| 13 | 하위 항목: #track span 띠 제거(522), 측정폭 65ch와 --ui-item(443), 점선 초점 링 2줄 삭제(#30), summary 44px(686), #chatPanel 인라인과 !important 정리(#25), 축소 모션 1벌(#25), 정적 primary 중복 제거(#review와 #render의 class="primary"; JS가 상태에 따라 하나만 켬), tabular-nums 묶음 규칙(1023), generic aria-label(#27). | studio.css:443, 522, 686, 1023 / index.html:14 |
| 30 | 점선 초점 링 규칙 794-795를 삭제해 실선 하나로 통일했다. 잘림 방지용 offset 예외(-3px, 트랙 버튼과 stage-bar)는 목적이 [미확인]이라 유지했다. | studio.css (삭제) |
| 32, 52 | production-review-error의 2px 왼쪽 띠를 제거했다(배경과 텍스트는 유지). #track span 띠도 제거했다. | studio.css:721, 522 |
| 33 | 알림 summary 높이를 24px에서 44px로 바꿨다. | studio.css:686 |
| 34 | 자산함 버튼 이름에 파일명, 샷, Take를 넣었다. 'VIDEO' 배지는 '영상'으로 바꿨다. | index.html:425 |
| 35 | 인스펙터 섹션의 h2를 summary 안에 그대로 둔다(summary를 쓰는 코드는 h2를 갱신하도록 고침). 인스펙터는 aside에서 div로 바꿨고, 레거시 aside 패딩과 테두리는 `aside,.inspector`로 보존했다. | index.html:24, 31, 302-303, 986-987 / studio.css:98, 173, 1024 |
| 37 | 장면과 take 단일 선택을 aria-pressed에서 aria-current="true"로 바꿨다. 관련 CSS(518, 776 forced-colors)도 갱신했다. | index.html:114-115 / studio.css:518, 776 |
| 375 select | ≤900px에서 `#songs { flex:1 1 12rem; width:auto }`로 바꿨다. 셸이 줄바꿈되므로 select가 최소 12rem을 확보하고 나머지는 다음 줄로 넘어간다. 렌더 확인은 [미확인]이다. | studio.css:458 |

### 제외·기록
- #12: 결함이 아니다. Hallmark 기각 기록만 남긴다. 56번 근거 보정: studio.css의 sticky 짝 887↔962는 서로 배타적인 조건이라 동시에 적용되지 않는다. 39a@728(활성 상태), 76@index.html:23, 41, F4, F6@715, 38iii는 sloplint에 그대로 남아 있다. 기각 확정은 소유자 몫이다.
- #41 #44 #45 #46 #49: B2 담당이라 손대지 않았다. media-card 마크업(mediaActionMarkup)도 손대지 않았다.

## 2. 테스트
명령(작업 디렉터리 /Users/leesungmin/Desktop/Loretune):
```
PYTHONPATH=tests PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/opt/python@3.15/bin/python3.15 -B -m unittest $(cat .omo/evidence/agent-tools-02-20261028/tasks/E1-design/ui-modules.txt)
```
- 기준선(tests-before.log): `Ran 133 tests in 57.264s / FAILED (errors=1)`. 오류는 기존 서버 측 test_saved_run_relation 하나였다.
- 편집 후(tests-after.log): `Ran 133 tests in 58.710s / OK`
- 중간에 FAIL 3건이 나왔다. 원인은 내 코드가 테스트 스텁에 없는 API를 호출한 것이었고, 소스를 고쳐 해소했다. 테스트는 수정하지 않았다.
  - general_chat 2건: addEventListener→onchange로 바꾸고, closest 기반 조회로 바꿨다.
  - scene_ui: setAttribute?.()로 바꿨다.
  - review_navigation: 처음에는 backToChat 참조를 공개 API 래퍼로 옮겨 고쳤다.
- 기준선 오류가 해소된 것은 동시에 작업 중인 다른 워커의 변경 때문으로 [추정]한다. 내 파일과는 무관하다.
- 참고: UI 모듈 중 일부(chat_sidebar, work_status, central_frame_preview)는 프로젝트가 자체적으로 띄우는 격리 headless Chrome 테스트이며, 기준선 때와 같은 방식으로 실행했다.
- JS 문법: 7개 파일과 index.html 인라인 스크립트 7개 모두 `node --check` OK.

## 3. 게이트
- sloplint(`design-gate/sloplint-after-e1.json`): FAIL 18→9, REFLEX 73→1, WARN 16→13. r2 대비 새 FAIL은 0이다.
  - 중간에 .lt-output-spec의 `1fr`이 gate 50 FAIL로 새로 잡혔고, minmax(0,1fr)로 바꿔 해소했다.
  - 게이트별 변화(before/r2→e1): 7a 6→0, 24b 72→0, 48 1→0, 63 1→0, 39a 2→1, 3 1→0, 25 1→0, 40 1→0.
  - 변화 없음: 20, 34×4, 50(658), 56, 76, 41×3, F3, F4, F6×5, F7, F23, F24, 38iii.
  - F6은 묶음 :where 규칙(1023)으로 tabular-nums를 적용했지만 디텍터는 규칙 단위로만 인식한다.
- impeccable detect index.html(파일 모드): rc=2. 결과는 `design-gate/impeccable-after-e1.txt`, 같은 엔진으로 돌린 시작 사본 결과는 `impeccable-start-e1.txt`.
  - broken-image 1과 advisory 12(thin-border-wide-shadow)는 시작 사본과 같다.
  - **새 항목 1건: monotonous-spacing "~4px 10/12"**. 원인 [검증됨]: 디텍터는 px 리터럴만 센다. 토큰화 후 남은 리터럴은 12개이고 그중 10개가 2px이다(시작 사본은 100개). 실제 간격은 토큰 척도(4/8/12/16/24/32)라서 디텍터 한계에 따른 오탐으로 판단했다. ignore 설정은 쓰기 범위 밖이라 추가하지 않았다.

## 4. 남은 공백
- 모든 시각·배치 결과는 렌더로 관찰하지 않았다 [미확인]. 특히 확인할 것: 375px 헤더, 288px 사이드바 헤더, cqw 재생 헤드, 단계 완료 표시, 제목 행 런처 배치, inspector 패딩, 입력 높이(10px→space-2라서 약 42→38px로 줄어듦 [추정]).
- #23 visibilitychange 즉시 갱신: 테스트 문자열 절단 계약 때문에 넣지 않았다.
- #24 서버 썸네일과 img width/height 속성은 하지 않았다.
- impeccable monotonous-spacing 1건이 남아 있다(위 분석 참조).
- 관찰만 하고 고치지 않은 것(범위 밖): drawFlow의 `[data-step]` 선택자가 body[data-step]에도 aria-current="false"를 쓴다(index.html:862).
- r2에서 이월된 B1 minor(같은 프롬프트 두 턴의 버튼 이름과 describedby가 같음)는 항목 밖이라 고치지 않았다.

## 5. 사용자 결정이 필요한 항목
1. impeccable monotonous-spacing: `impeccable hooks ignore-value`로 좁게 예외를 둘지, 남은 2px 리터럴 10개를 토큰화할지(2px 토큰은 없음) 정해야 한다. 근거는 위 3절.
2. #16 방식: 비례 막대 + 컷 번호 버튼(동등 컨트롤 예외)으로 충분한지, 막대 자체의 24px 확보(비례 포기)를 원하는지.
3. #51 완료 기준(음원 / 계획 또는 장면 / 전 장면 선택 / 출력 완료)이 제품 의도와 맞는지.
4. #9 입력 높이가 약 4px 줄어드는 것을 받아들일지. 아니면 min-height 토큰으로 유지할지.
5. #12 기각 묶음을 Hallmark 스탬프의 dismissed/waive로 확정할지.
6. 서버 reason 검증은 이미 있다. app.py:227-230 text()가 빈 사유를 거부하므로 #42의 서버 측 필수 검증은 충족된 상태다 [검증됨]. 결정할 것은 계승 사유(inherit_reason)를 계승할 때만 요구하는 현행 방식을 유지할지다.
