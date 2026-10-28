# 저장 상태 안내·출처 펼침 표시 최종 수정

이번 변경은 독립 시각 감사가 지정한 두 결함만 대상으로 한다. 새로운 디자인 점수나 90점 달성을 선언하지 않는다. 이전 여섯 상태의 검증 중 변경 없는 제작·비교·출력 동작의 근거는 유지한다.

## Library 전달 완료

| 이미지 | 확인된 Library ID |
|---|---|
| desktop-confirmed-save-rejection.png | libfile_36d9ad6fe9ec819195eab02fbf40b9af |
| mobile-save-outcome-unknown.png | libfile_4231ff16cec881918c40e03b37962a93 |
| desktop-disclosure-open.png | libfile_0c0cf20cf5a881919a6eb3f93c810ea2 |
| mobile-disclosure-open.png | libfile_31e8f49d16b08191a64abf8dfd19425b |
| mobile-disclosure-closed.png | libfile_8ff38e4ced54819198f3eb15bd67fee5 |
| mobile-confirmed-save-rejection.png | libfile_7cbc249650a8819188377f5d83e52bd8 |
| desktop-save-outcome-unknown.png | libfile_e0c62ca3b53c8191bc32b89daed0a664 |
| mobile-committed-refresh-failure.png | libfile_cd81ec0540e081919468272ea1c16dd7 |

각 파일의 저장 결과·버전·로컬 연결 메타데이터는 `library-upload-result.json` 및 `mobile-committed-refresh-failure-library.json`에 보존했다. 모든 이미지는 실제 localhost 화면 캡처이며 저장 오류 화면에는 합성 응답 대역이라는 표시가 있다. 이미지를 열어 픽셀을 직접 확인했다.

## 실제 변경

- `index.html`: 요청 결과를 서버의 명시적 거절, 응답 미확정, 저장 완료, 저장 완료 후 화면 갱신 실패로 구분한다. 4xx JSON의 명시적 오류만 확인된 거절로 처리하고, 네트워크·JSON 유실·5xx는 미확정 요청을 유지한다.
- 검토 폼 옆 안내가 무슨 일이 있었는지, 입력 보존 여부, 실제 버튼 이름을 설명한다. 403/409는 새로고침하여 저장된 검토와 보존된 초안을 확인하도록 별도 안내한다. 상단은 접힌 짧은 상태만 제공한다.
- 미확정 시 새 검토 제출은 비활성화하고 해당 폼의 `기존 저장 확인`으로 기존 요청 ID를 조회한다. 404도 서버 계약상 unknown이므로 자동 재제출하지 않는다. 다른 장면으로 이동하면 전역 복구 버튼으로 접근할 수 있다. 현재 폼에서는 중복 복구 버튼을 숨긴다.
- 저장 완료 조회 시 제출 당시 초안 revision만 제거한다. 조회를 기다리는 동안 작성한 새 초안이나 다른 장면·Take의 초안은 제거하지 않는다. F07의 기존 revision 보호 컨트롤러는 보존했다.
- `출처·사용권`은 native details/summary에 동일한 작은 chevron, 열린 상태 회전, focus-visible을 사용한다. 모바일 flex에서도 표시된다. 별도 카드나 custom keyboard 동작을 추가하지 않았다.
- 추가 회귀: `tests/test_save_feedback.py`, `tests/save_feedback.mjs`.

## 검증

| 시나리오 | 실제 결과 | 근거 종류 |
|---|---|---|
| 400/403 명시적 거절 | 미확정 요청 해제, 초안 보존, 실제 저장 버튼을 이름으로 안내 | JS 대역 + 실제 브라우저 400 |
| network/503/JSON 응답 유실 | unknown, 요청 ID 보존, 실패로 단정하지 않음 | JS 대역; 브라우저 network 대역 |
| 저장 성공 후 refresh 실패 | 저장 완료 상태 보존, 새로고침 안내 | JS 대역 |
| 기존 요청 조회404 | unknown 유지, POST 재발행0 | JS 대역 + 실제 브라우저 대역 |
| 기존 요청 조회committed | 해당 제출 revision만 정리, 새 초안 유지 | JS 대역 + 실제 브라우저 대역 |
| 장면 전환 | 다른 장면에 오류·초안 누출 없음; 돌아오면 보존된 입력 표시 | 실제 브라우저 |
| 저장 중 새 입력·컨텍스트 | 기존 F07 및 scoped draft 회귀 통과 | 9 review / 16 comment controls + 브라우저 |
| 펼침 표시 | desktop/mobile chevron, Enter 펼침, Space 접힘, focus 유지 | 실제 브라우저 |
| 390px reflow | 가로 overflow 없음; 저장/복구 버튼·보존 입력 확인 | 실제 브라우저/저장 이미지 |
| 회귀 | **327/327 통과, 42.909초** | `full-regression.log` |
| 정적 검사 | Python AST111개, inline JS4개 통과 | `static.json` |

신규 node 시험은 13개 결과·복구·표시 검사를 한 unittest에서 실행한다. 단순 unittest 개수를 기능 완성도로 환산하지 않는다. 브라우저 대역은 `/api/action`을 전송 전에 가로채며, 이 QA의 실제 서버 변경 POST0 / 외부 공급자 호출0 / 키 읽기0이다. 200 committed 조회도 합성 대역이며 실제 서버 저장 성공 증거로 사용하지 않는다. 테스트가 만든 초안과 대역은 제거하고 검증 공간21·22·23은 종료했다. 사용자 공간은 조작하지 않았다.

## 동결 실행 버전

- URL: http://127.0.0.1:8773
- source / served HTML SHA256: `a59b8c494770d23000973c1c1b702c39d8fcb955e38ed04f045ccc4c94373c1b`
- app.py SHA256(변경 없음): `c13df5375c1f2e4171a3f9b2abe53868d163536e5cce621de458d06c7295dfe7`
- 기존 유휴 검증 서버를 승인된 정상 경로로 재시작했다. 실행 데이터 경로는 `/tmp/loretune-ms-qa-20261025`, provider 활성화 없음.
- `frozen-runtime.json`, `browser-final-evidence.json`, `integration.patch`, `before/index.html` 참조.

## 캡처 리비전 구분

첫 7개 캡처는 HTML `a29802f327b74e863562302fc4908935877c979e880865d4507ea836ab14a73a`에서 촬영했다. 이후 기존 요청의 committed 확인 직후 refresh만 실패할 때 unknown으로 되돌아가던 catch 분기만 수정했다. 앞선 캡처의 문구/레이아웃/경로는 변경하지 않았다. 8번째 `mobile-committed-refresh-failure.png`는 최종 `a59b8c49…94373c1b`에서 실제 대역으로 검증·캡처했고, 새 초안과 committed 상태 보존을 확인했다. 이 서버는 HTML을 매 요청 디스크에서 읽으므로 마지막 HTML-only 수정은 추가 프로세스 변경 없이 제공되며 최종 GET 바이트 일치를 검증했다. backend는 정상 재시작한 동일 코드이다.

## 한계·남은 평가

이번 두 결함의 구현/로컬 검증/전달 차단 없음. 독립 동일 기준 시각 재평가는 부모가 수행한다. 실제 장애를 일으키거나 실사용자·screen reader·200/400% zoom을 새로 검증하지 않았다. 실제 외부 모델 권한·결과 수신의 기존 차단은 그대로이며 이번 화면 QA와 무관하다. Ego Lite 업데이트 알림은 관찰했지만 업그레이드는 하지 않았다.
