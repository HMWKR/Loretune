# Aethon · 일반 대화 제작 도구 연결 + 현재 작업 개선 — 실행 계획 (검토용 초안)

작성 2026-10-28 · 상태: **승인됨 — 실행 중**
> 사용자 승인 인용: "권장대로 진행을 해주며 전체적으로 전부 다 진행을 해줘" (2026-10-28). §6 결정은 모두 권장값으로 확정. D15(대화 모델의 model_id ≠ 프로젝트 선택 → 거절)는 사용자 질문에 근거 설명 후 이의 없으면 거절로 진행, 기존 이미지 준비 경로에도 같은 규칙 적용·보고.
> 실행 시점 사실: 57888 검토 서버 실행 중(PID 39837, 조작 금지), 8765 미실행. 편집 전 사본 `before/`(240파일, `before-inventory.json`).
근거: 읽기 전용 워크플로 3개(공백·계획 8에이전트, 개선점 41에이전트, 패턴 추상화 5에이전트). 각 결과는 반박 검토(critic)를 거침.
원자료: `~/.claude/projects/-Users-leesungmin-Desktop-Loretune/1ebfb89f-…/subagents/workflows/{wf_ab48758b-349,wf_f4d8f59a-70c,wf_d7cf8986-d38}/journal.jsonl`

---

## 0. 이해한 의도와 가정

- 대상: 인계 문서 "다음 순서" 3번 **일반 대화 제작 도구 연결(AGENT-TOOLS-02)** + 방금 끝난 **검토 카드 이동 기능의 개선**.
- 가정 A1: "진행해"는 1번(문서 등록 승인)·2번(녹화 검토)·4/5번(실제 Claude·AI 영상·비용) 승인이 **아니다**. 이번 범위의 외부·유료 호출 0.
- 가정 A2: 사용자 서버 8765·검토 서버 57888·그 데이터·Ego Space는 건드리지 않는다. 실화면 검증은 전용 포트+임시 데이터 폴더.
- 가정 A3: Git 저장소가 아니므로 편집 전 대상 파일을 `.omo/evidence/<작업>/before/`에 사본+해시로 보존한다(되돌리기 수단).
- 원칙: Karpathy 4원칙(가정 명시·최소 코드·외과적 변경·검증 가능 목표), 새 프레임워크·의존성 금지, 기존 카드·토큰 재사용.

---

## 1. 현재 작업(검토 카드 이동) 개선 — 확정 32건을 8묶음으로

반박 검토를 통과한 것만 실었다(기각 6건은 §1-b). 등급은 검토자 보정 후 값.

| 묶음 | 등급 | 문제 → 이유 | 근거(파일:줄) | 수정 |
|---|---|---|---|---|
| I1 | **High** | 같은 턴에 같은 장면 제작안이 2개+면 버튼 이름이 동일 → 스크린리더·음성제어·시각 사용자 모두 구분 불가 | `general-chat-ui.js:58`, 다중 생성 가능 `production_tools.py:31`(tool_rounds=8), 호출마다 새 action `action_execution.py:61` | 순번/모델/승인상태를 라벨·aria-describedby에(내부 ID 미노출) + 다중 대상 테스트 |
| I2 | Medium | 실패 뒤 성공해도 "열지 못했습니다"가 남음 / 마지막 단계 실패 문구가 이미 숨겨진 채팅 패널에 써져 화면·aria-live 모두 미전달 / 실패 사유 3종을 문구 1개로 처리 / 대체(superseded)된 이동에도 실패 문구 | `general-chat-ui.js:67`, `chat-sidebar.js:154-155,214` | 성공 시 문구 정리, reviewMediaAction이 사유 코드(dirty·missing·blocked·superseded) 반환 → 해결 행동 안내, 마지막 단계 실패 시 버튼으로 복귀+보이는 status |
| I3 | Medium | busy/inFlight 동안 검토 버튼이 활성처럼 보이나 무반응 / 재렌더 시 검토 버튼 포커스 소실 / 중간 실패 시 단계·샷 전환이 되돌려지지 않고 포커스가 제목에 남음 | `general-chat-ui.js:42,53-58,67`, `chat-sidebar.js:138-155`, `index.html:859` | controls()에 검토 버튼 포함, 렌더 전후 포커스 복원(기존 :53-56 패턴), 사전 확인 후 전환·실패 시 원 버튼 포커스 |
| I4 | Medium | 마우스 이동 시 도착 카드 시각 표시 없음(`:focus-visible`만) / 카드 article 접근 이름 없음 / 이동 중 포커스 여러 번 튐 | `studio.css:757,289,792`, `chat-sidebar.js:97`, `index.html:801,859,1022` | 기존 `--ui-focus` 토큰으로 일시 강조, h3 id+aria-labelledby, setStep 포커스 생략 옵션 |
| I5 | Low | 버튼 묶음 컨테이너 미사용, 버튼 문구가 결정 상태 미반영 | `general-chat-ui.js:58`, `studio.css:953,991` | 기존 `.general-chat-actions` 재사용, '보기 · 거절됨' 꼬리말 |
| I6 | Medium | 테스트 공백: VM 테스트가 종료코드만 봄(끝나지 않는 비동기 회귀 통과) / esc를 테스트가 복제 / 클릭 핸들러·실패 문구·dirty 같은 장면·375 장면 전환 미검증 / 바뀐 파일을 읽는 기존 테스트 4개 미재실행 | `tests/test_general_chat_review_navigation.py:89-93`, `tests/general_chat_review_navigation.cjs:36,40,47,52`, `worker/related-ui-tests.log` | 완료 플래그 단언, 제품 esc 슬라이스 주입, 핸들러 VM 케이스, 누락 4개(`test_general_model_schedule_ui`, `test_agent_work_status_context`, `test_chat_general_http`, `test_general_chat_media_preparation`) 재실행 |
| I7 | Low~Medium | 증거 문구가 실제보다 강함: "연속 녹화"=약 5fps 캡처를 24fps 복제 / POST 0·DB 불변이 고정 리터럴 / "공개 사본 변조 불가" 단언은 실패할 수 없음 / held·required 이동은 실패 시도에서만 관측 / 375 버튼 캡처에 버튼 없음 / REMAINING-WORK:21 "카드 이동 미구현" 잔존 | `worker/actual_navigation.cjs:91`, `recording.json`, `tests/test_general_chat_review_navigation.py:37-41`, `review-button-375.png`, `docs/qa/REMAINING-WORK.md:21` | 측정값으로 기록·재캡처, 문구 정정(문서 본문 수정만, 등록은 별도 승인) |
| I8 | Low (별도 과제) | 거절된 카드에 거절·보류 버튼 잔존 / 이동 후 대화로 돌아갈 경로 없음 | `index.html:802`, `chat-sidebar.js:154,214` | 기존 기능 범위 → 등재만, 이번엔 미수정 권장 |

### 1-b. 기각 6건(이유)
- 대체된 이동 후 실패 문구 덮어쓰기(재현 순서가 실제로 성립 어려움 → I2의 superseded로 흡수) · 장면 표기 차이(해악 없음) · 도착 카드의 action id 노출(접힌 진단 영역, 문구 다듬기 수준) · Puppeteer 사용(작업자 정책상 허용 경로 — 단 D12로 결정 필요) · 다른 대화 경계 테스트(저장 단위가 작품이라 유효) · 200% 조건 기록(참고 수준).

---

## 2. 일반화 패턴 — "Aethon 대화 도구 표준형"

우리 잘된 구현 16개 + Refero 실제 화면 10개(fal·Runway·Manus·Canva·Ozone·Cycle 등) + 공식 문서 13개(Runway·Luma·Kling·Descript·Claude Agent SDK·MCP·Gemini 영상이해)에서 추출 → 반박 검토로 6개 원칙 문구 정정.

**원칙 10개 (정정 반영)**
1. 도구 허용 = 정적 레지스트리 ∩ 실행 시점 권한(min) ∩ 사람이 승인한 manifest 선언. 새 허용 경로 금지. (`production_tools.py:36-55`, `agent_preferences.py:61-79`, `chat_general.py:396-397,424`)
2. 범위는 서버 주입(LISTS 필터) **+ 함수별 가시성 검사(take_visible·owns·own_items)를 신규 도구가 직접 호출**. 모델 인자는 도메인 대상만.
3. 결과 = 저장된 제안 엔티티 + 출처(run·call·model·mode) + 하지 않은 일을 밝히는 부정 플래그(applied=False, cost_approval=False, external_calls=0…). 예외: FullAccess AUTO_DRAFT는 applied=True + actor=agent-draft로 기록.
4. 견적 = 정확한 입력 해시·모델·가격 출처·만료에 묶인 quote(입력 바뀌면 무효). 대화 추론 비용 = 승인 상한 안 최악값 사전 예약 + 사후 정산.
5. 승인은 사람이 본 대상에 묶는다(manifest_sha256 / base_version / context_hash). 결정 페이로드에 그 값을 echo, 서버가 재계산 대조. 불일치는 거부(HTTP 409/400 또는 blocked+STALE_*). 자동 리베이스 금지.
6. 부수효과 1회: (call.id, digest) 영수증 재생, grant당 1회 실행, 증명 불가 결과는 outcome_unknown으로 동결·자동 재호출 없음.
7. 화면은 서버 투영만 그린다: {표시 필드, can_approve, can_execute, can_cancel, reason}. 상태는 enum→한국어 라벨, 미지 상태는 '상태 확인 필요'. 서버 ID는 data-*·접힌 진단에만.
8. 채팅 결과는 새 승인 화면을 만들지 않고 기존 카드로 연결만(정확히 1개 해석, await마다 재검증, 사용자 탐색 우선, dirty 보호).
9. 모델로 돌려주는 결과는 압축 영수증. 관찰형 결과엔 coverage(무엇을 어느 간격으로 봤는지) 필수. **도구 결과는 이어쓰기 승인 후 외부로 전송된다**는 점을 data_scope에 반영.
10. 자율 등급 상향으로 넓어지는 건 '되돌릴 수 있는 초안 버전'뿐. 비용·외부 전송·권리·최종 출력·권한 상향은 항상 사람. 에이전트는 권한을 내리는 쪽만 제안.

**가져오지 않는 패턴(이유)**: 한도까지 자율 지출(Luma Agents)·즉시 차감 / 답변 뒤 자동 진행(Manus) / 비용·권리에 '승인+기억' / 사용자 수정 사실을 모델에 숨김 / 확률적 분류기 자동 승인 / 대화 안 폴링 루프(MAX_ROUNDS=4 소모) / 전체 화면 차단 모달 / 비용 표시 없는 재생성(Canva·Meiro) / 새 도구 프레임워크·메타데이터 힌트를 집행 근거로.

**구조적 제약(새로 드러남)**: 일반 대화는 MAX_ROUNDS=4이고 도구 실행마다 사람의 이어쓰기 승인이 필요 → 한 턴에 실제로 부를 수 있는 도구는 약 3회. 따라서 여러 단계가 필요한 흐름(준비→견적→이동)은 **카드 버튼(서버 투영)으로 넘기는 것**을 기본으로 한다.

**새 도구 접점 체크리스트(실제 목록)**: TOOLS → chat_protocols 스키마(list/dict) → validate(0 허용 키 포함) → READ_TOOLS/ALLOWED_TOOLS → execute 이름 집합+분기 → local_creation_tools._execute 분기 → keys 튜플(SAVEPOINT 롤백) → compact_result → (UI) toolLabels·reviewTargets·reviewMediaAction → 테스트.

---

## 3. 공백 대조 요약

| 역량 | 지금 | 이번 빌드 | 외부/유료 |
|---|---|---|---|
| 영상 제작안 준비 `prepare_video_action` | 스키마·분기 있음, 대화 미노출, 이동은 image 전용 | ✅ S4·S5 | 없음(fixture quote) |
| 견적 `estimate_media_plan` | 있음, 미노출. **held/rejected도 합산, owns 필터 없음** | ✅ S3(선행 수정 포함) | 없음 |
| 작업 상태 `get_generation_job` | READ_TOOLS엔 있음, 미노출. 3개 테이블 조회 | ✅ S2 | 없음 |
| 영상 생성 실행 `request_media_generation` | 사람 버튼만 | ❌ 계속 미노출(불변 테스트로 고정) | 있음 |
| 3D 장면 상태 읽기 | 없음 | ✅ S6 | 없음 |
| 3D 변경 제안 | 없음(provenance 필드도 없음) | ✅ S7a·S7b | 없음 |
| 3D·모션 카드 이동 | 없음 | ✅ S8 | 없음 |
| 승인된 3D 로컬 렌더 요청 | 없음 | 결정 D6 후 S12 | 없음(로컬 Docker) |
| 안전 설정 읽기 | 없음 | ✅ S9 | 없음 |
| 설정 변경 | 없음 | 선호 후보 제안만 S10(권한 상향·모델 변경 도구 금지) | 없음 |
| 자산 추천 | 없음 | 내부 자산 텍스트 추천만(외부 검색은 범위 밖) | 외부 검색=있음 |
| 음원 측정값 관찰 | 없음 | S11(결정 D9) | 이어쓰기 시 외부 전송됨 |
| 영상 프레임 관찰 | 없음 | 설계 문서만 S13 | 있음 |

---

## 4. 작업 단위(반박 검토 반영본)와 병렬 트랙

파일 소유를 트랙별로 나눠 **같은 파일을 두 트랙이 동시에 쓰지 않는다.** 공용 파일(`chat_general.py` ALLOWED_TOOLS, `general-chat-ui.js` toolLabels)은 트랙 A·B 소유로 고정하고, 다른 트랙은 요청만 넘긴다.

### 트랙 0 — 기준선 (선행, 단독)
- [x] **S0 기준선 회귀 드라이버 신규 작성** — 완료: `regression-s0/receipt.json` passed, 931개/553.437초, skip 0, warning 0, 소스·보호증거 불변, 잔존 프로세스 0. 문서 checker 시작=blocked(`doc-gate-start.txt`, 예상대로).: 기존 run.py는 출력 경로·소스 동결 목록이 고정돼 그대로는 실패 → 현재 소스 목록 새로 생성, 이전 수락 대비 의도된 변경 5파일 선언, OUT 인자화. 전체 회귀(약 930개·10분) + 문서 checker(읽기 전용) 시작 기록. 합격: exit 0, skip 0(skip은 결함), 소스 전후 해시 동일, 잔존 프로세스 0.
- [ ] **S1 불변 테스트** `tests/test_general_chat_tool_invariants.py`(신규): request_media_generation 대화 미노출, 삭제 이름 ∩ ALLOWED_TOOLS = ∅, AUTO_DRAFT 정확히 5개, **예전 대화 경로(chat_runtime 기본값=TOOLS 전체)도 단언**, 거절 시 상태는 outcome_unknown·미디어 예약(project:%) 0.

### 트랙 A — 서버 읽기·준비 도구 (소유: `chat_general.py`, `agent_preferences.py`, `app.py`, `fal_dispatch.py`, `production_tools.py`, `chat_protocols.py`, `local_creation_tools.py`)
- [ ] **A-pre 사전 가드 이전**: `job_id`·`plan_id`·`source_shot_id` 검사를 HTTP 사전 가드에서 도구 내부 구조화 거절(not_found/STALE)로 옮김(기존 `append_clips` 패턴 `app.py:534-548` 재사용, 사람 HTTP 가드는 약화하지 않음). 이유: 지금은 없는 id 한 번에 turn이 outcome_unknown이 되고 응답 비용은 이미 정산됨.
- [ ] **S2 get_generation_job 노출**: 로컬 렌더·3D job 케이스 포함, grant_id 결과 제외(D 결정), read_only에서도 허용.
- [ ] **S3 estimate_media_plan 노출**: 선행 수정 — held/rejected 제외 + owns 필터 + '준비된 작업 합계이며 계획 전체 견적 아님·청구 아님' 라벨.
- [ ] **S4 prepare_video_action 노출**: model_id가 프로젝트 선택과 다를 때 처리(D15), integration_blocked 모델 준비 시 문구, 없는 shot/take 구조화 거절.
- [ ] **S9 get_agent_settings(읽기)**, **S10 propose_preference_rule(후보만)** — S10은 `app.py` preference_items 전달 수정 포함, 같은 category에 active 규칙이 있을 때 동작 명시.
- 공통 합격: 슬라이스마다 **도구 정의+대표 결과 크기를 오프라인 측정해 입력 4096토큰 상한 대비 여유 기록**, SQLite 전 테이블 fingerprint(run·turn 외 불변), assert_no_media_execution 0, `test_chat_protocols` 개수 단언 변경은 의도된 diff로 보고.

### 트랙 B — 대화 UI (소유: `general-chat-ui.js`, `chat-sidebar.js`, `studio.css`, `index.html` 해당 함수, 관련 cjs/VM 테스트)
- [ ] **I1~I5 개선 반영** (위 §1)
- [ ] **S5 영상 제작안 카드 이동**: reviewTargets를 {prepare_image_action:'image', prepare_video_action:'video'} 매핑으로
- [ ] **S8 3D·모션 카드 이동**: 기존 viewWork 재사용, dirty 3D 입력 보존
- [ ] 트랙 A가 요청한 toolLabels 문구 반영
- **디자인 게이트(요청 반영)**: 각 UI 단위 완료 전 `/impeccable` critique→audit→polish, `/hallmark` 검사. 기존 Hallmark FAIL15/WARN1은 기준선으로 보존(해석으로 PASS 처리 금지). 실화면은 aside(또는 D12 결정) + `run-qa.sh` 375·1280 × 다크·라이트 캡처·axe → PNG 직접 확인.

### 트랙 C — 3D·문맥 읽기 (소유: `production_context.py`, `scene_project.py`, `scene_spec.py`, 신규 테스트)
- [ ] **S6 search_project_context 'scene-status' 질의**: grant id·경로 미노출, 다른 대화 장면 불가시.
- [ ] **S7a 3D 제안 스키마·검증기**(scene_spec SCHEMA, 0 허용 키) → **S7b 도구 연결·provenance·Scene Studio 표시**(트랙 A에 분기 추가 요청). head=0(승인 버전 없음) 장면의 결과 명시, 차단·미확인 자산 교체 제안은 승인 시 거절 테스트.
- [ ] **S11 음원 측정값 투영**(D9 후): rights 미확인 음원 처리·data_scope 문구 결정 포함.

### 트랙 D — 테스트·증거 (소유: `tests/` 신규 파일, `.omo/evidence/agent-tools-02-20261028/`)
- [ ] **I6 테스트 보강**, **I7 증거 재측정·재캡처**(문서 문구 정정은 D 결정 후)
- [ ] S13 프레임 관찰 설계 문서(D10)

### 마무리 — 통합 검증 (단독)
- [ ] **S14**: 전체 회귀(S0 대비 수집 수 = 기준 + 신규), 실화면 UI→API→저장→재열기 증거(전용 포트·8765/57888 프로세스·데이터 해시 전후 동일·종료 후 잔존 0), impeccable·hallmark 결과, **codex read-only 교차 검증(main 직접)**, 문서 checker 종료 기록, 정직 보고(한 일/안 한 일/가정/미검증).

**순서**: S0 → S1 → (A-pre·S2·S3 ∥ I1~I5 ∥ S6·S7a ∥ I6) → (S4 ∥ S7b) → (S5 ∥ S8 ∥ S9·S10 ∥ S11) → S14.
**에이전트 운용**: 트랙별 구현 워커 1명(Workflow, 파일 소유 분리), 각 결과는 critic 반박 → main 종합 → codex 교차 검증 → main 승인.

---

## 5. 범위 밖 (이번에 하지 않음)
실제 Claude·AI 영상·유료 호출과 청구 검증 / request_media_generation 대화 연결 / 전송 gate·복구 승인 등록 경로 / job 취소·복구 도구 / 외부 자산 검색·다운로드 / 프레임·이미지 바이트 모델 전송 구현 / 대상별 파일 삭제 허가(AGENT-PERM-05) / 모드 상향·모델·effort 변경 도구 / 3D 메시 생성·scene_review 승인·최종 출력 승인 도구화 / AUTO_DRAFT 확장 / 문서 등록·분류·승격 실행. **AGENT-TOOLS-02 중 '일반 설정 allowlist'와 '추천 자산 도구'는 이번에도 미충족으로 명시.**

---

## 6. 결정이 필요한 사항 (권장값 포함 — "권장대로"로 답해도 됨)

| # | 질문 | 권장 |
|---|---|---|
| D0 | 인계 1번(문서 등록 검토안)·2번(녹화 검토)을 먼저 끝낼지, 이 계획과 병행할지 | 병행(이 계획은 그 승인에 의존하지 않음) |
| D1 | request_media_generation을 대화에 계속 미노출, 예전 대화 경로 기본값도 명시 목록으로 좁힐지 | 미노출 유지 + 예전 경로도 좁힘 |
| D2 | estimate_media_plan을 read_only 모드에서도 허용 | 허용(읽기) |
| D4 | 테스트·실화면 증거에 fixture quote 사용 | 허용, 실제 가격 원천은 후속 |
| D5 | 3D 제안 도구가 최초 장면 생성까지 할지 | 기존 장면 변경만 |
| D6 | 승인된 3D 로컬 렌더 요청 도구(S12) 열기 | 이번엔 보류 |
| D7 | owner 기록 없는 예전 3D grant 거부 | 거부 |
| D8 | 설정 쓰기는 선호 후보 제안만 | 예 |
| D9 | 음원 측정값 투영(진행 중 이어쓰기 무효화 가능, 외부 전송 포함) | 보류 후 S13과 함께 설계 |
| D10 | 프레임 관찰은 설계 문서까지만, 위치 | 예, `docs/design/` 아래(등록은 별도 승인) |
| D11 | 도구 설명문을 의미 있는 문구로(manifest 해시 변경) | 예 |
| D12 | 실화면 검증 도구: 프로젝트 기존 puppeteer-core 헤드리스 테스트 유지 vs aside만 | 기존 tests/ 회귀는 유지 실행, **새 증거 수집은 aside** |
| D13 | propose_timeline_edit·propose_memory_update도 범위에 넣을지 | 제외 |
| D14 | grant_id를 job 조회 결과에서 제외 | 제외 |
| D15 | 영상 준비 시 모델이 프로젝트 선택과 다른 model_id를 주면 | **사용자 변경(2026-10-28)**: 거절하지 않고 *제안*으로 허용. 허용 여부는 사용자가 정한 권한 모드를 따름(read_only=준비 불가, review·full_access=제안 가능, 실행은 항상 사람 승인). **권한 레벨과 무관하게** 카드·결과에 항상 표시: 선택 모델, 프로젝트 선택과 다른지, 이 작업 견적 총액·단가(초당/장당)·가격 종류·출처·가격 개정·만료, 그 모델을 고른 이유(대화 모델이 제출한 `model_reason`, 사람이 준비한 경우 '프로젝트에서 사용자가 선택한 모델'). 이미지 준비 경로에도 동일 적용. |

> 용어 확정(사용자): "노력 레벨이라고 하는거는 effot이며 권한은 permission을 말한거야" → 권한 = permission mode(read_only/review/full_access), 노력 = reasoning effort. 둘 다 사용자가 고른 설정이며 에이전트가 올리지 않는다. 제안 카드의 출처에 그 제안이 만들어질 때의 대화 모델·permission·effort를 함께 기록·표시한다(기존 source{run,call,model,mode}에 effort 추가).
> 사용자 인용(D15 변경): "어떻게 보면 그거에 대해서 제안을 한다고 생각하면 돼 그리고 그거에 대한 권한 부여 또한 사용자의 선택이니까 … 단가의 비용이라던지 그러한것들 또한 합리적으로 왜 이모델들을 하였는지에 대해서는 권한이 어느 레벨에 있던 나오게끔 진행을 해줘"
| D16 | 개선 묶음 I8(거절 카드 버튼·대화 복귀) | 등재만, 이번엔 미수정 |
| D17 | I7 문서 문구 정정(REMAINING-WORK 등 본문)을 이번에 할지 | 본문만 정정, 등록·분류는 하지 않음 |
| D18 | 이 계획서를 프로젝트에 보존할 위치 | `.omo/evidence/agent-tools-02-20261028/PLAN-ko.md` |

---

## 7. 주요 위험
- 사전 가드 이전(A-pre)은 사람 HTTP 경로를 약화하면 안 됨 → 사람 경로 기존 테스트 전후 동일 단언.
- 도구 정의 증가로 입력 4096토큰 상한 초과 가능 → 슬라이스별 크기 측정, 여유 없으면 모드·질의별 노출 분리를 결정 항목으로.
- `test_chat_protocols` 개수 단언·VM 테스트의 함수 경계 문자열 마커가 의도적으로 깨짐 → 의도된 diff로 구분 보고.
- native 3D 회귀 env의 Blender 경로가 `/private/tmp` 아래 → 재부팅 시 skip이 PASS로 오인될 수 있어 skip 0을 합격 조건으로.
- 문서 게이트는 현재 blocked(REGISTERED_SOURCE_OUTDATED 등) → 본문을 고쳐도 blocked 유지가 정상, 오래된 해시를 덮어 경고를 없애지 않음.
- 영역 보고의 줄 번호 일부 어긋남이 반박 단계에서 발견됨 → 구현 시점에 재확인.
