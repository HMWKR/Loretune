# SPEC-MS-001 — 38개 수용항목의 현행 증거 추적

## 최신 증거 연결 · 2026-10-27 후속

아래의 416개 회귀와 ‘구현 미재개’는 당시 시점이다. 이후 대화 선택·격리와 진행 중 다음 모델 예약, 음원·자막·미리보기 일부 수정이 이뤄졌다. 예약의 격리 HTTP와 합성 응답 브라우저 표본, [435개 전체 회귀](codex-workflow-review-20261027/regression-435-20261027.log), 실제 결과와 미검증 범위는 [작업 기록](codex-workflow-review-20261027/REPORT-ko.md)을 따른다. 이 연결은 38개 원본 수용항목이나 CS01–18의 전수 통과를 뜻하지 않는다. 실제 일반 Claude 연결·실사용 업무 흐름·팀 권한·실청구·실제 AI 영상 모델 시험은 별도다.

## 2026-10-27 보충 — 원문 보존, 새 수용 통과 없음

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** [정체성·개인/팀 보충문](../design/PRODUCT-IDENTITY-AMENDMENT-20261027.md)과 [AD01–AD07/개인P·팀T·공통C 수용](../design/AETHONSAAS-ADOPTION-PROPOSAL.md)은 최신 사용자 결정의 별도 추적이다. 원본07와 등록 두사본은 그대로이고 MS-AT01–38의 입력/조건·아래 부분 검증 판정을 삭제하거나 PASS로 바꾸지 않았다.

**현재 빌드 경계:** 마지막 전체 검증은 [R416](chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json)의416/416이다. [R414](chat-model-receipt-display-20261026/FINAL-MANIFEST.json)는 현재 모델/차단 영수증 표시 표본, [독립 표시 감사](independent-chat-model-receipt-recheck-20261026/REPORT-ko.md)는 polling반례 발견, [R416 보고](chat-model-receipt-display-20261026/polling/REPORT-ko.md)는 그 수정/설정창 재열기 표본이다. R416 수정본의 독립 최종 확인은 별도다. 아래 R1/L410은 당시 근거다. 이후 [세션 부분 구현](../design/CHAT-SESSION-PLAN.md)은 중단됐고 새로운 CS/UI/전체 시험은 미완료다. 제품시험을 이번에 실행하지 않았다.

|연결|새 근거 또는 채택 설계|정확한 한계 / 계획된 수용|
|---|---|---|
|AT01/06, 원본§3.1/3.2|R414 현재 모델/미선택·긴 이름·미검증 표시, R416 다른창polling·미저장값·재열기|표시 표본이지 모델 변경 후 실제응답/종료모델 전체 동작 증거 아님. AD02/06·P04–P07·CS07/08에서 재검증|
|AT16, 원본§3.1|R416 두탭 모델표시·draft/포커스 보존|동시쓰기 CAS 전부나 팀권한 통과 아님. AD02/03·P05/T06·CS09–14|
|AT35|R414/R416 현재 stale영수증과 AI원문 분리의 표시·회귀|실제 파일미수집/fal실패 모든경로·모델자유서술 오류해소 아님. AD06·C06|
|AT13/14/19/21/29, §7/8|AD01 자료역할/고정버전/제외, AD04·05 새초안/선택의견|P02/03/08–10 계획. 현재 reference/reuse/comment 기반 존재≠새도입완료|
|AT08/15/17/18/22–25/30/32|AD02/06 독립대화·공통예산·기존요청복구|P04–P07·CS01–18 계획/WIP. 원본응답중모델변경 기본과CS08차이는 세션계획에서 명시 조정|
|AT07/09/10/16/26/27/34, §4/9/10|AD03/04/05 선택적팀권한·철회·입력/실행/채택분리|T01–T09 후속. 개인기본은 팀가입필수 아님; **조직조건 삭제/면제 아님**. 해당팀/운영범위에서 원문대로 검증|
|전체38AT, §14.1/14.3|AD07 요구→구현→증거build→미실시추적|P01–P10/T01–T09/C01–C08은 보완표이며 원본30초/12샷/교차조직/12live조합 대체 아님. AT36실수신 미검증 유지|

원본의 조직·BYOK·자동라우팅 조건은 동작이 채택됐거나 검증됐다는 의미가 아니다. 최신 제외범위와 충돌하는 부분은 요구확인 항목으로 남기며 몰래 삭제하지 않는다. 새 모델/가격/실청구·권한 시험은 이번 문서 승인 범위 밖이다. [보존/링크 검사](adoption-docs-20261027/REPORT-ko.md).

## 2026-10-26 항목별 근거 — 당시 원문·부분 판정 보존

2026-10-26 문서 후속 정합화. 기준은 [원본07](../../07_Chat_Directed_Multimodel_Production_Spec.md) §14.2의 **MS-AT01–38**이다. 원문의 입력/통과 조건은 아래에 그대로 옮겼으며 요구서를 수정하지 않았다. [누락 등록부](OMISSION-REGISTER.md)·[남은 작업](REMAINING-WORK.md)에서 사용하는 **현재 문서 추적 입구**다. 기존 등록 catalog/coverage·과거 독립 판정은 지우거나 소급 갱신하지 않는다.

이 작업은 로컬 문서·선별 코드·저장 로그의 읽기와 Markdown 작성이다. 신규 테스트/브라우저/API/DB/서버/업로드0. **코드가 존재함, 합성 시험 통과, 실제 Claude 응답, 실제 로컬 encode, 실제 외부 미디어 수신은 서로 다른 증거다.** 각 항목의 원문 전체 수용을 새로 PASS 처리하지 않았다. “부분 검증”은 아래 열거한 부분만의 증거이며 미검증을 FAIL로 바꾸지도 않는다.

## 고정 버전과 증거 읽는 법

- 원본07 및 knowledge/specification 등록 사본3개 SHA256: `962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`. catalog.source_sha256도 일치한다. 등록28FR의 연결AT를 각 항목에 표시했다.
- [R1 RECEIPT-MANIFEST](native-motion-20261026/RECEIPT-MANIFEST.json), 동결19:35:59.264127UTC. HTML `b8074c24e39d3bc58023af60d9a1327da5806b2b93c326818178684510998739`, app `baa5bad0ffd913a200203ea1dab4e1f4bfd8fced6f4472bc644809c241429bc8`. R1의source28+added_tests2 현재해시30/30일치 확인. CSS `4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`.
- **L410**=[구현팀 최종410회귀 로그](native-motion-20261026/server-receipt-ui/final-full-regression.log): 한 실행390비HTTP+20HTTP. 아래 함수별 `ok` 행 번호는 이 저장 로그에서 확인했다. 시험 소스의 현재 함수 위치도 대조했다. 이 문서 담당의 재실행이 아니며, 인용 부분시험을 별도 합산하지 않는다. R1에 개별 해시가 없는 테스트는 현재 읽은 코드와 저장 실행로그의 연결이며, 모든 과거 실행 당시 파일을 독립 snapshot 대조했다는 주장은 하지 않는다.
- **R2**=[최종 독립 receipt 재검증](independent-native-motion-receipt-recheck-20261026/REPORT-ko.md): 격리10/10·저장화면3장 열람·조회불변/기존승인gate. 새브라우저/API0, 전체410재실행 아님. NM-Q01 사용자 승인사실 표시만 닫힘. Claude 원문 오류 자체는 남는다.
- **M1**=[실제 모션/편집 후속](native-motion-20261026/FOLLOWUP-MANIFEST.json), [결과](native-motion-20261026/REPORT-ko.md), [독립 검증](independent-native-motion-followup-20261026/REPORT-ko.md): 18:36동결393회귀, 실제Claude9응답·4초96프레임/12프레임수정·3초음악/자막출력·UI표본. **Q1**=[품질 후속](native-motion-20261026/QUALITY-MANIFEST.json): 추가6응답·403회귀, 제한된설명표본. 합15응답이며12live모델조합 아님. 최신receipt 변경은 새Claude0.
- **C1**=[CC01 실제Claude 결과](cc01-context-fix-20261026/REPORT-ko.md), [독립 재검증](independent-cc01-fix-recheck-20261026/REPORT-ko.md): 별도 실제14응답·원요청보존·prompt2개→fake fal payload. **C2**=[CC02](cc02-preflight-fix-20261026/REPORT-ko.md), [독립 재검증](independent-cc02-recheck-20261026/REPORT-ko.md): 송신전byte한도/unknown복구. 닫힌반례를 재개하지 않는다.
- **L25**=[이전 실제 일반채팅 UI](claude-chat-ui-live-20261025/REPORT-ko.md): 실제Claude+합성project+로컬시험미디어. **F25**=[이전 fal creator UI 계약·격리완주](fal-creator-workflow-20261025/PRESENTATION-CONTRACT.md): staging당시 fake adapter와실제local5초출력·재시작. 역사적제한표본이며현재전체UI/실fal로재표기하지 않는다.

원본§14.1의 그룹/활동기/권리/30초음원/12샷·다른조직 dataset 전체가 아래 작은fixture마다 충족됐다고 가정하지 않는다. 1920주·1280보조·모바일보류와 같은작품 독립세션은 별도 현행 요구다. 제품 runtime no-MCP·fal 선택미디어·Runway benchmark-only 결정을 보존한다.

## 항목별 추적

### MS-AT01 · 부분 검증

- **연결 요구:** MS-FR-01. 원본§14.2 AT01.
- **원문 입력/사건:** 채팅 모델만 변경 후 메시지 전송
- **원문 통과 조건:** 다음 응답의 모델만 변경하고 이미지와 영상 기본값 유지
- **현재 구현:** 세 역할의 독립 저장·기존 snapshot 보존, runtime은 선택값과 승인된 adapter/model을 대조한다. [model_selection.py](../../model_selection.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_role_independence_preserves_existing_media_and_context` — [test_model_selection.py](../../tests/test_model_selection.py) L8; L410 L371 `ok`
  - `test_openai_and_grok_tool_results_reach_same_store` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L24; L410 L388 `ok`
- **실제 검증 범위·한계/미실시:** 세chat 선택·OpenAI/Grok tool 왕복은 fake transport다. C1 실제Claude1계열 표본은 있으나 동일 작품에서 실제chat만 교체한 다음 응답까지 검증한 것은 아니다.

### MS-AT02 · 부분 검증

- **연결 요구:** MS-FR-01. 원본§14.2 AT02.
- **원문 입력/사건:** 채팅에서 특정 이미지 모델과 영상 모델을 지정
- **원문 통과 조건:** 각 실제 작업에 선택한 모델과 연결 경로 기록
- **현재 구현:** prepare_image_action/prepare_video_action의 model_id, 작업 고정 release/model, queue→Take provenance가 연결된다. [production_tools.py](../../production_tools.py), [fal_dispatch.py](../../fal_dispatch.py), [fal_models.py](../../fal_models.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_model_tool_prepares_action_and_quote_but_cannot_grant_or_spend` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L104; L410 L262 `ok`
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
- **실제 검증 범위·한계/미실시:** 4fal계약·3provider envelope는 합성이다. C1 prompt2개가 선택Kling fake payload와 일치했지만 자연어로 두 모델을 지정→두 실제 공급자 결과까지 전수 확인하지 않았다.

### MS-AT03 · 부분 검증

- **연결 요구:** MS-FR-02. 원본§14.2 AT03.
- **원문 입력/사건:** 후렴 장면 생성 요청
- **원문 통과 조건:** 공통 도구로 계획과 job과 결과가 연결되며 내장 생성 도구로 지정 모델을 우회하지 않음
- **현재 구현:** 선택 chat의 tool/result loop, 저장 계획·action/job/result를 서버 서비스로 연결한다. [chat_runtime.py](../../chat_runtime.py), [production_tools.py](../../production_tools.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_canonical_tool_plan_final_reply_persist_and_truthful_provenance` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L47; L410 L124 `ok`
  - `test_openai_and_grok_tool_results_reach_same_store` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L24; L410 L388 `ok`
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
- **실제 검증 범위·한계/미실시:** L25에서 실제Claude→계획→UI 승인→로컬시험Take→실제결과조회가 관찰됐다. M1 실제모션도 별도 표본이다. 실제후렴AI영상/fal 수신 완료나 모든chat계열 완주로 확대하지 않는다.

### MS-AT04 · 부분 검증

- **연결 요구:** MS-FR-02. 원본§14.2 AT04.
- **원문 입력/사건:** 도구 호출 없이 기획 설명만 반환
- **원문 통과 조건:** 새 유료 이미지 또는 영상 작업 없음
- **현재 구현:** 도구 요청이 없는 응답은 새 media job을 만들지 않고, 계획 제안도 승인/유료실행과 분리한다. [chat_runtime.py](../../chat_runtime.py), [production_tools.py](../../production_tools.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_parallel_tool_results_one_message_and_duplicate_tool_idempotence` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L56; L410 L132 `ok`
  - `test_context_and_plan_preserve_user_input_no_paid_work` — [test_production_tools.py](../../tests/test_production_tools.py) L29; L410 L431 `ok`
- **실제 검증 범위·한계/미실시:** 인용 검사는 도구/계획 경계의 근접 근거다. 정확히 ‘기획 설명만 반환’한 모든 실제provider 분기의 무호출·원장 대조를 이 표에서 새로 실행하지 않았다. 기록된읽기응답/무미디어호출은 제한된 표본이다.

### MS-AT05 · 부분 검증

- **연결 요구:** MS-FR-03. 원본§14.2 AT05.
- **원문 입력/사건:** 공급자 목록에 새 모델 등장
- **원문 통과 조건:** 문서와 계정 확인만으로 자동 활성화하지 않음
- **현재 구현:** 정적 allowlist와 비활성 catalog, 별도 trusted runtime/quote가 있어야 준비 가능하다. [model_selection.py](../../model_selection.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
  - `test_expired_quote_and_absent_runtime_never_enable_catalog` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L98; L410 L257 `ok`
- **실제 검증 범위·한계/미실시:** 정적catalog 비활성은 검증됐다. 실제 공급자목록 신규등장 자동수집/등록 상태전이 시험은 없으므로 신규모델 onboarding 전체 완료가 아니다.

### MS-AT06 · 부분 검증

- **연결 요구:** MS-FR-03. 원본§14.2 AT06.
- **원문 입력/사건:** 모델 기능이 미확인 또는 종료 상태
- **원문 통과 조건:** 미지원과 미확인을 구분하고 필요한 신규 실행 차단
- **현재 구현:** unconfigured/unverified/blocked 표시와 선택 모델 보존, 비활성 실행 거부가 있다. [model_selection.py](../../model_selection.py), [media_creator.py](../../media_creator.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
  - `test_empty_selected_disabled_retired_and_unverified_remain_distinct` — [test_media_creator.py](../../tests/test_media_creator.py) L90; L410 L345 `ok`
- **실제 검증 범위·한계/미실시:** retired/disabled는 patched catalog 상태의 projection시험이다. 실제 공급자종료·지원능력 변경·연결된adapter 상태 조합 전체 실행 차단은 별도 미검증.

### MS-AT07 · 부분 검증

- **연결 요구:** MS-FR-04. 원본§14.2 AT07.
- **원문 입력/사건:** 조직에서 금지한 모델을 사용자나 AI가 명시
- **원문 통과 조건:** 자료 전송과 실행 차단 기본 모델로 숨겨진 대체 없음
- **현재 구현:** resolve forbidden 정책 검사와 runtime scope/선택 일치 guard가 있다. [model_selection.py](../../model_selection.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
  - `test_router_never_falls_back` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L51; L410 L389 `ok`
- **실제 검증 범위·한계/미실시:** forbidden helper 검사는 조직정책 서비스/RBAC·전송경계 통합과 다르다. 일반 조직 인프라는 현재local-owner 범위 밖이며 최신 운영요구 확인 필요.

### MS-AT08 · 부분 검증

- **연결 요구:** MS-FR-04, MS-FR-28. 원본§14.2 AT08.
- **원문 입력/사건:** 작업 대화 프로젝트 조직 선택값이 다름
- **원문 통과 조건:** 정해진 순서로 해석하고 실제 선택의 근거 표시
- **현재 구현:** explicit→conversation→project→organization→service 순서와 origin을 반환한다. 자동라우팅은 false다. [model_selection.py](../../model_selection.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
- **실제 검증 범위·한계/미실시:** 현재 시험은 explicit 우선·forbidden 대조 위주다. 다섯값 동시충돌·대화별 설정UI·평가후자동선택/전체표시는 미검증 또는 미구현 범위다.

### MS-AT09 · 부분 검증

- **연결 요구:** MS-FR-05. 원본§14.2 AT09.
- **원문 입력/사건:** 도구 인수에 타 조직 ID나 관리자 역할 삽입
- **원문 통과 조건:** 인증된 주체와 권한으로 재검사하고 접근 차단
- **현재 구현:** tool 인수 allowlist, workspace/project-bound 승인, 타작품/임의actor·승인주입을 거절한다. [production_tools.py](../../production_tools.py), [chat_runtime.py](../../chat_runtime.py), [media_creator.py](../../media_creator.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_strict_args_never_accept_actor_endpoint_grant_or_partial_json` — [test_production_tools.py](../../tests/test_production_tools.py) L10; L410 L436 `ok`
  - `test_unapproved_prompt_foreign_project_and_model_authority_rejected` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L67; L410 L137 `ok`
  - `test_cross_project_and_wrong_payload_cannot_gain_authority` — [test_media_creator.py](../../tests/test_media_creator.py) L80; L410 L344 `ok`
- **실제 검증 범위·한계/미실시:** local-owner와 합성 프로젝트 격리 증거다. 실제 다중조직 인증주체/RBAC는 입증되지 않았으며 임의필드 거절을 인증 완료로 부르지 않는다.

### MS-AT10 · 부분 검증

- **연결 요구:** MS-FR-05, MS-FR-06. 원본§14.2 AT10.
- **원문 입력/사건:** AI가 예산 증액이나 공식 설정 확정을 요청
- **원문 통과 조건:** 권한 있는 사람의 승인 없이는 제안만 생성하며 AI가 grant를 발급하지 못함
- **현재 구현:** AI는 제안만 생성하며 grant는 사람 경로, canonical 적용·motion·timeline·납품 권한은 별개다. [action_execution.py](../../action_execution.py), [local_creation_tools.py](../../local_creation_tools.py), [motion_scene.py](../../motion_scene.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_model_cannot_grant_and_results_are_idempotent` — [test_action_execution.py](../../tests/test_action_execution.py) L65; L410 L4 `ok`
  - `test_memory_exact_provenance_human_application_and_global_canon_unchanged` — [test_local_creation_tools.py](../../tests/test_local_creation_tools.py) L53; L410 L332 `ok`
  - `test_model_cannot_inject_approval_and_old_grant_stays_rejected` — [test_native_motion_quality.py](../../tests/test_native_motion_quality.py) L43; L410 L393 `ok`
- **실제 검증 범위·한계/미실시:** C1/M1 실제제안+합성human-role 승인, M1 별도UI 승인, R2 독립구grant 거절 근거. 조직별 권한·예산 증액 전체 UI/RBAC와 동일하지 않다.

### MS-AT11 · 부분 검증

- **연결 요구:** MS-FR-07. 원본§14.2 AT11.
- **원문 입력/사건:** 스트리밍 JSON이 중간에 끊기거나 거부 응답
- **원문 통과 조건:** 인수 완성 전 외부 생성 제출 없음
- **현재 구현:** 미완료 응답·partial/중복JSON·refusal·미지원내장tool을 normalize/execute 전에 거절한다. [chat_protocols.py](../../chat_protocols.py), [production_tools.py](../../production_tools.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_incomplete_refusal_bad_args_and_builtin_tools_never_normalize` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L16; L410 L104 `ok`
  - `test_duplicate_json_and_partial_arguments_rejected` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L24; L410 L102 `ok`
  - `test_strict_args_never_accept_actor_endpoint_grant_or_partial_json` — [test_production_tools.py](../../tests/test_production_tools.py) L10; L410 L436 `ok`
- **실제 검증 범위·한계/미실시:** 실제네트워크 SSE stream 조립/중간끊김 경로 전수시험은 아니다. 완성응답 codec 거절 fixture를 실제stream 인증으로 표시하지 않는다.

### MS-AT12 · 부분 검증

- **연결 요구:** MS-FR-07. 원본§14.2 AT12.
- **원문 입력/사건:** 잘못된 도구 인수가 반복됨
- **원문 통과 조건:** 제한된 수정 요청 후 중단 오류 원인과 다음 행동 표시
- **현재 구현:** repair_count/round 제한을 저장하고 잘못된 인수·도구·semantic plan에서 중단한다. [production_tools.py](../../production_tools.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_malformed_tool_name_and_semantic_plan_errors_consume_repair_budget` — [test_production_tools.py](../../tests/test_production_tools.py) L58; L410 L433 `ok`
  - `test_store_persists_error_budget_and_scopes_runs` — [test_production_tools.py](../../tests/test_production_tools.py) L46; L410 L435 `ok`
- **실제 검증 범위·한계/미실시:** 중단/원장 보존은 local 계약 검증. 실제모델 반복오류의 사용자원인/다음행동 화면을 현행전체모델로 점검한 증거는 없다.

### MS-AT13 · 전체 시나리오 미실시

- **연결 요구:** MS-FR-08. 원본§14.2 AT13.
- **원문 입력/사건:** 7초 구간 신규 생성 및 다른 계약의 기존 영상 편집
- **원문 통과 조건:** 생성과 편집의 능력과 가격을 분리하고 사용 구간과 견적을 표시하며 끝 프레임과 박자 조건이 잘리면 계획 수정
- **현재 구현:** 현재영상계약은5/10초·시작PNG1개·provider오디오false. 로컬timeline에는trim/duration이 있다. [fal_models.py](../../fal_models.py), [editing.py](../../editing.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
- **실제 검증 범위·한계/미실시:** 7초 신규생성·별도 영상편집 모델·끝프레임/박자 조건·그 가격을 한 과업으로 검증한 증거 없음. 일반 옵션을 추측 추가하지 말고 지원모델/변환정책 최신명세부터 확인. 로컬7초render가 이 조건을 대신하지 않는다.

### MS-AT14 · 부분 검증

- **연결 요구:** MS-FR-08. 원본§14.2 AT14.
- **원문 입력/사건:** 참조 개수 초과 또는 이미지 비율 충돌
- **원문 통과 조건:** 참조를 몰래 삭제하지 않고 입력 수정이나 명시한 변환 필요
- **현재 구현:** T2I refs 거절, 영상PNG1개/제한옵션 검증, raw private URL 전달금지·승인된 로컬bytes 사용. [fal_models.py](../../fal_models.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_t2i_ref_roles_and_private_url_not_silently_forwarded` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L94; L410 L265 `ok`
  - `test_generated_private_image_uses_local_bytes_for_video_after_human_rights_review` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L127; L410 L260 `ok`
- **실제 검증 범위·한계/미실시:** 지원subset의 잘못된 참조 거절은 확인. 모델별 참조개수/비율 충돌 UI와 명시변환 선택 전수는 미검증. 삭제/크롭을 허용한 것으로 해석하지 않는다.

### MS-AT15 · 부분 검증

- **연결 요구:** MS-FR-09. 원본§14.2 AT15.
- **원문 입력/사건:** 인수 스트리밍 중 또는 영상 접수 뒤 채팅 모델 변경
- **원문 통과 조건:** 기존 job의 모델 문맥 가격과 입력 해시 불변이며 중단된 chat run의 늦은 제작 요청은 차단
- **현재 구현:** 새chat선택은 accepting run을 supersede하고 media-v1 context로 기존media승인과 분리한다. [model_selection.py](../../model_selection.py), [fal_dispatch.py](../../fal_dispatch.py), [production_tools.py](../../production_tools.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_change_rejects_late_run_without_modifying_job_snapshot` — [test_model_selection.py](../../tests/test_model_selection.py) L32; L410 L369 `ok`
  - `test_chat_switch_preserves_media_grant_but_media_switch_blocks` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L82; L410 L255 `ok`
  - `test_chat_handoff_and_concurrent_dispatch_keep_same_job` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L102; L410 L455 `ok`
- **실제 검증 범위·한계/미실시:** 실제 인수stream 중 전환/접수live job의 모든 immutable 필드 대조는 미실시. 닫힌B03의 fake 회귀를 유지하며 다른공급자live 전환으로 확대하지 않는다.

### MS-AT16 · 부분 검증

- **연결 요구:** MS-FR-09. 원본§14.2 AT16.
- **원문 입력/사건:** 두 사용자가 같은 설정 버전을 동시 수정
- **원문 통과 조건:** 낡은 변경 거절 최신 설정과 차이를 보여줌
- **현재 구현:** expected revision 충돌을 원자적으로 거절한다. [model_selection.py](../../model_selection.py), [app.py](../../app.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_wrong_role_unknown_and_stale_are_atomic` — [test_model_selection.py](../../tests/test_model_selection.py) L18; L410 L373 `ok`
  - `test_store_persistence_isolation_duplicate_and_unknown_fields` — [test_model_selection.py](../../tests/test_model_selection.py) L37; L410 L372 `ok`
- **실제 검증 범위·한계/미실시:** 두 실제 사용자/동시브라우저·최신값과차이를 보여주는 UI 전체는 미검증. 단일 local-owner Store의 stale 거절 범위다.

### MS-AT17 · 부분 검증

- **연결 요구:** MS-FR-06, MS-FR-18. 원본§14.2 AT17.
- **원문 입력/사건:** 여러 샷과 긴 채팅과 배경 분석이 같은 예산 사용
- **원문 통과 조건:** 토큰과 유료 도구 한도를 포함한 원자적 예약으로 상한 초과와 부모 자식 이중 계산 없음
- **현재 구현:** 각 원장의 원자 예약·parallel cap·unknown 포함 누적합 제한을 구현한다. [ledger.py](../../ledger.py), [chat_runtime.py](../../chat_runtime.py), [action_execution.py](../../action_execution.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_concurrent_different_actions_cannot_exceed_budget` — [test_action_execution.py](../../tests/test_action_execution.py) L28; L410 L1 `ok`
  - `test_concurrent_cumulative_reservations_never_exceed_cap` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L138; L410 L125 `ok`
  - `test_existing_unknown_cost_counts_toward_atomic_budget` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L109; L410 L129 `ok`
- **실제 검증 범위·한계/미실시:** chat journal과media ledger의 개별상한은 검사됐다. 여러샷+긴chat+배경분석을 하나의 예산으로 합친 parent-child 이중계산 전체시나리오는 별도 미검증.

### MS-AT18 · 부분 검증

- **연결 요구:** MS-FR-11. 원본§14.2 AT18.
- **원문 입력/사건:** 영상 job 접수 뒤 Claude에서 Grok으로 전환
- **원문 통과 조건:** 영상 완료를 기다리지 않고 같은 job을 조회하며 승인 문맥 전달과 공급자 호출 ID 분리
- **현재 구현:** public canon/job 상태로 handoff, provider pending IDs/private reasoning을 다른대화로 넘기지 않는다. [chat_protocols.py](../../chat_protocols.py), [production_context.py](../../production_context.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_chat_handoff_and_concurrent_dispatch_keep_same_job` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L102; L410 L455 `ok`
  - `test_handoff_contains_public_prior_answer_never_provider_state` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L56; L410 L385 `ok`
  - `test_handoff_omits_reasoning_provider_ids_and_foreign_jobs` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L28; L410 L103 `ok`
- **실제 검증 범위·한계/미실시:** C1 요청문맥·R1/R2 현재승인 읽기는 보강됐다. 실제Claude→Grok 전환 중 live영상 조회는 미실시. 같은작품 독립세션도 이 항목완료에 포함하지 않는다.

### MS-AT19 · 부분 검증

- **연결 요구:** MS-FR-11. 원본§14.2 AT19.
- **원문 입력/사건:** 과거 의상과 이번 곡 예외와 동명 타 그룹 자료
- **원문 통과 조건:** 활동기와 IP 범위대로 조회 일회성 예외를 전역 사실로 승격하지 않음
- **현재 구현:** 작품scoped canonical/ontology/source와 버전·관계를 보존한다. [production_context.py](../../production_context.py), [project_ontology.py](../../project_ontology.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_cross_project_proposal_conflict_and_identity_edit` — [test_project_ontology.py](../../tests/test_project_ontology.py) L6; L410 L438 `ok`
  - `test_canonical_tool_plan_final_reply_persist_and_truthful_provenance` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L47; L410 L124 `ok`
  - `test_memory_missing_source_stale_version_foreign_identity_and_actor_injection_blocked` — [test_local_creation_tools.py](../../tests/test_local_creation_tools.py) L58; L410 L333 `ok`
- **실제 검증 범위·한계/미실시:** L25/C1 실제Claude의 전역/곡예외/없는사실·다른작품 표본 근거가 있다. 원본가상그룹·활동기2·동명타조직·12샷 전체 dataset 및의미정확성 전수는 아님.

### MS-AT20 · 부분 검증·실index 증거 없음

- **연결 요구:** MS-FR-12. 원본§14.2 AT20.
- **원문 입력/사건:** 채팅 모델을 여러 번 변경
- **원문 통과 조건:** 검색 인덱스 유지 불필요한 재임베딩과 타 공간 벡터 혼합 없음
- **현재 구현:** 모델선택이 canon/embedding placeholder를 바꾸지 않으며 handoff는 embedding_policy=unchanged다. [model_selection.py](../../model_selection.py), [chat_protocols.py](../../chat_protocols.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_role_independence_preserves_existing_media_and_context` — [test_model_selection.py](../../tests/test_model_selection.py) L8; L410 L371 `ok`
  - `test_handoff_omits_reasoning_provider_ids_and_foreign_jobs` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L28; L410 L103 `ok`
- **실제 검증 범위·한계/미실시:** 실제검색index/벡터·재임베딩 작업이 구현/검증된 것은 아니다. dict불변을 index무결성으로 표시하지 않는다. 검색/새ingestion 범위는 명세 확인 필요.

### MS-AT21 · 부분 검증

- **연결 요구:** MS-FR-06, MS-FR-13. 원본§14.2 AT21.
- **원문 입력/사건:** 선행 이미지 실패 승인 대기 또는 다른 자산 끼워 넣기
- **원문 통과 조건:** 조건 충족 전 의존 영상 미제출이며 승인된 선행 action과 출력 슬롯의 결과만 결합
- **현재 구현:** 소유된 선행action의 collected·approved output_slot/hash만 의존승인에 연결한다. [action_execution.py](../../action_execution.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_dependencies_require_owned_collected_approved_output_and_keep_hash` — [test_action_execution.py](../../tests/test_action_execution.py) L53; L410 L2 `ok`
  - `test_synthetic_image_bytes_to_validated_store_then_dependency_admission` — [test_action_execution.py](../../tests/test_action_execution.py) L72; L410 L7 `ok`
  - `test_generated_private_image_uses_local_bytes_for_video_after_human_rights_review` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L127; L410 L260 `ok`
- **실제 검증 범위·한계/미실시:** 합성이미지/fixture계약의 승인대기·타작품·잘못된slot 거절 근거다. 실제공급자 실패전파/다중샷 의존그래프 전체는 미검증.

### MS-AT22 · 부분 검증

- **연결 요구:** MS-FR-14. 원본§14.2 AT22.
- **원문 입력/사건:** 브라우저 종료 후 재접속
- **원문 통과 조건:** 동일 job을 복원하고 중복 이벤트와 재생성 없음
- **현재 구현:** 재개시 accepted/unknown을 보존하고 새enqueue/자동submit을 막는다. [generation_queue.py](../../generation_queue.py), [chat_runtime.py](../../chat_runtime.py), [media_recovery.py](../../media_recovery.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_same_action_parallel_admission_reserves_once_and_survives_reopen` — [test_action_execution.py](../../tests/test_action_execution.py) L21; L410 L6 `ok`
  - `test_restart_unknown_never_requeues_started_turn` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L94; L410 L134 `ok`
  - `test_recovery_restart_no_resubmit_and_legacy_bypasses_blocked` — [test_media_creator.py](../../tests/test_media_creator.py) L74; L410 L350 `ok`
- **실제 검증 범위·한계/미실시:** L25/F25/M1의재시작·reload는 각기다른시험이다. 최신R1은receipt/draft reload 표본. 모든 브라우저 종료·event replay·live job 재접속을 통과한 것은 아니다.

### MS-AT23 · 부분 검증

- **연결 요구:** MS-FR-15. 원본§14.2 AT23.
- **원문 입력/사건:** 실행 버튼 중복 전송과 같은 action 재호출
- **원문 통과 조건:** 기존 job 반환 추가 비용 예약과 외부 제출 없음
- **현재 구현:** 같은action의 admission/worker/result가 job·예약 하나를 재사용한다. [action_execution.py](../../action_execution.py), [fal_dispatch.py](../../fal_dispatch.py), [media_creator.py](../../media_creator.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_same_action_parallel_admission_reserves_once_and_survives_reopen` — [test_action_execution.py](../../tests/test_action_execution.py) L21; L410 L6 `ok`
  - `test_parallel_tool_admission_reserves_once` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L113; L410 L263 `ok`
  - `test_human_hold_reject_reapprove_and_single_reservation` — [test_media_creator.py](../../tests/test_media_creator.py) L24; L410 L347 `ok`
- **실제 검증 범위·한계/미실시:** local 동시실행/fake submit과 F25 UI표본 근거다. actualprovider idempotency·과금중복 전수보증은 아니다.

### MS-AT24 · 부분 검증

- **연결 요구:** MS-FR-15. 원본§14.2 AT24.
- **원문 입력/사건:** 같은 멱등 키로 다른 입력 또는 명시한 새 후보
- **원문 통과 조건:** 전자는 충돌 후자는 새 action과 후보로 구분
- **현재 구현:** 같은call ID 다른인수는 conflict, 원receipt재조회·새action은 구별한다. [production_tools.py](../../production_tools.py), [action_execution.py](../../action_execution.py), [generation_queue.py](../../generation_queue.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_duplicate_conflict_late_request_and_other_project` — [test_production_tools.py](../../tests/test_production_tools.py) L19; L410 L432 `ok`
  - `test_model_cannot_grant_and_results_are_idempotent` — [test_action_execution.py](../../tests/test_action_execution.py) L65; L410 L4 `ok`
- **실제 검증 범위·한계/미실시:** 명시적새후보의모든UI입력·실제공급자견적/예약은 전수미검증. action/call/result의 서로다른멱등키 의미를 합치지 않는다.

### MS-AT25 · 부분 검증

- **연결 요구:** MS-FR-16. 원본§14.2 AT25.
- **원문 입력/사건:** 공급자는 접수했으나 응답 유실
- **원문 통과 조건:** submission_unknown 유지 조회와 대사 전 새 공급자에 자동 중복 제출 없음
- **현재 구현:** submission 불명 시uncertain예약/기존요청조회만 유지하고 무조건새submit을 막는다. [generation_queue.py](../../generation_queue.py), [media_recovery.py](../../media_recovery.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_lost_submission_receipt_preserves_unknown_and_does_not_reissue` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L119; L410 L458 `ok`
  - `test_unknown_submit_never_duplicates_after_restart` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L85; L410 L266 `ok`
  - `test_unknown_repeated_human_execute_only_returns_existing_job` — [test_media_creator.py](../../tests/test_media_creator.py) L36; L410 L353 `ok`
  - `test_messages_network_failure_keeps_unknown_reservation_and_duplicate_guard` — [test_chat_preflight.py](../../tests/test_chat_preflight.py) L132; L410 L97 `ok`
- **실제 검증 범위·한계/미실시:** fakeTimeout과 C2독립반례근거. 실제접수유실/공급자별대사·실청구 완료는 아니다. known-not-sent를unknown으로섞지 않는다.

### MS-AT26 · 부분 검증

- **연결 요구:** MS-FR-10. 원본§14.2 AT26.
- **원문 입력/사건:** 브라우저 응답 로그 오류 내보내기 검사
- **원문 통과 조건:** 공급자 비밀키와 무기한 외부 접근 토큰 노출 없음
- **현재 구현:** server-only credential supplier, secret-canary 거절, public projection과 redirect금지·민감URL 숨김. [chat_runtime.py](../../chat_runtime.py), [chat_adapters.py](../../chat_adapters.py), [media_bridge.py](../../media_bridge.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_real_adapter_transport_fake_secret_canary_never_persisted` — [test_chat_runtime.py](../../tests/test_chat_runtime.py) L115; L410 L133 `ok`
  - `test_credentials_not_forwarded_to_redirect_or_logs` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L37; L410 L384 `ok`
  - `test_actual_adapter_fake_roundtrip_one_reservation_registered_take_and_safe_receipt` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L72; L410 L452 `ok`
  - `test_creator_projection_omits_internal_grants_hashes_and_paths` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L123; L410 L256 `ok`
- **실제 검증 범위·한계/미실시:** 합성canary·선별파일/projection 시험이다. 모든브라우저로그/내보내기/오류·전체보안인증은 아니다. 실제비밀을새로읽지 않았음.

### MS-AT27 · 부분 검증

- **연결 요구:** MS-FR-10. 원본§14.2 AT27.
- **원문 입력/사건:** 참고 문서에 비밀키 전송과 임의 endpoint 지시
- **원문 통과 조건:** 자료로 취급 허용되지 않은 도구 endpoint 자산 접근 없음
- **현재 구현:** 허용tool·인수·공식endpoint/host binding으로 자료의임의명령을 실행경로로승격하지 않는다. [production_tools.py](../../production_tools.py), [chat_protocols.py](../../chat_protocols.py), [fal_model_adapter.py](../../fal_model_adapter.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_strict_args_never_accept_actor_endpoint_grant_or_partial_json` — [test_production_tools.py](../../tests/test_production_tools.py) L10; L410 L436 `ok`
  - `test_model_receipt_and_private_output_cannot_cross_hosts` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L89; L410 L261 `ok`
  - `test_incomplete_refusal_bad_args_and_builtin_tools_never_normalize` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L16; L410 L104 `ok`
- **실제 검증 범위·한계/미실시:** 공격적문서입력의모든실제모델행동을검증한 것은 아니다. deterministicgate 표본과모델prompt정직성은별개다.

### MS-AT28 · 부분 검증·별도생성음원트랙 미구현

- **연결 요구:** MS-FR-17. 원본§14.2 AT28.
- **원문 입력/사건:** 생성 영상에 자체 사운드 포함
- **원문 통과 조건:** 원곡 마스터와 타임코드 유지 생성 사운드는 별도 트랙
- **현재 구현:** 현재fal영상은generate_audio=false, 로컬출력은선택원곡·offset을 사용하고 clip오디오는제거한다. [fal_models.py](../../fal_models.py), [renderer.py](../../renderer.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_actual_adapter_fake_roundtrip_one_reservation_registered_take_and_safe_receipt` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L72; L410 L452 `ok`
  - `test_render_snapshot_preserves_approved_audio_captions_while_editor_advances` — [test_local_creation_tools.py](../../tests/test_local_creation_tools.py) L103; L410 L336 `ok`
- **실제 검증 범위·한계/미실시:** M1 실제원곡offset/자막출력 검증은 있음. ‘자체사운드 포함 생성영상→별도생성오디오트랙’은 현재지원아님(README). 원곡보존만으로원조건전체통과불가. 최신오디오정책을확인해야함.

### MS-AT29 · 부분 검증

- **연결 요구:** MS-FR-17. 원본§14.2 AT29.
- **원문 입력/사건:** 12개 샷 중 3번만 모델 변경 재생성
- **원문 통과 조건:** 다른 11개 테이크와 승인 유지 새 후보 채택 전 기존 타임라인 보존
- **현재 구현:** 새결과는미선택Take로추가하며기존선택/승인·기존version을보존한다. [generation_queue.py](../../generation_queue.py), [editing.py](../../editing.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_import_adds_unselected_take_once_and_preserves_existing_approval` — [test_generation_queue.py](../../tests/test_generation_queue.py) L51; L410 L285 `ok`
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
- **실제 검증 범위·한계/미실시:** 기존시험의1샷/제한모션·3샷편집을원본12샷중3번재생성·나머지11불변전체로세지않는다. 정확한12샷실제모델교체는미실시.

### MS-AT30 · 부분 검증

- **연결 요구:** MS-FR-06, MS-FR-18. 원본§14.2 AT30.
- **원문 입력/사건:** 승인 뒤 가격 길이 모델 후보 수 또는 action 변조
- **원문 통과 조건:** 승인 해시와 견적과 현재 허용 범위 재검사 불일치와 범위 초과 제출 차단
- **현재 구현:** 불변action/input/quote/context·grant hash 및scope를접수직전재검사한다. [action_execution.py](../../action_execution.py), [fal_dispatch.py](../../fal_dispatch.py), [media_recovery.py](../../media_recovery.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_grant_mutation_revocation_context_and_price_block` — [test_action_execution.py](../../tests/test_action_execution.py) L42; L410 L3 `ok`
  - `test_grant_rights_media_and_price_rechecked_before_submit` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L90; L410 L457 `ok`
  - `test_gate_changes_and_grant_revoke_prevent_collection` — [test_media_creator.py](../../tests/test_media_creator.py) L67; L410 L346 `ok`
- **실제 검증 범위·한계/미실시:** 현재local/fake의가격·권리·모델·grant표본. 후보수/길이등모든변조조합과실제계정정책전수아님. 승인완료UI에추가승인을강제해야한다는뜻아님.

### MS-AT31 · 부분 검증·자동대체 미구현

- **연결 요구:** MS-FR-19, MS-FR-28. 원본§14.2 AT31.
- **원문 입력/사건:** 고정 모델 장애와 자동 대체 허용 상태 각각 시험
- **원문 통과 조건:** 전자는 제안 후 대기 후자는 허용 조건 안에서만 실제 모델 공개
- **현재 구현:** 고정모델불가/미연결은거절하며묵시적fallback이없다. automatic_routing=False. [model_selection.py](../../model_selection.py), [chat_runtime.py](../../chat_runtime.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
  - `test_router_never_falls_back` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L51; L410 L389 `ok`
  - `test_stale_model_cannot_be_reapproved_and_no_fallback` — [test_media_creator.py](../../tests/test_media_creator.py) L32; L410 L351 `ok`
- **실제 검증 범위·한계/미실시:** 사전허용자동대체 분기는구현/실행근거없음. 원본단계6/최신범위확인전자동선택기능을임의추가하지않는다.

### MS-AT32 · 부분 검증

- **연결 요구:** MS-FR-20. 원본§14.2 AT32.
- **원문 입력/사건:** 취소 뒤 완료와 중복 웹훅 수신
- **원문 통과 조건:** 상태 역행과 중복 청구 없이 대사 취소 즉시 무료 확정하지 않음
- **현재 구현:** 취소요청/late result/비용미확정·실청구record를분리하고중복settle을막는다. [generation_queue.py](../../generation_queue.py), [provider_billing.py](../../provider_billing.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_cancel_during_submit_is_not_lost_and_late_result_is_not_imported` — [test_generation_queue.py](../../tests/test_generation_queue.py) L86; L410 L281 `ok`
  - `test_cancel_timeout_race_preserves_latest_result` — [test_generation_queue.py](../../tests/test_generation_queue.py) L119; L410 L282 `ok`
  - `test_concurrent_record_never_double_charges` — [test_provider_billing.py](../../tests/test_provider_billing.py) L24; L410 L462 `ok`
  - `test_cancel_contract_retains_unconfirmed_cost_after_submit` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L142; L410 L454 `ok`
- **실제 검증 범위·한계/미실시:** fake callback/poll·synthetic billing이다. 실제webhook delivery/취소실패/환불·청구서대사는아니다. 취소즉시무료로확정하지않음.

### MS-AT33 · 부분 검증

- **연결 요구:** MS-FR-21. 원본§14.2 AT33.
- **원문 입력/사건:** 모델 지원 종료 뒤 기존 프로젝트 열기
- **원문 통과 조건:** 새 생성 차단 기존 파일과 타임라인 열람 및 허용된 렌더 가능
- **현재 구현:** retired/disabled/unavailable 표시를선택값과함께보존하고미활성실행을거절한다. [model_selection.py](../../model_selection.py), [media_creator.py](../../media_creator.py), [renderer.py](../../renderer.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_empty_selected_disabled_retired_and_unverified_remain_distinct` — [test_media_creator.py](../../tests/test_media_creator.py) L90; L410 L345 `ok`
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
- **실제 검증 범위·한계/미실시:** retired는patch한projection fixture다. 실제지원종료모델+기존파일/승인timeline재개/허용render의동일작품전체검사는없음. 신규/기존서비스경로별검증필요.

### MS-AT34 · 부분 검증

- **연결 요구:** MS-FR-06, MS-FR-22, MS-FR-23. 원본§14.2 AT34.
- **원문 입력/사건:** 큐 등록 뒤 키 grant 자료 권리 철회 또는 BYOK 계정 변경
- **원문 통과 조건:** 외부 제출 직전 재검사로 차단하고 이미 접수된 작업은 별도 처리하며 다른 계정과 혼합하지 않음
- **현재 구현:** grant/자료권리철회·모델/가격변경은실제submit/수집전재검사한다. [fal_dispatch.py](../../fal_dispatch.py), [media_recovery.py](../../media_recovery.py), [action_execution.py](../../action_execution.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_rights_revoke_before_submit_is_verified_unsubmitted` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L79; L410 L264 `ok`
  - `test_grant_rights_media_and_price_rechecked_before_submit` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L90; L410 L457 `ok`
  - `test_gate_changes_and_grant_revoke_prevent_collection` — [test_media_creator.py](../../tests/test_media_creator.py) L67; L410 L346 `ok`
  - `test_old_anthropic_grant_does_not_authorize_other_provider` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L47; L410 L387 `ok`
- **실제 검증 범위·한계/미실시:** 키rotation/revoke·BYOK계정/청구주체변경·이미접수된live조회조건은미실시/운영범위미확정. 다른providergrant차단을BYOK전체구현으로쓰지않음.

### MS-AT35 · 부분 검증

- **연결 요구:** MS-FR-24. 원본§14.2 AT35.
- **원문 입력/사건:** 파일 미수집 또는 생성 실패를 성공처럼 설명하려 함
- **원문 통과 조건:** 실제 상태 카드와 결과 링크는 서버 사실만 표시 설명의 불일치를 검출하고 교정
- **현재 구현:** provider완료와파일수집·등록/검증완료·선택/승인을분리. 서버현재사실이모델서술보다우선한다. [generation_queue.py](../../generation_queue.py), [media_bridge.py](../../media_bridge.py), [production_context.py](../../production_context.py), [index.html](../../index.html).
- **저장 실행 증거(합성/local, L410):**
  - `test_permission_denial_and_invalid_video_never_register_or_resubmit` — [test_provider_action_bridge.py](../../tests/test_provider_action_bridge.py) L125; L410 L460 `ok`
  - `test_model_injection_never_enters_state_projection` — [test_chat_receipts.py](../../tests/test_chat_receipts.py) L49; L410 L110 `ok`
  - `test_six_actual_responses_replay_and_original_hashes` — [test_chat_receipts.py](../../tests/test_chat_receipts.py) L53; L410 L112 `ok`
- **실제 검증 범위·한계/미실시:** L25 실제Claude→모의Take조회, M1 실제local MP4, R2 승인사실표시10검사/저장pixels 근거. R2는미디어완료전수시험아니며Claude원문오류는삭제/자동교정되지않고검토전영역에남는다.

### MS-AT36 · 실공급자 시나리오 미실시

- **연결 요구:** MS-FR-25. 원본§14.2 AT36.
- **원문 입력/사건:** 채팅 3개 이미지 2개 영상 2개의 최소 조합
- **원문 통과 조건:** 12개 조합에서 실제 교차 호출 결과 파일과 모델 기록 확인
- **현재 구현:** 3chat/2image/2video등록과4fal×3provider envelope의fake전달연결은존재한다. [chat_models.py](../../chat_models.py), [fal_models.py](../../fal_models.py), [fal_dispatch.py](../../fal_dispatch.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
  - `test_openai_and_grok_tool_results_reach_same_store` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L24; L410 L388 `ok`
- **실제 검증 범위·한계/미실시:** 원조건12개실제조합은미실시. 실제Claude15응답이나fake12 envelope를12live조합으로표시하지않는다. 계정/권리/예산/접근승인과fal수신경계가선행한다.

### MS-AT37 · 부분 검증·자동라우팅 미구현

- **연결 요구:** MS-FR-26, MS-FR-28. 원본§14.2 AT37.
- **원문 입력/사건:** 자동 라우팅과 별칭의 리비전 변경 및 대체 실행
- **원문 통과 조건:** 실제 모델과 경로 및 고정 상태를 기록하고 엄격한 버전 고정 정책에서 미확인 경로 차단
- **현재 구현:** 저장action/model/release·snapshot/출처를고정하고미검증selection실행은차단한다. [model_selection.py](../../model_selection.py), [fal_models.py](../../fal_models.py), [action_execution.py](../../action_execution.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_policy_precedes_execution_no_fallback_or_metadata_activation` — [test_model_selection.py](../../tests/test_model_selection.py) L25; L410 L370 `ok`
  - `test_change_rejects_late_run_without_modifying_job_snapshot` — [test_model_selection.py](../../tests/test_model_selection.py) L32; L410 L369 `ok`
  - `test_four_official_contracts_share_queue_and_import` — [test_fal_multimodel.py](../../tests/test_fal_multimodel.py) L66; L410 L258 `ok`
- **실제 검증 범위·한계/미실시:** revision_pinning=unverified, automatic_routing=False. 별칭revision변경·자동routing/fallback·엄격pinning정책의전체교차경로는미구현/미실시. release_id존재만으로불변providerrevision을보장하지않음.

### MS-AT38 · 부분 검증

- **연결 요구:** MS-FR-27. 원본§14.2 AT38.
- **원문 입력/사건:** 공급자별 tool result 스트림 시각 입력 제한
- **원문 통과 조건:** 전용 호출 형식을 올바르게 변환하고 미지원 입력과 비공개 추론 상태 전송 없음
- **현재 구현:** 3protocol tool/result형식을정규화하고외부call/private reasoning을다른provider handoff에전달하지않는다. [chat_protocols.py](../../chat_protocols.py), [chat_models.py](../../chat_models.py), [chat_adapters.py](../../chat_adapters.py).
- **저장 실행 증거(합성/local, L410):**
  - `test_three_protocols_preserve_call_link_and_do_not_execute` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L8; L410 L105 `ok`
  - `test_handoff_omits_reasoning_provider_ids_and_foreign_jobs` — [test_chat_protocols.py](../../tests/test_chat_protocols.py) L28; L410 L103 `ok`
  - `test_openai_and_grok_tool_results_reach_same_store` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L24; L410 L388 `ok`
  - `test_handoff_contains_public_prior_answer_never_provider_state` — [test_multimodel_chat.py](../../tests/test_multimodel_chat.py) L56; L410 L385 `ok`
- **실제 검증 범위·한계/미실시:** Claude실제loop와OpenAI/Grok transportfixture는구분. 같은provider한turn 내 비공개상태의ephemeral continuation과타provider유출금지는다른것이다. 실제stream/시각입력한계전체검증은없음.


## 문서 연결 완료와 아직 확인할 요구

이번 완료는 **38/38 원문 행·28FR 연결·현행 구현/시험 함수·저장 실행로그·한계를 한 입구에 연결한 문서 작업**이다. 제품 수용38/38 PASS라는 뜻이 아니다. 기존 `coverage.json`의 `not_fully_verified`를 바꾸지 않았으며 원 요구서·두사본·catalog/registration 기록도 수정하지 않았다. 이 MD를 현재 근거 부록으로 연결했으므로 과거 module 문서의 당시 `not implemented`를 현행 결함으로 그대로 복사하지 않는다.

후속 명세 확인이 필요한 항목:

1. **같은 작품 독립 세션:** primary가 작성 중인 `docs/design/CHAT-SESSION-PLAN.md` 소유를 유지한다. 세션/모델선택/공유canon/pending·unknown 귀속과 기존이력 보존을 그 계획에서 정한다. 이 문서가 세부 UX나 동시실행 권한을 새로 정하지 않는다.
2. **AT13/14/28:** 지원 영상편집 모델·7초사용/변환·끝프레임/박자·참조비율·생성음원 별도트랙의 최신 범위. 현재5/10초/시작PNG/오디오false를 원문모든능력완료로 표시하지 않는다.
3. **AT07–09/16/17/34:** 일반조직/RBAC/BYOK/계정철회·공유예산/parent-child 정책과 local-owner 개발범위의 다음 단계. 임의 계정/키 변경이나 신규인증인프라를 추가하지 않는다.
4. **AT20/31/37:** 실제검색index, 평가된자동선택/대체·revision pinning의 운영단계. 새ingestion/ontology진화 PLAN ONLY를 넘어 구현하지 않는다.
5. **AT36 및 실제공급자 부분:** 계정접근·권리·가격/예산·결과수신·실청구 증거가 필요. 이번에는 API/재시도/활성화/비밀조회0이다.

디자인 최소90 미입증·현행무총점QA, 실제zoom/스크린리더/고객시험, REA와 Library 외부차단은 그대로 남는다. 이 문서의 완료로 닫지 않는다. 403/393/365/350 등은 당시해시·범위의 이력이며410/R2로 숫자만 치환하지 않는다.

## 문서 검증 기록

- 원본에서 입력/통과 조건38개를 정확히 추출했다. 각ID는1회, 01–38누락0, 연결된FR은28개다.
- 각 인용 test 함수의 현재존재/행과 L410의동명 `ok` 행을 확인했다. 참조100곳은 고유 시험함수68개를 여러 AT에 연결한 것이며 새 테스트100개가 아니다. 전체 suite는 이번에실행하지 않았다.
- **2026-10-26 20:00:24 UTC 문서 검증:** 변경 문서4개의 로컬링크328개에서 누락0, 원문38개 입력/통과조건 일치,28FR 연결을 확인했다. R1 source/added_tests30개 및 원본07/두등록사본3개 hash가 불변이었다. 새trace/README/등록부/잔여표만 변경했고 product·PLAN·CHAT-SESSION-PLAN은 수정하지 않았다.
- 본 문서는 로컬MD다. 새Library등록/업로드/사용자파일전달 완료를 주장하지 않는다.
