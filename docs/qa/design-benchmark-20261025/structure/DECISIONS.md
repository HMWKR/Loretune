# 구조 개선 reference lock · 2026-10-25

사용자 요청: Neural Frames의 실제 작업 화면을 기준으로 비교하되 Loretune의 IP·계획·승인 흐름에 맞게 적용. 공용 index/JS/backend를 직접 바꾸지 않는다. 기존 무채색 브랜드와 semantic token을 유지한다.

## 근거와 한계

- **현재 직접 관찰**: 인증된 Neural Frames `/videos`는 정상 접근되며 All 목록은 비어 있다. 새 프로젝트·생성 없이 열 기존 editor를 확인하지 못했다. 로그인벽이 아니다. 이름 없는 버튼이나 생성 진입 컨트롤은 조작하지 않았다.
- **공식 튜토리얼 이미지(V)**: [Autopilot handbook](https://help.neuralframes.com/en/articles/12038142-handbook-the-four-stages-of-autopilot)의 Track, Storyboard 원본 이미지를 저장하고 열었다. 원본 3194×1494 / 3210×1690. 2026-04-09 파일명의 설명용 캡처이며 현재 계정의 실시간 editor가 아니다. 원본 UI viewport/DPR는 미확인. 보라색 번호는 튜토리얼 주석이지 제품 accent token이 아니다.
- **기존 Refero(R/V)**: system/DECISIONS.md의 Krea style와 Clipchamp editor, ElevenLabs 검토·출력 screen을 재사용. 기존 사용자 승인된 자료이며 신규 관찰이라고 표시하지 않는다.
- **Loretune(M)**: 8773, 기존 `디자인 통합 완주 QA 20261025 1100` fixture. 구조 변경 전 실제 화면을 새 캡처한다. 후보는 같은 페이지의 임시 DOM/CSS preview이며 소스 통합본이 아니다. 단색 fixture의 미적 품질은 평가하지 않는다.

## 가장 큰 세 차이

1. NF는 짧은 단계 표시와 작업물 중심으로 이어진다. Loretune은 로고·프로젝트·단계·현재 설명·전체 요약·저장 안내·모델 줄이 연속되어 작업 영역이 약317px에서 시작한다.
2. NF Storyboard의 장면 이미지와 개체 chip은 장면별 맥락을 만든다. Loretune은 작은 rail, 큰 preview, 긴 아래쪽 inspector가 분리되어 검토 조작이 첫 화면 밖으로 밀린다.
3. NF는 모델·비용·주 실행을 우측 한 영역에 모은다. Loretune의 선택·검토·모의 실행·비용 승인을 하나로 합치면 안 되지만, 현재 선택 작업의 검토와 실행 조건은 미디어 옆에서 읽을 수 있어야 한다.

## 채택·배제·적용

|결정|출처|채택|배제/이유|
|---|---|---|---|
|기존 무채색 토큰 유지|Krea R + 기존 Loretune M|canvas/raised/media 역할, 흰 실행 CTA, 14px 본문|NF coral branding·보라색 주석 복제 금지|
|하나의 compact project shell|NF V + 사용자 지시|프로젝트/설정/모델 진입을 한 줄, secondary 상태는 disclosure|여러 층의 반복 안내와 과장된 제품 상태|
|rail / preview / inspector + timeline dock|Clipchamp V + NF 장면/실행 맥락 V|184px / 유동 / 288px, 미디어와 review 동시 표시|모든 기능을 같은 검정 테두리 카드로 세로 나열|
|Loretune 승인 분리|사용자 도메인 요구|Take 검토, 계획 승인, 실행 승인, 출력 승인은 ID와 handler 보존|NF 생성 단축 흐름을 승인 없이 복제|
|mobile 작업 focus|사용자 지시 + craft|장면 / 미리보기 / 검토 선택, 한 패널씩, 44px targets|desktop 3열을 모두 길게 쌓기|
|정밀 편집 disclosure|Clipchamp timeline V + 현 기능 제약|실제 track/status는 먼저, 숫자/음원/자막/복원은 펼쳐서 접근|가짜 waveform·playhead·미지원 drag 기능 추가|

## 제안 geometry(P)

Desktop1280×900: shell56 + stage56 + status30 이하, 작업대 top≤160. rail184 / gap16 / center 유동 / gap16 / inspector288. preview 높이≤324(36vh), 실제 영상 비율은 contain. takes와 비교는 한 줄, timeline overview 첫 화면 안에 포함. inspector는 독립 scroll이며 필요 항목만 펼친다.

Mobile390/320×900: shell 두 줄 이내 → 단계 가로 strip → status → 작업 focus tabs. 기본 preview, 장면 선택 뒤 preview로 이동. 설정은 같은 데이터와 handler를 유지하며 별도 panel에서 접근. 실제 media와 timeline은 축소된 desktop 복사본이 아니라 현재 과업만 노출한다.

## 검증 판정

전후 동일 프로젝트/step/viewport, CSS 실측 너비 기록. 경쟁사 튜토리얼은 이미지 비율로만 비교하고 동일 viewport 성능 시험으로 주장하지 않는다. 실제 브라우저 200/400% 확대·screenreader·실사용자 시험은 미검증 유지. 통합 전 후보 시각 검증과 기능팀 통합 후 회귀를 구분한다.
