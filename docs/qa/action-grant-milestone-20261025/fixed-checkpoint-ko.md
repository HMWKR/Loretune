# 실행 승인 UI · 모델 인계 · 고정 런타임 검증

2026-10-25. 이 문서는 같은 디렉터리 `REPORT.md`의 과거 체크포인트를 갱신한다. 테스트 수는 기능 완성도가 아니다. 실제 AI 영상은 이번 검증에 사용하지 않았다.

## 고정 상태

- 앱 코드 고정 시각: 2026-10-25T10:27:42.648840Z. URL: http://127.0.0.1:8773, 격리 데이터 `/tmp/loretune-ms-qa-20261025`, 소유 exec session 60587.
- `fixed-runtime.json`의 app.py/index.html/rehearsal_workflow.py/action_execution.py/production_tools.py/chat_protocols.py/anthropic_ontology.py 해시가 현재 파일과 모두 일치한다. 이후 변경은 별도 합성 평가 런처·테스트·보고서뿐이다. QA 중 앱 소스 drift를 만들지 않았다.
- 전체 HTTP 포함 회귀: **194개, 23.917초, 모두 통과**. `frozen-app-evaluation-regression.log`. 이전 189개 23.856초 로그도 보존했다. 새 5개는 답변 평가기의 문맥 축약·출처·토큰 사전 차단·예산/비밀 보호 검사이며 제품 기능 5개 완료를 의미하지 않는다.
- 기존 8765 서버/사용자 실제 데이터/다른 브라우저 공간은 변경하지 않았다. 기존 `ps` 거절을 재실행하지 않았다. 승인된 localhost 시험과 소유 exec session 종료/재시작만 사용했다.

## 수정한 실제 결함

| 결함 | 변경 | 검증 |
|---|---|---|
| B01: 새 action job이 모델 전환 handoff에서 누락 | `action_execution.project_jobs`에서 legacy/new 작업을 동일 workspace/project로 조회. Store `model_handoff`와 도구 조회가 이 함수를 공유 | `test_b01_handoff_preserves_new_job_after_model_switch`: 모델 설정 변경 후 prepared job ID/mode 유지, 다른 프로젝트에 미노출 |
| B02: 없는 action ID가 repair 오류를 남기지 않음 | 저장점으로 실행 부작용만 롤백하고 `INVALID_ACTION_REFERENCE`와 repair counter를 저장. 승인 부족·stale 문맥과 인수 오류 구분 | `test_b02_invalid_references_are_persisted_and_bounded`: 2회 오류 후 안전 중단, 예약 0 |
| 사람 승인 카드가 채팅 단계 안에 있어 승인 후 장면 단계에서 사라짐 | 카드 영역을 inspector로 이동하고 현재 장면 준비 버튼 제공 | 실제 브라우저에서 보류→승인→실행→후보 승인→작업대 이동 완료 |
| 음악 구간 미확정 계획도 승인 버튼이 활성 | 시간 미정 계획의 승인 비활성, 이유·음악 입력 이동 제공. 원문 입력 유지 | 소스/전체 회귀 통과. 디자이너의 기존 uncertain 재제출은 반복하지 않음 |

독립 감사 원본은 수정하지 않았다. B01/B02는 기능 측 재현·회귀 결과이며 독립 재감사 완료라고 주장하지 않는다. F01–F04/R01/R02 이전 수정도 전체 회귀에 포함되어 있다.

## 실제 사용자 흐름 증거

대상은 별도 프로젝트 **실행 승인 QA 20261025**이다. 합성 클릭 음원과 단색 PNG만 사용했다.

1. 브라우저에서 요청과 장면 문구 입력, 계획 저장·검토·샷 추가.
2. 장면의 모의 작업 준비, 보류, $0 모의 작업 승인. 불변 action/grant/예약/job 영수증 저장.
3. 승인한 작업 실행, 실제 PNG 파일 검증·저장·Take 등록. **단색 fixture이며 AI가 아님을 화면에 표시**.
4. 후보 검토 승인 후에도 선택된 Take는 자동 변경되지 않음. 작업대로 이동해 사용자가 Take 1 선택.
5. 타임라인 동기화, 한국어 자막 0–1초 입력, 편집 v1 저장·승인, 렌더 큐 등록.
6. 완료 출력 재생 화면에서 duration=2, width=1920, height=1080, readyState=4, video error=null 확인. 서버 재시작 후에도 유지.

| 산출물 | 확인값 |
|---|---|
| Job | `d8ea0fc45c4d4f7e9737e02fdf09696a` |
| MP4 | `human-flow-output.mp4`, 2.000초, 1920×1080, 24fps, 음원 48kHz, subtitle track |
| MP4 SHA-256 | `6a62802edef795e729b2ed7ffde46abb13a7d757462f6f94122ec3706fb0bf26` |
| 자막 | `human-flow-output.srt`: 00:00:00,000–00:00:01,000, “모의 후보 승인 검증” |
| 고정 manifest | `human-flow-output.json`: 선택 Take/음원 해시, 구간, 자막·출력 버전 및 검증 메타데이터 |
| 캡처 | `human-candidate-approved.png`, `human-output-completed.png` 저장 후 이미지 확인 |

음악·자막 트랙 존재와 브라우저 재생 준비를 확인했다. 이번 출력은 사람이 만든 장면을 의미적으로 그린 영상이 아니다. 모든 장면 수/오디오 경계의 수작업 청취·프레임별 검사는 이 한 건의 증거로 대체하지 않는다.

## SPEC-MS-001와 이번 증거의 관계

| 요구 | 이번 증거 | 아직 부족한 기준 |
|---|---|---|
| MS-FR-02 / AT03–04 | 실제 Claude의 문맥 도구→tool_result→계획 저장→최종 근거 답변. 별도 합성 런처 | 일반 앱 채팅 입력의 지속 실행 transport/UI 통합, 다른 공급자 live |
| MS-FR-05/06 | 로컬 사람 승인 UI와 모델에 노출하지 않은 grant controller | 실제 다중 사용자 인증/역할 위임, 유료 dispatch 연결 |
| MS-FR-07 | 완결 인수 검사, invalid action 오류 보존·횟수 제한, refusal/incomplete 계약 테스트 | 실제 streaming 조각·중단·교차 모델 검증 |
| MS-FR-11/12 | B01 job 인계 및 private reasoning/pending provider ID 배제 테스트 | 실제 두 공급자 전환, 검색 embedding 서비스 |
| MS-FR-13/15/18 | dependency/중복 admission/동시 예산/unknown 예약 테스트, UI 승인 영수증 | 일반 외부 asset 사용권 조회를 새 action claim에 연결(G01), 실제 이미지·영상 결과 회수 |
| MS-FR-24 | 파일 검증·저장·등록 전 앱 완료 금지 계약, 기존 fal 실패 기록 보존 | fal private 결과 수신 실경로 해결 |
| MS-FR-26/27 | 실제 Anthropic request/usage/hash와 공통 tool adapter, fake 세 공급자 envelope | 전체 provider 연결·stream·멀티모달·실청구 대조 |

따라서 38 MS-AT 전체 통과나 원본 96 FR/143 API 전체 완료를 주장하지 않는다.

## 다음 작업과 제한

1. 디자인 재검증용 source freeze는 지금부터 바로 사용 가능하다. 해제 전에는 앱/HTML/backend를 수정하지 않는다.
2. 실제 Claude 호출은 별도 합성 런처에서만 수행했다. 일반 사용자의 채팅 입력을 외부로 자동 전송하는 UI는 아직 완성되지 않았다.
3. 새 action 경로의 일반 외부 asset 사용권 lookup→claim, 실제 provider dispatch/회수 연결은 남았다. 지금 모의 경로는 외부 입력 asset을 받지 않으므로 이를 실제 제공자 권한 검증 완료로 세지 않는다.
4. 실제 200/400% browser zoom, screenreader, 키보드만의 전체 제작 여정, 긴 프로젝트 부하/실사용자 실험은 미완료. 캡처에서 미디어/하단 조작의 높은 스크롤 위치도 디자인 후속 대상이다.
5. fal 추가 생성·기존 403 재시도·공개 fallback은 하지 않았다. 다중 사용자/클라우드 배포 준비도 미검증이다.
