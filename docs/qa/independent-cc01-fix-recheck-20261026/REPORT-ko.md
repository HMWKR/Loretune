# CC01 독립 재검증 — 2026-10-26

## 판정 먼저

**원 CC01은 검사 범위에서 닫을 수 있다.** 원래 “첫 제약 요청 + 중립 8턴 + Store 재열기” 반례를 기존 독립 스크립트의 같은 함수로 실행했고, 첫 요청이 새 provider body까지 보존됨을 확인했다. 현재 canonical correction/provenance·프로젝트 격리 독립 probe도 PASS다. 단, 새 byte 상한의 **미전송 오류를 outcome_unknown으로 오분류하는 P2(CC02)**가 재현됐다. 실제 과금 누출이 아니라 사용하지 않은 예약과 프로젝트 대화를 잠그는 복구 문제다.

|검증|독립 결과|근거 한계|
|---|---|---|
|원 CC01·canonical/provenance/isolation 기존 독립 probe|2/2 PASS|fake response로 앱 문맥 계약 검증. 실제 Claude 품질 증거와 별개|
|요청 이력7 + 관련 runtime guard6 + fake transport12|25/25 PASS|선택된 snapshot 단위 시험. 전체358 또는 실제 HTTP를 재실행/주장하지 않음|
|64KiB 바로 아래/위 control|2개 기대 동작|허용 count fixture + fake opener, 실제 tokenization 아님|
|count 허용·Messages byte 초과 경계|**FAIL, P2 CC02**|Messages opener0에도 unknown/예약유지|
|저장 live 기록|14 request ID와 출력/usage 연결 일치|새 API 확인·invoice 확인 아님; 입력 원문 재계산 제한 아래 명시|
|실제 Claude authored prompt→fake fal payload|2개 동일|실제 fal 생성·다운로드·영상 품질은 미검증|

## CC02 — P2: Messages 미전송을 불명 제출로 기록해 대화/예약 잠금

**재현:** `python3 docs/qa/independent-cc01-fix-recheck-20261026/run_offline.py`. 스크립트는 고정 snapshot을 import하고 임시 synthetic Store/journal만 만든다. socket connect/bind는 차단한다. provider key는 하드코딩된 synthetic canary이고 fake opener만 사용한다. source는 수정하지 않는다.

41개의 과거 요청(각 2,000자 이하)을 준비하고 경계 길이의 첫 요청을 조정했다. fake count는 승인 범위의 12,000 tokens를 반환한다. approval input16,384/output8,192를 사용했다. 실제 토큰 수나 Claude 동작을 측정한 시험은 아니다.

- count 직렬화 **65,529 bytes**, count opener1회.
- Messages 직렬화 **65,549 bytes**, 상한65,536을 초과. **Messages opener0회**.
- 기대: definite local not-submitted → `blocked_before_message`, 사용하지 않은 예약0, 후속 접수 가능.
- 실제: `outcome_unknown`, `held_micro=5735`, `actual_micro=null`, 후속 접수 차단.
- control: message65,510 bytes는 completed와 actual60으로 정산(보수적 held가 남아도 budget은 actual을 사용); count65,570 bytes는 양쪽 opener0, blocked_before_message/held0/후속 접수 가능.

**원인 파일:** `chat_runtime.py:85`의 count는 max_tokens를 제거하지만 complete는 유지한다. `chat_runtime.py:198`은 complete 호출 전에 submitted=True를 기록한다. `anthropic_ontology.py:172–173`은 byte 초과를 opener 전에 거절한다. adapter는 이 확정 미전송을 일반 오류로 가리고(`chat_runtime.py:83`), runtime은 unknown으로 보존한다(`chat_runtime.py:224–226`). `chat_runtime.py:150`은 unknown이 있는 프로젝트의 다음 요청을 막는다.

**영향:** 경계 길이의 이력이 있는 승인된 합성 대화에서 실제 Messages 요청 없이 예약과 대화가 잠긴다. 원 CC01의 silent context drop이 재발한 것은 아니다. 실제 청구/외부 전송/권한 상승은 관찰하지 않았다.

**최소 수정 제안:** full Messages envelope를 같은 serializer/byte 상한으로 count 전에 preflight하거나, 확정 before-send 거절만 별도 typed outcome으로 전달한다. 해당 경우만 미사용 예약 해제·blocked_before_message 처리한다. 모든 adapter exception을 release하면 실제 unknown 비용이 유출되므로 timeout/전송불명 예약은 유지해야 한다. `byte-boundary-evidence.json`, `offline-results.json`에 실제값을 보존했다. 관련 계약은 MS-FR11/MS-AT18 문맥 지속과 bounded submission/unknown 복구 경계이며 새로운 FR 번호를 만들지 않았다.

## CC01 수정의 정확한 범위

- `chat_runtime.py:147`에서 project 필터와 rowid 순서를 고정하고, `47–58`에서 요청 원문/turn ID/sequence/hash/status/workspace/project/project-default/digest를 만든다. 최근 완료8턴과 별도 채널로 전달(`157–160`)하므로 원래 누락은 해결됐다.
- cancelled/failed 원문은 처리 상태를 붙인 요청 증거이며 완료행동/승인 사실이 아니다. assistant 답변은 이 요청 이력에 섞이지 않는다. 최근 assistant 답변은 unreviewed다. 수정·해제·인용·조건문은 순서대로 유지하고 자동 canonical/active constraint로 승격하지 않는다.
- 현재 canonical revision2가 이전 assistant 서술보다 우선되는 payload, stable entity/relation, source provenance, historic version 보존, A/B canary 제외를 기존 독립 probe로 확인했다.
- prepare 시 handoff는 저장 snapshot이며 사후 이력 변경을 소급 반영하지 않는다. context 변경은 제출 전 guard로 차단한다. max_input 초과는 Messages0/예약해제, max_tokens 응답은 유료 invalid response, 실제 제출 여부 불명 timeout은 예약유지·자동재시도 없음으로 관련 control 통과.
- 전체 이력을 유지하므로 무한 문맥은 아니다. byte/token 상한에 도달하면 중단한다. 독립 세션 ID/새 세션 UI는 여전히 없고 `project-default` 단위다. 자연어 수정·범위·충돌을 결정적으로 해결하는 엔진이나 자동 요약도 없다. 이 한계들은 primary 보고서에서 명시돼 있다.

## 저장된 실제 Claude 증거 독립 검산

`check_saved_evidence.py`로 원본 evidence JSON만 읽었다. 실제 journal DB와 credential/auth/env 파일은 열지 않았다. 기록을 다시 공급자에게 조회하지 않았으므로 원격 진위의 독립 인증 또는 invoice 증명으로 표현하지 않는다.

- 고유 request ID14개. 입력94,603/output10,547. 기록된 표준 단가로 **$0.0147338**, 이전 기록$0.0077580을 더해 **$0.0224918**를 재계산했다. 현재 가격을 외부로 새 조회하지 않았다. invoice/실청구는 미확인이다. 원장 보수적 합계$0.022503은 DB를 열지 않아 이번 독립 검산 대상으로 삼지 않았다.
- visible output hash14/14 일치, provenance↔turn↔saved request의 recorded input hash 연결14/14 일치.
- public body에서 원 input hash/byte를 직접 재계산할 수 있는 것은 **6/14**. 나머지8개는 Recorder가 후속 요청의 prior thinking/redacted_thinking을 제거한 뒤 public_request만 저장한다(`scripts/cc01_context_trial.py:87–94`). 원 hash와 byte는 제거 전 값이다. 따라서 이8개의 원 전송 본문은 보존 증거만으로 독립 재구성 불가. 이는 개인정보/추론 비저장 설계와 일치하며 변조 발견으로 분류하지 않는다. 개선 가능 사항은 `public_request_sha256`, `public_request_bytes`, redaction 종류를 별도 저장하여 두 계층을 명시하는 것이다. private reasoning을 저장할 필요는 없다.
- L1의 오래된 금지·dolly, L2의 orbit 해제/교체·인용과 조건문 제외, L3의 violet/source-v2와 unknown age, L4의 B-only 문맥은 실제 저장 답변과 tool input에서 확인했다. 단순 단어 포함 여부만으로 품질을 판정하지 않았다.
- L1/L2 원곡과 generate_audio 혼동, L3 grant 의미 오류, L4 빈 shot 목록을 ontology 승인 부재로 해석한 오류가 실제로 있다. primary는 이를 실패로 숨기지 않았고 S1/S2에 semantic rules가 포함된 새 요청과 정정 답변이 보존돼 있다. S1은 scoped grant/current execution/final output을 분리하고 S2는 canonical revision과 shot inventory를 분리한다. **두 좁은 후속 질문에서 개선 확인**이며 동일 초기 prompt 전체 재실행이나 모든 대화 품질 보장은 아니다.
- 모델의 두 `prepare_video_action` prompt → 저장 action input → fake fal payload/transport가 byte 수준 문자열 동일하고, 모델 id도 fal-kling-2-5-turbo로 같다. wrong grant blocked 및 duplicate same job evidence 일치. actual Claude 기록과 fake fal transport를 구분한다. 후속 count JSON의 before/after 동등성은 확인했지만 사용자 DB를 열어 부작용 전체를 재검증한 것은 아니다.

## 고정 파일·실행 제약

제품 3개 hash는 primary FINAL-MANIFEST와 같다.

- chat_runtime.py `bd47f1779e9c210064e396773bf8d03fce558c8a3f8e27be46d3a587ecd0a8cd`
- chat_models.py `d34e013bbb4e42329213076884eaaa1364d86c4080915d6b64b1afb2c7c730c8`
- anthropic_ontology.py `952159519d939e2ef4f156b415a737d0199b95130cca8272b120eeee18c61fdf`

`snapshot-manifest.json`에 snapshot 경로·mtime·hash, `final-integrity.json`에 종료 시 source 불변 및 primary manifest 비교를 기록했다. UI hash도 primary 기록과 일치하지만 브라우저 검증은 하지 않았다. `original_probes.py`는 이전 독립 probe의 함수는 그대로 두고 import snapshot 위치와 선택 실행만 바꿨다. 초기 증거 검산은 redaction 전 hash를 public body와 같다고 가정해 멈췄고, Recorder source 확인 후 검산을 두 층으로 분리했다. 이를 제품 실패로 세지 않았다.

이번 감사에서 liveAPI/CLI inference/REA/browser/listener/upload/secret/shared DB 접근은 **0**. 작성은 새 QA 폴더와 임시 snapshot/fixture뿐이다. 차단된 승인 행동은 없으며, 남은 actionable 항목은 위 P2 CC02다. 제품 수정은 primary 담당이다.
