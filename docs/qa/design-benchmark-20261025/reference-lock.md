# Reference lock · 2026-10-25

목표: 기존 Loretune 무채색 제작 작업대를 유지하며 현재 단계·작업물·다음 행동 위계를 개선. 기능/데이터 변경 없음.

주 방향은 기존 Loretune + Refero Krea style 3a63b3fa-dc79-4dc3-935e-3f8f4ab447a7. 검정/회색 표면, 흰색 주 행동, 8px 모서리, 시스템 한국어 폰트 유지. 마케팅 대형 헤드라인·그라데이션은 가져오지 않는다.
보조는 Pika ec19c3ae-5e48-4b90-996f-9433c7cf4aa7의 미디어 contain 처리만. 크림색·로그인 레이아웃 제외.
Clipchamp flow https://refero.design/flows/10860: 미디어→미리보기→타임라인 순서와 선택 후 속성 편집. ElevenLabs https://refero.design/flows/8684: 흐름 상세 조회 근거는 refero-1.json. 실제 서비스 수행 검증과 구분.

|결정|근거|역할|
|---|---|---|
|단계 제목 20px, 설명 14px|Krea type scale + 현 화면 제목 구분 부족|현재 작업 우선|
|상단 세로 padding 축소|01/02 캡처에서 상단 약 428px 점유|콘텐츠 공간 회복|
|다음 행동 흰색|기존 primary + Krea CTA|진행 행동만 강조|
|장면 단계 넓은 화면에서 보드/미디어 2열|Clipchamp editor 흐름|작업물과 선택 맥락 동시 확인|
|한국어 줄바꿈, minimum 44px disclosure|사용자 확대·모바일 요구|조작 가능성|

CSS는 통합 후보다. 실제 서버에는 CSS 정적 라우트가 없고 index/백엔드는 기능 스레드 소유이므로 통합 후 실화면 확인 전 개선 완료 판정 금지.
