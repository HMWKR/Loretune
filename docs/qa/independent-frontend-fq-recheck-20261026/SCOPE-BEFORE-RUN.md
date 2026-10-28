# 오프라인 FQ 재검증 범위

원래 ASY01/ASY02/MED02/STO02의 입력과 assertion을 보존하여 before/after 양쪽에서 실행한다. 원래 suite 중 네 반례만 선택한다. 새 global/helper를 VM에 추가하고 snapshot 경로 및 기대 hash를 대상에 맞춘다. source body는 변경하지 않는다. 모든 변경은 harness diff로 남긴다.

추가 guard: 동일 revision jobs/generation 진행; 늦은 poll의 workspace/busy/context/epoch 거절과 느린 poll 진행; native ended의 clip/controller/manual-pause/audio-clock 경계; denied Storage와 정상 empty 구별, known ID 조회/추가 POST 차단, settled response 보존, draft fallback. 기존 F07/DM01–03/저장 피드백 회귀를 재실행한다.

HTTP·포트·브라우저·외부 provider·키·공유DB·설치·앱수정 금지. 실제 브라우저 재검증은 기존 거절 경계를 유지한다. VF01/VF02(VQ1/VQ2)는 source inspection만 하며 시각 pass로 세지 않는다. 종합점수 없음.
