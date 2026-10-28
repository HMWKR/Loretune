# Private 실연동 사전검증 계획

2026-10-25. 상태: 계획만 작성. 새 upload/token/ACL/API키 조회/생성/기존 거절 다운로드 재시도는 실행하지 않음. 추가 Kling1회 예산1USD는 사용자가 승인했다. 단, 원인/수정 근거 확보 후에만 실행하는 조건부 승인이다. 아래 사전 근거 없이 같은 조건을 재발행하지 않는다. 계정/팀/키 metadata 조회는 별도 Aside에서 명시적 승인 부족으로 자동 승인심사에 거절됐고 새 사용자 승인 대기다. 이 경로를 우회하지 않는다.

## 비용을 쓰기 전 정상 경로 검증

공식 File Access Controls는 모델 추론 없이 direct upload에 lifecycle/initial_acl을 적용하는 경로를 제공한다. 따라서 **새 synthetic 파일1개를 private owner-only/1시간 만료로 직접 업로드 → 같은 기존 인증 주체의 단기 token으로 읽기 → 바이트 SHA256 일치 및 익명 접근 차단 확인**을 사전 통제로 제안한다. 이 단계는 모델 생성이 아니지만 별도의 외부 업로드·인증 사용이며 아직 승인되지 않았다. 저장/전송 비용을 무료라고 보장하지 않는다. 기본 공개 업로드 대조군은 필요하지 않으며 공개 노출 승인을 요구하지 않는다.

공식 절차: rest.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3에서 lifecycle과 PNG MIME으로 initiate한 후 반환된 presigned upload URL에 PUT한다. 원본 키는 rest.fal.ai 인증에만, 업로드 URL에는 키를 전달하지 않는다. URL은 공식 CDN 저장 계약에 맞는 HTTPS 목적지인지 사전 확인하고 예상 밖 host/redirect면 중단한다. private 읽기는 storage/auth/token 교환 후 CDN Bearer다. 로그에는 HTTP 상태·바이트수·해시·단계만 기록하고 URL/토큰은 남기지 않는다. 새 키나 영구 grant는 만들지 않는다.

이 검증이 성공해도 Kling 출력의 caller 소유권 전달은 따로 검증해야 한다. 직접 업로드 소유권과 모델 출력 소유권은 같은 것으로 가정하지 않는다. 실패하면 모델 생성은 진행하지 않고 scope/계정/팀/소유권 근거를 먼저 확보한다.403은 갱신이나 다른 키·sign/public fallback으로 우회하지 않는다.

## 가설별 증거와 통제 변수

| 가설 | 필요한 안전한 증거 | 판별과 한계 |
|---|---|---|
| custom key에 assets:read 없음 | 사용자/관리자 화면의 비밀 없는 권한 목록과 계정·팀 식별 | inference 성공은 assets:read 증명이 아님. 임의scope변경 금지 |
| 개인/팀 및 asset owner 불일치 | Dashboard가 확인한 request 귀속, provider가 확인한 output owner | metadata 조회 가능만으로 파일 소유권을 증명하지 않음 |
| caller token/requestID가 Kling 내부 upload에서 누락 | provider 지원/배포 담당의 해당request 추적 결과 | SDK 소스는 지원 계약만 입증; Kling 배포 동작은 미확인 |
| local token/CDN 구현 오류 | 승인 후 private 직접 업로드의 동일주체 인증 읽기, 해시 대조 | 성공 시 기본 client 경로 정상 근거. 모델 경로까지 증명하지 않음 |
| 파일 만료 | provider 보존/삭제 metadata 또는 지원 확인 | 1시간 요청만으로 정확한 삭제시각 추정 확정 금지. 기존403 재시도로 판별하지 않음 |
| redirect/host/부분 전송 | 현재 로컬 fault QA91개 및 향후 승인된 응답의 비민감 상태 | 로컬 방어 검증 통과. 실제 파일 미수신 상태의 코덱은 판단 불가 |

## 추가 실생성 게이트와 증거

1. 사전 private 읽기 통제 성공 또는 provider의 구체적 원인·정상 접근 복구 근거를 확보한다.
2. 사용자 추가1회/1USD 승인을 확인한다. 기존 승인 소진을 새 승인으로 간주하지 않는다. 공식 가격 재확인, frozen PNG/prompt/hash·duration10/audiofalse·private1시간·retry0 고정. 중요한 조건/가격 변경이면 중단한다.
3. 제출 전에 기존request/원장 조회로 중복접수 없음 확인. receipt 유실은 unknown으로 보존하고 새 요청을 만들지 않는다.
4. generated: requestID/status 완료와 결과 MIME/크기 metadata. 이는 로컬 완성 아님.
5. downloaded: 정상 인증200, 허용host, 크기·hash.403이면 중단하며 추가생성 없음.
6. validated: FFprobe 길이/코덱/해상도 및 FFmpeg 전체 decode.10초±0.2초, 실제 크기 기록. 요청 해상도와 관찰해상도 구분.
7. saved/registered: 임시파일 검증→원자 rename→DB Take1회, 기존 선택·승인 보존; 결과 hash 및 요청 연결.
8. export: 로컬 synthetic음원/한국어자막만 합성. 영상·음원·자막 stream, 길이·해상도·실제 재생 확인. 외부로 음악/자막 전송 안 함.
9. 비용: 견적/예약과 Dashboard 또는 Billing 실청구를 분리 기록. 실패·취소를 환불로 처리하지 않음.
10. 재시작 후 같은request/Take/export 유지 확인. 실제 동시 생성은 수행하지 않는다. 동시성·오류·격리는 synthetic fixture 결과로 별도 표기한다. 부하·다중host·실클라우드 배포는 미검증이며 단1회 성공으로 production 무결함을 보장하지 않는다.

## 부모가 요청할 정확한 추가 승인

조건부로 승인된 추가1회 Kling1USD와 별개로: **기존 FAL_KEY를 서버메모리에서만 사용해 동결된 비식별 PNG1개를 fal CDN에 private/1시간 만료로 직접 업로드하고, 같은 계정의 단기토큰으로1회 정상 읽기 및 익명 차단을 확인하는 사전검증**. 신규 credential/persistent grant/공개 ACL/기존 파일 변경은 없음. 모델 추론은 없지만 저장/전송 과금의 확정 자료가 없으므로 무료라고 약속하지 않는다. 계정 정책상 이 작업의 비용 범위가 불명확하면 실행 전 확인한다. 기존403파일 재시도 권한을 이 새파일 검증으로 자동 부여하지 않는다.

## 공식 근거

- https://fal.ai/docs/documentation/model-apis/file-access-controls : 직접 업로드 lifecycle 및 caller-token 계약. 직접 open은 도구 오류였으나 공식 검색 반환 본문으로 확인.
- https://fal.ai/docs/platform-apis/v1/storage/files/acl/get : assets:read 요구. 현재 문서 확인 성공.
- https://fal.ai/docs/platform-apis/v1/storage/files/sign : 임시 서명 기능과 assets:read 요구. 별도 접근 부여 기능이며 본 계획에서 호출하지 않음.

Dashboard 조사와 중복하지 않으며 해당 결과가 도착하면 계정/팀/소유권 가설만 갱신한다.

## 후속 증거 · Dashboard 확인 및 합산 예산

부모가 전달한 승인된 Aside 조회 보고서 `../live-kling-20261025/aside-dashboard-metadata-ko.md`를 실제 읽었다. 개인 계정/Owner, 동일 개인 요청 이력, 요청 Auth Method와 UI key 이름 일치, API / All models 표시는 확인됐다. 다른 팀을 잘못 선택했다는 증거는 없다. 다만 UI 이름으로 .env key 동일성이나 실제 asset owner를 입증할 수 없고, UI의 API 표시가 문서의 assets:read 포함 API preset과 정확히 같은 의미인지는 미확인이다. 권한 부족을 확정 원인으로 진술하지 않는다. metadata 조회 승인은 완료됐지만 실제 private 업로드 사전검증은 사용자 답변 대기다.

공식 비용 재확인(2026-10-25): Kling2.6 Pro I2V 페이지는 audio off $0.07/초를 명시한다.10초 모델 비용은 $0.70이며, 추가 테스트 총 $1에서 나머지 $0.30은 사전검증 등 부대 비용에 쓸 수 있는 잔여 한도이지 확인된 비용이 아니다. 이전 요청의 $0.70은 이미 지출된 별도 이력이다.

확인한 공식 CDN 문서·Model API Pricing·Data Retention 문서에서는 직접 파일 업로드/저장/다운로드/token 교환의 구체 요율 또는 무료 보장을 찾지 못했다. 이는 요금이 반드시 있다는 뜻도, 무료라는 뜻도 아니다. 따라서 사전검증과 추가 모델을 합친 공급자 청구가 $1 이하임을 현재 공식 근거만으로 보장할 수 없다. 모델 요율을 storage 요율로 대체하지 않는다. 실제 작업 전 저장/전송 부대비용이 잔여 $0.30 내임을 확인할 계정 요금 정보 또는 공급자 확인이 필요하다. 앱 요청 제한으로 공급자의 실제 총청구 상한을 강제할 수 없다.

- https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video (무음 초당 $0.07 재확인)
- https://fal.ai/docs/documentation/model-apis/fal-cdn (업로드·ACL·보존 설명, 무료/가격 보장 확인 못 함)
- https://fal.ai/docs/documentation/model-apis/pricing (Model API 출력별 과금·prepaid 설명; 직접 CDN 요금표 아님)
- https://fal.ai/docs/documentation/model-apis/media-expiration (업로드/출력 파일 보존 설명; 직접 CDN 요금 확정 불가)

이번 후속 작업은 문서 및 기존 로컬 보고서 읽기와 계획 수정뿐이다. 실키/실제 upload/token/CDN/모델 요청0. 현재 차단은 (1) private preflight 사용자 승인 대기 (2) 부대비용 확정 근거 부족이며, 자동심사 거절을 다른 경로로 재시도하지 않았다.

### 사전시험 사용자 승인 수신 후 실행 판정

부모가 사용자 “진행해” 승인을 전달했다. 신규 private PNG upload/read의 행동 승인은 충족됐다. 다만 “비용조건이 불명확해 예산 내 판정 불가면 실행하지 말라”는 조건은 그대로다. 공식 CDN 가격/무료 보장 근거가 확보되지 않아 총 $1 내 판정이 불가하므로 실제 initiate/upload/token/read는 실행하지 않았다. 현재 남은 차단은 승인 부족이 아니라 비용 조건 미확정이다. 모델 추가 호출도0이다. 필요한 다음 증거는 해당 계정의 직접 CDN 업로드·1시간 보관·다운로드·token 교환이 포함/무료인지, 또는 합계 $0.30 이하인지에 대한 요금 근거다. 이를 사용자에게 비용 제한 포기로 해석하거나 동일 승인 질문을 반복하지 않는다.


### 실행 근거 갱신 및 결과
부모가 공식 inference 과금 설명과 이미 승인된 소규모 통제시험을 근거로 진행 지시했다. 비용의 절대보장이 아니라 모델추론0 및 한정된 사용량의 합리적 근거로 실행했다. private-preflight-result-ko.md 참조: initiate/upload/token/read 모두200,4423bytes SHA일치. 추가Kling은 아직0회이며 부모 검토 대기.
