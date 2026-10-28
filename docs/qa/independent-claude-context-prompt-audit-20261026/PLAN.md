# Aethon Claude 문맥·영상 프롬프트 독립 검증 계획

1. **앱 보존:** 합성 작품 A의 여러 turn을 임시 SQLite에 저장하고 Store/runtime을 다시 열어 다음 요청 payload에 최근 대화와 현재 승인 facts가 들어가는지 확인한다. 같은 작품의 독립 session ID가 실제 존재하는지 별도로 확인한다. 이는 모델 자체 기억을 증명하지 않는다.
2. **온톨로지:** 알아보기 쉬운 합성 canary entity/relation·provenance·version을 승인하고 수정한다. 새 문맥의 stale 사실 대체, 근거/충돌/unknown 표현, 작품 B canary 격리를 실제 handoff/search 출력으로 검증한다.
3. **모델·프롬프트:** chat/image/video 선택 분리, 모델이 만든 tool args의 prompt/options/reference가 검증·승인 후 저장 action을 거쳐 fake fal payload로 동일하게 전달되는지 확인한다. 사용자 수정→실제 Claude의 의미 반영은 별도 live 증거가 필요하다. fake 응답의 문자열 존재를 품질 통과로 계산하지 않는다.
4. **실행 경계:** 미승인 submit 차단, 승인 hash/가격/권리/모델 고정, stale·unknown·retry/idempotency를 기존 집중 시험과 독립 반례로 확인한다. 실제 provider 호출·공유 DB 접근·앱 변경은 금지한다.
5. **실제 Claude 증거:** 기존 live harness와 비용 기록 보고서를 읽고 최소 시험표를 작성한다. 각 run의 source hash, 모델 ID, prompt/context hash, redacted request/visible response/tool args, usage/request ID, 예상·실제 비용, 판정 근거가 있어야 한다. 이 감사자는 live를 실행하지 않는다. fal은 fake transport까지이며 실제 영상 품질은 미검증이다.

진행: source 고정 완료 → 관련 계약 읽기 → offline 재현 → live 실행 계획·보고서. 외부 웹/API/브라우저/포트·키 조회·설치 없이 수행한다. 저장소의 audit 스킬은 접근성 전용이므로 이번 correctness 범위에는 적용하지 않는다. 관련 홈 지침과 harness-execution-policy의 버전 연결/관측·추론 분리만 적용한다.
