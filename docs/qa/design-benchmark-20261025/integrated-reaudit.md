# 8773 통합본 재감사 · 2026-10-25

핵심: 제목/주 행동/모드 선택은 개선됐다. 미디어가 중심인 작업대 수준에는 아직 미달한다. 모델 설정을 열면 1280×900에서도 preview 시작 y=964.6으로 화면 밖이다. 320px에서는 y=1387이다. 단순 색상 교체보다 상단 정보 압축과 작업 영역으로 모델 설정 이동이 우선이다.

## 실행본·소스 일치성 정정

부모의 후속 인계에 따르면 contract fixes 4개는 소스에 적용됐지만 8773 서버는 재시작되지 않았다. 따라서 이 보고서는 **CSS/세 모델 1차 통합본을 실행 중인 8773에서 관측한 UI**에 한정된다. 최신 contract fixes의 런타임 동작·UI 회귀 통과를 의미하지 않는다.

첫 Ego 연결 시도 로그는 2026-10-25 18:48:10(호스트 로그 시각). 정확한 served backend commit/revision 및 전체 감사 종료 시각은 수집하지 않았다. 캡처 파일 mtime은 아래 증거 메타데이터에 기록했으며 브라우저 관측 순간의 정밀 timestamp나 코드 revision을 대신하지 않는다.

app.py는 GET `/`에서 index.html을 디스크에서 읽으므로, 서버 재시작 없이도 새 HTML/CSS와 이전 Python 런타임이 섞일 수 있다. 관측 뒤 바뀐 현재 소스를 곧바로 당시 served UI로 간주하지 않는다. 독립 QA의 `미검증` 항목과 최소 수정 제안은 기능 세션 최신 수정 여부를 대조한 뒤 적용해야 한다.

HTTP bind 테스트 17건 거절 이슈는 부모 인계 사실이며 이 디자인 세션이 직접 재현한 결과가 아니다. 서버 재시작·다른 port 신규 listener·우회 없음. 이번 정정에서는 추가 HTTP 또는 브라우저 요청도 하지 않았다.

## 전후와 수치
기존 Chrome 873×819 대비 Ego 873×819를 캡처했다. 기존은 음원/샷/테이크가 있는 `화면 검증 첫 곡`, 새 서버는 빈 `MS 계약 검증 A`이므로 미디어 크기·콘텐츠 총 높이의 직접 인과 비교는 불가. 같은 UI 부분의 제목 20px, 좌측 정렬, 흰색 다음 버튼, 선택 모드 밑줄은 확인했다. 통합 main top=462.1px. 이전 캡처의 공통 chrome 하단 약428px보다 낮아졌다(신규 모델 행 추가 영향 포함).

## 휴리스틱 rubric (실사용자 실험 아님)
0=수행 불가/부재, 1=큰 마찰, 2=기본 가능하나 명확한 마찰, 3=확인한 상태에서 명확, 4=전체 상태와 실사용자 검증. 전체 평균은 미검증 항목을 감추므로 산정하지 않는다.

|항목|통합본 점수|화면 근거|
|---|---|---|
|제목·다음 행동 위계|3|03/04 제목·흰색 CTA 명확|
|미디어 우선 레이아웃|1|model-1280에서 preview 화면 밖|
|빈 상태 다음 행동|2|04 첫 샷 안내 있으나 추가가 접힘, 하단 무관한 폼 계속 노출|
|모델·승인 설명|3|model-320 별도 미연결 설명, plan-review 비용 승인 분리|
|초보/상세 모드 인지|3|모드 밑줄+pressed 상태|
|모바일 재배치|2|320/390 가로 overflow 없음, 세로 탐색 부담 큼|
|키보드|미평가|skip→heading→next와 modal Escape 복귀만 확인|
|오류·로딩·400%|미평가|실제 전이/배율 미확인|

## 재현 결과
- 320/390/1280: document.scrollWidth=innerWidth. 긴 모델명 native select는 잘리지만 독립 상태 설명은 줄바꿈됨. `integrated-metrics.json`.
- skipFlow Enter: focus flowHeading, 흰색2px outline. Tab: flowNext 흰색2px outline.
- 새 작품 모달 열기: 닫기 버튼 focus. Escape: newProject 복귀. 제출하지 않음.
- 기존 계획 v1 검토 카드: 장면 2개/길이 미정/음원 필요/계획 승인≠유료 승인 표시. 승인 클릭하지 않음.
- reduced-motion CDP emulation: matchMedia true, button animation none. 운영체제 설정 자체는 변경/검증하지 않음.
- 브라우저 확대 단축키4회: innerWidth1280/dpr1/visualViewport.scale1 불변. 200/400% 실제 확대 성공으로 인정하지 않는다. 320 viewport는 400% 확대를 대체하는 증거가 아니다.
- 로딩/네트워크 실패/full keyboard production journey/스크린리더/모든 상태 대비/실제 미디어 preview 재생은 미검증. 새 생성 실행 금지 때문에 생성 전이를 누르지 않았고 기존 출력 fixture도 이 서버에서 확인하지 못했다. 기존 기능팀 테스트를 독립 증거로 대체하지 않는다.

## 최소 수정 전달
`integration-followup.patch` 및 기존 design-polish.css에 모델 패널 gutter/읽기 폭/행간 3개 규칙 추가. 후속 CSS는 아직 통합·렌더 검증 전. 모델 설정 row를 상단에서 다른 위치로 이동하거나 미디어를 숨기는 강제 CSS는 넣지 않았다.
기능 구조 결함 우선순위: (1) 빈 샷에서 #prepareGeneration/#assignReference/#reviewReference/#reviewTake 비활성화 및 이유 연결, (2) 음악 미확정이면 다음 버튼 근처 확정 진입 링크, (3) 모델 설정을 작업물 위 대형 폼 대신 요약+별도 편집 패널로 전환. 현재 기능 스레드가 수정 중이므로 동시 DOM 덮어쓰기 금지.

## 증거 목록
03-integrated-music-873.png / 04-integrated-scenes-873.png / integrated-model-320.png / integrated-model-390.png / integrated-model-1280.png / integrated-plan-1280.png / integrated-plan-review.png / zoom-attempt.png. 03/04/320/1280/plan/plan-review 파일을 image viewer로 열어 검사. 390와 zoom-attempt는 캡처만 있어 시각 수락 전.

## 도구 및 한계
이번 턴에는 CUA 도구가 노출되지 않아 Ego CLI의 실제 guide를 읽고 사용. 첫 sandbox 실행은 Mac XPC/launch 실패, 동일 작업 승인된 escalation 후 성공. 거절 없음. TaskSpace3만 사용하고 finish keep[] 성공. 사용자/기능 탭 접촉0, 데이터 쓰기0, 서버 재시작0, 호출/업로드0. Ego Lite 업데이트 안내가 있으나 설치/업데이트하지 않음.

남은 작업은 단순히 CSS 전달로 완료되지 않는다: 위 미검증 상태 및 실배율 검사, 실제 미디어가 있는 독립 fixture, 후속 CSS 렌더 검증이 필요하다. 부모가 기능 수정 완료 이후 같은 서버/fixture 조건으로 재개할 수 있다.
