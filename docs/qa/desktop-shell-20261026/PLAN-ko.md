# 1920 우선 작업 공간 조정

> 계획 실행 결과는 [REPORT-ko.md](REPORT-ko.md)에 고정했다. 전체342회귀 및 실제1920 열린 편집/긴 패널/키보드 표본을 통과했다. 아래는 구현 전 계획이며 독립 최종 디자인 점수의 근거로 단독 사용하지 않는다.

기준: JS ae019c88(독립 DM01–03 종료), CSS f6f9ebff, HTML846e18d4. 사용자 요청은 작업 화면의 document 세로 스크롤을 줄이고 상세 내용만 해당 영역에서 접근하는 것이다.

- 관측:1920 기본/sequence는scrollHeight1080; 정밀편집 펼침은1710. 단순 전체overflow:hidden은 입력·포커스를 가릴 수 있어 제외한다.
- 선택: 단계3/4, 충분한창, 앱100%에서 viewport flex shell. 기존 노드/이벤트를 유지한 미디어 영역·타임라인과 장면/검토 내부 scroll을 사용한다. 작은창/확대글자는flow로 돌아가며 내용 접근을 보존한다.
- timeline: 원래공통x좌표 유지. 표시 라벨만 실제 너비로 간소화하며 시작/끝 보존. tick시간·clip폭·waveform·playhead·재생코드는 변경하지 않는다.
- control:기존32/28px desktop조작을36px역할토큰으로 올리되 글자를 줄이지 않는다.
- 검증:1920 default/sequence/expanded/output/longpanel/keyboard;1280aux;200% reflow·눈금간격;초안·취소·context;미디어hash불변;전체회귀. 새 API호출/사용자데이터변경 없음.
- 참고:기존 승인 reference-lock(Descript 시간정렬, Frame.io 미디어/선택인접, Runway 중성shell) 재사용. 경쟁사전부무스크롤이라는주장 없음. 새1920 시각rubric은독립디자인담당과별도.
