# 왜 이 방법으로 디자인을 검토하는가

이번 검토는 ‘마음에 드는 편집기처럼 보이게 만들기’보다 **실제 제작 과업을 안정적으로 연결하는지**를 먼저 본다. 작업 맥락을 정하고, 참고 패턴의 역할을 좁히고, 토큰과 컴포넌트에 의도를 연결한 뒤, 같은 과업의 실제 렌더를 측정한다. 마지막에 반례와 키보드·확대 조건을 확인한다. 이는 전문가 검토이며 실제 사용자 실험을 수행한 결과가 아니다.

## 이번에 확인한 방법론과 적용 한계

| 근거 | 확인한 내용 | Loretune에 적용하는 이유와 경계 |
|---|---|---|
| [Adobe Premiere: 패널 조정](https://helpx.adobe.com/premiere/desktop/get-started/tour-the-workspace/customize-panels.html) | 패널 열기/닫기, 그룹 내 탭 스크롤, 구분자를 통한 크기 조절. 2026-01-07 갱신 공식 문서를 이번 턴에 읽음 | 작업 맥락을 유지하면서 세부 패널에 접근하는 근거. ‘모든 경쟁사는 스크롤이 없다’ 또는 Loretune의 특정 폭/높이 정답을 증명하지 않음 |
| [Blender HIG: paradigms](https://developer.blender.org/docs/features/interface/human_interface_guidelines/paradigms/) | 연구 담당이 관련 도구의 non-overlapping 분할 작업영역 근거로 전달 | 이번 직접 재열람은 웹 도구 `402 Payment Required`로 실패. 문서가 유료라는 판단이 아니며 전달 근거로만 표시. 접근 우회 없음 |
| [Spectrum: design tokens](https://spectrum.adobe.com/foundations/design-data/design-tokens) | primitive/semantic/component-specific 역할과 alias를 구분하고, 값보다 재사용 가능한 의도를 우선 | 같은 색이어도 ‘장식선’과 ‘필수 입력 경계’의 목적은 다르다. 기존 값의 의미를 보존·통합하는 근거이며 Spectrum의 색상을 복제할 이유가 아님 |
| [NN/g: progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) | 빈번하고 중요한 옵션을 먼저 두고 전문·드문 옵션은 요청 시 공개 | 검토 결과/행동을 우선, 제작 도구와 진단은 명확한 상세로. 비용·승인·실패를 숨기는 허가가 아님 |
| [NN/g: recognition and recall](https://www.nngroup.com/articles/recognition-and-recall/) | 맥락과 선택 단서를 제공해 사용자가 기억에 의존하지 않게 함 | 현재 장면·Take·버전·검토 상태를 같은 언어로 연결. 모든 패널에 모든 문장을 반복하는 근거가 아님 |
| [W3C: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | 2차원 의미가 필요한 부분은 예외가 있지만 일반 설명·폼의 가독성은 여전히 보존 | 시간축 자체와 주변 문장을 분리해 확대에서 검토. 편집기 전체를 reflow 예외로 처리하지 않음 |
| [W3C: Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) | 200%까지 내용·기능의 손실 없이 문자 확대가 가능해야 함 | 앱 문자배율과 브라우저 확대 결과를 구분. 이번 샘플 통과를 WCAG 전체 준수로 확대하지 않음 |

Refero/공식 편집기 이미지의 역할·원본 해상도·촬영 맥락은 [참고 표](PROPOSALS-AND-REFERENCES-ko.md)에 분리했다. Descript는 시간 정렬, Frame.io는 미디어·버전·검토 인접성, Neural Frames는 장면 제작 맥락, Runway는 공식 Studio의 수동/채팅 편집 맥락을 참고한다. Runway home 이미지를 시간축 증거로 사용하지 않는다. 내부 HEX나 경쟁사 품질 점수는 추정하지 않는다.

추가로 전달된 HTA/OOUX/Human-AI/색상 방법론의 채택·조건부·제외 판단은 [전체 적합성 표](../METHODOLOGY-FIT-MATRIX-ko.md)에 기록했다. 새로운 기능 도입이나 검증 완료와 구분한다.

## 과업에서 검증까지의 추적표

아래 구현 위치는 현재 파일에서 존재를 확인한 selector/함수명이다. 줄 번호는 새 freeze에서 다시 고정한다. `기존`은 이전 구현의 관찰, `이번`은 no-page-scroll 변경의 검증 대상이다. 소스 존재는 실제 UI 동작 통과를 뜻하지 않는다.

| ID / 사용자 과업 | 참고 근거 | 설계 이유 | 구현 위치 | 기존 근거 / 이번 검증 |
|---|---|---|---|---|
| L01 영상을 보며 장면·시간·검토를 함께 조작 | Premiere 패널, Descript 시간축, 사용자 요구 | 문서가 밀려 다른 작업 구역을 잃지 않게 한다. 긴 설정은 패널 내부에서 접근 | `studio.css`: `.lt-edit-workspace`, `[data-desktop-shell=bounded]`, `.inspector`, `.lt-timeline-controls` | 기존 기본1080/1080, 정밀 편집1710/1080(S). 이번 기본/sequence/expanded/output의 문서·패널 scroll과 Tab 가시성 직접 확인 예정 |
| L02 실제 미디어 세부를 읽는다 | Frame.io player 인접, 사용자 미디어 중심 방향 | 넓은 검정 무대가 아니라 실제 영상의 가용 면적을 본다. portrait 여백은 정상 | `#preview`, `.preview video`, `.comparison-media-stage` | 기존16:9 실제 약533×300, stage1376×300. 이번 높이 증가와 timeline/controls 가시성의 절충을 동일 영상으로 측정 |
| L03 현재 장면/Take/검토를 인지한다 | NN/g recognition, Frame.io version 맥락 | ‘선택’은 편집 채택, ‘승인’은 검토 결과. 같은 객체를 여러 위치에서 매칭 가능하게 함 | `#shotlist`, `#takes`, `#takeReviewStatus`, `#track`, `studioBadge()` | 기존 rail/Take에 thumbnail·상태 있음. 이번 구성 변경 뒤 label·현재 대상 보존 확인. 승인 완료에 새 강한 CTA 강제하지 않음 |
| L04 긴 검토 메모를 읽고 필요할 때 수정 | NN/g progressive disclosure, ElevenLabs 선택 문맥(기존 reference lock) | 완료 상태는 짧은 결과 카드, 수정 중에만 입력/저장/취소 노출 | `#creatorReviewRecord`, `#creatorSavedReason`, `#creatorReviewEditor`, `renderTakeReview()` | 기존 카드·scope draft·취소 정상. 이번 내부 스크롤 뒤 메모/행동 접근·저장하지 않는 임시 초안 보존을 재확인 |
| L05 색으로 표면과 상태 역할을 구분 | Spectrum semantic tokens, 기존 Loretune palette | 중성 면은 미디어를 방해하지 않도록, 필수 경계·선택·focus·오류는 별도 의미로 | `studio.css:root`의 `--ui-*`, `.lt-review-state`, `:focus-visible` | 기존 주요 대비표 있음(S). 이번 실제 적용 FG/BG·opacity·ancestor 합성과 상태별 단서 확인. 새색 추가 자체가 목표 아님 |
| L06 한국어 제목/메모/시간을 빠르게 읽는다 | Spectrum type/spacing 역할, W3C resize | 제목600/항목500/본문400, 시간 tabular, 조용한 metadata. 고정높이로 확대 글자를 자르지 않음 | `--ui-title/context/body-size/meta`, `--ui-leading-*`, `#timeRuler`, `#creatorSavedReason` | 기존 본문14/21, 메모14/23.8 등 역할 차이. 이번 1920/1280·100/150/200%의 줄바꿈/눈금/컨트롤 실측 |
| L07 카드/입력/상세의 관계를 이해 | Spectrum semantic/component 역할 | spacing4/8/12/16/24/32, radius4/6/8/12의 목적이 있어야 함. 모든 테두리를 같은 강조로 만들지 않음 | `--ui-space-*`, `--ui-radius-*`, `.shot`, `.timeline`, `dialog`, `.creator-source` | 기존 토큰은 존재. 실제 computed가 역할을 따르는지 검토; override 개수만으로 결함 판정하지 않음 |
| L08 아이콘/썸네일로 대상을 찾는다 | Frame.io actual asset, recognition | 실제 poster는 대상 확인, 화살표/체크는 펼침·검토를 돕는다. 설명 없는 장식 기호로 기능을 암시하지 않음 | `.lt-media-kind img`, `.lt-take-kind img`, `.lt-review-state`, `summary` | 기존 실제 thumbnail/텍스트 동반. 이번 광학 정렬·동일 의미·accessible name 확인. 가짜 waveform/transport 금지 |
| L09 대화로 계획하고 모델을 선택 | Runway 공식 Studio 맥락, progressive disclosure | 내부 routing 대신 사용자 모델 선택/가용 이유/다음 행동. 실행과 단순 선택 저장을 구분 | `#modelSettingsPanel`, `#modelSlots`, `#modelSettingsStatus`, `#modelSettingsForm`, `#modelChatPrompt`, `#guidedPlans`, `#chatPlans` | 모델선택 dialog 설명은 JS가 creator copy로 대체함. 원시 HTML 문구만 보고 노출 결함이라 판정하지 않음. 새 freeze에서 열기/닫기만 관찰; 저장/외부호출 없음 |
| L10 비용·전송·승인 범위를 판단 | 제품 안전 계약, progressive disclosure의 중요 정보 우선 원칙 | 확정 시점에 모델·비용·전송/승인 범위를 유지. 진단을 숨겨도 의사결정 사실은 숨기지 않음 | `.media-action-card`, `#mediaActionCards`, 계획/승인 렌더 함수 | 기존 기능팀 회귀와 디자인 표시 검증 분리. 이번 새 승인을 만들지 않고 저장된 계획·상태 표시만 읽음; 없으면U |
| L11 실패에서 입력을 잃지 않고 복구 | 사용자 요구, 상태 피드백/가까운 recovery 원칙 | 실패의 영향과 다음 행동을 입력 가까이 제공. raw exception/trace는 진단으로 분리 | `#productionReviewError`, `#takeReviewDraftState`, scoped review controller | 기존 저장 실패/초안 회귀가 수정됨. 새 실패를 발명하지 않음. 기존 허용된 mock 근거 없으면 이번 동적 오류는U |
| L12 시간 위치와 편집 길이를 확인 | Descript timeline, Neural Frames 공식 editor | ruler/clip/wave/playhead가 같은 시간좌표를 써야 함. 원본 길이와 편집 길이는 다름 | `#timeAxis`, `#timeRuler`, `#timeWave`, `#track`, `#timePlayhead`, `studio-media.js` | 1/2/4초와 source trim/offset. 이번 눈금 겹침 개선은 라벨 표시만 바꾸며 좌표 무결성 재확인 |
| L13 Take를 비교하되 채택/승인은 바꾸지 않는다 | Loretune 제품 제안; 타사 동기 비교 실증 아님 | audition은 관찰용. 공통 시간·aspect 보존·각 Take 상태 유지 | `#compareDialog`, `.comparison-media-stage`, `#compareSeek`, comparison controller | DM01–03은 Node VM에서 종료(S). 이번 혼합 aspect/재생정지/시간·선택 불변의 실제 브라우저 표본만 추가 |
| L14 키보드/확대로 같은 작업에 접근 | W3C resize/reflow, 사용자 요구 | focus와 selection은 역할이 다름. overflow로 핵심조작을 숨기지 않음 | `:focus-visible`, `@media(prefers-reduced-motion)`, bounded-shell 조건 | 기존 실제 browser zoom 미확인. 이번 Tab 경로·focus 반환·reduced-motion·글자 확대를 별도 기록 |

## 실무적 검토 순서와 종료 조건

1. **과업·상태 고정:** 합성 작품/장면/Take/시간/배율과 source·served hash를 기록한다.
2. **대안과 비용 비교:** 미디어를 키우는 대신 timeline/transport를 숨기지 않는다. 같은 과업에서 패널 배분과 읽기 폭의 장단점을 설명한다.
3. **역할을 구현에 연결:** token→selector→실제 computed를 매칭한다. 선언만 있고 쓰이지 않으면 그 차이를 기록한다.
4. **시각·동작 분리 검증:** 저장 이미지를 열어 구성 판단, DOM으로 치수/대비 측정, 정상 UI로 키보드·전이 확인. 기능팀 테스트는 별도 증거다.
5. **반례 검토:** 긴 한국어, 확대, 펼친 상세, dirty/cancel, 미연결/오류, 다른 aspect를 본다. 접근 범위 밖은U로 남긴다.
6. **동일 기준 평가:** 고정 7축과 gate로 결과를 설명하고 남은 문제만 제안한다. 점수를 높이려고 기능·안전 정보·기준을 바꾸지 않는다.

이번 직접 웹 확인에서 Blender 한 페이지의 fetch만 실패했다. Adobe/Spectrum/NN/g/W3C 읽기는 완료했으며 대체 계정·인증·우회는 하지 않았다. 이 자료는 설계 이유의 근거이고 Loretune의 실제 UI 검증을 대신하지 않는다.
