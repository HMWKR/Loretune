# Loretune 창작자 화면 단순화 — 통합 전 후보 결과

**통합 가능한 패치를 완성했다. 실제 앱에는 적용하지 않았으며, 90점 달성을 주장하지 않는다.** 이번 범위는 반복 안내·내부 진단을 정리하고 검토 결과/수정 상태를 분명하게 만드는 것이다. 기존 독립 평가 **66/100**은 아직 유효한 실제 통합본 평가다. 후보 의도나 스크린샷으로 그 점수를 올리지 않았다.

## 산출물

- [정확한 통합 diff](integration-creator.patch), [독립 CSS](creator.css), [후보 HTML](candidate-index.html)
- [병합 계약·주의점](INTEGRATION-ko.md), [화면별 정보 분류·문구 결정표](VISIBILITY-LEDGER-ko.md), [reference lock](DECISIONS.md)
- [21개 집중 테스트 결과](test-results.json), [7개 브라우저 상호작용 결과](browser-interaction-results.json), [주요 화면 보존 검사](candidate-primary-results.json)

기준 소스/실행 서버 SHA256: `0a8ef8436b8d751c4581c648beeaa688f054217b5781d1a9528c30d2cca5c6ae`.
후보 SHA256: `68d1032f86aabbfc858dcf734c90f685b577cc2f1c277931d0ab0de19bb0ba14`.
2026-10-25 15:21:50 UTC에8773의 기준 해시가 그대로임을 확인했다. 원본 파일도 동일하다. 별도 QA 공간14를 종료했다. 외부 생성/경쟁사 조작/새 프로젝트/서버 재시작/DB 변경은 없다.

## 바뀐 사용 흐름

저장된 승인·거절은 상태/메모와 **검토 수정**을 보여준다. 수정하면 기존 결정·메모가 채워진 form과 저장/취소가 나타난다. 미검토 Take는 바로 form으로 시작한다. 저장 중 새로 입력한 값, 다른 장면의 초안, 오류 뒤 값은 보존된다. 빈 Take는 기존 미디어 연결 경로를 연다.

상단은 작품·저장·설정과4단계로 정리했다. 상시 지시 행과 다음단계 버튼은 제작 진행·도움말로 이동했다. 모바일 검토/미리보기/장면 탭 위에는 현재 장면·Take·검토 상태를 유지한다. 출처·사용권은 발견 가능한 disclosure에 있고 중지/미확인 경고, 테스트 미디어 배지, 실행 비용과 승인 사실은 숨기지 않았다.

비교, 출력, 모델, 생성/복구, 예산과 설정 화면의 내부 ID/hash/adapter/revision/도구 trace는 명시적 상세로 옮겼다. 오류는 가능한 결과와 다음 행동을 말하며 원문은 남긴다. 진행 중 요청을 새 생성으로 재시도하거나 환불된 것처럼 표시하지 않는다.

## 실제 측정과 한계

같은1280×900, 같은 QA 프로젝트/첫 장면/Take2, 같은324px media 높이로 비교했다. baseline HTML도 같은 브라우저 iframe에서 측정했다. 후보는 개발자 전용 iframe의 로컬 미리보기이며 실제 배포/통합 UI가 아니다.

| 항목 | 기준 | 후보 | 관찰 |
|---|---:|---:|---|
| 상단 shell+단계+지시 영역 끝 |142px|104px|지시 행 제거,38px 감소|
| 미리보기 위쪽 |224.1px|206px|18.1px 위로 이동|
| 미리보기 크기 |736×324px|736×324px|미디어 축소로 공간을 만든 것이 아님|
| 타임라인 아래쪽 |885.4px|867.3px|둘 다900px 안, 후보18.1px 여유 증가|
| 검토 section 높이 |562.9px|415.5px|저장된 결과에서147.4px 감소|

측정 파일: [baseline geometry](baseline-geometry-desktop.json), [candidate geometry](candidate-geometry-desktop.json).

390×844에서 장면 title/Take/status가 먼저 보이며 action의 아래쪽은 승인489.9px, 거절466.8px, 미검토·dirty647.5px, 오류750.5px였다. 주요 action44px. 모든5상태의 document width390px. 오류는 펼쳐도 수정 내용과 저장/취소가 한 화면에 남는다. [상태 측정](candidate-mobile-states.json)

320px 검토·빈 상태에서도 수평 document overflow가 없었다. 이 검사와 saving 스크린샷은 최종 모델 안내/출력 배지 문구 수정 전 후보(8ca5a1e…63d73)의 보조 증거다. 해당 수정은 검토 DOM/CSS/F07 제어기를 변경하지 않았다. 최종5상태390px/desktop/주요 화면은 최종68d1032…0ba14로 다시 캡처했다.

## 증거 화면

모두 로컬에 저장한 실제 브라우저 렌더 픽셀을 이미지 도구로 열어 확인했다. `before-*`는 실제 고정 앱, `candidate-*`는 임시 후보 iframe이다. 단색 미디어 품질은 평가하지 않는다.

| 상태 | 화면 | 출처 |
|---|---|---|
| 기준 desktop |[before review](before-review-1280.png)|실제 고정 앱·저장된 승인 상태|
| 후보 desktop |[approved1280](candidate-approved-1280.png)|기존 다중장면 fixture·저장된 승인 데이터|
| 비교 |[comparison1280](candidate-comparison-1280.png)|기존 Take2/Take1, 실제 미디어·상태|
| 승인 read-only |[approved390](candidate-approved-390.png)|저장된 승인 데이터|
| 거절 read-only |[rejected390](candidate-rejected-390.png)|브라우저 메모리에만 거절 review 투영|
| 미검토 |[unreviewed390](candidate-unreviewed-390.png)|실제로 미검토인 장면2 Take1을 메모리에서 선택|
| 미저장 |[dirty390](candidate-dirty-390.png)|후보에서만 작성한 scoped draft|
| 오류 |[error390](candidate-error-390.png)|로컬 주입 네트워크 오류·입력 보존|
| 저장 중 |[saving390](candidate-saving-390.png)|실제 controller + deferred local response, 서버 저장 아님|
|320 검토·빈 상태 |[review320](candidate-review-320.png) / [empty320](candidate-empty-320.png)|검토·noTake 브라우저 투영, 위 버전 한계 적용|
| 음악 |[music1280](candidate-music-1280.png)|기존 로컬 음원|
| 계획 |[plan1280](candidate-plan-1280.png)|현재 fixture의 빈 계획 화면|
| 모델 |[models1280](candidate-models-1280.png)|현재 fixture의 미선택·미검증 상태|
| 새 작품 |[project1280](candidate-project-1280.png)|입력 dialog만 열음, 새 작품 만들지 않음|
| 출력 |[output1280](candidate-output-1280.png)|기존 승인 출력v2·편집v3 구분, 테스트 미디어 표시|

출력 screenshot은 기존 결과를 연 직후 프레임이다. 일부 native video loading 표시는 이 캡처에서 재생 성능이 검증됐다는 뜻도, 재생 고장 증거도 아니다. 새로 렌더하지 않았다.

## 참조 출처와 판단

[Clipchamp editor](https://refero.design/pages/be21ed55-791a-4527-91d6-be6551ad877f)는 media/transport/timeline 중심 composition, [ElevenLabs Studio](https://refero.design/pages/8f4551a8-6e46-40dc-94ad-05c708570e44)는 선택 대상과 관련 조작을 가까이 배치하는 패턴을 참고했다. 이번에 Refero 실제 이미지를 읽었다. metadata는 정확히 계측한 CSS 값으로 쓰지 않았다.

[Neural Frames 공식 Track 이미지](../structure/neural-official-track.png)와 [공식 Storyboard 이미지](../structure/neural-official-storyboard.png)는 이전에 확보한 공식 튜토리얼 자료다. 직접 로그인 editor session을 관찰한 근거로 바꾸어 설명하지 않는다. 이번에 경쟁사 계정은 열거나 조작하지 않았다. 기존 Krea 기반 coal/white-action palette를 유지하며 타사 브랜드·보라색 강조를 복제하지 않았다.

## 동일 rubric과 다음 통합 판단

| 항목 /20 | 실제 고정본 독립 평가 | 이번 후보가 겨냥한 변화 | 아직 남는 격차 |
|---|---:|---|---|
|정보·행동 명확성|15|review read/edit 분리, 모바일 정체성|새 media_actions UI 통합 후 전체 승인 흐름 검증 필요|
|타이포·간격·위계|14|상단 반복 제거, 메모/메타 분리|계획 입력·모델 dialog의 form 비중이 여전히 큼|
|미디어·작업 효율|15|미디어 크기 유지, 검토 높이 감소|출력 단계는 결과와 timeline이 함께 있을 때 아래쪽이 길어짐|
|컴포넌트·상태 일관성|14|승인/거절/초안/오류의 동일 상태 모델|새 공급자 준비·권리·복구 상태와 결합 검증 필요|
|브랜드·시각 완성도|8|조용한 tonal surface, 목적별 소제목|여전히 기본 form 중심, 도구 전체의 정교한 시각 표현은 부족|
|합계|**66**|후보 점수는 매기지 않음|최소90 목표 미달|

가장 중요한 다음 작업은 이 bounded patch와 실제07 multimodel 승인·권리 UI를 한 번 통합한 뒤, 같은5상태와 populated 계획/실행/출력 맥락을 재평가하는 것이다. 기능 화면이 생성되기 전에 꾸밈만 더해 점수를 만들지 않는다. 시각적으로는 계획·모델 화면의 긴 기본 form과 출력 단계의 이중 미디어/타임라인 길이가 다음 우선순위다.

21개 단위·계약 검사와7개 후보 browser checks는 실제 사용자 연구가 아니다. 실제200/400% 브라우저 zoom, screenreader, 전체 keyboard workflow, WCAG 적합성은 이번 pass에서 확인하지 않았다. 일부 키보드 경로와 focus 복귀만 직접 확인했다. synthetic 오류/거절 투영을 실제 공급자 오류 처리 성공으로 주장하지 않는다. 마지막 서버/소스 해시는 유지됐다.

Ego Lite 업데이트 알림이 있었지만 설치·설정 변경은 하지 않았다. 도구 차단은 없었고 현재 남은 선행 조건은 기능 세션의 통합 및 회귀검증이다.
