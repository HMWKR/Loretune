# 1920×1080 디자인 검토 — 기준 고정 및 수정 전 판단

2026-10-26. **현재 결과는 최종 채점 전 체크포인트다.** 기본 화면의 핵심 조작은 한 화면에 들어오지만, 실제 영상에 할당된 면적이 작고 정밀 편집을 펼칠 때 문서가 길어진다. 새 no-page-scroll shell은 기능 담당이 구현 중이다. 최종 점수는 그 고정본의 실제 렌더와 상태 시험 뒤에 작성한다. 점수를 먼저 정하거나 미검증을 성공으로 채우지 않는다.

이 문서는 1920×1080 **브라우저 content viewport/CSS px**를 다룬다. 모니터 물리 해상도와 구분한다. 앱 문자배율100%, 제공 캡처 DPR1이다. 모바일 추가 작업은 보류했고 1280×900은 보조 회귀다.

## 먼저 확인된 세 가지

1. **미디어 무대와 실제 영상의 비율이 불균형하다.** stage는1376×300px, 16:9 영상은 약533×300px다. 실제 영상 면적은 stage의38.76%, viewport의7.72%다. 매우 넓어진 중앙 칸이 실제 영상을 크게 보여주는 데 쓰이지 못한다. 단, 단색/테스트 패턴의 품질을 디자인 감점으로 삼지 않는다.
2. **기본 화면 무스크롤과 작업 전체 무스크롤은 다르다.** 기능팀의 기존 상태 측정은 기본·sequence에서 문서1080/1080이지만, 정밀 편집 펼침은1710/1080이다. 새 사용자 요구에 따르면 후자는 재배치 대상이다. 단순히 document overflow를 숨기면 통과가 아니다.
3. **상태 언어와 중성 토큰은 보존할 가치가 있다.** rail/Take의 실제 썸네일, 선택과 승인 구분, 차분한 승인 결과+‘검토 수정’, 테스트 미디어 표시, 시간 비례1/2/4초는 읽을 수 있다. 이 부분을 새 테마나 과한 CTA로 다시 쓰지 않는다. 기능팀이 고친 저장/초안/미디어 결함을 재발 근거 없이 새 결함으로 계산하지 않는다.

## 이 판단에 사용한 증거

| 증거 | 조건 / 출처 | 이번 검토에서 한 일 |
|---|---|---|
| [실제 1920 화면](../../design-media-fixes-20261026/final-desktop-1920.png) | 기능팀이2026-10-26T01:21:37Z에 저장. 작품 ‘디자인 시스템 기능 QA 20261026’, 장면01/Take1, 선택 Take, 합성320×180 영상, readyState4 | 저장 파일을 직접 열어 의도한 화면·텍스트·여백·미디어 표시 확인. 독립 재캡처라고 주장하지 않음 |
| [computed 측정](../../design-media-fixes-20261026/desktop-1920-computed.json) | HTML846e18…, CSS f6f9ebff…dd58, JS ae019c88…982e | 제공된 값에서 실제 contain 면적을 계산. 독립 DOM 추출값과 구분 |
| [기본/sequence/펼침 치수](../../desktop-shell-20261026/before-measurements.json) | 같은 수정 전 CSS의 기능팀 측정 | 상태별 문서 높이와 timeline/transport 위치를 비교 |
| [미디어 독립 재검증](../../independent-design-media-recheck-20261026/REPORT.md) | Node VM 반례·근접 control8/8, 관련 unittest12 | DM01–03 종료 근거로 읽음. 실제 브라우저 장시간 동기까지 통과로 확대하지 않음 |
| [이번 파생 계산](baseline1920-analysis.json) | 위 제공 치수에서 산출 | stage/content 면적, 가설별 공간 예산을 명시 |

분류: 제공자 측정은S, 이번 저장 픽셀 관찰은O, 이번 산술은제공 측정의 파생값, 제안은P다. 최종 새 shell의 직접DOM/키보드 증거는 아직U다.

## 실제 구성과 해석

| 영역 | 제공된1920 실측 | 판단 |
|---|---:|---|
| 상단 shell + 단계 |56+48=104px| 작품/설정과4단계가 분리돼 있다. 중복 안내가 늘어난 예전 화면을 현재 결함으로 가져오지 않는다 |
| rail / inspector |184 /288px| 기본 장면과 짧은 검토를 담는다. 폭 숫자만으로 좁다/좋다 판정하지 않음. 긴 한국어·모델명·오류는 새 고정본에서 확인 |
| 중앙 폭 / 열 간격 |1376 /16px| 큰 모니터 공간이 주로 중앙 가로폭으로 이동. 읽는 메모는 inspector 안에 있어 무제한 긴 행이 되지 않음 |
| preview |x220,y206,1376×300| 높이 상한이300px라 영상은533×300. 실제 영상 면적보다 검정 무대가 큼 |
| Takes / 비교 |y564–642 /583–623| 실제 thumbnail·선택·승인이 가까이 있고 비교 버튼 접근 가능. 객체 식별은 개선된 상태 |
| timeline / 정밀 편집 진입 |y658–944 /895–931| 기본 상태에서는 모두 첫 화면에 보임 |
| sequence transport |높이약134px, timeline하단1044| 같은 화면 안이지만 높이 여유가 거의 사라짐. 영상 높이만 늘리면 다시 밀릴 가능성 |
| 정밀 편집 펼침 |문서1710px /viewport1080px| 세부 입력 때문에 전체 작업 맥락이 내려감. 새 bounded-shell 요구의 명확한 개선 대상 |

가로 영상의 contain 면적 산식은 `W=min(stageW, stageH×16/9); H=W÷(16/9)`다. 여기서는533.33×300≈160,000px²이다. border/브라우저 native controls overlay를 제외한 근사치이며 perceptual 품질 척도가 아니다. portrait의 정상 여백은 이 결함과 구분한다.

## 구성 수정의 이유와 두 가지 가설

원인은 현재 preview의 `clamp(220px,28vh,300px)` 상한과 유동 중앙 폭의 조합이다. 넓은 화면에서 stage만 길어지므로 영상 세부를 확인할 때 공간 이득이 제한된다. 사용자가 느끼는 시간 손실은 실제 사람으로 측정하지 않았으므로 수치로 주장하지 않는다.

**미디어 높이만 키우는 방법은 충분하지 않다.** 선택 모드보다 sequence 모드의 transport가 약100px 더 높다. 펼친 상세는 더 커진다. 따라서 상단 문맥·transport·Take행·timeline의 전체 예산을 먼저 맞춰야 한다.

다음 두 예시는 경쟁사 실측이나 공식 정답이 아니라 새 구현을 판단할 Loretune 가설이다. 모든 치수는 글자 크기·컨트롤 접근성을 유지할 때만 유효하다.

| 가설 | 예산 합계 | 실제16:9 영상 | 장단점 |
|---|---:|---:|---|
| A: chrome104 + main여백32 + 문맥56 + preview350 + transport64 + Take64 + gap24 + timeline286 |1080px|약622×350, 기존 대비면적+36.1%| 현재 timeline 높이에 가까워 보수적. transport/문맥 재배치가 필요 |
| B: 동일 구성에서 preview400, timeline230 |1074px|약711×400, 기존 대비면적+77.8%| 미디어 이득이 크지만 timeline은 label/파형/주요제어가230px에 실제로 읽히는지 확인해야 함 |

하단 상세 폼은 timeline 패널 내부에서 스크롤하고 요약·현재시간·transport는 남기는 방향이다. 주요 제어를 숨기거나 텍스트를 줄여 예산을 맞추지 않는다. 새 기능팀 구현이 다른 치수로 같은 과업을 더 잘 충족하면 그 구현을 평가한다. 제안 수치를 맞추는 것이 목표가 아니다.

## 토큰과 형태: 무엇이 정확한 값이고 무엇이 판단인가

아래는 이전 고정1920의 computed custom-property/실제 요소 기록이다. [전체 토큰CSV](baseline1920-tokens.csv)는 제공 JSON의 값과 캡처시각을 보존한다. 새 shell의 코드가 이미 달라졌을 수 있으므로 이것을 새 최종 전체 스타일이라고 표시하지 않는다.

| 역할 | 현재 baseline 값 | 해석과 검증 과제 |
|---|---|---|
| 기본면 / 패널 / raised / hover |`#101010` / `#1B1B1B` / `#242424` / `#303030`| 중성 미디어 중심. 차이가 작다는 이유만으로 문제는 아님; 구조·텍스트·필수경계와 함께 구분되는지 확인 |
| 강한 글자 / 본문 / 보조 |`#F4F4F2` / `#DEDEDB` / `#BDBDBB`| supporting text를 지나치게 흐리게 만들지 않는 방향. 실제 weight/spacing과 함께 위계 판단 |
| 선택 면 / 선택 경계 / marker |`#2A2A28` / `#EEEEEE` / `#D8D8D2`| 선택 표시와 승인 문구를 분리. 모든 승인 객체에 강한 프레임을 넣지 않음 |
| 장식선 / 필수 제어 경계 |`#383838` / `#858585`| 같은 테두리 역할이 아님. 장식선의 낮은 대비를 모든 입력 경계 실패로 계산하지 않음 |
| focus / 오류 / 오류면 / 경고 |`#E4DDBE` / `#FFB49D` / `#28201E` / `#E6C58B`| focus는 dashed outline, 검토는 symbol+text. 색만으로 구분되지 않는지 실제 상태에서 확인 |
| primary / on-primary |`#F4F4F2` / `#101010`| 필요할 때의 결정 행동용. 승인 완료 카드에 무조건 밝은 버튼을 추가하지 않음 |
| type |meta12, item13, body14, section16, context18, title20, display24px;400/500/600| 1920이라고 모든 글자를 비례 확대하지 않음. 제목/본문/metadata의 실제 읽기 위계를 검토 |
| 실제 행간 |body14/21, 비교13/18.85, 검토버튼14/20.3; 메모의 별도1.7 선언| token body1.45와 base1.5의 차이는 존재. 역할상 의도인지 불필요한 잔재인지 확인하며 선언 차이만으로 가독성 결함을 만들지 않음 |
| spacing / radius |4/8/12/16/24/32px; clip4/control6/panel8/dialog12px| 실제 gap16, timeline padding12, Take gap8. 예외값은 용도와 실제 영향으로 판단 |
| motion |120ms, `cubic-bezier(.2,0,0,1)`| reduced-motion 선언 존재와 실제 preference 시험은 구분 |

주요 선언 위치는 `studio.css:root`(색상6–29, spacing30–35, radius36–39, 타입41–53, motion54–55), `body`65, `#creatorSavedReason`691, 비교stage729–730, focus758–759, 시간축774–788이다. 이는 이번 읽기 시점의 위치이며 새 freeze에서는 줄 번호/해시를 다시 확인한다. cascade가 있는 것은 곧바로 오류가 아니다. 최종 computed와 충돌하는지·동일 의미를 바꾸는지가 문제다.

### 지정 색상쌍의 대비

| 전경 / 배경 | 대비 | 범위 |
|---|---:|---|
| strong / panel |15.641:1| 일반 글자에 충분한 지정쌍 |
| body / panel |12.777:1| 일반 글자에 충분한 지정쌍 |
| muted / panel |9.154:1| 보조 글자에 충분한 지정쌍 |
| control / panel; control / hover |4.668:1;3.577:1| 필수 비문자 경계3:1 목표에 대한 지정쌍 |
| focus / panel |12.619:1| focus가 실제 인접면에서 보이는지도 확인 필요 |
| error / error-bg |9.325:1| 오류 지정쌍 |
| decorative line / panel |1.469:1| 장식선 전용. 필수 식별 경계로 쓰이면 별도 문제 |

값은 sRGB 불투명 지정쌍에 대한 기능팀 계산이다. 모든 hover/disabled, 영상 위 native controls, 투명 합성까지 시험한 것이 아니다. 따라서 H4 전체PASS나 WCAG 인증으로 표시하지 않는다.

## 방법론과 경쟁사 근거를 적용하는 방식

[방법론 적합성 표](../METHODOLOGY-FIT-MATRIX-ko.md)에는 채택·조건부·제외와 불확실성을, [전체 결정 추적표](METHODOLOGY-AND-DECISION-LEDGER-ko.md)에14개 과업을 구현 위치와 검증에 연결했다. 핵심은 분할 작업영역으로 맥락을 유지하고, 기본·상세를 나누되 중요한 결정 사실을 보존하며, 현재 객체/버전을 인지할 단서를 남기는 것이다. [Premiere 패널 문서](https://helpx.adobe.com/premiere/desktop/get-started/tour-the-workspace/customize-panels.html), [Spectrum 토큰 방법론](https://spectrum.adobe.com/foundations/design-data/design-tokens), [NN/g 점진적 공개](https://www.nngroup.com/articles/progressive-disclosure/), [인지 단서](https://www.nngroup.com/articles/recognition-and-recall/)가 각각 이 판단을 뒷받침한다.

Descript/Frame.io/Runway/Neural Frames는 서로 다른 기능의 참고다. 원본 해상도·촬영 시점·내용이 달라1920 동일 조건 비교가 아니며 경쟁사 점수는 만들지 않는다. 확대 시 일반 설명·폼은 보존해야 하므로 편집기라는 이유로 전체 reflow를 면제하지 않는다. [W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html).

## 점수와 필수 gate: 아직 채점하지 않은 이유

[사전 기준v1.0](RUBRIC-v1-ko.md)과 [새 사용자 요구v1.1](RUBRIC-v1.1-ADDENDUM-ko.md)을 hash로 고정했다. 7축은20/15/15/15/15/10/10, 세부26항목 합100이다. 각 항목0–4 앵커를 배점에 적용한다. 미검증은null이며, 확인 배점이100 미만이면 전체 확정 점수를 보류한다. 과거5축90점과 환산하지 않는다.

현재 새 shell의 최종 채점 coverage는0/100이다. 이는 디자인이0점이라는 뜻이 아니라 **평가 대상 고정본의 직접 확인을 아직 시작하지 않았다는 뜻**이다. 위 baseline 판단은 새 결과 점수로 전용하지 않는다.

| Gate | 현재 최종본 판정 | 필요한 증거 |
|---|---|---|
| H1 media/seek/sync |UNVERIFIED| DM01–03 코드검증은 종료. 실제 새 shell의 표본 재생·seek·비교 전환 확인 필요 |
| H2 승인/비용/버전 |UNVERIFIED| 새 승인·생성 없이 기존 fixture 비교 전후와 저장된 계획 표시 검증 |
| H3 핵심 keyboard |UNVERIFIED| 내부 scroll된 마지막 제어·검토 초안 취소·dialog 닫기/복귀까지 정상Tab 경로 |
| H4 필수 대비 |UNVERIFIED| 새 적용 상태의 FG/BG·focus·오류·선택 단서 확인. 지정 색상쌍만으로 전체 통과 불가 |

## 재검증할 순서

1. 기능팀의 bounded-shell 최종 HTML/CSS/JS source·served hash를 대조한다.
2. 같은 작품/장면/Take에서 기본·sequence·펼침·긴 패널·출력 확인의1920 캡처와 scroll/panel rect를 기록한다.
3. transport와 실제 frame, ruler/clip/wave/playhead 좌표, mixed-aspect comparison, 저장하지 않는 draft/cancel을 확인한다.
4. 키보드·focus·앱150/200%와1280 회귀를 수행한다. 실제 browser zoom이 확인되지 않으면 미검증으로 남긴다.
5. 새 화면별로 token/computed/style·차단 상태를 기록하고 gate→coverage→항목별 점수와 이유를 제시한다. 남은 결함은 원인→영향→근거→최소 수정→동일 과업 재검증으로 연결한다.

앱 코드·서버·DB·경쟁사 계정은 변경하지 않았다. 이번 작성은 별도 QA 경로뿐이다. 현재 의존성은 기능팀의 새 freeze이고, 실행 권한 거절은 없다. 공식 Blender 문서 재조회만 웹 도구402로 실패했으며 다른 자료 읽기와 문서화는 완료했다. 이 체크포인트에는 새 Library 업로드를 시도하지 않았다.
