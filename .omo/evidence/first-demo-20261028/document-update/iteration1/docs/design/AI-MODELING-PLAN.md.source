# Aethon 선택형 모델화·조명·카메라 계획

## 공통 에이전트와 선택적 3D의 연결 · 2026-10-28

**제품 중심은 음원 기반 음악영상이며 3D는 선택 기능이다.** 최신 사용자는 모든 제작 단계와 모션/3D 작업창에서 같은 오른쪽 AI 사이드 패널을 열고 선택 모델로 질문·추천·편집·설정 지원을 받도록 요청했다(AGENT-UI-01/TOOLS-02). [대화·모델별 추론/권한 계약](CHAT-SESSION-PLAN.md)과 [디자인 QA](CURRENT-DESIGN-QA-PLAN.md)를 공통 기준으로 사용하며 이 문서에 별도 에이전트/승인 체계를 만들지 않는다.

[현재 도구 감사](../../.omo/evidence/first-demo-20261028/chat-capability-audit/report.json)의 CAP07/08은 사람용 3D UI/API·SceneSpec 저장/승인/내부 렌더와 일반 AI 대화의 3D 도구 연결을 구분했다. 조회·제안/실행 schema와 문맥 연결은 보완 대상으로 남으며, 새 3D 메시 생성·리깅·애니메이션까지 지원한다는 뜻이 아니다. 실제 모델이 조명·카메라·구도를 다루는지는 typed 변경→사람 검토/적용→정확 버전→실제 프레임·Take·음원 출력으로 확인해야 한다. 미저장 3D 초안을 서버 AI 문맥에 이미 전달한 것처럼 표시하지 않는다.

계정 삭제는 permission/Full Access와 무관하게 항상 금지한다. 파일 등 다른 삭제는 대상·영향과 사용자 개별 명시 허용이 필요하며, 자산/SceneSpec 원본·기존 Take·출력의 보존·권리·비용 검사는 유지한다. 현재 작업과 실제 협업자의 상태도 구분한다. 1차 화면 녹화 검토와 구체 비용별 승인 전 AI 영상 모델을 호출하지 않으며, 실제 Claude 검증도 별도 모델·자료·예산 승인 범위에서 진행한다. [현행 구현·잔여](../qa/codex-workflow-review-20261027/REPORT-ko.md)를 따르고 아래 시점별 원문·검증 한계를 보존한다.

## 통제 비교 이후 기준 · S819 · 2026-10-28

[색 해석·재조명4조건](../qa/AI-3D-ARCHITECTURE-RESEARCH-20261027.md)에서 원본 색 데이터가 존재함과 색 의미/조명의 민감도를 분리했다. 더 어두운 결과가 올바른 albedo/감마라는 증거는 없으므로 제품 자동 변환은 추가하지 않는다. 다음 모델 adapter는 색/재질 의미와 고정 revision·원본/변환 이력·자원 예산을 선언해야 하며, 미확인 조건은 비교에서 표시한다. 이는 아직 adapter 구현이 아닌 계약 방향이다.

S819에서는 복잡도 초과의 복구 안내와 실제 GLB UI 가져오기·거절/입력 보존을 보강했다. 기존 기하 한도와 원본 바이트·검증/권리/승인 경계는 유지한다. 음원 제작이 중심이며 실제 AI 영상 모델 시험은 실무 흐름 준비 이후다. [현행 증거·남은 도구/모델 연결](../qa/codex-workflow-review-20261027/REPORT-ko.md)을 따르고 아래 단계별 원문은 보존한다.

## 실제 공개 모델 자산 연결 · S813 · 2026-10-28

[실제 생성·형상/색·편집·음원 출력 근거](../qa/codex-workflow-review-20261027/REPORT-ko.md)를 연결한다. 고정 TripoSR 코드·가중치의 원본 cube/chair 두 개는 정점 색 v2로 원본 바이트를 유지한 채 내부 렌더·편집·권리 검사를 통과했다. 실제 UI의 의자 회전/크기/카메라→재승인→Take2→음원·한글 자막 MP4도 확인했다. v1 metadata/hash는 불변, 정규화 COLOR_0만 제한적으로 확장했다. Blender 색 양자화와 cube 퇴화면4개 제거를 무손실로 표현하지 않는다.

공개 모델 추론은 격리 실험이다. **사이트의 AI3D 생성 adapter/채팅3D도구·재질 편집·움직임은 미구현**이며 3D는 음악영상의 선택 수단이다. 전처리 추가1회는 배경 분리 부족·129,841정점/177성분으로 실패했고 원본을 감량하거나 색을 버려 통과시키지 않았다. 같은 입력·전처리·구도·조명의 상용 Tripo 비교는 미입증이다. 실제 입력보다 옅은 색/거친 표면의 원인은 분리 검증해야 한다. 아래 S789의 ‘실제 생성 미실행’ 등은 당시 기록이다.

아키텍처는 기존 asset→SceneSpec→사람 승인→격리 worker→Take→음원 편집 계약을 재사용한다. 배경 오류 수정과 loaded 구현 지문을 승인/대기/게시 경계에 연결했으며 원본/옛 결과를 보존한다. 다음 레벨과 남은 품질/전처리/모델 adapter는 [단일 조사](../qa/AI-3D-ARCHITECTURE-RESEARCH-20261027.md)를 따른다.

## 산출물 연구와 핵심 과업 우선 · S789 · 2026-10-28

Tripo의 추가 창작자 사례·직접 이미지 5개와 통제 비교의 한계는 [단일 조사 기록](../qa/AI-3D-ARCHITECTURE-RESEARCH-20261027.md)에 연결한다. 원본/최적화 자산 크기가 현재 8MiB 한도에 맞는지 실제 GLB로 확인되지 않았으며 공개 이미지의 조회를 메시 사용권이나 호환 통과로 해석하지 않는다. 별도 3D 기능을 메인으로 확대하지 않고 음원 중심 대화 이력·내부 모션 색상·30초 제작/편집/복원 검증을 [최신 작업 기록](../qa/codex-workflow-review-20261027/REPORT-ko.md)에서 이어갔다. 실제 AI 3D 생성·동등 품질 비교·3D 채팅/움직임은 여전히 남아 있다.

## 현재 증거의 범위 보충 · S774 · 2026-10-28

[최신 전체 회귀 774개와 인계](../qa/codex-workflow-review-20261027/REPORT-ko.md)를 확인한다. 자체 절차적 장면으로 동일 카메라·빛·해상도의 [비교 입력 2개](../qa/codex-workflow-review-20261027/current-774-20261028/benchmark-inputs/manifest.json)를 실제 렌더했으나 Tripo 상용·공개 모델 결과 비교는 미실행이다. 공개 Space 캐시 여부를 알 수 없는 조회로 GPU 추론을 유발하지 않았다. AI 3D 생성·채팅 3D 편집·동영상 3D는 여전히 남아 있고 제품 중심은 음원 기반 음악영상이다. 일반 채팅 adapter의 제한된 연결 구현을 3D 도구의 구현으로 해석하지 않는다.

## 최신 구현과 통합 방향 — 2026-10-28

**제한된 내부 3D 정지 장면과 작은 정적 GLB 연결이 구현됐다.** SceneSpec v1의 도형 계약을 보존하고 v2의 등록 자산 ID·해시 참조, 원래 재질을 유지한 배치·카메라·빛 변경, 격리 Blender PNG→새 Take를 연결했다. 자기 제작 합성 자산의 PNG/JPEG 두 재질·수정 전후 렌더, 실제 UI의 음원·한글 자막 MP4까지는 [725개 단계와 후속 검증 기록](../qa/codex-workflow-review-20261027/REPORT-ko.md)을 따른다. 제품의 중심은 음악영상이며 3D 없이 음원만/선택적 사진으로 진행하는 경로를 유지한다. 아래 PLAN ONLY·바이너리 관측만 가능·제품 미연결 문구는 이전 계획 시점의 기록이다.

사용자는 **Tripo와 Blender를 결합해 플랫폼의 한 기능으로 제공**하도록 요청했다. 사용자 과업은 음원 우선·사진 선택, AI 자산 후보/기존 자산→플랫폼 내 구도·빛·재질 편집→검토·내부 렌더→음악영상 사용이다. 기능의 사용자 흐름·현재/제안 계약·모델 도입 대안·단계별 합격 기준은 [단일 조사·아키텍처 문서](../qa/AI-3D-ARCHITECTURE-RESEARCH-20261027.md)에서 관리하고 이 문서에 중복 API를 만들지 않는다.

GLB 가져오기는 `gltf2-static-pbr-v1`의 제한 프로파일과 8MiB 한도이며 모든 외부 mesh나 실제 Tripo 산출물을 지원한다는 뜻이 아니다. AI 3D 생성·실시간 뷰포트·채팅 3D 도구·3D 애니메이션/리깅은 남아 있다. 기존 PNG를 타임라인에서 늘려 쓰는 것은 3D 움직임이 아니다. 다음 3D 확인은 출처·사용권과 버전을 확인한 실제 모델 산출물의 호환·편집성 및 동일 입력 비교다. 실제 Tripo 호출과 공개 모델 추론은 환경·입력·비용·license를 확인하고, 음악영상 핵심 과업의 우선순위를 유지하며 별도로 검증한다.

## 이전 계획 보충 — 아래 날짜별 관측과 승인 범위 보존

## 최신 사용자 방향과 남은 확인 · 2026-10-27

사용자는 이후 문서만 작성하던 제한을 넘어 기능 구현과 실제 워크플로 검증의 진행을 요청했다. AI 모델 연결은 예외로 하되 제작·편집·저장·출력은 다른 플랫폼 서비스 연결을 필수로 하지 않는 자체 플랫폼을 목표로 한다. 아래 ‘구현 전 승인’과 ‘이번 실행 0’은 해당 계획 작성 당시의 기록이며 현재 전체 작업의 중단 지시로 해석하지 않는다.

다만 현재 확인한 Blender REA 증거는 아래 Mach-O 요약까지이며, 사용자께서 과거 말씀하신 Blender와 플랫폼 내부 REA MCP 결합의 정확한 원문은 찾지 못해 확인을 요청한 상태다. 이 상세 범위를 추측해 완료로 기록하거나, 보류 중인 별도 AI 학습 구상을 3D 구현 지시로 합치지 않는다. 선택형 3D 제작·채팅/직접 조작의 공통 상태·렌더·복구와 환경 호환성은 제품 구현 및 실동작 검증이 남았다.

## 2026-10-27 REA 재시도 · 현재 관측

이전 REA 차단은 당시 실행 기록으로 유지한다. 현재 세션에서는 REA MCP `open_binary`와 `inspect_macho`가 설치된 `/Applications/Blender.app/Contents/MacOS/Blender`에 성공했고 세션을 닫았다. 대상은 arm64 Mach-O, SHA-256 `f5c1f2a0c0bca3389ec772d355242b700975ea84e66cbb3f5257a7bce8e5adeb`; `blender --version`은 5.2.2 LTS를 반환했다. [REA 요약 증거](../qa/codex-workflow-review-20261027/rea-blender-macho-summary.json), parent Evidence `ev_2b47aa66396d25247384f1abcafbc06b810ddbc6fc0ff51ec7f18bbbd346dde1`. 이 검사는 바이너리 형식·구성 관측이며 Blender의 조명·카메라 조작, 렌더, 격리 worker 또는 플랫폼 연결의 성공이 아니다. 기존 선택형 3D 구현은 여전히 미완료다. 사용자가 언급한 과거 Blender·REA 결합 지시의 정확한 원문과 추가 범위는 이 문서에서 확인되지 않아 별도로 질문했다.

## 2026-10-27 범위 보충

**PLAN ONLY 유지.** [AD01–AD07 채택 문서](AETHONSAAS-ADOPTION-PROPOSAL.md)는 개인 제작 기본·팀 협업 선택의 문서 설계만 승인됐다. AD01 자료역할/버전 도입은 Blender 설치·SceneSpec compiler/worker·새 ingestion/OCR/자동 온톨로지 진화 구현 승인으로 확대되지 않는다. [정체성/범위 보충문](PRODUCT-IDENTITY-AMENDMENT-20261027.md), [현재 단일 PLAN](../qa/codex-cli-assessment-20261026/PLAN-ko.md).

선택형 모델화는 개인에게도 건너뛸 수 있는 단계이며 팀 생성·공유의 선행 조건이 아니다. 이 문서의 구현 전 버전·license·worker격리·카메라/조명 수용 gate는 그대로다. 이번에는 제품/테스트·DB·서버·설치·REA/Blender 실행0. 아래 계획 작성 완료와 제품 구현 완료를 구분한다.

2026-10-26 · **PLAN ONLY / 설계 문서 완료, 제품 구현·설치·실행 미수행**

목표는 영상 제작 전에 필요할 때만 간단한 3D 구도와 빛을 정하고, 채팅과 직접 조작으로 같은 장면 데이터를 수정하는 것이다. Blender UI를 복제하거나 영화 수준 인체 모델·리깅을 약속하지 않는다. 초기 범위는 단순 도형과 사용이 승인된 자산을 이용한 **블로킹·프리비주얼라이제이션**이다. 건너뛰면 기존 이미지/영상 제작 흐름을 그대로 사용한다.

이 문서는 [canonical PLAN](../qa/codex-cli-assessment-20261026/PLAN-ko.md)을 대체하지 않는 OM-22 전용 설계다. [누락 등록부](../qa/OMISSION-REGISTER.md)의 문서 공백만 닫는다. Native 2D motion, 이질 데이터 ingestion/온톨로지 자동 진화와는 다른 범위이며, 해당 기능의 완료 상태를 이 문서로 바꾸지 않는다. 제품 코드·primary PLAN·DB·서버는 수정하지 않는다.

## 1. 요구와 근거의 성격

사용자 요구를 부모가 전달했다: 영상 전 선택형 ‘모델화’, Aethon 안의 조작, 채팅 모델을 통한 조명 방향·카메라 조정, 의도한 결과가 모호할 때만 질문, 공개 GitHub 소스 활용. 이미 명확한 입력을 반복 확인하지 않는다.

|자료|채택할 근거|적용하지 않거나 아직 확인하지 않은 것|
|---|---|---|
|[ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) — 구 blender-mcp|부모의 공개 정적 연구: `server.py`, `addon.py`, `safe_mode.py`, `telemetry.py`, `pyproject.toml`의 연결·실행 경계 참고|커뮤니티 MIT 저장소이며 공식 Blender 제품이 아님. addon의 raw exec와 background-mode server 거절 때문에 GUI MCP를 headless production worker로 그대로 채택하지 않음|
|[Blender 5.0 command-line arguments](https://docs.blender.org/manual/en/5.0/advanced/command_line/arguments.html)|배경 렌더 worker의 실행·인수·종료 계약을 구현 전에 검증할 공식 근거|설치/렌더 성공, 허용 플래그 또는 모든 버전 동작을 이미 확인했다는 뜻 아님|
|[Blender 4.5 render passes](https://docs.blender.org/manual/en/4.5/render/layers/passes.html)|이미지·깊이 등 산출물이 서로 다른 의미/준비 조건을 가진다는 참고|5.0 CLI 문서와 같은 검증 버전으로 섞지 않음. depth가 모든 영상 모델 입력이라는 주장 금지|
|[Blender FAQ](https://www.blender.org/support/faq/)|Blender GPL과 렌더 산출물·배포 경계의 검토 출발점|커뮤니티 addon MIT, Blender GPL, worker 배포 방식, 자산별 라이선스를 하나로 취급하지 않음. 이번 문서가 라이선스 수락/배포 승인 아님|
|기존 [Aethon reference lock](../qa/design-system-redesign-20261026/REFERENCE-LOCK.md)|중성 미디어 작업대, 선택 대상에 인접한 속성/검토, 위험 기반 상세 공개|타사 내부 token 복제, 마케팅 hero, Blender 전체 메뉴/단축키 복제 없음|

위 외부 자료의 내용은 **부모의 이미 수행한 웹/정적 연구를 인계받은 것**이다. 이번 문서 작성에서 새 fetch·REA·Blender 실행을 하지 않았다. REA는 등록 확인과 실제 분석 실행을 구분하며, 실행은 기존 차단 상태다. 정적 GitHub 분석을 REA 결과로 부르지 않는다.

**구현 전 고정할 것:** 커뮤니티 저장소의 정확한 commit/파일 SHA/당시 LICENSE·notice, 선택 Blender 버전·build hash·공식 문서 버전, 렌더 engine·device·색 관리·seed·font/asset manifest. 현재 commit과 실제 설치 버전은 미확인이다. 저장소 main의 이동이나 버전 혼합을 고정 근거로 삼지 않는다. 필요한 개념만 참고하고 외부 코드를 Aethon 소유로 재표시하지 않는다.

## 2. 선택한 구조와 대안

|대안|이점|결정·이유|
|---|---|---|
|모델이 Python을 작성해 addon에서 직접 실행|넓은 Blender 기능에 빠르게 접근|제외. 파일/네트워크/실행 권한, 재현성과 변경 범위를 모델 코드에 맡기게 됨|
|기존 GUI MCP를 제품 worker로 연결|대화형 데모와 관찰에 유용|초기 제품 경로로 제외. GUI 연결과 headless 작업·취소·복구는 같은 계약이 아니며, 개발 REA/MCP와 Aethon 런타임을 혼동하지 않음|
|Blender 전체 UI를 웹에 복제|전문가에게 많은 기능 제공|제외. 사용자의 구도·빛 조정 과업보다 학습/구현 범위가 커짐|
|**SceneSpec → 결정적 검증 → 신뢰된 bpy compiler → 격리 Blender worker**|모델과 직접 편집이 동일 데이터·diff·버전을 사용. 허용 범위와 원본 보존을 검사 가능|선택한 설계안. compiler/worker/UX를 구현·검증하기 전까지 실행 가능한 제품이라고 부르지 않음|

SceneSpec은 기존 ontology의 캐릭터/장소/스타일 **ID와 승인 revision을 참조**한다. 모양·카메라 제안이 정식 설정을 자동 수정하지 않는다. 채팅 역할은 기존에 사용자가 선택한 모델을 유지하고, 이미지·영상 모델 선택이나 기존 Take를 몰래 바꾸지 않는다.

## 3. 사용자 흐름과 Aethon UI

1. 장면에서 **‘모델화로 구도 잡기 · 선택’** 또는 ‘기존 제작 계속’을 선택한다. 처음부터 모든 프로젝트에 모델화를 강제하지 않는다.
2. 현재 장면/ontology revision과 사용할 도형·승인 자산을 확인한다. 자산이 없으면 단순 도형으로 시작하며 완성된 인물 자산처럼 표시하지 않는다.
3. 중앙 preview, 왼쪽 객체 목록, 오른쪽 **선택 대상의** 조명/카메라/위치만 표시한다. 현재 제품의1920×1080 기본 shell을 유지하고1280×900은 보조 검증한다. 긴 설정만 패널 내부 scroll; 모바일 새 설계는 후속 범위다.
4. ‘광원을 화면 왼쪽 위로’, ‘카메라를 더 낮게’ 같은 채팅 또는 직접 handle/숫자/프리셋으로 변경한다. 둘 다 같은 SceneSpec proposal service에 들어가며, UI만 다른 숨은 저장 상태를 만들지 않는다.
5. 변경 요약은 **대상 → 전/후 → 유지한 잠금 → 영향** 순서다. 임시 preview와 저장 revision, 검토 승인, 렌더 허용을 구분한다. 명확하고 허용된 직접 편집마다 불필요한 확인 dialog를 반복하지 않는다.
6. 사용자가 적용하면 새 scene revision을 저장한다. undo/restore는 과거 데이터를 덮지 않고 복원한 새 revision을 만든다. 승인된 원본·기존 Take·출력은 유지한다.
7. 다음 경로를 선택한다: **직접 렌더** 또는 **지원되는 모델의 참조로 사용**. 직접 렌더는 고정 장면을 그린다. 생성 영상은 참조를 재해석하므로 같은 geometry·조명·카메라를 보장하지 않는다.
8. 비용/모델/수량/권리/허용 범위를 실제 결정 시점에 보여주고, 결과 검증 후 새 미채택 후보를 등록한다. 후보 선택·Take 검토·최종 편집/출력 승인은 기존 계약을 따른다.

### 조명·카메라 조작

|대상|초보 기본 조작|보조/고급 조작과 보존 조건|
|---|---|---|
|조명|명확한 선택 표시가 있는 방향 handle, 밝기, 부드러움; 정면/측면/역광 프리셋|광원 종류·크기·거리·색은 상세에 공개. 밝기와 softness를 하나의 강도값으로 합치지 않음. light ID와 잠금 상태 유지|
|카메라|정면/측면/로우앵글/오버숄더 프리셋; 거리·높이·대상·화각|실제 선택 target 표시. 오버숄더의 피사체/전경 객체가 없으면 대상부터 정함. lens와 FOV는 동등한 독립 저장값이 아니라 하나에서 계산|
|객체|선택 객체의 이동·회전·크기, 원점/축 표시|승인 자산 원본은 변경하지 않고 instance transform을 버전화. 잠긴 객체/속성 변경은 거절하거나 별도 변경안으로 표시|
|preview|현재 scene/카메라/revision, draft/저장 상태, frame/time|준비 중·실패·오래된 결과를 구분. 근거 없는 ‘실시간’/완성품 품질 문구 없음|

방향 handle에만 의존하지 않고 프리셋·숫자 입력·단일 pointer와 키보드 대안을 둔다. selected/focus/locked/dirty/error는 색만으로 구분하지 않는다. 정확한 타깃 크기와 세부 배치는 구현 후보를 실제 렌더한 뒤 현행 token·접근성 기준으로 결정한다.

## 4. SceneSpec v1 스케치 — 제안 계약

|영역|필드·단위·역할|
|---|---|
|서버 envelope|workspace/project/shot stable ID, scene ID, base revision, proposal ID, actor/run/call provenance, ontology revision, 변경허용 scope. actor/approval/path를 모델이 결정하지 않음|
|좌표|오른손 world XYZ, +Z 위, 거리 meter. 화면 좌/우는 active camera basis에 상대적, 인물 좌/우는 해당 객체의 명시된 local basis에 상대적. UI 각도 degree→compiler 단위 변환은 한 곳에 정의|
|장면|schema_version, canvas/profile ID, fps, frame_count, renderer/색 관리/seed/profile. 첫 프리뷰는 정지 프레임; 짧은 카메라 동작은 별도 수용 gate 후 활성화|
|객체|instance ID, ontology entity reference, primitive enum 또는 승인 asset ID/version/hash, transform, target/forward-axis 정보, locked_properties. 모델 입력에 임의 파일경로·URL·script 없음|
|조명|light ID/type, position 또는 direction+target, brightness·단위, size/softness, color, 좌표 frame. 프리셋은 실제 필드 diff로 풀어 보여줌; engine별 물리량 매핑은 고정 profile에서 검증|
|카메라|camera ID, position, target, up/basis, projection, lens_mm와 고정 sensor 설정. UI FOV는 여기서 계산. path는 none 또는 frame별 position/target keyframes; 첫 MVP는 none을 기본으로 free-form curve/rig는 제외|
|시간|정수 frame, 구간 [in_frame,out_frame), fps와 scene revision에 귀속. path의 frame/좌표/easing은 allowlist·상한·유한값·증가순서 검사|
|자산·출처|승인 asset manifest/권리 상태/출처/version, 사용한 compiler/Blender/profile hash. 모델 제안·직접 편집·검토·실행을 별도 이벤트로 기록|
|산출물|SQLite에 scene revision/job/status/approval/manifest 메타데이터, 파일저장소에 preview·렌더·선택적 .blend/pass artifact. 원본 자산과 임시/검증완료 결과 경로를 분리|

모델은 예를 들어 `set_light_direction`, `set_light_brightness`, `set_camera_pose`, `set_camera_lens`, `set_object_transform` 같은 **허용된 typed 변경안**을 제시한다. 서버는 unknown field, NaN/Infinity, 외부 경로/실행 코드, foreign asset, stale revision, 잠금 위반을 거절한다. 구체적인 객체·프레임·해상도·메모리·렌더시간 상한은 capability 검증 후 profile에 고정하며, 검증 전에 무제한 요청을 허용하지 않는다.

## 5. 모호성·질문 규칙

- ‘화면 왼쪽에서 비춰’와 ‘인물의 왼쪽에서 비춰’는 서로 다른 명시 요청으로 처리한다. **그냥 ‘왼쪽’이고 두 해석이 다른 결과를 만들면** 어떤 기준인지 짧게 묻는다. 자동으로 한쪽을 선택하지 않는다.
- 대상이 하나로 선택돼 있고 요청·좌표 기준이 명확하면 반복 질문하지 않는다. 여러 카메라/대상 중 미지정이면 의도한 대상만 확인한다.
- ‘부드럽게’는 조명 panel/선택 light 문맥에서는 softness 후보로 제시하되, 카메라 움직임/이미지 질감 중 의미가 갈리면 원하는 결과를 확인한다. 단위·기술 용어를 먼저 외우게 하지 않는다.
- 기본값은 visible preset과 변경 요약에 명시한다. 색/스타일·인물 identity·잠긴 객체를 요청 없이 바꾸지 않는다. 잠금 해제, 외부 전송, 비용 발생은 단순 모호성 질문과 별도의 권한 결정이다.
- 모델은 사용자 요청을 proposal로 해석할 뿐 승인 권한을 만들지 않는다. unknown 실행 결과는 재제출 대신 기존 job 조회로 이어간다.

## 6. worker·산출물·권리 경계

신뢰된 compiler만 bpy 코드를 구성하고, 모델은 데이터만 제공한다. 작업별 디렉터리·프로세스·시간/CPU/메모리 한도와 읽을 수 있는 승인 자산을 제한한다. 네트워크 차단과 파일 격리는 **실제로 검증할 gate**이지 subprocess 사용만으로 충족됐다고 주장하지 않는다. 임의 addon/raw exec, 외부 link, 자동 Python 실행, drivers/handlers가 포함된 자산은 검증 없이 열지 않는다.

취소/timeout/worker crash는 임시 결과를 완료 후보로 등록하지 않는다. 검증된 결과만 원자적으로 게시하고, request/scene/profile hash로 중복 제출을 구별한다. 취소·실패·접수 불명·재시작 후 interrupted 상태와 기존 결과는 각각 보존한다. 같은 version/seed/profile에서 재현성을 시험하되 OS·GPU·Blender 버전 간 bit-identical 결과를 미리 보장하지 않는다.

fal 경로는 선택 모델의 **실제 지원 입력**만 사용한다. 지원되는 이미지/시작 프레임 등을 권리 확인 후 전달하며 `.blend`, depth, normal, camera JSON을 보편적 입력으로 가정하지 않는다. 지원하지 않으면 명확히 차단하고 임의 변환/대체 모델을 쓰지 않는다. 직접 렌더와 생성형 재해석은 UI와 provenance에서 구분한다.

## 7. 실행 전 gate와 수용 시나리오 — 아직 실행하지 않음

|ID|검증할 시나리오|수용 근거|
|---|---|---|
|BM-G0 환경·출처|버전/commit/license와 실제 Blender 실행환경, headless·font·렌더·종료·격리 확인|고정 manifest, 작은 무과금 단순장면 probe. 미설치/권한 실패면 정확한 blocker; 자동 설치/REA 우회 없음|
|BM-01 선택형 진입|모델화 건너뛰기와 진입/취소|기존 모델선택·Take·편집·출력 상태 불변, 되돌아갈 경로 존재|
|BM-02 동일 데이터 편집|채팅으로 light 변경 후 직접 brightness 조정, 다시 채팅 조회|동일 scene/revision/diff, 초안 보존, stale 응답이 새 값 덮지 않음|
|BM-03 방향 기준|카메라 회전 전후 화면왼쪽/인물왼쪽 요청과 미지정 요청|각 basis로 예상 방향을 계산·프레임으로 확인. 모호한 경우만 질문하며 명확한 요청에는 반복 확인 없음|
|BM-04 범위·잠금|‘빛 방향만’ 변경, 잠긴 객체와 다른 작품 자산 제안|허용된 diff 외 변경0, 잠금/foreign/stale 거절, source·canon·원본 hash 불변|
|BM-05 카메라·시간|거리/높이/target/lens 프리셋 및 선택적 짧은 path|단위·FOV 변환·target 구도·정수 frame 일치; preview와 export의 동일 평가값. 미지원 path는 버튼으로 가능하다고 약속하지 않음|
|BM-06 버전·승인|apply→새 revision→restore→reopen, 승인 뒤 입력 변경|이전 version/output 보존, restore는 새 revision, 변경 입력에 오래된 render 허용 재사용 불가|
|BM-07 실패·취소|worker crash/timeout/cancel/디스크 실패/중복 요청|미완성 Take0, 기존 결과 보존, 실제 상태와 다음 행동 표시, 불명 작업 자동 재제출0|
|BM-08 두 출력 경로|고정 장면 직접 렌더 vs 지원되는 fal reference|직접 렌더 manifest·frame 검증과 생성형 provenance 분리. 지원불가 입력 차단; 실 fal 검증은 별도 허용된 live gate|
|BM-09 실제 UX|1920 기본/긴 한글/dirty/error/keyboard와1280 보조|preview+선택 대상+핵심조작 가시, 패널scroll/focus 접근, 숫자·프리셋 대안, 의미 있는 상태. 앱배율과 실제zoom 별도|
|BM-10 실제 모델 저작|허용된 경우 선택 chat의 원 tool 응답→검증→사용자 적용→로컬 렌더|hand-authored fixture와 실제 모델 산출을 분리. raw response의 공개 가능한 근거·정확한 diff·최종 파일이 연결돼야 E2E로 판정|

## 8. 단계·소유·종료

**현재는 P0 문서 단계만 완료**했다. 부모가 이 계획의 이유·대안을 설명하고 구현 범위를 별도로 확정하기 전에는 설치/컴파일/렌더/모델 호출/DB 변경을 하지 않는다.

후속 순서는 P1 버전·license·worker capability(BM-G0) → P2 pure SceneSpec/typed diff/validator → P3 승인 자산을 쓰는 로컬 preview·render·버전/복원 → P4 Aethon UI·채팅 연결/실제 화면 → P5 별도로 허용된 모델 저작·필요 시 지원 fal 경로다. 제품 writer는 기존 통합 담당 한 명, 독립 담당은 frozen build의 계약·실제 화면·산출물을 검토한다. 기존 2D motion/fal/편집 guard를 불필요하게 재작성하지 않는다.

각 단계는 해당 수용 사례·영향 회귀·source/served hash·동일 조건 전후·실행 제한을 갖춘 뒤 닫는다. 계획 완료, backend 통과, 사용자 UI 완료, 실제 공급자 성공을 네 상태로 구분한다. 프로덕션용 모델링/리깅, physics, 복잡한 재질/노드, 자유 곡선 camera rig, 협업, 모바일 전면개편, 임의모델코드 실행은 초기 범위 밖이며 자동 추가하지 않는다.

미결정: 실제 설치/버전·engine/device, 정확한 resource profile, 승인 자산 형식/검역, license 배포 영향, path 활성화 범위, live 제공자 입력·가격 검증. 이는 숨겨진 완료 조건이 아니라 P1–P5 진입 gate다. 이번 문서의 검증은 기존 동등 문서 검색, 요구/대안/수용항목 및 링크 정합성 확인만이며 제품 시험0이다.
