# 승인된 Kling 1회 실검증

사용자가 승인한 기존 fal.ai 키의 서버 메모리 인증으로 단1회 요청. 동결한 기하학 PNG·영문프롬프트만 전송, 오디오·자막은 로컬용이다. 키·토큰·결과URL은 이 보고서에 포함하지 않는다.

2026-10-25 실행 직전 공식 모델 페이지에서 무음 $0.07/초를 재확인했다. 10초 예상 $0.70, 로컬 승인한도$1, 자동재시도0. 실제 청구액·잔액·자동충전은 미조회이며 생성 성공만으로 비용을 확정하지 않는다.

- 모델: fal-ai/kling-video/v2.6/pro/image-to-video
- 옵션: duration10, generate_audio false, enable_safety_checker true
- 결과 정책: initial_acl default forbid / rules [], expiration_duration_seconds3600
- CDN 인증: 기존 키를 CDN에 보내지 않고 서버에서600초 토큰을 교환하여 사용
- 원본·최종 결과 메타데이터와 진행은 result.json 및 후속 보고서 참조
- 기존 QA 브라우저 공간2가 사라졌으므로 이번 실제 UI 회귀는 아직 미실행. 공간0은 조작하지 않았다.

공식 근거: https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video · https://fal.ai/docs/documentation/model-apis/file-access-controls · https://fal.ai/docs/documentation/model-apis/media-expiration

주의: 1시간 만료는 CDN파일 정책이며 모든 공급자 로그/요청이1시간 후 삭제된다는 뜻은 아니다. 실제 만료 시점 삭제는 별도 관찰 전 미검증이다.
