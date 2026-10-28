# 통합 순서와 소유 경계

1. 기능 스레드의 `docs/qa/fal-creator-workflow-20261025/integration-fal-creator.patch`를 먼저 통합한다.
2. 이 디렉터리의 `integration-presentation.patch`를 적용한다. 대상은 `index.html` 한 파일이다. CSS와 순수 표시 함수를 내부 block으로 넣으므로 새 static route가 필요 없다. 분리 원문은 `production-finish.css`, `production-presentation.js`.
3. 기능 회귀를 통과시킨 뒤 runtime을 고정하고 지정된 화면 packet만 재검증한다. 현재8773은 수정하지 않았다.

기능 staging 원본 `b6872f3f…d2138`로 작성했다. 최종 기능 staging `b094f68a…da7a`에서 dry-run과 격리 복사본 실제 apply 모두 exit0. 병합본4개 script 문법 통과. [적용 근거](staging-dry-run.json), [실제 격리 병합](syntax-merge-checks.json), [병합 문법](merged-syntax.json).

보존: mediaPreparation 권한/참고 계산, mediaActionMarkup의 금액·승인·출력 정책·recovery·candidate 상태, 모든 media command handler와data-* handle, scoped media draft, 기존 review controller/F07, timeline/caption handler.19검사에 함수/handler 원문 동일성 및 모든 기존 ID 보존 포함.

변경 접점은 세 가지다. `drawMediaCreator`의 summary markup을 pure projection으로 교체하고 disclosure 동기화. `initializeCreatorUI`에서 기존 DOM 노드를 ‘제작 도구’ 아래 이동. review save callback은 동일 `act(action,data)`를 호출하는 presentation wrapper로 연결해 실패 알림만 원래 project/scene/Take key에 보존한다. controller나payload/재시도/저장 성공 판정은 바꾸지 않는다. `false`는 실패 확정이라고 단정하지 않고 ‘저장 확인 필요’로 표시한다.

선택 모델/연결 projection의 backend 정합성은 기능 패치 소유다. 선택한 모델을 지우지 않고 연결 미검증을 분리 표시한다. 입력 준비 가능을 실행 승인으로 해석하지 않는다. 기존 job의 원래 모델과 cost/approval/rights/action buttons는 기능 renderer 그대로다. 이전 이미지 연결 요약은 중복 기본표면에서 숨기며 기존 recovery DOM과 작업 기록은 유지한다.

새 명령·provider routing·비용 계산·유료 호출·poster 생성 없음. 기능 패치 이후 함수 구간이 다시 바뀌면 패치가 거절되는 부분만 위 접점 기준으로 수동 병합한다. 현재 소스를 후보 HTML 전체로 덮어쓰지 않는다.

최종 후보 HTML SHA256 `b02db8e75b4690c43b2a7681156acaffcb025c5de000a70c82b9a915cb0bd9ec`. 화면은 이 후보 iframe + 기존8773 합성 프로젝트의 read-only 데이터로 확인했다. 최신기능backend에 통합된 실제 화면으로 오인하지 않는다.
