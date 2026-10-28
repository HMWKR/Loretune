# 공개 공식 계약 근거

2026-10-25 조회. API/계정 인증 및 생성 요청 0. 문서상 지원과 실제 계정 사용 가능성을 구분한다.

| 계약 | 1차 근거 | 적용 / 제한 |
|---|---|---|
| Anthropic client tool | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview | tool_use→서버 검증→tool_result. 기존 합성 gate 유지 |
| Haiku5.5 | https://platform.claude.com/docs/en/models/haiku-5-5/overview | 기존 모델/소액 합성 가격 계약 유지. 이번 실제 호출0 |
| OpenAI Responses | https://developers.openai.com/api/docs/guides/function-calling | function_call_output+call_id. 같은 공급자 continuation에 reasoning items 유지, 다른 공급자로 인계·로그 보존하지 않음 |
| GPT6Luna | https://developers.openai.com/api/docs/models/gpt-6-luna | 공식 ID gpt-6-luna, function calling 지원. 표준 입력0.10/출력0.50 USD/MTok 문서값. 계정/실행/다른 tariff 미검증 |
| xAI Responses | https://docs.x.ai/developers/tools/function-calling | 공식 api.x.ai/v1/responses. 서버 client tool 왕복. 저장하지 않는 full-history continuation의 실제 계정 검증은 별도 |
| Grok4.7 | https://docs.x.ai/developers/models | 공식 ID grok-4.7, 입력2/출력6 USD/MTok 문서값. 변경 가능한 alias이므로 revision pinning 미검증 |
| fal queue | https://fal.ai/docs/documentation/model-apis/inference/queue | submit receipt의 owner/app/requests/ID URL만 사용. 전체 endpoint suffix로 상태 URL을 만들지 않음. NO retry header, 취소=환급 아님 |
| Schnell | https://fal.ai/models/fal-ai/flux/schnell/api | text-to-image prompt/image_size/num_images1/output PNG/steps4/safety true. 캐릭터·스타일 참고 입력을 지원하는 모델이라고 가정하지 않음 |
| FLUX Pro1.1 | https://fal.ai/models/fal-ai/flux-pro/v1.1/api | text-to-image. safety_tolerance2, enhance_prompt false. Schnell 필드를 그대로 보내지 않음 |
| Kling2.6Pro | https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api | start_image_url,duration5/10,generate_audio false,safety true |
| Kling2.5TurboPro | https://fal.ai/models/fal-ai/kling-video/v2.5-turbo/pro/image-to-video/api | image_url,duration5/10,safety true. 지원되지 않은 generate_audio 필드를 넣지 않음 |
| fal private output | https://fal.ai/docs/documentation/model-apis/file-access-controls | 기존 default forbid / 1h 요청 계약 재사용, 실제 제공자 출력 접근 지원은 미검증. 공개 fallback 없음 |

새 fal 모델의 현재 유료 견적은 이번 공개 본문에서 확정하지 않았다. 시험 코드는 명시된 fixture 견적만 사용한다. 운영 모델 견적은 모델/입력 hash/가격 revision/유효시간/공식 source에 고정된 서버 주입을 요구하며 없으면 접수 불가. 과거 Kling0.70을 다른 모델 가격으로 전용하지 않는다.

OpenAI/xAI의 실제 토큰 사전 계산기는 아직 검증하지 않았다. 어댑터는 명시적으로 주입된 counter 없이는 제출하지 않으며, 문서에 없는 count endpoint를 생성하지 않았다. 실제 인증/요금 승인과 계정 계약이 확보되면 각 공식 counter/토크나이저 계약을 검증해야 한다. 캐시·비표준 서비스 tier를 정상 요금으로 확정하지 않고 unknown/예약 보존으로 처리한다.

비공개 생성 이미지의 fal URL을 영상 모델이 읽을 수 있다고 가정하지 않는다. 수신·검증·로컬 저장한 PNG를 사용권과 현재 시작 프레임 승인 후 data URI로 인코딩한다. 실제 외부 재전송은 그 영상 작업의 별도 gate 범위다. URL 만료를 서버 삭제 보장으로 표현하지 않는다.
