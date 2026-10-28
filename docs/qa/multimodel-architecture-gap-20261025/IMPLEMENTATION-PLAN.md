# 확인 후 구현 순서

사용자 확인: 2026-10-25 14:44 UTC. 원본 문서 보존. fal을 미디어 호출 경로로 사용하고 MCP·직접 Runway/Higgsfield 연결을 제외한다.

1. **모델별 계약**: 공개 공식 endpoint에서 확인한 fal FLUX Schnell / FLUX Pro1.1 / Kling2.6 I2V / Kling2.5Turbo I2V 계약을 등록한다. 등록은 검증/활성화가 아니며 기본 선택은 없다. 가격/계정/출력 접근이 확인되지 않으면 live 실행을 차단한다.
2. **공통 미디어 dispatch**: 기존 GenerationQueue·action/grant/ledger·권리/결과 저장 경계를 재사용한다. action의 모델/connection 고정값으로 라우팅하고 신규 승인된 tool 요청이 같은 큐에 접수되도록 연결한다. 기존 Kling 시험 경로·원장·실패 요청은 보존한다.
3. **채팅 분리**: 모델 protocol/body/continuation/usage를 provider adapter로 이동한다. resolver를 실제 선택에 적용하고 각 provider의 도구 결과를 같은 Store 도구에 연결한다. 기존 Anthropic 합성 gate를 일반 권한으로 확대하지 않는다.
4. **인계/명시적 선택**: 진행 job·원곡·IP·곡 예외를 보존하고 새 run에 공개 문맥과 receipt를 전달한다. 명시한 미지원 모델은 다른 모델로 자동 교체하지 않는다.
5. **fixture부터 검증**: 실제 파일·DB + synthetic HTTP로 3 chat protocol×2image×2video의 계약 조합, unknown/취소/중복/권리 철회/모델 변경을 검증한다. fake 조합은 MS-AT36 live pass가 아니다.
6. **통합/별도 live gate**: source baseline 비교, 전체 회귀, UI 연결/검증 후 각 공급자 계정·정확한 모델·자료·예산을 제시한다. 이번 단계 새 keys/인증 전송/유료 media 호출0.

현재 작업 위치와 원본 baseline은 `stage.json`. 실행 중인 앱/공유 데이터/디자인 전용 파일은 수정하지 않는다. 단계별 검증된 결과를 먼저 보고한다.
