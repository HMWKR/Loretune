# REA 연결 상태와 공개 벤치마크

확인일 2026-10-25. REA CLI /opt/homebrew/bin/rea 6.7.0, 스킬 /Users/leesungmin/.agents/skills/reverse-engineer-anything/SKILL.md.

사실: 현재 ALL_TOOLS에서 __rea__, inspect_analysis, analyze_javascript, capture_browser_scenario 이름을 검색했으나 REA MCP 도구 없음. `rea doctor --client codex --json` 승인된 실행에서 Codex registration healthy, Node 26.11.1 healthy. 설정 내용/비밀 값을 출력하거나 변경하지 않음. 첫 sandbox 진단은 Swift 캐시 쓰기 제한으로 실패했으며 승인된 재시도로 진단 완료.

공식 로컬 안내 references/connection-and-recovery.md: “Aligned registration, but no connected tools → Restart/reconnect the client. Doctor checks registration; it cannot establish the current agent's connection.” 따라서 재연결/새 세션이 다음 확인 단계이나 성공은 아직 검증되지 않음. 현재 도구에는 MCP 재연결 액션 없음. 사용자가 REA가 실제 노출되는 새 실행 세션을 열거나 클라이언트를 재연결한 뒤 도구 노출을 확인해야 함. 특정 UI 버튼은 확인되지 않아 추측 안내하지 않음. 재설정·인증 변경·엔진 설치 불필요.

Ego Lite로 https://www.krea.ai/ 와 /video 공개 화면 관측: 공통 좌측 탐색, Video composer의 Add image/video/audio, 모델 선택, 시작/끝 프레임, 6s 길이, 16:9 표시, Sign in. 영상 생성은 누르지 않았으며 로그인 불필요 범위까지만 확인. 이 관측은 실제 UI이지 서버 구조 증거가 아님.

브라우저 performance에 실제 나타난 자체 entry/chunk 경로 2개를 로컬 정적 분석 입력으로 확보하려 했으나 첫 직접 HTTP 요청이 거절되어 파일 0개. 접근 제한 우회/동일 요청 반복 안함. 이어 실행된 REA CLI 분석은 빈 디렉터리를 분석했으므로 경쟁사 구현에 관한 유효한 Evidence가 아님. ev_452bf1935631ebd9170a26df44dcf5835c8922d5de826ba589c1f90d847112b6를 제품 분석 성공으로 사용하지 않음.

MCP 실행은 미실행/연결 대기. CLI 설치·doctor 성공과 MCP 노출은 별개. DB, 큐, 스토리지, 모델 routing, 성능, 로그인 이후 상태는 UNKNOWN. Refero 조사는 별도 design-reference-lock.md와 design-ux-benchmark-ko.md에 기록.
