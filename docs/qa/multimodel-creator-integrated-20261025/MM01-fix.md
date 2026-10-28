# MM01 좁은 수정·재검증 요청

원 independent-multimodel-tools-audit-20261025 증거는 변경하지 않았다.

production_context.py가 현재 작품의 안정 shot ID/name/revision/Take hash/권리 상태, 현재 EDL/음원/자막/사람 출력승인 handle, 미접수 production action과 기존 유효 grant handle, ontology revision을 읽기 전용으로 반환한다. chat handoff와 search_project_context에 같은 projection을 사용한다. 기본 creator UI에는 이 원문을 표시하지 않는다. 서버 실행 단계의 권리/문맥/가격/만료/소유권 검사는 그대로다. 인증 토큰·경로·공급자 URL은 포함하지 않는다.

fal prepare 도구의 shot_id와 source_shot_id는 동일 production_context.shot_key 매핑으로 stable ID를 해석한다. 기존 UI name key와 호환하되 두 대상에 걸치는 ambiguous 값/다른 작품 ID는 거절한다. 승인 snapshot/hash 형식은 변경하지 않았다.

현재 원본 tests/test_execution_context.py의3개 회귀 통과: 모델 전환 후 조회된 타임라인 승인만으로 render 재사용, 승인된 미접수 action/grant를 조회해 request/안정 shot ID prepare 성공, 다른 작품/모호 ID 거부. 기존35개 chat/fal/local-tool/protocol 집중 시험도 통과했다. 전체 통합 UI와 최종 회귀는 진행 중이다.

독립 재검증은 MM01의 조회→인수 구성→기존 승인 실행에만 한정해 요청한다. 새 외부 호출/키 조회 없음.
