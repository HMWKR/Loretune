# Loretune 현행 디자인 시스템 감사 · 2026-10-26

현재 화면에는 일관된 어두운 편집 작업대, 의미가 구분된 선택·검토 상태, 충분한 주요 문자 대비가 있습니다. 그러나 **전체 디자인 시스템이 단일 토큰 체계로 완성됐다고 보기는 어렵습니다.** 후속 스타일이 누적됐고, 간격 토큰은 선언만 있으며, 앱의 글자 크기 설정을 일부 고정 px 스타일이 따르지 않습니다. 기존 90점은 제한된 화면의 전문가 휴리스틱 평가로 보존하되, 토큰 시스템 완성도·실사용자 검증·경쟁사 동등성의 증거로 확대하지 않습니다.

## 범위와 근거 상태

- 현행 `index.html` SHA256: `a59b8c494770d23000973c1c1b702c39d8fcb955e38ed04f045ccc4c94373c1b`. 전달받은 최종 B와 일치합니다.
- 앱 코드는 읽기 전용으로 검사했습니다. DB·서버·설정·경쟁사 계정·비밀 파일은 변경하거나 열지 않았습니다. 이 디렉터리에 감사 산출물만 작성했습니다.
- **소스 확인:** 현재 8개 inline `<style>` 블록, 관련 DOM 및 표시 함수. QA 디렉터리의 과거 독립 CSS 후보를 현재 적용 CSS로 취급하지 않았습니다.
- **실제 이미지 확인:** [최종 B 데스크톱](../final-delivery-20261025/final-desktop.png), [모바일](../final-delivery-20261025/final-mobile.png), [모바일 출처 펼침](../final-delivery-20261025/final-mobile-disclosure.png)을 저장 파일에서 열어 확인했습니다. 각각 1280×900, 390×844, 390×844입니다. 촬영은 2026-10-25 17:30 UTC이며 오늘 새 캡처가 아닙니다. 이미지별 해시는 기존 [manifest](../final-delivery-20261025/capture-manifest.json)에 있습니다.
- **실시간 접근 실패:** 별도 ego-browser 검증 공간에서 `http://127.0.0.1:8773`의 `page.goto`가 `net::ERR_CONNECTION_REFUSED`로 종료됐습니다. 서버 재시작·대체 listener·다른 경로 재시도는 하지 않았습니다. 현재 served hash와 새 computed style·focus·hover 동작은 미확인입니다. 자동 승인 거절이 아니라 로컬 연결 실패입니다. Ego Lite 업데이트 알림만 관찰했으며 업데이트하지 않았습니다.
- 이하 값은 **현재 소스의 선언 및 명확한 cascade 근거**입니다. 픽셀 관찰·계산·제안을 구분합니다. 실제 브라우저 computed-style 재측정으로 표기하지 않습니다.

## 1. 정확한 색상과 역할

색상 이름 하나가 모든 화면을 지배하지 않습니다. `--lt-*` 기반 위에 `--craft-*`, `--creator-*`, `--finish-*`가 적용됩니다. 예를 들어 `--lt-text`는 `#F5F5F5`로 남아 있지만 작업대 기본 글자는 `--craft-text`의 `#F4F4F2`, 검토 메모는 `--finish-body`의 `#DEDEDB`입니다.

| 역할 | 현행 HEX / 적용 위치 | 정확한 근거 |
|---|---|---|
| 작업대 바탕 | `#101010` | `--lt-canvas`, `--craft-canvas`; [index.html:63](/Users/leesungmin/Desktop/Loretune/index.html:63), [339](/Users/leesungmin/Desktop/Loretune/index.html:339) |
| 기본 패널·dialog | `#171717` | `--lt-surface`; `.lt-system dialog`, 63·123행 |
| 검토 inspector | `#1B1B1B` | `--creator-surface`, `.lt-creator main>.inspector`; [494](/Users/leesungmin/Desktop/Loretune/index.html:494), 503행 |
| 타임라인 패널 | `#191919` | `.lt-craft .timeline`; [377](/Users/leesungmin/Desktop/Loretune/index.html:377) |
| 입력·모델 내부 영역 / shell | `#141414` | `--craft-input`, `.lt-craft .lt-studio-shell`, `.production-models`; 339·346·349·613행 |
| 모바일 현재 맥락 / 단계 chrome | `#151515` | `--lt-chrome`, `#creatorMobileContext`; 179·541행 |
| 미디어 stage | preview `#050505`, 비교 `#080808` | `--lt-media`, `.comparison-media-stage`; 64·631행 |
| 기본 주요 글자 | 작업대 `#F4F4F2`, 기반 `#F5F5F5` | `--craft-text`, `--lt-text`; 341·344 / 64행 |
| 검토 메모·일부 본문 | `#DEDEDB` | `--finish-body`, `#creatorSavedReason`, `.media-action-card p`; [569](/Users/leesungmin/Desktop/Loretune/index.html:569), 593·627행 |
| 보조 글자 | 최종 `#BDBDBB`; 남은 역할 `#C1C1BE`, `#B5B5B5` | `--finish-meta`, `--creator-muted`; 기존 craft-secondary / lt-text-secondary; 569·494·341·64행 |
| 주요 실행 | 검토 저장 `#F4F4F2` / 글자 `#101010`; 기반 primary `#F5F5F5` / `#101010` | [596](/Users/leesungmin/Desktop/Loretune/index.html:596), 66·84행 |
| 보조 버튼 | 기본 `#252525`; 검토 수정 `#242424` | 350·595행 |
| 일반 hover / pressed | `#333333` / `#3D3D3D` | 351·352행. 장면·Take는 별도 hover `#222222` / `#242424`(585·588행) |
| 현재 선택 | 장면·Take·timeline `#2A2A28`, 왼쪽 표시 `#D8D8D2` | `--finish-selected`, 586·589·591행 |
| 현재 단계 / 모바일 탭 | 단계 `#292929` + `#EEEEEE` 밑줄, 모바일 탭 `#303030` + `#EEEEEE` | 357 / 310행. 객체 선택과 다른 역할 |
| 승인 / 대기 | 승인 `#DEDEDB`, 대기 `#BDBDBB` + 상태 단어·기호 | 578·579행, `studioBadge` [743](/Users/leesungmin/Desktop/Loretune/index.html:743) |
| 오류·거절·수정 요청 | `#FFB49D`; 검토 오류 바탕 `#28201E` | 580·600·619행; `--lt-danger` 67행 |
| 주의 색상 | `#E6C58B` | `--lt-warning`, `.lt-status[data-state="review"]`; 67·128행. 모든 pending UI에 적용된다는 뜻은 아님 |
| focus | 기본 후속 규칙 `#E4DDBE`, 2px dashed / offset 3px | 569·592행. **출처 summary는 더 구체적인 12행 규칙으로 `currentColor`(이 영역 `#BDBDBB`) solid 2px** |
| 입력 테두리 / 보조 실행 테두리 | 입력 `#707070`; 검토 수정·제작 선택 `#777777` | 349 / 595·621행 |
| 수동·비활성 그룹 선 | `#383838`, 타임라인 `#363636`, Take `#484848` | 503·601 / 377 / 587행 |
| 비활성 | 일반 글자 `#858585` / 바탕 `#222222` / 선 `#444444`; 검토 저장 `#A6A6A3` / `#292929` / `#555555` | `!important` 규칙 353 / 598행 |
| 테스트 표시 | 글자 `#D5D5D1`, 바탕 `#242424`, dashed 선 `#797977` | `.creator-test-badge`; 507행 |

**판단:** 흰 동작, 따뜻한 focus, 살구색 오류, 중성 승인이라는 역할은 합리적입니다. 승인을 초록색으로 바꾸거나 승인 완료 화면에 강한 실행 CTA를 추가할 필요는 없습니다. 선택은 면·왼쪽 표시, 승인 여부는 기호·단어로 분리됩니다. 단색 파랑 fixture 자체는 브랜드 팔레트가 아니며 평가하지 않았습니다.

## 2. 실제 사용되는 쌍의 대비 계산

현재 selector가 사용하는 불투명 전경/배경 쌍에 sRGB 상대 휘도 공식을 적용했습니다. 선언값 기준 계산이며 문자 안티앨리어싱 픽셀을 대비값으로 사용하지 않았습니다. 일반 문자 4.5:1, 필요한 비문자 식별 단서 3:1은 참고 기준입니다. 비활성 요소와 장식 경계는 같은 기준으로 일괄 실패 판정하지 않습니다. [W3C 문자 대비 설명](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [W3C 비문자 대비 설명](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

| 실제 역할 | 전경 / 배경 | 계산 대비 | 해석 |
|---|---|---:|---|
| 검토 메모 | `#DEDEDB / #1B1B1B` | 12.78:1 | 주요 본문 충분 |
| 보조문자 | `#BDBDBB / #1B1B1B` | 9.15:1 | 충분; 작은 글자 크기 문제와는 별도 |
| 선택 Take의 보조문자 | `#BDBDBB / #2A2A28` | 7.64:1 | 충분 |
| 검토 수정 | `#F4F4F2 / #242424` | 14.10:1 | 승인 완료 상태의 보조 행동으로 적절 |
| 활성 검토 저장 | `#101010 / #F4F4F2` | 17.28:1 | 활성/비활성 구분 근거 존재 |
| 검토 오류 | `#FFB49D / #28201E` | 9.32:1 | 오류 텍스트 충분 |
| 테스트 배지 | `#D5D5D1 / #242424` | 10.55:1 | 테스트 구분 유지 |
| 입력 경계 | `#707070 / #141414`(안), `#1B1B1B`(밖) | 3.72 / 3.48:1 | 표본 입력 경계 충분 |
| 검토 수정 경계 | `#777777 / #242424` | 3.47:1 | 충분 |
| 일반 버튼 경계 | `#555555 / #252525`(안), `#1B1B1B`(밖) | 2.06 / 2.31:1 | 약한 경계. 읽을 수 있는 버튼 문구로 식별되는 경우라 **자동 WCAG 실패 아님** |
| 선택 표시 | `#D8D8D2 / #2A2A28` | 10.05:1 | 면 색 차이만으로 선택을 전달하지 않음 |
| 기본 focus | `#E4DDBE / #141414` | 13.50:1 | 충분한 색 대비; 전체 focus 여정은 미검증 |
| 출처 focus | `#BDBDBB / #1B1B1B` | 9.15:1 | 대비 문제는 아니나 스타일 체계와 예외 존재 |
| 그룹 분리선 | `#383838 / #1B1B1B` | 1.47:1 | 장식·그룹 경계. 모든 divider를 3:1로 올릴 이유 없음 |
| 비활성 일반 / 검토 저장 | `#858585 / #222222`, `#A6A6A3 / #292929` | 4.31 / 5.96:1 | 비활성 예외; 일반 문자 불합격으로 계산하지 않음 |

전체 원값과 출처는 [contrast.json](contrast.json)에 있습니다. hover·겹침·동영상 자막·모든 dialog·OS native 미디어 제어까지 전체 검사한 것이 아니므로 접근성 인증이 아닙니다.

## 3. 타이포그래피·간격·표면·컴포넌트

| 범주 | 현재 근거 | 판단 / 남은 한계 |
|---|---|---|
| 글꼴 | `system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif`(71행) | 한국어 fallback 명시. 웹폰트 설치·실제로 선택된 글꼴은 오늘 측정하지 않음 |
| 크기 | 기반 12/14/16/20×text-scale(72–75행); 후속 UI 12/13/14/18/20px(342·365·451–474·504·513행) | desktop 장면 제목20, 검토 제목18, 본문14, item13, metadata12의 계층. 일부 dialog에는 기반 scale이 남음 |
| 굵기 | finish 의도는 400 본문, 500 객체/동작, 600 제목(570–575행). 개별 규칙에는 650(타임라인 heading, inspector summary), logo750도 존재(347·378·385행) | 표본에서는 제목/메모/보조정보 차이가 보임. 단일 3-weight 시스템으로 완전히 정규화됐다고 말할 수는 없음 |
| 행간·한국어 | 본문1.5–1.6, 메모1.7; keep-all + overflow-wrap(476·504·513·593·612행) | 최종 B 긴 장면명·검토 메모가 폭 안에서 읽힘. 모든 사용자 문자열/언어 검증은 아님 |
| 간격 | 4/8/12/16/24/32 토큰 선언(68–69행); **`var(--lt-space-*)` 참조 0회**. 실제 padding/gap은 리터럴 | 규칙적인 간격이 화면에 있어도 토큰으로 관리되는 것은 아님. 3/5/6/7/10/14px의 광학·밀도 보정은 무조건 오류가 아님 |
| 구조 | desktop rail184 / inspector288 / gap16, 901–1150에서는148/260/12(178–185·288–290행) | 3열의 역할이 분리됨. 900px 이하에는 장면/미리보기/검토 전환으로 한 과업씩 노출 |
| radius | 선언 4/8/12; 실제 chip4, media/scene6, controls8, preview/inspector12. track5 및 일부10/16도 남음 | 전부 같은 radius일 필요는 없음. 5/6·10/12 차이를 역할 표로 정리하면 변경 실수 감소 |
| border / shadow | 대부분1px, 선택 inset2px, focus2px. dialog `0 16px 48px #0006`; 상태 popover `0 12px 36px #0008`(123·497행) | 패시브 면은 조용하게, 실행·focus는 강하게 구성. 모든 검정 패널을 강한 선으로 둘러싸던 이전 문제를 현재 결함으로 반복하지 않음 |
| 버튼·입력 | desktop 대체로40–42px; 모바일 주요 조작44px(82·389·431·649행), 라벨 유지 | 동작·상태 의미를 읽을 수 있음. 전체 터치타깃 실측은 현재 runtime 부재로 미확인 |
| 아이콘 | 승인✓/대기○/거절×/수정↺ + 텍스트, 기호 aria-hidden(743행). 출처는 native details + 회전 chevron(7–12행) | 색만으로 의미를 전달하지 않음. 통일된 SVG icon library는 아니며 글꼴별 광학 차이가 날 수 있음. 고쳐진 출처 화살표는 재결함이 아님 |
| dialog / tab | native dialog, 닫기 버튼·상태 영역, aria labels(1031행). 단계·모바일 탭은 다른 현재 상태 표기 | DOM 근거 존재. 모든 dialog focus trap·Escape 복귀·스크린리더는 이번에 실행 검증하지 않음 |
| 빈 상태·진행·오류 | 빈 미디어 문구, cursor progress, native progress, 사용자용 오류 + diagnostics disclosure; 87·899행 등 | 모델/비용/테스트/권리 구분 유지. 3개 최종 B 기본 이미지는 모든 loading/error 상태를 보여주지 않음 |

### 눈에 보이는 geometry

최종 B 1280×900 이미지의 픽셀을 읽은 근사치(±2px, DOM 실측 아님): shell 약56px + 단계 약48px, 작업대 y≈120; preview x≈220/y≈206/w≈736/h≈324; Take 행 y≈538; 타임라인 y≈632–859. 미리보기·native 재생 조작·Take·타임라인 요약이 첫 화면에 함께 있습니다. inspector x≈972/w≈288로 검토 맥락이 옆에 있습니다.

390×844 모바일은 shell·단계·현재 장면/Take·작업 탭 뒤 y≈214에서 검토 카드가 시작됩니다. 승인 상태, 검토 메모, ‘검토 수정’이 첫 화면에 함께 보입니다. 완료된 검토에는 다시 승인하라는 강한 CTA가 필요하지 않습니다. 상단 약200px의 밀도는 화면에서 관찰되지만, 정보별 역할이 있으므로 즉시 결함이나 새 재설계 근거로 판정하지 않습니다.

## 4. responsive·focus·motion·미디어

- **Responsive:** 현재 핵심 전환은 900/901px, desktop 압축1150px, 아주 좁은 화면359px입니다. 기반 CSS의 700/1000/1050/1100px 규칙도 남아 있습니다. 숫자가 많다는 이유만으로 깨짐을 주장하지 않습니다. 다만 경계 조합 회귀 비용이 증가합니다. 현재 저장된 B 근거는1280/390이며, 오늘320px·901px·1150px·브라우저200/400% 검증은 하지 못했습니다.
- **Focus:** 후속 기본은 따뜻한 dashed 외곽선으로 선택의 왼쪽 막대·승인 기호와 다릅니다. 출처 summary에는 더 높은 specificity의 solid currentColor 예외가 실제 소스와 B 펼침 이미지에 남습니다. 이것은 통일성 개선 사항이지 focus가 없다는 결함이 아닙니다.
- **Motion:** 기본 hover는120ms/cubic-bezier(.2,0,0,1); reduced-motion에서 animation/transition/scroll-behavior를 끄는 규칙이 여러 층에 있습니다(163–173·331–332·438·652행). 검토 저장은 transition:none(597행). CSS상 지원을 확인한 것이며 OS 설정을 바꾼 실제 시험은 아닙니다. forced-colors 대응도 있으나 전체 상태 실동작은 미검증입니다.
- **미디어:** preview와 비교는 contain, 비교 stage는 desktop `height:min(32vh,300px);min-height:180px`, mobile210px(631–647행). 서로 다른 종횡비를 강제 crop하지 않습니다. rail/Take thumbnail은 cover(372·460행)이므로 보조 썸네일과 비교 원본의 목적을 구분합니다. 영상은 native controls, 이미지는 영상 재생 조작을 흉내 내지 않습니다.
- **타임라인:** `renderStudioTrack`은 duration별 flex와 최소144px의 상태 요약입니다(467·748행). 정확한 비례 눈금·재생 head·드래그 편집기로 단정할 수 없습니다. 실제 정밀 조작은 숫자/음원/자막 disclosure에 있습니다. duration·현재 선택·승인·출력 승인 상태가 구분되며, 영상 원본2초와 편집1초는 서로 다른 값으로 표시됩니다. 파형 함수는 실제 measured PCM 데이터가 있을 때만 그림을 생성합니다(688행). 이 기능 범위는 경쟁사 full timeline과 동등하다는 근거가 아닙니다.

## 5. 하드코딩·중복이 실제 문제인지

정적 집계: 8개 style 블록, custom property 선언81개/이름72개, HEX literal 출현202회/표기78종, `!important`56회입니다. HEX 수에는 기존 덮인 규칙·축약 표기·알파 값이 포함되므로 ‘화면에78색’이라는 뜻이 아닙니다. [source-inventory.json](source-inventory.json), [TOKENS.csv](TOKENS.csv).

| 분류 | 구체적인 사실 | 우선순위·권고(미적용) |
|---|---|---|
| **실제 소스 계약 불일치** | 글자 크기 select(657행)의 handler는 `--text-scale`만 변경(1032행). 현재 핵심 title20px, 메모14px, rail/meta12px, control14px는 고정값이므로 이 설정에 반응하지 않음 | **P1 다음 수정 우선.** 모든 문자 역할을 배율에 연결하거나, 제공하는 설정의 범위를 정직하게 재정의. 브라우저zoom 문제/WCAG 실패로 확대 해석하지 않음. 오늘 실동작 재현은 불가 |
| **시스템 관리 부채** | 간격 토큰6개가 실제 사용0회. craft/creator/finish에서 같은 역할에 다른 색·크기를 반복 정의 | **P2.** 최종 적용값을 보존하며 단일 semantic 토큰과 component alias로 정리. 팔레트 교체나 전면 리브랜딩 필요 없음 |
| **기본 focus의 구체적 예외** | finish dashed warm ring보다 12행 `.creator-source>summary:focus-visible` solid currentColor가 구체적 | **P2 낮음.** 같은 focus 토큰으로 수렴하거나 의미 있는 예외로 문서화. 대비·키보드 인지 실패로 재분류하지 않음 |
| **활성/비활성 표현의 분산** | 일반 disabled는353행 important, review disabled는598행 더 구체적 important; 색이 서로 다름 | **P2 관리.** 의도된 역할 차이인지 component 계약으로 명시. 활성 상태가 비활성으로 오표시된 새 증거는 없음 |
| **하드코딩이지만 정상 역할 차이** | media `#050505/#080808`, panel/dialog `#1B1B1B/#171717`, 선택/승인/hover의 다른 값 | 버그로 계산하지 않음. token alias로 설명하면 충분 |
| **조용한 경계** | divider1.47:1, 일반 버튼 경계2.06:1 | 일괄 밝게 만드는 개선 불필요. 식별에 경계가 꼭 필요한 개별 컨트롤만 재검증 |
| **정리 필요 문서** | 통합된 style/DOM 주석에 ‘Candidate, not integrated’가 남음(176–177·337·1206행) | **P3.** 실제 배포 상태와 주석 정합성. 화면 품질 결함 아님 |

글자 크기 문제의 CSS상 예상 예: 설정100%→200%에서 body 기반14→28px, 반면 장면 제목20→20px, 검토 메모14→14px, Take metadata12→12px. 이는 현재 선언/handler의 수학적 결과이며 runtime 측정 표가 아닙니다.

## 6. 경쟁사 근거와 ‘90’ 해석

이 감사는 기존 reference lock을 재사용했습니다. [Clipchamp editor](https://refero.design/pages/be21ed55-791a-4527-91d6-be6551ad877f)는 조용한 chrome과 media/timeline 배치, [ElevenLabs Studio](https://refero.design/pages/8f4551a8-6e46-40dc-94ad-05c708570e44)는 선택 맥락의 조작부, [Neural Frames 공식 handbook](https://help.neuralframes.com/en/articles/12038142-handbook-the-four-stages-of-autopilot)은 Track/Storyboard 설명 이미지를 참고한 것입니다. 이번에 타사 계정·내부 editor·토큰을 새로 열거나 측정하지 않았습니다.

과거 [TOKEN-COMPARISON](../design-benchmark-20261025/system/TOKEN-COMPARISON.md)의 값은 metadata·시각 추정·signup/landing 실측이 섞여 각각 표시돼 있습니다. 이를 타사 내부 작업대의 정확한 디자인 토큰으로 재사용하면 안 됩니다. 이후 [구조 결정](../design-benchmark-20261025/structure/DECISIONS.md)에서 인증 접근은 됐으나 새 데이터 없이 열 기존 편집기를 확인하지 못했다는 경계와, 공식 튜토리얼 이미지 사용을 명시합니다. 초기에 적힌 로그인 경계를 현재 사실로 반복하지 않습니다.

기존 [최종 인계](../final-delivery-20261025/Loretune-구현-QA-인계.md)의90/100(±3, 같은 다섯 항목 각18)은 표본 렌더링에 대한 독립 전문가 판단입니다. 이번 감사는 새 전체 점수를 만들지 않습니다. **정확한 현재 HEX와 높은 주요 대비는 확인됐지만, 단일 토큰 관리·모든 상태/화면·실제 확대·스크린리더·고객 사용성·경쟁사 동일 조건 비교까지90점으로 검증된 것은 아닙니다.**

## 종료 상태

완료: 최종 B 소스 hash 확인, 저장된 B 이미지3장 열람, 정확한 token/selector inventory, 주요 실제 색 쌍19개 대비 계산, 범주별 진단과 우선순위.

차단: localhost8773 연결 거절로 현행 served hash·새 computed style·상호작용/확대 재검증 불가. 앱 코드·DB·서버 변경 없이 진단 산출물만 보존했습니다. 저장 오류 안내·disclosure 수정을 다시 결함으로 계산하지 않았으며, 승인 완료 화면의 CTA 강화를 요구하지 않았습니다.
