# 실제 private CDN 통제시험 결과

판정: 성공. 사용자 승인된 synthetic PNG1개, 모델 추론0회, 재시도0회, 기존403 자산 접근0회. 신규키/권한변경/공개fallback 없음.

| 단계 | 실제 결과 |
|---|---|
| private lifecycle initiate | HTTP200 |
| presigned URL PUT | HTTP200, PNG4423바이트 |
| 같은 기존 FAL_KEY로 단기token 교환 | HTTP200 |
| Bearer 인증 GET1회 | HTTP200,4423바이트 |
| SHA256 비교 | 원본과 일치 |

원본 SHA256: `345156ca8dfe5abcfc54a9382820164fc42de77a32cf67ce9eb49e4dcdfcbcb1`.
정책 요청: default forbid/rules[], expiration_duration_seconds3600. 정확한 삭제시각·실제ACL조회·익명차단은 이번1읽기 제한에서 검증하지 않았다. 따라서 성공의 정확한 범위는 **private 정책을 요청한 직접 업로드를 동일키의 단기토큰으로 원본 그대로 읽기 성공**이다. 익명 접근 차단까지 검증한 것으로 확대하지 않는다.

기존.env는 승인된 인증 목적의 프로세스 메모리에서만 파싱했다. 원본키는 rest.fal.ai에만 전송했고 presigned PUT에는 키를 보내지 않았다. CDN GET에는 단기 Bearer만 사용했다. 키/토큰/URL은 출력·저장하지 않았으며 파일1개는 공급자에1시간 보존을 요청했다. 증거 JSON에는 상태/바이트/해시만 포함한다.

## 진단 변화

현재 클라이언트의 기본 직접업로드→동일주체 토큰→CDN읽기 경로가 일반적으로 고장났다는 가설은 약해졌다. 기존 Kling 출력403은 출력별 소유권/ACL·요청 귀속·provider caller-token 전달·당시상태 등으로 조사범위를 좁힐 수 있다. 이 시험은 과거요청의실키동일성/asset owner/ACL을 입증하지 않으며 assets:read 기반 Platform ACL API와 CDN Bearer 읽기도 별개다. 기존403의 확정 원인이나 수정 완료로 발표하지 않는다.

추가Kling1회는 부모가 이 결과와원인범위를 검토한 후 판단할 gate로 남는다. 같은설정 재생성만으로과거문제가수정됐다고추정하지않는다. 기존파일 재시도와추가모델호출은 하지않았다.

## 비용

공식 Model API 요금에서 실제 inference work 과금이라는 부모의 확인 근거와 사용자 구체승인에 따라 시행했다. 모델 호출0이므로 추가모델추론비용은0으로 예상한다. 별도storage/read실청구는 이HTTP응답으로확인할수없으며 미확정이다. 무료보장/총액확정으로표시하지않는다. 응답에는추가상품구매/업그레이드요구가없었다. 합산예산1USD 중 추후Kling 예상0.70외 부대비용은관측가능한계정사용량근거로별도확인이필요하다. Billing API를추가호출하지않았다.

실행: `scripts/private_cdn_preflight.py`, 증거: `private-preflight-result.json`. 같은명령재실행은결과파일exclusive-create로차단한다. 실제키가사용된결과를재현하기위한자동실행/재시도는없다.
