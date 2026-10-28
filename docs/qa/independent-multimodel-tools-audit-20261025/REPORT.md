# 07 멀티모델 도구 — 독립 staging correctness 감사

**판정: 부분 통과 / 통합 전 보완 필요. 재현 결함 MM01(P1) 1건.**

승인 우회·숨은 공급자 대체는 검사 범위에서 재현되지 않았다. 그러나 새 채팅에서 도구 실행에 필요한 현재 작업 식별자를 조회할 수 없어, “이미 승인한 제작/출력을 채팅으로 실행”하는 연결을 완료로 볼 수 없다. 기존 모델 테스트는 필요한 식별자를 fixture에서 직접 넣어 이 누락을 가린다.

## MM01 — 모델용 현재 작업 문맥 누락 (P1, 기능 차단)

**범위:** 고정 19파일 staging. frontend 미통합과 별개인 서버 도구 입력 계약 문제. 권한 상승/보안 결함으로 분류하지 않는다.

**재현:** [reproduce-context-gap.py](reproduce-context-gap.py), [실제 합성 Store 결과](context-gap.json).

1. 임시 Store에 사람 검토된 타임라인 v1과 실제 render approval ID를 만든다. 외부 호출 없는 새 ChatRuntime turn을 준비한다.
2. 모델에 제공되는 handoff와 `search_project_context`의 전체 결과를 취합한다.
3. 승인된 타임라인 버전/clip 상태/approval ID가 없다. `request_render`는 정확한 버전 및 approval ID를 필수로 요구한다. 숨겨진 ID 대신 `current-approved`를 사용하면 `VALIDATION_OR_HUMAN_APPROVAL_REQUIRED`로 차단된다.
4. 별도의 합성 Store에 applied plan→fal image action→사람 grant까지 만든 뒤 새 채팅을 준비한다. action/plan/grant ID와 실제 샷 이름이 모델 문맥에 모두 없다.
5. handoff가 제공한 샷 stable UUID를 `prepare_image_action.shot_id`에 사용하면 `INVALID_MEDIA_INPUT`으로 거절된다. 실제 서비스는 `p['shots'][shot]`의 이름 키(예: `장면 1`)를 요구한다. 모델이 그 키를 조회할 도구가 없다.

**기대:** 모델이 서버의 현재 작품 조회 결과만으로 정확한 샷·후보·승인·타임라인 식별자를 얻고, 사람의 기존 승인을 재사용할 수 있어야 한다. 승인 발급·권한 확대는 그대로 불가해야 한다.

**실제/영향:** 사용자 또는 fixture가 내부 ID를 별도로 주입해야 한다. 새 모델/새 run에서 이미 승인된 미접수 action의 실행, 현재 출력 접수, 기존 EDL을 근거로 한 정확한 편집 제안이 정상적으로 연결되지 않는다. 이미 접수된 job ID/state/mode의 인계·조회는 통과했으므로 전체 handoff가 실패했다고 확대하지 않는다.

**원인 위치 (아래는 보관 snapshot 기준):**

- [chat_protocols.py:55](snapshot/chat_protocols.py#L55): handoff는 제한된 model snapshot·공개 대화·job id/state/mode만 제공.
- [model_selection.py:60](snapshot/model_selection.py#L60): shot stable ID/selected/revision만 제공; name/Take refs/EDL/approval/action 목록 없음.
- [production_tools.py:70](snapshot/production_tools.py#L70): 검색은 음악·canonical context·source만 반환.
- [production_tools.py:12](snapshot/production_tools.py#L12): plan/action/grant/shot refs/timeline version을 필수 인수로 선언.
- [fal_dispatch.py:48](snapshot/fal_dispatch.py#L48): prepare는 샷 이름 키로 조회.
- [local_creation_tools.py:73](snapshot/local_creation_tools.py#L73): 현재 타임라인과 정확한 사람 approval ID를 검사.
- [tests/test_local_creation_tools.py:85](snapshot/tests/test_local_creation_tools.py#L85) 부근의 fixture는 `self.grant()`로 내부 승인 ID를 직접 공급한다. 실제 모델이 조회해서 얻은 값이 아니다.

**관련 요구:** SPEC-MS-001 MS-FR-02 / AT03 공통 제작 도구 실행 연결, MS-FR-11 / AT18 승인 문맥 인계. MS-FR-05 / AT09–10 사람 권한 검사는 유지할 제약이다. 이 재현은 해당 AT의 전체 실행을 뜻하지 않는다.

**최소 수정:** 현재 작품에 한정된 read-only production-context 도구/응답을 추가하거나 기존 검색을 확장한다. 정확한 shot key+stable ID+revision, 허용된 Take refs와 현재 권리 상태, 현재 EDL/version, 검토된 plan/action과 재사용 가능한 승인 handle, 현재 ontology revision을 필요한 범위만 제공한다. 사용자 화면의 기본 카드에 내부 ID를 표시할 필요는 없다. 대안으로 명시적인 현재 대상 요청을 서버가 고정된 승인 대상으로 해석하되 승인 hash/version 재검사는 유지한다. 새 fake 모델 시험은 fixture가 grant/shot 이름을 응답에 넣지 않고 오직 서버 조회 결과에서 도구 인수를 조립하도록 구성한다. 모델 교체 후에도 같은 절차를 검사한다.

## 통과 근거

독립 임시 source snapshot에서 network connect/bind를 fail-fast로 막고 다음을 실행했다.

- [focused-tests.log](focused-tests.log): 기존 집중 시험 **53개 통과**. protocol, 신규 chat/fal/local tools, 기존 chat runtime. 실제 Store·임시 DB·합성 미디어/fake transport만 사용.
- [independent-controls.log](independent-controls.log): 감사자가 추가한 **10개 control 통과**. [실행 코드](independent-controls.py).
- 별도 MM01 재현은 위 통과 개수에 포함하지 않는다. 구현 보고의 전체306/HTTP tests를 독립 실행했다고 주장하지 않는다.

| 계약 | 독립 관찰 |
|---|---|
| 공급자 envelope/도구 결과 | Claude/OpenAI/xAI 공통 Store 실행, 호출 ID 연결·다른 run/provider 결과 거절; endpoint/approved/권한 도구 주입 거절 |
| 모델 선택 | 프로젝트 Schnell 기본값과 명시 Pro1.1 선택을 정확히 구분; 명시 모델의 연결이 없으면 첫 모델로 대체하지 않고 차단 |
| 멱등/새 후보 | 같은 call ID+내용은 같은 action; 같은 ID+다른 내용은 충돌; 새 call ID는 새 후보 action이며 자동 grant/예약 없음 |
| 예산/불명 접수 | 다른 두 승인 action이 한 작업 예산을 경쟁하면 한 건만 예약·접수; 응답유실은 예약과 actual unknown 유지, 재시작/재조회는 추가 submit 없음, 새 후보도 예산 차단 |
| 제출 직전 검증 | grant 철회, 원본 파일 byte 변경, price revision 변경을 제출 전에 차단. 확인된 미전송만 예약 해제 |
| 모델 교체 | chat-only 변경 후 기존 media job/grant 유지; media 선택 변경 시 차단. 새 모델 handoff에 기존 job id/state/mode 전달 |
| 제안/사람 승인 | timeline·memory 도구는 제안만 저장. stale/다른 작품/authority 인수 차단. 사람 적용 전 EDL/canon 불변. render는 현재 사람 approval 요구; 기존 승인별 receipt 재사용·취소 뒤 자동 재생성 없음 |
| token/cost 계약 | provider별 요율로 계산, input counter 초과 시 메시지 제출0·미전송 예약 해제, Anthropic max_tokens/Responses max_output_tokens 전달, output usage에 reasoning 부분을 다시 더하지 않음. 미지원 tier/cache·usage 오류는 확정 비용을 꾸미지 않고 보수적 reservation 유지 경로 |
| 실제 연결 상태 | 등록 상태는 모두 unverified/blocked, 자동 active 없음. OpenAI/xAI는 disabled/미검증 counter 경로에서 credential supplier 미호출. noMCP/이미지·영상 fal 경로 유지; Runway 실행 경로 추가 없음 |

추가 control의 첫 실행에서는 금액 문자열 `0`과 `0.000000` 비교 차이로 assertion 1개가 실패했다. 기능 결함이 아니며 동일 통화 정수 단위 비교로 harness만 수정했다. [첫 로그](independent-controls-initial.log)도 보존했다. 수정 후 10개 통과했다.

## 고정 증거·한계

- 패치 SHA256: `44cea955e8f21ac7e62cf440bb80490dc1e3ac30e06c42a04770b964dff65acd`, 19개 파일. 앞선15개가 아닌 최신 manifest의 after hash를 전부 확인했다.
- [snapshot.json](snapshot.json): 캡처 시각, 원 stage/독립 임시 위치, bytes/mtime/SHA256. [snapshot/](snapshot/)은 실행했던 Python source/test의 지속 보관 사본이다. [finish-evidence.json](finish-evidence.json)은 종료 시 staging drift와 보관 hash 대조다.
- 원본 소스·원본 패치·공유 DB/서버를 변경하지 않았다. 소스 import 및 Store 실행은 독립 snapshot/임시 synthetic DB만 사용했다. key/.env/API/listener/browser 접근 없음.
- live 모델 정확한 token counter·현재 계정 모델 지원·실청구·서비스별 실제 protocol 호환·실제12조합·frontend는 미검증이다. fake count와 공식 구조를 흉내 낸 응답의 성공은 live 검증을 대체하지 않는다. live 모델 활성화 승인을 주지 않는다.
- MM01 수정 후 그 조회→도구 연결만 좁게 재검증하면 된다. 다른 범용 감사로 확대할 필요는 없다.
