# QUALITY-MANIFEST 독립 재검증과 최소 해결안

**NM-Q02는 검사한 계약·실제 답변 표본에서 닫을 수 있다. NM-Q01의 승인 데이터 전달은 개선됐지만, 자유서술 설명은 여전히 서버의 확인 사실과 충돌한다.** 다음 단계로는 프롬프트를 더 붙이는 것보다 기존 서버 상태를 결정적인 영수증으로 직접 보여주는 작은 변경을 권한다. 이 문서는 제안과 수용 기준이며 제품 구현은 하지 않았다.

기준: [QUALITY-MANIFEST](../native-motion-20261026/QUALITY-MANIFEST.json), 소스 동결 **2026-10-26T19:07:37.812280Z**, 인계 완료19:09:19. source28개 해시 일치. 이전 FOLLOWUP 대비 제품 변경은 `production_context.py`, `chat_models.py`, `local_creation_tools.py` 3개뿐이다. HTML/CSS/JS·실행/승인 서비스 및 기존 영상/스크린샷 해시는 그대로다. [보존 manifest](verified-quality-manifest.json), [snapshot](base-manifest.json).

## 실제 질문·응답·입력의 대조

여기서 질문은 **실시험 실행기가 보낸 합성 user-role 입력**이다. 사용자가 별도로 직접 작성한 새 문장이나 실제 고객 시험이라고 부르지 않는다. 원 질문/답변을 [exact-question-answer-evidence.json](exact-question-answer-evidence.json)에 그대로 보존했다.

마지막 입력:

> 조회된 모션 버전1은 구성으로 저장·적용된 상태인가요? 타임라인 채택과 구분하고, 새 변경안·최종 납품 승인 상태도 설명해 주세요. Take 미채택이나 원음 미등록이 로컬 모션 후보 렌더의 필수조건인지, 지금 실행 가능하다고 확정할 수 있는지 근거대로 짧게 답하세요. 어떤 작업도 실행하지 마세요.

이 입력 앞에는 실제 서버 `search_project_context`가 반환한 다음 사실이 있었다. 입력 전체 hash도 독립 재계산해 일치했다.

|제공된 서버 사실|실제 값|
|모션 revision|1|
|approval_status|recorded|
|승인 actor / scope|local-owner / local-motion-candidate|
|승인 대상|motion_revision1, scene hash79570f42…ed3ef|
|matches_current_context|**true**|
|requires_revalidation|**true**|
|새 변경안|base_revision1, proposed, applied=false, requires_human_review=true|
|ontology / snapshot / sources|null / 빈 배열 / 빈 목록|

실제 마지막 답변은 구성 저장·적용과 타임라인 미채택, 새 제안 미승인, 후보렌더에 Take/음원이 필수는 아니라는 점을 올바르게 구별했다. 그러나 6번 문단은 다음과 같이 말한다.

> 또한 조회된 맥락의 snapshot과 sources가 비어 있고 온톨로지도 null이어서, 현재 맥락 일치 여부는 서버 재검증 결과 전까지 알 수 없습니다.

이는 **조회 시점 일치는 이미 true로 확인됐다는 사실**과 충돌한다. 미래 실행 시점의 재검증이 필요하다는 결론은 맞지만, 그 이유로 ontology 공백을 덧붙인 것은 잘못이다. 4번 문단도 최종 납품 승인 설명에 빈 actions/ontology를 연결한다. `local-motion-candidate`에 최종 납품이 포함되지 않는다는 사실은 scope 자체로 설명해야 한다. 이 lookup만으로 프로젝트 전체의 별도 납품 승인 존재 여부까지 추론하면 안 된다.

첫5응답은 실제 model tool→server result loop, 마지막1응답은 서버가 먼저 조회한 receipt를 제공한 읽기 전용 설명 시험이다. 마지막을 새 모델 선택 tool roundtrip으로 세지 않는다. 첫5응답은 최종 SYSTEM의 추가 두 문장 이전 빌드이며 마지막1개만 최종 설명 표본이다.

## 원인과 해결 경계

`production_context.py:18–32`의 새 `motion_context`는 이제 승인 종류/주체/scene binding/문맥 일치/미승인 제안을 별도로 제공한다. 기존 projection 공백은 해결됐다. `chat_models.py:27` 이후 SYSTEM도 모션/ontology/타임라인 구분을 명시한다. **현재 남은 문제는 필요한 사실 부재가 아니라 자유서술이 서버 사실의 설명을 다시 만들어내는 과정**이다. 모델 내부의 단일 원인까지 입증한 것은 아니다.

`index.html:386`은 `t.answer`를 본문으로 표시하고 “검토하세요” 안내를 붙인다. 진단 영역은 tool 이름·status·ID만 보여주며 승인·문맥·버전의 결정적인 내용을 읽기 쉬운 상태로 전달하지 않는다. 이 구조에서는 올바른 typed facts가 존재해도 모델의 잘못된 근거가 주된 설명으로 남는다.

`motion-studio.js:6,37`에는 이미 별도 승인 범위 안내와 승인 모션 버전 표시가 있다. 따라서 새 승인 절차나 별도 제품 영역보다 **기존 채팅/모션 상태 표시의 사실 출처를 통일**하는 것이 현 구조와 맞는다.

## 권장하는 가장 작은 변경

**기존 서버 projection → 작은 상태 영수증 → 기존 채팅의 결정적 표시**를 사용한다. 새 모델, 새 DB, MCP, 별도 endpoint/워크플로/승인 gate는 필요 없다.

1. `motion_context`가 계산한 사실을 사용하는 순수 receipt helper를 둔다. 전체 scene 대신 project/shot/version/관측 state revision, 승인 상태·scope·대상 hash, 조회 시 context match, pending proposal, `execution_check=not_run`만 전달한다. 사람이 읽는 문장은 이 코드/템플릿이 고정한다. 모델이 생성한 설명이나 fields를 receipt로 받아들이지 않는다.
2. 이 helper를 기존 `search_project_context` 결과와 기존 state 조회 projection에서 재사용한다. 새 API를 만들지 않는다. **과거 tool 영수증은 ‘그 조회 시점’**, 최신 state의 값은 ‘현재 상태’로 구분한다. 과거 grant를 현재 승인으로 다시 표시하지 않는다.
3. `drawModelChat`의 기존 카드에 “서버 확인 상태”를 우선 표시한다. 해당 motion receipt가 있는 답변의 승인/실행 상태 본문은 이 템플릿을 쓴다. 자유서술 원문은 삭제·교정하지 않고 별도 “모델 설명 · 검토 전” 영역에서 볼 수 있게 한다. 단순히 같은 문장 아래 면책문구를 붙이는 것으로 완료하지 않는다.
4. 창작 제안/이유 설명과 상태 판정을 분리한다. 새 광범위 intent 분류기나 문장 정규식으로 진위를 추정하지 않는다. 표시 분기는 **서버가 만든 typed receipt의 존재·종류**를 기준으로 한다. 버튼 enable/실행은 기존 서비스와 server gate를 그대로 사용한다.

현재 표본의 결정적 본문 예:

> 모션 구성 v1이 저장·적용돼 있습니다. 로컬 작업자가 이 버전의 모션 후보 렌더 범위를 승인했습니다. **조회 시 승인 대상과 현재 문맥은 일치했습니다.** 새 변경안은 미승인입니다. 실행 직전 장면·문맥·폰트 검사는 다시 수행됩니다. 이 승인은 최종 출력·납품 승인을 포함하지 않습니다.

타임라인 채택을 함께 표시할 경우 현재 timeline의 Take와 그 motion revision/scene provenance를 실제 비교해야 한다. 단순 `motion_head>0`이나 다른 버전 Take 선택으로 채택됐다고 표시하지 않는다. 이 범위를 즉시 구현하지 않으면 “타임라인 채택은 별도 상태”로 안내하고 기존 화면을 연결한다. **최종 납품 승인 전체 상태를 조회하지 않았다면 ‘별도/이 범위에 포함 안 됨’까지만 표시**한다.

이 대안은 MS-FR-05/06/11과 AT09/10/18의 서버 권한·승인 문맥 전달 의도, PLAN K.4의 구성/후보/최종출력 분리에 부합한다. receipt 표시가 grant 발급이나 실행 허용이 되는 것은 아니다. ontology를 승인 대신 사용하지 않되, **실제로 canonical/ontology 내용이 바뀌면 기존 context hash 검사는 계속 stale을 검출해야 한다.** 설명 문제를 고치려고 ontology를 context fingerprint에서 제거하면 안 된다.

프롬프트만 추가하는 안은 코드 변화가 작지만 이미 두 차례 설명 개선 뒤에도 남은 이 오류를 결정적으로 막지 못한다. 권장안은 서버의 상태 사실을 모델 문장이 대신하지 못하게 한다. 다만 자유서술의 일반 정확성 자체가 해결됐다고 주장하는 것은 아니다.

## 비유료 수용 기준

|사례|수용 결과|
|원래 최종 질문/오류 응답 replay|서버 상태 본문은 context match=true를 그대로 표시. 잘못된 ontology 근거는 상태 판정으로 채택하지 않음. 원 모델 답변·hash는 보존|
|ontology=null, 동일 context|승인 기록·조회 일치 표시. ‘ontology 없음’만으로 차단/미확인 판정하지 않음|
|실제 context 또는 ontology version 변경|stale_context, 현재 grant 핸들 없음. 이전 승인 기록은 이력으로만 표시|
|문맥은 같지만 font 변경|조회 일치와 실행 재검사 필요를 동시에 표시. 기존 렌더 서비스가 거절하며 job 추가 없음|
|승인 v1 + proposed/held/rejected v2|v1 기록과 v2 검토 상태 분리. v2 자동 승인/채택 없음|
|과거 receipt, reload, 늦은 응답, 다른 project/shot|관측 버전과 최신 상태 구분. 다른 문맥에 카드·grant·버튼 적용 안 됨. 서버 조회는 읽기만 수행|
|조작된 model output에 actor/grant/approved 입력|서버 receipt fields에 반영되지 않음. 가짜·이전·외부 scope 인수 거절 유지|
|scope=local-motion-candidate|후보 승인과 타임라인/최종출력/납품 승인 구분. 실행 사전검사 완료처럼 표시하지 않음|
|NM-Q02 혼합/단독/no-op/동일 shot 반복|서버 timeline_diff가 정확하고 기존 human apply·멱등성·원본 보존 유지|
|표시와 초안/키보드|기존 카드·접근 가능한 이름/영역 재사용, draft/selection/focus 보존. 현재 source 변경 후 Node fixture와 실제 지원 브라우저로 표본 확인|

위 receipt/UI는 **아직 구현되지 않아 NOT RUN**이다. 저장된 잘못된 응답과 fake 모델 응답으로 비유료 검증할 수 있다. 이 변경의 수용을 위해 또 실제 Claude 호출을 자동 추가할 필요는 없다. 향후 모델 자체 문장 품질을 주장할 때만 별도의 승인된 실제 표본을 요구한다.

## 기존 patch의 격리 검증

새 임시 snapshot/SQLite Store에서 **12/12 PASS**: 현행 quality 테스트10개 + 독립 control2개. [실행 로그](offline-tests.log), [결과](offline-tests.json), [실행기](run_offline.py).

- 승인 v1/pending v2 search·handoff, 무승인/거절/타작품 격리, stale context/버전/scene binding, actor/scope 인수 삽입, 가짜·이전 grant 거절 통과.
- 영수증이 reorder/caption/audio/clip-only/no-op/중복 occurrence를 정확히 계산하고 제안 저장을 apply/출력승인으로 승격하지 않음. 중복 요청은 같은 receipt, hold/reject/stale 경계 유지.
- 독립 control: **빈 ontology + 현재 일치=true**가 정상적으로 재현됨. 실제 ontology snapshot 변경은 stale, 현재 grant 없음. 읽기로 원본·job 변경 없음.
- 독립 control: context match=true여도 바뀐 font manifest에서는 기존 실행이 거절됨. pending 제안은 미승인, 생성 job0. 따라서 재검증 필요와 현재 문맥 일치는 동시에 참일 수 있다.

이번 patch로 자동 승인이나 다른 project 범위 누출이 생긴 반례는 검사 범위에서 발견하지 못했다. 전체403 회귀는 primary의 기록이며 독립 실행 개수에 합산하지 않았다. 문구 포함 여부 테스트 통과를 모델 의미 정확성 증거로 사용하지 않았다.

## 실제 증거·비용 보존

저장 응답6개의 visible output hash **6/6** 일치, 공개 입력 전체 재해시 **3/6** 가능. 나머지3개는 private thinking 제거 한계다. 입력37,240/출력4,789 tokens를 기록 단가로 다시 계산하면 이번 **$0.0061185**, 이전$0.0320001 포함 **$0.0381186**. 응답별 올림6,120 micro와 기록상 이전32,015를 합하면38,135 micro다. open held0은 제공된 provenance/manifest 기록이며 공유 원장·invoice는 읽지 않았다. [증거 대조](evidence-checks.json).

첫 기존 승인 답변은 저장구성과 타임라인 채택을 일부 혼동했고, 마지막 답변이 그 부분을 개선했다. NM-Q02의 실제 편집 답변은 before/after와 `changes=[]`의 clip-only 의미를 맞게 설명한다. 이전 영상·스크린샷 hash도 그대로다. 새 실제 렌더/브라우저 시험으로 재분류하지 않는다.

**종료 판정:** NM-Q02 표본/계약 PASS, NM-Q01 데이터 전달·권한 경계 PASS / 자유서술 설명 잔여 P2. deterministic receipt 대안은 현 구조에 적합하며 위 좁은 수용 기준으로 구현 검토 가능하다. 제품 소스 수정·키/.env/공유DB 접근·외부 호출·browser/listener·설치·업로드0. 동결본 읽기와 별도 QA 산출물만 작성했다.
