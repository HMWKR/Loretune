# D1-frame-observation-design 결과 (S13, 설계 문서만)

## 한 일 (파일별)
- `docs/design/FRAME-OBSERVATION-DESIGN-ko.md` (신규 작성, 22,046바이트, sha256 `0d4c05d5d6f719ce99b014f8abaff7d20a16ccb054ce91953a845457748c59ef`)
  - §2 요구 원문 인용: 스펙 §7.4(`07_…Spec.md:322-324`), AT38(`:610`), MS-FR-27(`:556`), 일부 프레임 범위 표시(`:134`), 도구별 전송자료·권한·최대비용 등록(`:414`), 원본 이미지 무조건 복제 금지(`:418`), `CHAT-SESSION-PLAN.md:29`, `:31`, PLAN 원칙 9(`PLAN-ko.md:54`).
  - §3 재사용할 렌더러: `app.py:421-449` timeline_preview → `renderer.py:100-112`/`:70-98` clip_command, `app.py:412-419` motion_preview → `motion_renderer.py:28-35`. 각 렌더러의 기존 보호 장치(잠금·revision·권리 재검사·크기·타임아웃)를 정리했다. motion_preview에는 권리·revision 검사가 없다는 점도 적었다.
  - §4 이미지 블록 프로토콜: 현재 tool_result는 문자열만 담는다(`chat_protocols.py:49-51`). 이력은 누적된다(`chat_models.py:99`). transport 상한은 65536바이트(`anthropic_ontology.py:175`), `MAX_INPUT=4096`(`chat_general.py:28`). 이를 근거로 프레임 1~4장 상한, 바이트 상한, 토큰 상한, 바이트 비보관을 제안했다.
  - §5 data_scope: 고정 문구 "자산 파일은 전송하지 않음"(`chat_general.py:446`)은 프레임을 보내는 순간 거짓이 된다. 이어쓰기 흐름(`:777-790`), manifest 포함(`:242-245`), 전송 바이트 sha 재검사(`:618-626`)를 정리했다. 권리 검사는 현재 blocked만 거르는 음성 확인이므로(`app.py:1021-1024`, `:253`) 외부 전송에는 긍정 확인이 필요하다고 적었다.
  - §6 coverage 공개 형식, §7 비용(라운드당 최악 USD 0.0024576 산출, 프레임이 이후 라운드에서 다시 과금됨), §8 S11 위험(`check_music_context` `:290-318`·마커 `:779-782`의 무효화, `music.py:16-17` 파생 특징의 외부 전송), §9 사람 승인 항목 A1~A7(모델·자료·개수·최대비용·보관·재검사·S11).
- `.omo/evidence/agent-tools-02-20261028/tasks/D1-frame-observation-design/result.md` (이 파일)

## 실행한 검증 명령과 결과 (원문)
코드 변경이 없으므로 unittest는 실행하지 않았다. 대신 문서의 소스 `file:line` 인용 64개를 before 사본과 기계적으로 대조했다.
```
cd /Users/leesungmin/Desktop/Loretune && B=.omo/evidence/agent-tools-02-20261028/before && python3 - "$B" <<'EOF' ... (checks 64개: 파일·줄·기대 부분문자열) EOF
```
1차 결과 꼬리:
```
FAIL chat_general.py 243 data_scope |     keys=('id','binding','message_body','count_body','message_sha256','count_sha256',
FAIL renderer.py 107 PROFILES |     with tempfile.TemporaryDirectory(dir=root,prefix='timeline-frame-') as folder:
checked 64 fail 2
```
→ 두 인용을 `chat_general.py:242-245`와 `renderer.py:106`으로 고쳤다(`grep -n 'PROFILES' before/renderer.py` → `106:    width,height=PROFILES[project['profile']]`). 고친 뒤 두 줄 모두 기대 문자열을 포함한다는 것을 확인했다. 다만 64개 전체 스크립트를 다시 돌리지는 않았다.
문서 등록 여부 확인: `grep -rln 'FRAME-OBSERVATION-DESIGN' …`의 결과는 `.bkit/runtime/loop-counters.json` 1건뿐이었다(bkit 훅의 런타임 카운터이며 문서 게이트가 아님). 문서 게이트에 등록되지 않았다.

## 안 한 일 / 남은 빈칸
- 구현, 테스트 코드, 실제 모델 호출, Models API·count_tokens 조회는 하지 않았다(범위 밖이며 외부 호출 금지).
- 문서 게이트 등록·분류·승격을 하지 않았다(지시대로).
- 64개 인용 전체 대조를 수정 후 다시 실행하지 않았다(수정한 2건만 개별 확인).
- 프레임을 넣었을 때 64KiB 전송 본문에 남는 여유 바이트를 오프라인으로 측정하지 않았다. 문서에 [미확인]으로 표기했다.

## 가정·추측
- [미확인] Haiku 5.5의 이미지 입력 지원 여부와 이미지당 토큰 수. 근거로 쓴 이미지 블록 형식과 이미지당 토큰 상한(약 1,568~4,784)은 claude-api 스킬 문서에서 가져왔다. Haiku 5.5 값은 그 문서에 없다.
- [추정] 프레임이 `message_body`에 들어가면 기존 `message_wire_sha256` 검사(`chat_general.py:622-626`)가 바이트 변조를 막는다. 테스트로 확인하지는 않았다.
- 소스 줄 번호는 before 사본 기준이다. 작성 중 다른 트랙이 `chat_general.py`·`app.py`·`chat_protocols.py`·`production_context.py`·`production_tools.py`·`general-chat-ui.js`를 수정해 현재 줄이 밀렸다(예: result_message가 777에서 778로). 문서 머리말에도 이 사실을 적었다.

## 기각한 가설
- "motion_preview도 timeline_preview처럼 권리를 재검사한다" → 기각. `app.py:412-419`에 check_rights가 없다. 대신 모션 레이어가 text·rect·circle뿐(`motion_scene.py:9,31`)이라 외부 자산은 없다. 그러나 텍스트에 미공개 가사가 들어갈 수 있어 보완 항목으로 남겼다.
- "check_rights 통과 = 외부 전송 가능" → 기각. 기록이 없는(미확인) 자산도 통과한다(`app.py:1021-1024`). 테이블에는 외부 전송 필드가 없다(`app.py:253`).
- "4장 정도는 현재 상한 안에 들어간다" → 기각. 문서상 이미지 1장 상한만으로도 `MAX_INPUT=4096`에 가깝거나 그보다 크다. 4장을 넣으려면 상한 상향이나 해상도 축소에 대한 사람의 결정이 필요하다.

## requests_for_other_tracks
- 없음(코드 변경을 요청하지 않음). 참고로 트랙 C(S11)와 트랙 A(chat_general data_scope)가 같은 문제를 다룬다. 프레임 관찰과 음원 측정값 투영은 "자산 파생 데이터의 외부 전송" 문제로 같으므로, data_scope 문구, 긍정 권리 확인, 해시 마커 분리를 한 번에 설계하고 승인받아야 한다(문서 §8).
