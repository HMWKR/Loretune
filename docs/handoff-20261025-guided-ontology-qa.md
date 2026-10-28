# 안내형 제작·온톨로지 QA 인계

- 실제 서버 localhost:8765 PID28823, exec89359. 공급자disabled, revision81/프로젝트6, 실생성2건import_blocked보존. 새 유료호출/키조회0.
- 격리 QA localhost:8772 PID28839, exec89046, data /tmp/loretune-deep-qa-20261025. 기본흐름+30샷경계 프로젝트2. 실제사용자작품변경안함.
- 최신 전체 회귀133통과,18.970초. backup 연결ResourceWarning 수정뒤0. 이후CSS placeholder/border강화만 추가했고JS syntax/pycompile 재확인.
- 결과/증거 docs/qa/mvp-flow-audit-20261025/user-report-ko.md, current-cases.json, requirement-qa-matrix.json/csv(96), api-qa-classification.json(143), regression.txt, final-code-hashes.json, 화면01~07, guided-local-fixture.mp4/srt/json, media-probe.json.
- 소스 변경전 snapshot before-source. 신규 guided.py/ontology.py/project_ontology.py/anthropic_ontology.py. app/index/editing/backup 통합. 실제데이터 .env/.codex 보존.
- IAB4: 사용자앱 tab5 deliverable, QA tab4/tab6 handoff. viewport reset. tab3 이전자막실패검증의 미저장편집경고가 남을수있어 자동조작하지않음. 개인브라우저탭사용안함.
- ontology 하위작업완료, 추가writer없음.

## 아직 완료 선언하지 말 것

영상API만남은상태로 판정하지않음. Anthropic은fake+boundedtransport만완료, 실제모델/auth/account/structuredoutput 검증0. 실제제안작업 UI 활성화와 token-count/budget 승인실행게이트 연결 필요. 승인패킷 anthropic-approval-proposal.md: Haiku5.5 합성Mira/Theo, input4096/output2048,제안$0.01,1회/retry0/count_tokens포함승인필요. Kling예산재사용금지.

기존Kling첫요청 CDN403 vs 추가요청 token발급403을구분. 기존거절파일접근/추가생성0. 최신실청구미확인유지.

접근성:320px/200%제품글자/계획폼포커스/모달focus/30샷키보드선택/대비130샘플통과. 400%browserzoom은IAB단축키실제배율변화없어미검증. 전체키보드파일선택→납품완주/스크린리더/모든상태대비/reduced-motion실환경은남음. 제품전체96FR/143API의전체수용완료로환산금지. 실사용자실험/유료출시/팀RBAC·배포준비완료아님.
