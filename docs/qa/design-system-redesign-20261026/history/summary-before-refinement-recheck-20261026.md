# Loretune 디자인 업데이트 요약

작성일:2026-10-26 · 범위:1920×1080 중심 디자인·사용 흐름·방법론 문서 정합

**고정 shell의 독립1920 화면 감사를 완료했습니다.** 확인 가능한 배점 **98/100 중 74.3점**입니다. 정확한 합은74.25점이며 마지막에 소수1자리로 반올림했습니다. F3(실제 실패·복구)2점은 미검증이므로 전체 확정 점수는 보류합니다. 이를100점으로 재환산하지 않습니다. 새 사용 차단 결함은 이번 직접 표본에서 재현되지 않았지만3개 gate는 전체조건 미검증입니다. 아래2절의pre-shell은역사적baseline이며,이번최종검증은문서뒤의상세보고서에분리했습니다. 경쟁사동등성·90점·전체준수를주장하지않습니다.

## 1. 현재 무엇을 개선하려는가

주 작업 환경은1920×1080 **브라우저 내용 영역(CSS px)**입니다. 모니터 물리 해상도와 구분합니다.1280×900은 보조 회귀이며 모바일의 기존 동작은 보존하되 추가 작업은 보류합니다.

표준 글자배율에서 장면 목록, 미리보기와 재생 조작, 시간축, 검토/편집 주요 조작을 한 작업 공간에 유지합니다. 페이지 전체를 내려야 다른 작업 구역에 접근하는 상황을 줄이고, 긴 목록과 상세 설정만 해당 패널에서 스크롤하거나 펼칩니다. 내용을 잘라 숨기거나 글자를 줄여 맞추지 않습니다. 확대·작은 창에서는 접근성을 위해 적절한 reflow와 스크롤을 허용합니다.

승인 완료 화면은 차분한 결과·이유와 ‘검토 수정’이면 정상입니다. 밝은 CTA를 억지로 늘리지 않습니다. 선택·편집 채택·Take 검토·계획/실행 승인·출력 승인은 서로 다른 의미로 유지합니다.

## 2. 수정 전1920 화면에서 확인한 것

대상은 합성 작품 ‘디자인 시스템 기능 QA 20261026’, 장면01/Take1, 앱 문자배율100%, DPR1입니다. 기능팀이2026-10-26T01:21:37Z에 저장한 실제 이미지를 디자인 담당이 직접 열어 확인했습니다. 독립 라이브 재캡처나 새 shell 검증이라고 부르지 않습니다.

| 항목 | pre-shell 값 | 해석 |
|---|---:|---|
| 상단 프로젝트/설정 + 단계 |56+48=104px| 반복 안내가 크게 줄고 구역은 명료함 |
| 장면 rail / inspector |184 /288px| 기본 목록과 검토 내용이 읽힘. 폭만으로 품질을 판정하지 않음 |
| 미리보기 칸 |1376×300px| 중앙의 넓은 공간에 비해 높이 상한이 작음 |
| 실제16:9 영상 |약533×300px| 칸 면적의38.76%, 전체 viewport의7.72%. 검정 무대의 확대가 실제 영상 확대와 같지 않음 |
| 기본 타임라인 하단 |약944px| 기본 상태의 핵심 조작은 첫 화면 안에 보임 |
| 문서 높이: 기본/sequence |1080px /viewport1080px| 기본 상태에서는 페이지 세로 스크롤 없음 |
| 문서 높이: 정밀 편집 펼침 |1710px /viewport1080px| 새 사용자 요구에 맞춰 상세를 패널 안으로 배치할 필요 |

영상은 테스트 패턴이며 실모델 생성물이 아닙니다. 테스트 영상의 아름다움·화질은 디자인 점수에 넣지 않습니다. portrait 미디어의 정상 여백과 가로 영상의 공간 배분 문제도 구분합니다.

새 배분은 미리보기만 키우는 방식으로 끝낼 수 없습니다. sequence 재생 조작은 선택 모드보다 약100px 높아지므로, 미디어·transport·Take행·타임라인의 전체 예산을 함께 조정해야 합니다. 예를 들어350px 미리보기와 기존에 가까운 timeline, 또는400px 미리보기와 더 간결한 timeline은 검토할 가설입니다. 특정 px가 업계 정답이거나 확정 구현은 아닙니다.

## 3. 색상·타이포·간격은 어떤 상태인가

아래 값은 pre-shell 통합 baseline의 computed custom-property와 요소 측정에 근거합니다. 경쟁사 내부 토큰을 추정한 값이 아닙니다.

| 역할 | 값 | 유지·검토 이유 |
|---|---|---|
| canvas / panel / raised / hover |#101010 / #1B1B1B / #242424 / #303030| 미디어를 방해하지 않는 중성 면. 상태와 제어의 역할을 더 명확하게 사용 |
| 강한 글자 / 본문 / 보조 |#F4F4F2 / #DEDEDB / #BDBDBB| supporting text도 읽을 수 있도록 유지 |
| 선택 면 / 선택 경계 |#2A2A28 / #EEEEEE| 선택을 승인·hover와 구분 |
| 장식선 / 필수 제어 경계 |#383838 / #858585| 장식 구분선과 입력 식별 경계는 다른 역할 |
| focus / 오류 / 오류면 / 경고 |#E4DDBE / #FFB49D / #28201E / #E6C58B| 색 외에 텍스트·기호·경계로 의미를 전달 |
| 타입 역할 |12/13/14/16/18/20/24px;400/500/600| 메타·항목·본문·섹션·문맥·제목·display 역할. 큰 화면이라고 일괄 확대하지 않음 |
| 간격 / radius |4/8/12/16/24/32px;4/6/8/12px| 관계와 그룹을 표현하며 예외는 실제 역할로 판단 |
| motion |120ms| 필요한 피드백만. reduced-motion에서는 장식을 줄이고 의도된 영상 재생은 유지 |

불투명 지정 색상쌍의 sRGB 대비는 본문/패널12.777:1, 보조/패널9.154:1, 제어경계/패널4.668:1, 제어경계/hover3.577:1, 오류/오류면9.325:1입니다. 장식선/패널1.469:1은 필수 입력 경계용이 아닙니다. 이 계산이 모든 실제 상태·투명 합성·native 영상 조작을 검증하거나 WCAG 전체 준수를 인증하지는 않습니다.

## 4. 채택한 방법론과 이유

| 적용 | 방법 | Loretune에서 하는 일 | 한계 |
|---|---|---|---|
| 채택 | 과업 분석/가벼운 객체 정합 | 계획→제작→비교/검토→편집→출력/재개의 반복·실패 분기와 장면/Take/버전을 통일 | 실제 사용자의 빈도·순서를 관찰한 것은 아님. DB 용어를 UI에 노출하지 않음 |
| 채택 | 분할 작업 공간·맥락 유지 | 미디어/시간축/검토를 인접하게, 상세는 해당 패널에서 접근 | 모든 경쟁사가 무스크롤이라는 주장은 아님 |
| 채택 | 점진적 공개·인지 단서 | 기본 작업 우선, 진단은 명시적 상세. 현재 대상/버전을 알아볼 단서 유지 | 비용·권리·승인·실패는 숨기지 않음 |
| 채택 | semantic tokens·역할쌍 | 값의 개수보다 의도·재사용·실제 foreground/background를 관리 | 특정 HEX 또는 색비율이 보편 정답은 아님 |
| 채택 | Human–AI 역할·권한·실패 구분 | AI추천, 서버검증, 사람승인, 실행중/미확정/결과를 구분 | 모델 자기평가·근거 없는 성공 확률·자동 재제출 금지 |
| 채택 | 비파괴 비교·원본·기록 | audition과 사용확정/승인을 분리, 기존 초안/버전 보존 | 후보를 자동으로 유료 생성하지 않음 |
| 채택 | 전문가 walkthrough·heuristic·스트레스 표본 | 긴 한국어/다른 aspect/오류/확대/키보드로 가설 검토 | AI 검토를 실제 사람의 사용성 시험으로 부르지 않음 |
| 조건부 | JTBD·실제 task usability·CSI | 제작 목적이 불명확하거나 실제 창작 경험 검증이 필요할 때 사람 연구 | 현재 px 배분·점수의 근거로 쓰지 않음 |
| 조건부 | COFI·OKLCH | 공동창작 결정권의 일부 구분, 필요할 때 새 역할색 조정 | 새 실시간창작 기능이나 전체 palette 재생성 요구가 아님 |
| 제외 | 전자상거래 전환 최적화,60–30–10 강제,보라색AI,모든 CTA강조 | 현재 과업 근거가 없어 채택하지 않음 | 새색이나 강한 행동을 항상 금지한다는 뜻은 아님 |

보다 자세한 출처·구현 위치·검증·불확실성은 함께 전달하는 ‘METHODOLOGY-FIT-MATRIX-ko.md’에 있습니다. HAX의18개 지침을 모두 의무 적용하거나 새 프레임워크/공급자를 도입하지 않습니다.

## 5. 비교 참고의 역할

- Descript captured editor와 공식 문서: 공통 시간눈금·waveform·layer 정렬.
- Frame.io captured review: 실제 asset/version 썸네일과 player/검토의 인접성.
- Neural Frames 공식 Track/Storyboard 이미지: 장면 제작 단계와 미디어·설정의 연결. 현재 계정의 직접 편집 화면이라고 부르지 않습니다.
- Runway captured home: 조용한 prompt shell만. 시간축 증거가 아닙니다. 공식 Studio 문서는 수동/채팅 편집 맥락을 참고합니다. Runway는 API provider가 아닙니다.

서로 다른 원본 해상도·촬영 시점·콘텐츠이므로1920 동일 조건 경쟁 실험이 아닙니다. 경쟁사의 내부 HEX·점수·순위를 만들지 않습니다.

## 6. 사전에 고정한7축·26개 항목

이100점은 아래 기준에 대한 **전문가 디자인 평가**입니다. 객관적인 경쟁사 서열, 제품 완성률, 접근성 인증이 아닙니다. 예전5항목×20점과 가중치·범위가 달라 점수의 상승/하락으로 연결하거나 환산하지 않습니다. 새 ‘페이지 스크롤 없는 핵심 작업’ 요구가 추가됐다는 변경 이력도 남겼습니다.

각 세부항목은0/1/2/3/4 앵커를 사용하며 `획득점=배점×앵커/4`입니다.0은 실질적 실패/부재,1은 중대한 반복 혼동,2는 사용 가능하나 눈에 띄는 부담,3은 명료하고 안정적이지만 작은 잔여,4는 정의한 표본 전반에서 의미 있는 잔여가 없는 높은 완성도입니다. 미검증은null이고 성공이나 품질0점으로 단정하지 않습니다.

| 축 / 배점 | ID | 세부항목 | 배점 |
|---|---|---|---:|
| workspace 구성·밀도 /20 |A1|역할 구역과 시선 이동|6|
|  |A2|핵심 media/transport/시간축 가시성과 bounded shell|6|
|  |A3|읽기 밀도·행 길이|4|
|  |A4|1920 공간 사용과1280 적응|4|
| 정보·행동 위계 /15 |B1|작품·장면·Take·버전 맥락|5|
|  |B2|상태에 맞는 다음 행동|5|
|  |B3|중복·진단·중요 사실 노출|5|
| 색상·semantic 상태 /15 |C1|surface/action/선택/focus/검토 의미|5|
|  |C2|필수 전경·배경·경계 대비|5|
|  |C3|상태의 비색상 단서|5|
| 타입·간격·형태 /15 |D1|한국어·숫자·3단계 위계|5|
|  |D2|간격·정렬·그룹|4|
|  |D3|radius/border/shadow 역할|3|
|  |D4|icon·썸네일·대체 상태|3|
| 미디어·시간축 작업 /15 |E1|원본·preview·aspect·poster 맥락|3|
|  |E2|공통 시간좌표·길이·파형|4|
|  |E3|현재 위치·transport·seek/sequence|4|
|  |E4|Take 비교·audition과채택 분리|3|
|  |E5|음원·자막·편집 버전 관계|1|
| 상호작용 상태·키보드 /10 |F1|상태 전이·입력 보존|4|
|  |F2|핵심 keyboard/focus|3|
|  |F3|실패 영향·복구|2|
|  |F4|motion/reduced-motion|1|
| 디자인 시스템 일관성 /10 |G1|token→component 관리|4|
|  |G2|scale·responsive 계약|3|
|  |G3|component/state 재사용|3|

같은 결함을 여러 축에서 중복 감점하지 않습니다. 예를 들어 작은 preview는 구성, 반복 상태 문구는 정보위계, 파형 정렬은 미디어, 대비는 색상, token 관리는 구현 일관성에서 계산합니다. 모든 항목에 관찰값·이유·증거·한계를 붙입니다.

평가 coverage는 실제 증거를 확보한 항목의 최대 배점 합입니다.100%가 아니면 ‘확인된 배점C/100 중 획득P점’으로 표시하고 P/C를100점으로 재환산하지 않습니다. **이번결과는확인배점98/100중74.3점이며F3는미검증입니다. 원래template는변경하지않고별도finalscorecard에판단을기록했습니다.**

## 7. 점수로 상쇄할 수 없는4개 gate — 이번 결과

|Gate|결과|범위|
|---|---|---|
|H1미디어/seek/sync|UNVERIFIED|직접재생/trim/비교확인.로딩/오래된event/이전audio반례는별도코드증거이며브라우저전체미실행|
|H2승인/비용/버전|UNVERIFIED|비교·취소전후작품불변.신규승인/가격commit·복구전체미실행|
|H3핵심keyboard|UNVERIFIED|34Tab/모달복귀/취소/긴패널구간통과.처음부터전과정keyboard-only는미실행|
|H4필수대비|PASS·측정표본한정|본문·상태·경계·focus실제쌍.전체nativeoverlay/전체WCAG아님|

미검증을실패로단정하지도,성공으로부르지도않습니다. 이gate상태에서는전체표본수용완료/ready를선언하지않습니다. DM01–03의코드종료를재결함으로열지않았습니다.

## 8. 문서를 무엇을 바꿨는가

- 초기 요구/토큰/통합/reference/checkpoint 원문5개를 보존하고 최신 추가 합의를 날짜로 기록했습니다.
- 주 화면을1920,보조1280,모바일추가보류로 정리하고 bounded-shell 수용기준DS14를 추가했습니다.
- 낡은 ‘시간축 미구현’, ‘source disclosure 미수정’, ‘초기 연결거부가 현재 blocker’ 문구를 역사적 상태로 정리했습니다. 이미 고친 결함을 다시 계산하지 않습니다.
- 초기 token 제안과 실제 통합 baseline을 구분하고, 7축rubric+무스크롤추가요구를 채점 전에 hash로 고정했습니다.
- 방법론 적합성 표,14개과업의 결정 추적표,문서목차/변경기록을 추가하고 상대링크를 확인했습니다.
- 원본07 아키텍처, 앱코드/서버/DB, 구현·릴리스보고서, 과거QA이미지·시험결과는 변경하지 않았습니다. 모델독립선택·noMCP/fal·권리·비용·승인·초안/복구 계약을 보존했습니다.

## 9. 확인 가능한 공개 근거

다음은 이번 디자인 검토에서 직접 읽은 공개 자료입니다. 자료의 일반 원칙과 Loretune의 구체 치수/우선순위 판단은 구분합니다.

- [Adobe Premiere — 패널 조정](https://helpx.adobe.com/premiere/desktop/get-started/tour-the-workspace/customize-panels.html): 패널과 그룹의 접근·크기조절 근거.
- [Adobe Spectrum — design tokens](https://spectrum.adobe.com/foundations/design-data/design-tokens): primitive/semantic/component-specific,alias와의도 재사용.
- [NN/g — progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/): 중요한 기본옵션과 전문옵션의분리.
- [NN/g — recognition and recall](https://www.nngroup.com/articles/recognition-and-recall/): 현재대상/버전/상태의인지단서.
- [W3C — reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html):2D편집영역의예외가일반설명/폼전체면제는아님.
- [W3C — resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html):200%문자확대에서내용/기능보존.

[Blender HIG](https://developer.blender.org/docs/features/interface/human_interface_guidelines/paradigms/)의 분할 작업영역 근거는 연구 담당이 전달했습니다. **이번 디자인 담당의 직접 재조회는402오류로 실패했습니다.** 문서를 직접 읽었다거나 사이트가 유료라고 단정하지 않습니다. 다른 AI/색상/공동창작 자료의 제공자·검토범위는 적합성 표에 별도로 표시했습니다.

## 10. 이번 문서 변경과 남은 범위

최종1920실제화면15개,26항목별근거,대비/geometry/token계산,gate상태와미검증을추가했습니다. 이전pre-shell관찰과기능팀증거는구분해보존했습니다. 앱source/server/DB·원본07아키텍처는변경하지않았습니다. 문서원본의Library정체성과버전이력을유지해갱신합니다.

남은범위는실제저장오류/unknown복구·신규가격commit·처음부터전체keyboard-only·실제browserzoom·screenreader·실사용자시험입니다. 추가mobile작업은합의대로보류했습니다. 현재기능코드수정이나추가시각목표를생성하지않습니다.

---

# Loretune 최종 1920 독립 디자인·사용 흐름 QA

2026-10-26 · 고정 shell · 검토 종료02:15:51 UTC · 전문가 표본 평가

## 결과를 먼저

1920×1080 CSS viewport·앱100%에서 기본,sequence,정밀편집,긴패널,출력의 페이지 세로 스크롤은 제거됐고 주요 작업 맥락이 유지됐습니다. **이번 직접 표본에서 새로 재현된 사용 차단 결함은 없습니다.** 이는 모든 기능·오류·접근성의 통과나 경쟁사 동등성 선언이 아닙니다.

확인 가능한 배점 **98/100 중 74.3점**입니다. 정확한 합은74.25점이며 마지막에 소수1자리로 반올림했습니다. F3(실제 실패·복구)2점은 미검증이므로 전체 확정 점수는 보류합니다. 이를100점으로 재환산하지 않습니다. H1/H2/H3의 전체 gate는 미검증 범위가 남고, H4는 측정한 대비 표본에 한정해PASS입니다. 기준을 바꾸어90을 만들거나 과거5축점수와 비교하지 않습니다.

시각적으로는 미디어와시간축·검토의 인접성이 개선됐습니다. 남는 주요 절충은 정밀편집+sequence자막에서 실제영상이약334×188px로작아지는점,출력상세의내부검증문구,모델설정의반복안내·여백입니다. 승인완료카드가차분한것은정상이며강한CTA부재를감점하지않습니다.

## 1. 버전·자료·방법

작품:‘디자인 시스템 기능 QA20261026’. 장면길이1/2/4초,3개Take씩,합성시험패턴영상/파란이미지. 실모델생성결과가아닙니다. 실제콘텐츠미감·영상해상도를디자인감점에넣지않았습니다.

| 대상 | SHA256 |
|---|---|
|index.html|`202ea641e5c1f06d316babd21aa82ad29795f4f2d5de2ff077aef596ccb850c5`|
|studio.css|`8274aacf793e454fcc727801bdc3f7d9309345776e1e1fd6a049583e8469a3e9`|
|studio-media.js|`ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e`|
|app.py|`7fffd1402ebf8d1ea6f3c8828034145d158859ed4ba7aebf76656bc78f85163d`|

처음과끝의HTTP200제공본·현행소스해시가일치합니다. 작품JSON의시작/끝SHA256은`8ac30524626fcd58457cb62a2616710426e7ec33c1958f3d271bc3dca42a740d`로동일합니다. 이검토는저장/승인/새렌더/외부호출/DB편집/서버재시작을하지않았습니다. 임시초안·DOM스트레스는취소/제거했고앱배율100%로복원했습니다.

- O: 실제UI조작·저장후열어본스크린샷. M: 실제DOM/computed/시간/해시측정.
- S: 기능팀342회귀,7초렌더,독립코드8제어시나리오+7unit;DM01–03코드재검증. **시각점수근거가아니며O로부르지않습니다.**
- R: 지정된경쟁사공식/captured참고. P: 개선가설. U: 미실행.
- 기존EgoMac검증공간30을계속사용하고종료했습니다. 실제브라우저내용영역1920×1080,DPR1. 모니터물리해상도나실제browserzoom과구분합니다.

## 2. 실제 화면·상태 커버리지

| 순서 | 상태·과업 | 실제 결과·한계 | 증거 |
|---|---|---|---|
|1|기본승인장면검토|페이지1080px,preview·Take·timeline·review동시가시|[01](01-selected-1920.png)|
|2|sequence재생/멈춤|2.172/7초,장면02·한글자막표시. 장시간청취시험아님|[02](02-sequence-1920.png)|
|3|sequence+정밀편집|페이지1080px,영상은약188px높이.상세34개Tab가림0|[03](03-expanded-sequence-1920.png),keyboard-detail.json|
|4|선택Take+정밀편집|패널내스크롤후도핵심미디어유지.상단일부가스크롤된상태|[04](04-expanded-selected-1920.png)|
|5|영상+이미지비교|서로다른Take기본값,동일stage,원본비율|[05](05-comparison-image-video-1920.png)|
|6|가로+세로영상비교|동일상대1초,원본1.25/1.0초,무음·짧은쪽종료.선택불변|[06](06-comparison-video-video-1920.png)|
|7|dirty→단계전환→취소|값보존,저장활성,취소후원래메모/검토수정focus복귀|[07](07-review-dirty-1920.png),review-cancel.json|
|8|모델창|미선택과실행승인별도안내.저장없이Escape복귀|[08](08-model-dialog-1920.png)|
|9|앱글자150%|본문21px,문서1083px,가로overflow없음|[09](09-app150-1920.png)|
|10|앱글자200%|본문28px,flow·문서1226px,눈금겹침없음.브라우저zoom아님|[10](10-app200-1920.png)|
|11|1280보조회귀|정밀편집문서900px,핵심접근가능,영상작음|[11](11-expanded-1280.png)|
|12|긴패널|DOM임시60번째버튼/40개메모구간.문서1080,내부끝focus가시|[12](12-long-panels-1920.png),long-panels.json|
|13|기존출력상태|출력버전1·테스트미디어·납품검토전,새출력안함|[13](13-output-state-1920.png)|
|14|계획입력empty|기존계획commit없음.제출안함|[14](14-plan-state-1920.png)|
|15|제작도구empty|모델미선택/기존요청없음/비용확인안내,실행안함|[15](15-production-empty-1920.png)|
|16|reduced-motion|CDPpreference실제match,transition/animation0s|reduced-motion.json|
|U|실제loading/error/unknown복구|새저장실패·네트워크변형없이안전한표본없어미실행|F3null|
|U|반려/미검토revieweditor|비교/Take타일의검토전은관찰.반려/미검토inspector는미실행|범위구분|
|U|실제browser200/400%·screenreader|앱글자배율로대체하지않음|G2한계|
|U|처음부터전체keyboard-only|구간진입focus를사용한시험;모든첫진입·nativevideo조작완주아님|H3미검증|

긴패널의실측:rail client944/scroll5343px,마지막대상focus y913–996px,scrollTop4399. inspector client938/scroll3327px,검토수정y813–853px,scrollTop2388.5. 두경우document1080px입니다. 이는스크롤/가시성스트레스이지실제60개저장장면의성능시험이아닙니다.

## 3. 시각 QA — 구성·미디어 비율

아래는영상요소의가로폭이아니라intrinsicaspect와object-fit:contain으로계산한**실제그려지는미디어**입니다. 저장 픽셀과 대조했습니다. 04번의 측정 순간에는 미디어 readyState=0이었으므로 해당 행만 같은 선택 자산의 알려진 320×180 비율을 적용한 레이아웃 추정입니다. 04번을 재생 준비 완료의 증거로 사용하지 않습니다. 실제 기본·sequence·비교 재생 근거는 readyState=4인 01/02/03/05/06번입니다.

| 상태 | 문서높이/viewport | stage높이 | 실제미디어W×H | viewport면적 |timeline하단|
|---|---:|---:|---:|---:|---:|
|01-selected-1920|1080/1080|399.91|707.40×397.91|13.57%|1064.00|
|02-sequence-1920|1080/1080|299.52|528.92×297.52|7.59%|1064.00|
|03-expanded-sequence-1920|1080/1080|189.95|334.12×187.95|3.03%|1064.00|
|04-expanded-selected-1920|1080/1080|290.34|512.61×288.34|7.13%|1064.00|
|09-app150-1920|1083/1080|300.00|529.78×298.00|7.61%|1058.79|
|10-app200-1920|1226/1080|300.00|529.78×298.00|7.61%|1202.47|
|11-expanded-1280|900/900|165.70|291.03×163.70|4.14%|884.00|
|13-output-state-1920|1080/1080|290.34|512.61×288.34|7.13%|1064.00|

pre-shell의같은선택Take자료는기능팀제공캡처에서약533×300px,정밀편집문서1710px였습니다. 현재기본실영상약707×398px는면적약1.76배이고정밀편집문서1080px입니다. pre-shell은S제공본,current는O/M직접본이며동일상태완전동시AB실험은아닙니다. 모든화면에서같은1.76배개선이라고일반화하지않습니다.

구역폭184/1376/288px는동일하지만상단104px와timeline영역을유지하면서가용높이를분배합니다. 흑색letterbox는비율보존을위한정상영역입니다. 단순히가로여백이있다는이유로portraitcrop을요구하지않습니다. 반대로정밀편집에서가로여백이커지고실영상이줄어드는것은A4의작업효율절충으로기록합니다.

## 4. 시각 QA — 정확한 토큰·타입·형태

| 역할 | 현행값 | 적용·증거 |
|---|---|---|
|canvas/panel/raised/inset/chrome|#101010/#1B1B1B/#242424/#141414/#151515|studio.css:6–10,실제panel배경|
|hover/pressed/media/compare|#303030/#3D3D3D/#050505/#080808|studio.css:11–14;hover실측,pressed모든상태미실행|
|strong/body/muted/disabled|#F4F4F2/#DEDEDB/#BDBDBB/#A6A6A3|studio.css:15–18;본문실측|
|divider/control|#383838/#858585|장식선과필수입력경계구분|
|selected/marker/selection-edge|#2A2A28/#D8D8D2/#EEEEEE|실제rail은면+insetmarker,모든선택이edge토큰을쓰는것은아님|
|focus|#E4DDBE|2pxdashed+offset2px,선택표식과다름|
|error/errorbg/warning|#FFB49D/#28201E/#E6C58B|지정값;실제error화면이번미실행|
|primary/on-primary|#F4F4F2/#101010|dirty활성저장실측.완료카드의강한CTA강제없음|
|type|12/13/14/16/18/20/24px;400/500/600|root역할.실제heading20/600/28,항목13/500/19.5,메모14/400/23.8|
|font|system-ui,-apple-system,Apple SD Gothic Neo,Noto Sans KR,sans-serif|외부font요청추가없음|
|spacing|4/8/12/16/24/32px|예외10pxgap등은그룹역할로검토;곧바로결함아님|
|radius|clip4/control6/panel8/dialog12px|시간축연속clip0px예외의역할명확|
|motion|120ms|reduced-motion실측0s|

모든실제custom-property는[tokens.csv](tokens.csv),상태별계산값은[styles-states.json](styles-states.json)에있습니다. 줄간격토큰1.45/heading1.4와메모1.7예외를구분합니다. 컴포넌트별더높은specificity가실제값을정하므로root목록만읽고모든요소가같다고하지않습니다.

선택의왼쪽inset표식,focus의점선외곽,검토의✓/○+텍스트는서로다른역할입니다. hover는선택과달리pressed상태를바꾸지않습니다. 실제썸네일은원본첫프레임이며media의색을UIbrand로복제하지않습니다. Native영상control과텍스트glyph의광학차이는남습니다.

### 실제 대비 표본

CSS불투명색은요소에서조상방향으로배경층을추적해실제로대면하는배경과계산했습니다. 아래M표본은opacity1입니다. alpha가있는미검증nativeoverlay/모달backdrop을임의로불투명쌍으로대체하지않습니다.

| 역할 | 전경/배경 | sRGB대비 | 분류 |
|---|---|---:|---|
|제목/canvas|#F4F4F2/#101010|17.278:1|text;M|
|본문/panel|#DEDEDB/#1B1B1B|12.777:1|text;M|
|보조/panel|#BDBDBB/#1B1B1B|9.154:1|text;M|
|검토상태/선택면|#DEDEDB/#2A2A28|10.667:1|text;M|
|button문자/raised|#F4F4F2/#242424|14.096:1|text;M|
|필수경계/raised|#858585/#242424|4.207:1|nontext;M|
|필수경계/panel|#858585/#1B1B1B|4.668:1|nontext;M|
|필수경계/hover|#858585/#303030|3.577:1|nontext;M|
|focus/canvas|#E4DDBE/#101010|13.940:1|nontext;M|
|focus/hover|#E4DDBE/#303030|9.669:1|nontext;M|
|선택표식/선택면|#D8D8D2/#2A2A28|10.048:1|nontext;M|
|파형/inset|#BDBDBB/#141414|9.791:1|nontext;M|
|primary문자/primary면|#101010/#F4F4F2|17.278:1|text;M|
|장식선/panel|#383838/#1B1B1B|1.469:1|decorative;M|
|오류/오류면|#FFB49D/#28201E|9.325:1|specified_not_live_error;source_only|

장식선1.469:1은레이아웃구분용이고필수입력경계는#858585를사용합니다. inactivecontrol은별도예외입니다. 이것이전체WCAG준수,영상위모든자막/아이콘대비,스크린리더품질을보증하지않습니다.

## 5. 시각·사용 흐름의 잔여 — 원인과 재검증

| ID/중요도 | 원인·실제근거 | 사용자영향 | 범위내개선판단 | 재검증조건/감점축 |
|---|---|---|---|---|
|V1/P2 절충|정밀편집44%/최소360px와sequence/자막chrome가함께공간사용.실영상334×188px|타이밍입력중영상세부가작아짐|즉시재설계필수라단정안함.기존상태요약/세로gap을줄일때만의미·control보존.가짜확대/crop금지|동일scene/time/caption에서media증가,doc1080,34Tab접근유지;A4만|
|V2/P3 문구|출력상세에자산해시·최종렌더검사설명|사용자가필요없는내부방식을읽음|사용자문구는‘저장된버전과승인상태를확인합니다’;원본진단은명시적상세에유지|권리/모델/비용/승인누락없음;B3만|
|V3/P3 밀도|모델창선택·이름·미선택안내3행과큰간격|단순미선택사실의반복|선택모델명과실제조치안내만그룹.연결상세·비용재확인안내유지|미선택/선택/불가/긴이름표본에서행수와가독성;D2만|
|V4/관찰|sequence중편집선택01과재생02가동시에표기|서로다른맥락을읽어야함|오류로단정하지않음.기존‘재생중’과‘선택한장면’의역할을더명확히할여지|선택/승인/trim불변,재생대상직관성;B1만|

같은 문제를 다른 축에서 중복 감점하지 않습니다. 평가 coverage98은 일부 표본을 근거로 판단한 25개 항목의 배점 합이며, 모든 상태의98%를 시험했다는 의미가 아닙니다. 색상부족·저장오류·disclosure실패를새로발명하지않았고,닫힌DM01–03을다시열지않았습니다. 이보고서는진단이며앱패치를작성/적용하지않았습니다.

## 6. 고정26항목 점수와 이유

앵커0/1/2/3/4,획득=배점×앵커/4.4는정의한표본에서의높은완성도이며제품전체인증이아닙니다. ‘측정하지않은상태가있다’는문구는실패감점이아니라4를일반화하지않는범위설명입니다. F3는실제판단표본자체가없어U입니다.

| 축 | 고정배점 | 평가가능배점 | 획득점 |
|---|---:|---:|---:|
|A. workspace 구성·밀도|20|20|15.50|
|B. 정보·행동 위계|15|15|10.00|
|C. 색상·semantic 상태|15|15|11.25|
|D. 타입·간격·형태|15|15|11.25|
|E. 미디어·시간축 작업|15|15|12.75|
|F. 상호작용 상태·키보드|10|8|6.00|
|G. 디자인 시스템 일관성|10|10|7.50|

확인 가능한 배점 **98/100 중 74.3점**입니다. 정확한 합은74.25점이며 마지막에 소수1자리로 반올림했습니다. F3(실제 실패·복구)2점은 미검증이므로 전체 확정 점수는 보류합니다. 이를100점으로 재환산하지 않습니다. 미검증2점의추가확인에따라산술적으로74.3–76.3범위의합이가능하지만,현재의전체확정점수로부르지않습니다. 이범위는통계적신뢰구간도아닙니다.

### A. workspace 구성·밀도

**A1 역할 구역과 시선 이동 — 앵커3/4 → 4.5/6점**

측정: rail184px·중앙1376px·inspector288px. 장면→미디어→검토를 동시에 식별한다.

판단: 구역 역할과 인접성이 명료하다. 세 구역의 실제 작업 순서/탐색 시간을 사람에게 검증하지 않았으며 복잡한 장면 제작 상세는 내부 스크롤이 필요하다.

근거: 01-selected-1920.png; 15-production-empty-1920.png.
**A2 핵심 media/transport/시간축 가시성과 bounded shell — 앵커4/4 → 6/6점**

측정: 기본·sequence·정밀편집·긴패널·출력 문서1080/1080px,가로1920/1920px. timeline하단1064px. 정밀편집34개Tab대상 가시.

판단: 이 항목에 정한 표본에서 주요 진입점과 미디어/시간축이 남고 마지막 상세에도 도달한다. overflow:hidden으로 단순히 잘라낸 결과가 아니다. 긴 패널은DOM 시뮬레이션이며 실제60장면 프로젝트 성능은 검증하지 않았다.

근거: 01/02/03/12/13 캡처·JSON; keyboard-detail.json; long-panels.json.
**A3 읽기 밀도·행 길이 — 앵커3/4 → 3/4점**

측정: inspector288px,본문14px/23.8px. 긴 한글 입력과 메모는 줄바꿈되며 본문 폭이 중앙 전체로 늘어나지 않는다.

판단: 본문 읽기와 그룹은 안정적이다. 긴 메모는 단락 구조/요약 없이 세로 길이가 커진다. 이는 접근 불가가 아닌 읽기 부담이며 자동 요약 새 기능을 요구하는 것은 아니다.

근거: 01-selected-1920.png; 07-review-dirty-1920.png; 12-long-panels-1920.png.
**A4 1920 공간 사용과1280 적응 — 앵커2/4 → 2/4점**

측정: 실제contain 영상:기본707.40×397.91,sequence528.92×297.52,sequence+정밀334.13×187.95px.1280정밀291.03×163.70px.

판단: 기본 미디어는 커졌지만 정밀편집·자막 동시 상태에서1920의 실영상은 viewport약3.03%로 줄어든다. control접근은 유지되지만 세부 화면을 보는 여유가 작다. 작은preview 감점은A4에만 배정한다.

근거: 01/02/03/04/11 캡처·JSON.

### B. 정보·행동 위계

**B1 작품·장면·Take·버전 맥락 — 앵커3/4 → 3.75/5점**

측정: 선택장면01/Take1,재생장면02,저장버전1이 각각 표기된다. 비교창도Take별 선택/검토 상태를 표시한다.

판단: 선택과재생의 대상은 올바르게 분리된다. sequence재생 시 상단/inspector의 선택01과transport의재생02를 사용자가 함께 읽어야 하는 인지 부담은 남는다. 데이터 불일치라고 판정하지 않는다.

근거: 01-selected-1920.png; 02-sequence-1920.png; 06-comparison-video-video-1920.png.
**B2 상태에 맞는 다음 행동 — 앵커3/4 → 3.75/5점**

측정: 승인완료=검토수정,dirty=활성저장/취소,출력준비=결과검토/저장/납품검토전.

판단: 완료 상태에 강한CTA를 억지로 요구하지 않는다. 현재 관찰한 다음 행동은 적절하다. 미검토/반려 inspector와 실제저장오류·유료commit은 이번 상태표본에 없으므로 전 상태 최고앵커를 주지 않는다.

근거: 01-selected-1920.png; 07-review-dirty-1920.png; 08-model-dialog-1920.png; 13-output-state-1920.png.
**B3 중복·진단·중요 사실 노출 — 앵커2/4 → 2.5/5점**

측정: 기본화면은job/hash 없이 테스트미디어1개표시. 출력 정밀상세에는 “자산 해시와 승인 상태를 다시 검사”, “최종 렌더”가 남는다.

판단: 기본 창작 흐름은 정리됐다. 다만 사용자용 편집 상세에 내부 검증 방식과take 소문자 문구가 남아 읽기 비용을 높인다. 비용·모델·승인을 숨기지 않고 실제 결과/다음 행동 중심 문구로 바꿀 여지가 있다.

근거: 08-model-dialog-1920.png; 13-output-state-1920.png; 15-production-empty-1920.png.

### C. 색상·semantic 상태

**C1 surface/action/선택/focus/검토 의미 — 앵커3/4 → 3.75/5점**

측정: 선택#2A2A28+왼쪽#D8D8D2표식,hover#303030,focus#E4DDBE 2px dashed/offset2,승인은✓+텍스트.

판단: 선택/focus/검토는 같은 테두리로 처리되지 않는다. 반복 상태의 의미는 안정적이다. 강제색상과 반려/실패 상태의 실제 픽셀 표본은 없다.

근거: styles-states.json; 01-selected-1920.png; 07-review-dirty-1920.png.
**C2 필수 전경·배경·경계 대비 — 앵커3/4 → 3.75/5점**

측정: 실제불투명배경쌍:본문/패널12.78,보조/패널9.15,컨트롤경계/raised4.21,경계/hover3.58,focus/hover9.67.

판단: 측정한 필수본문·경계·focus는 필요한 대비를 확보한다. 반투명dialog backdrop와nativevideo overlay 모든 위치/상태를 측정한 것은 아니며 전체WCAG 인증이 아니다.

근거: contrast.csv; styles-states.json; 07-review-dirty-1920.json.
**C3 상태의 비색상 단서 — 앵커3/4 → 3.75/5점**

측정: 선택 aria-pressed+왼쪽표식,승인✓/검토전○+문구,모델미선택 문구,dirty저장활성.

판단: 색에만 의존하지 않는 단서가 실제로 보인다. 실제error/disabled 조작 전체를 이번에 열어 검증하지 않았으므로 최고앵커는 보류한다.

근거: 01-selected-1920.png; 06-comparison-video-video-1920.png; production-state.json.

### D. 타입·간격·형태

**D1 한국어·숫자·3단계 위계 — 앵커3/4 → 3.75/5점**

측정: 제목20px/600/28px;항목13px/500/19.5px;본문14px/400/23.8px;메타12px,시간tabular-nums.

판단: 제목·본문·메타의 세 읽기 층위가 분명하고 긴한글도 읽힌다.12px 메타가 많은 편집 화면 특성상 확대 때 패널폭과 줄 수의 절충이 남는다. 테스트화질은 평가하지 않는다.

근거: styles-states.json; 07/09/10 캡처.
**D2 간격·정렬·그룹 — 앵커3/4 → 3/4점**

측정: 4/8/12/16/24/32px 기본간격,Take내부8px/장면10pxgap,버튼8×12pxpadding.

판단: 인접항목 정렬과그룹은 일관적이다. 모델dialog는선택·이름·미선택안내가분리된3행이고 여백이커 정보대비높이가크다. 치명적잘림은 없다.

근거: 01-selected-1920.png; 08-model-dialog-1920.png; styles-states.json.
**D3 radius/border/shadow 역할 — 앵커3/4 → 2.25/3점**

측정: control6px,panel8px,dialog12px 계열. 기본panel은shadow없음,선택은2pxinset표식.

판단: 면·경계·형태의 역할이 비교적 명료하다. 시간축 버튼은0pxradius로연속성을보존한다.모든컴포넌트예외의완전한정규화까지검증한것은아니다.

근거: styles-states.json; studio.css:30–39,669–758.
**D4 icon·썸네일·대체 상태 — 앵커3/4 → 2.25/3점**

측정: 실제영상첫프레임poster,이미지thumbnail,영상nativecontrols. 검토✓/○와disclosure›/삼각형.

판단: 실제asset의대표이미지가대상인지를돕고허위이미지를쓰지않는다.텍스트glyph와native아이콘이혼용되어광학무게가완전히같지는않다.새아이콘세트를도입할필요까지단정하지않는다.

근거: 01-selected-1920.png; 05-comparison-image-video-1920.png; 06-comparison-video-video-1920.png.

### E. 미디어·시간축 작업

**E1 원본·preview·aspect·poster 맥락 — 앵커4/4 → 3/3점**

측정: 원본320×180/180×320,contain비율보존.비교두stage약471×300px.원본5초와편집1초구분.

판단: 정의한이미지/영상및혼합비율표본에서왜곡·crop없이실제poster와출처를보여준다.영상콘텐츠품질·장시간코덱호환성은별도다.

근거: 01-selected-1920.png; 05/06 비교 캡처·JSON.
**E2 공통 시간좌표·길이·파형 — 앵커3/4 → 3/4점**

측정: ruler/wave/track x233,w1350px공유.1/2/4초폭192.852/385.711/771.422.재생2.172s playheadx651.953,예측651.886(약0.07px차).

판단: 시간좌표와비례는실측으로맞는다.파형은실측진폭이며fixture가작은일정신호라거의평평하다.실제음악의강약/긴타임라인유용성은이fixture로검증하지못했다.

근거: 02-sequence-1920.json; styles-states.json.
**E3 현재 위치·transport·seek/sequence — 앵커3/4 → 3/4점**

측정: sequence00:02.172/00:07.000과원본frame약1.4386s,장면02자막.비교상대1.000s에서source1.250/1.000s.

판단: 시간과trim관계를관찰할수있고실제재생·멈춤이된다.로딩중seek/장시간브라우저동기검증은이번직접표본에없다.DM01–03코드종료를재결함으로계산하지않는다.

근거: 02-sequence-1920.png/json; 06-comparison-video-video-1920.json.
**E4 Take 비교·audition과채택 분리 — 앵커4/4 → 3/3점**

측정: 초기Take1과3으로상이한기본값.영상+이미지,가로+세로영상시험.비교무음·짧은1초구간정지·선택/승인/편집불변.

판단: 정해진표본에서비교와채택이구분되고모달닫기복귀가명확하다.프레임정밀비교가아니라는표시를보존한다.

근거: 05/06 비교 캡처; comparison-draft-journey.json; start.json; end.json.
**E5 음원·자막·편집 버전 관계 — 앵커3/4 → 0.75/1점**

측정: 편집7초,음원v1/0.5–7.5초,저장버전1·출력승인됨,납품검토전의별도표시.

판단: 화면에서음원·자막·출력버전관계를추적할수있다.새렌더·실제오디오청취·MP4자막재추출은이번에하지않았고기능팀증거로분리한다.

근거: 02-sequence-1920.png; 13-output-state-1920.png.

### F. 상호작용 상태·키보드

**F1 상태 전이·입력 보존 — 앵커3/4 → 3/4점**

측정: 임시초안작성→4단계→3단계후동일문자보존→Tab취소→원래메모·초점복귀.프로젝트SHA불변.

판단: 관찰한초안·취소전이는안정적이다.저장중추가타이핑/실제오류·프로젝트간전환은이번화면시험에서새로실행하지않았다.

근거: 07-review-dirty-1920.png; review-cancel.json; end.json.
**F2 핵심 keyboard/focus — 앵커3/4 → 2.25/3점**

측정: 정밀편집34개연속Tab중가림0.비교Escape복귀,검토수정→입력→취소→출처Enter.긴panel마지막대상가시.

판단: 초점과복귀는확인한경로에서안정적이다.각구간은명시적focus진입후시험했으며브라우저처음부터전과정을키보드만으로완주한시험은아니다.

근거: keyboard-detail.json; comparison-draft-journey.json; review-cancel.json; long-panels.json.
**F3 실패 영향·복구 — U/null**

측정: 현재안전하게재현할저장오류/unknown복구상태없음.공유데이터/네트워크를변형하지않음.

판단: 미검증이다.성공점수도실패0점도부여하지않는다.과거오류수정/다른담당시험을이번직접검증으로바꾸지않는다.

근거: 미실행.
**F4 motion/reduced-motion — 앵커3/4 → 0.75/1점**

측정: CDP의prefers-reduced-motion:reduce 실제match=true.버튼/shot/preview/summary transition·animation0s,scrollauto.

판단: 선호설정에따른장식동작제거는확인했다.전체장시간모션·OS설정·의도된영상재생의모든조합은시험하지않았다.

근거: reduced-motion.json; studio.css:552–554,754–756,810–812.

### G. 디자인 시스템 일관성

**G1 token→component 관리 — 앵커3/4 → 3/4점**

측정: primitive/semantic역할은root한곳,컴포넌트실측과연결.조건별기존selector순서는보존되어CSS857행내중복override가남음.

판단: 실제색/타입역할중앙화는진전이다.중복selector가곧결함은아니며현재표본에서값충돌은재현되지않았다.다만여러조건순서를추적해야하는유지보수부담이남아4는아니다.

근거: studio.css:1–64,669–758,824–857; styles-states.json.
**G2 scale·responsive 계약 — 앵커3/4 → 2.25/3점**

측정: 앱150%=본문21px,200%=28px,문서1083/1226px가로overflow0.1280정밀문서900/900.

판단: 글자축소없이큰문자에서flow로전환한다.실제browser200/400%zoom과screenreader는미검증이며앱배율시험을대체증거로쓰지않는다.

근거: 09/10/11 캡처·JSON; index.html:728–755.
**G3 component/state 재사용 — 앵커3/4 → 2.25/3점**

측정: rail/Take/inspector가같은승인✓/검토전○언어,선택은표식/pressed.시간축은길이·대상중심.

판단: 동일의미의주요상태가반복적용된다.모든오류/반려/empty변형의실제표본은없으며glyph/상세문구의잔여는각주축에서만계산했다.

근거: 01-selected-1920.png; 06-comparison-video-video-1920.png; styles-states.json.

## 7. 필수gate와 기능시험의 경계

| Gate | 결과 | 근거와미확인 |
|---|---|---|
|H1_media_seek_sync|UNVERIFIED|직접재생/비교/trim은확인.로딩중seek/오래된event/이전audioloop정지반례는S의Node검증이며이번브라우저에서모두재실행하지않았다.닫힌DM01–03재개아님.|
|H2_approval_cost_version|UNVERIFIED|비교·초안취소전후canonicalproject불변,모델선택≠실행승인표시는확인.현재fixture의실행commit가격·범위/복구는신규승인없이재현하지않았다.|
|H3_keyboard|UNVERIFIED|표본구간34Tab/모달Escape/초안취소/출처Enter/패널끝가시는통과.명시적focus진입을포함한구간시험으로처음부터전과정keyboard-only완료gate전체를대체하지않는다.|
|H4_contrast|PASS|표본쌍은본문4.5:1,필수비문자단서3:1이상.장식선/inactive는별도.모든nativevideo overlay/반투명상태/전체WCAG인증아님.|

기능팀342회귀/7초렌더와코드감사8시나리오+7unit는별도S근거입니다. 이번디자인판단의높은점수나브라우저geometry의증거로합치지않습니다. 실제음악청취·장기sync·유료provider·실사용자관찰·browserzoom·screenreader는미검증입니다. 닫힌코드결함과未시험브라우저조건은서로다릅니다.

## 8. 방법론→실제판단 추적

| 사용자과업 | 참고근거 | Loretune선택이유 | 구현위치 | 이번검증/불확실성 |
|---|---|---|---|---|
|미디어보며편집|Premiere패널·Descripttimeline|관련구역인접/긴상세만내부scroll|studio.css:836–854,index.html:728–755|O/M기본·정밀·34Tab·긴panel;장기실사용U|
|현재대상인지|Frame.ioasset/player,NN/grecognition|scene/Take/버전/승인관계표기|.lt-shot-header,.creator-review-context,#timeAxis|O/M비교·기본;실사용인지속도U|
|시간에맞게조절|Descript공통시간축,NF공식Track|1/2/4초비례,실제파형,같은x원점|studio.css:774–788,studio-media.js|O/M좌표·재생;음악강약fixture대표성낮음|
|모델/비용판단|PAIRmental-models·HAX|선택/승인/실행분리,정확한상태|#modelSettingsPanel,#productionTools|O미선택·설명,실제commitU|
|검토의견수정|NN/gprogressivedisclosure·비파괴창작|결과카드우선,수정시draft/save/cancel|#creatorEditReview,#reviewReason|O초안보존/취소,실제errorU|
|읽기/상태구분|Spectrumtokens/type·W3Ccontrast/resize|중성역할쌍·CJK·비색상단서|studio.css:4–64,669–758|M대비·타입,O앱배율,실browserzoomU|

직접공개자료URL과채택/조건부/제외전표는상위[METHODOLOGY-FIT-MATRIX-ko.md](../../METHODOLOGY-FIT-MATRIX-ko.md)에보존했습니다. BlenderHIG는연구팀제공내용이며디자인담당직접조회402실패를성공으로바꾸지않습니다.

## 9. 경쟁사 자료의 역할과 한계

- Descript [captured editor](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87),[공식timeline](https://help.descript.com/timeline/timeline-overview):시간좌표·레이어/파형참고.
- Frame.io [captured review](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871):실제asset/version과인접player·검토참고.
- NeuralFrames 공식Track3194×1494/Storyboard3210×1690이미지:제작단계·shot/media관계.실제인증계정직접관찰로부르지않음.
- Runway [captured home](https://refero.design/pages/bc5ff496-55ad-4478-a968-62f7e641b9db):조용한prompt쉘만. [공식Studio](https://help.runwayml.com/hc/en-us/articles/52685547867667-Trimming-and-Assembling-Clips-in-Studio):manual/chat맥락. home을timeline증거로쓰지않음,API연동대상아님.

참고화면의viewport·시점·미디어가다릅니다. 이보고서의1920은우리앱의실측조건이며경쟁사와동일조건성능/점수실험이아닙니다. 경쟁사내부HEX·순위·등가품질을만들지않습니다.

## 10. 산출물·완료범위

- [scorecard.json](scorecard.json),[scorecard.csv](scorecard.csv):26개고정배점·이유·gate·coverage.
- [geometry.json](geometry.json),[contrast.csv](contrast.csv),[tokens.csv](tokens.csv):실측/계산.
- [start.json](start.json),[end.json](end.json):제공본/소스/작품불변.
- 실제화면01–15는모두저장후열어확인.12는DOM스트레스명시,09/10은앱배율명시.이미지추정색/원본생성물로오인시키지않음.
- Library실제화면:기본`libfile_50bd16dd99a48191a07dd4e878b26afd`,sequence정밀`libfile_a972c3c6524081919b1055833572e54f`,비교`libfile_444d2eac91f481918852bddd31935d30`.

정의한독립화면감사는완료했습니다. 남은미검증을억지로채우기위해유료생성/승인/DB변형을하지않았습니다. 전체수용완료/90/출시준비라는포괄주장은하지않습니다. 별도QA공간은종료했으며사용자탭과실행서버를유지했습니다. Ego업데이트알림은있었지만환경은업데이트하지않았습니다.
