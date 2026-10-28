# Aethon Claude 문맥·프롬프트 독립 검증

**앱은 최신 승인 온톨로지와 최근 작품 대화를 저장·재전달하고, 모델 작성 prompt를 승인된 입력 그대로 fal adapter에 전달한다. 그러나 장기 세션의 금지사항이 8-turn 창 밖으로 사라지는 반례 1건(CC01/P2)을 재현했다. 이번 실제 Claude 호출은 0회이므로 모델의 이해·prompt 품질을 새로 통과 판정하지 않는다.**

2026-10-26. 읽기 전용 snapshot과 임시 synthetic Store/fake transports만 사용. [사전 계획](PLAN.md), [source hashes/mtime](source-manifest.json), [종료 source 확인](final-source-check.json). 핵심 14개 소스/명세의 시작·종료 hash 동일. app source/공유 DB·서버·비밀파일 변경 또는 조회, 의존성 설치, fal 호출은 하지 않았다. 별도 QA artifacts와 임시 fixture만 작성했다.

## 가장 중요한 발견

**CC01 / P2 — 최근 8개 밖의 세션 제약은 DB에 남아도 다음 모델 요청에서 누락된다.**

- 재현: turn 1에 `SESSION-LONG-913: For this session never orbit the camera.` → turn 2–9 중립 대화 → Store 재열기 → turn 10 “세션 제약을 유지하며 계속”.
- 기대: 중요한 금지사항이 raw history 압축 이후에도 근거와 함께 전달됨. 07 §7.2, 관련 MS-FR-11/MS-AT18. 모든 과거 발언의 무제한 기억을 요구하는 시험은 아니다.
- 실제: DB 10 turn에 첫 지시가 존재하지만 전송 body에는 없음. prior user messages는 2–9만 존재하고 별도 summary/active-session-constraints 없음. 임의 fake 답변은 금지사항을 다시 말하지 않도록 했으며, 이는 입력을 충분히 보냈다는 착각을 막는다.
- 위치: `chat_runtime.py:132,143–145`, `chat_protocols.py:55–60`, `model_selection.py:55–61`.
- 영향: 현재 canonical ontology에 별도 등록하지 않은 일회성 연출 금지/조건을 후속 prompt에 반영할 근거가 사라질 수 있다. 데이터 삭제나 실제 Claude의 기억 실패를 주장하지 않는다.
- 최소 수정: 활성 세션 제약/한시 예외를 provenance turn ID·scope·revision으로 별도 보존하고 raw history window와 분리해 전달. 한도 내 보존 불가 시 명시적으로 중단/재확인. 자동으로 IP 공식 설정으로 승격하지 않음.
- [재현 코드 C02](offline_probe.py), [전송 누락 증거](long-history-evidence.json), [최종 실행 결과](offline-results.json), [초기 checkpoint](CHECKPOINT.md).

별도 미구현: `chat_turn` 입력은 `song,prompt`만 받고 저장소 key는 project다(`chat_runtime.py:14–18,128–145`). session_id를 주면 거절되고 자연어 “새 세션”만으로 이전 작품 대화가 분리되지 않는다. **작품별 한 대화 흐름은 구현됐지만 같은 작품의 독립 session 격리는 아직 없다.** 07의 conversation_id(445행)/conversation message API(483행)와 구분한다. 다른 작품 정보 누출로 과장하지 않는다.

## 이번에 직접 확인한 것

독립 fixture **5개 중 4 PASS / 1 FAIL(CC01)**. capability 관찰인 C03 PASS는 “독립 세션 지원”의 PASS가 아니다. 관련 기존 회귀 **69 tests PASS**와 편집 부록 **4 tests PASS**를 별도 실행했다. 이 숫자들을 전체 명세 커버리지/점수로 합산하지 않는다. [회귀 결과](regression-results.json), [로그](regressions.log), [편집 결과](editing-addendum-results.json).

|요구 범위|관측·판정|근거 위치|
|---|---|---|
|여러 turn·reload/resume|임시 Store 재열기 후 최근 user prompt/assistant answer 복구, assistant는 unreviewed로 전달. 모델 자체 저장 기억이 아니라 앱 재전달. long-tail는 CC01 실패.|chat_runtime 128–166; C01/C02|
|entity/relation/version/provenance|승인 v1→v2 변경 후 새 handoff/search에 v2, 같은 stable ID·relation·새 provenance 전달. 과거 v1 불변. 모순 source 2개 및 unknown 보존, stale revision 거절. 의미적 모순 해결은 앱이 자동 수행하지 않음.|ontology 139–190; app 389–405; guided 9–12; C01/C04|
|작품 격리|A/B의 알아보기 쉬운 canary와 대화가 상대 요청에 없음. 외부 작품 ID 거절 및 권한 control 기존 회귀 통과. 같은 작품 session 분리는 미구현.|chat_runtime 132; production_context 20–34; C01/C03|
|독립 모델 선택|chat=Anthropic/image=Flux Pro/video=Kling 2.5 Turbo를 유지하고 명시한 video endpoint로 fake POST. first-model 대체 없음. unavailable 연결을 자동 활성화하지 않음.|model_selection 45–53; fal_dispatch 42–56; P01 및 fal 회귀|
|자동 prompt→검증→fal|실제 ChatRuntime에 **수작업 fake model tool_use**를 넣고 normalized prompt→saved action→grant→job→FalModelAdapter의 exact body 일치. subject/style/location/motion/constraints를 담은 prompt를 훼손 없이 전송. 의미 작성 품질은 NOT RUN.|production_tools 8–44; fal_dispatch 58–67; fal_models 28–41; P01|
|수정·참조·unsupported|수정 prompt는 새 action, 과거 prompt 불변, 과거 grant 재사용 거절. 승인된 current start-frame의 로컬 PNG hash가 exact payload와 일치. authority 추가 필드는 거절. current rights/hash·foreign refs 회귀 통과.|fal_dispatch 27–40,90–119; action_assets; P01/기존 fal tests|
|승인·비용·중복·unknown|승인 전 reservation/job/provider submit 0. 승인 후 fake submit 1, 중복 요청 동일 job·reservation 1. 권리 철회 직전 submit 차단, unknown 재시작 후 중복 없음·예약 유지 기존 회귀 통과.|fal_dispatch 78–119; chat_runtime 73–97,173–211; tests/test_fal_multimodel.py 및 test_chat_runtime.py|

`search_project_context`는 semantic search가 아니라 scoped snapshot 반환이다(`production_tools.py:71–75`). 타입/근거가 보존된다고 내용의 사실 정확성·충돌 해결을 검증한 것은 아니다. `propose_memory_update`는 정확한 current source excerpt와 revision을 요구하며 후보만 만든다. 사람 적용 전 canonical은 유지된다(`local_creation_tools.py:54–70`).

첫 기존 회귀 실행은 65 PASS + 1 harness import error였다. snapshot tests 경로가 빠져 `test_chat_live_scope`가 import되지 않은 문제로, 앱 결함이 아니다. runner sys.path만 보완한 후 69 PASS. [초기 로그](initial-regressions.log)를 보존했고 source/test 본문은 수정하지 않았다. 명시적 HTTP 시험 1개는 제외·NOT RUN이며 bind 재시도 없음.

## 실제 Claude에 관해 말할 수 있는 범위

읽은 역사적 자료: `claude-grounding-20261025/REPORT-ko.md`, `claude-chat-ui-live-20261025/live-summary.json`, `claude-receipt-recheck-20261025/result.json` 및 관련 scripts. 당시 실제 request ID/usage와 승인 사실·곡 한정 예외·unknown·실제 receipt 답변 기록이 있다. **현재 source의 새로운 자연어 영상 prompt 작성/수정·장기 대화 품질 시험으로 재사용하지 않는다.**

마지막 읽은 보고값은 누적 usage 계산 $0.0077580, billing_confirmed=false. 원장 `docs/qa/anthropic-smoke-20261025/usage.sqlite3`는 이번에 열지 않아 현재 총사용액·미정산 예약·잔여 한도를 재확인하지 않았다. $50는 기존 합성 개발 승인 상한이며 이번 감사자의 실행 권한이 아니다.

[최소 live 계획](LIVE-PLAN.md): 네 synthetic turn, 최대 Messages 12/count 12, 8,192 input/2,048 output, 기록된 가격 기준 보수적 $0.022128·stage cap $0.03 제안. 실제 response의 의미 평가, canonical/receipt 정확성, 최신 사실·수정 지시·unknown·다른 작품 격리를 분리한다. fal actual 0. primary가 현재 가격·승인·원장을 확인하고 실행해야 한다. 기존 UI trial script는 listener를 시작하므로 그대로 실행하지 않고 Store/runtime/recorder 부분만 재사용할 계획이다.

## 모션 그래픽·모델 편집 추가 요청

[모션 그래픽 부록](MOTION-GRAPHICS.md): 현재 keyframe/layer renderer 계약은 없고 FFmpeg drawtext도 미지원이다. 4초·1080p·24fps 한글+원/사각형을 **실제 Claude-authored scene JSON**으로 만들고 96 frames 및 0.5/1.5/2.5/3.5초 decode frame을 검증하는 최소안 제시. 아직 actual response/render/frame 증거가 없어 NOT RUN. fal로 대체하지 않는다.

[모델 편집/REA 부록](EDITING-ADDENDUM.md): Take/trim/duration proposal→사람 적용→출력 승인 경로는 존재한다. 모델의 reorder/caption/music 명령은 schema 밖이며 최소 edit-command 확장이 필요하다. Remotion의 프레임 기반 개념을 참고한 **Aethon native authoring/schema/renderer/version/undo/export** 경계를 제안하되 제3자 소스 소유권·라이선스를 재브랜딩하지 않는다. 설치·복사·상업 license 수락은 하지 않았다.

Codex CLI metadata는 `rea`, enabled=true, stdio 등록을 확인했다([결과](cli-rea-metadata.json)). 이 세션의 직접 callable REA 함수는 없지만 CLI 등록 부재로 오해하면 안 된다. REA tools/list·실제 분석 연결·candidate source/version/license는 별도 미검증이다. 새로운 결함 탐색으로 범위를 계속 확대하지 않고 핵심 결과를 반환한다.

**남은 경계:** 실제 Claude의 새 행동 검증과 모션 렌더는 이 감사자에게 실행 권한이 없어 미실행이며 실패한 호출은 없다. HTTP/browser/provider/secret 작업을 시도하지 않았다. workspace dependency 조회 도구는 local-thread-only unavailable을 반환해 추가 runtime 확인을 완료하지 못했다. 핵심 offline 검증은 완료됐으며 CC01은 열린 상태다.

CLI 작업 상태를 구분한다: 이 감사의 `codex mcp list` registration metadata 조회는 성공. 부모의 CLI 외부 소스 분석은 외부 소스 전달 승인 부재로 실행 전에 거절됐다는 인계를 받았으며, 이 감사에서는 해당 분석/동등 경로를 시도하지 않았다. Remotion source 실제 분석 완료를 주장하지 않는다.
