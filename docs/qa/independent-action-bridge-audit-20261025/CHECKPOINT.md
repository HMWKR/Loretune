# 새 action bridge 독립 감사 체크포인트

새 snapshot 기준, 소스수정/키조회/실API/HTTP listener0. audit.py / audit-results.json.

**B01 Medium 기능 연결 결함:** 정상 Store production_tool→persisted action job receipt 생성 후, scoped action_jobs를 chat_protocols.handoff(project,'A',jobs)에 주면 jobs=[]로 반환. 새 action_jobs body에는 context.song이 없지만 handoff는 기존 generation_jobs용 context.song만 필터함. MS-FR11 / MS-AT18,22. 이미 DB에 있던 job을 handoff에서 잃으며 새로 생성했다는 증거는 없음. 현재 UI/live handoff는 미연결이므로 함수 통합 반례다. 수정: 서버가 workspace/project 소유권으로 필터한 공통 job projection(내부id/state/mode)을 넘기고 각 job형식을 지원. 무조건 모든 job을 넘기는 수정 금지.

**B02 Medium 복구/도구 응답 계약:** 실제 Store에서 존재하지 않는 action_id를 다른 tool call ID로10회 요청. 각 ValueError는 거부하지만 run은 accepting_tools, repair_count0,calls0. production_tools는 schema validate만 repair 집계하고 request_generation callback의 semantic error가 Store 트랜잭션 전체를 롤백해 도구 결과/카운터가 남지 않음. MS-FR07 / MS-AT12. 외부API/예약/job 생성0. 새 모델 루프가 붙기 전 고칠 유한 오류/구조화 결과 누락이며 현재 유료 폭주를 주장하지 않음. 수정: semantic errors를 분류한 ToolResult로 기록하고 수정가능한 인수 오류의 횟수 제한, 실행 side effect는 savepoint로 rollback. 승인필요/일시적오류는 잘못된인수와 구별.

대조: 단일 action의 다른 call id→동일job/예약1, 동일call id 다른action→Conflict, grant철회 차단, action input/model 및 grant money 변조 거부, settings 변경 거부, role/endpoint 인수 거부, 권리 false claim→blocked/released, claimed 복구→outcome_unknown/uncertain 유지, 다른2action 동시0.70USD 예약에서1개만허용.

완료: REPORT.md 작성. 독립16case 중14pass/2fail, 기존nonHTTP95개 통과. F01–F04 4개 및 R01/R02 인접16개/guard12개 통과. Store 권리조회→action claim은 G01 integration gap으로 별도 보고.
