# 1920 V1–V4 한정 개선 — 구현·QA 인계

2026-10-26 · 실제 코드 고정 · localhost8773 · 외부 API 호출0

> 후속 한정 수정(2026-10-26): [원인 중립 unknown 안내·1280 높이 배분](../desktop-residual-20261026/REPORT-ko.md). 아래 화면/해시는 V1–V4 당시의 역사적 고정본이며 최신 해시는 후속 인계를 참조합니다.

## 결론과 범위

독립1920평가의 V1–V4를 실제 앱에 반영했다. 전체346개 자동 테스트와6개 JavaScript 문법 검사 통과. 같은 합성 작품·1920×1080 CSS viewport에서 sequence+자막+정밀편집의 실제16:9미디어가 약334×188에서505×284px로 커졌고 문서는1080px를 유지한다. 기존 정밀 입력·버튼34개와 추가 진단 summary의 키보드 접근을 확인했다. 초기 음악 화면부터 검토 수정·취소·모델창까지의 키보드 전용 경로도 별도로 완료했다.

이 문서는 구현자의 검증 결과이며 새로운 시각 점수가 아니다. 독립 이전 점수74.25/평가98점은 이전 고정본의 결과로 보존한다. 점수, 경쟁사 동등성, 출시 준비, WCAG전체 준수를 재판정하지 않았다. 신규 공급자 연결·키 열람·유료 생성·배포·원본 명세 수정은0이다.

## 실제 변경과 절충

| 발견 | 적용 및 이유 | 위치 | 검증 |
|---|---|---|---|
|V1 미디어 축소|기존 bounded shell에서 펼친 타임라인 배분44%/최소360px를38%/최소340px로 조정. transport상태와 자막을 같은 행에 배치하고 중복 여백 축소. 글자/캡션/조작을 제거하지 않음|`studio.css:842`, `studio.css:858` 이후|1920실측 문서1080, 타임라인하단1064, 실제영상505×284.34controls+1summary 모두 focus center가시|
|V2 구현 설명 노출|일상 설명은 ‘저장된 버전과 승인 상태를 확인합니다.’. 기존 자산 해시 검증 안내는 ‘검증 상세’ 아래 보존|`index.html:254` drawTimeline|접힘에서 실제checkVisibility=false, Enter펼침=true. 오류·주의·음원·버전·승인 정보는 그대로|
|V3 모델 선택 반복|선택 상자에 짧은 모델명 한 번 표시; 긴 모델명은 전체 이름을 별도 줄바꿈. 미선택에 빈진단숨김. 선택/미검증/차단/사용불가/지원종료 구분, 안내간격토큰 적용|`index.html:212` modelChoiceStatus/modelChoiceHint/creatorModelReason, drawModelSettings|실제브라우저 미선택·FLUX미검증·Kling차단·긴이름 unavailable. unit에retired/active표시도 포함. 실제active등록안함|
|V4 선택·재생 혼동|상단 ‘편집 선택 · Take1’, transport ‘재생 장면:02…’를 별도 표시|`index.html` draw, `studio-media.js:90`|편집장면01 상태에서02를2.172초에미리봄. canonical프로젝트·선택·승인 불변|

V1은 정밀 폼을 전부 한 화면에 펼치는 방식이 아니다. 미디어에 높이를 더 배정하는 대신 기존 내부 스크롤 사용량이 늘어난다. 주요 타임라인 조작은 초기 화면에 유지되고 세부 폼은 키보드로 접근한다. 긴 자막5회 반복도 잘라내지 않고63px로 줄바꿈되며 문서1080/가로넘침0이다. 1280은 보조 회귀이며 동일sequence+정밀 상태 영상약219×123px로 작다. 이 조건의 미디어 크기를1920성과처럼 일반화하지 않는다.

## 같은 상태 측정과 화면

실제Ego브라우저content1920×1080/DPR1/앱100%. 영상은 합성 로컬320×180패턴이며 실제AI결과가 아니다. contain·원본비율 유지. 원소의전체폭이 아니라 intrinsic aspect와client영역으로 실제그려지는미디어를 계산했다(소수반올림).

|상태|이전 독립 실측|현재 실제미디어|문서/타임라인하단|
|---|---:|---:|---:|
|선택Take|707×398|718×404|1080/1064|
|sequence+자막|529×298|599×337|1080/1064|
|sequence+자막+정밀|334×188|505×284|1080/1064|

모든 현재3상태 video.readyState4. 자세한 측정은 [layout-keyboard.json](layout-keyboard.json). 이전값은 [독립 baseline](../design-system-redesign-20261026/desktop1920/final-audit/REPORT-ko.md)의 같은작품·표시상태이며 동시A/B사용자실험이 아니다. 미디어높이 증가는 미감점수나 사용자성공률을 뜻하지 않는다.

직접 저장 픽셀을 확인한 전달 화면:

- [선택Take1920](final-selected-1920.png) / [sequence1920](final-sequence-1920.png) / [sequence+정밀1920](final-expanded-sequence-1920.png)
- [출력·진단 접힘](output-details-1920.png)
- [모델 미선택](model-empty-1920.png) / [미검증·차단 선택](model-selected-blocked-1920.png) / [합성 긴이름·사용불가](model-long-unavailable-1920.png)
- [제어된 저장 거절](controlled-rejection-1920.png) / [제어된 미확정·조회](controlled-unknown-1920.png)
- [앱글자200%](app-text200-1920.png) / [보조1280](secondary-expanded-1280.png)

`candidate-expanded.png`는 중간후보. 최종사용자화면은 `final-*`와위상태캡처. 각파일SHA256/캡처mtime은 [release-manifest.json](release-manifest.json)에 있다. 앱소스최종변경 후 모든최종캡처를 수행했다.

## QA 결과와 증거의 경계

|과업/시나리오|기대값|실제결과·증거|
|---|---|---|
|전체 회귀|기존342+신규4, 실패0|346/346,44.306초. [로그](full-regression.log). HTTP/격리DB/providerfake/실제FFmpeg합성렌더 포함|
|새 단위회귀|미선택≠비활성선택, 긴이름전체, active도실행승인별도, 미디어수명불변|`tests/test_desktop_refinement.py`4개. 관련desktop/save/media와10개targeted통과|
|문법|변경JS 구문오류0|6개검사PASS [static-check.json](static-check.json)|
|초기페이지 keyboard-only|마우스/focus강제없이 review/cancel/modelmodal완주|reload음악화면→Tab/Enter→검토수정→한국어입력→취소→모델창→Escape.45관측,취소focus복귀. [기록](keyboard-initial-journey.json)|
|정밀 폼 keyboard|기존34입력·버튼 접근가능|34controls+진단summary1,35모두가시·문서scrollY0. 이구간만 summary명시focus진입. 초기전체경로시험과구분 [기록](layout-keyboard.json)|
|확정400거절|입력보존·구체적수정/저장안내·다시제출가능|실제UI클릭,fetch가POST를가로채400합성응답.입력유지/pending없음/저장활성|
|응답유실·unknown|실패로단정하지않음·추가POST금지·기존GET조회|POST는서버로보내지않고TypeError합성.저장disabled,조회GET만실행,404unknown후pending보존|
|unknown후새초안/context|다른장면오염없음·이전receipt가새입력삭제금지|장면02에는01초안/오류없음,01복귀보존.새초안작성후합성committed조회로이전요청만정리.새초안유지. [상세](controlled-save-errors.json)|
|V3모델상태|실제선택값보존,unavailable를미선택으로안씀|저장하지않은select조작과임시합성catalog/state.종료시원상복원.긴이름dialog가로overflow0 [상세](model-states.json)|
|진단/확대|평상시기술문구숨김,키보드펼침가능;확대가로손실없음|진단false→true.앱200% body28px/flow/문서2515px/가로1920.정밀폼전체가펼쳐진상태.시간눈금간격유지 [상세](boundaries.json)|
|모바일보존|기존player중복/가로넘침없음|390폭document390/player1.심층개선은계속보류|
|데이터/권한|원래작품·선택·승인·모델활성상태불변|전후프로젝트SHA256동일,종료pendingfalse. [runtime](final-runtime.json)|

오류시험은 **제어된 browser fetch test doubles**이다. 실제서버장애·저장commit·유료공급자검증이아니다. 두POST는모두서버로전송0; 복구GET2건도합성응답이다. 마지막‘committed’응답은시험용기존요청정리분기이며 실제DB저장을증명하지않는다. 새초안은명시적취소했고fetch를복원했다. 인증헤더/키는기록하지않았다.

처음경계검사에서는접힌details안의pre.getClientRects가남는브라우저특성을가시성으로잘못측정해실패했다. 읽기전용진단에서checkVisibility=false를확인하고 harness v2로교체해통과했다. 앱수정이나실패은폐가아니다. 최초script와v2를보존했다.

## 고정 소스·데이터·보존

|파일|SHA256|
|---|---|
|index.html|`5fcc2cca3058d390968c08ce674463c08c6e777ed8c569e1c386d08fc41fd99b`|
|studio.css|`3a76cbdf0dc05834473d9d8a9d628f19bd12fcb363a216ee3a36faa1740268c4`|
|studio-media.js|`65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328`|
|app.py(불변)|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

HTTP200의HTML/CSS/mediaJS가소스와byte동일. 기존서버는정적파일을매요청읽으므로재시작하지않았다. backend/DB마이그레이션변경없음. URL `http://127.0.0.1:8773`, data `/tmp/loretune-ms-qa-20261025`. 미디어JS변경은표시문자열1개뿐이며 DM01–03수명처리와소스diff를unit으로보장한다. baseline와변경패치는 [baseline.json](baseline.json), [implementation.patch](implementation.patch), `before/`에보존.

작품`디자인 시스템 기능 QA20261026`의전후JSON SHA256:
`8ac30524626fcd58457cb62a2616710426e7ec33c1958f3d271bc3dca42a740d`.

이미완료한새보존백업: `docs/qa/desktop-shell-20261026/backup/20261026T021935Z`. SQLite mode=ro/query_only읽기트랜잭션과Connection.backup, integrityok·23테이블행수일치,DB1/자산16/출력21 총38파일6,627,800bytes와미디어해시검증. [백업검증](../desktop-shell-20261026/backup-location.json).10월25백업미변경,비밀/환경파일제외.이번브라우저QA는canonical불변이므로백업을중복작성하지않았다.

## 방법론 연결·변경 기록·남은 한계

디자인담당의 [methodology fit](../design-system-redesign-20261026/METHODOLOGY-FIT-MATRIX-ko.md)와 [L01–L14 decision ledger](../design-system-redesign-20261026/desktop1920/METHODOLOGY-AND-DECISION-LEDGER-ko.md)를단일설계근거로유지한다. 이번최소변경은 L01/L02의미디어·작업맥락에V1, L03/L04의객체정체성에V4, L09/L10의모델/실행구분에V3, L11오류복구와L14키보드에추가실험을연결한다. V2는위험정보를유지하면서기술세부를점진공개하는결정이다. 특정38%나HEX를경쟁사공식정답으로제시하지않는다.

변경기록:2026-10-26 이전342고정본→V1–V4소스3파일+회귀4개→346통과→현재정적응답hash고정. README현재인계만갱신했고기존독립감사·원본명세·점수표를고치지않았다.

남은한계:실제browser200/400%zoom·스크린리더전체·사용자실험·전체WCAG는미검증.앱글자배율과다르다.실공급자/실청구/외부403해결을이번시험으로입증하지않음.모든실제모델은미검증/차단상태유지.새브라우저렌더job·서버재시작은반복하지않았고기존렌더재현/FFmpeg회귀와구분했다.넓은미디어와세부폼내부스크롤의절충은독립디자인재평가대상이며스스로점수를올리지않는다.

Ego전용검증공간31은종료했다. 현재설치버전0.6.0.20에서업데이트알림이있었으나업그레이드하지않았다. 실행/접근차단없음.
