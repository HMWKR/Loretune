# Bounded desktop shell 독립 한정 검토

**검사한 코드·controlled fixture 범위에서 새 재현 결함 없음.** 변경된 layout adapter, text-scale 분기, adaptive ruler, 이벤트 수명, 노드/초안 보존은 통과했다. 실제 CSS 배치·전체 포커스/스크롤 접근성까지 독립 통과로 확장하지 않는다.

## 고정본과 변경 범위

- HTML `202ea641e5c1f06d316babd21aa82ad29795f4f2d5de2ff077aef596ccb850c5`
- CSS `8274aacf793e454fcc727801bdc3f7d9309345776e1e1fd6a049583e8469a3e9`
- media JS `ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e`
- app.py `7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`

release-manifest의 source 해시와 캡처 파일이 일치했다. 이번 before 대비 HTML은 presentation script 추가, CSS는 control 최소높이/자막 grid/조건부 bounded shell/눈금 stacking 변경이다. media JS와 backend는 이전 고정본 그대로다. DM01–03을 다시 열 근거가 없으며 재감사하지 않았다.

[snapshot.json](snapshot.json)에 시각·mtime·bytes·hash, [snapshot/](snapshot/)에 분리 파일, [finish.json](finish.json)에 종료 drift 기록. 원 소스·서버·공유 DB는 변경하지 않았다.

## 독립 실행 결과

[adapter-controls.cjs](adapter-controls.cjs)는 HTML의 실제 `loretuneDesktopLayout` script를 수정 없이 추출하여 controlled DOM/geometry에서 실행했다. [8개 결과](adapter-controls.json) 모두 통과했다.

| 확인 | 실제 fixture 관찰 |
|---|---|
| 노드 이동·초안 | preview, return anchor, 입력 form 객체가 그대로 한 번 이동. draft value·media currentTime·현재 activeElement 참조 보존. 복제/재생/저장/포커스 강제 호출 없음 |
| 중간 눈금 충돌 | 겹치는 중간 label만 hidden. 시작/끝은 유지 |
| 너비 변화 | 좁혀 숨겼던 label을 넓어진 측정폭에서 복원 |
| 극좁은 endpoint | endpoint 수평 충돌에서 stacked=true, 충분한 폭으로 돌아오면 false |
| text-scale/창 크기 |1920/1080/100%,1100/800/100% bounded.150/200%,1099px폭,799px높이는 flow. 반복 전환에도 입력 값·객체 보존 |
| 이벤트 증식 | resize/text change/두 MutationObserver/ResizeObserver를500회 반복 통지해도 pending RAF1개. flush 후0개. resize listener1/text change1/MutationObserver2/ResizeObserver1 유지 |
| ruler 교체·숨김 | 새 ruler를 관측할 때 old ResizeObserver 연결 해제. hidden→visible 후 label 계산 정상 |
| 부수 효과 | 네트워크/서버 mutation/storage/focus/media playback API 호출 없음 |

첫 harness 실행에서는 VM realm 배열과 host 배열의 prototype 차이 때문에 deepStrictEqual 한 곳이 실패했다. Array.from으로 비교값만 정규화한 뒤 재실행했다. 제품 코드 변경이나 기능 실패 은폐가 아니다.

[focused-tests.log](focused-tests.log): **7 unittest 통과 /0.364초**. 새 desktop layout4개 + F07 comment draft wrapper1개 + scoped review/비교 wrapper2개. wrapper 내부16/9/5 case를 총 test 수에 추가하지 않았다. source/API 호출 차단 경계를 유지하며 현재 파일에서 기존 delayed save/새초안/작품·장면·Take context 회귀가 통과했다.

## 코드 검토 근거

- `index.html:727–734`: mode 분기와 bounds 기반 label 선택. 시간좌표/clip duration/trim을 쓰거나 수정하지 않음.
- `index.html:735–741`: 한 번 실행하는 IIFE가 stage region/tabIndex0을 만들고 실제 node/anchor를 이동. draw/layout 갱신마다 initializer를 다시 부르는 경로 없음.
- `index.html:742–757`: 단일 pending RAF로 계산 합침. ruler identity 교체 때 resize.disconnect. body observer는 data-step/data-guided만 보므로 adapter 자신의 data-desktop-shell 변경을 다시 관측하지 않음. label hidden/stacked 속성도 dock childList observer 대상이 아님.
- `studio.css:113`: caption 텍스트 열 minmax(0,1fr), 삭제 열36px로 경계 확보.
- `studio.css:836–859`: bounded 조건에서 body를 overflow:hidden으로 덮지 않고 패널 overflow:auto, min-height0, scroll-padding/scroll-margin, 상세영역 stable scrollbar gutter 적용. 작은 창·확대에서는 JS가 flow로 전환.
- 새 adapter에는 keydown/wheel preventDefault, focus trap, 승인/선택/저장 호출이 없다. 신규 focus target은 이름이 있는 preview region 한 개다. 기존 compare modal focus 복귀 함수는 이 diff에서 변경되지 않았다.

이 근거에서는 숨은 action을 제거하거나 다른 focus target으로 강제 이동하는 새 경로를 찾지 못했다. 다만 nested scroll의 실제 사용성은 브라우저 geometry가 필요하므로 코드만으로 모든 offscreen 조작 도달을 인증하지 않는다.

## 구현팀 증거와 독립 미검증 구분

보고서, release manifest, 현 presentation contract 및 이번 CSS/HTML diff를 읽었다. 구현팀 `keyboard-verified.json`의34행은 inside/visible=true, docScroll0으로 내부 일관성이 있다. 긴 내용 증거는 DOM-only 스트레스이며 DB 대형프로젝트 성능 시험으로 세지 않았다. 이는 **기존 관측 기록의 검토**이고34개 actual focus target을 이번에 다시 눌렀다는 뜻이 아니다.

다음은 이번 독립 패스에서 미검증이다.

- 실제1920 문서 높이1080px, 정밀 편집/긴 inspector 끝 버튼의 실제 노출·스크롤/Tab 도달성.
- 실제 폰트 glyph/CSS layout에서 눈금 줄바꿈·text-scale clipping, browser200/400% zoom·스크린리더.
- 다른 OS/browser scrollbar/sticky-summary 조합 및 장시간 성능.
- 새 실제 브라우저/서버 요청/공유 DB 작업. 구현팀342전체 회귀와1080px/34focus 관측은 독립 결과로 대체하지 않았다.

별도 source snapshot만 읽고 fixture를 실행했으며 앱 코드·공유 DB·서버·계정/credential 접근·유료/외부 provider 호출 없음. 진행 중 사용자 초안/탭은 조작하지 않았다. 미해결 실행 blocker나 추가 권한 요청 없음. 이 한정 코드·회귀 검토는 완료했고 실제 기하·시각 수용 범위는 위 한계로 남긴다.
