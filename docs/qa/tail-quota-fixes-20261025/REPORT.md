# R01/R02 수정 및 재검증

2026-10-25. 독립 재검증 자료는 변경하지 않았다. 실제 공급자 호출, 키 조회, 기존 결과 재접근, 서버 재시작은 수행하지 않았다.

## R01: 승인된 타임라인 말미 보존

수정 전 정상 Store 승인→렌더 경로에서 0.131초×30컷(3.930초)이 94프레임(3.916667초)으로 내려갔다. 마지막 자막 3.920–3.930초와 3.925초 클릭음이 잘려도 completed가 됐다. `before-media.log`와 `media/store-tail-loss.mp4`에 재현했다.

`editing.py:12`의 내부 컷 경계는 누적 시간의 가장 가까운 프레임으로 유지하고 최종 경계만 올림한다. 마지막 영상 프레임은 필요한 만큼 유지한다. 음원·자막의 원래 타임스탬프는 변경하지 않는다. 내부 경계 오차는 반 프레임 이내이고 최종 길이는 요청보다 한 프레임 미만 길어질 수 있다. 이는 이전 F04 보고서의 최종 경계 반 프레임 정책을 대체한다.

`renderer.py:13`은 비디오 프레임 시간 검증 외에 음원 스트림이 요청 구간 말미까지 존재하는지 검사하고, 실제 출력에서 SRT를 추출하여 승인된 자막의 내용·시작·종료와 대조한다. 불일치가 있으면 completed로 처리하지 않는다.

수정 후 동일 Store 경로의 실제 출력은 95프레임, 3.958333초, 640×360, 24fps, 48kHz이다. 마지막 한국어 자막은 정확히 3.920–3.930초로 남았고, 3.920–3.940초 PCM의 peak는 20054로 마지막 클릭이 확인됐다. 결과 SHA256은 `26f5fd251fefe1c9292568add6a61cc50002da4c1efedf8f84c6a372aad2cac6`이다.

증거: `store-media-after.json`, `after-media.log`, `tail-audio-peak.json`, `media/store-tail-preserved.mp4`, `media/store-tail-preserved-manifest.json`. `tests/test_media_tail.py`는 이 실제 출력 경로를 재실행하며, 자막 기대값을 의도적으로 틀리게 주면 검증이 거절되는 것도 확인한다. 음질 전체나 모든 입력 코덱의 동등성을 입증한 시험은 아니다.

## R02: 확실히 미전송된 작업의 호출 한도 복구

수정 전 권리/게이트 변경으로 제출 전 차단되어 예약금이 반환돼도 작업 개수가 남아 명시적인 새 준비가 불가능했다. `before-quota.log`에서 외부 submit 0회와 차단을 재현했다.

`generation_queue.py:86`의 `consumes_call_quota`는 명시적인 verified_unsubmitted 표시, 제출 시작·receipt·result·확정 비용 없음, 취소된 예약 및 실제 금액 없음이 모두 확인된 경우에만 호출 한도에서 제외한다. `app.py:437`이 이 판정을 사용한다. legacy/unknown/실제 제출 작업은 보수적으로 한도를 계속 점유한다. 기존 작업을 재전송하지 않으며 사용자의 새 준비가 필요하다.

수정 후 old job은 submission_blocked로 유지되고 이전 submit은 0회다. 새 명시적 준비는 가능하며 fake provider에 정확히 1회 제출된다. 제출 결과가 불명확한 경우에는 uncertain 예약과 호출 한도가 유지된다. 증거: `after-quota.log`, `quota_after.py`, `tests/test_submission_authority.py`의 두 추가 회귀.

## 검증 범위와 남은 차단

- 허용된 전체 비HTTP 회귀: **156개 통과**, 13.997초 (`regression-non-http.log`). 테스트 개수는 요구사항 완료율이 아니다.
- 마지막 추가 음원/자막 부정 검증 포함 targeted test: **1개 통과**, 2.445초. 이후 production code 변경 없음.
- 현재 source SHA는 `final-code-hashes.json`에 기록했다.
- HTTP listener가 필요한 17개는 실행 제외. 앞선 격리 `127.0.0.1:0` bind가 `PermissionError: Operation not permitted`로 거절된 이후 재시도·새 포트·서버 재시작을 하지 않았다. 17건 각각의 거절을 관측했다는 뜻이 아니다.
- 기존 8773 서버는 이 수정 전 로드된 backend다. 최신 backend의 HTTP/UI 검증은 미실행이다. 모델 설정 요약/대화상자 소스 수정도 실제 최신 화면 검증을 완료했다고 표시하지 않는다.
- live Kling 토큰 발급 403, 실제 비용 미확인 및 결과 미수집 상태는 이번 로컬 수정으로 해결됐다고 주장하지 않는다. 실제 사용자 데이터·비용 원장은 변경하지 않았다.
