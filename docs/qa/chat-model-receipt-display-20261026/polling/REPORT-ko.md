# CQ-R01 polling 모델 표시 후속 수정

2026-10-26 UTC · 기능팀 수정·검증 완료, 이 수정본의 독립 재검증은 별도.

## 원인과 최소 변경

[독립 보고서](../../independent-chat-model-receipt-recheck-20261026/REPORT-ko.md)의 두 반례를 수정 전에 그대로 실행했다. 모션이 없는 작품에서 GPT→Grok와 GPT→미선택 응답이 도착해도 chat turn/connection/receipt가 같아서 `state=fresh`와 표시 갱신을 건너뛰었다. 3회 poll 뒤에도 client rev3/GPT가 남았다. 승인·모델 라우팅 실패가 아니라 현재 모델 표시 정합성 P2다. 원본07 §3.1/3.2가 근거다.

제품 변경은 `index.html` 두 곳이다([diff](implementation.patch)).

1. 기존 `chatChanged`에 프로젝트 `model_settings`와 표시용 `model_catalog` 비교를 추가했다. 기존 epoch/sequence/revision/workspace/project/shot/busy/dirty guard와 같거나 다른 revision 처리 규칙은 그대로다. 기존 chat draw 경로를 사용하며 입력 textarea를 다시 만들지 않는다. 열린 모델 설정창도 다시 그리지 않는다.
2. 실제 두 탭 검증 중, 닫혀 있던 설정창의 과거 DOM 값이 재열기 때 남는 인접 표시 경로를 확인했다. **설정창을 열 때만** `drawModelSettings()`로 현재 저장 상태를 채운다. 열린 창의 미저장 선택은 polling이 건드리지 않고, 닫았다 다시 열면 최신 저장값을 보여준다. 저장 handler·승인·라우팅은 그대로다.

CSS/색/위계/모델명 매핑/영수증 사실·강조 규칙·세션 계약·backend/media 코드는 변경하지 않았다. 같은 작품 독립 세션은 사용자 결정 대기다.

## 검증 결과

|검증|결과·범위|
|---|---|
|독립 원 코드 그대로 실행|수정 전4PASS/2FAIL → 최종6PASS/0FAIL. [전](before-counterexamples.json), [후](final-counterexamples.json). 새로 고친 두 변형은 모션/영수증 없는 상태다. 독립 감사자가 최종본을 재실행했다는 뜻은 아니다.|
|신규 Store+실제 JS 회귀|`tests/test_chat_model_polling.py`의2개 unittest: 실제 Store의 선택3상태를 실제 polling/draw 함수에 전달하는 Node VM12조건 + 설정창 열기 순서1개. 12조건을 unittest 개수에 다시 더하지 않는다.|
|12조건|Grok/미선택, 같은revision catalog 표시명, 역순 응답, 낮은revision/다른workspace/다른project/다른shot/epoch/dirty/busy 거절, dirty 해제 후 최신 poll. 초안·선택범위·focus·미저장 설정과 기존 shots/turns/jobs를 보존한다.|
|관련 회귀|최종 **18/18**,1.135초. 기존 FQ01–03/F07·DM/영수증 관련 테스트 포함. [로그](final-targeted.log).|
|전체 회귀|최종 **416/416**,60.686초, 한 실행. 기존414+신규2이며 관련18/VM12/원반례6을 더하지 않는다. [로그](final-full-regression.log). 중간415 실행 로그는 최종 전체로 사용하지 않는다.|
|문법|실제 main inline script 추출 후 `node --check` 통과.|

## 실제 브라우저

정상 앱 서버를 새 합성 Store(A/B 각각 한 장면, 모션/미디어/대화/작업0)로127.0.0.1:58484에 실행했다. 실제 source-served HTML이며 document.write replay/가짜 성공 버튼/원격 공급자는 사용하지 않았다. Chrome extension/CUA,1920×1080 우선·1280×900 보조/DPR1/앱100%. 정확한 Chrome 버전은 미확인.

- 첫 탭 A 상담에 `polling 중 보존할 합성 초안`을 입력하고 마지막 글자를 Shift+Left로 선택했다. 두 번째 탭의 기존 설정 저장으로 GPT→Grok, GPT 복원→미선택을 만들었다. **첫 탭 refresh 없이** 각 라벨이 바뀌었다. 현재 영수증0·요청버튼 비활성, draft/focus/선택범위18–19/scrollY179가 그대로다. `final-browser-initial.json`, `final-grok.json`, `final-cleared.json`.
- 열린 첫 탭 설정창에 Claude를 미저장 선택한 동안 다른 탭에서 GPT를 저장했다. 상담 현재값은GPT, 열린 select는Claude를 유지했다(`final-unsaved.json`). 취소 후 설정창을 다시 열면 실제 저장된 모델을 표시했다. 미선택 재열기도 확인(`final-dialog-reopened.json`).
- B로 전환하면 A 초안이 보이지 않고 B의 미선택을 표시했다. A로 복귀하면 A 초안을 복원했다(`final-project-b.json`, `final-project-return-a.json`). **지연 응답 경쟁 자체는 VM으로 검증**, 이 브라우저 관측을 네트워크 지연 주입으로 표현하지 않는다.
- [최종 Grok1920](final-grok-1920.jpg)과 [최종 미선택1280](final-cleared-1280.jpg)을 저장하고 픽셀을 직접 열어 확인했다. 캡처 메트릭의 실제 viewport가 기준이다. 중간 `cleared-poll-1280.jpg`는 파일명과 달리1920이었으므로 최종1280 근거에서 제외했다. 최종1280은 보조 탭을 닫고 override를 적용해1280×900을 직접 확인했다.
- 최종 opener 수정 후 첫 탭을 reload하고 두 반례·미저장 선택·재열기를 다시 검증했다. 과거 중간 캡처를 최종 코드로 표시하지 않는다. 파일별 해시와 final 접두사 캡처를 [manifest](FINAL-MANIFEST.json)에 고정했다.

## 보존·종료와 한계

격리 DB의 A에서 `model_settings`만 변경됐고 B의 모든 project 필드는 동일했다. shots/ontology/승인/기존 데이터 변경 없음. 최종 jobs0/generation_jobs0/chat_turns0. [보존 비교](preservation.json). 원본 QA DB나 고객 DB는 읽거나 쓰지 않았고 새 합성 Store만 사용했다.

최종 served HTML/CSS 해시가 소스와 일치했다([기록](served-source.json)). 임시 서버 PID31610에 SIGINT를 보내 종료하고58484 listener 없음 확인. 검증 탭1489480719/1489480720/1489480722를 닫고 viewport override 해제. 전체 회귀의 임시 HTTP listener도 테스트 종료됐다. 공식 permission 경로로 localhost 실행·해시 읽기·종료를 수행했다. 외부 API/키/유료 호출/설치/배포/업로드0이며 로컬 HTTP 설정 저장은 위 합성 DB에만 발생했다.

이전414 보고서와 독립 P2 발견 기록을 덮어쓰지 않았다. 이번은 CQ-R01과 인접 재열기 표시만 수정한 결과이며 전체 디자인 점수, 실제 모델 변경 실행, 독립 세션, 실제 zoom/AT, 모든 브라우저·긴 이력 수용시험으로 확대하지 않는다. 기존 stale 영수증 의미는 관련 회귀로 보존되며 새 모션 기능이나 렌더 시험은 하지 않았다.
