# 최신 8773 디자인 재감사

가장 큰 개선은 모델 설정의 dialog 전환이다. 동일 MS 계약 검증 A의 빈 장면·1280×900에서 이전 펼침 패널의 preview y=964.6 대비 현재 닫힌 dialog의 y=529.1이다. 이전 **접힘** 상태와의 개선량으로 해석하면 안 된다. preview 높이472.5/하단1001.6이므로 완전히 보이지 않으며 테이크 조작부도 첫 화면 아래다. 설정을 열 때 배경 작업대를 밀지 않고 modal로 덮는다.

## 적용 및 실행 경계
- 기존 followup의 좌우16px·문단1.6/줄바꿈은 실제 source/style에 반영. `#modelSettingsPanel>div max-width:960px`는 미반영이나 dialog 자체640px로 대체되어 필요 없음. 이전 followup patch를 재적용하지 말 것.
- startup manifest: docs/qa/action-grant-milestone-20261025/served-revision.json, recorded_at 2026-10-25T10:13:54.906227Z. 이번 브라우저 GET `/` 해시와 시각은 served-frontend.json; 이후 disk index 해시는 revision-check.json. backend 내부 revision을 별도 endpoint로 확인한 것은 아니다.
- 검사 도중 `접근 토큰이 만료되었습니다. 새로고침하세요.` 관측. 서버 재시작을 추정할 수 있으나 직접 확인하지 않았다. 이후 쓰기 검증을 중단했고 최신 action/grant UI 수락을 주장하지 않는다.

## 확인한 흐름
1. 기존 MS 계약 검증 A 음악/빈 장면 → 모델 dialog: 1280×900,320×900,390×900. 페이지 및 dialog 가로 넘침 없음. 320 긴 모델 선택값은 잘림; 상태 설명은 별도 문단으로 읽힌다. 전체 model ID를 항상 볼 수 있는 보조 텍스트는 아직 필요하다.
2. Escape로 model dialog 닫기 → editModelSettings 포커스 복귀 확인.
3. 전용 `디자인 QA 독립 20261025 최신` 생성. 입력/Tab/Enter로 제출, 생성 완료 후 newProject 포커스 복귀. 기존 A/B 데이터 변경 없음.
4. 긴 한국어 2장면 로컬 계획 미리보기 → 계획v1 검토 대기 저장. 외부 호출 없음. 승인 Enter 시 음악 구간 미확정으로 서버 거절, notice로 포커스 이동 및 오류 표시. 계획은 반영되지 않음.
5. 내부 synthetic-tone.wav를 전용 작품에 로컬 연결, 4초/48kHz 파형과 player 표시. 0–2초 구간 확정 시도는 토큰 만료로 실패. 저장된 계획1/음원1/음악 구간 미확정 상태를 읽기로 확인. 실제 렌더/출력까지 full journey 통과 아님.

## 실제 결함과 최소 패치
- P1: 승인 조건을 만족하지 않은 계획에도 승인 버튼이 활성. 서버 거절은 안전하지만 불필요한 실패를 유발한다. `plan-prerequisite.patch`는 duration null 장면이 있는 계획의 승인 버튼을 비활성화한다. 기존 음원 안내 문단은 유지. source에 적용하지 않은 검토용 diff이며 현재 기능 writer가 충돌 확인 후 통합해야 한다.
- P1: 상단5개 영역이 약471px를 차지. 모델 panel 문제는 개선됐지만 작업물+조작을 동시에 볼 수 없다. 다음 구조 변경 시 작품 선택과 모드 전환 toolbar 합치기 및 현재 단계 요약 압축을 권고. CSS로 DOM 순서를 시각적으로 뒤집지 않는다.
- P2: 음악 구간 미확정 오류의 회복 동작이 텍스트뿐. notice에 `음악 입력으로 이동` 버튼을 제공하고 해당 disclosure를 열면 재탐색을 줄일 수 있다. 토큰 만료도 명시적인 새로고침 동작이 필요하나 저장 전 입력 보존 범위와 함께 구현해야 한다.
- P2: 빈 샷의 prepareGeneration/assignReference/reviewReference/reviewTake disabled=false. 실제 실행은 클릭하지 않았다. 필요한 샷/선택 take 부재 시 비활성화+근거 표시 권고. 서버 안전성 결함으로 단정하지 않는다.

## 휴리스틱 rubric
0 부재/불가,1 큰 마찰,2 기본 가능하나 명확한 마찰,3 관측 상태에서 명확,4 전체 상태+실사용자 검증. 실사용자 연구가 아닌 전문가 관측이며 총점 없음.

|항목|이전→현재|근거|
|---|---|---|
|제목·진행 행동 위계|3→3|20px 제목, 흰색 CTA 유지|
|미디어 우선 공간|1→2|열린 설정이 밀던 작업대 복구, preview 전체는 아직 화면 밖|
|모델 설정/승인 의미|3→3|dialog와 별도 미연결 문단, 승인 비용 분리|
|모바일|2→2|가로 넘침 없지만 수직 chrome과 모델명 잘림|
|오류 회복|미평가→2|notice focus 정상, 회복 버튼 없음|
|키보드 전체 흐름|미평가|일부 Tab/Enter/Escape 확인, 전체 출력 완주 못함|

## 미검증 및 차단
실제200/400% browser zoom: viewport override를 해제한 정상 창에서 Meta+Equal4회 시도했으나 innerWidth900/dpr2/scale1 불변. 성공 주장 안 함. CSS zoom/CDP pageScale을 실제 browser zoom 대용으로 쓰지 않았다. 스크린리더, 전체 대비, 로딩 중 상태, 결과실패, 실제 미디어 preview 재생/출력, 전체 keyboard 제작 완주는 미검증.

자동 승인 심사가 계획 재제출을 거절: 이전 timeout 뒤 결과가 불확실하여 중복 저장 위험이라는 이유. 거절된 명령은 실행되지 않음. 이후 읽기 전용 확인은 성공했고 계획1/구간미확정/토큰만료를 확인했다. 해당 재제출은 재시도하지 않았다. 계속하기 전 최신 실행본·토큰과 기존 계획을 다시 확인해야 한다.

## 증거
01-scenes-1280.png,02-model-dialog-1280.png,model-320.png,model-390.png,scenes-390.png,03-local-plan-review.png,04-plan-blocked-error.png,05-audio-state.png 모두 저장 후 이미지로 열어 검사. 전후 동일 A 작품 비교는 첫5개이며 이후3개는 신규 독립 fixture이므로 동일 데이터 전후 비교 아님. 03의 계획 카드 전체는 화면 아래로 일부 잘려 전체 카드 증거로 쓰지 않는다.

Ego 별도 TaskSpace4. 사용자/기능 탭 접촉0. 서버 재시작0, 유료 생성0, 외부 업로드0. Ego Lite 업데이트 안내 있으나 업데이트 안 함. 기능 테스트180+4의 결과는 인계 맥락이며 이 디자인 검사 자체의 결과가 아니다.
