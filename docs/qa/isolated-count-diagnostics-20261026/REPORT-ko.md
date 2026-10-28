# Count 오류 안전 진단 — 격리 사본 patch, 미적용

**구현·집중시험 완료. 정규 제품 파일에 적용하지 않았다.** 제품2파일과 새 테스트1파일만 포함한 `diagnostic.patch`를 제공한다. 원 소스 권한0644를 유지했다. 현재 uncommitted source를 기준으로 필요한 Python import 의존성과 fixture만 임시 base/work 폴더에 복사했다(41개). 원본 DB/env/auth 파일은 복사하거나 열지 않았다.

## 변경

- `anthropic_ontology.py`: 오류 metadata를 고정 category 집합, 유효 정수 HTTP status(100–599), 형식 검증된 req_ header ID로 제한했다. JSON/형식 오류와 전송 오류를 구분한다. HTTP 오류 body는 읽지 않는다. response body의 `_request_id`는 provenance로 신뢰하지 않고 검증한 header만 사용한다.
- `chat_runtime.py`: credential/count/전송/응답 오류 분류를 일반 오류 문자열로 덮지 않고 `steps[].failure`와 해당 usage journal metadata에 보존한다. stage는 preflight/count/messages/response 중 런타임 상태에서 결정한다. credential과 같은 문자열을 포함한 request ID는 버린다. missing/invalid count 응답 및 승인 token 상한도 구분한다.
- 원문 exception text, response body, headers, key, 입력문장을 새 diagnostic에 넣지 않는다. 일반 logging framework, 자동 retry, 새 네트워크 경로를 추가하지 않았다.
- 상태/예산 전이는 그대로다. count 또는 preflight 실패는 blocked_before_message/미사용 예약해제. Messages 전송 시도 후 timeout은 outcome_unknown/예약유지/중복차단. 다른 예약과 이미 완료한 도구 결과는 유지한다.

기대 diagnostic 예(새 테스트에서 equality 검증): `stage=count, category=http, http_status=400, request_id=req_synthetic_count_01`; count timeout은 `stage=count, category=transport`; 응답 필드 누락은 `stage=count, category=malformed_response`. request ID 검증은 고정 endpoint 응답 header의 출처와 제한된 문자열 형식 검증이며 공급자 원격 재조회/암호학적 인증을 뜻하지 않는다.

## 집중시험 결과

**29/29 PASS, 0.471초.** 신규10 + 기존CC02 preflight7 + bounded transport12. Python AST 검사도 통과했다. 전체 suite는 실행하지 않았다.

신규10개는 HTTP status/ID, 유효하지 않은 status/ID 제거, 오류 body 비읽기, count timeout/no retry, invalid JSON, missing count field, body의 위조 request ID 제거, credential supplier 예외, Messages timeout 예약유지, key가 들어간 request ID 제거, token 상한 경계를 다룬다(일부 조건은 한 테스트에 포함). 합성 민감 문자열을 exception text·body·header·ID에 넣고 임시 파일 전체에 남지 않는지 검사한다. 기존CC02 시험은 다른 reservation/완료 비용·도구 결과 보존을 함께 확인한다.

증거: `run_tests.py`, `test-results.log`, `test-results.json`, `patch-files/tests/test_count_diagnostics.py`. socket connect/bind를 차단했고 opener/supplier는 fake만 사용했다. 실제 provider 호출·키 파일 읽기·공유DB·브라우저·CLI inference·REA·업로드0.

## 정확한 base

- chat_runtime.py: `50ec18343dc4619aa2df8a5ffda7008a0a96c6bef71917c805c482700a51c54a`
- anthropic_ontology.py: `e7021df88da62058a746b370f6eca26aa26f45012a3ae7a2195c3cea2be6d0f0`

`base-manifest.json`은 복사 시 hash/mtime/mode, `patch-manifest.json`은 base/patched hash와 종료 시 원본 일치를 기록한다. 검토자는 적용 전 해당2파일 hash를 다시 비교해야 한다. 정규 writer만 통합하며 이번 사본을 자동으로 덮어쓰지 않는다.

이 patch는 **15:51의 지워진 원인을 소급 복구하지 못한다.** 당시 증거는 여전히 count 반환 전 실패만 보여준다. 새로운 진단을 넣었다는 이유만으로 실호출 재시도를 수행하거나 승인된 것으로 간주하지 않는다. 이번에는 재시도하지 않았다.
