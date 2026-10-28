# 우선 발견: CC01 — 오래된 세션 금지사항 전달 누락 (P2)

독립 offline fixture 4개 중 3개 통과, 1개 반례 재현. **Claude를 호출한 결과가 아니라 실제 ChatRuntime이 만든 요청 payload 검사다.**

- `chat_runtime.py:143`이 완료 turn의 마지막 8개만 handoff에 추가한다. `chat_protocols.py:55`와 `model_selection.py:55`에도 비정규 세션 제약을 요약/보존하는 별도 필드가 없다.
- 합성 turn 1: `SESSION-LONG-913: For this session never orbit the camera.` → 2–9번 중립 대화 → Store 재열기 → 10번 계속 요청.
- 실제: DB 10 turn에 첫 금지사항이 남아 있지만 새 provider body에는 없음. 현재 canonical ontology에는 등록하지 않은 일회 세션 지시다. 데이터 삭제/Claude 기억 실패라고 과장하지 않는다.
- 기대: 07 §7.2의 중요한 금지사항·한시적 예외 보존. 관련 MS-FR-11/MS-AT18의 문맥 인계에도 영향을 준다. 최근 8 turn 지원 자체는 확인됐으나 일반적인 장기 세션 기억은 미충족.
- 최소 제안: session/project scope의 활성 제약을 provenance turn ID와 revision으로 보존하고, raw history window와 별도로 매 요청에 전달. 보존량 한도에 도달하면 조용히 버리지 말고 명시적 재확인/중단. 전체 과거 대화 무제한 전송은 제안하지 않음.
- 증거: `long-history-evidence.json`, `offline-results.json`, `offline_probe.py` C02. 원본 소스 수정 없음.

별도 capability gap: 현재 `chat_turn`은 `song,prompt`만 받으며 conversation/session ID가 없다. 같은 작품의 독립 대화 세션 분리는 미구현이고 작품 간 격리와 혼동하면 안 된다. 이것을 외부 프로젝트 정보 누출이나 확인된 제품 허위표시로 판정하지 않는다.
