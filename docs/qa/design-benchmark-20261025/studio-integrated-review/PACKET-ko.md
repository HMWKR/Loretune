# 실제 통합 화면 전달 checkpoint — 2026-10-25

## 즉시 전달 가능한 Library 이미지

| 화면 | confirmed Library ID | viewport · UTC |
|---|---|---|
| 다중 장면 작업대 | `libfile_fbdc5d5982048191affb77174a93ae45` | 1280×900 · 14:37:20 |
| Take 2 / Take 1 비교 | `libfile_55d99f52cebc8191bb1a44746cbfdbec` | 1280×900 · 14:38:17 |
| 승인된 Take 검토 | `libfile_433c90e733208191bf7acf67c763681a` | 390×844 · 14:38:19 |

모두 실제 제공 앱의 screenshot이며 후보 CSS 주입 화면이 아니다. 저장된 PNG를 열어 확인했고 Library 저장 및 로컬 identity metadata 적용을 확인했다. 합성 단색 media이며 실제 AI 생성 품질 평가 자료가 아니다.

소스/served SHA-256: `0a8ef8436b8d751c4581c648beeaa688f054217b5781d1a9528c30d2cca5c6ae`. 14:47:22 UTC 종료 확인에서도 동일하다. 전용 Ego Lite TaskSpace 13은 정상 종료했다. 서버·공용 소스 변경 없음.

## 실제 실행 앱에서 확인한 수정

1. 비교 기본값 Left 2 / Right 1. 여닫은 전후 프로젝트 JSON 불변. Escape 후 비교 버튼으로 focus 복귀.
2. 장면/작품 전환에서 검토 결정·이유가 분리되고 원래 초안이 복원된다. 실제 새로고침 후에도 같은 탭의 초안이 복원됐다.
3. 실제 served controller/DOM의 저장 경계에 지연 test double만 적용한 브라우저 시험에서 성공 응답 전 새 입력, 실패 응답 뒤 입력, 다른 작품의 초안이 보존됐다. 서버 POST/실제 네트워크 장애 시험은 아니다. 원래 act를 복원했고, 시험용 로컬 초안은 해당 UI로 지웠다. 서버 프로젝트 JSON은 시험 전과 동일했다.
4. 선택/Take 승인/편집 사용/출력 승인이 분리된다. 현재 선택 Takes는 승인됐고 편집 v3는 출력 승인 대기다. 두 번째 장면의 비교에는 다른 pending Take도 남아 있다.
5. 모바일 document overflow 0, 검토 버튼 44px. 전체 keyboard 완주, 실제 200/400% browser zoom, screenreader, 고객 사용성 시험은 미검증.

기능 세션의 회귀 과정에서 fixture의 기존 거절 Take가 승인으로 갱신됐다. 따라서 이전 candidate와 데이터가 완전히 같은 전후 비교라고 주장하지 않는다. 기존 이력은 기능 세션이 별도로 보존 확인했다.

1280×900에서 안내 띠33px, 작업 시작y142px, preview y224.15/h324px, timeline 하단885.44px. 이전 실제 craft의 안내 띠59.15px/작업 시작168.15px보다 상단은26.15px 줄었지만, 더 풍부한 상태를 표시하는 Take/track은 커졌다. timeline이 더 위로 올라왔다는 주장은 하지 않는다.

## 잠정 동일 rubric 평가

실제 표본 화면과 상호작용에 대한 전문가 휴리스틱 **69/100**: 정보·행동16, 타입·간격14, 미디어·효율15, 컴포넌트·상태16, 브랜드·시각8. 각20점 기준과 이전 평가 기준을 유지했다. 90달성이나 경쟁사 동등성·제품 완성도 판정이 아니다. 독립 리뷰어의 새 화면 판정 전 잠정치다.

가장 중요한 남은 문제는 **검토 대상의 맥락과 기록을 창작자 관점으로 보여주지 못하는 것**이다. 모바일 검토 탭에서 실제 두 번째 장면의 전체 이름은 visible body에 없고 `Take 2 검토`만 보인다. 저장된 승인도 긴 입력폼과 비활성 버튼 두 개로 보인다. [실제 모바일 근거](actual-long-scene-mobile-context-390.png), [관측 JSON](reload-gap-end.json).

다음 정확한 개선은 검토 패널에 장면 이름+Take identity를 계속 노출하고, 저장된 검토를 요약으로 보여주며 `검토 변경`으로 기존 폼을 펼치는 것이다. 미검토/미저장/실패 상태는 폼과 필요한 다음 행동을 바로 보여야 한다. provenance·권리·테스트 미디어 구분은 유지한다.

## 최신 사용자 요청을 반영한 다음 pass

14:45 UTC 사용자의 불필요한 내부 시스템 정보 비노출 요청에 따라, inspector만이 아니라 음악/계획/장면/비교/모델/승인/편집/출력/오류 화면 전체를 4분류로 감사해야 한다: 결정 필수, 선택적 맥락, 운영·개발 진단, 중복 노이즈.

현재 비교창의 전체 SHA-256, 내부 job 식별자, QA 설명 문단은 기본 창작자 화면에 불필요한 후보가 분명하다. 이를 삭제하는 대신 명시적인 진단/기록에 보존하고 기본 UI는 다음 행동으로 번역한다. 모델 선택·비용/승인 범위·진행과 오류 영향·저장 상태·의미 있는 출처/권리는 유지한다. mock은 간결한 `테스트 미디어` 표시로 정직하게 구분한다. 온톨로지는 재사용할 캐릭터/스타일/설정으로 설명한다.

다음 산출물: 화면별 before/after copy·가시성 결정표와 정밀한 creator-facing simplification 후보 patch. **이 checkpoint에서 전체 화면 분류와 해당 후속 patch는 아직 작성하지 않았다.** fresh screenshot packet을 먼저 전달하기 위한 경계다. 공용 소스 소유권은 기능 세션에 있다.

## 파일과 저장 경계

- [Desktop](actual-multiscene-desktop-1280.png), [Comparison](actual-comparison-1280.png), [Mobile](actual-review-390.png)
- [Library identity](library-images.json), [Desktop metadata](desktop-metadata.json), [Comparison/mobile metadata](comparison-mobile-metadata.json)
- [Runtime async draft 결과](runtime-draft-results.json), [새로고침·잔여 결함·종료 hash](reload-gap-end.json)

첫 Library batch helper는 tool discovery 단계에서 `Library prepare_uploads is not available`로 종료돼 저장이 시작되지 않았다. 지원되는 로컬 create route에서 위3개 저장을 완료했다. 미해결 업로드/승인 blocker는 없다. 브라우저 업데이트 알림은 확인했으나 설치하지 않았다.
