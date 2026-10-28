# 실제 creator 통합본 독립 디자인 검토

**기본 작업대의 내부 설명은 크게 줄었고, 저장된 검토는 사용할 수 있는 문맥 카드가 됐다. 모델 상태 모순과 기본 form 중심 표현이 남아 현재 표본 평가는70/100이다. 최소90에는 아직 미달한다.**

## 전달 가능한 실제 화면

| 화면 | Library 파일 ID | viewport·상태 |
|---|---|---|
| 다중장면 desktop | `libfile_2d137a902fb48191ad5ec838eb392b22` |1280×900·기존3장면·승인 Take|
| 같은 장면 비교 | `libfile_98f46c3741e881918260f3e2c45105f5` |1280×900·Take2/Take1·둘 다 승인|
| 모바일 검토 | `libfile_1cb5378d2730819190d6afd94dd17c2d` |390×844·저장된 승인·검토 수정|
| 승인/미검토 비교 | `libfile_be18f7db678081918364ec0f77710402` |1280×900·다른 기존 QA fixture·승인1/미검토2|
| 미저장 수정 | `libfile_02f67381ee508191840d4da33bf410a5` |390×844·실제 frontend의 임시 로컬 draft|
| 오류·입력 보존 | `libfile_a151b3382ddc8191a0b7b377c0ad22f1` |390×844·로컬 오류 투영, 서버 실패 아님|

이번에 직접 저장·이미지 도구로 열어 확인한 실제 통합 frontend다. 후보 CSS 주입/새 시안이 아니다. 단색 미디어는 기존 허용된 합성 fixture이며 품질 점수에 반영하지 않았다. 계정·키·결제 정보는 없다. Library identity 기록 성공.

Build `1b0ab597f7a16993cf9307ae4a5fdd948b7ed5948c2970b16b7d53670ef269b3`, 실제8773. 종료2026-10-25 16:11:39 UTC에도 동일. 전용 공간16 종료. 소스·서버·DB 변경, 생성·승인·출력 POST, 외부 호출0. [종료 확인](final-runtime-check.json)

## 흐름별 결과

1. **다중장면 작업대 — 개선 확인.** 같은3장면 fixture. 미리보기·native video transport·Take·timeline이1280×900 안에 함께 있다. 저장 검토는 메모와 검토 수정으로 시작한다. [desktop](01-actual-desktop-1280.png)
2. **Take 비교 — 표본 정상.** 양쪽 기본값은 다른 Take. 선택/승인 별도 표기. 별도 기존 fixture에서 승인/검토 대기도 확인. Escape 후 비교 버튼 focus 복귀. 이미지에 가짜 transport 없음. [비교](02-actual-comparison-1280.png), [혼합 상태](08-actual-approved-pending-comparison.png)
3. **모바일 검토 — 개선 확인.** 장면/Take/status/검토 수정이 첫 화면에 함께 있다. 긴 완료 form이 기본 화면을 차지하지 않는다. [390px](03-actual-approved-390.png)
4. **수정·전환·취소·오류 — 표본 통과.** 키보드 편집 진입, 장면A/B draft 분리, 지연 응답 뒤 새 텍스트, 오류 입력 유지, 현재 draft 취소와 focus 복귀, project JSON 불변.8checks pass. 저장 응답·오류는 로컬 모의 경계이며 서버 저장/실패가 아니다. [검사](draft-focus-checks.json)
5. **모델 설정→이미지 상태 — 모순 재현.** 저장된 이미지 모델FLUX Schnell을 이미지 패널은 미선택이라 표시한다. [선택](06-actual-model-selection-1280.png), [잘못된 상태](07-actual-image-status-1280.png)
6. **적용된 계획·편집안 — 구분 확인, 밀도 남음.** 장면 추가됨/새 편집 버전에 적용됨으로 표시하고 출력 승인과 구분. 기본 화면에 proposal ID 없음. 완료 카드와 큰 입력 form은 계속 공간을 차지한다. [계획](09-actual-plan-applied.png), [편집안](10-actual-edit-proposal-applied.png)
7. **Take 없는 장면 — 정상 진입.** 장면4의 미디어 연결 전과 기존 새 Take 연결 form 노출.390px document width390. [빈 상태](11-actual-no-take-390.png)
8. **버전·데이터 — 불변.** served/source hash 일치, project JSON 불변, runtime errors0·mutation attempts0. 임시 draft 복원 후 공간 종료.

## 내부 정보가 정말 정리됐는가

기본 작업대/비교/검토에서 job/hash/adapter/원장/schema/tool trace는 보이지 않았다. 출처·사용권·진단은 이름 있는 disclosure에 남았다. 모델명·미검증/차단·테스트 미디어·저장 상태·출력 승인 구분은 계속 보인다.

**완료된 것은 아니다.** registry 선택과 legacy 이미지 연결 상태가 별개 UI로 드러난다. 모델 화면은 제품명보다 긴 endpoint 식별자 반복이 강하다. 정밀 편집 일반 안내에도 ‘자산 해시를 다시 검사’라는 내부 표현이 남아 있다. 사용자에게 필요한 모델/결과/다음 행동과 진단을 더 정확히 나눠야 한다.

혼합 비교Take2는 실제 메모 ‘비교용 두 번째 합성 Take’를 보여주지만 같은 테스트 미디어 badge는 없다. 합성 사실을 감춘 것은 아니나 문장 패턴으로 provenance를 판별하는 방식의 일관성 한계다. 이번에 거절 상태를 새로 저장하거나 투영하지 않았으므로 새 런타임의 거절 상태 검증은 주장하지 않는다.

## 같은 과업의 전후 geometry

이전0a8ef843…의 같은3장면 fixture/1280×900과 비교. 새4장면 fixture는 상태 검사에만 쓰고 수치 개선량에 섞지 않았다.

| 항목 | 이전 | 이번 실제 통합본 |
|---|---:|---:|
| 작업대 시작 y |142|104|
| 미리보기 위쪽 y |224.1|206|
| 미리보기 크기 |736×324|736×324|
| timeline 아래쪽 y |885.4|867.3|
| 저장 검토 section 높이 |562.9|415.5|

상단38px, 검토147.4px 감소. timeline의18.1px 이동을 큰 구조 혁신으로 과장하지 않는다. 미디어 크기는 같다. [이번 측정](final-runtime-check.json), [이전 측정](../creator-pass/baseline-geometry-desktop.json)

## 같은5항목 평가

각20점.10–13은 사용 가능하나 큰 격차,14–17은 강점과 눈에 보이는 격차,18–20은 검사한 여러 상태의 높은 정리 수준이라는 기존 anchor 유지. 현재70은 픽셀·상호작용 표본의 전문가 heuristic이다. 이전66은 별도 평가자의 값이므로4점 차이는 통계적 효과 크기가 아니다.311코드 테스트를 점수로 환산하지 않았다.

| 항목 | /20 | 근거와 제한 |
|---|---:|---|
| 정보·행동 명확성 |16|읽기 카드/수정/모바일 정체성 개선. 선택 모델을 미선택이라 표시하는 모순 잔존.|
| 타이포·간격·위계 |15|메타/메모 분리와 중복 행 감소. 계획·모델은 긴 form·반복 label 중심.|
| 미디어·작업 효율 |15|실제 transport/비교/timeline 보존. 완료 제안·출력 맥락 추가 시 조작이 아래로 길어짐.|
| 컴포넌트·상태 일관성 |15|read/edit/dirty/error와 draft scope 일관. 모델 준비 상태·test badge는 불일치.|
| 브랜드·시각 완성도 |9|조용한 dark surface와 정돈된 구성. 기본 outline controls·회색 card 비중이 높음.|
|합계|**70/100**|**최소90까지20점 차이. 경쟁사 동등 수준/90으로 판정하지 않음.**|

경쟁사 UI를 이번에 다시 열지 않았다. 고정 참조는 [Clipchamp editor](https://refero.design/pages/be21ed55-791a-4527-91d6-be6551ad877f)의 media 우선 구성과 [ElevenLabs Studio](https://refero.design/pages/8f4551a8-6e46-40dc-94ad-05c708570e44)의 선택 맥락 조작이다. Neural Frames는 [기존 공식 Track 튜토리얼 이미지](../structure/neural-official-track.png)이며 직접 현재 editor 세션이라고 말하지 않는다. 동일 조건 경쟁사 사용자시험/점수는 없다.

## 다음 한 가지 개선

**선택 장면의 제작 상태 카드를 통합한다.** 모델 선택/실행 준비/기존 결과는 별개 사실로 표시하되 backend별 패널을 요구하지 않는다. FLUX 선택 시 ‘선택됨 · 연결 확인 필요’라고 하고 실행은 활성화하지 않는다. 실제 모순을 해결하면서 inspector의 메뉴·label 위계를 정리하는 bounded pass다. [구체 범위·수용 기준](NEXT-PASS-ko.md)

현재 실행본은 유지했다. 이 한 pass가90을 보장하지 않는다. 계획 form 밀도, 모델명 표현, 전체 control의 시각 완성도도 남는 격차다.

## 한계

실제200/400% browser zoom, screenreader, 고객 사용성 시험, 전체 keyboard flow는 수행하지 않았다.390px viewport를 zoom으로 계산하지 않았다. 비교 Escape·검토 edit/cancel 등 지정 경로만 확인했다. 유료 호출/provider activation/새 render는 하지 않았다. 실제 거절/공급자 오류/새 fal recovery 완료를 주장하지 않는다.311tests와 출력 성공은 구현 스레드의 별도 근거다.

Library 준비형 저장은 도구 가용성 확인 단계에서 불가로 종료돼 write가 시작되지 않았다. skill이 허용하는 local create 배치로6이미지와 identity 기록을 완료했다. 남은 전송 blocker 없음. Ego 업데이트 알림은 있었으나 설치·설정 변경은 하지 않았다.
