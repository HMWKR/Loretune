# Aethon 방법론 적용 현황

## 2026-10-27 사용자 흐름 단순화 — 적용 기준 보강

음원을 먼저 넣고 사진은 선택하는 개인 제작을 중심으로, 불필요한 내부 정보와 중복 단계를 줄인다. 이 절은 방법론과 검증 계획이며 전체 개선·사용자 시험 완료를 의미하지 않는다. 기존 방법론과 토큰 기준을 유지하고, 아래는 공식 출처를 다시 확인해 서로 다른 역할에 연결한 보강이다.

| 방법 | 이 제품에서의 적용 | 판단·검증 경계 |
|---|---|---|
| [과업과 사용자 요구 조사](https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs) | 음원만 있는 경우와 사진도 있는 경우를 각각 입력→계획→제작→편집→출력·재개의 실제 과업으로 살핀다. 중복 입력과 작업 전환을 찾아 합칠 후보를 기록한다. | 합성 fixture·전문가 walkthrough는 실제 사용자 관찰이 아니다. 작업시간·혼란·빈도는 사용자를 관찰하기 전까지 가설이다. |
| [점진적 공개](https://www.nngroup.com/articles/progressive-disclosure/) | 현재 행동에 필요한 선택과 상태를 먼저 보여 주고 내부 ID·원시 진단과 드문 옵션은 요청 시 확인하도록 한다. | 비용·권리·선택 모델·실제 전송·승인·실패 및 복구에 필요한 사실은 결정 시점에 보인다. 감추기와 삭제는 다르다. |
| [사용성 휴리스틱](https://www.nngroup.com/articles/ten-usability-heuristics/) | 현재 상태, 사용자 용어, 취소·복구, 일관성, 오류 예방과 인지 가능한 선택을 같은 과업을 따라 점검한다. | 전문가의 결함 탐색 기준이며 실사용자 성공률이나 임의의 전체 점수로 환산하지 않는다. |
| [Human–AI Interaction](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/) | 선택 모델이 할 수 있는 일·한계, 제안과 사람 승인, 수정과 복구를 구별한다. AI의 설명과 서버 확인 사실을 분리한다. | 실제 모델이 모든 편집을 이해한다고 가정하지 않는다. 원칙 적용과 실제 모델·사용자 검증은 별개다. |
| [인지 접근성: 단계 인지](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o1p04-clear-steps/) 및 [입력 안내](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o4p07-step-instructions/) | 현재 단계·완료한 선택·다음 행동을 복귀 후에도 확인하고 입력 조건을 필요한 곳에 미리 둔다. | W3C의 보충 패턴은 유용한 설계 지침이며 이것만으로 WCAG 적합을 판정하지 않는다. |
| [오류 식별](https://www.w3.org/WAI/WCAG22/Understanding/error-identification)·[오류 수정 제안](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html) | 어떤 입력이 문제인지 텍스트로 알리고 알려진 수정 방법을 제공한다. 초안과 기존 결과는 보존한다. | 실제 자동 감지 오류와 알려진 수정 제안에 적용한다. 항목 옆 표시만이 유일한 적합 방식은 아니다. |
| [Double Diamond](https://www.designcouncil.org.uk/resources/the-double-diamond/) | 실제 문제 확인→범위 정의→대안 비교→구현·검증 순서를 사용하되 작은 수정에는 필요한 만큼만 적용한다. | 반복 문서 생성이나 미실시 사용자 연구를 강제하지 않는다. 대안과 실측 결과는 구분한다. |

현재 관찰: 음원 입력에 16MiB 상한이 사전에 나타나지 않고, 초과 파일 오류가 입력에서 떨어진 상단에 표시되는 사례를 합성 파일로 재현했다. 입력 근처의 조건·복구 안내와 기존 구조를 유지하는 대안을 우선 검토한다. 전체 온보딩 재배치는 충분한 근거가 생기기 전 보류한다. 사진 선택 안내와 비용·권리·승인 사실은 유지한다. 디자인 구현과 같은 조건의 전후 검증은 기능 작업 이후 진행한다.

## 2026-10-27 채택 설계 보충 — 새 제품 검사 없음

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** [단일 AD 설계](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md)와 [정체성/개인·팀 보충문](../../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md)을 적용한다. 아래 81점과 각 hash는 과거 빌드의 기록이다. 최신 독립 전체 시각점수/90달성·고객실험으로 환산하지 않는다. 현재 제품은416 이후 세션 partial이며 이번에는 문서 링크·보존 해시만 검사했다.

|방법 / 적합성|현재 과업·결정|설계/향후 구현 연결|검증 계획·이번 결과 / 한계|
|---|---|---|---|
|작업분석·인지 walkthrough / 채택|개인 완주가 기본, 팀 인계는 별도 선택 과업|AD §7/§16 P01–10·T01–09, 기존07|개인에 팀선행단계0, 팀은권한별양/음성. 지금은문서계획, 실제사람관찰아님|
|객체/버전 정체성·recognition / 채택|자료role/version·대화scope·Take·검토의일관성|AD01/02/04/05, 기존context/reference/proposal경로|P02/04/08–10·CS. 새DB아키텍처전면복제 없음|
|위험기반점진공개·Human-AI 역할분리 / 채택|선택/실제전송/사람승인/실행/비용을분리|AD06, 기존serverreceipt/action/ledger|C02/03/06. 진단숨김≠실패/비용숨김, AI원문≠서버사실|
|참조기반 craft·semantic tokens / 채택|중성작업대/기존시각역할유지, donor는계약참고|[reference lock](REFERENCE-LOCK.md), [tokens](SEMANTIC-TOKEN-SPEC.md)|새 HEX변경/측정 없음. 동일조건pixels·computed표본이 있어야 변경효과 판단|
|상태전이·대표콘텐츠·회귀 / 채택|draft/dirty/error/unknown·긴한글·미지원모델·대화전환|AD C01–C07, 기존closed반례/CS01–18|fake/VM/actualbrowser/live분리. 중복분모/새점수 없음|
|실제팀사용자연구·협업효과 / 조건부|P3권한기반 이후 팀인계 가치 확인|AD07/P5|내부두actor시험을고객연구라부르지않음. 시간절감/경쟁우위 미측정|
|Hallmark / 보조채택|토큰·형태·컨트롤정합성 수동적용|[실제사용기록 §13](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md)|과거static sloplint exit1의9FAIL/73REFLEX/15WARN은후보. render인증/이번실행없음|
|Impeccable / 보조채택|Operate/harden/audit의입력보존·위계·오류복구|같은실제사용기록·기존폼반례|기존engine probe exit127, detector/overlay 미실행. 수동적용을자동검사로표기금지|
|Refero / 주요디자인연구|기존editor styles/screens/flows와적용/배제잠금|기존captured공식자료·CURRENT-DESIGN-QA-PLAN|과거tool조회와이번문서재사용구분. 내부토큰추정/계정조작 없음|
|전체스택/테마·범용메신저·자동재생성 / 제외|피벗이후IP영상 목적과유한개선범위유지|AD §6|가격/과거고객성과/REA실행성공을승계하지않음|

공개 방법론 출처와 채택/조건부/제외의 상세 근거는 아래 보존 표 및 [183행 workflow를 반영한 단일 PLAN](../codex-cli-assessment-20261026/PLAN-ko.md)에 있다. 새로운 외부 연구·엔진·Library 호출은 수행하지 않았다. 작업 순서는 G0근거→G1참조→G2진단→G3설명/문서승인까지, G4구현은 미개시; 향후 G5QA→G6독립→G7문서/전달을 각 단계별로 연결한다.

## 이전 방법론·검증 기록 — 당시 값과 결과 보존

## 2026-10-26 추가 기록 — 잔여 두 항목 수정, 재채점 없음

현재 HTML은 `0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109`입니다. **81/100은 이전 `5fcc2cca…fd99b` 고정본에 대한 최신 독립 전체 평가**로 보존합니다. 이번 수정본에 새 점수나 변경 앵커를 부여하지 않았습니다. 아래 과거 보고서의 잔여 지적은 당시 기록이며, 이 두 항목의 현행 상태는 이 추가 기록을 따릅니다.

- 미확정 저장 안내는 원인 중립 표현으로 변경됐습니다. 직접 열어본 저장 화면에서 ‘연결이 돌아오면’ 없이 입력 보존·같은 요청의 처리 결과 조회·확인 전 재제출 금지를 명시합니다. 기존 저장 확인 버튼과 비활성 저장 버튼이 보입니다.
- 보조1280×900의 정밀 패널 최소 높이를 해당 작은 desktop 조건에서만340→300px로 조정했습니다. 직접 열어본 화면에서 영상·자막·시간축·주요 조작이 함께 보입니다. 구현팀 실측은 실제영상218.14×122.70→289.25×162.70px, 문서900px,34controls+진단summary1 접근 보존입니다. 이 수치와 동작 검증은 이번 독립 라이브 재측정이 아닌 제공 근거입니다. 내부 상세 스크롤량 증가라는 절충은 유지됩니다.

확인 범위: 구현팀 REPORT/manifest/patch 읽기, 저장된 `final-expanded-1280.png`와 `controlled-unknown-1920.png`의 실제 픽셀 열기, 현행 소스 및 이미지 SHA256의 manifest 일치 확인. 새 브라우저 동작·HTTP 응답·오류 주입·키보드 전체 시험은 반복하지 않았습니다.346회귀/6문법/통제 오류와 새 초안 보존은 구현팀 결과로 구분합니다. 통제 오류 화면은 실제 서버 장애·DB 저장·청구 증거가 아닙니다.

방법론 연결: 작은viewport의 미디어/상세 공간 배분은 작업 맥락 유지 원칙의 제한적 적용이며, 원인 중립 안내는 확인된 사실과 다음 행동만 설명하는 실패 복구 원칙의 적용입니다. 새 기능·브랜드·가중치 변경은 없습니다. 코드 diff에서1920 규칙과미디어 수명 JS는 변경되지 않았습니다.

이전 독립 전체평가의 H1/H2 미검증 및 H3/H4 표본PASS 경계는 그대로입니다. 실제 공급자·비용/승인 실행·브라우저200/400%확대·스크린리더·사용자시험의 미검증을 해소한 것으로 주장하지 않습니다. 앱/DB/서버는 수정하지 않았고 기존 역사적 점수·근거를 보존합니다.

근거: [구현 보고서](../desktop-residual-20261026/REPORT-ko.md), [릴리스 manifest](../desktop-residual-20261026/release-manifest.json). CSS `2fbba70fa95d035aecd19a0fd9a2e7e3e00c5f6b789cf3fe0c3eed5cbef5cfab`, 불변 mediaJS `65e2468ec5ac6f53310383f2ec0939aa2adb4793e47da5dcca7b0f20b861e328`.

---

# 방법론 적합성 표 — 2026-10-26 V1–V4 검증 보강

기존 채택/조건부/제외 결정과 공개 출처는 유지합니다. 이번 갱신은 새 방법론 도입이 아니라 고정된 과업에 대한 실제 검증 추가입니다. 아래 기존 표의 과거 미검증 문구는 당시 기록이며, 현재 검증은 이 절과 새 보고서를 우선합니다.

| 방법·fit | Loretune 과업/결정 | 구현 연결 | 이번 검증 | 불확실성 |
|---|---|---|---|---|
|과업 분석·분할 공간 / 채택|영상·시간축·검토 맥락을 유지하며 상세만 내부scroll|bounded shell/transport V1|1920 정밀505×284,문서1080;35Tab 가시|1280영상218×123의절충. 실제작업속도시험없음|
|객체정체성·recognition / 채택|편집선택과재생장면을역할로명명|V4/B1|편집01·재생02·hash불변|고객인지시간미측정|
|위험기반점진공개 / 채택|기술검증은닫힌상세;모델·비용·승인안내는보존|V2/V3|진단숨김/Enter공개,미선택/차단/긴이름/승인별도|모든plancommit/공급자오류UI는이번표본밖|
|실패계획·상태전이 / 채택|400거절≠unknown,기존조회·초안보존|scopedreview/F1/F3|controlled POST4·GET4 모두가로챔,장면전환·새초안race보존|실제서버장애·DBcommit·청구아님;연결복구문구개선여지|
|semantic role·대비 / 채택|오류는문자+면+경계,선택/focus/승인분리|기존tokens보존|오류실제opacity1쌍9.325:1|nativeoverlay/forcedcolors전체미검증|
|키보드·resize / 채택|정상Tab진입과복귀,큰문자reflow|H3/G2|초기keyboard여정완료;앱200%=28px/문서2505|실제browserzoom/스크린리더/사용자시험없음|

새점수81.0은7축26항목전문가판단이며구방법론의5축90점과비교하지않습니다.26항목평가가능과전체상태통과를구분합니다.H1/H2는U,H3/H4는범위한정PASS입니다. Blender직접자료읽기402는여전히제약이며직접성공으로수정하지않습니다.

상세: [V1–V4 독립 재검토](desktop1920/refinement-recheck/REPORT-ko.md), [점수표](desktop1920/refinement-recheck/scorecard.json), [최신 사용자 요약](Loretune-Design-Update-20261026-ko.md).

---

## 기존 방법론 선택과 출처 — 역사적 검증 문구는 해당 시점 기준

# 방법론 적합성·채택·검증 추적표

2026-10-26. 하나의 프레임워크를 전면 도입하지 않고 Loretune의 음악영상 제작 과업에 맞는 부분만 사용한다. **채택은 설계 검토 방법을 사용한다는 뜻이며, 새 기능 구현이나 검증 완료를 뜻하지 않는다.** A=채택, C=조건부, X=이번 범위 제외. P=연구 담당이 제공한 요약/출처, D=이번 디자인 턴에서 직접 문서를 읽음. 실제 경쟁사 계정 조작은 없다.

## 과업·객체·상태·검토 방법

| 방법 / fit / 출처 | Loretune 과업과 설계 결정 | 구현·문서 연결 | 검증 방법 / 불확실성 |
|---|---|---|---|
| 작업 분석/HTA · A/P · [NN/g](https://www.nngroup.com/articles/task-analysis/) | ‘음악에 맞는 승인 영상 완성’을 계획→제작→비교/검토→편집→출력/재개와 실패 분기로 분해 | DS08/11/12, 아래 과업 지도, `#guidedPlans`, `.media-action-card`, timeline/output | 기존 합성 과업으로 경로 확인. 실제 사용자의 순서/빈도 관찰은 없으므로 빈도와 숙련도 가정은 가설 |
| 가벼운 OOUX · A/P · [A List Apart](https://alistapart.com/article/object-oriented-ux/) | Project/Track/Shot/Take/Asset/Review/Export의 대상·관계를 일관되게 표현. DB 용어 노출은 피함 | DS05, `#shotlist`, `#takes`, `#takeReviewStatus`, `#track`, output snapshot | 같은 객체가 패널을 이동해도 매칭되는지 확인. 아키텍처 전면 재작성/새 저장구조는 제외 |
| Cognitive walkthrough · A/P · [HCI handbook](https://hcibib.perlman.hosting.acm.org/tcuid/chap-4.html) | 초보자가 목표·조작·피드백을 연결할 수 있을지 단계별 질문 |7축B/F, 사용자용 문구와 contextual action | 전문가의 학습 가능성 가설. 실제 초보 성공률·시간 측정으로 부르지 않음 |
| Heuristic audit · A/P · [심각도](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/) | 영향·지속성·관찰된 재현으로 우선순위 결정 | 각 finding의 원인→영향→근거→수정→재검증 | 빈도는 실제 측정 없으면 가설. 동일 결함 중복 감점 금지 |
| 실제 task usability · C/P · [NN/g](https://www.nngroup.com/articles/usability-testing-101/) | 사람의 창작/복구 행동을 관찰해 현재 가설 보완 | 향후 사용자 연구; 현재 rubric의 한계 | 이번에는 사람 참가자 시험 없음. AI의 조작·평가는 사용자시험이 아님 |
| 위험 기반 점진적 공개 · A/D · [NN/g](https://www.nngroup.com/articles/progressive-disclosure/) | 자주 쓰는 기본 옵션 우선. 비용·권리·승인·실패는 결정시점에 보존 | DS08/11, `#creatorReviewRecord`, 제작 도구/출처 details, 승인카드 | ‘위험’까지 적용한 것은 우리 설계 판단. 모든 고급 옵션을 숨기거나 클릭 수만 줄이지 않음 |
| Recognition over recall · A/D · [NN/g](https://www.nngroup.com/articles/recognition-and-recall/) | 현재 장면/Take/버전/검토를 눈으로 매칭; 긴 상태 문단 반복 축소 | DS05/09, rail/Take/inspector/compare identity | 객체 일치/다른 상태 구분을 렌더로 확인. 단서 개수만 늘리는 접근 제외 |
| 상호작용 비용 · A/P · [NN/g](https://www.nngroup.com/articles/interaction-cost-definition/) | 클릭+탐색+기억+맥락 전환을 함께 고려 | workspace 인접성, 모델/계획/복구 문구 | 시선/시간 절약 수치는 실험 없으므로 주장하지 않음. 유료 승인 클릭 자체를 제거하지 않음 |
| 상태전이표 · A/P · [W3C SCXML](https://www.w3.org/TR/scxml/) | 생성/미디어/검토/저장/출력 상태를 독립 축으로 표현 | 아래 상태표, 기존 controllers/presentation fields | 형식적 참고일 뿐 SCXML 엔진 도입 없음. timeout≠실패, 재생가능≠승인, audition≠채택 확인 |
| 대표 콘텐츠 스트레스 · A/P · [심각도 기준](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/) | 긴 한국어, 많은 장면, 다른 aspect, 미디어 누락, 긴 오류, 혼합 검토 상태 |1920 S01–S08/DS02/08/09/14 | 기존 승인된 fixture만 사용. 없는 상태는U, 새 사용자 데이터/승인을 만들지 않음 |
| JTBD · C/P · [Christensen Institute](https://www.christenseninstitute.org/theory/jobs-to-be-done/) | 제작 목적이 불명확할 때 인터뷰로 동기 확인 | 향후 발견 단계 | 이번 명확한 과업에는 추가 인터뷰를 선행조건으로 삼지 않음. 패널 px의 근거로 쓰지 않음 |

## Human–AI 공동창작

| 방법 / fit / 출처 | Loretune 결정 | 구현·문서 연결 | 검증 / 한계 |
|---|---|---|---|
| HAX Workbook · A/P · [Microsoft](https://www.microsoft.com/en-us/haxtoolkit/workbook/) | 관련 지침만 UI/AI/server 요구에 연결 | DS08/11, model/plan/production presentation 계약 |18개 모두 의무 도입 아님. 선택·가용성·실행 결과의 표시를 검사 |
| Mental model / 적절한 신뢰 · A/P · [PAIR mental models](https://pair.withgoogle.com/guidebook-v2/chapter/mental-models/), [explainability](https://pair.withgoogle.com/guidebook-v2/chapter/explainability-trust/) | 계획 모델/생성 모델, AI 추천/서버 검증/사람 승인/실행을 분리. 대상·모델·비용·영향 중심 설명 | `#modelSettingsPanel`, `#modelSlots`, 계획카드, `.media-action-card` | 선택 모델이 unavailable이어도 유지. 미측정 성공 확률·모델 자기평가 노출 금지 |
| Mixed initiative / controls · A/P · [Horvitz](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/chi99horvitz.pdf), [PAIR controls](https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/) | 채팅 제안과 직접 편집 공존. 모호한 지시는 유료 실행 대신 제안/확인. 닫기·취소·실행중단 의미 분리 | chat→tool proposal→human approval, timeline numeric edit | 기존 권한/비용 계약 보존. Undo가 과금을 되돌린다는 암시 금지. 새 제어 기능 추가 요구 아님 |
| Creativity Support Tools · A/P · [Shneiderman](https://www.cs.umd.edu/~ben/papers/Shneiderman2007Creativity.pdf) | 대안 비교, 비파괴 원본, 기록·복귀 보존 | Take 비교, source trim, review history, saved snapshot | 비교 전후 canonical 선택/승인 불변. 자동 유료 후보 생성은 제외 |
| Failure planning · A/P · [HAX Playbook](https://www.microsoft.com/en-us/haxtoolkit/playbook/), [PAIR errors](https://pair.withgoogle.com/guidebook-v2/chapter/errors-failing/) | 실패 단계/유지된 결과/비용 상태/다음 행동을 구분. unknown은 기존 요청 조회 | existing-request recovery, scoped draft, `#productionReviewError` | 현재 허용된 mock/기존 상태로만 검증. 자연어 중심 Playbook이 영상 전체를 검증해 주지 않음 |
| COFI · C/P · [논문](https://arxiv.org/abs/2204.07666) | 기여 대상 Take/기여 종류/결정권 구분에 제한 적용 | proposal/Take/review identity | 음성·실시간 동시창작을 요구하거나 추가하지 않음 |
| CSI 설문 · C/P | 실제 사람의 창작 지원 경험을 나중에 확인하는 보조 도구 | 향후 연구만 | 현재 전문가 점수나90 주장에 사용하지 않음 |

## 색상·시각·작업 공간

| 방법 / fit / 출처 | Loretune 결정 | 구현·문서 연결 | 검증 / 한계 |
|---|---|---|---|
| 분할 작업 공간 · A/D+P · [Premiere](https://helpx.adobe.com/premiere/desktop/get-started/tour-the-workspace/customize-panels.html), [Blender](https://developer.blender.org/docs/features/interface/human_interface_guidelines/paradigms/) | no-page-scroll은 작업 맥락 유지 목표. 긴 상세는 패널 내부 | DS14, bounded shell, media/timeline dock | document+panel scroll, Tab 가시성. Blender 직접 fetch402라 제공 근거로만 표기. 모든 경쟁사 무스크롤 주장 없음 |
| Semantic tokens / 역할쌍 · A/D+P · [Spectrum](https://spectrum.adobe.com/foundations/design-data/design-tokens), [Material](https://developer.android.com/design/ui/mobile/guides/styles/color) | primitive→semantic→필요한 component alias. foreground/background 역할을 함께 정함 | `--ui-*`, token spec, state-style matrix | 실제 computed/대비 계산. Material 모바일 외형·동적 썸네일 테마 복제 제외 |
| 중성 canvas · A/P · [Spectrum color](https://spectrum.adobe.com/page/color-fundamentals/) | 기존 중성 팔레트의 영역·상태 역할 정리 | canvas/panel/raised, media/selection/focus | 현재 대비 충분한 쌍은 유지. 회색UI가 색보정 정확성을 보증하지 않음 |
| OKLCH · C/P · [CSS Color4](https://www.w3.org/TR/css-color-4/) | 새 역할색 조정이 필요할 때 지각적 조절 도구로 사용 | 향후 근거 있는 token 제안 | WCAG 대비 판정이나 Material HCT와 동일하지 않음. 현재 palette를 이유 없이 재생성하지 않음 |
| 중복 부호화 / forced colors · A/P · [CSS Color Adjust](https://www.w3.org/TR/css-color-adjust-1/) | 색+텍스트/기호/경계; shadow가 없어도 focus/선택 식별 | `:focus-visible`, `.lt-review-state`, forced-colors rules | 실제 emulation/설정 수행 여부를 기록. 코드 존재만으로 통과 아님 |
| Type role/CJK/time · A/P · [Spectrum typography](https://spectrum.adobe.com/foundations/typography/typography-system) | 제목·항목·본문·메타 구분, 한국어 wrap, 시간 tabular | DS02/04, `--ui-*` type, `#timeRuler` | 크기·weight·line-height·실제 줄바꿈. 특정 px를 공식 정답으로 쓰지 않음 |
| 사용자 text spacing · A/P · [W3C](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) | 사용자 간격 변경에도 내용/기능 보존 | CSS text/controls/layout | 문서 수치를 기본 UI line-height 강제로 해석하지 않음. 미실행이면U |
| 근접성/공통영역 · A/P · [proximity](https://www.nngroup.com/articles/gestalt-proximity/), [common region](https://www.nngroup.com/articles/common-region/) | 관련 제어를 간격/톤으로 묶고 박스 남발 축소 | review/production tools, timeline/control groups | 실제 시선 순서·간격·경계 역할 평가. 밝은 테두리 개수 자체가 품질 아님 |
| 기능적 motion · A/P · [Spectrum motion](https://spectrum.adobe.com/page/motion/) | 상태 변화를 설명하는 짧은 피드백만. reduced-motion에서 장식 제거 | `--ui-motion`, media/native controls, reduced-motion rules | 의도한 영상 재생은 유지. 화면이 정적이라는 이유만으로 reduced-motion 통과 아님 |
| Reflow/Resize · A/D · [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [resize](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) |2D 시간축 예외와 주변 설명/폼을 구분. 확대 접근 보존 | DS02/14, large-text fallback | 실제 앱 배율/브라우저 zoom 구분. 전체WCAG 인증 없음 |
|60–30–10 색비율·보라색AI·모든 CTA강조·전자상거래 전환 최적화 · X | 이 제작 과업에 직접 근거가 없으며 미디어/승인 맥락을 흐릴 수 있어 채택하지 않음 | 적용 없음 | 새색·강한 행동이 항상 금지라는 뜻은 아님. 구체 과업 필요가 있을 때만 새 제안 |

## 과업 지도: 관찰과 가설 분리

기본 흐름은 `음악/작품 확인 → 모델/계획 검토 → 사람 승인 → 실행 또는 기존 결과 확인 → Take 비교/검토 → 편집 시간 구성 → 출력 검토 → 저장본 재개`다. 이 순서는 현재 제품 계약과 합성 QA 흐름에 근거한다. 실제 창작자가 항상 이 순서로 작업한다는 관찰은 없다. 비교↔검토↔편집의 반복과 실패→기존 요청 조회/초안 복귀 분기를 보존한다.

현재1920 패스는 기존 자료의 보기·비교·임시 초안 취소·편집 상세 탐색을 실제 UI로 점검한다. 새 사람 승인/외부 실행/출력 생성은 기능팀 회귀 증거와 구분하며 디자인 감사에서 수행하지 않는다.

## 상태축을 섞지 않는 표시 계약

| 상태축 | 구분할 상태 | 사용자에게 필요한 내용 | 금지하는 축약 |
|---|---|---|---|
| 모델/생성 | 미선택 / 연결 미검증 / 차단 / 입력 준비 / 승인 필요 / 실행 중 / 결과 미확정 / 결과 확보 / 실패 | 현재 모델, 사용 가능 여부, commit시 비용·범위, 실제 다음 행동 | 미검증을 실패나 준비 완료로 표시, timeout 후 자동 재제출 |
| 미디어 | 없음 / 준비 중 / 재생 가능 / 일시정지 / 재생 / 끝 / 오류 | 대상·원본/편집 시간·재생 가능 상태 | 재생 가능=검토 승인, 숫자만 바뀐 seek=실제 frame 반영 |
| 검토 | 미검토 / 승인 / 수정 요청 / 거절 | scene+Take, 결과·이유, 필요한 수정 행동 | 현재 선택=승인, 승인 완료에도 강한 승인CTA 강제 |
| 편집 | 저장본 / 로컬 변경 / 승인된 snapshot / 변경안 | 원본trim·편집길이·저장 여부·승인 버전 | audition=편집 채택, 화면의 미확정 draft=출력 승인본 |
| 저장/복구 | dirty / saving / saved / 실패 / 결과 미확정 / 저장됨·갱신 실패 | 입력 보존, 확실한 결과와 다음 행동 | ‘닫기’=실행 취소, 기존 요청 조회=새 요청 |
| 출력 | 준비 / 승인 필요 / 실행 / 결과 / 실패·미확정 / 납품 검토 | 승인된 입력 버전, 음원·자막 관계, 실제 결과 | Take 승인=출력 승인, Undo=과금 취소 |

이 표는 기존 계약의 표시·검토 방법이다. 새 backend 상태나 라이브러리를 추가하는 요구가 아니다. 검증 시 해당 상태가 없으면 미검증으로 남기며 더 많은 상태를 찍기 위해 실제 사용자 데이터를 변경하지 않는다.


## 2026-10-26 최종 shell 검증 연결

위 표의 baseline·pending은 작성 당시 상태를 보존합니다. 이후 HTML202ea641…850c5/CSS8274aacf…69a3e9 고정본에서 독립1920 화면 검토를 완료했습니다. [최종 상세 보고서](desktop1920/final-audit/REPORT-ko.md)에 실제 관찰과 미검증을 분리했습니다.

| 방법 적용 | 이번 직접 확인 | 한계 |
|---|---|---|
| 분할 작업 공간·맥락 유지 | 기본/sequence/정밀/긴패널/출력의 문서1080px; 상세34개Tab·패널끝 접근 | 실제60장면 저장 프로젝트의 성능 시험은 아님 |
| 인지 단서·점진적 공개 | 선택·승인·출력버전, 모델미선택, 검토수정과 초안취소 | 반려/실제저장오류·신규가격commit은 미검증 |
| semantic tokens·타입 | 실제배경쌍 대비·20/14/12px 역할·선택/focus구분 | 모든nativeoverlay·forced-colors는 미검증 |
| 시간축·비파괴 비교 | 1/2/4초 비례,공통원점,trim비교,작품지문불변 | 로딩경계는별도코드근거,브라우저장기sync미검증 |
| 접근성 재배치·motion | 앱150/200%와1280,CDPreduced-motion | 실제browser200/400%·screenreader미검증 |

확인 가능한98배점 중74.3점이며 전체확정점수는 보류했습니다. 이는 방법론의효과를 실제사용자실험으로입증했다는 뜻이 아닙니다. 사전고정7축/26항목/4gate를 유지했고 경쟁사 순위를 만들지 않았습니다.
# 2026-10-26 추가 상태 — 프런트엔드 QA 기준·실행

기존 방법론·이전 점수 이력을 유지한다. 최신 [시각/CSS/키보드 QA](frontend-qa-inventory-20261026/REPORT-ko.md)는 실행 전 22개 기준과 10개 시각 영역을 별도로 고정했다. 새 합산 점수 없이 계약 위반·시각 과업 가설·미검증·표본 통과를 분리했다. 1920×1080 주,1280×900 보조, 모바일 보류다.

적용: 사용자 역할/이름 중심 조작, 실제 computed 스타일·font 확인, 같은환경 screenshot 조건, 표준과 제품 목표 구분, 초안취소·focus복귀 관측. 조건부: DOM-only 긴문구/오류 표시는 presentation coverage만 제공하며 실제 backend 실패를 대신하지 않는다. 제외: snapshot동일함을 미감점수로 바꾸기, VM pass를 실제decode로 바꾸기, 실제 확대가 안 된 상태를200%zoom으로 부르기.

실행 결과 15 PASS / 2 FAIL / 2 BLOCKED / 3 NOT RUN. VF01 확대 Take 포커스와 VF02 긴 연속 제목을 별도 보고했다. actual browser200/400 및axe는 BLOCKED, screenreader/customerstudy/cross-engine은 미실행이다. [결과표](frontend-qa-inventory-20261026/RESULTS.json), [불변성](frontend-qa-inventory-20261026/evidence/end.json). 이 로컬 추가문은 기존 Library version3에 자동 반영되었다는 뜻이 아니다.

