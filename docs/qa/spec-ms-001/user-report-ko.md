# 새 명세 분석·로컬 구현 체크포인트

SPEC-MS-001의 핵심은 세 개의 선택기가 아니라, 서버가 문맥·권한·승인·비용·작업을 소유하고 모델은 도구 요청만 제안하는 구조다. 현재 작업은 이 구조의 첫 계약 단계이며 다중 모델 제작 완성이나 출시 준비 완료가 아니다.

## 이번 구현
- `model_selection.py`: 채팅/이미지/영상 역할 검사, 등록부 상태·release 식별자·미연결 connection 표시, 선택 우선순위와 정책 거절, 설정 revision/history, 실행 문맥 해시. 미검증 모델은 실행 차단하며 fallback하지 않는다.
- `production_tools.py`: 9개 공통 도구 이름의 엄격한 인수 계약, 영속 local rehearsal run/도구 영수증, 중복 호출·다른 payload 충돌·불완전 입력·허용되지 않은 필드·제한된 형식 수정·모델 교체 후 늦은 요청 차단.
- 실제 연결한 로컬 동작은 scoped snapshot 조회, 모델 기능 조회, 직접 작성한 계획 제안, 기존 작업의 비민감 상태 조회다. 나머지 유료 실행/견적/렌더/메모리 변경 도구는 `LOCAL_TOOL_NOT_CONNECTED`로 차단한다. AI가 grant를 만들거나 외부 endpoint를 지정할 경로가 없다.
- 안내형 계획 미리보기도 같은 공통 계획 도구를 거치며 사용자 장면 문구를 보존한다. 엔진은 `local-contract-rehearsal`; LLM 호출이나 지능적 자동 기획으로 표시하지 않는다.
- `app.py`: SQLite 트랜잭션 안에서 설정과 run을 저장. 기존 request 멱등성/낙관적 잠금 재사용. `/api/model-catalog` 읽기 추가. 새 명세의 나머지 전용 REST 경로는 아직 미구현이다.
- `index.html`: 안내형/상세 작업대 공통 모델 설정 패널. 선택 저장과 외부 연결 구분, 이미지 모델 미구현·영상 수신 차단·온톨로지 Anthropic 별도 경로 표시. 디자인 세션 CSS를 기존 스타일 뒤에 통합. 구버전 공용 서버에서는 새 설정 저장을 비활성화하여 기존 제작 UI를 보존한다.

## 실제 확인한 것
- 기존 133개 baseline 보존. 추가 계약 테스트 포함 144개 전체 회귀 통과(최종 재실행 파일 확인). 로컬 HTTP bind가 제한된 최초 실행은 실패 기록을 남기고 허용된 localhost 실행으로 재검증했다.
- 실제 브라우저에서 A 작품의 채팅/영상 선택 저장 → B 작품 미선택 유지 → A로 돌아가 새로고침 후 값 보존을 확인했다.
- 통합 CSS 적용 후 제목 computed 20px, 1280px/320px 화면 확인. 320px viewport에서 document scrollWidth 305px로 페이지 전체 가로 넘침 없음.
- 모바일 선택기에서 긴 모델명과 함께 차단 상태가 잘리는 결함을 발견해 선택기 아래 독립 설명 문장으로 보완했다. 네이티브 옵션 자체의 긴 모델명 잘림은 유지되며 전체 상태 설명을 별도 제공한다.
- 외부 모델 호출/인증/업로드/키 조회/추가 비용 모두 이번 작업 0. 실제 기존 비용 상태 변경 없음.

## 아직 끝나지 않은 범위
- 영속 action/dependency/quote/grant를 기존 원장과 원자적으로 결합하는 통합 실행 경로, 실제 provider별 chat tool protocol 및 스트림, release/connection 생명주기 관리, 조직 인증·권한, SSE 재접속 등은 남아 있다. 3 역할 선택 화면만으로 MS-FR-01 전체 통과라고 하지 않는다.
- 현재 후보는 기존 구현 근거가 있는 Haiku/Kling뿐이며 모두 비활성이다. 이미지 어댑터·OpenAI/Grok 연결·12개 live 조합은 미구현/미검증이다. 메타데이터만으로 모델을 추가 활성화하지 않았다.
- Anthropic 실제 smoke test는 사용자 승인 대기다. 기존 fal 문제는 첫 CDN 403과 추가 요청 token 발급 403으로 구분하며 원인 미확정·추가 요청 실청구 미확인 유지.
- 전체 keyboard journey/screen reader/실제 400% browser zoom 및 디자인 세션의 통합 후 상세 QA가 남아 있다. 320px 검사를 WCAG 전체 준수로 해석하지 않는다.

## 증거
`source-manifest.json`, `analysis-and-plan-ko.md`, `acceptance-matrix.json` (28 MS-FR/38 MS-AT), `regression-final.txt`, `model-settings-saved.png`, `model-settings-polished.png`, `model-settings-320-final.png`, `design-integration.md`.

격리 QA: http://127.0.0.1:8773, 데이터 /tmp/loretune-ms-qa-20261025. 공용 8765/기존 8772 서버는 이 작업에서 재시작하지 않았다. 전담 디자인 원본 CSS는 수정하지 않았다.

최종 실제 계획 검증: 서버 재시작 직후 이전 탭 토큰은 403으로 거절됐고 입력 문구는 보존됐다. 새로고침으로 새 로컬 세션을 받은 뒤 동일 초안을 제출하여 계획 1개/run 1개를 저장했다. DB 증거에서 `propose_media_plan`, run completed, live_model_called false, generation_jobs 0을 확인했다. 이는 로컬 계획 도구 성공이며 영상 생성 성공이 아니다. 증거 `common-tool-plan-result.png`, `browser-plan-db-evidence.json`. 최종 회귀 144개/18.286초, Python compile/JS syntax 통과. QA 서버 최종 exec session 44092.
