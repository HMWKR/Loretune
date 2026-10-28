# MM01 통합 후 독립 재검증

**PASS — MM01(P1) 수정 확인, 이 이슈와 좁은 감사 범위를 종료한다.** 새 correctness blocker 없음.

## 원 반례 전후

| 관찰 | 이전 19파일 staging | 현재 통합 snapshot |
|---|---|---|
| 모델 문맥의 render approval handle | 누락 | handoff/search execution_targets.timeline.grant_id에 존재 |
| 현재 EDL/version | 누락 | timeline.version, clips, 음원·자막 제공 |
| 승인됐으나 미접수인 action/plan/grant | 누락 | 현재 작품 actions 및 approval_handles에서 조회 |
| 제공된 stable shot UUID로 prepare | INVALID_MEDIA_INPUT | proposed, 승인·예약·외부 호출 자동 생성 없음 |
| 모델 교체 후 조회만으로 출력 요청 | 내부 ID 수동 공급 필요 | Claude→Grok 조회 결과에서만 인수를 만들어 같은 job 재사용 |

[원 재현 전 증거](before-context-gap.json), [동일 재현 스크립트의 현재 결과](after-original-reproduction.json), [새 성공·거절 검증](evidence.json)을 보존했다. 원 스크립트의 `timeline_state_present:false`는 과거 키명 `timeline_version/timeline_head` 문자열만 찾는 관찰값이다. 새 실제 계약은 `execution_targets.timeline.version`이며 추가 시험은 이 필드를 직접 읽고 render 성공을 확인했다. 원 증거를 수정해 숨기지 않았다. 가짜 grant `current-approved`의 차단도 그대로 유지된다.

## 실행 증거

[recheck.py](recheck.py)와 [tests.log](tests.log): **24개 통과**, 5.438초. 독립 추가3개 + 현재 execution_context3개 + 관련 local tools11개 + protocol6개 + UI disclosure1개. 전체311개는 구현 세션 보고이며 이번에 다시 실행하지 않았다.

추가 검증은 사용자 식별자 수동 주입 대신 `search_project_context.execution_targets`에서 얻은 값을 사용했다.

- 새 모델에서 stable shot UUID로 image action 준비 성공, 기존 승인 action 접수 성공. transport calls 0.
- 외부 작품은 action/shot 목록이 비어 있고 원 작품 action/grant를 사용하면 INVALID_ACTION_REFERENCE로 거절.
- 조회 후 grant 철회 시 새 조회에서 handle 제외, 이미 queued된 job은 제출 직전 submission_blocked, transport calls 0.
- 이전 timeline/version handle은 편집 이후 STALE_VERSION으로 거절. 다른 작품 render handle도 거절.
- 읽기 조회는 canonical ontology/타임라인 버전을 변경하지 않으며, 기존 제안→사람 승인 및 역할 주입 거절 검사는 유지.
- 내부 handle을 얻어도 새 grant 발급·권한 확대·승인 없이 canonical/EDL 반영하는 도구는 생기지 않았다.

## 근거 위치

- `production_context.py:8–16`: 현재 작품의 stable ID/name 해석, 외부·모호한 ID 거절.
- `production_context.py:18–32`: 현재 작품의 샷/Take/EDL/출력 승인 및 scoped action/grant 조회. 조회 handle도 실행 시 재검사한다는 설명 포함.
- `chat_protocols.py:55–60`, `chat_runtime.py:141`: 실제 새 chat turn handoff에 같은 실행 대상 projection 포함.
- `production_tools.py:70–74`, `local_creation_tools.py:92`: 검색도 같은 read-only projection 사용.
- `fal_dispatch.py:59–66`: 도구에서 받은 stable ID를 현재 작품 샷 키로 변환한 뒤 기존 준비/검증 서비스 사용.
- `index.html:711,887,903`: creatorDiagnostic 닫힌 details, chat 진단 기록 및 media action 기록 분리. UI disclosure JS fixture 통과. 실제 브라우저/시각/접근성 재평가는 수행하지 않았다.

관련 요구: SPEC-MS-001 MS-FR-02/AT03, MS-FR-11/AT18의 MM01 관련 계약. MS-FR-05/AT09–10 권한 경계 회귀. 전체 MS-AT 통과 판정은 아니다.

## 고정 범위와 한계

[snapshot.json](snapshot.json)에 파일별 SHA256/mtime/bytes와 캡처 시각을 기록했다. 현재 캡처 대상 source/test는 integrated fixed-runtime의 hash와 모두 일치한다. app SHA256 `9d316c8269e0addfca609065912630b45b196107a84d86f3f997f0a75861c582`, production_context SHA256 `438b407e5e4574365bb9a75945fd2ac5eae7f0094b4ce18e7c02e211c912efd8`. [finish.json](finish.json)에 종료 시 drift 기록. [snapshot/](snapshot/)의 분리 사본에서만 import/시험했다.

실행은 synthetic 임시 DB/fake transports이며 socket connect/bind를 차단했다. 공유 소스·DB·서버 변경, 키/.env/실제 API/브라우저/listener 접근 없음. 원 감사 산출물은 보존했다. 실제 모델 호출, 일반 사용자 데이터, live 비용/권한 및 전체 제품 준비 상태는 이번 범위에 포함하지 않았다.
