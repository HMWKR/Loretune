# human 정상 흐름과 Loretune 비교

상태: 읽기 전용 비교. human 코드 실행·수정·키조회·자산전송0. user가 정상작동했다고 말한 내용을 실제파일/기록과대조했다. 분석원본은 `/Users/leesungmin/Desktop/human/tasks/platform-improvement-2026-10-21/hero-video/fal/kling_segment.py`다.

## 결정적인 차이

human은 **생성 요청에 private ACL/만료 헤더가 없고, 결과주소를 인증헤더 없이 urllib.request.urlretrieve로 저장**한다. Loretune은 **default forbid ACL·3600초 만료를 요청하고 CDN token을교환하여Bearer GET**한다. 즉human의성공은Loretune의비공개접근계약까지검증한성공이아니다.

fal기본동작은공개URL이지만, human기록에과거결과URL이없어그URL에서명자격이포함됐는지, 당시계정기본ACL이어땠는지확정하지못했다. 따라서 “human은명시적private ACL을사용하지않았고헤더없는다운로드가성공했다”까지가확인된사실이다. 이를“공개로바꾸면반드시해결”이라는결론으로확대하지않는다.

| 비교 | human | Loretune | 의미 |
|---|---|---|---|
| 실행/SDK | Python stdlib urllib, 외부falSDK없음 | Python stdlib urllib, 외부falSDK없음 | SDK버전차이증거없음 |
| 모델 | Klingv3Pro, Veo3.1, Seedance2.5분기 | Klingv2.6Pro I2V | 같은모델재현아님 |
| 입력 | 시작/끝프레임, JPEG변환 dataURI, 모델별해상도·negativeprompt | 동결PNG dataURI,시작프레임만,10초무음+safety | 생성성공후403의직접원인으로입력차이확정불가 |
| 키참조 | human루트.env의FAL_KEY | Loretune루트.env의FAL_KEY | 이름만같음. 값/소유계정/팀/권한같은지는미조회 |
| ACL/만료 | 코드에없음 | private default forbid,1시간 | 가장직접적인인증경로차이 |
| 결과받기 | urlretrieve(resultURL,out),인증헤더없음 | REST단기token→CDN BearerGET | human은private CDN token경로미검증 |
| URL/redirect | 응답URL그대로,urllib기본redirect | v3b.fal.media검증,redirect거절 | 이번실제응답은403이며클라이언트redirect는발생하지않음 |
| 폴링 |10초간격,COMPLETED후result조회 |같은단계,요청ID/상태DB보존 | 양쪽생성완료는확인됨 |
| 저장 | script옆{name}.mp4에직접저장→json기록 | 크기/타입→임시저장/디코드→해시파일이동→TakeDB | Loretune은다운로드이전403으로저장단계미진입 |
| 예산/재시도 | 별도장부추정·모델분기,과거사용자정책 | 이번1회/$1/자동재시도0 | human의승인을Loretune에승계하지않음 |

## 실제 성공 증거

영상내용/인물은열거나외부전송하지않고ffprobe로형식만검사했다. 아래JSON의video_file이실제파일명과일치하고request_id가존재한다.

| 기록/파일 | endpoint | 로컬 검증 |
|---|---|---|
| kl_c.json/mp4 | fal-ai/kling-video/v3/pro/image-to-video |21,438,994bytes,H264,1916×1080,7.041667초 |
| s1_try1.json/mp4 | 같은Klingv3Pro |11,161,700bytes,H264,1920×1080,5.041667초 |
| veo1.json/mp4 | fal-ai/veo3.1/first-last-frame-to-video |3,340,425bytes,H264,1920×1080,6초 |
| sd_a.json/mp4 | bytedance/seedance-2.5/us/image-to-video |3,661,499bytes,H264,1918×1080,5.041667초 |

이기록과파일존재는human의실제성공을뒷받침한다. 과거네트워크요청전체나동일키사용은증명하지않는다.

## Dashboard 추가 근거와 원인 트리

Aside보고(`aside-dashboard-check-072552-ko.md`)는Loretune요청200/Execution Finished/330.355초/Cost$0.70을확인했다. 따라서실청구미확인이라는이전보고는 **Dashboard에서$0.70관찰됨**으로갱신한다(별도billing API대사는미실행). 플레이어error4,readyState0,buffer0 및다운로드기록0은영상수신실패와일치하나403/코덱/만료중하나를독립적으로확정하지않는다.

1. 생성/입력문제: 큐COMPLETED·Dashboard200·결과메타데이터로우선순위낮음. 파일내용은미검증.
2. 로컬저장문제:403이save_media이전,프로젝트파일시스템fake저장·DB등록통과로이번직접원인아님.
3. 비공개전달/권한문제: human은이경로를사용하지않음. Loretune토큰교환성공→CDN403 및ACL GET403. **가장관련성높은분기이나단일하위원인미확정**.
4. 세부가설: 키의assets:read/auth:tokens:create권한, 파일소유계정·팀매핑, 모델runner의caller-token/requestID전달, CDN측인증처리, 실제tokenexpires_at. 원본키/토큰decode나계정전환으로추측검증하지않음.
5. 만료: 최초403은생성직후였으므로요청한1시간이흘러서최초실패했다는설명과맞지않는다. 실제provider만료값은없어정책적용자체는미확인; 이후에는실제만료가능성이추가됨.

## 최소 안전 검증과 해결 조건

| 가설 | 최소 확인 | 수정/완료 조건 |
|---|---|---|
| 키권한부족 | 사용자/지원이현재키의비밀없는preset/permissions와같은계정팀인지확인 | 누락확정시사용자승인후최소권한설정. 지금권한변경금지 |
| 파일소유자매핑오류 | fal이requestID의output owner와호출주체를대조 | 같은기존결과의소유자정상접근복원확인 |
| runner전달오류 | fal이Kling2.6의caller-token/requestID전달을확인 | 제공자수정근거확보후동일결과1회정상회수검증 |
| 클라이언트필드차이 | 구체공식계약/SDK증거와요청헤더를대조 | 증명된차이만코드수정+fake시험; 임의resource/audience추가금지 |
| 실제만료 | provider가expiry/삭제상태확인 | 삭제된경우회수불가로기록. 새생성은별도승인 |

지금확정된수정으로403을해결했다고말할수없다. 앱상태/UI/재개게이트개선은장애시중복과금을막는작업이며권한문제해결과별개다.

## 공식 근거 조사

- [Key permissions](https://fal.ai/docs/documentation/model-apis/authentication/key-based): 키별권한모델. 이사용자키의실제권한은미조회.
- [List keys schema](https://fal.ai/docs/platform-apis/v1/keys/list): API preset예시에assets:read/assets:write/auth:tokens:create와models요청권한이함께있음. 키관리API는호출하지않음.
- [File ACL](https://fal.ai/docs/documentation/model-apis/file-access-controls): owner접근예외,private기본값,token교환,runner의caller토큰/요청범위.
- [공식JS storage source](https://github.com/fal-ai/fal-js/blob/main/libs/client/src/storage.ts): lifecycle필드명일치. human/Loretune은이SDK를실행하지않는다.
- [공식SDK releases](https://github.com/fal-ai/fal-js/releases): REST도메인변경fix가있으나Loretune은이미rest.fal.ai사용. 해당fix를이번403해결근거로쓰지않음.

공식공개이슈검색에서이번private Kling2.6증상에직접일치하는확정known issue/수정방법을찾지못했다. 검색부재는제공자결함부재증명이아니다.
