# codex read-only review (thread 01a181a1-4066-7331-92d4-76843c5f035e, model gpt-6-astra, sandbox read-only)
# source rollout: /Users/leesungmin/.codex/sessions/2026/10/28/rollout-2026-10-28T17-29-51-01a181a1-4066-7331-92d4-76843c5f035e.jsonl
# note: final MCP message was overwritten by codex Stop hook (document gate); these are the verbatim assistant review messages.

**현재 상태는 통합 수락 보류입니다.** D15의 다른 모델 제안 허용은 사용자 의도에 맞습니다. 다만 제안·실행 경계와 가격·출처 표시를 완성해야 합니다. 아래는 기존 위험과 wave 1 미완료를 구분한 지적입니다. 경로는 프로젝트 루트 기준입니다.

1. **[High] D1과 반대로 legacy 실행 노출을 테스트로 고정했습니다.** `chat_runtime.py:175`는 전체 도구를 기본 허용하고, `tests/test_general_chat_tool_invariants.py:39`는 `request_media_generation` 포함을 통과 조건으로 삼습니다. 모델은 기존 사람 grant를 이용해 실행할 수 있습니다(`production_tools.py:125`). 무승인 지출 우회를 발견한 것은 아니지만, 계획의 “예전 경로도 좁힘”과 충돌합니다(`.omo/evidence/agent-tools-02-20261028/PLAN-ko.md:135`). **일반·legacy 양쪽에서 유효 grant가 있어도 모델의 실행 호출은 거절되고 예약·제출이 0임을 증명해야 합니다.**

2. **[High] D15 필수 정보가 현재 계약에 없습니다.** 준비 스키마에 `model_reason`이 없고(`production_tools.py:15`), 결과는 총액·가격 종류만 반환합니다(`fal_dispatch.py:71`). 카드 투영과 화면에도 단가·출처·개정·만료 시각·프로젝트 선택과의 차이·선정 이유가 없습니다(`media_creator.py:68`, `index.html:801`). **이미지/영상 × 모든 permission × 결과/카드/재열기에서 동일한 정보를 표시해야 합니다.** read_only에서는 새 준비를 막되 기존 제안의 정보는 보여야 합니다.

3. **[High·검증 공백] explicit 우선 선택과 실행 허가를 분리해야 합니다.** `model_selection.py:45`는 explicit-first이고 `execute=False`이면 blocked 모델도 반환합니다. `fal_dispatch.py:45`는 이 기본값으로 준비합니다. 이는 D15의 *제안*에는 맞지만 실행 가능성을 뜻하지 않습니다. 실제 실행은 별도 gate에 의존합니다(`fal_dispatch.py:83`, `fal_dispatch.py:95`). **다른 모델 제안은 설정을 바꾸지 않으며, 금지 모델·역할 불일치·미연결 모델은 적절히 거절되고, blocked 제안만으로 승인·예약·전송이 발생하지 않는 테스트가 필요합니다.**

4. **[High·계획 누락] 단가 계약과 quote 갱신 정책이 빠졌습니다.** `fal_models.py:51`은 정확한 입력 해시·모델·가격 출처·만료에 묶인 quote를 요구하지만 단가·수량·과금 단위를 검증하지 않습니다. 따라서 모델이 임의 프롬프트나 다른 모델을 제안해도 기존 quote를 재사용할 수 없습니다. **5초→10초, 이미지 비율·프롬프트·모델 변경 시 기존 quote 거절, 올바른 새 quote만 수락, 단가×수량과 총액의 반올림 일치를 검증해야 합니다.** 공식 단가와 총액을 나눈 환산 단가도 구별해야 합니다.

5. **[Medium] provenance의 `mode`는 permission이 아닙니다.** 기존 source의 `mode`는 `run['engine']`입니다(`production_tools.py:94`, `local_creation_tools.py:127`). 미디어 action에는 요구된 대화 모델·permission·effort 출처가 저장되지 않습니다(`fal_dispatch.py:56`). **서버가 생성 시점 설정을 동결해 저장하고, 이후 설정 변경·재시작에도 유지해야 합니다.** 모델 인수로 provenance를 위조하거나 permission·effort를 올리는 시도도 거절해야 합니다(`agent_preferences.py:61`).

6. **[Medium] 견적 합계가 현재 실행 가능한 견적인 것처럼 보일 수 있습니다.** 새 합산 경로는 소유권·보류/거절·만료만 검사합니다(`fal_dispatch.py:79`). 반면 승인은 media snapshot·장면 revision·계획 문맥을 검사합니다(`fal_dispatch.py:93`). 입력이나 프로젝트 미디어 선택이 바뀌어 승인 불가능한 작업도 `estimated` 합계에 남을 수 있습니다. **오래된 저장 견적과 현재 유효 견적을 구별하고**, 미디어 변경 시 무효화, 대화 모델만 변경 시 기존 미디어 승인 유지, `full-v1` 호환성을 검증해야 합니다(`model_selection.py:63`, `model_selection.py:73`).

7. **[Medium] “도구 결과는 이어쓰기 승인 후 전송”이라는 원칙은 legacy에 적용되지 않습니다.** 일반 경로는 승인 대기로 멈추지만(`chat_general.py:790`), legacy는 결과를 다음 메시지에 넣고 계속 진행합니다(`chat_runtime.py:330`). 새 scene-status도 이 경로에서 호출 가능합니다. **legacy 최초 승인에 결과 재전송까지 포함되는지 명시하고**, 거절·취소·권한 하향 후 추가 전송 0, 다른 대화 정보·경로·grant 비노출을 양쪽 경로에서 확인해야 합니다. 현재 코드만으로 무승인 유출이라고 단정할 수는 없습니다.

8. **[Medium] 입력 상한에 대한 합격 근거가 없습니다.** worker 보고의 review/full_access 본문은 단순 `/4` 추정부터 4096을 초과합니다(`.omo/evidence/agent-tools-02-20261028/tasks/A1-server-read-tools/result.md:77`). 실제 초과 여부는 미검증이며 서버는 초과 시 거절합니다(`chat_general.py:647`). 새 3D 조회도 장면 전체 개수 제한이 없습니다(`scene_project.py:303`). **도구·이력·대규모 조회 결과를 포함한 상한 검사와 초과 시 축소/페이지 처리 기준**이 필요합니다. 상한을 자동으로 올려서는 안 됩니다.

9. **[Medium] wave 1 테스트 통과는 통합 수락 증거가 아닙니다.** UI 실화면 검증은 미실행이고 모바일 중간 포커스 이동도 남았습니다(`.omo/evidence/agent-tools-02-20261028/tasks/B1-chat-ui/result.md:104`). 3D 조회의 HTTP 종단 검증도 없습니다(`.omo/evidence/agent-tools-02-20261028/tasks/C1-3d-read-schema/result.md:119`). **375/1280·양 테마의 실제 이동/실패/dirty 보존, 변경 후 전체 회귀, 승인→설정 변경→실행 경쟁·중복 호출·재시작 검증**을 최종 수락 조건으로 묶어야 합니다.

10. **[Low] 계획 상단이 변경된 D15와 모순됩니다.** 상단은 여전히 다른 모델을 거절한다고 명시하지만(`.omo/evidence/agent-tools-02-20261028/PLAN-ko.md:4`), §6은 제안을 허용합니다(`같은 파일:148`). 작업자가 이전 결정을 구현하지 않도록 상단과 작업별 수락 기준을 함께 갱신해야 합니다.

검증: 지정된 13개 파일의 전후 diff·관련 코드·worker 보고를 읽었고, 무쓰기 로컬 probe로 **blocked 모델의 제안 해석 허용**과 **단가 없는 quote 수락**을 확인했습니다. 파일 변경·외부 호출은 없으며, 전체 테스트·실화면·실제 지출 경로는 재실행하지 않았습니다.

---

**지정된 12개 파일을 `before/`와 비교했습니다. wave 1에서 새로 생긴 무승인 지출·자동 승인·삭제·permission/effort 상승 경로는 확인하지 못했습니다. 다만 아래 이유로 전체 수락은 보류해야 합니다.** 경로는 프로젝트 루트 기준이며, `PLAN`은 `.omo/evidence/agent-tools-02-20261028/PLAN-ko.md`입니다.

1. **[High — 기존 위험·계획 불이행] legacy는 모델의 미디어 실행을 계속 허용합니다.** `chat_runtime.py:175`의 기본값은 전체 도구이며, `production_tools.py:125`에서 기존 사람 grant로 실행 가능합니다. 새 테스트도 실행 도구 포함을 고정합니다(`tests/test_general_chat_tool_invariants.py:39`). 이는 D1의 경로 축소 결정(`PLAN:135`)과 반대입니다. **일반·legacy 모두 유효 grant가 있어도 모델 실행 호출을 거절하고, 예약·제출 0임을 테스트해야 합니다.** grant 없는 자동 지출 우회가 확인된 것은 아닙니다.

2. **[High — D15 미구현] 가격 설명과 모델 선정 이유가 빠졌습니다.** 준비 인수에 `model_reason`이 없고(`production_tools.py:15`), 결과는 총액·가격 종류만 반환합니다(`fal_dispatch.py:71`). 카드에도 단가·출처·가격 개정·만료 시각·프로젝트 선택과의 차이·선정 이유가 없습니다(`media_creator.py:68`, `index.html:801`). **이미지/영상 × 세 permission × 결과/카드/재열기에서 필수 정보 표시를 검증해야 합니다.** read_only는 준비 금지이며, 기존 제안 정보의 표시까지 숨기면 안 됩니다.

3. **[High — D15 실행 경계 검증 필요] explicit-first와 `execute=False`는 제안 허용이지 실행 허가가 아닙니다.** `model_selection.py:47`은 모델이 제출한 explicit 값을 프로젝트 선택보다 우선하고, `:51`은 `execute=True`일 때만 비활성 모델을 거절합니다. 준비 경로는 기본 `False`를 사용합니다(`fal_dispatch.py:45`). **다른 모델 제안은 설정을 변경하지 않고, blocked 모델은 실행 가능으로 표시하지 않으며, 별도 사람 승인·전송 gate 없이는 예약/전송 0임을 증명해야 합니다**(`fal_dispatch.py:83`, `:95`). 다른 모델이라는 이유만으로 거절하도록 바꾸는 것은 D15 위반입니다.

4. **[High — 계획 누락] quote 공급·갱신과 단가 검증 계약이 없습니다.** `fal_models.py:53`은 정확한 입력 해시·모델에 묶인 quote만 받으므로, 다른 모델이나 새 프롬프트에 기존 견적을 사용할 수 없습니다. 반면 단가·과금 단위·수량은 검증하지 않습니다(`:55`). **모델/프롬프트/비율/5→10초 변경 시 이전 quote 거절, 새 quote 취득 실패 시 준비 차단, 단가×수량·총액·반올림 일치 테스트**가 필요합니다. fixture 성공을 실제 가격 연결 성공으로 판단하면 안 됩니다.

5. **[Medium — D15 provenance 누락] 기존 `source.mode`는 permission이 아니라 실행 엔진입니다.** `production_tools.py:94`와 `local_creation_tools.py:127`은 `run['engine']`을 저장합니다. 미디어 action에는 요구된 대화 모델·permission·effort 출처가 없습니다(`fal_dispatch.py:56`). **서버가 생성 시점 값을 동결하고, 설정 변경·재시작 후에도 보존하며, 모델의 위조 인수를 거절하는 테스트**가 필요합니다. 현재 permission 상한의 `min` 집행은 유지해야 합니다(`agent_preferences.py:61`).

6. **[Medium — 새 견적 노출의 의미 오류] 오래된 입력의 견적도 `estimated` 합계에 들어갑니다.** 합산은 소유권·보류/거절·만료만 확인합니다(`fal_dispatch.py:79`). 실제 승인은 장면 revision·계획 문맥·media snapshot까지 검사합니다(`:93`). **현재 유효 견적과 저장 당시 견적을 구분해야 합니다.** 미디어 선택/입력 변경은 승인 무효화, 대화 모델만 변경은 기존 미디어 승인 보존, `full-v1` 호환성을 테스트해야 합니다(`model_selection.py:63`, `:73`).

7. **[Medium — 전송 승인 가정 불일치] “결과는 이어쓰기 승인 후 전송”은 legacy에는 성립하지 않습니다.** 일반 경로는 승인 대기로 멈추지만(`chat_general.py:790`), legacy는 도구 결과를 다음 메시지에 넣고 계속합니다(`chat_runtime.py:330`). 새 scene-status도 이 차이를 고려해야 합니다(`production_context.py:224`). **최초 승인에 후속 결과 전송이 포함되는지 명시하고, 거절·취소 후 전송 0 및 다른 대화 정보·경로·grant 비노출을 양쪽 경로에서 검증해야 합니다.** 현재 근거만으로 무승인 유출이라고 단정하지는 않습니다.

8. **[Medium — 용량·통합 검증 공백] 입력 상한과 실제 UI 수락 증거가 부족합니다.** worker 측정은 review/full_access 본문이 `/4` 추정부터 4096을 넘습니다(`tasks/A1-server-read-tools/result.md:77`, 위 evidence 디렉터리 기준). scene-status는 장면 수 전체에 상한이 없습니다(`scene_project.py:303`). UI 실화면과 3D 조회 HTTP 종단 검증도 미실행입니다(`tasks/B1-chat-ui/result.md:104`, `tasks/C1-3d-read-schema/result.md:119`). **대규모 결과·이력의 크기 제한, 초과 시 동작, 375/1280 양 테마에서 dirty/실패/포커스 보존을 수락 조건으로 추가해야 합니다.**

9. **[Medium — 후속 연결 시 필수] 3D 인수 검증을 권한 검증으로 오인하면 안 됩니다.** `scene_spec.py:207`은 형식·범위만 검사하며, asset도 구조 검증입니다(`:228`). **S7b에서 소유권·현재 head·잠긴 필드·자산 권리/차단 상태를 서버가 재검사하고, 승인 시점 변경·거절·중복 호출·재시작을 검증해야 합니다.** 현재 스키마 추가 자체가 자동 승인이나 삭제 경로를 만들지는 않습니다.

10. **[Low — 계획 모순] 상단의 이전 D15 결정을 제거해야 합니다.** `PLAN:4`는 다른 모델을 거절한다고 적고, 변경된 `PLAN:148`은 제안을 허용합니다. 모델 선정 이유·가격·provenance의 구현 담당 파일과 수락 테스트까지 작업 단위에 명시해야 합니다.

검증 근거: 현재 12개 파일의 전후 diff와 관련 호출·테스트·worker 보고를 확인했습니다. 파일 변경·게이트 재실행은 없으며, 이번 리뷰에서 전체 회귀·실화면·실제 공급자 실행은 수행하지 않았습니다.