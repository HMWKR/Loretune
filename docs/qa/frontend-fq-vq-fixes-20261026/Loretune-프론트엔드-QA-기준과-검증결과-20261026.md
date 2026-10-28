# Loretune 프론트엔드 QA 기준과 검증 결과

작성일: 2026-10-26. **로컬 전달용 통합본. Library 업로드는 승인 대기이며 수행하지 않았다.** 이 문서는 이미 존재하는 감사·수정·검증 근거를 통합한다. 새 브라우저 시험, 코드·DB·모델 설정 변경은 하지 않았다.

## 1. 결론과 읽는 방법

확인된 근본 원인5건(FQ01–03, VF01–02)을 수정했고, 해당 원 반례·인접 회귀 및 승인된 실제 브라우저 표본이 통과했다. 전체 자동시험은 **349개 = 비HTTP329 + HTTP20의 분할 실행**이다. 하나의 연속349회 실행이나 기능 완성도349/349를 뜻하지 않는다. 새 품질 점수는 산출하지 않는다.

원 기능 감사24건은11 PASS /4 FAIL /6 BLOCKED /3 NOT RUN, 원 시각 감사22건은15 PASS /2 FAIL /2 BLOCKED /3 NOT RUN이었다. 이 분모와 원 결과를 보존하고 후속 증거를 각 행에 붙인다. 서로 다른 층·버전의 결과를 합쳐 “46건 전체 통과”로 바꾸지 않는다. PASS는 명시한 표본과 방법에 한정, BLOCKED는 실행 조건 미확보, NOT RUN은 해당 검사를 수행하지 않았다는 뜻이다.

1920×1080 CSS viewport가 주 기준,1280×900은 보조다. 모바일 심층 개선은 보류했다. 모니터 해상도와 CSS viewport, 앱 글자배율과 브라우저zoom은 다르다. 실제 고객 시험은 하지 않았다.

## 2. 기능 QA의12개 영역과 근거

다음은24case를 사용자 과업 관점으로 묶은 통합 목차다. 원 case ID는 보존하며 신규 요구사항으로 확장하지 않는다. 공식 API 동작/표준과 Loretune의 수용 기준을 구별한다.

|영역|사용자 목표·case|공식/1차 근거와 적용|
|---|---|---|
|1 격리·환경|실자료/과금 없이 재현 ENV01|[Playwright 격리 원칙](https://playwright.dev/docs/best-practices): 방법 참고, 실제 도구는 Ego/VM|
|2 입력·조합·중복|정확한 요청/한글 초안 FUN01–02|[HTML forms](https://html.spec.whatwg.org/multipage/forms.html), [actionability](https://playwright.dev/docs/actionability); 중복1회는 제품 기준|
|3 모델 선택|세 슬롯 보존 FUN03|[PAIR mental models](https://pair.withgoogle.com/guidebook-v2/chapter/mental-models/): 역할 설명. 미선택 자동대체 금지는 제품 계약|
|4 문맥·버전·결정권|선택≠승인, 과거출력 보존 STA01–02|[PAIR control](https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/), [PROV-O](https://www.w3.org/TR/prov-o/): 계보 참고, 전면 표준 준수 주장 아님|
|5 비동기·불확실성|최신 상태/기존요청 유지 ASY01–03|[HAX](https://www.microsoft.com/en-us/haxtoolkit/playbook/): 실패 설계 참고; epoch/revision 정책은 앱 구현|
|6 미디어 수명|재생·대기·실패·종료 MED01–03|[HTML media](https://html.spec.whatwg.org/multipage/media.html#ended-playback): native 종료/paused 관계|
|7 시간·자막|음악/trim/자막 일치 TIM01–02|[WebVTT](https://www.w3.org/TR/webvtt1/), [rVFC](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback): decoded-frame 근거 필요|
|8 저장·복구|초안/unknown 중복방지 STO01–03|[Web Storage](https://html.spec.whatwg.org/multipage/webstorage.html): 접근 거부 가능. fail-closed는 제품 정책|
|9 자원·성능|오래 사용해도 안정 PER01–03|[Core Web Vitals](https://web.dev/articles/vitals), [long tasks](https://web.dev/articles/optimize-long-tasks): field와 lab 구별|
|10 키보드·접근성|포커스·이름·대안 DES01|[WCAG keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html), [Testing Library](https://testing-library.com/docs/guiding-principles/)|
|11 확대·시각 일관성|읽기·reflow·동일화면 DES02/VIS01|[resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html), [snapshot 조건](https://playwright.dev/docs/test-snapshots)|
|12 엔진 호환|지원환경에서 재현 XBR01|[Playwright browsers](https://playwright.dev/docs/browsers): 설치는 실행coverage가 아니며 WebKit≠실제Safari|

### 기준과 제안값의 경계

WCAG AA의 보통 텍스트4.5:1/큰글자3:1, 필수 비문자3:1은 해당 조건·예외를 적용한다. focus-not-obscured AA는 **완전히 가려지지 않음**이고 이번 제품 기준인 **전체 target 가시**와 다르다. focus appearance AAA를 AA 실패로 부르지 않는다. [대비](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [비문자](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), [focus](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).

기본 no-page-scroll, 핵심 desktop36px/touch44px, static seek±1 decoded frame, 탐색 AV drift≤100ms, cached-shot p95≤200ms는 제품 제안/목표다. 모든 scroll 금지가 아니며 긴 패널 내부scroll과 확대 reflow는 허용한다. 고정 px/HEX는 보편적 표준값이 아니다. LCP≤2.5s/INP≤200ms/CLS≤0.1은 field75percentile 지표이며 VM 함수시간으로 대체할 수 없다. long-task50ms 정의와 조사목표200ms도 구별한다.

## 3. 기능24case — 원 결과와 후속 확인

|ID·과업|기대|원 결과|관측·후속 및 한계|
|---|---|---|---|
|ENV01 격리·소스 식별|고정 소스와 합성 요청만 사용, 실제 전달 없음|PASS|고정 해시 일치, 허용1/차단2/실전달0|
|FUN01 입력·IME|native 빈값 검사와 한글 조합 중 잘못된 제출 방지|BLOCKED|격리 브라우저 경로 부족으로 공유 앱 제출하지 않음|
|FUN02 긴 입력·중복|10,000자 보존, 빈값0회·유효 입력1회, 새 초안 유지|PASS|VM에서 정확한 payload1회 및 새 초안 보존|
|FUN03 독립 모델 선택|채팅/이미지/영상 선택 독립, 미선택을 자동 대체하지 않음|PASS|3개 값과 null 보존, 실제 provider dispatch0|
|STA01 문맥·초안·권한|작품/샷/Take별 초안 분리, 비교가 선택·승인을 바꾸지 않음|PASS|F05–07/검토 store/비교 controls 통과; 서버 권한 전체 재검증 아님|
|STA02 출력 버전|과거 출력과 현재 편집/승인을 구분|PASS|타임라인2와 출력1 구별, 이전 결과·테스트 표시 보존|
|ASY01 응답 순서|늦은 응답이 최신 revision을 되돌리지 않음|FAIL|원본3→2 퇴행. FQ01 수정 후 원 반례 및 브라우저164→163 역순에서164 유지|
|ASY02 응답 문맥|대기 중 작품/샷/dirty/busy 변경을 뒤늦게 덮지 않음|FAIL|원본 busy/dirty/작품변경 뒤에도2 적용. 수정 후 독립 VM guards 통과|
|ASY03 미확정 저장·취소|unknown을 실패/취소완료로 단정하지 않고 기존 요청 조회|PASS|동일 request GET, 추가 POST 차단, canonical 불변|
|MED01 기존 미디어 수명|늦은 이벤트·Promise·metadata가 새 문맥을 변경하지 않음|PASS|DM01–03 controls 통과; VM과 디코더 구별|
|MED02 재생 오류·종료|거절·stall 처리, 자연 종료 시 다음 컷 또는 정지|FAIL|원본2.95초/재생표시 지속. 수정 후 VM 및 실제 무음2컷10초 정지 확인|
|MED03 실제 미디어 오류|실제 decode/error를 API 성공과 구별|BLOCKED|원 시험 BLOCKED. 후속 자연 종료만 확인; corrupt/stall 전체는 미검증|
|TIM01 시간좌표|누적 길이/trim/반개방 자막 구간 보존|PASS|30×0.131초=3.93초와 trim0.5초 좌표 VM 확인|
|TIM02 프레임·AV 정밀도|제안: seek±1decoded frame, 탐색 AV drift100ms 이하|BLOCKED|decoded frame/AV clock 미계측; 시간표시만으로 통과 아님|
|STO01 초안 저장 형태|문맥별 복원, malformed/old shape 거부, 메모리 fallback|PASS|store 재생성 모사와 write-denied 보존 통과; 실제 reload와 구별|
|STO02 저장소 거부|SecurityError를 안내하며 새 제출을 안전 차단|FAIL|원본 초기화/act 예외. 수정 후 독립 VM+브라우저 대역에서 예외0/POST0/초안유지|
|STO03 복구정보 저장|cache 실패/abort 시 POST0, busy해제, 중복 최대1회|PASS|실제 requestCache 함수의 synthetic 실패 controls 통과|
|PER01 반복 수명|활성 controller/RAF 제한과 dispose 보장|PASS|60샷·180Take·120자막 VM,60교체에서 활성최대1/정지RAF0; heap 판정 아님|
|PER02 성능 지표|실제 lab trace와 field p75 분리|BLOCKED|지원되는 격리 trace 부족; LCP/INP/CLS 통과 아님|
|PER03 상호작용 성능|제안 cached-shot p95≤200ms, network/decode 분리|BLOCKED|유효한 input-to-paint 표본 없음; 전환 시간값 제외|
|DES01 키보드·접근성|role/name/disabled/focus가 실제 작업과 일치|NOT RUN|기능 감사 미실행; 별도 시각 AX01–03 및 후속VF01 증거로 제한 연결|
|DES02 확대·reflow|앱배율/DPR와 실제 브라우저zoom 분리|NOT RUN|기능 감사 미실행; 별도 앱배율 검사 있음, 실제zoom 미검증|
|XBR01 브라우저 호환|실행한 엔진만 통과, WebKit과 Safari 구별|BLOCKED|설치/캐시만 확인; 다중엔진 실행 없음|
|VIS01 시각·geometry|동일 조건 화면과 근거로 비교, 미감 점수 생성 금지|NOT RUN|기능 감사 미실행; 별도22-case 시각 감사 참조|

## 4. 기능과 분리한10개 시각 그룹

|그룹|관측과 판단|방법론 근거|
|---|---|---|
|1 geometry·확대|기본 문서높이 viewport 유지. 확대Take3 실패는 후속수정; 전체zoom은 미검증|[W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)|
|2 공간·밀도|당시1920 stage1376×405.91, 정밀1376×285.98, rail184/inspector288.1280 세부판독 부담은 가설|[Blender HIG](https://developer.blender.org/docs/features/interface/human_interface_guidelines/paradigms/)|
|3 그룹·간격·정렬|패널16px,Take8px,비교열 정렬, 긴내용 내부scroll. 새 px법칙 아님|[Spectrum spacing](https://spectrum.adobe.com/foundations/layout-and-structure/spacing/component-spacing)|
|4 타입·CJK|제목20/600/28,본문14/400/23.8,metadata12/400/17.4. CJK Apple SD Gothic Neo, Latin SF NS, timecode Menlo 표본. 긴연속제목 수정|[Spectrum typography](https://spectrum.adobe.com/foundations/typography/typography-system), [text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html)|
|5 semantic색·대비|중성 역할쌍과20개 대비표본 확인. 전체상태인증 아님|[Spectrum tokens](https://spectrum.adobe.com/foundations/design-data/design-tokens)|
|6 focus·선택·재생위치|선택면/표식/문구, 승인체크/텍스트, dashed focus, playhead를 구분. VF01수정|[W3C focus](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html)|
|7 아이콘·control|아이콘+텍스트,36–40px control/6px radius/8px panel 표본. native OS별 광학차이 미검증|[Spectrum icons](https://spectrum.adobe.com/foundations/icons-and-illustrations/using-icons)|
|8 미디어·시간축|16:9/9:16 contain,비교동등stage,1/2/4초 비례. 작품 미감·decoded-sync와 별도|[Descript timeline](https://help.descript.com/timeline/timeline-overview)|
|9 surface·overlay·CSS|dialog viewport내/Escape복귀,backdrop과경계 구별. 모든popover 미검증|[WAI dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)|
|10 증거 신뢰성|동일 paused-ready PNG 동일. 원본보존, 잘못된fixture/시간측정 제외. 반복가능성≠미감|[snapshot](https://playwright.dev/docs/test-snapshots)|

당시 측정 색: canvas **#101010**, panel **#1B1B1B**, raised **#242424**, selected **#2A2A28**, 주문자 **#F4F4F2**, 본문 **#DEDEDB**, 보조 **#BDBDBB**, 오류 **#FFB49D**, focus **#E4DDBE**. 제목/canvas17.28:1,본문/panel12.78:1,보조/canvas10.11:1,오류/#28201E9.32:1,필수경계#858585/raised4.21:1,focus/panel12.62:1,playhead#D8D8D2/raised10.85:1. 장식divider#383838과 비활성control 예외를 실패로 계산하지 않는다. 색만으로 승인·실패를 전달하지 않는다.

경쟁사 참조는 Descript의 시간정렬, Frame.io의 자산/플레이어 인접성, Runway의 조용한 prompt 작업환경에 한정했다. 경쟁사 내부 토큰·라이브 성공률·동일조건 품질비교가 아니며 Runway는 연결 제공자가 아니다.

## 5. 시각22case — 원 결과와 후속 확인

|ID·과업|기대|원 결과|관측·후속 및 한계|
|---|---|---|---|
|ENV01 렌더링 환경/fixture 고정|현재소스일치,로드/폰트완료조건기록;누락값을추정하지않음|PASS|당시 source/served 일치, 실제 글꼴·뷰포트 기록. 정확한 engine build 미확인.|
|L01 기본 승인 작업대 두 viewport|문서세로scroll없음,preview/Take/timeline/review주요진입점함께가시,clipping없는경계|PASS|1920/1280 기본 화면 문서높이1080/900, 주요 진입점 함께 표시.|
|L02 sequence+정밀 편집 두 viewport|문서높이viewport,내부scroll허용,조작접근,media contain;최소면적숫자임의설정안함|PASS|sequence2.172/7초·자막·정밀편집 펼침, 문서높이 유지·내부scroll. 프레임정밀도 아님.|
|L03 긴 목록/한글 메모|document넘침없음,끝focus접근;실제60장면성능으로주장안함|FAIL|원본 긴 제목108px/scroll417px. 후속VF02에서108/108px·전체 문자열 줄바꿈. 긴60카드는 표시 fixture.|
|S01 계획 empty|빈상태대상/다음입력명확,불필요한내부상세기본노출없음|PASS|계획 빈 상태의 목적/제약/장면 입력과 외부전송 없는 미리보기 설명 확인. 제출 없음.|
|S02 미검토/반려 review 상태|현재scene/Take/검토상태/맞는행동;합성DOM은실제경로와별도|NOT RUN|저장된 선택은 승인본뿐. 미검토/반려 inspector 전환을 위해 canonical 변경하지 않아 미실행.|
|S03 dirty/cancel 두 viewport|저장/취소구별,입력가시,취소후focus복귀,canonical불변|PASS|두 뷰포트 긴 초안과 저장/취소, 취소 후 focus복귀. 저장은 실행하지 않음.|
|S04 error/unknown 시각표현|오류인접,원인중립,disabled저장과조회구분,긴문구줄바꿈;복구기능시험아님|PASS|원인중립 unknown 안내·disabled저장·조회버튼 표시 fixture만 확인. 실제 실패/조회 아님.|
|S05 실제 loading/poster-unavailable|loading을성공/실패와구별,안정화전캡처를일반완료화면으로채택하지않음|NOT RUN|안전한 queued/running/partial/failed/loading/poster오류 전체 표본 없음.|
|M01 모델 미선택/미검증/차단/긴이름|선택/불가이유/승인별도구별,모델명전체접근,가로넘침없음|PASS|미저장 선택에서 미선택/미검증/차단과 긴 이름 확인, 저장 없이 복원. 활성화 아님.|
|D01 비교 dialog/contain|동등boundedstage/원본비율,닫기focus복귀,상태는색만의존안함|PASS|두 stage471×300,16:9/9:16 contain, Escape복귀.1:1/투명은 미검증.|
|AX01 이름/역할/상태 트리|현재선택/disabled/expanded/name노출기록;스크린리더발화통과대체아님|PASS|initial14/dirty33/dialog6 AX control 표본에서 빈 이름 없음. 스크린리더 발화 아님.|
|AX02 초기 keyboard-only|AA:focus완전히가려지지않음;제품:전체control가시.명시focus로전체여정대체금지|PASS|초기BODY에서52관측/8과업target 키보드 도달, Escape/취소복귀. 저장·승인 제외.|
|AX03 정밀 폼 keyboard 두 viewport|AA최소와제품전체가시를따로기록|PASS|정밀폼35Tab target씩.1280 가시,1920 profile 즉시표본은 재검토 후 전체가시 확인.|
|AX04 실제 색상쌍|보통문자4.5:1,large3:1,필수비문자3:1;장식/비활성예외구분,반투명배경임의대체금지|PASS|실제 문자/비문자20쌍 적용대비 통과. 장식/비활성 예외 구별. 전체WCAG 아님.|
|AX05 forced-colors|shadow없이도필수단서/텍스트보존;실제Windows사용자환경통과아님|NOT RUN|일부 forced-colors 활성/텍스트/경계 확인, 오류+focus 미실행으로 전체case NOT RUN.|
|AX06 reduced-motion|불필요장식motion제거;영상재생을임의비활성화하지않음|PASS|reduce에서20control의transition/animation0s·scroll auto. 의도된 미디어 연속성 별도.|
|AX07 앱100/150/200% 두 viewport|글자확대와reflow,가로넘침/핵심clipping없음;브라우저zoom으로부르지않음|FAIL|원본1280 앱200 Take3 약43.1%가시. 후속동일조건 앞/중간/끝·역방향100%가시. 전체확대matrix 재실행 아님.|
|AX08 실제 browser200/400%|지원불가/변화미확인시BLOCKED;DPR/CSStransform/resize로대체금지|BLOCKED|shortcut 후 실제 배율변화 확인 안 됨. viewport/DPR/앱배율로 대체하지 않음.|
|AX09 비드래그 pointer 대안|해당drag과업에single-pointer대안,keyboard만으로통과하지않음;미디어decode정확도별도|PASS|장면02 single-click으로sequence1초 이동, 비드래그 입력 접근. reorder/저장 미실행.|
|AX10 기존 axe 실행|위반/incomplete/pass모두보존;자동검사=전체인증아님|BLOCKED|사용 가능한 axe bundle 없음. 설치/외부script 주입하지 않아 스캔 미실행.|
|VR01 같은환경 screenshot 재현성|차이는변화근거;미감점수아님;오류/중요영역mask나baseline교체금지|PASS|동일 paused-ready 두PNG byte동일. 전체동적상태/미감 통과 아님.|

## 6. 다섯 원인과 수정 전후

|원인·심각도|수정 전 증거|최소 수정|수정 후 근거|
|---|---|---|---|
|FQ01 P2: await 이후 순번/문맥/revision 미검사|ASY01/02 최신3→이전2, busy/dirty/작품변경 뒤에도 덮음|epoch/마지막적용순번/workspace/작품/샷/revision/busy/dirty 확인, poll동시최대2. 같은revision 합법적작업갱신 유지|독립원반례·guards. 실제브라우저 제어응답164→163에서164유지, 같은164 변경 허용|
|FQ02 P2: native EOF의 paused를 단순정지clock으로 해석|무음3초컷2.95초에 재생표시·RAF남음|현재controller/video/serial의 ended 처리, 원곡clock우선, 기존50ms허용경계 보존|독립VM 마지막/중간/trim/늦은event 통과. 실제5초영상2컷의 trusted ended 후10초에서 정지|
|FQ03 P2: storage read 예외 무방어|시작/act SecurityError 전파|guarded pending read/clear, 사용불가≠pending없음, 새POST차단. 알려진ID조회·unknown보존|독립VM 및 실제브라우저 SecurityError대역:예외0,POST0,초안보존|
|VF01 P2: 가로Take목록이 focus target전체를 노출하지 않음|1280/app200 Take3 약43.1%가시,scrollLeft0|focusin 시 target경계 기반 strip만 이동,4px여유. 선택/승인없음|같은조건 first/middle/last/reverse 모두100%가시. Take3 scrollLeft97.5px|
|VF02 P3: keep-all의 긴연속문자 emergency wrap 누락|실108px title,scroll417px,끝문자잘림|해당제목에 overflow-wrap:anywhere, 전체문자·글자크기 보존|1920 같은문자 client/scroll108px,높이117px,font13px,전체텍스트유지|

후속5원인 확인은 각 원case의 제한된 재검증이다. 시각 L03/AX07의 모든 스트레스 조합을 다시 실행했다는 뜻은 아니다. 앱200% 실측을 실제browser200/400%로 바꾸지 않는다. DM01–03/F07은 기존결함의 회귀controls로 유지하고 새결함으로 중복계상하지 않았다.

## 7. 독립 재검증과 자동시험의 분모

- 독립 FQ 원 실패 **4→4 PASS**, 독립 인접guard15 PASS, 집중 unittest14 PASS. wrapper 안의 F07/DM/Take/비교/저장 시나리오는14와 중복 합산하지 않는다.
- 구현측 원 suite13개 **전9PASS/4FAIL→후13PASS**. 새 async18시나리오는 전체suite의 unittest wrapper1개다.
- 최종 동일소스 **비HTTP329 PASS + HTTP20 PASS =349개**, 분할실행. HTTP20은약10.99초,오류/실패0. 정적검사 inlineJS6+mediaJS1=7 PASS는 별도 지표다.
- 최초347개 실행의21오류는20bind거부와1기존VM대역 helper누락이었다. 대역수정·시각2시험추가 뒤329통과, 승인후20HTTP통과. 최초실패로그는 보존했다.
- 테스트개수는 요구사항96FR/143API,전체MVP,12live조합,출시가능성의 완료율이 아니다.

## 8. 실제 실행 환경·데이터·종료

원 시각 감사는 과거 HTML0bfdbbb…의 실제 served페이지를 TaskSpace34에서 관측했다. 후속은 아래 최종소스의 **about:blank 격리 replay(TaskSpace36)**다. CSS/JS inline,asset→data URI,synthetic GET대역,메모리Storage를 사용했다. 이는 현재 서버의 served hash나 live provider 경로 검증이 아니다.

Ego CLI 실제실행버전0.6.0.20,설치앱 plist0.6.1.11/build6.1.11,UA Chrome/154.0.0.0 MacIntel. 이 서로다른값을 정확한 동일engine build로 합치지 않는다. 실제브라우저 CSS viewport를 매검사 innerWidth/innerHeight로 확인했다. 업데이트는 하지 않았다.

승인자료: 합성작품 `디자인 시스템 기능 QA 20261026` 1개,3장면/9Take/자막/합성검토와4고유미디어. 5초320×180 H264패턴영상,5초180×320 H264패턴영상,320×180단색PNG,8초440Hz시험음48000mono PCM. 사람/고객자료/실키 없음. 파일경로·해시는 포함됐다. 후속무음시험은 draft만두5초컷으로만들고복원,공유DB쓰기0.

페이지CSP connect-src none/form-action none,외부API0,최종fetch대역166기록은 실제HTTP166건이 아니다. nonGET0/resource network entries0/브라우저오류0. Ego 제어경로의 외부중계·보관여부는 미확인이고 이 한계를 공개한 뒤 허용받았다. 페이지격리를 Ego인프라전체의 로컬전용보장으로 확대하지 않는다.

HTTP시험은 실제127.0.0.1의임시리스너21개·연결88건,외부연결0. 모두socket폐쇄·실행exit0. TaskSpace36정상종료. 추가ps조회는 operation not permitted로 거부되어 재시도하지 않았고 process-list성공을 주장하지 않는다. 기존서버/사용자DB/권한변경0. 첫브라우저대기는 숨겨진Take버튼을 기다려timeout이었으나 로드는성공한상태였으므로 같은공간에서단계이동해검사했다.

원거절(합성fixture목적지승인부족·localhost bind)은 사용자2026-10-26 04:56UTC의 두범위명시승인 후 각각한번정식재요청해허용됐다. 이번 Library 업로드는 별도승인대기이며 이 문서작성은 업로드가 아니다.

## 9. 성능 해석에서 제외한 것

30회 warm 장면전환의 시간계측은 click capture의microtask가앱bubblinghandler보다먼저실행해잘못된대상을관측했으므로 **시간값·p95를 전부 제외**한다. 유효한 좁은관찰은 시작/15/30/종료 시 DOM1169/video3/audio1/playing0이 같았다는 점뿐이다. 이것은 누수없음·지연없음·input-to-paint·field성능 통과를 입증하지 않는다. VM의호스트함수시간도브라우저성능으로쓰지않는다.

## 10. 최종 해시·증거·남은 범위

|현재파일|SHA256|
|---|---|
|index.html|07535dfd93c359de25a6bccdd2713635733ea51063beb6ecebb124867667eed3|
|studio.css|a696a80585fff736b2da47ddd08ba8859c5ab94eb8631769b06a9dc8ba335ce0|
|studio-media.js|ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9|
|app.py 불변|7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d|
|현재fixture|6f7837799306643fc6484fed078120da2bf867e25b4138755cd2c38c3f600f46|

공유합성프로젝트 정렬JSON SHA `4f29f894cf49cdf48c82bbff27c13f4c447efa50098b827a6881c6955ad59792` 전후동일. 과거시각감사 fingerprint는 다른serialization값이므로 둘을직접비교해변경여부를추정하지않는다.각감사의동일절차전후불변증거를사용한다.

남은 BLOCKED/NOT RUN: 실제 Firefox/WebKit/Safari/다른OS,실제browser200/400zoom,axe scan,스크린리더발화,사용자text-spacing전체,forced-colors오류+focus전체,유효한성능trace/field p75/전환p95/heap누수,decoded-frame seek와AV drift,모든corrupt/stall/poster/queued/partial상태,실고객사용성,실provider/과금/다중사용자운영. 현재served최종hash는후속replay로검증하지않았다. 미검증은자동실패도자동통과도아니다. 새로운품질점수·WCAG인증·경쟁사동등·전체제품완료를선언하지않는다.

### 로컬 근거

- [기능24case 원감사](../frontend-functional-independent-20261026/REPORT-ko.md), [원결과](../frontend-functional-independent-20261026/results.json)
- [시각22case/10그룹 원감사](../design-system-redesign-20261026/frontend-qa-inventory-20261026/REPORT-ko.md), [원결과](../design-system-redesign-20261026/frontend-qa-inventory-20261026/RESULTS.json)
- [독립 FQ재검증](../independent-frontend-fq-recheck-20261026/REPORT-ko.md)
- [최종 승인후 실제브라우저/HTTP](authorized-verification/REPORT-ko.md), [manifest](authorized-verification/verification-manifest.json), [자료보존](authorized-verification/final-preservation.json)
- [Take3 최종화면](authorized-verification/vf01-take3-1280-app200.png), [긴제목 최종화면](authorized-verification/vf02-long-title-1920.png). 둘다현재해시의격리replay이며실픽셀열람완료. 실제served페이지캡처로재명명하지않는다.

변경기록: 기존보고서·원본명세·코드·데이터는보존하고 본로컬통합문서만추가했다. 외부업로드/새시험/새품질점수 없음.
