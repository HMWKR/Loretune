# 추가 실제 Kling 검증 결과

**추가1회 생성은 공급자 완료까지 진행됐으나, 단기 CDN 토큰 발급403으로 로컬 수신이 차단됐다. 실제 영상 저장·Take등록·음악/자막 최종출력은 미완료다.** 추가생성/권한우회/공개fallback/동일거절재시도는 하지 않았다.

- request ID: `01a17232-7047-7ae1-b491-7cfe70686742`
- local job: `299b1b20-f0f7-46ab-9051-1f2344f170b2`
- 모델: fal-ai/kling-video/v2.6/pro/image-to-video,10초,generate_audio:false,safety:true
- 신규request policy: default forbid, rules[{user:dltysl123,decision:allow}],retention3600. 기존asset ACL 변경없음.
- Username 근거: 공식Dashboard account/details Personal Profile Username, personal/Owner/Active; 부모확인2026-10-25T08:31:18.417Z.
- 동일동결4423byte PNG/prompt/hash. 키는기존.env를승인된프로세스메모리에서만사용. 새credential저장없음.

| 단계 | 실제 결과 |
|---|---|
| 제출 전 QA |95/95pass,헤더·정책hash고정검증 |
| 중복/예산확인 |기존generation1개/미확정reservation1개. 신규승인scope미사용확인 |
| 추가접수 |1회accepted. 새scope1USD예산,0.70예약 |
| provider조회 |running→result_ready,약218초후완료관찰 (정확한provider실행시간아님) |
| token교환 |rest.fal.ai/storage/auth/token POST가HTTP403;1회후중단 |
| 영상 CDN GET |미실행 |
| 파일검증/저장/새Take |미실행. 기존입력이미지Take1개보존 |
| 익명접근차단 검사 |미실행. 인증수신실패뒤추가파일접근하지않음 |
| 음악/한국어자막export |미실행. 생성영상없음 |
| 실패처리회귀 |96/96pass,토큰403과CDN403구분/재시도금지추가 |
| 재시작/UI |PID20767,127.0.0.1:8765,provider disabled. 두작업import_blocked보존,토큰403문구·재시도버튼없음확인 |

## 이전 실패와 다른 점

이전 요청은 token교환성공 뒤 CDN GET403이었다. 이번 error code `provider_http_403`은 FalKling.download의 첫 단계 `_request(POST,TOKEN_URL)`에서 반환됐다. 이코드와호출순서로 실패단계를 식별할수있다. CDN GET의HTTP403이면 `provider_media_http_403`이었을것이다. 실제응답body/토큰은저장하지않았다.

같은날 private PNG 직접upload/read는 모두200/hash일치였다. 따라서 현재 토큰발급의권한/일시상태/요청경로차이를새로확인해야한다. 이결과만으로 명시본인rule이실패했다거나 Kling output owner가잘못됐다고결론낼수없다. **이번시험은 토큰단계에서멈춰 수정된출력ACL의읽기동작을평가하지못했다.**

정적비교상 direct preflight는 Key+JSON로token교환하고 모델adapter의공통요청함수는 여기에X-Fal-No-Retry:1을추가한다. 이것이403원인이라는근거는없고, 헤더를바꾼실제재시도는하지않았다. `.env`파일/키변경여부를추가로조회·비교하지않았다.

## 비용

이번추가요청 예상$0.70(공식무음$0.07/초×10). provider완료는청구영수증이아니므로실청구는미확인이다. 기존1회는Aside Dashboard에서$0.70관찰됐고별도이력이다. 이번원장reservation0.70은uncertain상태이며자동환불/정산하지않았다. preflight storage/read실청구도미확인이다. 총추가예산1USD,추가모델1회허용은이미소진됐으므로재생성불가.

공식Billing Events API는billing:usage:read,auth:keys:read,account:users:read를요구하며BILLING/FULL preset을명시한다. 현재UI API/All models확인만으로그권한을가정해새키로전환하지않았다. 부모진단세션에서**이requestID의Dashboard Cost와완료상태를읽기전용확인**하면비용증거를보강할수있다. 요청payload/키reveal/다운로드재클릭은불필요하다.

## 다음 정상 해결 근거

새 유료생성 대신, fal 측에 이시각 token endpoint403의비민감 request correlation/계정상태와허용된동일주체의단기token발급조건을확인해야한다. 현재응답상태외확정사유는없다. 지원문의초안은아래파일이며발송하지않았다. 거절된token요청은새관련권한/설정근거없이반복하지않는다. 출력1시간수명요청은있으나정확한삭제시각은미확인이다.

운영판정: 실AI→로컬완성MVP 게이트미통과.96개로컬테스트는장애방어검증이며실연동/다중tenant/다중server/부하/실배포무결함보장이아니다.

근거: approval.json,policy.json,one-attempt.json,status.json,regression-96.txt,ui-blocked.txt/png. API키·토큰·서명URL 미포함.

공식가격: https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video
Billing권한: https://fal.ai/docs/platform-apis/v1/models/billing-events
