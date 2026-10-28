# 디자인 시스템 통합 · 고정 체크포인트

2026-10-25T10:49:41Z부터 앱 소스 고정. **http://127.0.0.1:8773**에서 디자인 전체 흐름 재감사를 진행할 수 있다. 소유 exec session **78045**, 기존 격리 데이터 `/tmp/loretune-ms-qa-20261025`를 유지했다.

## 적용

- `index.html`만 앱 소스로 변경했다. 후보 `design-system.css`를 마지막 inline style로 통합하고 body를 `.lt-system`으로 opt-in했다. 프로젝트/모드 도구 행을 wrapper로 묶어 상단 높이를 줄였다.
- 선택 상태와 실행 CTA, focus/disabled/error의 의미 토큰을 유지했다. 원래 147개 ID와 모든 form을 보존했다. 추가 style ID 포함148개, 중복0. 원본 디자인 후보·감사파일은 변경하지 않았다.
- 모델 select마다 전체 모델명/사유 문단을 만들고 `aria-describedby`로 연결했다. 선택 변경은 표시 문구만 갱신하며 저장 버튼 전에는 backend model settings를 변경하지 않는다.
- 기존 승인·작업·예산·온톨로지 backend 로직은 변경하지 않았다. 이전 고정본의 모든 backend source hash가 동일하다.

## 검증

| 검사 | 결과/증거 |
|---|---|
| patch baseline·dry run | 기존 index SHA `a2664470…` 일치 후 원본 백업. 두 patch apply check 통과 |
| CSS 동일성/DOM | 통합 CSS가 후보와 정확히 동일, 기존 ID/form 보존, 명시 body opt-in. `static-check.json` |
| JavaScript | `node --check integrated-script.js` 통과 |
| 승인 경로 targeted | 6개 통과, `targeted-regression.log` |
| 전체 HTTP 포함 회귀 | **194개, 23.887초, 모두 통과**, `full-regression.log` |
| 재시작 | jobs/generation_jobs 진행0 확인, 기존 소유 session60587 Ctrl-C 종료130 확인 후 동일 주소 재시작 |
| 실제 제공 HTML | GET200, 로컬 index와 SHA256 일치: `cb810ea713f5865b7feecaaf510fc8d5851941216be78560bcb4ade3a6d576a3` |
| 1280×900 | 실제 Take1 있는 fixture, preview top403.48/bottom808.48/720×405, 가로 넘침0 |
| 320×900 모델 dialog | 전체 `fal-ai/kling-video/v2.6/pro/image-to-video`가 별도 문단에 줄바꿈 표시, 수신 차단 이유/aria 연결 확인. 문서·dialog 넘침0 |
| 390×900 | 문서 가로 넘침0 |
| 키보드 일부 | Escape로 dialog 닫힘, `editModelSettings`로 focus 복귀 |

브라우저는 기존 기능 검증 IAB4/tab7만 사용했다. 프로젝트 **실행 승인 QA 20261025**, step3, 선택된 합성 Take1이며 디자이너의 빈 fixture와 다르다. 따라서 403/808px 결과를 빈 fixture의 373/778px와 동일조건 비교로 취급하지 않는다. 모델 선택은 화면에서만 바꾸고 저장하지 않았다. viewport override를 해제하고 tab을 후속 검증용으로 보존했다.

캡처 `integrated-desktop.png`, `integrated-model-mobile.png`를 저장 후 직접 이미지로 확인했다. 메트릭 `browser-smoke.json`. 모델 label selector 1회가 no-match로 미실행되어 새 DOM 관찰 후 실제 combobox role로 선택했다. 데이터 재제출이나 유료 요청은 없었다.

## 다음 기능 턴으로 이월

**B03 미수정:** 사람 승인 후 chat 모델만 변경하면 기존 승인 media action claim이 전체 model_settings snapshot hash 변화로 blocked된다. B01의 job 인계 포함과 실행 계속 가능은 별개다. `../independent-action-bridge-recheck-20261025/REPORT.md`에서 B01/B02는 독립 통과, B03은 실제 Store 경로 반례로 확인됐다.

다음 기능 작업은 chat freshness와 승인 media input/model/price/dependency freshness를 분리하면서 실제 권리·grant 철회·미디어 입력/모델 변경 안전 검사를 유지하는 것이다. 이번 디자인 통합 턴에서는 이 코드를 수정하지 않았다. 일반 채팅 live 연결 및 일반 asset rights→claim 연결도 계속 남는다.

전체 keyboard 제작 완주, 실제200/400% browser zoom, screenreader, 모든 loading/error/unknown 상태 및 새 디자인에서 결과 출력 재생까지는 디자인 후속 고정 버전 QA 범위다. 이번 부분 점검을 전체 접근성/제품 완료로 계산하지 않는다. 실제 provider 호출·키 조회·사용자 자료 변경·배포는 이번 턴0.
