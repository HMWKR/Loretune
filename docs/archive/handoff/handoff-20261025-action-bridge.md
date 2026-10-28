## 최신 고정본 — Claude 영수증·provider bridge·구조 UI 통합

`docs/qa/provider-action-bridge-20261025/REPORT-ko.md`가 최신. Claude 후속실제Messages1/count1,5검증pass,$0.0004961추가/누적$0.0077580(billing미확인). provider action→기존FalKling/GenerationQueue/단일예약/Take lineage 연결,9contract tests. 최종235tests28.310s+AST/JS pass. 구조patch원본7426e52f…확인후통합,중복preview/작품전환/모바일결과패널회귀수정. 실제browser새작품→음원/계획→승인→mockTake→2초1080p음악/한국어자막MP4→reload완주. sourcefreeze HTMLbe3ff1634a396e378d320cb32020f94a9332e643d2128b5c92209af312ababf5,8773exec82301/revision59/providerdisabled. fixed-runtime.json 및ui/screenshots+MP4. 기존65338readback은이전backend이며최신수용서버아님. 새영상호출0/권한변경0. 이미지actualadapter/실billingreader/다중사용자운영/전체접근성은남음;fal403근본원인해결로포장금지.

## 2026-10-25 실제 일반 채팅 Claude 시험 완료 범위 / F07 수정

`docs/qa/claude-chat-ui-live-20261025/REPORT-ko.md`가 최신. 승인 연속성 추가 후 정식 재심사1회 허용. 실제 Claude UI2입력/count5/messages5, stage usage$0.0023044,누적$0.0072619(billing미확인). 실제 canon조회→plan595787d6…저장→UI승인→mock job e6b8a59e…/Take1→actualClaude최종조회. 최종답변에서plan연결부족을정직하게표시; plan_id/version/release projection보강은offline검증,추가live없음. 원actualserver61586종료, key없는readback65338(exec92169)와shared8773(exec88376) 최신source로재시작. HTML7426e52f…일치. F07실제JS지연fakefetch16pass,원4실패보존,브라우저복원/저장/프로젝트격리pass. 전체226tests26.018s,staticpass. 실제사용자데이터/새영상/배포없음. 최신sourcefreeze hashes는final-runtime.json. 남은externalbridge 및live영수증재확인명시.

## 2026-10-25 일반 채팅 실제 Claude 시험 gate — 실행 전 차단

새 보고서: `docs/qa/claude-chat-ui-live-20261025/REPORT-ko.md`. 서버 도구/토큰/단계 예산 제한 및 Take 영수증 조회 보강. 225 tests pass, AST/JS pass. 실제 시험 서버 시작은 auto-review에서 exact external authorization 부족 사유로 denied, 명령 미실행. 실제 신규 count/messages 0, stage 원장 0행, 누적 usage $0.0049575 유지. 새 승인 근거 전 동일/간접 실행 금지. 기존8773은 재시작하지 않아 백엔드는 이전 freeze. HTML은 불변.

# 최신 기능 통합 체크포인트 — 2026-10-25 11:40 UTC

B03 media-v1 승인 문맥, canonical asset claim 검사, 새 scoped Anthropic chat tool-loop/일반 UI, F05/F06 및 tool-trace disclosure 수정 **원본 통합 완료**. 최종221개 tests/25.556s 통과. source freeze `docs/qa/next-functional-patch-20261025/final-runtime.json`이 우선 기준. http://127.0.0.1:8773, 소유 exec session7905, 기존격리데이터 `/tmp/loretune-ms-qa-20261025` 유지. HTML hash `25860298244aa518ed322fdc38cb8f9875168fb6c31aa766bc21dc3e2435acd3` 실제응답/source 일치.

실제API호출·키조회·이번추가비용0. 새채팅UI는 contract-fake로 canonical조회→계획저장→final answer 및 B03 Take등록/재시작복원 확인. 실제Claude UI end-to-end는 not run, 기존대표live script결과와 구분. shared8773은 실제provider 미연결. 임시52901 서버는 검증후 종료, synthetic DB보존. 보고서/patch/baseline/test/UI증거는 `docs/qa/next-functional-patch-20261025/REPORT-ko.md`. 영상API만남은상태라고판정하지않음. 다음우선순위: scoped실제Claude UI소규모검증, 실제media action dispatch통합, grounded답변/접근성남은검증. 기존fal403재접근·추가생성없음.

---

# 실행 계약 연결 인계

## 디자인 통합 최신 고정본 — 2026-10-25T10:49:41Z

이번 턴 앱 변경은 index.html의 디자인 시스템/상단 wrapper/모바일 전체 모델명 표시뿐이다. backend 변경0. 최신 URL http://127.0.0.1:8773, 소유 exec session78045, 같은 격리 데이터. HTML GET/source SHA256 `cb810ea713f5865b7feecaaf510fc8d5851941216be78560bcb4ade3a6d576a3` 일치. 소스 다시 freeze 완료. `docs/qa/design-integration-20261025/frozen-runtime.json`과 `REPORT-ko.md`가 현재 우선 기준이다.

전체194개23.887초/targeted6개/JS static 통과. 실제1280px preview와320px 전체 모델명/사유·aria 연결,390px overflow0,Escape focus return 확인. 전체flow는 디자인 세션 후속. 실제 유료 호출0, 기존 비용원장 유지.

새 독립 B03을 다음 기능 작업으로 이월: chat-only 모델 설정 변경이 이미 승인된 media action을 snapshot hash 불일치로 blocked시킴. B01/B02 독립재검증 pass와 구분. `docs/qa/independent-action-bridge-recheck-20261025/REPORT.md`. 디자인 source freeze 해제 뒤 B03 + 일반 chat live bridge + asset rights claim integration 순서로 진행. 이번 턴 B03 수정 안 함.

## 고정 런타임 최신 체크포인트 — 2026-10-25 (이전 기록보다 우선)

- 앱 source freeze: 10:27:42Z. `docs/qa/action-grant-milestone-20261025/fixed-runtime.json`의 7개 소스 hash 모두 현재 일치. URL http://127.0.0.1:8773, 소유 exec session60587, 격리 데이터 `/tmp/loretune-ms-qa-20261025`. 디자인 재검증/새 patch 전 앱 source 변경을 멈춘 상태다. 이후 변경은 standalone 평가 scripts/tests/docs뿐이다.
- 전체194 tests/23.917초 pass: `frozen-app-evaluation-regression.log`. B01 새 action job 인계 누락과 B02 잘못된 action repair 미기록 수정/회귀 pass. 파일·테스트 경로와 해시는 `latest-evidence.json`, 상세는 `fixed-checkpoint-ko.md`.
- 사람용 보류/승인/철회/실행/후보 검토 UI 연결. 모의 단색 PNG임을 명시. 실제 브라우저에서 계획→승인→실행→Take 검토/선택→자막/음원 포함2초1080p MP4 완료. 산출물 `human-flow-output.*`, 캡처 `human-candidate-approved.png`, `human-output-completed.png`. 새 실제 영상 호출0.
- 실제 Claude canonical lookup→tool_result→곡 한정 예외 계획 저장→간결한 tool receipt→출처 포함 최종 답변 확인. 계획ID46d0aa5d81584c85874dee1b295d77dc. 실제 모델이 승인/생성/결제됐다고 주장하지 않음. 단, 일반 앱 채팅 transport 통합이 아니라 별도 synthetic 런처이다.
- Anthropic Messages8회/count9회, usage 계산누적$0.0049575, billing미확인. 마지막request req_011CgNp3zRkXojFjzqBCWFhs, input3294/output231, 계산$0.0004449. 전체$50 승인원장 유지. `docs/qa/claude-grounding-20261025/REPORT-ko.md`에 실패포함 전체분모/요청/한계.
- 최초 final input cap 차단은 Messages 미전송이라 unknown 아님. 계획 tool receipt의 중복 context를 줄여 다음 bounded final-answer1회 성공. 원응답 semantic_failed는 과도하게 엄격한 검증기 때문이어서 원기록을 보존하고 exact source 기반 offline-review7개 pass. API 재호출 없이 검사 수정.
- 남은 핵심: 일반 chat transport/UI와 실제 provider bridge, 새 action의 일반 asset rights lookup→claim(G01), live adversarial ontology/tool 평가, typed conflict/scope 품질, keyboard전체/실제zoom/screenreader, fal private 다운로드 외부 문제. API만 남았다고 선언하지 않는다. 외부 호출/키/권한/배포 제한은 계속 유지.

## 최신 상태 (아래 초기 기록보다 우선)

서버8773: 원래 소유 exec session44092에 Ctrl-C를 전달해 종료130을 확인했고, 정식 require_escalated 승인으로 동일 주소/데이터에 최신 서버 시작 성공. 새 exec session82419, http://127.0.0.1:8773. ps 거절 명령을 재실행하지 않았다. served-revision.json에 소스해시. 디자인 세션은 새로고침 후 최신 화면 검증 가능. 실제 캡처 재검증은 아직 미완료.

전체 HTTP 포함180개23.771초 통과(full-http-regression-final.log). 이후 응답검증실패/결과불명 상태분리 수정 및 회귀1개추가; Anthropic smoke targeted4개0.012초통과. 181개 전체를 실행했다고 주장하지 않는다.

Anthropic 승인 누적50USD로 확대. 작은 시험 count1회/messages1회 실행완료. 입력1283/출력2048, stop_reason max_tokens로 미완결. request req_011CgNn1N4CFqz2GQs6XFV8b, 비용계산0.0011523USD/실청구미확인, 검증적용0. 자세한 결과 docs/qa/anthropic-smoke-20261025/REPORT.md. 단기런처는 scripts/anthropic_smoke.py, usage.sqlite3가 시도기록·누적예산원장. 기존ID재실행금지. 새실험은 공식effort/출력한도검토와 새목적/견적/시도ID준비후이며 자동fallback금지.

## 초기 체크포인트 기록

현재 핵심 증거: docs/qa/action-grant-milestone-20261025/REPORT.md, full-http-regression.log. 최종 전체177개 통과,23.948초. source 변경: app.py, production_tools.py, action_execution.py,index.html,tests/test_action_tool_bridge.py. 기존 F01–F04/R01/R02 수정 보존. 실제 공급자/키 사용0.

채팅 tool→서버 scope→저장 plan/action/grant→단일 예약/job receipt 모의 경로 연결. 공개 state/UI 진행요약은 모의임을 명시. 사람용 grant/action 생성 화면, 실제 provider dispatch는 아직 미완료. 자동으로 가짜 모델을 활성 registry로 등록하지 않았다.

사용자는 최신 검증 서버 재시작/127.0.0.1 HTTP 시험과 Anthropic 합성 structured extraction 1회+count_tokens, 총0.01USD를 승인했다. HTTP 전체 시험은 require_escalated 성공. 8773은 여전히 기존서버이며 lsof PID33482. 프로세스 상세확인 ps 명령은 operation not permitted 거절, 반복/종료/재시작 안 함. exec session44092는 과거 시작 세션 식별자, 현재 소유권/상태 재확인 필요. 그 외 서버를 건드리지 않는다.

Anthropic 공식 가격 재확인: claude-haiku-5-5 입력0.10/MTok,출력0.50/MTok(100k이하), 승인4096/2048 기준0.0014336USD. 합성 sources는 docs/qa/mvp-flow-audit-20261025/anthropic-approval-proposal.md 그대로. 기존 Anthropic_KEY 메모리 인증만. 현재 anthropic_ontology.BoundedMessagesTransport는 Messages만 허용하고 count_tokens를 지원하지 않음. Kling전용 live_launcher.parse_key는 대문자 전용 정규식이므로 그대로재사용하면 Anthropic_KEY 거절됨. 안전한 별도일회성 런처/카운트계약/실행기록 fixture시험후 실행할 것. 실제.env를 현재읽지않았고 실인증전송0. outcome불명확시재시도금지. 모델fallback/추가Kling/권한변경/배포승인없음.

사용자가 개발모델 gpt-6-astra/xhigh 지정. 현재 도구에서 실행모델 메타데이터는 독립확인 불가, 적용됐다고 증명하지 않았다.
