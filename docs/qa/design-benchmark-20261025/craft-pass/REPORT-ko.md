# Loretune craft 후보 · 통합 인계

2026-10-25. 현재 앱의 3열 구조를 유지하는 제한된 표현·상호작용 개선이다. **아래 after는 검증 탭에만 적용한 후보이며 실행 서버에 통합되지 않았다.** 실제 통합본의 56/100 점수를 이번 후보 때문에 올리지 않는다.

## 바로 적용할 파일

- [integration-craft.patch](integration-craft.patch): 기준 HTML `be3ff1634a396e378d320cb32020f94a9332e643d2128b5c92209af312ababf5`에 적용할 전체 패치. CSS 인라인 추가, 표시용 카드 마크업 변경, UI 전용 script 추가. `patch --dry-run -p1` 통과.
- [design-craft.css](design-craft.css): 독립 스타일 원본.
- [dom-only.patch](dom-only.patch): CSS를 별도 통합할 경우에만 사용하는 DOM/script 패치. 전체 패치와 동시에 적용하지 않는다.
- [craft-ui.js](craft-ui.js): UI 전용 추가 코드. ID와 기존 버튼을 교체하지 않고 기존 알림 노드를 이동하며 좁은 화면의 단계 표시만 단축한다.
- [build_candidate.py](build_candidate.py): 정확한 기준 해시를 확인한 뒤 후보·패치를 재현한다. 공용 index.html에는 쓰지 않는다. 기준이 바뀌면 실패하므로 기능 작업 통합 후 맹목적으로 재실행하지 않는다.
- [manifest.json](manifest.json): 기준·후보 해시. [candidate-index.html](candidate-index.html)은 통합 참고용 생성본이며 그대로 공용 소스를 덮어쓰는 파일이 아니다.

기능 세션의 이미지 adapter/reconciliation 변경과 합칠 때 `drawExecutionCards`의 **마크업 부분만** 비교해 병합해야 한다. 동작 버튼의 data 속성·조건·원래 handler는 보존했다. 다른 함수·backend·서버·데이터는 수정하지 않았다.

## 달라진 내용과 참조

기존 [reference lock와 토큰 결정](DECISIONS.md)을 따른다. Krea의 중립 canvas와 흰 실행 CTA가 주 방향, Clipchamp는 미디어·타임라인 배치, ElevenLabs는 작업물 옆 검토 위계의 보조 참조다. Neural Frames의 [공식 Track](../structure/neural-official-track.png)·[공식 Storyboard](../structure/neural-official-storyboard.png)는 실제 제품을 담은 공식 튜토리얼 이미지이며 현재 직접 로그인한 편집기 캡처가 아니다. 새 경쟁사 조사·계정 조작은 하지 않았다. 값은 타사 CSS 측정치가 아니라 Loretune 제안이다.

1. 검토 영역을 배경보다 한 단계 밝은 표면으로 묶었다. 입력 경계와 구조 경계의 강도를 구분하고 검토 본문·설명을 12px에서 13px로 키웠다. 장면 제목은 16→20px, 모바일은 18px다. 기존 한국어 system font를 유지한다.
2. 실행 카드의 장면 제목과 승인 상태를 분리했다. **모델명, AI 아님, 공급자 비용 $0, 외부 전송 없음, 로컬 연산비 미계측**은 펼침 여부와 무관하게 남는다. 반복된 모의 방식 설명과 작업 영수증은 ‘모의 방식·작업 영수증’ 아래에 보존했다. 작업 상태가 `collected`가 아니거나 미확인이면 상세가 기본적으로 펼쳐져 진행·실패 정보가 숨지 않는다.
3. 일상적인 저장 연결 안내는 ‘저장 상태’로 접는다. 실제 알림 문구가 바뀌거나 error가 붙으면 자동으로 펼쳐진다. 기존 status/live-region 노드는 그대로 유지한다. 스크린리더 발표 동작은 별도 검증이 필요하다.
4. 모바일 단계·작업 탭의 패딩을 줄였으며 조작 target은 44px 이상을 유지한다. 320px에서는 ‘1 음악 / 2 계획 / 3 장면 / 4 출력’으로 표시하고 원래 전체 문구는 버튼 접근성 이름으로 유지한다.
5. 흰 CTA, 중립 선택 강조, 명시적 disabled·focus 상태, 8px 조작부/12px 패널 radius를 일관되게 적용했다. 초기 3선 브랜드 표식은 메뉴 버튼으로 오인할 수 있어 삭제했다. 기존 wordmark만 다듬었다. 외부 font·아이콘·장식 gradient를 넣지 않았다.

## 같은 프로젝트·viewport의 전후

이번 비교는 모두 `구조 통합 최종 QA 20261025`, 장면 제작 단계, 로컬 파란 단색 fixture다. 기존 실제 통합 화면과 후보 화면의 데이터는 같고, 미디어의 심미적 품질은 평가하지 않는다. 후보 이미지 파일은 저장한 뒤 직접 열어 확인했다.

|화면|실제 통합 before|검증 탭 candidate after|
|---|---|---|
|1280×900|[before](../fixed-release/desktop-scenes-1280.png)|[candidate](candidate-scenes-1280.png)|
|390×900|[before](../fixed-release/mobile-scenes-390.png)|[candidate](candidate-scenes-390.png)|
|320×900|이번 비교에서는 추가 before 없음|[candidate](candidate-scenes-320.png)|
|모바일 검토 탭|기존 UI 기능 유지|[candidate / focus 표시](candidate-review-390.png)|
|모델 설정|기존 선택·차단 사유 유지|[candidate](candidate-model-dialog-1280.png)|

|실측|통합 before|candidate|판단|
|---|---:|---:|---|
|Desktop 작업 영역 y|141|142|상단 구조 사실상 유지|
|Desktop 미리보기 bottom|542|548|6px 차이, 전체 노출 유지|
|Desktop 비교 버튼 y / 높이|556 / 36|560 / 40|조작부 가독성·target 확대|
|Desktop 검토 버튼 y / 높이|346 / 40|400 / 42|본문·폼 여백의 대가로54px 내려감. 첫 화면 유지|
|Desktop 타임라인 bottom|781|803|읽기 여백 확대, 첫 화면 유지|
|390 작업 영역 y|283|248|35px 감소, 약12%|
|390 미리보기 top / bottom|356 / 562|326 / 532|30px 상향|
|390 타임라인 bottom|821|806|첫 화면 유지|
|320 타임라인 bottom|이 pass의 before 없음|767|첫 화면 노출|
|페이지 가로 넘침|1280/390 모두0|1280/390/320 모두0|후보 stage nav의 내부 가로 넘침도0|

[실제 before 측정](../fixed-release/actual-geometry.json), [최종 후보 측정](final-geometry.json). 본문 확대는 정보량을 마법처럼 줄이지 않는다. 검토 CTA가 내려간 tradeoff를 함께 기록하며, 전체 작업 시간이나 클릭 수 개선을 추정하지 않는다.

## 검증과 남은 범위

- 모든 기존 ID 보존, 중복 ID0. 주요 `reviewTake/executionCards/render/saveTimeline/jobs` onclick 참조 불변. QA 프로젝트 JSON 불변. [검증 결과](checks.json).
- 390px에서 ArrowRight로 미리보기→검토 전환, 선택·포커스 함께 이동. 모델 대화상자 Escape 후 ‘모델 설정’ 버튼으로 포커스 복귀.
- 영수증 펼침 시 원문·영수증이 표시되고 비용 사실은 계속 보임. 임시 DOM 오류 문구는 자동 펼침/가시성을 확인했고 disabled 비교 버튼의 cursor·색·opacity도 확인했다. **이것은 서버 실패·네트워크 재시도 시험이 아니다.** 실제 데이터를 바꾸지 않았다.
- `collected/failed/running/queued/미확인` 5가지 영수증 렌더 분기와 비용이 상세 밖에 남는 것을 격리된 렌더 테스트로 확인했다. [결과](receipt-render-checks.json). 마지막 ‘미완료 작업은 기본 펼침’ 조건은 DOM 캡처 이후 추가했지만, 캡처된 collected 상태의 마크업/표시 결과는 동일하다. 실패/진행 상태의 실제 브라우저 pixels는 미검증이다.
- 전체 후보의 JS 3블록 문법 검사와 패치 dry-run 통과. 실행 서버·공용 소스 해시는 종료까지 고정값 유지. [종료 기록](end-version.json).
- 현재 stage3 중심의 bounded pass다. 통합 후 단계1/2/4, 일반 채팅, 유료 견적/승인, 실패·복구, 긴 모델명, 다중 장면/다중 후보에 대한 회귀가 필요하다. 새 provider 카드에 이 mock 전용 `$0` 표현을 복사하면 안 된다.
- 실제200/400% 브라우저 확대·스크린리더·실사용자 시험·모든 contrast 조합은 미검증. 320px viewport를 확대 검사로 주장하지 않는다. 실제 경쟁 제품과 같은 조건의 사용성 시험도 아니다.

## 통합 시 수락 조건

전체 패치 또는 DOM+CSS 중 한 경로로만 통합한다. 기능 세션 변경과 기준 해시 차이를 먼저 확인한다. 기존 로컬 제작 회귀를 수행하고, 오류·진행·실패가 접힌 정보 뒤에 숨지 않는지 확인한다. 같은 QA 프로젝트의 desktop/390px에서 이번 미리보기·비교·타임라인 기하와 필수 조작을 확인한다. 통합본을 새 캡처한 뒤에만 사용자에게 현재 화면으로 전달한다.

부족한 점은 남는다. 검토 패널은 여전히 텍스트 비중이 크고, 기본 네이티브 select·단순 타임라인의 한계는 이 pass가 해결하지 않는다. 이번 결과는 읽기와 일관성을 개선한 후보이며 경쟁사 수준의 완성이나 점수 상승을 보장하지 않는다.

Ego Lite0.6.0.20 / guide2.1.0 / 전용 Space10으로 검증했고 종료했다. 업데이트 알림은 있었지만 설치·권한 변경은 하지 않았다.
