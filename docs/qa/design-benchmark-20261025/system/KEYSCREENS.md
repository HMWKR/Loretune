# Desktop / Mobile 핵심 화면 사양

값은 Loretune 제안(P)이며 경쟁사에서 그대로 측정한 값이 아니다. 최대폭은 고정폭 강제가 아니며 긴 한국어/확대 시 자연 재배치한다.

## 공통 shell
Desktop1280×900: brand row48→project/mode row약56→단계nav56→현재단계+요약+next 동일행→status30→modelsummary52→workspace. 목표는 media top≤400,첫 media와 비교 진입이 함께 보이기. dense mode로 글자를12px 미만 축소하지 않는다. 모델 수정은640max dialog, 배경 pane을 밀지 않는다.
Mobile320/390×900: brand→projectselector→mode→2×2stage→단계설명/next→status/model summary→작업. 최소44px 대상. 모델dialog는viewport-32, 내부 scroll. 전체 모델명은 선택기 밖 문단. 작은 화면에서 모든 정보를 한 화면에 우겨 넣지 않는다.

## 1 음악
첫 구간 미확정: 음원 연결→player/실제 파형→start/end가 핵심. 미확정 disclosure 자동 열기/직접 이동은 기능팀 패치 필요. 원본 길이·구간 버전·분석 범위를 명시. fake waveform 장식 금지.

## 2 채팅·계획
Desktop≥1100: 왼쪽 brief/대화 minmax0,1fr,오른쪽 계획 minmax0,1fr, gap24; heading full width. 현재 CSS는 **기존 brief+계획 카드**만 2열로 만든다. 실제 chat UI나 스트리밍은 생성하지 않는다. Plan에는 source music window,각scene timing,entity versions,조건,승인범위. 긴 카드에서는 페이지 scroll; 고정 높이로 마지막 승인 버튼 가리기 금지.
Mobile: 입력→검토 순서. 긴 plan은 설명/scene list 유지. primary 승인과 다음단계 이동을 혼동하지 않도록 조건을 표시. 계획 version의 승인≠유료 실행 승인.

## 3 장면·검토
Desktop: 좌측220 보드; 중앙 media max720×405(16:9),portrait max300; media 아래 takes와 compare; inspector는 현재 전체폭 아래(기능 DOM 현재 구조). 최종 inspector를 오른쪽으로 옮기려면 충분한가로폭≥1440에서240px별도pane와 같은 DOM focus order 검증 필요. 이 후보에서는 강제3열로 만들지 않음.
Mobile: 보드 compact/horizontal strip→선택된 장면 제목→media→takes→선택/승인/참고/IP. 빈 보드만 제목과 샷추가를 같은행. 실제 샷 목록/열린 추가폼은 원래 순서 유지.

## 4 편집·출력
원곡구간과 타임라인총길이 상단. numeric trim/timecode를 유지하고 track은 가로scroll 영역. 선택media thumbnail/자막/음원 track의 의미는 text로도 전달. 우측/아래 quote card에는 model release와 비용/만료/승인범위. 출력 완료와 사람 납품 검토는 다른 배지. 생성버튼 클릭 없이 UI를 완료 표시하지 않는다.

## 전후 수락 rubric
0=부재/실행불가,1=큰마찰,2=기본가능+명확한마찰,3=관측한 고정 fixture에서 명확,4=관련 전체상태와 실사용자검증까지. 실사용자조사 없는 이번 후보는4 부여금지. 총점 평균으로 미검증을 가리지 않는다.
- 위계: 현재단계/작업물/대표행동3개를 혼동 없이 찾는가?
- media:1280에서 media 전체+다음 조작 일부 동시 노출;비율/contain 불변.
- 일관성:같은역할의버튼/카드/type/radius가 token에 일치하는가?
- 상태:선택/승인/실행/수신/실패/비용 상태가 각각 text로 구분되는가?
- 반응형:가로overflow0(의도한timeline/strip 제외),focus clipping0,44pxmobile.
- 회복:에러후입력보존,조건해결·재시도진입명확,unknown재실행금지.
- 접근성:실제zoom/keyboard/screenreader 검사없으면 미검증 유지.

baseline/candidate는 동일페이지·동일작품·동일viewport·같은state·동일reduced-motion 조건으로 캡처하고 HTML/CSS hash를 남긴다. 이번 임시탭 CSS validation은 실제 소스 통합이나 backend회귀의 대체가 아니다.
