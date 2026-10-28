# API 생성은 완료됐는데 로컬 영상이 없는 이유

## 사용자용 결론

API의 생성 완료는 **fal 서버에서 결과가 준비됐다는 의미**다. Loretune에 영상이 생기려면 그 결과를 인증해 내려받고, 파일을 검사해 저장한 뒤 작품에 연결해야 한다. 이번에는 **다운로드 HTTP 요청이403으로 거절되어 영상 본문을 읽기도 전에 중단됐다.** 저장하려다 경로를 잃은 것이 아니라, 저장할 영상 바이트를 받지 못한 것이다.

## 단계별 실제 증거

| 단계 | 실제 결과 | 의미 |
|---|---|---|
| 1. 생성 요청 접수 | 성공, 요청1회, requestID보존 | 이미지·프롬프트를fal이접수 |
| 2. 작업 조회 | COMPLETED, inference_time330.355초 | 서버측처리완료. 로컬파일완료와다름 |
| 3. 결과주소 추출 | 성공, video/mp4, 신고크기8,379,663bytes | URL/메타데이터만받음. 영상바이트미수신 |
| 4. 단기토큰교환 | 성공, token문자열수신.600초요청 | 토큰발급자체가해당파일접근권한을보장하지않음 |
| 5. CDN GET | 익명403, Bearer인증도403 | 영상본문read_video호출전에HTTPError |
| 6. 크기·형식·디코딩검증 | 실제결과에대해서미실행 | 길이·해상도·내용을확정할수없음 |
| 7. 임시저장·원자적이동 | 미실행 | 새영상파일·upload임시폴더생성경로에도달하지않음 |
| 8. Asset/Take/Job DB | 새영상Take등록미실행; job import_blocked기록 | 원본PNG Take1개만존재, 기존선택보존 |
| 9. 음악·자막합성 | 미실행, 해당작품export0 | 최종MP4가없는것이정확한현재상태 |

로컬DB읽기확인: 실제작품take_count1/video_takes0/job asset hash없음/export0/upload임시폴더0. 보관된result URL은비공개DB내에있으며보고서에출력하지않았다.

## 403 발생 위치와 리다이렉트

`generation_queue.py`의 `import_result()`는 먼저 `raw=download(url)`을 호출하고 그다음 `Store.save_media()`를 호출한다. `fal_provider.py`의 다운로드는 `build_opener(NoRedirect()).open()`이성공해야 `read_video()`를호출한다. 실제오류는 `provider_media_http_403`으로분류됐으므로후속함수에도달하지않았다.

NoRedirect는리다이렉트를따라가지않는다. 따라서 **이클라이언트가기록한403은다른호스트로리다이렉트해원본키를보낸뒤발생한오류가아니다.** HTTP오류응답자체에는본문이있을수있지만그오류본문은보관하지않았으며영상본문을읽지않았다. CDN내부프록시/라우팅행위는관찰하지못했으므로확정하지않는다.

## 로컬 저장 문제의 별도 검증

실제사용자자산을변경하지않고프로젝트안에생성한새임시fixture에서검사했다.

- fake403을발생시키면 `read_video()`와 `save_media()`가둘다0회호출됨.
- 합성10초MP4로프로젝트파일시스템쓰기→FFprobe/첫프레임디코드→동일파일시스템의임시파일replace가성공.
- 임시폴더정리확인. 잘못된미디어는거절하고이미저장한합성원본해시/파일을보존.
- 기존격리테스트에서새Take·Job imported를DB에기록하고Store재개후유지되는것, 중복import가새다운로드를하지않는것도재검증통과.
- 다운로드크기/타입/ContentLength/서명경계테스트통과. 실제파일의신고8.38MB는128MiB수신한도보다작지만실제바이트검증은아직없다.

증거: `local-file-diagnosis.json`, 기존 `test_import_adds_unselected_take_once_and_preserves_existing_approval` 및 `test_download_size_type_truncation_and_signature_boundaries` 재실행2/2통과. 실제data/assets권한실패증거는없으며이번403보다뒤에있는경로라직접원인이될수없다. 파일replace와DB트랜잭션은하나의분산원자적작업은아니므로그사이프로세스중단시미연결파일이남을가능성은있으나이번에는replace자체가실행되지않아해당하지않는다.

## 하위 원인 가설: 확인된 것과 미확인

| 가설 | 현재근거 | 판정 |
|---|---|---|
| 토큰endpoint/헤더오타 | 공식POST /storage/auth/token?storage_type=fal-cdn-v3, Key인증, 반환token의Bearer사용과일치 | 확인되지않음 |
| 결과호스트오류/서명제거 | 원본결과URL과현재동일; https v3b.fal.media /files/b/, query/fragment없음 | 해당증거없음 |
| 토큰만료 |600초요청직후사용. 하지만반환expires_at은저장하지않음 | 가능성낮아보이나확정배제불가 |
| audience/resource누락 | 공식클라이언트토큰예시에별도audience/resource/requestID파라미터없음 | 임의필드추가근거없음 |
| 계정/팀/파일소유권불일치 | 같은키의큐조회성공, CDN GET403, 공식ACL GET도403 | 관련가설이나주체/소유자미조회라확정불가 |
| ACL조회권한만부족 | ACL관리조회와미디어읽기가다른권한일수있음 | ACL403만으로파일소유권오류를증명하지못함 |
| 제공자runner의소유권전달누락 | 공식문서는runner가caller token/requestID를전달하도록설명 | 가능한공급자측가설; 내부구현미확인 |
| CDN/WAF/다른인증실패 |403오류본문·비민감응답분류를보존하지않음 | 현재403만으로ACL외원인배제불가 |

원본키유출·공개fallback·다른계정시도·토큰범위확대는수행하지않았다. 이번진단에는새HTTP호출도없다.

## 정상 접근 복원 후보와 검증 방법

1. **진행중Dashboard진단과대조:** 같은계정/팀에서해당requestID의기존파일을다운로드할수있는지확인한다. 가능하면원본MP4를Mac로회수하고해당작업의메타데이터/출처에연결해검증한다. 새Generate를누를필요없다. 브라우저진단은다른세션이담당하므로중복하지않았다.
2. **fal측확인:** Dashboard에서도불가하면요청ID와큐COMPLETED/토큰교환성공/CDN403/ACL GET403을제시해실제파일소유주와키의계정·팀매핑, 정상다운로드권한을확인한다. 지원연락은부모/사용자판단사항이며자동발송하지않았다.
3. **명확한수정근거후1회검증:** 공식문서나fal답변으로정상토큰주체/필수스코프/구체클라이언트오류가확인되면먼저fake계약검증후같은기존결과만1회조회한다. 지금은그근거가없으므로다운로드를반복하지않는다. 공개전환/ACL완화/다른계정/새키는회수수단으로사용하지않는다.
4. **진단성개선후보:** 향후허용된시도에서는토큰원문대신발급시각·expires_at·요청한TTL, HTTP상태·ContentType·공급자요청추적ID의안전한필드만기록한다. 오류본문전체/JWT원문/서명URL은기록하지않는다. 이것은원인판별을돕는개선이며그자체로403을해결하지않는다. 이번읽기전용진단에서제품코드는변경하지않았다.

요청한만료는1시간이며정확한서버만료값은없다. 추정삭제시각은2026-10-25약07:59UTC/16:59KST로이전보고에전달했다. 이미만료됐다면이승인으로재생성하지않는다. 실제비용은여전히미확인이다.

공식근거: [File Access Controls](https://fal.ai/docs/documentation/model-apis/file-access-controls), [fal CDN](https://fal.ai/docs/documentation/model-apis/fal-cdn). 클라이언트API계약과서버리스runner계약을구분했다.
