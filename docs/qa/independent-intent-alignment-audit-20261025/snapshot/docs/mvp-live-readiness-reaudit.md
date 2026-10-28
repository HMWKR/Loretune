# Kling 준비 재감사 — 2026-10-25

판정: **이번 감사에서 발견한 6개 로컬 게이트는 수정·검증 완료. 실제 provider 통합과 비용·비공개 동작은 승인 후 검증 대기. MVP 전체 완료 아님.**

## 개별 기준과 증거

| 게이트 | 수정 및 실제 검증 | 판정 |
|---|---|---|
| 영구 오류/원장/재시도0 | 접수 또는 조회422는 failed로 종료. 예약 uncertain, 자동 환급/재발행 없음. 일시 오류3회 후 reconciliation_required, 접수번호 있을 때 수동 상태 조회만 제공 | local pass: test_live_gates 422 두 경로, transient test, readiness-error-classification.json |
| 승인 입력 고정 | workspace/작품/샷, 이미지SHA256, trim한 프롬프트SHA256, 모델, 무음10초, privacy/retention, 가격·확인시각 고정. 1회·최대$1 로컬발행제한 | local pass: 입력·가격·privacy 불일치 거절 및 기존 큐/예산 회귀 |
| 파일/다운로드 경계 | 일반 업로드16MiB 유지, 서버 provider 결과128MiB 제한·bounded read·ContentLength·MIME·ftyp·FFmpeg 실제 디코드. 리다이렉트 불허·v3b.fal.media만 허용 | local pass: 정확한 한도/초과/잘못된 길이·타입·서명 및17MiB reader 검사. 실제128MiB 유효 영상 생성은 미수행 |
| 화면·복구 | 모바일390px 준비/실행/503대사/재조회/422/취소/모드왕복. Tab·Enter 준비 저장 및 notice 포커스 복구. 기존 비교/음원출력 UI 회귀는 BQA1–21 | local pass: BQA22–25, 화면3장. 모든 OS/보조기기 접근성 인증을 의미하지 않음 |
| 비공개 결과 | 생성 헤더 initial_acl.default=forbid, 만료3600초. 서버가 rest.fal.ai에서 단기 토큰을 받아 CDN Bearer로 사용. 원본키는 CDN에 보내지 않음. receipt/result/input은 브라우저 state 제외 | fake contract pass. 실제 ACL/토큰 발급·익명 접근차단 미검증, 실행승인 필요 |
| .env 런처 | 명시 플래그/유효 승인문서 전 파일접근0. O_NOFOLLOW 단일파일 open, regular/64KiB 제한, 리터럴 한 항목만 파싱, shell/환경변수 변경/저장 없음 | synthetic fixture pass: 중복·보간·명령·symlink·과대·인코딩 거절. 실제.env 미조회 |

최종 자동 회귀 **80/80, 실패0**, Python AST 및 최종 JavaScript `node --check` 통과. 브라우저 누적25건. 96FR/192조건 및143API 추적 유지. 전체 원문FR/API 완료0은 전체명세의 조직권한·프로덕션 인증/공급자·비기능 기준까지 모두 증명하지 않았기 때문이다. FR067 로컬 출력 수용기준 충족과 전체 출시판정은 별도다.

10초 합성 리허설의 실제1920×1080/24fps/48kHz+자막 MP4는 `qa/20261025/local-ten-second-rehearsal.*`에 보존. AI 결과 아님. 기존 승인take를 새 결과가 덮어쓰지 않는 큐/취소/늦은응답/복구 테스트 통과. 전체 시스템은 로컬 단일 사용자 MVP 범위이며 원격 다중 사용자 자산 ACL은 제공하지 않는다.

## 최종 실호출 승인안 — 아직 실행 안 함

- Endpoint: `fal-ai/kling-video/v2.6/pro/image-to-video`, Kling2.6 Pro I2V, duration `10`, `generate_audio:false`, safety checker 활성. API에 고정 해상도 필드가 없어 원본1080p는 보장하지 않고 수신 후 측정. 로컬 출력1080p는 별도 리사이즈다.
- 외부 전송: `qa/fixtures/kling-live-v1/start-frame.png`(1280×720,4423bytes)와 `prompt.txt`의 trim한220bytes 이하 영어 프롬프트. 기하학 풍경이며 인물·상표·개인정보 없음. `local-audio.wav`/`captions.srt`는 외부 전송하지 않는다. manifest의4개 파일 해시 전부 재확인·변경없음.
- 가격 공식 확인: 2026-10-25T05:10:14Z 이후 확인. $0.07/초 ×10초=$0.70. 제안 상한$1/1회. 재시도0 (`X-Fal-No-Retry:1`), 응답유실은 새POST하지 않음. 로컬 제한은 공급자 계정 청구·세금·다른앱 사용을 통제하는 결제 한도가 아니다. 실행 직전 가격 재확인하고 승인 문서에 시각 고정.
- fal prepaid credit 방식은 공식 문서 근거. 사용자 계정 잔액/청구유형/자동충전은 미조회. 충전·구매는 하지 않는다.
- 500+ 미과금 안내가 있지만422는 GPU사용 후 실패면 과금 가능. 취소는 환급보장 아님. 실제 청구 증거 없이는 예약을 실비/환급으로 변경하지 않는다.
- 기존 `.env`의 지정 키 항목을 **서버 메모리에만 읽는 일회 실행**과 해당 fal 생성/상태조회/비공개 결과토큰교환/다운로드 승인이 필요. 새 키저장·영구 연결설정·계정 보안설정 변경 없음. 승인 문서는 최대1시간/지정작업/해시/가격/1회만 유효하게 구성한다. 아직 실제 승인 문서/실행 서버를 만들거나 실제 파일을 읽지 않았다.
- 비공개 생성 요청 header는 코드로 준비했으나 공급자에 아직 전송하지 않았다. fal URL 기본공개 특성과 로컬 접근은 별개. 비공개 옵션 실제 지원 실패 시 공개 fallback하지 않고 보류한다. 공식지원CDN과 다른 결과host도 보류한다.

공식 근거: [모델/요율](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video), [입력 계약](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api), [가격](https://fal.ai/docs/documentation/model-apis/pricing), [실패 과금](https://fal.ai/docs/documentation/model-apis/faq), [큐 재시도](https://fal.ai/docs/documentation/model-apis/inference/reliability), [파일 ACL](https://fal.ai/docs/documentation/model-apis/file-access-controls), [만료](https://fal.ai/docs/documentation/model-apis/media-expiration).

## 남은 범위

실제 Kling 생성 성공·얼굴/동작 품질·대기시간·최종 해상도·실비·비공개ACL은0회라 미검증. 실제 결과의 로컬 take 연결→검토→음악포함출력까지 최종 live QA 필요. 한 번의10초 호출은 실제 재생성 품질/반복일관성을 검증하지 못한다. 별도 테스트 승인이 없으면 fake 리테이크 계약 검증 범위로 남긴다. 자동 음악/가사 분석·립싱크·조직SSO·상용 결제 등은 후속 범위이며 UI에서 구현됐다고 표시하지 않는다.

이번 작업에서 실제 키조회0/이미지 외부전송0/모델호출0/비용0. 로컬 기본서버8765는 새 코드로 재시작, PID93882, provider 비활성. 기존 렌더6건완료/진행0 및 provider작업0 확인 후 재시작했다. 권한 거절: 제한된 셸의 ps 조회가 OS에서 거절되어 반복하지 않았고, lsof의 소유 cwd/포트와 알려진 자체 PID로 확인했다. 미확정 외부작업 없음.
