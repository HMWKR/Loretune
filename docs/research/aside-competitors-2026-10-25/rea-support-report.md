# REA 6.7.0 지원 요청용 최소 오류 보고서

## 증상

Aside에서 mcp__REA__binary_session은 성공한다. mcp__REA__analyze_javascript_application은 공개 JavaScript의 부분 결과를 남기지만 cleanup_incomplete로 실패한다. 같은 입력의 새 허용 시도에서도 재발했다. 추가 실행·프로세스 조작은 중단했다.

## 환경과 입력

- macOS arm64; REA/rea-agents 6.7.0, Aside MCP client aside-browser 1.26.1024.24.
- 분석 형식 directory. Neural Frames 공개 페이지에서 받은 index-101cccd2a3df7a34.js, Login-bf41993a33b74436.js, _buildManifest.js.
- 선택 입력 총 52,769바이트. 공개 텍스트만 대상으로 하며 비밀·쿠키·계정 데이터는 입력하지 않았다.
- detail: summary, analysis_timeout_ms:30000, max_heap_mb:512.

## 정확한 오류

code: cleanup_incomplete; category: execution_failure; retryable:false.
provider_id: javascript-static-analysis; operation: analyze_javascript_application.
진단: process ownership token could not be read for 1 live process(es): reader_failure=1; live candidates 22118=reader_failure.
worker_pid:22118. PID는 오류 발생 당시 식별자이며 현재 소유권/생존 여부를 보장하지 않는다.
공식 응답: Provider cleanup could not be fully confirmed. Review the reported local resources before opening another target.

## 수행한 확인

현재 binary_session의 open:false/cleanup_pending:false는 이전 워커 정리 완료를 보장하지 않는다. 새 분석 실패 후 보존 Evidence의 요약·모듈 참조 조회와 정식 번들 export는 성공했다. 과거 ID만 조회한 missing 오류와 새 호출의 cleanup 오류를 구분했다. ps 접근 거절을 우회하거나 종료 명령을 실행하지 않았다.

## 재현 정보와 사용자가 할 수 있는 다음 행동

지원팀에 버전·도구명·공개 입력 파일명·위 오류를 전달하고, macOS reader_failure의 지원되는 진단 방법과 소유권 확인/정리 절차를 요청한다. 이 문서는 지금 같은 분석을 반복하라는 실행 지시가 아니다.

공식 설치 문서는 일부 바이너리 제공자의 실패 원인 처리 후 같은 연결에서 close_binary를 재시도하는 흐름을 설명한다. 이를 JavaScript 워커에 적용해도 안전한지 확인되지 않았고 close_binary는 세션 자료 폐기 효과가 있으므로 실행하지 않았다. 설치·권한 변경·PID만을 근거로 한 종료·임시 폴더 삭제를 해결책으로 권하지 않는다. 필요한 조치는 지원팀이 해당 워커의 소유권과 제공자별 정리 동작을 확인한 뒤 정해야 한다.

공식 근거: https://github.com/morluto/rea/blob/main/docs/installation.md 및 실제 MCP 오류 응답. 원시 인증 응답·내부 대화·개인 경로는 이 문서에 포함하지 않았다.
