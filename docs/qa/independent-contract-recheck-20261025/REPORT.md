# 수정 독립 재검증 — 2026-10-25

**원래 F01–F04는 새 스냅샷에서 모두 기대값을 충족했다. 다만 전체 수정 완료 판정은 보류한다.** 인접 시험에서 끝 시간이 아래로 반올림될 때 승인된 자막/음원이 유실돼도 렌더가 completed가 되는 R01을 확인했다. 미전송 예약 반환 후 새 실행을 막는 R02 복구 제약도 확인했다.

## 판정 요약

| 범위 | 결과 | 증거 |
|---|---|---|
| 원래 네 반례 | **4/4 수정 확인** | recheck_original.py, before-evidence.json, after-evidence.json |
| 독립 인접 검사 | **13 pass / 3 fail 관측** | adjacent.py, adjacent-results.json; fail 2개는 같은 R01(자막/음원), 1개는 R02 |
| 정상 Store 경로 말미 재현 | **R01 재현** | store_media.py, store-media-evidence.json, media/store-tail-loss.mp4 |
| 선택한 비HTTP 회귀 | **73 통과 / 실패0 / 오류0** | run_controls.py, controls.log |
| 개발자가 제공한 미디어 | 길이3.916667초, 자막3.200–3.880 보존 | developer-media-inspection.json |
| 서버/UI/실공급자 | **미검증** | 실행·재시작·listener bind·키조회·외부API 모두 하지 않음 |

개발자의 137개 회귀 통과 보고를 이번 독립 실행 수로 사용하지 않았다. 이전 거절된 listener는 다른 포트/서버 방식으로도 시도하지 않았다. 비HTTP runner에서 connect뿐 아니라 bind도 금지했다.

## 1. 새 발견 R01 — Medium: 마지막 자막·음원이 잘려도 완료 및 검증 성공

**관측은 현재 snapshot의 정상 Store mutation→승인→render_job→process_next 경로다.** HTTP/UI 시험이 아니며, 함수에만 비정상 데이터를 넣어 만든 결과도 아니다.

- 입력: 합성 정지영상 한 샷을 0.131초씩 30컷 사용. 요청 총길이3.930초. 한국어자막 `끝 자막`은3.920–3.930초, 합성 click은3.925초. 시작 자막과0.25초/1.25초 click도 함께 둠.
- 기대: 승인된 말미 자막/음원을 보존하거나, 양자화로 사용할 수 없는 구간임을 저장/승인 전에 명시적으로 검토·거부. 해당 내용을 조용히 버리고 완료로 표시하지 않음.
- 실제: cumulative nearest 정책은 끝을94frame=3.916667초로 단축. mux의 공통 `-t` 때문에 마지막 자막이 통째로 사라지고 마지막 click peak=0. 첫 자막과 앞쪽 click은 보존된다.
- **Store job은 completed, verify_output 성공. export manifest에는 소실된 마지막 자막의3.920–3.930초가 그대로 남아있다.** 출력 실물과 승인 제작 기록이 불일치한다.
- 파일 위치(snapshot): `editing.py:12` frame_timing, `renderer.py:56` total 선택, `renderer.py:76` 공통 -t, `renderer.py:24–28` 출력 길이/트랙 존재만 검증.
- 관련 계약: FR-056/057/067/069, MS-AT28 원곡/타임코드 보존. 이전 F04의3.900초 사례가 통과해도 일반 timebase/매체 보존 완료는 아니다.
- 최소 제안: 마지막 경계는 승인된 audio/caption end를 포함하는 정책(예: 전체 끝 ceiling/pad)으로 구성하거나, 더 짧아지는 구간을 명시적인 편집 변경으로 승인받는다. 렌더 후 자막 cue 내용/시각과 오디오 유효 구간을 확인한다. 단순 tolerance 확대로 숨길 문제가 아니다.
- 영향 범위: 최대 수십 ms 미만의 끝부분이지만 짧은 말미 cue 전체가 사라질 수 있다. 원곡 전반 드리프트나 모든 자막 손실로 확대해 해석하지 않는다.

실물: `media/store-tail-loss.mp4`, SHA256 `ac501a206230f43ba8827a45ce8e868e825bc6057b37eab5d5ed8638372cc89f`.

원래 양의 반올림 사례(30×0.130초)는3.916667초로 출력되고3.880–3.890초 끝 자막이 남는다. 두 출력의 앞쪽 click onset은 각각0.250041667초와1.250041667초로, 원본과 약0.042ms 차이다. 문제는 누적 동기 오차가 아니라 아래로 반올림한 **끝 경계에서의 유실**이다.

## 2. R02 — 복구 제약 확인: 미전송 예약 반환과 승인 한도 복구가 불일치

- 정상 synthetic gate로 등록한 뒤 gate를 철회하고 worker 실행. 제출0, submission_blocked, reservation cancelled/released 확인.
- 동일한 서버 승인 gate를 복구한 뒤 **새 preparation을 명시적으로 작성**해 실행 요청. 기존 blocked action replay가 아니다.
- 기대(가설): 외부 호출을 한 번도 하지 않았으므로 같은 승인 대상의 새 준비를 실행하거나, 재승인이 필요한 이유와 소진 기준을 명확히 표시.
- 실제: `승인된 테스트 호출/비용 상한입니다. 추가 호출하지 않습니다.` 오류. 실제 submit은0이고 예산 예약은 이미 반환됐음.
- 원인: snapshot/app.py:436–439가 모든 generation_jobs의 건수와 견적 금액을 상태와 무관하게 합산. 미전송 blocked/cancelled 기록도 한도 소진으로 계산.
- 판정: **과소 허용/복구 UX 제약이며 지출 초과·과금 유실·권한 우회가 아니다.** 기존 narrow live gate의 maximum_calls를 'admission 시도 수'로 정의한 의도라면 현재 동작은 보수적 정책일 수 있다. 보고된 “미전송 예약해제”를 “허용 실행 기회도 복구됨”으로 표현해서는 안 된다.
- 제안: 승인 범위별로 제출 시작/접수 불명/실제 시도와 단순 admission 실패를 구분해 한도를 계산하거나, 새 승인 필요 상태를 명시한다. 미확정/기접수 작업을 제외해서 한도를 되돌려서는 안 된다.

이 항목은 정책 확정이 필요한 계약/복구 문제로 분리하며 새로운 보안 결함으로 주장하지 않는다. 자동 재실행을 허용하라는 의미도 아니다.

## 3. 원래 네 결함의 before/after

| ID | 이전 독립 관측 | 이번 독립 관측 | 판정 |
|---|---|---|---|
| F01 | 권리 철회 후 submit1, accepted | submit0, submission_blocked, 미전송 reservation released | 원래 반례 수정 확인 |
| F02 | cancel 실패가 cancelled_result를 cancel_sent/result null로 덮음 | cancelled_result와 URL 보존, revision7 | 원래 interleaving 수정 확인 |
| F03 | 관계 target 변경인데 impact=[] | relation 영향1건, context에 relations/dependencies 보존 | 직접 관계 범위 수정 확인 |
| F04 | 30×0.130초 요청3.900→3.750, 검증 실패 | 3.916667, 오차+0.016667, 검증 성공 | 해당 반례 수정 확인; R01 별도 |

before는 09:32:56 UTC 이전 감사 snapshot의 evidence 사본이며 이번에 옛 소스 전체를 재실행했다고 주장하지 않는다. after는 09:51:39 UTC 새 snapshot에서 독립 재현 스크립트를 실행한 결과다. recheck_original.py는 이전 독립 재현의 fixture/사건 순서를 유지하고 수정 후 기대 assertion만 바꿨다. 개발자의 before/after 로그를 그대로 검증 근거로 대체하지 않았다.

F02는 결정적 함수 interleaving이며 현재 단일 worker UI 도달성을 추가 입증한 것은 아니다. F03은 직접 outgoing 관계와 target 의존성 기준이며 전이적 그래프 추론/실제 AI 추출 전체 검증이 아니다.

## 4. 요청한 인접 경계 결과

**예산/철회/재개**

- gate 철회→미제출 차단: released 기록, actual=null. 환불이라고 표시/처리하지 않음.
- gate를 원래 값으로 복구: 기존 submission_blocked job은 submit0으로 유지. 자동 재시작 없음.
- fake submit 후 receipt timeout→reconciliation_required: 권리/gate 철회 및 recover 이후에도 uncertain 700000 micro-USD 예약 유지, release 이벤트 없음, submit1 유지.
- accepted 후 권리/gate 철회: 기존 reserved 유지, release 이벤트 없음. 추가 submit 없음.
- 제출 전 cancel: reservation released, refund 이벤트 없음, submit0.
- legacy prepared에서 신규 submission_binding 필드가 없는 경우: Store worker가 fail closed, submit0. 실제 DB migration이나 서버 재시작을 수행한 것은 아니며 synthetic persisted row의 구형 형상을 재현했다.
- 늦은 실제 청구/환불은 이번 실행에서 공급자 조회하지 않았다. 선택한 기존 ledger fake 회귀의 late settlement/disputed 정책은 통과했다.

**관계와 이력**

- 같은 relation의 provenance 변경이 impact를 발생시킴.
- relation 삭제가 impact를 발생시키고 revision1 원본 graph와 이미 bound된 context가 그대로 유지됨.
- revision1로 restore 시 revision4를 새로 만들고 내용이 같은 관계에 불필요한 impact 없음.
- 무관한 개체의 description 변경은 bound shot을 무효화하지 않음.

**프레임·미디어**

- 독립 seeded 500개 sequence, 총7663개 cumulative boundary를 검사. 최대 경계 오차0.020666667초 ≤1/48초, frame 수 최소3. frame quantization 오차가 컷 수만큼 누적되지 않음.
- 30×0.130초: 원래 길이 반례 수정, 음원 초기 click 및 한국어 끝 자막 보존.
- 30×0.131초: 길이 오차 자체는 bounded이나 R01처럼 말미 데이터 유실. frame 오차 한도 통과를 media preservation 통과로 환산하지 않음.
- 개발자의 `fractional-30cuts-audio-caption.mp4`를 별도 ffprobe/SRT 추출로 읽음.3.916667초 및3.200–3.880초 Unicode cue 확인. 이 사례는 아래로 반올림되는 말미 유실 경계를 포함하지 않는다.

## 5. 버전, 범위, 미검증

새 snapshot 시각: **2026-10-25T09:51:39.854848+00:00**. `snapshot-manifest.json`에 각 path/mtime_ns/bytes/SHA256 기록. 모든 import는 이 snapshot만 사용했다. `source-drift.json` 시점 app.py에는 action_execution import/initialize 추가가 생겼으며 이번 검증 대상 snapshot에는 그 변경이 없다. 따라서 개발 중 최신 통합 전체에 대한 완료 선언이 아니다.

보고서·증거·synthetic fixture·snapshot은 새 `independent-contract-recheck-20261025` 폴더에만 작성. 이전 감사 증거/제품 소스/사용자 DB/키/인증파일은 수정하거나 열지 않았다. 외부 API, 유료 호출, 실제/임시 HTTP listener, 서버 재시작은0회.

재현:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-recheck-20261025/recheck_original.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-recheck-20261025/adjacent.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-recheck-20261025/store_media.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/independent-contract-recheck-20261025/run_controls.py
```

adjacent.py의 fail은 관측 보고값이며 프로그램 실행 오류가 아니다. store_media.py는 R01의 현재 결함을 assert하는 characterization이다.

**준비 수준:** local demo는 양자화 끝손실 경계를 제한한 조건부 유지. limited pilot은 R01과 기존 실공급자/권한/상태 통합의 남은 범위 때문에 보류. full spec은 미충족이며 신규38AT 완료로 환산하지 않는다. 새 서버/UI는 실행하지 않아 미검증이며, 이전 listener 거부를 재시도하지 않았으므로 이번 턴에 새 denied/pending 작업은 없다.
