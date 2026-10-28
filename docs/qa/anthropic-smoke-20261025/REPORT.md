# Anthropic 합성 온톨로지 실제 시험

> 후속 실제 추출·tool roundtrip·최종 답변 결과는 [통합 보고서](../claude-grounding-20261025/REPORT-ko.md)를 참조한다. 아래는 최초 smoke 기록이다.

2026-10-25. 사용자가 승인한 합성 인물/장소/의상 충돌 텍스트만 전송했다. 기존 `Anthropic_KEY`는 메모리 인증에만 사용했다. 키·thinking block·원본 응답은 저장하지 않았다. 실 프로젝트 문서·음원·이미지는 전송하지 않았다.

## 결과

- 모델: `claude-haiku-5-5`, 공식 Messages API. count_tokens 1회, Messages 1회. 재시도/모델 fallback/충전 없음.
- 입력 해시: `a647f21005713304a5ac9c8ce1eb020a1bb073a91b824b80ed806b35255d4293`. 합성 요청 전체는 `request.json`에 있다.
- 사전 입력 1,283 tokens. 실제 usage 입력 1,283 / 출력 2,048 tokens.
- request ID: `req_011CgNn1N4CFqz2GQs6XFV8b`, message ID: `msg_011CgNn1PDtGp38a4bALiegf`.
- API 응답을 받았지만 stop_reason=`max_tokens`. 완전한 구조화 제안이 아니므로 schema/provenance/conflict 검증을 통과시키지 않고 적용을 거절했다. proposal 파일은 생성하지 않았다.
- 상태는 `response_validation_failed`. 접수 여부 불명이나 인증 실패로 분류하지 않는다. 자동 재호출하지 않는다.

공식 모델 단가(2026-10-25 재확인): 입력 $0.10/MTok, 출력 $0.50/MTok, prompt 100k 이하. 사용량 계산 비용은 **$0.0011523**이다. 계정 billing 실청구는 별도 미확인이다. 누적 원장 `usage.sqlite3`에는 반올림한 micro-USD 1153을 보수적으로 기록했다. 이번 예약은 $0.001434, 사용자 승인 누적 한도는 $50이며 지출 목표가 아니다. 다른 공급자 원장과 분리했다.

## 구현 및 검증

`scripts/anthropic_smoke.py`는 SQLite BEGIN IMMEDIATE로 예산과 시도 ID를 먼저 기록한다. 동일 ID 재실행을 거절하고 응답 불명 때 예약을 보존한다. count와 Messages transport는 고정된 공식 origin/endpoint, TLS, redirect 거부, 응답 크기·시간 제한을 유지한다. 실제 요청 전 fake 시험으로 중복 호출 차단·키 비노출·토큰 초과 중단·정확한 변수명 처리를 확인했다.

기본 adaptive thinking을 포함한 출력 한도 2048이 이번 응답에는 부족했다. 다음 평가 전에 공식 지원되는 effort 설정과 출력 상한을 검토하고, 동일 합성 자료의 완결된 추출/충돌 보존을 목표로 별도 입력 해시·견적·시도 ID를 준비해야 한다. 현재 결과는 연결 성공의 증거이며 온톨로지 품질 성공의 증거가 아니다. 더 큰 batch나 자동 fallback을 실행하지 않았다.

근거: [모델·가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview), [token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting), [count_tokens 계약](https://platform.claude.com/docs/en/api/messages/count_tokens), 로컬 `result.json`, `usage.sqlite3`.
