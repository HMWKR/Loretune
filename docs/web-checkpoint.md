# 로컬 웹 단계 검증 — 2026-10-25

프로젝트: /Users/leesungmin/Desktop/Loretune
변경: app.py, index.html, tests/test_app.py, README.md. 기존 loretune.py, tests/test_workflow.py와 원본·.env·.codex 보존.

디자인: 외부 서비스 금지에 따라 Refero live 검색은 하지 않음. refero-design의 bundled craft-details (명시 label, focus-visible, 로딩/오류 상태, semantic forms)를 기준으로 직접 구현. 흰 작업면·짙은 녹색 CTA, 좌측 승인 기준/작품 생성, 우측 샷 작업/출력의 기능 중심 방향을 채택. 기존 구현 디자인 없음. feature-verification 지침 적용.

Ego Lite 0.6.0.20 / CLI 가이드 v2.1.0, task space 0에서 http://127.0.0.1:8765 실제 UI 검증. 승인 설정, 작품 생성, 샷 생성, 이미지 업로드, take 1 선택, 이유를 달리한 take 2 추가/선택, 실제 MP4 출력, 다음 작품 생성 및 설정 재사용 완료. 샘플은 명시적으로 '화면 검증' 이름으로 남김. 외부 이미지/모델 사용 없이 FFmpeg color fixture 사용.

1280×900, 375×812 스크린샷 직접 확인. 375px에서 scrollWidth=375. 전체 페이지를 캡처한 것은 아니며 표본 viewport 시각 확인. 자동 접근성 검사와 성능 지표는 미측정.

서버 프로세스를 종료하고 같은 data 경로로 재시작한 뒤 브라우저 reload: 두 작품, 승인 스냅샷, Take 2 선택 보존 확인. 브라우저 결과 탭은 사용자 계속 작업을 위해 남김. 실행 서버 세션 87181 (런타임 종료 시 사라질 수 있으며 README 실행 명령으로 재시작 가능).

10개 테스트 skip 없이 통과. HTTP 실제 200/400/403/409/404 응답, 동일 요청 중복 반환, SQLite 동시 작성자 1개 성공/1개 충돌, 롤백, 재연결 보존, 실제 렌더 및 ffprobe 3초 확인. 첫 HTTP 테스트는 sandbox bind 제한으로 실패했고 승인된 localhost 실행에서 성공. 자동 승인 거절 없음.

남음: 음원 결합, 가변 샷 길이, 타임라인, 자막/전환, 다중 IP와 사용자/권한, 작업 큐/진행률, 실제 모델 연동, 제품 전체 명세. 원본 지식 CLI와 비용 모델 테스트는 미실행. 공급자 호출·유료 생성·배포·push·환경변수/자격 증명 변경 없음. Ego Lite 업데이트 알림을 받았으나 업데이트하지 않음.
