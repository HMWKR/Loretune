# 현재 화면 감사와 적용 결정

2026-10-25, 사용자 테스트가 아닌 구현자 검토. 원본 `.env`와 실제 공급자 원장을 사용하지 않은 별도 localhost:8772 fixture 환경이다.

## 관찰 → 변경

| 관찰 | 심각도 | 변경 | 근거 / 검증 |
|---|---|---|---|
| 약 11개 상단 동급 버튼이 좁은 폭에서 음절 단위로 끊어짐 | P1 | 관리 기능 disclosure, 생성/출력 승인 버튼은 안내형 마지막 단계만 표시, keep-all | 01-before-desktop.png → 02-guided-plan.png. 기존 팔레트 유지 |
| 채팅 모드가 작업대 전체를 그대로 붙여 단계가 불명확 | P1 | 음악→계획→장면→출력 4단계, 같은 DOM/프로젝트 데이터로 상세 작업대와 왕복 | Refero Clipchamp 10860 / Fourmula 11840 / ElevenLabs 8684 sequencing. 실제 경쟁사 클릭 검증이 아닌 부모의 metadata 조사 |
| 자유 입력 줄 나누기만 있어 목표·보존 조건 누락 | P1 | 구조화 목표/스타일/보존 조건 + 직접 작성 장면. 규칙·한계 표시 | HAX capability/explanation. 균등 배분 규칙을 명시하고 사용자의 문구 변경 없음 |
| 음악 구간이 바뀐 계획 적용 가능성 | P0 | 계획 context hash 검증, 변경 후 적용 거절 | tests/test_guided.py stale/missing/music offset |
| 저장 전 길이가 계획과 불일치, 선택 구간 오프셋 누락 | P0 | planned_duration과 music.start를 새 EDL에 반영 | 32–47초 → 15초, 시작32 검증 |
| 자막 입력 DOM값과 저장 draft가 어긋남 | P0 | input 이벤트 및 저장 시 현재 필드값 수집 | 브라우저 실패 재현 후 동일 자막 저장 성공 |
| 외부 참고 계보가 존재하지 않는 노드로 향함 | P1 | origin을 가진 proxy node, 역할 보존 | tests/test_project_ontology.py |
| ontology stale 충돌이400으로 반환됨 | P1 | 별도 Conflict도409 매핑 | 코드 수정; HTTP 회귀 추가 대상 |
| 기존 인물 수정 UI가 새 UUID를 만들었음 | P1 | 개체 선택 수정과 stable ID 전달 | 수정 후 같은 ID/1개체, 버전 복원 DB 검사 |
| 안내형 입력이 새로고침·프로젝트 전환 시 유실/혼입 가능 | P1 | workspace/project별 session draft | 실제 모드 왕복·새로고침 문자열 보존 확인 |
| 타임라인 이동 버튼 폭이24px 미만 | P2 | 26px 최소 폭 | 320px 관찰 후 수정; 최종 재측정 필요 |

## 방법론 적용 범위

- [HAX](https://www.microsoft.com/en-us/haxtoolkit/guideline/make-clear-what-the-system-can-do/): 로컬 규칙과 실제 AI를 구분. 이유는 실제 입력·규칙만 표시.
- [PAIR](https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/): 검토 버전 고정, 계획 승인과 비용 승인 분리.
- [Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/): 저장/승인/렌더/공급자 완료/로컬 수신 차단을 분리.
- [WCAG2.2](https://www.w3.org/TR/WCAG22/): 320px reflow·포커스·키보드 대안·타깃 검사. 전체 AA 인증 아님.
- [PROV-O](https://www.w3.org/TR/prov-o/): source/version/derivation을 참고. RDF/OWL 추론 엔진을 구현했다는 의미 아님.
- Refero 도구는 이 세션에서 link_id 누락 오류로 직접 조회하지 못함. 부모가 제공한 흐름·metadata와 기존 보고서를 역사적 비교 근거로 사용. REA 새 도구 미노출, 실행했다고 주장하지 않음.

## 남은 감사 범위

400% 브라우저 확대·200% 글자 확대·전체 키보드 경로·스크린리더·수백샷/다중worker 부하·대비 전수검사·실제 고객 usability test는 미완료. 현재 캡처와 과거25건 QA를 합산해 새 통과율을 만들지 않는다. 수정 뒤 실제 현재 화면/fixture만 새 증거다.

추가:30샷/긴설명320px검사통과, CSS텍스트대비130개샘플최소6.07. 전수접근성검사가아님.
