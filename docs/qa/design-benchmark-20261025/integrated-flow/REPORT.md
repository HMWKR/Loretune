# 통합 고정본 · 실제 로컬 제작 QA 결과

**새 합성 프로젝트에서 모델 선택→음악→계획→사람 승인→모의 후보→검토→선택→부분 편집→한국어 자막→출력→새로고침 재개를 완료했다.** 영상은1.5초1920×1080, AAC48kHz, mov_text와 SRT 포함. 실제 AI 생성·외부 호출은0. 기능 완주가 경쟁력 있는 시각 완성도를 뜻하지 않는다.

11:11:32 UTC 종료 확인: 고정7개 소스 해시 불변, 제공 HTML SHA256 `cb810ea713f5865b7feecaaf510fc8d5851941216be78560bcb4ade3a6d576a3` 일치. `source-start.json`, `served-start.json`, `source-end.json`. 공용 소스 직접 변경0, 서버 재시작0. 전용 Ego TaskSpace7 정상 종료. 테스트194개는 기능팀 결과이며 이번 브라우저 감사의 테스트 개수로 계상하지 않았다.

## 완주 증거

새 프로젝트 `디자인 통합 완주 QA 20261025 1100`만 변경. 기존 사용자 프로젝트 수정0. 음원은 직접 만든3초440Hz sine, 후보는 로컬 단색128×128 PNG다. 모델 선택은 anthropic-haiku-5-5/fal-kling-2-6-pro 기본값 저장뿐이며 연결 성공이 아니다. 이미지 모델 없음·영상 수신 차단 이유를 확인했다.

|실행한 과업|관측 결과|
|---|---|
|새 작품 생성·불확실 응답 복구|Ego 화면 읽기 실패 후 재제출하지 않고 state조회→작품1개 확인→UI기존요청조회로 committed복구. 중복0|
|모델설정·닫기|전체release문단과aria-describedby,320overflow0. Escape호출버튼복귀. nativeArrowDown이 선택값을 바꾸지 않아 selectOption 사용|
|긴한국어·계획|743자goal·장면 입력. 음악 미확정v1저장→구간확정 후 명시적v2저장. 기존불확실계획 재제출0|
|음악오류·복구|3초음원에끝5초→범위오류·notice focus·입력5보존.0.5–2.5초로정정확정|
|승인·모의작업|v2승인으로장면1개. 준비→보류(실행버튼없음)→$0승인→실행.연속Enter후job1/take1|
|검토·선택분리|후보검토승인후selected=null.명시적Take1선택후만선택변경|
|부분편집·자막|길이2→1.5초,음원offset0.75,자막0–1초“부분 편집 · 한글 자막 검증”.단계3→4왕복해미저장값보존|
|미저장승인차단|“편집을 먼저 저장하세요.”;편집값유지.저장v1→승인|
|렌더확인·닫기|v1/1.5초/1920×1080/음원0.75–2.25/자막1줄확인.닫아도편집유지.단,focus가render아닌notice로돌아감|
|렌더·연속Enter|렌더job1개완료.플레이어duration1.5,width1920,height1080,readyState4,errornull.Space재생후currentTime1.5/endedtrue|
|토큰오류|QA탭메모리토큰을고정무효값으로바꾸는모의검사.새검토의견전송거절·입력즉시보존·pendingfalse.실시간만료기다림시험은아님|
|실제새로고침·재개|CDPPage.reload후정상연결,plan743자복구,선택Take/승인v1/자막/완료출력/납품검토유지.미저장검토의견은유실(F06)|

`qa-output.mp4`, `qa-output.srt`, `qa-output.json` 저장. MP4 SHA256 `daf47a88a9bab44eaed096a04142292e775c13a2141875b122182c1b36471cd1`. renderjob `d62e299babef4dd3bb2fb1b5b0d1517b`,모의job `0571ee6f9bc6470aa3deeabd5c5a56e6`. `completed-state.json`, `mock-result.json`, `unsaved-edit-guard.json`, `music-error.json`, `invalid-token.json`, `actual-reload-after-token.json` 근거.

## 재현된 결함·최소 패치

**F05 / Medium / 조건부 승인버튼 활성화 덮어쓰기**
음악미확정계획을저장하면drawGuided는disabled를설정하지만sendRequest.finally가모든버튼을false로바꾼다.실제DOM disabled=false와차단title을동시에확인.명시적새로고침후같은v1 disabled=true.서버우회/잘못된샷추가로확대해주장하지않는다(해당승인클릭안함).
`F05-plan-disabled.patch`:미확정계획에data-plan-blocked표식,request완료/캐시실패의busy해제시보존.**현고정본apply check+JSsyntax만통과;미적용·회귀미실행.** 기능팀은공통busy와businessdisabled상태관리로확장검토할것.

**F06 / Medium / 토큰복구 안내가 미저장 검토의견 유실을 유도**
comment초안입력→무효토큰으로제출→“접근 토큰이 만료되었습니다. 새로고침하세요.”→실제Page.reload→comment빈값.직후에는보존됐고743자brief는새로고침후에도보존됨.자연만료가아닌인증실패모의검사라는경계유지.
`F06-comment-draft.patch`:workspace/project별sessionStorage초안복구,성공한저장후만clear.**apply check+JSsyntax만통과;미적용.** 저장소오류/프로젝트전환/정상저장회귀필요.

**F07 / Low / 렌더확인창 Escape복귀**
렌더견적저장의finally가notice로focus를옮긴뒤dialog를열므로닫으면notice로돌아온다.수정안은renderConfirm close/cancel시명시적으로#render.focus(),그외dialog와분리.확인창중복accessible name도정리대상.이번턴에서기능소스직접수정없음.

## 시각·구조 평가

현재semantic토큰/전체모델명/selected와primary구분은일관성이좋아졌다.그러나chrome와반복문장이차지하는공간,세로inspector,미디어와편집의분리가핵심장애다.단색fixture자체는감점하지않았다.실제작업물을풍부하게넣었을때의시각품질은이번증거로판정하지않는다.

|실제새QA viewport|workspace top|preview top/bottom|모의준비CTA top|문서가로넘침|
|---|---|---|---|---|
|1280×900|317|403/808|1112|0|
|390×900|570|867/1073|1394|0|
|320×900|621|918/1085|1428|0|

`final-geometry.json`. 모바일에서는빈보드때보다실제1샷보드가추가되어미디어가더밀린다.빈fixture의y695/746개선수치를실제1샷화면의품질로일반화하지않는다.타임라인은step3에서숨겨져미디어/transport/타임라인이동시에보이지않는다.다음구조패치는shell통합·단일대표CTA·장면rail·미디어/transport/timeline동시노출·분리inspector·모바일taskfocus를목표로한다.정확geometry는실제NeuralFramesworkspace참조후동일viewport로검증할것.

부모가사용자에게공개한**45/100 휴리스틱 기준은이freeze에서상향하지않는다**:정보구조11/20,타입·간격10/20,미디어·효율7/20,일관성·상태12/20,브랜드·시각5/20.원래평가의주관적전문가관측이며정량사용자실험/동일조건경쟁사점수가아니다.이번QA는점수부풀리기보다317px상단과1112pxCTA같은실측으로마찰을확인했다.

## 범위·미검증

키보드Enter/Space/Tab/Escape와focus표시·복귀를실제사용했으나focus(selector),native selectOption,file input설정도사용했다.따라서**키보드만으로Tab순서를따라완주했다는claim은불가**.스크린리더미실행.정상Meta+Equal4회에도888px/dpr2/scale1불변(`zoom-attempt.json`),실제200/400%확대미검증.단순viewport320/390를확대로대체하지않음.
요청복구/범위오류/무효토큰/승인·보류·결과·완료·모델불가를확인했으나모든loading/running/failure/unknown전이캡처는미완료.외부provider실패·일반chatlive·assetrights는완료로평가하지않음.짧은합성영상메타데이터/끝까지재생과실제콘텐츠청취·의미품질은별개.

## 캡처 목록

01-model-320,02-plan-unconfirmed,03-music-error,04-candidate-review,05-render-confirm,06-output-preview,07-token-error,08-final-scenes-1280/390/320,09-settled-scenes-1280 PNG를저장후이미지로열어검사.02는승인버튼이아래에있어F05는DOMjson이주증거.08desktop은viewport변경직후미디어페인트가검게잡혀**최종미디어시각근거에서제외**,이미지complete/natural128확인후09정착캡처로대체.모바일08은첫화면정보밀도/위치근거이며미디어전체품질근거아님.
사용자에게전달한show-*3개는기존`실행 승인 QA 20261025`화면이라이번새QA의동일데이터전후쌍이아니다.원본system/final-baseline-*과candidate-*는동일빈fixture전후쌍으로보존.현재09와비교시데이터차이를명시한다.

현재전체로컬flow checkpoint는완료.다음작업은실제NeuralFramesworkspace의정상접근확인·같은viewport비교·구조DOM/CSS후보이며,현소스freeze는유지했다.
