# 우선 발견: CC02, P2

원 CC01 9턴/재접속 반례와 canonical/provenance/isolation 독립 probe는 PASS. 관련 단위 회귀25개 PASS.

64KiB count/Message 직렬화 크기 차이: `AnthropicChatAdapter.count()`는 max_tokens를 제거(chat_runtime.py:85)하지만 Messages는 포함한다. count body가 상한 바로 아래일 때 메시지 body는 초과할 수 있다. transport가 opener 전 거절(anthropic_ontology.py:172–173)해도 runtime은 이미 submitted=True(chat_runtime.py:198)라 outcome_unknown/예약유지/후속접수거절로 처리한다(224–226,150).

`byte-boundary-evidence.json`과 `run_offline.py`로 재현. no live/no listener, synthetic-key/fake opener, temp DB. 기대: 확실한 로컬 미전송은 blocked_before_message 및 미사용예약해제. 현재: Messages opener0회인데 unknown/잠금. 실제 과금 누출은 아님.

최소 수정: count와 complete 전 전체 Messages envelope도 동일 함수로 preflight하고, transport가 보장하는 before-send rejection만 명시적으로 구분해 release. 실제 timeout/전송여부불명은 unknown 유지. 변경은 primary가 수행; audit는 소스 무수정.
