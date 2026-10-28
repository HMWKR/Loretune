# 명시적 본인 nickname ACL 후보 검토

판정: 공식 계약상 기술적으로 지원된다. 정확한 본인 fal nickname에 allow를 부여하고 default forbid/1시간 만료를 유지하는 신규 요청별 규칙은 공개 fallback이나 계정 전체 권한 확대가 아니다. 다만 현재 정확한 nickname 근거가 없으므로 실제 요청에 활성화하지 않았다.

## 반드시 구분할 점

공식 문서상 owner는 ACL과 무관하게 항상 접근한다. 따라서 output owner가 실제로 다른 provider principal이라면 본인 rule을 추가해도 그 owner의 접근을 제거하지 못한다. **검증된 본인만 명시적 허용**과 **물리적으로 본인 외 아무 주체도 읽지 못함**은 다른 주장이다. 후자를 현 근거로 보장하지 않는다. unknown nickname은 조용히 무시될 수 있으므로 이메일·display name·URL 조각을 추측해서 넣으면 안 된다.

직접 private 업로드 성공은 기본 client/token 경로의 정상 근거다. 하지만 과거 key identity/그 시각 token 상태/asset별 정책/만료 등을 모두 소거한 것은 아니므로 원인이 provider ownership/ACL 두 가지뿐이라고 확정하지 않는다. 이 규칙으로 성공해도 결과는 '명시적 본인 rule을 둔 경로 검증'이며 provider root cause 확정이 아니다.

## 로컬 코드와 fake 검증

fal_provider.py의 private_lifecycle_candidate(nickname)는 순수 후보 빌더다.1시간/defaultforbid/정확히1개allow만 생성하고 ambiguous 문자열을 거절한다. 형식 검증은 신원 검증을 대신하지 않는다. 현재 실제 submit은 기존 LIFECYCLE(rules[])를 그대로 사용한다. gate에 nickname이 묶이기 전 활성화할 수 없도록 실제 런처에 연결하지 않았다. 기존 정책 객체도 mutation되지 않는다.

tests/test_fal_provider.py에 후보범위/변형격리/기존실요청미변경/미확인입력거절 테스트2개 추가. 관련18개 fake 회귀 모두통과. evidence explicit-reader-fake-tests.txt. 이 시점 새 전체93개 회귀는 아직 실행하지 않았으며, 실제정책 활성화 후 실행전 gate에서 필요하다. 실제키조회/외부요청/모델생성은이번검토에서0.

## 부모 진단 세션에 필요한 정확한 조회

기존 승인된 지정 personal/Owner 계정에서 **fal nickname 또는 handle로 명시된 항목의 정확한 값**, 그 항목이 해당 personal 계정에 속한다는 같은화면 맥락, 확인시각, 필드label 및 공식프로필 경로를 비밀없는 로컬보고서로 전달해 달라. 표시이름/이메일/키이름은 대체근거가 아니다. 설정 저장·nickname변경·다른계정전환·키reveal은 필요없다. UI에서 nickname/handle 의미를 확인할 수 없다면 추정하지 말고 미확인으로 보고한다. 공개프로필 링크로 확인할 경우에도 어느계정에서 링크됐는지 함께 남겨야 한다.

## 실행 전 남은 게이트

1. 위 nickname 증거와 원래 승인된 본인주체 일치 확인.
2. 승인 입력에 정확한nickname/증거경로/정책hash를 고정하고 런처 및 요청빌더 양쪽에서 일치 검사. UI/client가 임의reader를 주입하는 경로는 만들지 않음.
3. 모델/PNG/prompt/10초/audiofalse/safety/private1h/retry0/한번/$1합산예산 유지. 기존키 변경 없음. 시작전 중복request와비용근거확인.
4. 전체로컬회귀, 실제헤더가이정책으로직렬화됨을fake로검증한뒤 부모의실행판정. 현재는후속판정전이므로생성하지않음.
5. 실패하면재시도/공개fallback/기존파일ACL변경금지. 성공하면길이/해상도/파일검증→원자저장→Take등록→음악/자막export를분리증거화. 익명차단검사는추가read범위를명확히한후진행.

공식근거: https://fal.ai/docs/documentation/model-apis/file-access-controls (2026-10-25 공식검색반환본문 교차확인). owner always retains access와fal nickname per-user rules는동시에적용된다.
