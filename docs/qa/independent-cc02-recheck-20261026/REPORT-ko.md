# CC02 한정 독립 재검증 — 2026-10-26

**PASS: CC02를 검사 범위에서 닫을 수 있다.** 원래 독립 반례 1개와 가장 가까운 guard 6개를 새 격리 snapshot에서 실행했다. 전체365 시험이나 HTTP/live 시험은 실행하지 않았다.

## 원 반례의 전후

|관찰|이전 독립 감사|이번 독립 재검증|
|---|---|---|
|count / Messages 직렬화|65,529 / 65,549 bytes|**정확히 같은 크기**|
|count opener|1|0|
|Messages opener|0|0|
|synthetic credential supplier|이전 결과에서 별도 측정 안 함|0|
|상태|outcome_unknown|blocked_before_message|
|예약 held / actual|5,735 / null|0 / null|
|다음 명시적 요청|차단|접수 가능|

이전 독립 `boundary_run` 함수를 복사해 같은 41개 accepted-history 경로와 실제 bounded transport/fake opener를 사용했다. 새 상태를 만들기 위해 제품 코드나 queued handoff를 수정하지 않았다. 시간 필드 길이 변동만 막도록 fixture clock을 고정하고 첫 prompt 길이를 조절했다. fake count가 반환할 값은12,000이고 승인 input16,384/output8,192지만 이번 반례에서는 count까지 도달하지 않는다. 실제 토큰 수/청구를 측정한 시험이 아니다.

## 가장 가까운 guard: 6/6 PASS

- Messages 정확히65,536 bytes: 사전검사한 UTF-8 본문 그대로 fake POST, completed.
- Messages65,537 bytes: count와 Messages 전에 거절, 예약0.
- count timeout: Messages0, 예약해제, 자동 retry 없음.
- Messages timeout: unknown 및 held5,735 유지, 자동 retry와 중복 접수 차단.
- 별도 unknown 예약1,234: 그대로 보존하고 새 거절 attempt만 해제.
- 첫 round의 완료 응답/도구 계획 뒤 다음 round가 너무 큼: 완료 비용60(fixture)·저장 계획 보존, 뒤 attempt만 예약해제.

6개는 primary가 추가한 테스트의 실제 assertion/source를 읽고 새 snapshot에서 선택 실행한 결과다. 원 반례는 기존 독립 구현을 재사용했다. 숫자를 primary 전체 회귀365와 합산하지 않는다.

## 수정 코드 확인

`chat_runtime.py:71–76`은 최종 Messages body를 검사하며 credential을 읽지 않는다. `chat_runtime.py:199–207`은 예약 후 preflight를 먼저 수행하고, 성공한 경우에만 count/submit으로 이동한다. `anthropic_ontology.py:158–166,178`의 동일한 `encode_body`를 사전검사와 POST에 재사용하므로 서로 다른 byte 계산이 아니다. 실제 제출 후 불명 상태의 예약 해제 규칙은 완화하지 않았다.

고정 source hash는 primary FINAL-MANIFEST와 일치했다.

- chat_runtime.py: `50ec18343dc4619aa2df8a5ffda7008a0a96c6bef71917c805c482700a51c54a`
- anthropic_ontology.py: `e7021df88da62058a746b370f6eca26aa26f45012a3ae7a2195c3cea2be6d0f0`
- tests/test_chat_preflight.py: `38281ba014e83af7b4ae396f4e9075fb6b2d4cdc1a6e73c5964361654b4c0e00`

## 증거와 한계

`recheck.py`, `recheck.log`, `results.json`, `snapshot-manifest.json`, `final-integrity.json`. 실행: `python3 docs/qa/independent-cc02-recheck-20261026/recheck.py`.

검토 전후 복사한 source hash가 모두 같았다. 제품 파일은 수정하지 않았다. 모든 DB는 임시 synthetic fixture이며 socket connect/bind를 차단했다. 실제 API·비밀파일·공유DB·브라우저·CLI inference·REA·업로드0. 이번 한정 검사에서 새 결함/실행 blocker 없음. 이전의 장기 기억·별도 세션·live evidence redaction 한계를 이 수정으로 해결했다고 주장하지 않는다.
