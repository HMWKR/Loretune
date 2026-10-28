# 통합 디자인 시스템 독립 화면 QA · 2026-10-26

**새로 확인한 중대한 시각·조작 손실은 없습니다.** 토큰 적용, 앱 글자 배율, 시간 비례 표시, 실제 poster, 모바일 미디어·검토 연결은 표본에서 개선을 확인했습니다. 다만 **동적 미디어 최종 수용은 보류**합니다. 검토 도중 부모가 독립 코드 감사의 미디어 P2 세 건과 기능팀 수정 착수를 알려 왔기 때문입니다. 이 보고서는 수정 전 고정 버전의 관찰이며90점·경쟁사 동등성·출시 준비를 선언하지 않습니다.

## 확인된 Library 이미지

모두 이 독립 검토에서 새로 캡처하고 저장 픽셀을 열어 확인한 실제 앱 화면입니다. 합성 fixture이며 실제 AI 생성 결과가 아닙니다.

| 화면 | Library ID | viewport / 상태 |
|---|---|---|
| [Desktop](01-desktop-1280.png) | `libfile_160ffbb5458c819186690df5c19e9305` |1280×900,3장면·각3Take·승인된 Take1 |
| [비교](02-comparison-1280.png) | `libfile_4bf6d7961cbc8191a57714e8776f1aaf` |1280×900, landscape/portrait 영상 비교, 닫기 focus |
| [Mobile](03-mobile-approved-390.png) | `libfile_81e57dd5c82c8191a18a52092bd3d38d` |390×844, 같은 플레이어+승인 카드 |

Library는 Codex 로컬 파일용 create 경로의 성공 응답으로 ID를 확인했고 공식 metadata helper도 성공했습니다. 이번 세 파일에는 prepared helper write를 시작하지 않았습니다. 기능팀의 다른 파일 업로드 시도와 별개의 독립 감사 파일입니다.

## 버전·범위·불변 확인

- URL `http://127.0.0.1:8773`, 사용자 Mac의 별도 Ego Lite TaskSpace27. 검토 종료 시 해당 공간만 정상 종료했습니다. 기존 사용자 탭은 사용하지 않았습니다.
- HTML `846e18d44d6361cf423ba6ad568ede4280fcb22b34bee17a3eeb0a647974d839`
- CSS `5f50efffbb79f30da17e231d9257559d2e174c969cb04796f8fbd2779d6fe271`
- JS `8f95c231d4ab45307c9ec0b37c5e54fe8d05b6039b96b92d03a44e6d1d0ba91a`
- [시작](served-start.json)과 [종료](served-end.json)의 GET200·해시는 동일했습니다. 이후 기능팀 수정본의 검증 결과는 포함하지 않습니다.
- 주 fixture `디자인 시스템 기능 QA 20261026`:1/2/4초,3장면·각3Take. [QA 프로젝트 시작](qa-project-before.json)과 [종료](qa-project-after.json)의 전체 project JSON fingerprint가 같습니다. 실제 선택·검토·승인·timeline 저장은 실행하지 않았습니다.
- 임시 로컬 UI 상태만 변경: 프로젝트/패널 보기, 비교 좌우 선택, 합성 영상 비교 재생, 입력 초안 작성 후 취소, 앱 배율 변경 후100% 복원, focus/disclosure. 새 승인·생성·삭제·export·외부 호출 없음.
- 기능팀의337 tests 및7초1080p 음악·한국어 자막 출력/재시작 보존은 [기능팀 보고](../design-system-implementation-20261026/REPORT-ko.md)에서 읽은 증거입니다. 이 독립 검토가 회귀337개나 렌더를 다시 수행했다고 말하지 않습니다.

## 직접 수행한 흐름

| 단계 | 직접 관찰 | 판정과 한계 |
|---|---|---|
|1 작업대 진입 |1280×900 실제 poster·3장면·3Take, 제목/검토 상태/테스트 표시, page 가로 overflow0 | 기본 작업대 정상. 아래 타임라인 일부는 fold 밖 |
|2 비교 진입·재생 | Enter로 비교, 다른 Take1/2, stage 각각471×288, contain. 공통1초 종료 시 source1.25/1.00초 및 둘 다paused | 이 표본 정상. 미디어 lifecycle 일반 통과는 별도 코드 결함 때문에 보류 |
|3 비교 닫기 | Escape 후 dialog closed, activeElement=`compareButton` | 표본 focus 복귀 정상 |
|4 모바일 검토 |390×844, player DOM1개, 현재 장면·Take·승인 상태, 메모·검토 수정 함께 표시 | 기본 승인 카드 정상; 물리 모바일 기기/OS키보드는 미시험 |
|5 검토 수정·탭 왕복 | ‘독립 디자인 QA 임시 입력 — 저장하지 않음’ 입력, 미리보기→검토 복귀 후 같은 값/dirty 상태 유지, 저장 버튼 enabled | 같은 맥락 tab 왕복 표본. 다른 프로젝트/Take의 비동기 F07 전체 시나리오는 재실행 안 함 |
|6 초안 취소·disclosure | 키보드 Enter 취소 후 원래 memo/read card 복귀, focus=`creatorEditReview`. 출처 Enter로 open/closed, warm dashed2px focus | 정상. 저장 요청은 하지 않음 |
|7 좁은 화면 |320×568 overflow0, 수정 버튼44px, 현재 장면/Take 유지 | 자연 세로 scroll 필요. 모든 콘텐츠가 첫 화면에 보인다는 뜻은 아님 |
|8 앱 글자 배율 |100→200%에서 body14→28, title20→40, memo14→28, meta12→24, action14→28px; overflow0 | 앱 배율의 핵심 표본 확인. 브라우저zoom과 별개 |
|9 실제 브라우저 확대 시도 | emulation clear 후 정상 `ControlOrMeta+0`, `ControlOrMeta+Equal`5회. viewport900×845, DPR2, visualViewport.scale1 유지 | **실제200% 확대 실패/미검증**. 변경되지 않은 값을200% 통과로 표기하지 않음 |

근거: [desktop 수치](desktop-observed.json), [비교](comparison-observed.json), [mobile](mobile-observed.json), [keyboard](review-keyboard-observed.json), [320](mobile320-observed.json), [앱 배율](app-scale-observed.json), [브라우저 확대 시도](browser-zoom-attempt.json).

## 주요 시각·사용성 판단

### 1. 선택·승인·오류와 정보 위계

rail/Take에서 현재 선택은 면과 왼쪽 표시, 검토는 기호+문자로 분리됩니다. 미선택 Take의 ‘검토 전’도 함께 보입니다. inspector의 긴 장면명 반복이 ‘장면01’로 줄었으며 중앙 제목과 대응됩니다. 승인된 검토는 읽는 카드와 보조 ‘검토 수정’으로 표시돼 적절합니다. 강한 승인 CTA가 없다는 이유로 결함을 만들지 않았습니다.

검토 메모는 실제 computed400/14px, 색 `rgb(222,222,219)`이고 패널은 `rgb(27,27,27)`입니다. shell/미디어/검토 영역의 중성 면, 따뜻한 focus, 조용한 승인 표현이 유지됩니다. 과거의 출처 disclosure focus 예외도 현재 `rgb(228,221,190) dashed 2px`로 직접 확인했습니다. 이전 수정된 저장 오류와 disclosure를 재결함으로 계산하지 않습니다.

### 2. 시간·길이·미디어 이해

새 fixture1/2/4초 장면의 실제 폭은100.8516/201.7109/403.4219px입니다. 같은 과제의 기존1/1.5/2초도156.8828/235.3281/313.7734px로 비례합니다. 시간 눈금과 실제 PCM 진폭 영역이 같은 축에 있습니다. 낮은 진폭 합성 음원에서 파형이 거의 평평하게 보이는 것은 데이터 특성이므로 가짜 파형을 추가하라고 요구하지 않습니다.

영상 원본5초와 편집1초는 별도 문구로 표시됩니다. 비교는 두 aspect 모두 같은 contain stage에 놓이며 원본 시작·사용 구간·공통 상대시간이 제공됩니다. 문구가 많은 편이지만 trim과 짧은 쪽에서 멈추는 의미를 설명하는 정보이므로 무조건 삭제하지 않습니다. 이 자료가 경쟁사의 동일 기능이나 frame-sync 정밀성을 증명하지는 않습니다.

### 3. 모바일·입력 상태

390px 승인 화면에서 preview는 y274.5–461.25, 메모는 y624.04–647.84, ‘검토 수정’은 y663.84–707.84입니다. 현재 맥락 strip, 같은 player, 승인 결과·메모·수정이 한 화면 안에 있습니다. 320px에서는 미디어와 상태가 먼저 보이고 메모·수정은 자연 scroll로 이어집니다.

[dirty 화면](04b-mobile-dirty-visible-390.png)에서 입력은 유지되며 저장은 흰 활성 버튼, 취소는 보조 버튼, keyboard focus는 독립 dashed ring으로 구분됩니다. 자동 도구의 취소 클릭은 viewport 경계에서 실패했지만, 실제 wheel 후 버튼이 보이고 keyboard Enter 취소가 정상 동작했습니다. 이 도구 접근 실패를 제품의 취소 불능으로 판정하지 않습니다. 실제 touch·soft keyboard는 미검증입니다.

### 4. 남는 화면 밀도 — P2 개선 항목, 기능 차단 아님

1280×900에서 shell56 + 단계48, 작업대 y120, preview y206–530는 유지됩니다. 새 preview mode와 시간축 때문에 timeline은 y682.30–992.89, clip행은 y848.49–908.49입니다. 따라서 **타임라인 하단 약9px 및 정밀 편집 진입은 첫 화면 밖**입니다. 정상 scroll로 접근되므로 기능 유실이나 출시 차단으로 부풀리지 않습니다. ‘미리보기·핵심 조작·타임라인 전체가 첫 화면 안’이라는 이전 수용 목표에는 부분 충족입니다.

후속 조정이 필요하면 timeline의 헤더/축 주변 여백과 preview 높이의 desktop 균형을 한 번에 조정합니다. metadata 크기 축소, 승인/권리 정보 삭제, 추가 panel 중첩으로 해결하지 않습니다. 이 검토에서 앱 CSS를 수정하지 않았습니다.

## DS01–13 대조

| 기준 | 독립 판정 | 구체적 범위 |
|---|---|---|
|DS01 token consolidation|소스 구조 확인·부분|inline8층 대신studio.css와`--ui-*`역할. 실제 colors/fonts 확인. retained55 priority 규칙 최소성 전체 감사는 안 함 |
|DS02 scaling|핵심 표본 확인|5종100/200 실제 computed2배;150은 기능팀 증거. 실제 browserzoom은 미검증 |
|DS03 semantic states|표본 확인|중성 승인/선택 marker/focus/테스트 표시. 전체 상태·접근성 인증 아님 |
|DS04 type/spacing|표본 확인·밀도 잔여|본문400, meta계층, 정렬 개선. desktop timeline fold는 위 P2 |
|DS05 duplicate identity|표본 확인|중앙 전체 제목·inspector 짧은번호·mobile identity |
|DS06 time axis|정적 geometry 확인 / 동적 보류|1:2:4 실측. playhead/lifecycle 수정본 재검증 필요 |
|DS07 mobile preview/review|기본 승인/dirty 표본 확인|390·320, 동일player1개. 물리 기기/short-landscape/OSkeyboard는 미검증 |
|DS08 contextual actions|읽기·dirty·취소 표본 확인|오류저장/미확정/F07 전체는 기존 기능팀 회귀 증거, 이번 새 승인 요청 없음 |
|DS09 compare|표본 관찰 / 최종 보류|같은 stage, 다른Take,1초 재생, Escape. 이전sequence잔존 결함 수정 재확인 필요 |
|DS10 keyboard/motion|키보드 일부 확인|Enter review·취소·disclosure, Escape 비교. reduced-motion은 기능팀 증거와 CSS; 이번 OS설정 실험 안 함 |
|DS11 safety|QA project불변 확인|전체project JSON fingerprint 동일. 실제provider·새export 재시험 없음 |
|DS12 audition|최종 보류|parent가 알려온 media lifecycle/seek 결함 수정 이후 검증 |
|DS13 poster|정상표본 확인|로컬 영상 실제 첫프레임 표시. pending/unavailable 모든코덱은 미검증 |

## 부모가 알려온 동적 결함 — 직접 재현과 구분

검토 도중 부모가 독립 코드 감사의 Node VM 재현 결과를 전달했습니다:①오래된 media 이벤트가 새 상태에 영향,②무음 비교 중 이전 sequence 음악/루프 잔존,③로딩 중 seek가 frame에 반영되지 않음. 이 세 건은 **다른 감사자의 발견**입니다. 기능팀이 최소 수정 중이므로 이 버전에서 관찰한 정상 비교 한 번을 일반 통과로 확대하지 않습니다. 수정 hash를 받은 다음 해당 세 경로만 재검증해야 합니다.

## 캡처·도구 한계

- 제공된 `release-desktop.png`, `release-mobile.png`, `final-video-comparison.png`를 먼저 열어 확인했고, 위 Library3장은 독립 캡처입니다. 비교 이미지의 A/B 차이는 기능팀 manifest의 설명과 구분합니다.
- 직접 찍은 `06-same-task-desktop-1280.png`와 제공된 `final-desktop-same-task.png`를 열자 native video loading spinner가 있었습니다. **안정된 미디어 전후비교 화면으로는 수락하지 않았습니다.** 당시 geometry 수치는 별도로 보존했지만 영상 준비 완료 증거로 쓰지 않습니다. [capture-manifest](capture-manifest.json)에 제외 이유를 적었습니다.
- 첫 비교 wait는 기본값이 영상+이미지인데 영상2개를 기다린 도구 가정 오류였습니다. 실제 상태를 읽고 영상Take2를 고른 뒤 재생을 확인했습니다. 이는 제품 오류가 아닙니다.
- 취소 자동 클릭의 viewport 문제와 중첩 summary 선택자 모호성은 상태를 확인해 스크롤/정확한 summary/키보드로 해결했습니다. 서버 쓰기를 재시도하지 않았습니다.
- 브라우저 실제200/400%, screen reader 전체 여정, 실제 고객 연구, 물리 모바일·OS키보드, 장시간 동기성, 모든 provider/출력 흐름은 미검증입니다.
- Ego Lite0.6.0.20 업데이트 알림을 관찰했지만 업그레이드하지 않았습니다.

## 인계

정적 화면·token·표본 접근성 검토는 이 버전 기준으로 종료했습니다. 동적 미디어 최종 수용만 수정본에 대기합니다. 앱·서버·DB 변경 없음, 새 승인/미디어 생성/삭제 없음, QA프로젝트 fingerprint 불변, 종료 시 제공 hash 동일입니다. 임의 점수나 경쟁사 동등성은 부여하지 않습니다.
