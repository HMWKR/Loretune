# R01/R02 최종 독립 재검증 — 2026-10-25

**R01/R02의 원래 반례는 모두 통과했고 F01–F04 control도 통과했다. 이번 고정 스냅샷에서 해당 수정 범위의 새 correctness blocker는 관측하지 않았다.** 서버/UI/실공급자 및 개발 중 전체 action/ledger 기능의 완료를 뜻하지 않는다.

## 핵심 before/after

| 항목 | 이전 독립 관측 | 새 독립 관측 | 판정 |
|---|---|---|---|
| R01 말미 자막 | 30×0.131초, 승인3.920–3.930초 cue가 사라졌으나 completed | 끝 자막 내용과3.920–3.930초 모두 보존, Store job completed, manifest 일치 | 통과 |
| R01 말미 음원 |3.925초 click peak0 | peak20054, 앞쪽 click도 시각 유지 | 통과 |
| R02 반환된 실행 한도 | submit0인데 새 준비가 호출/비용 상한으로 거부 | 기존 미전송 reservation released 유지, 새 준비 admit 및 fake submit **1회** | 통과 |
| F01 권리 철회 | submit1 | submit0 / submission_blocked | 통과 유지 |
| F02 취소 경합 | cancel_sent/result null로 회귀 | cancelled_result/URL 보존 | 통과 유지 |
| F03 관계 변경 | impact=[] | 관계 영향 감지 및 관계/dependency snapshot 보존 | 통과 유지 |
| F04 30×0.130초 |3.750초, 검증 실패 |3.916667초, 검증 성공 | 통과 유지 |

R01의3.930초 요청은 최종 끝을 ceiling한 **3.958333초(95frame)**로 출력된다. 요청 대비+0.028333초이며 마지막 boundary는1frame 미만 확장, 내부 boundary는 nearest 반올림으로 최대0.5frame 오차라는 서로 다른 정책을 적용한다. 예전 “모든 경계 최대0.5frame” 조건으로 평가하지 않았다. 승인 음원/자막을 time-stretch하거나 cue 시간을 바꾼 것은 아니다.

## 실행 결과

- 독립 원래 반례/control **4/4 통과**: `recheck_original.py`, `after-evidence.json`.
- 인접 검사 **16/16 통과**: `adjacent.py`, `adjacent-results.json`, `adjacent.log`.
- 추가 방어조건 **12/12 통과**: `guards.py`, `guard-results.json`.
- 선택한 비HTTP 기존 회귀 **75개 통과, 실패0, 오류0**: `run_controls.py`, `controls.log`. 개발자의 전체 suite 수를 독립 실행 수로 사용하지 않음.
- 정상 Store 승인→render_job→process_next 경로로 R01 재검증: `store_media.py`, `store-media-evidence.json`.

숫자는 서로 중복되는 동작을 포함하므로 합쳐 전체 기능 수용률로 계산하지 않는다. 신규38AT 전체 통과 선언도 아니다.

## 예산/호출 한도 경계

다음은 모두 synthetic temporary DB와 fake adapter에서 실행했다.

1. 명시적 `verified_unsubmitted=True`, 미전송 terminal state, submission 시작/receipt/result/cost확정 증거 없음, reservation cancelled·actual=null·refunded0일 때만 호출 한도가 반환된다.
2. grant 철회→미제출 차단→같은 grant 복구만으로 기존 blocked job을 재실행하지 않는다. 별도의 **새 preparation 요청**은 admit되고 한 번 제출된다.
3. legacy(미전송 증명 없음), submitting 시작 이력, receipt 존재, result 존재, cost확정 또는 unknown state이면 quota를 유지한다. 일부 조합은 검증 함수의 fail-closed synthetic row 검사이며 외부 API 공격/정상 고객 상태로 주장하지 않는다.
4. 미전송 예약 release 후 synthetic late settlement를 기록하면 quota 점유가 복귀한다. 미전송 증명만 보고 과금 기록을 무시하지 않는다.
5. fake submit 응답 유실 뒤 새 준비 요청은 거부된다. submit1 유지, reservation **uncertain/700000 micro-USD**, quota 점유 유지. 권리/gate 철회 및 recover가 불명 비용을 해제하지 않는다.
6. accepted 뒤 철회는 기존 reserved 유지. 제출 전 cancel은 released이며 refund로 기록하지 않는다.

구현 근거(snapshot): generation_queue.py `dispatch`, `consumes_call_quota`; app.py `start_generation`. 실제 공급자 사용량·청구 내역은 조회하지 않았다.

## 관계·미디어 경계

- 관계 provenance 변경, 관계 삭제가 impact를 발생시킴. revision1 graph와 기존 bound context 보존.
- 과거 관계 restore는 새 revision4로 기록되고 내용이 같으면 불필요한 impact 없음. 무관한 entity 변경도 bound shot에 영향 없음.
- seeded500개 sequence/7663개 boundary 검사: 내부 boundary half-frame 이하, 마지막 boundary는 요청 끝 이상이면서1frame 미만 확장. 컷별 반올림 누적 없음.
-3.930초 영상의 끝 자막 `끝 자막`은3.920–3.930초로 SRT 추출 확인.3.925초 click peak20054.0.25초/1.25초 click onset은0.250041667초/1.250041667초로 보존.
- 승인 자막의 내용만 바꿔 검증하거나 종료시각을1ms 바꾸면 **자막 내용·시각 불일치로 거부**한다.
- 영상/자막은 유지하고 synthetic audio track만3.900초로 짧게 remux한 negative artifact는 **음원 말미 잘림으로 거부**한다.
- audio-tail 검증은 길이 경계 검사이며 waveform/원곡 동일성의 일반 증명은 아니다. 이번 click 시험이 실제 샘플 보존의 추가 근거다.

실물: `media/store-tail-preserved.mp4` 및 `media/store-tail-preserved-manifest.json`.

출력 SHA256: `26f5fd251fefe1c9292568add6a61cc50002da4c1efedf8f84c6a372aad2cac6`.

## 스냅샷과 증거 보존

- capture: **2026-10-25T10:05:24.340564+00:00**.
- 각 파일의 bytes/mtime_ns/SHA256: `snapshot-manifest.json`.
- 종료 비교: `source-drift.json`의 snapshot 대상 파일 변경 **0건**. 복사 뒤 새로 생긴 파일까지 포함한 저장소 전체 freeze라고 주장하지 않는다.
- 이전 관측 사본: `before-adjacent-results.json`, `before-store-media-evidence.json`, `before-after-evidence.json`. 이전 감사 디렉터리는 수정하지 않았다.
- 이번 코드는 모두 새 snapshot import. 개발 중 action/ledger의 원본을 직접 import/수정하지 않았다. 테스트 script·snapshot·synthetic DB·media·보고서만 새 QA 디렉터리에 생성.

재현(루트에서 순서대로):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-final-recheck-20261025/recheck_original.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-final-recheck-20261025/adjacent.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-final-recheck-20261025/store_media.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-final-recheck-20261025/guards.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-final-recheck-20261025/run_controls.py
```

## 남은 범위와 준비 수준

**요청된 여섯 반례와 검사한 인접 경계에서는 미해결 blocker 없음.** 실제 서버/UI가 새 코드를 로드하는지, live provider 파일 수집/권한/비용 대사, 범용 action/grant/ledger의 전체 계약, 신규38AT 전체 수용은 이번 확인 범위 밖이다. F02는 여전히 함수 interleaving 검증이고 다중 worker 실제 운영 검증이 아니다.

local demo의 해당 계약 수정은 수용 가능. limited pilot/full spec 준비 완료는 선언하지 않는다. 외부 API·유료호출·키조회·서버 재시작·listener bind는0회. 이전 denied bind를 재시도하지 않았으며 이번 작업에 신규 거부/보류/불명 실행 결과는 없다.
