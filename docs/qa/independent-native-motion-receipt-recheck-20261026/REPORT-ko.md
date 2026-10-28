# 결정적 승인 영수증 최종 독립 재검증

2026-10-26 UTC. **현재 범위 통과. 승인 사실 표시의 결정성 문제를 닫는다. 모델 원문의 설명 오류 자체가 수정됐다는 판정은 아니다.** 새 재현 가능한 중대 결함은 발견하지 않았다. 추가 범용 감사나 제품 변경은 하지 않았다.

## 고정 기준과 실제 실행

- 대상: `native-motion-20261026/RECEIPT-MANIFEST.json`, 동결 `2026-10-26T19:35:59.264127+00:00`.
- HTML SHA256 `b8074c24e39d3bc58023af60d9a1327da5806b2b93c326818178684510998739`.
- manifest의 소스 28개·신규 테스트 2개·기록된 증거 모두 해시 일치. QUALITY 대비 제품 변경은 `app.py`, `production_context.py`, `index.html`뿐이다. CSS·motion/approval/execution 서비스 해시 보존.
- 현재 소스/필요한 의존성/공개 합성 응답 증거 63개를 권한·mtime를 보존해 새 임시 snapshot으로 복사했다. `base-manifest.json`에 각 해시와 위치 기록. 기존 감사 결과는 덮어쓰지 않았다.
- **10/10 PASS**: 기존 receipt tests 7개, 독립 반례 2개, 기존 AI 승인 삽입/구 grant 거절 control 1개. 전체 410은 중복 실행하지 않았다. 실제 6응답 visible output 해시와 실 렌더 함수 replay는 기존 7개 중 한 검사에 포함된다. tool-use 3개는 본문이 비어 있으므로 설명문 6개로 세지 않는다.
- `run_offline.py`의 감사 hook은 socket connect/bind를 거절하고 지정한 두 Node VM fixture만 subprocess로 허용했다. 실제 차단 시도 0. 공유 DB/키/외부 API/브라우저/listener 접근 0. 모든 Store 쓰기는 임시 합성 DB에서만 수행했다.

## 주요 확인 결과

|계약/반례|관찰과 판정|소스|
|---|---|---|
|현재 사실의 출처|`motion_receipts`는 저장된 current-head 승인 기록을 투영한다. 모델 answer/임의 server_receipts 필드를 읽지 않는다. observed revision, true/false/null match, execution_check=not_run, 별도 납품 범위를 보존. PASS|`production_context.py:34`, `app.py:167`|
|현재 stale + 과거 true + 잘못된 모델 원문 동시 표시|실제 `drawModelChat`를 VM에서 실행. 현재 section에는 stale 거절 문장만, 과거에는 당시 true와 “현재 승인 아님”, 원문에는 검토 전/서버 사실과 다를 수 있다는 설명. 원문의 틀린 ontology 설명과 악성 HTML 문자열 모두 escaping 후 원문 보존. PASS|`index.html:379`, `:390`, `:401`|
|버전/범위/없는 현재 승인|현재 v2와 과거 v1을 분리. 현재 영수증이 없는 경우 과거 기록으로 현재 카드를 만들지 않는다. 다른 project/shot filter에서 현재·과거 영수증 모두 제외. 합성 상태와 draft/scroll 값은 렌더 전후 동일. PASS|`index.html:391`, `:392`, `:396`, `:402`|
|과거 기록의 권한 승격 없음|과거 receipt는 성공한 search tool result에서만 읽는다. 모델 원문/turn-level 임의 receipt는 현재 상태에 들어가지 않는다. receipt 자체에 실행/승인 버튼 없음. 기존 disabled chat submit 상태 보존. PASS|`index.html:392`, `:398`, `:401`|
|조회 불변/기존 실행 gate|상태·검색 projection 반복 전후 합성 DB 전체 SQL dump 동일. 잘못된 grant, 구 버전 grant, 모델 actor/scope 삽입 거절. 조회 match=true라도 font manifest 변경 시 실제 render preflight 거절, job 0. PASS|`production_context.py:18`, `:51`; 승인·실행 서비스 변경 없음|
|문서의 주장 경계|현재 보고서 첫 문장과 메인 보고서 상단, OMISSION-REGISTER 상단이 모두 표시 결정성과 모델 자유서술 품질을 분리. “모델 오류가 사라짐”이라는 주장 없음. 역사적 미흡 기록은 날짜/이전 결과로 남김. PASS|`server-receipt-ui/REPORT-ko.md:3`, `:47`; `native-motion-20261026/REPORT-ko.md:5`; `OMISSION-REGISTER.md:3`|

Python AST 대조에서 `app.py`는 `Store.state`만 바뀌었고, `production_context.py`는 `read` 수정·`motion_receipts` 추가뿐이다. 기존 `motion_context`, `Store.mutate` 및 승인/렌더 경로는 그대로다. `end-check.json`의 함수 비교와 종료 해시 확인을 참조한다.

## 저장된 화면 증거 대조

manifest와 해시가 일치하는 `receipt-1920.jpg`, `receipt-1280.jpg`, `stale-and-history-1920.jpg`의 픽셀을 직접 열어 확인했다. 현재 사실이 원문 카드보다 먼저 나오고, “모델 설명 · 검토 전” 및 “과거 조회 영수증 · 현재 승인 아님”이 분리돼 있다. stale 화면은 현재 거절과 과거 일치를 동시에 보여준다. 최종 출력·납품 승인을 포함하지 않는다는 범위 설명도 실제 화면에 있다.

이것은 **primary가 저장한 Chrome 표본의 독립 열람**이다. 독립 브라우저 상호작용 재실행은 아니다. 1920×1080/1280×900, DPR1, 앱100%, 초안/포커스/scroll/reopen 기록은 `browser-checks.json`에 있으며 browser version은 미확인, 실제 browser zoom은 미실행이다. VM의 draft/scroll 보존 결과를 실제 키보드·레이아웃·접근성 검증으로 확대하지 않는다.

## 종료 판단과 한계

NM-Q01은 **서버 승인 사실을 사용자에게 신뢰할 수 있게 표시하는 계약** 범위에서 닫을 수 있다. 모델 원문 자체의 일반 정확성은 여전히 보장하지 않으며, 해당 문장은 삭제·교정되지 않고 별도 검토 영역에 보존된다. NM-Q02의 기존 timeline diff/실제 표본 결과는 변경하지 않았다.

새 모델 호출, 새 영상 생성, 전 엔진·스크린리더·zoom, 모든 장기 polling 조합은 이번 검증 대상이 아니다. 이미 보고된 410개 전체 통과를 이번 독립 실행 결과로 다시 주장하지 않는다. 새 비용/예약 0이며 기존 usage 누적 $0.0381186, 보수 기록 $0.038135, 실청구 미확인 상태를 유지한다. 원장/고객 DB는 열지 않았다.

검토 시작·종료 해시와 검증 결과: [base-manifest](base-manifest.json), [end-check](end-check.json), [실행 결과](offline-tests.json), [개별 로그](offline-tests.log), [독립 Node 반례](independent_render.cjs), [재현 runner](run_offline.py).
