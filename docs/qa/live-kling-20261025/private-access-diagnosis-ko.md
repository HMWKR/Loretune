# 비공개 CDN403 읽기 전용 진단

## 결론

**확정된 클라이언트 계약 오류를 찾지 못했다.** 동일 fal키가 큐/결과 조회에는 성공하지만 CDN토큰 인증 다운로드와 파일ACL 읽기에는403을 받았다. 파일소유권/계정·키 권한 또는 공급자 내부 전달 문제 중 무엇인지는 현재 증거만으로 결정할 수 없다. 권한 문제를 단순 네트워크 재시도로 해결할 근거가 없어 재다운로드0, 추가생성0, ACL변경0을 유지했다.

## 문서와 코드 대조

| 항목 | 공식 계약과 현재 코드 | 판정 |
|---|---|---|
| 토큰 endpoint | POST `https://rest.fal.ai/storage/auth/token?storage_type=fal-cdn-v3` | 일치 |
| 토큰 인증 | Authorization: Key (기존FAL_KEY); JSON본문 | 일치, 발급 성공 |
| 본문·만료 | 기본{} 허용, `expiration_seconds`로단축 가능. 현재600초 | 문서상 지원. 실제 expires_at은 이전 코드가 보존하지 않아 미검증 |
| CDN인증 | Authorization: Bearer (반환token), 원본키직접사용금지 | 일치, 실제403 |
| 대상도메인 | https://v3b.fal.media, v3파일 | 일치. 실제 URL query/fragment없음, 기본443, /files/b/ 경로. 전체URL비공개 |
| resource scope | 클라이언트token발급 예시에는 별도resource/requestID필드없음 | 누락으로단정불가. 서버리스 runner의 X-Fal-CDN-Token/requestID범위는제공자구현사항이며클라이언트에서임의추가하지않음 |
| 소유권 | default forbid라도파일소유자는접근가능 | 실제소유자와키/토큰주체일치미확인 |
| 결과ACL | 초기 default forbid/rules[],만료3600초 | 공식private-to-me 예시와일치. 요청했으나실제ACL GET403으로값확인불가 |
| fileACL 조회 | GET rest.fal.ai/storage/files/acl?url=... / 동일키 | 새읽기진단1회에서403. 재시도없음 |

공식 문서는 https://fal.ai/docs/documentation/model-apis/file-access-controls 이며 읽기 토큰, 소유자 예외, v3범위, 만료단축, ACL조회 API를 확인했다. 문서에 없는 allowed_domain/resource필드를추정하여토큰범위를확대하지않았다. 기존키가어떤계정/조직에속하는지또는권한스코프가무엇인지별도관리API로탐색하지않았다.

## 기존 작업의 실제 조회

`readonly-diagnosis.json`에secret-free증거를보존했다.

- requestID `01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d`
- 현재COMPLETED, inference_time330.355초
- 결과video/mp4, 제공자신고파일크기8,379,663bytes
- 기존결과URL과동일함을메모리내비교확인(문서/로그에URL미출력)
- 결과응답은video만포함. 청구/usage/price없음. 정확한파일만료시각도없음.
- 결과내용·길이·해상도는파일미수신으로여전히미검증. 청구$0.70은추정이며실제청구미확인.

## 즉시 필요한 정상 조치

사용자가 **해당키와같은fal계정/팀으로로그인한Dashboard의기존요청**에서 요청ID를확인하고 기존결과다운로드가가능한지확인해야한다. 새Generate/재실행을누르지말것. 가능하면그기존MP4를Mac프로젝트로저장하면추가생성없이로컬음원/자막검증을계속할수있다. 키·토큰·서명URL은채팅에보내지말것.

Dashboard에서도접근할수없다면fal지원에요청ID와 “queue COMPLETED; CDN token exchange succeeds; authenticated CDN GET403; same-key ACL GET403”를전달하여생성파일소유권/팀키주체매핑과정상접근방법을확인해야한다. 지원팀연락은아직보내지않았다. 소유권/권한문제가해결됐다는새근거가확인되면동일결과의정상다운로드1회재시도를검토할수있다. 공개전환·ACL완화·다른계정·새키는이번회수방법으로사용하지않는다.

만료는생성결과에3600초를요청했으므로완료시점근처부터대략1시간을가정해빠르게확인해야하지만, 정확한삭제시각은응답에없어보장할수없다. 파일이만료돼도새생성은승인범위밖이다.
