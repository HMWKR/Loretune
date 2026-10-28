# 최종19파일 기능 계약과 표현 연결

2026-10-25 추가된 편집 제안/설정 제안/출력 계약을 읽었다. 원본 앱과 완성된 `integration-creator.patch`는 수정하지 않았다. 기존 screenshot과 후보 해시는 그대로다. 이 파일은 새 backend 구현이나 실행 화면을 검증했다는 뜻이 아니다.

| 새 계약 | 창작자 기본 표현 | 반드시 유지할 구분 | 통합 담당자가 연결할 동작 |
|---|---|---|---|
| timeline_edit_proposals | **편집 변경안 · 아직 적용하지 않음** | 기준 편집 버전/변경 장면·Take·시작점·길이, 음원·자막 유지 | **변경안 승인·새 버전 저장 / 보류 / 거절**. 기존 review_timeline_proposal 사람 경로만 호출 |
| 편집 적용 완료 | **새 편집 버전에 적용됨** | 적용 승인과 출력 승인은 별도 | 새 버전 출력 승인 필요. 이미 적용된 제안의 거절을 되돌리기로 쓰지 않음 |
| ontology 제안 저장 | **캐릭터·장소·스타일 설정 변경 제안 · 검토 대기** | 대상 이름·유형·설명·정확한 인용 근거/이 작품 범위 | 기존 ontology_apply 사람이 검토. ‘기억 저장 완료’/전역 세계관 수정 완료로 표시하지 않음 |
| render accepted/existing | 실제 state에 따라 **출력 대기 / 출력 중 / 출력 실패 / 출력 취소됨** | 접수≠완료. existing은 기존 작업 상태 확인 | job ID는 attrs/진단에만. 실패·취소 뒤 자동 새 작업 없음 |
| finished_verified=true | **출력 파일 준비됨 · 납품 검토 전** | 파일 검증≠사람 최종 승인 | 기존 결과 검토·저장·delivery_review 동작 |
| output_approved=true + finished_verified=true | **납품 검토 승인됨** | Take 승인/편집 출력 승인/납품 검토 승인 구분 | 이미 승인된 결과에 새 승인 필요처럼 표시하지 않음 |

`contract-copy.mjs`는 위 세 receipt의 기본 제목·상태·설명만 반환하는 독립 presentation adapter다. API 호출, gate, 값 저장, DOM 삽입은 없다. `test_contract_copy.mjs`8검사 통과. 내부 job/proposal/grant ID는 표시 객체로 전파하지 않는다. 비용·모델·승인 범위는 기존 실제 카드의 별도 필수 필드로 유지해야 한다.

현재 creator 후보의 drawJobs는 기존 state.jobs의 queued/running/completed 상태를 읽고, 원래 출력/자막/납품 handlers를 보존한다. raw tool trace는 진단 기록 안에 있다. 새 제안 데이터는 구버전 실행 서버에 없으므로 새 편집 변경안 비교/보류/승인 카드의 UI hookup은 기능 통합에서 필요하다. `contract-copy.mjs`만 추가한다고 그 UI가 연결되는 것은 아니다.

통합 시 위 정확한 문구를 실제 카드에 적용하고 실제 저장된 제안 및 오류/기준버전 변경 상태를 다시 캡처한다. 기존 단순화 패치는 이 hookup을 삭제하거나 구버전 전체 HTML로 덮어쓰는 용도로 사용하지 않는다. 라이브 검증 전 새 모델 연결과 생성 버튼은 미검증/비활성 상태를 유지한다.
