# Loretune 디자인 시스템 개선 요구·수용기준

상태: **현행 설계 요구 / 2026-10-26 추가 요구 반영**. 기존 구현과 최종 수용은 구분한다.

주 평가1920×1080 CSS viewport, 보조1280×900. 모바일 추가 작업은 보류한다. 표준 배율의 기본 데스크톱 작업은 페이지 전체 세로 스크롤 없이, 긴 목록/설정은 패널 내부에서 접근한다. 확대·작은 창의 reflow는 허용한다. [날짜별 변경안](AMENDMENT-20261026-DESKTOP-METHODOLOGY-ko.md)과 [현행 문서 목차](INDEX.md)를 함께 읽는다. 초기 문서는 [보존본](history/initial-design-stage-20261026/REQUIREMENTS-AND-ACCEPTANCE-ko.md)에 있다.

초기 설계의 역사적 기준은 [당시 감사](../design-system-audit-20261026/REPORT-ko.md)와 직접 열어 확인한 [최종 B 데스크톱](../final-delivery-20261025/final-desktop.png), [모바일](../final-delivery-20261025/final-mobile.png), [출처 펼침](../final-delivery-20261025/final-mobile-disclosure.png)이다. 기준 HTML SHA256은 `a59b8c494770d23000973c1c1b702c39d8fcb955e38ed04f045ccc4c94373c1b`였다. 이는 현재 실행본 hash를 뜻하지 않는다. 미디어 수정본과 shell 변경의 상태는 변경안 및 각 기능팀 release 보고서에서 구분한다.

외부 연구 세션의 새 reference lock을 수신했다. 기존 Loretune 중성 미디어 중심을 주축으로 하며 Descript는 시간 정렬, Frame.io는 asset/player 인접성, Runway home은 조용한 prompt shell에만 사용한다. [채택 결정](REFERENCE-LOCK.md)에 출처와 전달 근거의 한계를 기록했다. 경쟁사 HEX를 추정하지 않는다. 이 문서는 실제 구현 결과나 새 점수가 아니다.

## 결과로 해결해야 하는 일

1. 사용자는 선택한 작품·장면·Take, 검토 결과와 다음에 가능한 일을 바로 알 수 있어야 한다.
2. 제작 모델·비용·승인 범위는 결정할 때 읽을 수 있어야 하며, 내부 구현 설명은 기본 작업면을 차지하지 않아야 한다.
3. 색·타입·간격·상태를 한 곳에서 관리할 수 있고, 앱 글자 배율 변경이 모든 사용자 문자를 일관되게 확대해야 한다.
4. 음악영상의 시간·원본 길이·편집 길이를 혼동하지 않아야 한다. 미구현 편집 기능을 시각적으로 암시하지 않는다.
5. 1920×1080에서 미디어·장면·타임라인·검토/편집 조작을 같은 작업 공간에 유지한다. 모바일의 기존 preview/review 계약은 보존하되 추가 설계·시험은 이번 패스에서 보류한다.

## 변경하지 않는 계약

- 선택, 편집 채택, Take 검토 승인, 계획 승인, 실행 승인, 출력 스냅샷 승인, 납품 검토는 서로 다르다.
- 승인 완료·변경 없음 상태는 결과를 읽는 카드와 보조 ‘검토 수정’으로 충분하다. 밝고 강한 CTA를 억지로 추가하지 않는다.
- 저장 중/실패/결과 미확정/저장됨·화면 갱신 실패를 구분하고 입력을 보존한다. 미확정 요청은 조회로 복구하며 자동 재제출하지 않는다.
- 초안은 작품+장면+Take에 귀속한다. 비동기 저장 완료는 제출 이후 새 입력이나 다른 맥락의 초안을 지우지 않는다(F07).
- 실제 선택한 모델을 보존한다. 미검증·차단·미선택·실행 중·결과 준비됨을 섞지 않는다. Runway는 벤치마크이며 연결 모델로 표시하지 않는다.
- 테스트 미디어 표시는 남긴다. 권리·차단 이유·오류 영향·예상 비용·승인 범위·저장 여부는 장식 때문에 숨기지 않는다.
- 원본 미디어, 사용자 프로젝트, 서버/DB/권한/비밀, 실제 외부 모델 연결은 디자인 작업에서 변경하지 않는다.

## 요구사항과 관찰 가능한 통과 조건

| ID / 우선순위 | 개선 요구 | 통과 조건 | 판정 근거 |
|---|---|---|---|
| DS-01 / P1 | 최종 의미 토큰 단일화 | 활성 컴포넌트의 색·타입·간격·radius·focus·motion이 공통 역할 토큰 또는 문서화한 component alias를 사용. 동일 selector의 낡은 층을 계속 추가하지 않음. 상태 관련 `!important`는 불가피한 사유를 기록 | 정적 inventory와 최종 computed-style 표; 단순 HEX 개수 감소를 성공으로 보지 않음 |
| DS-02 / P1 | 글자 크기 계약 복구 | 앱100/150/200%에서 제목·본문·metadata·button/input·dialog·오류가 각각1/1.5/2배. 상태/조작이 잘리거나 겹치지 않음. line-height는 비례하고 터치영역은 축소되지 않음 | 고정 selector별 computed font-size/line-height 전후. 브라우저 실제zoom200/400%는 별도 시험 |
| DS-03 / P1 | 의미별 색·표면 | canvas/media/passive grouping/control/selected/focus/approved/error의 역할 분리. 주요 문자와 입력·focus 등 필요한 식별 쌍을 계산. 승인 색은 중립 유지 가능 | 실제 FG/BG 쌍 + 상태별 픽셀. 대비 계산과 전체 접근성 준수를 혼동하지 않음 |
| DS-04 / P2 | 타입·간격·형태 일관성 | 제목·객체/행동·본문/metadata의 읽기 순서가1920 주 평가/1280 보조에서 명확. 긴 한국어는 단어 중심으로 감기고 필요할 때만 강제 줄바꿈. 패널은 조용하고 주요 동작만 강조 | 동일 fixture의 기본/긴 문구/오류 상태; 400/500/600을 기본으로 하고 예외는 역할로 명시 |
| DS-05 / P1 | 반복 장면 정보 정리 | desktop의 전체 장면 제목은 중심 작업영역에서 주 제목으로 한 번. inspector는 짧은 장면번호+Take+검토 맥락. rail과 timeline의 객체 식별은 유지. mobile은 하나의 현재 맥락 strip 사용 | 현재 장면과 Take를 어떤 패널에서도 추적 가능하면서 동일 문단·긴 제목의 연속 중복이 줄어듦. 헤딩/aria 연결 보존 |
| DS-06 / P1 | 시간 기반 timeline | 공통 시간 눈금·표시 위치·폭이 **편집 시간**에 근거함. 실제 PCM 파형과 실제 재생상태 playhead를 연결. 축 단위/총 길이와 원본 trim·편집 길이 구분. 1초:2초:4초 항목은 같은 scale에서1:2:4 비례(반올림±1px). 최소 카드폭이 비례를 깨지 않음 | clip start/end 및 px/sec 수치, 실제 clip box 측정. 좁으면 scroll 또는 Storyboard 요약 전환; 숫자 편집 접근 유지. 파형 없으면 미분석, 재생 불가면 playhead/transport를 작동하는 것처럼 표시하지 않음 |
| DS-07 / P1 · 이번 추가 작업 보류 | 모바일 preview와 review 연결 | 390×844 및320×568 기본 배율에서 현재 장면/Take/상태와 bounded 실제 preview, 핵심 검토 맥락/행동을 함께 확인할 수 있음. 긴 메모는 자연 scroll. 확대·키보드에서는 겹침 없이 명시적인 preview 접기/펼치기 허용 | 실제 이미지/영상 각각 캡처. 같은 미디어 player를 중복 생성하거나 독립 재생 상태를 만들지 않음 |
| DS-08 / P1 | 맥락별 행동 | no Take=기존 연결 경로; 미검토=결정·이유·저장; 승인/거절 완료=결과·메모·수정; dirty=저장/취소; saving=입력 보존+중복 방지; error=인접 복구 | 상태표와 순수 상태 시험, 실제 UI dirty/error 캡처. 저장 성공과 검토 승인 상태를 혼동하지 않음 |
| DS-09 / P1 | Take 비교 | 2개 이상이면 기본 서로 다른 Take. 0/1개는 명확한 기존 동작. 동일 높이 contain stage, scene/Take/검토상태/종류/원본과 편집 길이 정렬. 비교로 선택·승인을 변경하지 않음 | image/image, image/video, video/video·혼합 aspect. 동기 재생을 지원하지 않으면 그대로 안내. 기존 수정된 비교 로직은 보존 |
| DS-10 / P1 | focus·키보드·motion | 선택 표시는 inset/면, focus는 독립 외곽선, 검토는 기호+단어. Enter/Space/native details 동작, dialog Escape·focus 복귀. reduced-motion에서 장식 transition/animation 없음 | 실제 키보드 표본 경로·설정 시험. 스크린리더를 실행하지 못하면 미검증 표기 |
| DS-11 / P1 | 안전·정보 보존 | 선택 모델/가격/승인 범위는 commit 지점에 함께 표시. 오류는 기본 화면 가까이. provenance/원장/식별자는 접근 가능한 명시적 상세로 유지 | plan→approval→existing-result→Take→timeline→export→reopen 로컬 fixture 회귀 |
| DS-12 / P1 | 미리보기 모드와 임시 audition | sequence/selected-shot 미리보기를 명시. 다른 Take를 비교 재생하는 audition은 편집 사용확정·검토 승인과 분리. 전환 후 기존 시간/trim·사용 선택을 의도 없이 초기화하지 않음 | 각 전환 전후 실제 재생 position과 canonical timeline/선택/승인 상태를 비교. 실제 binding이 없는 버튼은 노출하지 않음 |
| DS-13 / P2 | 실제 poster와 대체 상태 | 현재 asset/version에서 추출한 영상 poster를 사용하고 버전이 다르면 재사용하지 않음. unavailable/pending은 명확히 표시. test badge 유지 | image/video/미연결/로딩/실패 표본. 임의 생성 이미지·다른 작품 썸네일 사용 금지 |
| DS-14 / P1 · 2026-10-26 추가 | 1920 bounded desktop workspace | 앱100%에서 기본/sequence/펼친 상세/출력의 문서 세로 스크롤 없음. 긴 패널은 내부 스크롤, 마지막 필수 컨트롤의 키보드 가시성. 글자 축소·잘림 금지. 확대/작은창은 접근 가능한 reflow 허용 | document/client/scroll 치수, panel overflow/scrollTop, focus rect, 동일 과업의 실제1920 캡처. [상세 조건](desktop1920/RUBRIC-v1.1-ADDENDUM-ko.md) |

## 시간 기반 timeline의 구현 경계

초기 최종B의 카드 flex는 최소144px 때문에 정확한 시간축이 아니었다. 이 문제는 역사적 설계 출발점이며 현재 결함으로 다시 계산하지 않는다. 후속 통합에서는 공통 시간축·파형·playhead가 구현돼 실제1/2/4초 비례 증거가 제공됐다. 새 shell에서는 같은 시간 좌표와 실제 재생 binding의 보존을 검증한다. 카드형 overview를 제공한다면 시간축과 혼동하지 않도록 Storyboard로 구분한다. transport/파형/playhead의 functional binding은 기능 소유 세션이 구현하며, 디자인 후보가 이를 가짜로 대신하지 않는다.

- `start[i] = sum(duration[0:i])`, `end[i] = start[i] + duration[i]`를 현재 timeline 데이터로 계산한다.
- 원본 시작 지점(trim)과 편집상 시작 위치를 다른 이름으로 표시한다. 음원 offset·자막 구간은 실제 저장 데이터를 사용한다.
- 짧은 clip의 레이블은 축 아래 연결된 목록/선택 맥락으로 읽게 할 수 있다. 표시 폭을 늘려 가짜 시간 비례를 만들지 않는다.
- 기존 숫자 편집·순서 변경·저장/취소·승인·출력 기능은 유지한다. 조작을 구현하지 않은 영역에는 resize handle·scrub cursor를 달지 않는다.
- export 결과·native preview의 재생시간을 무조건 프로젝트 시간으로 쓰지 않는다. selected-shot의 source time은 trim과 편집 start를 이용해 변환하며, sequence clock의 기준·duration·seek 범위를 기능 계약으로 명시한다.
- 실제 원곡 파형은 amplitude 데이터와 audio offset/time domain을 확인한다. 파형 미분석을 가짜 beat나 반복 장식 파형으로 채우지 않는다.
- 동기 Take 비교는 Loretune의 제안으로만 표시한다. 이번 전달 자료가 경쟁사의 동기 비교 기능을 증명한다고 말하지 않는다. 실제 동기 binding이 제공되기 전에는 기존 독립 native 재생을 유지한다.

## 화면 수용 범위

| 화면 | 우선 구조 | 필수 확인 |
|---|---|---|
| Desktop1920×1080 · 주 평가 | viewport shell; rail / media·transport / contextual review; 공통 timeline | 기본/sequence/정밀편집 펼침에서 document.scrollHeight≤clientHeight+1. 내부패널의 마지막 제어까지 키보드 접근. 영상·시간·주요행동 유지 |
| Desktop1280×900 · 보조 회귀 | compact project/save/settings + 단계; rail / media / contextual review; media 아래 time summary | preview·native controls·Take·timeline이 기본 첫 화면 안에 있음. 승인 완료 inspector에는 불필요한 primary 없음 |
| Desktop901/1150 경계 | 열 폭과 긴 제목 대응 | 숨겨진 필수 조작·겹침 없음. 최소 너비가 부족하면 의미 있는 패널 전환 |
| Mobile390×844 · 기존 계약, 추가 시험 보류 | compact shell; current identity; bounded preview+review 중심 | 승인/미검토/거절/dirty/error에서 object identity 유지. native player와 입력이 화면을 가리지 않음 |
| Mobile320×568 · 기존 계약, 추가 시험 보류 | 제목 줄바꿈과 순차 흐름 | 필요한 경우 세로 scroll. page 전체 가로 overflow 없음; timeline만 의미 있는 수평 scroll 허용 |
| 비교 | 두 미디어에 같은 contain stage, aligned metadata | 원본 aspect 보존·기본 다른 Take·선택/승인 불변 |
| 모델/계획/실행/출력/재개 | 모델·예상비용·승인·현재상태 중심 | 기술 trace 기본 노출 금지, 근거·상세는 접근 가능, 상태에 맞는 기존 행동 |

## 검증 방법과 종료 기준

1. **소스·화면 기준 고정:** 통합 전후 HTML/CSS hash와 fixture·viewport를 기록한다. 과거 후보를 새 통합본이라고 표시하지 않는다.
2. **정적 계약 검사:** token mapping, 실제 글자 배율, selector/ID·event 보존, 순수 상태 projection을 검사한다. 구현과 같은 답을 반복하는 테스트는 추가하지 않는다.
3. **통합 회귀:** 기능 소유 세션이 mock/local 제작 경로와 draft/저장/승인/복구를 검증한다. 테스트 건수를 시각 점수로 환산하지 않는다.
4. **실제 픽셀 수용:**1920 populated desktop·sequence·정밀편집 펼침·혼합aspect 비교·검토/dirty·기존 오류 또는 명시적 mock,1280 보조 회귀를 동일 fixture로 촬영하고 저장 이미지를 연다. 모바일 추가 촬영은 보류한다. native player·빈/미연결은 정직하게 표시한다.
5. **현행 rubric:** [7축 사전 기준](desktop1920/RUBRIC-v1-ko.md)과 [v1.1 추가 요구](desktop1920/RUBRIC-v1.1-ADDENDUM-ko.md)의20/15/15/15/15/10/10을 사용한다. 과거5×20 점수와 비교·환산하지 않는다.26개 세부항목, 평가 coverage, media/승인/keyboard/대비 gate를 별도로 보고한다. 전문가 판단이며 경쟁사 서열이나 사용자 연구 결과가 아니다.
6. **한계 분리:** 실사용자 연구, 전체 스크린리더, 실제zoom, live provider, 경쟁사 동일 조건 실험을 수행하지 않았으면 그대로 미검증이다.

수용 조건 통과가 자동으로90점이나 출시 준비를 뜻하지 않는다. 미디어 binding 계약과 이전 통합 증거는 이미 제공됐다. 현재 의존성은 새 bounded-shell 최종 source/served freeze와 실제1920 상태 검증이다. 초기 연결 실패나 이미 종료된 DM01–03을 현재 blocker로 재사용하지 않는다.


## 2026-10-26 최종 독립 검증 상태

고정된1920 shell의 직접 화면 검토와 실제 토큰/geometry 측정을 완료했습니다. [최종 독립 보고서](desktop1920/final-audit/REPORT-ko.md)와 [항목별평가](desktop1920/final-audit/scorecard.json)를 참조하세요. 이 추가 기록은 기존 제안·과거 검증을 소급 변경하지 않습니다. 기본/sequence/정밀/긴패널/출력의1080px 문서와 상세접근을 확인했고, 실제오류·commit·전체keyboard-only·browserzoom·screenreader는 미검증 범위를 유지합니다. 앱코드와 원본07 아키텍처는 변경하지 않았습니다.
