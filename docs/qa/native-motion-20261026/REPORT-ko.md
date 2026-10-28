# Aethon — 제한된 네이티브 모션·모델 편집 구현 결과

## 최신 표시 후속 — NM-Q01 서버 영수증, 2026-10-26 19:34 UTC

모델 원문은 그대로 보존하고, 서버 승인 사실을 별도로 표시했다. 현재/과거 조회·true/false/null 일치·미적용 제안·실행 전 재검사를 구분한다. **승인 사실 표시의 결정성 검증 완료이며 모델 문장 오류 없음이라는 판정은 아니다.** 전체410/410(390비HTTP+20HTTP), 기존6응답 fixture 재생, 실제 served1920/1280·초안·포커스·재열기 통과. 추가Claude/fal0, 누적usage$0.0381186/실청구미확인 유지. [현재 상세 보고서](server-receipt-ui/REPORT-ko.md), [현재 manifest](RECEIPT-MANIFEST.json). 아래19:05 및 이전 결과는 해당 시점의 역사적 근거다.

## 이전 품질 후속 — NM-Q01/NM-Q02, 2026-10-26 19:05 UTC

독립 감사의 두 P2를 좁게 수정했다. **승인 기록의 전달과 편집 영수증의 결정적 차이 계산은 회귀를 통과했다. 실제 Claude는 기존 승인·새 제안과 편집 before/after를 구별했으나, 실행 가능성 설명의 불필요한 온톨로지 근거는 아직 남는다.** NM-Q01의 모든 문장 품질을 통과로 닫지 않는다. [현재 source/test/provider manifest](QUALITY-MANIFEST.json), [표본별 판정](quality-fix/quality-evaluation.json), [실제 요청·비용 근거](quality-fix/live-provenance.json).

|수정|실제 범위|보존한 경계|
|---|---|---|
|`production_context.py`|현재 작품·샷의 저장된 모션 승인 id/actor/scope/revision/scene hash, 문맥 일치 여부와 재검사 필요를 읽기 전용 전달. 제안/보류/거절은 별도 목록|미승인/다른작품/잘못된 binding에 승인 생성 없음. 오래된 문맥은 현재 grant 핸들 없음. 실행 서비스와 권한 생성 로직은 그대로|
|`chat_models.py` SYSTEM|모션 구성의 저장·적용, 타임라인 채택, 새 제안, 온톨로지와 최종 납품 승인의 의미를 구별|모델이 승인하거나 실행을 확정할 권한을 추가하지 않음|
|`local_creation_tools.py`|기존 `changes` 유지 + `changes_scope=clip_take_trim_duration`. 기준/제안 timeline의 `timeline_diff`로 컷 occurrence 순서·컷 속성·자막·음원 version/offset before/after 계산|모델 설명문을 diff로 복사하지 않음. 무변경은 changed=false이며 불필요한 원문 반복 없음. 원본/승인/자동apply 불변|

신규10검사는 승인v1+대기v2의 search/handoff 동일성, 무승인·타작품·오래된context/버전/scene, actor/scope 인수 주입 및 가짜·이전 grant 차단, 순서/자막/음원 단독·혼합·no-op·동명 occurrence, 중복영수증, hold/reject/stale와 적용/출력승인 분리를 확인한다. 보존한 수정 전 소스에서는 핵심2반례가 실패했고, 수정 후10/10 통과했다. 마지막 지침 수정 후 관련27/27, **최종403/403 = 383비HTTP+20HTTP**,57.951초 및 Python AST 통과. 중첩 조건/관련27개는403에 다시 더하지 않는다. [반례 이전](quality-fix/before-counterexamples.log), [신규검사](quality-fix/targeted.log), [관련검사](quality-fix/final-focused-corrected.log), [전체](quality-fix/final-full-regression.log).

### 실제 Claude 판정 — 6응답 한도 사용 후 종료

1. 기존 승인 조회는 실제 model tool-use→server search→tool-result→최종 답변의2응답이었다. local-owner / local-motion-candidate / revision1과 새 제안 미승인을 정확히 설명했다. 다만 “적용 기록 없음”이라고 타임라인 채택과 모션 적용을 혼동했다.
2. 편집은 실제 search→propose_timeline_changes→최종 답변의3응답이었다. `0,1,2 → 2,0,1`, 수정 전 자막→시작/움직임/완성, 원음버전1 유지·offset0→1, 컷 Take/trim/duration 불변을 정확히 설명했다. `changes=[]`를 전체 변경 없음으로 읽지 않았으며 적용·출력승인 전 상태임을 밝혔다. [실제 편집 답변](quality-fix/live/case-2/turn.json).
3. 모션 적용/채택 차이를 SYSTEM에 명시한 뒤 마지막1응답으로 좁게 확인했다. 이때 **서버가 실제 scoped search를 먼저 호출한 영수증**을 제공했다. 모델이 새 도구 roundtrip을 선택한 시험은 아니다. 저장된 모션v1 적용과 타임라인 미채택, 새 제안 미승인, 후보렌더에 Take/음원이 필수는 아님을 올바르게 구별했다. [마지막 답변·입출력 hash](quality-fix/live/final-clarification/result.json).

**남은 정확성 한계:** 마지막 답변은 실행 전 재검사가 필요하다는 결론은 맞지만, `matches_current_context=true`인 조회에 대해 온톨로지/snapshot/sources가 비어 있다는 사실을 “현재 맥락 일치를 알 수 없음”의 추가 근거로 들었다. 최종 납품 승인 설명에도 관련 없는 ontology 상태를 덧붙였다. 이 문장들을 정확한 설명으로 채점하지 않았다. 실제 권한·현재 문맥 검사는 서버가 수행하며 모델 문장 때문에 우회되지 않는다. 최대6응답을 모두 사용했으므로 추가 반복/모델교체/손수 답변 교정은 하지 않았다. **NM-Q02는 이 실제 표본에서 통과, NM-Q01은 핵심 승인 구분 개선 확인·설명 근거 일부 잔여**다.

이번 추가 usage 가격 **$0.0061185**, 이전$0.0320001, 누적 **$0.0381186**. 응답별 micro 올림 원장은 이번$0.006120/누적$0.038135, 열린 예약0. 실청구는 미확인이다. [공식 Haiku5.5 가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview)을 재확인했고 입력16,384/출력8,192, 최대6응답의 보수 상한$0.0344064, 별도 stage$0.10·누적$50로 제한했다. 기존9응답 stage는 종료 그대로 두고 새 stage `native-motion-quality-20261026`을 같은 원자 누적 원장에 분리했다. 자동retry/fallback0, 실제fal0, 새영상렌더0. 첫5응답과 마지막1응답의 SYSTEM 차이를 구분한다.

6출력 hash 검증, 전체 공개 입력 재해시3/6; 나머지3개는 provider private thinking redaction 제한이다. 합성 데이터만 사용했으며 실제 키/인증헤더/오류원문을 기록하지 않았다. 실제 모델이 작성한 이전 모션 scene/MP4를 시험용으로 재사용했으므로 이번 시험을 신규 모션 저작이나 신규 렌더라고 부르지 않는다.

### 보존·실패 이력·동결

연결 해제 시 프로세스 생성이 실패했고 로그/원장 확인으로 해당 명령 미실행·추가API0을 확인한 뒤 재연결해 재개했다. 최초 오프라인 harness는 `chat_connection`/`chat_turns`라는 조회용 파생 필드를 사용자자료 변경으로 오인해 중단했다. 실제 source/승인 자료는 같았고 이 비교 범위만 교정했다. 별도 focused 실행2개의 import 경로 오류는 `PYTHONPATH=.:tests`로 고쳤다. 이전 실패 로그는 보존하고 제품 결함과 구분한다.

제품 변경은 위3개 Python 파일뿐이며, `tests/test_native_motion_quality.py`와 제한된 시험 실행기2개를 추가했다. **HTML/CSS/JS와 승인 생성·실행 서비스는 불변**이므로 새 브라우저/서버/캡처를 만들지 않았다. 이전1920/1280 화면은 UI 동일 빌드의 증거로 유지하지만 새로운 모델 답변을 브라우저에서 검증한 증거는 아니다. 두 live 실행과 전체 회귀 프로세스는 종료됐으며 HTTP 시험의 임시 서버는 정상 정리됐다. 기존 영상3개/스크린샷/SQLite 보존본 hash도 모두 일치했다.

신규 ingestion/자동 온톨로지 진화·Blender는 계획 전용이다. 새 의존성/credential/권한 변경/배포/업로드/사용자 canonical DB 변경은 없다. 이전 Mac 렌더러·다른모델·실제fal·접근성 coverage 한계는 아래와 같이 유지한다.

## 현행 결과 — 실제 Claude와 로컬 웹 UI 후속 검증

> 아래는 앞선18:36 동결본 결과다. 실행·브라우저 증거는 보존하며, 이후 NM-Q01/NM-Q02와 누적비용·최종 소스는 위 최신 품질 후속을 따른다.

2026-10-26 UTC. **실제 Claude가 모션 구성과 수정안을 작성하고, 서버 검증·사람 역할의 승인 경로를 거쳐 로컬 영상으로 출력하는 3개 실행 표본을 완료했다.** 영상 인코딩은 신뢰된 Aethon 렌더러가 수행한다. 임의 모델 코드를 실행하지 않았고, fal 유료 생성은0회다. 모델 답변의 승인 상태 설명에는 아래 잔여 문제가 있어 전체 품질 통과로 판정하지 않는다.

- [실제 Claude 모션 원본 MP4](artifacts/claude-motion-v1.mp4), [원만12프레임 지연한 MP4](artifacts/claude-motion-v2.mp4): 각4초,1920×1080,24fps,96프레임.
- [실제 Claude 편집 제안에서 나온 음악·한국어 자막 MP4](artifacts/claude-edited-audio-captions.mp4): 3초,자막은 선택형 트랙.
- [최종1920 앱 화면](browser-followup/motion-final-1920.jpg), [최종1280 앱 화면](browser-followup/motion-preview-1280.jpg): 현재 source와 일치하는 served 앱에서 촬영하고 저장된 픽셀을 확인했다.
- [최종 소스·served·자산·정리 manifest](FOLLOWUP-MANIFEST.json), [실제 요청/usage/hash 근거](live-provenance.json), [전체393 회귀 로그](browser-followup/final-regression.log).

### count 실패 진단과 수정 근거

기존 진단 패치는 base hash 일치를 확인한 뒤 적용했다. stage, 제한된 오류 범주, 유효 HTTP status, 검증된 request ID만 남기며 오류 응답 본문·인증 헤더·키는 기록하지 않는다. 진단29검사 통과 후, 앞선 Messages 미전송 시도와 구분한 사전 count1회를 수행했다. **HTTP400 / Messages0 / 예약0**을 확인했다. request ID는 `req_011CgRJvbES8e4ihJ1FgZ9W1`이며 [진단 결과](count-followup/result.json)를 보존한다.

오프라인 대조에서 count envelope는 이미 `max_tokens`를 제외하고 있었다. 새 motion strict tool schema에는 `minimum`/`maximum`/`maxItems` 등 공식 structured-output 부분집합이 지원하지 않는 제약이 남아 있었다. `chat_models.py`의 Anthropic 전송용 schema에서만 해당 제약을 설명문으로 옮겼다. **서버 원본 schema와 결정적 범위 검사는 유지**하고 `strict:true`도 유지한다. 같은 이름의 일반 property를 schema keyword로 오인하지 않도록 회귀를 추가했다. 다른 공급자 schema는 바꾸지 않았다. [공식 JSON Schema 제한과 SDK 변환 방식](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [count 계약](https://platform.claude.com/docs/en/api/messages/count_tokens).

수정 후31개 관련 검사가 통과했고, 명시적으로 구분한 수정 시험에서 count9회와 Messages9회가 성공했다. 이는 **문서상 계약 차이와 수정 후 성공**의 증거다. 오류 원문을 수집하지 않았으므로 최초400의 특정 필드 원인을 공급자가 확정했다고 쓰지 않는다. count는 schema compile을 수행하지 않으므로 compile 실패라고도 단정하지 않는다. 이전 실패 marker/원장행은 지우지 않았으며 불명 결과 재시도·자동 fallback은0이다.

### 실제 모델 실행과 품질을 분리한 결과

|표본|실제로 작성·실행한 내용|판정/근거|
|---|---|---|
|1 모션 저작|Claude가 한국어 “새로운 리듬”, 사각형, 원의 scene/keyframes 작성 → 저장 제안 → 승인 →96프레임 렌더 → 미선택 Take → 재열기|실행 PASS. [case1](live-schema-corrected/case-1/turn.json), [render](live-schema-corrected/case-1/render.json)|
|2 제한 수정|원의 진입/종료와 모든 keyframe을 정확히12프레임 지연. 다른 레이어·문구·색·원본 hash 보존. 승인/렌더/재열기, 복원은 새v3|실행 PASS. [case2](live-schema-corrected/case-2/turn.json). **최종 답변의 승인 상태 설명은 미흡**|
|3 모델 지시 편집|3→1→2 순서, 시작/움직임/완성 자막0–1/1–2/2–3초, 같은 원곡의 source offset1초 → 사람 apply/출력승인 →3초 MP4 → 재열기|실행 PASS. [case3](live-schema-corrected/case-3/turn.json). 결과 영수증의 차이 요약은 개선 여지|

위 승인 단계는 모델이 스스로 권한을 얻은 것이 아니라 격리 시험 제어기가 기존 human-role 승인 서비스를 호출한 것이다. 아래 브라우저 검증에서는 같은 승인·보류·거절·복원 조작을 실제 UI로 따로 확인했다. 실제 Claude 요청은 시험 실행기에서 발생했으며, 브라우저에서 새 Claude 응답을 생성했다는 뜻은 아니다.

**남은 답변 품질:** case2 최종 문장은 이미 승인된 모션의 승인을 확인하지 못했다고 설명했다. 서버의 승인과 `grant_id`는 존재하지만 모델에 주는 읽기 문맥에는 승인 종류/주체/범위가 충분히 설명되지 않는다. case3에서는 `changes=[]`를 보고 상세 차이를 확인할 수 없다고 했으나, commands와 제안 timeline 및 실제 적용값은 정확했다. 현재 영수증의 변화 요약이 legacy clip diff 중심인 한계를 드러낸다. 둘 다 실제 저장·권한 검사의 우회는 아니며, 이 시험은 **실행3/3 통과와 최종 설명 일부 미흡**으로 기록한다. 이미9응답 상한을 사용했으므로 추가 호출·손수 답변 수정으로 성공을 꾸미지 않았다. 다음 좁은 개선 대상은 승인 종류/버전/범위의 읽기 문맥과 편집 영수증 요약이다.

### 비용·출처·미디어 검증

모델은 `claude-haiku-5-5`, 요청당 입력16,384/출력8,192 상한, 총9 Messages, stage$0.075·증분$1·누적$50 이하로 제한했다. [공식 가격](https://platform.claude.com/docs/en/models/haiku-5-5/overview)의100k 이하 입력$0.10/MTok·출력$0.50/MTok로 실제 usage를 계산했다. 이번 **$0.0095083**, 이전$0.0224918, 누적 **$0.0320001**이다. 보수적 원장은$0.032015, 이번 unresolved held reservation은0이다. **invoice 실청구는 확인하지 않았다.** count 진단과 실패를 유료 Messages 성공으로 세지 않는다.

9응답의 output hash와 usage를 검증했다. 입력 원문 전체를 독립적으로 재해시할 수 있는 것은3/9이며, 나머지6개는 provider의 private thinking을 공개 기록에서 제거해 원래 입력 hash와 공개 body만 별도 보존했다. 9개 모두 완전 재현 가능한 원문이라고 주장하지 않는다. [출처표](live-provenance.json)에 request ID와 검증 가능 범위를 기록했다.

두 모션 각각 frame0/12/24/36/48/60/72/84/95를 디코딩해 동일 시점의 preview PNG와 비교했다. RGB 평균 절대 오차 **0.33333–0.39430**으로, 이 시험에서 제안한 codec 허용치<3을 통과했다. 픽셀 동일·지각 품질 표준이라는 뜻은 아니다. 편집출력은0.5초 blue/2.5초 red, 한글cue 시각과 Unicode, 첫100ms 음원RMS0.17519를 확인했다. 원곡 첫1초 무음 fixture에서 source offset1초가 실제 적용됐음을 보여준다. [미디어 검사](live-media-verification.json), [검사 코드](verify-live-media.py). 전체 프레임을 사람이 청취·시각 평가한 것은 아니다.

### 실제 UI에서 발견해 수정한 결함

1. **모션 저장 거절 뒤 승인 버튼 상태와 오류 위치:** 공통 요청 처리의 재활성화가 모션 prerequisite를 덮었고, 오류가 dialog 밖에 표시됐다. `motion-studio.js`가 요청 종료 후 현재 입력/대기 상태로 controls를 다시 계산하고 dialog 안에 실제 저장 상태를 표시하도록 수정했다. confirmed rejection, unknown, 저장 성공 후 refresh 실패를 구분하고 입력을 보존한다. unknown에는 이미 있는 요청 확인 경로만 제공한다.
2. **새 모션 Take 등록 후 오래된 프로젝트 revision:** poll이 jobs만 갱신해 뒤이은 복원에서 stale conflict가 났다. `index.html`은 local-motion job의 완료 전환과 새 revision을 확인한 경우 기존 전체 상태 갱신을 수행한다. 일반 진행 poll은 불필요하게 다시 불러오지 않으며 기존 dirty/edit/media guard를 유지한다.

실제 Chrome149.0.7827.55의 새 격리 탭에서 현재 Aethon localhost 앱을 열었다. 합성 DB/media 복사본만 사용하고 외부 provider runtime이나 credential을 브라우저에 구성하지 않았다. 1920×1080/DPR1 주 기준,1280×900/DPR1 보조에서 저장·보류·거절·승인·frame preview·후보 render·복원·Escape focus 반환·초안 보존·장면 간 초안 격리·reload를 확인했다. 두 결함은 수정 후 같은 경로에서 재검증했다. 최종DB는 motion versions5/proposals7/Takes4, **기존 Take1 선택 유지**, 새Take 권리는 미확인으로 유지됐다. [UI 수용표](browser-followup/acceptance.json), [DB 확인](browser-followup/db-final.json).

최종 HTML/motionJS/mediaJS의 source와 served hash가 일치했다. CSS는 그대로이며 별도 served hash 일치 검사는 하지 않았다. 최종1920·1280 캡처는 최종HTML 기준이다. `motion-error-1920.jpg`와 초기`motion-preview-1920.jpg`는 모션 오류 수정 후, 마지막 poll revision 수정 전 캡처이므로 최종HTML 캡처로 재표기하지 않는다. unknown/committed-refresh-failed의 상태 제어는 Node double에서 검증했으며 실제 브라우저 장애 주입은 수행하지 않았다.

### 최종 회귀·동결·종료

- 전체 **393/393**, 한 실행 **373비HTTP+20HTTP**,57.487초. Node 내부 시나리오는 별도 테스트 개수로 중복 합산하지 않았다. Python AST, inlineJS/motionJS 구문 검사 통과.
- HTML `25bfab1a9ef92abed34150ac01b2b075036af259fdba2dd97bc0d467df8e768b`.
- motion JS `71e8959f23dc14863c63d619b23420b9d199165e5bd28a01901d391cfa37e40e`.
- Anthropic schema adapter `e5707b73708e6a18918ef965dc611d138833a84041bfe668936f086773f0d528`.
- 기존 media lifecycle JS `ac41a983…2832c9`는 그대로다. CC01/CC02·F07/DM/FQ 관련 회귀를 보존했다.
- 검증 탭 닫기/viewport 복원, 임시127.0.0.1:49481 서버 종료와 listener0 확인. [종료 기록](browser-followup/cleanup.json). Swift/FFmpeg/시험 프로세스 종료. SQLite supported backup integrity `ok`; 해당 QA backup의 일부 참조는 임시 media 경로이므로 독립 배포 가능한 번들이 아니다.

남은 범위는 모델의 승인/변경 설명 품질, Mac 이외 raster backend, 모든 모델/큰 구성/실사용자/다중 사용자 운영, screen reader·실제 브라우저 zoom·다른 브라우저·모바일 검증이다. 실제 fal403과 일반 media live 수용 gate도 남는다. 기존 Codex 앱 CUA 거절은 재시도하지 않았다. 설치·새 credential·권한 변경·Library 업로드·배포·공유 사용자DB 변경은0이며 ingestion/온톨로지 자동 진화·Blender는 계획만 유지했다.

## 이전379개 검증 시점의 기록 — 역사적 상태 보존

아래 내용은 후속 수정 전 결과다. 당시 Messages0/count 차단 및 UI 미검증은 위 현재 결과로 갱신됐지만 원인을 소급해 꾸미지 않기 위해 당시 문장을 보존한다. `FINAL-MANIFEST.json`은 그 빌드, 현재는 `FOLLOWUP-MANIFEST.json`을 사용한다.

2026-10-26 UTC. **로컬 모션/편집 코드와 합성 회귀는 완료했다. 실제 Claude 저작과 현재 UI 브라우저 수용은 미완료다.** 실제 모델 결과를 손수 작성한 fixture로 대체하지 않았다. 전체 **379/379** 회귀(359 비HTTP + 기존20 HTTP), 56.714초. [정확한 소스/자산/원장 해시](FINAL-MANIFEST.json), [전체 로그](final-full-regression-379.log), [단일 계획 K.4/K.5](../codex-cli-assessment-20261026/PLAN-ko.md).

## 바로 볼 수 있는 산출물

- [최초 한글·도형 PNG](m0/korean-shapes.png): 설치된 Swift/CoreText의 capability 확인. glyph0 없음, 1920×1080. 저장 이미지를 직접 확인했다.
- [합성 모션 v1 MP4](artifacts/fixture-motion-v1.mp4), [원만12프레임 지연 v2 MP4](artifacts/fixture-motion-v2.mp4): 각4초/1920×1080/24fps/96프레임. **사람이 정의한 fake tool 응답 fixture이며 Claude 저작 아님.**
- [음악·한글 자막 포함 편집 MP4](artifacts/fixture-edited-audio-captions.mp4): 3초, 파랑→모션→빨강. 자막은 선택형 트랙이며 번인이 아니다.
- [v1 프레임24](artifacts/fixture-v1-frame-24.png), [v2 프레임24](artifacts/fixture-v2-frame-24.png): 실제 픽셀을 확인했다. 새 앱 화면 스크린샷은 아니다.

## 구현한 범위

|경계|실제 코드와 동작|검증/한계|
|---|---|---|
|M0 설치 없이 한글 raster|`native/motion_frame_renderer.swift`: 신뢰된 독립 작성 코드, CoreText/CoreGraphics/ImageIO, 고정 시스템 폰트|컴파일/한글/사각형/원 PNG 성공. Remotion 코드 복사·임의 모델 코드 실행 없음|
|M1 제한 scene/evaluator|`motion_scene.py`: 72–96frames,24fps,1920×1080,text/rect/circle 1–8layers,≤8keys/layer,x/y/opacity,linear/cubic,정수 frame clock|unknown fields·NaN·임의 경로·glyph 부재·텍스트 상자 넘침 차단. 일반 3D/영상효과 엔진 아님|
|제안·사람 검토·버전|`propose_motion_scene`, Store `motion_review`, `motion_restore`; 기존 production run/idempotency/트랜잭션 재사용|hold/reject/approve, stale/다른 작품 차단, 복원은 새 승인 버전. canonical ontology 변경 없음|
|로컬 후보 렌더|`request_motion_render`, `motion_renderer.py`, 기존 jobs/asset/Take 경로|동일 승인 기존job 재사용, 취소/중단 자동 재실행 없음. font/source hash 재검사, 단일motion worker,180초/128MB 임시한도|
|원자 등록·권리|검증 MP4만 Take 등록. 등록 실패는 DB rollback 및 새 미참조 파일 정리|기존 파일은 삭제 안 함. 새Take는 미선택/권리미확인. 최종납품승인과 분리|
|편집 E1|`propose_timeline_changes`: 전체순열 reorder, 명시적 caption 전체교체, 같은 원음version의source offset, 기존set_clip|기존 timeline proposal→사람 승인→editing.validate/save→새version 사용. 자동적용 없음. 원본·이전승인 버전 보존|
|모델 계약|`production_tools.py`, `chat_protocols.py`, `production_context.py`|Anthropic/OpenAI/xAI3형식 fake tool/result loop;14개 정확한 허용도구 집합 검사. 실제 모든 모델 지원/품질통과 아님|
|최소 UI 연결|`motion-studio.js`, `index.html`: 장면별 구성 dialog, layer 문구/색/시간/위치, 저장/보류/거절/승인, 저장frame PNG, 후보렌더/취소/버전복원|실제 서버 동작을 호출하는 연결. 제어된 DOM 시험 통과; 실제 브라우저/키보드/1920·1280 화면 미검증|

scene schema는 플랫폼 중립이다. 현재 raster backend는 **macOS/CoreText 전용**이며 Linux 배포 가능성을 확인하지 않았다. 현재 설치된 font hash/OS/renderer source를 승인에 고정하고 폰트를 복사하지 않는다. helper는 모델 데이터만 읽고 network/표현식/외부경로를 받지 않는다. 이를 OS sandbox나 범용 보안 인증과 동일시하지 않는다.

프레임은 trusted evaluator→제한된 PNG sequence→기존FFmpeg libx264/yuv420p로 인코딩한다. 계획의 raw stream 대신 PNG sequence를 택해 프레임 검사/취소/용량 한도를 단순화했다. 새 의존성은 없다. 완료된 후보와 최종 음악·자막 출력은 별도다. 렌더 중 UI 닫기는 취소가 아니다.

## 검증 결과와 실패 이력

|검사|결과|증거|
|---|---|---|
|M0 컴파일·glyph·PNG|통과, 누락glyph0|[result](m0/result.json)|
|motion9개 unit/integration|schema/frame,3protocol,승인/복원/격리,grant/font,실제96frameMP4,취소/rollback,preview/font/context,재시작·worker|`tests/test_motion.py`;전체379에 포함|
|E1 4개|3protocol proposal/human apply/restore,명시하지않은caption/audio보존,invalid/stale인수,base clip index 후reorder|`tests/test_timeline_commands.py`;전체에 포함|
|UI1개, 내부7시나리오|동일문구 재입력, 늦은저장응답/작품전환,작품별초안,늦은frame,dirty preview차단,poll중input보존,닫기focusreturn|`tests/test_motion_ui.py`: Node DOM doubles. 실제 browser 증거 아님,7을test개수에 중복합산 안 함|
|관련27개 + UI1개|통과|[관련로그](final-focused.log), 전체최종379에 포함|
|전체기존+신규|**379/379**|[최종로그](final-full-regression-379.log)|
|정적검사|제품 Python AST,inlineJS/motionJS syntax 통과|manifest 파일집합|
|모의 전체 여정|create→승인→render→Take→reopen→dot12frame수정→restore→순서/caption/audio제안→승인→최종output/reopen|[모의summary](offline-1793029812/summary.json), 해당case1–3/turn·render 기록|
|프리뷰/영상 대응|v1/v2 frame0/24/60 RGB MAE **0.0239–0.0377**, 제안한fixture허용<3 통과|[미디어 측정](media-verification.json), [실행기](verify-media.py). lossless 동일파일이라고 주장하지 않음|
|편집출력|0.5초 blue(0,0,255),2.5초 red(254,0,0);0–1/1–2/2–3초 한글cue;audio첫100ms RMS0.17519|원음첫1초는무음이므로source offset1 적용 확인. 사람청취/음질평가 아님|

초기 전체375회에서374통과/1실패는 기존 도구수11 단언이었다. 새14개 **정확한 집합 및 strict schema** 검사로 갱신했다. CC02 경계 fixture는 tool schema 증가로 원pad길이가음수가되어 seed 길이를 조정했으며 실제65536byte경계 검사를 유지했다. 제품의 CC01 사용자 요청 이력을 자르는 변경은 하지 않았다. 개별실행의 module import 경로 실패는 `PYTHONPATH=.:tests`로 바로잡았다. 미디어측정의 FFmpeg `.1` 문자열은`0.1`로 수정했다. 이 실행기 문제들을 제품품질 성공으로 숨기지 않았다. 과거 실패로그는 보존했다.

## 실제 Claude 시험 — 중단, 저작 검증 미완료

정식 실행 심사는 통과했고 `scripts/native_motion_trial.py --live`가 **한 번 실행**됐다. 기존키 메모리인증/공식Anthropic/합성입력만 사용하도록 작성한 경로다. 사전 count 경로1회, **Messages 전송0회**, 새 model requestID/출력/usage 없음. 상태`blocked_before_message`, 예약0, 추가usage가격$0. 자동retry/fallback0, fal실호출0. [transport](live/case-1/transport.json), [turn](live/case-1/turn.json), [시도한도](live/attempt.json), [중단summary](live/summary.json).

최종Messages본문7336bytes는 로컬byte preflight를 통과했으나 `adapter.count` 경로가 성공값을 반환하지 못했다. 기존 adapter가 credential supplier/전송/응답 예외를 동일한 비밀없는 오류로 감싸므로 **현재증거로는 키읽기·DNS/TLS·HTTP인증·응답형식 중 원인을 확정할 수 없다. count HTTP의 실제 외부접수 여부도 확인 불가**다. 이를API403/모델부재/권한심사거절로 단정하지 않는다. Messages는호출전이라미전송이확실하고CC02경로가이예약만반환했다. 이미시도한live script는재실행하지않는다.

모델은`claude-haiku-5-5`,입력16384/output8192,최대9Messages,stage75000µUSD($0.075),증분hardcap$1/aggregate$50. 공식[Haiku5.5 요금](https://platform.claude.com/docs/en/models/haiku-5-5/overview) ≤100k 입력$0.10/MTok·출력$0.50/MTok 재확인. 누적usage가격 **$0.0224918**, 보수원장 **$0.022503**, invoice미확인으로변화없음. 모의summary의`usage_usd`는fake원장 수치이고 실제청구에합산하지않는다.

앞선CC01의실제14응답·프롬프트시험은역사적실증이며이번모션성공증거가아니다. 앞선output14hash확인/input전체6재해시가능·8thinkingredacted제한도그대로다.

## 브라우저와 종료 상태

CUA inventory에서Mac의Ego Lite를 확인했다. bundle ID조회는설치경로2개로ambiguous여서`/Applications/ego lite.app`을명시했다. 그`getApp`조회가완료되지않고 **7573.5초 뒤 aborted by user**로끝났다. 웹페이지로드·로컬앱서버시작·브라우저UI검사·새스크린샷은수행하지못했다. 다른브라우저/CLI/REA로우회하지않았다. 이지연은미디어렌더가장시간실행된것이아니다.

전체HTTP회귀는기존정식승인경로의임시localhost만사용하고shutdown/server_close/join한다. fullsuite프로세스는종료코드0. 별도UI서버/listener/장기worker는시작하지않았다. Swift/FFmpeg child는동기실행완료 또는취소finally에서종료한다. fixture디렉토리는결과재현용으로유지하고검증MP4/PNG를위durable QA경로에도복사했다. 공유QA DB/사용자자료/기존Take/원장과거행은변경하지않았다. 새live원장행은위count실패1행뿐이다. 설치/Library업로드/배포/권한변경0.

## 남은 유한 gate

1. **실제Claude저작**: count 경로의민감하지않은단계별진단(비밀값없이)을검토한후, 이미전송0인Messages와불확실한count를구분하여부모가다음명시시도를판단해야한다. 이번시도marker/원장을지우거나blind retry하지않는다.
2. **현재UI수용**: Ego연결을복구한정상경로에서합성데이터만사용해1920주/1280보조,layer수정→preview→검토→candidate→output/reopen,keyboard·focus·장면전환을검증해야한다. Node시험은이gate를닫지않는다.
3. **운영범위**: Mac로컬최소기능이다. Linuxraster/대규모구성/일반사용자live활성화/동시다중사용자/모든chat모델품질은이번범위밖. unconfigured/unverified provider를활성화하지않았다.
4. 새이질데이터ingestion/온톨로지진화·Blender모델화는계획만유지했다. 기존fal403도미해결이며유료영상호출은추가하지않았다.

기존CSS·미디어lifecycle JS 및CC01/CC02 runtime/transport 해시는보존했다. HTML/app/tool연결은바뀌었으므로과거served screenshots를현재화면이라고부르지않는다. 현재source는manifest고정이며실행서버에반영됐다는주장은하지않는다.
