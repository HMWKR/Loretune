# 실행 전 고정: 프론트엔드 시각·상태 QA

2026-10-26T04:03:14.289335+00:00

새종합점수없음.각항목은PASS/FAIL/BLOCKED/NOT RUN.기존닫힌결함은회귀케이스이며새결함이아니다.기능/미디어/성능/저장동작시험은다른담당소유.현재표는실행기준이며세부10그룹시각matrix수신시실행전별도appendix로고정한다.

## 안전·증거 조건

기존승인된합성작품만사용.모든외부provider요청및변경요청차단,실제API변경요청금지.임시브라우저초안/표시fixture만취소/복원.브라우저차단이backend격리증거라는주장금지.모든실제write는격리fakebackend가증명된경우에만해당소유담당수행.앱/DB/server/dependencies/계정불변.기존TaskSpace는종료됨;새goal용별도검증공간하나사용.

## 환경·스크린샷 조건

CSSviewport1920×1080/DPR1/앱100%기본,1280×900보조.실제browserzoom은별도.브라우저빌드·OS표시·언어·timezone·fontready·실사용글꼴·media readiness·현재시간·hover/focus·scroll·열린details·원본sha/fixturefingerprint기록.캡처후파일을열어검사.성공API와decodedframe은분리.

| ID/과업 | 기준 종류 | fixture·순서 | 기대값 | 출처 |
|---|---|---|---|---|
|ENV01 렌더링 환경/fixture 고정|method / evidence protocol|existing project; 브라우저버전/viewport/DPR/visualscale/fonts ready/실제platformfont/소스·servedhash 기록|현재소스일치,로드/폰트완료조건기록;누락값을추정하지않음|[공식](https://playwright.dev/docs/test-snapshots)|
|L01 기본 승인 작업대 두 viewport|Loretune proposal|existing approved shot01; 1920×1080/1280×900,앱100%,기본Take를캡처|문서세로scroll없음,preview/Take/timeline/review주요진입점함께가시,clipping없는경계|[공식](https://playwright.dev/docs/test-snapshots)|
|L02 sequence+정밀 편집 두 viewport|Loretune proposal|existing01 editing /02 playback 2.172s; 같은장면/시간/자막,상세펼침|문서높이viewport,내부scroll허용,조작접근,media contain;최소면적숫자임의설정안함|[공식](https://playwright.dev/docs/test-snapshots)|
|L03 긴 목록/한글 메모|Loretune proposal|temporaryDOM60rail/40paragraphs; 원본clone보존후목록/메모늘리고패널끝Tab;복원|document넘침없음,끝focus접근;실제60장면성능으로주장안함|[공식](https://playwright.dev/docs/test-snapshots)|
|S01 계획 empty|Loretune proposal|existing empty conversation/plan; 계획단계열기,제출안함|빈상태대상/다음입력명확,불필요한내부상세기본노출없음|[공식](https://testing-library.com/docs/guiding-principles/)|
|S02 미검토/반려 review 상태|Loretune proposal|existing authorized fixture if present; 저장없이보기가능한표본만선택;없으면NOT RUN|현재scene/Take/검토상태/맞는행동;합성DOM은실제경로와별도|[공식](https://testing-library.com/docs/guiding-principles/)|
|S03 dirty/cancel 두 viewport|Loretune proposal|temporary local review draft; 검토수정→긴한글입력→취소;저장없음|저장/취소구별,입력가시,취소후focus복귀,canonical불변|[공식](https://testing-library.com/docs/guiding-principles/)|
|S04 error/unknown 시각표현|Loretune proposal|temporary in-memory presentation fixture only; 기존error rendering에fixture상태만주입;서버요청없음|오류인접,원인중립,disabled저장과조회구분,긴문구줄바꿈;복구기능시험아님|[공식](https://testing-library.com/docs/guiding-principles/)|
|S05 실제 loading/poster-unavailable|evidence gap|functional owner controlled fixture; 안전한로딩시점근거제공시검사;없으면NOT RUN|loading을성공/실패와구별,안정화전캡처를일반완료화면으로채택하지않음|[공식](https://playwright.dev/docs/test-snapshots)|
|M01 모델 미선택/미검증/차단/긴이름|Loretune proposal|actual catalog unsaved + synthetic long name; 모델창열고저장없이선택/긴이름표시,Escape복원|선택/불가이유/승인별도구별,모델명전체접근,가로넘침없음|[공식](https://testing-library.com/docs/guiding-principles/)|
|D01 비교 dialog/contain|Loretune proposal|existing Take1/3 image-video; 비교열기,두media크기/identity측정,Escape|동등boundedstage/원본비율,닫기focus복귀,상태는색만의존안함|[공식](https://playwright.dev/docs/test-snapshots)|
|AX01 이름/역할/상태 트리|method / evidence protocol|default/dialog/dirty; CDP accessibility snapshot과user-facingname검사|현재선택/disabled/expanded/name노출기록;스크린리더발화통과대체아님|[공식](https://testing-library.com/docs/guiding-principles/), [공식](https://playwright.dev/docs/accessibility-testing)|
|AX02 초기 keyboard-only|WCAG AA boundary + Loretune proposal|reload initial page; 초기BODY부터Tab/Enter/Arrow/Escape,미리보기/비교/검토취소/출처/모델|AA:focus완전히가려지지않음;제품:전체control가시.명시focus로전체여정대체금지|[공식](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html), [공식](https://playwright.dev/docs/actionability)|
|AX03 정밀 폼 keyboard 두 viewport|WCAG AA boundary + Loretune proposal|L02; summary에서연속Tab,상세패널scroll관찰|AA최소와제품전체가시를따로기록|[공식](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)|
|AX04 실제 색상쌍|WCAG AA boundary|normal/selected/focus/dirty/error; computedFG/BG/opacity층+스크린샷으로계산|보통문자4.5:1,large3:1,필수비문자3:1;장식/비활성예외구분,반투명배경임의대체금지|[공식](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [공식](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)|
|AX05 forced-colors|Loretune proposal|same selected/dirty; CDPforcedcolorsactive,match확인,선택/focus/오류단서캡처;복원|shadow없이도필수단서/텍스트보존;실제Windows사용자환경통과아님|[공식](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)|
|AX06 reduced-motion|Loretune proposal|same editor; CDPmedia reduce확인,computedtransition/animation,복원|불필요장식motion제거;영상재생을임의비활성화하지않음|[공식](https://playwright.dev/docs/test-snapshots)|
|AX07 앱100/150/200% 두 viewport|Loretune proposal|same editor; textScale정상UI변경,문서/패널/라벨/조작확인,복원|글자확대와reflow,가로넘침/핵심clipping없음;브라우저zoom으로부르지않음|[공식](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html), [공식](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)|
|AX08 실제 browser200/400%|WCAG AA boundary|same app100 editor; 정상브라우저확대경로지원확인,실제배율변화를검증한때만실행|지원불가/변화미확인시BLOCKED;DPR/CSStransform/resize로대체금지|[공식](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html), [공식](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)|
|AX09 비드래그 pointer 대안|WCAG AA boundary|existing timeline/range; drag없이단일pointer로위치선택/숫자입력UI접근;저장없음|해당drag과업에single-pointer대안,keyboard만으로통과하지않음;미디어decode정확도별도|[공식](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)|
|AX10 기존 axe 실행|method / evidence protocol|meaningful default/dialog/dirty; 현재설치/페이지axe존재확인후가능할때실행;설치금지|위반/incomplete/pass모두보존;자동검사=전체인증아님|[공식](https://playwright.dev/docs/accessibility-testing)|
|VR01 같은환경 screenshot 재현성|method / evidence protocol|paused ready selected scene; font/미디어ready/포커스/hover/scroll고정한2캡처바이트차이와위치확인|차이는변화근거;미감점수아님;오류/중요영역mask나baseline교체금지|[공식](https://playwright.dev/docs/test-snapshots)|
