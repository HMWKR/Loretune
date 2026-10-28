# CQ-R01 최종 독립 재검증

2026-10-26 UTC. **PASS — CQ-R01을 검사 범위에서 닫는다.** 원래 두 실패가 고쳐졌고 늦은 polling/작품 전환/미저장 설정 보호가 유지된다. 전체 플랫폼 완료나 디자인 점수 판정이 아니다.

## 고정 소스와 보존

`polling/FINAL-MANIFEST.json` 동결 `2026-10-26T20:48:43.131965+00:00`, HTML SHA256 `4e96344612858c553cb47ec6c7561524016d384c77b61aa655eb2b9a72851e91`. source/artifact 해시가 시작·종료 모두 일치했다. 별도 임시 snapshot에서만 검사했다.

실제 제품 diff는 `index.html:619`의 model_settings/catalog 비교 추가, `:589`의 정상 설정 opener에서 최신값을 채운 뒤 열기 두 곳이다. `:617`의 epoch/sequence/revision/workspace/project/shot/busy/dirty guard와 `:590`의 저장 handler는 이전과 동일하다. CSS·backend/media 9개 해시도 이전 manifest와 같다. 승인·모델 해석·라우팅 서비스를 수정하지 않았다.

## 독립 실행 결과

이전 독립 감사의 `probe.cjs`와 `synthetic-probe-input.json`을 그대로 복사했다. probe 해시 동일성을 기록하고 새 HTML의 실제 draw/polling 함수만 로드했다. 전 결과를 덮어쓰지 않았다.

|원래 반례|이전|현재 실제 관측|
|---|---|---|
|모션 없는 작품 GPT→Grok|서버 rev4/client rev3, GPT 유지|서버/client rev4 일치, `Grok 4.7 · 작품 기본값 · 다음 요청 기준`; 초안 보존|
|모션 없는 작품 GPT→미선택|서버 rev5/client rev3, GPT 유지|서버/client rev5 일치, `미선택 · 모델 설정에서 선택하세요.`; 초안 보존|

원래 스크립트는 **6 PASS/0 FAIL**이다. 현재/과거 모델 구분, 없는/다른 역할 모델, 텍스트 안전 표시, stale/past 분리 control도 그대로 통과했다. [전 독립 결과](../independent-chat-model-receipt-recheck-20261026/independent-probe.json), [후 독립 결과](original-counterexamples-after.json).

추가로 신규 `test_chat_model_polling.py`의 실제 단언을 읽은 뒤 **2/2 unittest PASS**. 포함된 Node 12조건은 Grok/미선택, 같은 revision catalog 변경, 역순 응답, 낮은 revision·다른 workspace·project·shot·epoch·dirty·busy 거절, dirty 해제 후 갱신을 확인한다. 입력값·선택범위·focus·기존 shots/turns/jobs·미저장 select 값 보존을 단언하며, polling 중 `drawModelSettings` 호출 시 실패하도록 구성돼 있다. 정상 opener는 `drawModelSettings → showModal` 순서를 확인한다.

12조건 출력은 원래 합성 입력으로 한 번 더 캡처해 [guard-observations.json](guard-observations.json)에 남겼다. 이는 위 unittest와 겹치는 증거이며 테스트 수에 더하지 않는다. 전체416/관련18은 primary 보고로 남기고 재실행하지 않았다.

## 화면 증거와 한계

manifest의 `final-grok-1920.jpg`와 `final-cleared-1280.jpg` 픽셀을 직접 열어 확인했다. 각각 Grok와 미선택, 보존된 합성 초안/선택 글자 및 비활성 요청 상태가 보인다. final JSON에는 열린 설정창 Claude 미저장 선택 유지, 재열기 최신 저장값, 다른 작품 미선택/초안 분리와 원작품 복원 기록이 있다. 잘못 명명된 중간 `cleared-poll-1280.jpg`는 최종 근거로 사용하지 않았다.

이것은 primary가 저장한 Chrome 표본의 독립 대조다. 이번 독립 브라우저 조작/두 탭 재실행은 없으며, 늦은 응답의 증거는 실제 JS를 실행한 VM fake fetch다. 픽셀·모의 DOM 검사를 전 엔진/AT/zoom 검증으로 확대하지 않는다.

제품 수정·canonical/shared DB·키·외부 API·HTTP·listener·설치·업로드 0. 신규 unittest의 Store는 임시 합성 DB만 사용했다. 독립 세션은 변경하지 않았다. 추가 결함이나 범위 확대 없이 이 재검증을 종료한다.

[고정 목록](base-manifest.json) · [종료 확인](end-check.json) · [결과 요약](result.json) · [검사 로그](targeted-tests.log) · [재현 runner](run_offline.py)
