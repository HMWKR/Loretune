# Aethon CC02 — 최종 Messages 본문 사전검사 수정

2026-10-26 15:22 UTC 소스 고정. **CC02/P2를 수정했고 전체365/365 회귀가 통과했다.** 실제 API 호출·키 조회·공유 DB 변경·모션 구현은0이다. [독립 원 감사](../independent-cc01-fix-recheck-20261026/REPORT-ko.md)는 변경하지 않았다.

## 결함과 최소 수정

count_tokens 요청은 `max_tokens`가 없어65,529bytes로 상한65,536 아래였지만, 실제 Messages는65,549bytes였다. 기존 런타임은 Messages의 로컬 byte 검사가 일어나기 전에 `submitted=True`로 표시했다. 따라서 실제 전송0이어도 결과 불명으로 남고5,735µUSD 예약 및 다음 대화 차단이 유지됐다. **실제 청구 누출이 아니라 미전송 요청의 상태·예약 오류**다.

- `anthropic_ontology.py:158` — 기존 UTF-8 JSON 직렬화와 크기 검사를 순수 `encode_body`로 분리했다. 실제 POST도 같은 함수를 사용하므로 count 본문이나 문자 수를 대신 검사하지 않는다. 상한/endpoint/redirect/timeout/응답 검사는 그대로다.
- `chat_runtime.py:71` — Anthropic adapter가 최종 Messages 전체 본문을 transport의 동일 검사로 검증한다. 검사 자체는 credential supplier나 네트워크를 호출하지 않는다. 주입된 fixture transport에는 기본 채팅 상한을 적용한다.
- `chat_runtime.py:200` — 각 round의 예약 후 `preflight_started → count_started → message_started` 순서다. 알려진 로컬 거절은 기존 `blocked_before_message` 경로로 해당 attempt의 예약만 반환한다. 실제 전송을 시도한 뒤 응답이 불명확한 경우의 예약/중복방지는 해제하지 않는다.
- `tests/test_chat_preflight.py` — 격리 Store와 fake HTTP로7개 회귀를 추가했다. 기존 원장/unknown 기록을 일괄 수정하는 복구나 자동 재시도는 추가하지 않았다.

제품 수정은 위2파일뿐이다. [runtime diff](chat_runtime.py.diff), [transport diff](anthropic_ontology.py.diff), [수정 전 사본](before/), [최종 해시](FINAL-MANIFEST.json).

## 전후 결과

[같은 재현 실행기](reproduce.py)는 socket connect/bind를 금지하고 현재 모듈 또는 보존한 수정 전2모듈을 로드한다. 원 감사 파일을 수정하지 않았다. [수정 전 수치](before-evidence.json), [수정 후 수치](after-evidence.json).

|조건|수정 전|수정 후|
|---|---|---|
|원 반례: count65,529 / Messages65,549bytes|fake count1, Messages0; outcome_unknown, held5,735, 다음 대화 차단|count0/ Messages0/ supplier0; blocked_before_message, held0, 새 명시 요청 가능|
|Messages 정확히65,536bytes|fake 정상 완료|같은 정확한 UTF-8 본문으로 fake 정상 완료|
|Messages65,537bytes|미전송인데 unknown|사전 차단·예약0·count/ Messages0|
|count 네트워크 timeout|Messages0, 예약0|동일. count1회만, 자동 retry0|
|Messages 네트워크 timeout|unknown·held5,735·새 enqueue 차단|동일. Messages1회만, 자동 retry0|
|별도 unknown 예약1,234µUSD 존재|해당 예약 유지; 새 미전송 예약도 잘못 유지|별도 예약1,234 유지, 새 거절 attempt만0|
|첫 응답의 계획 저장 후 다음 round 크기 초과|기존 완료 응답/도구 결과 보존|그대로 보존, 뒤 거절 round만 해제. 이미 완료한 응답을 무료로 처리하지 않음|

표의 사용량과60µUSD 완료 비용은 **fake 응답 fixture**이며 실제 Anthropic 청구가 아니다. 새 명시 요청을 허용한다는 것은 이전 실패를 자동 재전송한다는 뜻이 아니다.

## 실행한 검사

|검사|실제 결과|증거|
|---|---|---|
|새7조건, 수정 전|4통과/3실패|[before-regression.log](before-regression.log)|
|새7조건 + CC01/기존chat/transport|44/44 통과; 새7조건도 모두 통과|[targeted-regression.log](targeted-regression.log)|
|전체 기존+신규 suite|**365/365,45.039초**, 한 실행.345비HTTP+20HTTP|[full-regression.log](full-regression.log)|
|Python AST|변경2제품파일+새test 통과|[static-checks.json](static-checks.json)|

새7개와 관련44개는 전체365에 포함되므로 합산하지 않는다. CC01의 원9턴/재열기/정정·해제·격리·상한 보호, 기존 unknown/중복/취소/도구 승인과 미디어 회귀도 전체에 포함된다. Python3.15.0, macOS26.5.1 arm64에서 실행했다. 전체 suite는 승인된 정식 `require_escalated` 경로를 사용했으며 HTTP는 임시 localhost/격리 데이터다. 실행 프로세스는 종료됐고 테스트의 shutdown/server_close/temporary-directory cleanup을 수행했다. 제품 서버는 시작·재시작하지 않았다. 로그의 로컬 날짜와 manifest의 UTC는 시간대가 다를 수 있다.

## 보존·범위·다음 단계

`chat_models.py`, `chat_protocols.py`, `app.py`, `index.html`, `studio.css`, `studio-media.js` 해시는 앞선 CC01 기준과 같다. UI 새 브라우저 검증은 수행하지 않았고 필요 없는 live 시험도 반복하지 않았다. 새로운 source는 [FINAL-MANIFEST](FINAL-MANIFEST.json)의 고정값을 사용한다.

- chat_runtime SHA256: `50ec18343dc4619aa2df8a5ffda7008a0a96c6bef71917c805c482700a51c54a`
- anthropic_ontology SHA256: `e7021df88da62058a746b370f6eca26aa26f45012a3ae7a2195c3cea2be6d0f0`
- HTML 유지: `d82ca93a64f31e71bf0c469b1b72b7c59c6a4bbe0403b969881349d8ec82f6e2`

이번 실제 provider0이므로 앞선 누적 usage가격 **$0.0224918**, 보수 원장 **$0.022503**, invoice미확인 상태가 유지된다. 앞선14개 output hash/usage는 독립 확인됐지만 **전체 원 입력 재해시는6개만 가능하고8개는 thinking redaction 제한**이 있다. 새 코드 통과로 그 증거 한계를 제거했다고 하지 않는다.

모션은 [단일 PLAN K.4/K.5](../codex-cli-assessment-20261026/PLAN-ko.md)에만 준비했다. 설치된 Swift/CoreText/CoreGraphics의 한글1프레임 capability부터 확인하고, 제한된 scene/keyframes→사람 승인→신뢰된 로컬 renderer→새 미채택 Take→기존 음악/자막 출력으로 연결하는 최소안이다. FFmpeg9.0.2는 있지만 drawtext가 없어 FFmpeg 단독 한글 렌더를 약속하지 않는다. Swift/SDK/font 존재는 확인했지만 컴파일·glyph 렌더는 아직 미검증이다. 실제 Claude 저작/수정은 그 gate 후 별도 단계다. 모델의 컷 순서·자막·원음 시작점 제안 확장은 같은 기존 timeline 승인서비스를 재사용하는 별도 묶음이다. 모션·신규 ingestion/ontology진화·Blender 구현은 이번에 하지 않았다.

현재 CC02 수정·로컬 회귀의 실행 blocker는 없다. 이미 거절된 CLI/REA 소스검토·Library 쓰기는 재시도하지 않았고, 외부 모델/영상403/배포 gate는 이 수정으로 해결됐다고 주장하지 않는다.
