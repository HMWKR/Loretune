# 이미지 공급자·접근·비용: 결정에 필요한 최소 사실

공식 문서 재확인: 2026-10-25T13:53:25.863972+00:00. 실제 인증·생성·권한 조회 0. 이 문서는 Runway 활성화 승인을 대신하지 않는다.

## URL 수명과 파일 보관·접근권한은 다르다

공식 원문: https://docs.dev.runwayml.com/assets/outputs/ — API Output Formats, 현재 본문 121행.

> these URLs are ephemeral: they will expire within 24-48 hours of accessing the API.

위 문장은 **API를 조회한 시점 기준 결과 URL의 만료**를 설명한다. 생성 시점부터 정확히 24시간 또는 48시간 보장, 원본 파일의 서버 삭제 시각, 백업/로그의 삭제를 뜻하지 않는다. 같은 페이지는 결과를 자체 저장소로 내려받고 제품에 원격 URL을 직접 노출하지 않도록 안내한다.

예시에는 CloudFront 결과 URL의 `_jwt` query가 있다. 이 때문에 이전 문서에서 서명 URL이라고 불렀지만, 이 페이지는 구체적인 JWT 검증 주체·사용자/팀 ACL·본인만 접근하는 정책을 명세하지 않는다. **누구나 공개 열람 가능**이나 **계정 소유자만 열람 가능** 모두 이 자료만으로 확정할 수 없다. URL을 아는 제3자의 접근, 별도 인증 요구, 철회·만료 이후 보관은 실제 계정 및 별도 공식 계약에서 확인해야 한다. fal의 default-forbid·본인 allow·3600초 요청과 동등하다는 근거가 없다.

staging UI는 “API 조회 후 24–48시간 내 URL 만료 · 서버 파일 삭제 시각·본인 전용 접근 미확인”으로 수정했다. 정책 식별자 `runway-signed-url-24-48h; local-copy; not-fal-private-1h`는 기존 내부 계약 식별자이며 삭제 보장이나 검증된 ACL이라는 의미로 사용하지 않는다.

## 인증 필요와 기존 승인 범위

공식 시작 문서 https://docs.dev.runwayml.com/guides/using-the-api/ 는 Runway Dev 계정과 Bearer API 인증을 사용하며 예시 환경변수는 `RUNWAYML_API_SECRET`이다. 현재 `runway_provider.py`도 서버에서 주입받은 `key`를 Runway API에만 사용하고 다운로드에는 전송하지 않는 구조다. 자동 환경변수 로딩/활성화는 없다.

Runway용 인증이 기술적으로 필요하다. **사용자에게 해당 키가 이미 있는지는 미확인**이다. `.env`나 키 목록을 조회하지 않았으므로 “새 키를 반드시 발급해야 한다” 또는 “기존 키가 없다”고 단정하지 않는다. 지금 확인된 기존 사용자 승인은 fal과 Anthropic에 관한 것이고 Runway 인증 전송·계정 연결·실제 이미지 비용은 승인되지 않았다. 다른 서비스 키를 재사용할 수 없다.

## 명세가 Runway를 강제하는가

- `07_Chat_Directed_Multimodel_Production_Spec.md:79–88`: Runway/Luma/xAI/Google/중개 공급자를 대표 연결 경로의 **예시**로 열거하고 모든 행을 첫 출시에서 동시에 연결할 필요가 없다고 명시한다. 81행의 이미지 예시는 `gen4_image`다.
- 같은 문서 67행은 모델 예시가 영구 기본값이나 계정 호출 가능성 보장이 아니라고 밝힌다.
- `docs/knowledge/project_kit/sources/current_spec/chapters/01_business.md:104`: gen4_image를 비용 모델 시나리오의 기준으로 사용한다. 제품 최종 공급자 선택이나 인증·유료 호출 승인 문장이 아니다.

따라서 현재 Runway 경로는 좁은 어댑터 후보다. registry는 `integration_unverified`, 일반 실행은 비활성으로 유지한다. 이 문서 작성으로 후보를 사용 가능으로 바꾸지 않았다.

## 사용자에게 필요한 최소 선택

1. **MVP 이미지 입력을 지금처럼 기존 이미지 업로드로 유지할지, Runway gen4_image를 다음 실제 연결 검증 후보로 선택할지.** 전자는 새 credential·이미지 비용·외부 전송 없이 계속 사용할 수 있다. 후자는 Runway용 인증 사용과 별도 합성 입력/소액 시험 승인이 필요하다. 선택 자체가 live 실행 승인은 아니다. 본인만 접근·1시간 삭제가 필수라면 현재 Runway 자료로 충족을 입증하지 못하므로 먼저 해당 계약을 확인하거나, 명세의 중개 공급자 확장 중 구체적인 이미지 endpoint를 별도로 선택해야 한다. fal 이미지 endpoint는 이 패치에 구현되어 있지 않다.
2. **비용 자동 조회가 지금 필요한가.** 현재 기록 가져오기/대조 hook과 미확정 표시를 유지하면 새 승인 없이 로컬 흐름을 완료할 수 있다. 자동화를 원하면 과거 fal 요청 ID와 기간·워크스페이스로 한정한 billing records 읽기를 승인받고 기존 연결이 지원하는 읽기 범위를 확인해야 한다. 권한이 부족하면 자동 확대하지 않으며 사용자 제공 내보내기 기록을 대조하는 대안이 있다. 새로운 billing 호출·스케줄러·계정 변경은 이번에 구현/실행하지 않았다.

공식 비용 API 근거: https://fal.ai/docs/platform-apis/v1/models/billing-events (요청별 기록), https://fal.ai/docs/platform-apis/v1/models/usage (집계 usage). 기록 없는 금액을 actual로 만들지 않는다. Runway task credits는 보고된 credit 사용량이며 USD 청구서가 아니다. 이번 패치는 이 구분을 그대로 보존한다.
