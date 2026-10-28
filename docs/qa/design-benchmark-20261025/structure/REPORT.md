# Loretune 작업대 구조 개선 · 통합 대기

## 결과 먼저

**구조 후보를 구현하고 1280/390/320 실제 브라우저 화면에서 비교했다. 공용 앱에는 아직 적용하지 않았다.** 기존 색상 미세조정 대신 상단을 통합하고, desktop의 장면 rail / 미리보기 / 검토 inspector를 분리했으며, 타임라인 요약을 미리보기 아래에 함께 배치했다. mobile은 장면·미리보기·검토 중 현재 작업만 보여 준다.

**기능 세션의 실제 통합과 전체 회귀가 다음 단계다.** 작업 중 소스 변경과 일시적인 `ERR_CONNECTION_REFUSED`가 있었으나 부모의 복구 안내 후 같은8773에 재접속해 최종 후보를 다시 검증했다. 서버 재시작·새 listener·다른 기능 검증 서버 접근은 하지 않았다. 기존 저장된 synthetic 프로젝트를 이용했으며 프로젝트 생성/업로드/생성/승인/저장/외부 전송 없이 디자인 후보만 탭에 임시 적용했다.

- 즉시 검토: [나란히 비교 HTML](comparison.html)
- 통합: [integration-workspace.patch](integration-workspace.patch)
- 독립 원본: [design-workspace.css](design-workspace.css), [workspace-layout.js](workspace-layout.js)
- 근거와 설계: [DECISIONS.md](DECISIONS.md), [TOKENS-AND-STATES.md](TOKENS-AND-STATES.md)

## Neural Frames 접근 결과

현재 정상 인증된 `/videos`를 읽었고 All 목록은 비어 있었다. **로그인벽이 아니다.** 새 데이터 생성 없이 열 기존 editor는 확인하지 못했다. 계정/비용 부분이 포함된 인증 화면은 공유하지 않았다. 생성·삭제·이름 없는 버튼은 누르지 않았다.

[공식 Autopilot handbook](https://help.neuralframes.com/en/articles/12038142-handbook-the-four-stages-of-autopilot)에서 실제 제품의 Track/Storyboard 설명 이미지를 내려받아 저장하고 열었다. 이들은 **공식 튜토리얼의 기존 작업 화면**이며 현재 계정의 live editor 관찰이 아니다. 원본 캡처 파일명은 2026-04-09, 이번 다운로드는 2026-10-25 11:50 UTC. viewport/DPR를 알 수 없어 CSS px로 환산하지 않는다. 이미지의 보라색 숫자는 문서 주석이다.

|자료|확인된 화면|한계|
|---|---|---|
|[neural-official-track.png](neural-official-track.png)|음악 범위, 실제 waveform, 설정과 주 실행, 자막, 기존 clip 영역|3194×1494 원본 이미지; 현재 live state/동작 측정 아님|
|[neural-official-storyboard.png](neural-official-storyboard.png)|개념·스타일·인물, 우측 모델/비용/실행, 장면 이미지 grid|3210×1690 원본 이미지; 실제 computed token 미확보|
|공식 frame editor 튜토리얼 영상|공식 help에 embed URL 확인|직접 embed에서 오류153. 영상 프레임 캡처·타임라인 검증 근거로 사용하지 않음|
|기존 Refero Clipchamp / ElevenLabs|미디어+timeline 동시 배치 / 작업물 인접 검토·출력|이전 승인된 연구 재사용. 신규 관찰이라고 표시하지 않음|

## 세 가지 구조 차이와 적용

1. **상단 반복 안내**: 로고/프로젝트/모드/단계/설명/전체 요약/저장 안내/모델을 연속 배치하던 구조를 compact shell + stage + status로 줄였다. 모델 전체 이름과 상태는 삭제하지 않고 명확한 설정/상태 진입에 보존했다.
2. **미디어와 조작의 거리**: 아래로 밀리던 Take 검토를 오른쪽 inspector의 첫 항목으로 옮겼다. 샷 선택은 왼쪽, 비교와 기존 native video controls는 미리보기 가까이 유지한다. 이미지 fixture에는 가짜 재생 버튼을 추가하지 않았다.
3. **다음 작업의 맥락**: 실제 timeline track/status를 같은 화면에 드러내고 정밀 편집·음원·자막·복원을 disclosure로 묶었다. 계획 승인, Take 검토, 모의 실행 승인, 출력 승인의 의미와 원래 ID/handler는 합치지 않았다.

## 동일 fixture 전후 실측

프로젝트 `디자인 통합 완주 QA 20261025 1100`, step3. 동일 단색 합성 이미지/1.5초 편집 데이터. 단색 이미지 자체는 감점하지 않았다. 값은 CSS px이며 actual viewport width/height를 함께 기록했다. 확대 표시는 시뮬레이션하지 않았다.

|항목|이전|구조 후보|의미|
|---|---:|---:|---|
|1280×900 작업대 시작|317|141|상단176px 절감, 약56%|
|미리보기 top / bottom|403 / 808|218 / 542|전체 preview와 아래 조작 동시 노출|
|Take 비교 버튼 top|956|556|첫 화면에 진입|
|Take 검토 기록 top|2437|346|미디어 옆에서 검토 가능|
|모의 작업 준비 top|1112|598|조건·카드와 함께 우측에서 확인|
|타임라인 요약|step3에서 숨김|614–781|미디어/비교/편집 맥락이 함께 보임|
|390×900 preview top / bottom|867 / 1073|356 / 562|선택 panel에서 preview 전체 노출|
|320×900 preview top / bottom|918 / 1085|374 / 540|선택 panel에서 preview 전체 노출|
|390 / 320 timeline bottom|step3 숨김|821 / 799|첫 화면 안에서 편집 진입|
|문서 가로 넘침|0 / 0 / 0|0 / 0 / 0|의도적 단계 strip/정밀 편집 내부 scroll은 별도|

치수 원본: [before-geometry.json](before-geometry.json), [candidate-geometry.json](candidate-geometry.json). 최신 accepted 후보 캡처는 12:17 UTC. 모바일 resize 후 두 animation frame을 기다려 panel 상태가 반영된 결과만 수락했다.

## Desktop / mobile wire-layout

```text
DESKTOP >= 901
┌ Loretune · 작품 선택 · 작품/설정 · 상태                 모델 설정 ┐
├ 제작 단계 1 / 2 / 3 / 4                              다음 단계 ┤
├ 현재 과업 · 저장/오류 status                                  ┤
├ 장면184 ┬ 미리보기 fluid                     ┬ 선택 Take 검토288 ┤
│ rail    │ 실제 media + native video controls │ 이유/결정/기록      │
│         │ Take strip + 비교                  │ 별도 실행 승인      │
│         ├ 실제 timeline/status               │ 참고/의견 disclosure│
│         │ 정밀 편집 펼치기                    │ 독립 scroll         │
└─────────┴────────────────────────────────────┴────────────────────┘
MOBILE <= 900
작품 shell → 단계 strip/다음 → status → [장면 | 미리보기 | 검토]
현재 panel 하나만 노출. 미리보기 panel: media → Take/비교 → timeline.
모델/상태는 작품·설정 안에서 접근. ID와 원래 데이터/저장 handler 유지.
```

## 기존 rubric으로 본 변화

부모가 제시한 **45/100은 주관적 전문가 휴리스틱**이며 경쟁사 동일 과업 실험이나 사용자 연구 결과가 아니다. 이번에도 숫자를 객관적 경쟁력으로 바꾸지 않는다. 최종 통합과 키보드/상태 회귀 전에는 새 총점을 확정하지 않는다.

|항목 / 이전 점수|이번 직접 확인한 변화|남은 한계|
|---|---|---|
|정보구조11/20|프로젝트 shell 통합, 현재 미디어와 검토 인접|secondary 정보 발견성, 새 사용자 학습 검증 필요|
|타입·간격10/20|16/14/12 위계 유지하며 영역별 밀도 조절|실제200/400% 확대·긴 한국어 전체 상태 미검증|
|미디어·효율7/20|preview·비교·검토·timeline이 desktop 첫 화면에 있음|독립 inspector scroll, 실제 영상 transport 및 전체 과업 소요시간 미검증|
|일관성·상태12/20|semantic surfaces, 선택/실행/오류 의미 보존|모바일 tab과 모델 Escape 복귀 확인. 새 승인/disabled 상태 전체 회귀 pending|
|브랜드·시각5/20|같은 테두리 카드 반복을 줄이고 media 영역에 집중|브랜드 리뉴얼 아님. 경쟁사와 같은 완성도를 입증하지 못함|

## 소스/패치와 검증 경계

- 최초 캡처는 HTML `25860298244aa518ed322fdc38cb8f9875168fb6c31aa766bc21dc3e2435acd3` 기반이었다. 최종 전후 파일은 아래 최신7426e5… 버전에서 같은 fixture로 다시 캡처했다.
- 12:03:04 UTC에 원본 HTML이 `7426e52fdb37487dbf7dba35344146a8d13408795aff9aa363334a860f6d5fa3`으로 변경됐다. 기존 browser script와 비교해 comment draft revision tracking/조건부 정리 변경을 확인했다. [source-change-observed.diff](source-change-observed.diff)에 보존했다.
- 최신 root와 served HTML 해시7426e5… 일치를 읽기 확인했고 최신 해시에 맞춰 패치를 만들었다. 일시적인 connection refused 이후 부모의 복구 안내에 따라 같은8773에 재접속했고 최종 후보 검증을 완료했다. [runtime-boundary.json](runtime-boundary.json)
- 첫 DOM 검사에서 `modelDefaultsBar` 누락을 발견해 보존하도록 고쳤다. 이어 detached node query로 생긴 null 텍스트와 설정 메뉴가 단계 전환 후 열려 있는 문제를 수정했다. 최종 runtime: ID 누락0, 중복0, null 텍스트0, 기존 핵심 handler 변경0, QA 프로젝트 fingerprint 변경0. [dom-preservation.json](dom-preservation.json)
- 최종 CSS의 disabled primary override와 inspector 여백8px가 포함된 상태로 캡처했다. 실제 disabled 전환과 모든 focus clipping 상태를 통과했다고 주장하지 않는다. 모바일 ArrowRight로 검토 panel 선택/포커스 이동, 모델 dialog Escape 닫기와 opener 복귀는 직접 확인했다. 출력 승인/렌더 CTA는 timeline 헤더 y627–667에 배치했다.
- `node --check`(독립 layout JS 및 통합 후보 scripts), `git apply --check` 통과. 실제 patch apply는 하지 않았다. 기존 기능 함수의 본문은 패치에서 변경하지 않는다.
- `app.py`는 `/`의 index.html과 assets/exports만 제공한다. 별도 CSS 파일 URL이 제공된다고 가정하지 않았으며 patch는 CSS/DOM enhancement script를 기존 index에 삽입한다. backend/server 변경 없음.
- keyboard-only 전체 흐름, 실제200/400% 브라우저 확대, screenreader, 오류/만료/재개/전체 모델 상태, 후보 통합 후 출력은 **미검증**이다. 기존 통합 전 전체 로컬 제작 QA 결과는 [../integrated-flow/REPORT.md](../integrated-flow/REPORT.md)에 별도로 보존돼 있으며 이 후보의 검증으로 전용하지 않는다.

## 기능 세션에 넘길 최소 절차

1. `candidate-manifest.json`의 base HTML hash와 최신 source 일치 확인. 다르면 보존된 patch를 검토해 재기반화.
2. `git apply --check` 후 기능 세션이 `integration-workspace.patch` 적용. 디자인 세션은 원본 index/backend를 직접 수정하지 않음.
3. 기능 세션이 통합된 freeze URL/revision 전달. 디자인 세션은 같은 QA 프로젝트를 재사용.
4. model 설정·모바일 탭 키보드·모든 단계·상세 작업대·숨긴 정밀편집·기존 승인/모의/출력 회귀. 의미상 승인과 비용 조건 누락 여부 우선 확인.

지원 문의·복구·재업로드는 사용자 지시에 따라 하지 않았고 사고 기록은 보존했다. Aside 직접 관찰과 Ego Lite0.6.0.20 / guide2.1.0을 사용했다. REA는 이번 구조 작업에 사용하지 않았다. Ego update 안내를 받았지만 설치/업데이트하지 않았다. 검증 Space8의 후보 점검을 완료했고 기존 사용자 탭과 기능 QA 탭은 건드리지 않았다.

## 최종 단계별 읽기 검증

1. 음악 입력: 음원/구간 UI 유지,1280 가로 넘침0. [화면](candidate-step-1-1280.png)
2. 계획 검토: 기존 입력/계획 카드 유지,1280 가로 넘침0. [화면](candidate-step-2-1280.png)
3. 장면 검토: desktop3영역 및 mobile focus panel; 미디어/검토/timeline 동시 접근. [화면](candidate-scenes-1280.png)
4. 편집·출력: preview 유지, timeline 승인·렌더 CTA y627–667, 기존 완료 job 표시. 새 렌더/승인 실행은 하지 않음. [화면](candidate-step-4-1280.png)

단계 전환과 읽기 표시 검사이며 새 후보에서 제작을 다시 완주했다는 뜻이 아니다. 기존 계획·모의·렌더의 실제 저장 승인 회귀는 통합 담당자의 다음 검증이다.
