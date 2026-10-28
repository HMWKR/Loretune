# 도구·Evidence 장부

| 도구 | 대상 | 결과 | Evidence ID | 한계 |
|---|---|---|---|---|
| mcp__REA__binary_session | REA 서버 | 6.7.0 정상 응답, open:false cleanup_pending:false | 없음 | 제품 분석·이전 워커 정리 완료 증거 아님 |
| mcp__REA__inspect_analysis_view | 이전 보존 ID | evidence_integrity_mismatch (missing) | 새 ID 없음 | 현재 서버 세션에 이전 기록 없음; 변조 판정 아님 |
| mcp__REA__analyze_javascript_application | Neural Frames 공개 JS3개 | cleanup_incomplete, reader_failure, retryable:false | ev_1a6e8701a11c0a4085a4c1fe5b69a4e02a53d54a349e51a4f81f5fa2584ddab7 (부분) | 전체 호출 실패; 추가 분석 중단 |
| mcp__REA__inspect_analysis_view / summary | 이번 부분 Evidence | 성공 | ev_9b683d37018636a971403cc2f1d7402f8efcbf8dca1977840f70363c4fa94e05 | JS3개·52769바이트·7모듈, partial/unknown |
| mcp__REA__inspect_analysis_view / modules references | 동일 부분 Evidence | 페이지 조회 성공 | ev_c00cad6a6e7e318acb4465d347318c6348ff131502ced1dac668c4c88faae7bf | 16/89 참조 페이지. 89는 복원 모듈 수가 아님 |
| mcp__REA__export_evidence_bundle | 현재 보존 기록 | 3건·12585748바이트 export 성공 | 별도 신규 분석 ID 없음 | 원본은 별도 로컬 보존. 사용자용 ZIP에 포함하지 않음 |
| Aside 일반 브라우저 snapshot/locator/screenshot | 12개 서비스의 제한된 화면 | UI·무료 조건·차단 관찰 | REA ID 없음 | 모든 기능·실제 완성 영상·서버 내부 미검증 |

Neural Frames의 AST와 모듈 후보는 클라이언트의 정적 관찰이다. 동적 실행·네트워크 요청·서버 모델 연결을 증명하지 않는다. 나머지11개 서비스는 REA 제품 분석 미완료이다. [최소 지원 오류보고서](rea-support-report.md)를 참고한다.
