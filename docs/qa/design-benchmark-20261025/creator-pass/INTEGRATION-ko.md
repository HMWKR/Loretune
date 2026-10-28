# 통합 담당자용 checkpoint

**적용 가능한 후보와 검증 완료. 공유 앱에는 미적용.**

- 패치: `integration-creator.patch` (index.html만 변경하는 정확한 unified diff)
- 재현: `build_candidate.py`, 독립 `creator.css`, `creator-ui.js`, `creator-renderers.js`
- baseline SHA256 `0a8ef8436b8d751c4581c648beeaa688f054217b5781d1a9528c30d2cca5c6ae`
- candidate SHA256 `68d1032f86aabbfc858dcf734c90f685b577cc2f1c277931d0ab0de19bb0ba14`
- 원본 index와8773의 해시는 종료 시 동일. TaskSpace14 종료, 서버 재시작·소스·DB 변경 없음.

## 병합 순서와 계약

`docs/qa/multimodel-architecture-gap-20261025/implementation/PRESENTATION-CONTRACT.md`를 읽었다. 현재 candidate는 고정 서버 계약만 미리보기한 것이며 새 live 연결을 활성화했다고 표시하지 않는다. 새 backend/staging 데이터 전체를 구버전 HTML로 덮어쓰지 않는다. hash가 같을 때만 본 diff를 바로 적용한다. 다른 frontend hunk와 겹치면 아래 presentation renderer 단위로 병합한다.

- 기존 ID, form name, action handler, data-* 식별자, 승인 조건, 가격/예산 gate는 보존. 기존 `createTakeReviewStore`/`createTakeReviewController` F07 코드는 byte-for-byte 불변.
- `renderTakeReview` 마지막에 `renderCreatorReview(c,local)`을 합성. helper가 form/저장된 결과 표시만 나눈다. 외부 `act()`/API payload 변경 없음.
- `drawModelSettings`는 state.model_catalog의 role/id/model/state/reason을 사용. 새로운 chat3/image2/video2 목록을 받아도 선택 값은 id 그대로다. `integration_unverified`=연결 확인 필요, `integration_blocked`=사용 불가. 선택 저장 자체는 권한 아님.
- `media_actions`/`media_prepare`/`media_approve`/rights declaration 새 fields나 handler를 이 diff에서 삭제하거나 덮어쓰지 말 것. 이 후보는 해당 미구현 UI를 지원한다고 주장하지 않는다. 새 UI는 장면/모델/입력/견적·만료/승인·진행을 기본에 두고 action ID는 연결 attrs에만 둔다.
- 새 live 모델을 검증하기 전 disabled 유지. 일반 chat의 합성 전용 제한을 해제할 기능 근거가 있다면 functional 계약에 맞춰 capability 설명도 변경해야 한다. 이번 candidate의 고정 `anthropic-live` 설명은 현재 서버 허용 범위를 정직하게 유지한 것이다.
- fal 신규 job에 기존 image recovery action을 임의로 연결하지 않는다. can_status/can_collect 조건은 기존 경로만 존중한다.
- Runway는 벤치마크 참조 전용. provider나 credential 안내에 추가하지 않는다.
- `showRenderPreview` 변경은 제목/테스트 배지 markup뿐. 승인 자막 track/onload/onerror 보호는 그대로. output test 여부는 immutable snapshot의 selected media reason에서 확인한다.

## 검증

`node docs/qa/design-benchmark-20261025/creator-pass/test_creator.mjs`:21pass.
inline script4개 `node --check` pass. `git apply --check` pass (checkout에 .git이 없어도 apply 검사 가능).
브라우저 후보: 별도 iframe, GET만 허용. 7interaction checks pass, duplicate IDs0, runtime errors0, 요청 mutation0, project JSON unchanged. `browser-interaction-results.json`, `candidate-primary-results.json`.

새로운 기능과 합친 뒤 필수 recheck: 승인/거절 read card→수정→새 입력 중 지연 save→context 전환→cancel→reload, 사용자선택 모델 전체명/미검증/차단, 새 media action 가격/사람 승인/rights, 출력v2와 편집v3 및 자막 분리. 이 검증 뒤 실제 통합 screenshot을 독립 평가자에게 전달한다. candidate 점수는 부여하지 않았다.

최종19파일 기능 패치의 추가 계약은 [CONTRACT-ADDENDUM-ko.md](CONTRACT-ADDENDUM-ko.md) 참조. 독립 copy adapter와8개 테스트를 추가했으며 기존 통합 diff/후보 hash/캡처는 변경하지 않았다. 실제 새 proposal 카드 hookup은 통합 세션에서 수행한다.
