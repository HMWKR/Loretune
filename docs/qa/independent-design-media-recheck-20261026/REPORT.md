# DM01·DM02·DM03 독립 재검증

**PASS — 원래 미디어 P2 세 건 수정 확인, 해당 이슈와 이번 좁은 검토 범위를 종료한다.** 검사 범위에서 남은 재현 결함 없음.

| 결함 | 원 반례 기준 현재 관찰 | 코드 근거 |
|---|---|---|
| DM01 metadata 전 seek | trim2초인 컷에서 로딩 중1.5초로 이동하면 재생 없이 원본3.5초로 반영. 연속seek0.5→2.25 후 metadata만 도착해도4.25초. 이후1.25로 재탐색하고 data 도착 시3.25초, paused 유지 | `studio-media.js:97–100` 최신 at 재계산 및 현재 컷/element 검사 |
| DM02 stale callback | 옛 error/waiting는 새 컷을 멈추거나 clock을 고정하지 않음. 폐기된 controller의 error가 현재 라벨/버튼을 바꾸지 않음. 옛 comparison canplay는 새 ready 쌍을 disable하지 않음 | `:71–80,92–102,124–133` dispose/serial/playEpoch/active 검사 |
| DM03 비교 진입 정지 | 비교 진입 즉시 detached Audio paused=true 및 sequence RAF0. 과거 audio 시간이 움직여도 sequence 위치 불변. 역방향 전환도 기존 compare 정지 | `:108,112,133` controller 명시 pause |

모든 독립 시나리오에서 project/Take 선택·승인·draft JSON을 전후 비교해 불변을 확인했다. 현재 유효한 영상 error는 계속 사용자에게 표시되며 정지한다. 오류 전체를 숨겨 통과한 수정이 아니다.

## 증거와 개수

- [recheck.cjs](recheck.cjs), [independent-harness.cjs](independent-harness.cjs): 이전 독립 최소 DOM fixture를 재사용한 원 반례6개 및 근접 control2개. 함수 body/조건을 바꾸지 않고 export seam만 추가했다. 이벤트 해제 후에도 저장해 둔 옛 callback을 호출해 단순 listener 제거뿐 아니라 세션 검사까지 검증했다.
- 같은 성공 조건을 [수정 전 JS](before-studio-media.js)에 실행: [7실패/1통과](before-same-contract.json). 현재 snapshot: [8/8통과](after-same-contract.json). 구현팀 보고의8실패→12통과와 다른 독립 시험 집합이다.
- [focused-tests.log](focused-tests.log): 관련 unittest **12개 통과 /0.629초**. 시간/trim/파형/불변·F07·검토초안·비교·새 async lifecycle wrapper 포함.
- 새 구현팀 lifecycle의12시나리오도 고정 snapshot에서 실제 다시 실행해 [12/12통과](implementation-controls-rerun.json)를 확인했다. 늦은 play Promise 성공/실패, 역방향 재생 전환, 정상 audio offset/caption/공통 길이 종료의 근접 회귀다. 이12개는 위 wrapper에 포함되므로 test 총계에 별도로 더하지 않는다.
- `node --check` 통과. 전체338회귀 및 구현팀 실제 브라우저 확인은 이번 독립 실행의 증거로 대신 사용하지 않았다.

## 고정본과 경계

- JS SHA256 `ae019c88ae442b129ff7d43e8a93b4b9cf1339fd00dd09d900ced142ac3a982e`
- CSS SHA256 `f6f9ebff08ba722bf05f038697671c1c299d778a72d7729e63a4d7a33c87dd58`
- HTML `846e18d44d6361cf423ba6ad568ede4280fcb22b34bee17a3eeb0a647974d839` 유지.

[snapshot.json](snapshot.json)에 파일별 hash/mtime/bytes와 캡처시각, [snapshot/](snapshot/)에 분리 소스/fixture, [finish.json](finish.json)에 종료 시 drift를 보관했다. 원 감사 자료는 변경하지 않았다.

Node VM controlled media events 검증이다. 실제 브라우저의 자연 발생 이벤트, 모든 코덱/장시간 동기, 최종 데스크톱 밀도·CSS 시각 수용 여부는 이번 범위에서 미검증이다. CSS는 전달 hash 및 기존 문자배율 정적 회귀만 확인했다.

앱 코드·서버·공유 DB 수정, 비밀/키 조회, 외부 호출, browser/listener 사용 없음. 기존 소스는 읽기만 하고 분리 snapshot에서 단위 검증했다. 추가 수정 제안·승인 요청·미해결 blocker 없음.
