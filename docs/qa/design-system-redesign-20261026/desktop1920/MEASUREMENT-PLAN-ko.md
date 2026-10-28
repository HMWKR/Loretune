# 1920 주 평가 측정·캡처 계획

주1920×1080,보조1280×900. 모두브라우저content viewport의CSS px이며물리모니터해상도라고부르지않는다. DPR/실제캡처픽셀크기/apptextscale/browserzoom을별도로기록한다. 모바일은이번패스에서새로시험하지않는다.

## 현행 추가 조건

2026-10-26 업데이트: JS ae019c88 /CSS f6f9ebff의 미디어 수정 freeze는 이미 전달됐고, 실제1920 캡처·computed를 baseline으로 읽었다. 현재 대기 대상은 그 이후의 **bounded-shell 최종 freeze**다. [v1.1](RUBRIC-v1.1-ADDENDUM-ko.md)에 따라 document scrollHeight/clientHeight 및 패널 내부 scroll·Tab 가시성을 모든 정상 작업 상태에서 측정한다. 모바일은 보류한다. 아래 ‘설계 시작 때’는 당시 상황을 보존한 기록이다.

## 버전과 baseline

현재이전검증값은HTML846e18…/CSS5f50ef…/mediaJS8f95c2…이다. 이번설계시작때디스크에서CSS`f6f9ebff08ba722bf05f038697671c1c299d778a72d7729e63a4d7a33c87dd58`,JS`ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e`가읽혀수정중임을확인했다. 이중간파일을새고정본으로평가하지않는다.

기능팀이새freeze/hash를전달하면GET으로source/served를대조한뒤시작한다. 종료에도해시를확인하며,도중변경시영향받은항목만보류한다. 이전1920안정캡처가없으므로1280이미지를늘려‘1920before’로만들지않는다. 첫고정1920을B1baseline으로,후속실제수정1920을B2로비교한다.1280기존/수정본은같은viewport·과제일때만별도로비교한다.

## 과제·상태 고정

| 표본 | 작품/미디어/상태 | 목적 |
|---|---|---|
|S01 기준작업대|`디자인 시스템 기능 QA 20261026`,장면01/Take1/승인완료,원본paused0초,100%앱배율|composition·token·정보위계·첫화면 |
|S02 기존과제연속성|`디자인 다중장면 QA 20261025 1330`,장면01/Take2/기존검토,1/1.5/2초timeline|동일과제1280과새1920의사용성기록.새영상생성없음 |
|S03 sequence/time|S01의1/2/4초timeline,0/1/3/7초및구간중간위치|시간축·현재장면/위치·trim·음원offset·caption |
|S04 comparison|S01의Take1/2,가로/세로영상,공통상대0초와종료;Take3이미지혼합|equalcontain·상태/identity·audition독립 |
|S05 reviewed→dirty→cancel|현재승인카드,저장하지않는식별가능한임시이유,취소복귀|행동위계·입력/focus·저장enabled |
|S06 unavailable/error/disabled|기존미연결모델/권리·미디어불가상태및기능팀이제공하는허용된로컬오류fixture|실제상태표현.새유료호출·실서버실패유발·승인추가금지 |
|S07 keyboard/focus|S01에서Tab/Enter/Space/Escape로핵심경로|focus구분·도달·복귀.프로그램focus만으로전체journey통과금지 |
|S08 scale/motion|앱100/150/200%각각;브라우저실제200%가능할때;reduced-motion|서로다른변수를혼동하거나double-scale하지않음 |

미검토/거절표본을만들기위해새승인·거절데이터를기록하지않는다.기존fixture/비교에서상태를읽거나승인된표시용mock을사용하며모의상태를표시한다.못얻으면해당항목은U이다.

## 캡처 수락

1. 명시적project/state/mode를읽고selectedTake·timelineversion·sourceURI의동일성을확인한다.
2. 영상readyState와실제frame·현재시간을확인한다. spinner/blank/반쯤읽힌poster면안정증거로수락하지않는다.
3. capture저장→그파일열기→민감정보없음/의도한상태확인→acceptedmanifest.새image는확인후에만Library전달한다.
4. 비교그리드에는viewport,원본pixel크기,DPR,mediaaspect,상태,촬영시각,source/servedhash를붙인다.
5. hover와focus는같은대상을default→hover→focus로촬영한다.선택/승인/disabled는다른의미임을명시한다.

## 정확한 측정 항목

| 범주 | 추출값 | 판정 방법 |
|---|---|---|
| canvas/surfaces |computedbackground,color,border,opacity,ancestor배경|rootHEX와최종적용값을구분.투명층은실제합성배경계산 |
| text |font-family,size,weight,line-height,letter-spacing,word-break|한국어제목/메모/metadata/시간/버튼/오류별.폰트fallback명만으로실제glyphfont확정하지않음 |
| geometry |각panel의x/y/w/h,padding/gap/border/scrollWidth|동일DOMrole의표.숫자·rect와시각판단을별도로표시 |
| media stage |stagecontentrect,원본intrinsicW/H,fit,actualvisibleframe|contain기준이미지영역과검정stage면적을별도산출.큰stage자체를큰영상으로계산하지않음 |
| media 면적 |Astage,Acontent,Acontent/viewport,Acontent/stage|`w=min(stageW,stageH×aspect); h=w/aspect`.UAcontrolsoverlay/border는별도.면적이클수록무조건가점하지않음 |
| prose |실제줄수/최장행폭/읽는텍스트최대폭|1920폭전체를메모문장으로늘리지않음.한국어에ch단위의정확글자수보장은하지않음 |
| first-screen |preview/transport/axis/현재정보/필수actionrect와viewportintersection|전체표시/일부/scroll필요를구분.‘아래보임’과‘아래끝까지보임’다름 |
| time coordinates |t→x,각clipstart/end,rulertick,wavewindow,playhead|같은x원점/scale.1/2/4초의폭은1:2:4,반올림허용±1CSSpx |
| playback |mode,clockdomain,currentTime,sourceTime,trim,offset,ready/paused/error|숫자position만바뀌고frame이안바뀌면통과아님.이전event·루프·음악누출도확인 |
| state/control |hover/focus/selected/disabled/review/outcome,outline,border,text/symbol,label|실제현재상태와보이는의미가맞는지.강한CTA의개수로품질평가금지 |
| icon/shape |glyph/svgsize,stroke,alignment,radius,shadow|역할이같은것끼리비교.모든radius를같게할필요없음 |

## 고정 측정 selector 후보

현행계약의`.lt-studio-shell`,`.lt-stage-bar`,`.shot-board`,`.lt-shot-header`,`.inspector`, `#preview`, `#sequenceTransport`, `#previewMode`, `#sequenceTime`, `#sequenceSeek`, `#takes`, `#timeAxis`, `#timeRuler`, `#timeWave`, `#timePlayhead`, `#track`, `#takeReviewStatus`, `#creatorSavedReason`, `#creatorEditReview`, `#reviewReason`, `#reviewTake`, `#discardTakeReviewDraft`, `#compareDialog`, `.comparison-media-stage`, `#comparisonTransport`를사용한다.새freeze에서존재/의미를다시확인하며옛selector를억지로맞추지않는다.

## 결과 파일

- source/served-start/end, fixturefingerprint-before/after
- metrics-1920.json / metrics-1280.json / state-style-matrix.json / contrast.json
- time-coordinate-observed.json / media-regression-observed.json / keyboard-path.json
- accepted-capture-manifest.json / rejected-capture-notes.md
- rubric-scorecard.json (U는null) / REPORT-ko.md

이목록은계획이며아직생성·통과했다는뜻이아니다.앱코드·서버·DB는디자인담당이변경하지않는다.
