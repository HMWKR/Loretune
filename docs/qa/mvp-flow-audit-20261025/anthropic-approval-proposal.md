# Anthropic 온톨로지 제안 시험 승인안 — 미실행

2026-10-25. 실제 키 조회·인증 전송·count_tokens·유료 호출은 0회. 기존 Kling 예산과 별개다.

## 제안하는 단일 시험

- 모델 `claude-haiku-5-5`, Messages API `https://api.anthropic.com/v1/messages`.
- 목적: 합성 문장에서 인물/장소/스타일 및 관계를 **제안**하고 출처와 모순을 검토하는 것. 채팅 기획이나 실제 고객 자료 전송은 이번 범위에서 제외.
- 합성 입력: “Mira and Theo perform on a rooftop. Mira wears a blue coat.” 및 별도 문서 “Mira wears a red coat in the studio. It is unknown whether this replaces the rooftop costume.” 실제 음악·사진·개인정보·다른 프로젝트 데이터는 제외.
- 서버 `Anthropic_KEY`를 기존 환경에서만 읽는 credential supplier를 추후 승인 후 연결. 키 생성/복사/저장, .env 수정, 프런트 전달 없음. 키가 노출되면 해당 계정의 무단 API 사용 위험이 있으므로 인증 헤더·예외·응답 로그에 비밀을 남기지 않는다.
- 제안 입력 예산 4,096 tokens / 출력 `max_tokens=2048`, 1회, 자동 retry 0, cache 0, tools 0, fallback 0. 입력 토큰 검사는 승인 후 수행하며 초과하면 제출하지 않는다. 현재 12KB 로컬 요청 제한은 토큰 수 검증을 대체하지 않는다.
- 공식 100K 이하 입력 $0.10/MTok, 출력 $0.50/MTok 기준: 4,096×0.10/1,000,000 + 2,048×0.50/1,000,000 = **$0.0014336 예상 상한**. 제안 승인 예산 **$0.01**, 실제 계정 가격/모델 가용성과 전체 요청 토큰은 실행 전 재확인. 앱 예산은 제공자의 최종 청구액을 강제 제한하는 보장은 아니다.
- 구조화 출력 `output_config.format = {type:'json_schema', schema:...}`. 스키마 통과도 의미적 사실 정확성 보장은 아니다. 미완료/refusal/max_tokens/출처 불일치/상충하는 확정 주장은 거부한다. 결과는 사용자 승인 전 데이터에 적용하지 않는다.

공식 근거(2026-10-25 공개 문서 조회): [Haiku 5.5 모델·가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview), [구조화 출력](https://platform.claude.com/docs/en/build-with-claude/structured-outputs). 모델·계정 실제 통합은 아직 검증하지 않았다.

## 구현 계약과 부모 연결 예시

`ontology.initialize(conn)`은 기존 Store 초기화 트랜잭션 안에서 호출한다. scope는 HTTP 요청 값을 신뢰하지 않고 인증된 workspace/IP/project ID로 서버가 생성한다. 이 모듈 자체는 인증 또는 조직 권한 시스템이 아니다.

```python
# 모두 Store.connect()의 같은 transaction 안에서 수행
head = ontology.snapshot(conn, authorized_scope)
proposal = ontology.propose(conn, authorized_scope, reviewed_graph,
                            head['revision'], actor=user_id)
# 별도 검토 화면에서 사용자가 승인한 뒤
updated = ontology.apply(conn, authorized_scope, proposal['id'],
                         head['revision'], approved_by=user_id, approved=True)
# 필요한 Studio 상태 갱신도 같은 connection transaction에서 수행
```

`rollback`은 이전 버전을 삭제하거나 수정하지 않고 선택한 버전의 내용을 새 revision으로 기록한다. 동일 proposal 재적용·오래된 base revision은 Conflict로 막으며 외부 작업 재요청을 유발하지 않는다. 안정 ID는 `stable_id(scope, type, immutable_source_key)`로 생성한다. label이나 변경 가능한 프로젝트 표시명으로 source_key를 만들지 않는다.

Anthropic 어댑터 `AnthropicOntology(transport, credential_supplier, enabled=False)`는 기본적으로 연결이 차단된다. 실제 네트워크 transport는 이 구현에 없다. 승인 후 서버 전용 transport가 필요하며 redirect 금지·timeout·응답 크기 제한·인증정보 비노출을 적용해야 한다. fake transport는 반환 body를 검증한다. 현재 UI 연결·사용자 review/apply·레거시 Studio stable-ID 매핑은 부모 통합 작업이며 이 독립 모듈 완료로 제품 전체 온톨로지 완료를 주장하지 않는다.

## 로컬 증거와 한계

`python3 -m unittest discover -s tests -p '*ontology.py' -v`: 16개 통과. 임시 SQLite만 사용. 승인 필요, 스코프 격리, dangling/type mismatch, 파생 사이클, ID 재유형화 방지, stale/중복 적용, fault-trigger 원자 롤백, 바깥 Studio transaction 롤백, 재시작·버전 복원, disabled provider, exact-source-span, conflict uncertainty, refused/truncated response, duplicate JSON, 키 예외 비노출, retry 0을 검증했다.

Haiku 5.5 기본 adaptive thinking 응답 블록은 저장하지 않고 text 블록만 검증한다. 출력 예산은 thinking을 포함한 제공자 전체 출력 한도이다.

출처 excerpt는 입력에 정확히 포함되어야 하지만 자연어 사실 일치의 완전한 검증기는 아니다. 상충 주장은 같은 type/label의 다른 설명을 최소 탐지하며 모든 자연어 모순을 해결하지 않는다. 다중 사용자 인증·네트워크 운영·실제 Anthropic 품질·UI 연결은 이 16개 테스트의 범위가 아니다.


## 통합 후 갱신

현재 `BoundedMessagesTransport` 서버 전송 구현도 존재한다. 공식 endpoint 고정·TLS·redirect 거부·100KB 응답·30초 socket/read deadline·자동 재시도0을 fake opener에서 검증했다. credential supplier 예외 내용도 제거한다. 실제 인증/요청은 실행하지 않았다. 수동 후보 검토·승인·복원 UI와 SQLite transaction은 앱에 연결됐고, 실제 Anthropic 제안 요청 버튼/작업 실행 경로는 아직 활성화하지 않았다. 승인 후 synthetic smoke 연결과 실제 structured-output 모델 지원 여부 확인이 필요하다. count_tokens 전송 역시 승인에 포함되어야 한다.
