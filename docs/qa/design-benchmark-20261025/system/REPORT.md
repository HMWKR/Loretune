# 디자인 시스템 후보 · 통합 체크포인트

2026-10-25 10:43 UTC. **후보 CSS와 정확한 patch 준비 완료. 공용 소스에는 아직 미적용.** 같은 빈 장면/작품/viewport로 임시 탭에 적용해 desktop·mobile을 검증했다. 전체 제작 flow는 기능 세션 통합 후 동일 revision에서 이어갈 항목이다.

## 먼저 통합할 파일

1. `design-system.css` — 기존 무채색 브랜드를 유지한 semantic tokens와 component rules. `.lt-system` opt-in.
2. `integration-system.patch` — 현재 `index.html`에 CSS inline 추가, body opt-in, 기존 project/mode toolbar 2개를 wrapper로 묶기만 한다. JS/backend 변경 없음. 현재 정적 CSS route에 의존하지 않는 방식. `git apply --check` 통과.
3. `model-full-name.patch` — 모바일 native select에서 잘리는 전체 release ID를 별도 문단에 표시하고 선택 변경에 동기화. `aria-describedby` 연결. **생성 patch의 JS syntax와 apply check만 통과; 실제 통합 UI 재검증 필요.**

두 patch는 같은 `a2664470…` 소스 기준이며 서로 다른 구간을 변경한다. 기존 `integration-followup.patch`를 다시 적용하지 않는다. 현재 소스에는 model dialog, 간격 보완이 이미 반영되어 있다.

## 비교 결과와 중요한 결함

|항목|현재 실제 화면|후보/후속 조치|
|---|---|---|
|P1 미디어 가시성|1280×900에서 preview bottom1002px로 주요 조작이 화면 밖|후보 bottom778px, take 비교 버튼도 첫 화면에 보임. project/mode 행 통합 및 요약/next 같은 행|
|P1 모델 식별|320px에서 `fal-ai/kling-video/v2.6/pro/image…`로 release 잘림|별도 full-name patch 제공. native select 자체 줄바꿈에 의존하지 않음|
|P2 selected/primary 혼동|단계 선택과 대표 CTA 모두 흰색|선택은 charcoal+underline, 실행/다음 CTA는 흰색. 별도 focus outline 유지|
|P2 모바일 수직 밀도|390 preview top785 / 320 top836|후보 top695 /746. 빈 shot board만 compact. 320 bottom912로 첫 화면에 전체 미디어가 들어오지는 않음|
|P2 상태 시스템 미완결|모델 불가 이유는 있으나 chat/action/job 전체 상태를 이번에 완주하지 않음|컴포넌트 상태 계약 제공. backend 상태 없는 성공/진행 표시를 CSS로 만들지 않음|

최초 audit와의 역사 비교는 상위 `report-ko.md`, `latest/REPORT.md`를 본다. 이번 전후 쌍은 모두 **MS 계약 검증 A / step3 / 음원0·장면0 / 900px height / reduced-motion reduce**로 동일하다. 다른 fixture의 결과와 섞지 않았다.

|동일 viewport|baseline preview (y / h / bottom)|candidate preview (y / h / bottom)|가로 overflow|
|---|---|---|---|
|1280×900|529 /472.5 /1001.6|373 /405 /778.1|둘 다0|
|390×900|785.4 /205.9 /991.3|694.9 /205.9 /900.8|둘 다0|
|320×900|836.5 /166.5 /1003.0|746.0 /166.5 /912.5|둘 다0|

## 참조와 디자인 방향

5개 참조의 역할을 나눴다. 주 참조는 Krea Refero style의 dark-neutral/white action과 기존 Loretune, 보조는 [Clipchamp 편집 flow](https://refero.design/flows/10860)의 media/timeline 배치와 [ElevenLabs flow](https://refero.design/flows/8684)의 작업물 가까운 review/export다. 이번에 Refero 실제 screen image를 열어 확인했다. 색상·서체 metadata에 불확실성이 있어 직접 계측으로 표시하지 않았다.

[Neural Frames](https://www.neuralframes.com/)는 signup, [Tunee](https://www.tunee.ai/)는 login/create-account 경계까지만 접근됐다. 내부 editor, responsive, 상태 전이 토큰은 미확인. 인증·업로드·생성·결제 없이 중단했다. signup/landing의 computed styles를 내부 editor 토큰으로 일반화하지 않았다. 세부 **M(실계측)/R(Refero metadata)/V(이미지 관측)/P(제안)** 구분은 `TOKEN-COMPARISON.md`에 있다.

Loretune 고유 의미는 대화→버전 있는 계획→IP/인물/장소와 연결된 장면→사람 검토→출력이다. 선택/승인/실행/수신을 구분하고, 비용/모델 release/만료는 실행 근처에 둔다. 경쟁사 로고·브랜드색·마케팅 hero를 복제하지 않았다.

## 검사 범위와 rubric

휴리스틱 0=부재/불가,1=큰 마찰,2=기본 가능하나 마찰,3=관측 fixture에서 명확,4=관련 전체 상태+실사용자 검증. 실제 사용자 연구가 아니며 총점은 내지 않는다.

|관점|현재→후보|근거/제한|
|---|---|---|
|미디어 중심 배치|2→3|동일 desktop 빈 장면에서 전체 preview+비교 버튼 노출. 실제 media 재생은 미검증|
|역할/선택 위계|2→3|selected와 primary의 표면/underline 분리. 이해도 사용자 연구는 없음|
|token 일관성|2→3|surface/type/space/radius/action/state 명시. 새 상태 DOM은 일부 미연결|
|모바일 작업성|2→2|overflow0/빈 board 압축, 전체 모델 ID와 긴 flow는 후속 통합 필요|
|오류·상태 회복|2→미평가|이전 audit에서 발견한 오류 회복은 이번 후보 검증에서 재실행하지 않음|
|전체 키보드/확대/스크린리더|미평가|부분 keyboard 결과를 전체 준수로 확대하지 않음|

모델 dialog는 Enter로 열리고 초기 닫기 버튼에 focus, Escape로 닫고 호출 버튼에 focus 복귀했다. focus outline white2px 확인. 1280/390/320에서 dialog 가로 넘침0. reduced-motion emulation에서 transition0s 확인. OS 설정/고대비/스크린리더 미검증.

`contrast-check.json`: 지정 opaque 조합에서 본문17.45:1, secondary8.74:1, disabled5.58:1, controlborder4.00:1. 수학적 token 조합 확인이며 전체 화면 WCAG 준수 판정이 아니다.

**실제 browser200/400% zoom은 미확인.** 이전 Meta+Equal 조작은 viewport/dpr 변화가 없어 성공으로 인정하지 않았다. 이번 320/390 viewport emulation도 browser zoom을 대신하지 않는다. loading/error/unknown/model unavailable/plan review 전체 상태 전이, keyboard 제작 완주, 결과 preview 재생/출력, 긴 한국어2000자·30샷은 후속 통합 flow 대상이다.

## revision과 증거

10:40:47 UTC GET `/` SHA256와 10:42:25 로컬 `index.html` SHA256가 모두 `a2664470f4680a84da5b683d28de32e607a15187aca01956d787925255344969`로 일치했다. 예전 `served-revision.json`은10:13 기록이므로 현재 판정에 재사용하지 않았다. 테스트 탭은 이전에 로드한 화면에 메모리 CSS/wrapper만 주입했다. GET 일치가 메모리 탭 전체의 동일 revision을 증명하지 않으므로 **통합 후 reload+hash 후 전체 flow**가 필요하다. 후보 CSS SHA256는 `175dc1899ea725489e7d20f043333e5fa6be59133c8c2b047dc2c8b57e4186df`.

최종 전후 이미지6개와 model dialog3개 모두 저장 후 이미지로 열어 검사했다:

- `final-baseline-1280.png` ↔ `final-candidate-1280.png`
- `final-baseline-390.png` ↔ `final-candidate-390.png`
- `final-baseline-320.png` ↔ `final-candidate-320.png`
- `candidate-models-1280.png`, `candidate-models-390.png`, `candidate-models-320.png`

측정 원본: `final-metrics.json`, `dialog-metrics.json`, `loretune-computed.json`. 초기 `loretune-candidate-desktop.png`는 실제 viewport888이라 matched 비교에서 제외. `neural-access.png`는 전환 중 빈 화면이라 근거에서 제외. `neural-auth-boundary.png`, `tunee-auth-boundary.png`가 최종 접근 경계 근거다.

## 통합 이후 수락 순서

기능 세션이 두 patch를 적용하고 freeze → public GET/source hash 비교 → 새로고침 → 동일 A 빈 상태/desktop/320/390 전후 재캡처 → 전용 local fixture의 계획/모의승인/결과선택/검토/출력 전체 keyboard flow. 유료 생성 클릭·외부 upload 없이 수행한다. loading/failure/unknown은 기능팀 고정 mock fixture가 제공될 때 각각 캡처한다. 아직 미완료인 이 절차를 완료로 보고하지 않는다.

도구: 실제 UI Ego TaskSpace5를 별도로 사용하고 정상 finish 완료. Refero metadata/image 도구 사용. 이번 system 작업에서 Aside/REA 사용했다고 주장하지 않는다. 기존 다른 탭/공용 서버/.env/프로젝트 데이터 변경0. Ego Lite 업데이트 안내는 있었으나 업데이트하지 않았다. 현재 디자인 전달은 차단되지 않았고, full flow는 후보 통합 checkpoint를 기다리는 상태다. 이전 계획 재제출 auto-review 거절/토큰만료 기록은 `../latest/REPORT.md`에 보존했으며 재시도하지 않았다.
