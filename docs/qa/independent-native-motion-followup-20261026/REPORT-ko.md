# Native motion 후속 동결본 — 독립 검증

**실행 연결·제한·표본 출력은 검사 범위 내 통과. 모델의 승인 설명과 편집 영수증 의미는 P2 잔여 2건이다. 전체 품질 PASS로 닫지 않는다.** 제품 소스와 공유 DB는 변경하지 않았고 새 모델/API 호출은 0회다.

대상은 [FOLLOWUP-MANIFEST](../native-motion-20261026/FOLLOWUP-MANIFEST.json)의 2026-10-26 **18:36:58.879242Z** 소스다. 검토 중 18:43:24에 manifest의 문서 인계·미디어 검사·잔여 gate metadata가 추가됐다. 소스 25개와 최종 인계 문서 해시는 일치하며, 검토 snapshot 45파일과 기존 증거는 manifest 외 변경 0이다. 최종 manifest SHA256 `78556126f134846bc47ab0b56e7f974a5ab8143e16d09d4899a5f4dafd2fd951`; [보존본](verified-release-manifest.json), [종료 대조](end-check.json).

## 먼저 수정할 설명 문제

### NM-Q01 — 기존 모션 승인을 확인할 수 없다고 답함 · P2

**재현 근거:** 실제 [case2 turn](../native-motion-20261026/live-schema-corrected/case-2/turn.json)의 마지막 답변은 “조회 결과에는 승인 기록이 없고 온톨로지도 null”이라며 revision 1의 사람 승인을 확인할 수 없다고 한다. 그러나 같은 최종 요청의 앞선 search tool result에는 revision=1과 grant `2f9d3b53c8c140f7acb07a36bdd39d2b`가 있다. 승인된 v1에는 actor=`local-owner`, scope=`local-motion-candidate`, scene hash가 실제 저장돼 있다. 새 v2 제안이 아직 미승인이라는 답변 부분은 맞다.

**기대/실제:** “기존 v1은 로컬 모션 후보 렌더 범위의 사람 승인 기록이 있고, 이번 새 v2 제안은 미승인”으로 구별해야 한다. 실제 응답은 기존 v1 승인까지 불명확하다고 설명했다. 사용자가 불필요하게 다시 승인하거나 현재 상태를 오해할 수 있다. 실행 승인 우회나 원본 손실은 관측되지 않았다.

**코드 원인:** `production_context.py:26–27`은 motion의 revision/scene/grant_id만 내보내며 actor/scope/scene binding을 생략한다. `chat_models.py:21–26`의 역할 설명은 ontology와 media action approval_handles를 다루지만 motion 승인의 의미는 설명하지 않는다. 독립 합성 Store에서도 정상 v1 승인 + pending v2를 만들면 정확히 이 projection 누락이 재현된다. 이 누락은 검증 가능한 기여 원인이다. 해당 문구가 생긴 유일한 모델 내부 원인이라고 단정하지 않는다.

**최소 수정 제안:** 두 위치에서 기존 승인 기록의 읽기 전용 의미만 보강한다. motion에 저장된 `approval` 요약(id, actor, scope, 적용 revision, scene_hash)을 제공하고 `requires_revalidation=true`를 명시한다. 단순 ID 존재를 현재 실행 가능으로 판정하지 않는다. SYSTEM에 “현재 승인 기록·새 제안·최종 출력 승인·ontology 유무는 독립”임을 짧게 설명한다. 모델 tool input, 승인 생성 서비스, render gate는 변경하지 않는다.

**비유료 수용 기준:**

1. 승인 v1 + pending v2 fixture의 조회와 handoff에 정확한 v1 승인 범위가 포함되고 v2는 미승인으로 남는다.
2. 무승인, 다른 작품, 오래된 revision/context/scene 입력을 승인·실행 가능으로 표시하지 않는다. 권리/현재 조건은 여전히 실행 시 재검사한다.
3. 모델은 actor/approval/scope를 tool 인수로 주입할 수 없고, 가짜·이전·다른 작품 grant는 계속 거절한다.
4. 위 offline 조건은 앱 계약 수정의 수용이다. **Claude 문장 자체의 개선은 향후 승인된 실제 응답 재시험 전에는 미검증**으로 남긴다.

연결: SPEC-MS-001 **MS-FR-11 / MS-AT18** 승인 문맥 인계, **MS-FR-05/06 / AT09/10** 권한 분리 및 PLAN K.4. 기존 media AT를 모션 전체 신규 시험 완료로 재분류하지 않는다.

### NM-Q02 — 편집 영수증의 `changes=[]`가 전체 변경 없음처럼 읽힘 · P2

**재현 근거:** 실제 [case3 turn](../native-motion-20261026/live-schema-corrected/case-3/turn.json)에서 `propose_timeline_changes`는 reorder `[2,0,1]`, 자막 3개 전체 교체, audio offset=1을 성공적으로 저장했다. `commands`는 모두 반환되지만 `changes=[]`다. 모델은 “서버가 계산한 세부 차이는 확인할 수 없고, 저장된 명령 내용만 확인”됐다고 설명했다. 저장된 proposal timeline·적용 v2·렌더 snapshot은 요구와 일치한다.

**코드 원인:** `local_creation_tools.py:70–89`의 `changes`는 `set_clip` 분기에서만 채워진다. `save_timeline_proposal`의 반환(`:64–69`)은 이 legacy clip diff를 범위 설명 없이 `changes`로 제공한다. 이번 세 명령은 모두 clip take/trim/duration 변경이 아니므로 빈 배열이 정상이다. 수신자가 전체 timeline diff로 해석할 여지가 있다. `chat_runtime.compact_result`는 이 결과를 삭제하지 않으며 압축 손실 문제가 아니다.

**최소 수정 제안:** legacy `changes`는 호환을 위해 그대로 두고 `changes_scope=clip_take_trim_duration` 같은 명시적 범위와 작은 **서버 계산 diff**를 추가한다. 저장 candidate와 base에서 clip 순서/동일 occurrence, captions before→after, audio version/offset before→after를 비교한다. 모델 description을 authoritative diff로 복사하지 않는다. proposal ID/base_version과 `applied=false/output_approved=false`는 유지한다.

**비유료 수용 기준:**

1. 이번 원 표본에서 세 종류 변경의 before/after가 정확하고 `changes=[]`는 legacy clip 속성이 그대로라는 뜻으로 표시된다.
2. reorder-only면 caption 절대 시각/audio는 unchanged; audio-only·caption-only·set_clip+reorder 혼합도 실제 candidate와 일치한다.
3. 중복 tool call은 동일 proposal/diff를 반환하고, stale 버전은 차단한다. diff 생성으로 적용·승인·원본 변경이 발생하지 않는다.
4. 거절/보류/미적용과 이미 적용된 편집·출력 승인을 별도로 유지한다. 실제 모델의 설명 개선은 별도 live 수용으로 남긴다.

연결: PLAN **K.5 E1**, SPEC-MS-001 **MS-FR-07/11/17**, 관련 AT12/18/29의 계약 의도. 전체 AT 통과 주장 아님.

## 실제 provider → 도구 → 영상 연결

- `anthropic-live`, `claude-haiku-5-5`로 기록된 **9개 응답의 visible output hash 9/9**를 독립 재계산했다. 9 request ID는 중복 없고, request 파일·transport input hash·step이 연결된다. 보이는 tool_use 6개(search 3 + 제안 3)의 인수는 저장된 normalized call과 일치한다.
- 입력 전체 재해시 **3/9** 일치. 나머지 6개는 recorder가 private thinking을 제거해 전체 원 hash를 재현할 수 없다. 저장된 공개 입력·원 hash·출력은 연결했지만 모두 완전한 raw request 증거라고 부르지 않는다. 실제 공급자 응답은 저장 기록으로 검증했으며 이번에 새 호출하거나 공급자 서버에서 request ID를 재조회하지 않았다.
- case1/2의 모델 scene input = 제안 result = 승인 version = render job scene. source run/call/model/mode가 Take provenance와 연결된다. 기존 v1→v2는 **dot의 in/out과 모든 keyframe에 +12만 변경**, 나머지 전체 데이터 동일. restore v3은 v1 scene을 새 버전으로 보존한다.
- case3은 기존 clip occurrence `[2,0,1]`, cues 0–1/1–2/2–3초 “시작/움직임/완성”, 같은 audio v1 offset 1초만 변경했다. proposal timeline·적용 version·render snapshot이 모두 일치하며 원본 v1 timeline은 남아 있다.
- 모델 응답 시점의 result는 `applied=false`와 미렌더/미승인이다. 이후 harness가 명시적으로 **local-owner 역할**의 기존 서비스를 호출했다. 사람이 실제 UI에서 누른 승인 증거와 이 harness 승인을 같은 것으로 세지 않는다. 새 motion Take는 자동 채택되지 않으며 후보 출력은 최종 납품 승인이 아니다.
- 재열기 주장은 harness의 새 Store 생성 및 비교 assertion과 저장 after-state로 뒷받침된다. 이번에는 원래 trial DB나 공유 usage DB를 열지 않았다.

## schema 변경과 독립 실행 검사

`chat_models.py:32–58`은 deepcopy한 Anthropic 전송 schema의 bound를 description으로 옮긴다. 원 schema와 `production_tools`/`motion_scene`/timeline validator는 유지된다. 요청 본문 9개 모두 strict=true다. “HTTP400의 원인이 특정 필드였음”은 provider error body가 없어 확정할 수 없지만, 수정 전 count400와 수정 후 count/Messages 성공은 별도로 기록돼 있다.

**격리 offline 시험 6/6 PASS:** 기존 strict-wire 4개 + 독립 2개. 원 schema 불변·다른 provider 계약 불변, motion frame/canvas/layer/keyframe/text/font/opacity/NaN/unknown path 제한 유지, 승인 projection 누락, 가짜/이전/다른 작품 grant 거절, 중복·취소 job 재사용과 Take 미생성을 확인했다. socket/listener/subprocess·canonical 접근을 차단한 새 임시 Store에서만 수행했다. [offline 증거](offline-tests.json). 전체393 suite를 다시 실행하지 않았다.

## 비용과 요청 수

usage 합계는 입력 **62,853**, 출력 **6,446** tokens. 기록된 단가(입력$0.10/MTok, 출력$0.50/MTok)로 재계산한 이번 비용은 **$0.0095083**. 기록된 이전 $0.0224918을 더한 누적은 **$0.0320001**이다. 단가의 원 출처는 primary 보고서에 있으며 이번에는 계정/청구를 조회하지 않았다.

- 수정 후 count 진입 9 / Messages 9 / 응답 9.
- 별도 진단 count 1은 HTTP400 / Messages 0.
- 최초 15:51 count 진입 1은 전송·수신 단계 미확인 / Messages 0.
- 따라서 모션 관련 저장 기록의 **count 진입 합계는 11**이다. count 성공 11회나 paid Messages 11회가 아니다. 자동 retry=0과 원인 확인 후 명시한 새 시험을 구별한다.
- 응답별 비용을 micro 단위 올림한 합계는 9,512. 이전 보수 원장 22,503과 합하면 보고된 32,015와 일치한다. 이번 unknown held=0은 **저장된 provenance의 값**이며 공유 원장을 독립 조회한 결과가 아니다. fal0, **실청구(invoice) 미확인**.

## 출력·브라우저 증거의 강도

실제 MP4 세 파일 hash가 manifest/job/Take와 일치한다. 독립 ffprobe는 모션 각1920×1080/24fps/96frames/4초, 편집 출력72frames/3초와 video/audio/subtitle stream을 확인했다.

저장 파일을 새로 decode한 표본에서 v1 frame12와 v2 frame24의 dot 색 영역 bounds는 둘 다 `[502,802,557,857]`, v2 frame0에는 dot 없음. 해당 두 frame의 trusted preview PNG 대비 RGB MAE는0.352813/0.385470. 기존 시험 제안치<3을 통과했으며 지각 품질 표준이나 전체 프레임 정확성 증명은 아니다. 편집 출력의0.5초 blue/2.5초 red, 정확한 한국어 SRT 구간0–1/1–2/2–3초, 첫100ms audio RMS0.175193을 독립 확인했다. 연속 AV drift·전체 음원 보존·전 장면 시각 품질은 별도다. [표본 증거](media-samples.json).

저장된 **최종1920·1280 JPEG를 실제 열어** 한국어 제목·도형 preview, 모션 승인/후보렌더/복원 버튼과 focus outline을 확인했다. manifest hash 및 기록된 served HTML/JS hash는 일치한다. HTML은 `25bfab1a9ef92abed34150ac01b2b075036af259fdba2dd97bc0d467df8e768b`다. 초기 error/preview1920은 마지막 poll 수정 전이라는 primary의 구분을 유지했다.

Chrome149.0.7827.55, viewport1920×1080/1280×900/DPR1의 실제 클릭·초안·Escape·장면 격리·reload는 **primary의 acceptance/DB 요약 기록**이다. 정적 screenshot만으로 그 시간 순서를 독립 재현했다고 주장하지 않는다. unknown/refresh-failure는 Node double 범위로 올바르게 표시돼 있다. 이번 브라우저·Codex 앱·listener 실행 0. CSS served hash 미검증, 다른 engine/실제 zoom/보조기술/모바일 미검증을 유지한다.

## 종료 판정

|범위|판정|
|동결 소스/제안·승인·버전·파일 연결/대표 디코딩 출력|PASS — 위 표본·격리 검사 범위|
|서버 입력 제한 및 승인 실행 경계|PASS — 검사한 반례·대조군 범위|
|승인 설명·편집 영수증 의미|잔여 NM-Q01/NM-Q02, 개선 후 offline 재검증 필요|
|실제 UI 전 과정·393 전체회귀|primary 실행 증거 검토; 독립 재실행 아님|
|모델 문장 개선·청구·전체 운영/모든 모델/전수 품질|미검증|

local demo의 실제 Claude 저작과 로컬 출력 증거는 확보됐다. limited pilot/full spec readiness는 이번 표본으로 닫지 않는다. [실행 기준](CRITERIA.md), [연결 검사](evidence-checks.json), [snapshot/hash](base-manifest.json)를 보존했다. 새 제품 patch·key/.env/공유 DB 읽기·provider 호출·설치·업로드는 없다.
