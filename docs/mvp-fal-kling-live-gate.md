> 최신 재감사: [mvp-live-readiness-reaudit.md](mvp-live-readiness-reaudit.md). 아래 이전 감사의 미구현/실패 판정은 이력이며 최신 문서가 우선합니다.

> 최신 준비 감사: [mvp-live-readiness-audit.md](mvp-live-readiness-audit.md). **NOT READY**. 정확한fixture/프롬프트·가격재확인·credit·키주입미구현·비공개ACL·영구422오류와MVP선행게이트를 그 문서에서 확인하세요. 아래는 최초 제안이며 완료 판정이 아닙니다.

# MVP 마지막 실호출 게이트 — fal.ai Kling

2026-10-25. 사용자 지시: 시스템과 디자인을 먼저 마무리하고 마지막에 약10초 실제 테스트. `.env`에 API키가 있다는 사실만 전달받았으며 값·존재·유효성은 조회하지 않았다. Runway 제안은 폐기했다.

## 실제 MVP 완료 기준과 순서

음악/장면 요청 → 실제 Kling 영상 생성 → 샷 검토/선택/승인 → 부분 수정 → 음악·자막 포함 MP4 → 새로고침/재시작 복구. 채팅형과 작업대는 동일 프로젝트를 사용한다. 기존 96FR/143API 전체가 MVP 필수는 아니다. 조직 SSO, 결제, 다중공급자, 자동 음악분석, 립싱크, 자동 공유배포는 후속 범위다. 규칙 기반 콘티는 AI 기획으로 표시하지 않는다.

1. 로컬 저장·작업 상태·원장·견적·실패 복구 및 디자인 검증.
2. fal 어댑터 fake 계약 테스트와 비활성/비밀 비노출 검증. 실제 요청0.
3. 동일 프로젝트의 생성 요청/결과 수집/테이크 연결과 검토 UI 연결. 충돌·응답 유실에서 재발행 금지.
4. 전체 로컬 회귀 및 키보드·반응형·실제 브라우저 흐름 QA.
5. **마지막 live gate**: 아래 범위 확인 후에만 기존 키를 서버 환경으로 주입하고1회 생성. 현재 live_enabled 기본false이며 서버에서 어댑터를 실행하지 않는다.

## 선택 모델과 입력

- ID: `fal-ai/kling-video/v2.6/pro/image-to-video` (Kling2.6 Pro I2V). immutable release hash는 공개 페이지에서 확인하지 못했으므로 endpoint/요금확인시각/입력hash를 기록하고 재실행 전 재확인한다.
- `duration: "10"`, `generate_audio: false`, `enable_safety_checker: true`. native audio 기본값은true여서 반드시false를 명시한다. voice_ids/end_image_url은 보내지 않는다.
- 전송 자료: 새로 만든 비식별 추상 풍경 PNG1장(1280×720)과 움직임 프롬프트1개. base64 data URI로 전송. 원본 사용자 음원·가사·사진·IP 문서는 전송하지 않는다. 테스트 음원은 로컬에서 합성한다.
- 결과: 영상URL을 받은 뒤 신뢰할 수 있는fal 미디어 호스트, 크기·형식·실제 디코딩을 검증하고 로컬 take로 저장. 생성 성공과 사용자 승인은 별개다. 생성 원본 해상도는 실측하고1080p 캔버스 리사이즈와 구분한다.

## 비용 및 요청 한도

공식 가격은 무음$0.07/초이므로 **10초1회 예상$0.70**. 네이티브 음원과 voice control을 사용하지 않는다. **제안 승인 상한: 생성1회, 총사용량$1.00, 자동 재시도0회**. 상한은 현재 문서 단가에 근거한 로컬 발행 제한이며 제공자 요금 변경/세금/별도 잔액충전까지 보장하는 지출계약이 아니다. 호출 전 단가가상한을 넘으면 중단한다. 기존 잔액/결제상태는 미확인이다. 추가 생성·리테이크·충전은 이1회에 포함하지 않는다.

한 번의10초 호출은 연결/출력 smoke test다. 실제 공급자 부분 재생성까지 완전 검증하려면 별도 추가 호출 승인이 필요하다. 그 전에는 부분 수정·승인본 보존을 fake/기존 로컬take로만 검증했다고 표시한다.

Queue POST에는 `X-Fal-No-Retry: 1`을 사용한다. 공식 설명상 기본 큐 재시도가 있으므로 명시적으로 끈다. 접수 응답의 request_id와 상태/결과URL을 저장하고 조회한다. POST응답 유실은 미확정 예약을 유지하고 자동 재발행하지 않는다. 서버5xx 실패는 공식적으로 미과금이라고 설명하지만 로컬 타임아웃/취소가 무조건무료라는 뜻은 아니다. 실행 중 취소는 중단 신호이며 환급 확인은 별도다. 과금 확정 근거가 없으면 견적을 실제 비용으로 정산하지 않는다.

## 실행 직전에 필요한 질문만

“시스템·디자인 QA가 끝난 뒤, 기존 fal 키를 서버 프로세스에서만 사용해 위 비식별 PNG/프롬프트로 Kling2.6 Pro 무음10초를1회(예상$0.70, 사용량상한$1, 재시도없음) 실행해도 될까요? 기존 키가 서버에서 사용하는 환경변수 이름이 `FAL_KEY`인지 이름만 알려주세요.”

키 값은 질문하지 않는다. `.env`를 출력하거나 브라우저·로그·보고서에 전달하지 않는다. 기존 credential의 프로세스주입은 승인 후 필요 최소 방식으로 처리하며 새 키·지속 연결·결제·자동충전은 만들지 않는다. 지금은 질문 준비 단계이며 시스템 QA를 건너뛰고 실호출하지 않는다.

## 근거

- 모델 가격: https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video
- 입력스키마/dataURI/결과: https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api
- 큐수명/응답URL/재시도해제: https://fal.ai/docs/documentation/model-apis/inference/queue
- 서버오류 과금설명: https://fal.ai/docs/documentation/model-apis/inference/reliability
- 취소: https://fal.ai/docs/inference-api/queue/cancel

공개 공식 문서 조회만 실행했고 키·계정·잔액 조회와 생성은 하지 않았다. `fal_provider.py`는 기본 비활성, 환경 변수는 명시 live_enabled 이후에만읽도록 구성. 현재 테스트는 fake transport이며 네트워크·공급자 통합완료가 아니다.
