# SPEC-MS-001 구현 인계

원문 전체 분석 및 해시 inventory: docs/qa/spec-ms-001/analysis-and-plan-ko.md, source-manifest.json.
구현/검증/남은 범위: docs/qa/spec-ms-001/user-report-ko.md.
144 tests 통과(18.286초), py_compile/node syntax 통과. 코드 hash final-code-hashes.json.

새 파일 model_selection.py, production_tools.py, tests/test_model_selection.py, tests/test_production_tools.py. 수정 app.py/index.html/tests/test_guided.py. 모델 기본 설정은 세 역할 분리, 현재 후보 둘 모두 통합 미완료. 이미지 모델 없음. 연결ID None, 모델 revision 고정 미검증. 실제 연결·권한 부여는 하지 않음.
로컬 guided_plan은 production_tools propose_media_plan으로 실행 후 run completed 저장; LLM 아님. 공통 tool 9개 중 조회/직접 작성 계획만 연결; 유료 실행 도구 차단 유지. 원장/grant/action/dependency 연결과 공급자별 protocol은 다음 안전한 구현 범위.

디자인 세션 CSS는 원본을 수정하지 않고 index style id=designPolish로 통합. 기존 selector/숨김/이벤트 보존. docs/qa/design-benchmark-20261025/는 디자인 세션 소유로 유지. 새 모델 패널은 #modelSettingsPanel/#modelSlots/#modelSettingsStatus. 모바일 선택기 밖 상태 설명 추가.
검증 앱 http://127.0.0.1:8773, /tmp/loretune-ms-qa-20261025, exec session44092. 최종코드 재시작완료. 브라우저 IAB4 tab7 handoff. viewport reset. 공용8765/기존8772 재시작 안 함. 구형 서버 UI에 model_catalog 없으면 신규 설정 저장 비활성화하여 TypeError 방지.
실제 QA A/B프로젝트 설정 격리/저장/새로고침,320px 넘침없음, 직접 작성 2장면 계획 원문 보존/음악 누락 질문/비용 승인 분리 확인. token재시작403은 갱신 후 해결; 공급자403과 무관.

외부 호출/키조회/credential 설정/추가 지출0. Anthropic $0.01 질문 승인 대기, 12조합 live 미승인. 기존 fal 첫 CDN403과 추가token403·실청구미확인 유지. 남은 로컬 작업과 전담디자인 재검증을 진행해야 하므로 전체 MVP/새 명세 완료로 보고하지 말 것.
