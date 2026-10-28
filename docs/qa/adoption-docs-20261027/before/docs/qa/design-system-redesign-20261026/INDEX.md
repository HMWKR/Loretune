# Aethon 디자인·방법론 현행 문서

현행 범위:1920×1080 주 평가,1280×900 보조 회귀, 모바일 추가 작업 보류. 앱 source/server/DB와 구현·릴리스 보고서는 기능 담당 소유다. 이 폴더는 설계·참고·수용 기준·독립 평가를 관리한다.

제품명은 사용자 결정에 따라 Aethon이다. 실행 UI와 현재 안내의 표시명 전환 DP26-11은 완료됐으며 기존 Loretune 폴더/호환 식별자/원본 명세/역사적 증거는 유지한다.

## 먼저 읽기

**현재 계획:** [전체 디자인 작업·검증 통합 계획](../codex-cli-assessment-20261026/PLAN-ko.md). 사용자 제공 워크플로 전체를 대조해 화면·상태 coverage, 완료/열린 문제, 대안·의존성·검증·종료 조건을 한 문서로 정합화했다. 계획 설명 후 표시명과 핵심 상태·격리 제작 검증을 마쳤고, 다음 Claude/모델 편집 감사에 앞서 소스를 고정했다.

**최신 구현 기준:** [Aethon 구현 인계](../codex-cli-assessment-20261026/REPORT-ko.md), [정확한 소스/served·종료 manifest](../codex-cli-assessment-20261026/implementation/FINAL-MANIFEST.json). HTML `d82ca93a…f6e2`, CSS `4c52de6d…db8644`, media JS `ac41a983…2832c9`. 전체350회귀,현재8상태 치수·폼12조건 및 격리3초1080p 합성 출력/재개를 확인했다. [이전 헤더 개선](../context-header-space-20261026/REPORT-ko.md)의 +36px를 유지하며 이번 새 시각 개선량으로 세지 않는다. 임시 서버/공간 종료. 실제 공급자/전체 접근성 통과를 뜻하지 않는다.

**닫힌 결함과 남은 coverage:** 아래 이전 감사의 VF01 확대 Take 포커스, VF02 긴 장면명 잘림은 후속 수정/승인된 브라우저 재검증으로 닫혔다. FQ01–03도 독립 코드 재검증으로 닫혔다. [통합 기능·시각 QA 결과](../frontend-fq-vq-fixes-20261026/Loretune-프론트엔드-QA-기준과-검증결과-20261026.md), [독립 FQ 재검증](../independent-frontend-fq-recheck-20261026/REPORT-ko.md)를 참조한다. 실제 browser zoom·screenreader·cross-browser 등 미검증과 현재 전체 화면 coverage는 현행 계획에서 별도로 추적한다. 새 제품 결함이나 점수는 추가하지 않는다.

이전 프런트엔드 감사: [시각·CSS·키보드 결과](frontend-qa-inventory-20261026/REPORT-ko.md), [케이스별 결과](frontend-qa-inventory-20261026/RESULTS.json)의 15 PASS / 2 FAIL / 2 BLOCKED / 3 NOT RUN은 **수정 전 해당 빌드의 역사적 결과**로 보존한다. 아래81점도 이전 혼합 rubric의 이력이다.

사용자 전달용: [독립형 한국어 디자인 업데이트 요약](Loretune-Design-Update-20261026-ko.md). 요약과 방법론 적합성 표는2026-10-26 Library 등록이 확인됐으며, 로컬 파일의 Library 식별 metadata도 보존했다.

1. [2026-10-26 추가 합의](AMENDMENT-20261026-DESKTOP-METHODOLOGY-ko.md) — 최신 요구/구현 상태/역사적 기준 구분
2. [요구·DS01–14 수용기준](REQUIREMENTS-AND-ACCEPTANCE-ko.md)
3. [reference lock](REFERENCE-LOCK.md)와 [semantic tokens](SEMANTIC-TOKEN-SPEC.md)
4. [디자인/기능 통합 계약](INTEGRATION-CONTRACT.md)
5. [방법론 fit matrix](METHODOLOGY-FIT-MATRIX-ko.md) — 채택/조건부/제외, 출처·과업·구현·검증·한계
6. [변경 기록](CHANGELOG-ko.md)

## 이전 V1–V4 재검토 — 혼합 rubric 이력

- [이전 상세 보고서](desktop1920/refinement-recheck/REPORT-ko.md):81.0/100,항목평가배점커버리지100.전체상태통과는아님. 최신 별도 프런트엔드 QA 점수로 사용하지 않는다.
- [현행scorecard](desktop1920/refinement-recheck/scorecard.json),[geometry](desktop1920/refinement-recheck/geometry.json),[통제오류](desktop1920/refinement-recheck/controlled-errors.json),[종료불변](desktop1920/refinement-recheck/end.json).
- H1/H2미검증,H3키보드/H4측정대비표본PASS.앱코드/DB/서버읽기전용.

## 이전 shell 독립 감사 — 이력 보존

- [최종1920상세보고서](desktop1920/final-audit/REPORT-ko.md) — 확인배점98중74.3점,전체확정점수보류. 이전5축점수와비교불가.
- [항목별scorecard](desktop1920/final-audit/scorecard.json),[실제geometry](desktop1920/final-audit/geometry.json),[대비](desktop1920/final-audit/contrast.csv),[종료불변확인](desktop1920/final-audit/end.json).
- 실제화면15개열어검사,3개Library등록. 3gate전체미검증;전체ready주장없음.

## 1920 평가 자료

- [사전 고정7축 rubric v1](desktop1920/RUBRIC-v1-ko.md), [무스크롤 추가 요구 v1.1](desktop1920/RUBRIC-v1.1-ADDENDUM-ko.md), [고정 hash](desktop1920/rubric-lock.json)
- [측정 계획](desktop1920/MEASUREMENT-PLAN-ko.md), [상세 결정 추적표](desktop1920/METHODOLOGY-AND-DECISION-LEDGER-ko.md)
- [참고 provenance/구성 가설](desktop1920/PROPOSALS-AND-REFERENCES-ko.md)
- [현재 체크포인트 보고](desktop1920/REPORT-ko.md), [baseline 산술](desktop1920/baseline1920-analysis.json), [baseline 토큰CSV](desktop1920/baseline1920-tokens.csv)
- [채점 template](desktop1920/scorecard-template.json) — 사전고정원본의null을보존;최종판단은별도scorecard 참조

## 과거 증거와 구현 기록 — 읽기 전용

- [초기 설계 문서 보존본](history/initial-design-stage-20261026/)
- [최종B 토큰 감사](../design-system-audit-20261026/REPORT-ko.md)
- [시스템1차 구현](../design-system-implementation-20261026/REPORT-ko.md)
- [1차 독립 UI 감사](../design-system-independent-audit-20261026/REPORT-ko.md)
- [미디어 수정1920 증거](../design-media-fixes-20261026/DESKTOP-1920-ko.md)
- [DM01–03 독립 코드 재검증](../independent-design-media-recheck-20261026/REPORT.md)
- [bounded-shell 구현 계획](../desktop-shell-20261026/PLAN-ko.md) — 최종 release와 구분

원본07 아키텍처는 변경하지 않았다. 이 문서들의 모델/권리/비용/승인/noMCP/fal 계약은 원본을 덮어쓰지 않는다. 공급자 연결이나 생성 실행은 디자인 범위에 포함하지 않는다.

변경 기록 — 2026-10-26: 부모의 명시적 문서 정합화 요청으로 현재 입구의 VF01/VF02 상태와 최신 헤더 manifest/통합 계획 링크만 정정했다. 원감사·원점수·수용기준은 수정하지 않았다.

현행 입구 갱신 — 2026-10-26: DP11 완료와 현재 E8 인계를 연결했다. 설계 기준·원감사·점수·방법론은 변경하지 않았다.
