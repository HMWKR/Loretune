# CC01 독립 재검증 범위

1. FINAL-MANIFEST와 현재 source hash 비교, 별도 snapshot 고정.
2. 원래 9개 완료 turn + Store 재열기 반례와 canonical correction/isolation probe를 그대로 재사용.
3. 요청 원문 순서/status/hash/scope/assistant 권한 분리, token/byte 한도와 reservation/unknown 경계만 검사.
4. 저장된 실제 응답의 input/output hashes, request IDs, usage 합계, tool prompt→action→fake fal payload 일치 검산. 실제 답변의 의미 오류와 수정 범위를 직접 확인.
5. 모든 실행은 임시 DB/fake transport. socket connect/bind 차단. fullsuite·HTTP·liveAPI·secret·CLI·브라우저 없음.
