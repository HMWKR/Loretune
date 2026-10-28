# 독립 감사 중요 체크포인트

2026-10-25. 실제 소스 수정/공용DB 변경/외부 호출/키 조회 없음. `snapshot-manifest.json` 시점의 코드에만 적용. 개발 중 최신 코드 해결 여부는 별도 확인 필요.

1. **F01 High / 제출 직전 권리 철회 미검사**: 정상 Store API로 PNG 업로드→참고 승인→준비→서버 synthetic gate로 큐 등록→`asset_rights blocked=True`→`process_generation()`. 사용권 blocked=true인데 fake submit 1회, accepted. app.py:620–621은 gate 만료만 검사하고 generation_queue.dispatch는 quote 만료만 검사. MS-AT34 / MS-FR23, FR016/018. 입력 hash/권리와 grant identity를 제출 직전 재검사하고 미전송 예약 처리 필요.
2. **F02 Medium / 늦은 취소 실패가 완료 결과 유실**: send_cancel이 cancel_sent 저장→fake cancel 안에서 poll 완료(cancelled_result/result URL)→cancel TimeoutError. 예외 처리에서 오래된 job 저장하여 cancel_sent/result null로 회귀. generation_queue.py:159–168. MS-AT32 / FR051. 예외 트랜잭션에서 latest 재조회하고 오류 필드만 변경.
3. **F03 Medium / 온톨로지 관계 변경 영향 누락**: character references asset A 승인→character bind→동일 entity 유지, relation target만 B로 승인. graph digest 변경에도 impact=[]; semantic_context에는 revision/entities만 있고 관계 없음. project_ontology.py:55–66. FR024/023. 사용 관계/의존성 hash와 스냅샷 보존 필요. 현재 수동 UI는 관계 작성이 없어 그래프 모듈 수준 반례임.
4. **F04 Medium / 합법 컷 길이 누적 오차**: 0.130초 정지영상 30개를 24fps로 렌더. 요청 3.900초, 실제 3.750초, verify_output 실패. editing.validate는 0.125초 이상 허용하지만 각 컷을 프레임으로 양자화하고 총 timeline은 초 합 사용. renderer.py:59–82. FR056/067, MS-AT28 관련 하위 계약. 프레임 단위 타임라인 정책 필요.

실행: `PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-audit-20261025/reproduce.py`
증거: `counterexamples.json`, 네트워크 차단 포함 재현 코드 `reproduce.py`, 원본 해시와 snapshot. F01 전체 local Store 경로; F02 deterministic event interleaving; F03 graph module; F04 real local FFmpeg. 고객/실공급자 시험 아님.

진행 상태: 감사 완료. REPORT.md / 28FR·38AT 매핑 작성. 대조 회귀67개 통과. F02는 현재 단일 worker UI 도달 미입증인 모듈 경합이며 F03은 그래프 모듈 수준. HTTP bind 시험1건 환경 거부로 제외.
