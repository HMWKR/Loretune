> 최신 재감사: [mvp-live-readiness-reaudit.md](mvp-live-readiness-reaudit.md). 아래 이전 감사의 미구현/실패 판정은 이력이며 최신 문서가 우선합니다.

# Kling 실호출 전 준비 감사

판정: **NOT READY — 로컬 선행 작업이 남아 있어 지금 실호출 승인 요청을 진행하지 않는다.**
확인: 2026-10-25T05:10:14Z부터 공식 자료 재조회, 독립 QA 약05:13Z. Mac은 KST(UTC+9)이다. 이전 인계의 `14:09 UTC`는 표기 오류로 `14:09 KST / 05:09 UTC`가 맞다.

## 1. 정확한 요청안

- 모델/버전: `fal-ai/kling-video/v2.6/pro/image-to-video`, Kling2.6 Pro **I2V**.
- 접수: `POST https://queue.fal.run/fal-ai/kling-video/v2.6/pro/image-to-video`.
- 불변 release digest는 공개 문서에서 확인하지 못했다. version 경로만 고정됨.
- 옵션: `duration:"10"`, `generate_audio:false`, `enable_safety_checker:true`. voice_ids/end_image_url/negative_prompt는 전송하지 않는다.
- **해상도:** 입력 PNG는1280×720(16:9). 공식 입력 스키마에 resolution/ratio 필드가 없어 생성 결과 해상도를 지정·보장할 수 없다. 결과 원본을 ffprobe로 실측한다. 최종1920×1080은 로컬 리사이즈 캔버스이며 AI 원본1080p와 다르다.

실제 준비한 파일(아직 전송0): `docs/qa/fixtures/kling-live-v1/`

| 파일 | 내용 | 외부 전송 |
|---|---|---|
| start-frame.png | 새로 합성한 남색 하늘·청록 바닥·파란 직사각형·금색 정사각형. 사람/문자/로고 없음.1280×720,4,423 bytes | 승인 후 data URI로만 |
| prompt.txt | 아래 정확한 문장,220 bytes(개행포함) | 승인 후 |
| local-audio.wav | 자체 합성 C/E/G톤,10초,48kHz,960,078bytes | 안 함; 로컬합성용 |
| captions.srt | “로컬 검증 · 비식별 테스트” 0–10초 | 안 함; 로컬자막용 |

프롬프트:

> A quiet abstract geometric landscape. The camera slowly moves forward. The blue rectangular structure stays stable while soft clouds drift across the dark blue sky. Gentle cinematic motion. No people, no text, no logos.

PNG SHA256: `345156ca8dfe5abcfc54a9382820164fc42de77a32cf67ce9eb49e4dcdfcbcb1`

prompt.txt SHA256: `5338518e4872f716ec7dd77c2a61865083732c7a1f1999a7aafc99109c9b96e7`

전체 해시는 같은 폴더 `manifest.json`. 실제 전송문은 파일의 마지막 개행을 제거하므로 런타임 승인바인딩에는 그 정규화된 문자열 해시를 별도로 계산해야 한다. 기존 QA 작품의 파란320×180 이미지/이전 프롬프트를 이 승인자료와 혼동하지 않는다.

## 2. 가격·credit·취소

공식 모델 페이지를05:10:14Z 이후 재확인: 무음$0.07/초. 계산은10×0.07=$0.70. 제안은 **1회/$1.00 사용량 한도**, 추가재생성0회. UI/계정 할인은 반영하지 않는다.

현재코드의 상한은 DB트랜잭션에서 누적 job 견적을 integer micro-USD로 합산하고 `maximum_calls=1`, `maximum_units=1000000`과 비교하는 **로컬 요청발행 제한**이다. 예약액은700000, 미확정도호출수를차지한다. 공급자 계정의 실제 청구 상한/세금/충전/다른 앱 사용까지 보장하지 않는다. 현재 요금은 코드상0.70 고정이며 동적 가격확인 API는미구현이다. 실행직전 재검증·가격시각을핀하는 절차가필요하다.

fal 공식문서는 prepaid credit 차감 방식을설명한다. **사용자 계정의 잔액·충전·자동충전·청구유형은 미조회**. 일부기업계정의invoice방식도있어 이사용자의계정유형을확정하지않는다. 키보유가잔액보유를의미하지않는다. 추가구매/충전은수행하지않는다.

재시도: 클라이언트POST자동재시도없음, `X-Fal-No-Retry:1`로fal queue기본재시도해제. 로컬타임아웃/응답유실은예약을유지하고재발행하지않는다. 공식FAQ는서버500+는미과금, **422같은클라이언트오류는GPU처리후발견되면과금될수있음**을명시한다. 취소는큐제거또는실행기에중단신호를보내는것이며무조건환급보장이아니다. 결과성공/취소를실청구확정으로자동전환하지않는다.

근거:
- https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video
- https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api
- https://fal.ai/docs/documentation/model-apis/pricing
- https://fal.ai/docs/documentation/model-apis/faq
- https://fal.ai/docs/documentation/model-apis/inference/reliability
- https://fal.ai/docs/documentation/model-apis/inference/queue
- https://fal.ai/docs/inference-api/queue/cancel

## 3. 키·파일 공개 범위

현재 `.env`를읽거나값/변수이름을확인하지않았다. 코드에는 `.env` 로더가없다. `FalKling.from_environment(live_enabled=True)`가프로세스환경의`FAL_KEY`를읽는구조만있다. 기본false에서는읽지않는다. **“이미기존.env를프로세스에주입했다”는설명은틀리다.**

계획은승인후필요한기존항목만서버메모리로주입하고새키파일·환경설정·브라우저값·로그를만들지않는것이다. shell source는임의코드실행위험이있으므로사용하지않는다. 안전한단일항목파서/런처와비밀비노출시험은아직미구현이다. 현서버는provider_adapter=None/generation_approval=None.

추가차단: fal CDN결과URL은기본적으로링크소지자에게공개된다. 현재어댑터는비공개ACL과CDN단기토큰접근을구현하지않았다. 공개생성을승인받았다고해석하지않는다. 공식문서의`initial_acl.default=forbid` 및서버전용단기토큰다운로드를구현·fake검증해야한다. 원본API키를CDN으로그대로보내면안된다. 토큰교환역시실행은최종승인후다.

- https://fal.ai/docs/documentation/model-apis/file-access-controls
- https://fal.ai/docs/documentation/model-apis/media-expiration

## 4. MVP 선행 게이트 판정

| 필수흐름 | 검증된 사실 | 현재판정/잔여 |
|---|---|---|
| 음악/지시·동일프로젝트 두모드 | 수동구간·음원업로드·규칙콘티·모드왕복 실제UI | 로컬pass. AI기획아님 |
| 정확한입력·비용승인 | 준비버전·해시변조/참고승인·견적만료·호출/예산한도 | partial. gate가승인대상파일/프롬프트해시에핀되지않음 |
| 생성접수/중복방지/저장 | fake HTTP/큐·예산예약·중복클릭·재시작·응답유실 | localpass. 실통합미검증 |
| 실패/취소복구 | fake 취소경쟁·늦은결과·손상출력수동복구 | **fail**: 영구422도accepted에남아반복조회. 오류분류·폴링종료·안내필요 |
| 결과수집 | fake10초MP4디코딩·새take·기존선택보존 | partial.16MB제한으로유효한10초결과가막힐수있음. boundedstream/확장한도·경계QA필요 |
| 검토/부분수정 | 나란히비교·승인분리·타임라인버전 | localpass. actual-provider리테이크품질은1회테스트범위밖 |
| 음악포함출력 | 이번10초합성영상→take선택/승인→10초음악/자막→실제1920×1080,24fps,48kHz MP4 | localpass. `local-ten-second-rehearsal.json/mp4` 근거. AI결과아님 |
| 디자인/접근성 | neutral다크UI,비교390px,Tab/Escape,상태폴링수정 | partial. 생성전체여정의모바일/키보드,영구오류/취소UI,실생성대기상태QA는남음 |
| 비밀주입·비공개결과 | 어댑터기본비활성,키미조회 | **not implemented**: .env안전주입/승인핀/비공개ACL다운로드 |
| 실비용대사 | 예약·환급·분쟁원장컴포넌트fake검증 | actualbilling미검증. 견적을실비로표시하지않음 |

기존자동70/70·브라우저21건은그범위의통과다. 이번추가readiness진단은 **독립1pass(10초전체로컬출력),1fail(영구422분류)**. `readiness-error-classification.json`에재현증거. 이를70개회귀통과와상쇄하거나“전체준비완료”로요약하지않는다.

전체명세조직SSO/결제/자동음악분석/립싱크는MVP후속범위로분리하지만 위표의로컬미완료는실호출전에끝내야한다. 지금은권한거절이아니라**로컬선행작업미완료+외부실행승인대기**다. 실제요청0,비밀조회0,서버설정변경0.
