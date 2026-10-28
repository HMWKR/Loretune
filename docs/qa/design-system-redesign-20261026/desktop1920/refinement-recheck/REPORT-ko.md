# Loretune V1–V4 독립 디자인 재검토

2026-10-26 · 실제 CSS viewport 1920×1080 우선 · 1280×900 보조 · 종료 2026-10-26T03:05:56.350Z

## 결과

**고정된 7축·26항목 기준 81.0/100점입니다.** 26항목 모두 평가 가능한 표본을 확보해 배점 커버리지는100/100입니다. 이는 모든 상태를 시험했다는 뜻이 아닙니다. 점수는 아래 고정표에 대한 전문가 판단이며 객관적 경쟁사 순위·제품 완성률·90점 달성·접근성 인증이 아닙니다. 이전5축 점수와 비교하지 않습니다.

이번 직접 표본에서 새 사용 차단 결함은 재현되지 않았습니다. 기본1920 작업 공간의 페이지 높이1080px를 유지하면서 정밀 편집·자막 동시 화면의 실제 영상이334×188에서505×284px로 커졌습니다. 편집 선택과 재생 장면의 역할, 모델 선택의 현재 이유, 저장 거절과 미확정 결과의 다음 행동이 명확해졌습니다.

**필수 gate: H3 키보드 PASS, H4 측정 대비 표본 PASS. H1 미디어 경계 전체와 H2 실제 비용·승인 실행 구간은 UNVERIFIED입니다.** 따라서 전체수용/ready를 선언하지 않습니다. 미검증을 실패로 계산하지도 않습니다.

## 같은 평가표의 이력과 점수 변화

평가표 [v1.0](../RUBRIC-v1-ko.md)와 [무스크롤 추가 합의v1.1](../RUBRIC-v1.1-ADDENDUM-ko.md)의 가중치·앵커를 유지했습니다. 항목별0–4 정수 앵커×배점/4로 계산하며 결과를 보고 새 기준을 만들지 않았습니다. 옛 [74.25점/평가98점 보고서](../final-audit/REPORT-ko.md)와 원본scorecard는 수정하지 않았습니다.

| 이력 | 확인 가능한 배점 | 획득점 | 의미 |
|---|---:|---:|---|
| 이전 shell202ea641 |98/100|74.25 (표시74.3)|F3=U, 전체점수 보류.100점으로 환산하지 않음|
| 현재 refinement5fcc2cca |100/100|81.00 (표시81.0)|허용된 통제 오류 시험으로F3도 평가 가능. 전체 상태 커버리지는 아님|

차이6.75점 중 시각·문구 개선은 A4+1, B1+1.25, B3+1.25, D2+1로 **4.5점**입니다. F2+0.75는 키보드 증거 보강이며, F3+1.5는 기존 미검증 범위를 새로 평가한 점수입니다. 이6.75점을 모두 디자인 코드 개선률로 주장하지 않습니다.

| 축 | 배점 | 현재 획득 |
|---|---:|---:|
| A workspace 구성·밀도 | 20 | 16.5 |
| B 정보·행동 위계 | 15 | 12.5 |
| C 색상·semantic 상태 | 15 | 11.25 |
| D 타입·간격·형태 | 15 | 12.25 |
| E 미디어·시간축 작업 | 15 | 12.75 |
| F 상호작용 상태·키보드 | 10 | 8.25 |
| G 디자인 시스템 일관성 | 10 | 7.5 |
| **합계** |**100**|**81.0**|

## V1–V4 실제 재검토와 시각 판단

| 항목 | 원인·기존 부담 | 현재 직접 측정/관찰 | 판단·잔여 |
|---|---|---|---|
|V1 / A4|정밀 폼과sequence·자막이 높이를 경쟁해 실제 영상188px|1920 영상283.98px높이, 면적2.28배. 문서1080px.34controls+진단summary1의Tab중심 가림0|개선됨.1280 정밀 영상은122.70px높이로 작아져 보조화면 절충이 남음. 숨긴 조작으로 만든 개선은 아님|
|V2 / B3|사용자 편집 상세에 자산hash검사 설명|닫힌 ‘검증 상세’ 안에 원문 보존. checkVisibility=false→Enter후true|기본 기술 설명 노출 해소. 모델·승인·테스트 표시와 오류는 유지. 모든 계획/공급자 경로를 재감사한 것은 아님|
|V3 / D2|모델 미선택 사실의 반복과 큰 간격|미선택 창 외곽559.09px; 선택불가 이유를 역할별 한 줄. 긴이름 전체줄바꿈/가로overflow0|현재 표본의 그룹·정렬 문제 해소. 전체 모델명은 길어야 할 때만 두 번째 영역에 제공|
|V4 / B1|편집 대상01과 재생 대상02를 사용자가 추론|‘편집 선택 · Take1’, ‘재생 장면:02…’ 명시. 선택·승인·trim 불변|현재 표본의 역할 혼동을 해소. 실제 사람의 인지시간 측정은 아님|

### 동일 과업 geometry

모든 값은 브라우저 내용영역 CSS px입니다.16:9 실제 영상 면적은 요소의전체폭이 아니라 intrinsic320×180과contain 내부영역으로 계산했고 저장 픽셀과 대조했습니다. 영상은 로컬 합성 패턴이며 실모델 생성물이 아닙니다. 테스트 화질·아름다움은 감점하지 않았습니다. 검정letterbox는 비율보존의 정상 영역입니다.

| 상태 | 실제영상 W×H | viewport 면적 | 문서/viewport높이 | timeline하단 |
|---|---:|---:|---:|---:|
| 01-selected-1920 | 718.07×403.91px | 13.99% | 1080 / 1080 | 1064px |
| 05-sequence-1920 | 598.96×336.91px | 9.73% | 1080 / 1080 | 1064px |
| 06-expanded-sequence-1920 | 504.86×283.98px | 6.91% | 1080 / 1080 | 1064px |
| 07-expanded-sequence-1280 | 218.14×122.70px | 2.32% | 900 / 900 | 884px |

1920 정밀 편집에서 영상은 약6.91%의 viewport면적을 차지합니다(이전3.03%). 이것만으로 미감이나 작업 성공률을 추론하지 않습니다.1280의 영상 면적은 이전 동일 정밀 상태보다 약44% 작습니다. [07화면](07-expanded-sequence-1280.png)은 내부 폼이 아래로 스크롤된 상태이며 마지막 버튼 일부가 처음 프레임에 보이지 않습니다. 후속Tab35개가 모두 화면 안으로 들어오는 것을 [boundaries.json](boundaries.json)으로 확인했으므로 접근 불가능한 clipping으로 판정하지 않습니다.

## 색상·타입·형태·상태

기존 palette와token 역할을 유지합니다: canvas#101010, panel#1B1B1B, raised#242424, hover#303030; 강한문자#F4F4F2, 본문#DEDEDB, 보조#BDBDBB; 필수경계#858585, 장식선#383838. 선택면#2A2A28+왼쪽표식#D8D8D2, focus#E4DDBE 2px점선+2pxoffset, 승인은기호+텍스트로 구분합니다. 원본 computed/tokens는 이전 [tokens.csv](../final-audit/tokens.csv)와 현재 캡처JSON에 있습니다. 경쟁사의 내부HEX를 추정해 비교하지 않습니다.

기존 실제 대비 표본(본문/패널12.777:1, 보조/패널9.154:1, 제어경계/hover3.577:1, focus/hover9.669:1)을 유지합니다. 이번에는 오류의 실제전경#FFB49D·배경#28201E·조상opacity1을 확인했고 **9.325:1**입니다. 이전 source-only 오류쌍을 이번에는M관찰로 보강했습니다. nativevideo 반투명overlay 전체나 모든 상태를 인증한 것은 아닙니다.

제목20px/600/28px, 본문14px/400/23.8px, 메타12px와tabular시간의 읽기 층위를 유지합니다.4/8/12/16/24/32px 간격과control6/panel8/dialog12px의 형태 역할도 유지합니다. 모델 폼은 select와이유·상세를 같은 그룹으로 묶고 미선택의 불필요한 이름 행을 제거했습니다. 긴 이름의 전체문구는3줄67.20px로 읽히고, 폭을 넘어가거나 가로스크롤을 만들지 않았습니다. 글자와native아이콘의 광학무게가 완전히 같지는 않으며D4의 기존 잔여로 유지합니다.

## 직접 수행한 흐름·통제 시험과 커버리지

| 상태/검증 | 증거 등급·결과 | 하지 않은 것 |
|---|---|---|
|기본/sequence/정밀1920|O/M:01,05,06. readyState4,문서1080. 편집01/재생02|장시간동기·실음악청취 없음|
|초기 keyboard-only|O/M:BODY에서Tab/Enter/Arrow/입력/Escape,52관측/8목표. 비교/모델닫기·초안취소의focus복귀|nativevideo 모든 메뉴/스크린리더 전체 없음|
|정밀 폼1920/1280|O/M:34개input/button+진단summary.35Tab 중심가림0|이 구간은summary명시focus 진입. 초기여정과 구분|
|모델 미선택/미검증/차단|O/M:실제catalog선택을 저장 없이 표시,Escape복귀|모델 활성화/저장/호출 없음|
|긴이름 unavailable|O/M:임시in-memory catalog,전체이름·줄바꿈·overflow0,원상복원|실제등록모델/서비스상태 아님|
|400저장거절|O/M controlled:입력 보존,구체적안내,다시저장활성|실제서버400장애 아님|
|응답유실→404unknown|O/M controlled:새저장disabled,기존조회만,입력보존|새POST전달/실청구/DB저장 없음|
|장면전환/새초안 race|O/M controlled:02에01초안없음,01복귀보존;응답 대기 중 추가한새문자 유지|프로젝트간/앱재시작 후 복구는 이번 미실행|
|앱글자200%|O/M:본문28px,flow,문서2505px,가로넘침0,눈금겹침0|실제브라우저zoom200/400% 아님|
|긴panel·혼합aspect·reduced-motion|이전 독립O/M 증거를 관련코드불변으로유지|이번에 모두다시실행한것으로표시하지않음|
|회귀346/문법6·DM01–03|S:구현/독립코드팀 근거|코드테스트 수를 시각점수로 사용하지 않음|
|미실행|실제browserzoom,screenreader,forced-colors 전체,실제고객시험,livebilling,모든생성오류,모바일새QA|미검증을실패나성공으로대체하지않음|

통제 오류 시험은 두 번 수행했습니다. 첫 실행은400→unknown→장면전환→응답대기중새초안→합성committed분기를 검증했습니다. 두 번째는 첫08/09화면의native영상로딩spinner를 제외하기 위해readyState4를 기다린 깨끗한 픽셀을 확보한 것입니다. **합계 변경POST4건·조회GET4건은 모두 가로챘고 전달0,예상외변경0**입니다. 마지막committed는 클라이언트분기를 정리하기 위한 합성응답이지 실제저장증거가 아닙니다. 임시초안은취소,fetch와catalog는복원했습니다.08/09/10은해당검토상태만의증거로보존하며ready영상전달용에는13/14를사용합니다.

처음테스트harness가shots를배열로가정해wait가timeout된1건은실제객체구조를확인한뒤계수검증으로수정했습니다. 이는제품실패나저장실패가아니며점수에포함하지않습니다. 실행도구의접근거부는없었습니다.

## 필수 gate

| Gate | 상태 | 근거와 범위 |
|---|---|---|
|H1 media/seek/sync|UNVERIFIED|현재재생/정지/sequence와기존비교는확인.로딩중seek/staleevent/이전audio반례전체는이번브라우저미실행. DM01–03코드종료는유지|
|H2 승인·비용·버전|UNVERIFIED|비교/초안/모델창 전후project불변과controlled복구확인. 실제비용·승인commit/DB저장/청구는하지않음|
|H3 핵심keyboard|PASS(정의된표본)|초기정상Tab부터고정핵심여정완주. focus가시·닫기/취소복귀확인|
|H4 필수대비|PASS(측정표본)|기존쌍+실제오류9.325:1. 전체WCAG/nativeoverlay인증아님|

## 26항목별 점수·유지 강점·감점 이유

표의숫자는0–4앵커입니다. 이전U는0점이아닙니다. 동일결함을여러축에서중복감점하지않습니다. 이전근거를유지한항목은 [scorecard.json](scorecard.json)의evidence_disposition에명시했습니다.

| 항목 | 배점 | 앵커 이전→현재 | 획득 | 실제값/근거 | 판단·남은한계 | 대표파일 |
|---|---:|---:|---:|---|---|---|
| A1 역할 구역과 시선 이동 | 6 | 3 → 3 | 4.5 | rail184px·중앙1376px·inspector288px. 장면→미디어→검토를 동시에 식별한다. | 구역 역할과 인접성이 명료하다. 세 구역의 실제 작업 순서/탐색 시간을 사람에게 검증하지 않았으며 복잡한 장면 제작 상세는 내부 스크롤이 필요하다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/15-production-empty-1920.png](../final-audit/15-production-empty-1920.png) |
| A2 핵심 media/transport/시간축 가시성과 bounded shell | 6 | 4 → 4 | 6 | 기본·sequence·정밀 편집 문서 1080/1080px, timeline 하단1064px. 정밀 입력·버튼34개와 진단 summary1개를1920 및1280에서 Tab 이동, 중심 가림0. | 기존 bounded shell의 강점을 유지한다. 긴 rail/메모 스트레스는 이전 직접 증거를 유지하며 이번 새 실행으로 바꾸지 않는다. 상세는 내부 스크롤을 사용한다. | [01-selected-1920.json](01-selected-1920.json), [05-sequence-1920.json](05-sequence-1920.json) |
| A3 읽기 밀도·행 길이 | 4 | 3 → 3 | 3 | inspector288px,본문14px/23.8px. 긴 한글 입력과 메모는 줄바꿈되며 본문 폭이 중앙 전체로 늘어나지 않는다. | 본문 읽기와 그룹은 안정적이다. 긴 메모는 단락 구조/요약 없이 세로 길이가 커진다. 이는 접근 불가가 아닌 읽기 부담이며 자동 요약 새 기능을 요구하는 것은 아니다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/07-review-dirty-1920.png](../final-audit/07-review-dirty-1920.png) |
| A4 1920 공간 사용과1280 적응 | 4 | 2 → 3 | 3 | 1920 실제 contain 영상: 기본718.07×403.91, sequence598.96×336.91, 정밀504.86×283.98px. 1280 정밀218.14×122.70px. 문서1080/900px. | 1920 정밀 영상의 면적은 이전334.12×187.95보다2.28배로 개선됐다. 하지만1280 정밀 영상은 이전291.03×163.70보다 면적 약44% 작다. 보조 viewport의 세부 미디어 판단 부담 때문에4가 아니다. 이 감점은A4에만 반영한다. | [01-selected-1920.png](01-selected-1920.png), [05-sequence-1920.png](05-sequence-1920.png) |
| B1 작품·장면·Take·버전 맥락 | 5 | 3 → 4 | 5 | 편집 선택01/Take1과 재생 장면02/Take1을 명시적으로 구분. sequence시각2.172/7초, 선택·승인·편집 project hash불변. | 정해진 장면 선택/sequence/비교 표본에서 대상 역할이 명확하고 모순이 없다. 재생이 편집 선택을 바꾸지 않는다. 이는 객체 문맥의 표본 평가이며 실제 사용자의 이해 시간을 측정한 것은 아니다. | [05-sequence-1920.png](05-sequence-1920.png), [06-expanded-sequence-1920.png](06-expanded-sequence-1920.png) |
| B2 상태에 맞는 다음 행동 | 5 | 3 → 3 | 3.75 | 승인완료=검토수정,dirty=활성저장/취소,출력준비=결과검토/저장/납품검토전. | 승인 완료에는 검토 수정, dirty에는 활성 저장/취소, 통제된 거절에는 수정 후 재저장, unknown에는 기존 저장 확인이 표시된다. 반려/미검토 inspector와 실제 비용 commit의 모든 변형은 이번 표본에 없으므로3을 유지한다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/07-review-dirty-1920.png](../final-audit/07-review-dirty-1920.png) |
| B3 중복·진단·중요 사실 노출 | 5 | 2 → 3 | 3.75 | 일상 문구는 저장된 버전·승인 상태 중심. 자산 해시 검증 방식은 닫힌 검증 상세 안에서 checkVisibility=false, Enter로true. 테스트 미디어·모델 불가 이유·실행 승인 별도 안내 유지. | 기존 기본 노출 기술 설명 문제는 해소됐다. 진단을 삭제하지 않고 사용자가 필요할 때 열 수 있다. 계획 commit·공급자 오류 등 모든 경로의 진단 분리까지 실제 관찰하지 않았으므로 전 범위4를 선언하지 않는다. 모델 창의 공간 감점은D2에서만 다룬다. | [diagnostic.json](diagnostic.json), [controlled-errors.json](controlled-errors.json) |
| C1 surface/action/선택/focus/검토 의미 | 5 | 3 → 3 | 3.75 | 선택#2A2A28+왼쪽#D8D8D2표식,hover#303030,focus#E4DDBE 2px dashed/offset2,승인은✓+텍스트. | 기존 선택 면/왼쪽 표식, focus 점선, 승인 기호의 역할을 유지한다. 이번에는 오류 면과 비활성 저장의 실제 픽셀도 확인했다. forced-colors와 모든 반려/실행 상태는 미검증이므로3을 유지한다. | [../final-audit/styles-states.json](../final-audit/styles-states.json), [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png) |
| C2 필수 전경·배경·경계 대비 | 5 | 3 → 3 | 3.75 | 실제불투명배경쌍:본문/패널12.78,보조/패널9.15,컨트롤경계/raised4.21,경계/hover3.58,focus/hover9.67. 현재 오류#FFB49D/오류면#28201E도 opacity1 실제쌍으로9.325:1 확인. | 측정한 필수본문·경계·focus는 필요한 대비를 확보한다. 반투명dialog backdrop와nativevideo overlay 모든 위치/상태를 측정한 것은 아니며 전체WCAG 인증이 아니다. | [../final-audit/contrast.csv](../final-audit/contrast.csv), [../final-audit/styles-states.json](../final-audit/styles-states.json) |
| C3 상태의 비색상 단서 | 5 | 3 → 3 | 3.75 | 선택 aria-pressed+왼쪽표식,승인✓/검토전○+문구,모델미선택 문구,dirty저장활성. | 선택·승인·focus의 기존 비색상 단서를 유지하며 오류 문구/왼쪽 경계, unknown의 비활성 저장과 활성 조회를 추가로 확인했다. 모든 provider/권리/계획 오류의 비색상 단서는 표본 밖이므로3을 유지한다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/06-comparison-video-video-1920.png](../final-audit/06-comparison-video-video-1920.png) |
| D1 한국어·숫자·3단계 위계 | 5 | 3 → 3 | 3.75 | 제목20px/600/28px;항목13px/500/19.5px;본문14px/400/23.8px;메타12px,시간tabular-nums. | 제목·본문·메타의 세 읽기 층위가 분명하고 긴한글도 읽힌다.12px 메타가 많은 편집 화면 특성상 확대 때 패널폭과 줄 수의 절충이 남는다. 테스트화질은 평가하지 않는다. | [../final-audit/styles-states.json](../final-audit/styles-states.json), ../final-audit/07/09/10 캡처 |
| D2 간격·정렬·그룹 | 4 | 3 → 4 | 4 | 미선택 모델창 외곽 높이559.09px; 실제 모델 미검증/차단 선택은657.09px, 합성 긴 이름은683.28px. 긴 이름67.20px 줄바꿈, 가로overflow0. | 기존 미선택 사실을 세 줄로 반복하던 공간 문제가 해결됐다. 관련 label/select/현재 이유와 상세가 한 그룹이고, 긴 이름은 필요한 때만 전체를 보여준다. 이번 표본에서 간격·정렬의 의미 있는 잔여는 재현되지 않았다. 타입 굵기/아이콘 미감은D1/D4에서 별도 평가한다. | [04-model-empty-1920.png](04-model-empty-1920.png), [11-model-selected-blocked-1920.png](11-model-selected-blocked-1920.png) |
| D3 radius/border/shadow 역할 | 3 | 3 → 3 | 2.25 | control6px,panel8px,dialog12px 계열. 기본panel은shadow없음,선택은2pxinset표식. | 면·경계·형태의 역할이 비교적 명료하다. 시간축 버튼은0pxradius로연속성을보존한다.모든컴포넌트예외의완전한정규화까지검증한것은아니다. | [../final-audit/styles-states.json](../final-audit/styles-states.json), ../final-audit/studio.css:30–39,669–758 |
| D4 icon·썸네일·대체 상태 | 3 | 3 → 3 | 2.25 | 실제영상첫프레임poster,이미지thumbnail,영상nativecontrols. 검토✓/○와disclosure›/삼각형. | 실제asset의대표이미지가대상인지를돕고허위이미지를쓰지않는다.텍스트glyph와native아이콘이혼용되어광학무게가완전히같지는않다.새아이콘세트를도입할필요까지단정하지않는다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/05-comparison-image-video-1920.png](../final-audit/05-comparison-image-video-1920.png) |
| E1 원본·preview·aspect·poster 맥락 | 3 | 4 → 4 | 3 | 원본320×180/180×320,contain비율보존.비교두stage약471×300px.원본5초와편집1초구분. | 정의한이미지/영상및혼합비율표본에서왜곡·crop없이실제poster와출처를보여준다.영상콘텐츠품질·장시간코덱호환성은별도다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), ../final-audit/05/06 비교 캡처·JSON |
| E2 공통 시간좌표·길이·파형 | 4 | 3 → 3 | 3 | ruler/wave/track x233,w1350px공유.1/2/4초폭192.852/385.711/771.422.재생2.172s playheadx651.953,예측651.886(약0.07px차). | 시간좌표와비례는실측으로맞는다.파형은실측진폭이며fixture가작은일정신호라거의평평하다.실제음악의강약/긴타임라인유용성은이fixture로검증하지못했다. | [../final-audit/02-sequence-1920.json](../final-audit/02-sequence-1920.json), [../final-audit/styles-states.json](../final-audit/styles-states.json) |
| E3 현재 위치·transport·seek/sequence | 4 | 3 → 3 | 3 | sequence00:02.172/00:07.000과원본frame약1.4386s,장면02자막.비교상대1.000s에서source1.250/1.000s. | 시간과trim관계를관찰할수있고실제재생·멈춤이된다.로딩중seek/장시간브라우저동기검증은이번직접표본에없다.DM01–03코드종료를재결함으로계산하지않는다. | ../final-audit/02-sequence-1920.png/json, [../final-audit/06-comparison-video-video-1920.json](../final-audit/06-comparison-video-video-1920.json) |
| E4 Take 비교·audition과채택 분리 | 3 | 4 → 4 | 3 | 초기Take1과3으로상이한기본값.영상+이미지,가로+세로영상시험.비교무음·짧은1초구간정지·선택/승인/편집불변. | 정해진표본에서비교와채택이구분되고모달닫기복귀가명확하다.프레임정밀비교가아니라는표시를보존한다. | ../final-audit/05/06 비교 캡처, [../final-audit/comparison-draft-journey.json](../final-audit/comparison-draft-journey.json) |
| E5 음원·자막·편집 버전 관계 | 1 | 3 → 3 | 0.75 | 편집7초,음원v1/0.5–7.5초,저장버전1·출력승인됨,납품검토전의별도표시. | 화면에서음원·자막·출력버전관계를추적할수있다.새렌더·실제오디오청취·MP4자막재추출은이번에하지않았고기능팀증거로분리한다. | [../final-audit/02-sequence-1920.png](../final-audit/02-sequence-1920.png), [../final-audit/13-output-state-1920.png](../final-audit/13-output-state-1920.png) |
| F1 상태 전이·입력 보존 | 4 | 3 → 3 | 3 | 이전 dirty→단계 전환→취소를 보존. 이번 controlled unknown에서 장면02 초안/오류 오염0,01복귀 초안 보존. receipt 응답 대기 중 새 문자를 입력한 뒤 committed 합성 응답에도 새 초안 유지. | 새 비동기/장면 전환 표본은 안정적이다. 프로젝트 간 전환·브라우저 종료 후 미확정 요청 복구·실제 서버 저장 지연은 이번 독립 시험에서 실행하지 않았다. 전체 상태전이 최고앵커가 아니라3을 유지한다. | [controlled-errors.json](controlled-errors.json), [10-newer-draft-preserved-1920.png](10-newer-draft-preserved-1920.png) |
| F2 핵심 keyboard/focus | 3 | 3 → 4 | 3 | reload한 초기BODY에서 Tab/Enter/Arrow/문자입력/Escape만으로 미리보기·비교·닫기·검토 수정·초안 취소·출처·모델창 여정 완료. 52관측/8목표. 정밀 구간35Tab 모두 가시. | 고정 H3에 정의된 핵심 여정을 처음부터 키보드만으로 완료하고 비교/모델/취소의 focus 복귀를 확인했다. 정밀 폼 구간만 summary 명시focus 진입을 사용했으며 이를 초기 여정과 구분한다. 모든 native 영상 메뉴나 스크린리더 검증은 아니다. | [keyboard-initial.json](keyboard-initial.json), [precision-keyboard.json](precision-keyboard.json) |
| F3 실패 영향·복구 | 2 | U → 3 | 1.5 | 2회 실행을 합쳐 변경POST4건·기존조회GET4건 모두 브라우저에서 가로챔. 400거절=입력 유지/다시 저장 가능. unknown=새 저장 disabled/기존 조회. 조회 응답 후 새 초안 보존. DB 전달0. | 실패 영향과 다음 행동을 실제 UI에서 확인했으므로U에서 평가 가능으로 변경한다. 다만unknown 안내의 “연결이 돌아오면”은 정상 연결의404unknown에도 원인을 네트워크로 좁혀 말한다. “잠시 후 기존 저장 확인”처럼 확인된 사실 중심 표현이 더 정확하므로3. 실제 서버 장애/청구/DB commit은 증명하지 않는다. | [controlled-errors.json](controlled-errors.json), [controlled-error-clean-captures.json](controlled-error-clean-captures.json) |
| F4 motion/reduced-motion | 1 | 3 → 3 | 0.75 | CDP의prefers-reduced-motion:reduce 실제match=true.버튼/shot/preview/summary transition·animation0s,scrollauto. | 선호설정에따른장식동작제거는확인했다.전체장시간모션·OS설정·의도된영상재생의모든조합은시험하지않았다. | [../final-audit/reduced-motion.json](../final-audit/reduced-motion.json), ../final-audit/studio.css:552–554,754–756,810–812 |
| G1 token→component 관리 | 4 | 3 → 3 | 3 | 동일 primitive/semantic 역할과 컴포넌트 토큰 유지. 현재 CSS 870행; 이번 변경은 기존 bounded rule 조정 및 model/transport 규칙 추가. | 토큰 역할은 유지되고 current computed 값에서 충돌은 재현되지 않았다. selector/조건별 override 추적 부담은 남는다. 중복이 곧 기능 결함이라는 뜻은 아니며 코드 축약을 새 필수 목표로 추가하지 않는다. | ../final-audit/studio.css:1–64,669–758,824–857, [../final-audit/styles-states.json](../final-audit/styles-states.json) |
| G2 scale·responsive 계약 | 3 | 3 → 3 | 2.25 | 현재 앱200% 본문28px, flow, 문서2505px,가로1920px/넘침0; 눈금 겹침0. 1280 정밀 문서900px와35Tab 접근 보존. 이전150%표본은 역사적 유지. | 큰 글자에서는 의도적으로 페이지 reflow/스크롤을 허용한다. 이는 기본1920 무스크롤 요구와 충돌하지 않는다. 실제 browser200/400%zoom·screenreader·사용자 text-spacing은 미검증이며 앱배율로 대체하지 않는다. | [15-app-text200-1920.png](15-app-text200-1920.png), [boundaries.json](boundaries.json) |
| G3 component/state 재사용 | 3 | 3 → 3 | 2.25 | rail/Take/inspector가같은승인✓/검토전○언어,선택은표식/pressed.시간축은길이·대상중심. | 동일의미의주요상태가반복적용된다.모든오류/반려/empty변형의실제표본은없으며glyph/상세문구의잔여는각주축에서만계산했다. | [../final-audit/01-selected-1920.png](../final-audit/01-selected-1920.png), [../final-audit/06-comparison-video-video-1920.png](../final-audit/06-comparison-video-video-1920.png) |

## 남은 실행 가능한 사항 — 새 목표 추가 아님

| 우선 | 원인→영향 | 현재근거 | 후속판단/재검증 | 점수반영 |
|---|---|---|---|---|
|P2 절충|작은viewport에서도정밀폼최소높이를유지→실영상세부판단공간감소|1280 영상218×123,문서900,Tab35접근성유지|1920배분을되돌리기보다1280조건에서폼/transport높이배분을검토. 같은작품·시간·자막과control접근유지로검증. 현재앱수정없음|A4만|
|P3 문구|unknown원인이확인되지않았는데연결복구를전제→기다려야할원인오해가능|통제404unknown에서도‘연결이돌아오면’|‘아직저장여부를확인하지못했습니다. 잠시후기존저장확인으로조회하세요’처럼확인된사실/행동중심. 입력보존/재제출차단유지|F3만|
|기존잔여|긴메모의세로읽기,작은메타·native/glyph광학차이,조건별CSS추적|이전직접자료+현재변경범위|기존표본내작업부담. 신규아이콘세트/자동요약/재설계등을이번완료의새조건으로추가하지않음|A3/D1/D4/G1각독립역할|

승인 완료에 밝은CTA가 없는 것은 결함이 아닙니다. 테스트 패턴의 화질, portraitletterbox,접근 가능한 내부scroll을미감감점으로잘못사용하지않습니다.1280작은영상과위문구외에새중대결함을만들어내지않습니다.

## 참고의 역할과 방법론 추적

| 사용자과업 | 참고근거 | 설계이유 | 구현/검증 |
|---|---|---|---|
|미디어를보며정밀시간편집|[Descript공식timeline](https://help.descript.com/timeline/timeline-overview),[ReferoDescript](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87)|분할작업맥락과시간좌표를유지;Loretune의px배분은우리판단|studio.css bounded높이·transport,V1,A4/Tab검증|
|선택대상과재생대상인지|[NN/g recognition](https://www.nngroup.com/articles/recognition-and-recall/),[Frame.io참조](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871)|대상/버전단서를보이게해기억부담완화|index.html상단,studio-media.js표시문구,V4/B1|
|모델선택·위험판단|[progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/),[PAIR mental models](https://pair.withgoogle.com/guidebook-v2/chapter/mental-models/)|선택/실행승인구분;기술진단은필요시열기|drawModelSettings/modelChoiceHint,closeddiagnostic,V2/V3|
|저장불확실성에서복구|[PAIR errors](https://pair.withgoogle.com/guidebook-v2/chapter/errors-failing/)|확정거절≠unknown,입력보존,같은요청조회|reviewSaveCheck/scopeddraft,F1/F3controlled시험|
|확대/키보드로작업|[W3C resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html)|글자축소나hidden으로맞추지않고필요시reflow|앱200%·35Tab·H3,실제zoom은U|

경쟁사참고는원본뷰포트/시점/과업이다른captured이미지와공식자료입니다.1920라이브동일조건비교나경쟁사점수는만들지않았습니다. Runwaycapturedhome은조용한prompt shell만참고하며timeline증거로쓰지않습니다. NeuralFrames는공식tutorial Track/Storyboard이미지이며직접경쟁사계정관찰이아닙니다. Blender직접읽기402제약은이전기록그대로이며이번성공으로바꾸지않습니다. 방법론은 [적합성표](../../METHODOLOGY-FIT-MATRIX-ko.md)의채택/조건부/제외를유지합니다.

## 버전·보존·인계

| 소스 | SHA256 |
|---|---|
|index.html|`5fcc2cca3058d390968c08ce674463c08c6e777ed8c569e1c386d08fc41fd99b`|
|studio.css|`3a76cbdf0dc05834473d9d8a9d628f19bd12fcb363a216ee3a36faa1740268c4`|
|studio-media.js|`65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328`|
|app.py|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

시작·종료HTTP200제공본과로컬소스해시가동일합니다. 작품JSON해시도 `8ac30524626fcd58457cb62a2616710426e7ec33c1958f3d271bc3dca42a740d`로불변입니다. 새서버시작/재시작·앱/DB편집·키열람·유료호출·경쟁사계정작업은하지않았습니다. 앱배율100%,pendingfalse,모든임시fetch/catalog복원후별도Ego검증공간32를종료했습니다.

변경문서는새 [재검토scorecard](scorecard.json), [geometry](geometry.json), [상태/오류증거](controlled-errors.json),현재보고서이며이전감사원본은그대로입니다. 사용자요약과방법론표는기존Library정체성으로갱신합니다. 화면전달은비민감합성자료만이며Library결과는별도receipt에기록합니다.


## 확인된 Library 화면 전달

아래3개는현재고정본의1920×1080합성자료입니다.마지막화면은통제된클라이언트오류이며실제서버장애가아닙니다.

| 파일 | 확인된 Library ID |
|---|---|
| 06-expanded-sequence-1920.png | `libfile_16d638894f4c8191b4d1b922b76743f8` |
| 11-model-selected-blocked-1920.png | `libfile_22c9bf1630d48191a0fe821cabb7ae43` |
| 14-controlled-unknown-ready-1920.png | `libfile_d8f9f1968fd4819198709bb0b1ac0d94` |
