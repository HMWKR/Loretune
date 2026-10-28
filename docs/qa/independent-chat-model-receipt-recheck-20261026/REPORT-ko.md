# CQ-01/02 한정 독립 재검증

2026-10-26 UTC. **CQ-01 stale 강조는 검사 범위 통과. CQ-02 직접 표시/저장 경로는 통과했지만 polling 정합성 P2 1건이 남아 전체 완료로 닫지 않는다.** 승인·모델 선택 실행 로직 변경이나 권한 우회는 발견하지 않았다. 독립 대화 세션은 건드리지 않았다.

## CQ-R01 — P2: 모델 선택만 바뀐 polling 응답을 버려 현재 모델이 이전값으로 남음

**관련 요구:** SPEC-MS-001 §3.2 (`07_Chat_Directed_Multimodel_Production_Spec.md:109`)의 입력 주변 현재 모델 표시, §3.1/3.2의 다음 요청 적용 범위. MS-FR-01/09와 관련된 표시 정합성 사례이며 MS-AT 전체 통과/실행 실패를 뜻하지 않는다.

**원인:** `index.html:619`의 `chatChanged`는 `chat_turns`, `chat_connection`, `chat_receipts`만 비교한다. 모션 구성이 없는 작품은 `chat_receipts=[]`이고, 미연결 상태에서는 선택 변경 전후 `chat_connection`도 같다. 따라서 새 서버 revision과 `model_settings`가 와도 `:624`의 `state=fresh`와 `:628`의 `drawModelChat()`를 실행하지 않는다. 새 라벨 함수 `:215`/`:405` 자체는 올바르나, 오래된 client state를 읽는다.

**독립 재현:** 새 임시 Store에서 작품 A/shot s를 만들고 모션은 만들지 않는다. 제품의 실제 `Store.mutate(model_settings)`로 GPT를 저장해 revision3 상태를 얻는다. 이어 Grok 저장(revision4), 미선택 저장(revision5) 상태를 만든다. 각 응답을 복제 소스의 실제 polling callback과 `drawModelChat`를 실행하는 Node VM의 fake fetch로 전달한다. HTTP 요청/브라우저/외부 모델은 없다.

|변경|기대|3회 polling 후 실제|
|---|---|---|
|GPT → Grok|`기획 모델: Grok 4.7 · 작품 기본값 · 다음 요청 기준`|서버 rev4, client rev3. 여전히 GPT 6 Luna|
|GPT → 미선택|`기획 모델: 미선택 · 모델 설정에서 선택하세요.`|서버 rev5, client rev3. 여전히 GPT 6 Luna|

같은 fresh 응답에 채팅 진행 변경도 포함시키면 라벨이 갱신되는 control은 통과했다. 실제 backend가 생성한 두 응답 모두 chat receipt/connection이 같음을 먼저 assertion으로 확인했다. 증거: [independent-probe.json](independent-probe.json), [합성 상태 입력](synthetic-probe-input.json), [실행 코드](probe.cjs), [runner](run_offline.py).

**영향/한계:** 다른 창 등 기존 설정 저장 경로에서 선택을 변경한 경우 현재 입력 위 모델 정보가 수동 새로고침 또는 다른 chat 변화 전까지 틀릴 수 있다. 같은 화면의 정상 저장→refresh 경로와 primary가 수행한 모션 영수증이 있는 fixture의 polling 표본을 부정하지 않는다. 현재 receipt에 observed revision이 있어 바뀌는 fixture는 이 누락을 가릴 수 있다. provider 호출/다른 모델 실제 실행/자동 승인 문제를 재현한 것은 아니며, 표시 정합성 P2로 한정한다. 독립 세션 기능의 신규 구현 요청이 아니다.

**최소 수정 제안:** 기존 epoch/sequence/busy/dirty/project/shot/revision guard를 그대로 두고, 선택 기본값과 표시용 catalog 변경을 별도 비교해 필요한 state와 입력 라벨을 갱신한다. 현재 label은 저장된 서버 선택을 읽도록 유지하고 과거 답변/연결 모델로 대체하지 않는다. 모델 설정창의 미저장 선택을 무조건 다시 그리거나 채팅 초안을 지우지 않는다. 승인·실행 서비스를 변경할 이유가 없다. 제품 patch는 작성·적용하지 않았다.

**수용기준:** 모션이 없는 작품에서 GPT→Grok, GPT→null의 각 정상 최신 응답 후 라벨이 일치할 것. 오래된 응답/다른 project/dirty 중 응답은 기존 guard대로 처리할 것. 새 catalog 표시명이 들어오면 라벨을 갱신하되, 입력 초안·과거 답변 모델·승인 상태·현재 실행은 유지할 것. 기존 motion receipt polling 표본도 계속 통과할 것. 이 반례는 fake Store/VM만으로 수정 재검증 가능하다.

## 통과한 경계

- 새 표시 함수는 `model_settings.selections.chat`와 같은 역할의 catalog 항목만 사용한다. 현재 GPT/과거 Claude 구분, null 미선택, 사라진 ID/다른 역할 정보 미확인, 긴/악성 표시명 textContent 경로 통과. capability가 Claude를 가리켜도 현재값으로 대신하지 않는다. `index.html:213`–`:220`, `:405`.
- 저장 선택의 상태가 disabled/unverified/retired여도 선택 이름과 연결 상태를 혼동하지 않고, 기존 submit 비활성 판단을 바꾸지 않는다. 기존 신규 display unittest 4개를 원문 그대로 재실행해 4/4 통과.
- 현재 `matches_current_context===false`에서만 실행불가 문장이 첫 목록 항목/strong/기존 warning 색으로 표시된다. true/null과 과거 영수증에는 stale 강조를 넣지 않는다. 사실 배열/입력 객체/버튼 권한 불변. `index.html:399`, `studio.css:305`–`:306`.
- 독립 VM 6개 시나리오 중 4 PASS, 위 같은 결함의 두 변형 FAIL. 기존 4개와 합쳐 8 PASS/2 FAIL이며, primary의 414/16 숫자를 독립 실행으로 합산하지 않는다.
- baseline 대비 backend/media 8개 해시와 모델 설정 submit handler가 동일하다. 변경은 표시 helper/라벨/markup/CSS에 한정되고 저장·라우팅·승인 로직은 유지된다.

## 고정 버전·화면·검증 한계

FINAL-MANIFEST 동결 `2026-10-26T20:34:55.516417+00:00`.

- HTML `4c2fa6e647e09b0182a394819792cee344ff36095bd019a28b48e9003cdd8418`
- CSS `348e0f0fbe4bdc617ff0d94b7e7a11d4bfd3862df2020312412bc264fa65361b`

manifest의 source/artifact 해시는 시작과 종료 모두 일치했다. 권한·mtime를 보존한 별도 snapshot에서 실행했다. [base-manifest](base-manifest.json), [end-check](end-check.json), [결과](result.json), [기존 검사 로그](existing-tests.log).

저장된 `after-1920.jpg`, `after-1280.jpg`, `empty-1920.jpg`, `history-1280.jpg` 픽셀을 직접 열어 현재 선택/미선택/과거 모델과 stale 첫 줄·과거 중립 상태를 확인했다. 화면은 primary의 Chrome 1920×1080/1280×900 표본이며 이번 독립 브라우저 조작은 0이다. primary의 초안/포커스/reopen 관측을 새로 실행했다고 주장하지 않는다. 긴 이름의 실제 레이아웃, zoom, AT, mobile, 일반 전체 디자인은 재평가하지 않았다.

제품/공유 DB/키/API/서버 변경 없음. 모든 쓰기는 새 QA 파일 또는 별도 합성 임시 Store에만 수행. provider 호출·HTTP·listener·브라우저·설치·업로드 0, 금지 동작 시도 0. 위 좁은 반례 외 새로운 범용 감사는 수행하지 않았다.
